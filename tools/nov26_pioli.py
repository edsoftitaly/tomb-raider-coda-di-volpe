"""26 Nov: Tindari, three small wall switches piolo_1..3 on the south wall of the dig compound, east of the door
(T_02_01 sectors 24..26, 21; the wall is row 22).   usage: nov26_pioli.py <in.prj2> <out.prj2>"""
import sys

import nov26_lib as L
import prj2_patch as P

src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms = dict(top)[b"TeRooms"]
assert b"piolo_1" not in rooms
tpl = L.template(rooms, "mov")
oid = L.max_oid(rooms) + 1
for i in range(3):
    rooms = P.add_objects(rooms, "T_02_01", [L.mov_chunk(tpl, oid + i, 801, ((24 + i) * 1024 + 512.0, 256.0, 21 * 1024 + 512.0), ry=0.0, name="piolo_%d" % (i + 1))])
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
print("pegs: 3")
