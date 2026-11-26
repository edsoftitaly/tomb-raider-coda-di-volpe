"""26 Nov: the tally board of the net store of Marinello: three small wall switches (801) tacca_1..3 on the south face
of the wall east of the door (T_02_01 sectors 6..8, 16; the wall is row 17), left to right as she faces it.
usage: nov26_tacche.py <in.prj2> <out.prj2>"""
import sys

import nov26_lib as L
import prj2_patch as P

src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms = dict(top)[b"TeRooms"]
assert b"tacca_1" not in rooms
tpl = L.template(rooms, "mov")
oid = L.max_oid(rooms) + 1
for i in range(3):
    rooms = P.add_objects(rooms, "T_02_01", [L.mov_chunk(tpl, oid + i, 801, ((6 + i) * 1024 + 512.0, 512.0, 16 * 1024 + 512.0), ry=0.0, name="tacca_%d" % (i + 1))])
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
print("pegs: 3")
