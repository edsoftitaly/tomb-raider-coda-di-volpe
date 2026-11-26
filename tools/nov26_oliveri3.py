"""26 Nov, Oliveri after Ed's test: the 61 barriers on the edge of the sector mask are taken away. What stays is the
line of the Carabinieri before the police cars (8 barriers, x 51.5) and two new lines across the cross street of the
town hall, north and south of the main street (x 13-20, z 25.5 and z 16.5: one sector inside each mouth).   usage: nov26_oliveri3.py <in> <out>"""
import json
import os
import struct
import sys

import nov26_lib as L
import prj2_mesh as M
import prj2_patch as P

here = os.path.dirname(os.path.abspath(__file__))
OLD = {(round(b[0]), round(b[2])) for b in json.load(open(os.path.join(here, "nov26_oliveri_mask.json")))["bars"]}
src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms_p = dict(top)[b"TeRooms"]
rooms, _ = M.read_rooms(src)
pos_of = {r["name"]: r["pos"] for r in rooms}
gone = [0]


def drop(room, cid, p):
    if cid == b"TeStaTn3":
        _, o = L._leb_at(p)
        x, y, z = struct.unpack("<3f", p[o:o + 12])
        _, o2 = L._leb_at(p[o + 28:])
        t = struct.unpack("<I", p[o + 28 + o2:o + 32 + o2])[0]
        px, py, pz = pos_of[room]
        if t == 333 and (round(x + px * 1024), round(z + pz * 1024)) in OLD:
            gone[0] += 1
            return None
    return p


rooms_p = P.map_objects(rooms_p, drop)
assert gone[0] == 61, gone
oid = L.max_oid(rooms_p) + 1
st = L.template(rooms_p, "sta")
n = 0
for wz in (25.5 * 1024, 16.5 * 1024):
    for sx in range(13, 21):
        wx, wy = sx * 1024 + 512.0, 1280.0
        hit = L.room_of(rooms, sx, int(wz // 1024), y=wy)
        assert hit, (sx, wz)
        r = hit[0]
        rooms_p = P.add_objects(rooms_p, r["name"], [L.static_chunk(st, oid, 333, (wx - r["pos"][0] * 1024, wy - r["pos"][1], wz - r["pos"][2] * 1024), ry=0.0)])
        oid += 1
        n += 1
P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])
print("barriers removed:", gone[0], " new:", n)
