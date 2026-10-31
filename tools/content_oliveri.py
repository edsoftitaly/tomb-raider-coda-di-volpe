"""Livello 1 - Oliveri, Via Gaspare Amodeo (notte). v6: small zone aligned with the street.

The level is a 164 x 80 m strip of Via Gaspare Amodeo, rotated so that the street runs along +x
(episode.LEVELS["Oliveri"]["frame"]): every facade on the street lies on a sector edge.
References: Google satellite view and Street View (31/10/2026) for the house and the street; nothing
is copied, textures are procedural.

Route: Ed's house, second floor (Lara wakes up) -> stairs down to the first and ground floor (thieves,
the box-room key) -> back up -> the key in the lock beside the box-room door (native KEY_HOLE1) ->
from the step, jump and pull the ceiling trapdoor down (native CEILING_TRAPDOOR1) -> roof terrace ->
down the drainpipe on the street front (climbable wall) -> Via Amodeo (dogs, the thief's look-out) ->
the thief runs to the junction with Via Stesicoro: level end.
"""
import math

import numpy as np

import kit as K
from kit import CLICK

HOUSE_LATLON = (38.1241402, 15.0600308)
W_COLS, H_ROWS = 8, 5            # interior plan: 8 x 5 sectors (16 x 10 m), the street on the south side
H0 = H1 = 1536                   # storeys 3 m
H2 = 1792                        # second floor 3.5 m (4 clicks under the hatch, standing on a 3-click step)

# Plans: rows from north (back) to south (street); columns west to east.
F0_PLAN = ["....#..P",           # stairs up (cols 1-3, rising east); pantry (secret) behind the wall
           ".....#..",
           ".K..##.#",           # kitchen
           "........",
           "..A.#.E."]           # entrance hall; E = the barred street door
F1_PLAN = ["........",           # stairwell from the ground floor at cols 2-3
           ".SSS....",           # stairs up (cols 3 -> 1, rising west)
           ".....#..",
           "##.###.#",
           "...T...."]           # living room on the balcony side
F2_PLAN = ["...#....",           # stairwell at cols 1-2, arrival at col 0
           "...#.7..",           # chimney stack north of the hatch, a floor raised to the ceiling (not a
                                 # wall: TEN finds the roof ledge above it), the wall Lara grabs to climb out
           "...#.3..",           # box room: the hatch over the 3-click step at col 5
           "##.##.##",           # doorways: col 2 (stairs), col 5 (box room, closed by the door)
           ".S.....M"]           # Ed's bedroom (Lara wakes up here)
STAIR0 = [(1, 4), (2, 4), (3, 4)]          # (col, row) rising east, top lands at (4, 4) on F1
STAIR1 = [(3, 1), (2, 1), (1, 1)]          # rising west, top lands at (0, 1) on F2
HATCH = (5, 2)
DOORWAY = (5, 3)
DOOR = (5, 4)                              # door item: the sector in front of the doorway, turned 180
LOCK = (4, 4)                              # keyhole on the wall north of this sector


def house_rect(world):
    """Largest W_COLS x H_ROWS rectangle of the house's footprint, back against the street front."""
    hx, hz = world.sector_of(*HOUSE_LATLON)
    bid = int(world.building_id[int(hx), int(hz)])
    mask = world.building_id == bid
    best = None
    for x0 in range(int(hx) - W_COLS, int(hx) + 1):
        for z0 in range(int(hz) - H_ROWS, int(hz) + 1):
            if x0 < 1 or z0 < 1:
                continue
            m = mask[x0:x0 + W_COLS, z0:z0 + H_ROWS]
            if m.shape == (W_COLS, H_ROWS) and m.all() and not mask[x0:x0 + W_COLS, z0 - 1].any():
                if best is None or z0 < best[1]:
                    best = (x0, z0)
    assert best is not None, "house footprint smaller than the plan"
    return bid, best


def prepare(world):
    bid, (x0, z0) = house_rect(world)
    street = int(np.median(world.floor[x0:x0 + W_COLS, z0 - 1].mean(axis=1)) // 64 * 64)
    roof = street + H0 + H1 + H2
    mask = world.building_id == bid
    world.floor[mask] = roof
    # Town ground: pavements (brick pavers) instead of dirt wherever a street or a building is near.
    from scipy import ndimage
    town = ndimage.binary_dilation((world.building_id >= 0) | (world.mat == "asfalto"), iterations=3)
    soft = (world.building_id < 0) & (world.mat != "asfalto") & town & ~world.water
    world.mat[soft] = "marciapiede"
    world.buildings[bid]["roof_m"] = roof / 512.0
    world.casa = dict(bid=bid, x0=x0, z0=z0, G=street, ROOF=roof)
    street_fronts(world, street)


# Street fronts (Street View, 31/10/2026). x ranges in sectors of the level frame, inclusive; side = the
# direction the facade faces; pattern = facade columns from west to east; h = height in metres.
STREET_FRONTS = [
    dict(name="casa", side="-z", x=(25, 32), h=9.5, lato="fac_lato_crema",
         pattern=["fac_casa_tubo", "fac_casa_finestra", "fac_casa_porta", "fac_casa_finestra", "fac_casa_finestra",
                  "fac_casa_piena", "fac_casa_finestra", "fac_casa_finestra"],
         balconies=[("BALCONE_VERDE", 3.2, range(1, 8))]),
    dict(name="rosa", side="-z", x=(33, 36), h=9.5, lato="fac_lato_rosa",
         pattern=["fac_rosa_porta", "fac_rosa_finestra", "fac_rosa_finestra", "fac_rosa_finestra"],
         balconies=[("BALCONE_NERO", 3.2, range(1, 3)), ("BALCONE_NERO", 6.2, range(1, 3))]),
    dict(name="arancio", side="-z", x=(37, 45), h=9.5, lato="fac_lato_beige",
         pattern=["fac_arancio_porta", "fac_arancio_finestra", "fac_arancio_finestra", "fac_arancio_finestra",
                  "fac_arancio_porta", "fac_arancio_finestra", "fac_arancio_finestra"],
         balconies=[("BALCONE_ARANCIO", 3.2, (1, 2, 5, 6)), ("BALCONE_ARANCIO", 6.2, (1, 2, 5, 6))]),
    dict(name="bianco", side="-z", x=(10, 19), h=6.9, lato="fac_lato_bianco",
         pattern=["fac_bianco_finestra", "fac_bianco_finestra", "fac_bianco_porta"]),
    dict(name="bianco_s", side="+z", x=(22, 25), h=6.9, lato="fac_lato_bianco",
         pattern=["fac_bianco_finestra", "fac_bianco_porta", "fac_bianco_finestra"]),
    dict(name="ponteggio", side="+z", x=(26, 28), h=9.5, lato="fac_lato_beige",
         pattern=["fac_lato_beige"], scaffold=True),
    dict(name="rosa_s", side="+z", x=(29, 31), h=9.5, lato="fac_lato_rosa",
         pattern=["fac_rosa_finestra", "fac_rosa_porta", "fac_rosa_finestra"],
         balconies=[("BALCONE_NERO", 3.2, (0, 2)), ("BALCONE_NERO", 6.2, (0, 2))]),
    dict(name="pizzeria", side="+z", x=(32, 40), h=6.6, lato="fac_lato_beige",
         pattern=["fac_pizzeria_vetrina", "fac_pizzeria_vetrina", "fac_pizzeria_porta"], awning=(32, 37)),
]


def street_fronts(world, street_h):
    """Assigns the facade columns of the street fronts and the real heights of those buildings."""
    cols = {}
    fronts = []
    for f in STREET_FRONTS:
        dz = -1 if f["side"] == "-z" else 1
        bids, row = set(), {}
        for x in range(f["x"][0], f["x"][1] + 1):
            # the front sector: the building sector next to the open street in direction `side`
            zs = [z for z in range(world.nz - 1) if world.building_id[x, z] >= 0
                  and world.building_id[x, z + dz] < 0 and 0 <= z + dz < world.nz]
            if not zs:
                continue
            z = min(zs, key=lambda z: abs(z - (24 if dz < 0 else 17)))
            row[x] = z
            bids.add(int(world.building_id[x, z]))
        if not row:
            continue
        top = street_h + int(f["h"] * 512) // 64 * 64
        for b in bids:
            mask = world.building_id == b
            world.floor[mask] = max(top, world.floor[mask].max()) if f["name"] == "casa" else top
            world.buildings[b]["base_m"] = street_h / 512.0
            world.buildings[b]["roof_m"] = top / 512.0
            for (x, z) in zip(*np.nonzero(mask)):
                for d, (ddx, ddz) in (("+x", (1, 0)), ("-x", (-1, 0)), ("+z", (0, 1)), ("-z", (0, -1))):
                    nx_, nz_ = x + ddx, z + ddz
                    if 0 <= nx_ < world.nx and 0 <= nz_ < world.nz and world.building_id[nx_, nz_] != b:
                        cols.setdefault((int(x), int(z), d), f["lato"])
        for i, x in enumerate(sorted(row)):
            cols[(x, row[x], f["side"])] = f["pattern"][i % len(f["pattern"])]
        fronts.append(dict(f, row=row, top=top))
    world.facade_cols = cols
    world.fronts = fronts


def cell(c, col, row):
    """Plan (col, row) -> world sector (x, z). Row 0 is the north (top) row."""
    return c["x0"] + col, c["z0"] + (H_ROWS - 1 - row)


def ramp(it, cells, step):
    for i, (wx, wz) in enumerate(cells):
        s = it.room.sectors[wx - it.room.x][wz - it.room.z]
        lo, hi = i * 2 * CLICK, (i + 1) * 2 * CLICK
        s.floor = [lo, hi, hi, lo] if step > 0 else [hi, lo, lo, hi]


def house(ctx):
    k, c = ctx.kit, ctx.world.casa
    G = c["G"]
    F0 = k.interior("CASA_TERRA", F0_PLAN, c["x0"], c["z0"], G, H0, "cementine", "soffitto", "intonaco_interno",
                    ambient=(0.3, 0.29, 0.33))
    F1 = k.interior("CASA_PRIMO", F1_PLAN, c["x0"], c["z0"], G + H0, H1, "maiolica", "soffitto", "intonaco_interno",
                    ambient=(0.3, 0.29, 0.33))
    F2 = k.interior("CASA_SECONDO", F2_PLAN, c["x0"], c["z0"], G + H0 + H1, H2, "parquet", "soffitto",
                    "intonaco_interno", ambient=(0.3, 0.29, 0.33))
    s0 = [cell(c, *p) for p in STAIR0]
    s1 = [cell(c, *p) for p in STAIR1]
    k.link_vertical(F0, F1, s0[1:])
    k.link_vertical(F1, F2, s1[1:])
    ramp(F0, s0, +1)
    ramp(F1, s1, -1)
    hx, hz = cell(c, *HATCH)
    roof_room = k.room_at(hx, hz)
    k.link_vertical(F2, roof_room, [(hx, hz)])
    return F0, F1, F2, roof_room


# Furniture: (name, col, row, dx, dz, rot, floor); position = sector of (col, row) + (dx, dz) sectors.
FURNITURE = [
    ("CASA_CUCINA", 0, 2, 0.32, 0.6, 0.0, 0), ("CASA_FRIGO", 0, 1, 0.35, 0.75, 0.0, 0),
    ("CASA_TAVOLO", 2, 3, 0.4, 0.5, 0.0, 0), ("CASA_SCAFFALE", 7, 0, 0.8, 0.5, 180.0, 0),
    ("CASA_DIVANO", 7, 4, 0.55, 0.5, 180.0, 0), ("CASA_TAVOLINO", 6, 3, 0.4, 0.2, 0.0, 0),
    ("CASA_SEDIA_ROVESCIATA", 3, 2, 0.0, 0.3, 30.0, 0), ("CASA_GRADINI", 2, 4, 0.5, 0.5, 0.0, 0),
    ("CASA_LIBRERIA", 7, 0, 0.8, 0.6, 180.0, 1), ("CASA_SCRIVANIA", 6, 0, 0.6, 0.7, 180.0, 1),
    ("CASA_SEDIA_ROVESCIATA", 6, 1, 0.0, 0.9, 120.0, 1), ("CASA_DIVANO", 0, 4, 0.45, 0.5, 0.0, 1),
    ("CASA_TAVOLINO", 1, 4, 0.6, 0.5, 0.0, 1), ("CASA_GRADINI", 2, 1, 0.5, 0.5, 180.0, 1),
    ("CASA_CORRIMANO", 2, 0, 1.0, 0.0, 0.0, 1),
    ("CASA_LETTO", 0, 4, 0.55, 0.5, 0.0, 2), ("CASA_COMODINO", 0, 4, 0.25, 0.92, 0.0, 2),
    ("CASA_ARMADIO", 3, 4, 0.5, 0.84, 90.0, 2), ("CASA_SCAFFALE", 7, 1, 0.8, 0.5, 180.0, 2),
    ("CASA_CORRIMANO", 1, 1, 1.0, 0.0, 0.0, 2), ("CASA_BAGNO", 7, 4, 0.55, 0.6, 90.0, 2),
]
DOORFRAMES = {0: [(3, 3), (6, 2)], 1: [(2, 3), (6, 3)], 2: [(2, 3)]}   # doorways in wall rows (frame across x)
WINDOWS = [(1, "S"), (3, "S"), (6, "S"), (0, "W"), (7, "E")]          # inside views on the outer walls


def house_dressing(ctx, floors):
    k, c = ctx.kit, ctx.world.casa
    for name, col, row, dx, dz, rot, f in FURNITURE:
        x, z = cell(c, col, row)
        it = floors[f]
        k.prop(name, x + dx, z + dz, rot=rot, h=it.floor_h, room=it.room)
    for f, it in enumerate(floors[:3]):
        for col, row in DOORFRAMES.get(f, []):
            x, z = cell(c, col, row)
            k.prop("CASA_PORTA_ALTA" if f == 2 else "CASA_PORTA", x + 0.5, z + 0.5, rot=90.0, h=it.floor_h, room=it.room)
        for col, side in WINDOWS:
            if side == "S":
                x, z = cell(c, col, H_ROWS - 1)
                k.prop("CASA_FINESTRA", x + 0.5, z + 0.0, rot=270.0, h=it.floor_h, room=it.room)
            elif side == "W":
                x, z = cell(c, 0, 2)
                k.prop("CASA_FINESTRA", x + 0.0, z + 0.5, rot=0.0, h=it.floor_h, room=it.room)
            else:
                x, z = cell(c, W_COLS - 1, 2)
                k.prop("CASA_FINESTRA", x + 1.0, z + 0.5, rot=180.0, h=it.floor_h, room=it.room)
        for col, row in ((2, 2), (6, 4), (6, 1)):
            x, z = cell(c, col, row)
            pos = ((x + 0.5 - it.room.x) * 1024, 1100, (z + 0.5 - it.room.z) * 1024)
            ctx.level.add_light(it.room, 0, pos, color=(1.0, 0.82, 0.6), intensity=0.6, inner=1.5, outer=5.0)
    x, z = cell(c, DOORWAY[0], DOORWAY[1])
    k.prop("CASA_VANO_RIPOSTIGLIO", x + 0.5, z + 0.5, rot=90.0, h=floors[2].floor_h, room=floors[2].room)


def fronts_dressing(ctx):
    """Balconies, the pizzeria's awning and fruit stand, scaffolding, and the street lights at night."""
    k, w, c = ctx.kit, ctx.world, ctx.world.casa
    G = c["G"]
    for f in w.fronts:
        dz = -1 if f["side"] == "-z" else 1
        rot = 0.0 if dz > 0 else 180.0              # model +z points out of the wall
        xs = sorted(f["row"])
        for name, hm, idx in f.get("balconies", []):
            for i in idx:
                if i < len(xs):
                    x = xs[i]
                    zf = f["row"][x] + (1 if dz > 0 else 0)
                    k.prop(name, x + 0.5, zf, rot=rot, h=G + int(hm * 512))
        if f.get("scaffold"):
            for x in xs:
                k.prop("PONTEGGIO", x + 0.5, f["row"][x] + (1 if dz > 0 else 0), rot=rot, h=G)
        if f.get("awning"):
            a0, a1 = f["awning"]
            for x in range(a0, a1 + 1):
                if x in f["row"]:
                    k.prop("TENDA_PIZZERIA", x + 0.5, f["row"][x] + 1, rot=rot, h=G)
            x = a0 + 1
            if x in f["row"]:
                k.prop("BANCO_FRUTTA", x + 0.5, f["row"][x] + 1.5, rot=rot, h=G)
    # Roofs: parapets on the house's street edge (gap over the drainpipe), water tanks, antennas, the pergola.
    R = c["ROOF"]
    for col in range(1, W_COLS):
        k.prop("PARAPETTO", c["x0"] + col + 0.5, c["z0"] + 0.11, rot=0.0, h=R)
    k.prop("PERGOLATO", c["x0"] + 5.0, c["z0"] + 3.2, rot=0.0, h=R)
    k.prop("SERBATOIO", c["x0"] + 1.6, c["z0"] + 4.2, rot=0.0, h=R)
    k.prop("ANTENNA_TV", c["x0"] + 3.5, c["z0"] + 4.5, rot=0.0, h=R)
    for f in w.fronts:
        if f["name"] in ("rosa", "arancio", "rosa_s"):
            xs = sorted(f["row"])
            x = xs[len(xs) // 2]
            z = f["row"][x] + (2 if f["side"] == "-z" else -2)
            k.prop("SERBATOIO", x + 0.5, z + 0.5, rot=90.0, h=f["top"])
            k.prop("ANTENNA_TV", x + 1.5, z + 1.0, rot=0.0, h=f["top"])
    # warm street lights every 14 m on both pavements, and a cold moonlight
    room = k.room_at(c["x0"], c["z0"] - 3)
    for x in range(4, w.nx - 4, 7):
        for z in (c["z0"] - 1, c["z0"] - 8):
            if 0 <= z < w.nz and w.building_id[x, z] < 0:
                r = k.room_at(x, z)
                pos = ((x + 0.5 - r.x) * 1024, G + 2600 - r.y, (z + 0.5 - r.z) * 1024)
                ctx.level.add_light(r, 0, pos, color=(1.0, 0.78, 0.5), intensity=0.9, inner=2.0, outer=7.0)
    del room


def street(ctx):
    """Via Amodeo as on Street View: Fiat 500s and a white van parked on both kerbs, palms and white
    planters on the pavements, the pizzeria's tables on the opposite side; dogs and a look-out."""
    k, w, c = ctx.kit, ctx.world, ctx.world.casa
    zf = c["z0"] - 1                      # pavement in front of the house
    rot_along = 90.0                      # cars: local +Z along +x
    cars = [("AUTO_UTILITARIA_BIANCA", c["x0"] + 2, zf - 2), ("AUTO_UTILITARIA_BIANCA", c["x0"] + 9, zf - 2),
            ("AUTO_BERLINA_GRIGIA", c["x0"] - 6, zf - 2), ("FURGONE_BIANCO", c["x0"] + 4, zf - 7),
            ("AUTO_UTILITARIA_ROSSA", c["x0"] + 12, zf - 7), ("AUTO_SUV_BLU", c["x0"] - 3, zf - 7)]
    for name, x, z in cars:
        if 0 <= x < w.nx and 0 <= z < w.nz and w.building_id[x, z] < 0:
            k.prop(name, x + 0.5, z + 0.5, rot=rot_along)
    for dx in (-1, 6, 11):
        x = c["x0"] + dx
        if w.building_id[x, zf] < 0:
            k.prop("VASO_BIANCO_PALMA", x + 0.5, zf + 0.35, rot=0.0)
    k.prop("SCOOTER_ROSSO", c["x0"] + 7.4, zf + 0.4, rot=0.0)
    for dx in (3, 5):
        x, z = c["x0"] + dx, zf - 8
        if w.building_id[x, z] < 0:
            k.prop("DEHORS_TAVOLO", x + 0.5, z + 0.5, rot=0.0)
            k.prop("DEHORS_OMBRELLONE", x + 0.5, z + 0.5, rot=0.0)


DECOR = dict(centre=None)


def build(ctx):
    k, lua, c, w = ctx.kit, ctx.lua, ctx.world.casa, ctx.world
    ctx.decor_block = [(c["x0"] - 14, c["z0"] - 10, c["x0"] + 16, c["z0"] + H_ROWS + 1)]
    F0, F1, F2, roof_room = house(ctx)
    house_dressing(ctx, (F0, F1, F2))
    street(ctx)
    fronts_dressing(ctx)

    def at(it, col, row, dh=0):
        x, z = cell(c, col, row)
        return k.lua_pos(x, z, it.floor_h + dh)

    sx, sz = cell(c, 1, 4)
    k.place(K.LARA, sx, sz, room=F2.room, rot=180.0, name="lara_start")
    k.place(K.SMALLMEDI, *cell(c, 7, 4), room=F2.room)
    k.place(K.FLARE_ITEM, *cell(c, 0, 2), room=F2.room)
    k.place(K.SHOTGUN_ITEM, *cell(c, 1, 2), room=F0.room)
    k.place(K.SHOTGUN_AMMO1, *cell(c, 2, 4), room=F0.room)
    k.place(K.BADDY2, *cell(c, 3, 4), room=F1.room, name="ladro_primo")
    k.place(K.BADDY2, *cell(c, 6, 3), room=F0.room, name="ladro_terra")
    k.place(K.BADDY1, *cell(c, 1, 4), room=F0.room, name="ladro_chiave")
    hx, hz = cell(c, *HATCH)
    # TEN ceiling trapdoor (generic_trapdoor.cpp): the player must be 256..768 units behind the item
    # (local z -768..-256) and 0..900 below it; the leaf spans local z 0..-1024 and hangs from the item
    # when open. Turned 180 on the south edge of the hatch sector the leaf covers the hatch, Lara is
    # caught jumping from the middle of the 3-click step, and the open leaf hangs on the door side, away
    # from the chimney wall she then grabs to climb through.
    k.place(K.CEILING_TRAPDOOR1, hx, hz, room=roof_room, rot=180.0, dz=0.0, name="botola_tetto")
    dx, dz = cell(c, *DOOR)
    door = k.place(K.DOOR_TYPE1, dx, dz, room=F2.room, rot=180.0, name="porta_ripostiglio")
    lx, lz = cell(c, *LOCK)
    lock = k.place(K.KEY_HOLE1, lx, lz, room=F2.room, rot=0.0, name="serratura_ripostiglio")
    k.trigger(lx, lz, room=F2.room, trig_type=K.T_KEY, target=lock)
    k.trigger(lx, lz, room=F2.room, trig_type=K.T_KEY, target=door)
    # Down from the roof: the drainpipe on the street front, at the west end of the house.
    cx = c["x0"]
    k.climb(cx, c["z0"] - 1, "+z")
    k.prop("CASA_PLUVIALE", cx + 0.5, c["z0"] - 0.02, rot=0.0, h=c["G"])

    lua.start('CDV.Say("Oliveri, notte. Rumori al piano di sotto... qualcuno e\' entrato in casa.", 7)')
    lua.zone("primo", at(F1, 4, 0), r=1400, dy=900, fn='CDV.Enable("ladro_primo")',
             text="Uno della banda della Volpe! Cercano il diario bizantino.")
    lua.zone("terra", at(F0, 4, 0), r=1600, dy=900, fn='CDV.Enable("ladro_terra")\nCDV.Enable("ladro_chiave")')
    lua.drop("chiave", "ladro_chiave", "ID.KEY_ITEM1",
             "Il tombarolo aveva la chiave del ripostiglio. Il diario pero' non c'e': l'ha preso il loro capo.")
    lua.zone("portone", at(F0, 6, 4), r=1200, dy=900, once=True,
             text="Il portone e' sbarrato da fuori. Resta la botola del ripostiglio, sul tetto.")
    lua.use("chiave_ripostiglio", "ID.KEY_ITEM1", at(F2, *LOCK), r=700, dy=600,
            text="La serratura scatta: il ripostiglio e' aperto.",
            fn='CDV.InsertKey("serratura_ripostiglio", "porta_ripostiglio")')
    lua.zone("ripostiglio_chiuso", at(F2, *LOCK), r=1100, dy=900, once=False, secs=4,
             need='not CDV.Has(ID.KEY_ITEM1) and not CDV.Done("use_chiave_ripostiglio")',
             text="Il ripostiglio della botola e' chiuso a chiave. Uno dei ladri ha la chiave.")
    lua.zone("tetto", k.lua_pos(hx, hz, c["ROOF"]), r=1800, dy=300,
             text="Sulla terrazza. Sul davanti, verso la via, si scende lungo il pluviale.")

    # Via Amodeo: the look-out and two dogs; the thief runs off towards Via Stesicoro.
    zf = c["z0"] - 1
    k.place(K.DOBERMAN, *k.spot(c["x0"] + 10, zf - 4), name="cane1")
    k.place(K.DOBERMAN, *k.spot(c["x0"] + 12, zf - 5), name="cane2")
    k.place(K.BADDY1, *k.spot(c["x0"] - 8, zf - 4), rot=90.0, name="palo")
    k.place(K.SMALLMEDI, *k.spot(c["x0"] + 14, zf - 1))
    street_c = k.spot(c["x0"], zf - 2)
    lua.zone("via", k.lua_pos(*street_c, ctx.ground(*street_c)), r=4000, dy=6000,
             fn='CDV.Enable("cane1")\nCDV.Enable("cane2")\nCDV.Enable("palo")',
             text="I cani della banda! E il ladro corre verso Via Stesicoro.")
    jx, jz = w.sector_of(38.124132, 15.059829)
    ex, ez = k.spot(jx, jz)
    lua.zone("fine", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2600, dy=4000,
             need='CDV.Dead("palo")', fn="CDV.End(2, 1)",
             text="Il ladro ha preso Via Stesicoro, verso la piazza e il castello.")
    lua.zone("fine_no", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2600, dy=4000, once=False, secs=4,
             need='not CDV.Dead("palo")', text="Prima devo togliermi di torno il palo della banda.")
    lua.secret(0, at(F0, 7, 0), r=800)
    ctx.notes += [
        "LIVELLO 1 - OLIVERI, VIA GASPARE AMODEO",
        "1. Lara si sveglia in camera al secondo piano (medikit vicino al letto, razzi vicino alle scale).",
        "2. Le scale scendono al primo piano (un ladro) e al piano terra (due ladri, fucile in cucina).",
        "   Il ladro dell'ingresso lascia la Chiave del ripostiglio. Segreto 1: la dispensa dietro la cucina.",
        "3. Si risale al secondo piano: la chiave va nella serratura sul muro accanto alla porta del ripostiglio",
        "   (Azione davanti alla serratura). La porta si apre.",
        "4. Nel ripostiglio, dal gradino: salto in alto + Azione per tirare giu' la botola; poi salto, aggrappo, su.",
        "5. Dalla terrazza, sul lato della via, ci si cala lungo il pluviale.",
        "6. In Via Amodeo due cani e il palo della banda. Fine del livello all'incrocio con Via Stesicoro.",
    ]
