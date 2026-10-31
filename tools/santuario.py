"""Basilica Santuario di Maria Santissima del Tindari: real layout on the Tindari promontory (v2).

Sources:
- OpenStreetMap footprints (converted to the local frame below): way 156320182 (the church, with the
  low north wing and the tall north-east block), way 233937884 (the convent, L-shaped, with the old
  fortified sanctuary on the east cliff), way 233937885 (the terrace on the south side of the nave,
  roof of a lower building, curved edge along the road), way 233937915 (annex south of the transept),
  way 233937881 (Segreteria del Santuario, the long low building on the south-west side of the square).
- Ed's photos (29/10/2026) and Street View: pink ashlar facade-tower about 34 m with belfry and
  Madonna mosaic; side bays with arched doors under pediments; orange plaster sides with white
  pilasters, blind arches with blue oculi below and rectangular windows with oculi above; low grey
  roof; orange drum with arched windows, ring of oculi, golden tiled dome with railing and lantern.
Heights are estimates from the photos (people, doors and storeys as scale).

Local frame (metres): u along the nave towards the east end, v to the north, origin at the centre of
the facade line, y = 0 at the square / church floor (F).
"""
import math

import numpy as np

ORIGIN = (207.65, 217.9)           # facade centre, world sectors
AXIS_DEG = 13.44                   # static rotation: local +X (u) -> world east-south-east
A = (math.cos(math.radians(AXIS_DEG)), -math.sin(math.radians(AXIS_DEG)))
N = (math.sin(math.radians(AXIS_DEG)), math.cos(math.radians(AXIS_DEG)))

# ------------------------------------------------------------------ plan (OSM, local metres)
HALF_W = 10.6
NAVE_END = 74.1
TOWER_D = 8.0                      # depth of the facade tower
TOWER_HW = 4.8                     # half width of the tower (9.6 m)
TRANSEPT = (40.1, 51.7, -15.0)     # south arm: u0, u1, v of its south wall
CROSSING_U = 45.9

CHURCH = [(-0.1, -10.6), (8.9, -10.6), (40.1, -10.6), (40.1, -15.0), (51.7, -15.0), (51.8, -10.7),
          (74.1, -10.8), (73.1, 0.7), (78.7, 1.6), (78.5, 2.4), (79.7, 2.8), (79.7, 7.3), (85.9, 7.3),
          (85.9, 13.0), (53.7, 13.1), (53.7, 10.5), (2.1, 10.5), (0.0, 10.6)]
NAVE = [(0.0, -10.6), (74.1, -10.6), (74.1, 10.5), (0.0, 10.5)]
TRANSEPT_ARM = [(40.1, -15.0), (51.7, -15.0), (51.7, -10.6), (40.1, -10.6)]
NE_BLOCK = [(73.4, 0.7), (78.7, 1.6), (78.5, 2.4), (79.7, 2.8), (79.7, 7.3), (85.9, 7.3), (85.9, 13.0), (73.4, 13.05)]
NORTH_WING = [(53.7, 10.5), (73.4, 10.5), (73.4, 13.05), (53.7, 13.1)]
CONVENT = [(51.6, -23.3), (88.6, -23.5), (88.4, -13.3), (92.9, -12.6), (91.9, -9.0), (93.7, -8.7), (92.3, -3.4),
           (96.7, -1.9), (94.9, 4.3), (89.1, 2.7), (88.4, 4.6), (79.7, 2.8), (78.5, 2.4), (78.7, 1.6), (73.1, 0.7),
           (74.1, -10.8), (51.8, -10.7), (51.7, -15.0)]
TERRACE = [(39.8, -23.3), (40.1, -14.9), (40.1, -10.6), (8.9, -10.6), (11.4, -11.4), (13.8, -12.1), (16.2, -12.9),
           (18.6, -13.7), (21.1, -14.4), (23.5, -15.2), (24.8, -15.9), (26.2, -16.6), (27.5, -17.2), (29.1, -18.5),
           (30.6, -19.8), (31.1, -20.9), (31.5, -22.1), (32.0, -23.2), (33.5, -23.2)]
TERRACE_EDGE = TERRACE[3:] + [(39.8, -23.3)]          # outer edge, from the facade corner to the annex
ANNEX = [(39.8, -23.3), (51.6, -23.3), (51.7, -15.0), (40.1, -14.9)]
SEGRETERIA = [(-38.8, -2.9), (-33.7, -4.7), (-30.5, -5.8), (-27.3, -6.9), (-17.8, -10.2), (-14.6, -11.3),
              (-11.4, -12.4), (-8.2, -13.5), (-5.0, -14.6), (-6.6, -19.3), (-40.4, -7.6)]
SQUARE = (-30.0, -0.2, -22.0, 22.0)

# Heights above F (metres)
EAVES = 16.0          # nave cornice
RIDGE = 19.5          # grey nave roof
TOWER_H = 31.0        # tower attic top (pediment and statues up to about 35 m)
DOME_TOP = 44.0       # cross on the lantern
CONVENT_H = 12.0
NE_H = 18.0
WING_H = 5.0
ANNEX_H = 6.0
SEGRETERIA_H = 4.5
SKIRT = 16.0          # walls go this far below F (hidden by the terrain / the cliff)

# Solid blocks inside the buildings (room geometry gives Lara real collision; statics are only skins).
BLOCKS = [(NAVE, EAVES), (TRANSEPT_ARM, EAVES), (NE_BLOCK, NE_H), (NORTH_WING, WING_H), (CONVENT, CONVENT_H),
          (ANNEX, ANNEX_H), (SEGRETERIA, SEGRETERIA_H)]


def to_world(u, v):
    """Local metres -> world sectors (float)."""
    return (ORIGIN[0] + (u * A[0] + v * N[0]) / 2.0, ORIGIN[1] + (u * A[1] + v * N[1]) / 2.0)


def to_local(x, z):
    dx, dz = (x - ORIGIN[0]) * 2.0, (z - ORIGIN[1]) * 2.0
    return dx * A[0] + dz * A[1], dx * N[0] + dz * N[1]


def inside(poly, u, v):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > v) != (y2 > v) and u < (x2 - x1) * (v - y1) / (y2 - y1) + x1:
            c = not c
    return c


def rect(r):
    u0, u1, v0, v1 = r
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def church_polygon():
    return CHURCH


def segreteria_frame():
    """Centre (u, v), long-axis angle phi (radians, from u towards v), length and width of the Segreteria."""
    a, b = np.array((-39.6, -5.25)), np.array((-5.8, -16.95))
    c = (a + b) / 2
    d = b - a
    return (float(c[0]), float(c[1])), math.atan2(d[1], d[0]), float(np.linalg.norm(d)), 4.9


def prepare(world):
    """Re-shape the terrain under and around the sanctuary (call before rooms are built).

    - OSM buildings of the complex are removed (they become static meshes).
    - The square, the terrace and a 1-sector apron around the buildings are flattened to F.
    - Sectors entirely inside a building become solid blocks up to just under its roof: real collision
      for Lara and the AI, hidden inside the static skins.
    """
    cx, cz = int(ORIGIN[0]), int(ORIGIN[1])
    sq = []
    for x in range(cx - 14, cx + 2):
        for z in range(cz - 12, cz + 13):
            u, v = to_local(x + 0.5, z + 0.5)
            if SQUARE[0] <= u <= SQUARE[1] and abs(v) <= 12 and world.building_id[x, z] < 0:
                sq.append(world.terrain_m[x, z].mean())
    F = float(np.median(sq)) if sq else float(world.terrain_m[cx, cz].mean())
    Fu = int(round(F * 512 / 64.0)) * 64
    polys = [p for p, _ in BLOCKS] + [TERRACE]
    win = [(x, z) for x in range(cx - 30, cx + 56) for z in range(cz - 30, cz + 30)
           if 0 <= x < world.nx and 0 <= z < world.nz]
    ids = set()
    for x, z in win:
        u, v = to_local(x + 0.5, z + 0.5)
        if any(inside(p, u, v) for p in polys) and world.building_id[x, z] >= 0:
            ids.add(int(world.building_id[x, z]))
    for b in ids:
        gone = world.building_id == b
        world.building_id[gone] = -1
        world.floor[gone] = world.floor_terrain[gone]
    blocks = solid = 0
    for x, z in win:
        if world.building_id[x, z] >= 0:
            continue
        u, v = to_local(x + 0.5, z + 0.5)
        corners = [to_local(x + dx, z + dz) for dx, dz in ((0, 0), (1, 0), (1, 1), (0, 1))]
        h = None
        for p, ph in BLOCKS:
            if inside(p, u, v):
                h = ph if h is None else max(h, ph)
        near = h is not None or inside(TERRACE, u, v) or \
            any(inside(p, cu, cv) for p in polys for cu, cv in corners)
        on_square = SQUARE[0] <= u <= SQUARE[1] and SQUARE[2] <= v <= SQUARE[3]
        if not (near or on_square):
            continue
        full = h is not None and all(any(inside(p, cu, cv) for p, _ in BLOCKS) for cu, cv in corners)
        if full:
            world.floor[x, z] = Fu + int((h - 0.5) * 512) // 256 * 256
            world.mat[x, z] = "castello_pav"
            solid += 1
        else:
            world.floor[x, z] = Fu
            world.mat[x, z] = "lastricato"
        world.water[x, z] = False
        if hasattr(world, "terraced"):
            world.terraced[x, z] = False
        blocks += 1
    world.santuario = {"F": Fu, "F_m": F, "sectors": blocks, "solid": solid}
    return world.santuario


def place(ctx):
    """Place the sanctuary statics: building skins (church frame) and railings along the terrace."""
    from decor import santuario_models as SM
    k = ctx.kit
    F = ctx.world.santuario["F"]
    n = 0
    for name, (u, v) in SM.ANCHORS.items():
        x, z = to_world(u, v)
        k.prop(name, x, z, rot=AXIS_DEG, h=F)
        n += 1
    (cu, cv), phi, _, _ = segreteria_frame()
    k.prop("SANTUARIO_SEGRETERIA", *to_world(cu, cv), rot=AXIS_DEG - math.degrees(phi), h=F)
    n += 1
    for (u, v), ang in railing_spots(TERRACE_EDGE):
        k.prop("SANTUARIO_RINGHIERA", *to_world(u, v), rot=AXIS_DEG - ang, h=F)
        n += 1
    return n


def railing_spots(line, step=2.4):
    """Centres and angles (degrees, from u towards v) of 2 m railing pieces along a polyline."""
    out = []
    for (u0, v0), (u1, v1) in zip(line, line[1:]):
        L = math.hypot(u1 - u0, v1 - v0)
        k = max(1, int(math.ceil(L / step)))     # pieces are 2.5 m long: they always overlap a little
        ang = math.degrees(math.atan2(v1 - v0, u1 - u0))
        for i in range(k):
            t = (i + 0.5) / k
            out.append(((u0 + (u1 - u0) * t, v0 + (v1 - v0) * t), ang))
    return out
