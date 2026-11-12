"""Missing textures of a .prj2 as Tomb Editor saved it: every wall, floor and ceiling face that the geometry asks
for and that has no texture takes the nearest one of its kind (fill.py), doorway frames included. Works on the
file in place (prj2_patch), nothing is regenerated.

usage: prj2_fill.py <in.prj2> [<out.prj2>] [room name prefix ...]   (without out: only counts)"""
import collections
import sys

import fill
import prj2
import prj2_mesh
import prj2_patch as P
from prj2_check import Reader


def model(path):
    rooms, _ = prj2_mesh.read_rooms(path)
    _, top = P.load(path)
    meta = []
    for c, p in P.chunks(dict(top)[b"TeRooms"])[0]:
        r = Reader(p)
        r.leb(), r.leb()
        d = dict(P.chunks(p[r.s.tell():])[0])
        pors = []
        for oc, op in P.chunks(d.get(b"TeObjects", b"\x00"))[0]:
            if oc == b"TePor2":
                rr = Reader(op)
                rr.leb()
                area = [rr.leb() for _ in range(4)]
                adj = rr.leb()
                pors.append((area, adj, rr.raw(1)[0]))
        meta.append((Reader(d[b"TeI"]).leb(), bool(d.get(b"TeOutside", b"\x00")[0]), pors))
    out, by_index = [], {}
    for rm, (idx, outside, pors) in zip(rooms, meta):
        room = prj2.Room(rm["name"], rm["nx"], rm["nz"], x=int(rm["pos"][0]), y=int(rm["pos"][1]), z=int(rm["pos"][2]))
        room.outside = outside
        for (lx, lz), sec in rm["sectors"].items():
            s = room.sectors[lx][lz]
            s.wall = sec.get("wall", False)
            s.floor = list(sec.get("floor", [0] * 4))
            s.ceil = list(sec.get("ceil", [0] * 4))
            s.fsplits = [list(v) for v in sec.get("fsplits", [])]
            s.csplits = [list(v) for v in sec.get("csplits", [])]
            s.tex = {f: (c, sec.get("ti", {}).get(f, 0), 0) for f, c in sec["tex"].items()}
            s.invisible = set(sec["inv"])
        room.pors = pors
        out.append(room)
        by_index[idx] = room
    for a in out:                                   # doorways: the border sector takes the heights of the room beyond
        for area, adj, direction in a.pors:
            b = by_index.get(adj)
            if direction < 2:                       # a hole in the floor (0) or in the ceiling (1): no face there
                for lx in range(area[0], area[2] + 1):
                    for lz in range(area[1], area[3] + 1):
                        a.sectors[lx][lz].invisible |= set(fill.FLOORS if direction == 0 else fill.CEILS)
                continue
            if b is None:
                continue
            for lx in range(area[0], area[2] + 1):
                for lz in range(area[1], area[3] + 1):
                    bx, bz = a.x + lx - b.x, a.z + lz - b.z
                    if not (0 <= bx < b.nx and 0 <= bz < b.nz) or b.sectors[bx][bz].wall:
                        continue
                    s, o = a.sectors[lx][lz], b.sectors[bx][bz]
                    s.wall = False
                    s.floor = [v + b.y - a.y for v in o.floor]
                    s.ceil = [v + b.y - a.y for v in o.ceil]
                    s.fsplits, s.csplits = [], []
    return out


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    prefixes = sys.argv[3:]
    rooms = [r for r in model(src) if not prefixes or any(r.name.startswith(p) for p in prefixes)]
    before = {(r.name, lx, lz): set(r.sectors[lx][lz].tex) for r in rooms for lx in range(r.nx) for lz in range(r.nz)}

    class L:
        pass
    L.rooms = rooms
    n = fill.fill_missing(L)
    added = collections.defaultdict(dict)
    per = collections.Counter()
    for r in rooms:
        for lx in range(r.nx):
            for lz in range(r.nz):
                s = r.sectors[lx][lz]
                for f in set(s.tex) - before[(r.name, lx, lz)]:
                    added[(r.name, lx, lz)][f] = s.tex[f]
                    per[(r.name, fill._kind(f))] += 1
    print("faces without a texture:", n)
    for k, v in sorted(per.items()):
        print("  ", k, v)
    if not dst or not n:
        return
    head, top = P.load(src)
    names = set(k[0] for k in added)

    def fn(rn, lx, lz, faces):
        for f, (coords, ti, mode) in added.get((rn, lx, lz), {}).items():
            quad = list(coords) + [coords[-1]] * (4 - len(coords))
            faces[f] = (quad, mode, ti)
    rp, done = P.edit_room(dict(top)[b"TeRooms"], lambda rn: rn in names, fn)
    P.save(dst, head, [(c, rp if c == b"TeRooms" else p) for c, p in top])
    print("sectors changed:", done, "->", dst)


if __name__ == "__main__":
    main()
