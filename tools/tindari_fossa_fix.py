"""Tindari, cryptoporticus: the side walls of the widened pit (rows 0 and 4, sectors 6..8) had been given the
textures of the walls of the old pit but not their ceiling subdivisions, so the lower faces had nothing to sit on
and stayed untextured. The whole sector is now copied (floor, ceiling, subdivisions, textures) from its neighbour at
sector 9, and so are the bottom sectors.

  tindari_fossa_fix.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

ROOM = "U_CRIPTOPORTICO"
COPY = {(x, z): (9, z) for x in (6, 7, 8) for z in range(5)}


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
    print(done, "sectors of the pit copied whole from column 9")


if __name__ == "__main__":
    main()
