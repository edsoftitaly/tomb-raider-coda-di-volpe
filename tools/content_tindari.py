"""Livello 2 - Tindari. GDD v3.

Late afternoon on the plateau of Tyndaris, 24 m over a rocky shore: to the north and east the cliff (a fall is
death, as it should be), to the south and west the hill and the Greek walls. On the east side the terrace of
the sanctuary stands 10 m higher behind a retaining wall: the only way up is the stage building of the theatre,
three tiers of 4 m each. Under the stage is the old machine: three winches, each raises one block.

Route: the path from the cave -> the camp of the tombaroli on the decumanus -> winch 1 in the orchestra (stage)
-> the Roman house (kick door; the mosaic floor: only the dark caps of Castore, the mortal twin, hold) -> winch 2
(second tier) -> the undercroft of the basilica (stairs down, the rope over the gap) -> winch 3 (top) -> over the
scene to the terrace -> the crypt under the sanctuary (the two marble twins pushed on their stars) -> the well.

Mechanics from Livello 0: kick door, raising blocks, rope, pushables. New, scripted: the mosaic (damage by Lua on
a wrong tile), the winches (Action near them).
"""
import math
import sys

import numpy as np

import content_marinello as CM
import content_marinello2 as M2
import kit as K
import zona as Z
from kit import CLICK

FRAME = (38.1412, 15.0454, 0.0, (0.0, 0.0, 176.0, 176.0))    # 3 x 3 tiles
P, T = 24.0, 34.0                # plateau and sanctuary terrace (m)
ORCH = (54.5, 29.5)
STAGE_X = range(49, 60)
HOUSE = (20, 44, 32, 58)
MOSAIC_X, MOSAIC_Z = range(23, 30), range(51, 57)
SAFE = {51: {26}, 52: {26, 27, 28}, 53: {28}, 54: {24, 25, 26, 27, 28}, 55: {24}, 56: {24, 25, 26}}
BASILICA = (38, 46, 50, 54)
UPIT = [(40, 49), (40, 50), (40, 51)]
CPIT = [(65, 42), (66, 42), (67, 42)]
CHURCH = (63, 47, 69, 57)
BLOCKS = {"a": (54, 29), "b": (52, 30), "c": (56, 31)}


def prepare(world):
    nx, nz = world.nx, world.nz
    X = np.arange(nx)[:, None] + 0.5 + np.zeros((1, nz))
    Zg = np.arange(nz)[None, :] + 0.5 + np.zeros((nx, 1))
    wob = (CM.smooth(3, (nx, nz), 5.0) - 0.5) * 4.0
    spots = CM.smooth(8, (nx, nz), 2.0)
    Hs = np.full((nx, nz), P)
    c = CM.softmin(Zg - (12.5 + wob), X - (12.5 + wob))
    hill = c < 0
    Hs = np.where(hill, np.minimum(P + 4.5 * (1 + np.floor(-c / 1.3)), P + 31.5), Hs)
    d = CM.softmin((68.5 + wob * 0.4) - Zg, (74.5 + wob * 0.4) - X)
    shore = (d < 0) & (d > -7)
    sea = d <= -7
    Hs = np.where(shore, 1.0, Hs)
    Hs = np.where(sea, -np.minimum(0.4 + 0.35 * (-d - 7), 5.0), Hs)
    terrace = (X > 61) & (Zg > 30) & (d >= 0)
    Hs = np.where(terrace, T, Hs)
    # the theatre: orchestra 2 m under the plateau, four low rings, the stage building in three tiers of 4 m
    r = np.hypot(X - ORCH[0], Zg - ORCH[1])
    cavea = (Zg < 29) & (r < 7.2) & (X < 61) & ~hill
    Hs = np.where(cavea, np.minimum(P, P - 2.0 + 0.5 * np.ceil(np.clip(r - 3.2, 0, None))), Hs)
    front = (Zg > 29) & (Zg < 30) & (X > 49) & (X < 60)
    Hs = np.where(front, P - 2.0, Hs)
    scene = (X > 49) & (X < 60)
    for zi, h in ((30, P + 2.0), (31, P + 6.0), (32, T)):
        Hs = np.where(scene & (Zg > zi) & (Zg < zi + 1), h, Hs)
    par = ((X > 48) & (X < 49) | (X > 60) & (X < 61)) & (Zg > 30) & (Zg < 33)
    Hs = np.where(par, T, Hs)

    fl = (np.round(Hs * 512 / CLICK) * CLICK).astype(int)
    water = Hs < -0.1
    world.water[:, :] = water
    world.lagoon[:, :] = False
    world.depth[:, :] = np.where(water, np.maximum(-Hs, 0.3), 0.0)
    fl = np.where(water, 0, fl)
    world.floor[:, :, :] = fl[:, :, None]
    world.floor_terrain[:, :, :] = fl[:, :, None]
    world.building_id[:, :] = -1
    world.buildings[:] = []

    mat = np.full((nx, nz), "m_erba", dtype=object)
    mat[spots > 0.6] = "m_terra"
    mat[spots < 0.38] = "m_macchia"
    mat[hill] = "m_roccia"
    mat[hill & (spots > 0.58)] = "m_macchia"
    mat[shore] = "m_ciottoli"
    mat[terrace] = "m_erba"
    mat[terrace & (Zg > 36) & (Zg < 47) & (X > 62) & (X < 70)] = "t_lastre"
    mat[(Zg > 38) & (Zg < 41) & (X > 14) & (X < 61) & ~hill] = "t_lastre"
    mat[cavea | front] = "t_lastre_muschio"
    mat[(r < 3.2) & (Zg < 30)] = "m_terra"
    mat[scene & (Zg > 30) & (Zg < 33)] = "t_lastre"
    mat[par] = "t_lastre"
    world.mat[:, :] = mat

    cols = {}

    def face(x, z, col):
        for dd in ("+x", "-x", "+z", "-z"):
            cols[(x, z, dd)] = col

    for x in range(nx):
        for z in range(nz):
            if terrace[x, z]:
                face(x, z, "t_opera_muschio" if (x * 3 + z * 5) % 7 == 0 else "t_opera")
            elif cavea[x, z] or (scene[x, z] and 30 <= z <= 32) or par[x, z]:
                face(x, z, "t_opera")
    bid = 0
    world.buildings.append({"id": "ruderi", "tags": {"building": "ruins"}, "sectors": 0, "ground_m": P, "base_m": P, "roof_m": P + 6})

    def wall(x, z, top, col, topmat="m_muro_cima"):
        CM._land(world, x, z, top, topmat)
        world.building_id[x, z] = bid
        face(x, z, col)

    def floor(x, z, m, h=P):
        CM._land(world, x, z, h, m)

    # the Greek walls along the south side
    for x in range(14, 61):
        if not hill[x, 13]:
            wall(x, 13, P + (5.0 if x % 7 else 4.5), "t_opera_muschio")
    # the Roman house
    x0, z0, x1, z1 = HOUSE
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            solid = edge or z == 50 or (z > 50 and (x < MOSAIC_X[0] or x > MOSAIC_X[-1]))
            if (x, z) in ((26, 44), (26, 50)):
                floor(x, z, "t_marmo_pav")
            elif solid:
                wall(x, z, P + (4.5 if (x + z) % 5 else 5.0), "t_mattoni" if edge else "t_rosso")
            elif z in MOSAIC_Z:
                safe = x in SAFE[z]
                floor(x, z, "t_mos_castore" if safe else ("t_mos_polluce" if (x * 7 + z * 3) % 5 < 3 else "t_mos_vuoto"))
            elif z == 57:
                floor(x, z, "t_marmo_pav")
            else:
                floor(x, z, "t_mattoni_pav" if (x + z) % 4 else "t_mos_vuoto")
    for x, z, m in ((23, 47, "t_mos_castore"), (24, 47, "t_mos_castore"), (29, 47, "t_mos_polluce")):
        floor(x, z, m)                                  # the intact panel of the first room: the clue
    # the basilica: two rows of piers, the paved nave
    x0, z0, x1, z1 = BASILICA
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if z in (z0, z1) and x % 2 == 0:
                wall(x, z, P + (7.0 if x % 4 == 0 else 6.0), "t_opera")
            else:
                floor(x, z, "t_lastre")
    # the sanctuary: nave, two bell towers on the front, an open porch of three bays between them
    x0, z0, x1, z1 = CHURCH
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            tower = z <= z0 + 1 and (x <= x0 + 1 or x >= x1 - 1)
            if z == z0 and not tower:
                floor(x, z, "t_marmo_pav", T)                       # the porch
            else:
                top = 18.0 if tower else (12.0 if abs(x - (x0 + x1) / 2) < 1.6 else 10.0)
                wall(x, z, T + top, "t_marmo", topmat="m_tegole")
    world.facade_cols = cols
    world.rock_prefix = "rupe_faccia"
    world.bed_mat = "m_fondale"
    world.ambient = (0.56, 0.5, 0.45)
    world.sun = dict(color=(1.0, 0.72, 0.46), intensity=0.6, rot_y=250.0, rot_x=18.0)
    world.tindari = dict(hill=hill, terrace=terrace, cavea=cavea | front, drop=(d < 0))


def winch(ctx, name, p, block, text, hint):
    lua = ctx.lua
    lua.add('''CDV.Loop(function()
    if CDV.Flag("%s") then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) then return end
    if Lara:GetState() ~= 2 then return end
    if CDV.Near(%d, %d, %d, 1250, 700) then
        CDV.Flag("%s", true)
        CDV.Enable("%s")
        CDV.Say("%s", 8)
    end
end)''' % (name, p[0], p[1], p[2], name, block, text))
    lua.zone(name + "_hint", p, r=1250, dy=700, once=False, secs=6, need='not CDV.Flag("%s")' % name, text=hint)


def build(ctx):
    k, lua, w = ctx.kit, ctx.lua, ctx.world
    ctx.decor_block = [(0, 0, w.nx, w.nz)]
    rng = np.random.default_rng(23)
    tp, tt = Z.u(P), Z.u(T)

    def gh(x, z):
        return ctx.ground(x, z)

    def prop(name, x, z, rot=0.0, h=None, scale=1.0):
        k.prop(name, x, z, rot=rot, h=gh(int(x), int(z)) if h is None else h, scale=scale)

    def Pl(t, x, z, **kw):
        return k.place(t, x, z, **kw)

    def pos(x, z, dx=0.5, dz=0.5, h=None):
        return k.lua_pos(x, z, gh(x, z) if h is None else h, dx=dx, dz=dz)

    # --- arrival and the camp on the decumanus
    Pl(K.LARA, 16, 17, rot=45.0, name="lara_start")
    Pl(K.LARA_START_POS, 16, 17, ocb=1)
    lua.start('CDV.Say("Tindari, nel pomeriggio. Le mura greche, il decumano, il teatro. E sopra tutto, il santuario: Turi e\' la\'.", 9)')
    for name, x, z, rot in (("SCOGLIO_GRANDE", 14.6, 15.4, 0), ("TENDA", 22.5, 24.5, 30), ("TENDA", 26.4, 27.6, 200), ("FALO", 24.5, 26.5, 0),
                            ("CASSA_LEGNO", 21.5, 27.5, 10), ("CASSA_LEGNO", 27.6, 24.4, 60), ("FARO_CANTIERE", 28.5, 30.5, 220),
                            ("IMPALCATURA", 34.5, 36.5, 0), ("TRANSENNA", 30.5, 37.4, 0), ("TRANSENNA", 32.5, 37.4, 0),
                            ("TRANSENNA", 36.5, 41.6, 0), ("TRANSENNA", 38.5, 41.6, 0), ("FARO_CANTIERE", 43.5, 42.5, 100),
                            ("BOTTE", 23.4, 29.5, 0), ("ANFORA", 33.5, 42.4, 40), ("MACERIE", 18.5, 34.5, 0), ("MACERIE", 44.5, 36.4, 80)):
        prop(name, x, z, rot=float(rot))
    Pl(K.BADDY1, 24, 28, rot=180.0, name="t1")
    Pl(K.BADDY1, 30, 33, rot=200.0, name="t2")
    Pl(K.DOBERMAN, 26, 24, rot=180.0, name="c1")
    Pl(K.BADDY2, 42, 39, rot=270.0, name="t3")
    lua.zone("campo", pos(19, 21), r=2200, dy=2000, fn='CDV.Enable("t1")\nCDV.Enable("c1")', text="Il campo dei tombaroli. Hanno recintato gli scavi.")
    lua.zone("decumano", pos(30, 39), r=2400, dy=2000, fn='CDV.Enable("t2")\nCDV.Enable("t3")',
             text="Il decumano. A est il teatro e, dieci metri piu' in alto, la terrazza del santuario: nessuna scala.")
    Pl(K.SMALLMEDI, 22, 26)
    Pl(K.SHOTGUN_AMMO1, 27, 26)
    Pl(K.FLARE_ITEM, 35, 37)
    for x in range(16, 60, 3):                          # the colonnade of the decumanus, mostly fallen
        kind = ("COLONNA", "COLONNA_ROTTA", "COLONNA_ROTTA", "ROCCHIO")[(x * 5) % 4]
        if not (HOUSE[0] - 1 <= x <= HOUSE[2] + 1) and not (BASILICA[0] - 1 <= x <= BASILICA[2] + 1):
            prop(kind, x + 0.5, 42.5, rot=float(x * 37 % 360))
        prop(("COLONNA_ROTTA", "COLONNA", "ROCCHIO")[(x * 3) % 3], x + 0.5, 36.5, rot=float(x * 53 % 360))

    # --- the theatre and its machine
    for name, (x, z) in BLOCKS.items():
        Pl(K.RAISING_BLOCK1, x, z, name="blocco_" + name)
    prop("ARGANO", 54.5, 26.5, rot=0.0)
    winch(ctx, "argano1", pos(54, 26), "blocco_a",
          "L'argano gira, una fune corre sotto l'orchestra: davanti al palco sale un blocco di pietra.",
          "Un argano di legno, con la fune che sparisce sotto il palco. (Azione: girarlo.)")
    lua.zone("teatro", pos(54, 23), r=2600, dy=2500, secs=9, fn='CDV.Enable("t4")\nCDV.Enable("t5")',
             text="Il teatro greco. La scena ha tre ordini, alti quattro metri l'uno: in cima si passa sulla terrazza del santuario. "
                  "Sotto il palco c'era una macchina: tre argani, tre blocchi.")
    Pl(K.BADDY1, 50, 24, rot=90.0, name="t4")
    Pl(K.BADDY2, 58, 30, rot=180.0, h=tp + Z.u(2.0), name="t5")
    for i in range(7):                                   # stone seats on the rings
        a = math.pi + 0.35 + i * 0.4
        x, z = ORCH[0] + math.cos(a) * 5.6, ORCH[1] + math.sin(a) * 5.6
        if z < 28.4 and 47 < x < 60.5:
            prop("GRADINATA", x, z, rot=float(90 - math.degrees(a)))
    Pl(K.SMALLMEDI, 59, 30, h=tp + Z.u(2.0))
    Pl(K.SHOTGUN_AMMO1, 49, 31, h=tp + Z.u(6.0))
    lua.zone("palco", k.lua_pos(54, 30, tp + Z.u(2.0)), r=2000, dy=600, secs=8, need='not CDV.Flag("argano2")',
             text="Sul palco. Il secondo ordine e' a quattro metri: serve il secondo blocco. Il suo argano non e' qui.")
    lua.zone("ordine2", k.lua_pos(54, 31, tp + Z.u(6.0)), r=2000, dy=600, secs=8, need='not CDV.Flag("argano3")',
             text="Secondo ordine. Manca l'ultimo blocco: il terzo argano.")

    # --- the Roman house: the mosaic of the twins
    CM.kick(ctx, "porta_casa", 26, 43, lara_yaw=0)
    Pl(K.BADDY1, 29, 48, rot=180.0, name="t6")
    lua.zone("casa", pos(26, 46), r=1500, dy=1200, secs=9, fn='CDV.Enable("t6")',
             text="Una casa romana, con i pavimenti a mosaico. I tombaroli hanno lasciato qui uno dei loro.")
    lua.zone("mosaico_indizio", pos(24, 47, dx=0.0), r=1300, dy=1200, once=False, secs=10,
             text="Un mosaico intatto: due berretti scuri di Castore, e una scritta. \\\"Castore il mortale calca la terra. "
                  "Polluce cammina tra gli dei.\\\" Piu' in la', un berretto d'oro circondato da ossa.")
    for name, x, z, rot in (("ANFORA", 21.5, 45.5, 0), ("ANFORA", 22.4, 45.4, 90), ("MACERIE", 30.4, 46.0, 0), ("BRACIERE", 21.5, 48.5, 0),
                            ("CASSA_LEGNO", 30.5, 48.5, 20)):
        prop(name, x, z, rot=float(rot))
    Pl(K.SHOTGUN_AMMO1, 22, 46)
    lua.secret(1, pos(21, 45), r=900, text="Dietro le anfore della casa romana: una Stella dei Dioscuri!", give="ID.SMALLMEDI_ITEM")
    safe = ", ".join('["%d_%d"] = true' % (x, z) for z, xs in SAFE.items() for x in xs)
    lua.add('''CDV.Loop(function()
    local p = Lara:GetPosition()
    local sx, sz = math.floor(p.x / 1024), math.floor(p.z / 1024)
    if sx < %d or sx > %d or sz < %d or sz > %d then return end
    if p.y < %d - 60 then return end                       -- in the air over the tiles: nothing happens
    local key = sx .. "_" .. sz
    local safe = { %s }
    if safe[key] or CDV.Flag("mosaico_ultimo") == key then return end
    CDV.Flag("mosaico_ultimo", key)
    Lara:SetHP(math.max(Lara:GetHP() - 340, 0))
    CDV.Say("Le tessere cedono: sotto ci sono punte di bronzo! Solo i berretti scuri di Castore reggono.", 5)
end)''' % (MOSAIC_X[0], MOSAIC_X[-1], MOSAIC_Z[0], MOSAIC_Z[-1], -tp, safe))
    lua.zone("mosaico", pos(26, 50), r=900, dy=900, secs=8,
             text="Un pavimento intero di berretti: scuri e dorati. In fondo alla sala, un argano.")
    prop("ARGANO", 26.5, 57.5, rot=0.0)
    winch(ctx, "argano2", pos(26, 57, dz=0.2), "blocco_b",
          "L'argano gira. Lontano, nel teatro, un secondo blocco sale sul palco.",
          "Il secondo argano della macchina del teatro. (Azione: girarlo.)")
    Pl(K.BIGMEDI, 28, 57)

    # --- the basilica and its undercroft: stairs down, the rope over the gap, winch 3
    for x in range(BASILICA[0] + 1, BASILICA[2], 2):
        for z in (BASILICA[1], BASILICA[3]):
            k.prop("RUDERE_ARCO", x + 0.5, z + 0.5, rot=0.0, h=tp)
    FU = tp - 22 * CLICK
    rows = ["............"] * 3
    u = M2.cave(k, "U_CRIPTOPORTICO", rows, 40, 49, FU, 20 * CLICK, wall="t_opera", floor="t_lastre", ceil="t_volta",
                amb=(0.34, 0.31, 0.28), rough=0)
    rel = {40: 18, 41: 14, 42: 10, 43: 8, 44: 8, 45: 8, 46: 4, 49: 8, 50: 8, 51: 8}
    for x, cl in rel.items():
        for z in (49, 50, 51):
            u.sector(x, z).floor = [cl * CLICK] * 4
    k.link_vertical(u, ctx.terrain_room_at(*UPIT[0]), UPIT)
    k.place(K.ROPE, 47, 50, room=u.room, h=FU + 20 * CLICK - 64, name="fune_cripto")
    lua.start('CDV.Enable("fune_cripto")')
    k.prop("ARGANO", 50.5, 50.5, rot=90.0, h=FU + 8 * CLICK, room=u.room)
    winch(ctx, "argano3", k.lua_pos(50, 50, FU + 8 * CLICK), "blocco_c",
          "L'argano gira. Sopra la tua testa la pietra trema: nel teatro e' salito l'ultimo blocco.",
          "Il terzo argano. (Azione: girarlo.)")
    M2.light(ctx, u, 44.5, 50.5, 14 * CLICK, (1.0, 0.8, 0.55), 0.7, 1.0, 5.0)
    M2.light(ctx, u, 50.5, 50.5, 14 * CLICK, (1.0, 0.8, 0.55), 0.7, 1.0, 5.0)
    k.prop("BRACIERE", 43.5, 51.5, h=FU + 8 * CLICK, room=u.room)
    k.prop("BRACIERE", 51.5, 49.5, h=FU + 8 * CLICK, room=u.room)
    k.place(K.BAT, 47, 49, room=u.room, h=FU + 15 * CLICK, name="pip_u1")
    k.place(K.BAT, 48, 51, room=u.room, h=FU + 15 * CLICK, name="pip_u2")
    k.place(K.SHOTGUN_AMMO1, 51, 51, room=u.room, h=FU + 8 * CLICK)
    lua.zone("basilica", pos(44, 50), r=1800, dy=1200, secs=8,
             text="La basilica: restano i pilastri e gli archi. Nel pavimento, una scala scende nel buio.")
    lua.zone("cripto", k.lua_pos(44, 50, FU + 8 * CLICK), r=1300, dy=700, secs=9, fn='CDV.Enable("pip_u1")\nCDV.Enable("pip_u2")',
             text="Il criptoportico. Il pavimento e' crollato per tre campate; dalla volta pende una fune. Di la', un argano. "
                  "(Salta sulla fune, dondola con Scatto, lasciati con Salto.)")
    lua.secret(2, k.lua_pos(48, 49, FU), r=900, text="Tra le macerie sotto la fune: una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    k.prop("MACERIE", 47.6, 49.6, h=FU, room=u.room, scale=0.6)

    # --- the terrace: the sanctuary, the belvedere, the crypt
    Pl(K.BADDY2, 66, 38, rot=180.0, h=tt, name="t7")
    Pl(K.DOBERMAN, 64, 36, rot=180.0, h=tt, name="c2")
    lua.zone("terrazza", k.lua_pos(60, 32, tt), r=1500, dy=700, secs=9, fn='CDV.Enable("t7")\nCDV.Enable("c2")',
             text="In cima alla scena. Di qui si passa sulla terrazza del santuario.")
    lua.zone("santuario", k.lua_pos(66, 45, tt), r=1500, dy=900, secs=10,
             text="Il santuario della Madonna Nera. Sul portale: NIGRA SUM SED FORMOSA. Davanti, una scala scende nella cripta.")
    for name, x, z, rot in (("COLONNA", 62.5, 46.4, 0), ("COLONNA", 70.5, 46.4, 0), ("TRANSENNA", 64.5, 41.5, 90), ("FARO_CANTIERE", 68.6, 40.5, 250),
                            ("CASSA_LEGNO", 70.4, 38.5, 30), ("BRACIERE", 64.5, 46.4, 0), ("BRACIERE", 68.5, 46.4, 0)):
        k.prop(name, x, z, rot=float(rot), h=tt)
    Pl(K.SMALLMEDI, 70, 39, h=tt)
    bz = max(z for z in range(58, 70) if w.tindari["terrace"][71, z])
    lua.zone("belvedere", k.lua_pos(70, bz - 1, tt), r=1700, dy=900, secs=11,
             text="Il belvedere. Trecento metri piu' in basso, la lingua di sabbia e i laghetti: il Mergolo vuoto, il Lago Verde pieno. "
                  "Da quassu' la sabbia disegna due stelle, una a ovest e una a est.")
    lua.secret(3, k.lua_pos(72, bz, tt), r=900, text="Sull'orlo del belvedere: una Stella dei Dioscuri!", give="ID.BIGMEDI_ITEM")
    k.prop("COLONNA_ROTTA", 72.5, bz - 0.5, h=tt)

    FC = tt - 12 * CLICK
    plan = ["####.####"] + ["........."] * 8 + ["###...###", "###...###"]
    cr = M2.cave(k, "C_CRIPTA", plan, 62, 42, FC, 10 * CLICK, wall="t_marmo", floor="t_marmo_scuro", ceil="t_volta",
                 amb=(0.3, 0.29, 0.33), rough=0)
    for x in (65, 66, 67):
        cr.sector(x, 42).floor = [8 * CLICK] * 4
        cr.sector(x, 43).floor = [4 * CLICK] * 4
    k.link_vertical(cr, ctx.terrain_room_at(*CPIT[0]), CPIT)
    import walls
    stars = {"castore": (64, 50), "polluce": (68, 46)}
    for (x, z) in stars.values():
        walls.set_floor(cr.sector(x, z), k.atlases, "t_stella", 0)
    k.place(K.PUSHABLE, 64, 46, room=cr.room, name="statua_castore")
    k.place(K.PUSHABLE, 68, 50, room=cr.room, name="statua_polluce")
    k.place(K.DOOR_TYPE1, 66, 52, room=cr.room, rot=180.0, name="porta_pozzo")
    for i, (x, z) in enumerate(((63, 51), (69, 51), (63, 45))):
        k.place(K.BAT, x, z, room=cr.room, h=FC + 7 * CLICK, name="pip_k%d" % i)
    for name, x, z, rot in (("STATUA_DIOSCURO", 62.5, 48.5, 90), ("STATUA_DIOSCURO", 70.5, 48.5, 270), ("SARCOFAGO", 63.0, 52.4, 0),
                            ("SARCOFAGO", 69.2, 52.4, 0), ("BRACIERE", 64.5, 44.5, 0), ("BRACIERE", 68.5, 44.5, 0)):
        k.prop(name, x, z, rot=float(rot), h=FC, room=cr.room)
    M2.light(ctx, cr, 66.5, 48.5, 8 * CLICK, (0.7, 0.75, 1.0), 0.8, 1.5, 6.0)
    M2.light(ctx, cr, 66.5, 44.5, 6 * CLICK, (1.0, 0.8, 0.55), 0.6, 1.0, 4.0)
    lua.add('''CDV.Loop(function()
    if CDV.Flag("stelle_ok") then return end
    local function on(name, sx, sz)
        local b = CDV.M(name)
        if b == nil or not b:GetValid() then return false end
        local p = b:GetPosition()
        return math.floor(p.x / 1024) == sx and math.floor(p.z / 1024) == sz
    end
    local a, b = on("statua_castore", %d, %d), on("statua_polluce", %d, %d)
    if a and b then
        CDV.Flag("stelle_ok", true)
        CDV.Enable("porta_pozzo")
        CDV.Say("I gemelli sulle loro stelle: la lastra in fondo alla cripta scorre via. Sotto, un pozzo.", 8)
    elseif (a or b) and not CDV.Flag("stelle_una") then
        CDV.Flag("stelle_una", true)
        CDV.Say("Un gemello e' al suo posto. Manca l'altro.", 4)
    end
end)''' % (stars["castore"] + stars["polluce"]))
    lua.zone("cripta", k.lua_pos(66, 45, FC), r=1400, dy=700, secs=10, fn='CDV.Enable("pip_k0")\nCDV.Enable("pip_k1")\nCDV.Enable("pip_k2")',
             text="La cripta. Due blocchi di marmo con i berretti dei gemelli, fuori posto. Nel pavimento, due stelle: una a ovest, una a est.")
    wl = M2.cave(k, "C_POZZO", ["...", "...", "..."], 65, 53, FC, 10 * CLICK, wall="c_cisterna", floor="g_bagnato", ceil="t_volta",
                 amb=(0.2, 0.26, 0.28), rough=0)
    k.link_wall(cr, wl, span=(66, 66))
    M2.light(ctx, wl, 66.5, 54.5, 3 * CLICK, (0.4, 0.8, 0.9), 0.9, 1.0, 4.0)
    lua.zone("pozzo", k.lua_pos(66, 54, FC), r=900, dy=900, need='CDV.Flag("stelle_ok")', fn="CDV.End(0, 1)",
             text="Il pozzo scende nelle cisterne, e piu' giu' ancora: fino alle grotte marine sotto il capo. Turi e' passato di qui.")
    for rm in (u, cr, wl):
        rm.room.no_path = False

    # --- nature and scattered ruins
    info = w.tindari
    taken = set(k.links)

    def free(x, z):
        xi, zi = int(x), int(z)
        if not (2 < xi < w.nx - 3 and 2 < zi < w.nz - 3) or (xi, zi) in taken or w.water[xi, zi] or w.building_id[xi, zi] >= 0:
            return False
        if info["cavea"][xi, zi] or info["drop"][xi, zi] or 36 <= zi <= 42 or 29 <= zi <= 33 and 47 <= xi <= 61:
            return False
        for (a, b, cc, dd) in (HOUSE, BASILICA, CHURCH, (14, 14, 20, 20), (62, 36, 70, 46), (20, 20, 30, 32)):
            if a - 1 <= xi <= cc + 1 and b - 1 <= zi <= dd + 1:
                return False
        return True

    for name, count, hills in (("PINO_ALEPPO_GIOVANE", 16, True), ("PINO_ALEPPO_INCLINATO", 8, True), ("FICO_INDIA_GRANDE", 12, False),
                               ("FICO_INDIA_PICCOLO", 16, False), ("ELICRISO_GRUPPO", 50, False), ("ASPARAGO_ROVO", 24, True),
                               ("COLONNA_ROTTA", 7, False), ("ROCCHIO", 8, False), ("MACERIE", 6, False)):
        n = tries = 0
        while n < count and tries < 3000:
            tries += 1
            x, z = rng.uniform(4, 76), rng.uniform(4, 72)
            xi, zi = int(x), int(z)
            if free(x, z) and (hills or not info["hill"][xi, zi]) and gh(xi, zi) < Z.u(P + 14):
                k.prop(name, x, z, rot=float(rng.uniform(0, 360)), h=gh(xi, zi), scale=float(rng.uniform(0.85, 1.2)))
                if name.startswith(("PINO", "COLONNA", "ROCCHIO", "MACERIE", "FICO_INDIA_GRANDE")):
                    taken.add((xi, zi))
                n += 1
    for rm in ctx.level.rooms:
        if rm.name.startswith("T_"):
            rm.no_path = False
    ctx.notes += ["LIVELLO 2 - TINDARI", __doc__]
