"""Rebuild textured geometry from a .prj2 file (verification renders, not used by the game).

Reads the file back (same parsing rules as prj2_check), keeps floor and wall faces with their
texture coordinates and exports a JSON mesh for the three.js preview in tools/render/.
Usage: python3 prj2_mesh.py file.prj2 out.json [room_name_prefix ...]
"""
import json
import struct
import sys

from prj2_check import Reader

DIRS = {0: ((0, 1), (3, 2), (0, 1)), 1: ((2, 3), (1, 0), (0, -1)),
        3: ((1, 2), (0, 3), (1, 0)), 2: ((3, 0), (2, 1), (-1, 0))}   # face id -> owner/other corners
CORNER_XZ = [(0, 1), (1, 1), (1, 0), (0, 0)]  # XnZp, XpZp, XpZn, XnZn offsets


def read_rooms(path):
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
                    r.leb()
                    [r.leb() for _ in range(4)]
                elif c4 in (b"\x09", b"\x0a"):
                    for _ in range(4 * r.leb()):
                        r.leb()
                elif c4 == b"\x12":
                    face = r.leb()
                    tc = r.f(8)
                    r.f(4); r.leb(); r.leb()
                    sec["tex"][face] = [(tc[i], tc[i + 1]) for i in range(0, 8, 2)]
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
            if c3 == b"TeMovTen2":
                pos = r.f(3); rot = r.f(3); r.leb(); t = r.u32(); r.i16(); r.raw(3); r.f(3); r.ustr()
                objects.append({"room": rm, "type": t, "pos": pos, "rot": rot[0]})
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
    return rooms, objects


def build_mesh(rooms, prefixes):
    pos, uv = [], []

    def tri(p, t):
        for a, b in zip(p, t):
            pos.extend(a)
            uv.extend(b)

    for rm in rooms:
        if prefixes and not any(rm["name"].startswith(p) for p in prefixes):
            continue
        rx, ry, rz = rm["pos"]
        for (x, z), s in rm["sectors"].items():
            f = s["floor"]
            P = [((rx + x + dx) * 2.0, (ry + f[k]) / 512.0, (rz + z + dz) * 2.0) for k, (dx, dz) in enumerate(CORNER_XZ)]
            if 25 in s["tex"]:
                t = s["tex"][25]
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
            for face, (oi, pi, (dx, dz)) in DIRS.items():
                if face not in s["tex"]:
                    continue
                o = rm["sectors"].get((x + dx, z + dz))
                if o is None:
                    continue
                g = o["floor"]
                ox, oz = CORNER_XZ[oi[0]], CORNER_XZ[oi[1]]
                ya = sorted([f[oi[0]], g[pi[0]]])
                yb = sorted([f[oi[1]], g[pi[1]]])
                A = lambda c, h: ((rx + x + c[0]) * 2.0, (ry + h) / 512.0, (rz + z + c[1]) * 2.0)  # noqa: E731
                tl, tr, br, bl = A(ox, ya[1]), A(oz, yb[1]), A(oz, yb[0]), A(ox, ya[0])
                t = s["tex"][face]
                tri([tl, tr, br], [t[0], t[1], t[2]])
                tri([tl, br, bl], [t[0], t[2], t[3]])
    return pos, uv


if __name__ == "__main__":
    rooms, objects = read_rooms(sys.argv[1])
    pos, uv = build_mesh(rooms, sys.argv[3:])
    lara = None
    for ob in objects:
        rx, ry, rz = ob["room"]["pos"]
        p = ob["pos"]
        lara = [(rx * 1024 + p[0]) / 512.0, (ry + p[1]) / 512.0, (rz * 1024 + p[2]) / 512.0, ob["rot"]]
    json.dump({"pos": pos, "uv": uv, "lara": lara}, open(sys.argv[2], "w"))
    print("triangles", len(pos) // 9, "lara", lara)
