"""Livello 2 - Il Lungomare (alba).

Stazione Oliveri-Tindari -> la moto della banda -> Via Stazione -> lungomare (Corso Cristoforo Colombo)
-> posto di blocco al Lido Baiadera -> cani alla Ruota -> Marinello (Piro Piro Bar) -> fine.
"""
import kit as K

START = (240, 86)
BIKE = (242, 90)


def build(ctx):
    k, lua = ctx.kit, ctx.lua
    sx, sz = k.spot(*START)
    k.place(K.LARA, sx, sz, rot=0.0, name="lara_start")
    k.place(K.LARA_START_POS, sx, sz, ocb=1)
    bx, bz = k.spot(*BIKE)
    k.place(K.MOTORBIKE, bx, bz, rot=315.0, name="moto")
    k.place(K.SMALLMEDI, *k.spot(246, 84))
    lua.start('''CDV.Say("Alba alla stazione di Oliveri-Tindari. La moto della banda e' ancora qui: verso Marinello!", 7)''')

    # Uzi and ammo at the Lido Baiadera, guarded by two gunmen.
    lido = (264, 187)
    for i, (dx, dz) in enumerate(((-4, -3), (3, 4))):
        k.place(K.BADDY1, *k.spot(lido[0] + dx, lido[1] + dz), name="blocco%d" % i)
    k.place(K.UZI_ITEM, *k.spot(lido[0] + 6, lido[1] - 2))
    k.place(K.UZI_AMMO, *k.spot(lido[0] + 7, lido[1]))
    k.place(K.BIGMEDI, *k.spot(lido[0] - 6, lido[1] + 6))
    lua.zone("blocco", k.lua_pos(lido[0], lido[1], ctx.ground(*k.spot(lido[0], lido[1] - 15))), r=26000, dy=8000,
             fn='CDV.Enable("blocco0")\nCDV.Enable("blocco1")', text="Posto di blocco al Lido Baiadera!")

    # Dogs at La Ruota.
    ruota = (213, 220)
    for i, (dx, dz) in enumerate(((2, -3), (-3, 2))):
        k.place(K.DOBERMAN, *k.spot(ruota[0] + dx, ruota[1] + dz), name="cane_ruota%d" % i)
    lua.zone("ruota", k.lua_pos(ruota[0], ruota[1], ctx.ground(*k.spot(*ruota))), r=18000, dy=8000,
             fn='CDV.Enable("cane_ruota0")\nCDV.Enable("cane_ruota1")')
    k.place(K.SHOTGUN_AMMO1, *k.spot(ruota[0] + 5, ruota[1] + 5))

    # Last guard before Marinello.
    k.place(K.BADDY2, *k.spot(185, 345), name="guardia_marinello")
    lua.zone("marinello_guardia", k.lua_pos(185, 345, ctx.ground(*k.spot(185, 345))), r=16000, dy=8000,
             fn='CDV.Enable("guardia_marinello")')

    # Secrets: on the beach rocks and behind the camp site.
    s1 = k.spot(300, 140)
    lua.secret(3, k.lua_pos(*s1, ctx.ground(*s1)), r=900)
    k.place(K.FLARE_ITEM, *s1)
    s2 = k.spot(130, 330)
    lua.secret(4, k.lua_pos(*s2, ctx.ground(*s2)), r=900)
    k.place(K.SMALLMEDI, *s2)

    end = k.spot(174, 372)
    lua.zone("fine", k.lua_pos(*end, ctx.ground(*end)), r=3000, dy=4000,
             text="Marinello. Il Casello FS e' poco piu' avanti, ai piedi della rupe.", fn="CDV.End(3, 1)")
    ctx.notes += [
        "",
        "LIVELLO 2 - IL LUNGOMARE",
        "1. Davanti alla stazione c'e' la moto: si sale e si prende Via Stazione verso il mare, poi il lungomare a nord.",
        "2. Posto di blocco al Lido Baiadera: due uomini con le Uzi; Uzi, munizioni e medikit grande vicino al lido.",
        "3. Alla Ruota due dobermann. Prima di Marinello un'ultima guardia.",
        "   Segreto 4: sugli scogli della spiaggia, a sud del lido. Segreto 5: dietro il campeggio Villaggio Marinello, verso la collina.",
        "4. Il livello finisce davanti al Piro Piro Bar.",
    ]
