"""Statics of the myth (ids 321-339): the cave of Donna Villa, the ruins of Tindari, the temple of the Dioscuri.
Metres, Y up, origin at the base centre (hanging pieces: origin at the top)."""
import math

from decor import geom as G
from decor.models import cbox, model


@model(321, "ALTARE_CONCHIGLIA", "Altare di roccia con una grande conchiglia (il canto di Donna Villa)")
def altare_conchiglia():
    m = G.cylinder(0.5, 0.38, 0.9, "m_cave", n=7)
    m.merge(G.cylinder(0.38, 0.55, 0.12, "m_cave", n=7, base=(0, 0.9, 0)))
    m.merge(G.ellipsoid(0.3, 0.2, 0.22, "m_shell", n=8, rings=4, center=(0, 1.2, 0)))
    m.merge(G.cylinder(0.05, 0.16, 0.3, "m_shell", n=6, base=(0.22, 1.12, 0), axis="x"))
    return m, cbox(1.0, 1.3, 1.0)


@model(322, "STALAGMITE", "Stalagmite, 1,8 m")
def stalagmite():
    m = G.cylinder(0.42, 0.2, 0.9, "m_cave", n=7, top_cap=False)
    m.merge(G.cylinder(0.2, 0.03, 0.9, "m_cave", n=7, base=(0.03, 0.9, 0.02)))
    return m, cbox(0.7, 1.6, 0.7)


@model(323, "STALATTITE", "Stalattite, 1,6 m, appesa (origine in alto)")
def stalattite():
    m = G.cylinder(0.04, 0.22, 0.8, "m_cave", n=6, base=(0, -1.6, 0), top_cap=False)
    m.merge(G.cylinder(0.22, 0.4, 0.8, "m_cave", n=6, base=(0, -0.8, 0), top_cap=False))
    return m, None


@model(324, "PIEDISTALLO", "Piedistallo di marmo, 1 m")
def piedistallo():
    m = G.box(0.8, 0.14, 0.8, "m_marble")
    m.merge(G.box(0.56, 0.74, 0.56, "m_marble", center=(0, 0.14, 0)))
    m.merge(G.box(0.76, 0.12, 0.76, "m_marble", center=(0, 0.88, 0)))
    return m, cbox(0.8, 1.0, 0.8)


def _drums(h, r0=0.46, r1=0.38, n=10, y0=0.0):
    m = G.Mesh()
    k = max(1, int(round(h / 1.0)))
    for i in range(k):
        a, b = i / k, (i + 1) / k
        m.merge(G.cylinder(r0 + (r1 - r0) * a, r0 + (r1 - r0) * b, h / k, "m_limestone", n=n, base=(0, y0 + h * a, 0), top_cap=(i == k - 1)))
    return m


@model(325, "COLONNA", "Colonna dorica, 5 m, con capitello")
def colonna():
    m = _drums(4.5)
    m.merge(G.cylinder(0.4, 0.6, 0.22, "m_limestone", n=10, base=(0, 4.5, 0)))
    m.merge(G.box(1.25, 0.28, 1.25, "m_limestone", center=(0, 4.72, 0)))
    return m, cbox(0.95, 5.0, 0.95)


@model(326, "COLONNA_ROTTA", "Colonna spezzata, 1,7 m")
def colonna_rotta():
    m = _drums(1.5)
    m.merge(G.cylinder(0.4, 0.3, 0.25, "m_limestone", n=7, base=(0.05, 1.5, 0.04)))
    return m, cbox(0.95, 1.7, 0.95)


@model(327, "ROCCHIO", "Rocchio di colonna caduto")
def rocchio():
    return G.cylinder(0.44, 0.42, 1.0, "m_limestone", n=10, base=(-0.5, 0.44, 0), axis="x", cap="m_limestone"), cbox(1.0, 0.9, 0.9)


@model(328, "STATUA_DIOSCURO", "Statua di un Dioscuro con il berretto a punta e la lancia, 2,7 m con la base")
def statua():
    m = G.box(0.9, 0.5, 0.9, "m_marble")
    m.merge(G.cylinder(0.3, 0.22, 0.9, "m_marble", n=8, base=(0, 0.5, 0)))            # legs and tunic
    m.merge(G.cylinder(0.24, 0.34, 0.6, "m_marble", n=8, base=(0, 1.4, 0)))           # chest
    m.merge(G.ellipsoid(0.16, 0.19, 0.17, "m_marble", n=8, rings=4, center=(0, 2.2, 0)))
    m.merge(G.cylinder(0.18, 0.04, 0.3, "m_marble", n=8, base=(0, 2.33, 0)))          # the pileus
    m.merge(G.tube([(0.3, 1.9, 0), (0.42, 1.5, 0.12), (0.4, 1.2, 0.2)], [0.08, 0.07, 0.06], "m_marble", n=5))
    m.merge(G.tube([(-0.3, 1.9, 0), (-0.45, 1.6, 0.1), (-0.45, 1.35, 0.25)], [0.08, 0.07, 0.06], "m_marble", n=5))
    m.merge(G.cylinder(0.025, 0.025, 2.2, "m_bronze", n=5, base=(-0.45, 0.5, 0.25)))
    return m, cbox(0.9, 2.7, 0.9)


@model(329, "ARGANO_TEATRO", "Argano di legno del teatro: tamburo con la fune e quattro stanghe")
def argano():
    m = G.Mesh()
    for x in (-0.7, 0.7):
        m.merge(G.box(0.16, 1.3, 0.9, "m_wood_dark", center=(x, 0, 0)))
    m.merge(G.cylinder(0.26, 0.26, 1.24, "m_rope", n=8, base=(-0.62, 0.95, 0), axis="x", cap="m_wood"))
    for a in range(4):
        an = math.pi / 2 * a + 0.4
        m.merge(G.tube([(0.86, 0.95, 0), (0.86, 0.95 + math.cos(an) * 0.6, math.sin(an) * 0.6)], [0.04, 0.035], "m_wood", n=5))
    m.merge(G.box(1.6, 0.12, 1.0, "m_wood", center=(0, 0, 0)))
    return m, cbox(1.7, 1.4, 1.0)


@model(330, "ALTARE_ASTRI", "Altare dei Dioscuri: due incavi rotondi, uno di bronzo e uno d'oro")
def altare_astri():
    m = G.box(2.6, 0.2, 1.3, "m_marble")
    m.merge(G.box(2.2, 0.75, 1.0, "m_marble", center=(0, 0.2, 0)))
    m.merge(G.box(2.5, 0.15, 1.25, "m_marble", center=(0, 0.95, 0)))
    m.merge(G.disc(0.3, "m_bronze", center=(-0.6, 1.105, 0), n=10))
    m.merge(G.disc(0.3, "m_gold", center=(0.6, 1.105, 0), n=10))
    return m, cbox(2.6, 1.1, 1.3)


@model(331, "BRACIERE", "Braciere di bronzo su treppiede")
def braciere():
    m = G.Mesh()
    for k in range(3):
        a = 2 * math.pi * k / 3
        m.merge(G.tube([(math.cos(a) * 0.4, 0, math.sin(a) * 0.4), (math.cos(a) * 0.18, 1.0, math.sin(a) * 0.18)], [0.04, 0.03], "m_bronze", n=5))
    m.merge(G.cylinder(0.2, 0.42, 0.25, "m_bronze", n=9, base=(0, 1.0, 0), top_cap=False))
    m.merge(G.disc(0.4, "m_ember", center=(0, 1.22, 0), n=9))
    return m, cbox(0.8, 1.3, 0.8)


@model(332, "SARCOFAGO", "Sarcofago di pietra con il coperchio spostato")
def sarcofago():
    m = G.box(2.2, 0.8, 0.9, "m_limestone")
    m.merge(G.box(2.3, 0.18, 1.0, "m_limestone", center=(0.25, 0.8, 0.12)))
    return m, cbox(2.3, 1.0, 1.0)


@model(333, "TRANSENNA", "Transenna arancione dei tombaroli, 2 m")
def transenna():
    m = G.Mesh()
    for x in (-0.95, 0.95):
        m.merge(G.cylinder(0.035, 0.035, 1.1, "m_iron", n=5, base=(x, 0, 0)))
    m.merge(G.quad((-0.95, 1.05, 0), (0.95, 1.05, 0), (0.95, 0.25, 0), (-0.95, 0.25, 0), "m_orange", double=True))
    return m, cbox(2.0, 1.1, 0.2)


@model(334, "IMPALCATURA", "Impalcatura di tubi e tavole, 2 x 1 x 3 m")
def impalcatura():
    m = G.Mesh()
    for x in (-1.0, 1.0):
        for z in (-0.5, 0.5):
            m.merge(G.cylinder(0.035, 0.035, 3.0, "m_iron", n=5, base=(x, 0, z)))
    for y in (1.5, 2.9):
        m.merge(G.box(2.1, 0.06, 1.0, "m_wood", center=(0, y, 0)))
    m.merge(G.tube([(-1.0, 0.1, -0.5), (1.0, 1.5, -0.5)], [0.03, 0.03], "m_iron", n=4))
    m.merge(G.tube([(1.0, 1.5, 0.5), (-1.0, 2.9, 0.5)], [0.03, 0.03], "m_iron", n=4))
    return m, None


@model(335, "FARO_CANTIERE", "Faro da cantiere su treppiede")
def faro():
    m = G.Mesh()
    for k in range(3):
        a = 2 * math.pi * k / 3
        m.merge(G.tube([(math.cos(a) * 0.45, 0, math.sin(a) * 0.45), (0, 1.5, 0)], [0.025, 0.025], "m_iron", n=4))
    m.merge(G.box(0.5, 0.35, 0.18, "m_yellow", center=(0, 1.5, 0)))
    m.merge(G.quad((-0.2, 1.8, 0.1), (0.2, 1.8, 0.1), (0.2, 1.55, 0.1), (-0.2, 1.55, 0.1), "m_ember", double=True))
    return m, None


@model(336, "MACERIE", "Mucchio di macerie e blocchi caduti")
def macerie():
    m = G.ellipsoid(1.1, 0.5, 0.9, "m_limestone", n=7, rings=4, center=(0, 0.1, 0), squash_bottom=0.3)
    m.merge(G.box(0.7, 0.45, 0.5, "m_limestone", center=(0.5, 0.3, 0.3)).transformed(ry=0.5, rz=0.3))
    m.merge(G.box(0.6, 0.4, 0.45, "m_limestone", center=(-0.6, 0.25, -0.2)).transformed(ry=-0.8, rx=0.2))
    return m, cbox(2.0, 0.8, 1.6)


@model(337, "GRADINATA", "Sedile di pietra del teatro, 2 m")
def gradinata():
    m = G.box(2.0, 0.42, 0.8, "m_limestone")
    return m, cbox(2.0, 0.42, 0.8)


@model(338, "RUOTA_CHIUSA", "Casello della chiusa: gabbiotto di ferro con il volante della paratoia")
def ruota_chiusa():
    m = G.box(0.9, 1.2, 0.6, "m_rust")
    m.merge(G.cylinder(0.05, 0.05, 0.3, "m_iron", n=5, base=(0, 0.75, -0.6), axis="z"))
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = 2 * math.pi * (k + 1) / 8
        m.merge(G.tube([(math.cos(a) * 0.4, 0.75 + math.sin(a) * 0.4, -0.5), (math.cos(b) * 0.4, 0.75 + math.sin(b) * 0.4, -0.5)], [0.03, 0.03], "m_iron", n=4))
    for k in range(4):
        a = math.pi / 2 * k
        m.merge(G.tube([(0, 0.75, -0.5), (math.cos(a) * 0.4, 0.75 + math.sin(a) * 0.4, -0.5)], [0.02, 0.02], "m_iron", n=4))
    return m, cbox(0.9, 1.2, 0.6)


@model(339, "COLONNA_TEMPIO", "Colonna del tempio dei Dioscuri, 13 m, marmo: dal fondo della cella alla volta")
def colonna_tempio():
    m = G.box(1.5, 0.3, 1.5, "m_marble")
    k = 8
    for i in range(k):
        a, b = i / k, (i + 1) / k
        m.merge(G.cylinder(0.62 - 0.12 * a, 0.62 - 0.12 * b, 12.0 / k, "m_marble", n=12, base=(0, 0.3 + 12.0 * a, 0), top_cap=(i == k - 1)))
    m.merge(G.cylinder(0.5, 0.78, 0.3, "m_marble", n=12, base=(0, 12.3, 0)))
    m.merge(G.box(1.6, 0.4, 1.6, "m_marble", center=(0, 12.6, 0)))
    return m, cbox(1.3, 13.0, 1.3)
