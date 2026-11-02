"""Livello 3 - Marinello (mattina). v9: zona compatta disegnata a mano (livello.py).

Nord: la spiaggia dei pescatori; il cancello della pineta si apre con l'ordine d'uscita delle barche
scritto sulla tabella del capanno (gommone, barchetta, gozzo). Centro: il laghetto di Marinello; la
Chiave del Casello e' sul fondo. Sud: il Casello FS, il capo e la via verso la rupe.
"""
import kit as K
import livello as L

FRAME = L.frame(38.1370, 15.0520)


def paint(P):
    P.pool(38, 48, 49, 54, 1.5, lagoon=True)                     # a small pond by the huts
    P.block("capanno", 54, 59, 49, 56, 3.0)
    P.pool(8, 48, 28, 34, 3.0, lagoon=True)                      # Laghetto di Marinello
    P.rock(34, 35, 30, 31, 0.25)                                 # islet (secret)
    P.block("casello", 42, 50, 6, 13, 6.0)
    P.ground(2, 59, 2, 4, 2.0, "lastricato")                     # the old railway track bed


SPEC = dict(
    paint=paint, mat="sabbia", gate1=26, gate2=40,
    start=(12, 57), north_zone=(20, 50),
    start_text="Marinello. La banda ha portato qualcosa al Casello FS, oltre il laghetto.",
    seq=[("GOMMONE", 12, 48, 0.0), ("BARCHETTA_SPIAGGIA", 22, 55, 0.0), ("GOZZO", 6, 53, 0.0)],
    seq_hint="Il cancello della pineta e' chiuso: la catena passa nel capanno di un pescatore, e il pescatore apre solo "
             "a chi esce in mare nell'ordine giusto. Sulla tabella: \"Prima il gommone, poi la barchetta, ultimo il gozzo.\"",
    seq_step="La barca giusta... (%d di %d)",
    seq_bad="Non e' l'ordine della tabella: il pescatore scuote la testa. Si ricomincia dal gommone.",
    seq_done="Il pescatore fa un cenno e toglie la catena: il cancello della pineta si apre.",
    north_enemies=[(K.DOBERMAN, 34, 46)], north_text="Un cane della banda!",
    centro_enemies=[(K.BADDY1, 52, 36), (K.DOBERMAN, 54, 30)], centro_text="Altri due della banda, al laghetto.",
    item=4, item_cells=[(20, 31)], device="ARGANO",
    device_text="La Chiave del Casello apre il quadro del passaggio a livello: la sbarra si alza.",
    gate2_hint="Il passaggio a livello e' chiuso col lucchetto del Casello. Ho visto qualcosa luccicare sul fondo del laghetto.",
    south_enemies=[(K.BADDY1, 26, 8), (K.BADDY1, 34, 14)], boss=(36, 9),
    south_text="Il Casello FS! Il capo della banda e i suoi uomini.",
    exit=(56, 3), end_text="La vecchia ferrovia porta ai laghetti di Tindari, sotto la rupe.",
    end_no="Il capo della banda e' ancora qui al Casello.",
    pickups=[(K.SMALLMEDI, 16, 44), (K.SHOTGUN_AMMO1, 56, 26), (K.BIGMEDI, 20, 16), (K.UZI_AMMO, 36, 5)],
    secrets={5: (34, 30, 0.25, "Sull'isolotto in mezzo al laghetto: una Stella dei Dioscuri!"),
             6: (57, 58, None, "Dietro il capanno del pescatore: una Stella dei Dioscuri!")},
    props=[("OMBRELLONE_SPIAGGIA", 30.5, 52.5, 0.0), ("PINO_ALEPPO_GIOVANE", 8.5, 38.5, 0.0), ("PINO_ALEPPO_GIOVANE", 52.5, 40.5, 0.0),
           ("PINO_ALEPPO_GIOVANE", 14.5, 24.5, 0.0), ("BICICLETTA", 51.5, 14.5, 0.0), ("APE_PIAGGIO", 38.5, 16.5, 0.0)],
    notes=["", "LIVELLO 3 - MARINELLO",
           "1. Il cancello della pineta: si passa accanto alle barche nell'ordine della tabella (gommone, barchetta, gozzo).",
           "2. La Chiave del Casello e' sul fondo del laghetto, a ovest dell'isolotto: si usa sul quadro accanto al passaggio a livello.",
           "3. Al Casello il capo della banda; morto lui, si esce a est lungo la ferrovia.",
           "   Segreto 6: l'isolotto nel laghetto. Segreto 7: dietro il capanno del pescatore."],
)


def extra(ctx):
    k = ctx.kit
    x, z = 20, 31
    room = ctx.water_room_at(x, z)
    h = int(ctx.world.depth[x, z] * -512) + 64
    k.place(K.PUZZLE_ITEM[4], x, z, room=room, h=h, name="chiave_casello")
    ctx.lua.zone("luccica", k.lua_pos(20, 36, ctx.ground(20, 36)), r=2500, dy=2000,
                 text="Qualcosa luccica sul fondo del laghetto, a ovest dell'isolotto.")


SPEC["extra"] = extra


def prepare(world):
    L.paint_base(world, SPEC)


def build(ctx):
    L.build(ctx, SPEC, 4)
