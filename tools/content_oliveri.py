"""Livello 1 - Oliveri (notte).

Casa di Via Gaspare Amodeo 1 (tre piani, botola sul tetto) -> scala sulla facciata -> Piazza 24 Maggio
-> tombino di Via Saia Interna -> La Saia (enigma delle chiuse, E1) -> campo -> rampa nord del castello
-> porta ovest -> cortile (pietre dei Gemelli sulle stelle, E2) -> cisterna (Diario) -> mura (E3) -> fine.
"""
import numpy as np
from scipy import ndimage

import kit as K
from kit import CLICK

# --- coordinates (world sectors) -----------------------------------------------------------
HOUSE_X0, HOUSE_Z0, HOUSE_W, HOUSE_H = 208, 157, 8, 6
G0, H0 = 1344, 1536          # ground floor height and storey heights (units)
H1 = 1536
ROOF = 6208
H2 = ROOF - (G0 + H0 + H1)   # 1792
ROOF_HATCH = (214, 161)
F2_HOLE = (213, 159)         # F2 -> F1
F1_HOLE = (209, 158)         # F1 -> F0
LADDER = (207, 160)          # street sector, climbable wall towards +x

MANHOLE = (197, 102)
SAIA_EXIT = (152, 101)
SAIA_FLOOR = -64

YARD_SEED = (47, 37)
YARD_H = 19968               # 39 m
GATE = K.rect(35, 36, 41, 36)
RAMP = K.rect(33, 38, 34, 72)
CISTERN_HOLE = (47, 35)
PUSH = [((44, 37), (44, 40)), ((49, 37), (49, 40))]   # (pushable start, star tile)
CLIMB_WALL = (52, 38)        # yard sector, wall on +x
E3_SPOT = (55, 38)


def prepare(world):
    # House roof hatch area and street ladder are already flat (roof / pavement).
    K.flatten(world, K.rect(MANHOLE[0] - 1, MANHOLE[1] - 1, MANHOLE[0] + 1, MANHOLE[1] + 1))
    K.flatten(world, K.rect(SAIA_EXIT[0] - 1, SAIA_EXIT[1] - 1, SAIA_EXIT[0] + 1, SAIA_EXIT[1] + 1), mat="terra")
    # Castle: flat courtyard, a gate through the west wall, a ramp up the north slope.
    castle = [i for i, b in enumerate(world.buildings) if b["tags"].get("historic") == "castle"]
    walls_mask = np.isin(world.building_id, castle)
    lab, _ = ndimage.label(~walls_mask)
    yard = lab == lab[YARD_SEED]
    world.yard = yard
    for x, z in zip(*np.nonzero(yard)):
        world.floor[x, z, :] = YARD_H
        world.floor_terrain[x, z, :] = YARD_H
        world.mat[x, z] = "castello_pav"
    for x, z in GATE:
        world.building_id[x, z] = -1
    K.flatten(world, GATE, YARD_H, mat="castello_pav")
    K.flatten(world, K.rect(30, 36, 34, 37), YARD_H, mat="castello_pav")
    bottom = int(world.floor[33, 72].mean()) // 64 * 64
    K.ramp(world, RAMP, "z", 38, 73, YARD_H, bottom)


def house(ctx):
    k = ctx.kit
    x0, z0 = HOUSE_X0, HOUSE_Z0
    # Plans: rows z = 162 (top) .. 157 (bottom), columns x = 208 .. 215.
    f2 = ["...#....",
          ".S.#..r.",
          "........",
          "####....",
          "........",
          "M..#...."]
    f1 = ["........",
          "........",
          "..##....",
          "..#..u..",
          "........",
          "...T...."]
    f0 = ["......#P",
          ".K.#..#.",
          "...#....",
          "........",
          ".v..#...",
          "....#.A."]
    F0 = k.interior("CASA_TERRA", f0, x0, z0, G0, H0, "cementine", "soffitto", "intonaco_interno")
    F1 = k.interior("CASA_PRIMO", f1, x0, z0, G0 + H0, H1, "maiolica", "soffitto", "intonaco_interno")
    F2 = k.interior("CASA_SECONDO", f2, x0, z0, G0 + H0 + H1, H2, "parquet", "soffitto", "intonaco_interno")
    k.link_vertical(F0, F1, [F1_HOLE])
    k.link_vertical(F1, F2, [F2_HOLE])
    roof_room = k.room_at(*ROOF_HATCH)
    k.link_vertical(F2, roof_room, [ROOF_HATCH])
    k.climb(LADDER[0], LADDER[1], "+x")
    return F0, F1, F2


def build(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    F0, F1, F2 = house(ctx)

    # Lara wakes up on the second floor.
    sx, sz = F2.anchors["S"]
    k.place(K.LARA, sx, sz, room=F2.room, rot=180.0, name="lara_start")
    k.place(K.SMALLMEDI, *F2.anchors["M"], room=F2.room)
    k.place(K.FLARE_ITEM, 210, 162, room=F2.room)
    k.place(K.SHOTGUN_ITEM, *F0.anchors["K"], room=F0.room)
    k.place(K.SHOTGUN_AMMO1, *F0.anchors["A"], room=F0.room)
    k.place(K.BADDY2, *F1.anchors["T"], room=F1.room, name="ladro_primo")
    k.place(K.BADDY2, 213, 161, room=F0.room, name="ladro_terra")
    k.place(K.BADDY1, 214, 157, room=F0.room, name="ladro_chiave")
    trap = k.place(K.FLOOR_TRAPDOOR1, ROOF_HATCH[0], ROOF_HATCH[1], name="botola_tetto")

    def at(it, cell, dh=0):
        return k.lua_pos(cell[0], cell[1], it.floor_h + dh)

    lua.start('CDV.Say("Oliveri, notte. Rumori al piano di sotto... qualcuno e\' entrato in casa.", 7)')
    lua.zone("primo", at(F1, F2_HOLE), r=1200, dy=900, fn='CDV.Enable("ladro_primo")',
             text="Uno della banda della Volpe! Cercano il diario bizantino.")
    lua.zone("terra", at(F0, F1_HOLE), r=1400, dy=900, fn='CDV.Enable("ladro_terra")\nCDV.Enable("ladro_chiave")')
    lua.drop("chiave", "ladro_chiave", "ID.PUZZLE_ITEM2",
             "Il tombarolo aveva la chiave della botola della terrazza. Il diario pero' non c'e': l'ha preso il loro capo.")
    lua.zone("portone", at(F0, (215, 160)), r=1200, dy=900, once=True,
             text="Il portone e' sbarrato da fuori. Resta la botola sul tetto.")
    lua.use("botola", "ID.PUZZLE_ITEM2", at(F2, ROOF_HATCH), r=1300, dy=1200,
            text="La botola si apre. Sul tetto!", fn='CDV.Enable("botola_tetto")')
    lua.zone("tetto", k.lua_pos(ROOF_HATCH[0], ROOF_HATCH[1], ROOF), r=1500, dy=900,
             text="Dalla terrazza si scende con la grondaia sul lato di Via Amodeo. Il ladro scappa verso la piazza.")
    ctx.notes += [
        "LIVELLO 1 - OLIVERI",
        "1. Secondo piano: medikit nel bagno, razzi in camera. Il buco nel pavimento del corridoio porta al primo piano.",
        "2. Primo piano: un tombarolo. Il buco vicino alle scale porta al piano terra.",
        "3. Piano terra: due tombaroli; uno lascia la Chiave della terrazza. Fucile in cucina, cartucce nell'ingresso.",
        "   Segreto 1: la dispensa nell'angolo nord-est del piano terra.",
        "4. Si risale sulle casse (salto + aggrappo) fino al secondo piano, si usa la chiave sotto la botola e si sale sul tetto.",
        "5. Dal tetto ci si cala con la grondaia (muro scalabile) sul lato ovest, su Via Amodeo.",
    ]
    lua.secret(0, at(F0, F0.anchors["P"]), r=800)

    # --- piazza 24 Maggio ----------------------------------------------------------------
    k.place(K.DOBERMAN, 188, 178, name="cane1")
    k.place(K.DOBERMAN, 190, 175, name="cane2")
    k.place(K.SMALLMEDI, 186, 176)
    lua.zone("piazza", k.lua_pos(194, 172, ctx.ground(194, 172)), r=9000, dy=4000,
             fn='CDV.Enable("cane1")\nCDV.Enable("cane2")', text="I cani della Volpe!")
    lua.zone("saia_hint", k.lua_pos(190, 176, ctx.ground(190, 176)), r=3000, dy=4000, need='CDV.Dead("cane1") and CDV.Dead("cane2")',
             text="Le tracce del ladro portano a Via Saia Interna, verso il tombino del vecchio canale.")
    ctx.notes += ["6. In Piazza 24 Maggio due dobermann. Le tracce portano a Via Saia Interna (a sud): tombino in mezzo al vicolo."]

    saia(ctx)
    castle(ctx)


def saia(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    # Tunnel A: x 172..200, z 100..104 ; channel along z = 102.
    w = 200 - 172 + 1
    side = "1" * w
    chan = list("." * w)
    chan[MANHOLE[0] - 172] = "m"
    chan[180 - 172] = "R"
    plan_a = [side, side, "".join(chan), side, side]
    A = k.interior("SAIA_A", plan_a, 172, 100, SAIA_FLOOR, 1536, "pietra_bagnata", "soffitto_roccia", "canale_saia")
    # Hall B: x 150..171, z 96..106 ; west chamber x 150..156 behind a gate at x = 157.
    rows = []
    for z in range(106, 95, -1):
        r = []
        for x in range(150, 172):
            if x == 157:
                r.append("." if z == 101 else "#")
            elif x < 157:
                r.append("." if 98 <= z <= 104 else "#")
            else:
                r.append(".")
        rows.append(r)

    def setc(x, z, ch):
        rows[106 - z][x - 150] = ch
    setc(SAIA_EXIT[0], SAIA_EXIT[1], "x")
    setc(150, 98, "N")
    setc(154, 103, "B")
    B = k.interior("SAIA_B", ["".join(r) for r in rows], 150, 96, SAIA_FLOOR, 1536, "pietra_bagnata", "soffitto_roccia", "canale_saia")
    k.link_wall(B, A)
    street = k.room_at(*MANHOLE)
    k.link_vertical(A, street, [MANHOLE])
    field = k.room_at(*SAIA_EXIT)
    k.link_vertical(B, field, [SAIA_EXIT])

    for i, x in enumerate((184, 189, 194)):
        k.place(K.BIG_RAT, x, 103 if i % 2 else 101, room=A.room, name="ratto%d" % i)
    k.place(K.SMALLMEDI, *A.anchors["R"], room=A.room)
    lua.zone("saia", k.lua_pos(MANHOLE[0], MANHOLE[1], SAIA_FLOOR), r=2500, dy=1200,
             text="La Saia: il vecchio canale che scendeva dal castello al mare.",
             fn='CDV.Enable("ratto0")\nCDV.Enable("ratto1")\nCDV.Enable("ratto2")')

    # E1: three levers (Castore, Polluce, Tindaro), each lights a small flame; Castore and Tindaro
    # open, Polluce closed -> the gate opens.
    names = ["castore", "polluce", "tindaro"]
    for i, x in enumerate((161, 165, 169)):
        # Floor levers (TR4 rail switch): used from the south, pushed back from the north.
        lev = k.place(K.LEVER_SWITCH, x, 103, room=B.room, rot=0.0, name="leva_" + names[i])
        fl = k.place(K.FLAME_EMITTER2, x + 1, 103, room=B.room, ocb=1, name="fiamma_" + names[i])
        k.trigger(x, 103, room=B.room, trig_type=K.T_SWITCH, target=lev)
        k.trigger(x, 103, room=B.room, trig_type=K.T_SWITCH, target=fl)
        lua.zone("leva_" + names[i], k.lua_pos(x, 102, SAIA_FLOOR), r=900, dy=1000, once=False, secs=3,
                 text="Leva della chiusa di %s" % ("Castore", "Polluce", "Tindaro")[i])
    k.place(K.DOOR_TYPE3, 157, 101, room=B.room, rot=90.0, name="cancello_saia")
    k.place(K.SHOTGUN_AMMO1, 165, 97, room=B.room)
    k.place(K.BIGMEDI, *B.anchors["B"], room=B.room)
    lua.zone("iscrizione", k.lua_pos(165, 97, SAIA_FLOOR), r=1500, dy=1000, once=False, secs=8,
             text="Inciso sui segni di piena: \"Castore beve, Polluce dorme, Tindaro apre la via.\"")
    lua.loop('''
local c, p, t = CDV.Pulled("leva_castore"), CDV.Pulled("leva_polluce"), CDV.Pulled("leva_tindaro")
if not CDV.Flag("saia_aperta") and c and t and not p then
    CDV.Flag("saia_aperta", true)
    CDV.Enable("cancello_saia")
    CDV.Say("L'acqua scende nel canale giusto: il cancello si apre.", 6)
end''')
    lua.secret(1, k.lua_pos(*B.anchors["N"], SAIA_FLOOR), r=800)
    lua.zone("uscita_saia", k.lua_pos(SAIA_EXIT[0], SAIA_EXIT[1], SAIA_FLOOR), r=1200, dy=1200,
             text="Su per il tombino: si esce nel campo sotto il castello.")
    ctx.notes += [
        "7. La Saia: tre ratti. Nella sala delle chiuse tre leve (Castore, Polluce, Tindaro), ognuna accende una fiammella.",
        "   ENIGMA E1: iscrizione \"Castore beve, Polluce dorme, Tindaro apre la via\": leve di Castore e Tindaro alzate,",
        "   quella di Polluce abbassata. Il cancello a ovest si apre.",
        "   Segreto 2: nicchia nell'angolo sud-ovest della camera dietro il cancello.",
        "8. Si sale dal tombino nel campo e si va a ovest verso il castello.",
    ]


def castle(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    world = ctx.world
    # Field guards near the ramp.
    k.place(K.BADDY1, 40, 74, name="vedetta1")
    k.place(K.BADDY2, 36, 66, name="vedetta2")
    lua.zone("campo", k.lua_pos(60, 80, ctx.ground(60, 80)), r=12000, dy=6000,
             fn='CDV.Enable("vedetta1")\nCDV.Enable("vedetta2")',
             text="Il castello di Oliveri. La rampa sale dal lato nord.")
    k.place(K.SMALLMEDI, 34, 60)
    # Courtyard: the thief, two Gemini stones and their stars.
    k.place(K.BADDY1, 47, 41, name="capo_ladri")
    lua.zone("cortile", k.lua_pos(41, 36, YARD_H), r=1500, dy=1500, fn='CDV.Enable("capo_ladri")',
             text="Il capo dei ladri! Ha qualcosa in mano...")
    lua.zone("morto_capo", k.lua_pos(47, 38, YARD_H), r=6000, dy=2000, need='CDV.Dead("capo_ladri")',
             text="Prima di cadere ha gettato il diario nella cisterna. La botola si apre solo con le due pietre dei Gemelli sulle stelle.")
    trap = k.place(K.FLOOR_TRAPDOOR1, CISTERN_HOLE[0], CISTERN_HOLE[1], name="botola_cisterna")
    for i, (start, star) in enumerate(PUSH):
        k.place(K.PUSHABLE, start[0], start[1], name="pietra%d" % i)
        bits = 0x03 if i == 0 else 0x1C
        k.trigger(star[0], star[1], trig_type=K.T_HEAVY, target=trap, code_bits=bits, one_shot=True)
        room = k.room_at(*star)
        sec = room.sectors[star[0] - room.x][star[1] - room.z]
        import walls
        walls.set_floor(sec, ctx.atlases, "stella_dioscuri")
    lua.zone("stelle", k.lua_pos(46, 40, YARD_H), r=2500, dy=1500, once=True,
             text="Due stelle incise nel lastricato: Castore e Polluce. Le pietre vanno spinte sopra.")

    # Cistern: air room with ledges and a pool, water room below.
    cx0, cz0 = 44, 31
    air_plan = [
        "1111111",
        "1111111",
        "111c111",   # z = 35 : hole at x = 47 -> crate on the ledge
        "1.....1",
        "1.....1",
        "1.....1",
        "1111111",
    ]
    air_h = YARD_H - 7 * CLICK
    AIR = k.interior("CISTERNA", air_plan, cx0, cz0, air_h, 7 * CLICK, "pietra_bagnata", "soffitto_roccia", "pietra_viva")
    # the crate cell: ledge 1 click + crate 2 clicks
    s = AIR.sector(*CISTERN_HOLE)
    s.floor = [3 * CLICK] * 4
    water_plan = ["#######", "#######", "#######", "#.....#", "#.....#", "#..D..#", "#######"]
    WAT = k.interior("CISTERNA_ACQUA", water_plan, cx0, cz0, air_h - 4 * 512, 4 * 512, "pietra_bagnata", "pietra_bagnata",
                     "pietra_viva", water=True, ambient=(0.3, 0.42, 0.45))
    k.water_surface(AIR, WAT, K.rect(45, 32, 49, 34))
    yard_room = k.room_at(*CISTERN_HOLE)
    k.link_vertical(AIR, yard_room, [CISTERN_HOLE])
    k.place(K.PUZZLE_ITEM[1], *WAT.anchors["D"], room=WAT.room, name="diario")
    k.place(K.BAT, 45, 36, room=AIR.room, h=air_h + 5 * CLICK, name="pipistrello1")
    k.place(K.BAT, 49, 36, room=AIR.room, h=air_h + 5 * CLICK, name="pipistrello2")
    lua.zone("cisterna", k.lua_pos(CISTERN_HOLE[0], CISTERN_HOLE[1], air_h + 3 * CLICK), r=1500, dy=1500,
             fn='CDV.Enable("pipistrello1")\nCDV.Enable("pipistrello2")', text="La cisterna del castello. Il diario e' sul fondo.")
    lua.secret(2, k.lua_pos(45, 36, air_h + CLICK), r=700)

    # E3: on the walls, read the diary against the coast.
    k.climb(CLIMB_WALL[0], CLIMB_WALL[1], "+x")
    roof_h = int(world.floor[E3_SPOT].mean())
    lua.zone("mura", k.lua_pos(E3_SPOT[0], E3_SPOT[1], roof_h), r=3000, dy=1500, need="CDV.Has(ID.PUZZLE_ITEM1)",
             text="Da qui si vede tutta la costa fino a Capo Tindari. E' il momento di usare il diario.")
    lua.use("diario_mura", "ID.PUZZLE_ITEM1", k.lua_pos(E3_SPOT[0], E3_SPOT[1], roof_h), r=3500, dy=1500, consume=False,
            text="La griglia del diario sovrapposta alla costa: il segno cade sul Casello di Marinello. La' scava la Volpe.",
            fn='CDV.Flag("fine", 0)')
    lua.loop('''
local t = CDV.Flag("fine")
if t ~= nil then
    t = t + 1
    CDV.Flag("fine", t)
    if t == 240 then CDV.End(2, 1) end
end''')
    ctx.notes += [
        "9. Nel campo due vedette. Una rampa sale dal lato nord-ovest del colle fino al pianoro, poi la porta ovest del castello.",
        "10. Nel cortile il capo dei ladri. ENIGMA E2: spingere le due pietre verso nord sulle stelle incise",
        "    (pietra ovest e pietra est, tre spinte ciascuna). La botola della cisterna si apre.",
        "11. Cisterna: due pipistrelli, il Diario bizantino sul fondo dell'acqua. Segreto 3: sul cornicione a nord-ovest.",
        "    Si risale con la cassa sotto la botola.",
        "12. ENIGMA E3: muro scalabile sul lato est del cortile. In cima alle mura usare il Diario: indica il Casello di Marinello.",
    ]
