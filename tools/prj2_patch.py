"""Small in-place edits of a .prj2 written by tools/prj2.py (uncompressed): add a level texture, retexture faces.
The file is re-serialised chunk by chunk; everything not touched is copied byte for byte."""
import struct

import prj2
from prj2_check import Reader


def chunks(data):
    """[(id, payload)] of a chunk list; stops at the END byte. Returns (list, bytes consumed)."""
    r = Reader(data)
    out = []
    while r.s.tell() < len(data):
        n = r.leb()
        if n == 0:
            break
        cid = r.raw(n)
        size = r.leb()
        out.append((cid, r.raw(size)))
    return out, r.s.tell()


def pack(items):
    return b"".join(prj2.chunk(c, p) for c, p in items) + prj2.END


def add_texture(settings_payload, path):
    items, _ = chunks(settings_payload)
    index = None
    for k, (c, p) in enumerate(items):
        if c == b"TeTextures":
            texs, _ = chunks(p)
            for tc, tp in texs:
                sub, _ = chunks(tp)
                if dict(sub).get(b"TePath", b"").decode("utf-8", "replace").lower().endswith(path.split("\\")[-1].lower()):
                    index = Reader(dict(sub)[b"TeI"]).leb()
            if index is None:
                index = len(texs)
                body = prj2.c_int("TeI", index) + prj2.c_str("TePath", path) + prj2.c_str("TeTextureCustomBumpmapPath", "")
                body += prj2.c_bool("Te512C", False) + prj2.c_bool("TeMagentaR", True) + prj2.END
                texs.append((b"TeLvlTexture", body))
                items[k] = (c, pack(texs))
    return pack(items), index


def edit_room(rooms_payload, name, fn):
    """fn(lx, lz, face_dict) edits {face: (coords, bbox, mode, texture)} of each sector of the named room."""
    rooms, _ = chunks(rooms_payload)
    done = 0
    for k, (c, p) in enumerate(rooms):
        r = Reader(p)
        nx, nz = r.leb(), r.leb()
        head = p[:r.s.tell()]
        items, _ = chunks(p[r.s.tell():])
        rname = dict(items).get(b"TeName", b"").decode("utf-8", "replace")
        if callable(name):
            if not name(rname):
                continue
            room_fn = lambda lx, lz, f, rn=rname: fn(rn, lx, lz, f)      # noqa: E731
        else:
            if dict(items).get(b"TeName", b"").split(b"\x00")[0].decode("utf-8", "replace").strip("\x00") .find(name) < 0:
                continue
            room_fn = fn
        for j, (c2, p2) in enumerate(items):
            if c2 != b"TeSecs":
                continue
            secs, _ = chunks(p2)
            for s, (c3, p3) in enumerate(secs):
                idx = struct.unpack_from("<i", p3, 0)[0]
                sub, _ = chunks(p3[4:])
                faces, rest = {}, []
                for c4, p4 in sub:
                    if c4 == prj2.cid(prj2.TEX_LEVEL2):
                        rr = Reader(p4)
                        face = rr.leb()
                        vals = struct.unpack("<12f", rr.raw(48))
                        mode, tex = rr.leb(), rr.leb()
                        faces[face] = ([(vals[i], vals[i + 1]) for i in range(0, 8, 2)], mode, tex)
                    else:
                        rest.append((c4, p4))
                before = dict(faces)
                room_fn(idx % nx, idx // nx, faces)
                if faces != before:
                    done += 1
                    for face, (coords, mode, tex) in faces.items():
                        us, vs = [q[0] for q in coords], [q[1] for q in coords]
                        body = prj2.leb(face) + prj2.f32(*[v for q in coords for v in q])
                        body += prj2.f32(min(us), min(vs), max(us), max(vs)) + prj2.leb(mode) + prj2.leb(tex)
                        rest.append((prj2.cid(prj2.TEX_LEVEL2), body))
                    secs[s] = (c3, p3[:4] + pack(rest))
            items[j] = (c2, pack(secs))
        rooms[k] = (c, head + pack(items))
    return pack(rooms), done


def load(path):
    d = open(path, "rb").read()
    assert d[:8] == b"PRJ2\x00\x00\x00\x00", "compressed or foreign .prj2"
    top, _ = chunks(d[8:])
    return d[:8], top


def save(path, head, top):
    open(path, "wb").write(head + pack(top))


def objects(path):
    """[(room name, kind 'mov'|'sta', type, (x, y, z) room-local, rot_y, lua name, extra)] of a .prj2."""
    from prj2_check import Reader
    _, top = load(path)
    out = []
    for c, p in chunks(dict(top)[b"TeRooms"])[0]:
        r = Reader(p)
        r.leb(), r.leb()
        items, _ = chunks(p[r.s.tell():])
        d = dict(items)
        name = d.get(b"TeName", b"").decode("utf-8", "replace")
        for oc, op in chunks(d.get(b"TeObjects", b"\x00"))[0]:
            rr = Reader(op)
            if oc in (b"TeMovTen2", b"TeMovTn3"):
                rr.leb()
                x, y, z, ry, rx, rz = struct.unpack("<6f", rr.raw(24))
                rr.leb()
                t = struct.unpack("<I", rr.raw(4))[0]
                ocb = struct.unpack("<h", rr.raw(2))[0]
                rr.raw(3 + 12)
                n = rr.raw(struct.unpack("<i", rr.raw(4))[0]).decode("utf-8", "replace")
                out.append((name, "mov", t, (x, y, z), ry, n, {"ocb": ocb, "rx": rx, "rz": rz}))
            elif oc in (b"TeStaTen2", b"TeStaTn3"):
                rr.leb()
                x, y, z, ry, rx, rz, sc = struct.unpack("<7f", rr.raw(28))
                rr.leb()
                t = struct.unpack("<I", rr.raw(4))[0]
                rr.raw(12 + 2)
                n = rr.raw(struct.unpack("<i", rr.raw(4))[0]).decode("utf-8", "replace")
                out.append((name, "sta", t, (x, y, z), ry, n, {"scale": sc, "rx": rx, "rz": rz}))
    return out


def add_objects(rooms_payload, room_name, raw_chunks):
    """Append object chunks [(chunk id, payload)] to the TeObjects of the room called exactly room_name."""
    from prj2_check import Reader
    rooms, _ = chunks(rooms_payload)
    done = False
    for k, (c, p) in enumerate(rooms):
        r = Reader(p)
        r.leb(), r.leb()
        head = p[:r.s.tell()]
        items, _ = chunks(p[r.s.tell():])
        if dict(items).get(b"TeName", b"").decode("utf-8", "replace") != room_name:
            continue
        items = [(c2, pack(chunks(p2)[0] + list(raw_chunks)) if c2 == b"TeObjects" else p2) for c2, p2 in items]
        rooms[k] = (c, head + pack(items))
        done = True
    assert done, room_name
    return pack(rooms)


def raw_objects(path):
    """[(room name, chunk id, payload)] of every object chunk; the payload starts with the LEB object id."""
    from prj2_check import Reader
    _, top = load(path)
    out = []
    for c, p in chunks(dict(top)[b"TeRooms"])[0]:
        r = Reader(p)
        r.leb(), r.leb()
        d = dict(chunks(p[r.s.tell():])[0])
        name = d.get(b"TeName", b"").decode("utf-8", "replace")
        for oc, op in chunks(d.get(b"TeObjects", b"\x00"))[0]:
            out.append((name, oc, op))
    return out


def edit_sectors(rooms_payload, room_name, fn):
    """fn(lx, lz, sec) may change sec = {"props": int, "floor": [4], "fsplits": [[4]...], "faces": {face: (coords,
    mode, texture)}} of every sector of the room called exactly room_name. Returns (payload, sectors changed)."""
    from prj2_check import Reader
    import copy
    rooms, _ = chunks(rooms_payload)
    done = 0
    for k, (c, p) in enumerate(rooms):
        r = Reader(p)
        nx, nz = r.leb(), r.leb()
        head = p[:r.s.tell()]
        items, _ = chunks(p[r.s.tell():])
        if dict(items).get(b"TeName", b"").decode("utf-8", "replace") != room_name:
            continue
        for j, (c2, p2) in enumerate(items):
            if c2 != b"TeSecs":
                continue
            secs, _ = chunks(p2)
            for s, (c3, p3) in enumerate(secs):
                idx = struct.unpack_from("<i", p3, 0)[0]
                sub, _ = chunks(p3[4:])
                sec = {"props": 0, "floor": [0] * 4, "fsplit": 0, "fsplits": [], "faces": {}}
                for c4, p4 in sub:
                    rr = Reader(p4)
                    if c4 == b"\x00":
                        sec["props"] = rr.leb()
                    elif c4 == b"\x07":
                        sec["fsplit"] = rr.leb()
                        sec["floor"] = [rr.leb() for _ in range(4)]
                    elif c4 == b"\x09":
                        sec["fsplits"] = [[rr.leb() for _ in range(4)] for _ in range(rr.leb())]
                    elif c4 == prj2.cid(prj2.TEX_LEVEL2):
                        face = rr.leb()
                        vals = struct.unpack("<12f", rr.raw(48))
                        mode, tex = rr.leb(), rr.leb()
                        sec["faces"][face] = ([(vals[i], vals[i + 1]) for i in range(0, 8, 2)], mode, tex)
                before = copy.deepcopy(sec)
                fn(idx % nx, idx // nx, sec)
                if sec == before:
                    continue
                done += 1
                out, seen = [], set()
                for c4, p4 in sub:
                    if c4 == b"\x00":
                        out.append((c4, prj2.leb(sec["props"])))
                    elif c4 == b"\x07":
                        out.append((c4, prj2.leb(sec["fsplit"]) + b"".join(prj2.leb(h) for h in sec["floor"])))
                    elif c4 == b"\x09":
                        seen.add("fs")
                        out.append((c4, prj2.leb(len(sec["fsplits"])) + b"".join(prj2.leb(h) for sp in sec["fsplits"] for h in sp)))
                    elif c4 == prj2.cid(prj2.TEX_LEVEL2):
                        continue
                    else:
                        out.append((c4, p4))
                if "fs" not in seen and sec["fsplits"]:
                    out.append((b"\x09", prj2.leb(len(sec["fsplits"])) + b"".join(prj2.leb(h) for sp in sec["fsplits"] for h in sp)))
                for face, (coords, mode, tex) in sec["faces"].items():
                    us, vs = [q[0] for q in coords], [q[1] for q in coords]
                    body = prj2.leb(face) + prj2.f32(*[v for q in coords for v in q])
                    body += prj2.f32(min(us), min(vs), max(us), max(vs)) + prj2.leb(mode) + prj2.leb(tex)
                    out.append((prj2.cid(prj2.TEX_LEVEL2), body))
                secs[s] = (c3, p3[:4] + pack(out))
            items[j] = (c2, pack(secs))
        rooms[k] = (c, head + pack(items))
    return pack(rooms), done


def map_objects(rooms_payload, fn):
    """fn(room name, chunk id, payload) -> payload (kept, maybe changed) or None (the object is removed)."""
    from prj2_check import Reader
    rooms, _ = chunks(rooms_payload)
    for k, (c, p) in enumerate(rooms):
        r = Reader(p)
        r.leb(), r.leb()
        head = p[:r.s.tell()]
        items, _ = chunks(p[r.s.tell():])
        name = dict(items).get(b"TeName", b"").decode("utf-8", "replace")
        new = []
        for c2, p2 in items:
            if c2 == b"TeObjects":
                obs = [(oc, fn(name, oc, op)) for oc, op in chunks(p2)[0]]
                p2 = pack([(oc, op) for oc, op in obs if op is not None])
            new.append((c2, p2))
        rooms[k] = (c, head + pack(new))
    return pack(rooms)
