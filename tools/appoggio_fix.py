"""Statics put back on what they stand on (found by appoggio.py, 16 Nov).

  RAISE: (room, static id, x, z) -> new height, for things sunk in a block or hovering over a roof
  CLEAR: (room, static id, x, z): things standing half inside a block are moved out of it by the shortest way that
         leaves the four corners of their footprint on their own floor

usage: appoggio_fix.py <level key> <in.prj2> <out.prj2> <wad dir>"""
import math
import struct
import sys

import appoggio
import prj2_patch as P
from prj2_check import Reader

RAISE = {
    "Sommersa": [("D_ACQUA", 317, 7680, 3584, 512.0)],                 # an amphora inside a two-click block
    "Oliveri": [("T_01_00", 232, 1536, 15360, 3328.0)],                # a TV aerial 3 m above its roof
    "Marinello": [("T_00_00", 100, 12297, 27669, 970.0), ("T_00_00", 103, 11812, 27800, 960.0),
                  ("T_00_00", 105, 11545, 30205, 768.0),               # three plants sunk in the slope
                  ("W_00_01", 303, 9728, 17818, 704.0), ("W_00_01_PIENO", 303, 9728, 17818, 704.0)],   # nets under the lake bed
}
CLEAR = {
    "Oliveri": [("T_00_00", 137, 30208, 17920), ("T_02_00", 143, 8704, 10752), ("T_02_00", 143, 8704, 12800),
                ("T_02_00", 143, 8704, 26112)],                        # the van and three cafe tables half inside house fronts
    "Sommersa": [("A0_GROTTA", 305, 3584, 3686)],                      # the tent across a ledge
}


def corners(bb, x, z, rot):
    lo, hi, x0, x1, z0, z1, _ = bb
    a = math.radians(rot)
    for cx, cz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        yield x + cx * math.cos(a) + cz * math.sin(a), z - cx * math.sin(a) + cz * math.cos(a)


def free(g, bb, x, y, z, rot):
    for wx, wz in corners(bb, x, z, rot):
        s = g.get((int(wx // 1024), int(wz // 1024)))
        if s is None or s[0] & 1 or not s[1] or abs(max(s[1]) - y) > 100 or abs(min(s[1]) - y) > 100:
            return False
    return True


def main():
    key, src, dst, wad_dir = sys.argv[1:5]
    rooms = appoggio.rooms_of(src)
    stat = appoggio.wads_of(src, wad_dir)
    head, top = P.load(src)
    done = []

    def fn(room, oc, op):
        if oc not in (b"TeStaTn3", b"TeStaTen2"):
            return op
        r = Reader(op)
        r.leb()
        o = r.s.tell()
        x, y, z, rot = struct.unpack_from("<4f", op, o)
        sid = struct.unpack_from("<I", op, o + 28 + 1)[0]
        for rn, s, ex, ez, ny in RAISE.get(key, []):
            if rn == room and s == sid and abs(x - ex) < 3 and abs(z - ez) < 3:
                done.append((room, sid, "y %d -> %d" % (y, ny)))
                return op[:o] + struct.pack("<3f", x, ny, z) + op[o + 12:]
        for rn, s, ex, ez in CLEAR.get(key, []):
            if rn == room and s == sid and abs(x - ex) < 3 and abs(z - ez) < 3:
                g, bb = rooms[room][3], stat[sid]
                best = None
                for d in range(64, 1600, 32):
                    for ax, az in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if best is None and free(g, bb, x + ax * d, y, z + az * d, rot):
                            best = (x + ax * d, z + az * d)
                    if best:
                        break
                assert best, (room, sid, x, z)
                done.append((room, sid, "(%d, %d) -> (%d, %d)" % (x, z, best[0], best[1])))
                return op[:o] + struct.pack("<3f", best[0], y, best[1]) + op[o + 12:]
        return op
    rooms_p = P.map_objects(dict(top)[b"TeRooms"], fn)
    want = len(RAISE.get(key, [])) + len(CLEAR.get(key, []))
    for d in done:
        print("  ", *d)
    assert len(done) == want, (len(done), want)
    P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])


if __name__ == "__main__":
    main()
