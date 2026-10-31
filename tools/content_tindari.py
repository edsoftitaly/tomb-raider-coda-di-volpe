"""Livello 5 - Tindari.

In cima al Sentiero Coda di Volpe -> piazzale del Santuario (corvi) -> belvedere (E7: la forma della
lingua di sabbia) -> Basilica e Torre: due leve gemelle da tirare entro 30 secondi (E8) -> la botola
nell'orchestra del Teatro Greco -> cripta: il Sigillo della tonnara apre la sala, tre leve nell'ordine
della sabbia (E9) -> Astro di Castore -> Donna Villa -> Rocca Femmina: il tuffo -> fine.
"""
import numpy as np

import kit as K
from kit import CLICK

START = (246, 172)
BELVEDERE = (202, 231)
BASILICA = (122, 296)
TORRE = (85, 305)
ORCH = (58, 338)
ROCCA = (258, 212)


def prepare(world):
    import santuario
    santuario.prepare(world)
    # Teatro Greco: the OSM outline is a solid block; carve a cavea of 1-click terraces around the orchestra.
    ids = [i for i, b in enumerate(world.buildings) if b["tags"].get("name") == "Teatro Greco di Tindari"]
    mask = np.isin(world.building_id, ids)
    xs, zs = np.nonzero(mask)
    h_orch = int(world.floor_terrain[mask].min()) // CLICK * CLICK
    top = int(world.floor_terrain[mask].max())
    world.h_orch = h_orch
    for x, z in zip(xs, zs):
        dx, dz = x - ORCH[0], z - ORCH[1]
        r = (dx * dx + dz * dz) ** 0.5
        behind = (dx + dz) < 2      # seats are on the south-west side, the stage towards the sea
        h = h_orch + (max(0, int(r) - 5) * CLICK if behind else 0)
        h = min(h, top // CLICK * CLICK)
        world.building_id[x, z] = -1
        world.floor[x, z, :] = h
        world.floor_terrain[x, z, :] = h
        world.mat[x, z] = "lastricato" if behind else "castello_pav"
    K.flatten(world, K.rect(ORCH[0] - 4, ORCH[1] - 4, ORCH[0] + 4, ORCH[1] + 4), h_orch, mat="castello_pav")
    # Ruined tower: a 3x3 block, 6 m high.
    tx, tz = TORRE
    base = int(world.floor[tx - 1:tx + 2, tz - 1:tz + 2].max()) // 64 * 64
    for x, z in K.rect(tx - 1, tz - 1, tx + 1, tz + 1):
        world.floor[x, z, :] = base + 12 * CLICK
        world.mat[x, z] = "castello_pav"
    K.flatten(world, K.rect(tx - 1, tz - 4, tx + 1, tz - 2), base, mat="castello_pav")


DECOR = dict(centre=(200, 225, 25))


def santuario_scene(ctx):
    """The basilica and its square (see santuario.py for sources and estimates)."""
    import santuario as S
    k = ctx.kit
    S.place(ctx)
    F = ctx.world.santuario["F"]
    # Square (Piazza Quasimodo): double lamps along the axis, benches on the open north side and along
    # the Segreteria, big white pots at the doors. The Segreteria fills the south-west side.
    for u, v in ((-6, -8), (-6, 8), (-20, -6), (-20, 8)):
        k.prop("LAMPIONE_PIAZZA", *S.to_world(u, v), rot=S.AXIS_DEG, h=F)
    for u, v in ((-12, 13), (-24, 13), (-12, -9)):
        k.prop("PANCHINA", *S.to_world(u, v), rot=S.AXIS_DEG + (0 if v < 0 else 180), h=F)
    for v in (-5.6, 5.6):
        k.prop("VASO_BIANCO_FIORI", *S.to_world(-1.5, v), rot=S.AXIS_DEG, h=F)


def build(ctx):
    ctx.decor_block = [(30, 322, 72, 362), (78, 296, 92, 312), (204, 198, 252, 232)]
    k, lua = ctx.kit, ctx.lua
    santuario_scene(ctx)
    import santuario_interno
    santuario_interno.build(ctx)
    sx, sz = k.spot(*START)
    k.place(K.LARA, sx, sz, rot=315.0, name="lara_start")
    k.place(K.LARA_START_POS, sx, sz, ocb=1)
    lua.start('''if not CDV.Has(ID.PUZZLE_ITEM6) then CDV.Give(ID.PUZZLE_ITEM6, 1) end
CDV.Say("Tindari, in cima alla rupe. Il santuario della Madonna Nera, e piu' in la' la citta' greca.", 7)''')

    # Crows on the sanctuary square.
    for i, (x, z) in enumerate(((197, 222), (205, 226), (190, 216))):
        p = k.spot(x, z)
        k.place(K.CROW, *p, h=ctx.ground(*p) + 6 * CLICK, name="corvo%d" % i)
    sq = k.spot(197, 222)
    lua.zone("piazzale", k.lua_pos(*sq, ctx.ground(*sq)), r=9000, dy=6000,
             fn='CDV.Enable("corvo0")\nCDV.Enable("corvo1")\nCDV.Enable("corvo2")')
    k.place(K.SMALLMEDI, *k.spot(215, 200))
    bx, bz = k.spot(*BELVEDERE)
    lua.zone("belvedere", k.lua_pos(bx, bz, ctx.ground(bx, bz)), r=2200, dy=3000, once=False, secs=10,
             text="Laggiu' la lingua di sabbia: da qui sembra disegnare una luna, poi una stella, e l'ultimo ricciolo e' un sole.")

    # E8: twin levers at the Basilica and the Tower, 30 seconds.
    tor = k.lever_spot(TORRE[0], TORRE[1] - 3)
    bas = k.lever_spot(BASILICA[0], BASILICA[1] - 9)
    trap = None
    flames = {}
    for key, (x, z) in (("basilica", bas), ("torre", tor)):
        rot = 0.0
        lev = k.place(K.LEVER_SWITCH, x, z, rot=rot, name="leva_" + key)
        k._taken = getattr(k, "_taken", set())
        k._taken.add((x, z))
        fx, fz = k.spot(x, z, r=3)
        fl = k.place(K.FLAME_EMITTER2, fx, fz, ocb=1, name="fiamma_" + key)
        flames[key] = fl
        k.trigger(x, z, trig_type=K.T_SWITCH, target=lev, timer=30)
        k.trigger(x, z, trig_type=K.T_SWITCH, target=fl)
    for i, (x, z) in enumerate(((118, 284), (128, 306))):
        k.place(K.BADDY1, *k.spot(x, z), name="tombarolo_b%d" % i)
    k.place(K.BADDY2, *k.spot(TORRE[0] + 4, TORRE[1] - 5), name="tombarolo_t")
    pb = k.spot(BASILICA[0], BASILICA[1] - 14)
    lua.zone("parco", k.lua_pos(*pb, ctx.ground(*pb)), r=16000, dy=8000,
             fn='CDV.Enable("tombarolo_b0")\nCDV.Enable("tombarolo_b1")\nCDV.Enable("tombarolo_t")',
             text="Gli uomini della Volpe scavano tra le rovine di Tyndaris.")
    lua.zone("leve_gemelle", k.lua_pos(bas[0], bas[1], ctx.ground(bas[0], bas[1])), r=2500, dy=3000, secs=8,
             text="Una leva con il simbolo di Castore. Il fratello Polluce dev'essere da qualche parte, verso la Torre.")
    k.place(K.UZI_AMMO, *k.spot(100, 300))
    k.place(K.BIGMEDI, *k.spot(70, 320))

    # Theatre crypt.
    h_orch = ctx.world.h_orch
    fl0 = h_orch - 7 * CLICK
    trap = k.place(K.FLOOR_TRAPDOOR1, *ORCH, name="botola_teatro")
    lua.loop('''
local b, t = CDV.Pulled("leva_basilica"), CDV.Pulled("leva_torre")
if not CDV.Flag("teatro") and b and t then
    CDV.Flag("teatro", true)
    CDV.Enable("botola_teatro")
    CDV.Say("Un rombo sotto il teatro: nell'orchestra si e' aperta una botola!", 6)
end''')
    tex = ("lastre_greche", "soffitto_roccia", "opera_greca")
    A = k.interior("CRIPTA_INGRESSO", [".....", ".....", "D.c..", ".....", "....."], 56, 336, fl0, 7 * CLICK, *tex,
                   ambient=(0.35, 0.33, 0.3))
    k.link_vertical(A, k.room_at(*ORCH), [ORCH])
    rows = []
    for z in range(342, 333, -1):
        r = []
        for x in range(46, 56):
            if x == 46:
                r.append("N" if z == 338 else "#")
            elif x == 47 and z in (337, 339):
                r.append("#")
            else:
                r.append(".")
        rows.append(r)
    H = k.interior("CRIPTA_SALA", ["".join(r) for r in rows], 46, 334, fl0, 7 * CLICK, *tex, ambient=(0.35, 0.33, 0.3))
    k.link_wall(H, A, span=(338, 338))
    k.place(K.DOOR_TYPE3, *A.anchors["D"], room=A.room, rot=90.0, name="porta_cripta")
    k.place(K.DOOR_TYPE3, 47, 338, room=H.room, rot=90.0, name="porta_astro")
    k.place(K.PUZZLE_ITEM[7], *H.anchors["N"], room=H.room, name="astro_castore")
    names = {"sole": 48, "luna": 51, "stella": 54}
    for key, x in names.items():
        lev = k.place(K.LEVER_SWITCH, x, 340, room=H.room, rot=0.0, name="leva_" + key)
        fl = k.place(K.FLAME_EMITTER2, x + 1, 341, room=H.room, ocb=1, name="fiamma_" + key)
        k.trigger(x, 340, room=H.room, trig_type=K.T_SWITCH, target=lev, timer=5)
        k.trigger(x, 340, room=H.room, trig_type=K.T_SWITCH, target=fl)
        lua.zone("cripta_" + key, k.lua_pos(x, 339, fl0), r=900, dy=1200, once=False, secs=3,
                 text="Leva del %s" % {"sole": "Sole", "luna": "Luna", "stella": "Stella"}[key])
    for i, (x, z) in enumerate(((50, 335), (53, 336))):
        k.place(K.BIG_RAT, x, z, room=H.room, name="ratto_cripta%d" % i)
    lua.use("sigillo", "ID.PUZZLE_ITEM6", k.lua_pos(57, 338, fl0), r=1500, dy=1200,
            text="Il Sigillo della tonnara entra nella pietra: la cripta si apre.",
            fn='CDV.Enable("porta_cripta")\nCDV.Enable("ratto_cripta0")\nCDV.Enable("ratto_cripta1")')
    lua.zone("cripta", k.lua_pos(58, 338, fl0), r=1500, dy=1500,
             text="La cripta sotto il teatro. Una porta di pietra con l'impronta di un sigillo.")
    lua.add('''
local ORDER = { "luna", "stella", "sole" }
local was = { luna = false, stella = false, sole = false }
CDV.Loop(function()
    if CDV.Flag("cripta_ok") then return end
    for _, key in ipairs({ "luna", "stella", "sole" }) do
        local on = CDV.Pulled("leva_" .. key)
        if on and not was[key] then
            local step = CDV.Flag("cripta_step") or 0
            if ORDER[step + 1] == key then
                step = step + 1
                CDV.Flag("cripta_step", step)
                if step == 3 then
                    CDV.Flag("cripta_ok", true)
                    CDV.Enable("porta_astro")
                    CDV.Say("La nicchia si apre: l'Astro di Castore!", 6)
                end
            else
                CDV.Flag("cripta_step", 0)
                local n = (CDV.Flag("cripta_errori") or 0) + 1
                CDV.Flag("cripta_errori", n)
                if n <= 2 then
                    CDV.Enable("ratto_extra" .. (2 * n - 2))
                    CDV.Enable("ratto_extra" .. (2 * n - 1))
                end
                CDV.Say("Il meccanismo torna indietro e dalle fessure escono i topi!", 4)
            end
        end
        was[key] = on
    end
end)''')
    k.place(K.SHOTGUN_AMMO1, 54, 335, room=H.room)
    lua.secret(8, k.lua_pos(55, 334, fl0), r=800, text="Dietro una colonna della cripta: una Stella dei Dioscuri!")

    for i, (x, z) in enumerate(((49, 341), (55, 341), (49, 335), (55, 335))):
        k.place(K.BIG_RAT, x, z, room=H.room, name="ratto_extra%d" % i)

    # The Astro opens the way down to the sea (Sommersa starts in a sea cave under the cape);
    # Donna Villa's spirits come into the crypt to stop Lara. No more 470 m run back to the Rocca.
    D = k.interior("CRIPTA_DISCESA", ["."] * 9 + ["M"], 51, 343, fl0, 7 * CLICK, *tex, ambient=(0.25, 0.3, 0.34))
    k.link_wall(H, D, span=(51, 51))
    k.place(K.DOOR_TYPE3, *D.anchors["M"], room=D.room, rot=0.0, name="porta_mare")
    for i, (x, z) in enumerate(((48, 336), (54, 341))):
        k.place(K.WRAITH2 if i == 0 else K.WRAITH3, x, z, room=H.room, h=fl0 + 3 * CLICK, name="donna_villa%d" % i)
    lua.zone("astro", k.lua_pos(*H.anchors["N"], fl0), r=1500, dy=1500, need="CDV.Has(ID.PUZZLE_ITEM7)",
             fn='CDV.Enable("donna_villa0")\nCDV.Enable("donna_villa1")\nCDV.Enable("porta_mare")',
             text="Donna Villa! \"L'Astro di Castore e' mio, come quello di Polluce sotto il mare.\" A nord si apre un cunicolo: si sente il mare!")
    lua.zone("discesa", k.lua_pos(51, 351, fl0), r=1500, dy=1500, need="CDV.Has(ID.PUZZLE_ITEM7)",
             text="Il cunicolo scende sotto il capo, fino al mare. Donna Villa e' passata di qui.", fn="CDV.End(6, 1)")
    s2 = k.spot(30, 360)
    lua.secret(9, k.lua_pos(*s2, ctx.ground(*s2)), r=900)
    k.place(K.FLARE_ITEM, *s2)
    ctx.notes += [
        "",
        "LIVELLO 5 - TINDARI",
        "1. Si parte in cima al Sentiero Coda di Volpe. Sul piazzale del santuario tre corvi.",
        "2. ENIGMA E7: dal belvedere (a nord-ovest del santuario) si legge l'ordine: LUNA, STELLA, SOLE.",
        "3. Nel parco archeologico (nord-ovest) tre tombaroli. ENIGMA E8: la leva di Castore alla Basilica e quella",
        "   di Polluce alla Torre vanno attivate entro 30 secondi l'una dall'altra (le fiammelle restano accese 30 s).",
        "   Si apre la botola nell'orchestra del Teatro Greco.",
        "4. Cripta: usare il Sigillo della tonnara sulla porta a ovest. Due ratti.",
        "5. ENIGMA E9: tre leve sul muro nord (da ovest: Sole, Luna, Stella). Tirarle nell'ordine Luna, Stella, Sole.",
        "   La nicchia a ovest si apre: Astro di Castore. Segreto 9: angolo sud-est della sala.",
        "   Ordine sbagliato: il meccanismo si azzera ed escono due topi (alla prima e alla seconda volta).",
        "6. Preso l'Astro entrano due spiriti di Donna Villa e si apre una porta a nord: il cunicolo scende al mare.",
        "   In fondo al cunicolo finisce il livello. Segreto 10 (facoltativo): dietro il teatro, a ovest.",
    ]
