"""Static meshes of the Santuario di Tindari (ids 150-169), v2: built from Ed's photos and the OSM plan.

Pieces are modelled in the church frame of santuario.py (X = u towards the east end, Z = v north,
Y up, metres) around their anchor; the level places them with rotation AXIS_DEG.
The Segreteria and the terrace railing pieces are modelled in their own frame and placed apart.

Winding: every face goes through `fface`, which takes the intended OUTWARD normal and orders the
corners so that TombLib's rule holds (cross(b - a, c - a) of the STORED order points out of the
front face). `check_winding()` verifies it on the built meshes.

Collision: the buildings are solid room geometry under the skins (santuario.prepare), so the skins
carry no collision box; only the railing pieces (on walkable ground) have one.
"""
import math

import numpy as np

import santuario as S
from decor import geom as G
from decor.geom import M
from decor.models import model

ANCHORS = {}
UP = np.array([0.0, 1.0, 0.0])


def V(u, y, v):
    return np.array([u, y, v], float)


def fface(m, pts, region, n, uv=None, blend=0, double=False):
    """Face with corners in metres (u, y, v) and intended outward normal n."""
    q = [np.asarray(p, float) for p in pts]
    if uv is None:
        uv = [(0, 1), (1, 1), (1, 0), (0, 0)][:len(q)]
    uv = list(uv)
    c = np.cross(q[1] - q[0], q[2] - q[0])
    if len(q) == 4 and np.linalg.norm(c) < 1e-9:
        c = np.cross(q[2] - q[0], q[3] - q[0])
    # Mesh.face reverses the order it is given: hand it the order whose normal points INWARD.
    if np.dot(c, n) > 0:
        q, uv = q[::-1], uv[::-1]
    m.face([p * M for p in q], region, uv=uv, blend=blend, double=double)


def rectf(m, o, r, up, w, h, region, n, tile=(2.0, 2.0), blend=0, double=False):
    """Rectangle seen from the front: o = bottom-left corner, r = viewer's right, up (metres)."""
    o, r, up = (np.asarray(a, float) for a in (o, r, up))
    nu = 1 if tile is None else max(1, int(round(w / tile[0])))
    nv = 1 if tile is None else max(1, int(round(h / tile[1])))
    for i in range(nu):
        for j in range(nv):
            a0, a1, b0, b1 = w * i / nu, w * (i + 1) / nu, h * j / nv, h * (j + 1) / nv
            bl, br = o + r * a0 + up * b0, o + r * a1 + up * b0
            tr, tl = o + r * a1 + up * b1, o + r * a0 + up * b1
            fface(m, [bl, br, tr, tl], region, n, [(0, 1), (1, 1), (1, 0), (0, 0)], blend, double)


def frame(n2):
    """Outward plan normal (nu, nv) -> 3D normal and viewer's right (left-handed TombEngine space)."""
    n = V(n2[0], 0, n2[1])
    r = V(-n2[1], 0, n2[0])
    return n, r


def wall(m, a, b, y0, y1, n2, region, tile=(2.0, 2.0), off=0.0, double=False, blend=0):
    """Vertical wall between plan points a and b (u, v), outward plan normal n2."""
    n, r = frame(n2)
    pa, pb = V(a[0], 0, a[1]), V(b[0], 0, b[1])
    left = pa if np.dot(pb - pa, r) > 0 else pb
    w = float(np.linalg.norm(pb - pa))
    rectf(m, left + V(0, y0, 0) + n * off, r, UP, w, y1 - y0, region, n, tile, blend, double)


def overlay(m, c, n2, y0, w, h, region, tile=None, off=0.03, blend=0, double=False):
    """Panel of width w centred on plan point c, in front of a wall."""
    n, r = frame(n2)
    o = V(c[0], y0, c[1]) - r * (w / 2) + n * off
    rectf(m, o, r, UP, w, h, region, n, tile, blend, double)


def door(m, c, n2, y0, w, h, off=0.03):
    """The bronze doors (tn_porta_i_j, 2 x 4 regions of santuario_tex.bronze_door_big), centred on plan point c."""
    n, r = frame(n2)
    o = V(c[0], y0, c[1]) - r * (w / 2) + n * off
    for i in range(2):
        for j in range(4):
            rectf(m, o + r * (w * i / 2) + UP * (h * (3 - j) / 4), r, UP, w / 2, h / 4, "tn_porta_%d_%d" % (i, j), n, None)


def obox(m, c, n2, w, d, y0, y1, region, top=None, tile=None):
    """Box standing out of a wall: back on plan point c, front at c + n * d, width w (pilasters, kerbs)."""
    n, r = frame(n2)
    cb = V(c[0], 0, c[1])
    t = tile or (w, y1 - y0)
    rectf(m, cb + n * d - r * (w / 2) + V(0, y0, 0), r, UP, w, y1 - y0, region, n, t)
    for s in (-1, 1):
        p0 = cb + r * (s * w / 2)
        p1 = p0 + n * d
        fface(m, [p0 + V(0, y0, 0), p1 + V(0, y0, 0), p1 + V(0, y1, 0), p0 + V(0, y1, 0)], region, r * s,
              [(0, 1), (0.15, 1), (0.15, 0), (0, 0)])
    q = [cb - r * (w / 2), cb + r * (w / 2), cb + r * (w / 2) + n * d, cb - r * (w / 2) + n * d]
    fface(m, [p + V(0, y1, 0) for p in q], top or region, UP)


def cornice(m, a, b, y, n2, h=0.45, d=0.4, region="tn_cornice", ext=None):
    """Moulding along a wall: front face (tiled), top and bottom faces; extended by d at both ends."""
    n, r = frame(n2)
    pa, pb = V(a[0], 0, a[1]), V(b[0], 0, b[1])
    e = d if ext is None else ext
    dirv = (pb - pa) / np.linalg.norm(pb - pa)
    pa, pb = pa - dirv * e, pb + dirv * e
    left, right = (pa, pb) if np.dot(pb - pa, r) > 0 else (pb, pa)
    w = float(np.linalg.norm(pb - pa))
    rectf(m, left + n * d + V(0, y, 0), r, UP, w, h, region, n, (2.0, h))
    for yy, nn in ((y + h, UP), (y, -UP)):
        q = [left + V(0, yy, 0), right + V(0, yy, 0), right + n * d + V(0, yy, 0), left + n * d + V(0, yy, 0)]
        fface(m, q, "tn_marmo", nn, [(0, 0), (1, 0), (1, 0.1), (0, 0.1)])
    for p in (left, right):   # end caps
        sn = (p - (left + right) / 2)
        sn = sn / np.linalg.norm(sn)
        q = [p + V(0, y, 0), p + n * d + V(0, y, 0), p + n * d + V(0, y + h, 0), p + V(0, y + h, 0)]
        fface(m, q, "tn_marmo", sn, [(0, 1), (0.2, 1), (0.2, 0), (0, 0)])


def tri(m, a, b, apex, region, n, double=False):
    fface(m, [a, b, apex], region, n, [(0, 1), (1, 1), (0.5, 0)], double=double)


def plan_normal(a, b, poly):
    """Outward unit normal (nu, nv) of edge a -> b of polygon poly."""
    d = np.array(b, float) - np.array(a, float)
    d /= np.linalg.norm(d)
    n = np.array([d[1], -d[0]])
    mid = (np.array(a) + np.array(b)) / 2
    if S.inside(poly, *(mid + n * 0.05)):
        n = -n
    return float(n[0]), float(n[1])


def neighbour_height(poly, a, b, n2):
    """Height of the other building that this wall leans on (0 if free)."""
    mid = (np.array(a) + np.array(b)) / 2 + np.array(n2) * 0.6
    h = 0.0
    for p, ph in S.BLOCKS:
        if p is not poly and S.inside(p, *mid):
            h = max(h, ph)
    return h


def hgrid(m, poly, y, region, tile=2.0, n=UP, shrink=0.0):
    """Horizontal surface over a polygon: grid squares whose centre is inside (roofs, seen from above)."""
    us, vs = [p[0] for p in poly], [p[1] for p in poly]
    u = min(us)
    while u < max(us):
        v = min(vs)
        while v < max(vs):
            if S.inside(poly, u + tile / 2, v + tile / 2):
                q = [V(u, y, v), V(u + tile, y, v), V(u + tile, y, v + tile), V(u, y, v + tile)]
                fface(m, q, region, n)
            v += tile
        u += tile


def ring(m, c, r, y0, y1, n, region, tile_h=None, start=0.0, blend=0, double=False, pick=None):
    """Vertical polygonal ring (drums, lanterns): one full texture per segment unless tile_h is given."""
    pts = [(c[0] + r * math.cos(start + 2 * math.pi * k / n), c[1] + r * math.sin(start + 2 * math.pi * k / n)) for k in range(n)]
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        mid = ((a[0] + b[0]) / 2 - c[0], (a[1] + b[1]) / 2 - c[1])
        L = math.hypot(*mid)
        reg = pick(k) if pick else region
        if reg is None:
            continue
        w = math.hypot(b[0] - a[0], b[1] - a[1])
        wall(m, a, b, y0, y1, (mid[0] / L, mid[1] / L), reg, (w, tile_h or (y1 - y0)), blend=blend, double=double)
    return pts


def annulus(m, c, r0, r1, y, n, region, nrm=UP, start=0.0):
    for k in range(n):
        a0, a1 = start + 2 * math.pi * k / n, start + 2 * math.pi * (k + 1) / n
        q = [V(c[0] + r0 * math.cos(a0), y, c[1] + r0 * math.sin(a0)), V(c[0] + r1 * math.cos(a0), y, c[1] + r1 * math.sin(a0)),
             V(c[0] + r1 * math.cos(a1), y, c[1] + r1 * math.sin(a1)), V(c[0] + r0 * math.cos(a1), y, c[1] + r0 * math.sin(a1))]
        fface(m, q, region, nrm, [(0, 1), (0, 0), (1, 0), (1, 1)])


def statue(m, u, y, v, h=2.0):
    m.merge(G.cylinder(0.3, 0.2, h * 0.82, "tn_marmo", n=8, base=(u, y, v)))
    m.merge(G.ellipsoid(0.15, 0.19, 0.15, "tn_marmo", n=8, rings=4, center=(u, y + h * 0.82 + 0.17, v)))


def shifted(m, du, dv):
    return m.transformed(t=(-du * M, 0, -dv * M))


def piece(sid, name, anchor, note):
    """Register a piece built in church coordinates, re-centred on its anchor (no collision box)."""
    def deco(fn):
        ANCHORS[name] = anchor

        def build():
            return shifted(fn(), *anchor), None
        model(sid, name, note)(build)
        return fn
    return deco


# ---------------------------------------------------------------------------------------- facade
@piece(150, "SANTUARIO_FACCIATA", (4.0, 0.0),
       "Facciata e torre campanaria in conci rosa: portale bronzeo, trifora, cella, Madonna in mosaico")
def facciata():
    m = G.Mesh()
    hw, tw, td = S.HALF_W, S.TOWER_HW, S.TOWER_D
    nF = (-1.0, 0.0)

    def at(s):           # facade coordinate s (to the viewer's right) -> plan point on the facade
        return (0.0, -s)

    # walls
    wall(m, (0, hw), (0, -hw), -S.SKIRT, 0, nF, "tn_forte")
    wall(m, (0, hw), (0, -hw), 0, 16.0, nF, "tn_ashlar")
    for s0, s1 in ((-hw, -tw), (tw, hw)):
        wall(m, at(s0), at(s1), 16.0, 17.6, nF, "tn_ashlar", (2.0, 1.6))
        wall(m, (0.35, -s0), (0.35, -s1), 15.0, 17.6, (1.0, 0.0), "tn_ashlar", (2.0, 2.6))   # back of the parapet
        cornice(m, at(s0), at(s1), 17.4, nF, h=0.3, d=0.3)
    wall(m, at(-tw), at(tw), 16.0, S.TOWER_H, nF, "tn_ashlar")
    for side in (-1, 1):
        wall(m, (0, side * tw), (td, side * tw), 16.0, S.TOWER_H, (0.0, side), "tn_ashlar")
    wall(m, (td, tw), (td, -tw), 17.0, S.TOWER_H, (1.0, 0.0), "tn_ashlar")
    # sagrato in marble in front of the doors
    hgrid(m, S.rect((-6.0, 0.0, -hw, hw)), 0.03, "tn_marmo")
    # ground order: bronze door, niches with St Peter and St Paul, side doors under pediments
    door(m, at(0), nF, 0.0, 3.2, 6.4)
    for s in (-3.4, 3.4):
        overlay(m, at(s), nF, 1.0, 1.3, 3.2, "tn_marmo", off=0.02)
        obox(m, at(s), nF, 1.0, 0.7, 0.0, 1.1, "tn_marmo")
        statue(m, -0.4, 1.1, -s, 2.1)
    for s in (-7.7, 7.7):
        door(m, at(s), nF, 0.0, 1.8, 3.6)
        obox(m, at(s), nF, 2.9, 0.3, 3.7, 4.0, "tn_marmo")
        tri(m, V(-0.06, 4.0, -(s - 1.3)), V(-0.06, 4.0, -(s + 1.3)), V(-0.06, 5.4, -s), "tn_timpano", V(-1, 0, 0))
        cornice(m, (0, -(s - 1.45)), (0, -(s + 1.45)), 5.3, nF, h=0.15, d=0.2, ext=0.0)
    for s, y1 in ((-2.2, 8.3), (2.2, 8.3), (-4.45, 15.5), (-5.15, 15.5), (4.45, 15.5), (5.15, 15.5), (-10.3, 15.5), (10.3, 15.5)):
        obox(m, at(s), nF, 0.5, 0.3, 0.0, y1, "tn_marmo")
    # frieze band, mosaic bands, trifora with mosaic archivolt
    cornice(m, at(-hw), at(hw), 8.3, nF, h=0.3, d=0.4)
    overlay(m, at(0), nF, 8.6, 2 * tw, 1.4, "tn_fregio", tile=(tw, 1.4))
    for s in (-7.7, 7.7):
        overlay(m, at(s), nF, 8.6, hw - tw, 1.4, "tn_mosaico")
    cornice(m, at(-hw), at(hw), 10.0, nF, h=0.3, d=0.35)
    overlay(m, at(0), nF, 10.8, 4.4, 8.0, "tn_trifora")
    for s in (-2.45, 2.45):
        obox(m, at(s), nF, 0.35, 0.2, 10.6, 18.8, "tn_marmo")
    overlay(m, at(0), nF, 18.8, 5.6, 1.0, "tn_mosaico")
    cornice(m, at(-hw), at(hw), 15.5, nF, h=0.45, d=0.5)
    # tower: cornices, belfry, attic, pediment with three statues, cross
    faces = [((0, tw), (0, -tw), nF), ((0, -tw), (td, -tw), (0.0, -1.0)), ((td, -tw), (td, tw), (1.0, 0.0)), ((td, tw), (0, tw), (0.0, 1.0))]
    for a, b, n2 in faces:
        for y, h, d in ((22.0, 0.45, 0.4), (28.8, 0.5, 0.45), (S.TOWER_H - 0.3, 0.3, 0.3)):
            cornice(m, a, b, y, n2, h=h, d=d)
    for s in (-3.6, -1.9, 1.9, 3.6):
        overlay(m, at(s), nF, 23.4, 1.5, 3.0, "tn_cella")
    overlay(m, at(0), nF, 23.1, 1.8, 3.6, "tn_madonna")
    for side in (-1, 1):
        for uc in (1.6, 4.0, 6.4):
            overlay(m, (uc, side * tw), (0.0, side), 23.4, 1.5, 3.0, "tn_cella")
    for vc in (-2.4, 0.0, 2.4):
        overlay(m, (td, vc), (1.0, 0.0), 23.4, 1.5, 3.0, "tn_cella")
    for s in (-tw + 0.25, tw - 0.25):
        obox(m, at(s), nF, 0.5, 0.25, 16.0, 28.8, "tn_marmo")
    hgrid(m, S.rect((0.0, td, -tw, tw)), S.TOWER_H, "tn_lastrico")
    tri(m, V(-0.1, S.TOWER_H, 3.2), V(-0.1, S.TOWER_H, -3.2), V(-0.1, S.TOWER_H + 2.2, 0), "tn_timpano", V(-1, 0, 0), double=True)
    for s in (-3.0, 3.0):
        statue(m, 0.4, S.TOWER_H, -s, 1.8)
    statue(m, 0.0, S.TOWER_H + 2.1, 0.0, 1.6)
    m.merge(G.box(0.12, 1.8, 0.12, "in_oro", center=(td / 2, S.TOWER_H, 0)))
    m.merge(G.box(0.12, 0.12, 1.0, "in_oro", center=(td / 2, S.TOWER_H + 1.3, 0)))
    return m


# ---------------------------------------------------------------------------------------- sides
def side_elevation(m, u0, u1, v, side, y_from=0.0, lower=True):
    """Orange side of the nave: blind arches with blue oculi below, windows and oculi above, white
    pilasters, two cornices, stone skirt down to the rock."""
    n2 = (0.0, float(side))
    if y_from <= 0:
        wall(m, (u0, v), (u1, v), -S.SKIRT, 0, n2, "tn_forte")
    wall(m, (u0, v), (u1, v), y_from, S.EAVES, n2, "tn_intonaco")
    k = max(1, int(round((u1 - u0) / 5.6)))
    bw = (u1 - u0) / k
    for i in range(k):
        cu = u0 + (i + 0.5) * bw
        if lower and y_from < 6:
            overlay(m, (cu, v), n2, 0.6, 3.0, 6.0, "tn_arco_cieco")
        if y_from < 10:
            overlay(m, (cu, v), n2, 9.9, 1.9, 1.9, "tn_finestra")
        overlay(m, (cu, v), n2, 12.3, 1.3, 1.3, "tn_oculo")
    for i in range(k + 1):
        obox(m, (u0 + i * bw, v), n2, 0.6, 0.3, max(0.0, y_from), S.EAVES - 0.5, "tn_marmo")
    if y_from < 8:
        cornice(m, (u0, v), (u1, v), 8.0, n2, h=0.5, d=0.35)
    cornice(m, (u0, v), (u1, v), S.EAVES - 0.5, n2, h=0.5, d=0.55)


@piece(151, "SANTUARIO_FIANCO_NORD", (37.0, S.HALF_W), "Fianco nord della navata, sul ciglio della rupe")
def fianco_nord():
    m = G.Mesh()
    side_elevation(m, 0.0, S.NAVE_END, 10.5, +1)
    return m


@piece(152, "SANTUARIO_FIANCO_SUD", (20.0, -S.HALF_W), "Fianco sud della navata, sulla terrazza")
def fianco_sud():
    m = G.Mesh()
    side_elevation(m, 0.0, S.TRANSEPT[0], -S.HALF_W, -1)
    return m


@piece(153, "SANTUARIO_TRANSETTO", (52.0, -12.0), "Braccio sud del transetto e testata est")
def transetto():
    m = G.Mesh()
    u0, u1, vs = S.TRANSEPT
    side_elevation(m, u0, u1, vs, -1)
    wall(m, (u0, vs), (u0, -S.HALF_W), 0.0, S.EAVES, (-1.0, 0.0), "tn_intonaco", (2.2, 2.0))
    cornice(m, (u0, vs), (u0, -S.HALF_W), S.EAVES - 0.5, (-1.0, 0.0), h=0.5, d=0.55)
    wall(m, (u1, vs), (u1, -S.HALF_W), 11.0, S.EAVES, (1.0, 0.0), "tn_intonaco", (2.2, 2.5))
    tri(m, V(u0 - 0.2, S.EAVES, vs), V(u1 + 0.2, S.EAVES, vs), V((u0 + u1) / 2, S.RIDGE, vs), "tn_intonaco", V(0, 0, -1))
    overlay(m, ((u0 + u1) / 2, vs), (0.0, -1.0), S.EAVES + 0.4, 1.6, 1.6, "tn_oculo")
    # the south side after the transept: only its top shows above the convent
    side_elevation(m, u1, S.NAVE_END, -S.HALF_W, -1, y_from=11.0, lower=False)
    # east end (mostly hidden by the convent and the north-east block)
    wall(m, (S.NAVE_END, -S.HALF_W), (S.NAVE_END, 10.5), 11.0, S.EAVES, (1.0, 0.0), "tn_intonaco")
    tri(m, V(S.NAVE_END, S.EAVES, 10.9), V(S.NAVE_END, S.EAVES, -10.9), V(S.NAVE_END, S.RIDGE, 0), "tn_intonaco", V(1, 0, 0))
    return m


# ---------------------------------------------------------------------------------------- roofs
def slope(m, a0, a1, c0, c1, y0, y1, along, region="tn_tetto", centre=0.0, side=1, tile=(2.0, 2.0)):
    """Roof slope: `along` = 'u' (ridge along u) or 'v'; c is the distance from the ridge line."""
    na = max(1, int(round(abs(a1 - a0) / tile[0])))
    nc = max(1, int(round(abs(c1 - c0) / tile[1])))
    for i in range(na):
        for j in range(nc):
            p0, p1 = a0 + (a1 - a0) * i / na, a0 + (a1 - a0) * (i + 1) / na
            q0, q1 = c0 + (c1 - c0) * j / nc, c0 + (c1 - c0) * (j + 1) / nc
            ya = y0 + (y1 - y0) * (q0 - c0) / (c1 - c0)
            yb = y0 + (y1 - y0) * (q1 - c0) / (c1 - c0)
            if along == "u":
                q = [V(p0, ya, centre + side * q0), V(p1, ya, centre + side * q0), V(p1, yb, centre + side * q1), V(p0, yb, centre + side * q1)]
                n = V(0, 1.0, side * (y0 - y1) / abs(c1 - c0))
            else:
                q = [V(centre + side * q0, ya, p0), V(centre + side * q0, ya, p1), V(centre + side * q1, yb, p1), V(centre + side * q1, yb, p0)]
                n = V(side * (y0 - y1) / abs(c1 - c0), 1.0, 0)
            fface(m, q, region, n, [(0, 0), (1, 0), (1, 1), (0, 1)])


@piece(154, "SANTUARIO_TETTO", (37.0, 0.0), "Tetto grigio a due falde della navata e del transetto")
def tetto():
    m = G.Mesh()
    over = 0.5
    drop = (S.RIDGE - S.EAVES) * over / S.HALF_W
    for side in (-1, 1):
        slope(m, 0.3, S.NAVE_END + over, 0.0, S.HALF_W + over, S.RIDGE, S.EAVES - drop, "u", side=side, tile=(2.0, 2.2))
    u0, u1, vs = S.TRANSEPT
    hu = (u1 - u0) / 2
    for side in (-1, 1):
        slope(m, vs - over, -1.0, 0.0, hu + over, S.RIDGE, S.EAVES - (S.RIDGE - S.EAVES) * over / hu, "v",
              centre=S.CROSSING_U, side=side, tile=(2.0, 2.2))
    return m


@piece(155, "SANTUARIO_CUPOLA", (S.CROSSING_U, 0.0), "Tiburio, tamburo arancio con finestre e oculi, cupola dorata, lanterna")
def cupola():
    m = G.Mesh()
    c = (S.CROSSING_U, 0.0)
    hs = 5.8
    sq = [(c[0] - hs, -hs), (c[0] + hs, -hs), (c[0] + hs, hs), (c[0] - hs, hs)]
    for a, b in zip(sq, sq[1:] + sq[:1]):
        n2 = plan_normal(a, b, sq)
        wall(m, a, b, 16.5, 20.5, n2, "tn_intonaco", (2.0, 2.0))
        cornice(m, a, b, 20.2, n2, h=0.3, d=0.3)
    hgrid(m, S.rect((c[0] - hs, c[0] + hs, -hs, hs)), 20.5, "tn_tetto")
    n, r = 16, 5.2
    ring(m, c, r, 20.5, 27.0, n, None, pick=lambda k: "tn_intonaco")
    for k in range(n):
        a0 = 2 * math.pi * (k + 0.5) / n
        mid = (c[0] + r * math.cos(math.pi / n) * math.cos(a0), r * math.cos(math.pi / n) * math.sin(a0))
        n2 = (math.cos(a0), math.sin(a0))
        if k % 2 == 0:
            overlay(m, mid, n2, 21.2, 1.8, 3.6, "tn_finestra_arco")
        else:
            overlay(m, mid, n2, 20.5, 0.45, 6.5, "tn_marmo")
    ring(m, c, r, 27.0, 29.0, n, "tn_oculo")
    ring(m, c, r + 0.35, 29.0, 29.45, n, "tn_cornice", tile_h=0.45)
    annulus(m, c, r, r + 0.35, 29.0, n, "tn_marmo", nrm=-UP)
    annulus(m, c, 0.0, r + 0.35, 29.45, n, "tn_marmo")
    ring(m, c, r + 0.25, 29.45, 30.45, n, "tn_ringhiera", blend=1, double=True)
    # the dome: slightly raised profile, golden glazed tiles
    rows = 7
    base_y, hgt, rad = 29.45, 8.0, 4.9
    prof = [(rad * math.cos(t * math.pi / 2) ** 0.85, base_y + hgt * math.sin(t * math.pi / 2)) for t in np.linspace(0, 1, rows + 1)]
    for j in range(rows):
        (ra, ya), (rb, yb) = prof[j], prof[j + 1]
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            pa0 = V(c[0] + ra * math.cos(a0), ya, ra * math.sin(a0))
            pa1 = V(c[0] + ra * math.cos(a1), ya, ra * math.sin(a1))
            pb0 = V(c[0] + rb * math.cos(a0), yb, rb * math.sin(a0))
            pb1 = V(c[0] + rb * math.cos(a1), yb, rb * math.sin(a1))
            cen = (pa0 + pa1 + pb0 + pb1) / 4
            nn = cen - V(c[0], base_y, 0)
            if rb < 0.05:
                fface(m, [pa0, pa1, pb0], "tn_oro", nn, [(0, 1), (1, 1), (0.5, 0)])
            else:
                fface(m, [pa0, pa1, pb1, pb0], "tn_oro", nn)
    top = base_y + hgt
    # lantern
    ring(m, c, 1.3, top - 0.6, top + 2.8, 8, "tn_finestra_arco")
    annulus(m, c, 0.0, 1.6, top + 2.8, 8, "tn_marmo", nrm=-UP)
    ring(m, c, 1.6, top + 2.8, top + 3.1, 8, "tn_cornice")
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p0 = V(c[0] + 1.6 * math.cos(a0), top + 3.1, 1.6 * math.sin(a0))
        p1 = V(c[0] + 1.6 * math.cos(a1), top + 3.1, 1.6 * math.sin(a1))
        ap = V(c[0], top + 4.6, 0)
        tri(m, p0, p1, ap, "tn_oro", (p0 + p1) / 2 - V(c[0], top + 3.1, 0) + V(0, 1.0, 0))
    m.merge(G.box(0.14, 2.2, 0.14, "in_oro", center=(c[0], top + 4.5, 0)))
    m.merge(G.box(0.14, 0.14, 1.1, "in_oro", center=(c[0], top + 5.9, 0)))
    return m


# ---------------------------------------------------------------------------------------- annexes
def extrude(m, poly, top, wall_fn, roof="tn_lastrico", parapet=0.9, skirt=True):
    """Walls along the polygon edges (outward normals, skipping the parts leaning on other buildings),
    a flat roof and a parapet. wall_fn(m, a, b, n2, y0, y1) draws the visible part of each edge."""
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if math.dist(a, b) < 0.3:
            continue
        n2 = plan_normal(a, b, poly)
        y0 = neighbour_height(poly, a, b, n2)
        if y0 >= top:
            continue
        if y0 > 0:
            y0 -= 0.5
        elif skirt:
            wall(m, a, b, -S.SKIRT, 0.0, n2, "tn_forte")
        wall_fn(m, a, b, n2, y0, top)
        if parapet:
            wall(m, a, b, top, top + parapet, n2, "tn_beige", (2.0, parapet), double=True)
            cornice(m, a, b, top + parapet, n2, h=0.15, d=0.15, ext=0.0)
    hgrid(m, poly, top, roof)


def convent_wall(m, a, b, n2, y0, y1):
    mid_u = (a[0] + b[0]) / 2
    if mid_u > 86.0:          # the old fortified sanctuary on the east cliff
        wall(m, a, b, y0, min(y1, 7.0), n2, "tn_forte")
        if y1 > 7.0:
            wall(m, a, b, max(7.0, y0), y1, n2, "tn_convento", (3.0, 2.5))
        return
    if n2[1] < -0.7 and y0 < 3.0:     # south front: arcade on the ground floor
        wall(m, a, b, y0, 3.0, n2, "tn_loggia_conv", (3.0, 3.0))
        y0 = 3.0
    wall(m, a, b, y0, y1, n2, "tn_convento", (3.0, 3.0))


@piece(156, "SANTUARIO_CONVENTO", (74.0, -10.0), "Convento a L e santuario antico fortificato sulla rupe, pannelli solari sul tetto")
def convento():
    m = G.Mesh()
    extrude(m, S.CONVENT, S.CONVENT_H, convent_wall)
    for u in np.arange(54.0, 86.0, 2.4):
        for v in np.arange(-21.8, -13.0, 2.0):
            q = [V(u, 12.4, v), V(u + 2.0, 12.4, v), V(u + 2.0, 12.9, v + 1.0), V(u, 12.9, v + 1.0)]
            fface(m, q, "tn_solare", V(0, 1, -0.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # rounded bastion at the north-east corner of the old sanctuary, with merlons
    bc, br = (95.4, 1.4), 3.0
    ring(m, bc, br, -S.SKIRT, 10.5, 12, "tn_forte", tile_h=2.0)
    annulus(m, bc, 0.0, br, 10.5, 12, "tn_lastrico")
    for k in range(12):
        a0 = 2 * math.pi * (k + 0.5) / 12
        p = (bc[0] + (br - 0.25) * math.cos(a0), bc[1] + (br - 0.25) * math.sin(a0))
        obox(m, p, (math.cos(a0), math.sin(a0)), 0.8, 0.45, 10.5, 11.3, "tn_forte")
    for a, b in zip(S.CONVENT, S.CONVENT[1:] + S.CONVENT[:1]):
        if (a[0] + b[0]) / 2 > 86.0 and math.dist(a, b) > 1.5:
            n2 = plan_normal(a, b, S.CONVENT)
            L = math.dist(a, b)
            for t in np.arange(0.9, L - 0.5, 1.8):
                p = (a[0] + (b[0] - a[0]) * t / L - n2[0] * 0.3, a[1] + (b[1] - a[1]) * t / L - n2[1] * 0.3)
                obox(m, p, n2, 0.9, 0.3, S.CONVENT_H + 0.9, S.CONVENT_H + 1.6, "tn_forte")
    return m


def plain_wall(region, tile=(3.0, 3.0)):
    def fn(m, a, b, n2, y0, y1):
        wall(m, a, b, y0, y1, n2, region, tile)
    return fn


@piece(157, "SANTUARIO_BLOCCO_NE", (79.6, 7.0), "Edificio alto a nord-est (sei piani) sul ciglio della rupe")
def blocco_ne():
    m = G.Mesh()
    extrude(m, S.NE_BLOCK, S.NE_H, plain_wall("tn_convento"))
    return m


@piece(158, "SANTUARIO_ALA_NORD", (63.5, 11.8), "Ala bassa lungo il fianco nord, tetto in coppi")
def ala_nord():
    m = G.Mesh()
    extrude(m, S.NORTH_WING, S.WING_H, plain_wall("tn_convento", (3.0, 2.5)), parapet=0.0)
    u0, u1 = 53.4, 73.4
    q = [V(u0, S.WING_H + 1.0, 10.5), V(u1, S.WING_H + 1.0, 10.5), V(u1, S.WING_H - 0.1, 13.5), V(u0, S.WING_H - 0.1, 13.5)]
    slope(m, u0, u1, 0.0, 3.0, S.WING_H + 1.0, S.WING_H - 0.1, "u", region="tn_coppi", centre=10.5, side=1, tile=(2.0, 1.5))
    tri(m, V(53.7, S.WING_H, 10.5), V(53.7, S.WING_H, 13.1), V(53.7, S.WING_H + 1.0, 10.5), "tn_convento", V(-1, 0, 0))
    del q
    return m


def annex_wall(m, a, b, n2, y0, y1):
    wall(m, a, b, y0, y1, n2, "tn_intonaco")
    L = math.dist(a, b)
    k = int(L // 3.0)
    for i in range(k):
        t = (i + 0.5) * L / k
        p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
        overlay(m, p, n2, 1.2, 1.5, 3.0, "tn_finestra_arco")


@piece(159, "SANTUARIO_ANNESSO", (45.7, -19.2), "Corpo basso a sud del transetto")
def annesso():
    m = G.Mesh()
    extrude(m, S.ANNEX, S.ANNEX_H, annex_wall)
    return m


@piece(160, "SANTUARIO_TERRAZZA", (24.0, -16.0), "Muro della terrazza sud (edificio sottostante) e cordolo in marmo")
def terrazza():
    m = G.Mesh()
    edge = S.TERRACE_EDGE
    for a, b in zip(edge, edge[1:]):
        n2 = plan_normal(a, b, S.TERRACE)
        wall(m, a, b, -S.SKIRT, -9.0, n2, "tn_forte")
        wall(m, a, b, -9.0, 0.0, n2, "tn_convento", (3.0, 3.0))
        L = math.dist(a, b)
        mid = ((a[0] + b[0]) / 2 - n2[0] * 0.35, (a[1] + b[1]) / 2 - n2[1] * 0.35)
        obox(m, mid, n2, L + 0.3, 0.35, 0.0, 0.35, "tn_marmo", tile=(2.0, 0.35))
    return m


# ---------------------------------------------------------------------------------------- separate frames
@model(161, "SANTUARIO_SEGRETERIA", "Segreteria del santuario: corpo basso arancio con aperture ad arco e tetto in coppi")
def segreteria():
    m = G.Mesh()
    _, _, L, W = S.segreteria_frame()
    hl, hw, h = L / 2, W / 2, S.SEGRETERIA_H
    sq = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]
    for a, b in zip(sq, sq[1:] + sq[:1]):
        n2 = plan_normal(a, b, sq)
        wall(m, a, b, -6.0, 0.0, n2, "tn_forte")
        wall(m, a, b, 0.0, h, n2, "tn_intonaco")
        cornice(m, a, b, h - 0.3, n2, h=0.3, d=0.25)
        Ln = math.dist(a, b)
        k = int(Ln // 3.6)
        for i in range(k):
            t = (i + 0.5) * Ln / k
            p = (a[0] + (b[0] - a[0]) * t / Ln, a[1] + (b[1] - a[1]) * t / Ln)
            if n2[1] > 0.5:       # towards the square: arched doors and windows
                overlay(m, p, n2, 0.0, 1.8, 3.6, "tn_portone_seg")
            else:
                overlay(m, p, n2, 1.3, 1.2, 1.2, "tn_finestra")
    over, ridge = 0.4, h + 1.6
    for side in (-1, 1):
        slope(m, -hl - over, hl + over, 0.0, hw + over, ridge, h - 1.6 * over / hw, "u", region="tn_coppi", side=side, tile=(2.0, 1.5))
    for x, nx in ((-hl, -1.0), (hl, 1.0)):
        tri(m, V(x, h, -hw), V(x, h, hw), V(x, ridge, 0), "tn_intonaco", V(nx, 0, 0))
    return m, None


@model(162, "SANTUARIO_RINGHIERA", "Ringhiera in ferro sulla terrazza (2.5 m, con collisione)")
def ringhiera():
    m = G.Mesh()
    rectf(m, V(-1.25, 0.0, 0.0), V(1, 0, 0), UP, 2.5, 1.3, "tn_ringhiera", V(0, 0, -1), tile=None, blend=1, double=True)      # down to the paving (it began 35 cm up)
    m.merge(G.box(2.5, 0.06, 0.08, "tn_cornice", center=(0, 1.3, 0)))
    return m, ((-1.25 * M, 0, -0.15 * M), (1.25 * M, 1.35 * M, 0.15 * M))
