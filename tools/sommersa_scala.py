"""The lost half, the cella (rooms H_CELLA and its flooded twin H_CELLA_ACQUA): the stair up to the gallery was four
steps of four clicks, which no man of Turi's kind can climb (the engine lets him step up one click). It is now a
stair of fifteen steps of one click that doubles back along the south side: up the second row from west to east
(1 to 7 clicks), then back along the wall from east to west (8 to 15), to the same landing under the gallery.
Lara walks it, and so does he.

Every side of every step gets its texture, at the same scale and height as the old stair (v = 1281 - height / 4 on
texture 17, columns 1536..1792), and the faces of the south wall are shortened to what still shows above the steps.

  sommersa_scala.py <in.prj2> <out.prj2>"""
import copy
import sys

import prj2_patch as P
import tindari_pm as TP
from prj2_check import Reader

ROOMS = ("H_CELLA", "H_CELLA_ACQUA")
CLICK = 256
HEIGHT = {(x, 4): 19 - x for x in range(4, 12)}          # 15 .. 8, west to east along the wall
HEIGHT.update({(x, 5): x - 4 for x in range(5, 12)})     # 1 .. 7, west to east in the second row
DIRS = {0: (0, 1), 1: (0, -1), 2: (-1, 0), 3: (1, 0)}     # face id of the top segment -> neighbour
U0, U1, TEX = 1536.0, 1792.0, 17


def v_of(h):
    return 1281.0 - h / 4.0


def seg_face(d, k):
    return d if k == 0 else d + 5 if k == 1 else 29 + (k - 2) * 10 + d


def wall_ids(d):
    """face ids of a wall-type sector on side d (QA, then the ceiling-side segments)"""
    return [d, 15 + d, 20 + d] + [34 + 10 * k + d for k in range(6)]


def main():
    src, dst = sys.argv[1:3]
    head, top = P.load(src)
    rooms = dict(top)[b"TeRooms"]
    total = 0
    for room in ROOMS:
        old = {}
        P.edit_sectors(rooms, room, lambda x, z, s: old.__setitem__((x, z), copy.deepcopy(s)))
        top_face = old[(7, 4)]["faces"][25]

        def height(k):
            if k in HEIGHT:
                return HEIGHT[k] * CLICK
            s = old.get(k)
            if s is None or s["props"] & 1:
                return None                                   # a wall: nothing to show against it
            return max(s["floor"])

        def fn(x, z, s):
            k = (x, z)
            if k in HEIGHT:
                f = HEIGHT[k] * CLICK
                s["floor"] = [f] * 4
                s["fsplits"] = [[f - 1024 * i] * 4 for i in range(1, 16) if f - 1024 * i > 0]
                keep = {fid: v for fid, v in s["faces"].items() if fid in (25, 27)}
                keep[25] = top_face if 25 not in s["faces"] or old[k]["floor"][0] == 0 else s["faces"][25]
                bounds = [f] + [sp[0] for sp in s["fsplits"]] + [0]
                for d, (dx, dz) in DIRS.items():
                    nb = height((x + dx, z + dz))
                    if nb is None or nb >= f:
                        continue
                    for i in range(len(bounds) - 1):
                        hi, lo = bounds[i], max(bounds[i + 1], nb)
                        if hi > lo:
                            keep[seg_face(d, i)] = ([(U0, v_of(lo)), (U0, v_of(hi)), (U1, v_of(hi)), (U1, v_of(lo))], 0, TEX)
                s["faces"] = keep
            elif z == 3 and (x, 4) in HEIGHT and s["props"] & 1:
                # the south wall behind the stair: what shows of it now starts at the new step
                nb = HEIGHT[(x, 4)] * CLICK
                for fid in wall_ids(0):
                    if fid in s["faces"]:
                        pts, mode, tex = s["faces"][fid]
                        vs = [q[1] for q in pts]
                        vbot, vtop = max(vs), min(vs)
                        if vtop < v_of(nb) < vbot:
                            s["faces"][fid] = ([(q[0], v_of(nb) if q[1] == vbot else q[1]) for q in pts], mode, tex)
        rooms, n = P.edit_sectors(rooms, room, fn)
        total += n

    # what stood where the stair now is: the decorations go (two columns, an amphora, rubble: they would be
    # inside the steps), the man moves to the middle of the floor
    moved = []

    def objs(room, oc, op):
        if room in ROOMS and oc in (b"TeMovTn3", b"TeMovTen2", b"TeStaTn3", b"TeStaTen2"):
            import struct
            r = Reader(op); r.leb(); a = r.s.tell()
            x, y, z = struct.unpack_from("<3f", op, a)
            k = (int(x // 1024), int(z // 1024))
            if k in HEIGHT and y < HEIGHT[k] * CLICK:
                static = oc.startswith(b"TeSta")
                moved.append((room, "static" if static else TP.name_of(op), k))
                if static:
                    return None
                return op[:a] + struct.pack("<3f", 10.5 * 1024, y, 6.5 * 1024) + op[a + 12:]
        return op
    rooms = P.map_objects(rooms, objs)
    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
    print("stair of 15 steps: %d sectors changed in %s; moved off it: %s" % (total, " and ".join(ROOMS), moved))


if __name__ == "__main__":
    main()
