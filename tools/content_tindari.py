"""Livello 5 - Tindari (tramonto). v9: zona compatta disegnata a mano (livello.py).

Nord: il piazzale del santuario; il cancello degli scavi si apre al rito del pellegrino (ulivo nel vaso,
lampione, panchina). Centro: la citta' greca; l'Astro di Castore e' in cima al basamento di un tempio
(si scala), l'Astro di Polluce ce l'ha il custode della banda. Tutti e due sull'altare aprono il teatro.
Sud: il Teatro Greco, il capo, la discesa verso il mare.
"""
import kit as K
import livello as L

FRAME = L.frame(38.1412, 15.0454)


def paint(P):
    P.ground(2, 59, 43, 59, 2.0, "lastricato")
    P.block("santuario", 44, 59, 48, 57, 12.0)
    P.block("convento", 2, 8, 50, 57, 9.0)
    P.ground(2, 59, 23, 40, 2.0, "castello_pav")
    P.rock(12, 14, 30, 32, 6.0)                                    # temple podium, 4 m
    P.rock(40, 46, 33, 36, 2.5)                                    # foundations of a house (scenery)
    # the theatre: the orchestra 3 m below the excavations, the cavea climbs back up in half-metre rows
    P.ground(13, 39, 5, 13, -1.0, "castello_pav")
    for i, z in enumerate(range(14, 20)):
        P.ground(12, 40, z, z, -0.5 + 0.5 * i, "lastricato")


SPEC = dict(
    paint=paint, mat="lastricato", gate1=24, gate2=34,
    start=(20, 57), north_zone=(24, 50),
    start_text="Tindari, al tramonto. Turi 'a Vulpi e' passato di qui: il cancello degli scavi e' chiuso.",
    seq=[("VASO_BIANCO_ULIVO", 12, 47, 0.0), ("LAMPIONE_PIAZZA", 36, 54, 0.0), ("PANCHINA", 28, 46, 0.0)],
    seq_hint="Il cancello degli scavi e' chiuso. Sulla targa dei pellegrini: \"Il pellegrino saluta l'ulivo, "
             "accende la lampada e siede ad aspettare: allora il custode gli apre.\" Il custode e' uno della banda...",
    seq_step="Il rito del pellegrino... (%d di %d)",
    seq_bad="Non e' il rito della targa. Si ricomincia dall'ulivo.",
    seq_done="Il rito e' compiuto: il cancello degli scavi si apre. E il custode non e' un custode.",
    north_enemies=[(K.BADDY1, 40, 46)], north_text="Uno della banda sul piazzale!",
    centro_enemies=[(K.BADDY2, 36, 30), (K.DOBERMAN, 50, 26)], centro_text="Il falso custode e il suo cane!",
    item=(7, 8), item_cells=[(13, 31)], climbs={(13, 29): [(13, 30)]},
    device="INTERNO_ALTARE", device_at=(30.5, 25.5), device_r=1700,
    device_half="Il primo Astro e' al suo posto sull'altare. Ne manca uno.",
    device_text="Castore e Polluce di nuovo insieme sull'altare: il cancello del teatro si apre.",
    gate2_hint="Il cancello del Teatro Greco e' chiuso. Sull'altare accanto ci sono due impronte a stella.",
    gate2_have="Gli Astri vanno sull'altare qui accanto: Azione davanti all'altare.",
    south_enemies=[(K.BADDY1, 18, 8), (K.BADDY1, 34, 8)], boss=(26, 9),
    south_text="Il Teatro Greco. Turi 'a Vulpi non c'e': c'e' il suo braccio destro.",
    exit=(56, 4), end_text="Dalla rupe una scala scende al mare. Turi e' andato giu', verso la citta' sommersa.",
    end_no="Il braccio destro di Turi e' ancora nel teatro.",
    pickups=[(K.SMALLMEDI, 16, 52), (K.UZI_AMMO, 52, 38), (K.BIGMEDI, 44, 16), (K.SHOTGUN_AMMO1, 8, 6)],
    secrets={9: (42, 34, 2.5, "Sulle fondamenta della casa greca: una Stella dei Dioscuri!"),
             10: (57, 46, None, "All'angolo del santuario: una Stella dei Dioscuri!")},
    props=[("INTERNO_COLONNA", 18.5, 36.5, 0.0), ("INTERNO_COLONNA", 24.5, 36.5, 0.0), ("INTERNO_COLONNA", 50.5, 30.5, 0.0),
           ("ULIVO", 54.5, 25.5, 0.0), ("LAMPIONE_PIAZZA", 16.5, 44.5, 0.0), ("PANCHINA", 40.5, 58.0, 0.0)],
    notes=["", "LIVELLO 5 - TINDARI",
           "1. Il cancello degli scavi: il rito del pellegrino (ulivo nel vaso, lampione, panchina).",
           "2. L'Astro di Castore e' in cima al basamento del tempio (si scala dalla parete sud); l'Astro di Polluce",
           "   lo lascia il falso custode. Tutti e due sull'altare accanto al cancello del teatro.",
           "3. Nel teatro il braccio destro di Turi; morto lui, si esce a sud-est verso il mare.",
           "   Segreto 10: le fondamenta della casa greca. Segreto 11: l'angolo del santuario."],
)


def extra(ctx):
    k = ctx.kit
    k.climb(13, 29, "+z")
    k.place(K.PUZZLE_ITEM[7], 13, 31, name="astro_castore")
    ctx.lua.drop("polluce", "centro0", "ID.PUZZLE_ITEM8", "Il falso custode aveva l'Astro di Polluce.")
    ctx.lua.zone("tempio", k.lua_pos(13, 27, ctx.ground(13, 27)), r=2200, dy=2000,
                 text="Sul basamento del tempio brilla qualcosa. La parete a sud si puo' scalare.")


SPEC["extra"] = extra


def prepare(world):
    L.paint_base(world, SPEC)


def build(ctx):
    L.build(ctx, SPEC, 6)
