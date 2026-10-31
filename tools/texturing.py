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

# Vertical floor faces (TombLib RoomExtensionMethods.Get*WallData): the face belongs to the HIGHER
# sector and faces the lower neighbour. Corner indices (start, end) for owner and neighbour;
# start is on the left of a viewer standing in the lower sector.
DIRS = {"+z": ((1, 0), (2, 3), (0, 1)), "-z": ((3, 2), (0, 1), (0, -1)),
        "+x": ((2, 1), (3, 0), (1, 0)), "-x": ((0, 3), (1, 2), (-1, 0))}
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
    def __init__(self, atlas, floor, mat, building_id, styles, bases, macro=None, columns=None):
        self.a = atlas
        self.columns = columns or {}   # extra vertical columns: name -> (texture index, x0, x1)
        self.macro = macro or {}   # material -> (texture index, x0, y0, size px): seamless big tiles
        self.floor = floor
        self.mat = mat
        self.bid = building_id
        self.styles = styles
        self.bases = bases
        self.px = atlas["px_per_m"] * 255.5 / 256.0  # 2 m segment = 255.5 px, inside the 256 px limit
        self.size = atlas["size"]

    # Floors -----------------------------------------------------------------
    def floor_coords(self, wi, wj, f, split):
        name = self.mat[wi, wj]
        if name in self.macro:
            ti, x0, y0, size = self.macro[name]
            n = size // 256
            col, row = wi % n, (n - 1) - (wj % n)   # u along +X, v along -Z (tl = XnZp corner)
            ax, ay = x0 + col * 256, y0 + row * 256
            e = 0.25
            tl, tr, br, bl = (ax + e, ay + e), (ax + 256 - e, ay + e), (ax + 256 - e, ay + 256 - e), (ax + e, ay + 256 - e)
            if prj2_is_quad(f):
                return [(prj2.F_FLOOR, [tl, tr, br, bl], ti)]
            if split:
                return [(prj2.F_FLOOR, [tr, br, bl, bl], ti), (prj2.F_FLOOR_TRI2, [bl, tl, tr, tr], ti)]
            return [(prj2.F_FLOOR, [tl, tr, br, br], ti), (prj2.F_FLOOR_TRI2, [br, bl, tl, tl], ti)]
        if name in ("asfalto", "erba_secca") and h32("t2", wi, wj) % 2:
            name = name + "2"
        x0, y0, x1, y1 = self.a["tiles"][name]
        tl, tr, br, bl = (x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x1 - 0.5, y1 - 0.5), (x0 + 0.5, y1 - 0.5)
        quad = [tl, tr, br, bl]
        if name in NATURAL_TILES:
            r = h32("r", wi, wj) % 4
            quad = quad[r:] + quad[:r]
        tl, tr, br, bl = quad
        if prj2_is_quad(f):
            return [(prj2.F_FLOOR, [tl, tr, br, bl], 0)]
        if split:   # diagonal XnZn-XpZp
            return [(prj2.F_FLOOR, [tr, br, bl, bl], 0), (prj2.F_FLOOR_TRI2, [bl, tl, tr, tr], 0)]
        return [(prj2.F_FLOOR, [tl, tr, br, br], 0), (prj2.F_FLOOR_TRI2, [br, bl, tl, tl], 0)]

    # Walls ------------------------------------------------------------------
    # Tomb Editor accepts at most 256 x 256 px per face, i.e. 2 m of facade at 128 px/m.
    # Tall walls are split with extra floor splits (up to 8, so 9 segments = 18 m).
    MAX_SPLITS = 8
    SEG = 1024  # 2 m per segment

    def column_for(self, wi, wj, d):
        b = self.bid[wi, wj]
        fc = getattr(self, "facade_cols", None)
        if fc and (wi, wj, d) in fc:
            return fc[(wi, wj, d)], self.bases[b] if b >= 0 else None
        if b < 0:
            if "roccia_faccia_0" in self.columns:
                along = wi if d in ("+z", "-z") else wj   # position along the wall: continuous rock face
                return "roccia_faccia_%d" % (along % 8), None
            return "roccia_parete", None
        style = self.styles[b]
        if style == "castello":
            return "pietra_castello", self.bases[b]
        if style == "crema":
            return ("crema_piena" if h32("w", wi, wj, d) % 3 == 0 else "crema_finestre"), self.bases[b]
        return style + "_finestre", self.bases[b]

    def segment_coords(self, col, ref, top, bot, room_y):
        """top/bot: (start, end) heights in room units. Returns TL, TR, BR, BL pixel coords."""
        if col in self.columns:
            _, x0, x1 = self.columns[col]
        else:
            x0, _, x1, _ = self.a["columns"][col]
        world = [(h + room_y) / M for h in (top[0], top[1], bot[1], bot[0])]
        if ref is None:  # rock: keep the segment inside the 16 m column
            lo = min(world[2], world[3])
            ref = lo - (lo % 14.0)
        v = [self.size - 0.5 - (h - ref) * self.px for h in world]
        span = max(v) - min(v)
        if span > 255.5:
            # Portal (border) walls cannot be split: squeeze into one tile, using plain plaster
            # for facades so shutters do not turn into a ladder.
            plain = {"crema_finestre": "crema_piena", "rosa_finestre": "rosa_piena", "bianco_finestre": "bianco_piena"}
            p = plain.get(col)
            if p in self.a["tiles"]:
                tx0, ty0, tx1, ty1 = self.a["tiles"][p]
                hs = [world[0], world[1], world[2], world[3]]
                lo, hi = min(hs), max(hs)
                vv = [ty1 - 0.5 - (h - lo) / (hi - lo) * 255.0 for h in hs]
                return [(tx0 + 0.5, vv[0]), (tx1 - 0.5, vv[1]), (tx1 - 0.5, vv[2]), (tx0 + 0.5, vv[3])]
            vmax = max(v)
            v = [vmax - (vmax - y) * 255.0 / span for y in v]
        v = [float(np.clip(y, 0.5, self.size - 0.5)) for y in v]
        if max(v) - min(v) > 255.5:
            v = [max(min(y, min(v) + 255.5), min(v)) for y in v]
        return [(x0 + 0.5, v[0]), (x1 - 0.5, v[1]), (x1 - 0.5, v[2]), (x0 + 0.5, v[3])]

    def make_splits(self, room, lx, lz):
        s = room.sectors[lx][lz]
        lowest = min(min(room.sectors[lx + dx][lz + dz].floor) for _, _, (dx, dz) in DIRS.values())
        drop = max(s.floor) - lowest
        n = min(self.MAX_SPLITS, max(0, -(-drop // self.SEG) - 1))
        s.fsplits = [[h - self.SEG * k for h in s.floor] for k in range(1, n + 1)]

    def wall_faces(self, room, s, other, d, wi, wj):
        (oi, pi, _) = DIRS[d]
        nb = (other.floor[pi[0]], other.floor[pi[1]])
        tops = [(s.floor[oi[0]], s.floor[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in s.fsplits]
        col, ref = self.column_for(wi, wj, d)
        for k, top in enumerate(tops):
            bot = nb
            if k + 1 < len(tops) and tops[k + 1][0] >= nb[0] and tops[k + 1][1] >= nb[1]:
                bot = tops[k + 1]
            if top[0] <= bot[0] and top[1] <= bot[1]:
                continue
            ti = self.columns[col][0] if col in self.columns else 0
            s.set_tex(prj2.f_wall_floor(d, k), self.segment_coords(col, ref, top, bot, room.y), ti)

    def apply_room(self, room, wx0, wz0):
        """wx0, wz0: world array index of the room's local sector (0, 0)."""
        n_x, n_z = room.nx, room.nz
        # Splits first: only interior sectors can have them (portal sectors are ignored by the editor).
        for lx in range(1, n_x - 1):
            for lz in range(1, n_z - 1):
                self.make_splits(room, lx, lz)
        for lx in range(n_x):
            for lz in range(n_z):
                s = room.sectors[lx][lz]
                wi, wj = wx0 + lx, wz0 + lz
                border = lx in (0, n_x - 1) or lz in (0, n_z - 1)
                if not border:
                    for face, coords, ti in self.floor_coords(wi, wj, s.floor, s.fsplit):
                        s.set_tex(face, coords, ti)
                    s.set_invisible(prj2.F_CEILING)
                    s.set_invisible(prj2.F_CEILING_TRI2)
                for d, (oi, pi, (dx, dz)) in DIRS.items():
                    nx_, nz_ = lx + dx, lz + dz
                    if not (0 <= nx_ < n_x and 0 <= nz_ < n_z):
                        continue
                    other = room.sectors[nx_][nz_]
                    other_border = nx_ in (0, n_x - 1) or nz_ in (0, n_z - 1)
                    if other_border:
                        continue  # No faces towards border sectors (border-to-border included).
                    if border:
                        # Border sectors draw the faces towards the room interior; ceiling steps are hidden.
                        s.set_invisible(prj2.F_WALL_WS[d])
                    if not any(s.floor[oi[k]] > other.floor[pi[k]] for k in (0, 1)):
                        continue  # The face exists only on the higher side.
                    self.wall_faces(room, s, other, d, wi, wj)


def prj2_is_quad(f):
    xnzp, xpzp, xpzn, xnzn = f
    return xpzp - xpzn == xnzp - xnzn and xpzp - xnzp == xpzn - xnzn
