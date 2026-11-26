"""26 Nov, Tindari: the walls of the dig compound could be mounted where the hill outside comes up to them (and the
key of the terrace taken without the Dig Site Key). A prickly pear (static 100, solid, scale 1.3 = the whole
sector) now grows on each stretch of wall top that can be reached from outside: list in the script, found by reach.py.
usage: nov26_tindari.py <in.prj2> <out.prj2>"""
import json
import sys

import nov26_lib as L
import prj2_mesh as M
import prj2_patch as P

FENCE = [(73, z) for z in range(73, 82)] + [(89, 54), (89, 62)]
src, dst = sys.argv[1:3]
if len(sys.argv) > 3:
    FENCE = [tuple(v) for v in json.load(open(sys.argv[3]))]
head, top = P.load(src)
rooms_p = dict(top)[b"TeRooms"]
rooms, _ = M.read_rooms(src)
tpl = L.template(rooms_p, "sta")
oid = L.max_oid(rooms_p) + 1
n = 0
for i, (X, Z) in enumerate(FENCE):
    cands = []
    for r in rooms:
        hit = L.room_of([r], X, Z)
        if hit:
            cands.append(hit)
    r, lx, lz, f = max(cands, key=lambda c: c[3])
    y = f - r["pos"][1]
    ch = L.static_chunk(tpl, oid, 100, (lx * 1024 + 512.0, float(y), lz * 1024 + 512.0), ry=float((i * 77) % 360), scale=1.3)
    rooms_p = P.add_objects(rooms_p, r["name"], [ch])
    oid += 1
    n += 1
P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])
print("prickly pears on wall tops:", n)
