"""Livello 1 - La maga dei laghetti, parte 1: la tonnara (alba). GDD v3.

A hand-sculpted bowl of 184 x 184 m: the sandbar of Marinello with the Mergolo della Tonnara in the middle,
the ruined tonnara on its east shore, the sea to the north and east (it runs into the dawn mist: no visible
edge), the cliff of Tindari to the south and west. One mechanism: the sluice drains the lake (flipmap).

Route: jetty -> the tonnara (three kick-door houses: shotgun, medikit, the block puzzle of the net store that
gives the crank) -> the sluice: the Mergolo drains -> on the dry bed two levers to pull within 20 s open the
seal chamber -> the Sigillo della tonnara opens the gate of the reed path at the west pass: end of part 1.

Only mechanics proven in Livello 0 (pickups, plinth pickup, kick door, pushable + plate + raising block,
twin levers, item on a device, climbable wall, drawers, swimming) plus the flipmap of the lake.
"""
import math
import sys

import numpy as np
from scipy import ndimage

import content_marinello2 as M2
import kit as K
import zona as Z
from kit import CLICK

FRAME = (38.1420, 15.0515, 0.0, (0.0, 0.0, 236.0, 236.0))   # 4 x 4 tiles: 46 sectors of open sea beyond the jetty
NOFLIP = False                   # fallback build without the flipmap: the Mergolo is dry from the start
G = 1.0                          # ground of the tonnara (m): 2 clicks
LAKE = (44.0, 46.0, 11.0, 8.0)   # centre x, z, radii
FLIP = 1
SEA_Z, SEA_X = 67.0, 75.0        # coast lines (sectors), wobbling
CLIFF_Z, CLIFF_X = 24.0, 6.5
PASS = (27, 28, 45, 46)          # the west pass: x0, x1, z0, z1


def smooth(seed, shape, sigma):
    n = ndimage.gaussian_filter(np.random.default_rng(seed).random(shape), sigma, mode="reflect")
    return (n - n.min()) / (n.max() - n.min())


def softmin(a, b, k=2.5):
    return -k * np.log(np.exp(-a / k) + np.exp(-b / k))


# Ruins: name -> outer rectangle (x0, z0, x1, z1), wall top above the ground (m), plaster style, door gaps
RUINS = {
    "rais": dict(rect=(62, 38, 67, 43), h=4.5, style="giallo", gaps=[(62, 40)], floor="m_cotto"),
    "reti": dict(rect=(62, 47, 70, 53), h=8.5, style="pietra", gaps=[(65, 47)], floor="m_terra"),
    "sigillo": dict(rect=(62, 54, 64, 56), h=7.0, style="blocchi", gaps=[(62, 55)], floor="m_cotto"),
    "guardiano": dict(rect=(67, 56, 71, 60), h=4.5, style="bianco", gaps=[(67, 58)], floor="m_cotto"),
}
TOWER = (70, 38, 72, 40)         # solid lookout, 9 m
LOFT = [(x, z) for x in (68, 69) for z in range(48, 53)]      # in the net store, 9 clicks above its floor


def prepare(world):
    P = Z.Painter(world, G)
    nx, nz = world.nx, world.nz
    cx, cz = np.meshgrid(np.arange(nx + 1, dtype=float), np.arange(nz + 1, dtype=float), indexing="ij")
    n1, n2 = smooth(1, (nx + 1,), 4), smooth(2, (nz + 1,), 4)
    n4, n5 = smooth(4, (nx + 1,), 3), smooth(5, (nz + 1,), 3)
    dune = smooth(6, (nx + 1, nz + 1), 3.2)
    rough = smooth(7, (nx + 1, nz + 1), 1.2)

    s = softmin(SEA_Z + 3.0 * (n1[:, None] - 0.5) - cz, SEA_X + 3.0 * (n2[None, :] - 0.5) - cx)   # > 0 inland
    c = softmin(cz - (CLIFF_Z + 4.0 * (n4[:, None] - 0.5)), cx - (CLIFF_X + 4.0 * (n5[None, :] - 0.5)), 2.0)
    # the west pass: two rock masses close the sandbar west of the lake, a 2-sector gap between them
    spur_s = 5.5 - np.hypot((cx - 27.5) / 1.0, (cz - 34.0) / 2.6)        # from the cliff up to z 44
    spur_n = 6.0 - np.hypot((cx - 27.5) / 1.0, (cz - 60.0) / 3.3)        # from the pass into the sea
    rockmass = np.maximum(spur_s, spur_n)
    in_pass = (cx >= 22) & (cx <= 33) & (cz >= PASS[2]) & (cz <= PASS[3] + 1)      # the corridor cut through the rocks

    H = np.where(s >= 0, np.minimum(0.14 + 0.11 * s, 1.0) + np.clip((s - 7) / 5, 0, 1) * (0.9 * dune - 0.1),
                 -np.minimum(0.25 + 0.22 * -s, 5.5))
    # the lake
    lx, lz, rx, rz = LAKE
    r = np.hypot((cx - lx) / rx, (cz - lz) / rz)
    H = np.where(r < 1.0, -(0.35 + 2.7 * (1 - r)), np.where(r < 1.4, np.minimum(H, 0.3 + (r - 1.0) * 2.0), H))
    # the tonnara terrace and the jetty
    vil = (cx >= 58) & (cx <= 74) & (cz >= 36) & (cz <= 61)
    H = np.where(vil, G, H)
    blend_v = ndimage.gaussian_filter(vil.astype(float), 1.2)
    H = np.where(~vil & (r >= 1.0) & (s > 0), H * (1 - blend_v) + G * blend_v, H)
    # cliff and rock masses: terraces of ~3 m, flat per sector (set below)
    cliff = 2.0 + 5.2 * np.clip(-c, 0, None) + 3.5 * rough
    # every rock step is at least 4.5 m (9 clicks): Lara grabs ledges up to 7 clicks, so nothing here is climbable
    H = np.where(c < 0, np.minimum(7.0 + np.floor(np.clip(cliff - 2.0, 0, None) / 4.5) * 4.5, 43.0), H)
    H = np.where((c >= 0) & (c < 3) & (r > 1.4), H + (3 - c) * 0.45, H)
    rm = np.where(rockmass > 0, 1.5 + 2.6 * np.clip(rockmass, 0, 4) + 2.0 * rough, 0)
    H = np.where((rockmass > 0) & ~in_pass, np.maximum(H, 7.0 + np.floor(rm / 4.5) * 4.5), H)
    H = np.where(in_pass, 1.0, H)
    H, r2 = M2.sculpt(H, cx, cz)                              # the hollow of the Lago Verde, west of the pass
    world.H_sculpt = H

    q = lambda v: np.round(v * 512 / 64).astype(int) * 64
    Hq = q(H)
    fl = np.stack([Hq[:-1, 1:], Hq[1:, 1:], Hq[1:, :-1], Hq[:-1, :-1]], axis=2)     # XnZp, XpZp, XpZn, XnZn
    mean = fl.mean(axis=2)
    cs = (c[:-1, :-1] + c[1:, 1:]) / 2
    ss = (s[:-1, :-1] + s[1:, 1:]) / 2
    rs = np.hypot((np.arange(nx)[:, None] + 0.5 - lx) / rx, (np.arange(nz)[None, :] + 0.5 - lz) / rz)
    rk = ((c < 0) | ((rockmass > 0) & ~in_pass)) & (r2 >= 1.02)      # per corner
    rock = rk[:-1, :-1] | rk[1:, :-1] | rk[:-1, 1:] | rk[1:, 1:]   # a sector with any rock corner is rock: no half steps
    flat = (np.round(fl.max(axis=2) / CLICK) * CLICK).astype(int)
    fl = np.where(rock[:, :, None], flat[:, :, None], fl)
    water = (mean < -0.15 * 512) & ~rock
    lake = water & (rs < 1.05)
    r2s = np.hypot((np.arange(nx)[:, None] + 0.5 - M2.VERDE[0]) / M2.VERDE[2], (np.arange(nz)[None, :] + 0.5 - M2.VERDE[1]) / M2.VERDE[3])
    verde = water & (r2s < 1.3)
    dry_bed = lake & NOFLIP
    water &= ~dry_bed
    lake &= ~dry_bed
    world.water[:, :] = water
    world.lagoon[:, :] = lake | verde
    world.verde = verde.copy()
    world.depth[:, :] = np.where(water, np.maximum(-mean / 512.0, 0.3), 0.0)
    fl = np.where(water[:, :, None], 0, np.where(dry_bed[:, :, None], fl, np.maximum(fl, 64)))
    world.floor[:, :, :] = fl
    world.floor_terrain[:, :, :] = fl
    assert not (water & ~verde)[1:31, 31:61].any(), "only the Lago Verde in its tile"
    assert not (water & ~lake)[30:62, 30:62].any(), "the sea must stay out of the lake tile"
    assert not lake[:32].any() and not lake[60:].any() and not lake[:, :32].any() and not lake[:, 60:].any()

    # materials
    spots = smooth(8, (nx, nz), 2.0)
    mat = np.full((nx, nz), "m_sabbia", dtype=object)
    mat[(ss < 1.1) & ~water] = "m_battigia"
    mat[(ss >= 1.6) & (ss < 6) & (spots > 0.62)] = "m_ciottoli"
    mat[(ss > 8) & (spots > 0.55) & (rs > 1.5)] = "m_macchia"
    mat[(cs < 4) & (cs >= 0)] = "m_macchia"
    mat[(rs < 1.42) & ~water] = "m_terra"
    mat[(r2s < 1.3) & ~water] = "m_terra"
    mat[dry_bed] = "m_fango"
    mat[rock] = "m_roccia"
    mat[rock & (spots > 0.6)] = "m_erba"
    mat[58:74, 36:61] = "m_selciato"
    mat[(spots > 0.7) & (np.arange(nx)[:, None] >= 58) & (np.arange(nx)[:, None] < 74)
        & (np.arange(nz)[None, :] >= 36) & (np.arange(nz)[None, :] < 61)] = "m_terra"
    world.mat[:, :] = mat

    # jetty: planks 0.9 m over the water, from the terrace out to sea
    for x in range(73, 81):
        for z in (49, 50):
            _land(world, x, z, 0.9, "m_tavole")
    # flat bed under the two levers of the lake (3 x 3 each)
    for (bx, bz) in LEVERS:
        world.depth[bx - 1:bx + 2, bz - 1:bz + 2] = 2.0
        if NOFLIP:
            world.floor[bx - 1:bx + 2, bz - 1:bz + 2] = -1024
            world.floor_terrain[bx - 1:bx + 2, bz - 1:bz + 2] = -1024

    # ruins
    cols = {}
    M2.carve(world, _land, _wall, cols, NOFLIP)
    for name, R in list(RUINS.items()) + [("casello", M2.HUT)]:
        x0, z0, x1, z1 = R["rect"]
        bid = len(world.buildings)
        world.buildings.append({"id": name, "tags": {"building": "ruins"}, "sectors": 0, "ground_m": G, "base_m": G, "roof_m": G + R["h"]})
        rng = np.random.default_rng(abs(hash(name)) % 1000)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                if not edge or (x, z) in R["gaps"]:
                    _land(world, x, z, G, R["floor"] if edge is False or (x, z) in R["gaps"] else "m_selciato")
                    continue
                corner = x in (x0, x1) and z in (z0, z1)
                h = R["h"] + (0.5 if corner else 0.0) - (rng.choice([0, 0, 0, 0.5]) if not corner else 0)
                _wall(world, cols, bid, x, z, G + max(h, 4.0), R["style"], window=(not corner and (x + z) % 2 == 0))
    # the loft of the net store and the lookout tower: part of the masonry
    bid = len(world.buildings)
    world.buildings.append({"id": "soppalco", "tags": {"building": "ruins"}, "sectors": 0, "ground_m": G, "base_m": G, "roof_m": G + 4.5})
    for (x, z) in LOFT:
        _wall(world, cols, bid, x, z, G + 4.5, "blocchi", top="m_tavole")      # 9 clicks: out of reach from the floor, the raising block (4) + a jump and grab of 5
    bid = len(world.buildings)
    world.buildings.append({"id": "torre", "tags": {"building": "ruins"}, "sectors": 0, "ground_m": G, "base_m": G, "roof_m": G + 9.0})
    x0, z0, x1, z1 = TOWER
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            _wall(world, cols, bid, x, z, G + 9.0, "pietra", window=(x == 71 or z == 39))
    world.facade_cols = cols
    world.rock_prefix = "rupe_faccia"
    world.flip = {} if NOFLIP else {(1, 1): FLIP, (0, 1): M2.FLIP2}
    world.flip_inverted = set() if NOFLIP else {(0, 1)}       # the Lago Verde starts dry and is flooded
    world.bed_mat = "m_fondale"
    world.dry_mat = "m_fango"
    world.ambient = (0.5, 0.51, 0.55)
    world.dry_ambient = (0.44, 0.44, 0.47)
    world.sun = dict(color=(1.0, 0.84, 0.66), intensity=0.5, rot_y=70.0, rot_x=28.0)


LEVERS = [(39, 46), (49, 46)]


def _land(world, x, z, h_m, mat):
    h = Z.u(h_m)
    world.floor[x, z] = h
    world.floor_terrain[x, z] = h
    world.water[x, z] = False
    world.lagoon[x, z] = False
    world.depth[x, z] = 0.0
    world.mat[x, z] = mat


def _wall(world, cols, bid, x, z, top_m, style, window=False, top="m_muro_cima"):
    _land(world, x, z, top_m, top)
    world.building_id[x, z] = bid
    for d in ("+x", "-x", "+z", "-z"):
        cols[(x, z, d)] = "fac_ton_%s%s" % (style, "_fin" if window and style != "blocchi" else "")


DECOR = {}


# ------------------------------------------------------------------------------------------- content
def build(ctx):
    k, lua, w = ctx.kit, ctx.lua, ctx.world
    ctx.decor_block = [(0, 0, w.nx, w.nz)]          # every prop is placed on purpose
    g = Z.u(G)
    rng = np.random.default_rng(11)

    def gh(x, z):
        return ctx.ground(x, z)

    def prop(name, x, z, rot=0.0, h=None, scale=1.0):
        k.prop(name, x, z, rot=rot, h=gh(int(x), int(z)) if h is None else h, scale=scale)

    def P(t, x, z, **kw):
        return k.place(t, x, z, **kw)

    def pos(x, z, dx=0.5, dz=0.5, h=None):
        return k.lua_pos(x, z, gh(x, z) if h is None else h, dx=dx, dz=dz)

    # --- start: the jetty
    P(K.LARA, 78, 49, rot=270.0, name="lara_start")
    P(K.LARA_START_POS, 78, 49, ocb=1)
    lua.start('CDV.Say("Alba a Marinello. La barca dei tombaroli e\' passata di qui: la vecchia tonnara non e\' deserta.", 8)')
    prop("GOZZO", 81.6, 50.0, rot=10.0, h=0)
    prop("PALO_ORMEGGIO", 80.5, 48.7)
    prop("PALO_ORMEGGIO", 76.5, 51.3)
    prop("RETI", 75.3, 49.6, rot=40.0)
    prop("CASSA_LEGNO", 74.4, 50.6, rot=12.0)

    # --- the tonnara: dressing
    for name, x, z, rot in (
            ("BOTTE", 60.6, 44.6, 0), ("BOTTE", 61.3, 45.3, 30), ("CASSA_LEGNO", 60.5, 37.6, 20), ("RETI", 59.6, 52.4, 100),
            ("ANCORA", 59.5, 41.5, 60), ("RETI", 66.5, 45.2, 10), ("BOTTE", 71.4, 46.4, 0), ("CASSA_LEGNO", 72.3, 53.5, 45),
            ("PALO_ORMEGGIO", 58.6, 49.0, 0), ("ANCORA", 72.6, 43.4, 200), ("TRAVI_CROLLATE", 64.5, 40.5, 20),
            ("TRAVI_CROLLATE", 69.0, 58.0, 110), ("BARCHETTA_SPIAGGIA", 59.4, 57.6, 70), ("RUDERE_ARCO", 60.0, 48.5, 90)):
        prop(name, x, z, rot=float(rot))
    # roofs still standing: one bay over the store, one over the rais' house, one over the keeper's
    for x, z, rot, top in ((64.0, 51.2, 0.0, 8.5), (66.0, 41.6, 180.0, 4.5), (69.5, 58.6, 90.0, 4.5)):
        k.prop("FALDA_TETTO", x, z, rot=rot, h=g + Z.u(top) - 64)

    # --- tombaroli: the look-out on the square and his dog; one in the store; two more when the lake drains
    P(K.BADDY1, 66, 45, rot=90.0, name="t1")
    P(K.DOBERMAN, 71, 53, rot=270.0, name="c1")
    lua.zone("piazzale", pos(73, 49), r=1800, dy=2000, fn='CDV.Enable("t1")\nCDV.Enable("c1")',
             text="Qualcuno di guardia. E un cane.")
    prop("TENDA", 60.5, 58.6, rot=20.0)
    prop("FALO", 62.4, 58.9)
    prop("CASSA_LEGNO", 59.0, 59.8, rot=5.0)
    P(K.FLARE_ITEM, 61, 60)

    # --- K1, the rais' house: shotgun on the table, the note that explains the lake
    kick(ctx, "porta_rais", 61, 40, lara_yaw=90)
    prop("TAVOLACCIO", 65.5, 40.5, rot=90.0)
    P(K.SHOTGUN_ITEM, 65, 40, h=g + 410, ocb=K.OCB_PLINTH_LOW, dx=0.2, rot=90.0, name="fucile")     # taken from the west edge
    P(K.SHOTGUN_AMMO1, 64, 42)
    P(K.SMALLMEDI, 63, 42)
    prop("BOTTE", 66.4, 42.4)
    prop("ANFORA", 63.5, 39.4, rot=40.0)
    lua.zone("nota_rais", pos(65, 40), r=1100, dy=1200, secs=10,
             text="Il registro del rais, 1911: \\\"Chiusa la paratoia, il Mergolo si riempie in una notte. La manovella "
                  "sta nel magazzino delle reti, sul soppalco. Il sigillo e' sotto chiave: le due leve sono rimaste sul fondo.\\\"")

    # --- K3, the keeper's house: drawers, ammo
    kick(ctx, "porta_guardiano", 66, 58, lara_yaw=90)
    P(K.SEARCH_DRAWERS, 70, 59, rot=0.0, name="cassetti_guardiano")      # against the north wall: Lara faces north
    P(K.SMALLMEDI, 70, 59, name="medi_cassetti")
    P(K.SHOTGUN_AMMO1, 69, 57)
    prop("CASSA_LEGNO", 68.5, 59.4, rot=8.0)

    # --- K2, the net store: push the crate onto the slab, the block rises beside the loft, the crank is up there
    kick(ctx, "porta_reti", 65, 46, lara_yaw=0)
    P(K.PUSHABLE, 66, 49, name="cassa_reti")
    prop("PIASTRA_PIETRA", 64.5, 51.5)
    P(K.RAISING_BLOCK1, 67, 50, name="blocco_soppalco")
    lua.add('''CDV.Loop(function()
    if CDV.Flag("piastra_reti") then return end
    local b = CDV.M("cassa_reti")
    if b == nil or not b:GetValid() then return end
    local p = b:GetPosition()
    if math.floor(p.x / 1024) == 64 and math.floor(p.z / 1024) == 51 then
        CDV.Flag("piastra_reti", true); CDV.Enable("blocco_soppalco")
        CDV.Say("La lastra cede sotto la cassa: dal pavimento sale un blocco, accanto al soppalco. Da li' si salta e ci si aggrappa.", 7)
    end
end)''')
    P(K.PUZZLE_ITEM[9], 69, 52, h=g + 9 * CLICK, name="manovella")
    P(K.BIGMEDI, 69, 48, h=g + 9 * CLICK)
    P(K.BADDY1, 68, 50, rot=270.0, h=g + 9 * CLICK, name="t2")
    lua.zone("agguato_reti", pos(65, 49), r=1400, dy=1500, fn='CDV.Enable("t2")', text="Dal soppalco! Un altro.")
    for name, x, z, rot in (("RETI", 63.6, 48.6, 0), ("RETI", 66.4, 52.4, 70), ("BOTTE", 63.4, 52.5, 0), ("CASSA_LEGNO", 67.4, 48.5, 30),
                            ("ANCORA", 65.5, 52.3, 100)):
        prop(name, x, z, rot=float(rot))
    lua.zone("indizio_reti", pos(65, 49), r=1500, dy=1500, once=False, secs=7, need='not CDV.Flag("piastra_reti")',
             text="Una lastra di pietra con un anello di ferro, nel pavimento. E una cassa che si puo' spingere.")

    # --- the sluice on the east shore of the Mergolo
    sx, sz = 57, 46
    prop("CHIUSA", sx + 0.5, sz + 0.5, rot=90.0)
    sp = pos(sx + 1, sz)
    lua.use("chiusa", "ID.PUZZLE_ITEM9", sp, r=1500, dy=1500,
            text="La manovella gira, la paratoia si alza." + ("" if NOFLIP else " Il Mergolo si svuota nel mare con un boato."),
            fn='%sCDV.Flag("lago_vuoto", true)\nCDV.After(120, function() CDV.Enable("t3"); CDV.Enable("t4"); '
               'CDV.Say("Il rumore li ha svegliati: ne arrivano altri dal canneto.", 6) end)' % ("" if NOFLIP else "TEN.Flow.FlipMap(%d)\n" % FLIP))
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, 1300, ID.PUZZLE_ITEM9, "use_chiusa") end)' % sp)
    lua.zone("chiusa_senza", sp, r=1500, dy=1500, once=False, secs=7, need='not CDV.Done("use_chiusa") and not CDV.Has(ID.PUZZLE_ITEM9)',
             text="La chiusa del Mergolo. La paratoia e' abbassata e manca la manovella dell'ingranaggio.")
    P(K.BADDY2, 31, 46, rot=90.0, name="t3")
    P(K.BADDY1, 32, 45, rot=90.0, name="t4")

    # --- the bed of the lake: wreck, anchors, amphorae, the two levers of the seal chamber
    wr = None if NOFLIP else ctx.water_room_at(44, 46)       # NOFLIP: the bed is plain terrain

    def bed(x, z):
        return gh(x, z) if NOFLIP else k.floor_at(wr, x, z)

    def bprop(name, x, z, rot=0.0):
        k.prop(name, x, z, rot=rot, h=bed(int(x), int(z)), room=wr)

    for name, x, z, rot in (("RELITTO", 44.5, 47.5, 30), ("ANCORA", 41.5, 43.5, 120), ("ANFORA", 46.4, 44.5, 10), ("ANFORA", 46.9, 45.1, 200),
                            ("ANFORA", 42.3, 49.4, 80), ("SCOGLIO", 50.5, 49.5, 0), ("SCOGLIO", 37.5, 44.4, 50), ("RETI", 47.5, 48.6, 0),
                            ("ANCORA", 51.4, 43.6, 300), ("SCOGLIO_GRANDE", 44.5, 41.6, 0)):
        bprop(name, x, z, float(rot))
    for i, (x, z) in enumerate(LEVERS):
        k.place(K.LEVER_SWITCH, x, z, room=wr, h=bed(x, z), rot=0.0, name="leva_fondo_%d" % i)
    k.place(K.SMALLMEDI, 45, 46, room=wr, h=bed(45, 46))
    k.place(K.SHOTGUN_AMMO1, 43, 48, room=wr, h=bed(43, 48))
    lua.add('CDV.TwinLevers("fondo", "leva_fondo_0", "leva_fondo_1", 600, '
            '"La leva scatta, una catena corre sotto il fango. Hai 20 secondi per l\'altra.", '
            '"Troppo tardi: la catena si e\' fermata. Hai 20 secondi da adesso per l\'altra leva.", '
            'function() CDV.Enable("porta_sigillo"); CDV.Say("Le due catene tirano insieme: nella tonnara si apre la camera del sigillo.", 7) end)')
    lua.zone("fondo", k.lua_pos(44, 46, bed(44, 46)), r=5200, dy=900, need='CDV.Flag("lago_vuoto")', secs=8,
             text="Il fondo del Mergolo: un relitto, anfore, e due leve di ferro incrostate, lontane una dall'altra.")

    # --- the seal chamber
    P(K.DOOR_TYPE1, 61, 55, rot=270.0, name="porta_sigillo")
    P(K.PUZZLE_ITEM[6], 63, 55, name="sigillo")
    lua.zone("sigillo_chiuso", pos(61, 55), r=1300, dy=1200, once=False, secs=7, need='not CDV.Flag("fondo_ok")',
             text="Una porta di ferro senza serratura. Due catene escono dal muro e scendono verso il lago.")

    # --- the west pass: the gate of the reed path
    P(K.DOOR_TYPE1, 28, 45, rot=90.0, name="cancello_canneto")
    prop("PALIZZATA", 28.5, 46.5, rot=90.0)
    gp = pos(29, 45)
    lua.use("lucchetto", "ID.PUZZLE_ITEM6", gp, r=1500, dy=1200,
            text="Il Sigillo entra nell'incavo del chiavistello: il cancello del canneto si apre.",
            fn='CDV.Enable("cancello_canneto")')
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, 1300, ID.PUZZLE_ITEM6, "use_lucchetto") end)' % gp)
    lua.zone("cancello_senza", gp, r=1500, dy=1200, once=False, secs=7, need='not CDV.Done("use_lucchetto") and not CDV.Has(ID.PUZZLE_ITEM6)',
             text="Il passo verso il canneto e il Lago Verde. Sul chiavistello c'e' un incavo rotondo, con il tonno della tonnara.")
    # --- the cave of Donna Villa: seen from below, out of reach
    zc = next(z for z in range(34, 10, -1) if gh(44, z) > 5 * 512)          # the first row of the cliff
    k.prop("SCALA_CORDA", 44.5, zc + 1.06, rot=0.0, h=g + Z.u(12.0))
    lua.zone("grotta_vista", pos(44, 30), r=2600, dy=3000, secs=8,
             text="In alto nella rupe, una bocca scura: la grotta di Donna Villa. La scala di corda e' spezzata: ci sara' un'altra via.")

    # --- secrets
    k.climb(71, 41, "-z")                       # the north face of the lookout is climbable
    P(K.SHOTGUN_AMMO1, 72, 40, h=g + Z.u(9.0))
    lua.secret(1, k.lua_pos(71, 39, g + Z.u(9.0)), r=1300, text="In cima alla torre di vedetta: una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    sw = ctx.water_room_at(79, 53)
    sh = k.floor_at(sw, 79, 53)
    k.prop("ANFORA", 79.5, 53.5, rot=120.0, h=sh, room=sw)
    lua.secret(2, k.lua_pos(79, 53, sh), r=1000, text="Sul fondo, sotto il pontile: una Stella dei Dioscuri!", give="ID.BIGMEDI_ITEM")

    M2.build(ctx, sys.modules[__name__])

    # --- nature: reeds round the lake and at the pass, boulders at the foot of the cliff, scrub, pines
    scatter(ctx, rng)

    # --- the sea has no edge: the current turns Lara back before the mist ends
    lua.add('''CDV.Loop(function()
    local p = Lara:GetPosition()
    local zmax, xmax = %d, %d
    if p.x < 34 * 1024 then zmax = 72 * 1024 end      -- nor round the rocks of the west pass
    if p.z > zmax or p.x > xmax then
        Lara:SetPosition(TEN.Vec3(math.min(p.x, xmax - 96), p.y, math.min(p.z, zmax - 96)))
        if not CDV.Flag("corrente_t") or CDV.Flag("corrente_t") <= 0 then
            CDV.Say("La corrente al largo e' troppo forte: meglio restare vicino alla riva.", 4)
            CDV.Flag("corrente_t", 240)
        end
    end
    if CDV.Flag("corrente_t") and CDV.Flag("corrente_t") > 0 then CDV.Flag("corrente_t", CDV.Flag("corrente_t") - 1) end
end)''' % (86 * 1024, 91 * 1024))

    for rm in ctx.level.rooms:
        if rm.name.startswith("T_"):
            rm.no_path = False
    ctx.notes += ["LIVELLO 1 - LA MAGA DEI LAGHETTI, PARTE 1: LA TONNARA", __doc__]


def kick(ctx, name, x, z, lara_yaw):
    """A kick door: the door item stands in the sector in front of the doorway, its leaf on the far edge."""
    ctx.kit.place(K.DOOR_TYPE1, x, z, rot=float((lara_yaw + 180) % 360), name=name)
    ctx.lua.kick_door(name)


def scatter(ctx, rng):
    k, w = ctx.kit, ctx.world
    lx, lz, rx, rz = LAKE
    taken = set()

    def free(x, z):
        xi, zi = int(x), int(z)
        return (0 < xi < w.nx - 1 and 0 < zi < w.nz - 1 and not w.water[xi, zi] and w.building_id[xi, zi] < 0
                and (w.floor[xi, zi].max() < 3 * 512 or high)
                and (xi, zi) not in taken and not (58 <= xi <= 73 and 36 <= zi <= 60) and (xi, zi) not in k.links)

    high = False

    def put(name, x, z, scale=1.0):
        if not free(x, z):
            return False
        k.prop(name, x, z, rot=float(rng.uniform(0, 360)), h=ctx.ground(int(x), int(z)), scale=scale)
        return True

    # reeds on the bank of the lake (not on the village side, where the sluice is) and across the west clearing
    for a in np.linspace(0, 2 * math.pi, 64, endpoint=False):
        if -0.9 < a < 0.9:
            continue
        for rr in (1.12, 1.26):
            x = lx + math.cos(a) * rx * rr + rng.uniform(-0.3, 0.3)
            z = lz + math.sin(a) * rz * rr + rng.uniform(-0.3, 0.3)
            put("CANNE_FITTE" if rng.random() < 0.5 else "CANNE", x, z, scale=float(rng.uniform(0.85, 1.2)))
    for _ in range(60):
        x, z = rng.uniform(17, 26), rng.uniform(30, 66)
        if abs(z - 46) > 1.6 and not (14 <= x <= 22 and 56 <= z <= 66) and not (18 <= x <= 22 and 33 <= z <= 41):
            put("CANNE_FITTE", x, z, scale=float(rng.uniform(0.9, 1.3)))
    # boulders: foot of the cliff, the shore, in the shallows
    H = w.floor.mean(axis=2)
    n = 0
    while n < 46:
        x, z = rng.uniform(4, 88), rng.uniform(4, 88)
        xi, zi = int(x), int(z)
        near_rock = (H[max(xi - 2, 0):xi + 3, max(zi - 2, 0):zi + 3] > 3 * 512).any()
        if w.mat[xi, zi] in ("m_macchia", "m_ciottoli", "m_battigia") and (near_rock or rng.random() < 0.25):
            if put("SCOGLIO_GRANDE" if rng.random() < 0.3 else "SCOGLIO", x, z, scale=float(rng.uniform(0.7, 1.5))):
                taken.add((xi, zi))
                n += 1
    # scrub and prickly pears on the dry ground, pines at the back
    for name, count, mats in (("ELICRISO_GRUPPO", 70, ("m_macchia", "m_sabbia")), ("FICO_INDIA_GRANDE", 14, ("m_macchia",)),
                              ("FICO_INDIA_PICCOLO", 18, ("m_macchia", "m_erba")), ("ASPARAGO_ROVO", 30, ("m_macchia", "m_erba")),
                              ("PINO_ALEPPO_INCLINATO", 9, ("m_macchia",)), ("PINO_ALEPPO_GIOVANE", 10, ("m_macchia", "m_erba"))):
        n = tries = 0
        high = name.startswith(("PINO", "ASPARAGO", "FICO_INDIA_PICCOLO"))
        while n < count and tries < 4000:
            tries += 1
            x, z = rng.uniform(4, 88), rng.uniform(4, 88)
            xi, zi = int(x), int(z)
            if w.mat[xi, zi] in mats and H[xi, zi] < 14 * 512 and not (PASS[0] - 1 <= xi <= PASS[1] + 1 and PASS[2] - 1 <= zi <= PASS[3] + 1):
                if put(name, x, z, scale=float(rng.uniform(0.85, 1.25))):
                    if name.startswith(("PINO", "FICO_INDIA_GRANDE")):
                        taken.add((xi, zi))
                    n += 1
