"""Ed's house (ids 190-199: exterior) and furniture for the house interiors (ids 200-229).

Exterior from Street View (Via Gaspare Amodeo 1): cream plaster on a brown base band, street door in
patterned dark metal (art deco), garage shutter, windows with green shutters, a long balcony with
iron railing and French windows on the first floor, cornice, roof terrace with parapet and a reed
pergola. Built in world-aligned metres around casa.ANCHOR (rotation 0). A recess with the drainpipe
on the Via Amodeo side is where Lara climbs down (the wall of the recess is the real climbable face).
"""
import math

import numpy as np

import casa as C
from decor import geom as G
from decor.geom import M
from decor.models import model
from decor.santuario_models import UP, V, cornice, fface, obox, overlay, plan_normal, rectf, wall

H = C.HEIGHT_M          # 9.5 m street -> roof
FLOORS = (0.0, 3.3, 6.4)


def poly_m():
    return [C.to_m(*p) for p in C.POLY]


def along(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def facade(m, a, b, n2, items, poly):
    """Plain cream wall with base band, cornice, parapet, plus `items` = [(t, y0, w, h, region)] overlays."""
    wall(m, a, b, -1.0, 0.9, n2, "ca_zoccolo", (2.0, 1.9))
    wall(m, a, b, 0.9, H, n2, "ca_intonaco", (2.0, 2.0))
    for t, y0, w, h, reg in items:
        overlay(m, along(a, b, t), n2, y0, w, h, reg, off=0.03)
    for y in (FLOORS[1] - 0.15, FLOORS[2] - 0.15):
        cornice(m, a, b, y, n2, h=0.15, d=0.08, region="tn_cornice", ext=0.0)
    cornice(m, a, b, H - 0.35, n2, h=0.35, d=0.3, region="tn_cornice", ext=0.0)
    wall(m, a, b, H, H + 1.0, n2, "ca_intonaco", (2.0, 1.0), double=True)
    cornice(m, a, b, H + 1.0, n2, h=0.12, d=0.12, region="tn_marmo", ext=0.0)


@model(190, "CASA_ESTERNO", "Casa di Via Gaspare Amodeo 1: facciate, balcone, portone liberty, terrazza con pergolato")
def esterno():
    m = G.Mesh()
    P = poly_m()
    n = len(P)
    cx, cz, gap = C.climb_spot()
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        n2 = plan_normal(a, b, P)
        L = math.dist(a, b)
        if i in (0, 1):           # attached to the neighbours: only the parapet shows
            wall(m, a, b, H, H + 1.0, n2, "ca_intonaco", (2.0, 1.0), double=True)
            continue
        items = []
        if (i, (i + 1) % n) == C.STREET_EDGE:
            # Via Amodeo: garage, street door, ground windows; balcony with three French windows; windows
            items += [(0.30, 0.0, 2.4, 2.4, "ca_saracinesca"), (0.55, 0.0, 1.6, 3.2, "ca_portone"),
                      (0.78, 0.9, 1.6, 2.0, "ca_finestra"), (0.92, 0.9, 1.6, 2.0, "ca_finestra")]
            for t in (0.3, 0.55, 0.8):
                items.append((t, FLOORS[1] + 0.1, 2.0, 3.0, "ca_portafinestra"))
                items.append((t, FLOORS[2] + 0.5, 1.6, 2.0, "ca_finestra_luce" if t == 0.8 else "ca_finestra"))
        else:
            k = max(1, int(L // 4.0))
            for j in range(k):
                t = (j + 0.5) / k
                for f, y in enumerate(FLOORS):
                    items.append((t, y + 0.9, 1.6, 2.0, "ca_finestra"))
        # the recess with the drainpipe: cut the street facade there
        if (i, (i + 1) % n) == C.STREET_EDGE:
            p0 = C.to_m(cx, cz + 1)
            p1 = C.to_m(cx + 1, cz + 1)
            ta = (np.dot(np.subtract(p0, a), np.subtract(b, a))) / L ** 2
            tb = (np.dot(np.subtract(p1, a), np.subtract(b, a))) / L ** 2
            ta, tb = max(0.0, ta), min(1.0, tb)
            items = [it for it in items if not (ta - 0.08 < it[0] < tb + 0.08)]
            facade(m, a, along(a, b, ta), n2, [((it[0]) / ta, *it[1:]) for it in items if it[0] < ta], P)
            facade(m, along(a, b, tb), b, n2, [((it[0] - tb) / (1 - tb), *it[1:]) for it in items if it[0] > tb], P)
            qa, qb = along(a, b, ta), along(a, b, tb)
            # back of the recess on the block face (z = cz + 1), climbable, with the drainpipe
            wall(m, p0, p1, -1.0, H, (0.0, -1.0), "ca_grondaia", (2.0, 2.0), off=0.02)
            wall(m, (p0[0], qa[1]), p0, -1.0, H, (1.0, 0.0), "ca_intonaco", (max(0.3, abs(p0[1] - qa[1])), 2.0))
            wall(m, (p1[0], qb[1]), p1, -1.0, H, (-1.0, 0.0), "ca_intonaco", (max(0.3, abs(p1[1] - qb[1])), 2.0))
            # close the gaps between the recess sides and the oblique facade
            for q, px in ((qa, p0[0]), (qb, p1[0])):
                if abs(q[0] - px) > 0.02:
                    wall(m, q, (px, q[1]), -1.0, H, n2, "ca_intonaco", (0.5, 2.0))
            for y in (H - 0.35,):
                cornice(m, p0, p1, y, (0.0, -1.0), h=0.35, d=0.25, region="tn_cornice", ext=0.0)
            wall(m, p0, p1, H, H + 1.0, (0.0, -1.0), "ca_intonaco", (2.0, 1.0), double=True)
            # long balcony on both sides of the recess
            for s0, s1 in ((0.04, ta - 0.02), (tb + 0.02, 0.97)):
                if s1 - s0 < 0.05:
                    continue
                c0, c1 = along(a, b, s0), along(a, b, s1)
                mid = along(a, b, (s0 + s1) / 2)
                Ls = math.dist(c0, c1)
                obox(m, mid, n2, Ls, 1.0, FLOORS[1] - 0.2, FLOORS[1], "tn_marmo", tile=(2.0, 0.2))
                front0 = (c0[0] + n2[0] * 0.95, c0[1] + n2[1] * 0.95)
                front1 = (c1[0] + n2[0] * 0.95, c1[1] + n2[1] * 0.95)
                wall(m, front0, front1, FLOORS[1], FLOORS[1] + 1.0, n2, "tn_ringhiera", (2.0, 1.0), double=True, blend=1)
                for c in (c0, c1):
                    q0 = c
                    q1 = (c[0] + n2[0] * 0.95, c[1] + n2[1] * 0.95)
                    fface(m, [V(q0[0], FLOORS[1], q0[1]), V(q1[0], FLOORS[1], q1[1]), V(q1[0], FLOORS[1] + 1.0, q1[1]),
                              V(q0[0], FLOORS[1] + 1.0, q0[1])], "tn_ringhiera", V(*np.cross([0, 1, 0], [q1[0] - q0[0], 0, q1[1] - q0[1]])),
                          double=True, blend=1)
            continue
        facade(m, a, b, n2, items, P)
    # roof terrace: reed pergola at the west corner, terracotta floor tiles are the room's
    w = P[3]
    inward = np.subtract(np.mean(P, axis=0), w)
    inward = inward / np.linalg.norm(inward)
    e1 = np.subtract(P[4], P[3]) / math.dist(P[4], P[3])
    e2 = np.subtract(P[2], P[3]) / math.dist(P[2], P[3])
    o = np.add(w, inward * 1.2)
    corners = [o, o + e1 * 4.5, o + e1 * 4.5 + e2 * 3.6, o + e2 * 3.6]
    for c in corners:
        m.merge(G.box(0.14, 2.5, 0.14, "ca_pergola", center=(c[0], H, c[1])))
    for i in range(4):
        c0, c1 = corners[i], corners[(i + 1) % 4]
        cm = (np.array(c0) + np.array(c1)) / 2
        d = np.subtract(c1, c0)
        Lb = float(np.linalg.norm(d))
        beam = G.box(Lb, 0.14, 0.12, "ca_pergola").transformed(ry=-math.atan2(d[1], d[0]))
        m.merge(beam.transformed(t=(cm[0] * M, (H + 2.5) * M, cm[1] * M)))
    q = [V(c[0], H + 2.66, c[1]) for c in corners]
    fface(m, q, "ca_canne", UP, double=True, blend=1)
    return m, None


# ------------------------------------------------------------------------------- furniture
def box(m, w, h, d, reg, x=0.0, y=0.0, z=0.0, top=None):
    m.merge(G.box(w, h, d, reg, center=(x, y, z), top=top))


def cb(w, h, d, x=0.0, z=0.0):
    return ((x - w / 2) * M, 0.0, (z - d / 2) * M), ((x + w / 2) * M, h * M, (z + d / 2) * M)


def furniture(sid, name, note, coll=True):
    def deco(fn):
        def build():
            m, c = fn()
            return m, (c if coll else None)
        model(sid, name, note)(build)
        return fn
    return deco


@furniture(200, "CASA_LETTO", "Letto matrimoniale con testiera in noce")
def letto():
    m = G.Mesh()
    box(m, 2.0, 0.35, 1.7, "ca_noce", y=0.05)
    box(m, 1.96, 0.18, 1.66, "ca_lenzuolo", y=0.4, top="ca_coperta")
    box(m, 0.08, 1.0, 1.7, "ca_noce", x=-1.0)
    for z in (-0.4, 0.4):
        box(m, 0.4, 0.12, 0.6, "ca_lenzuolo", x=-0.72, y=0.58, z=z)
    return m, cb(2.08, 0.6, 1.7)


@furniture(201, "CASA_COMODINO", "Comodino con lampada")
def comodino():
    m = G.Mesh()
    box(m, 0.45, 0.55, 0.45, "ca_noce")
    m.merge(G.cylinder(0.06, 0.06, 0.3, "ca_ceramica", n=6, base=(0, 0.55, 0)))
    m.merge(G.cylinder(0.18, 0.1, 0.2, "ca_tenda", n=8, base=(0, 0.82, 0)))
    return m, cb(0.45, 0.55, 0.45)


@furniture(202, "CASA_ARMADIO", "Armadio a due ante")
def armadio():
    m = G.Mesh()
    box(m, 0.6, 2.2, 2.0, "ca_noce")
    rectf(m, V(0.31, 0.1, 0.95), V(0, 0, -1), UP, 1.9, 2.0, "ca_porta", V(1, 0, 0), tile=(0.95, 2.0))
    return m, cb(0.6, 2.2, 2.0)


@furniture(203, "CASA_LIBRERIA", "Libreria piena di libri")
def libreria():
    m = G.Mesh()
    box(m, 0.4, 2.1, 2.0, "ca_noce")
    rectf(m, V(0.21, 0.1, 0.95), V(0, 0, -1), UP, 1.9, 1.9, "ca_libri", V(1, 0, 0), tile=(0.95, 0.95))
    return m, cb(0.4, 2.1, 2.0)


@furniture(204, "CASA_SCRIVANIA", "Scrivania messa a soqquadro, carte sparse")
def scrivania():
    m = G.Mesh()
    box(m, 0.7, 0.04, 1.5, "ca_rovere", y=0.74)
    for x, z in ((-0.3, -0.7), (0.3, -0.7), (-0.3, 0.7), (0.3, 0.7)):
        box(m, 0.05, 0.74, 0.05, "ca_rovere", x=x, z=z)
    box(m, 0.6, 0.6, 0.45, "ca_rovere", y=0.1, z=0.5)
    fface(m, [V(-0.3, 0.79, -0.6), V(0.3, 0.79, -0.6), V(0.3, 0.79, 0.4), V(-0.3, 0.79, 0.4)], "ca_carte", UP, blend=1)
    return m, cb(0.7, 0.8, 1.5)


@furniture(205, "CASA_SEDIA", "Sedia impagliata", coll=False)
def sedia():
    m = G.Mesh()
    box(m, 0.42, 0.05, 0.42, "ca_sedia", y=0.45)
    for x, z in ((-0.18, -0.18), (0.18, -0.18), (-0.18, 0.18), (0.18, 0.18)):
        box(m, 0.04, 0.45, 0.04, "ca_noce", x=x, z=z)
    box(m, 0.04, 0.5, 0.42, "ca_noce", x=-0.19, y=0.5)
    return m, None


@furniture(206, "CASA_SEDIA_ROVESCIATA", "Sedia rovesciata dai ladri", coll=False)
def sedia_rovesciata():
    m, _ = sedia()
    return m.transformed(rz=math.pi / 2, t=(0.48 * M, 0.21 * M, 0)), None


@furniture(207, "CASA_DIVANO", "Divano a tre posti")
def divano():
    m = G.Mesh()
    box(m, 0.9, 0.42, 2.2, "ca_divano")
    box(m, 0.25, 0.45, 2.2, "ca_divano", x=-0.33, y=0.42)
    for z in (-1.0, 1.0):
        box(m, 0.9, 0.25, 0.2, "ca_divano", y=0.42, z=z)
    return m, cb(0.9, 0.85, 2.2)


@furniture(208, "CASA_TAVOLINO", "Tavolino basso su tappeto", coll=False)
def tavolino():
    m = G.Mesh()
    fface(m, [V(-1.2, 0.01, -0.9), V(1.2, 0.01, -0.9), V(1.2, 0.01, 0.9), V(-1.2, 0.01, 0.9)], "ca_tappeto", UP)
    box(m, 0.6, 0.04, 1.1, "ca_rovere", y=0.4)
    for x, z in ((-0.25, -0.5), (0.25, -0.5), (-0.25, 0.5), (0.25, 0.5)):
        box(m, 0.04, 0.4, 0.04, "ca_rovere", x=x, z=z)
    return m, None


@furniture(209, "CASA_TAVOLO", "Tavolo da pranzo con quattro sedie")
def tavolo():
    m = G.Mesh()
    box(m, 0.9, 0.05, 1.6, "ca_rovere", y=0.75)
    for x, z in ((-0.4, -0.75), (0.4, -0.75), (-0.4, 0.75), (0.4, 0.75)):
        box(m, 0.06, 0.75, 0.06, "ca_rovere", x=x, z=z)
    s, _ = sedia()
    for x, z, a in ((-0.75, -0.4, 0), (-0.75, 0.4, 0), (0.75, -0.4, math.pi), (0.75, 0.4, math.pi)):
        m.merge(s.transformed(ry=a, t=(x * M, 0, z * M)))
    return m, cb(0.9, 0.8, 1.6)


@furniture(210, "CASA_CUCINA", "Cucina componibile: mobili, piano cottura, lavello, piastrelle")
def cucina():
    m = G.Mesh()
    box(m, 0.6, 0.86, 3.0, "ca_mobile", top="ca_fornelli")
    rectf(m, V(0.31, 0.05, 1.5), V(0, 0, -1), UP, 3.0, 0.8, "ca_mobile", V(1, 0, 0), tile=(1.2, 0.8))
    rectf(m, V(-0.29, 0.9, 1.5), V(0, 0, -1), UP, 3.0, 0.7, "ca_piastrelle", V(1, 0, 0), tile=(0.75, 0.7))
    box(m, 0.35, 0.7, 3.0, "ca_mobile", x=-0.12, y=1.6)
    return m, cb(0.6, 0.9, 3.0)


@furniture(211, "CASA_FRIGO", "Frigorifero")
def frigo():
    m = G.Mesh()
    box(m, 0.65, 1.85, 0.65, "ca_ceramica")
    rectf(m, V(0.33, 0.02, 0.32), V(0, 0, -1), UP, 0.64, 1.8, "ca_frigo", V(1, 0, 0), tile=None)
    return m, cb(0.65, 1.85, 0.65)


@furniture(212, "CASA_BAGNO", "Bagno: vasca, lavabo, water")
def bagno():
    m = G.Mesh()
    box(m, 0.75, 0.55, 1.7, "ca_ceramica", z=0.5)
    m.merge(G.cylinder(0.2, 0.18, 0.42, "ca_ceramica", n=8, base=(0, 0, -0.75)))
    box(m, 0.2, 0.4, 0.4, "ca_ceramica", x=-0.25, y=0.4, z=-0.75)
    m.merge(G.cylinder(0.08, 0.08, 0.8, "ca_ceramica", n=6, base=(-0.15, 0, -1.4)))
    box(m, 0.45, 0.12, 0.55, "ca_ceramica", x=-0.1, y=0.8, z=-1.4)
    return m, cb(0.75, 0.6, 2.4, z=-0.2)


@furniture(213, "CASA_MOBILE_TV", "Mobile basso con televisore")
def mobile_tv():
    m = G.Mesh()
    box(m, 0.45, 0.5, 1.8, "ca_noce")
    box(m, 0.08, 0.62, 1.1, "ca_tv", y=0.55)
    rectf(m, V(0.05, 0.6, 0.53), V(0, 0, -1), UP, 1.06, 0.56, "ca_tv", V(1, 0, 0), tile=None)
    return m, cb(0.45, 0.5, 1.8)


@furniture(214, "CASA_QUADRO", "Quadro: la rupe di Tindari al tramonto", coll=False)
def quadro():
    m = G.Mesh()
    rectf(m, V(0.02, 1.3, 0.6), V(0, 0, -1), UP, 1.2, 0.9, "ca_quadro", V(1, 0, 0), tile=None)
    return m, None


@furniture(215, "CASA_FINESTRA", "Finestra vista da dentro, di notte, con tende", coll=False)
def finestra():
    m = G.Mesh()
    rectf(m, V(0.02, 0.9, 0.65), V(0, 0, -1), UP, 1.3, 1.7, "ca_finestra_notte", V(1, 0, 0), tile=None)
    for z in (-0.95, 0.65):
        rectf(m, V(0.06, 0.6, z + 0.3), V(0, 0, -1), UP, 0.3, 2.1, "ca_tenda", V(1, 0, 0), tile=None)
    box(m, 0.2, 0.06, 1.5, "tn_marmo", x=0.05, y=0.84)
    return m, None


def porta_vano(top):
    """The doorway is a whole sector (2 x 2 m) between two wall sectors: the jambs sit on the walls'
    faces (local z = +-1), the passage runs along local x. Above 2.3 m the opening is closed with
    plaster up to the ceiling, so the frame never floats in the middle of the hole."""
    m = G.Mesh()
    for z, nz in ((-0.99, 1.0), (0.99, -1.0)):
        # jamb lining on the wall face, the whole depth of the passage
        rectf(m, V(-1.0, 0.0, z), V(1, 0, 0), UP, 2.0, 2.3, "ca_noce", V(0, 0, nz), tile=(2.0, 2.3))
        box(m, 0.12, 2.3, 0.1, "ca_noce", x=-1.0, z=z + 0.04 * nz)
        box(m, 0.12, 2.3, 0.1, "ca_noce", x=1.0, z=z + 0.04 * nz)
    # lintel: plaster from 2.3 m up to the ceiling, wood soffit
    box(m, 2.0, top - 2.3, 1.98, "ca_intonaco", y=2.3)
    fface(m, [V(-1.0, 2.3, -0.99), V(1.0, 2.3, -0.99), V(1.0, 2.3, 0.99), V(-1.0, 2.3, 0.99)], "ca_noce", -UP)
    for x in (-1.0, 1.0):
        box(m, 0.1, 0.12, 2.0, "ca_noce", x=x, y=2.3)
    # door leaf open against the jamb
    leaf = G.Mesh()
    rectf(leaf, V(0.0, 0.0, 0.0), V(1, 0, 0), UP, 0.95, 2.25, "ca_porta", V(0, 0, 1), tile=None, double=True)
    m.merge(leaf.transformed(t=(-0.5 * M, 0, 0.93 * M)))
    return m, None


@furniture(216, "CASA_PORTA", "Vano porta (stanze alte 3 m): stipiti a filo dei muri, architrave fino al soffitto, anta aperta", coll=False)
def porta():
    return porta_vano(2.98)


@furniture(221, "CASA_PORTA_ALTA", "Vano porta (stanze alte 3,5 m)", coll=False)
def porta_alta():
    return porta_vano(3.48)


@furniture(217, "CASA_PORTONE_INT", "Portone di casa visto da dentro, sbarrato", coll=False)
def portone_int():
    m = G.Mesh()
    rectf(m, V(0.02, 0.0, 0.8), V(0, 0, -1), UP, 1.6, 3.0, "ca_portone", V(1, 0, 0), tile=None)
    return m, None


@furniture(218, "CASA_SCAFFALE", "Scaffale della dispensa con barattoli")
def scaffale():
    m = G.Mesh()
    box(m, 0.4, 2.0, 1.8, "ca_rovere")
    rectf(m, V(0.21, 0.1, 0.85), V(0, 0, -1), UP, 1.7, 1.8, "ca_libri", V(1, 0, 0), tile=(0.85, 0.9))
    return m, cb(0.4, 2.0, 1.8)


@furniture(219, "CASA_CORRIMANO", "Ringhiera della scala (2 m)")
def corrimano():
    m = G.Mesh()
    rectf(m, V(-1.0, 0.0, 0.0), V(1, 0, 0), UP, 2.0, 1.0, "tn_ringhiera", V(0, 0, -1), tile=None, double=True, blend=1)
    box(m, 2.0, 0.05, 0.07, "ca_noce", y=1.0)
    return m, ((-1.0 * M, 0, -0.08 * M), (1.0 * M, 1.05 * M, 0.08 * M))


@furniture(220, "CASA_GRADINI", "Gradini in marmo sopra la rampa (6 m, 3 m di salita)", coll=False)
def gradini():
    """Visual steps along +x over a 6 m ramp rising 3 m, 2 m wide (the ramp under them is the room floor)."""
    m = G.Mesh()
    n = 18
    run, rise = 6.0 / n, 3.0 / n
    for i in range(n):
        x0 = -3.0 + i * run
        y0 = i * rise
        fface(m, [V(x0, y0 + rise, -1.0), V(x0 + run, y0 + rise, -1.0), V(x0 + run, y0 + rise, 1.0), V(x0, y0 + rise, 1.0)],
              "tn_marmo", UP, [(0, 0), (1, 0), (1, 0.15), (0, 0.15)])
        fface(m, [V(x0, y0, -1.0), V(x0, y0, 1.0), V(x0, y0 + rise, 1.0), V(x0, y0 + rise, -1.0)], "tn_marmo",
              V(-1, 0, 0), [(0, 0.2), (1, 0.2), (1, 0.3), (0, 0.3)])
    return m, None
