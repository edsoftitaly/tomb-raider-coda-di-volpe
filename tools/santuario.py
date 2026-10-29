"""Santuario di Maria Santissima del Tindari: real-world layout on the Tindari promontory.

Sources (checked 29/10/2026):
- santuariotindari.it/nuovo-santuario and it.wikipedia "Santuario di Tindari": basilica built 1957-1979,
  Latin cross with three naves, square transept, semicircular apse, 64 x 24 m; facade to the WEST,
  gabled ("a capanna") between two bell towers, central body projecting on the square, rusticated
  portal and lower wall, bronze doors, statues of St Peter and St Paul in niches beside the door,
  round window above the entrance, triangular pediment with the inscription "AVE MARIA"; bell towers
  with simple frames below, eight-pointed stars in the middle orders, right tower with single-light
  windows at the bell chamber, left tower with the clock in a blind oculus and a small outer bell frame,
  square pinnacles on top; roof slopes in blue ceramic; base in Billiemi stone; a loggia 76 x 8 m
  along the north side, over the Marinello lagoons; dome over the crossing (frescoed inside).
- santuariotindari.it/antico-santuario: the old sanctuary (1552-1598, keystone of the portal dated
  1598) was kept beside the new church.
- OpenStreetMap way 156320182 (building=church): footprint and orientation (axis 13.4 deg south of east).

Heights are NOT documented anywhere I could reach: eaves 14 m, pediment apex 22 m, towers 32 m,
dome 28 m are estimates to be checked against photos.

Local frame (metres): u along the nave towards the apse (east), v to the north, origin at the centre
of the facade line, y = 0 at the floor of the church / square (F).
"""
import math

import numpy as np

# Facade centre (world sectors, from the OSM footprint) and axis.
ORIGIN = (207.65, 217.9)
AXIS_DEG = 13.44                     # static rotation: local +X (u) -> world east-south-east
A = (math.cos(math.radians(AXIS_DEG)), -math.sin(math.radians(AXIS_DEG)))   # u direction in world (x, z)
N = (math.sin(math.radians(AXIS_DEG)), math.cos(math.radians(AXIS_DEG)))    # v direction

# Plan (metres, local frame). Measured on the OSM footprint, rounded.
HALF_W = 10.6            # nave + aisles: v in [-10.6, 10.6]
TOWER = 5.5              # bell towers: u in [0, 5.5], |v| in [10.6 - 5.5, 10.6]
FACADE_HALF = HALF_W - TOWER   # central body between the towers
FACADE_PROJ = 1.2        # projection of the central body over the square
NAVE_END = 66.0          # east wall of the nave
APSE_R = 7.0             # semicircular apse, centre (NAVE_END, 0)
TRANSEPT = (40.0, 52.0, -14.8)   # south arm only on the footprint: u0, u1, v of the south wall
CROSSING_U = 46.0
OLD = (74.0, 86.0, 0.6, 13.0)    # old sanctuary block: u0, u1, v0, v1
LOGGIA = (-2.0, 74.0, HALF_W, HALF_W + 8.0)   # u0, u1, v0, v1 (76 x 8 m)
SQUARE = (-30.0, -FACADE_PROJ, -22.0, 22.0)

# Heights (estimates, see above).
EAVES = 14.0
APEX = 22.0
TOWER_H = 32.0
RIDGE = 19.0
APSE_H = 12.0
OLD_H = 9.0
SKIRT = 16.0             # stone base walls go this far below the floor (hidden by the terrain)


def to_world(u, v):
    """Local metres -> world sectors (float)."""
    return (ORIGIN[0] + (u * A[0] + v * N[0]) / 2.0, ORIGIN[1] + (u * A[1] + v * N[1]) / 2.0)


def to_local(x, z):
    dx, dz = (x - ORIGIN[0]) * 2.0, (z - ORIGIN[1]) * 2.0
    return dx * A[0] + dz * A[1], dx * N[0] + dz * N[1]


def church_polygon():
    """Outline of the new church (towers, nave, south transept, apse) in local metres."""
    pts = [(-FACADE_PROJ, -FACADE_HALF), (0, -FACADE_HALF), (0, -HALF_W), (TRANSEPT[0], -HALF_W),
           (TRANSEPT[0], TRANSEPT[2]), (TRANSEPT[1], TRANSEPT[2]), (TRANSEPT[1], -HALF_W),
           (NAVE_END, -HALF_W), (NAVE_END, -APSE_R)]
    for k in range(1, 12):
        a = -math.pi / 2 + math.pi * k / 12
        pts.append((NAVE_END + APSE_R * math.cos(a), APSE_R * math.sin(a)))
    pts += [(NAVE_END, APSE_R), (NAVE_END, HALF_W), (0, HALF_W), (0, FACADE_HALF), (-FACADE_PROJ, FACADE_HALF)]
    return pts


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


def prepare(world):
    """Re-shape the terrain under and around the sanctuary (call before rooms are built).

    - The OSM building is replaced: its sectors become plain ground (the church is made of static
      meshes with collision); the church floor, the loggia and the square are flattened to F.
    - The church interior is closed (bronze doors): those sectors are only a hidden platform.
    """
    import texturing
    # Floor level: the square in front of the facade.
    cx, cz = int(ORIGIN[0]), int(ORIGIN[1])
    sq = []
    for x in range(cx - 14, cx + 2):
        for z in range(cz - 12, cz + 13):
            u, v = to_local(x + 0.5, z + 0.5)
            if SQUARE[0] <= u <= SQUARE[1] and abs(v) <= 12 and world.building_id[x, z] < 0:
                sq.append(world.terrain_m[x, z].mean())
    F = float(np.median(sq)) if sq else float(world.terrain_m[cx, cz].mean())
    Fu = int(round(F * 512 / 64.0)) * 64
    # Remove the OSM church building (and anything else of the complex under the footprint).
    church = rect((-FACADE_PROJ, NAVE_END + APSE_R, TRANSEPT[2], HALF_W))
    full = [church_polygon(), rect(OLD), rect(LOGGIA)]
    ids = set()
    for x in range(cx - 10, cx + 50):
        for z in range(cz - 25, cz + 25):
            if not (0 <= x < world.nx and 0 <= z < world.nz):
                continue
            u, v = to_local(x + 0.5, z + 0.5)
            if any(inside(p, u, v) for p in full) and world.building_id[x, z] >= 0:
                ids.add(int(world.building_id[x, z]))
    for b in ids:
        if "Segreteria" in str(world.buildings[b]["tags"]):
            continue
        gone = world.building_id == b
        world.building_id[gone] = -1
        world.floor[gone] = world.floor_terrain[gone]     # back to the natural ground (roof height before)
    # Platform: church + old sanctuary + loggia at F (sectors whose centre is inside); square too.
    plat = 0
    for x in range(cx - 20, cx + 50):
        for z in range(cz - 25, cz + 25):
            if not (0 <= x < world.nx and 0 <= z < world.nz) or world.building_id[x, z] >= 0:
                continue
            u, v = to_local(x + 0.5, z + 0.5)
            on_square = SQUARE[0] <= u <= SQUARE[1] and SQUARE[2] <= v <= SQUARE[3]
            if any(inside(p, u, v) for p in full) or on_square:
                world.floor[x, z] = Fu
                world.water[x, z] = False
                if hasattr(world, "terraced"):
                    world.terraced[x, z] = False
                world.mat[x, z] = "lastricato" if (on_square or inside(rect(LOGGIA), u, v)) else "castello_pav"
                plat += 1
    world.santuario = {"F": Fu, "F_m": F, "sectors": plat}
    return world.santuario


# ------------------------------------------------------------------------------ placement
STATICS = []   # (name, u, v) anchors filled by decor/santuario_models.py


def place(ctx):
    """Place the sanctuary statics (anchors in local metres) in the level."""
    from decor.santuario_models import ANCHORS, PIERS
    k = ctx.kit
    F = ctx.world.santuario["F"]
    n = 0
    for name, (u, v) in list(ANCHORS.items()) + [("SANTUARIO_PILASTRO", p) for p in PIERS]:
        if name == "SANTUARIO_PILASTRO" and (u, v) == (0.0, 0.0):
            continue
        x, z = to_world(u, v)
        k.prop(name, x, z, rot=AXIS_DEG, h=F)
        n += 1
    return n
