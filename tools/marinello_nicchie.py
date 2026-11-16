"""Marinello, the way out of the cave (G5_USCITA): two more niches, one each side, at the fourth sector from the
gate, so that the boulders set off at the gate can be escaped (the first ones were at the eighth). Each niche is a
copy, sector for sector, of an existing one with the three wall sectors around it.

  marinello_nicchie.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

ROOM = "G5_USCITA"
# target sector <- source sector
COPY = {(1, 4): (1, 8), (0, 4): (0, 8), (1, 3): (1, 7), (1, 5): (1, 9),
        (5, 4): (5, 12), (6, 4): (6, 12), (5, 3): (5, 11), (5, 5): (5, 13)}


def main():
    src, dst = sys.argv[1:3]
    head, top = P.load(src)
    rooms, _ = P.chunks(dict(top)[b"TeRooms"])
    done = 0
    for k, (c, p) in enumerate(rooms):
        r = Reader(p)
        nx, nz = r.leb(), r.leb()
        hd = p[:r.s.tell()]
        items, _ = P.chunks(p[r.s.tell():])
        if dict(items)[b"TeName"].decode() != ROOM:
            continue
        for j, (c2, p2) in enumerate(items):
            if c2 != b"TeSecs":
                continue
            secs, _ = P.chunks(p2)
            by = {}
            for s, (c3, p3) in enumerate(secs):
                i = struct.unpack_from("<i", p3, 0)[0]
                by[(i % nx, i // nx)] = s
            for tgt, srcs in COPY.items():
                c3, p3 = secs[by[tgt]]
                secs[by[tgt]] = (c3, p3[:4] + secs[by[srcs]][1][4:])
                done += 1
            items[j] = (c2, P.pack(secs))
        rooms[k] = (c, hd + P.pack(items))
    assert done == len(COPY)
    P.save(dst, head, [(c, P.pack(rooms) if c == b"TeRooms" else p) for c, p in top])
    print("two niches at the fourth sector of", ROOM)


if __name__ == "__main__":
    main()
