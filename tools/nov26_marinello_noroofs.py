"""26 Nov, after Ed's test: the 18 roof pitches (static 318) placed blind on the houses of Marinello are taken away.
usage: nov26_marinello_noroofs.py <in.prj2> <out.prj2>"""
import struct
import sys

import nov26_lib as L
import prj2_patch as P

src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms = dict(top)[b"TeRooms"]
gone = [0]


def drop(room, cid, p):
    if cid == b"TeStaTn3":
        _, o = L._leb_at(p)
        _, o2 = L._leb_at(p[o + 28:])
        if struct.unpack("<I", p[o + 28 + o2:o + 32 + o2])[0] == 318:
            gone[0] += 1
            return None
    return p


rooms = P.map_objects(rooms, drop)
assert gone[0] == 18, gone
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
print("roof pitches removed:", gone[0])
