"""The inside of the sanctuary of Tindari, as one room to graft into the Tindari.prj2 on Ed's disk
(tools/tindari_santuario.py). Not a level of its own.

The room lies right under the church of the map (facade centre at world sector 130.5, 52.5), 60 m below the
square: nave and aisles, crossing under the dome, raised presbytery with the high altar and, behind it, the
icon of the Madonna Nera (decor/santuario_interno_models.py, from Ed's photos of 29/10). In the plot: the men of
Turi are ransacking it, and the Astro di Castore is behind the high altar.
"""
import kit as K
import santuario_interno as SI
from decor import santuario_interno_models as IM

SQUARE = 24576                 # the height of the plateau in Tindari (48 m)
SI.IX0, SI.IZC = 132, 52.5
FLOOR = SQUARE - int(SI.DEPTH * 512)


def build_standalone(ctx):
    k, L = ctx.kit, ctx.level
    rows = SI.plan()
    z0 = int(SI.IZC - IM.HW / SI.SECTOR_M) - 2
    it = k.interior("BASILICA", rows, SI.IX0, z0, FLOOR, int((IM.DOME_TOP + 1.0) * 512), "castello_pav", "soffitto",
                    "intonaco_interno", ambient=(0.5, 0.46, 0.4), tags=("interno", "basilica"))
    room = it.room
    for lx in range(1, room.nx - 1):
        for lz in range(1, room.nz - 1):
            s = room.sectors[lx][lz]
            if s.wall:
                continue
            x, z = (room.x + lx + 0.5 - SI.IX0) * SI.SECTOR_M, (room.z + lz + 0.5 - SI.IZC) * SI.SECTOR_M
            s.ceil = [int(SI.ceiling_m(x, z) * 512)] * 4
    for name, (x, z) in IM.ANCHORS.items():
        k.prop(name, *SI.to_world(x, z), rot=0.0, h=FLOOR, room=room)
    for name, spots in IM.SPOTS.items():
        for x, z, rot in spots:
            h = FLOOR + int(IM.floor_y(x) * 512)
            if name == "INTERNO_LAMPADARIO":
                h = FLOOR + int(10.5 * 512)
            if name == "INTERNO_BANCO" and (x, z) in OVERTURNED:
                rot = OVERTURNED[(x, z)]
            k.prop(name, *SI.to_world(x, z), rot=rot, h=h, room=room)
    for x, z, y in ((10, 0, 9.5), (20, 0, 9.5), (30, 0, 9.5), (58, 0, 9.5), (46, 0, 16.0), (64, 0, 5.0), (20, 8, 6.0),
                    (20, -8, 6.0), (46, -13, 6.0), (2, 0, 4.0)):
        wx, wz = SI.to_world(x, z)
        L.add_light(room, 0, ((wx - room.x) * 1024, y * 512.0, (wz - room.z) * 1024), color=(1.0, 0.86, 0.62),
                    intensity=0.9, inner=3.0, outer=9.0)

    def cell(x, z):
        wx, wz = SI.to_world(x, z)
        return int(wx), int(wz)
    # the men of Turi in the nave and at the altar, the Astro di Castore behind the high altar
    k.place(K.BADDY1, *cell(24.0, 3.0), room=room, rot=270.0, name="b1")
    k.place(K.BADDY1, *cell(44.0, -4.0), room=room, rot=270.0, name="b2")
    k.place(K.BADDY2, *cell(57.0, 1.0), room=room, rot=270.0, name="b3")
    k.place(K.PUZZLE_ITEM[7], *cell(64.6, 0.0), room=room, name="astro_castore")
    k.place(K.SMALLMEDI, *cell(47.0, -13.5), room=room)
    k.place(K.SHOTGUN_AMMO1, *cell(3.0, 9.0), room=room)
    k.place(K.BIGMEDI, *cell(63.0, 9.0), room=room)
    room.no_path = False
    ctx.inside = k.lua_pos(*[v - 0.5 for v in SI.to_world(2.0, 0.0)], FLOOR)
    ctx.exit_zone = k.lua_pos(*[v - 0.5 for v in SI.to_world(0.6, 0.0)], FLOOR)
    ctx.points = {"navata": k.lua_pos(*[v - 0.5 for v in SI.to_world(8.0, 0.0)], FLOOR),
                  "icona": k.lua_pos(*[v - 0.5 for v in SI.to_world(60.0, 0.0)], FLOOR + 256),
                  "segreto": k.lua_pos(*[v - 0.5 for v in SI.to_world(63.0, 9.0)], FLOOR + 256)}
    print("BASILICA", room.nx, room.nz, (room.x, room.y, room.z), "inside", ctx.inside, "exit", ctx.exit_zone, ctx.points)


# a few pews thrown about by the tombaroli (position -> rotation)
OVERTURNED = {}
