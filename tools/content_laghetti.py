"""Livello 4 - I Laghetti (pomeriggio). v9: zona compatta disegnata a mano (livello.py).

Nord: la masseria; la grata del sentiero si apre a chi fa il giro del pastore (fico d'India, ulivo nel
vaso, panchina). Centro: la Conchiglia del canto e' in cima a uno sperone, che si scala dalla parete
liscia a sud. Sud: il Lago Verde, il capo e l'imbocco del Sentiero Coda di Volpe.
"""
import kit as K
import livello as L

FRAME = L.frame(38.1420, 15.0515)
PILLAR = (44, 46, 30, 32)          # x0, x1, z0, z1: rock spur, 4 m above the path


def paint(P):
    P.block("masseria", 40, 52, 49, 57, 6.0)
    P.ground(2, 59, 43, 59, 2.0, "erba_secca")
    P.ground(2, 59, 23, 40, 2.0, "terra")
    x0, x1, z0, z1 = PILLAR
    P.rock(x0, x1, z0, z1, 6.0)
    P.rock(8, 12, 30, 36, 3.0)                                    # a lower ledge, just scenery
    P.pool(8, 30, 6, 14, 2.5, lagoon=True)                        # Lago Verde


SPEC = dict(
    paint=paint, mat="erba_secca", gate1=20, gate2=36,
    start=(10, 57), north_zone=(22, 50),
    start_text="I laghetti sotto la rupe. Il sentiero sale, ma la grata del pastore e' chiusa.",
    seq=[("FICO_INDIA_GRANDE", 12, 47, 0.0), ("VASO_BIANCO_ULIVO", 30, 56, 0.0), ("PANCHINA", 32, 46, 0.0)],
    seq_hint="La grata del sentiero e' chiusa. Sul palo, il cartello del pastore: \"Chi vuole passare fa il mio giro: "
             "il fico d'India, l'ulivo nel vaso bianco, la panchina della masseria. Il cane sente e apre.\"",
    seq_step="Il giro del pastore... (%d di %d)",
    seq_bad="Il giro e' sbagliato. Si riparte dal fico d'India.",
    seq_done="Il giro del pastore e' completo: un fischio, e la grata del sentiero si apre.",
    north_enemies=[(K.DOBERMAN, 26, 52), (K.DOBERMAN, 34, 50)], north_text="I cani della masseria!",
    centro_enemies=[(K.BADDY1, 24, 34), (K.BADDY2, 54, 27)], centro_text="Gli uomini della Volpe sorvegliano lo sperone.",
    item=5, item_cells=[(45, 31)], climbs={(45, 29): [(45, 30)]},
    device="INTERNO_ALTARE", device_at=(32.5, 25.5), device_r=1700,
    device_text="La Conchiglia del canto nell'edicola: un suono lungo, e la grata del lago si apre.",
    gate2_hint="La grata del lago e' chiusa. Sull'edicola accanto c'e' un incavo a forma di conchiglia.",
    gate2_have="La conchiglia va nell'incavo dell'edicola, qui accanto: Azione davanti all'edicola.",
    south_enemies=[(K.BADDY1, 38, 10), (K.BADDY1, 46, 16)], boss=(42, 8),
    south_text="Il Lago Verde. Il capo della banda aspetta all'imbocco del sentiero.",
    exit=(55, 4), end_text="Il Sentiero Coda di Volpe sale la rupe fino al santuario di Tindari.",
    end_no="Il capo della banda e' ancora qui al lago.",
    pickups=[(K.SMALLMEDI, 8, 45), (K.SHOTGUN_ITEM, 16, 26), (K.SHOTGUN_AMMO1, 52, 38), (K.BIGMEDI, 36, 18), (K.SHOTGUN_AMMO1, 54, 10)],
    secrets={7: (10, 33, 3.0, "Sulla cengia sopra il sentiero: una Stella dei Dioscuri!"),
             8: (57, 58, None, "Dietro la masseria: una Stella dei Dioscuri!")},
    props=[("ULIVO", 8.5, 54.5, 0.0), ("ULIVO", 22.5, 57.5, 90.0), ("PINO_ALEPPO_GIOVANE", 54.5, 34.5, 0.0),
           ("FICO_INDIA_PICCOLO", 40.5, 37.5, 0.0), ("ELICRISO_GRUPPO", 47.5, 28.5, 0.0), ("BARCHETTA_SPIAGGIA", 33.5, 10.5, 0.0)],
    notes=["", "LIVELLO 4 - I LAGHETTI",
           "1. La grata del sentiero: il giro del pastore (fico d'India, ulivo nel vaso bianco, panchina).",
           "2. La Conchiglia del canto e' in cima allo sperone: si scala dalla parete a sud. Va nell'edicola accanto alla grata del lago.",
           "3. Al Lago Verde il capo della banda; morto lui, si esce a sud-est dal sentiero.",
           "   Segreto 8: la cengia a ovest (ci si arrampica dal sentiero). Segreto 9: dietro la masseria."],
)


def extra(ctx):
    k = ctx.kit
    k.climb(45, 29, "+z")
    k.place(K.PUZZLE_ITEM[5], 45, 31, name="conchiglia")
    ctx.lua.zone("sperone", k.lua_pos(45, 27, ctx.ground(45, 27)), r=2200, dy=2000,
                 text="In cima allo sperone qualcosa brilla. La parete liscia a sud ha appigli: si puo' scalare.")


SPEC["extra"] = extra


def prepare(world):
    L.paint_base(world, SPEC)


def build(ctx):
    L.build(ctx, SPEC, 5)
