"""The lost half, cistern (S2_CISTERNA): the shotgun shells lay inside the brazier of the corner (same sector, same
height) and could not be picked up. Moved two sectors along the ledge, onto free floor.

  sommersa_munizioni.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader


def main():
    src, dst = sys.argv[1:3]
    head, top = P.load(src)
    done = []

    def fn(room, oc, op):
        if room == "S2_CISTERNA" and oc in (b"TeMovTen2", b"TeMovTn3") and P.mov_type(op)[1] == 955:
            r = Reader(op); r.leb(); a = r.s.tell()
            x, y, z = struct.unpack_from("<3f", op, a)
            if (x, z) == (2560.0, 1536.0):
                done.append(1)
                return op[:a] + struct.pack("<3f", 4608.0, y, z) + op[a + 12:]
        return op
    top = [(c, P.map_objects(p, fn) if c == b"TeRooms" else p) for c, p in top]
    assert len(done) == 1, done
    P.save(dst, head, top)
    print("shells moved to sector 4, 1 of the cistern")


if __name__ == "__main__":
    main()
