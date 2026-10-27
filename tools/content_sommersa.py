"""Livello 6 - La Citta' Sommersa (finale).

Grotta marina sotto Capo Tindari -> la meta' di Tyndaris franata in mare (Plinio) -> squali e Donna Villa
(strega della laguna) -> la sua morte apre il tempio -> sala d'aria: Turi 'a Vulpi e i guardiani di
ossa -> Astro di Polluce -> i due Astri sull'altare dei Dioscuri -> finale.
"""
import random

import kit as K
from kit import CLICK

X0, Z0, N = 10, 10, 32
SEA_FLOOR = -8192


def sea_plan():
    rnd = random.Random(7)
    g = [["." for _ in range(N)] for _ in range(N)]   # g[z][x], z = 0 south
    # Avenue of columns north-south (x 13..18 local) towards the temple.
    for z in range(4, 30, 3):
        g[z][12] = "#"
        g[z][19] = "#"
    # Ruined houses: raised foundations with broken walls.
    for (x0, z0, w, h) in ((3, 4, 6, 5), (22, 5, 6, 6), (3, 15, 5, 7), (23, 16, 6, 5), (5, 25, 5, 4), (24, 25, 5, 4)):
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + h):
                edge = x in (x0, x0 + w - 1) or z in (z0, z0 + h - 1)
                g[z][x] = "#" if edge and rnd.random() < 0.55 else "2"
    # Fallen blocks.
    for _ in range(25):
        x, z = rnd.randrange(1, N - 1), rnd.randrange(1, N - 1)
        if g[z][x] == "." and not (13 <= x <= 18):
            g[z][x] = rnd.choice("1234")
    g[2][15] = "S"      # sharks
    g[26][16] = "W"     # Donna Villa
    g[8][4] = "U"
    g[17][27] = "Y"     # secret
    g[10][25] = "M"
    return ["".join(g[z]) for z in range(N - 1, -1, -1)]


def build_standalone(ctx):
    k, lua = ctx.kit, ctx.lua
    sea = k.interior("MARE_ANTICO", sea_plan(), X0, Z0, SEA_FLOOR, -SEA_FLOOR, "sabbia_fondo", "soffitto_roccia",
                     "opera_greca", water=True, ambient=(0.22, 0.34, 0.42), tags=("sommersa",))
    # Sea cave above: a rock ledge all around, open water in the middle.
    cave = []
    for z in range(N - 1, -1, -1):
        r = ""
        for x in range(N):
            r += "2" if (x < 3 or z < 3 or x >= N - 3 or z >= N - 3) else "."
        cave.append(r)
    cave_rows = [list(r) for r in cave]
    cave_rows[N - 1 - 1][15] = "L"     # Lara on the south ledge
    cave_rows[N - 1 - 1][15] = "2"
    cave = ["".join(r) for r in cave_rows]
    grotta = k.interior("GROTTA_MARINA", cave, X0, Z0, 0, 24 * CLICK, "roccia", "soffitto_roccia", "roccia_mare",
                        ambient=(0.3, 0.38, 0.45), tags=("sommersa",))
    k.water_surface(grotta, sea, K.rect(X0 + 3, Z0 + 3, X0 + N - 4, Z0 + N - 4), tex="acqua_mare")
    k.place(K.LARA, X0 + 15, Z0 + 1, room=grotta.room, rot=0.0, name="lara_start")
    k.place(K.LARA_START_POS, X0 + 15, Z0 + 1, room=grotta.room, ocb=1)
    k.place(K.SMALLMEDI, X0 + 17, Z0 + 1, room=grotta.room)

    # Temple north of the sea: flooded hall with an air chamber above its northern half.
    tx0, tz0 = X0 + 10, Z0 + N        # x 20..31, z 42..53
    tplan = []
    for z in range(tz0 + 11, tz0 - 1, -1):
        r = ""
        for x in range(tx0, tx0 + 12):
            if z == tz0 and x != X0 + 15:
                r += "#"
            elif x in (tx0, tx0 + 11) and z < tz0 + 5:
                r += "#"
            else:
                r += "."
        tplan.append(r)
    temple = k.interior("TEMPIO", tplan, tx0, tz0, SEA_FLOOR, 4096 + 4096, "lastre_greche", "soffitto", "opera_greca",
                        water=True, ambient=(0.25, 0.35, 0.42), tags=("sommersa",))
    for x in range(tx0, tx0 + 12):
        for z in range(tz0, tz0 + 12):
            s = temple.sector(x, z)
            if not s.wall:
                s.ceil = [4096 + (4096 if z >= tz0 + 5 else 0)] * 4
    k.link_wall(sea, temple, span=(X0 + 15, X0 + 15))
    k.place(K.DOOR_TYPE3, X0 + 15, tz0, room=temple.room, rot=0.0, name="porta_tempio")
    aplan = []
    for z in range(tz0 + 11, tz0 + 4, -1):
        r = ""
        for x in range(tx0, tx0 + 12):
            r += "." if z <= tz0 + 7 and tx0 + 1 <= x <= tx0 + 10 else "1"
        aplan.append(r)
    aplan = [list(r) for r in aplan]
    aplan[0][5] = "A"          # altar (z = tz0 + 11, x = tx0 + 5)
    air = k.interior("TEMPIO_ARIA", ["".join(r) for r in aplan], tx0, tz0 + 5, -4096 + 4096 - 4096 + 0 if False else 0, 7 * CLICK,
                     "mosaico", "soffitto", "opera_greca", ambient=(0.4, 0.37, 0.33), tags=("sommersa",))
    # The air chamber floor sits on the flooded hall's ceiling (0 = sea level of the cave).
    k.water_surface(air, temple, K.rect(tx0 + 1, tz0 + 5, tx0 + 10, tz0 + 7), tex="acqua_scura")
    ax, az = air.anchors["A"]
    k.place(K.BADDY1, tx0 + 3, tz0 + 10, room=air.room, name="turi")
    k.place(K.SKELETON, tx0 + 8, tz0 + 9, room=air.room, name="guardiano1")
    k.place(K.SKELETON, tx0 + 2, tz0 + 9, room=air.room, name="guardiano2")
    k.place(K.SHOTGUN_AMMO1, tx0 + 10, tz0 + 10, room=air.room)
    k.place(K.BIGMEDI, tx0 + 1, tz0 + 11, room=air.room)

    # Sea creatures.
    sx, sz = sea.anchors["S"]
    k.place(K.SHARK, sx, sz, room=sea.room, h=SEA_FLOOR + 8 * CLICK, name="squalo1")
    k.place(K.SHARK, sx + 8, sz + 6, room=sea.room, h=SEA_FLOOR + 10 * CLICK, name="squalo2")
    wx, wz = sea.anchors["W"]
    k.place(K.LAGOON_WITCH, wx, wz, room=sea.room, h=SEA_FLOOR + 4 * CLICK, name="donna_villa")
    k.place(K.UZI_AMMO, *sea.anchors["U"], room=sea.room)
    k.place(K.SMALLMEDI, *sea.anchors["M"], room=sea.room)

    lua.start('''if not CDV.Has(ID.PUZZLE_ITEM7) then CDV.Give(ID.PUZZLE_ITEM7, 1) end
CDV.Say("Una grotta marina sotto Capo Tindari. Sotto di me, nell'acqua, la meta' perduta di Tyndaris.", 8)''')
    lua.zone("tuffo", k.lua_pos(X0 + 15, Z0 + 10, SEA_FLOOR + 8 * CLICK), r=12000, dy=6000,
             fn='CDV.Enable("squalo1")\nCDV.Enable("squalo2")', text="Tyndaris sommersa: la via delle colonne porta al tempio.")
    lua.zone("strega", k.lua_pos(wx, wz, SEA_FLOOR + 4 * CLICK), r=9000, dy=6000, fn='CDV.Enable("donna_villa")',
             text="Donna Villa, nella sua vera forma! Finche' vive, il tempio resta chiuso.")
    lua.loop('''
if not CDV.Flag("tempio") and CDV.Flag("strega_vista") and CDV.Dead("donna_villa") then
    CDV.Flag("tempio", true)
    CDV.Enable("porta_tempio")
    CDV.Say("Il canto si spegne. La porta del tempio si apre.", 6)
end
if CDV.Active("donna_villa") then CDV.Flag("strega_vista", true) end''')
    lua.zone("sala_aria", k.lua_pos(tx0 + 5, tz0 + 7, 0), r=3000, dy=2000,
             fn='CDV.Enable("turi")\nCDV.Enable("guardiano1")\nCDV.Enable("guardiano2")',
             text="Turi 'a Vulpi! \"L'Astro di Polluce e' mio, signorina.\" I guardiani di ossa si risvegliano.")
    lua.drop("polluce", "turi", "ID.PUZZLE_ITEM8", "Turi cade. Aveva con se' l'Astro di Polluce.")
    lua.use("altare", "ID.PUZZLE_ITEM8", k.lua_pos(ax, az, CLICK), r=1800, dy=1500, consume=True,
            need="CDV.Has(ID.PUZZLE_ITEM7)", fail="Serve anche l'Astro di Castore.",
            text="Castore e Polluce di nuovo insieme. Il mare si ritira...", fn='CDV.Take(ID.PUZZLE_ITEM7)\nCDV.Flag("finale", 0)')
    lua.use("altare2", "ID.PUZZLE_ITEM7", k.lua_pos(ax, az, CLICK), r=1800, dy=1500, consume=False,
            need="CDV.Has(ID.PUZZLE_ITEM8)", fail="Sull'altare ci sono due impronte: manca l'Astro di Polluce.",
            text="Castore e Polluce di nuovo insieme. Il mare si ritira...", fn='CDV.Take(ID.PUZZLE_ITEM7)\nCDV.Take(ID.PUZZLE_ITEM8)\nCDV.Flag("finale", 0)')
    lua.loop('''
local t = CDV.Flag("finale")
if t ~= nil then
    t = t + 1
    CDV.Flag("finale", t)
    if t == 200 then CDV.Say("All'alba, la lingua di sabbia di Marinello e' di nuovo li'. Come quando salvo' la bambina caduta dalla rupe.", 8) end
    if t == 470 then CDV.Say("Gli Astri dei Dioscuri restano a Tindari. Donna Villa tace. FINE - Coda di Volpe.", 8) end
    if t == 740 then TEN.Flow.EndLevel() end
end''')
    lua.secret(10, k.lua_pos(*sea.anchors["Y"], SEA_FLOOR + 2 * CLICK), r=1000, text="Tra le rovine sommerse: una Stella dei Dioscuri!")
    lua.secret(11, k.lua_pos(tx0 + 10, tz0 + 11, CLICK), r=900, text="Dietro l'altare: l'ultima Stella dei Dioscuri!")
    ctx.notes += [
        "",
        "LIVELLO 6 - LA CITTA' SOMMERSA",
        "1. Si parte su una cengia di una grotta marina. Ci si tuffa: sul fondo le rovine di Tyndaris, due squali.",
        "2. Si segue il viale delle colonne verso nord: Donna Villa (strega della laguna). Ucciderla apre la porta del tempio.",
        "   Segreto 11: tra le rovine a est. ",
        "3. Nel tempio si risale nella sala d'aria: Turi 'a Vulpi e due guardiani di ossa (meglio il fucile).",
        "   Turi lascia l'Astro di Polluce. Segreto 12: dietro l'altare.",
        "4. Usare l'Astro di Polluce (o di Castore) sull'altare: finale.",
    ]
