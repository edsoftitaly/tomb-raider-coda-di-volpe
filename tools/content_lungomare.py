"""Livello 2 - Il Lungomare (alba). v9: zona compatta disegnata a mano (livello.py).

Nord: il lungomare e i palazzi; il cancello del molo si apre solo se il "palo" fa il segnale giusto
(lampione del molo -> vaso con la palma -> panchina). Centro: lo stabilimento; il finto bagnino ha la
Chiave della terrazza, che apre il cancello del Lido Baiadera. Sud: il lido, il capo della banda, il gozzo.
"""
import kit as K
import livello as L

FRAME = L.frame(38.1300, 15.0548)


def paint(P):
    P.pool(2, 7, 2, 59, 3.0)                                     # the sea along the west side
    P.ground(13, 19, 2, 59, 2.0, "lastricato")                    # the promenade
    P.ground(20, 23, 2, 59, 2.0, "asfalto")                       # Corso Cristoforo Colombo
    P.ground(24, 25, 2, 59, 2.0, "marciapiede")
    P.rock(3, 4, 33, 34, 0.25)                                    # a rock in the sea (secret)
    # north: houses on the corso
    P.block("casa_n1", 27, 36, 48, 57, 9.5)
    P.block("casa_n2", 40, 50, 48, 57, 12.5)
    P.block("casa_n3", 54, 59, 47, 57, 6.6)
    # middle: the bathing establishment and a block of flats
    P.block("stabilimento", 27, 35, 28, 35, 4.0)
    P.block("palazzine", 40, 59, 28, 36, 9.5)
    # south: the lido's cabins and the hotel
    P.block("cabine", 27, 29, 6, 14, 2.5)
    P.block("albergo", 45, 59, 4, 14, 9.5)
    P.ground(26, 44, 2, 16, 2.0, "lastricato")


SPEC = dict(
    paint=paint, mat="marciapiede", gate1=16, gate2=17, walls="block",
    start=(17, 56), north_zone=(17, 50),
    start_text="Alba sul lungomare di Oliveri. Il palo della banda e' scappato verso il Lido Baiadera.",
    seq=[("LAMPIONE_LUNGOMARE", 14, 47, 0.0), ("VASO_BIANCO_PALMA", 22, 55, 0.0), ("PANCHINA", 14, 57, 90.0)],
    seq_hint="Il cancello del lungomare e' chiuso dall'altra parte. Sul pilastro, un biglietto della banda: "
             "\"Il palo passa dal lampione del molo, poi dalla palma, poi si siede sulla panchina. Solo allora gli apriamo.\"",
    seq_step="Il segnale... (%d di %d)",
    seq_bad="Ordine sbagliato: dall'altra parte nessuno si muove. Si ricomincia dal lampione del molo.",
    seq_done="Il segnale giusto! Dall'altra parte qualcuno apre il cancello... e non sono amici.",
    centro_enemies=[(K.BADDY1, 22, 33), (K.BADDY1, 36, 25)], centro_text="Il finto bagnino e il suo compare!",
    item=2, device="ARGANO",
    device_text="La Chiave della terrazza gira nella centralina: il cancello del Lido Baiadera si apre.",
    gate2_hint="Il cancello del Lido Baiadera e' chiuso: la centralina vuole la Chiave della terrazza. Il finto bagnino ce l'aveva in tasca.",
    south_enemies=[(K.DOBERMAN, 36, 10), (K.DOBERMAN, 38, 6)], boss=(40, 9),
    south_text="Il lido! Il capo della banda sta caricando il gozzo.",
    exit=(10, 8), end_text="Il gozzo e' mio. Verso Marinello, lungo la costa.",
    end_no="Prima devo fermare il capo della banda: e' qui nel lido.",
    pickups=[(K.SMALLMEDI, 24, 52), (K.UZI_ITEM, 25, 38), (K.UZI_AMMO, 23, 26), (K.BIGMEDI, 33, 18), (K.UZI_AMMO, 42, 4)],
    secrets={3: (3, 33, 0.25, "Sullo scoglio in mezzo al mare: una Stella dei Dioscuri!"),
             4: (58, 38, None, "Nel vicolo dietro le palazzine: una Stella dei Dioscuri!")},
    props=[("OMBRELLONE_SPIAGGIA", 10.5, 12.5, 0.0), ("OMBRELLONE_SPIAGGIA", 10.5, 18.5, 0.0), ("OMBRELLONE_SPIAGGIA", 9.5, 26.5, 0.0),
           ("GOZZO", 4.5, 8.5, 0.0), ("BARCHETTA_SPIAGGIA", 10.5, 36.5, 0.0), ("LAMPIONE_LUNGOMARE", 14.2, 24.5, 0.0),
           ("LAMPIONE_LUNGOMARE", 14.2, 34.5, 0.0), ("LAMPIONE_LUNGOMARE", 14.2, 14.5, 0.0), ("AUTO_UTILITARIA_ROSSA", 21.5, 50.5, 0.0),
           ("SCOOTER_ROSSO", 25.0, 45.0, 0.0), ("DEHORS_OMBRELLONE", 38.5, 20.0, 0.0), ("DEHORS_TAVOLO", 37.5, 18.5, 0.0)],
    notes=["", "LIVELLO 2 - IL LUNGOMARE",
           "1. Il cancello del lungomare si apre col segnale del palo: lampione del molo, vaso con la palma, panchina (in quest'ordine).",
           "2. Allo stabilimento il finto bagnino lascia la Chiave della terrazza: si usa sulla centralina accanto al cancello del lido.",
           "3. Nel lido due cani e il capo della banda. Morto il capo, il livello finisce al gozzo sulla spiaggia.",
           "   Segreto 4: lo scoglio in mezzo al mare (a nuoto). Segreto 5: il vicolo in fondo dietro le palazzine."],
)


def extra(ctx):
    ctx.lua.drop("chiave_terrazza", "centro0", "ID.PUZZLE_ITEM2", "Il finto bagnino aveva la Chiave della terrazza.")


SPEC["extra"] = extra


def prepare(world):
    L.paint_base(world, SPEC)


def build(ctx):
    L.build(ctx, SPEC, 3)
