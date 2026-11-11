"""Livello 3 - La meta' perduta. GDD v3.

The sea caves under Capo Tindari and the temple of the Dioscuri, in the half of Tyndaris that slid into the sea.
The temple is a gallery round a sunken cella, 8 m deep. It has two states, like the twins, and the altar on the
west gallery changes them (flipmap 1, the cella and the gallery have a flooded twin each):
  dry      - the cella is a pit: a stair goes down, the men of Turi shoot from below, the east gallery is out of reach;
  flooded  - Castore, the mortal one, on the altar: the sea fills the cella to the gallery. Whoever is down there
             drowns; Lara swims across (a shark comes in with the sea), and into the alcove half way up the wall.

Route: the sea cave -> the underwater tunnel -> the propylaeum -> the altar: flood -> swim to the east gallery,
the lever (the bronze doors of the inner chamber: they open only when the water is gone) -> back, drain -> down
the stair -> the chamber: Turi 'a Vulpi with the Astro di Polluce, and bullets do not stop him -> up and flood:
he drowns, the Astro is Lara's -> both stars on the altar: the temple starts to fall, 75 seconds -> swim to the
east gallery, the way out under the boulder, the steps, daylight.

New here: an interior flipmap, the shark. Everything else is from Livello 0.
"""
import copy

import numpy as np

import content_marinello2 as M2
import kit as K
import prj2
import walls
from kit import CLICK

FLIP = 1
DEEP = -16 * CLICK               # the floor of the cella
VOID = K.rect(25, 13, 33, 17)
ALTAR = (23, 19)
LEVER = (35, 18)
ESCAPE_FRAMES = 75 * 30


def build_standalone(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    log = []
    real_add = L.add_portal

    def add_portal(room, area, direction, other, opacity=0):
        log.append((room, area, direction, other, opacity))
        return real_add(room, area, direction, other, opacity=opacity)
    L.add_portal = add_portal

    # ---------------------------------------------------------------- geometry
    a0 = M2.cave(k, "A0_GROTTA", ["##....##", "#......#", "........", "........", "........", "........", "........", "#......#", "##....##"],
                 2, 11, 0, 2304, seed=31, rough=448, amb=(0.3, 0.36, 0.4))
    a0w = M2.cave(k, "A0_ACQUA", ["..."] * 3, 6, 14, -2048, 2048, floor="g_bagnato", water=True, amb=(0.16, 0.36, 0.4))
    tun = M2.cave(k, "TUNNEL", ["......."] * 2, 9, 14, -2048, 1536, floor="g_bagnato", water=True, amb=(0.12, 0.3, 0.36))
    a1w = M2.cave(k, "A1_ACQUA", ["..."] * 3, 16, 14, -2048, 2048, floor="g_bagnato", wall="t_opera_muschio", water=True, amb=(0.16, 0.36, 0.4))
    a1 = M2.cave(k, "A1_PROPILEO", ["#.....#"] + ["......."] * 5 + ["#.....#"], 15, 12, 0, 2560, wall="t_opera", floor="t_lastre_muschio",
                 ceil="t_volta", amb=(0.34, 0.36, 0.38), rough=0)
    k.water_surface(a0, a0w, K.rect(6, 14, 8, 16))
    k.water_surface(a1, a1w, K.rect(16, 14, 18, 16))
    k.link_wall(a0w, tun, span=(14, 15))
    k.link_wall(tun, a1w, span=(14, 15))

    ring = "...#########..."
    u = M2.cave(k, "U_GALLERIA", [ring] * 3 + ["..............."] * 5 + [ring] * 3, 22, 10, 0, 11 * CLICK, wall="t_marmo", floor="t_marmo_pav",
                ceil="t_volta", amb=(0.36, 0.36, 0.4), rough=0)
    k.link_wall(a1, u, span=(14, 16))
    solid = "###############"
    rows = [solid] * 3 + ["###.........#..", "###.........#..", "#..............", "###.........#..", "###.........#.."] + [solid] * 3
    h = M2.cave(k, "H_CELLA", rows, 22, 10, DEEP, 15 * CLICK, wall="t_marmo", floor="t_marmo_scuro", ceil="t_volta",
                amb=(0.3, 0.3, 0.34), rough=0)
    for x in (23, 24):
        h.sector(x, 15).floor = [8 * CLICK] * 4                  # the alcove, half way up the west wall
    for x, cl in ((25, 15), (26, 11), (27, 7), (28, 3)):
        h.sector(x, 13).floor = [cl * CLICK] * 4                 # the stair: its top step is 1 click under the gallery
    k.link_vertical(h, u, VOID)
    e_rows = ["############", "####.#######", "........2468", "........2468", "........2468", "####.#######", "############"]
    e = M2.cave(k, "E_FUGA", e_rows, 37, 12, 0, 17 * CLICK, wall="t_opera", floor="t_lastre", ceil="g_soffitto", amb=(0.34, 0.33, 0.32), rough=0)
    k.link_wall(u, e, span=(15, 15))
    L.add_portal = real_add
    M2.shape(k, a0, protect=[(3, 15), (3, 13), (9, 17), (2, 13)])
    # the temple: a higher nave over the cella, the mosaic of the twins on its floor
    for (wx, wz) in VOID:
        u.sector(wx, wz).ceil = [15 * CLICK] * 4
    for wx in range(26, 33):
        for wz in (14, 15, 16):
            name = "t_stella" if (wx, wz) == (29, 15) else "t_mos_castore" if wx < 29 and wz == 15 else "t_mos_polluce" if wx > 29 and wz == 15 else "t_mos_vuoto"
            walls.set_floor(h.sector(wx, wz), k.atlases, name, 0)
    for wz in (14, 15, 16):
        walls.set_floor(u.sector(23, wz), k.atlases, "t_mos_vuoto", 0)
        walls.set_floor(u.sector(35, wz), k.atlases, "t_mos_vuoto", 0)
    walls.set_floor(u.sector(23, 18), k.atlases, "t_stella", 0)
    k.finish_interiors()

    # ---------------------------------------------------------------- the flooded twins of gallery and cella
    ur, hr = u.room, h.room
    twins = {}
    for rm, suffix in ((ur, "_ACQUA"), (hr, "_ACQUA")):
        alt = copy.deepcopy(rm)
        alt.name = rm.name + suffix
        alt.index = None
        alt.objects = []
        alt.meta = []
        L.add_room(alt)
        rm.alternate = (FLIP, alt)
        twins[rm] = alt
    twins[hr].room_type = 3
    twins[hr].ambient = (0.14, 0.34, 0.4)
    for (wx, wz) in VOID:
        rot = walls.rot_for(wx, wz)
        us = twins[ur].sectors[wx - ur.x][wz - ur.z]
        hs = twins[hr].sectors[wx - hr.x][wz - hr.z]
        for s, faces in ((us, (prj2.F_FLOOR, prj2.F_FLOOR_TRI2)), (hs, (prj2.F_CEILING, prj2.F_CEILING_TRI2))):
            for f in faces:
                if s.invisible:
                    s.invisible.discard(f)
        walls.set_floor(us, k.atlases, "acqua_scura", rot, blend=2)
        walls.set_ceiling(hs, k.atlases, "acqua_scura", rot, blend=2)
    for (room, area, direction, other, opacity) in log:
        if room in twins:
            real_add(twins[room], area, direction, other, opacity=2 if other in twins else opacity)

    def light2(it, wx, wz, hh, color, intensity=0.8, inner=1.0, outer=5.0):
        M2.light(ctx, it, wx, wz, hh, color, intensity, inner, outer)
        if it.room in twins:
            rm = twins[it.room]
            L.add_light(rm, 0, ((wx - rm.x) * 1024.0, float(hh), (wz - rm.z) * 1024.0), color=color, intensity=intensity, inner=inner, outer=outer)

    # ---------------------------------------------------------------- the sea cave and the propylaeum
    k.place(K.LARA, 3, 15, room=a0.room, rot=90.0, name="lara_start")
    lua.start('if not CDV.Has(ID.PUZZLE_ITEM7) then TEN.Inventory.GiveItem(ID.PUZZLE_ITEM7, 1) end\n'
              'CDV.Say("Le grotte marine sotto Capo Tindari. Il pozzo finiva qui: oltre l\'acqua, da qualche parte, la meta\' perduta della citta\'.", 9)')
    light2(a0, 7.5, 15.5, 400, (0.4, 0.9, 0.95), 0.9, 1.5, 6.0)
    for name, x, z, rot, sc in (("STALAGMITE", 3.5, 18.5, 0, 1.1), ("STALAGMITE", 8.4, 12.5, 60, 0.9), ("STALAGMITE", 4.4, 12.4, 0, 0.7),
                                ("ANFORA", 5.5, 18.4, 30, 1.0), ("CASSA_LEGNO", 2.6, 13.5, 10, 1.0)):
        k.prop(name, x, z, rot=float(rot), h=0, room=a0.room, scale=sc)
    M2.stalactites(k, a0, 12, 41)
    k.place(K.SMALLMEDI, 3, 13, room=a0.room)
    k.place(K.SHOTGUN_AMMO1, 9, 17, room=a0.room)
    k.place(K.BIGMEDI, 12, 14, room=tun.room, h=-2048)
    lua.secret(1, k.lua_pos(12, 14, -2048), r=900, text="Sul fondo del sifone: una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    lua.zone("sifone", k.lua_pos(7, 13, 0), r=1300, dy=600, secs=8, text="L'acqua continua sotto la roccia, verso est. Un sifone: fiato, e giu'.")
    for name, x, z, rot in (("COLONNA", 15.5, 13.5, 0), ("COLONNA", 15.5, 17.5, 0), ("COLONNA", 21.5, 13.5, 0), ("COLONNA", 21.5, 17.5, 0),
                            ("BRACIERE", 20.5, 13.5, 0), ("BRACIERE", 20.5, 17.5, 0), ("MACERIE", 19.5, 12.6, 40), ("TRANSENNA", 19.5, 18.2, 0),
                            ("FARO_CANTIERE", 16.6, 12.6, 140), ("CASSA_LEGNO", 17.5, 18.5, 20)):
        k.prop(name, x, z, rot=float(rot), h=0, room=a1.room)
    light2(a1, 20.5, 15.5, 1500, (1.0, 0.8, 0.5), 0.8, 1.0, 5.0)
    lua.zone("propileo", k.lua_pos(20, 15, 0), r=1300, dy=600, secs=9,
             text="Colonne, sotto il mare. Il propileo del tempio dei Dioscuri. I fari sono dei tombaroli: Turi e' gia' dentro.")
    k.place(K.SHOTGUN_AMMO1, 16, 18, room=a1.room)

    # ---------------------------------------------------------------- the temple
    k.prop("ALTARE_ASTRI", ALTAR[0] + 0.5, ALTAR[1] + 0.6, rot=0.0, h=0, room=ur)
    for name, x, z, rot in (("STATUA_DIOSCURO", 22.5, 10.5, 45), ("STATUA_DIOSCURO", 36.5, 20.5, 225), ("BRACIERE", 22.5, 17.5, 0),
                            ("BRACIERE", 24.5, 20.5, 0), ("BRACIERE", 34.5, 10.5, 0), ("BRACIERE", 36.5, 12.5, 0), ("COLONNA_ROTTA", 24.5, 10.5, 0),
                            ("MACERIE", 35.5, 20.4, 0),
                            ("COLONNA", 24.5, 12.5, 0), ("COLONNA", 24.5, 18.5, 0), ("COLONNA", 34.5, 12.5, 0), ("COLONNA", 34.5, 18.5, 0),
                            ("COLONNA", 22.5, 12.5, 0), ("COLONNA", 36.5, 18.5, 0), ("COLONNA", 22.5, 13.4, 0), ("COLONNA", 22.5, 17.6, 0)):
        k.prop(name, x, z, rot=float(rot), h=0, room=ur)
    light2(u, 23.5, 18.5, 1700, (1.0, 0.85, 0.55), 0.9, 1.0, 5.0)
    light2(u, 35.5, 15.5, 1700, (1.0, 0.85, 0.55), 0.8, 1.0, 5.0)
    light2(u, 29.5, 15.5, 3300, (0.55, 0.7, 1.0), 0.9, 2.0, 9.0)
    light2(h, 29.5, 15.5, 2600, (0.5, 0.75, 0.9), 0.7, 2.0, 8.0)
    light2(h, 35.5, 15.5, 1500, (1.0, 0.8, 0.45), 0.9, 1.0, 4.0)
    k.place(K.LEVER_SWITCH, LEVER[0], LEVER[1], room=ur, rot=0.0, name="leva_valve")
    k.place(K.DOOR_TYPE1, 36, 15, room=ur, rot=270.0, name="porta_fuga")
    k.place(K.DOOR_TYPE1, 33, 15, room=hr, rot=270.0, h=DEEP, name="porta_valve")
    k.place(K.BADDY1, 30, 16, room=hr, rot=270.0, h=DEEP, name="g1")
    k.place(K.BADDY1, 32, 14, room=hr, rot=270.0, h=DEEP, name="g2")
    k.place(K.BADDY2, 36, 15, room=hr, rot=270.0, h=DEEP, name="turi")
    k.place(K.SHARK, 30, 15, room=hr, rot=270.0, h=DEEP + 2000, name="squalo", invisible=True)
    k.place(K.BIGMEDI, 23, 15, room=hr, h=DEEP + 8 * CLICK)
    lua.secret(2, k.lua_pos(23, 15, DEEP + 8 * CLICK), r=900, text="Nella nicchia a meta' parete: una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    k.place(K.SHOTGUN_AMMO1, 35, 17, room=hr, h=DEEP)
    k.place(K.BIGMEDI, 36, 13, room=hr, h=DEEP)
    lua.secret(3, k.lua_pos(36, 13, DEEP), r=800, text="Il tesoro dei Dioscuri, dietro Turi: l'ultima Stella!", give="ID.BIGMEDI_ITEM")
    # the colonnade of the cella: six columns 13 m tall, from the floor of the cella to the vault over the gallery
    for x, z in ((26.5, 17.55), (29.5, 17.55), (32.5, 17.55), (30.5, 13.45), (32.5, 13.45)):
        k.prop("COLONNA_TEMPIO", x, z, rot=0.0, h=DEEP, room=hr)
    for x, z, rot in ((25.5, 16.5, 90), (33.4, 16.5, 270), (33.4, 13.6, 270)):
        k.prop("STATUA_DIOSCURO", x, z, rot=float(rot), h=DEEP, room=hr, scale=1.3)
    for name, x, z, rot in (("SARCOFAGO", 29.5, 16.6, 0), ("ANFORA", 26.5, 16.5, 30), ("ANFORA", 32.5, 13.5, 100), ("STATUA_DIOSCURO", 29.5, 13.5, 180),
                            ("MACERIE", 31.5, 14.5, 0), ("ANFORA", 35.5, 13.5, 0), ("ANFORA", 36.4, 17.4, 60)):
        k.prop(name, x, z, rot=float(rot), h=DEEP, room=hr)
    lua.zone("tempio", k.lua_pos(23, 15, 0), r=1300, dy=600, secs=10, fn='CDV.Enable("g1")\nCDV.Enable("g2")',
             text="Il tempio. Una galleria intorno alla cella, otto metri piu' in basso: una scala scende, e la' sotto ci sono gli uomini di Turi. "
                  "La galleria di fronte non si raggiunge. In fondo a questa, un altare con due incavi.")
    ap = k.lua_pos(ALTAR[0], ALTAR[1] - 1, 0)
    lp = k.lua_pos(LEVER[0], LEVER[1], 0)
    lua.add('''local function Drown(name)
    local m = CDV.M(name)
    if m ~= nil and m:GetValid() and CDV.Active(name) and m:GetHP() > 0 then m:SetHP(0) return true end
    return false
end
local function SetWater(on)
    if (CDV.Flag("acqua") or false) == on then return end
    TEN.Flow.FlipMap(%d)
    CDV.Flag("acqua", on)
    if on then
        local n = 0
        if Drown("g1") then n = n + 1 end
        if Drown("g2") then n = n + 1 end
        if CDV.Flag("turi_sveglio") and not CDV.Flag("turi_morto") then
            CDV.After(120, function()
                Drown("turi")
                CDV.Flag("turi_morto", true)
            end)
            CDV.Say("Castore e' il gemello mortale: il mare entra nella cella, e Turi e' la' sotto. Le pallottole non lo fermavano. L'acqua si'.", 9)
        elseif n > 0 then
            CDV.Say("Il mare riempie la cella fino alla galleria. Chi era la' sotto non risale.", 7)
        else
            CDV.Say("L'Astro di Castore nell'incavo di bronzo: il mare riempie la cella fino alla galleria. Ora si puo' nuotare fino all'altra parte.", 8)
        end
        CDV.Enable("squalo")
    else
        CDV.Disable("squalo")
        if CDV.Flag("leva_valve") and not CDV.Flag("valve_aperte") then
            CDV.Flag("valve_aperte", true)
            CDV.Enable("porta_valve")
            CDV.Say("L'acqua si ritira, e senza piu' il suo peso le valve di bronzo in fondo alla cella si aprono.", 8)
        else
            CDV.Say("Ripreso l'Astro, l'acqua si ritira nei canali: la cella e' di nuovo asciutta.", 6)
        end
    end
end
CDV.Loop(function()
    -- the altar: Action puts Castore in its socket or takes it back
    local cd = CDV.Flag("altare_cd") or 0
    if cd > 0 then CDV.Flag("altare_cd", cd - 1) end
    if cd == 0 and not CDV.Flag("fuga") and TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) and Lara:GetState() == 2
        and CDV.Near(%d, %d, %d, 1300, 600) then
        CDV.Flag("altare_cd", 90)
        SetWater(not CDV.Flag("acqua"))
    end
    -- the lever of the bronze doors, on the east gallery
    if not CDV.Flag("leva_valve") then
        local m = CDV.M("leva_valve")
        if m ~= nil and m:GetValid() then
            local s = m:GetState()
            if CDV.Flag("leva_s0") == nil then CDV.Flag("leva_s0", s) end
            if s ~= CDV.Flag("leva_s0") then
                CDV.Flag("leva_valve", true)
                CDV.Say("Sotto l'acqua qualcosa si sblocca, ma le valve di bronzo non si muovono: l'acqua le tiene chiuse.", 8)
            end
        end
    end
    -- Turi wakes when Lara reaches the chamber on foot
    if CDV.Flag("valve_aperte") and not CDV.Flag("turi_sveglio") and not CDV.Flag("acqua") and CDV.Near(%d, %d, %d, 1500, 700) then
        CDV.Flag("turi_sveglio", true)
        CDV.Enable("turi")
        local m = CDV.M("turi")
        if m ~= nil then m:SetHP(20000) end
        CDV.Say("Turi 'a Vulpi, con l'Astro di Polluce al collo. Polluce e' l'immortale: finche' lo porta, le armi non lo fermano. Via di qui!", 9)
    end
    -- the fall of the temple
    local t = CDV.Flag("fuga_t") or 0
    if t > 0 then
        t = t - 1
        CDV.Flag("fuga_t", t)
        if t == 0 then
            Lara:SetHP(0)
            CDV.Say("Il tempio si chiude sopra di te.", 6)
        elseif t %% 450 == 0 then
            CDV.Say("Il tempio crolla: " .. math.floor(t / 30) .. " secondi.", 3)
        end
    end
end)''' % ((FLIP,) + ap + k.lua_pos(33, 15, DEEP)))
    lua.drop("polluce", "turi", "ID.PUZZLE_ITEM8",
             "Turi non risale. L'Astro di Polluce viene a galla da solo, come se sapesse dove andare. All'altare: i gemelli insieme.")
    lua.zone("altare", ap, r=1300, dy=600, once=False, secs=7, need='not CDV.Flag("fuga")',
             text="L'altare dei Dioscuri: un incavo di bronzo e uno d'oro. (Azione: posare o riprendere l'Astro di Castore.)")
    lua.zone("leva", lp, r=1300, dy=600, secs=7, need='not CDV.Flag("leva_valve")',
             text="La galleria est. Una leva di bronzo, e una porta di pietra senza maniglia.")
    lua.zone("valve", k.lua_pos(32, 15, DEEP), r=1300, dy=700, once=False, secs=7, need='not CDV.Flag("valve_aperte") and not CDV.Flag("acqua")',
             text="Due valve di bronzo, chiuse. Nessuna serratura: il meccanismo e' altrove, piu' in alto.")
    lua.use("altare2", "ID.PUZZLE_ITEM8", ap, r=1300, dy=600,
            text="Castore e Polluce, insieme dopo duemila anni. Il mare entra da ogni parte e la volta comincia a cedere: "
                 "la porta della galleria est si e' aperta. 75 secondi!",
            fn='if not CDV.Flag("acqua") then TEN.Flow.FlipMap(%d); CDV.Flag("acqua", true) end\n'
               'CDV.Flag("fuga", true)\nCDV.Flag("fuga_t", %d)\nCDV.Enable("porta_fuga")\nCDV.Enable("squalo")' % (FLIP, ESCAPE_FRAMES))
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, 1300, ID.PUZZLE_ITEM8, "use_altare2") end)' % ap)

    # ---------------------------------------------------------------- the way out
    k.place(K.ROLLINGBALL, 44, 15, room=e.room, rot=270.0, h=512, name="masso_fuga")
    lua.zone("masso_fuga", k.lua_pos(39, 15, 0), r=900, dy=900,
             fn='CDV.Enable("masso_fuga")\nlocal b = CDV.M("masso_fuga")\nif b ~= nil then b:SetItemFlags(-800, 0) end',
             text="Un masso! Nelle nicchie!")
    light2(e, 38.5, 15.5, 1300, (1.0, 0.8, 0.55), 0.6, 1.0, 4.0)
    light2(e, 48.5, 15.5, 3400, (1.0, 0.93, 0.8), 1.8, 2.0, 9.0)
    k.place(K.SMALLMEDI, 41, 13, room=e.room)
    lua.zone("fine", k.lua_pos(48, 15, 8 * CLICK), r=1100, dy=900, need='CDV.Flag("fuga")',
             fn='CDV.Flag("fuga_t", 0)\nCDV.After(240, function() CDV.End(0, 1) end)',
             text="Aria. Luce. L'alba sulla lingua di sabbia di Marinello, e in mano i due Astri dei Dioscuri. Sopra, il santuario; "
                  "sotto, la meta' perduta di Tindari si chiude per sempre. FINE.")
    for it in (a0, a1, u, h, e):
        it.room.no_path = False
    for alt in twins.values():
        alt.no_path = False
    ctx.notes += ["LIVELLO 3 - LA META' PERDUTA", __doc__]
