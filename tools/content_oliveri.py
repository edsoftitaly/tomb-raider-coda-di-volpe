"""Livello 1 - Oliveri, Via Gaspare Amodeo (notte). v6: small zone aligned with the street.

The level is a 164 x 80 m strip of Via Gaspare Amodeo, rotated so that the street runs along +x
(episode.LEVELS["Oliveri"]["frame"]): every facade on the street lies on a sector edge.
References: Google satellite view and Street View (31/10/2026) for the house and the street; nothing
is copied, textures are procedural.

Route: Ed's house, second floor (Lara wakes up) -> down the U stair to the first and ground floor (thieves,
the box-room key, the winch crank) -> back up -> the key in the lock beside the walk-in wardrobe door
(native KEY_HOLE1) -> up the ladder through the roof hatch -> roof terrace ->
down the drainpipe on the street front (climbable wall) -> Via Amodeo (dogs, the thief's look-out) ->
the thief runs to the junction with Via Stesicoro: level end.
"""
import math

import numpy as np

import kit as K
import prj2
from kit import CLICK

HOUSE_LATLON = (38.1241402, 15.0600308)
W_COLS, H_ROWS = 8, 5            # house footprint: 8 x 5 sectors (16 x 10 m), the street on the south side
H0 = H1 = 1536                   # storeys 3 m
H2 = 1792                        # second floor 3.5 m

# v9 (piante Capri 140 adattate a 16 x 10 m): every room is its own TR room, joined to its neighbours by
# thin-wall door portals. House-local coordinates: col 0..7 west -> east, row 0..4 from the street (south)
# to the back (north); one cell = one sector = 2 x 2 m.
#   name: (storey, (col0, col1), (row0, row1), floor texture)
ROOMS = {
    # ground floor (not in the plans): entrance hall with the stair, pantry, workshop, cellar
    "INGRESSO": (0, (2, 5), (0, 2), "cementine"),
    "DISPENSA": (0, (0, 1), (0, 2), "cementine"),
    "LAB": (0, (6, 7), (0, 2), "cementine"),
    "CANTINA": (0, (0, 7), (3, 4), "cementine"),
    # first floor = Erdgeschoss: Diele with the stair, WC, utility room, kitchen, living/dining across the back
    "DISIMPEGNO": (1, (2, 5), (0, 2), "cementine"),
    "WC": (1, (0, 1), (0, 0), "maiolica"),
    "LAVANDERIA": (1, (0, 1), (1, 2), "maiolica"),
    "CUCINA": (1, (6, 7), (0, 2), "maiolica"),
    "SOGGIORNO": (1, (0, 7), (3, 4), "parquet"),
    # second floor = Obergeschoss: gallery round the stair well, bath, bedroom, walk-in wardrobe, two kids' rooms
    "GALLERIA": (2, (2, 5), (0, 2), "parquet"),
    "BAGNO": (2, (0, 1), (0, 2), "maiolica"),
    "CAMERETTA2": (2, (6, 7), (0, 2), "parquet"),
    "CAMERA": (2, (0, 2), (3, 4), "parquet"),
    "RIPOSTIGLIO": (2, (3, 4), (3, 4), "parquet"),
    "CAMERETTA1": (2, (5, 7), (3, 4), "parquet"),
}
# Openings: (room a, room b, (col, row) of the cell in a, of the cell in b, kind): True = doorway with a
# frame, "chiave" = the box-room door (frame without leaf, the TEN door closes it), an int = an open
# passage that many sectors wide.
DOORS = [
    ("INGRESSO", "DISPENSA", (2, 2), (1, 2), True), ("INGRESSO", "LAB", (5, 2), (6, 2), True),
    ("INGRESSO", "CANTINA", (3, 2), (3, 3), True),
    ("DISIMPEGNO", "LAVANDERIA", (2, 2), (1, 2), True), ("LAVANDERIA", "WC", (0, 1), (0, 0), True),
    ("DISIMPEGNO", "CUCINA", (5, 2), (6, 2), True), ("DISIMPEGNO", "SOGGIORNO", (3, 2), (3, 3), True),
    ("CUCINA", "SOGGIORNO", (6, 2), (6, 3), 2),
    ("GALLERIA", "BAGNO", (2, 1), (1, 1), True), ("GALLERIA", "CAMERA", (2, 2), (2, 3), True),
    ("GALLERIA", "CAMERETTA1", (5, 2), (5, 3), True), ("GALLERIA", "CAMERETTA2", (5, 2), (6, 2), True),
    ("GALLERIA", "RIPOSTIGLIO", (3, 2), (3, 3), "chiave"),
]
# The stair: a U in a well, the same on both storeys. Flight A rises east along row 1 (A1 from the hall
# floor, then A2), a 2 x 4 m landing on col 5, flight B rises west along row 0 and arrives on the next floor
# at (3, 0). Ground floor: sector ramps (solid under them). First floor: A1 is a sector ramp; A2, the landing
# and B float over the ground-floor well as TEN bridges (a sector has one floor). The well (cols 4-5,
# rows 0-1) is open through the first and the second floor.
A1, A2, LAND, B, ARRIVE = (3, 1), (4, 1), [(5, 0), (5, 1)], (4, 0), (3, 0)
WELL = [(4, 0), (4, 1), (5, 0), (5, 1)]
HATCH = (3, 4)                             # RIPOSTIGLIO: ladder on the west wall, hole to the roof above
DOOR = (3, 2)                              # door item in GALLERIA, leaf on the north edge (rot 180)
LOCK = (4, 2)                              # lock plate on the north wall of GALLERIA (rot 0)
START = (0, 3)                             # CAMERA


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


G_STREET = 1280                  # street level (units): the house interiors hang on it

# v7.1: a straight town plan ("a croce") instead of the rasterised map: every street runs along x or z,
# every building is a rectangle, so no staircase of obliquely cut blocks. Real places kept: the house,
# its two neighbours, the street front opposite (pizzeria), the courtyard inside the southern block,
# the crossing with Via Stesicoro at the west end of the house block. The map border is a ring of tall
# buildings, and every street ends against a facade: from the street and from the roofs the town never
# just stops.
STREETS_X = [(19, 22)]                   # Via Gaspare Amodeo (z range), runs along x
STREETS_Z = [(15, 18), (70, 73)]         # Via Stesicoro and the next cross street (x range), along z
STREET_N = (42, 45)                      # the street behind the house block, along x
PAVE = 2                                 # pavement width on each side (sectors)


def town_plan(world):
    """Returns (building cells -> block id map, heights in metres per block)."""
    nx, nz = world.nx, world.nz
    road = np.zeros((nx, nz), bool)
    pave = np.zeros((nx, nz), bool)
    for z0, z1 in STREETS_X + [STREET_N]:
        road[2:nx - 2, z0:z1 + 1] = True
        pave[2:nx - 2, z0 - PAVE:z1 + PAVE + 1] = True
    for x0, x1 in STREETS_Z:
        road[x0:x1 + 1, 2:nz - 2] = True
        pave[x0 - PAVE:x1 + PAVE + 1, 2:nz - 2] = True
    pave &= ~road
    return road, pave


def prepare(world):
    import zlib
    G = G_STREET
    nx, nz = world.nx, world.nz
    road, pave = town_plan(world)
    open_ = road | pave
    yard_x0, yard_x1, yard_z0, yard_z1 = YARD
    open_[yard_x0:yard_x1 + 1, yard_z0:yard_z1 + 1] = True
    for z in range(PASSAGE_Z[0], PASSAGE_Z[1] + 1):
        open_[PASSAGE_X, z] = True
    world.water[:, :] = False
    world.floor[:, :, :] = G
    world.floor_terrain[:, :, :] = G
    world.building_id[:, :] = -1
    world.buildings = []
    # Blocks: everything not open is built; split into buildings 4..9 sectors long along the street
    # they face, one depth band of 5..7 sectors, heights 2..5 storeys; the outer ring is 5 storeys.
    fixed = [("casa", 25, 32, 25, 29, 9.5), ("rosa", 33, 36, 25, 30, 9.5), ("arancio", 37, 45, 25, 31, 9.5)]
    taken = np.zeros((nx, nz), bool)

    def add(name, x0, x1, z0, z1, h):
        cells = np.zeros((nx, nz), bool)
        cells[x0:x1 + 1, z0:z1 + 1] = True
        cells &= ~open_ & ~taken
        if not cells.any():
            return None
        bid = len(world.buildings)
        world.building_id[cells] = bid
        taken[cells] = True
        top = G + int(round(h * 512 / 256.0)) * 256
        world.floor[cells] = top
        world.buildings.append({"id": name, "tags": {"building": "yes"}, "sectors": int(cells.sum()),
                                "ground_m": G / 512.0, "base_m": G / 512.0, "roof_m": top / 512.0})
        return bid

    for f in fixed:
        add(*f)
    heights = (6.6, 9.5, 9.5, 12.6, 12.6, 15.7)
    # outer ring first (tall), then the rest in strips
    ring = np.zeros((nx, nz), bool)
    ring[:2, :] = ring[-2:, :] = True
    ring[:, :2] = ring[:, -2:] = True
    k = 0
    for x in range(0, nx, 6):
        add("anello_s%d" % k, x, min(nx - 1, x + 5), 0, 1, 15.7); add("anello_n%d" % k, x, min(nx - 1, x + 5), nz - 2, nz - 1, 15.7)
        k += 1
    for z in range(2, nz - 2, 6):
        add("anello_w%d" % k, 0, 1, z, min(nz - 3, z + 5), 15.7); add("anello_e%d" % k, nx - 2, nx - 1, z, min(nz - 3, z + 5), 15.7)
        k += 1
    # remaining built cells: split into rectangles by scanning x strips of the blocks
    free = ~open_ & ~taken
    ids = 0
    for z0 in range(0, nz):
        for x0 in range(0, nx):
            if not free[x0, z0]:
                continue
            h_seed = zlib.crc32(b"%d,%d" % (x0, z0))
            w = 4 + h_seed % 6
            x1 = x0
            while x1 + 1 < nx and free[x1 + 1, z0] and x1 - x0 + 1 < w:
                x1 += 1
            d = 5 + (h_seed >> 4) % 3
            z1 = z0
            while z1 + 1 < nz and z1 - z0 + 1 < d and free[x0:x1 + 1, z1 + 1].all():
                z1 += 1
            add("palazzina_%d" % ids, x0, x1, z0, z1, heights[(h_seed >> 8) % len(heights)])
            ids += 1
            free[x0:x1 + 1, z0:z1 + 1] = False
    # materials
    world.mat[:, :] = "marciapiede"
    world.mat[road] = "asfalto"
    world.mat[world.building_id >= 0] = "terrazza"
    world.mat[yard_x0:yard_x1 + 1, yard_z0:yard_z1 + 1] = "lastricato"
    for z in range(PASSAGE_Z[0], PASSAGE_Z[1] + 1):
        world.mat[PASSAGE_X, z] = "lastricato"
    bid = int(world.building_id[25, 25])
    x0, z0 = 25, 25
    roof = G + H0 + H1 + H2
    world.floor[world.building_id == bid] = roof
    world.buildings[bid]["roof_m"] = roof / 512.0
    world.casa = dict(bid=bid, x0=x0, z0=z0, G=G, ROOF=roof)
    world.cortile = dict(cells=[(x, z) for x in range(yard_x0, yard_x1 + 1) for z in range(yard_z0, yard_z1 + 1)])
    street_fronts(world, G)


# The courtyard inside the block south of the street (open on the satellite view, x 37-48, z 5-10), reached
# through an archway cut in the building at x = PASSAGE_X; an iron gate on the pavement side, opened by
# the shutter winch with the crank Lara finds in the house.
PASSAGE_X = 43
PASSAGE_Z = (11, 16)
YARD = (37, 48, 5, 10)


def courtyard(world, street):
    for z in range(PASSAGE_Z[0], PASSAGE_Z[1] + 1):
        world.building_id[PASSAGE_X, z] = -1
    x0, x1, z0, z1 = YARD
    cells = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if world.building_id[x, z] < 0]
    cells += [(PASSAGE_X, z) for z in range(PASSAGE_Z[0], PASSAGE_Z[1] + 2)]
    K.flatten(world, cells, h=street, mat="lastricato")
    world.cortile = dict(cells=cells)


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
    dict(name="bianco", side="-z", x=(3, 12), h=6.9, lato="fac_lato_bianco",
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


def storey_h(c, f):
    return c["G"] + (0, H0, H0 + H1)[f], (H0, H1, H2)[f]


def sramp(it, c, col_row, rise_x, lo):
    """One-sector ramp, 2 clicks (1 m) over 2 m: walkable (TEN slides only above 36 degrees). Rises toward
    +x (rise_x > 0) or -x from `lo` (room-relative). The floor face is invisible: the marble flight static
    (SCALA_RAMPA) is what shows; the plastered sides stay."""
    wx, wz = cell(c, *col_row)
    s = it.room.sectors[wx - it.room.x][wz - it.room.z]
    hi = lo + 2 * CLICK
    s.floor = [lo, hi, hi, lo] if rise_x > 0 else [hi, lo, lo, hi]     # corners XnZp, XpZp, XpZn, XnZn
    s.set_invisible(prj2.F_FLOOR)
    s.set_invisible(prj2.F_FLOOR_TRI2)


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
    for a, b, ca, cb_, kind in DOORS:
        wa, wb = cell(c, *ca), cell(c, *cb_)
        w = wa[1] if wa[0] != wb[0] else wa[0]
        width = kind if isinstance(kind, int) and not isinstance(kind, bool) else 1
        k.link_wall(R[a], R[b], span=(w, w + width - 1))
    # The stair (see A1 ... WELL): ground floor all sector ramps and a raised landing, first floor A1 only.
    I0, D1, G2 = R["INGRESSO"], R["DISIMPEGNO"], R["GALLERIA"]
    sramp(I0, c, A1, +1, 0)
    sramp(I0, c, A2, +1, 2 * CLICK)
    for p in LAND:
        wx, wz = cell(c, *p)
        I0.room.sectors[wx - I0.room.x][wz - I0.room.z].floor = [4 * CLICK] * 4
    sramp(I0, c, B, -1, 4 * CLICK)
    sramp(D1, c, A1, +1, 0)
    well = [cell(c, *p) for p in WELL]
    k.link_vertical(I0, D1, well)
    k.link_vertical(D1, G2, well)
    hx, hz = cell(c, *HATCH)
    roof_room = k.room_at(hx, hz)
    k.link_vertical(R["RIPOSTIGLIO"], roof_room, [(hx, hz)])
    k.climb(hx, hz, "-x", room=R["RIPOSTIGLIO"].room)
    return R, roof_room


def stair(ctx, R):
    """Marble flights, landings, the TEN bridges of the first-floor flights, railings and the well's walls."""
    k, c = ctx.kit, ctx.world.casa

    def P(name, cr, rot, h, room, dx=0.5, dz=0.5):
        k.prop(name, c["x0"] + cr[0] + dx, c["z0"] + cr[1] + dz, rot=rot, h=h, room=room)

    for f, it in ((0, R["INGRESSO"]), (1, R["DISIMPEGNO"])):
        y = storey_h(c, f)[0]
        rm = it.room
        P("SCALA_RAMPA", A1, 0.0, y + 2 * CLICK, rm)
        if f == 0:
            P("SCALA_RAMPA", A2, 0.0, y + 4 * CLICK, rm)
            P("SCALA_RAMPA", B, 180.0, y + 6 * CLICK, rm)
            for p in LAND:
                P("SCALA_PIANEROTTOLO", p, 0.0, y + 4 * CLICK, rm)
        else:
            # over the ground-floor well: BRIDGE_TILT2 at rotation 0 rises toward +x, its box top (= the
            # item's y) is the high end; at 180 it rises toward -x. BRIDGE_FLAT: box top = the landing.
            k.place(K.BRIDGE_TILT2, *cell(c, *A2), room=rm, h=y + 4 * CLICK, rot=0.0, name="scala_rampa_a2")
            for i, p in enumerate(LAND):
                k.place(K.BRIDGE_FLAT, *cell(c, *p), room=rm, h=y + 4 * CLICK, name="scala_pianerottolo_%d" % (i + 1))
            k.place(K.BRIDGE_TILT2, *cell(c, *B), room=rm, h=y + 6 * CLICK, rot=180.0, name="scala_rampa_b")
            # the well's north side, under the floating flight and landing, walled (and blocking)
            P("SCALA_PANNELLO_RAMPA", A2, 0.0, y, rm, dz=1.025)
            P("SCALA_PANNELLO", LAND[1], 0.0, y, rm, dz=1.025)
        P("SCALA_RINGHIERA", A1, 0.0, y + CLICK, rm, dz=1.0)          # A1, north side
        P("SCALA_RINGHIERA", A1, 0.0, y + CLICK, rm, dz=0.0)          # A1, south side
        P("SCALA_RINGHIERA", A2, 0.0, y + 3 * CLICK, rm, dz=1.0)      # A2, north side
        P("SCALA_RINGHIERA", B, 180.0, y + 5 * CLICK, rm, dz=1.0)     # B, between the two flights
        P("CASA_CORRIMANO", LAND[1], 0.0, y + 4 * CLICK, rm, dz=1.0)  # landing, north side
    g, y2 = R["GALLERIA"].room, storey_h(c, 2)[0]
    P("CASA_CORRIMANO", (4, 1), 90.0, y2, g, dx=0.0, dz=0.5)
    P("CASA_CORRIMANO", (4, 1), 0.0, y2, g, dz=1.0)
    P("CASA_CORRIMANO", (5, 1), 0.0, y2, g, dz=1.0)


# Furniture: (model, x, z in house-local METRES, rot, room). Rotation 0: the front faces +x; 90: -z; 180: -x;
# 270: +z (Tomb Editor).
FURNITURE = [
    # ground floor
    ("CASA_PORTONE_INT", 5.0, 0.0, 270.0, "INGRESSO"), ("CASA_SCAFFALE", 4.2, 3.0, 0.0, "INGRESSO"),
    ("CASA_SCAFFALE", 0.2, 1.6, 0.0, "DISPENSA"), ("CASA_SCAFFALE", 0.2, 3.8, 0.0, "DISPENSA"),
    ("CASA_SCAFFALE", 2.0, 5.8, 90.0, "DISPENSA"),
    ("CASA_TAVOLO", 14.6, 4.6, 0.0, "LAB"), ("CASA_SCAFFALE", 15.8, 1.5, 180.0, "LAB"),
    ("CASA_SEDIA_ROVESCIATA", 13.0, 1.2, 120.0, "LAB"),
    ("CASA_SCAFFALE", 2.0, 9.8, 90.0, "CANTINA"), ("CASA_SCAFFALE", 5.0, 9.8, 90.0, "CANTINA"),
    ("CASA_SCAFFALE", 11.0, 9.8, 90.0, "CANTINA"), ("CASA_SCAFFALE", 14.0, 9.8, 90.0, "CANTINA"),
    ("CASA_SEDIA_ROVESCIATA", 9.0, 7.5, 40.0, "CANTINA"),
    # first floor
    ("CASA_WC", 0.3, 1.0, 0.0, "WC"),
    ("CASA_LAVATRICE", 3.65, 2.7, 180.0, "LAVANDERIA"), ("CASA_LAVATRICE", 3.65, 3.4, 180.0, "LAVANDERIA"),
    ("CASA_SCAFFALE", 2.0, 5.8, 90.0, "LAVANDERIA"),
    ("CASA_QUADRO", 4.02, 2.0, 0.0, "DISIMPEGNO"),
    ("CASA_CUCINA", 15.7, 2.4, 180.0, "CUCINA"), ("CASA_FRIGO", 15.65, 4.6, 180.0, "CUCINA"),
    ("CASA_TAVOLO", 13.5, 2.2, 0.0, "CUCINA"),
    ("CASA_DIVANO", 0.5, 8.0, 0.0, "SOGGIORNO"), ("CASA_TAVOLINO", 2.1, 8.0, 0.0, "SOGGIORNO"),
    ("CASA_MOBILE_TV", 3.9, 8.0, 180.0, "SOGGIORNO"), ("CASA_LIBRERIA", 6.0, 9.8, 90.0, "SOGGIORNO"),
    ("CASA_LIBRERIA", 8.2, 9.8, 90.0, "SOGGIORNO"), ("CASA_TAVOLO", 11.0, 8.2, 90.0, "SOGGIORNO"),
    ("CASA_SEDIA_ROVESCIATA", 8.6, 8.6, 30.0, "SOGGIORNO"), ("CASA_QUADRO", 15.98, 8.0, 180.0, "SOGGIORNO"),
    # second floor
    ("CASA_BAGNO", 0.4, 3.2, 0.0, "BAGNO"),
    ("CASA_LIBRERIA", 4.2, 1.0, 0.0, "GALLERIA"),
    ("CASA_LETTO", 3.0, 8.95, 90.0, "CAMERA"), ("CASA_COMODINO", 1.75, 9.7, 0.0, "CAMERA"),
    ("CASA_COMODINO", 4.25, 9.7, 0.0, "CAMERA"), ("CASA_ARMADIO", 5.7, 8.0, 180.0, "CAMERA"),
    ("CASA_QUADRO", 0.02, 8.0, 0.0, "CAMERA"),
    ("SCALA_PIOLI", 6.0, 9.0, 0.0, "RIPOSTIGLIO"), ("CASA_ARMADIO", 9.7, 7.6, 180.0, "RIPOSTIGLIO"),
    ("CASA_SCAFFALE", 9.0, 9.8, 90.0, "RIPOSTIGLIO"),
    ("CASA_LETTINO", 15.0, 8.95, 90.0, "CAMERETTA1"), ("CASA_SCRIVANIA", 10.35, 8.5, 0.0, "CAMERETTA1"),
    ("CASA_ARMADIO", 13.0, 6.3, 270.0, "CAMERETTA1"),
    ("CASA_LETTINO", 15.0, 4.6, 180.0, "CAMERETTA2"), ("CASA_SCRIVANIA", 12.35, 2.0, 0.0, "CAMERETTA2"),
    ("CASA_ARMADIO", 15.7, 1.8, 180.0, "CAMERETTA2"),
]
# Windows from inside, where the outside has them: the street front (facade columns with a window on that
# storey; col 2 is the portone, col 5 is blind, col 4 is behind the stair on the lower floors) and, on the
# second floor only, the back, which rises above the neighbour's roof (6.5 m).
WINDOWS = {0: [(0, "S"), (1, "S"), (3, "S"), (6, "S"), (7, "S")],
           1: [(0, "S"), (1, "S"), (3, "S"), (6, "S"), (7, "S")],
           2: [(0, "S"), (1, "S"), (3, "S"), (4, "S"), (6, "S"), (7, "S"), (0, "N"), (6, "N")]}


def house_dressing(ctx, R):
    k, c = ctx.kit, ctx.world.casa
    for name, x, z, rot, rn in FURNITURE:
        it = R[rn]
        k.prop(name, c["x0"] + x / 2.0, c["z0"] + z / 2.0, rot=rot, h=it.floor_h, room=it.room)
    ctx.lua.kicks = []
    for a, b, ca, cb_, kind in DOORS:
        if not kind or (isinstance(kind, int) and not isinstance(kind, bool)):
            continue
        ia, ib = R[a], R[b]
        ra, rb = ia.room, ib.room
        if kind == "chiave":
            model = "CASA_VANO_RIPOSTIGLIO"
        else:
            model = "CASA_PORTA_ALTA" if ia.storey == 2 else "CASA_PORTA"
        if kind is True:
            # a real door in every doorway (Trinity's modern doors, DOOR_TYPE5-8): Action in front of it, from
            # either side. The item stands in room a, its leaf on the edge towards room b.
            dx, dz = cb_[0] - ca[0], cb_[1] - ca[1]
            yaw = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[(dx, dz)]
            name = "porta_%s_%s" % (a.lower(), b.lower())
            k.place(854 + len(ctx.lua.kicks) % 4, c["x0"] + ca[0], c["z0"] + ca[1], room=ra, rot=float((yaw + 180) % 360), name=name)
            ctx.lua.kick_door(name, both=True)
            ctx.lua.kicks.append(name)
        if ca[0] != cb_[0]:
            xb = max(ra.x, rb.x) + 1
            k.prop(model, xb, c["z0"] + ca[1] + 0.5, rot=0.0, h=ia.floor_h, room=ra)
        else:
            zb = max(ra.z, rb.z) + 1
            k.prop(model, c["x0"] + ca[0] + 0.5, zb, rot=90.0, h=ia.floor_h, room=ra)
    for name, (f, (c0, c1), (r0, r1), _) in ROOMS.items():
        it = R[name]
        for col, side in WINDOWS[f]:
            if not c0 <= col <= c1:
                continue
            if side == "S" and r0 == 0:
                model = "CASA_PORTAFINESTRA" if f == 1 else "CASA_FINESTRA"
                k.prop(model, c["x0"] + col + 0.5, c["z0"], rot=270.0, h=it.floor_h, room=it.room)
            elif side == "N" and r1 == H_ROWS - 1:
                k.prop("CASA_FINESTRA", c["x0"] + col + 0.5, c["z0"] + H_ROWS, rot=90.0, h=it.floor_h, room=it.room)
        # one warm ceiling lamp per room, a little off-centre
        room = it.room
        h = (H0, H1, H2)[f] - 300
        pos = (((c0 + c1 + 1) / 2.0 + c["x0"] - room.x) * 1024, h, ((r0 + r1 + 1) / 2.0 + c["z0"] - room.z) * 1024)
        ctx.level.add_light(room, 0, pos, color=(1.0, 0.8, 0.55), intensity=0.75, inner=1.5, outer=6.0)
    stair(ctx, R)


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
    k.prop("ANTENNA_TV", c["x0"] + 4.6, c["z0"] + 4.6, rot=0.0, h=R)      # clear of the hatch at (3, 4)
    for f in w.fronts:
        if f["name"] in ("rosa", "arancio", "rosa_s"):
            xs = sorted(f["row"])
            x = xs[len(xs) // 2]
            z = f["row"][x] + (2 if f["side"] == "-z" else -2)
            k.prop("ANTENNA_TV", x + 1.5, z + 1.0, rot=0.0, h=f["top"])
    # warm street lights every 14 m on both pavements, and a cold moonlight
    room = k.room_at(c["x0"], c["z0"] - 3)
    # (v7.2: staggered, one pool of light every 7 m along the street, dimmer and shorter: the overlapping
    # lamps of v7.1 burned the facades white)
    for x in range(4, w.nx - 4, 7):
        for z, dx in ((c["z0"] - 1, 0), (c["z0"] - 8, 3)):
            xx = x + dx
            if 0 <= z < w.nz and xx < w.nx and w.building_id[xx, z] < 0:
                r = k.room_at(xx, z)
                pos = ((xx + 0.5 - r.x) * 1024, G + 2600 - r.y, (z + 0.5 - r.z) * 1024)
                ctx.level.add_light(r, 0, pos, color=(1.0, 0.84, 0.62), intensity=0.42, inner=0.8, outer=4.5)
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
    # Dusk: a dimmer, bluer ambient outside than the daytime levels, so the street lamps and the lit
    # windows carry the light.
    for rm in ctx.level.rooms:
        if rm.name.startswith("T_"):
            rm.ambient = (0.27, 0.28, 0.37)
    R, roof_room = house(ctx)
    house_dressing(ctx, R)
    street(ctx)
    fronts_dressing(ctx)

    def at(rn, col, row, dh=0):
        x, z = cell(c, col, row)
        return k.lua_pos(x, z, R[rn].floor_h + dh)

    def put(t, rn, col, row, **kw):
        return k.place(t, *cell(c, col, row), room=R[rn].room, **kw)

    put(K.LARA, "CAMERA", *START, rot=90.0, name="lara_start")
    put(K.FLARE_ITEM, "CAMERA", 1, 3)
    put(K.SMALLMEDI, "CUCINA", 6, 2)
    put(K.SHOTGUN_ITEM, "SOGGIORNO", 7, 4)
    put(K.SHOTGUN_AMMO1, "LAB", 7, 0)
    put(K.SMALLMEDI, "LAB", 7, 1)
    put(K.BADDY2, "SOGGIORNO", 4, 3, rot=270.0, name="ladro_primo")
    put(K.BADDY2, "LAB", 6, 1, rot=270.0, name="ladro_terra")
    put(K.BADDY1, "INGRESSO", 2, 1, rot=0.0, name="ladro_chiave")
    hx, hz = cell(c, *HATCH)
    # The hatch: a wooden lid hinged on its east edge, lying on the roof over the hole. Lara pushes it
    # open climbing the ladder (Lua zone near the top), then climbs out west onto the roof.
    k.prop("BOTOLA_LEGNO", hx + 1.0, hz + 0.5, rot=0.0, h=c["ROOF"], room=roof_room, lua_name="botola_legno")
    # The box-room (walk-in wardrobe) door: TEN door in the gallery, at 180 degrees it closes the sector
    # north of it (generic_doors.cpp), i.e. the doorway into RIPOSTIGLIO; the lock is on the wall beside it.
    put(K.DOOR_TYPE1, "GALLERIA", *DOOR, rot=180.0, name="porta_ripostiglio")
    put(K.KEY_HOLE1, "GALLERIA", *LOCK, rot=0.0, name="serratura_ripostiglio")
    # Down from the roof: the drainpipe on the street front, at the west end of the house.
    cx = c["x0"]
    k.climb(cx, c["z0"] - 1, "+z")
    k.prop("CASA_PLUVIALE", cx + 0.5, c["z0"] - 0.02, rot=0.0, h=c["G"])

    lua.start('CDV.Say("Oliveri, notte. Rumori al piano di sotto... qualcuno e\' entrato in casa.", 7)')
    lua.zone("primo", at("DISIMPEGNO", 2, 1), r=1200, dy=700, fn='CDV.Enable("ladro_primo")',
             text="Uno della banda della Volpe! Cercano il diario bizantino.")
    lua.zone("terra", at("INGRESSO", LAND[1][0], LAND[1][1], dh=4 * CLICK), r=1300, dy=700,
             fn='CDV.Enable("ladro_terra")\nCDV.Enable("ladro_chiave")')
    lua.drop("chiave", "ladro_chiave", "ID.KEY_ITEM1",
             "Il tombarolo aveva la chiave del ripostiglio. Il diario pero' non c'e': l'ha preso il loro capo.")
    lua.zone("portone", at("INGRESSO", 2, 0), r=1100, dy=700, once=True,
             text="Il portone e' sbarrato da fuori. Resta la botola del ripostiglio, sul tetto.")
    lua.add('CDV.Loop(function() CDV.KeyPrompt("serratura_ripostiglio", ID.KEY_ITEM1, "use_chiave_ripostiglio") end)')
    lua.use("chiave_ripostiglio", "ID.KEY_ITEM1", at("GALLERIA", *LOCK), r=900, dy=600, near="serratura_ripostiglio",
            text="La serratura scatta: il ripostiglio e' aperto.",
            fn='CDV.InsertKey("serratura_ripostiglio", "porta_ripostiglio")')
    lua.zone("ripostiglio_chiuso", at("GALLERIA", *LOCK), r=900, dy=700, once=False, secs=4,
             need='not CDV.Has(ID.KEY_ITEM1) and not CDV.Done("use_chiave_ripostiglio")',
             text="La cabina armadio e' chiusa a chiave: da li' si sale sul tetto. Uno dei ladri ha la chiave.")
    lua.zone("botola", at("RIPOSTIGLIO", *HATCH, dh=1100), r=600, dy=500, fn='CDV.Swing("botola_legno", "z", 75, 30)',
             text="Una spinta e la botola si apre.")
    lua.zone("tetto", k.lua_pos(hx - 1, hz, c["ROOF"]), r=1400, dy=300, secs=10,
             text="Dal tetto si vede il mare: una barca senza luci lascia la riva verso Marinello. Hanno il diario. "
                  "Sul davanti, verso la via, si scende lungo il pluviale.")

    # Via Amodeo: the look-out and two dogs; the thief runs off towards Via Stesicoro.
    zf = c["z0"] - 1
    k.place(K.DOBERMAN, *k.spot(c["x0"] + 10, zf - 4), name="cane1")
    k.place(K.DOBERMAN, *k.spot(c["x0"] + 12, zf - 5), name="cane2")
    k.place(K.BADDY1, 40, 6, rot=0.0, name="palo")
    G_ = c["G"]
    gz = PASSAGE_Z[1] + 1                       # pavement sector in front of the archway
    k.prop("CANCELLO", PASSAGE_X + 0.02, gz, rot=0.0, h=G_, lua_name="cancello_cortile")
    k.place(K.DOOR_TYPE1, PASSAGE_X, gz, rot=0.0, name="blocco_cancello", h=G_)
    # v8.1: the winch box faces the pavement (+z; at 180 degrees it sat inside the wall and could not be seen),
    # it is lit by its own wall lamp, and Action in front of it opens the inventory on the crank.
    k.prop("ARGANO", PASSAGE_X - 0.5, gz, rot=0.0, h=G_)
    k.prop("LAMPIONE_MURO", PASSAGE_X - 0.15, gz, rot=0.0, h=G_)
    k.prop("LAMPIONE_MURO", PASSAGE_X + 0.5, PASSAGE_Z[0], rot=0.0, h=G_)
    ra = k.room_at(PASSAGE_X - 1, gz)
    ctx.level.add_light(ra, 0, ((PASSAGE_X - 0.5 - ra.x) * 1024, G_ + 1500 - ra.y, (gz + 0.6 - ra.z) * 1024),
                        color=(1.0, 0.85, 0.62), intensity=0.6, inner=0.6, outer=3.0)
    put(K.PUZZLE_ITEM[9], "LAB", 6, 2)
    wx, wy, wz = k.lua_pos(PASSAGE_X - 1, gz, G_, dz=0.25)
    lua.use("argano", "ID.PUZZLE_ITEM9", (wx, wy, wz), r=1300, dy=900,
            text="La manovella entra nell'argano. Qualche giro, e il cancello del cortile si apre.",
            fn='CDV.Enable("blocco_cancello")\nCDV.Swing("cancello_cortile", "y", 90, 50)')
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, 1100, ID.PUZZLE_ITEM9, "use_argano") end)' % (wx, wy, wz))
    lua.zone("cancello_chiuso", k.lua_pos(PASSAGE_X, gz, G_), r=1300, dy=900, once=False, secs=6,
             need='not CDV.Done("use_argano") and not CDV.Has(ID.PUZZLE_ITEM9)',
             text="Il cancello del cortile e' chiuso. L'argano e' sul muro accanto, sotto la lampada, ma senza manovella non gira: "
                  "ce n'era una in casa, nel laboratorio.")
    lua.zone("cancello_manovella", k.lua_pos(PASSAGE_X, gz, G_), r=1300, dy=900, once=False, secs=5,
             need='not CDV.Done("use_argano") and CDV.Has(ID.PUZZLE_ITEM9)',
             text="L'argano del cancello e' sul muro accanto, sotto la lampada. Ho la manovella: davanti all'argano, Azione.")
    lua.zone("cortile", k.lua_pos(PASSAGE_X, PASSAGE_Z[0], G_), r=2500, dy=1500, fn='CDV.Enable("palo")',
             text="Eccolo, il palo della banda. Ha qualcosa che mi serve.")
    yx, yz = (YARD[0] + YARD[1]) // 2, YARD[2] + 1
    rr = k.room_at(yx, yz)
    ctx.level.add_light(rr, 0, ((PASSAGE_X + 0.5 - rr.x) * 1024, G_ + 2400 - rr.y, (PASSAGE_Z[0] - 0.3 - rr.z) * 1024),
                        color=(1.0, 0.78, 0.5), intensity=0.9, inner=2.0, outer=8.0)
    k.prop("CASSONETTI", YARD[1] - 0.6, YARD[2] + 3.5, rot=90.0, h=G_)
    k.prop("VASO_BIANCO_FIORI", YARD[0] + 0.5, YARD[3] + 0.4, rot=0.0, h=G_)
    k.prop("BICICLETTA", YARD[0] + 1.5, YARD[3] + 0.3, rot=90.0, h=G_)
    k.place(K.SHOTGUN_AMMO1, YARD[0] + 1, YARD[2] + 1)
    lua.secret(1, k.lua_pos(YARD[1], YARD[2], G_), r=700, give="ID.SMALLMEDI_ITEM",
               text="Hai trovato una Stella dei Dioscuri, dietro i bidoni del cortile!")
    lua.secret(2, k.lua_pos(c["x0"] + 19, c["z0"] + 3, c["ROOF"]), r=800, give="ID.SHOTGUN_AMMO1_ITEM",
               text="Hai trovato una Stella dei Dioscuri sui tetti dei vicini!")
    k.place(K.SMALLMEDI, *k.spot(c["x0"] + 14, zf - 1))
    street_c = k.spot(c["x0"], zf - 2)
    lua.zone("via", k.lua_pos(*street_c, ctx.ground(*street_c)), r=4000, dy=6000,
             fn='CDV.Enable("cane1")\nCDV.Enable("cane2")\nCDV.Enable("palo")',
             text="I cani della banda! E il palo e' scappato nel cortile, dietro il cancello.")
    ex, ez = (STREETS_Z[0][0] + STREETS_Z[0][1]) // 2, (STREETS_X[0][0] + STREETS_X[0][1]) // 2   # Stesicoro crossing
    lua.zone("fine", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2600, dy=4000,
             need='CDV.Dead("palo")', fn="CDV.End(2, 1)",
             text="Il palo e' a terra, ma la barca e' gia' al largo. All'alba, a Marinello.")
    lua.zone("fine_no", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2600, dy=4000, once=False, secs=4,
             need='not CDV.Dead("palo")', text="Prima devo prendere il palo della banda: e' nel cortile dietro il cancello.")
    lua.secret(0, at("CANTINA", 7, 4), r=800)
    ctx.notes += [
        "LIVELLO 1 - OLIVERI, VIA GASPARE AMODEO",
        "1. Lara si sveglia in camera da letto, al secondo piano (razzi ai piedi del letto).",
        "2. Dalla galleria la scala a U scende al primo piano (un ladro nel soggiorno, medikit in cucina,",
        "   fucile in fondo al soggiorno) e al piano terra (due ladri). Il ladro dell'ingresso lascia la",
        "   Chiave del ripostiglio. Nel laboratorio la manovella dell'argano. Segreto 1: in fondo alla cantina.",
        "3. Si risale al secondo piano: la chiave va nella serratura sul muro della galleria, accanto alla",
        "   porta della cabina armadio (usare la chiave dall'inventario davanti alla serratura). La porta si apre.",
        "4. Nella cabina armadio si sale la scala a pioli: a meta' Lara spinge la botola, in cima esce sul tetto.",
        "5. Dalla terrazza, sul lato della via, ci si cala lungo il pluviale.",
        "6. In Via Amodeo due cani e il palo della banda. Fine del livello all'incrocio con Via Stesicoro.",
    ]
