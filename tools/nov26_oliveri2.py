"""26 Nov, Oliveri (Ed: no wandering outside the needed areas, no way past the Carabinieri, no turning off after the gate
and the diary, nothing to reach over the roofs). The playable ground is now a mask of sectors (nov26_oliveri_mask.json,
made with reach.py): the house; the roofs from the hatch to the Star and down to the street; the street to the gate;
the lane and the courtyard; the main street west to the town hall end. Barriers of the Carabinieri (static 333) on
every street edge of the mask; the 32 barriers of the rectangle of this morning are taken away; stella_4 moves to a
roof next to the route.   usage: nov26_oliveri2.py <in.prj2> <out.prj2>"""
import json
import os
import struct
import sys

import nov26_lib as L
import prj2_mesh as M
import prj2_patch as P

here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "nov26_oliveri_mask.json")))
OLD = {(round(x), round(z)) for x, y, z, ry in json.load(open(os.path.join(here, "nov26_oliveri_fences.json"))) if abs(y - 1280) < 10}
src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms_p = dict(top)[b"TeRooms"]
rooms, _ = M.read_rooms(src)
pos_of = {r["name"]: r["pos"] for r in rooms}
gone = [0, 0]
star = []


def drop(room, cid, p):
    if cid == b"TeStaTn3":
        r = P.Reader(p) if hasattr(P, "Reader") else None
        _, o = L._leb_at(p)
        x, y, z = struct.unpack("<3f", p[o:o + 12])
        _, o2 = L._leb_at(p[o + 28:])
        t = struct.unpack("<I", p[o + 28 + o2:o + 32 + o2])[0]
        px, py, pz = pos_of[room]
        if t == 333 and (round(x + px * 1024), round(z + pz * 1024)) in OLD:
            gone[0] += 1
            return None
    if cid == b"TeMovTn3" and b"stella_4" in p:
        gone[1] += 1
        star.append((cid, p))
        return None
    return p


rooms_p = P.map_objects(rooms_p, drop)
assert gone[1] == 1, gone
oid = L.max_oid(rooms_p) + 1
X, Z, y = D["stella_4"]
r, lx, lz, f = L.room_of(rooms, X, Z, y=y)
rooms_p = P.add_objects(rooms_p, r["name"], [L.mov_chunk(star[0], oid, 515, (lx * 1024 + 512.0, float(f - r["pos"][1]), lz * 1024 + 512.0), name="stella_4")])
oid += 1
st = L.template(rooms_p, "sta")
n = 0
for (wx, wy, wz, ry) in D["bars"]:
    hit = L.room_of(rooms, int(wx // 1024), int(wz // 1024), y=wy)
    if not hit:
        continue
    r = hit[0]
    rooms_p = P.add_objects(rooms_p, r["name"], [L.static_chunk(st, oid, 333, (wx - r["pos"][0] * 1024, wy - r["pos"][1], wz - r["pos"][2] * 1024), ry=float(ry))])
    oid += 1
    n += 1
P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])
print("old barriers removed:", gone[0], " new barriers:", n, " stella_4 at", r["name"] if False else (X, Z, y))
