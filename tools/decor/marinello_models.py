"""Statics of Marinello and the tonnara (ids 200-229). Metres, Y up, origin at the base centre."""
import math

import numpy as np

from decor import geom as G
from decor.geom import M
from decor.models import cbox, hull_mesh, model


@model(300, "CHIUSA", "Chiusa della tonnara: due spalle di pietra, paratoia di ferro, vite e scatola dell'ingranaggio (qui va la manovella)")
def chiusa():
    m = G.Mesh()
    for x in (-1.15, 1.15):
        m.merge(G.box(0.6, 1.9, 0.9, "m_stone", center=(x, 0, 0)))
    m.merge(G.box(2.9, 0.22, 0.35, "m_wood_dark", center=(0, 1.9, 0)))
    m.merge(G.box(1.7, 1.25, 0.1, "m_iron", center=(0, 0.05, 0)))
    m.merge(G.cylinder(0.05, 0.05, 1.0, "m_rust", n=6, base=(0, 1.3, 0)))
    m.merge(G.box(0.34, 0.34, 0.3, "m_rust", center=(1.15, 1.0, -0.55)))
    m.merge(G.cylinder(0.05, 0.05, 0.18, "m_iron", n=6, base=(1.15, 1.12, -0.78)))
    return m, cbox(2.9, 2.1, 0.9)


@model(301, "CASSA_LEGNO", "Cassa di legno, 90 cm")
def cassa():
    return G.box(0.9, 0.9, 0.9, "m_wood"), cbox(0.9, 0.9, 0.9)


@model(302, "BOTTE", "Botte da tonnara con i cerchi di ferro")
def botte():
    m = G.cylinder(0.36, 0.42, 0.5, "m_wood", n=10, top_cap=False)
    m.merge(G.cylinder(0.42, 0.36, 0.5, "m_wood", n=10, base=(0, 0.5, 0), cap="m_wood_dark"))
    for y in (0.12, 0.5, 0.86):
        m.merge(G.cylinder(0.43, 0.43, 0.05, "m_iron", n=10, base=(0, y, 0), top_cap=False))
    return m, cbox(0.85, 1.0, 0.85)


@model(303, "RETI", "Mucchio di reti con i galleggianti")
def reti():
    m = G.ellipsoid(0.9, 0.38, 0.65, "m_net", n=8, rings=4, center=(0, 0.1, 0), squash_bottom=0.3)
    m.merge(G.ellipsoid(0.5, 0.3, 0.45, "m_net", n=6, rings=4, center=(0.5, 0.12, 0.35), squash_bottom=0.3))
    for x, z in ((-0.5, 0.4), (0.2, -0.45), (0.8, 0.1)):
        m.merge(G.ellipsoid(0.09, 0.09, 0.09, "m_float", n=5, rings=3, center=(x, 0.36, z)))
    return m, None


@model(304, "ANCORA", "Ancora di ferro arrugginita, 2 m, coricata")
def ancora():
    m = G.tube([(0, 0.18, -1.0), (0, 0.22, 0.9)], [0.07, 0.06], "m_rust", n=6)
    m.merge(G.tube([(-0.75, 0.5, -0.55), (-0.45, 0.2, -0.95), (0, 0.15, -1.05), (0.45, 0.2, -0.95), (0.75, 0.5, -0.55)],
                   [0.03, 0.07, 0.08, 0.07, 0.03], "m_rust", n=6))
    m.merge(G.tube([(-0.6, 0.22, 0.7), (0.6, 0.22, 0.7)], [0.05, 0.05], "m_rust", n=5))
    return G.grounded(m), cbox(1.5, 0.5, 2.0)


@model(305, "TENDA", "Tenda canadese dei tombaroli, 3 x 2,4 m")
def tenda():
    m = G.Mesh()
    L, W, H = 1.5, 1.2, 1.7
    for s in (-1, 1):
        m.merge(G.quad((0, H, -L), (0, H, L), (s * W, 0, L), (s * W, 0, -L), "m_canvas", double=True))
    m.merge(G.quad((0, H, -L), (W, 0, -L), (-W, 0, -L), (-W, 0, -L), "m_canvas", double=True))
    m.merge(G.cylinder(0.03, 0.03, H, "m_wood_dark", n=4, base=(0, 0, L)))
    return m, cbox(2.2, 1.5, 3.0)


@model(306, "FALO", "Fuoco da campo: pietre, legni, brace")
def falo():
    m = G.Mesh()
    for k in range(8):
        a = 2 * math.pi * k / 8
        m.merge(G.ellipsoid(0.14, 0.1, 0.12, "m_rock", n=5, rings=3, center=(math.cos(a) * 0.5, 0.08, math.sin(a) * 0.5)))
    m.merge(G.tube([(-0.35, 0.05, -0.2), (0.3, 0.3, 0.2)], [0.06, 0.05], "m_wood_dark", n=5))
    m.merge(G.tube([(0.35, 0.05, -0.25), (-0.3, 0.28, 0.2)], [0.06, 0.05], "m_wood_dark", n=5))
    m.merge(G.disc(0.33, "m_ember", center=(0, 0.04, 0), n=8))
    return m, None


@model(307, "CANNE", "Ciuffo di canne (Arundo), 2,8 m")
def canne():
    return G.cross_cards(2.4, 2.8, "m_reed", 3, rng=np.random.default_rng(71)), None


@model(308, "CANNE_FITTE", "Canneto fitto: quattro ciuffi, 3,2 m")
def canne_fitte():
    r = np.random.default_rng(72)
    m = G.Mesh()
    for x, z in ((0, 0), (0.8, 0.5), (-0.7, 0.6), (0.2, -0.8)):
        m.merge(G.cross_cards(2.4, r.uniform(2.6, 3.3), "m_reed", 3, center=(x, 0, z), rng=r))
    return m, None


def boulder(rx, ry, rz, seed, n=9):
    """An irregular rock: an ellipsoid whose vertices are pushed in and out by a lumpy field of their own
    position (so the duplicated seam vertices move together and the surface stays closed)."""
    r = np.random.default_rng(seed)
    m = G.ellipsoid(rx, ry, rz, "m_rock", n=n, rings=6, center=(0, ry * 0.5, 0), squash_bottom=0.5)
    ph = r.uniform(0, 6.28, 6)
    for p in m.v:
        x, y, z = p[0] / M, p[1] / M, p[2] / M
        k = 1 + 0.2 * math.sin(3.1 * x / rx + ph[0]) * math.sin(2.7 * z / rz + ph[1]) + 0.14 * math.sin(4.3 * y / ry + ph[2] + 2 * x)
        k += 0.1 * math.sin(7 * x + ph[3]) * math.sin(6 * z + ph[4])
        p[0] *= k
        p[2] *= k
        p[1] *= 1 + 0.16 * math.sin(2.2 * x / rx + ph[5]) * math.cos(2.5 * z / rz)
    return m


@model(309, "SCOGLIO", "Masso di roccia, 1,6 m")
def scoglio():
    return boulder(0.8, 0.6, 0.65, 81), cbox(1.3, 0.9, 1.1)


@model(310, "SCOGLIO_GRANDE", "Scoglio grande, 3 m")
def scoglio_grande():
    m = boulder(1.5, 1.2, 1.2, 82, n=8)
    m.merge(boulder(0.9, 0.8, 0.8, 83).transformed(t=(1.1 * M, 0, 0.6 * M)))
    return m, cbox(3.0, 1.6, 2.2, cx=0.3)


@model(311, "PALO_ORMEGGIO", "Palo d'ormeggio con la cima")
def palo():
    m = G.cylinder(0.13, 0.11, 1.4, "m_wood_dark", n=7)
    m.merge(G.cylinder(0.15, 0.15, 0.12, "m_rope", n=7, base=(0, 0.9, 0), top_cap=False))
    return m, cbox(0.3, 1.4, 0.3)


@model(312, "TRAVI_CROLLATE", "Travi del tetto crollate, 4 m, appoggiate di sbieco")
def travi():
    m = G.tube([(-1.8, 0.1, -0.4), (1.8, 2.3, 0.3)], [0.11, 0.1], "m_wood_dark", n=5)
    m.merge(G.tube([(-1.5, 0.1, 0.8), (1.9, 1.9, 0.9)], [0.1, 0.1], "m_wood_dark", n=5))
    m.merge(G.tube([(-0.9, 0.12, -1.2), (0.6, 0.14, 1.4)], [0.1, 0.1], "m_wood_dark", n=5))
    return m, None


@model(313, "RELITTO", "Relitto di barca da tonnara, 5 m, sbandato e mezzo insabbiato")
def relitto():
    m, st = hull_mesh(5.0, 1.8, 0.85, "m_wreck")
    for z in (-1.6, -0.8, 0.0, 0.8, 1.5):
        m.merge(G.box(1.5, 0.07, 0.08, "m_wood_dark", center=(0, 0.5, z)))
    return m.transformed(rz=0.38, t=(0, -0.2 * M, 0)), cbox(2.0, 0.9, 5.0)


@model(314, "PALIZZATA", "Tratto di palizzata di tavole, 2 x 2,4 m")
def palizzata():
    m = G.Mesh()
    r = np.random.default_rng(84)
    for k in range(7):
        m.merge(G.box(0.27, 2.2 + r.uniform(-0.15, 0.2), 0.06, "m_wood", center=(-0.86 + k * 0.287, 0, 0)))
    for y in (0.5, 1.7):
        m.merge(G.box(2.0, 0.14, 0.08, "m_wood_dark", center=(0, y, 0.07)))
    return m, cbox(2.0, 2.4, 0.3)


@model(315, "PIASTRA_PIETRA", "Lastra di pietra a pressione, 1,6 m")
def piastra():
    m = G.box(1.6, 0.06, 1.6, "m_stone", top="m_rock")
    m.merge(G.box(0.9, 0.04, 0.9, "m_iron", center=(0, 0.06, 0)))
    return m, None


@model(316, "TAVOLACCIO", "Tavolo grezzo da lavoro, 1,4 x 0,8 m, alto 80 cm")
def tavolaccio():
    m = G.box(1.4, 0.07, 0.8, "m_wood", center=(0, 0.73, 0), bottom=True)
    for x in (-0.6, 0.6):
        for z in (-0.3, 0.3):
            m.merge(G.box(0.08, 0.73, 0.08, "m_wood_dark", center=(x, 0, z)))
    return m, cbox(1.4, 0.8, 0.8)


@model(317, "ANFORA", "Anfora romana incrostata")
def anfora():
    m = G.tube([(0, 0.0, 0), (0, 0.25, 0), (0, 0.6, 0), (0, 0.85, 0), (0, 1.0, 0)], [0.03, 0.2, 0.24, 0.1, 0.09], "m_clay", n=7)
    return G.grounded(m.transformed(rz=1.25), 0.02), None          # lying on its side, on the ground (it used to hover 11 cm)


@model(318, "FALDA_TETTO", "Falda di tetto in coppi su travi, 4 x 4,4 m: si appoggia in cima ai muri (origine al colmo basso)")
def falda():
    m = G.Mesh()
    for i in range(2):          # 2 x 2 panels, the tile texture once per panel
        for j in range(2):
            x0, x1 = -2 + 2 * i, 2 * i
            z0, z1 = -2.2 + 2.2 * j, 2.2 * j
            y = lambda z: 1.3 * (2.2 - z) / 4.4
            m.merge(G.quad((x0, y(z0), z0), (x1, y(z0), z0), (x1, y(z1), z1), (x0, y(z1), z1), "m_tiles", double=True))
    for x in (-1.6, 0, 1.6):
        m.merge(G.tube([(x, 1.22, -2.2), (x, -0.08, 2.2)], [0.08, 0.08], "m_wood_dark", n=4))
    return m, None


@model(319, "SCALA_CORDA", "Scala di corda spezzata, 5 m, appesa (origine in alto)")
def scala_corda():
    m = G.Mesh()
    for x in (-0.25, 0.25):
        m.merge(G.tube([(x, 0, 0), (x * 1.1, -2.5, 0.05), (x, -5.0, 0)], [0.025, 0.025, 0.025], "m_rope", n=4))
    for k in range(11):
        m.merge(G.box(0.6, 0.04, 0.06, "m_wood_dark", center=(0, -0.4 - k * 0.42, 0)))
    return m, None


@model(320, "RUDERE_ARCO", "Arco di pietra del portale della tonnara, luce 2 m, alto 3,4 m")
def arco():
    m = G.Mesh()
    for x in (-1.3, 1.3):
        m.merge(G.box(0.6, 2.4, 0.9, "m_stone", center=(x, 0, 0)))
    for k in range(7):
        a = math.pi * (k + 0.5) / 7
        m.merge(G.box(0.62, 0.5, 0.9, "m_stone", center=(math.cos(a) * 1.3, 2.3 + math.sin(a) * 0.75 - 0.25, 0)))
    return m, None
