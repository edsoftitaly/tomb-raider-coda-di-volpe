"""Static meshes of the Santuario di Tindari (ids 150-179), built in the church frame of santuario.py.

Every piece is modelled around its own anchor (u, v) at floor level, local +X = u (towards the apse),
+Z = v (north), +Y up; the level places it at to_world(anchor) with rotation AXIS_DEG. Pieces are
split so that each one stays inside about 30 m from its anchor (room culling and int16 safety) and
so that the solid ones can carry a single collision box (TombEngine statics collide as oriented boxes).
Walls are tiled every 2 m so the stone keeps 128 px per metre (no stretched textures).
"""
import math

import numpy as np

import santuario as S
from decor import geom as G
from decor.geom import M
from decor.models import model

ANCHORS = {}


def P(u, y, v):
    return np.array([u * M, y * M, v * M], float)


def panel(m, o, r, up, w, h, region, tile=(2.0, 2.0), uvrect=None):
    """Flat rectangle seen from the front: o = bottom-left corner, r = unit vector to the viewer's right,
    up = unit vector up (metres). tile = size of one texture repeat, or None to stretch uvrect once."""
    o, r, up = (np.array(a, float) for a in (o, r, up))
    if tile is None:
        nu, nv = 1, 1
    else:
        nu, nv = max(1, int(round(w / tile[0]))), max(1, int(round(h / tile[1])))
    for i in range(nu):
        for j in range(nv):
            a0, a1 = w * i / nu, w * (i + 1) / nu
            b0, b1 = h * j / nv, h * (j + 1) / nv
            bl = o + r * a0 + up * b0
            br = o + r * a1 + up * b0
            tr = o + r * a1 + up * b1
            tl = o + r * a0 + up * b1
            if uvrect is None:
                uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
            else:
                u0, v0, u1, v1 = uvrect
                uv = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
            m.face([tl * M, tr * M, br * M, bl * M], region, uv=uv[::-1])


# Viewer's right for each outward normal (TombEngine space is left-handed: facing -v, right is -u).
RIGHT = {"+v": (-1, 0, 0), "-v": (1, 0, 0), "-u": (0, 0, -1), "+u": (0, 0, 1)}
UP = (0, 1, 0)


def wall(m, a, b, y0, y1, facing, region, tile=(2.0, 2.0)):
    """Wall between plan points a and b (u, v), outward normal 'facing'; drawn from the viewer's left."""
    r = np.array(RIGHT[facing], float)
    pa, pb = np.array([a[0], 0, a[1]], float), np.array([b[0], 0, b[1]], float)
    left = pa if np.dot(pb - pa, r) > 0 else pb
    w = float(np.linalg.norm(pb - pa))
    panel(m, left + np.array([0, y0, 0]), r, UP, w, y1 - y0, region, tile)


def hquad(m, corners, y, region, tile=2.0, down=False):
    """Horizontal rectangle (u0, v0, u1, v1) at height y, seen from above (or below)."""
    u0, v0, u1, v1 = corners
    nu, nv = max(1, int(round((u1 - u0) / tile))), max(1, int(round((v1 - v0) / tile)))
    for i in range(nu):
        for j in range(nv):
            a0, a1 = u0 + (u1 - u0) * i / nu, u0 + (u1 - u0) * (i + 1) / nu
            b0, b1 = v0 + (v1 - v0) * j / nv, v0 + (v1 - v0) * (j + 1) / nv
            pts = [P(a0, y, b0), P(a1, y, b0), P(a1, y, b1), P(a0, y, b1)]
            if down:
                pts = pts[::-1]
            m.face(pts, region)


def shifted(m, du, dv):
    return m.transformed(t=(-du * M, 0, -dv * M))


def piece(sid, name, anchor, note):
    """Register a piece built in church coordinates and re-centred on its anchor."""
    def deco(fn):
        ANCHORS[name] = anchor

        def build():
            mesh, coll = fn()
            mesh = shifted(mesh, *anchor)
            if coll is not None:
                (a, b) = coll
                coll = ((a[0] - anchor[0] * M, a[1], a[2] - anchor[1] * M), (b[0] - anchor[0] * M, b[1], b[2] - anchor[1] * M))
            return mesh, coll
        model(sid, name, note)(build)
        return fn
    return deco


def box_coll(u0, u1, v0, v1, y0, y1):
    return ((u0 * M, y0 * M, v0 * M), (u1 * M, y1 * M, v1 * M))


def gable(m, u0, u1, half, y_eave, y_ridge, region, axis="u", over=0.6, centre=0.0):
    """Two roof slopes with the ridge along `axis` (u or v), from u0..u1 along it, +-half across."""
    for side in (-1, 1):
        for i in range(max(1, int(round((u1 - u0) / 2.0)))):
            a0 = u0 + (u1 - u0) * i / max(1, int(round((u1 - u0) / 2.0)))
            a1 = u0 + (u1 - u0) * (i + 1) / max(1, int(round((u1 - u0) / 2.0)))
            n_across = max(1, int(round((half + over) / 2.0)))
            for j in range(n_across):
                c0 = (half + over) * j / n_across
                c1 = (half + over) * (j + 1) / n_across
                y_at = lambda c: y_ridge - (y_ridge - y_eave) * c / half  # noqa: E731
                if axis == "u":
                    q = [P(a0, y_at(c1), centre + side * c1), P(a1, y_at(c1), centre + side * c1),
                         P(a1, y_at(c0), centre + side * c0), P(a0, y_at(c0), centre + side * c0)]
                else:
                    q = [P(centre + side * c1, y_at(c1), a0), P(centre + side * c1, y_at(c1), a1),
                         P(centre + side * c0, y_at(c0), a1), P(centre + side * c0, y_at(c0), a0)]
                # slopes seen from above: keep the front up whatever the side
                if (side > 0) != (axis == "u"):
                    q = q[::-1]
                m.face(q, region)


def gable_end(m, u, half, y_eave, y_ridge, facing, region, centre=0.0, axis="u"):
    """Triangular wall closing a gable."""
    if axis == "u":
        a, b, c = P(u, y_eave, centre - half), P(u, y_eave, centre + half), P(u, y_ridge, centre)
    else:
        a, b, c = P(centre - half, y_eave, u), P(centre + half, y_eave, u), P(centre, y_ridge, u)
    tri = [a, b, c] if facing in ("-u", "+v") else [b, a, c]
    m.face(tri, region, uv=[(0, 1), (1, 1), (0.5, 0)])


# ---------------------------------------------------------------------------------------- facade
@piece(150, "SANTUARIO_FACCIATA", (0.0, 0.0), "Facciata: corpo centrale aggettante, portale, oculo, frontone AVE MARIA")
def facciata():
    m = G.Mesh()
    fh, pr = S.FACADE_HALF, S.FACADE_PROJ
    u = -pr
    # Front of the central body: rusticated up to 8 m, smooth stone above, split around the openings.
    # Portal: 4.4 m wide, 7.2 m tall; niches with statues at v = +-3.2.
    pw, ph = 4.4, 7.2
    # rusticated band left / right of the portal, and above it up to 8 m
    wall(m, (u, -fh), (u, -pw / 2), 0, 8.0, "-u", "sp_bugnato")
    wall(m, (u, pw / 2), (u, fh), 0, 8.0, "-u", "sp_bugnato")
    wall(m, (u, -pw / 2), (u, pw / 2), ph, 8.0, "-u", "sp_bugnato", tile=(pw / 2, 0.8))
    # bronze doors, slightly recessed
    panel(m, (u + 0.5, 0, pw / 2 - 0.4), (0, 0, -1), UP, pw - 0.8, ph - 0.6, "sp_porta", tile=None)
    for side in (-1, 1):     # portal reveals
        wall(m, (u, side * pw / 2), (u + 0.5, side * pw / 2), 0, ph, "+v" if side < 0 else "-v", "sp_bugnato", (0.5, 2.0))
        wall(m, (u, side * (pw / 2 - 0.4)), (u + 0.5, side * (pw / 2 - 0.4)), 0, ph, "+v" if side < 0 else "-v", "sp_pietra", (0.5, 2.0))
    hquad(m, (u, -pw / 2, u + 0.5, pw / 2), ph - 0.6, "sp_pietra", down=True)
    # niches with statues of St Peter (south, viewer's right) and St Paul
    for side in (-1, 1):
        vc = side * 3.4
        panel(m, (u - 0.02, 0.9, vc + 0.6), (0, 0, -1), UP, 1.2, 3.2, "sp_nicchia", tile=None)
        st = G.cylinder(0.32, 0.26, 2.2, "sp_marmo", n=8, base=(u - 0.35, 1.1, vc))
        st.merge(G.ellipsoid(0.16, 0.2, 0.16, "sp_marmo", n=8, rings=4, center=(u - 0.35, 3.48, vc)))
        st.merge(G.box(0.8, 0.3, 0.5, "sp_pietra", center=(u - 0.3, 0.8, vc)))
        m.merge(st)
    # cornice at 8 m
    panel(m, (u - 0.15, 8.0, fh + 0.15), (0, 0, -1), UP, 2 * fh + 0.3, 0.5, "sp_cornice", tile=(2.0, 0.5))
    hquad(m, (u - 0.15, -fh - 0.15, u, fh + 0.15), 8.5, "sp_pietra")
    # smooth upper wall 8.5 -> 16 m with the oculus (diameter 4 m, centre 12 m)
    wall(m, (u, -fh), (u, -2.0), 8.5, 16.0, "-u", "sp_pietra")
    wall(m, (u, 2.0), (u, fh), 8.5, 16.0, "-u", "sp_pietra")
    wall(m, (u, -2.0), (u, 2.0), 8.5, 10.0, "-u", "sp_pietra", (2.0, 1.5))
    wall(m, (u, -2.0), (u, 2.0), 14.0, 16.0, "-u", "sp_pietra")
    panel(m, (u - 0.02, 10.0, 2.0), (0, 0, -1), UP, 4.0, 4.0, "sp_oculo", tile=None)
    # cornice at 16 m, frieze with AVE MARIA, triangular pediment up to APEX
    panel(m, (u - 0.15, 16.0, fh + 0.15), (0, 0, -1), UP, 2 * fh + 0.3, 0.5, "sp_cornice", tile=(2.0, 0.5))
    panel(m, (u - 0.05, 16.5, 3.0), (0, 0, -1), UP, 6.0, 1.1, "sp_fregio", tile=None)
    wall(m, (u, -fh), (u, -3.0), 16.5, 17.6, "-u", "sp_pietra", (2.0, 1.1))
    wall(m, (u, 3.0), (u, fh), 16.5, 17.6, "-u", "sp_pietra", (2.0, 1.1))
    gable_end(m, u, fh + 0.2, 17.6, S.APEX, "-u", "sp_pietra")
    # pediment mouldings (raking cornices as thin slabs)
    for side in (-1, 1):
        a = P(u - 0.2, 17.6, side * (fh + 0.3))
        b = P(u - 0.2, S.APEX + 0.25, 0)
        c = P(u - 0.2, S.APEX + 0.6, 0)
        d = P(u - 0.2, 17.95, side * (fh + 0.3))
        q = [a, b, c, d] if side < 0 else [b, a, d, c]
        m.face(q, "sp_cornice", uv=[(0, 1), (1, 1), (1, 0), (0, 0)])
    # sides of the projecting body and its top behind the pediment
    for side in (-1, 1):
        wall(m, (u, side * fh), (0, side * fh), 0, 17.6, "-v" if side < 0 else "+v", "sp_pietra", (pr, 2.0))
    # roof slopes behind the pediment (blue), meeting the nave roof
    gable(m, u, 0.6, fh + 0.2, 17.6, S.APEX, "sp_tegole", axis="u", over=0.0)
    # small iron cross on the apex
    m.merge(G.box(0.12, 1.6, 0.12, "iron", center=(u + 0.2, S.APEX + 0.5, 0)))
    m.merge(G.box(0.12, 0.12, 0.9, "iron", center=(u + 0.2, S.APEX + 1.6, 0)))
    return m, box_coll(-pr, 0.3, -fh, fh, 0, S.APEX)


# ---------------------------------------------------------------------------------------- towers
def tower(clock):
    m = G.Mesh()
    t, hw = S.TOWER, S.HALF_W
    v0, v1 = (hw - t, hw) if clock else (-hw, -hw + t)
    u0, u1 = 0.0, t
    eps = 0.05
    u0e, u1e, v0e, v1e = u0 - eps, u1 + eps, v0 - eps, v1 + eps
    faces = [((u0e, v0e), (u0e, v1e), "-u"), ((u1e, v0e), (u1e, v1e), "+u"),
             ((u0e, v0e), (u1e, v0e), "-v"), ((u0e, v1e), (u1e, v1e), "+v")]
    for a, b, f in faces:
        # first order: rusticated base to 8 m, then smooth with simple frames
        wall(m, a, b, -0.0, 8.0, f, "sp_bugnato", (t / 3, 2.0))
        wall(m, a, b, 8.0, 14.0, f, "sp_pietra", (t / 3, 2.0))
        wall(m, a, b, 14.0, 15.6, f, "sp_pietra", (t / 3, 1.6))
        wall(m, a, b, 18.4, 20.0, f, "sp_pietra", (t / 3, 1.6))
        # middle order: eight-pointed star medallion (1.6 m) centred at 17 m
        r = np.array(RIGHT[f], float)
        pa, pb = np.array([a[0], 0, a[1]]), np.array([b[0], 0, b[1]])
        left = pa if np.dot(pb - pa, r) > 0 else pb
        n_out = {"+v": (0, 0, 1), "-v": (0, 0, -1), "+u": (1, 0, 0), "-u": (-1, 0, 0)}[f]
        o = left + r * 0.0 + np.array(n_out) * 0.0
        wall(m, a, b, 15.6, 18.4, f, "sp_pietra", (t / 3, 2.8))
        panel(m, o + r * (t / 2 - 1.0) + np.array([0, 16.0, 0]) + np.array(n_out) * 0.02, r, UP, 2.0, 2.0, "sp_stella", tile=None)
        # bell chamber 20 -> 26 m: monofore (right tower) or clock + small bell frame (left tower)
        if clock:
            wall(m, a, b, 20.0, 26.0, f, "sp_pietra", (t / 3, 2.0))
            panel(m, o + r * (t / 2 - 1.1) + np.array([0, 21.6, 0]) + np.array(n_out) * 0.02, r, UP, 2.2, 2.2, "sp_orologio", tile=None)
        else:
            wall(m, a, b, 20.0, 21.0, f, "sp_pietra", (t / 3, 1.0))
            wall(m, a, b, 25.0, 26.0, f, "sp_pietra", (t / 3, 1.0))
            wall(m, a, b, 21.0, 25.0, f, "sp_pietra", (1.5, 4.0))
            panel(m, o + r * (t / 2 - 0.8) + np.array([0, 21.0, 0]) + np.array(n_out) * 0.02, r, UP, 1.6, 3.6, "sp_monofora", tile=None)
        # cornices at 14 and 26 m
        for y in (14.0, 26.0):
            panel(m, o - r * 0.15 + np.array([0, y - 0.25, 0]) + np.array(n_out) * 0.15, r, UP, t + 0.3, 0.5, "sp_cornice", tile=(t + 0.3, 0.5))
    # square pinnacle (pyramid) from 26 to TOWER_H, with a cross
    top = P((u0 + u1) / 2, S.TOWER_H, (v0 + v1) / 2)
    c = [P(u0 - 0.2, 26.0, v0 - 0.2), P(u1 + 0.2, 26.0, v0 - 0.2), P(u1 + 0.2, 26.0, v1 + 0.2), P(u0 - 0.2, 26.0, v1 + 0.2)]
    for i in range(4):
        m.face([c[(i + 1) % 4], c[i], top], "sp_pietra", uv=[(1, 1), (0, 1), (0.5, 0)])
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
    m.merge(G.box(0.12, 1.8, 0.12, "iron", center=(cu, S.TOWER_H, cv)))
    m.merge(G.box(0.12, 0.12, 1.0, "iron", center=(cu, S.TOWER_H + 1.3, cv)))
    if clock:   # the small outer bell frame on top of the cornice, towards the square
        fu = u0 + 0.6
        for dv in (-0.8, 0.8):
            m.merge(G.box(0.3, 2.0, 0.3, "sp_pietra", center=(fu, 26.0, cv + dv)))
        m.merge(G.box(0.4, 0.3, 2.0, "sp_pietra", center=(fu, 28.0, cv)))
        m.merge(G.cylinder(0.35, 0.22, 0.6, "sp_porta", n=8, base=(fu, 27.0, cv)))   # bronze bell
    return m, box_coll(u0, u1, v0, v1, 0, 26.0)


@piece(151, "SANTUARIO_CAMPANILE_SX", (S.TOWER / 2, S.HALF_W - S.TOWER / 2), "Campanile sinistro (nord): orologio nell'oculo cieco e piccola cella esterna")
def campanile_sx():
    return tower(clock=True)


@piece(152, "SANTUARIO_CAMPANILE_DX", (S.TOWER / 2, -S.HALF_W + S.TOWER / 2), "Campanile destro (sud): monofore alla cella campanaria")
def campanile_dx():
    return tower(clock=False)


# ---------------------------------------------------------------------------------------- nave walls
def side_wall(m, u0, u1, v, facing, h=S.EAVES, windows=True, bay=6.0):
    """Long wall: rusticated plinth 1.5 m, smooth stone, tall stained-glass windows every bay, cornice."""
    wall(m, (u0, v), (u1, v), 0, 1.5, facing, "sp_bugnato", (2.0, 1.5))
    wall(m, (u0, v), (u1, v), 1.5, h - 0.5, facing, "sp_pietra")
    r = np.array(RIGHT[facing], float)
    n_out = {"+v": (0, 0, 1), "-v": (0, 0, -1), "+u": (1, 0, 0), "-u": (-1, 0, 0)}[facing]
    pa, pb = np.array([u0, 0, v]), np.array([u1, 0, v])
    left = pa if np.dot(pb - pa, r) > 0 else pb
    length = abs(u1 - u0)
    if windows:
        k = int(length // bay)
        for i in range(k):
            c = (i + 0.5) * length / k
            panel(m, left + r * (c - 1.0) + np.array([0, 4.5, 0]) + np.array(n_out) * 0.02, r, UP, 2.0, 7.0, "sp_finestra", tile=None)
    panel(m, left - r * 0.15 + np.array([0, h - 0.5, 0]) + np.array(n_out) * 0.15, r, UP, length + 0.3, 0.5, "sp_cornice", tile=(2.0, 0.5))
    # plinth / skirt below the floor: the stone base of the platform on the cliff
    wall(m, (u0, v), (u1, v), -S.SKIRT, 0, facing, "sp_bugnato")


@piece(153, "SANTUARIO_NAVATA_NORD", (36.0, S.HALF_W), "Fianco nord della navata (verso la loggia)")
def navata_nord():
    m = G.Mesh()
    side_wall(m, S.TOWER, S.NAVE_END, S.HALF_W, "+v")
    return m, box_coll(S.TOWER, S.NAVE_END, S.HALF_W - 0.8, S.HALF_W, 0, S.EAVES)


@piece(154, "SANTUARIO_NAVATA_SUD", (23.0, -S.HALF_W), "Fianco sud della navata fino al transetto")
def navata_sud():
    m = G.Mesh()
    side_wall(m, S.TOWER, S.TRANSEPT[0], -S.HALF_W, "-v")
    return m, box_coll(S.TOWER, S.TRANSEPT[0], -S.HALF_W, -S.HALF_W + 0.8, 0, S.EAVES)


@piece(155, "SANTUARIO_TRANSETTO", (46.0, -12.7), "Braccio sud del transetto")
def transetto():
    m = G.Mesh()
    u0, u1, vs = S.TRANSEPT
    side_wall(m, u0, u1, vs, "-v", bay=4.0)
    for u, f in ((u0, "-u"), (u1, "+u")):
        wall(m, (u, vs), (u, -S.HALF_W), 0, 1.5, f, "sp_bugnato", (2.1, 1.5))
        wall(m, (u, vs), (u, -S.HALF_W), 1.5, S.EAVES, f, "sp_pietra", (2.1, 2.0))
        wall(m, (u, vs), (u, -S.HALF_W), -S.SKIRT, 0, f, "sp_bugnato", (2.1, 2.0))
    # gable end of the transept roof
    gable_end(m, vs, (u1 - u0) / 2 + 0.3, S.EAVES, S.RIDGE, "-v", "sp_pietra", centre=(u0 + u1) / 2, axis="v")
    return m, box_coll(u0, u1, vs, -S.HALF_W, 0, S.EAVES)


@piece(156, "SANTUARIO_NAVATA_SUD_EST", (59.0, -S.HALF_W), "Fianco sud dopo il transetto")
def navata_sud_est():
    m = G.Mesh()
    side_wall(m, S.TRANSEPT[1], S.NAVE_END, -S.HALF_W, "-v")
    return m, box_coll(S.TRANSEPT[1], S.NAVE_END, -S.HALF_W, -S.HALF_W + 0.8, 0, S.EAVES)


@piece(157, "SANTUARIO_ABSIDE", (S.NAVE_END, 0.0), "Testata est con abside semicircolare e tetto a semicono")
def abside():
    m = G.Mesh()
    ue, r = S.NAVE_END, S.APSE_R
    for side in (-1, 1):   # east wall pieces beside the apse
        a, b = (ue, side * r), (ue, side * S.HALF_W)
        wall(m, a, b, 0, S.EAVES, "+u", "sp_pietra", (1.8, 2.0))
        wall(m, a, b, -S.SKIRT, 0, "+u", "sp_bugnato", (1.8, 2.0))
    # gable of the nave on the east wall above the apse roof
    gable_end(m, ue, S.HALF_W + 0.6, S.EAVES, S.RIDGE, "+u", "sp_pietra")
    n = 12
    pts = [(ue + r * math.cos(-math.pi / 2 + math.pi * k / n), r * math.sin(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
    for k in range(n):
        (ua, va), (ub, vb) = pts[k], pts[k + 1]
        # outward normal of this segment: the facing names are only used for the viewer's right
        ang = math.atan2((va + vb) / 2, (ua + ub) / 2 - ue)
        rvec = np.array([math.sin(ang), 0, -math.cos(ang)])          # viewer's right on a curved wall
        left = np.array([ua, 0, va]) if np.dot(np.array([ub - ua, 0, vb - va]), rvec) > 0 else np.array([ub, 0, vb])
        w = math.hypot(ub - ua, vb - va)
        panel(m, left + np.array([0, -S.SKIRT, 0]), rvec, UP, w, S.SKIRT, "sp_bugnato", (w, 2.0))
        panel(m, left, rvec, UP, w, 1.5, "sp_bugnato", (w, 1.5))
        panel(m, left + np.array([0, 1.5, 0]), rvec, UP, w, S.APSE_H - 1.5, "sp_pietra", (w, 2.1))
        if k % 3 == 1:
            panel(m, left + rvec * (w / 2 - 0.6) + np.array([0, 5.0, 0]) + np.array([math.cos(ang), 0, math.sin(ang)]) * 0.02,
                  rvec, UP, 1.2, 4.0, "sp_finestra", tile=None)
        # half-cone roof segment
        top = P(ue, S.APSE_H + 3.0, 0)
        e1 = P(ue + (r + 0.5) * math.cos(-math.pi / 2 + math.pi * k / n), S.APSE_H, (r + 0.5) * math.sin(-math.pi / 2 + math.pi * k / n))
        e2 = P(ue + (r + 0.5) * math.cos(-math.pi / 2 + math.pi * (k + 1) / n), S.APSE_H, (r + 0.5) * math.sin(-math.pi / 2 + math.pi * (k + 1) / n))
        m.face([e2, e1, top], "sp_tegole", uv=[(1, 1), (0, 1), (0.5, 0)])
    return m, box_coll(ue, ue + r, -r, r, 0, S.APSE_H)


# ---------------------------------------------------------------------------------------- roofs
@piece(158, "SANTUARIO_TETTO", (33.0, 0.0), "Tetto della navata in ceramica azzurra")
def tetto():
    m = G.Mesh()
    gable(m, 0.3, S.NAVE_END + 0.6, S.HALF_W, S.EAVES, S.RIDGE, "sp_tegole", axis="u", over=0.7)
    # tower-facing gable wall above the facade (between the towers, hidden mostly by the pediment)
    gable_end(m, 0.3, S.HALF_W + 0.7, S.EAVES, S.RIDGE, "-u", "sp_pietra")
    return m, None


@piece(159, "SANTUARIO_CUPOLA", (S.CROSSING_U, 0.0), "Tetto del transetto e cupola sull'incrocio")
def cupola():
    m = G.Mesh()
    u0, u1, vs = S.TRANSEPT
    hu = (u1 - u0) / 2
    gable(m, vs - 0.7, 0.0, hu, S.EAVES, S.RIDGE, "sp_tegole", axis="v", over=0.6, centre=S.CROSSING_U)
    # octagonal drum and dome over the crossing
    n, rr = 8, 5.0
    y0, y1 = S.RIDGE - 1.0, S.RIDGE + 2.8
    ring = [(S.CROSSING_U + rr * math.cos(2 * math.pi * k / n + math.pi / 8), rr * math.sin(2 * math.pi * k / n + math.pi / 8)) for k in range(n)]
    for k in range(n):
        (ua, va), (ub, vb) = ring[k], ring[(k + 1) % n]
        ang = math.atan2((va + vb) / 2, (ua + ub) / 2 - S.CROSSING_U)
        rvec = np.array([math.sin(ang), 0, -math.cos(ang)])
        left = np.array([ua, 0, va]) if np.dot(np.array([ub - ua, 0, vb - va]), rvec) > 0 else np.array([ub, 0, vb])
        w = math.hypot(ub - ua, vb - va)
        panel(m, left + np.array([0, y0, 0]), rvec, UP, w, y1 - y0, "sp_pietra", (w / 2, y1 - y0))
        panel(m, left + rvec * (w / 2 - 0.5) + np.array([0, y0 + 0.6, 0]) + np.array([math.cos(ang), 0, math.sin(ang)]) * 0.02,
              rvec, UP, 1.0, 2.2, "sp_finestra", tile=None)
    # dome: 4 rings of tiles
    rings = 4
    prev = [(u, y1, v) for u, v in ring]
    for j in range(1, rings + 1):
        t = j / rings
        rad = rr * math.cos(t * math.pi / 2)
        y = y1 + 5.0 * math.sin(t * math.pi / 2)
        cur = [(S.CROSSING_U + (u - S.CROSSING_U) * rad / rr, y, v * rad / rr) for u, v in ring]
        for k in range(n):
            a, b = prev[k], prev[(k + 1) % n]
            c, d = cur[(k + 1) % n], cur[k]
            if j < rings:
                m.face([P(*d), P(*c), P(*b), P(*a)], "sp_tegole")
            else:
                m.face([P(*c), P(*b), P(*a)], "sp_tegole", uv=[(0.5, 0), (1, 1), (0, 1)])
        prev = cur
    # lantern
    m.merge(G.cylinder(0.9, 0.9, 1.6, "sp_pietra", n=8, base=(S.CROSSING_U, y1 + 4.8, 0), cap="sp_tegole"))
    m.merge(G.box(0.12, 1.6, 0.12, "iron", center=(S.CROSSING_U, y1 + 6.4, 0)))
    m.merge(G.box(0.12, 0.12, 0.9, "iron", center=(S.CROSSING_U, y1 + 7.5, 0)))
    return m, None


# ---------------------------------------------------------------------------------------- loggia
BAY = 4.75


def loggia_piece(u0, u1):
    """Arcade on the outer edge of the loggia, balustrade between the piers, lean-to roof."""
    m = G.Mesh()
    v_out = S.LOGGIA[3] - 0.3
    k = int(round((u1 - u0) / BAY))
    for i in range(k):
        a = u0 + (u1 - u0) * i / k
        b = u0 + (u1 - u0) * (i + 1) / k
        # arch face, double-sided alpha (seen from the lagoons and from inside the loggia)
        panel(m, (b, 0, v_out), (-1, 0, 0), UP, b - a, 5.5, "sp_arcata", tile=None)
        m.f[-1] = m.f[-1][:3] + (1, True)
        # balustrade between the piers
        panel(m, (b - 0.45, 0, v_out - 0.05), (-1, 0, 0), UP, b - a - 0.9, 1.0, "sp_balaustra", tile=(2.0, 1.0))
        for q in range(len(m.f) - max(1, int(round((b - a - 0.9) / 2.0))), len(m.f)):
            m.f[q] = m.f[q][:3] + (1, True)
    # roof slab from the nave wall (5.8 m) down to the arcade (5.5 m), blue tiles; ceiling below
    for i in range(int(round((u1 - u0) / 2.0))):
        a, b = u0 + 2.0 * i, min(u1, u0 + 2.0 * (i + 1))
        for j in range(4):
            c0, c1 = S.HALF_W + 2.0 * j, S.HALF_W + 2.0 * (j + 1)
            ya, yb = 6.3 - 0.2 * j, 6.3 - 0.2 * (j + 1)
            m.face([P(a, yb, c1), P(b, yb, c1), P(b, ya, c0), P(a, ya, c0)], "sp_tegole")
            m.face([P(a, ya - 0.3, c0), P(b, ya - 0.3, c0), P(b, yb - 0.3, c1), P(a, yb - 0.3, c1)], "sp_pietra")
    # fascia on top of the arcade
    panel(m, (u1, 5.5, v_out + 0.05), (-1, 0, 0), UP, u1 - u0, 0.5, "sp_cornice", tile=(2.0, 0.5))
    # outer stone base of the terrace down to the rock, and a ledge that hides the sector grid
    wall(m, (u0, S.LOGGIA[3] + 1.5), (u1, S.LOGGIA[3] + 1.5), -S.SKIRT, -0.02, "+v", "sp_bugnato")
    hquad(m, (u0, v_out, u1, S.LOGGIA[3] + 1.5), 0.02, "sp_pietra")
    return m


def loggia_columns(u0, u1):
    """Piers of the arcade (solid): a separate static each, so each one gets its collision box."""
    return [u0 + (u1 - u0) * i / int(round((u1 - u0) / BAY)) for i in range(int(round((u1 - u0) / BAY)) + 1)]


_L = [(S.LOGGIA[0] + 19.0 * i, S.LOGGIA[0] + 19.0 * (i + 1)) for i in range(4)]
for _i, (_a, _b) in enumerate(_L):
    def _mk(a=_a, b=_b):
        m = loggia_piece(a, b)
        v_out = S.LOGGIA[3] - 0.3
        # the balustrade line is solid (1 m) along the whole piece
        return m, box_coll(a, b, v_out - 0.25, v_out + 0.25, 0, 1.1)
    piece(160 + _i, "SANTUARIO_LOGGIA_%d" % (_i + 1), ((_a + _b) / 2, S.LOGGIA[3] - 0.3),
          "Loggia nord (76 x 8 m) sui laghetti, tratto %d di 4" % (_i + 1))(_mk)


@piece(164, "SANTUARIO_PILASTRO", (0.0, 0.0), "Pilastro della loggia (con collisione), piazzato a ogni campata")
def pilastro():
    m = G.box(0.7, 5.5, 0.7, "sp_pietra")
    m.merge(G.box(0.9, 0.35, 0.9, "sp_pietra", center=(0, 5.15, 0)))
    m.merge(G.box(0.9, 0.3, 0.9, "sp_pietra"))
    return m, box_coll(-0.35, 0.35, -0.35, 0.35, 0, 5.5)


PIERS = [(u, S.LOGGIA[3] - 0.3) for a, b in _L for u in loggia_columns(a, b)]


# ---------------------------------------------------------------------------------------- old sanctuary
@piece(165, "SANTUARIO_ANTICO", ((S.OLD[0] + S.OLD[1]) / 2, (S.OLD[2] + S.OLD[3]) / 2),
       "Santuario antico (1552-1598): intonaco, portale con chiave datata 1598, campanile a vela, tetto in coppi")
def antico():
    m = G.Mesh()
    u0, u1, v0, v1 = S.OLD
    h = S.OLD_H
    for a, b, f in (((u0, v0), (u1, v0), "-v"), ((u1, v0), (u1, v1), "+u"), ((u0, v1), (u1, v1), "+v")):
        wall(m, a, b, 0, h, f, "sp_intonaco")
        wall(m, a, b, -S.SKIRT, 0, f, "sp_bugnato")
    wall(m, (u0, v0), (u0, v1), h - 2.0, h, "-u", "sp_intonaco")   # above the apse of the new church
    # portal on the south side (towards the sea terrace) and two small windows
    uc = (u0 + u1) / 2
    panel(m, (uc - 1.2, 0, v0 - 0.03), (1, 0, 0), UP, 2.4, 4.8, "vs_portale", tile=None)
    for du in (-3.6, 3.6):
        panel(m, (uc + du - 0.5, 4.8, v0 - 0.03), (1, 0, 0), UP, 1.0, 1.6, "sp_finestra", tile=None)
    # hipped roof in coppi
    top0, top1 = P(u0 + 3.0, h + 3.0, (v0 + v1) / 2), P(u1 - 3.0, h + 3.0, (v0 + v1) / 2)
    e = [P(u0 - 0.4, h, v0 - 0.4), P(u1 + 0.4, h, v0 - 0.4), P(u1 + 0.4, h, v1 + 0.4), P(u0 - 0.4, h, v1 + 0.4)]
    m.face([e[1], e[0], top0, top1], "sp_coppi")
    m.face([e[3], e[2], top1, top0], "sp_coppi")
    m.face([e[0], e[3], top0], "sp_coppi", uv=[(0, 1), (1, 1), (0.5, 0)])
    m.face([e[2], e[1], top1], "sp_coppi", uv=[(0, 1), (1, 1), (0.5, 0)])
    # bell gable (campanile a vela) on the south wall, one bell
    gu, gv = u1 - 2.5, v0
    wall(m, (gu - 1.4, gv), (gu + 1.4, gv), h, h + 3.6, "-v", "sp_intonaco", (2.8, 3.6))
    wall(m, (gu - 1.4, gv + 0.5), (gu + 1.4, gv + 0.5), h, h + 3.6, "+v", "sp_intonaco", (2.8, 3.6))
    panel(m, (gu - 0.7, h + 0.9, gv - 0.02), (1, 0, 0), UP, 1.4, 2.4, "sp_monofora", tile=None)
    return m, box_coll(u0, u1, v0, v1, 0, h)


# ---------------------------------------------------------------------------------------- base
@piece(166, "SANTUARIO_BASAMENTO", (20.0, 0.0), "Basamento in pietra sotto la facciata e i campanili (fino alla roccia)")
def basamento():
    m = G.Mesh()
    fh, pr, hw = S.FACADE_HALF, S.FACADE_PROJ, S.HALF_W
    wall(m, (-pr, -fh), (-pr, fh), -S.SKIRT, 0, "-u", "sp_bugnato")
    wall(m, (0, -hw), (0, -fh), -S.SKIRT, 0, "-u", "sp_bugnato")
    wall(m, (0, fh), (0, hw), -S.SKIRT, 0, "-u", "sp_bugnato")
    wall(m, (0, -hw), (S.TOWER, -hw), -S.SKIRT, 0, "-v", "sp_bugnato")
    return m, None
