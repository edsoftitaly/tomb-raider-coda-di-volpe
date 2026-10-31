"""The visitable interior of the Basilica of Tindari.

The church on the square is a set of static skins over solid blocks; its interior is a separate,
axis-aligned room built 60 m under the square, reached through the main bronze door with a short fade
(like the Casello in Marinello). Interior frame: x east from the inside of the door, z north from the
axis (metres); see decor/santuario_interno_models.py for the design.
"""
import math

import kit as K
import santuario as S
from decor import santuario_interno_models as IM

IX0 = 207            # world sector x of the inner face of the door (x = 0)
IZC = 213.5          # world sector z of the axis (z = 0)
DEPTH = 60.0         # metres under the square
SECTOR_M = 2.0


def to_world(x, z):
    return IX0 + x / SECTOR_M, IZC + z / SECTOR_M


def plan():
    """13 rows (north -> south), 33 columns (west -> east): nave and aisles, south chapel, raised presbytery."""
    ncol = int(IM.L / SECTOR_M)
    rows = []
    for r in range(11):
        rows.append("".join("1" if (c * SECTOR_M + 1) >= IM.PRESB else "." for c in range(ncol)))
    for r in range(2):
        rows.append("".join("." if IM.CHAPEL[0] <= c * SECTOR_M + 1 <= IM.CHAPEL[1] else "#" for c in range(ncol)))
    return rows


def ceiling_m(x, z):
    if IM.CROSS[0] <= x <= IM.CROSS[1] and abs(z) < IM.CROSS_HZ:
        return IM.DOME_TOP + 1.0
    if abs(z) < IM.NAVE:
        return IM.VAULT_TOP
    return IM.AISLE_H


def build(ctx):
    k, lua = ctx.kit, ctx.lua
    F = ctx.world.santuario["F"]
    fl = (F - int(DEPTH * 512)) // 256 * 256
    rows = plan()
    z0 = int(IZC - IM.HW / SECTOR_M) - 2          # two chapel rows south of the aisle
    it = k.interior("BASILICA", rows, IX0, z0, fl, int((IM.DOME_TOP + 1.0) * 512), "castello_pav", "soffitto",
                    "intonaco_interno", ambient=(0.55, 0.5, 0.42), tags=("interno", "basilica"))
    room = it.room
    for lx in range(1, room.nx - 1):
        for lz in range(1, room.nz - 1):
            s = room.sectors[lx][lz]
            if s.wall:
                continue
            wx, wz = room.x + lx + 0.5, room.z + lz + 0.5
            x, z = (wx - IX0) * SECTOR_M, (wz - IZC) * SECTOR_M
            s.ceil = [int(ceiling_m(x, z) * 512)] * 4
    # statics: skins (rotation 0: the interior frame is the world frame), then furniture with collision
    for name, (x, z) in IM.ANCHORS.items():
        k.prop(name, *to_world(x, z), rot=0.0, h=fl, room=room)
    for name, spots in IM.SPOTS.items():
        for x, z, rot in spots:
            h = fl + int(IM.floor_y(x) * 512)
            if name == "INTERNO_LAMPADARIO":
                h = fl + int(10.5 * 512)
            k.prop(name, *to_world(x, z), rot=rot, h=h, room=room)
    # light: warm ambient plus chandeliers, the dome and the apse
    lights = [(10, 0, 9.5), (20, 0, 9.5), (30, 0, 9.5), (58, 0, 9.5), (46, 0, 16.0), (64, 0, 5.0),
              (20, 8, 6.0), (20, -8, 6.0), (46, -13, 6.0), (2, 0, 4.0)]
    for x, z, y in lights:
        wx, wz = to_world(x, z)
        pos = ((wx - room.x) * 1024, y * 512 + (fl - room.y), (wz - room.z) * 1024)
        ctx.level.add_light(room, 0, pos, color=(1.0, 0.86, 0.62), intensity=0.9, inner=3.0, outer=9.0)
    # the door: out on the square -> in, and back
    out_u = -3.0
    ox, oz = S.to_world(out_u, 0.0)
    dx, dz = S.to_world(-0.7, 0.0)
    ix, iz = to_world(2.0, 0.0)
    ex, ez = to_world(0.6, 0.0)
    out_room = k.room_at(ox, oz)
    yaw_in = 90.0
    yaw_out = (270.0 + S.AXIS_DEG) % 360
    inside = k.lua_pos(ix - 0.5, iz - 0.5, fl)
    outside = k.lua_pos(ox - 0.5, oz - 0.5, F)
    lua.zone("entra_basilica", k.lua_pos(dx - 0.5, dz - 0.5, F), r=650, dy=1200, once=False,
             fn='CDV.Teleport(%d, %d, %d, "BASILICA", %d)' % (inside + (int(yaw_in),)))
    lua.zone("esci_basilica", k.lua_pos(ex - 0.5, ez - 0.5, fl), r=600, dy=1200, once=False,
             fn='CDV.Teleport(%d, %d, %d, "%s", %d)' % (outside + (out_room.name, int(yaw_out))))
    lua.zone("navata", k.lua_pos(*to_world(8.0, 0.0), fl), r=2500, dy=2000,
             text="La basilica della Madonna Nera. Le colonne di marmo rosa, i mosaici dei Misteri, la volta dipinta.", secs=7)
    lua.zone("cupola", k.lua_pos(*to_world(IM.DOME_C[0], 0.0), fl), r=2600, dy=2000, once=False, secs=8,
             text="Sotto la cupola, tra i santi delle vetrate, tre finestre diverse: una luna, una stella, un sole. In quest'ordine.")
    lua.zone("icona", k.lua_pos(*to_world(60.0, 0.0), fl + 256), r=2200, dy=2000, secs=8,
             text="\"Nigra sum sed formosa.\" La Madonna Nera di Tindari, arrivata dal mare secondo la leggenda.")
    k.place(K.SMALLMEDI, *[int(v) for v in to_world(47.0, -13.5)], room=room)
    k.place(K.FLARE_ITEM, *[int(v) for v in to_world(3.0, 9.0)], room=room)
    ctx.notes += [
        "   La basilica si visita: dal portale bronzeo si entra (dissolvenza). Dentro, sotto la cupola, tre vetrate",
        "   ripetono l'ordine dell'enigma E9: luna, stella, sole. Nella cappella dorata del transetto sud un medikit.",
    ]
    return it
