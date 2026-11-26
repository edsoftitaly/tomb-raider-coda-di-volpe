"""26 Nov: tiled roofs on the four houses of the fishery of Marinello (they were open boxes: 'boxy', the reviews said).
Static 318 FALDA_TETTO of CdV_Decorazioni (a pitch of tiles on beams, 4 x 4.4 m, not solid, made for these walls on
14 Nov and never placed): a gable of two pitches per house, scaled to the depth of the house, resting on the highest
wall. Seen from inside, the underside (the static is double sided).
usage: nov26_roofs.py <in.prj2> <out.prj2>"""
import sys

import nov26_lib as L
import prj2_patch as P

HALF_Z, WIDTH = 1126.4, 2048.0
# room, centre x, centre z (room-local units), y of the eaves, outer depth along z, modules along x
HOUSES = [("T_02_01", 5120.0, 11264.0, 3072.0, 6144.0, 2),      # the house of the rais
          ("T_02_01", 6656.0, 20992.0, 5120.0, 7168.0, 3),      # the net store
          ("T_02_01", 9728.0, 29184.0, 3072.0, 5120.0, 2),      # the keeper's house
          ("T_00_02", 18944.0, 2560.0, 3072.0, 5120.0, 2)]      # the hut of the salt works
src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms = dict(top)[b"TeRooms"]
tpl = L.template(rooms, "sta")
oid = L.max_oid(rooms) + 1
n = 0
for room, cx, cz, y, depth, mods in HOUSES:
    sc = (depth / 4) / HALF_Z
    w = WIDTH * sc
    for k in range(mods):
        x = cx + (k - (mods - 1) / 2.0) * w
        for dz, ry in ((depth / 4, 0.0), (-depth / 4, 180.0)):
            rooms = P.add_objects(rooms, room, [L.static_chunk(tpl, oid, 318, (x, y, cz + dz), ry=ry, scale=sc)])
            oid += 1
            n += 1
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
print("roof pitches:", n)
