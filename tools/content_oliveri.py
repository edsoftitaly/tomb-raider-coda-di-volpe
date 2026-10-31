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
W_COLS, H_ROWS = 8, 5            # house footprint: 8 x 5 sectors (16 x 10 m), the street on the south side
H0 = H1 = 1536                   # storeys 3 m
H2 = 1792                        # second floor 3.5 m

# v7: every room is its own TR room, joined to its neighbours by thin-wall door portals (TRLE practice),
# instead of one plan per storey with sector-thick walls. House-local coordinates: col 0..7 west -> east,
# row 0..4 from the street (south) to the back (north).
#   name: (storey, (col0, col1), (row0, row1), floor texture)
ROOMS = {
    "INGRESSO": (0, (0, 3), (0, 2), "cementine"),
    "SCALA0": (0, (0, 2), (3, 4), "cementine"),
    "LAB": (0, (4, 7), (0, 2), "cementine"),
    "DISPENSA": (0, (4, 7), (3, 4), "cementine"),
    "SOGGIORNO": (1, (0, 4), (0, 2), "maiolica"),
    "CUCINA": (1, (5, 7), (0, 2), "maiolica"),
    "SCALA1": (1, (0, 3), (3, 4), "cementine"),
    "STUDIO": (1, (4, 7), (3, 4), "parquet"),
    "CAMERA": (2, (0, 3), (0, 2), "parquet"),
    "BAGNO": (2, (4, 5), (0, 2), "maiolica"),
    "RIPOSTIGLIO": (2, (6, 7), (0, 2), "parquet"),
    "SCALA2": (2, (0, 2), (3, 4), "parquet"),
    "CORRIDOIO": (2, (3, 7), (3, 4), "parquet"),
}
# Doorways: (room a, room b, the col (z border) or row (x border) of the opening).
DOORS = [
    ("INGRESSO", "SCALA0", 1), ("INGRESSO", "LAB", 1), ("LAB", "DISPENSA", 6),
    ("SCALA1", "SOGGIORNO", 0), ("SOGGIORNO", "CUCINA", 1), ("SCALA1", "STUDIO", 4),
    ("SCALA2", "CORRIDOIO", 4), ("CAMERA", "CORRIDOIO", 3), ("BAGNO", "CORRIDOIO", 4),
    ("RIPOSTIGLIO", "CORRIDOIO", 7),
]
STAIR0 = [(0, 4), (1, 4), (2, 4)]          # SCALA0, rising east; top cells open into SCALA1
STAIR1 = [(3, 3), (2, 3), (1, 3)]          # SCALA1, rising west; top cells open into SCALA2, landing (0, 3)
HATCH = (6, 1)                             # RIPOSTIGLIO: ladder on the west wall, hole to the roof above
DOOR = (7, 3)                              # door item in CORRIDOIO, leaf on the south edge (rot 0)
LOCK = (6, 3)                              # lock plate on the south wall of CORRIDOIO (rot 180)
START = (2, 1)                             # CAMERA


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
    # Every other building of the zone: an ordinary palazzina facade (four variants by building), so no
    # face keeps the old generic atlas look. Door on the middle column of each street face.
    variants = ("ocra", "bianca", "grigia", "crema")
    for b in np.unique(world.building_id[world.building_id >= 0]):
        b = int(b)
        v = variants[(b * 7) % 4]
        faces = {}
        for (x, z) in zip(*np.nonzero(world.building_id == b)):
            for d, (ddx, ddz) in (("+x", (1, 0)), ("-x", (-1, 0)), ("+z", (0, 1)), ("-z", (0, -1))):
                nx_, nz_ = x + ddx, z + ddz
                if 0 <= nx_ < world.nx and 0 <= nz_ < world.nz and world.building_id[nx_, nz_] != b:
                    faces.setdefault(d, []).append((int(x), int(z)))
        for d, cells in faces.items():
            cells.sort()
            mid = cells[len(cells) // 2]
            for (x, z) in cells:
                kind = "porta" if (x, z) == mid and len(cells) > 2 else "finestra"
                cols.setdefault((x, z, d), "fac_gen_%s_%s" % (v, kind))
        bb = world.buildings[b]
        if "base_m" not in bb or bb.get("base_m") is None:
            bb["base_m"] = street_h / 512.0
    world.facade_cols = cols
    world.fronts = fronts


def cell(c, col, row):
    """House-local (col, row) -> world sector (x, z). Row 0 is the street (south) row."""
    return c["x0"] + col, c["z0"] + row


def ramp(it, cells, step):
    for i, (wx, wz) in enumerate(cells):
        s = it.room.sectors[wx - it.room.x][wz - it.room.z]
        lo, hi = i * 2 * CLICK, (i + 1) * 2 * CLICK
        s.floor = [lo, hi, hi, lo] if step > 0 else [hi, lo, lo, hi]


def storey_h(c, f):
    return c["G"] + (0, H0, H0 + H1)[f], (H0, H1, H2)[f]


def house(ctx):
    k, c = ctx.kit, ctx.world.casa
    R = {}
    for name, (f, (c0, c1), (r0, r1), ftex) in ROOMS.items():
        h, height = storey_h(c, f)
        plan = ["." * (c1 - c0 + 1)] * (r1 - r0 + 1)
        x0, z0 = cell(c, c0, r0)
        R[name] = k.interior("CASA_" + name, plan, x0, z0, h, height, ftex, "soffitto", "intonaco_interno",
                             ambient=(0.2, 0.2, 0.26))
        R[name].storey = f
    for a, b, at in DOORS:
        ra, rb = R[a].room, R[b].room
        x_border = ra.x + ra.nx - 2 == rb.x or rb.x + rb.nx - 2 == ra.x
        w = cell(c, 0, at)[1] if x_border else cell(c, at, 0)[0]
        k.link_wall(R[a], R[b], span=(w, w))
    s0 = [cell(c, *p) for p in STAIR0]
    s1 = [cell(c, *p) for p in STAIR1]
    ramp(R["SCALA0"], s0, +1)
    ramp(R["SCALA1"], s1, -1)
    k.link_vertical(R["SCALA0"], R["SCALA1"], s0[1:])
    k.link_vertical(R["SCALA1"], R["SCALA2"], s1[1:])
    hx, hz = cell(c, *HATCH)
    roof_room = k.room_at(hx, hz)
    k.link_vertical(R["RIPOSTIGLIO"], roof_room, [(hx, hz)])
    k.climb(hx, hz, "-x", room=R["RIPOSTIGLIO"].room)
    return R, roof_room


# Furniture: (model, x, z in house-local sectors (fractions), rot, room).
FURNITURE = [
    ("CASA_LETTO", 0.55, 1.5, 0.0, "CAMERA"), ("CASA_COMODINO", 0.25, 2.6, 0.0, "CAMERA"),
    ("CASA_ARMADIO", 2.5, 2.84, 90.0, "CAMERA"), ("CASA_QUADRO", 0.02, 1.5, 0.0, "CAMERA"),
    ("CASA_BAGNO", 5.45, 1.0, 90.0, "BAGNO"),
    ("CASA_SCAFFALE", 7.8, 0.7, 180.0, "RIPOSTIGLIO"), ("SCALA_PIOLI", 6.0, 1.5, 0.0, "RIPOSTIGLIO"),
    ("CASA_SCAFFALE", 7.8, 3.6, 180.0, "CORRIDOIO"),
    ("CASA_DIVANO", 0.45, 1.5, 0.0, "SOGGIORNO"), ("CASA_TAVOLINO", 1.6, 1.5, 0.0, "SOGGIORNO"),
    ("CASA_MOBILE_TV", 4.75, 1.5, 180.0, "SOGGIORNO"), ("CASA_LIBRERIA", 2.5, 2.8, 90.0, "SOGGIORNO"),
    ("CASA_SEDIA_ROVESCIATA", 3.2, 0.8, 30.0, "SOGGIORNO"),
    ("CASA_CUCINA", 7.68, 1.5, 180.0, "CUCINA"), ("CASA_FRIGO", 7.7, 2.6, 180.0, "CUCINA"),
    ("CASA_TAVOLO", 6.0, 1.2, 0.0, "CUCINA"), ("CASA_SEDIA", 6.0, 0.6, 0.0, "CUCINA"),
    ("CASA_SCRIVANIA", 5.6, 4.7, 180.0, "STUDIO"), ("CASA_LIBRERIA", 7.8, 3.9, 180.0, "STUDIO"),
    ("CASA_SCAFFALE", 0.2, 1.0, 0.0, "INGRESSO"), ("CASA_PORTONE_INT", 2.5, 0.02, 0.0, "INGRESSO"),
    ("CASA_TAVOLO", 5.5, 1.5, 0.0, "LAB"), ("CASA_SEDIA_ROVESCIATA", 6.6, 1.0, 120.0, "LAB"),
    ("CASA_SCAFFALE", 7.8, 1.5, 180.0, "LAB"),
    ("CASA_SCAFFALE", 7.8, 3.6, 180.0, "DISPENSA"), ("CASA_SCAFFALE", 4.2, 4.0, 0.0, "DISPENSA"),
]
# Windows on the outer walls: (col or row, side, rooms by storey).
WINDOWS = [(1, "S"), (3, "S"), (6, "S"), (1, "W"), (1, "E")]


def house_dressing(ctx, R):
    k, c = ctx.kit, ctx.world.casa
    for name, x, z, rot, rn in FURNITURE:
        it = R[rn]
        k.prop(name, c["x0"] + x, c["z0"] + z, rot=rot, h=it.floor_h, room=it.room)
    for a, b, at in DOORS:
        ia, ib = R[a], R[b]
        ra, rb = ia.room, ib.room
        tall = "CASA_PORTA_ALTA" if ia.storey == 2 else "CASA_PORTA"
        if ra.x + ra.nx - 2 == rb.x or rb.x + rb.nx - 2 == ra.x:
            xb = max(ra.x, rb.x) + 1
            k.prop(tall, xb, c["z0"] + at + 0.5, rot=0.0, h=ia.floor_h, room=ra)
        else:
            zb = max(ra.z, rb.z) + 1
            k.prop(tall, c["x0"] + at + 0.5, zb, rot=90.0, h=ia.floor_h, room=ra)
    for name, (f, (c0, c1), (r0, r1), _) in ROOMS.items():
        it = R[name]
        for at, side in WINDOWS:
            if side == "S" and r0 == 0 and c0 <= at <= c1:
                k.prop("CASA_FINESTRA", c["x0"] + at + 0.5, c["z0"], rot=270.0, h=it.floor_h, room=it.room)
            elif side == "W" and c0 == 0 and r0 <= at <= r1:
                k.prop("CASA_FINESTRA", c["x0"], c["z0"] + at + 0.5, rot=0.0, h=it.floor_h, room=it.room)
            elif side == "E" and c1 == W_COLS - 1 and r0 <= at <= r1:
                k.prop("CASA_FINESTRA", c["x0"] + W_COLS, c["z0"] + at + 0.5, rot=180.0, h=it.floor_h, room=it.room)
        # one warm ceiling lamp per room, a little off-centre
        room = it.room
        h = (H0, H1, H2)[f] - 300
        pos = (((c0 + c1 + 1) / 2.0 + c["x0"] - room.x) * 1024, h, ((r0 + r1 + 1) / 2.0 + c["z0"] - room.z) * 1024)
        ctx.level.add_light(room, 0, pos, color=(1.0, 0.8, 0.55), intensity=0.75, inner=1.5, outer=6.0)
    # handrails along the stair wells
    for x, z, rot, rn in ((1.0, 4.0, 0.0, "SCALA1"), (1.5, 3.0, 0.0, "SCALA2")):
        it = R[rn]
        k.prop("CASA_CORRIMANO", c["x0"] + x + 0.5, c["z0"] + z, rot=rot, h=it.floor_h, room=it.room)


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
    # Street life on the facades: air-conditioner units, laundry in front of some balconies, the street
    # name plaque, overhead cables across the road, the bins on the opposite pavement.
    import random
    rnd = random.Random(7)
    for f in w.fronts:
        dz = -1 if f["side"] == "-z" else 1
        rot = 0.0 if dz > 0 else 180.0
        xs = sorted(f["row"])
        for i, x in enumerate(xs):
            zf = f["row"][x] + (1 if dz > 0 else 0)
            if f["name"] != "casa" and rnd.random() < 0.35:
                hm = rnd.choice((4.4, 7.4)) if f["top"] - G > 7 * 512 else 4.4
                k.prop("CONDIZIONATORE", x + rnd.uniform(0.25, 0.75), zf, rot=rot, h=G + int(hm * 512))
        for name, hm, idx in f.get("balconies", []):
            for j, i in enumerate(idx):
                if i < len(xs) and (j + int(hm)) % 3 == 0:
                    x = xs[i]
                    zf = f["row"][x] + (1 if dz > 0 else 0) + 0.4 * dz
                    k.prop("PANNI_STESI", x + 0.5, zf, rot=0.0, h=G + int((hm + 0.95) * 512))
    k.prop("TARGA_VIA", c["x0"] + 1.5, c["z0"], rot=180.0, h=G + int(2.9 * 512))
    k.prop("CONDIZIONATORE", c["x0"] + 6.6, c["z0"], rot=180.0, h=G + int(7.3 * 512))
    opp = [f for f in w.fronts if f["side"] == "+z"]
    if opp:
        z_opp = min(min(f["row"].values()) for f in opp) + 1
        zc = (z_opp + c["z0"]) / 2.0
        for x in (c["x0"] - 6, c["x0"] + 4, c["x0"] + 13):
            k.prop("CAVI_AEREI", x + 0.5, zc, rot=0.0, h=G)
        k.prop("CASSONETTI", c["x0"] + 9.5, z_opp + 0.5, rot=0.0, h=G)
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
    R, roof_room = house(ctx)
    house_dressing(ctx, R)
    street(ctx)
    fronts_dressing(ctx)

    def at(rn, col, row, dh=0):
        x, z = cell(c, col, row)
        return k.lua_pos(x, z, R[rn].floor_h + dh)

    def put(t, rn, col, row, **kw):
        return k.place(t, *cell(c, col, row), room=R[rn].room, **kw)

    put(K.LARA, "CAMERA", *START, rot=0.0, name="lara_start")
    put(K.FLARE_ITEM, "CAMERA", 3, 0)
    put(K.SMALLMEDI, "CUCINA", 5, 2)
    put(K.SHOTGUN_ITEM, "STUDIO", 6, 4)
    put(K.SHOTGUN_AMMO1, "LAB", 7, 0)
    put(K.SMALLMEDI, "LAB", 4, 0)
    put(K.BADDY2, "SOGGIORNO", 3, 1, rot=270.0, name="ladro_primo")
    put(K.BADDY2, "LAB", 6, 1, rot=270.0, name="ladro_terra")
    put(K.BADDY1, "INGRESSO", 1, 1, rot=0.0, name="ladro_chiave")
    hx, hz = cell(c, *HATCH)
    # The hatch: a wooden lid hinged on its east edge, lying on the roof over the hole. Lara pushes it
    # open climbing the ladder (Lua zone near the top), then climbs out west onto the roof over the bathroom.
    k.prop("BOTOLA_LEGNO", hx + 1.0, hz + 0.5, rot=0.0, h=c["ROOF"], room=roof_room, lua_name="botola_legno")
    # The box-room door: TEN door (collision, opened by the lock) + a hinged static leaf for the look
    # (the door moveable's own mesh does not show in this setup).
    dx_, dz_ = cell(c, *DOOR)
    k.prop("CASA_ANTA", dx_ + 0.02, dz_, rot=0.0, h=R["CORRIDOIO"].floor_h, room=R["CORRIDOIO"].room,
           lua_name="anta_ripostiglio")
    door = put(K.DOOR_TYPE1, "CORRIDOIO", *DOOR, rot=0.0, name="porta_ripostiglio")
    lock = put(K.KEY_HOLE1, "CORRIDOIO", *LOCK, rot=180.0, name="serratura_ripostiglio")
    del door, lock
    # Down from the roof: the drainpipe on the street front, at the west end of the house.
    cx = c["x0"]
    k.climb(cx, c["z0"] - 1, "+z")
    k.prop("CASA_PLUVIALE", cx + 0.5, c["z0"] - 0.02, rot=0.0, h=c["G"])

    lua.start('CDV.Say("Oliveri, notte. Rumori al piano di sotto... qualcuno e\' entrato in casa.", 7)')
    lua.zone("primo", at("SCALA1", 0, 3), r=1200, dy=700, fn='CDV.Enable("ladro_primo")',
             text="Uno della banda della Volpe! Cercano il diario bizantino.")
    lua.zone("terra", at("SCALA0", 1, 3), r=1200, dy=700, fn='CDV.Enable("ladro_terra")\nCDV.Enable("ladro_chiave")')
    lua.drop("chiave", "ladro_chiave", "ID.KEY_ITEM1",
             "Il tombarolo aveva la chiave del ripostiglio. Il diario pero' non c'e': l'ha preso il loro capo.")
    lua.zone("portone", at("INGRESSO", 2, 0), r=1100, dy=700, once=True,
             text="Il portone e' sbarrato da fuori. Resta la botola del ripostiglio, sul tetto.")
    lua.use("chiave_ripostiglio", "ID.KEY_ITEM1", at("CORRIDOIO", *LOCK), r=700, dy=600,
            text="La serratura scatta: il ripostiglio e' aperto.",
            fn='CDV.InsertKey("serratura_ripostiglio", "porta_ripostiglio", "anta_ripostiglio")')
    lua.zone("ripostiglio_chiuso", at("CORRIDOIO", *LOCK), r=900, dy=700, once=False, secs=4,
             need='not CDV.Has(ID.KEY_ITEM1) and not CDV.Done("use_chiave_ripostiglio")',
             text="Il ripostiglio e' chiuso a chiave. Uno dei ladri ha la chiave.")
    lua.zone("botola", at("RIPOSTIGLIO", *HATCH, dh=1100), r=600, dy=500, fn='CDV.Swing("botola_legno", "z", -110, 30)',
             text="Una spinta e la botola si apre.")
    lua.zone("tetto", k.lua_pos(hx - 1, hz, c["ROOF"]), r=1400, dy=300,
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
    lua.secret(0, at("DISPENSA", 7, 4), r=800)
    ctx.notes += [
        "LIVELLO 1 - OLIVERI, VIA GASPARE AMODEO",
        "1. Lara si sveglia in camera, al secondo piano (razzi vicino alla finestra).",
        "2. Le scale scendono al primo piano (un ladro nel soggiorno, medikit in cucina, fucile nello studio)",
        "   e al piano terra (due ladri). Il ladro dell'ingresso lascia la Chiave del ripostiglio.",
        "   Segreto 1: la dispensa dietro il laboratorio.",
        "3. Si risale al secondo piano: la chiave va nella serratura sul muro del corridoio, accanto alla",
        "   porta del ripostiglio (usare la chiave dall'inventario davanti alla serratura). La porta si apre.",
        "4. Nel ripostiglio si sale la scala a pioli: a meta' Lara spinge la botola, in cima esce sul tetto.",
        "5. Dalla terrazza, sul lato della via, ci si cala lungo il pluviale.",
        "6. In Via Amodeo due cani e il palo della banda. Fine del livello all'incrocio con Via Stesicoro.",
    ]
