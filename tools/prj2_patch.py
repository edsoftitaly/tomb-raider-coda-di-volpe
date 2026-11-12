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
        if dict(items).get(b"TeName", b"").split(b"\x00")[0].decode("utf-8", "replace").strip("\x00") .find(name) < 0:
            continue
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
                fn(idx % nx, idx // nx, faces)
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
