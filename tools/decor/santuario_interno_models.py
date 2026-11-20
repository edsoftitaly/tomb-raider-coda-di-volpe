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
from decor.santuario_models import UP, V, annulus, cornice, door, fface, frame, obox, overlay, rectf, wall

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


def trabeazione(m, x0, x1, zw, n2):
    """The entablature on the columns of the nave, as in the church: a beam of white marble, the blue frieze with
    the gold lettering running all along, the gilded cornice on its brackets."""
    n, r = frame(n2)
    w = x1 - x0
    xm = (x0 + x1) / 2
    obox(m, (xm, zw), n2, w, 0.5, AISLE_H - 0.8, AISLE_H, "in_architrave", tile=(1.6, 0.8))
    k = max(1, int(round(w / 5.6)))
    left = V(xm, AISLE_H, zw) - r * (w / 2) + n * 0.38
    for i in range(k):
        rectf(m, left + r * (w * i / k), r, UP, w / k, 0.7, "in_scritta%d" % (i % 4), n, None)
    cornice(m, (x0, zw), (x1, zw), AISLE_H + 0.7, n2, h=0.5, d=0.75, region="in_mensole", ext=0.0)


APSE_S, APSE_T = 0.6, 0.8      # how far the apse wall bows (m), how far the half dome leans over


def apse_x(z):
    return L - 0.15 - APSE_S * (z / NAVE) ** 2


def abside(m):
    """The apse behind the high altar. The room ends in a flat wall, so the apse is a shallow bow built in front of
    it: red marble dado, pilasters of green marble, panels of red damask, the band MATER MEA FIDUCIA MEA, a gilded
    cornice, and over it the half dome with its painting (Ed's photograph), under a gilded arch."""
    y0, y1, y2, y3, y4 = PRESB_H, PRESB_H + 1.2, 7.6, 8.3, 9.0
    zs = np.linspace(NAVE, -NAVE, 11)                 # from the viewer's left (north) to the right
    kinds = "PDdPCCPDdP"
    for s in range(10):
        a, b = V(apse_x(zs[s]), 0, zs[s]), V(apse_x(zs[s + 1]), 0, zs[s + 1])
        w = float(np.linalg.norm(b - a))
        r = (b - a) / w
        n = V(r[2], 0, -r[0])
        rectf(m, a + UP * y0, r, UP, w, y1 - y0, "in_marmo_rosso", n, None)
        kind, hh = kinds[s], y2 - y1
        if kind == "P":
            rectf(m, a + UP * y1, r, UP, w, hh, "in_pilastro", n, None)
        elif kind == "C":
            rectf(m, a + UP * y1, r, UP, w, hh, "in_giallo", n, (w, hh / 3))
        else:
            i = 0 if kind == "D" else 1
            for j in range(2):
                rectf(m, a + UP * (y1 + hh * (1 - j) / 2), r, UP, w, hh / 2, "in_damasco_%d_%d" % (i, j), n, None)
        u0, u1 = (s % 2) / 2, (s % 2 + 1) / 2
        fface(m, [a + UP * y2, b + UP * y2, b + UP * y3, a + UP * y3], "in_fascia%d" % (s // 2), n, [(u0, 1), (u1, 1), (u1, 0), (u0, 0)])
        # cornice: 25 cm out, with its underside and its top (the sill of the half dome)
        d = V(-0.25, 0, 0)
        fface(m, [a + d + UP * y3, b + d + UP * y3, b + d + UP * y4, a + d + UP * y4], "in_mensole", n,
              [(u0, 1), (u1, 1), (u1, 0), (u0, 0)])
        fface(m, [a + UP * y3, b + UP * y3, b + d + UP * y3, a + d + UP * y3], "in_oro", -UP)
        fface(m, [a + UP * y4, b + UP * y4, b + d + UP * y4, a + d + UP * y4], "in_oro", UP)
    # half dome: the painting laid on it as seen from the nave (two regions, left and right)
    R, rings, sect = NAVE, 4, 12

    def pt(rho, th):
        z, y = rho * R * math.cos(th), rho * R * math.sin(th)
        return V(apse_x(z) - APSE_T * (y / R) ** 2, y4 + y, z)

    def uv(p, i):
        return ((NAVE - p[2]) / (2 * NAVE) * 2 - i, 1 - (p[1] - y4) / R)

    for k in range(sect):
        t0, t1 = math.pi * k / sect, math.pi * (k + 1) / sect
        i = 0 if k < sect // 2 else 1
        for j in range(rings):
            ra, rb = max(0.004, j / rings), (j + 1) / rings      # (a quad to the last: no triangle fan at the centre)
            q = [pt(rb, t0), pt(rb, t1), pt(ra, t1), pt(ra, t0)]
            fface(m, q, "in_catino_%d_0" % i, V(-1, 0, 0), [tuple(min(1.0, max(0.0, c)) for c in uv(p, i)) for p in q])
    # the arch in front of it: a gilded band on the edge of the half dome, the wall up to the vault
    xa = L - 0.15 - max(APSE_S, APSE_T) - 0.03
    for k in range(sect):
        t0, t1 = math.pi * k / sect, math.pi * (k + 1) / sect

        def ring(rad, t):
            return V(xa, y4 + rad * math.sin(t), rad * math.cos(t))

        def top(t):
            z = (R + 0.01) * math.cos(t)
            return V(xa, VAULT_SPRING + (VAULT_TOP - VAULT_SPRING) * math.sqrt(max(0.0, 1 - (z / NAVE) ** 2)) + 0.3, max(-NAVE, min(NAVE, z)))
        fface(m, [ring(R - 0.2, t0), ring(R - 0.2, t1), ring(R + 0.45, t1), ring(R + 0.45, t0)], "in_oro", V(-1, 0, 0))
        fface(m, [ring(R + 0.45, t0), ring(R + 0.45, t1), top(t1), top(t0)], "in_volta", V(-1, 0, 0))


def baldacchino(m):
    """The golden shrine of the Madonna Nera, high behind the altar: a platform against the apse wall (the two bronze
    angels that carry it are a static of their own, INTERNO_ANGELO), four columns, the statue between the curtains
    (Ed's photograph), a little dome with its crown. The floor under it stays free."""
    cx, yb = 64.45, PRESB_H + 3.3
    m.merge(G.box(2.2, 0.3, 2.9, "in_oro", center=(cx, yb, 0), bottom=True))
    m.merge(G.box(0.45, 0.3, 2.4, "in_oro", center=(cx + 1.3, yb, 0), bottom=True))           # corbel into the wall
    m.merge(G.box(1.9, 0.25, 2.5, "in_oro", center=(cx, yb + 0.3, 0)))
    yc, hc = yb + 0.55, 3.0
    for dx in (-0.7, 0.7):
        for dz in (-1.0, 1.0):
            m.merge(G.cylinder(0.16, 0.16, 0.18, "in_oro", n=6, base=(cx + dx, yc, dz), top_cap=False))
            m.merge(G.cylinder(0.12, 0.10, hc - 0.42, "in_oro", n=6, base=(cx + dx, yc + 0.18, dz), top_cap=False))
            m.merge(G.cylinder(0.10, 0.18, 0.24, "in_oro", n=6, base=(cx + dx, yc + hc - 0.24, dz), top_cap=False))
    rectf(m, V(cx + 0.35, yc, 0.75), V(0, 0, -1), UP, 1.5, hc, "in_statua", V(-1, 0, 0), None)
    for s in (-1, 1):                                        # the sides of the niche: gilded lattice
        rectf(m, V(cx + 0.35, yc, s * 0.75), V(1, 0, 0), UP, 0.6, hc, "in_giallo", V(0, 0, float(s)), (0.6, 1.0), double=True)
    m.merge(G.box(2.2, 0.4, 2.9, "in_oro", center=(cx, yc + hc, 0), bottom=True))
    m.merge(G.cylinder(1.15, 0.8, 0.4, "in_oro", n=8, base=(cx, yc + hc + 0.4, 0), top_cap=False))
    m.merge(G.cylinder(0.8, 0.25, 0.55, "in_oro", n=8, base=(cx, yc + hc + 0.8, 0)))
    m.merge(G.ellipsoid(0.18, 0.22, 0.18, "in_oro", n=6, rings=4, center=(cx, yc + hc + 1.5, 0)))


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
                if (i + (side > 0)) % 3 == 0:               # the real mosaic of 1954, bigger, every third bay
                    goverlay(m, (xc, zw), n2, 1.8, 4.6, 2.3, "in_murale", 4, 2, off=off * 2)
                else:
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
            for xc in bay_list(x0, x1, 5.0)[0]:               # over the cornice: three lights side by side
                for dz in (-0.8, 0.0, 0.8):
                    goverlay(m, (xc + dz, zw), n2, 10.4, 0.75, 1.5, "in_vetrata%d" % (int(xc) % 5), 1, 2, off=off * 2)
            trabeazione(m, x0, x1, zw, n2)
    # entrance wall (inside of the facade) and the gilded apse wall
    wall(m, (0.0, -HW), (0.0, HW), 0.0, AISLE_H, (1.0, 0.0), "in_parete", off=off)
    wall(m, (0.0, -NAVE), (0.0, NAVE), AISLE_H, VAULT_TOP, (1.0, 0.0), "in_parete", off=off)
    door(m, (0.0, 0.0), (1.0, 0.0), 0.0, 3.2, 6.4, off=off * 2)
    for zc in (-2.2, 0.0, 2.2):
        goverlay(m, (0.0, zc), (1.0, 0.0), 9.2, 1.8, 3.6, "in_vetrata%d" % (int(zc + 3) % 5), 1, 2, off=off * 2)
    for zc in (-8.0, 8.0):
        door(m, (0.0, zc), (1.0, 0.0), 0.0, 1.8, 3.6, off=off * 2)
    wall(m, (L, HW), (L, -HW), 0.0, AISLE_H, (-1.0, 0.0), "in_parete", off=off)
    abside(m)
    baldacchino(m)
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
    # as in the church: a plinth of grey-blue marble, a white base, the shaft of pink marble, a Corinthian
    # capital of white stone (it was a block of gold)
    m.merge(G.box(1.1, 0.3, 1.1, "in_base"))
    m.merge(G.cylinder(0.5, 0.44, 0.2, "tn_marmo", n=10, base=(0, 0.3, 0), top_cap=False))
    m.merge(G.cylinder(0.42, 0.38, 7.0, "in_marmo_rosa", n=10, base=(0, 0.5, 0), top_cap=False))
    m.merge(G.cylinder(0.4, 0.62, 0.6, "in_capitello", n=10, base=(0, 7.5, 0)))
    m.merge(G.box(1.3, 0.35, 1.3, "tn_marmo", center=(0, 8.1, 0)))
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


@model(178, "INTERNO_LAMPADARIO", "Lampadario in ferro battuto a due giri di candele, appeso alla trabeazione (origine: il gancio)")
def lampadario():
    """As in the church: black wrought iron, a long chain, two rounds of candles. The origin is the hook, the
    chandelier hangs 2 to 3 m under it."""
    m = G.Mesh()
    m.merge(G.box(0.035, 1.9, 0.035, "in_ferro", center=(0, -1.9, 0)))
    m.merge(G.ellipsoid(0.11, 0.42, 0.11, "in_ferro", n=6, rings=4, center=(0, -2.3, 0)))
    m.merge(G.ellipsoid(0.07, 0.09, 0.07, "in_ferro", n=6, rings=3, center=(0, -2.82, 0)))
    for r, y, n, ph in ((0.75, -2.6, 8, 0.0), (0.45, -2.2, 4, math.pi / 4)):
        for k in range(n):
            a = 2 * math.pi * k / n + ph
            c, s = math.cos(a), math.sin(a)
            m.merge(G.tube([(0.08 * c, y + 0.12, 0.08 * s), (0.55 * r * c, y - 0.16, 0.55 * r * s), (r * c, y, r * s)],
                           [0.022, 0.02, 0.018], "in_ferro", n=4))
            m.merge(G.cylinder(0.07, 0.05, 0.04, "in_ferro", n=6, base=(r * c, y, r * s), top_cap=False))
            m.merge(G.cylinder(0.028, 0.028, 0.2, "tn_marmo", n=5, base=(r * c, y + 0.04, r * s)))
            m.merge(G.ellipsoid(0.03, 0.06, 0.03, "in_fiamma", n=4, rings=3, center=(r * c, y + 0.3, r * s)))
    return m, None


@model(179, "INTERNO_ANGELO", "Angelo di bronzo che regge il baldacchino della Madonna Nera, 3.3 m (con collisione)")
def angelo():
    """One of the two dark bronze angels that carry the shrine: robe, raised arms, wings. Faces -X (the nave)."""
    m = G.Mesh()
    b = "in_bronzo"
    m.merge(G.cylinder(0.50, 0.42, 0.25, b, n=8))                                              # plinth
    m.merge(G.cylinder(0.42, 0.20, 1.75, b, n=8, base=(0, 0.25, 0), top_cap=False))            # robe
    m.merge(G.ellipsoid(0.23, 0.44, 0.30, b, n=8, rings=5, center=(0, 2.1, 0)))                # chest
    m.merge(G.ellipsoid(0.14, 0.17, 0.14, b, n=6, rings=4, center=(-0.03, 2.68, 0)))           # head
    for s in (-1, 1):
        m.merge(G.tube([(0, 2.38, s * 0.26), (-0.12, 2.8, s * 0.40), (0.02, 3.3, s * 0.36)], [0.085, 0.07, 0.055], b, n=5))
        m.merge(G.quad((0.2, 2.45, s * 0.12), (0.5, 3.25, s * 0.7), (0.55, 2.3, s * 1.1), (0.32, 1.15, s * 0.5), b, double=True))
        m.merge(G.quad((0.2, 2.45, s * 0.12), (0.32, 1.15, s * 0.5), (0.3, 1.6, s * 0.1), (0.22, 2.0, s * 0.05), b, double=True))
    return m, ((-0.45 * M, 0, -0.45 * M), (0.45 * M, 3.3 * M, 0.45 * M))


# spots for the repeated pieces (interior frame)
SPOTS["INTERNO_COLONNA"] = [(x, s * NAVE, 0.0) for x in COLS for s in (-1, 1)]
SPOTS["INTERNO_BANCO"] = [(x, s * 2.85, 0.0) for x in np.arange(7.0, 37.5, 1.25) for s in (-1, 1)]
SPOTS["INTERNO_ALTARE"] = [(62.0, 0.0, 0.0), (46.0, -14.0, 90.0)]
# 20 Nov: the chandeliers hang in the arcades, between one column and the next, from the beam (hook at 8.2 m)
SPOTS["INTERNO_LAMPADARIO"] = [(x, s * NAVE, 0.0) for x in np.arange(6.5, 37.0, 5.0) for s in (-1, 1)]
LAMP_HOOK = AISLE_H - 0.8
SPOTS["INTERNO_ANGELO"] = [(64.0, s * 1.75, 0.0) for s in (-1, 1)]
