"""Decoration statics for Coda di Volpe. Every model: (id, name, mesh, collision box or None, note).

Sizes are real (metres). Collision boxes are in units, wad space (Y up), around the solid part only:
bushes and flowers have none, trees only their trunk.
"""
import math

import numpy as np

from decor import geom as G
from decor.geom import M

MODELS = []


def model(sid, name, note=""):
    def deco(fn):
        MODELS.append((sid, name, fn, note))
        return fn
    return deco


def cbox(w, h, d, cx=0.0, cz=0.0, y0=0.0):
    return ((cx - w / 2) * M, y0 * M, (cz - d / 2) * M), ((cx + w / 2) * M, (y0 + h) * M, (cz + d / 2) * M)


# ---------------------------------------------------------------------------------- vegetation
def lens(w, h, t, n=8):
    """Flat oval pad (outline in the XY plane, base at the origin) bulging +-t in Z: 2n triangles."""
    m = G.Mesh()
    rim = [np.array([math.sin(2 * math.pi * i / n) * w, h - math.cos(2 * math.pi * i / n) * h, 0]) * M for i in range(n + 1)]
    for side in (1, -1):
        c = np.array([0, h, side * t]) * M
        for i in range(n):
            a, b = (rim[i], rim[i + 1]) if side > 0 else (rim[i + 1], rim[i])
            u = lambda p: (0.5 + p[0] / M / (2 * w), 1 - p[1] / M / (2 * h))
            m.face([a, b, c], "opuntia", uv=[u(a), u(b), (0.5, 0.5)])
    return m


def opuntia(seed, levels, height):
    """Prickly pear: pads grow from the rim of the previous pad, leaning outwards, 2 per tip."""
    r = np.random.default_rng(seed)
    m = G.Mesh()
    size = height / levels / 0.8

    def pad(p, ry, tilt, s):
        w, h, t = 0.3 * s, 0.4 * s, 0.05
        body = lens(w, h, t)
        R = G.rot(tilt, ry, 0)
        m.merge(body.transformed(rx=tilt, ry=ry, t=np.array(p) * M))
        if r.random() < 0.3:
            for k in range(r.integers(1, 3)):
                a = r.uniform(-0.9, 0.9)
                q = R @ np.array([math.sin(a) * w, 2 * h * (0.88 + 0.1 * math.cos(a)), 0]) + np.array(p)
                m.merge(G.ellipsoid(0.045, 0.065, 0.045, "fruit", n=3, rings=2, center=q))
        tips = []
        for a in (-0.6, 0.6):
            tips.append(R @ np.array([math.sin(a) * w * 0.8, 2 * h * 0.85, 0]) + np.array(p))
        return tips

    m.merge(G.tube([(0, 0, 0), (0.05, 0.35, 0.02)], [0.12, 0.09], "olive_bark", n=6))
    tips = [(np.array([x, 0.25, z]), r.uniform(0, 6.3)) for x, z in ((0, 0), (0.3, 0.15), (-0.25, 0.2), (0.05, -0.3))]
    for lev in range(levels):
        new = []
        for t, ry in tips:
            out = 0.2 + 0.25 * lev
            ty = ry + r.uniform(-0.6, 0.6)
            lean = r.choice([-1, 1]) * r.uniform(out * 0.6, out)
            for nt in pad(t, ty, lean, size * r.uniform(0.85, 1.1) * (1 - 0.08 * lev)):
                if r.random() < (0.75 if lev < 2 else 0.45):
                    new.append((nt, ty + r.uniform(0.8, 2.2)))
        tips = new[:7]
    return m


@model(100, "FICO_INDIA_GRANDE", "Opuntia ficus-indica, circa 2,2 m")
def fico_a():
    return opuntia(1, 4, 2.2), cbox(1.6, 1.8, 1.6)


@model(101, "FICO_INDIA_PICCOLO", "Opuntia giovane, circa 1,2 m")
def fico_b():
    return opuntia(2, 3, 1.2), cbox(1.0, 1.1, 1.0)


@model(102, "ELICRISO", "Helichrysum italicum, cuscinetto argentato con fiori gialli")
def elicriso_a():
    r = np.random.default_rng(3)
    m = G.cross_cards(0.7, 0.5, "heli_card", 3, rng=r)
    return m, None


@model(103, "ELICRISO_GRUPPO", "Tre cespi di elicriso")
def elicriso_b():
    r = np.random.default_rng(4)
    m = G.Mesh()
    for (x, z, s) in ((0, 0, 1.0), (0.5, 0.3, 0.8), (-0.4, 0.4, 0.7)):
        m.merge(G.cross_cards(0.7 * s, 0.5 * s, "heli_card", 3, center=(x, 0, z), rng=r))
    return m, None


@model(104, "ASPARAGO_SELVATICO", "Asparagus acutifolius, cespuglio spinoso")
def asparago_a():
    r = np.random.default_rng(5)
    return G.cross_cards(1.0, 0.9, "asp_card", 3, rng=r), None


@model(105, "ASPARAGO_ROVO", "Asparagi selvatici intrecciati a un cespuglio")
def asparago_b():
    r = np.random.default_rng(6)
    m = G.Mesh()
    for (x, z, s) in ((0, 0, 1.2), (0.6, -0.3, 0.9)):
        m.merge(G.cross_cards(1.1 * s, 1.0 * s, "asp_card", 3, center=(x, 0, z), rng=r))
    return m, None


def canopy(m, centers, region, r, card_w=2.4, card_d=2.0, layers=2, tilt=0.25):
    for c in centers:
        for k in range(layers):
            m.merge(G.hcard(card_w * r.uniform(0.85, 1.15), card_d * r.uniform(0.85, 1.15), region,
                            center=(c[0], c[1] + k * 0.35, c[2]), ry=r.uniform(0, math.pi), tilt=r.uniform(-tilt, tilt)))
        m.merge(G.card(card_w * 0.9, card_d * 0.7, region, center=(c[0], c[1] - card_d * 0.25, c[2]), ry=r.uniform(0, math.pi)))


def aleppo(seed, height, lean):
    r = np.random.default_rng(seed)
    m = G.Mesh()
    lx, lz = math.cos(lean[0]) * lean[1], math.sin(lean[0]) * lean[1]
    trunk = [(0, 0, 0), (lx * 0.3, height * 0.35, lz * 0.3), (lx * 0.7, height * 0.65, lz * 0.7), (lx, height * 0.8, lz)]
    m.merge(G.tube(trunk, [0.22, 0.18, 0.14, 0.1], "pine_bark", n=7))
    top = np.array(trunk[-1])
    centers = [top + np.array([0, 0.3, 0])]
    for k in range(r.integers(5, 8)):
        a = r.uniform(0, 2 * math.pi)
        d = r.uniform(1.0, height * 0.22)
        end = top + np.array([math.cos(a) * d, r.uniform(-0.6, 0.6), math.sin(a) * d])
        start = np.array(trunk[2]) + (top - np.array(trunk[2])) * r.uniform(0.3, 0.9)
        m.merge(G.tube([start, (start + end) / 2 + np.array([0, 0.3, 0]), end], [0.08, 0.06, 0.04], "pine_bark", n=5))
        centers.append(end + np.array([0, 0.2, 0]))
    for c in centers:
        for j in range(3):
            q = np.array(c) + np.array([r.uniform(-0.8, 0.8), r.uniform(-0.5, 0.6), r.uniform(-0.8, 0.8)])
            w = height * r.uniform(0.16, 0.24)
            m.merge(G.hcard(w, w * 0.8, "pine_card", center=q, ry=r.uniform(0, math.pi), tilt=r.uniform(-0.45, 0.45)))
            m.merge(G.card(w * 0.9, w * 0.55, "pine_card", center=q - np.array([0, w * 0.2, 0]), ry=r.uniform(0, math.pi)))
    return m


@model(106, "PINO_ALEPPO_GRANDE", "Pinus halepensis adulto, 12 m, chioma a ombrello")
def pino_a():
    return aleppo(7, 12.0, (0.4, 1.2)), cbox(0.5, 4.0, 0.5)


@model(107, "PINO_ALEPPO_INCLINATO", "Pino d'Aleppo piegato dal vento, 9 m")
def pino_b():
    return aleppo(8, 9.0, (2.0, 2.4)), cbox(0.45, 3.0, 0.45)


@model(108, "PINO_ALEPPO_GIOVANE", "Pino d'Aleppo giovane, 5 m")
def pino_c():
    r = np.random.default_rng(9)
    m = G.Mesh()
    m.merge(G.tube([(0, 0, 0), (0.1, 2.5, 0), (0.15, 4.6, 0.1)], [0.12, 0.08, 0.04], "pine_bark", n=6))
    for k, h in enumerate((1.8, 2.8, 3.7, 4.5)):
        s = 1.0 - k * 0.2
        canopy(m, [(0.1, h, 0)], "pine_card", r, card_w=2.6 * s, card_d=1.6 * s, layers=1)
    return m, cbox(0.3, 2.0, 0.3)


def olive(seed, height, width, gnarl):
    r = np.random.default_rng(seed)
    m = G.Mesh()
    # Twisted trunk splitting in 2-3 limbs.
    base = [(0, 0, 0), (r.uniform(-0.2, 0.2), 0.6, r.uniform(-0.2, 0.2)), (r.uniform(-0.3, 0.3), 1.2, r.uniform(-0.3, 0.3))]
    m.merge(G.tube(base, [0.35 * gnarl, 0.28 * gnarl, 0.22 * gnarl], "olive_bark", n=7))
    tops = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + r.uniform(-0.4, 0.4)
        p1 = np.array(base[-1]) + np.array([math.cos(a) * width * 0.15, height * 0.25, math.sin(a) * width * 0.15])
        p2 = p1 + np.array([math.cos(a) * width * 0.2, height * 0.25, math.sin(a) * width * 0.2])
        m.merge(G.tube([base[-1], p1, p2], [0.16 * gnarl, 0.11, 0.07], "olive_bark", n=6))
        tops.append(p2)
    centers = [t + np.array([0, 0.2, 0]) for t in tops] + [np.array([0, height * 0.82, 0])]
    canopy(m, centers, "olive_card", r, card_w=width * 0.55, card_d=width * 0.45, layers=2, tilt=0.35)
    return m


@model(109, "ULIVO", "Olea europaea coltivato, 5 m")
def ulivo_a():
    return olive(10, 5.0, 5.0, 1.0), cbox(0.8, 1.5, 0.8)


@model(110, "ULIVO_GIOVANE", "Ulivo giovane, 3,5 m")
def ulivo_b():
    return olive(11, 3.5, 3.4, 0.6), cbox(0.5, 1.2, 0.5)


@model(111, "ULIVO_SECOLARE", "Ulivo secolare dal tronco contorto, 6 m")
def ulivo_c():
    return olive(12, 6.0, 6.5, 1.6), cbox(1.2, 1.6, 1.2)


# ---------------------------------------------------------------------------------- lamps
def lantern(m, y, scale=1.0, x=0.0, z=0.0):
    """Classic four-sided cast-iron lantern (historic centres): glass box + pyramid hat + finial."""
    s = scale
    m.merge(G.box(0.18 * s, 0.06 * s, 0.18 * s, "iron", center=(x, y, z)))
    m.merge(G.cylinder(0.12 * s, 0.2 * s, 0.38 * s, "lamp_glass", n=4, base=(x, y + 0.06 * s, z), top_cap=False))
    m.merge(G.cylinder(0.26 * s, 0.02 * s, 0.2 * s, "iron", n=4, base=(x, y + 0.44 * s, z)))
    m.merge(G.cylinder(0.03 * s, 0.03 * s, 0.12 * s, "iron", n=4, base=(x, y + 0.62 * s, z)))


@model(112, "LAMPIONE_PIAZZA", "Palo in ghisa con lanterna, piazze e corso (4 m)")
def lamp_piazza():
    m = G.Mesh()
    m.merge(G.cylinder(0.16, 0.12, 0.6, "iron", n=8))
    m.merge(G.cylinder(0.07, 0.05, 3.0, "iron", n=6, base=(0, 0.6, 0)))
    m.merge(G.box(0.24, 0.05, 0.24, "iron", center=(0, 3.55, 0)))
    lantern(m, 3.6, 1.0)
    return m, cbox(0.3, 3.6, 0.3)


@model(113, "LAMPIONE_MURO", "Lanterna a braccio da muro, vicoli del centro (montare sulla facciata, il braccio va verso +Z)")
def lamp_muro():
    m = G.Mesh()
    m.merge(G.box(0.12, 0.3, 0.04, "iron", center=(0, 0, 0)))
    m.merge(G.tube([(0, 0.25, 0.02), (0, 0.32, 0.3), (0, 0.25, 0.55)], [0.025, 0.025, 0.025], "iron", n=4))
    m.merge(G.tube([(0, 0.05, 0.02), (0, 0.2, 0.25)], [0.02, 0.02], "iron", n=4))
    lantern(m, -0.35, 0.85, z=0.55)
    m.merge(G.cylinder(0.01, 0.01, 0.15, "iron", n=3, base=(0, -0.05, 0.55)))
    return m.transformed(t=(0, 3.4 * M, 0)), None


@model(114, "LAMPIONE_STRADA", "Palo stradale moderno a sbraccio, 8 m (lato strada verso +Z)")
def lamp_strada():
    m = G.Mesh()
    m.merge(G.cylinder(0.1, 0.06, 7.6, "galv", n=8))
    m.merge(G.tube([(0, 7.5, 0), (0, 8.0, 0.4), (0, 8.05, 1.4)], [0.05, 0.045, 0.04], "galv", n=5))
    m.merge(G.box(0.3, 0.12, 0.6, "galv", center=(0, 7.92, 1.6)))
    m.merge(G.quad((-0.12, 7.91, 1.35), (0.12, 7.91, 1.35), (0.12, 7.91, 1.85), (-0.12, 7.91, 1.85), "lamp_glass", double=True))
    return m, cbox(0.25, 7.0, 0.25)


@model(115, "LAMPIONE_LUNGOMARE", "Lampione del lungomare a due globi, 4,5 m")
def lamp_lungomare():
    m = G.Mesh()
    m.merge(G.cylinder(0.15, 0.1, 0.5, "iron_green", n=8))
    m.merge(G.cylinder(0.06, 0.05, 3.6, "iron_green", n=6, base=(0, 0.5, 0)))
    for s in (-1, 1):
        m.merge(G.tube([(0, 3.8, 0), (0.3 * s, 4.1, 0), (0.55 * s, 4.05, 0)], [0.03, 0.03, 0.03], "iron_green", n=4))
        m.merge(G.ellipsoid(0.17, 0.17, 0.17, "lamp_glass", n=8, rings=5, center=(0.55 * s, 4.25, 0)))
    m.merge(G.ellipsoid(0.17, 0.17, 0.17, "lamp_glass", n=8, rings=5, center=(0, 4.35, 0)))
    return m, cbox(0.3, 4.0, 0.3)


# ---------------------------------------------------------------------------------- street furniture
@model(116, "PANCHINA", "Panchina in legno e ghisa, 1,8 m")
def panchina():
    m = G.Mesh()
    for x in (-0.75, 0.75):
        m.merge(G.box(0.08, 0.45, 0.5, "iron", center=(x, 0, 0)))
        m.merge(G.box(0.08, 0.45, 0.08, "iron", center=(x, 0.45, 0.22)))
    m.merge(G.box(1.8, 0.06, 0.45, "wood_slats", center=(0, 0.42, 0)))
    m.merge(G.box(1.8, 0.35, 0.05, "wood_slats", center=(0, 0.55, 0.24)))
    return m, cbox(1.8, 0.5, 0.5)


def big_pot(m, plant, r):
    m.merge(G.cylinder(0.55, 0.7, 0.9, "white_plaster", n=10, cap="soil"))
    m.merge(G.cylinder(0.72, 0.72, 0.08, "white_plaster", n=10, base=(0, 0.9, 0), cap="soil"))
    if plant == "grass":
        m.merge(G.cross_cards(1.2, 1.1, "grass_card", 3, center=(0, 0.95, 0), rng=r))
    elif plant == "palm":
        m.merge(G.tube([(0, 0.95, 0), (0.05, 1.8, 0), (0.08, 2.4, 0)], [0.12, 0.1, 0.08], "pine_bark", n=6))
        for k in range(7):
            a = 2 * math.pi * k / 7
            q = G.card(2.0, 0.5, "frond", center=(0, 0, 0), ry=0, tilt=0)
            q = q.transformed(rz=-0.9 + r.uniform(-0.2, 0.2), ry=a, t=(0.08 * M, 2.35 * M, 0))
            m.merge(q)
    else:   # olive in a pot
        m.merge(G.tube([(0, 0.95, 0), (0.05, 1.6, 0)], [0.07, 0.05], "olive_bark", n=5))
        canopy(m, [(0, 1.9, 0)], "olive_card", r, card_w=1.4, card_d=1.0, layers=2)


@model(117, "VASO_BIANCO_FIORI", "Vaso gigante bianco con piante fiorite")
def vaso_a():
    m = G.Mesh()
    big_pot(m, "grass", np.random.default_rng(13))
    return m, cbox(1.4, 1.0, 1.4)


@model(118, "VASO_BIANCO_PALMA", "Vaso gigante bianco con palma nana")
def vaso_b():
    m = G.Mesh()
    big_pot(m, "palm", np.random.default_rng(14))
    return m, cbox(1.4, 1.0, 1.4)


@model(119, "VASO_BIANCO_ULIVO", "Vaso gigante bianco con ulivo")
def vaso_c():
    m = G.Mesh()
    big_pot(m, "olive", np.random.default_rng(15))
    return m, cbox(1.4, 1.0, 1.4)


# ---------------------------------------------------------------------------------- playground
@model(120, "GIOCHI_SCIVOLO", "Scivolo con scaletta, 3 m")
def scivolo():
    m = G.Mesh()
    for x in (-0.3, 0.3):
        m.merge(G.box(0.06, 1.6, 0.06, "plastic_blue", center=(x, 0, -1.0)))
        m.merge(G.box(0.06, 1.6, 0.06, "plastic_blue", center=(x, 0, -0.5)))
    m.merge(G.box(0.7, 0.08, 0.6, "plastic_yellow", center=(0, 1.5, -0.75)))
    for k in range(5):
        m.merge(G.box(0.6, 0.04, 0.12, "plastic_blue", center=(0, 0.3 * k, -1.2 - 0.12 * (5 - k))))
    m.merge(G.quad((-0.3, 1.55, -0.45), (0.3, 1.55, -0.45), (0.3, 0.25, 1.4), (-0.3, 0.25, 1.4), "plastic_red", double=True))
    for x in (-0.32, 0.32):
        m.merge(G.quad((x, 1.75, -0.45), (x, 1.75 - 0.0, -0.45), (x, 0.45, 1.4), (x, 0.25, 1.4), "plastic_red", double=True))
    return m, cbox(0.8, 1.6, 3.0, cz=0.0)


@model(121, "GIOCHI_ALTALENA", "Altalena a due posti, 2,2 m")
def altalena():
    m = G.Mesh()
    for x in (-1.3, 1.3):
        m.merge(G.tube([(x, 0, -0.7), (x, 2.2, 0)], [0.05, 0.05], "plastic_green", n=5))
        m.merge(G.tube([(x, 0, 0.7), (x, 2.2, 0)], [0.05, 0.05], "plastic_green", n=5))
    m.merge(G.tube([(-1.35, 2.2, 0), (1.35, 2.2, 0)], [0.05, 0.05], "plastic_green", n=5))
    for x in (-0.6, 0.6):
        for dx in (-0.2, 0.2):
            m.merge(G.tube([(x + dx, 2.2, 0), (x + dx, 0.45, 0)], [0.01, 0.01], "galv", n=3))
        m.merge(G.box(0.45, 0.04, 0.2, "rubber", center=(x, 0.43, 0)))
    return m, cbox(2.8, 2.2, 0.4)


@model(122, "GIOCHI_DONDOLO", "Altalena a bilico")
def dondolo():
    m = G.Mesh()
    m.merge(G.box(0.3, 0.45, 0.3, "plastic_yellow"))
    m.merge(G.quad((-0.15, 0.6, -1.5), (0.15, 0.6, -1.5), (0.15, 0.3, 1.5), (-0.15, 0.3, 1.5), "plastic_red", double=True))
    for z, y in ((-1.3, 0.58), (1.3, 0.33)):
        m.merge(G.box(0.4, 0.05, 0.3, "plastic_blue", center=(0, y, z)))
    return m, cbox(0.4, 0.5, 3.0)


@model(123, "GIOCHI_MOLLA", "Gioco a molla a forma di cavalluccio marino")
def molla():
    m = G.Mesh()
    m.merge(G.box(0.4, 0.05, 0.4, "concrete"))
    m.merge(G.cylinder(0.1, 0.1, 0.45, "iron", n=6, base=(0, 0.05, 0)))
    body = G.ellipsoid(0.18, 0.35, 0.4, "plastic_orange", n=8, rings=5, center=(0, 0.8, 0))
    m.merge(body)
    m.merge(G.ellipsoid(0.12, 0.18, 0.2, "plastic_orange", n=6, rings=4, center=(0, 1.2, 0.3)))
    m.merge(G.box(0.3, 0.04, 0.05, "rubber", center=(0, 1.05, 0.2)))
    return m, cbox(0.5, 1.0, 0.9)


@model(124, "GIOCHI_CASTELLO", "Torretta da arrampicata con tettuccio")
def castello_giochi():
    m = G.Mesh()
    for x in (-0.6, 0.6):
        for z in (-0.6, 0.6):
            m.merge(G.box(0.1, 2.6, 0.1, "wood_slats", center=(x, 0, z)))
    m.merge(G.box(1.3, 0.08, 1.3, "wood_slats", center=(0, 1.2, 0)))
    for x0, z0, x1, z1 in ((-0.65, 0.65, 0.65, 0.65), (0.65, -0.65, -0.65, -0.65), (0.65, 0.65, 0.65, -0.65)):
        m.merge(G.quad((x0, 1.9, z0), (x1, 1.9, z1), (x1, 1.28, z1), (x0, 1.28, z0), "plastic_green", double=True))
    m.merge(G.cylinder(1.0, 0.0, 0.8, "plastic_red", n=4, base=(0, 2.6, 0)).transformed(ry=math.pi / 4))
    for k in range(6):
        m.merge(G.box(0.05, 0.05, 1.2, "plastic_yellow", center=(-0.72, 0.2 * k, 0)))
    return m, cbox(1.4, 2.6, 1.4)


# ---------------------------------------------------------------------------------- sports fields
@model(125, "FARO_CAMPO", "Torre faro per campo sportivo, 14 m (proiettori verso +Z)")
def faro():
    m = G.Mesh()
    m.merge(G.cylinder(0.25, 0.12, 13.0, "galv", n=8))
    m.merge(G.box(2.2, 0.1, 0.3, "galv", center=(0, 13.0, 0.2)))
    for x in (-0.8, 0, 0.8):
        for y in (13.2, 13.9):
            m.merge(G.box(0.55, 0.5, 0.25, "galv", center=(x, y, 0.35)))
            m.merge(G.quad((x - 0.24, y + 0.46, 0.48), (x + 0.24, y + 0.46, 0.48), (x + 0.24, y + 0.04, 0.48), (x - 0.24, y + 0.04, 0.48), "lamp_glass"))
    return m, cbox(0.5, 13.0, 0.5)


@model(126, "RECINZIONE_CAMPO", "Rete metallica 2 x 3 m (modulo da affiancare lungo X)")
def recinzione():
    m = G.Mesh()
    for x in (-1.0, 1.0):
        m.merge(G.cylinder(0.04, 0.04, 3.0, "galv", n=5, base=(x, 0, 0)))
    m.merge(G.quad((-1.0, 3.0, 0), (1.0, 3.0, 0), (1.0, 0, 0), (-1.0, 0, 0), "chainlink", blend=1, double=True))
    m.merge(G.tube([(-1.0, 2.95, 0), (1.0, 2.95, 0)], [0.03, 0.03], "galv", n=4))
    return m, cbox(2.0, 3.0, 0.1)


@model(127, "PORTA_CALCIO", "Porta da calcio a 7 (5 x 2 m), rete verso -Z")
def porta():
    m = G.Mesh()
    for x in (-2.5, 2.5):
        m.merge(G.cylinder(0.06, 0.06, 2.0, "white_plaster", n=6, base=(x, 0, 0)))
    m.merge(G.tube([(-2.5, 2.0, 0), (2.5, 2.0, 0)], [0.06, 0.06], "white_plaster", n=6))
    m.merge(G.quad((-2.5, 2.0, 0), (2.5, 2.0, 0), (2.5, 0, -1.2), (-2.5, 0, -1.2), "goal_net", blend=1, double=True))
    for x in (-2.5, 2.5):
        m.merge(G.quad((x, 2.0, 0), (x, 2.0, 0.0), (x, 0, -1.2), (x, 0, 0), "goal_net", blend=1, double=True))
    return m, None


# ---------------------------------------------------------------------------------- boats
def hull_mesh(length, beam, depth, region, sheer=0.15, bow_rise=0.25, n=8):
    """Simple hull: stations along Z (bow at +Z), V section, deck at the top."""
    m = G.Mesh()
    stations = []
    for k in range(n + 1):
        t = k / n
        z = (t - 0.5) * length
        half = beam / 2 * math.sin(math.pi * min(0.98, 0.15 + 0.85 * t)) ** 0.7 if t > 0.5 else beam / 2 * (0.75 + 0.25 * math.sin(math.pi * t))
        if t > 0.97:
            half = 0.02
        top = depth + sheer * (2 * t - 1) ** 2 + (bow_rise * (t - 0.6) / 0.4 if t > 0.6 else 0)
        keel = depth * 0.0 + (0.25 * depth * (t - 0.8) / 0.2 if t > 0.8 else 0)
        stations.append((z, half, top, keel))
    for k in range(n):
        z0, h0, t0, k0 = stations[k]
        z1, h1, t1, k1 = stations[k + 1]
        u0, u1 = k / n, (k + 1) / n
        for s in (-1, 1):
            # side panel: gunwale -> chine -> keel
            pts = [(s * h0, t0, z0), (s * h1, t1, z1), (s * h1 * 0.85, depth * 0.35 + k1, z1), (s * h0 * 0.85, depth * 0.35 + k0, z0)]
            if s < 0:
                pts = [pts[1], pts[0], pts[3], pts[2]]
            m.merge(G.quad(*[np.array(p) / 1 for p in pts], region, uv=[(u0, 0.05), (u1, 0.05), (u1, 0.6), (u0, 0.6)] if s > 0 else
                           [(u1, 0.05), (u0, 0.05), (u0, 0.6), (u1, 0.6)]))
            pts2 = [(s * h0 * 0.85, depth * 0.35 + k0, z0), (s * h1 * 0.85, depth * 0.35 + k1, z1), (0, k1, z1), (0, k0, z0)]
            if s < 0:
                pts2 = [pts2[1], pts2[0], pts2[3], pts2[2]]
            m.merge(G.quad(*pts2, region, uv=[(u0, 0.62), (u1, 0.62), (u1, 1), (u0, 1)]))
    # transom
    z0, h0, t0, k0 = stations[0]
    m.merge(G.quad((h0, t0, z0), (-h0, t0, z0), (-h0 * 0.85, depth * 0.35, z0), (h0 * 0.85, depth * 0.35, z0), region))
    return m, stations


def deck(m, stations, region, inset=0.04):
    for k in range(len(stations) - 1):
        z0, h0, t0, _ = stations[k]
        z1, h1, t1, _ = stations[k + 1]
        m.merge(G.quad((-h0 + inset, t0 - 0.06, z0), (h0 - inset, t0 - 0.06, z0), (h1 - inset, t1 - 0.06, z1),
                       (-h1 + inset, t1 - 0.06, z1), region))


@model(128, "GOZZO", "Gozzo siciliano in legno, 6 m: bianco, fascia blu, opera viva rossa. Base = linea di galleggiamento")
def gozzo():
    m, st = hull_mesh(6.0, 2.0, 0.9, "hull_gozzo")
    deck(m, st, "deck_wood")
    m.merge(G.box(0.5, 0.25, 1.6, "deck_wood", center=(0, 0.55, -0.2)))
    m.merge(G.cylinder(0.06, 0.05, 0.6, "deck_wood", n=5, base=(0, 0.9, 2.6)))   # bow post
    return m.transformed(t=(0, -0.35 * M, 0)), cbox(2.0, 1.0, 6.0, y0=-0.35)


@model(129, "GOMMONE", "Gommone con consolle, 5 m")
def gommone():
    m = G.Mesh()
    m.merge(G.tube([(-0.85, 0.3, -2.3), (-0.8, 0.32, 1.2), (0, 0.4, 2.4), (0.8, 0.32, 1.2), (0.85, 0.3, -2.3)],
                   [0.25, 0.25, 0.25, 0.25, 0.25], "rib_tube", n=8))
    m.merge(G.quad((-0.7, 0.15, -2.3), (0.7, 0.15, -2.3), (0.6, 0.15, 1.6), (-0.6, 0.15, 1.6), "rubber", double=True))
    m.merge(G.box(0.6, 0.9, 0.5, "white_plaster", center=(0, 0.15, 0.2)))
    m.merge(G.box(0.35, 0.6, 0.45, "rubber", center=(0, 0.1, -2.5)))
    return m.transformed(t=(0, -0.15 * M, 0)), cbox(2.0, 0.8, 5.0, y0=-0.15)


@model(130, "MOTOSCAFO", "Motoscafo cabinato, 7 m")
def motoscafo():
    m, st = hull_mesh(7.0, 2.5, 1.2, "hull_motor", sheer=0.1, bow_rise=0.3)
    deck(m, st, "white_plaster")
    m.merge(G.box(1.8, 0.7, 2.2, "white_plaster", center=(0, 1.1, 0.4)))
    m.merge(G.quad((-0.85, 1.75, 1.45), (0.85, 1.75, 1.45), (0.9, 1.15, 1.6), (-0.9, 1.15, 1.6), "glass"))
    return m.transformed(t=(0, -0.45 * M, 0)), cbox(2.5, 1.6, 7.0, y0=-0.45)


@model(131, "BARCA_VELA", "Barca a vela da 8 m all'ormeggio, albero 11 m")
def vela():
    m, st = hull_mesh(8.0, 2.7, 1.3, "hull_motor", sheer=0.12, bow_rise=0.2)
    deck(m, st, "deck_wood")
    m.merge(G.box(1.6, 0.45, 2.6, "white_plaster", center=(0, 1.15, -0.3)))
    m.merge(G.cylinder(0.08, 0.06, 11.0, "galv", n=6, base=(0, 1.2, 1.0)))
    m.merge(G.tube([(0, 2.4, 1.0), (0, 2.4, -2.6)], [0.06, 0.06], "galv", n=5))
    m.merge(G.box(0.3, 0.3, 3.3, "plastic_blue", center=(0, 2.35, -0.8)))   # furled mainsail cover
    for p in ((0, 12.0, 1.0), ):
        m.merge(G.tube([p, (0, 1.4, 3.9)], [0.01, 0.01], "galv", n=3))
        m.merge(G.tube([p, (0, 1.4, -3.9)], [0.01, 0.01], "galv", n=3))
    return m.transformed(t=(0, -0.5 * M, 0)), cbox(2.7, 1.7, 8.0, y0=-0.5)


@model(132, "BARCHETTA_SPIAGGIA", "Barchetta a remi tirata in secca, 4 m (base = sabbia)")
def barchetta():
    m, st = hull_mesh(4.0, 1.5, 0.7, "hull_gozzo", sheer=0.12, bow_rise=0.15, n=6)
    deck(m, st, "deck_wood")
    m.merge(G.box(1.4, 0.06, 0.25, "deck_wood", center=(0, 0.45, 0.2)))
    return m.transformed(rz=0.12), cbox(1.5, 0.9, 4.0)


# ---------------------------------------------------------------------------------- vehicles
def car(body, length, width, height, cabin=(0.45, 0.55, 0.0), van=False):
    m = G.Mesh()
    L, W, H = length, width, height
    lower = 0.55 * H if not van else 0.45 * H
    m.merge(G.box(W, lower - 0.2, L, body, center=(0, 0.2, 0), top="glass" if False else body))
    if van:
        m.merge(G.box(W * 0.98, H - lower, L * 0.82, body, center=(0, lower, -L * 0.09)))
        m.merge(G.quad((-W * 0.45, H - 0.08, L * 0.32), (W * 0.45, H - 0.08, L * 0.32), (W * 0.47, lower + 0.05, L * 0.42),
                       (-W * 0.47, lower + 0.05, L * 0.42), "glass"))
    else:
        cl, cf, sh = cabin
        z0, z1 = -L * cl / 2 + sh, L * cl / 2 + sh
        top = H
        # cabin as a trapezoid prism: windows on all sides
        m.merge(G.quad((-W * 0.42, top, z1 - 0.25), (W * 0.42, top, z1 - 0.25), (W * 0.47, lower, z1 + 0.15), (-W * 0.47, lower, z1 + 0.15), "glass"))
        m.merge(G.quad((W * 0.42, top, z0 + 0.2), (-W * 0.42, top, z0 + 0.2), (-W * 0.47, lower, z0 - 0.1), (W * 0.47, lower, z0 - 0.1), "glass"))
        for s in (-1, 1):
            pts = [(s * W * 0.42, top, z0 + 0.2), (s * W * 0.42, top, z1 - 0.25), (s * W * 0.47, lower, z1 + 0.15), (s * W * 0.47, lower, z0 - 0.1)]
            if s < 0:
                pts = [pts[1], pts[0], pts[3], pts[2]]
            m.merge(G.quad(*pts, "glass"))
        m.merge(G.quad((-W * 0.42, top, z0 + 0.2), (W * 0.42, top, z0 + 0.2), (W * 0.42, top, z1 - 0.25), (-W * 0.42, top, z1 - 0.25), body))
    # lights strip front/back
    m.merge(G.quad((-W * 0.5, lower - 0.05, L / 2 + 0.002), (W * 0.5, lower - 0.05, L / 2 + 0.002), (W * 0.5, lower - 0.2, L / 2 + 0.002),
                   (-W * 0.5, lower - 0.2, L / 2 + 0.002), "lights", uv=[(0.25, 0), (0, 0), (0, 1), (0.25, 1)]))
    m.merge(G.quad((W * 0.5, lower - 0.05, -L / 2 - 0.002), (-W * 0.5, lower - 0.05, -L / 2 - 0.002), (-W * 0.5, lower - 0.2, -L / 2 - 0.002),
                   (W * 0.5, lower - 0.2, -L / 2 - 0.002), "lights", uv=[(1, 0), (0.75, 0), (0.75, 1), (1, 1)]))
    for x in (-W / 2 + 0.05, W / 2 - 0.05):
        for z in (-L * 0.32, L * 0.32):
            m.merge(G.wheel(0.3, 0.2, (x, 0.3, z)))
    return m


# v8: replaced by decor/veicoli.py  @model(133, "AUTO_UTILITARIA_ROSSA", "Utilitaria, 3,6 m")
def auto_a():
    return car("car_red", 3.6, 1.65, 1.5, cabin=(0.55, 0.5, -0.1)), cbox(1.65, 1.5, 3.6)


# v8: replaced by decor/veicoli.py  @model(134, "AUTO_UTILITARIA_BIANCA", "Utilitaria bianca, 3,6 m")
def auto_b():
    return car("car_white", 3.6, 1.65, 1.5, cabin=(0.55, 0.5, -0.1)), cbox(1.65, 1.5, 3.6)


# v8: replaced by decor/veicoli.py  @model(135, "AUTO_BERLINA_GRIGIA", "Berlina, 4,5 m")
def auto_c():
    return car("car_silver", 4.5, 1.8, 1.45, cabin=(0.5, 0.5, -0.15)), cbox(1.8, 1.45, 4.5)


# v8: replaced by decor/veicoli.py  @model(136, "AUTO_SUV_BLU", "SUV compatto, 4,3 m")
def auto_d():
    return car("car_blue", 4.3, 1.8, 1.65, cabin=(0.55, 0.5, -0.2)), cbox(1.8, 1.65, 4.3)


# v8: replaced by decor/veicoli.py  @model(137, "FURGONE_BIANCO", "Furgone, 5 m")
def furgone():
    return car("car_white", 5.0, 1.95, 2.3, van=True), cbox(1.95, 2.3, 5.0)


# v8: replaced by decor/veicoli.py  @model(138, "CAMPER", "Camper mansardato, 6,5 m")
def camper():
    m = G.Mesh()
    m.merge(G.box(2.2, 2.6, 4.8, "camper", center=(0, 0.45, -0.75)))
    m.merge(G.box(2.2, 0.75, 1.4, "camper", center=(0, 2.3, 1.75)))   # overcab
    m.merge(G.box(2.0, 1.05, 1.6, "car_white", center=(0, 0.45, 2.45)))
    m.merge(G.quad((-0.95, 2.25, 2.95), (0.95, 2.25, 2.95), (0.98, 1.5, 3.2), (-0.98, 1.5, 3.2), "glass"))
    for x in (-1.1, 1.1):
        for z in (-2.0, 2.4):
            m.merge(G.wheel(0.36, 0.22, (x, 0.36, z)))
    return m, cbox(2.2, 3.1, 6.5)


# v8: replaced by decor/veicoli.py  @model(139, "SCOOTER_ROSSO", "Scooter 125, 1,9 m")
def scooter_a():
    return scooter("scooter_red"), cbox(0.7, 1.1, 1.9)


# v8: replaced by decor/veicoli.py  @model(140, "SCOOTER_CREMA", "Scooter crema")
def scooter_b():
    return scooter("scooter_cream"), cbox(0.7, 1.1, 1.9)


def scooter(body):
    m = G.Mesh()
    for z in (-0.65, 0.65):
        m.merge(G.wheel(0.22, 0.1, (0, 0.22, z)))
    m.merge(G.box(0.35, 0.12, 0.8, "rubber", center=(0, 0.28, 0)))            # floorboard
    m.merge(G.ellipsoid(0.22, 0.25, 0.45, body, n=8, rings=4, center=(0, 0.6, -0.4)))
    m.merge(G.box(0.3, 0.12, 0.6, "rubber", center=(0, 0.8, -0.35)))          # saddle
    m.merge(G.quad((-0.2, 1.0, 0.55), (0.2, 1.0, 0.55), (0.18, 0.3, 0.62), (-0.18, 0.3, 0.62), body, double=True))
    m.merge(G.tube([(0, 0.3, 0.65), (0, 1.0, 0.58)], [0.04, 0.04], "iron", n=4))
    m.merge(G.tube([(-0.35, 1.05, 0.55), (0.35, 1.05, 0.55)], [0.02, 0.02], "iron", n=4))
    m.merge(G.ellipsoid(0.08, 0.06, 0.04, "lamp_glass", n=6, rings=3, center=(0, 1.0, 0.62)))
    return m


@model(141, "BICICLETTA", "Bicicletta da citta' appoggiata al cavalletto")
def bici():
    m = G.Mesh()
    for z in (-0.52, 0.52):
        ring = G.Mesh()
        n = 12
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            ring.merge(G.tube([(0, 0.34 + math.sin(a0) * 0.34, z + math.cos(a0) * 0.34),
                               (0, 0.34 + math.sin(a1) * 0.34, z + math.cos(a1) * 0.34)], [0.015, 0.015], "rubber", n=3))
        m.merge(ring)
    frame = [((0, 0.34, -0.52), (0, 0.45, 0.0)), ((0, 0.45, 0.0), (0, 0.85, -0.15)), ((0, 0.45, 0.0), (0, 0.8, 0.4)),
             ((0, 0.8, 0.4), (0, 0.34, 0.52)), ((0, 0.85, -0.15), (0, 0.34, -0.52)), ((0, 0.8, 0.4), (0, 1.0, 0.38))]
    for a, b in frame:
        m.merge(G.tube([a, b], [0.02, 0.02], "plastic_blue", n=4))
    m.merge(G.tube([(-0.28, 1.0, 0.36), (0.28, 1.0, 0.36)], [0.015, 0.015], "iron", n=4))
    m.merge(G.box(0.12, 0.05, 0.25, "rubber", center=(0, 0.9, -0.17)))
    return m.transformed(rz=0.06), None


# ---------------------------------------------------------------------------------- bars and restaurants
def chair(x, z, ry):
    c = G.Mesh()
    for dx in (-0.2, 0.2):
        for dz in (-0.2, 0.2):
            c.merge(G.box(0.03, 0.45, 0.03, "chair_alu", center=(dx, 0, dz)))
    c.merge(G.box(0.44, 0.04, 0.44, "chair_alu", center=(0, 0.45, 0)))
    c.merge(G.box(0.44, 0.4, 0.03, "chair_alu", center=(0, 0.49, -0.21)))
    return c.transformed(ry=ry, t=(x * M, 0, z * M))


def table(m, top="cloth"):
    m.merge(G.cylinder(0.04, 0.04, 0.72, "chair_alu", n=5))
    m.merge(G.box(0.8, 0.04, 0.8, top, center=(0, 0.72, 0)))


@model(142, "DEHORS_TAVOLO", "Tavolino con quattro sedie (dehors di bar e ristoranti)")
def dehors_a():
    m = G.Mesh()
    table(m)
    for k in range(4):
        a = math.pi / 2 * k
        m.merge(chair(math.sin(a) * 0.65, math.cos(a) * 0.65, a + math.pi))
    return m, cbox(0.9, 0.8, 0.9)


@model(143, "DEHORS_OMBRELLONE", "Tavolino, due sedie e ombrellone verde")
def dehors_b():
    m = G.Mesh()
    table(m)
    for k in range(2):
        a = math.pi * k
        m.merge(chair(math.sin(a) * 0.65, math.cos(a) * 0.65, a + math.pi))
    m.merge(G.cylinder(0.03, 0.03, 2.3, "chair_alu", n=4, base=(0, 0.74, 0)))
    m.merge(G.disc(1.5, "umbrella_bar", center=(0, 2.6, 0), n=8, cone=0.45))
    return m, cbox(0.9, 0.8, 0.9)


@model(144, "DEHORS_FIORIERA", "Fioriera divisoria in legno con piante, 1,6 m")
def fioriera():
    m = G.Mesh()
    m.merge(G.box(1.6, 0.6, 0.45, "wood_slats", top="soil"))
    r = np.random.default_rng(16)
    for x in (-0.5, 0.0, 0.5):
        m.merge(G.cross_cards(0.6, 0.6, "grass_card", 2, center=(x, 0.6, 0), rng=r))
    return m, cbox(1.6, 0.6, 0.45)


@model(145, "OMBRELLONE_SPIAGGIA", "Ombrellone da spiaggia a strisce blu")
def ombrellone():
    m = G.Mesh()
    m.merge(G.cylinder(0.025, 0.025, 2.3, "chair_alu", n=4))
    m.merge(G.disc(1.1, "umbrella_beach", center=(0, 2.1, 0), n=8, cone=0.35))
    return m, None


# v8 (01/11/2026): the vehicles are lofted bodies with painted projections, see decor/veicoli.py
VEICOLI = [
    (133, "AUTO_UTILITARIA_ROSSA", "panda141_rossa", "Fiat Panda prima serie (141), rossa, 3,41 m"),
    (134, "AUTO_UTILITARIA_BIANCA", "panda_bianca", "Fiat Panda terza serie, bianca, 3,65 m"),
    (135, "AUTO_BERLINA_GRIGIA", "punto_grigia", "Fiat Grande Punto 5 porte, grigio metallizzato, 4,03 m"),
    (136, "AUTO_SUV_BLU", "ypsilon_blu", "Lancia Ypsilon 5 porte, blu, 3,84 m"),
    (137, "FURGONE_BIANCO", "daily_bianco", "Iveco Daily furgone, bianco, 5,48 m"),
    (138, "CAMPER", "camper", "Camper profilato su Fiat Ducato, 6,99 m"),
    (139, "SCOOTER_ROSSO", "vespa_rossa", "Vespa Primavera 125, rossa, sul cavalletto"),
    (140, "SCOOTER_CREMA", "vespa_crema", "Vespa Primavera 125, crema, sul cavalletto"),
    (146, "AUTO_500_AZZURRA", "cinquecento_azzurra", "Fiat 500 (2007), azzurra, 3,55 m"),
    (147, "APE_PIAGGIO", "ape", "Piaggio Ape 50 con cassone, 2,46 m"),
]


def _veicolo(key):
    def fn():
        from decor import veicoli
        mesh = veicoli.model_mesh(key)
        lo, hi = mesh.bbox()
        if key.startswith("vespa"):
            return mesh, None
        return mesh, ((lo[0], 0.0, lo[2]), (hi[0], hi[1], hi[2]))
    return fn


for _sid, _name, _key, _note in VEICOLI:
    MODELS.append((_sid, _name, _veicolo(_key), _note))


def build_all():
    out = []
    for sid, name, fn, note in MODELS:
        mesh, coll = fn()
        out.append((sid, name, mesh, coll, note))
    return out
