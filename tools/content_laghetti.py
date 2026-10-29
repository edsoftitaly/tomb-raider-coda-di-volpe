"""Livello 4 - I Laghetti di Marinello.

Arrivo dal balcone sulla riva sud -> la Mappa delle maree letta dalla riserva (E4) indica il Mergolo della
Tonnara -> tuffo: sul fondo un pozzo porta alla tonnara sommersa -> le reti si aprono solo nell'ordine del
tonno: levante, tramontana, ponente (E5) -> camera della morte: Sigillo della tonnara e sacca d'aria ->
tornati su, la lingua di sabbia e la banda della Volpe -> piedi della rupe, Sentiero Coda di Volpe -> fine.
"""
import kit as K
from kit import CLICK

START = (275, 15)
HOLE = (215, 55)
SHORE = (252, 30)      # south-east shore of the Mergolo: where the tide map is read
WEST = (180, 52)       # west shore, under the cliff: the gang waits here
END = (170, 44)        # foot of the cliff: the Sentiero Coda di Volpe
FL = -6144          # tonnara floor
HT = 2048           # chamber height


def prepare(world):
    pass


DECOR = dict(boats=15)


def build(ctx):
    """Compact route (about 250 m instead of 1.3 km): shore -> Turi's boat over the deep spot -> tonnara
    -> west shore ambush -> cliff path. The rest of the lagoons stays open for the secrets."""
    ctx.decor_block = [(200, 40, 230, 70), (160, 35, 190, 65)]
    k, lua = ctx.kit, ctx.lua
    sx, sz = k.spot(*START)
    k.place(K.LARA, sx, sz, rot=270.0, name="lara_start")
    k.place(K.LARA_START_POS, sx, sz, ocb=1)
    lua.start('''if not CDV.Has(ID.PUZZLE_ITEM3) then CDV.Give(ID.PUZZLE_ITEM3, 1) end
CDV.Say("I laghetti di Marinello all'alba. Turi cercava qualcosa sott'acqua.", 6)''')

    # E4: the tide map says "where the Mergolo is deepest"; Turi's boat is anchored right there.
    k.prop("GOZZO", HOLE[0] + 0.3, HOLE[1] + 0.6, rot=35.0, h=0)
    vx, vz = k.spot(*SHORE)
    lua.use("mappa", "ID.PUZZLE_ITEM3", k.lua_pos(vx, vz, ctx.ground(vx, vz)), r=4000, dy=3000, consume=False,
            text="\"Il tonno entra dove il Mergolo e' piu' profondo.\" E in mezzo al Mergolo c'e' una barca all'ancora, senza nessuno a bordo...",
            fn='CDV.Flag("mappa_letta", true)')
    lua.zone("riva", k.lua_pos(vx, vz, ctx.ground(vx, vz)), r=5000, dy=3000,
             text="Il Mergolo della Tonnara. Forse la Mappa delle maree dice qualcosa di questo posto.")
    tonnara(ctx)

    # The gang waits on the west shore for whoever comes up with the seal: two from the cliff path,
    # one along the shore, two dogs. They come from three sides.
    gang = [(K.BADDY1, (WEST[0] - 6, WEST[1] - 8)), (K.BADDY2, (WEST[0] - 4, WEST[1] + 10)),
            (K.BADDY1, (WEST[0] + 4, WEST[1] + 16)), (K.DOBERMAN, (WEST[0] - 8, WEST[1] + 2)),
            (K.DOBERMAN, (WEST[0] - 8, WEST[1] - 2))]
    names = []
    for i, (t, (x, z)) in enumerate(gang):
        n = "banda%d" % i
        k.place(t, *k.spot(x, z), rot=90.0, name=n)
        names.append(n)
    wx, wz = k.spot(*WEST)
    lua.zone("agguato", k.lua_pos(wx, wz, ctx.ground(wx, wz)), r=16000, dy=8000,
             fn="\n".join('CDV.Enable("%s")' % n for n in names),
             need="CDV.Has(ID.PUZZLE_ITEM6)", text="Gli uomini della Volpe aspettavano il sigillo sulla riva!")
    k.place(K.SHOTGUN_AMMO1, *k.spot(WEST[0] + 2, WEST[1] - 4))
    # Optional exploration: the rest of the lagoons.
    s = k.spot(30, 330)
    k.place(K.FLARE_ITEM, *s)
    k.place(K.UZI_AMMO, *k.spot(32, 328))
    lua.secret(7, k.lua_pos(*s, ctx.ground(*s)), r=900, text="Sulla riva del Lago Verde: una Stella dei Dioscuri!")

    ex, ez = k.spot(*END)
    lua.zone("fine", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2500, dy=4000, need="CDV.Has(ID.PUZZLE_ITEM6)",
             text="Il Sentiero Coda di Volpe sale la rupe fino al santuario di Tindari.", fn="CDV.End(5, 1)")
    lua.zone("fine_no", k.lua_pos(ex, ez, ctx.ground(ex, ez)), r=2500, dy=4000, once=False, secs=4,
             need="not CDV.Has(ID.PUZZLE_ITEM6)", text="Non posso salire senza aver trovato cosa cercava Turi nel Mergolo.")
    ctx.notes += [
        "",
        "LIVELLO 4 - I LAGHETTI",
        "1. Si parte sulla riva sud-est del Mergolo della Tonnara (il lago a ovest).",
        "2. ENIGMA E4: sulla riva usare la Mappa delle maree: \"il tonno entra dove il Mergolo e' piu' profondo\".",
        "   In mezzo al lago c'e' la barca di Turi all'ancora: sotto la barca, sul fondo, si apre un pozzo.",
        "3. ENIGMA E5 (la tonnara): dalla camera centrale si entra nelle camere nell'ordine del tonno:",
        "   LEVANTE (est), TRAMONTANA (nord), PONENTE (ovest). Ordine sbagliato: le reti si stringono e l'aria cala.",
        "   Con l'ordine giusto si apre la rete a sud: camera della morte, sacca d'aria, Sigillo della tonnara.",
        "   Segreto 7: angolo sud-ovest della camera di ponente.",
        "4. Si risale e si nuota alla riva ovest, sotto la rupe: imboscata (tre uomini e due cani).",
        "5. Ai piedi della rupe inizia il Sentiero Coda di Volpe: fine livello.",
        "   Segreto 8 (facoltativo, lontano): riva del Lago Verde, a nord-ovest.",
    ]


def tonnara(ctx):
    k, lua = ctx.kit, ctx.lua
    tex = ("sabbia_fondo", "pietra_bagnata", "pietra_viva")

    def chamber(name, plan, x0, z0):
        return k.interior(name, plan, x0, z0, FL, HT, *tex, water=True, ambient=(0.25, 0.35, 0.42), tags=("tonnara",))

    hub = chamber("TONNARA_CENTRO", ["......."] * 7, 212, 52)
    east = chamber("TONNARA_LEVANTE", [".....", ".....", "..E..", ".....", "....."], 219, 53)
    east.room.nx  # noqa
    north = chamber("TONNARA_TRAMONTANA", ["....."] * 3 + ["..N.."] + ["....."] * 3, 213, 59)
    west = chamber("TONNARA_PONENTE", [".....", ".....", "..W..", ".....", "....."], 207, 53)
    # The west chamber is 5 wide: x 207..211 so that its east border meets the hub at x = 211.
    death = chamber("TONNARA_MORTE", ["##D##", ".....", ".....", ".....", ".S...", "....."], 213, 46)
    k.link_wall(hub, east)
    k.link_wall(hub, north)
    k.link_wall(west, hub)
    k.link_wall(death, hub)
    lake = ctx.water_room_at(*HOLE)
    k.link_vertical(hub, lake, [HOLE])
    # Air pocket over part of the death chamber.
    air = k.interior("TONNARA_ARIA", ["...", "...", "..."], 214, 47, FL + HT, 4 * CLICK, "pietra_bagnata",
                     "soffitto_roccia", "pietra_viva", tags=("tonnara",))
    k.water_surface(air, death, K.rect(214, 47, 216, 49))
    k.place(K.DOOR_TYPE3, *death.anchors["D"], room=death.room, rot=0.0, name="rete_morte")
    k.place(K.PUZZLE_ITEM[6], *death.anchors["S"], room=death.room, name="sigillo")
    k.place(K.BIGMEDI, 215, 48, room=air.room)
    k.place(K.SHOTGUN_AMMO1, 216, 49, room=air.room)
    for i, (x, z) in enumerate(((214, 57), (217, 53))):
        k.place(K.BIG_RAT, x, z, room=hub.room, h=FL + CLICK, name="ratto_tonnara%d" % i)
    lua.zone("tonnara", k.lua_pos(*HOLE, FL + HT), r=1800, dy=2500,
             fn='CDV.Enable("ratto_tonnara0")\nCDV.Enable("ratto_tonnara1")',
             text="La tonnara sommersa! Inciso sulle reti: \"Il tonno entra da levante, gira a tramontana, muore a ponente.\"")
    e, n, w = east.anchors["E"], north.anchors["N"], west.anchors["W"]
    for key, cell in (("levante", e), ("tramontana", n), ("ponente", w)):
        lua.zone("camera_" + key, k.lua_pos(cell[0], cell[1], FL + CLICK), r=1400, dy=2200, once=False, secs=2,
                 fn='CDV.Tonnara("%s")' % key)
    lua.add('''
local SEQ = { "levante", "tramontana", "ponente" }
function CDV.Tonnara(name)
    if CDV.Flag("tonnara_ok") then return end
    local step = CDV.Flag("tonnara_step") or 0
    if CDV.Flag("tonnara_last") == name then return end
    CDV.Flag("tonnara_last", name)
    if SEQ[step + 1] == name then
        step = step + 1
        CDV.Flag("tonnara_step", step)
        if step == 3 then
            CDV.Flag("tonnara_ok", true)
            CDV.Enable("rete_morte")
            CDV.Say("Le reti si aprono: la camera della morte!", 6)
        else
            CDV.Say("La rete dietro di me si allenta...", 3)
        end
    else
        CDV.Flag("tonnara_step", 0)
        Lara:SetAir(300)
        CDV.Say("Le reti si stringono! Ordine sbagliato, devo uscire e ricominciare.", 5)
    end
end''')
    lua.secret(6, k.lua_pos(208, 54, FL + CLICK), r=900, text="Nell'angolo della camera di ponente: una Stella dei Dioscuri!")
