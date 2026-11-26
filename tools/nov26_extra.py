"""26 Nov, third pass: two more Stars of the Dioscuri in every level (stella_4, stella_5), and Oliveri's streets closed
with the barriers of the Carabinieri (static 333) on the edge of the playable rectangle (x 12..52, z 3..33 sectors).
usage: nov26_extra.py <level name> <in.prj2> <out.prj2>"""
import json
import os
import sys

import nov26_lib as L
import prj2_mesh as M
import prj2_patch as P

# world sector x, z, world y of the floor
STARS = {
    "Marinello": [(11, 57, 2560), (5, 38, 512)],
    "Sommersa": [(31, 37, -2048), (40, 19, 0)],
    "Oliveri": [(52, 31, 4608), (24, 17, 1280)],
    "Tindari": [(86, 57, 24576), (74, 67, 24576)],
}
name, src, dst = sys.argv[1:4]
head, top = P.load(src)
rooms_p = dict(top)[b"TeRooms"]
rooms, _ = M.read_rooms(src)
found = []


def see(room, cid, p):
    if cid == b"TeMovTn3" and b"stella_" in p and not found:
        found.append((cid, p))
    return p


P.map_objects(rooms_p, see)
tpl = found[0]
oid = L.max_oid(rooms_p) + 1
for i, (X, Z, y) in enumerate(STARS[name]):
    r, lx, lz, f = L.room_of(rooms, X, Z, y=y)
    assert abs(f - y) < 300, (X, Z, y, f)
    pos = (lx * 1024 + 512.0, float(f - r["pos"][1]), lz * 1024 + 512.0)
    rooms_p = P.add_objects(rooms_p, r["name"], [L.mov_chunk(tpl, oid, 515, pos, name="stella_%d" % (4 + i))])
    oid += 1
    print("stella_%d" % (4 + i), r["name"], pos)
if name == "Oliveri":
    st = L.template(rooms_p, "sta")
    fences = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nov26_oliveri_fences.json")))
    n = 0
    for (wx, wy, wz, ry) in fences:
        if abs(wy - 1280) > 10:                 # the streets only: nothing on the roofs
            continue
        hit = L.room_of(rooms, int(wx // 1024), int(wz // 1024), y=wy)
        if not hit:
            continue
        r = hit[0]
        pos = (wx - r["pos"][0] * 1024, wy - r["pos"][1], wz - r["pos"][2] * 1024)
        rooms_p = P.add_objects(rooms_p, r["name"], [L.static_chunk(st, oid, 333, pos, ry=float(ry))])
        oid += 1
        n += 1
    print("barriers:", n)
P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])
