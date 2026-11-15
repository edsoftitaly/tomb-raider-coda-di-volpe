"""Set or clear "exclude from pathfinding" (TeNoPath) on named rooms. Enemies only walk where rooms have boxes: a
room excluded here is a wall to them, so they stop at its edge and never follow Lara into it.
usage: prj2_nopath.py <in.prj2> <out.prj2> on|off ROOM [ROOM ...]"""
import sys

import prj2_patch as P
from prj2_check import Reader

src, out, mode = sys.argv[1:4]
names = sys.argv[4:]
val = b"\x01" if mode == "on" else b"\x00"
head, top = P.load(src)
rooms, _ = P.chunks(dict(top)[b"TeRooms"])
done = []
for k, (c, p) in enumerate(rooms):
    r = Reader(p)
    r.leb(), r.leb()
    h = p[:r.s.tell()]
    items, _ = P.chunks(p[r.s.tell():])
    name = dict(items)[b"TeName"].decode()
    if name in names:
        rooms[k] = (c, h + P.pack([(a, val if a == b"TeNoPath" else b) for a, b in items]))
        done.append(name)
assert sorted(done) == sorted(names), done
P.save(out, head, [(c, P.pack(rooms) if c == b"TeRooms" else p) for c, p in top])
print(mode, done)
