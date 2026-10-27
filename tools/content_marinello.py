"""Livello 3 - Marinello.

Arrivo da sud -> Casello FS (base della Volpe: guardiano con la chiave, ufficio chiuso, Mappa delle maree)
-> lungo la spiaggia fino alla Grotta di Donna Villa -> bivio del canto (E6) -> sala del pozzo, Donna Villa
appare, Conchiglia del canto -> il "balcone": camino scalabile e uscita sulla rupe -> fine.
"""
import kit as K
from kit import CLICK

START = (232, 30)
CASELLO_DOOR_OUT = (203, 66)
CASELLO_ARRIVE_OUT = (203, 63)
ENTRANCE = (224, 157)
EXIT = (234, 181)


def prepare(world):
    K.flatten(world, K.rect(ENTRANCE[0] - 1, ENTRANCE[1] - 1, ENTRANCE[0] + 1, ENTRANCE[1] + 1), mat="terra")
    K.flatten(world, K.rect(EXIT[0] - 1, EXIT[1] - 1, EXIT[0] + 1, EXIT[1] + 1), mat="roccia")


DECOR = dict(boats=20)


def build(ctx):
    ctx.decor_block = [(194, 58, 214, 78)]
    k, lua = ctx.kit, ctx.lua
    sx, sz = k.spot(*START)
    k.place(K.LARA, sx, sz, rot=0.0, name="lara_start")
    k.place(K.LARA_START_POS, sx, sz, ocb=1)
    lua.start('CDV.Say("Marinello. Il Casello FS, la base della Volpe, e\' davanti a me.", 6)')
    casello(ctx)
    grotta(ctx)


def casello(ctx):
    k, lua = ctx.kit, ctx.lua
    g = 3776   # ground floor of the Casello (7.4 m), rounded to 64
    plan = ["..#...",
            "M.D...",
            "..#...",
            "P.#.E."]
    C = k.interior("CASELLO", plan, 200, 68, g, 7 * CLICK, "cemento", "soffitto", "intonaco_interno")
    k.place(K.DOOR_TYPE3, *C.anchors["D"], room=C.room, rot=90.0, name="porta_ufficio")
    k.place(K.PUZZLE_ITEM[3], *C.anchors["P"], room=C.room, name="mappa")
    k.place(K.UZI_AMMO, *C.anchors["M"], room=C.room)
    k.place(K.BADDY1, 204, 71, room=C.room, name="casellante")
    k.place(K.SMALLMEDI, 205, 70, room=C.room)
    # Yard guard with the key, and a dog.
    k.place(K.BADDY2, *k.spot(208, 64), name="guardiano")
    k.place(K.DOBERMAN, *k.spot(196, 62), name="cane_casello")
    lua.zone("cortile_casello", k.lua_pos(203, 60, ctx.ground(*k.spot(203, 60))), r=9000, dy=4000,
             fn='CDV.Enable("guardiano")\nCDV.Enable("cane_casello")', text="La base della Volpe. Uomini armati!")
    lua.drop("chiave_casello", "guardiano", "ID.PUZZLE_ITEM4", "Il guardiano aveva la Chiave del Casello.")
    ex, ez = C.anchors["E"]
    out = k.spot(*CASELLO_ARRIVE_OUT)
    door_out = k.spot(*CASELLO_DOOR_OUT)
    inside = k.lua_pos(203, 69, g)
    outside = k.lua_pos(*out, ctx.ground(*out))
    lua.zone("entra_casello", k.lua_pos(*door_out, ctx.ground(*door_out)), r=650, dy=1200, once=False,
             fn="CDV.Teleport(%d, %d, %d, \"CASELLO\", 0)\nCDV.Enable(\"casellante\")" % inside)
    lua.zone("esci_casello", k.lua_pos(ex, ez, g), r=600, dy=1200, once=False,
             fn="CDV.Teleport(%d, %d, %d, \"%s\", 180)" % (outside + (k.room_at(*out).name,)))
    lua.use("ufficio", "ID.PUZZLE_ITEM4", k.lua_pos(203, 70, g), r=1500, dy=1200,
            text="La chiave gira. L'ufficio di Turi 'a Vulpi.", fn='CDV.Enable("porta_ufficio")')
    lua.zone("mappa_presa", k.lua_pos(201, 69, g), r=2500, dy=1200, need="CDV.Has(ID.PUZZLE_ITEM3)",
             text="Una carta delle maree con la scrittura di Turi: \"Grotta di Donna Villa - il canto - il balcone\".")
    ctx.notes += [
        "",
        "LIVELLO 3 - MARINELLO",
        "1. Al Casello FS un guardiano e un cane. Il guardiano lascia la Chiave del Casello.",
        "2. La porta del Casello e' sul lato sud: dentro un uomo della Volpe. La chiave apre l'ufficio a ovest:",
        "   Mappa delle maree e munizioni Uzi. Si esce dalla stessa porta (angolo sud-est della stanza).",
    ]


def grotta(ctx):
    k, lua = ctx.kit, ctx.lua
    h_e = ctx.ground(*ENTRANCE)
    fc = (h_e - 2048) // 64 * 64
    hh = 7 * CLICK
    tex = ("grotta_pav", "soffitto_roccia", "roccia_grotta")

    def cave(name, plan, x0, z0, height=hh, floor=fc):
        return k.interior(name, plan, x0, z0, floor, height, *tex, ambient=(0.3, 0.3, 0.34), tags=("grotta",))

    # Atrium (x 218..226, z 153..160), entrance hole at (224,157) with a rock under it.
    ga = ["." * 9 for _ in range(8)]
    ga = [list(r) for r in ga]
    ga[160 - 157][224 - 218] = "e"
    GA = cave("GROTTA_ATRIO", ["".join(r) for r in ga], 218, 153)
    surf = k.room_at(*ENTRANCE)
    k.link_vertical(GA, surf, [ENTRANCE])
    # Junction (x 206..217, z 153..160).
    gb = [list("." * 12) for _ in range(8)]
    gb[160 - 157][210 - 206] = "J"
    GB = cave("GROTTA_BIVIO", ["".join(r) for r in gb], 206, 153)
    k.link_wall(GB, GA)
    # North tunnel (correct) x 214..217, z 161..175; rises 2 clicks halfway as a rocky step.
    gn = []
    for z in range(175, 160, -1):
        gn.append("...." if z < 168 else "1111")
    GN = cave("GROTTA_NORD", gn, 214, 161)
    k.link_wall(GB, GN)
    # South tunnel (wrong): spikes at the end, x 208..211, z 140..152.
    gs = []
    for z in range(152, 139, -1):
        gs.append("...." if z > 143 else "SSSS")
    GS = cave("GROTTA_SUD", gs, 208, 140)
    k.link_wall(GS, GB)
    for x in range(208, 212):
        for z in range(140, 144):
            k.place(K.TEETH_SPIKES, x, z, room=GS.room, ocb=1)
    # West tunnel (wrong, but the secret is at its end): boulder trap, x 196..205, z 155..158.
    gw = ["..........", "..........", "..........", ".........."]
    GW = cave("GROTTA_OVEST", gw, 196, 155)
    k.link_wall(GW, GB)
    ball = k.place(K.ROLLINGBALL, 197, 157, room=GW.room, rot=90.0, name="masso")
    k.trigger(201, 155, room=GW.room, target=ball, size=(1, 4), one_shot=True)
    lua.secret(5, k.lua_pos(196, 156, fc), r=800,
               text="Ossa di un cervo estinto e graffi sulla roccia: la leggenda di Donna Villa ha un fondo vero. Una Stella dei Dioscuri!")
    k.place(K.SHOTGUN_AMMO1, 196, 158, room=GW.room)

    # Hall of the well (x 214..231, z 176..186) with a pool for the wraith, the altar and the door east.
    rows = []
    for z in range(186, 175, -1):
        r = []
        for x in range(214, 232):
            if x == 231:
                r.append("." if z == 181 else "#")
            elif 218 <= x <= 221 and 178 <= z <= 181:
                r.append("~")
            else:
                r.append(".")
        rows.append(r)
    rows[186 - 185][216 - 214] = "A"
    rows[186 - 181][231 - 214] = "D"
    plan3 = ["".join(r).replace("~", ".") for r in rows]
    G3 = cave("GROTTA_POZZO", plan3, 214, 176, height=9 * CLICK)
    k.link_wall(GN, G3)
    W3 = k.interior("GROTTA_POZZO_ACQUA", ["####", "####", "####", "####"], 218, 178, fc - 1536, 1536,
                    "sabbia_fondo", "soffitto_roccia", "roccia_grotta", water=True, ambient=(0.25, 0.32, 0.36))
    for x in range(218, 222):
        for z in range(178, 182):
            W3.sector(x, z).wall = False
    k.water_surface(G3, W3, K.rect(218, 178, 221, 181))
    k.place(K.PUZZLE_ITEM[5], *G3.anchors["A"], room=G3.room, name="conchiglia")
    k.place(K.WRAITH1, 225, 184, room=G3.room, h=fc + 3 * CLICK, name="donna_villa_spirito")
    k.place(K.DOOR_TYPE3, *G3.anchors["D"], room=G3.room, rot=90.0, name="porta_balcone")
    k.place(K.FIREFLY_EMITTER, 215, 162, room=GN.room, ocb=6)
    k.place(K.BIGMEDI, 229, 177, room=G3.room)

    # The "balcone": landing, chimney with a climbable face, high ledge under the exit hole.
    h_exit = ctx.ground(*EXIT)
    ledge = (h_exit - 7 * CLICK - fc) // CLICK * CLICK
    cam = k.interior("GROTTA_BALCONE", ["..L"], 232, 181, fc, ledge + 7 * CLICK, *tex, ambient=(0.35, 0.35, 0.38))
    cam.sector(234, 181).floor = [ledge] * 4
    k.link_wall(G3, cam)
    k.climb(233, 181, "+x", room=cam.room)
    k.link_vertical(cam, k.room_at(*EXIT), [EXIT])

    # Logic.
    lua.zone("grotta", k.lua_pos(*ENTRANCE, fc), r=1500, dy=1500,
             text="La Grotta di Donna Villa. Dicono che col suo canto attirasse i marinai nel pozzo.")
    lua.zone("bivio", k.lua_pos(210, 157, fc), r=2500, dy=1500,
             text="Tre gallerie. Un canto lontano, dolcissimo... sembra venire da dove danzano le lucciole.")
    lua.zone("sud_ossa", k.lua_pos(209, 146, fc), r=1200, dy=1500, text="Il pavimento e' coperto di ossa. Non e' la strada giusta.")
    lua.zone("pozzo", k.lua_pos(216, 178, fc), r=2500, dy=2000, fn='CDV.Enable("donna_villa_spirito")',
             text="\"Chi cerca gli Astri, trova me.\" Lo spirito di Donna Villa! L'acqua lo dissolve.")
    lua.use("balcone", "ID.PUZZLE_ITEM5", k.lua_pos(230, 181, fc), r=1800, dy=1500, consume=True,
            text="La conchiglia vibra col canto e la porta di pietra si apre: il balcone di Donna Villa.",
            fn='CDV.Enable("porta_balcone")')
    lua.zone("camino", k.lua_pos(233, 181, fc), r=900, dy=1500, text="Un camino nella roccia: si puo' arrampicare.")
    lua.zone("fine", k.lua_pos(*EXIT, h_exit), r=1600, dy=1200,
             text="Il balcone: sotto ci sono i laghetti di Marinello e la lingua di sabbia.", fn="CDV.End(4, 1)")
    ctx.notes += [
        "3. Lungo la spiaggia verso nord fino ai piedi della rupe: l'ingresso della Grotta di Donna Villa e' una buca nel terreno.",
        "4. ENIGMA E6 (il canto): al bivio tre gallerie. Quella giusta e' a NORD, dove volano le lucciole.",
        "   La galleria SUD finisce in una fossa di punte. Quella OVEST ha un masso rotolante: correre indietro,",
        "   poi tornare in fondo per il Segreto 6 (ossa di cervo).",
        "5. Sala del pozzo: lo spirito di Donna Villa insegue Lara. Si attira nell'acqua della vasca e si dissolve.",
        "   Sull'altare a nord-ovest la Conchiglia del canto: usarla davanti alla porta a est.",
        "6. Il camino: muro scalabile fino alla cengia, poi salto e aggrappo nel foro del balcone. Fine livello.",
    ]
