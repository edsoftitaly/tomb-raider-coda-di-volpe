"""Livello 6 - La Citta' Sommersa (finale, notte). v9: zona compatta disegnata a mano (livello.py).

Nord: la spiaggia sotto Capo Tindari; il cancello della grotta si apre seguendo la rotta dei Dioscuri
(colonna, barca a vela, gozzo). Centro: la meta' di Tyndaris franata in mare, a nuoto tra le rovine; il
Sigillo della tonnara e' sul fondo. Sud: il tempio, Turi 'a Vulpi, il finale.
"""
import kit as K
import livello as L

FRAME = L.frame(38.1430, 15.0440)


def paint(P):
    P.ground(2, 59, 43, 59, 2.0, "sabbia")
    P.rock(2, 10, 52, 59, 6.0)                                     # Capo Tindari's foot (scenery)
    P.pool(6, 54, 27, 34, 4.0)                                     # the drowned city
    for x0, z0 in ((14, 29), (26, 32), (42, 28)):
        P.rock(x0, x0 + 1, z0, z0 + 1, 0.25)                       # ruins breaking the surface
    P.ground(2, 59, 2, 20, 2.0, "castello_pav")
    P.block("tempio", 22, 38, 6, 12, 7.0)


SPEC = dict(
    paint=paint, mat="sabbia", gate1=28, gate2=44,
    start=(20, 56), north_zone=(28, 50),
    start_text="Notte, sotto Capo Tindari. Turi 'a Vulpi e' sceso fin qui: la grotta della citta' sommersa e' chiusa da una grata.",
    seq=[("INTERNO_COLONNA", 14, 46, 0.0), ("BARCA_VELA", 40, 55, 0.0), ("GOZZO", 50, 46, 0.0)],
    seq_hint="La grata della grotta e' chiusa. Nel diario bizantino: \"La rotta dei Dioscuri: dalla colonna "
             "alla nave con la vela, poi alla barca dei pescatori. Cosi' il mare si apre.\"",
    seq_step="La rotta dei Dioscuri... (%d di %d)",
    seq_bad="Non e' la rotta del diario. Si ricomincia dalla colonna.",
    seq_done="La rotta e' giusta: la grata della grotta si alza, e l'acqua entra a scrosci.",
    north_enemies=[(K.BADDY1, 36, 47)], north_text="La sentinella di Turi!",
    centro_enemies=[(K.BADDY2, 52, 24), (K.BADDY1, 8, 38)], centro_text="Gli ultimi uomini di Turi, sulle rovine.",
    item=6, item_cells=[(46, 31)], device="INTERNO_ALTARE", device_at=(38.5, 25.5), device_r=1700,
    device_text="Il Sigillo della tonnara nell'altare: la porta del tempio si apre.",
    gate2_hint="La porta del tempio e' chiusa. L'altare accanto ha un'impronta tonda, come un sigillo. "
               "Laggiu', tra le rovine sommerse, qualcosa brilla sul fondo.",
    gate2_have="Il sigillo va nell'altare qui accanto: Azione davanti all'altare.",
    south_enemies=[(K.BADDY1, 14, 16), (K.BADDY1, 50, 16)], boss=(30, 15),
    south_text="Turi 'a Vulpi! Davanti al tempio dei Dioscuri.",
    exit=(30, 4), end_text="Il diario bizantino torna dove deve stare. Il mare, piano, si ritira.",
    end_no="Turi 'a Vulpi e' ancora vivo.",
    end_fn='CDV.Flag("finale", 0)',
    pickups=[(K.SMALLMEDI, 12, 44), (K.BIGMEDI, 56, 38), (K.UZI_AMMO, 4, 24), (K.SHOTGUN_AMMO1, 54, 6), (K.BIGMEDI, 8, 10)],
    secrets={11: (26, 32, 0.25, "Sulla rovina in mezzo al mare: l'ultima Stella dei Dioscuri!")},
    props=[("INTERNO_COLONNA", 24.5, 14.5, 0.0), ("INTERNO_COLONNA", 36.5, 14.5, 0.0), ("INTERNO_COLONNA", 14.5, 30.5, 0.0),
           ("BARCHETTA_SPIAGGIA", 24.5, 46.5, 0.0), ("PINO_ALEPPO_GIOVANE", 54.5, 56.5, 0.0)],
    lights=[(28.5, 44.5, 6.0), (44.5, 24.5, 6.0), (30.5, 6.0, 8.0)],
    notes=["", "LIVELLO 6 - LA CITTA' SOMMERSA",
           "1. La grata della grotta: la rotta dei Dioscuri (colonna, barca a vela, gozzo).",
           "2. Il Sigillo della tonnara e' sul fondo, tra le rovine a est: si usa sull'altare accanto alla porta del tempio.",
           "3. Davanti al tempio Turi 'a Vulpi; morto lui, il finale e' davanti al tempio.",
           "   Segreto 12: la rovina in mezzo al mare."],
)


def extra(ctx):
    k = ctx.kit
    x, z = 46, 31
    room = ctx.water_room_at(x, z)
    h = int(ctx.world.depth[x, z] * -512) + 64
    k.place(K.PUZZLE_ITEM[6], x, z, room=room, h=h, name="sigillo")
    ctx.lua.loop('''
local t = CDV.Flag("finale")
if t ~= nil then
    t = t + 1
    CDV.Flag("finale", t)
    if t == 200 then CDV.Say("All'alba, la lingua di sabbia di Marinello e' di nuovo li'. Come quando salvo' la bambina caduta dalla rupe.", 8) end
    if t == 470 then CDV.Say("Gli Astri dei Dioscuri restano a Tindari. Donna Villa tace. FINE - Coda di Volpe.", 8) end
    if t == 740 then CDV.Video("cdv_finale") end
    if t == 750 then TEN.Flow.EndLevel() end
end''')


SPEC["extra"] = extra


def prepare(world):
    L.paint_base(world, SPEC)


def build(ctx):
    L.build(ctx, SPEC, None)
