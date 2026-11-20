"""Interior of the Basilica of Tindari (ids 170-189), from Ed's photos of the nave, the atrium and the dome.

Interior frame (metres): x east from the inner face of the main door, z north from the axis, y up from
the nave floor. The room itself (santuario_interno.py) gives the volumes and the collision: nave
10 m wide with a 15 m vault, aisles 6 m wide and 9 m high, crossing under the dome, presbytery raised
by 0.5 m, a gilded side chapel in the south transept arm. These statics are the skins:
star/octagon marble in the central aisle, diamond marble in the aisles, red marble dado, mosaic panels,
stained glass, coffered aisle ceilings, painted barrel vault with gilded ribs, drum with stained glass
(three of them: moon, star, sun) and the inscription AVE MARIA GRATIA PLENA DOMINUS TECUM, frescoed
dome, gilded apse wall with the icon of the Madonna Nera, pink marble columns with gilded capitals,
wooden pews.
"""
import math

import numpy as np

from decor import geom as G
from decor.geom import M
from decor.models import model
from decor.santuario_models import UP, V, annulus, cornice, fface, frame, obox, overlay, rectf, wall

ANCHORS = {}
SPOTS = {}     # name -> list of (x, z, rot) for repeated pieces

L = 66.0            # inner length
HW = 11.0           # inner half width
NAVE = 5.0          # half width of the central nave
AISLE_H = 9.0
VAULT_SPRING, VAULT_TOP = 12.0, 15.0
CROSS = (40.0, 52.0)          # crossing along x
CROSS_HZ = 7.0                # crossing half width (high ceiling)
DOME_C = (46.0, 0.0)
DOME_R = 6.0
DRUM = (17.0, 22.0)
DOME_TOP = 29.0
PRESB = 54.0                  # presbytery starts here, raised
PRESB_H = 0.5
CHAPEL = (40.0, 52.0, -15.0)  # south chapel: x0, x1, z of its south wall
COLS = [4.0 + 5.0 * i for i in range(8)] + [56.0, 61.0]


def floor_y(x):
    return PRESB_H if x >= PRESB else 0.0


def piece(sid, name, anchor, note):
    def deco(fn):
        ANCHORS[name] = anchor

        def build():
            return fn().transformed(t=(-anchor[0] * M, 0, -anchor[1] * M)), None
        model(sid, name, note)(build)
        return fn
    return deco


def hrect(m, x0, x1, z0, z1, y, region, tile=2.0, down=False):
    nx, nz = max(1, int(round((x1 - x0) / tile))), max(1, int(round((z1 - z0) / tile)))
    for i in range(nx):
        for j in range(nz):
            a0, a1 = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
            b0, b1 = z0 + (z1 - z0) * j / nz, z0 + (z1 - z0) * (j + 1) / nz
            fface(m, [V(a0, y, b0), V(a1, y, b0), V(a1, y, b1), V(a0, y, b1)], region, -UP if down else UP)


def gpanel(m, o, r, up, w, h, name, nx, ny, n):
    """A big picture cut into nx x ny regions name_i_j (santuario_arte.grid), i from the left, j from the top."""
    for i in range(nx):
        for j in range(ny):
            bl = o + r * (w * i / nx) + up * (h * (ny - 1 - j) / ny)
            rectf(m, bl, r, up, w / nx, h / ny, "%s_%d_%d" % (name, i, j), n, None)


def goverlay(m, c, n2, y0, w, h, name, nx, ny, off=0.03):
    n, r = frame(n2)
    gpanel(m, V(c[0], y0, c[1]) - r * (w / 2) + n * off, r, UP, w, h, name, nx, ny, n)



# ------------------------------------------------------------------------------------ floors
@piece(170, "INTERNO_PAVIMENTO", (33.0, 0.0), "Pavimenti in marmo: stelle nella navata centrale, rombi nelle navate laterali")
def pavimento():
    m = G.Mesh()
    e = 0.05          # 2.5 cm over the room floor (1 cm flickered from afar)
    for x0, x1 in ((0.0, PRESB),):
        hrect(m, x0, x1, -NAVE, NAVE, e, "in_stelle")
        hrect(m, x0, x1, NAVE, HW, e, "in_rombi")
        hrect(m, x0, x1, -HW, -NAVE, e, "in_rombi")
    hrect(m, PRESB, L, -HW, HW, PRESB_H + e, "in_marmo_rosa")
    hrect(m, CHAPEL[0], CHAPEL[1], CHAPEL[2], -HW, e, "in_marmo_rosso")
    # step of the presbytery
    wall(m, (PRESB, HW), (PRESB, -HW), 0.0, PRESB_H, (-1.0, 0.0), "in_marmo_rosso", (2.0, PRESB_H))
    return m


# ------------------------------------------------------------------------------------ walls
def bay_list(x0, x1, w=6.0):
    k = max(1, int(round((x1 - x0) / w)))
    return [x0 + (x1 - x0) * (i + 0.5) / k for i in range(k)], (x1 - x0) / k


@piece(171, "INTERNO_PARETI", (33.0, 0.0), "Pareti: zoccolo in marmo rosso, mosaici dei Misteri, vetrate, cleristorio")
def pareti():
    m = G.Mesh()
    off = 0.10          # 5 cm in front of the room's own wall, the panels 5 cm more: 1 cm flickered from afar (20 Nov)
    for side in (-1, 1):
        zw = side * HW
        n2 = (0.0, -float(side))           # facing the inside
        segs = [(0.0, L)] if side > 0 else [(0.0, CHAPEL[0]), (CHAPEL[1], L)]
        for x0, x1 in segs:
            y0 = 0.0
            wall(m, (x0, zw), (x1, zw), y0, 1.2, n2, "in_marmo_rosso", (2.0, 1.2), off=off)
            wall(m, (x0, zw), (x1, zw), 1.2, AISLE_H, n2, "in_parete", (2.0, 2.0), off=off)
            cornice(m, (x0, zw), (x1, zw), 1.2, n2, h=0.15, d=0.08, region="in_oro", ext=0.0)
            xs, bw = bay_list(x0, x1)
            for i, xc in enumerate(xs):
                if xc > PRESB - 1:
                    continue
                goverlay(m, (xc, zw), n2, 2.2, 3.6, 1.8, "in_mosaico%d" % ((i + (side > 0)) % 4), 2, 1, off=off * 2)
                goverlay(m, (xc, zw), n2, 4.8, 1.5, 3.0, "in_vetrata%d" % (i % 5), 1, 2, off=off * 2)
            cornice(m, (x0, zw), (x1, zw), AISLE_H - 0.5, n2, h=0.5, d=0.3, region="tn_cornice", ext=0.0)
    # aisle ceilings: coffers
    for x0, x1 in ((0.0, CROSS[0]), (CROSS[1], L)):
        hrect(m, x0, x1, NAVE, HW, AISLE_H - 0.10, "in_cassettoni", down=True)
        hrect(m, x0, x1, -HW, -NAVE, AISLE_H - 0.10, "in_cassettoni", down=True)
    for x0, x1, zs in ((CROSS[0], CROSS[1], (CROSS_HZ, HW)), (CROSS[0], CROSS[1], (-HW, -CROSS_HZ))):
        hrect(m, x0, x1, zs[0], zs[1], AISLE_H - 0.10, "in_cassettoni", down=True)
    # clerestory (the walls of the nave above the arcade), both sides, outside the crossing
    for side in (-1, 1):
        zw = side * NAVE
        n2 = (0.0, -float(side))
        for x0, x1 in ((0.0, CROSS[0]), (CROSS[1], L)):
            wall(m, (x0, zw), (x1, zw), AISLE_H, VAULT_TOP, n2, "in_parete", (2.0, 2.0), off=off)
            for xc in bay_list(x0, x1, 5.0)[0]:
                goverlay(m, (xc, zw), n2, 9.4, 1.3, 2.6, "in_vetrata%d" % (int(xc) % 5), 1, 2, off=off * 2)
            obox(m, ((x0 + x1) / 2, zw), n2, x1 - x0, 0.5, AISLE_H - 0.8, AISLE_H, "in_oro", tile=(2.0, 0.8))
    # entrance wall (inside of the facade) and the gilded apse wall
    wall(m, (0.0, -HW), (0.0, HW), 0.0, AISLE_H, (1.0, 0.0), "in_parete", off=off)
    wall(m, (0.0, -NAVE), (0.0, NAVE), AISLE_H, VAULT_TOP, (1.0, 0.0), "in_parete", off=off)
    overlay(m, (0.0, 0.0), (1.0, 0.0), 0.0, 3.2, 6.4, "tn_porta", off=off * 2)
    for zc in (-2.2, 0.0, 2.2):
        goverlay(m, (0.0, zc), (1.0, 0.0), 9.2, 1.8, 3.6, "in_vetrata%d" % (int(zc + 3) % 5), 1, 2, off=off * 2)
    for zc in (-8.0, 8.0):
        overlay(m, (0.0, zc), (1.0, 0.0), 0.0, 1.8, 3.6, "tn_porta", off=off * 2)
    wall(m, (L, HW), (L, -HW), 0.0, AISLE_H, (-1.0, 0.0), "in_parete", off=off)
    wall(m, (L, NAVE), (L, -NAVE), PRESB_H, VAULT_TOP, (-1.0, 0.0), "in_giallo", off=off * 2)
    goverlay(m, (L, 0.0), (-1.0, 0.0), 3.2, 2.4, 4.8, "in_icona", 1, 2, off=0.30)
    obox(m, (L, 0.0), (-1.0, 0.0), 3.0, 0.1, 2.8, 8.4, "in_oro")
    goverlay(m, (L, 0.0), (-1.0, 0.0), 9.2, 7.2, 3.6, "in_mosaico1", 2, 1, off=0.26)
    for zc in (-3.6, 3.6):
        goverlay(m, (L, zc), (-1.0, 0.0), 3.0, 1.4, 2.8, "in_vetrata%d" % (2 if zc < 0 else 4), 1, 2, off=0.26)
    return m


# ------------------------------------------------------------------------------------ vault
@piece(172, "INTERNO_VOLTA", (33.0, 0.0), "Volta a botte dipinta: cassettoni, scene affrescate, costoloni dorati")
def volta():
    """The barrel vault as it is: four frescoed lengths (three in the nave, one over the presbytery), each one
    photograph laid over the whole width of the vault, a gilded rib between one length and the next."""
    m = G.Mesh()
    n_arc = 8
    arc = [(-NAVE * math.cos(math.pi * k / n_arc), VAULT_SPRING + (VAULT_TOP - VAULT_SPRING) * math.sin(math.pi * k / n_arc))
           for k in range(n_arc + 1)]
    third = CROSS[0] / 3
    panels = [(0.0, third, "a"), (third, 2 * third, "b"), (2 * third, CROSS[0], "c"), (CROSS[1], L, "a")]
    for x0, x1, kind in panels:
        for j in range(3):                                   # j = 0 is the end towards the altar
            xa, xb = x1 - (x1 - x0) * (j + 1) / 3, x1 - (x1 - x0) * j / 3
            for k in range(n_arc):
                (za, ya), (zb, yb) = arc[k], arc[k + 1]
                nrm = V(0, VAULT_SPRING - (ya + yb) / 2 - 0.01, -(za + zb) / 2)
                fface(m, [V(xa, ya, za), V(xb, ya, za), V(xb, yb, zb), V(xa, yb, zb)], "in_vp%s_%d_%d" % (kind, k, j), nrm,
                      [(1, 1), (1, 0), (0, 0), (0, 1)])
        for xr in ((x1,) if x1 < L else ()):                 # gilded transverse rib at the end of the length
            for k in range(n_arc):
                (za, ya), (zb, yb) = arc[k], arc[k + 1]
                q = [V(xr - 0.15, ya - 0.25, za * 0.98), V(xr + 0.15, ya - 0.25, za * 0.98),
                     V(xr + 0.15, yb - 0.25, zb * 0.98), V(xr - 0.15, yb - 0.25, zb * 0.98)]
                fface(m, q, "in_oro", V(0, VAULT_SPRING - (ya + yb) / 2, -(za + zb) / 2))
    # lunettes closing the space above the vault where it opens on the crossing
    for xe, nx in ((CROSS[0] - 0.01, -1.0), (CROSS[1] + 0.01, 1.0)):
        for k in range(n_arc):
            (za, ya), (zb, yb) = arc[k], arc[k + 1]
            fface(m, [V(xe, ya, za), V(xe, yb, zb), V(xe, VAULT_TOP + 0.6, zb), V(xe, VAULT_TOP + 0.6, za)], "in_parete",
                  V(-nx, 0, 0), [(0, 1), (1, 1), (1, 0), (0, 0)])
    return m


# ------------------------------------------------------------------------------------ crossing and dome
@piece(173, "INTERNO_CUPOLA", DOME_C, "Incrocio: pennacchi, tamburo con vetrate (luna, stella, sole), scritta AVE MARIA, cupola affrescata")
def cupola():
    m = G.Mesh()
    cx, cz = DOME_C
    hx, hz = (CROSS[1] - CROSS[0]) / 2, CROSS_HZ
    # crossing walls between the aisle ceiling / vault and the drum (inside faces)
    for (a, b, n2, y0) in (((CROSS[0], -hz), (CROSS[0], hz), (1.0, 0.0), VAULT_TOP),
                           ((CROSS[1], hz), (CROSS[1], -hz), (-1.0, 0.0), VAULT_TOP),
                           ((CROSS[0], hz), (CROSS[1], hz), (0.0, -1.0), AISLE_H),
                           ((CROSS[1], -hz), (CROSS[0], -hz), (0.0, 1.0), AISLE_H)):
        wall(m, a, b, y0, DRUM[0], n2, "in_parete", (2.0, 2.0), off=0.10)
        cornice(m, a, b, DRUM[0] - 0.6, n2, h=0.6, d=0.3, region="in_oro", ext=0.0)
    for x in CROSS:   # the arches open towards the nave: gilded band under the vault top
        n2 = (1.0, 0.0) if x == CROSS[0] else (-1.0, 0.0)
        obox(m, (x, 0.0), n2, 2 * NAVE, 0.4, VAULT_TOP - 0.6, VAULT_TOP, "in_oro", tile=(2.0, 0.6))
    # flat ring at the drum base: from the crossing square to the circle (pendentives)
    n = 16
    sq = [(cx - hx, cz - hz), (cx + hx, cz - hz), (cx + hx, cz + hz), (cx - hx, cz + hz)]
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = (cx + DOME_R * math.cos(a0), cz + DOME_R * math.sin(a0))
        p1 = (cx + DOME_R * math.cos(a1), cz + DOME_R * math.sin(a1))

        def to_sq(a):
            c, s = math.cos(a), math.sin(a)
            t = min(hx / abs(c) if abs(c) > 1e-6 else 1e9, hz / abs(s) if abs(s) > 1e-6 else 1e9)
            return (cx + t * c, cz + t * s)
        q0, q1 = to_sq(a0), to_sq(a1)
        fface(m, [V(p0[0], DRUM[0], p0[1]), V(p1[0], DRUM[0], p1[1]), V(q1[0], DRUM[0], q1[1]), V(q0[0], DRUM[0], q0[1])],
              "in_volta", -UP)
    del sq
    # drum: 16 stained-glass windows facing inwards, three of them the moon, the star and the sun
    special = {5: "in_vetrata_luna", 6: "in_vetrata_stella", 7: "in_vetrata_sole"}
    pts = [(cx + DOME_R * math.cos(2 * math.pi * k / n), cz + DOME_R * math.sin(2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        am = 2 * math.pi * (k + 0.5) / n
        n2 = (-math.cos(am), -math.sin(am))
        reg, hh = special.get(k, "in_vetrata%d" % (k % 5)), (DRUM[1] - DRUM[0]) / 2
        wall(m, a, b, DRUM[0], DRUM[0] + hh, n2, reg + "_0_1", (math.dist(a, b), hh))
        wall(m, a, b, DRUM[0] + hh, DRUM[1], n2, reg + "_0_0", (math.dist(a, b), hh))
        wall(m, a, b, DRUM[1], DRUM[1] + 0.7, n2, "in_scritta%d" % (k % 4), (math.dist(a, b), 0.7))
    # dome, frescoed, with a golden oculus at the top
    rows = 6
    base = DRUM[1] + 0.7
    prof = [(DOME_R * math.cos(t * math.pi / 2), base + (DOME_TOP - base) * math.sin(t * math.pi / 2)) for t in np.linspace(0, 0.92, rows + 1)]
    for j in range(rows):
        (ra, ya), (rb, yb) = prof[j], prof[j + 1]
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            pa0 = V(cx + ra * math.cos(a0), ya, cz + ra * math.sin(a0))
            pa1 = V(cx + ra * math.cos(a1), ya, cz + ra * math.sin(a1))
            pb0 = V(cx + rb * math.cos(a0), yb, cz + rb * math.sin(a0))
            pb1 = V(cx + rb * math.cos(a1), yb, cz + rb * math.sin(a1))
            cen = (pa0 + pa1 + pb0 + pb1) / 4
            nrm = V(cx, base, cz) - cen
            # the dome is four photographs of a quarter each: four segments wide, six rows high
            kk = k % 4
            u0, u1, v0, v1 = kk / 4, (kk + 1) / 4, 1 - j / rows, 1 - (j + 1) / rows
            fface(m, [pa0, pa1, pb1, pb0], "in_cupola%d" % (k // 4), nrm, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    r_top, y_top = prof[-1]
    annulus(m, (cx, cz), 0.0, r_top, y_top, n, "in_oro", nrm=-UP)
    return m


# ------------------------------------------------------------------------------------ chapel
@piece(174, "INTERNO_CAPPELLA", (46.0, -13.0), "Cappella nel transetto sud: pareti dorate con stelle rosse, altare laterale")
def cappella():
    m = G.Mesh()
    x0, x1, zs = CHAPEL
    for a, b, n2 in (((x0, zs), (x1, zs), (0.0, 1.0)), ((x0, -HW), (x0, zs), (1.0, 0.0)), ((x1, zs), (x1, -HW), (-1.0, 0.0))):
        wall(m, a, b, 0.0, 1.2, n2, "in_marmo_rosso", (2.0, 1.2), off=0.10)
        wall(m, a, b, 1.2, AISLE_H, n2, "in_giallo", (2.0, 2.0), off=0.10)
        cornice(m, a, b, AISLE_H - 0.5, n2, h=0.5, d=0.3, region="in_oro", ext=0.0)
    hrect(m, x0, x1, zs, -HW, AISLE_H - 0.10, "in_cassettoni", down=True)
    xc = (x0 + x1) / 2
    goverlay(m, (xc, zs), (0.0, 1.0), 1.2, 6.0, 7.2, "in_altare_sc", 2, 2, off=0.20)      # the real altar of the chapel
    return m


# ------------------------------------------------------------------------------------ furniture (with collision)
@model(175, "INTERNO_COLONNA", "Colonna in marmo rosa con base bianca e capitello dorato (con collisione)")
def colonna():
    m = G.Mesh()
    m.merge(G.box(1.0, 0.5, 1.0, "tn_marmo"))
    m.merge(G.cylinder(0.42, 0.38, 7.0, "in_marmo_rosa", n=10, base=(0, 0.5, 0), top_cap=False))
    m.merge(G.cylinder(0.4, 0.62, 0.6, "in_oro", n=10, base=(0, 7.5, 0)))
    m.merge(G.box(1.3, 0.35, 1.3, "in_oro", center=(0, 8.1, 0)))
    m.merge(G.box(1.0, 0.55, 1.0, "tn_marmo", center=(0, 8.45, 0)))
    return m, ((-0.5 * M, 0, -0.5 * M), (0.5 * M, 9.0 * M, 0.5 * M))


@model(176, "INTERNO_BANCO", "Banco in legno, 3.2 m (con collisione)")
def banco():
    m = G.Mesh()
    m.merge(G.box(0.42, 0.06, 3.2, "in_legno", center=(0, 0.42, 0)))           # seat
    m.merge(G.box(0.06, 0.55, 3.2, "in_legno", center=(-0.2, 0.48, 0)))        # back
    m.merge(G.box(0.3, 0.1, 3.2, "in_legno", center=(0.32, 0.75, 0)))          # book rest of the pew behind
    for z in (-1.55, 1.55):
        m.merge(G.box(0.6, 1.0, 0.06, "in_legno", center=(0, 0, z)))
    m.merge(G.box(0.25, 0.08, 3.1, "in_legno", center=(0.32, 0.12, 0)))        # kneeler
    return m, ((-0.3 * M, 0, -1.6 * M), (0.45 * M, 1.0 * M, 1.6 * M))


@model(177, "INTERNO_ALTARE", "Altare maggiore in marmo con fronte dorato (con collisione)")
def altare():
    m = G.Mesh()
    m.merge(G.box(1.4, 1.0, 3.2, "tn_marmo", sides="in_marmo_rosso"))
    m.merge(G.box(1.6, 0.1, 3.4, "tn_marmo", center=(0, 1.0, 0)))
    fr = G.Mesh()
    rectf(fr, V(-0.72, 0.15, 1.3), V(0, 0, -1), UP, 2.6, 0.7, "in_oro", V(-1, 0, 0), tile=None)
    m.merge(fr)
    for z in (-1.2, 1.2):    # candlesticks
        m.merge(G.cylinder(0.08, 0.05, 0.6, "in_oro", n=6, base=(0, 1.1, z)))
        m.merge(G.cylinder(0.03, 0.03, 0.25, "tn_marmo", n=6, base=(0, 1.7, z)))
    m.merge(G.box(0.06, 0.7, 0.06, "in_oro", center=(0, 1.1, 0)))
    m.merge(G.box(0.06, 0.06, 0.4, "in_oro", center=(0, 1.6, 0)))
    return m, ((-0.8 * M, 0, -1.7 * M), (0.8 * M, 1.1 * M, 1.7 * M))


@model(178, "INTERNO_LAMPADARIO", "Lampadario in ottone a due giri di bracci")
def lampadario():
    m = G.Mesh()
    m.merge(G.box(0.05, 3.0, 0.05, "in_oro", center=(0, 0, 0)))
    for r, y, n in ((1.0, 0.0, 8), (0.6, 0.5, 6)):
        for k in range(n):
            a = 2 * math.pi * k / n
            m.merge(G.box(0.06, 0.04, 0.06, "in_oro", center=(r * math.cos(a), y, r * math.sin(a))))
            m.merge(G.cylinder(0.05, 0.05, 0.25, "tn_marmo", n=6, base=(r * math.cos(a), y + 0.04, r * math.sin(a))))
        ring = G.cylinder(r, r, 0.06, "in_oro", n=n * 2, base=(0, y - 0.03, 0), top_cap=False)
        m.merge(ring)
    m.merge(G.ellipsoid(0.25, 0.3, 0.25, "in_oro", n=8, rings=4, center=(0, -0.2, 0)))
    return m, None


# spots for the repeated pieces (interior frame)
SPOTS["INTERNO_COLONNA"] = [(x, s * NAVE, 0.0) for x in COLS for s in (-1, 1)]
SPOTS["INTERNO_BANCO"] = [(x, s * 2.85, 0.0) for x in np.arange(7.0, 37.5, 1.25) for s in (-1, 1)]
SPOTS["INTERNO_ALTARE"] = [(62.0, 0.0, 0.0), (46.0, -14.0, 90.0)]
SPOTS["INTERNO_LAMPADARIO"] = [(x, 0.0, 0.0) for x in (10.0, 20.0, 30.0, 58.0)]
