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
# The rooms of the house are built 57.5 m under the street (the real house is rotated 44 degrees to
# the grid): see casa.py. Storeys 3 m, the second floor 3.5 m with a raised step under the hatch.
G0 = -29440
H0 = H1 = 1536
H2 = 1792
HATCH = (213, 160)           # second floor, ceiling trapdoor to the stair box on the roof
STAIR0 = [(209, 162), (210, 162), (211, 162)]     # ground -> first, rising east
STAIR1 = [(211, 161), (210, 161), (209, 161)]     # first -> second, rising west

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
    prepare_casa(world)
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


def prepare_casa(world):
    """The house block: only the sectors entirely inside the footprint stay solid (plus the ones that
    lean on the neighbours); the others go back to the street, under the static facades."""
    import casa
    bid = int(world.building_id[212, 160])
    full = casa.full_sectors()
    P = casa.POLY
    for x, z in zip(*np.nonzero(world.building_id == bid)):
        if (x, z) in full:
            continue
        c = (x + 0.5, z + 0.5)

        def dist(i):
            (ax, az), (bx, bz) = P[i], P[(i + 1) % len(P)]
            t = max(0.0, min(1.0, ((c[0] - ax) * (bx - ax) + (c[1] - az) * (bz - az)) / ((bx - ax) ** 2 + (bz - az) ** 2)))
            return np.hypot(c[0] - ax - t * (bx - ax), c[1] - az - t * (bz - az))
        if min(range(len(P)), key=dist) in (0, 1):
            continue
        world.building_id[x, z] = -1
        world.floor[x, z] = world.floor_terrain[x, z]
        world.mat[x, z] = "marciapiede"
    world.casa_bid = bid


def house(ctx):
    """Three floors with real stairs (ramps under marble steps), furniture, windows and doors."""
    k = ctx.kit
    x0, z0 = HOUSE_X0, HOUSE_Z0
    # Plans: rows z = 162 (top) .. 157 (bottom), columns x = 208 .. 215.
    f0 = ["....#..P",       # stairs up (209-211), dispensa (secret) behind the kitchen
          "....#...",
          ".K..##.#",
          "........",       # kitchen + dining (north), living room (south-east)
          "###.#...",
          "..A.#.E."]       # entrance hall with the barred street door
    f1 = ["........",       # stairwell from the ground floor at 210-211
          "....#...",       # stairs up (211 -> 209)
          ".....#..",
          "##.###.#",
          "...T....",       # living room with the balcony (south), study (north-east)
          "........"]
    f2 = ["...#....",       # stairwell at 209-210, arrival at 208
          "...#....",
          "...#.1..",       # box room with the roof hatch (raised step under it)
          "##.##.##",
          ".S......",       # Ed's bedroom
          "M..#...."]       # bathroom
    F0 = k.interior("CASA_TERRA", f0, x0, z0, G0, H0, "cementine", "soffitto", "intonaco_interno",
                    ambient=(0.32, 0.3, 0.34))
    F1 = k.interior("CASA_PRIMO", f1, x0, z0, G0 + H0, H1, "maiolica", "soffitto", "intonaco_interno",
                    ambient=(0.32, 0.3, 0.34))
    F2 = k.interior("CASA_SECONDO", f2, x0, z0, G0 + H0 + H1, H2, "parquet", "soffitto", "intonaco_interno",
                    ambient=(0.32, 0.3, 0.34))
    TOP = k.interior("CASA_BOTOLA", ["..", ".."], HATCH[0], HATCH[1], G0 + H0 + H1 + H2, 4 * CLICK,
                     "cementine", "soffitto", "intonaco_interno", ambient=(0.4, 0.4, 0.45))

    def ramp(it, cells, step):
        """Ramp rising 2 clicks per sector; step = +1 (east) or -1 (west). Corner order XnZp, XpZp, XpZn, XnZn."""
        for i, (wx, wz) in enumerate(cells):
            s = it.room.sectors[wx - it.room.x][wz - it.room.z]
            lo, hi = i * 2 * CLICK, (i + 1) * 2 * CLICK
            s.floor = [lo, hi, hi, lo] if step > 0 else [hi, lo, lo, hi]
    k.link_vertical(F0, F1, STAIR0[1:])
    k.link_vertical(F1, F2, STAIR1[1:])
    ramp(F0, STAIR0, +1)
    ramp(F1, STAIR1, -1)
    k.link_vertical(F2, TOP, [HATCH])
    return F0, F1, F2, TOP


# Furniture: (name, x, z, rot, floor) in world sectors (floats). rot 0 = model +X towards east.
CASA_FURNITURE = [
    # ground floor
    ("CASA_CUCINA", 208.32, 160.6, 0.0, 0), ("CASA_FRIGO", 208.35, 161.75, 0.0, 0),
    ("CASA_TAVOLO", 210.4, 160.3, 0.0, 0), ("CASA_SCAFFALE", 215.8, 162.0, 180.0, 0),
    ("CASA_DIVANO", 215.55, 158.5, 180.0, 0), ("CASA_TAVOLINO", 214.4, 158.5, 0.0, 0),
    ("CASA_MOBILE_TV", 213.25, 158.5, 0.0, 0), ("CASA_QUADRO", 213.02, 157.9, 0.0, 0),
    ("CASA_SEDIA_ROVESCIATA", 211.0, 159.3, 30.0, 0), ("CASA_PORTONE_INT", 212.0, 157.02, 270.0, 0),
    ("CASA_GRADINI", 210.5, 162.5, 0.0, 0),
    # first floor
    ("CASA_LIBRERIA", 215.8, 161.6, 180.0, 1), ("CASA_SCRIVANIA", 214.6, 161.7, 180.0, 1),
    ("CASA_SEDIA_ROVESCIATA", 214.0, 160.9, 120.0, 1), ("CASA_LIBRERIA", 213.25, 161.0, 0.0, 1),
    ("CASA_DIVANO", 208.45, 158.0, 0.0, 1), ("CASA_TAVOLINO", 209.6, 158.0, 0.0, 1),
    ("CASA_QUADRO", 208.02, 158.0, 0.0, 1), ("CASA_GRADINI", 210.5, 161.5, 180.0, 1),
    ("CASA_CORRIMANO", 211.0, 162.0, 0.0, 1), ("CASA_CORRIMANO", 210.0, 162.5, 90.0, 1),
    # second floor
    ("CASA_LETTO", 208.55, 158.0, 0.0, 2), ("CASA_COMODINO", 208.25, 158.85, 0.0, 2),
    ("CASA_COMODINO", 208.25, 157.15, 0.0, 2), ("CASA_ARMADIO", 211.25, 158.0, 180.0, 2),
    ("CASA_BAGNO", 210.55, 157.6, 90.0, 2), ("CASA_SCAFFALE", 215.8, 161.5, 180.0, 2),
    ("CASA_CORRIMANO", 210.0, 161.0, 0.0, 2), ("CASA_CORRIMANO", 210.0, 162.0, 0.0, 2),
    ("CASA_QUADRO", 208.02, 159.6, 0.0, 2),
]
# Windows (inside view) on the outer walls, and interior door frames in the doorways.
CASA_WINDOWS = [(208.0, 159.5, 0.0), (213.0, 157.0, 270.0), (215.0, 157.0, 270.0), (216.0, 159.5, 180.0),
                (210.0, 157.0, 270.0)]
CASA_DOORS = {0: [(211.5, 158.5, 90.0), (214.5, 160.5, 90.0)],
              1: [(210.5, 159.5, 90.0), (214.5, 159.5, 90.0)],
              2: [(210.5, 159.5, 90.0)]}


def street_dressing(ctx):
    """Via Gaspare Amodeo as on Street View: cars parked along the kerb opposite the house, palms and
    big white pots on the pavement, a couple of scooters by the door."""
    import math
    import casa
    k, w = ctx.kit, ctx.world
    (ax, az), (bx, bz) = casa.POLY[3], casa.POLY[4]
    L = math.hypot(bx - ax, bz - az)
    d = ((bx - ax) / L, (bz - az) / L)
    n = (d[1], -d[0])                     # outward (south-west) normal of the facade
    rot_car = math.degrees(math.atan2(d[0], d[1]))
    cx, cz, _ = casa.climb_spot()

    def free(x, z, r=1):
        xi, zi = int(x), int(z)
        if not (0 <= xi < w.nx and 0 <= zi < w.nz):
            return False
        if abs(xi - cx) <= 1 and abs(zi - cz) <= 1:
            return False
        return all(0 <= xi + i < w.nx and 0 <= zi + j < w.nz and w.building_id[xi + i, zi + j] < 0 and not w.water[xi + i, zi + j]
                   for i in range(-r, r + 1) for j in range(-r, r + 1))
    cars = ["AUTO_UTILITARIA_BIANCA", "AUTO_BERLINA_GRIGIA", "AUTO_UTILITARIA_ROSSA", "FURGONE_BIANCO", "AUTO_SUV_BLU"]
    i = 0
    for t in (-6.0, -3.2, 2.2, 5.0, 10.5, 13.3):     # parked along the kerb on the house side (satellite view)
        x, z = ax + d[0] * t + n[0] * 2.4, az + d[1] * t + n[1] * 2.4
        if free(x, z):
            k.prop(cars[i % len(cars)], x, z, rot=rot_car + (180 if i % 2 else 0))
            i += 1
    for t, name in ((0.8, "VASO_BIANCO_PALMA"), (7.6, "VASO_BIANCO_PALMA"), (8.6, "VASO_BIANCO_FIORI")):
        x, z = ax + d[0] * t + n[0] * 1.4, az + d[1] * t + n[1] * 1.4
        if free(x, z, 0):
            k.prop(name, x, z, rot=rot_car)
    for t, name in ((6.2, "SCOOTER_ROSSO"), (6.9, "SCOOTER_CREMA")):
        x, z = ax + d[0] * t + n[0] * 1.6, az + d[1] * t + n[1] * 1.6
        if free(x, z, 0):
            k.prop(name, x, z, rot=rot_car + 90)


def house_dressing(ctx, floors):
    k = ctx.kit
    for name, x, z, rot, f in CASA_FURNITURE:
        it = floors[f]
        k.prop(name, x, z, rot=rot, h=it.floor_h, room=it.room)
    for f, it in enumerate(floors[:3]):
        for x, z, rot in CASA_WINDOWS:
            k.prop("CASA_FINESTRA", x, z, rot=rot, h=it.floor_h, room=it.room)
        for x, z, rot in CASA_DOORS.get(f, []):
            k.prop("CASA_PORTA", x, z, rot=rot, h=it.floor_h, room=it.room)
        for lx, lz in ((210.0, 160.0), (214.0, 158.5), (214.0, 161.5)):
            pos = ((lx - it.room.x) * 1024, 1100, (lz - it.room.z) * 1024)
            ctx.level.add_light(it.room, 0, pos, color=(1.0, 0.82, 0.6), intensity=0.6, inner=1.5, outer=5.0)


DECOR = dict(centre=(190, 160, 70))


def build(ctx):
    ctx.decor_block = [(30, 34, 37, 74), (34, 35, 42, 38), (39, 30, 54, 45), (205, 155, 218, 165)]
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    street_dressing(ctx)
    import casa
    F0, F1, F2, TOP = house(ctx)
    house_dressing(ctx, (F0, F1, F2, TOP))
    k.prop("CASA_ESTERNO", *casa.ANCHOR, rot=0.0, h=casa.GROUND)
    cx, cz, _ = casa.climb_spot()
    k.climb(cx, cz, "+z")

    # Lara wakes up on the second floor.
    sx, sz = F2.anchors["S"]
    k.place(K.LARA, sx, sz, room=F2.room, rot=180.0, name="lara_start")
    k.place(K.SMALLMEDI, *F2.anchors["M"], room=F2.room)
    k.place(K.FLARE_ITEM, 210, 162, room=F2.room)
    k.place(K.SHOTGUN_ITEM, *F0.anchors["K"], room=F0.room)
    k.place(K.SHOTGUN_AMMO1, *F0.anchors["A"], room=F0.room)
    k.place(K.BADDY2, *F1.anchors["T"], room=F1.room, name="ladro_primo")
    k.place(K.BADDY2, 214, 159, room=F0.room, name="ladro_terra")
    k.place(K.BADDY1, 209, 157, room=F0.room, name="ladro_chiave")
    k.place(K.CEILING_TRAPDOOR1, HATCH[0], HATCH[1], room=TOP.room, name="botola_tetto")
    k.place(K.DOOR_TYPE3, 213, 159, room=F2.room, rot=0.0, name="porta_ripostiglio")

    def at(it, cell, dh=0):
        return k.lua_pos(cell[0], cell[1], it.floor_h + dh)

    rx, rz = casa.roof_spot()
    roof_room = k.room_at(rx, rz)
    lua.start('CDV.Say("Oliveri, notte. Rumori al piano di sotto... qualcuno e\' entrato in casa.", 7)')
    lua.zone("primo", at(F1, (212, 162)), r=1400, dy=900, fn='CDV.Enable("ladro_primo")',
             text="Uno della banda della Volpe! Cercano il diario bizantino.")
    lua.zone("terra", at(F0, (212, 161)), r=1600, dy=900, fn='CDV.Enable("ladro_terra")\nCDV.Enable("ladro_chiave")')
    lua.drop("chiave", "ladro_chiave", "ID.PUZZLE_ITEM2",
             "Il tombarolo aveva la chiave del ripostiglio della terrazza. Il diario pero' non c'e': l'ha preso il loro capo.")
    lua.zone("portone", at(F0, F0.anchors["E"]), r=1200, dy=900, once=True,
             text="Il portone e' sbarrato da fuori. Resta la botola del ripostiglio, sul tetto.")
    lua.zone("ripostiglio_chiuso", at(F2, (213, 158)), r=1100, dy=900, once=False, secs=4,
             need="not CDV.Has(ID.PUZZLE_ITEM2) and not CDV.Flag(\"ripostiglio\")",
             text="Il ripostiglio della botola e' chiuso a chiave. I ladri l'avranno presa...")
    lua.use("ripostiglio", "ID.PUZZLE_ITEM2", at(F2, (213, 158)), r=1300, dy=1200,
            text="La chiave gira: il ripostiglio. Sopra il gradino c'e' la botola del tetto: salto e la tiro giu'.",
            fn='CDV.Enable("porta_ripostiglio")\nCDV.Flag("ripostiglio", true)')
    lua.zone("sul_tetto", at(TOP, (HATCH[0] + 1, HATCH[1] + 1)), r=900, dy=700, once=False,
             fn='CDV.Teleport(%d, %d, %d, "%s", 225)' % (k.lua_pos(rx, rz, casa.ROOF) + (roof_room.name,)))
    lua.zone("tetto", k.lua_pos(rx, rz, casa.ROOF), r=1800, dy=900,
             text="Sulla terrazza. Dal lato di Via Amodeo si scende lungo il pluviale, nella rientranza della facciata.")
    ctx.notes += [
        "LIVELLO 1 - OLIVERI",
        "1. Secondo piano: Lara si sveglia in camera. Medikit in bagno, razzi vicino alle scale.",
        "   Le scale (sul lato nord) scendono al primo piano: soggiorno col balcone e lo studio messo a soqquadro.",
        "2. Primo piano: un tombarolo. Altre scale scendono al piano terra.",
        "3. Piano terra: due tombaroli; uno lascia la Chiave del ripostiglio. Fucile in cucina, cartucce nell'ingresso.",
        "   Segreto 1: la dispensa nell'angolo nord-est del piano terra (dietro la cucina).",
        "4. Si risale al secondo piano, si apre il ripostiglio con la chiave: dal gradino si salta e si tira giu'",
        "   la botola del soffitto (Azione durante il salto), poi si salta di nuovo, ci si aggrappa al bordo e si sale.",
        "5. Sulla terrazza (pergolato). Dal lato di Via Amodeo, nella rientranza col pluviale, ci si cala lungo il muro.",
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
    # Via Saia Interna (about 150 m of street): the thief with the diary has left a man behind
    # to cover his escape, shooting from a corner.
    k.place(K.BADDY1, *k.spot(197, 128), rot=0.0, name="copertura")
    lua.zone("vicolo", k.lua_pos(*k.spot(195, 145), ctx.ground(195, 145)), r=6000, dy=5000,
             fn='CDV.Enable("copertura")', text="Uno della banda copre la fuga del ladro!")
    ctx.notes += ["6. In Piazza 24 Maggio due dobermann. Le tracce portano a Via Saia Interna (a sud): tombino in mezzo al vicolo.",
                  "   Nel vicolo un uomo della banda copre la fuga del ladro."]

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
        "8. Si sale dal tombino nel campo e si va a ovest verso il castello. A meta' campo, tra gli ulivi,",
        "   due cani e una guardia.",
    ]


def castle(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    world = ctx.world
    # Field guards near the ramp.
    k.place(K.BADDY1, 40, 74, name="vedetta1")
    k.place(K.BADDY2, 36, 66, name="vedetta2")
    lua.zone("campo", k.lua_pos(60, 80, ctx.ground(60, 80)), r=12000, dy=6000,
             fn='CDV.Enable("vedetta1")\nCDV.Enable("vedetta2")\nCDV.Enable("vedetta3")',
             text="Il castello di Oliveri. La rampa sale dal lato nord.")
    # Halfway across the field (Saia exit -> castle is about 240 m): the gang's dogs come out of the
    # olive grove, and a third man watches from the top of the ramp.
    for i, (x, z) in enumerate(((98, 92), (102, 84))):
        k.place(K.DOBERMAN, *k.spot(x, z), name="cane_campo%d" % i)
    k.place(K.BADDY1, *k.spot(110, 88), name="guardia_campo")
    k.place(K.SHOTGUN_AMMO1, *k.spot(104, 90))
    lua.zone("campo_cani", k.lua_pos(*k.spot(120, 94), ctx.ground(120, 94)), r=9000, dy=6000,
             fn='CDV.Enable("cane_campo0")\nCDV.Enable("cane_campo1")\nCDV.Enable("guardia_campo")',
             text="Cani tra gli ulivi! La banda sorveglia il campo.")
    k.place(K.BADDY2, *k.spot(36, 74), name="vedetta3")
    # Courtyard: the thief, two Gemini stones and their stars.
    k.place(K.BADDY1, 47, 41, name="capo_ladri")
    lua.zone("cortile", k.lua_pos(41, 36, YARD_H), r=1500, dy=1500, fn='CDV.Enable("capo_ladri")',
             text="Il capo dei ladri! Ha qualcosa in mano...")
    lua.zone("morto_capo", k.lua_pos(47, 38, YARD_H), r=6000, dy=2000, need='CDV.Dead("capo_ladri")',
             text="Prima di cadere ha gettato il diario nella cisterna. La botola e' chiusa da un meccanismo.")
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
             text="Due stelle incise nel lastricato, con i nomi di Castore e Polluce.")

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
        "9. Sotto il castello tre vedette. Una rampa sale dal lato nord-ovest del colle fino al pianoro, poi la porta ovest del castello.",
        "10. Nel cortile il capo dei ladri. ENIGMA E2: spingere le due pietre verso nord sulle stelle incise",
        "    (pietra ovest e pietra est, tre spinte ciascuna). La botola della cisterna si apre.",
        "11. Cisterna: due pipistrelli, il Diario bizantino sul fondo dell'acqua. Segreto 3: sul cornicione a nord-ovest.",
        "    Si risale con la cassa sotto la botola.",
        "12. ENIGMA E3: muro scalabile sul lato est del cortile. In cima alle mura usare il Diario: indica il Casello di Marinello.",
    ]
