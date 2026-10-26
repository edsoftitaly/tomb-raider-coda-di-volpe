"""Materials and face texturing for generated zones.

materials(): one floor material per world sector (roads, sidewalks, roofs, land use, slope).
apply_room(): writes floor, wall and invisible-ceiling textures into a prj2.Room.

Texture coordinate conventions (from TombLib RoomGeometry / SectorFaceData):
  floor quad corners XnZp, XpZp, XpZn, XnZn  -> TexCoord0..3 = TL, TR, BR, BL
  vertical quad p0 start-top, p1 end-top, p2 end-bottom, p3 start-bottom -> TL, TR, BR, BL
"""
import hashlib
import math

import numpy as np
from matplotlib.path import Path

import prj2

M = 512
ROAD_WIDTH = {"motorway": 10.0, "trunk": 9.0, "primary": 9.0, "secondary": 8.0, "tertiary": 7.0,
              "unclassified": 5.5, "residential": 5.5, "service": 4.0, "living_street": 4.5,
              "pedestrian": 5.0, "footway": 2.0, "steps": 2.0, "path": 1.6, "track": 3.0}
PAVED = {"pedestrian": "lastricato", "footway": "lastricato", "steps": "lastricato",
         "path": "terra", "track": "terra"}
LANDUSE = {("landuse", "farmland"): "uliveto", ("landuse", "orchard"): "uliveto",
           ("landuse", "grass"): "erba_secca", ("landuse", "meadow"): "erba_secca",
           ("natural", "scrub"): "macchia", ("natural", "wood"): "macchia", ("natural", "grassland"): "erba_secca",
           ("natural", "beach"): "ciottoli", ("leisure", "park"): "lastricato"}
NATURAL_TILES = {"erba_secca", "erba_secca2", "terra", "terra2", "roccia", "roccia2", "macchia", "uliveto",
                 "ciottoli", "sabbia", "asfalto", "asfalto2"}
STYLES = ["crema", "rosa", "bianco"]

# Directions: owner/other corner indices (start, end) as seen from the owner looking at the other.
DIRS = {"+z": ((0, 1), (3, 2), (0, 1)), "-z": ((2, 3), (1, 0), (0, -1)),
        "+x": ((1, 2), (0, 3), (1, 0)), "-x": ((3, 0), (2, 1), (-1, 0))}
OPPOSITE = {"+z": "-z", "-z": "+z", "+x": "-x", "-x": "+x"}


def h32(*parts):
    return int(hashlib.md5("/".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def materials(floor_terrain, building_id, buildings, origin, ways, ring_xy, nodes):
    nwx, nwz = building_id.shape
    ox, oz = origin
    mat = np.full((nwx, nwz), "erba_secca", dtype=object)
    centres_x = ox + 2.0 * np.arange(nwx) + 1.0
    centres_z = oz + 2.0 * np.arange(nwz) + 1.0
    gx, gz = np.meshgrid(centres_x, centres_z, indexing="ij")
    pts = np.stack([gx.ravel(), gz.ravel()], axis=1)

    # Natural variation.
    for i in range(nwx):
        for j in range(nwz):
            if h32("v", i, j) % 5 == 0:
                mat[i, j] = "terra"

    # Land use polygons.
    for wid, (refs, tags) in ways.items():
        key = next((k for k in LANDUSE if tags.get(k[0]) == k[1]), None)
        if key is None or not refs or refs[0] != refs[-1]:
            continue
        ring = ring_xy(refs, nodes)
        if len(ring) < 3:
            continue
        inside = Path(ring).contains_points(pts).reshape(nwx, nwz)
        mat[inside] = LANDUSE[key]

    # Steep terrain becomes rock (corner range over 1.2 m on a 2 m sector).
    rng = (floor_terrain.max(axis=2) - floor_terrain.min(axis=2)) / M
    mat[rng > 1.2] = "roccia"

    # Roads and paths.
    for wid, (refs, tags) in ways.items():
        hw = tags.get("highway")
        if hw not in ROAD_WIDTH or tags.get("tunnel") == "yes" or tags.get("bridge") in ("yes", "viaduct"):
            continue
        if tags.get("layer", "0").lstrip("-").isdigit() and int(tags.get("layer", "0")) != 0:
            continue
        line = ring_xy(refs, nodes)
        half = ROAD_WIDTH[hw] / 2.0
        material = PAVED.get(hw, "asfalto")
        for (x0, z0), (x1, z1) in zip(line, line[1:]):
            n = max(1, int(math.hypot(x1 - x0, z1 - z0) / 0.5))
            for t in np.linspace(0, 1, n + 1):
                x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
                i0, i1 = int((x - half - ox) // 2), int((x + half - ox) // 2)
                j0, j1 = int((z - half - oz) // 2), int((z + half - oz) // 2)
                for i in range(max(0, i0), min(nwx, i1 + 1)):
                    for j in range(max(0, j0), min(nwz, j1 + 1)):
                        if (centres_x[i] - x) ** 2 + (centres_z[j] - z) ** 2 <= (half + 0.7) ** 2:
                            mat[i, j] = material

    # Sidewalks: one sector ring around buildings, where not already road or paving.
    is_b = building_id >= 0
    near = np.zeros_like(is_b)
    near[1:, :] |= is_b[:-1, :]
    near[:-1, :] |= is_b[1:, :]
    near[:, 1:] |= is_b[:, :-1]
    near[:, :-1] |= is_b[:, 1:]
    side = near & ~is_b & np.isin(mat, ["erba_secca", "terra", "uliveto", "macchia"])
    mat[side] = "marciapiede"

    # Roofs.
    for bid, b in enumerate(buildings):
        sel = building_id == bid
        castle = b["tags"].get("historic") == "castle"
        mat[sel] = "castello_pav" if castle else "terrazza"
    return mat


def building_styles(buildings, casa_id=None):
    out = []
    for bid, b in enumerate(buildings):
        t = b["tags"]
        if t.get("historic") == "castle":
            out.append("castello")
        elif bid == casa_id:
            out.append("crema")
        elif t.get("building") in ("church",) or t.get("amenity") == "place_of_worship":
            out.append("bianco")
        else:
            out.append(STYLES[h32("b", b["id"], bid) % 3])
    return out


class Texturer:
    def __init__(self, atlas, floor, mat, building_id, styles, bases):
        self.a = atlas
        self.floor = floor
        self.mat = mat
        self.bid = building_id
        self.styles = styles
        self.bases = bases
        self.px = atlas["px_per_m"]
        self.size = atlas["size"]

    # Floors -----------------------------------------------------------------
    def floor_coords(self, wi, wj, f, split):
        name = self.mat[wi, wj]
        if name in ("asfalto", "erba_secca", "terra", "roccia") and h32("t2", wi, wj) % 2:
            name = name + "2"
        x0, y0, x1, y1 = self.a["tiles"][name]
        tl, tr, br, bl = (x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x1 - 0.5, y1 - 0.5), (x0 + 0.5, y1 - 0.5)
        quad = [tl, tr, br, bl]
        if name in NATURAL_TILES:
            r = h32("r", wi, wj) % 4
            quad = quad[r:] + quad[:r]
        tl, tr, br, bl = quad
        if prj2_is_quad(f):
            return [(prj2.F_FLOOR, [tl, tr, br, bl])]
        if split:   # diagonal XnZn-XpZp
            return [(prj2.F_FLOOR, [tr, br, bl, bl]), (prj2.F_FLOOR_TRI2, [bl, tl, tr, tr])]
        return [(prj2.F_FLOOR, [tl, tr, br, br]), (prj2.F_FLOOR_TRI2, [br, bl, tl, tl])]

    # Walls ------------------------------------------------------------------
    def wall_coords(self, d, own_f, oth_f, own_w, oth_w, room_y):
        (oi, pi, _) = DIRS[d]
        ha = [own_f[oi[0]], oth_f[pi[0]]]
        hb = [own_f[oi[1]], oth_f[pi[1]]]
        top_a, bot_a = max(ha), min(ha)
        top_b, bot_b = max(hb), min(hb)
        if top_a <= bot_a and top_b <= bot_b:
            return None
        # The higher side decides the material.
        own_high = (own_f[oi[0]] + own_f[oi[1]]) > (oth_f[pi[0]] + oth_f[pi[1]])
        wi, wj = own_w if own_high else oth_w
        b = self.bid[wi, wj]
        world = lambda h: (h + room_y) / M  # noqa: E731
        if b >= 0:
            style = self.styles[b]
            if style == "castello":
                col = "pietra_castello"
            elif style == "crema":
                col = "crema_piena" if h32("w", wi, wj, d) % 3 == 0 else "crema_finestre"
            else:
                col = style + "_finestre"
            ref = self.bases[b]
        else:
            col = "roccia_parete"
            ref = math.floor(world(min(bot_a, bot_b)) / 16.0) * 16.0
        x0, _, x1, _ = self.a["columns"][col]

        def v(h):
            return float(np.clip(self.size - 0.5 - (world(h) - ref) * self.px, 0.5, self.size - 0.5))
        return [(x0 + 0.5, v(top_a)), (x1 - 0.5, v(top_b)), (x1 - 0.5, v(bot_b)), (x0 + 0.5, v(bot_a))]

    def apply_room(self, room, wx0, wz0):
        """wx0, wz0: world array index of the room's local sector (0, 0)."""
        n_x, n_z = room.nx, room.nz
        for lx in range(n_x):
            for lz in range(n_z):
                s = room.sectors[lx][lz]
                wi, wj = wx0 + lx, wz0 + lz
                border = lx in (0, n_x - 1) or lz in (0, n_z - 1)
                if not border:
                    for face, coords in self.floor_coords(wi, wj, s.floor, s.fsplit):
                        s.set_tex(face, coords)
                    s.set_invisible(prj2.F_CEILING)
                    s.set_invisible(prj2.F_CEILING_TRI2)
                for d, (_, _, (dx, dz)) in DIRS.items():
                    nx_, nz_ = lx + dx, lz + dz
                    if not (0 <= nx_ < n_x and 0 <= nz_ < n_z):
                        continue
                    other = room.sectors[nx_][nz_]
                    other_border = nx_ in (0, n_x - 1) or nz_ in (0, n_z - 1)
                    if border and other_border:
                        continue
                    if other_border:
                        continue  # Faces towards a border sector are owned by the border sector.
                    if border:
                        # Border sectors draw the faces towards the room interior; ceiling steps are hidden.
                        s.set_invisible(prj2.F_WALL_WS[d])
                    else:
                        (oi, pi, _) = DIRS[d]
                        if not any(other.floor[pi[k]] > s.floor[oi[k]] for k in (0, 1)):
                            continue  # The face exists only on the lower side.
                    coords = self.wall_coords(d, s.floor, other.floor, (wi, wj), (wi + dx, wj + dz), room.y)
                    if coords is not None:
                        s.set_tex(prj2.F_WALL_QA[d], coords)


def prj2_is_quad(f):
    xnzp, xpzp, xpzn, xnzn = f
    return xpzp - xpzn == xnzp - xnzn and xpzp - xnzp == xpzn - xnzn
