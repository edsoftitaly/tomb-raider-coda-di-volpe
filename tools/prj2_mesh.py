"""Rebuild textured geometry from a .prj2 file (verification renders, not used by the game).

Reads the file back (same parsing rules as prj2_check), keeps floor and wall faces with their
texture coordinates and exports a JSON mesh for the three.js preview in tools/render/.
Usage: python3 prj2_mesh.py file.prj2 out.json [room_name_prefix ...]
"""
import json
import os
import struct
import sys

from prj2_check import Reader

DIRS = {0: ((1, 0), (2, 3), (0, 1)), 1: ((3, 2), (0, 1), (0, -1)),
        3: ((2, 1), (3, 0), (1, 0)), 2: ((0, 3), (1, 2), (-1, 0))}   # face id -> owner/other corners
# Wall face id -> (QA face id of its direction, segment index).
FACE_SEG = {}
for _qa, _o in ((0, 0), (1, 1), (2, 2), (3, 3)):
    FACE_SEG[_qa] = (_qa, 0)
    FACE_SEG[5 + _o] = (_qa, 1)
    for _k in range(2, 9):
        FACE_SEG[29 + (_k - 2) * 10 + _o] = (_qa, _k)
CORNER_XZ = [(0, 1), (1, 1), (1, 0), (0, 0)]  # XnZp, XpZp, XpZn, XnZn offsets


def read_rooms(path):
    statics = []
    r = Reader(open(path, "rb").read())
    r.raw(8)
    rooms, objects = [], []

    def room_chunk():
        rm = {"sectors": {}}
        rm["nx"], rm["nz"] = r.leb(), r.leb()

        def sectors(c3, s3):
            pos = r.i32()
            sec = {"tex": {}, "inv": set(), "wall": False}

            def sc(c4, s4):
                if c4 == b"\x00":
                    sec["wall"] = bool(r.leb() & 1)
                elif c4 == b"\x07":
                    sec["split"] = bool(r.leb() & 1)
                    sec["floor"] = [r.leb() for _ in range(4)]
                elif c4 == b"\x08":
                    sec["csplit"] = bool(r.leb() & 1)
                    sec["ceil"] = [r.leb() for _ in range(4)]
                elif c4 == b"\x09":
                    n = r.leb()
                    sec["fsplits"] = [[r.leb() for _ in range(4)] for _ in range(n)]
                elif c4 == b"\x0a":
                    n = r.leb()
                    sec["csplits"] = [[r.leb() for _ in range(4)] for _ in range(n)]
                elif c4 == b"\x12":
                    face = r.leb()
                    tc = r.f(8)
                    r.f(4); r.leb(); ti = r.leb()
                    sec["tex"][face] = [(tc[i], tc[i + 1]) for i in range(0, 8, 2)]
                    sec.setdefault("ti", {})[face] = ti
                elif c4 == b"\x11":
                    sec["inv"].add(r.leb())
                else:
                    return False
                return True
            r.chunks(sc, "sector")
            rm["sectors"][(pos % rm["nx"], pos // rm["nx"])] = sec
            return True

        def objs(c3, s3):
            r.leb()
            if c3 in (b"TeMovTen2", b"TeMovTn3"):
                pos = r.f(3); rot = r.f(3); r.leb(); t = r.u32()
                objects.append({"room": rm, "type": t, "pos": pos, "rot": rot[0]})
                r.raw(s3 - (r.s.tell() - start[0]))
            elif c3 in (b"TeStaTen2", b"TeStaTn3"):
                pos = r.f(3); rot = r.f(4); r.leb(); t = r.u32()
                statics.append({"room": rm, "type": t, "pos": pos, "rot": rot[0], "scale": rot[3]})
                r.raw(s3 - (r.s.tell() - start[0]))
            else:
                r.raw(s3 - (r.s.tell() - start[0]))
            return True

        start = [0]

        def props(c2, s2):
            start[0] = r.s.tell()
            if c2 == b"TeName":
                rm["name"] = r.raw(s2).decode()
            elif c2 == b"TePos2":
                rm["pos"] = r.f(3)
            elif c2 == b"TeSecs":
                r.chunks(sectors, "secs")
            elif c2 == b"TeObjects":
                def o(c3, s3):
                    start[0] = r.s.tell()
                    return objs(c3, s3)
                r.chunks(o, "objs")
            else:
                r.raw(s2)
            return True
        r.chunks(props, "room")
        rooms.append(rm)
        return True

    def top(cid, size):
        if cid == b"TeRooms":
            r.chunks(lambda c, s: room_chunk(), "rooms")
        else:
            r.raw(size)
        return True
    r.chunks(top, "file")
    read_rooms.statics = statics
    read_rooms.objects = objects
    return rooms, objects


def build_mesh(rooms, prefixes):
    pos, uv, tix = [], [], []
    cur = [0]

    def tri(p, t):
        for a, b in zip(p, t):
            pos.extend(a)
            uv.extend(b)
        tix.append(cur[0])

    for rm in rooms:
        if prefixes and not any(rm["name"].startswith(p) for p in prefixes):
            continue
        rx, ry, rz = rm["pos"]
        for (x, z), s in rm["sectors"].items():
            f = s["floor"]
            P = [((rx + x + dx) * 2.0, (ry + f[k]) / 512.0, (rz + z + dz) * 2.0) for k, (dx, dz) in enumerate(CORNER_XZ)]
            # Floor portal to a water room (sea level, units 0): not drawn by the engine.
            if rm["name"].startswith("T_") and all(ry + h == 0 for h in f):
                s = dict(s, tex={k: v for k, v in s["tex"].items() if k not in (25, 26)})
            if 25 in s["tex"]:
                t = s["tex"][25]
                cur[0] = s.get("ti", {}).get(25, 0)
                quad = f[1] - f[2] == f[0] - f[3] and f[1] - f[0] == f[2] - f[3]
                if quad:
                    tri([P[0], P[1], P[2]], [t[0], t[1], t[2]])
                    tri([P[0], P[2], P[3]], [t[0], t[2], t[3]])
                elif s["split"]:
                    tri([P[1], P[2], P[3]], t[:3])
                    t2 = s["tex"].get(26, t)
                    tri([P[3], P[0], P[1]], t2[:3])
                else:
                    tri([P[0], P[1], P[2]], t[:3])
                    t2 = s["tex"].get(26, t)
                    tri([P[2], P[3], P[0]], t2[:3])
            for face, d in FACE_SEG.items():
                if face not in s["tex"]:
                    continue
                qa_face, seg = d
                oi, pi, (dx, dz) = DIRS[qa_face]
                o = rm["sectors"].get((x + dx, z + dz))
                if o is None:
                    continue
                g = o["floor"]
                nb = (g[pi[0]], g[pi[1]])
                tops = [(f[oi[0]], f[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in s.get("fsplits", [])]
                if seg >= len(tops):
                    continue
                top = tops[seg]
                bot = nb
                if seg + 1 < len(tops) and tops[seg + 1][0] >= nb[0] and tops[seg + 1][1] >= nb[1]:
                    bot = tops[seg + 1]
                ox, oz = CORNER_XZ[oi[0]], CORNER_XZ[oi[1]]
                A = lambda c, h: ((rx + x + c[0]) * 2.0, (ry + h) / 512.0, (rz + z + c[1]) * 2.0)  # noqa: E731
                tl, tr, br, bl = A(ox, top[0]), A(oz, top[1]), A(oz, bot[1]), A(ox, bot[0])
                t = s["tex"][face]
                t = [t[1], t[2], t[3], t[0]]          # stored from the bottom left corner (texturing.wall_order)
                cur[0] = s.get("ti", {}).get(face, 0)
                tri([tl, tr, br], [t[0], t[1], t[2]])
                tri([tl, br, bl], [t[0], t[2], t[3]])
            # Ceilings, middle and ceiling-part wall faces (enclosed rooms).
            c = s.get("ceil")
            if c is None:
                continue
            Pc = [((rx + x + dx) * 2.0, (ry + c[k]) / 512.0, (rz + z + dz) * 2.0) for k, (dx, dz) in enumerate(CORNER_XZ)]
            if 27 in s["tex"] and not s["wall"]:
                t = s["tex"][27]
                cur[0] = s.get("ti", {}).get(27, 0)
                quad = c[1] - c[2] == c[0] - c[3] and c[1] - c[0] == c[2] - c[3]
                if quad:
                    tri([Pc[0], Pc[1], Pc[2]], [t[0], t[1], t[2]])
                    tri([Pc[0], Pc[2], Pc[3]], [t[0], t[2], t[3]])
                elif s.get("csplit"):
                    tri([Pc[1], Pc[2], Pc[3]], t[:3])
                    tri([Pc[3], Pc[0], Pc[1]], s["tex"].get(28, t)[:3])
                else:
                    tri([Pc[0], Pc[1], Pc[2]], t[:3])
                    tri([Pc[2], Pc[3], Pc[0]], s["tex"].get(28, t)[:3])
            for qa_face in range(4):
                oi, pi, (dx, dz) = DIRS[qa_face]
                o = rm["sectors"].get((x + dx, z + dz))
                if o is None or o.get("ceil") is None:
                    continue
                nbf = (o["floor"][pi[0]], o["floor"][pi[1]])
                nbc = (o["ceil"][pi[0]], o["ceil"][pi[1]])
                ox, oz = CORNER_XZ[oi[0]], CORNER_XZ[oi[1]]
                A = lambda cc, h: ((rx + x + cc[0]) * 2.0, (ry + h) / 512.0, (rz + z + cc[1]) * 2.0)  # noqa: E731

                def wallq(face, top, bot):
                    if face not in s["tex"]:
                        return
                    t = s["tex"][face]
                    t = [t[1], t[2], t[3], t[0]]
                    cur[0] = s.get("ti", {}).get(face, 0)
                    tl, tr, br, bl = A(ox, top[0]), A(oz, top[1]), A(oz, bot[1]), A(ox, bot[0])
                    tri([tl, tr, br], [t[0], t[1], t[2]])
                    tri([tl, br, bl], [t[0], t[2], t[3]])
                if s["wall"]:
                    lo = (max(f[oi[0]], nbf[0]), max(f[oi[1]], nbf[1]))
                    hi = (min(c[oi[0]], nbc[0]), min(c[oi[1]], nbc[1]))
                    wallq(10 + qa_face, hi, lo)
                bots = [(c[oi[0]], c[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in s.get("csplits", [])]
                for k, bot in enumerate(bots):
                    top = nbc
                    if k + 1 < len(bots) and bots[k + 1][0] <= nbc[0] and bots[k + 1][1] <= nbc[1]:
                        top = bots[k + 1]
                    face = 15 + qa_face if k == 0 else 20 + qa_face if k == 1 else 34 + (k - 2) * 10 + qa_face
                    wallq(face, top, bot)
    return pos, uv, tix


NATLAS = 19


def add_statics(rooms, statics, keep, pos, uv, tix, out_dir):
    """Decoration statics (CdV_Decorazioni) as real meshes, textures 3.. = decor pages."""
    import math
    import numpy as np
    from decor import tex
    tex.build()
    from decor import models
    from decor import santuario_models, santuario_interno_models, casa_models, marinello_models, mito_models  # noqa: F401
    tex.save(out_dir)
    lib = {}
    for sid, name, mesh, coll, note in models.build_all():
        tris = []
        for idx, px, page, blend, dbl in mesh.f:
            ps = [np.array(mesh.v[i], float) for i in idx]
            for a, b, c in [(0, 1, 2)] + ([(0, 2, 3)] if len(ps) == 4 else []):
                tris.append(([ps[a], ps[b], ps[c]], [px[a], px[b], px[c]], page))
        lib[sid] = tris
    # the stair bridges (TEN moveables in CdV_Oggetti) drawn with the decoration's marble and plaster
    from decor import scala
    for mid, mesh in ((1340, scala.landing("tn_marmo", "ca_intonaco", thick=0.2, hw=0.99)),
                      (1342, scala.flight_bridge("tn_marmo", "ca_intonaco"))):
        tris = []
        for idx, px, page, blend, dbl in mesh.f:
            ps = [np.array(mesh.v[i], float) for i in idx]
            for a, b, c in [(0, 1, 2)] + ([(0, 2, 3)] if len(ps) == 4 else []):
                tris.append(([ps[a], ps[b], ps[c]], [px[a], px[b], px[c]], page))
        lib[("mov", mid)] = tris
    statics = list(statics) + [dict(o, type=("mov", o["type"]), scale=1.0) for o in getattr(read_rooms, "objects", [])
                               if o["type"] in (1340, 1342)]
    for st in statics:
        if st["type"] not in lib or (keep and not any(st["room"]["name"].startswith(p) for p in keep)):
            continue
        rx, ry, rz = st["room"]["pos"]
        a = math.radians(st["rot"])
        ca, sa = math.cos(a), math.sin(a)
        ox, oy, oz = rx * 1024 + st["pos"][0], ry + st["pos"][1], rz * 1024 + st["pos"][2]
        sc = st["scale"]
        for ps, px, page in lib[st["type"]]:
            for p, t in zip(ps, px):
                x, y, z = p * sc
                pos.extend([(ox + x * ca + z * sa) / 512.0, (oy + y) / 512.0, (oz - x * sa + z * ca) / 512.0])
                uv.extend([t[0] / 512.0, t[1] / 512.0])
            tix.append(NATLAS + page)


if __name__ == "__main__":
    rooms, objects = read_rooms(sys.argv[1])
    pos, uv, tix = build_mesh(rooms, sys.argv[3:])
    lara = None
    marks = []
    keep = set(sys.argv[3:])
    import kit
    for ob in objects:
        if keep and not any(ob["room"]["name"].startswith(p) for p in keep):
            continue
        rx, ry, rz = ob["room"]["pos"]
        p = ob["pos"]
        w = [(rx * 1024 + p[0]) / 512.0, (ry + p[1]) / 512.0, (rz * 1024 + p[2]) / 512.0]
        t = ob["type"]
        if t == 0:
            lara = w + [ob["rot"]]
            continue
        color = 0xff2020 if t in kit.ENEMIES else 0xffd020 if (950 <= t <= 990 or 500 <= t < 520) else \
            0x20e020 if 800 <= t < 830 else 0xffffff
        marks.append(w + [color])
    sizes = [2048.0, 2048.0, 1024.0] + [2048.0] * (NATLAS - 3) + [2048.0] * 20
    for i, t in enumerate(tix):
        for k in range(3):
            j = (i * 3 + k) * 2
            uv[j] /= sizes[t] if t < len(sizes) else 2048.0
            uv[j + 1] /= sizes[t] if t < len(sizes) else 2048.0
    if os.environ.get("DECOR", "1") == "1" and read_rooms.statics:
        add_statics(rooms, read_rooms.statics, keep, pos, uv, tix, os.path.dirname(sys.argv[2]))
    json.dump({"pos": pos, "uv": uv, "tix": tix, "lara": lara, "objects": marks}, open(sys.argv[2], "w"))
    print("triangles", len(pos) // 9, "lara", lara)
