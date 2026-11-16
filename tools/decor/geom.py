"""Tiny low-poly modelling kit for TombEngine statics.

Units: Tomb Editor units, 512 = 1 m; +Y up, +Z forward (north), origin at the base centre.
A Mesh keeps vertices and faces; each face has 3 or 4 vertex indices, per-corner pixel UVs on a
texture page, a blend mode (0 normal, 1 alpha test) and a double-sided flag.
"""
import math

import numpy as np

from decor.tex import REG

M = 512.0


class Mesh:
    def __init__(self):
        self.v = []          # [x, y, z]
        self.f = []          # (idx tuple, uv list, page, blend, double)

    def add_vertex(self, p):
        self.v.append([float(p[0]), float(p[1]), float(p[2])])
        return len(self.v) - 1

    def face(self, pts, region, uv=None, blend=0, double=False):
        """pts: 3 or 4 points (counter-clockwise seen from the front). uv: per corner in [0, 1] of the region."""
        page, x0, y0, x1, y1 = REG[region]
        if uv is None:
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)][:len(pts)]
        # TombLib winding: cross(b - a, c - a) points out of the front face, i.e. the reverse of the
        # clockwise order used by the helpers here; flip once at the end.
        pts = list(pts)[::-1]
        uv = list(uv)[::-1]
        idx = tuple(self.add_vertex(p) for p in pts)
        px = [(x0 + 0.5 + u * (x1 - x0 - 1), y0 + 0.5 + v * (y1 - y0 - 1)) for u, v in uv]
        self.f.append((idx, px, page, blend, double))

    def merge(self, other, transform=None):
        base = len(self.v)
        for p in other.v:
            q = transform(p) if transform else p
            self.v.append(list(q))
        for idx, px, page, blend, dbl in other.f:
            self.f.append((tuple(i + base for i in idx), px, page, blend, dbl))
        return self

    def transformed(self, s=(1, 1, 1), ry=0.0, rx=0.0, rz=0.0, t=(0, 0, 0)):
        out = Mesh()
        out.f = list(self.f)
        R = rot(rx, ry, rz)
        for p in self.v:
            q = R @ (np.array(p) * np.array(s, float))
            out.v.append(list(q + np.array(t, float)))
        return out

    def bbox(self):
        a = np.array(self.v)
        return a.min(axis=0), a.max(axis=0)


def grounded(m, sink=0.01):
    """The mesh moved up or down so that its lowest point is `sink` metres under its origin: a thing that lies on the
    ground touches it (models built by tilting or stacking parts easily end up hovering)."""
    lo = min(p[1] for p in m.v)
    return m.transformed(t=(0, -lo - sink * M, 0))


def rot(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


# ---------------------------------------------------------------------------------- primitives
def box(w, h, d, region, top=None, center=(0, 0, 0), sides=None, bottom=False):
    """Axis aligned box, base at y = center.y. Units in metres."""
    m = Mesh()
    cx, cy, cz = (c * M for c in center)
    x0, x1 = cx - w * M / 2, cx + w * M / 2
    z0, z1 = cz - d * M / 2, cz + d * M / 2
    y0, y1 = cy, cy + h * M
    reg = sides or region
    m.face([(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)], reg)     # +z
    m.face([(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)], reg)     # -z
    m.face([(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)], reg)     # +x
    m.face([(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)], reg)     # -x
    m.face([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], top or region)
    if bottom:
        m.face([(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)], region)
    return m


def cylinder(r0, r1, h, region, n=8, base=(0, 0, 0), cap=None, axis="y", top_cap=True, bend=(0, 0)):
    """Frustum along +Y (radii in m). bend = (dx, dz) offset of the top in m (leaning trunks)."""
    m = Mesh()
    bx, by, bz = (c * M for c in base)
    pts0, pts1 = [], []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        pts0.append((bx + math.cos(a) * r0 * M, by, bz + math.sin(a) * r0 * M))
        pts1.append((bx + bend[0] * M + math.cos(a) * r1 * M, by + h * M, bz + bend[1] * M + math.sin(a) * r1 * M))
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        m.face([pts1[i + 1], pts1[i], pts0[i], pts0[i + 1]], region, uv=[(u1, 0), (u0, 0), (u0, 1), (u1, 1)])
    if top_cap and r1 > 0:
        c = (bx + bend[0] * M, by + h * M, bz + bend[1] * M)
        for i in range(n):
            m.face([pts1[i], pts1[i + 1], c], cap or region, uv=[(0, 0), (1, 0), (0.5, 1)])
    return m


def tube(points, radii, region, n=6):
    """Generalised cylinder along a polyline (metres): trunks and branches."""
    m = Mesh()
    P = [np.array(p, float) * M for p in points]
    rings = []
    for k, p in enumerate(P):
        d = P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]
        d /= np.linalg.norm(d) + 1e-9
        a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
        u = np.cross(d, a)
        u /= np.linalg.norm(u)
        w = np.cross(d, u)
        r = radii[k] * M
        rings.append([p + (math.cos(2 * math.pi * i / n) * u + math.sin(2 * math.pi * i / n) * w) * r for i in range(n + 1)])
    for k in range(len(P) - 1):
        v0, v1 = k / (len(P) - 1), (k + 1) / (len(P) - 1)
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            m.face([rings[k + 1][i], rings[k + 1][i + 1], rings[k][i + 1], rings[k][i]], region,
                   uv=[(u0, 1 - v1), (u1, 1 - v1), (u1, 1 - v0), (u0, 1 - v0)])
    return m


def ellipsoid(rx, ry, rz, region, n=8, rings=5, center=(0, 0, 0), squash_bottom=1.0):
    m = Mesh()
    c = np.array(center, float) * M
    grid = []
    for j in range(rings + 1):
        t = math.pi * j / rings
        row = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            y = math.cos(t) * ry * (1 if j <= rings / 2 else squash_bottom)
            row.append(c + np.array([math.sin(t) * math.cos(a) * rx, y, math.sin(t) * math.sin(a) * rz]) * M)
        grid.append(row)
    for j in range(rings):
        for i in range(n):
            u0, u1, v0, v1 = i / n, (i + 1) / n, j / rings, (j + 1) / rings
            m.face([grid[j][i + 1], grid[j][i], grid[j + 1][i], grid[j + 1][i + 1]], region,
                   uv=[(u1, v0), (u0, v0), (u0, v1), (u1, v1)])
    return m


def card(w, h, region, center=(0, 0, 0), ry=0.0, blend=1, tilt=0.0):
    """Vertical double-sided alpha card, base at center.y."""
    m = Mesh()
    hw = w * M / 2
    pts = [(-hw, h * M, 0), (hw, h * M, 0), (hw, 0, 0), (-hw, 0, 0)]
    R = rot(tilt, ry, 0)
    c = np.array(center, float) * M
    pts = [R @ np.array(p) + c for p in pts]
    m.face(pts, region, blend=blend, double=True)
    return m


def cross_cards(w, h, region, count=3, center=(0, 0, 0), rng=None, blend=1):
    m = Mesh()
    off = rng.uniform(0, math.pi) if rng is not None else 0.0
    for k in range(count):
        m.merge(card(w, h, region, center=center, ry=off + math.pi * k / count, blend=blend))
    return m


def hcard(w, d, region, center=(0, 0, 0), ry=0.0, tilt=0.0, blend=1):
    """Horizontal (canopy) card, slightly tilted."""
    m = Mesh()
    hw, hd = w * M / 2, d * M / 2
    pts = [(-hw, 0, hd), (hw, 0, hd), (hw, 0, -hd), (-hw, 0, -hd)]
    R = rot(tilt, ry, 0)
    c = np.array(center, float) * M
    m.face([R @ np.array(p) + c for p in pts], region, blend=blend, double=True)
    return m


def quad(p0, p1, p2, p3, region, uv=None, blend=0, double=False):
    m = Mesh()
    m.face([np.array(p, float) * M for p in (p0, p1, p2, p3)], region, uv=uv, blend=blend, double=double)
    return m


def disc(r, region, center=(0, 0, 0), n=12, ry=0.0, tilt=0.0, double=True, cone=0.0):
    """Flat (or conical, cone = rise of the centre in m) disc: umbrellas, wheels."""
    m = Mesh()
    c = np.array(center, float) * M
    R = rot(tilt, ry, 0)
    top = R @ np.array([0, cone * M, 0]) + c
    ring = [R @ np.array([math.cos(2 * math.pi * i / n) * r * M, 0, math.sin(2 * math.pi * i / n) * r * M]) + c for i in range(n + 1)]
    for i in range(n):
        m.face([ring[i + 1], ring[i], top], region, uv=[(i / n, 1), ((i + 1) / n, 1), (0.5, 0)], double=double)
    return m


def wheel(r, width, center, ry=0.0, n=10, region="tyre"):
    """Wheel with its axle along X (before ry)."""
    m = cylinder(r, r, width, region, n=n, base=(0, -width / 2, 0))
    # bottom cap
    m.merge(disc(r, region, center=(0, -width / 2, 0), n=n))
    return m.transformed(rz=math.pi / 2, ry=ry, t=np.array(center) * M)
