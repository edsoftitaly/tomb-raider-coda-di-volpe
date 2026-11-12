"""Livello 1 - La maga dei laghetti, parte 2: il Lago Verde e la grotta di Donna Villa. GDD v3.

Beyond the west pass: the reed bed and the dry hollow of the Lago Verde, closed on the west by the cliff. Five
metres up the cliff, over the mud, a ledge with a swallow hole: the low way into the cave. A second sluice lets
the sea into the hollow (flipmap 2, inverted: the dry state is the base one), and Lara swims to the ledge.

Route: the salt keeper's hut (kick door, drawers: the key of the sluice cabin) -> the iron mast up to the
sluice gantry -> the Lago Verde fills -> swim to the ledge, drop into the swallow hole -> the wall of the
scratches (climb: the order of the song is written on it, bottom to top) -> the hall of the song (five shells)
-> the inner pool: the Astro di Castore wakes the spirit of Donna Villa, a fire wraith that dies only in water
-> the way out under the boulder -> daylight on the Coda di Volpe path.

New mechanics here (not in Livello 0): the fire wraith (TEN Wraith.cpp: WRAITH1 dies in a water room; the
script also ends it after 8 s of Lara in the pool), bats, a climbable wall.
"""
import math

import numpy as np

import kit as K
import prj2
import zona as Z
from kit import CLICK

VERDE = (11.5, 42.0, 5.5, 9.0)          # centre x, z, radii
FLIP2 = 2
NOTCH = [(6, 42), (6, 43)]              # the ledge, 0.125 m over the water
PIT = [(5, 42), (5, 43)]                # the swallow hole behind it
HUT = dict(rect=(16, 60, 20, 64), h=4.5, style="bianco", gaps=[(18, 60)], floor="m_cotto")
GANTRY = [(11, 57), (12, 57), (13, 57)]
POLE = (10, 57)
CANAL_X = 12
SONG = [3, 1, 4, 2, 5]                  # the altars, by number of holes, in the order of the scratches


# ------------------------------------------------------------------------------------------- terrain
def sculpt(H, cx, cz):
    """The hollow of the Lago Verde: 4.7 m deep against the west cliff, a walkable ramp from the east shore."""
    vx, vz, vrx, vrz = VERDE
    r2 = np.hypot((cx - vx) / vrx, (cz - vz) / vrz)
    taper = np.clip((1 - np.abs(cz - vz) / vrz) * 3.0, 0.12, 1.0)
    dv = np.minimum(4.7, 0.4 + 0.72 * np.clip(17.0 - cx, 0, None)) * taper
    H = np.where(r2 < 1.0, -dv, np.where(r2 < 1.3, np.minimum(H, 0.3 + (r2 - 1.0) * 2.0), H))
    return H, r2


def carve(world, land, wall, cols, noflip):
    """Forced cells, after the heightfield: the ledge and its hole, the canal, the yard, the gantry."""
    rock = Z.u(7.0)
    for x in range(2, 7):
        for z in range(39, 47):
            if (x, z) in NOTCH or (x, z) in PIT:
                land(world, x, z, 0.125, "m_roccia")
                world.floor[x, z] = 64
                world.floor_terrain[x, z] = 64
            else:
                land(world, x, z, max(world.floor[x, z].max() / 512.0, 7.0), "m_roccia")
                world.floor[x, z] = max(int(world.floor[x, z].max()), rock)
                world.floor_terrain[x, z] = world.floor[x, z]
    for x in (7, 8):
        for z in range(41, 45):
            world.water[x, z] = True
            world.lagoon[x, z] = True
            world.verde[x, z] = True
            world.floor[x, z] = 0
            world.floor_terrain[x, z] = 0
    world.depth[7:10, 40:46] = np.where(world.water[7:10, 40:46], 4.7, world.depth[7:10, 40:46])
    world.verde &= world.water
    # the canal from the sea to the hollow, the yard of the hut
    for z in range(51, 68):
        if not world.water[CANAL_X, z]:
            land(world, CANAL_X, z, 0.25, "m_fango")
            world.floor[CANAL_X, z] = 128
            world.floor_terrain[CANAL_X, z] = 128
    x0, z0, x1, z1 = HUT["rect"]
    for x in range(x0 - 1, x1 + 2):
        for z in range(z0 - 3, z1 + 2):
            land(world, x, z, 1.0, "m_selciato" if (x + z) % 3 else "m_terra")
    # the gantry of the sluice: 8 clicks over the foot of the mast
    land(world, POLE[0], POLE[1], 1.0, "m_terra")
    bid = len(world.buildings)
    world.buildings.append({"id": "chiusa2", "tags": {"building": "ruins"}, "sectors": 0, "ground_m": 1.0, "base_m": 1.0, "roof_m": 5.0})
    for (x, z) in GANTRY:
        wall(world, cols, bid, x, z, 1.0 + 4.0, "blocchi", top="m_tavole")


# ------------------------------------------------------------------------------------------- caves
def cave(k, name, plan, x0, z0, floor_h, height, wall="g_parete", floor="g_pav", ceil="g_soffitto",
         amb=(0.36, 0.37, 0.4), rough=320, seed=1, water=False):
    it = k.interior(name, plan, x0, z0, floor_h, height, floor, ceil, wall, water=water, ambient=amb, tags=("grotta",))
    if rough and not water:
        rm = it.room
        rng = np.random.default_rng(seed)
        n = rng.random((rm.nx + 1, rm.nz + 1))
        n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1) + np.roll(n, (1, 1), (0, 1))) / 4      # a little smoother
        c = height - (np.round(n * rough / 64) * 64).astype(int)
        for lx in range(1, rm.nx - 1):
            for lz in range(1, rm.nz - 1):
                s = rm.sectors[lx][lz]
                if s.wall:
                    continue
                s.ceil = [int(c[lx, lz + 1]), int(c[lx + 1, lz + 1]), int(c[lx + 1, lz]), int(c[lx, lz])]
                s.csplit = abs(s.ceil[1] - s.ceil[3]) <= abs(s.ceil[0] - s.ceil[2])
    return it


def stalactites(k, it, n, seed):
    rm = it.room
    rng = np.random.default_rng(seed)
    cells = [(lx, lz) for lx in range(1, rm.nx - 1) for lz in range(1, rm.nz - 1) if not rm.sectors[lx][lz].wall]
    for i in rng.choice(len(cells), size=min(n, len(cells)), replace=False):
        lx, lz = cells[i]
        s = rm.sectors[lx][lz]
        if min(s.ceil) - max(s.floor) < 1700:
            continue
        k.prop("STALATTITE", rm.x + lx + float(rng.uniform(0.2, 0.8)), rm.z + lz + float(rng.uniform(0.2, 0.8)),
               rot=float(rng.uniform(0, 360)), h=rm.y + min(s.ceil) + 40, room=rm, scale=float(rng.uniform(0.6, 1.1)))


def shape(k, it, protect=(), dome=3, talus=1):
    """Take the box out of a cave: where a corner touches rock the ceiling comes down (a vault) and the floor
    comes up (the foot of the wall). Run after the links and the objects, before the texturing.

    Left alone: corners at a portal (side or vertical), floors that are not one flat level around the corner
    (steps, ledges), cells holding a moveable or listed in `protect` (world cells).
    """
    rm = it.room
    nx, nz = rm.nx, rm.nz
    wall = np.array([[rm.sectors[x][z].wall for z in range(nz)] for x in range(nx)])
    border = np.zeros((nx, nz), dtype=bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    keep = np.zeros((nx, nz), dtype=bool)                 # cells whose geometry must not move
    keep |= border & ~wall                                # side portals
    for (wx, wz) in k.links:
        if 0 <= wx - rm.x < nx and 0 <= wz - rm.z < nz:
            keep[wx - rm.x, wz - rm.z] = True
    flat = np.zeros((nx, nz), dtype=bool)                 # cells whose floor must stay level
    for m in rm.meta:
        if m and m[0] == "moveable":
            flat[int(m[2][0] // 1024), int(m[2][2] // 1024)] = True
    for (wx, wz) in protect:
        flat[wx - rm.x, wz - rm.z] = True
    dc = np.zeros((nx + 1, nz + 1), dtype=int)
    df = np.zeros((nx + 1, nz + 1), dtype=int)
    for cx in range(1, nx):
        for cz in range(1, nz):
            cells = [(cx - 1, cz - 1), (cx, cz - 1), (cx - 1, cz), (cx, cz)]
            nw = sum(1 for c in cells if wall[c])
            if nw == 0 or any(keep[c] for c in cells):
                continue
            dc[cx, cz] = (dome + (1 if nw >= 2 else 0)) * CLICK
            opened = [c for c in cells if not wall[c]]
            levels = set()
            for (a, b) in opened:
                levels.update(rm.sectors[a][b].floor)
            if len(levels) == 1 and not any(flat[c] for c in opened):
                df[cx, cz] = (talus + (1 if nw >= 3 else 0)) * CLICK
    for lx in range(1, nx - 1):
        for lz in range(1, nz - 1):
            s = rm.sectors[lx][lz]
            if s.wall or keep[lx, lz]:
                continue
            corners = [(lx, lz + 1), (lx + 1, lz + 1), (lx + 1, lz), (lx, lz)]
            f = [s.floor[i] + df[c] for i, c in enumerate(corners)]
            c2 = [max(s.ceil[i] - dc[c], f[i] + 5 * CLICK) if dc[c] else s.ceil[i] for i, c in enumerate(corners)]
            s.floor, s.ceil = f, [min(a, b) for a, b in zip(c2, s.ceil)]
            s.fsplit = abs(f[1] - f[3]) <= abs(f[0] - f[2])
            s.csplit = abs(s.ceil[1] - s.ceil[3]) <= abs(s.ceil[0] - s.ceil[2])


def light(ctx, it, wx, wz, h, color, intensity=0.8, inner=1.0, outer=5.0):
    rm = it.room
    ctx.level.add_light(rm, 0, ((wx - rm.x) * 1024.0, float(h), (wz - rm.z) * 1024.0), color=color,
                        intensity=intensity, inner=inner, outer=outer)


# ------------------------------------------------------------------------------------------- content
def build(ctx, C):
    k, lua, w = ctx.kit, ctx.lua, ctx.world
    noflip = C.NOFLIP
    g = Z.u(1.0)

    def gh(x, z):
        return ctx.ground(x, z)

    def prop(name, x, z, rot=0.0, h=None, scale=1.0, room=None):
        k.prop(name, x, z, rot=rot, h=gh(int(x), int(z)) if h is None else h, scale=scale, room=room)

    def P(t, x, z, **kw):
        return k.place(t, x, z, **kw)

    def pos(x, z, dx=0.5, dz=0.5, h=None):
        return k.lua_pos(x, z, gh(x, z) if h is None else h, dx=dx, dz=dz)

    # --- arrival: the reed bed
    P(K.BADDY1, 19, 55, rot=180.0, name="t5")
    P(K.DOBERMAN, 15, 54, rot=90.0, name="c2")
    P(K.BADDY2, 19, 34, rot=0.0, name="t6")
    lua.zone("canneto", pos(21, 46), r=1700, dy=2500, need='CDV.Done("use_lucchetto")', secs=9,
             fn='CDV.Enable("t5")\nCDV.Enable("c2")\nCDV.Enable("t6")',
             text="Oltre il passo, il canneto. Il Lago Verde e' una conca di fango asciutto" if not noflip else
                  "Oltre il passo, il canneto e il Lago Verde. In fondo, nella rupe, una cengia a pelo d'acqua.")
    prop("TENDA", 20.4, 37.4, rot=110.0)
    prop("FALO", 19.2, 39.2)
    prop("CASSA_LEGNO", 20.6, 40.3, rot=14.0)
    P(K.SMALLMEDI, 20, 39)
    P(K.SHOTGUN_AMMO1, 21, 38)

    # --- the salt keeper's hut: the key of the sluice cabin in the drawers, the register that explains the hollow
    C.kick(ctx, "porta_casello", 18, 59, lara_yaw=0)
    P(K.SEARCH_DRAWERS, 18, 63, rot=0.0, name="cassetti_casello")
    P(K.PUZZLE_ITEM[4], 18, 63, name="chiave_casello")
    P(K.SHOTGUN_AMMO1, 17, 61)
    prop("BOTTE", 19.4, 61.5)
    prop("ANFORA", 17.4, 62.6, rot=70.0)
    k.prop("FALDA_TETTO", 18.5, 62.6, rot=0.0, h=g + Z.u(4.5) - 64)
    lua.zone("nota_casello", pos(18, 62), r=1300, dy=1200, secs=11,
             text="Il registro della salina: \\\"Aperta la chiusa grande, il mare riempie il Lago Verde fino alla cengia "
                  "della maga. Le donne ci salivano a nuoto, a portarle le conchiglie.\\\"")
    for name, x, z, rot in (("RETI", 15.5, 58.4, 30), ("BOTTE", 21.3, 59.5, 0), ("ANCORA", 15.6, 65.3, 140),
                            ("PALO_ORMEGGIO", 21.4, 64.5, 0), ("BARCHETTA_SPIAGGIA", 14.5, 62.0, 200)):
        prop(name, x, z, rot=float(rot))

    # --- the sluice gantry: the mast, the cabin, the wheel
    top = gh(*GANTRY[0])
    base = gh(*POLE)
    for i in range(3):
        P(K.POLEROPE, POLE[0], POLE[1], rot=90.0, h=base + i * 1024, name="albero%d" % i)
    prop("CHIUSA", CANAL_X + 0.5, 55.5, rot=0.0)
    k.prop("RUOTA_CHIUSA", 12.5, 57.6, rot=0.0, h=top)
    sp = k.lua_pos(12, 57, top)
    if noflip:
        lua.start('CDV.Flag("verde_pieno", true)')
        lua.use("chiusa2", "ID.PUZZLE_ITEM4", sp, r=1300, dy=900,
                text="La chiave apre il casello, il volante gira: la paratoia e' gia' alzata, il lago e' pieno.")
    else:
        lua.use("chiusa2", "ID.PUZZLE_ITEM4", sp, r=1300, dy=900,
                text="La chiave apre il casello, il volante gira. Il mare entra dal canale: il Lago Verde si riempie fino alla rupe.",
                fn='TEN.Flow.FlipMap(%d)\nCDV.Flag("verde_pieno", true)' % FLIP2)
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, 1100, ID.PUZZLE_ITEM4, "use_chiusa2") end)' % sp)
    lua.zone("chiusa2_senza", sp, r=1300, dy=900, once=False, secs=7, need='not CDV.Done("use_chiusa2") and not CDV.Has(ID.PUZZLE_ITEM4)',
             text="Il casello della chiusa grande, chiuso a chiave. Dietro la grata, il volante della paratoia.")
    lua.zone("albero", pos(POLE[0], POLE[1] - 1), r=1300, dy=1200, once=False, secs=7, need='not CDV.Done("use_chiusa2")',
             text="La chiusa grande: il casello e' lassu', sulla spalla di pietra. Un albero di ferro ci arriva: salta e arrampicati.")
    P(K.SMALLMEDI, 13, 57, h=top)

    # --- the hollow: wreck, amphorae, the third star; the ledge seen from below
    wr = ctx.water_room_at(11, 42)

    def bed(x, z):
        return k.floor_at(wr, x, z)

    for name, x, z, rot in (("RELITTO", 11.5, 45.5, 250), ("ANFORA", 9.4, 40.5, 30), ("ANFORA", 13.6, 38.4, 160), ("ANCORA", 12.5, 48.4, 20),
                            ("SCOGLIO", 14.5, 44.5, 0), ("SCOGLIO_GRANDE", 10.5, 36.6, 40), ("RETI", 9.5, 47.4, 0)):
        k.prop(name, x, z, rot=float(rot), h=bed(int(x), int(z)), room=wr)
    k.place(K.BIGMEDI, 10, 45, room=wr, h=bed(10, 45))
    lua.secret(3, k.lua_pos(11, 44, bed(11, 44)), r=1100, text="Nella stiva del relitto del Lago Verde: una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    if not noflip:
        lua.zone("cengia_sotto", k.lua_pos(8, 42, bed(8, 42)), r=2300, dy=1400, once=False, secs=8, need='not CDV.Flag("verde_pieno")',
                 text="Sopra il fango, a cinque metri, una cengia nella rupe e un buco nero dietro. Troppo in alto: qui ci voleva l'acqua.")
    for a in np.linspace(0.6, 2 * math.pi - 0.6, 26):
        x = VERDE[0] + math.cos(a) * (VERDE[2] + 1.0)
        z = VERDE[1] + math.sin(a) * (VERDE[3] + 1.0)
        xi, zi = int(x), int(z)
        if x > 12 and not w.water[xi, zi] and w.building_id[xi, zi] < 0 and w.floor[xi, zi].max() < 3 * 512 and xi != CANAL_X:
            k.prop("CANNE_FITTE" if int(a * 7) % 2 else "CANNE", x, z, rot=float(a * 57 % 360), h=gh(xi, zi), scale=1.1)

    grotta(ctx, C)
    ctx.notes += ["", "PARTE 2: IL LAGO VERDE E LA GROTTA DI DONNA VILLA", __doc__]


def grotta(ctx, C):
    k, lua = ctx.kit, ctx.lua
    L = ctx.level
    FL = -2560                                       # the low floor of the cave: 5 m under the lake

    # --- G1: the swallow hole. Lara drops 5 m from the ledge into a pool.
    g1 = cave(k, "G1_INGHIOTTITOIO", ["#...#", ".....", ".....", ".....", ".....", "#....", "##..#"], 2, 39, FL, 1792, seed=11)
    g1a = cave(k, "G1_ACQUA", ["..."] * 4, 4, 41, FL - 2048, 2048, wall="g_parete", floor="g_bagnato", water=True, amb=(0.2, 0.32, 0.36))
    k.water_surface(g1, g1a, K.rect(4, 41, 6, 44))
    troom = ctx.terrain_room_at(5, 42)
    k.link_vertical(g1, troom, PIT)
    alt = getattr(troom, "alt", None)
    if alt is not None:                              # the flooded twin of the terrain room has the same hole
        for (wx, wz) in PIT:
            s = alt.sectors[wx - alt.x][wz - alt.z]
            s.floor = list(troom.sectors[wx - troom.x][wz - troom.z].floor)
            s.set_invisible(prj2.F_FLOOR)
            s.set_invisible(prj2.F_FLOOR_TRI2)
        L.add_portal(alt, (PIT[0][0] - alt.x, PIT[0][1] - alt.z, PIT[-1][0] - alt.x, PIT[-1][1] - alt.z), prj2.P_FLOOR, g1.room)
    light(ctx, g1, 5.5, 43.0, 1900, (0.62, 0.78, 1.0), 1.1, 1.5, 6.0)
    k.prop("STALAGMITE", 2.6, 44.5, h=FL, room=g1.room)
    k.prop("STALAGMITE", 2.5, 41.5, rot=80.0, h=FL, room=g1.room, scale=0.8)
    lua.zone("cengia", k.lua_pos(6, 42, 64), r=1200, dy=700, secs=8,
             text="La cengia della maga. Dietro, un inghiottitoio: si sente l'acqua, in basso. Da qui non si torna indietro.")
    lua.zone("g1", k.lua_pos(3, 42, FL), r=1500, dy=900, secs=8,
             text="Sotto la rupe. L'aria e' fredda e sa di sale. Sulle pareti, lunghi graffi paralleli: come dita.")

    # --- G2: the wall of the scratches. A 6 m climb; the order of the song is on it, bottom to top.
    g2 = cave(k, "G2_GRAFFI", ["##..##", "#....#", "......", "......", "......", "......", "......", "#....#", "##..##"],
              2, 30, FL, 4608, seed=12, rough=448)
    up = FL + 3072                                   # the upper gallery: + 512
    for x in range(2, 8):
        for z in range(30, 34):
            s = g2.sector(x, z)
            if not s.wall:
                s.floor = [3072] * 4
    g2.step_col = "g_graffi"
    k.link_wall(g2, g1, span=(4, 5))
    for x in range(3, 7):
        k.climb(x, 34, "-z", room=g2.room)
    light(ctx, g2, 4.5, 36.0, 1300, (1.0, 0.8, 0.55), 0.6, 1.0, 5.0)
    light(ctx, g2, 5.0, 32.0, 3072 + 1100, (0.6, 0.72, 1.0), 0.6, 1.0, 5.0)
    k.prop("BRACIERE", 2.5, 36.5, h=FL, room=g2.room)
    k.prop("STALAGMITE", 7.4, 36.5, h=FL, room=g2.room)
    k.place(K.BAT, 3, 32, room=g2.room, h=up + 1100, name="pip_g1")
    k.place(K.BAT, 6, 32, room=g2.room, h=up + 1100, name="pip_g2")
    words = {1: "UN solo graffio", 2: "DUE graffi", 3: "TRE graffi", 4: "QUATTRO graffi", 5: "CINQUE graffi"}
    for i, n in enumerate(SONG):
        lua.zone("graffi_%d" % i, k.lua_pos(4, 34, FL + 100 + i * 614, dx=1.0, dz=0.2), r=1700, dy=300, once=False, secs=4,
                 text="%s: %s." % (("In basso", "Piu' su", "A meta' parete", "Quasi in cima", "In cima")[i], words[n]))
    lua.zone("graffi_base", k.lua_pos(4, 36, FL), r=1300, dy=600, secs=8,
             text="Una parete tutta graffiata, fino in alto: si puo' scalare. I graffi sono a gruppi, e ogni gruppo ne ha un numero diverso.")
    lua.zone("graffi_cima", k.lua_pos(4, 32, up, dx=1.0), r=1500, dy=500, secs=10, fn='CDV.Enable("pip_g1")\nCDV.Enable("pip_g2")',
             text="Dal basso verso l'alto: tre, uno, quattro, due, cinque. Sembra una melodia.")

    # --- G3: the hall of the song
    g3 = cave(k, "G3_CANTO", ["###..####", "##.....##", "#.......#", "........#", ".........", "........#", "#.......#", "##.....##", "#########"],
              1, 21, up, 2560, seed=13, rough=512, amb=(0.3, 0.29, 0.3))
    k.link_wall(g3, g2, span=(4, 5))
    altars = {1: (2, 27), 2: (8, 27), 3: (2, 23), 4: (8, 23), 5: (5, 22)}
    for n, (x, z) in altars.items():
        k.prop("ALTARE_CONCHIGLIA", x + 0.5, z + 0.5, rot=float(n * 72), h=up, room=g3.room)
        light(ctx, g3, x + 0.5, z + 0.5, 1500, (1.0, 0.86, 0.6), 0.45, 0.6, 3.0)
        lua.zone("altare_%d" % n, k.lua_pos(x, z, up), r=1150, dy=600, once=False, secs=5, need='not CDV.Flag("canto_ok")',
                 text="Un altare di roccia con %s e una conchiglia. (Azione: soffiarci dentro.)" % ("UN foro", "DUE fori", "TRE fori", "QUATTRO fori", "CINQUE fori")[n - 1])
    for i, (x, z) in enumerate(((3, 25), (7, 25), (4, 28), (6, 22))):
        k.place(K.BAT, x, z, room=g3.room, h=up + 1500, name="pip_c%d" % i)
    k.place(K.DOOR_TYPE1, 9, 25, room=g3.room, rot=270.0, name="porta_canto")
    pts = ", ".join("{%d, %d, %d, %d}" % (k.lua_pos(x, z, up) + (n,)) for n, (x, z) in altars.items())
    lua.add('''CDV.Loop(function()
    if CDV.Flag("canto_ok") then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) then return end
    if Lara:GetState() ~= 2 then return end
    local alt = { %s }
    local seq = { %s }
    for _, a in ipairs(alt) do
        if CDV.Near(a[1], a[2], a[3], 1150, 600) then
            local n = (CDV.Flag("canto_n") or 0) + 1
            if a[4] == seq[n] then
                CDV.Flag("canto_n", n)
                CDV.Track("cdv_conchiglia_" .. a[4])
                if n == #seq then
                    CDV.Flag("canto_ok", true)
                    CDV.Enable("porta_canto")
                    CDV.After(60, function() CDV.Track("cdv_canto_donna_villa") end)
                    CDV.Say("Le cinque note insieme: e' il canto con cui la maga chiamava i marinai. Nella roccia si apre un passaggio.", 8)
                else
                    CDV.Say("La conchiglia canta. (" .. n .. " di " .. #seq .. ")", 3)
                end
            else
                CDV.Flag("canto_n", 0)
                CDV.Track("cdv_conchiglia_stonata")
                local e = (CDV.Flag("canto_err") or 0) + 1
                CDV.Flag("canto_err", e)
                if e == 1 then CDV.Enable("pip_c0"); CDV.Enable("pip_c1") end
                if e == 2 then CDV.Enable("pip_c2"); CDV.Enable("pip_c3") end
                CDV.Say("Una nota stonata: l'eco si spegne e qualcosa si muove sul soffitto. Da capo. (L'ordine e' sulla parete dei graffi.)", 6)
            end
            return
        end
    end
end)''' % (pts, ", ".join(str(n) for n in SONG)))
    lua.zone("canto", k.lua_pos(5, 27, up), r=1500, dy=700, secs=9,
             text="Cinque altari, cinque conchiglie. Ognuno ha un numero diverso di fori nella roccia.")
    k.place(K.SMALLMEDI, 5, 25, room=g3.room)

    # --- G4: the inner pool of Donna Villa and the Astro di Castore
    F4 = -1024
    plan = [list(r) for r in ("#########.#", "###.......#", "##.........", "#..........", "...........", "...........",
                              "...........", "#..........", "##.........", "###.......#", "###########")]
    # rows: index 0 = z 30 ... index 10 = z 20; columns x 10..20. The balcony of the entrance and its steps.
    for z in (24, 25, 26):
        r = 30 - z
        plan[r][0], plan[r][1], plan[r][2], plan[r][3] = "6", "6", "4", "2"
    g4 = cave(k, "G4_LAGHETTO", ["".join(r) for r in plan], 10, 20, F4, 3584, seed=14, rough=640, amb=(0.24, 0.3, 0.33))
    k.link_wall(g3, g4, span=(25, 25))
    pool = K.rect(14, 23, 18, 27)
    g4a = cave(k, "G4_ACQUA", ["....."] * 5, 14, 23, F4 - 2048, 2048, floor="g_bagnato", water=True, amb=(0.16, 0.36, 0.38))
    k.water_surface(g4, g4a, pool)
    light(ctx, g4, 16.5, 25.5, 900, (0.4, 0.95, 0.85), 0.9, 2.0, 7.0)
    light(ctx, g4, 20.0, 25.5, 1400, (1.0, 0.82, 0.45), 1.0, 1.0, 4.5)
    k.prop("PIEDISTALLO", 20.5, 25.5, h=F4, room=g4.room, scale=0.8)
    k.place(K.PUZZLE_ITEM[7], 20, 25, room=g4.room, h=F4 + 410, ocb=K.OCB_PLINTH_LOW, dx=0.2, rot=90.0, name="astro_castore")
    k.place(K.WRAITH1, 20, 28, room=g4.room, h=F4 + 600, name="maga", invisible=True)
    for name, x, z, rot, sc in (("STALAGMITE", 12.5, 28.5, 0, 1.2), ("STALAGMITE", 13.4, 21.5, 90, 1.0), ("STALAGMITE", 19.5, 21.6, 30, 0.9),
                                ("BRACIERE", 19.5, 23.5, 0, 1.0), ("BRACIERE", 19.5, 27.5, 0, 1.0), ("ANFORA", 12.5, 22.4, 40, 1.0)):
        k.prop(name, x, z, rot=float(rot), h=F4, room=g4.room, scale=sc)
    k.place(K.DOOR_TYPE1, 19, 30, room=g4.room, rot=180.0, name="porta_uscita")
    k.place(K.BIGMEDI, 12, 28, room=g4.room)
    lua.zone("laghetto", k.lua_pos(11, 25, F4 + 1536), r=1300, dy=700, secs=9,
             text="Il laghetto di Donna Villa. Oltre l'acqua, su un piedistallo, una stella di bronzo: l'Astro di Castore.")
    x0, y0, z0 = k.lua_pos(14, 23, F4, dx=0, dz=0)
    x1, _, z1 = k.lua_pos(19, 28, F4, dx=0, dz=0)
    lua.add('''CDV.Loop(function()
    if CDV.Flag("maga_morta") then return end
    if not CDV.Flag("maga_sveglia") then
        if CDV.Has(ID.PUZZLE_ITEM7) then
            CDV.Flag("maga_sveglia", true)
            CDV.Enable("maga")
            CDV.Track("cdv_donna_villa_grido")
            CDV.Say("L'Astro e' tuo, e Donna Villa si sveglia. Le armi non le fanno niente: il fuoco muore solo nell'acqua. Tuffati!", 9)
        end
        return
    end
    local t = (CDV.Flag("maga_t") or 0) + 1
    CDV.Flag("maga_t", t)
    local p = Lara:GetPosition()
    local w = CDV.Flag("maga_w") or 0
    if p.x > %d and p.x < %d and p.z > %d and p.z < %d then w = w + 1 end
    CDV.Flag("maga_w", w)
    if (t > 90 and not CDV.Active("maga")) or w > 240 then
        CDV.Flag("maga_morta", true)
        CDV.Disable("maga")
        CDV.Enable("porta_uscita")
        CDV.Say("Lo spirito entra nell'acqua dietro di te e si spegne con un urlo. Nella parete di fondo si apre l'uscita.", 8)
    elseif t == 300 and w == 0 then
        CDV.Say("Nell'acqua! Il laghetto, al centro della sala.", 5)
    end
end)''' % (x0, x1, z0, z1))

    # --- G5: the way out under the boulder
    rows = []
    for z in range(46, 30, -1):                      # x 17..21
        rows.append({38: ".....", 42: ".....", 46: "#...#"}.get(z, "#...#"))
    g5 = cave(k, "G5_USCITA", rows, 17, 31, F4, 2304, seed=15, rough=256)
    k.link_wall(g4, g5, span=(19, 19))
    k.place(K.ROLLINGBALL, 19, 45, room=g5.room, rot=180.0, h=F4 + 512, name="masso_g")
    lua.zone("masso_g", k.lua_pos(19, 35, F4), r=900, dy=1200,
             fn='CDV.Enable("masso_g")\nlocal b = CDV.M("masso_g")\nif b ~= nil then b:SetItemFlags(-800, 1) end',
             text="Il soffitto cede: un masso! Nelle nicchie, ai lati!")
    k.place(K.SHOTGUN_AMMO1, 17, 42, room=g5.room)
    k.place(K.SMALLMEDI, 21, 38, room=g5.room)
    light(ctx, g5, 19.5, 33.0, 1200, (1.0, 0.8, 0.55), 0.5, 1.0, 4.0)
    light(ctx, g5, 19.5, 46.5, 1500, (1.0, 0.95, 0.82), 1.6, 2.0, 9.0)
    lua.zone("uscita", k.lua_pos(19, 45, F4), r=1200, dy=1500, need='CDV.Flag("maga_morta")', fn="CDV.End(3, 1)",
             text="Luce. La galleria sbuca in alto sulla rupe, sul sentiero Coda di Volpe. Sopra, le mura di Tindari.")
    altar_cells = [c for c in altars.values()]
    for i, rm in enumerate((g1, g2, g3, g4, g5)):
        shape(k, rm, protect=altar_cells if rm is g3 else ((20, 25), (19, 25)) if rm is g4 else ())
        rm.room.no_path = False
        stalactites(k, rm, (5, 9, 14, 18, 8)[i], 20 + i)
