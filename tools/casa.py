"""Ed's house, Via Gaspare Amodeo 1, Oliveri: footprint and shared geometry (pure, no world needed).

Footprint: OpenStreetMap way 233746690, in world sectors of the Oliveri level. The house is rotated
about 44 degrees to the sector grid, so the outside is a static skin (decor/casa_models.py) over solid
blocks made of the sectors that lie entirely inside the footprint; the rooms are separate interiors
(content_oliveri.house) reached through the floors' stairs, and the roof hatch leads onto the real roof.
"""
import math

POLY = [(217.61, 159.32), (216.21, 160.66), (212.05, 164.63), (207.91, 160.61), (214.82, 155.80)]
ANCHOR = (212.8, 160.2)          # sectors; static anchor (centroid, rounded)
GROUND = 1344                    # street level at the door (units, 2.625 m)
ROOF = 6208                      # roof terrace (units, 12.125 m)
HEIGHT_M = (ROOF - GROUND) / 512.0
STREET_EDGE = (3, 4)             # P4 -> P5: the facade on Via Amodeo (portone, balcony)


def inside(u, v, poly=POLY):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > v) != (y2 > v) and u < (x2 - x1) * (v - y1) / (y2 - y1) + x1:
            c = not c
    return c


def full_sectors():
    xs = [p[0] for p in POLY]
    zs = [p[1] for p in POLY]
    out = set()
    for x in range(int(min(xs)), int(max(xs)) + 1):
        for z in range(int(min(zs)), int(max(zs)) + 1):
            if all(inside(x + dx, z + dz) for dx, dz in ((0, 0), (1, 0), (1, 1), (0, 1))):
                out.add((x, z))
    return out


def _line_z(x):
    (x0, z0), (x1, z1) = POLY[STREET_EDGE[0]], POLY[STREET_EDGE[1]]
    return z0 + (z1 - z0) * (x - x0) / (x1 - x0)


def climb_spot():
    """Street sector (x, z) whose +z face (a block sector) is closest to the Via Amodeo facade, away from
    the street door: Lara climbs down there along the drainpipe. Returns (x, z, gap_sectors)."""
    full = full_sectors()
    best = None
    for (x, z) in full:
        if (x, z - 1) in full:
            continue
        if x > 212:          # keep it at the western end, the door is in the middle
            continue
        gap = z - _line_z(x + 0.5)
        if best is None or gap < best[2]:
            best = (x, z - 1, gap)
    return best


def to_m(x, z):
    """World sectors -> metres relative to the static anchor (mesh X east, Z north)."""
    return ((x - ANCHOR[0]) * 2.0, (z - ANCHOR[1]) * 2.0)


def roof_spot():
    """A roof sector near the north corner for the arrival from the hatch."""
    full = sorted(full_sectors(), key=lambda c: math.dist((c[0] + 0.5, c[1] + 0.5), (212.0, 161.5)))
    return full[0]
