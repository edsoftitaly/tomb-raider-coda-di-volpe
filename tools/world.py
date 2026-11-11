"""The whole Coda di Volpe map as one Tomb Editor level (real scale, 1 sector = 2 m).

World sector (wx, wz) covers metres [ox + 2*wx, ox + 2*wx + 2] east and [oz + 2*wz, ...] north
(EPSG:3004). Tomb Editor room coordinates are world sector indices directly.
Terrain tiles are rooms of (N+2) x (N+2) sectors with stride N; tile (i, j) has room.x = i*N.
Tiles are kept only where they touch the playable zones. Sea and lagoons are water rooms under
the terrain rooms, joined by floor/ceiling portals.
"""
import copy
import math
import os
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from matplotlib.path import Path
from pyproj import Transformer
from scipy import ndimage

import prj2
import texturing
import walls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DTM = os.path.join(ROOT, "data", "dtm", "dtm_2m_3004.tif")
OSM = [os.path.join(ROOT, "data", "osm", f) for f in ("Oliveri.osm", "Tindari.osm")]

M = 512
QUANT = 64
N = 30
HEADROOM = 48 * prj2.CLICK     # 24 m of air over the highest point: room for flyby cameras
to3004 = Transformer.from_crs(4326, 3004, always_xy=True)

# Playable zones (lat, lon polygons).
ZONES = {
    "A": [(38.1212, 15.0555), (38.1212, 15.0625), (38.1262, 15.0625), (38.1262, 15.0555)],
    "B": [(38.1255, 15.0556), (38.1262, 15.0605), (38.1342, 15.0552), (38.1342, 15.0512)],
    "C": [(38.1338, 15.0478), (38.1338, 15.0570), (38.1462, 15.0570), (38.1462, 15.0478)],
    "D": [(38.1372, 15.0390), (38.1372, 15.0478), (38.1462, 15.0478), (38.1462, 15.0390)],
}
DEFAULT_HEIGHT = {"apartments": 12.5, "church": 12.0, "civic": 9.5, "house": 7.0, "yes": 9.5,
                  "roof": 3.5, "garage": 3.0, "castle": 8.0, "ruins": 2.5, "train_station": 6.0}


def q(v):
    return int(round(v / QUANT)) * QUANT


def load_osm():
    nodes, ways, rels = {}, {}, []
    for f in OSM:
        root = ET.parse(f).getroot()
        for n in root.iter("node"):
            nodes[n.get("id")] = (float(n.get("lat")), float(n.get("lon")))
        for w in root.iter("way"):
            tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
            ways[w.get("id")] = ([nd.get("ref") for nd in w.findall("nd")], tags)
        for r in root.iter("relation"):
            tags = {t.get("k"): t.get("v") for t in r.findall("tag")}
            members = [(m.get("type"), m.get("ref"), m.get("role")) for m in r.findall("member")]
            rels.append((members, tags))
    return nodes, ways, rels


_OSM_CACHE = None


class World:
    def __init__(self, zones=None, frame=None):
        """frame = (pivot_lat, pivot_lon, angle_deg, (u0, v0, u1, v1)): a small zone in a local metric frame
        rotated by angle_deg (counter-clockwise) about the pivot, so that the main street runs along +x.
        u/v are metres in that frame; every OSM coordinate goes through xy() and lands aligned to the grid."""
        global _OSM_CACHE
        if _OSM_CACHE is None:
            _OSM_CACHE = load_osm()
        self.nodes, self.ways, self.rels = _OSM_CACHE
        ds = rasterio.open(DTM)
        dtm = ds.read(1).astype(np.float64)
        dtm[dtm < -100] = 0.0
        self.frame = frame
        if frame is not None:
            plat, plon, ang, (u0, v0, u1, v1) = frame
            self.px, self.pz = to3004.transform(plon, plat)
            self.ca, self.sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            self.nrx, self.nrz = -(-int(math.ceil((u1 - u0) / 2.0)) // N), -(-int(math.ceil((v1 - v0) / 2.0)) // N)
            self.nx, self.nz = self.nrx * N + 2, self.nrz * N + 2
            self.ox, self.oz = u0 - 2.0, v0 - 2.0
            # Heights at sector corners: sample the DTM (bilinear) at the rotated corner positions.
            cu = self.ox + 2.0 * np.arange(self.nx + 1)
            cv = self.oz + 2.0 * np.arange(self.nz + 1)
            U, Vv = np.meshgrid(cu, cv, indexing="ij")
            X = self.px + U * self.ca - Vv * self.sa
            Z = self.pz + U * self.sa + Vv * self.ca
            colf = (X - ds.bounds.left) / 2.0 - 0.5
            rowf = (ds.bounds.top - Z) / 2.0 - 0.5
            self.H = ndimage.map_coordinates(dtm, [rowf, colf], order=1, mode="nearest")
            corners = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            self.zones = {"Z": [self.latlon(u, v) for u, v in corners]}
        else:
            self.zones = zones or ZONES
            lats = [p[0] for z in self.zones.values() for p in z]
            lons = [p[1] for z in self.zones.values() for p in z]
            x0, z0 = to3004.transform(min(lons), min(lats))
            x1, z1 = to3004.transform(max(lons), max(lats))
            col0 = int(math.floor((x0 - ds.bounds.left) / 2.0))
            row_top = int(math.floor((ds.bounds.top - z1) / 2.0))
            span_x = int(math.ceil((x1 - x0) / 2.0)) + 2
            span_z = int(math.ceil((z1 - z0) / 2.0)) + 2
            self.nrx, self.nrz = -(-span_x // N), -(-span_z // N)
            self.nx, self.nz = self.nrx * N + 2, self.nrz * N + 2
            # Corner (cx, cz) world position = pixel centre of column col0+cx, row (row_bottom - cz).
            row_bottom = row_top + self.nz
            self.ox = ds.bounds.left + 1.0 + 2.0 * col0
            self.oz = ds.bounds.top - 1.0 - 2.0 * row_bottom
            cols = np.clip(np.arange(col0, col0 + self.nx + 1), 0, dtm.shape[1] - 1)
            rows = np.clip(np.arange(row_bottom, row_bottom - self.nz - 1, -1), 0, dtm.shape[0] - 1)
            self.H = dtm[np.ix_(rows, cols)].T  # metres, H[cx, cz]
        self.inside_dtm = np.ones_like(self.H, dtype=bool)
        self.centres = self._centres()
        self.zone_mask = self._zone_mask()

    def latlon(self, u, v):
        """Local frame metres -> (lat, lon)."""
        X = self.px + u * self.ca - v * self.sa
        Z = self.pz + u * self.sa + v * self.ca
        lon, lat = to3004.transform(X, Z, direction="INVERSE")
        return (lat, lon)

    # Coordinates ---------------------------------------------------------------
    def _centres(self):
        gx, gz = np.meshgrid(self.ox + 2.0 * np.arange(self.nx) + 1.0, self.oz + 2.0 * np.arange(self.nz) + 1.0,
                             indexing="ij")
        return gx, gz

    def xy(self, lat, lon):
        x, z = to3004.transform(lon, lat)
        if self.frame is None:
            return x, z
        dx, dz = x - self.px, z - self.pz
        return dx * self.ca + dz * self.sa, -dx * self.sa + dz * self.ca

    def sector_of(self, lat, lon):
        x, z = self.xy(lat, lon)
        return (x - self.ox) / 2.0, (z - self.oz) / 2.0

    def ring(self, refs):
        return [self.xy(*self.nodes[r]) for r in refs if r in self.nodes]

    def poly_mask(self, ring):
        """Sectors whose centre lies in a 3004 polygon, computed in its bounding window."""
        mask = np.zeros((self.nx, self.nz), dtype=bool)
        if len(ring) < 3:
            return mask
        xs = [p[0] for p in ring]
        zs = [p[1] for p in ring]
        i0 = max(0, int((min(xs) - self.ox) // 2) - 1)
        i1 = min(self.nx, int((max(xs) - self.ox) // 2) + 2)
        j0 = max(0, int((min(zs) - self.oz) // 2) - 1)
        j1 = min(self.nz, int((max(zs) - self.oz) // 2) + 2)
        if i0 >= i1 or j0 >= j1:
            return mask
        gx, gz = self.centres
        pts = np.stack([gx[i0:i1, j0:j1].ravel(), gz[i0:i1, j0:j1].ravel()], axis=1)
        mask[i0:i1, j0:j1] = Path(ring).contains_points(pts).reshape(i1 - i0, j1 - j0)
        return mask

    def _zone_mask(self):
        m = np.zeros((self.nx, self.nz), dtype=bool)
        for poly in self.zones.values():
            m |= self.poly_mask([self.xy(la, lo) for la, lo in poly])
        return m

    # Terrain and buildings -----------------------------------------------------------
    def build_terrain(self):
        H = self.H
        fl = np.zeros((self.nx, self.nz, 4))
        fl[:, :, 0] = H[:-1, 1:]
        fl[:, :, 1] = H[1:, 1:]
        fl[:, :, 2] = H[1:, :-1]
        fl[:, :, 3] = H[:-1, :-1]
        self.terrain_m = fl.copy()
        self.floor = (np.round(fl * M / QUANT) * QUANT).astype(np.int64)

        # Water: sea at DTM ~0 plus OSM lagoons.
        hmax = fl.max(axis=2)
        lagoon = np.zeros((self.nx, self.nz), dtype=bool)
        for wid, (refs, tags) in self.ways.items():
            if tags.get("natural") == "water" and refs and refs[0] == refs[-1]:
                lagoon |= self.poly_mask(self.ring(refs))
        water = (hmax <= 0.25) | lagoon
        self.lagoon = lagoon
        self.water = water
        dist = ndimage.distance_transform_edt(water) * 2.0
        depth = np.where(lagoon, np.clip(0.6 + 0.35 * dist, 0.6, 4.0), np.clip(0.8 + 0.10 * dist, 0.8, 18.0))
        depth[~water] = 0.0
        self.depth = depth
        self.floor[water] = 0

        # Buildings.
        self.building_id = np.full((self.nx, self.nz), -1, dtype=np.int64)
        self.buildings = []
        roof = np.zeros((self.nx, self.nz))

        def add(outer, inners, tags, ident):
            mask = self.poly_mask(outer)
            for r in inners:
                mask &= ~self.poly_mask(r)
            mask &= ~water
            if not mask.any():
                return
            ground = self.floor[mask].max() / M
            base = self.floor[mask].min() / M
            h = building_height(tags)
            bid = len(self.buildings)
            self.building_id[mask] = bid
            roof[mask] = ground + h
            self.buildings.append({"id": ident, "tags": tags, "sectors": int(mask.sum()), "ground_m": round(float(ground), 2),
                                   "base_m": round(float(base), 2), "roof_m": round(float(ground + h), 2)})

        for wid, (refs, tags) in self.ways.items():
            if ("building" in tags or tags.get("historic") == "ruins") and refs and refs[0] == refs[-1]:
                if tags.get("building") == "roof":
                    continue
                add(self.ring(refs), [], tags, "way/" + wid)
        for members, tags in self.rels:
            if "building" in tags or tags.get("historic") == "castle":
                outers = [self.ring(self.ways[r][0]) for t, r, role in members if t == "way" and role == "outer" and r in self.ways]
                inners = [self.ring(self.ways[r][0]) for t, r, role in members if t == "way" and role == "inner" and r in self.ways]
                for o in outers:
                    add(o, inners, tags, "relation/" + tags.get("name", "?"))
        is_b = self.building_id >= 0
        self.floor[is_b] = (np.round(roof[is_b] * M / QUANT) * QUANT).astype(np.int64)[:, None]
        self.terrace(is_b | water)
        self.floor_terrain = (np.round(fl * M / QUANT) * QUANT).astype(np.int64)
        self.floor_terrain[water] = 0

    TERRACE_DROP = 1280   # 2.5 m over one 2 m sector (> 51 deg): unwalkable, and a stretched texture

    def terrace(self, keep):
        """Very steep sectors become flat ledges at their mean height (rounded to a click).

        A floor face can carry at most 256 px, so a steep slope stretches its texture 1.5-4 times.
        As flat ledges, the height differences become vertical rock faces, which the texturer splits
        every 2 m: cliffs turn into stepped rock walls with undistorted texture.
        """
        f = self.floor
        drop = np.max(np.abs(f - np.roll(f, 1, axis=2)), axis=2)
        steep = (drop > self.TERRACE_DROP) & ~keep
        # Grow into the steep-ish neighbours, so a cliff does not alternate ledges and sloped
        # sectors (that made saw-tooth spikes).
        for _ in range(2):
            steep |= ndimage.binary_dilation(steep) & (drop > self.TERRACE_DROP * 0.55) & ~keep
        mean = np.round(f.mean(axis=2) / 256.0) * 256.0
        f[steep] = mean[steep].astype(np.int64)[:, None]
        self.terraced = steep
        return int(steep.sum())

    def build_materials(self):
        rng = np.random.default_rng(7)
        mat = np.full((self.nx, self.nz), "erba_secca", dtype=object)
        # Bare-earth patches: coherent areas of 10-30 m, not single random sectors (those made a checkerboard).
        from gen_textures import noise
        n = max(self.nx, self.nz)
        patches = noise(n, n, 12, 3, 77)[:self.nx, :self.nz]
        mat[patches > 0.66] = "terra"
        for wid, (refs, tags) in self.ways.items():
            key = next((k for k in texturing.LANDUSE if tags.get(k[0]) == k[1]), None)
            if key is None or not refs or refs[0] != refs[-1]:
                continue
            mat[self.poly_mask(self.ring(refs))] = texturing.LANDUSE[key]
        rngm = (self.floor_terrain.max(axis=2) - self.floor_terrain.min(axis=2)) / M
        mat[rngm > 1.2] = "roccia"
        gx, gz = self.centres
        for wid, (refs, tags) in self.ways.items():
            hw = tags.get("highway")
            if hw not in texturing.ROAD_WIDTH or tags.get("tunnel") == "yes" or tags.get("bridge") in ("yes", "viaduct"):
                continue
            if tags.get("layer", "0").lstrip("-").isdigit() and int(tags.get("layer", "0")) != 0:
                continue
            line = self.ring(refs)
            half = texturing.ROAD_WIDTH[hw] / 2.0
            material = texturing.PAVED.get(hw, "asfalto")
            for (xa, za), (xb, zb) in zip(line, line[1:]):
                n = max(1, int(math.hypot(xb - xa, zb - za) / 0.5))
                for t in np.linspace(0, 1, n + 1):
                    x, z = xa + (xb - xa) * t, za + (zb - za) * t
                    i0, i1 = max(0, int((x - half - self.ox) // 2)), min(self.nx, int((x + half - self.ox) // 2) + 1)
                    j0, j1 = max(0, int((z - half - self.oz) // 2)), min(self.nz, int((z + half - self.oz) // 2) + 1)
                    if i0 >= i1 or j0 >= j1:
                        continue
                    sel = (gx[i0:i1, j0:j1] - x) ** 2 + (gz[i0:i1, j0:j1] - z) ** 2 <= (half + 0.7) ** 2
                    sub = mat[i0:i1, j0:j1]
                    sub[sel] = material
        # Beaches next to the sea.
        near_sea = ndimage.binary_dilation(self.water & ~self.lagoon, iterations=6) & ~self.water
        low = self.floor_terrain.max(axis=2) < 3 * M
        mat[near_sea & low & np.isin(mat, ["erba_secca", "terra", "macchia"])] = "ciottoli"
        # Reeds and mud around lagoons.
        near_lag = ndimage.binary_dilation(self.lagoon, iterations=2) & ~self.water
        mat[near_lag] = "macchia"
        # Sidewalks and roofs.
        is_b = self.building_id >= 0
        near = ndimage.binary_dilation(is_b) & ~is_b
        mat[near & np.isin(mat, ["erba_secca", "terra", "uliveto", "macchia"])] = "marciapiede"
        for bid, b in enumerate(self.buildings):
            castle = b["tags"].get("historic") in ("castle", "ruins") or b["tags"].get("building") == "ruins"
            mat[self.building_id == bid] = "castello_pav" if castle else "terrazza"
        self.mat = mat

    # Rooms ---------------------------------------------------------------------------
    def tiles(self):
        out = []
        for i in range(self.nrx):
            for j in range(self.nrz):
                if self.zone_mask[i * N + 1:i * N + N + 1, j * N + 1:j * N + N + 1].any():
                    out.append((i, j))
        return out


def building_height(tags):
    if "height" in tags:
        try:
            return float(tags["height"].split()[0])
        except ValueError:
            pass
    if "building:levels" in tags:
        try:
            return float(tags["building:levels"]) * 3.2 + 1.0
        except ValueError:
            pass
    if tags.get("historic") == "castle":
        return DEFAULT_HEIGHT["castle"]
    if tags.get("historic") == "ruins" or tags.get("building") == "ruins":
        return DEFAULT_HEIGHT["ruins"]
    return DEFAULT_HEIGHT.get(tags.get("building", "yes"), DEFAULT_HEIGHT["yes"])


def rectangles(mask):
    """Greedy decomposition of a boolean 2D mask into rectangles (x0, z0, x1, z1) inclusive."""
    m = mask.copy()
    out = []
    nx, nz = m.shape
    for x in range(nx):
        for z in range(nz):
            if not m[x, z]:
                continue
            z1 = z
            while z1 + 1 < nz and m[x, z1 + 1]:
                z1 += 1
            x1 = x
            while x1 + 1 < nx and m[x1 + 1, z:z1 + 1].all():
                x1 += 1
            m[x:x1 + 1, z:z1 + 1] = False
            out.append((x, z, x1, z1))
    return out


def build_rooms(world, level, atlases, texer):
    """Terrain and water rooms for every kept tile, with all portals. Returns dicts of rooms."""
    tiles = set(world.tiles())
    terrain, water = {}, {}
    n = N + 2
    for (i, j) in sorted(tiles):
        sx0, sz0 = i * N, j * N
        block = world.floor[sx0:sx0 + n, sz0:sz0 + n]
        y = int(math.floor(block.min() / prj2.CLICK)) * prj2.CLICK
        ceil = int(block.max()) - y + HEADROOM
        room = prj2.Room("T_%02d_%02d" % (i, j), n, n, x=sx0, y=y, z=sz0)
        room.outside = True
        room.horizon = True
        room.ambient = getattr(world, "ambient", (0.62, 0.6, 0.58))
        room.tags = ["esterno"]
        room.no_path = True  # enemies get pathfinding only where content modules enable it
        for lx in range(n):
            for lz in range(n):
                s = room.sectors[lx][lz]
                f = block[lx, lz] - y
                s.floor = [int(v) for v in f]
                s.ceil = [ceil] * 4
                s.fsplit = abs(int(f[1]) - int(f[3])) <= abs(int(f[0]) - int(f[2]))
        texer.apply_room(room, sx0, sz0)
        terrain[i, j] = level.add_room(room)
        sun = getattr(world, "sun", None)
        if sun:     # one sun per terrain room: slopes and walls get shaded by their facing
            level.add_light(room, 4, (n * 512, ceil - 512, n * 512), color=sun["color"], intensity=sun["intensity"],
                            rot_y=sun["rot_y"], rot_x=sun["rot_x"])
        flip = getattr(world, "flip", {}).get((i, j))
        if flip is not None:
            # Alternate (flipped) terrain room: the same ground with no water surface (the lake is drained).
            alt = copy.deepcopy(room)
            alt.name = room.name + "_ASCIUTTO"
            alt.index = None
            alt.objects = []
            level.add_room(alt)
            if sun:
                level.add_light(alt, 4, (n * 512, ceil - 512, n * 512), color=sun["color"], intensity=sun["intensity"],
                                rot_y=sun["rot_y"], rot_x=sun["rot_x"])
            room.alternate = (flip, alt)
            room.alt = alt

        wsub = world.water[sx0:sx0 + n, sz0:sz0 + n]
        if wsub[1:n - 1, 1:n - 1].any():
            dsub = world.depth[sx0:sx0 + n, sz0:sz0 + n]
            # Corner depths: mean of the adjacent water sectors.
            pad = np.pad(np.where(wsub, dsub, np.nan), 1, constant_values=np.nan)
            corners = np.nanmean(np.stack([pad[:-1, :-1], pad[1:, :-1], pad[:-1, 1:], pad[1:, 1:]]), axis=0)
            corners = np.nan_to_num(corners, nan=0.4)
            ymin = -int(math.ceil(np.nanmax(dsub[wsub]) * M / prj2.CLICK + 1)) * prj2.CLICK
            wr = prj2.Room("W_%02d_%02d" % (i, j), n, n, x=sx0, y=ymin, z=sz0)
            wr.room_type = 3  # Water
            wr.ambient = (0.35, 0.5, 0.55)
            wr.tags = ["acqua"]
            wr.no_path = True
            top = 0 - ymin
            for lx in range(n):
                for lz in range(n):
                    s = wr.sectors[lx][lz]
                    s.ceil = [top] * 4
                    if wsub[lx, lz]:
                        c = corners
                        dd = [c[lx, lz + 1], c[lx + 1, lz + 1], c[lx + 1, lz], c[lx, lz]]  # XnZp, XpZp, XpZn, XnZn
                        s.floor = [q(-dv * M) - ymin for dv in dd]
                        s.floor = [min(v, top - QUANT) for v in s.floor]
                        s.fsplit = abs(s.floor[1] - s.floor[3]) <= abs(s.floor[0] - s.floor[2])
                        if 0 < lx < n - 1 and 0 < lz < n - 1:
                            depth = world.depth[sx0 + lx, sz0 + lz]
                            bed = getattr(world, "bed_mat", None)
                            if bed:
                                for face, coords, ti in texer.floor_coords(sx0 + lx, sz0 + lz, s.floor, s.fsplit, name=bed):
                                    s.set_tex(face, coords, ti)
                            else:
                                name = "posidonia" if (world.lagoon[sx0 + lx, sz0 + lz] or depth > 6) else "sabbia_fondo"
                                walls.set_floor(s, atlases, name, walls.rot_for(sx0 + lx, sz0 + lz))
                    else:
                        s.wall = True
                        s.floor = [top - prj2.CLICK] * 4
            water[i, j] = level.add_room(wr)
            walt = None
            if flip is not None:
                # Alternate water room: an ordinary room (air), the bed turns to cracked mud.
                walt = copy.deepcopy(wr)
                walt.name = wr.name + "_ASCIUTTO"
                walt.index = None
                walt.objects = []
                walt.room_type = 0
                walt.ambient = getattr(world, "dry_ambient", (0.5, 0.48, 0.44))
                level.add_room(walt)
                wr.alternate = (flip, walt)
                wr.alt = walt
                dry = getattr(world, "dry_mat", "m_fango")
                for lx in range(1, n - 1):
                    for lz in range(1, n - 1):
                        if wsub[lx, lz]:
                            s = walt.sectors[lx][lz]
                            for face, coords, ti in texer.floor_coords(sx0 + lx, sz0 + lz, s.floor, s.fsplit, name=dry):
                                s.set_tex(face, coords, ti)
            # Surface portals on interior water sectors.
            inner = wsub.copy()
            inner[0, :] = inner[-1, :] = False
            inner[:, 0] = inner[:, -1] = False
            for (x0, z0, x1, z1) in rectangles(inner):
                # Traversable faces = visible water surface (TRLE "opacity 2"), additive water texture.
                level.add_portal(room, (x0, z0, x1, z1), prj2.P_FLOOR, wr, opacity=2)
                level.add_portal(wr, (x0, z0, x1, z1), prj2.P_CEILING, room, opacity=2)
                if walt is not None:
                    level.add_portal(room.alt, (x0, z0, x1, z1), prj2.P_FLOOR, wr, opacity=0)
                    level.add_portal(walt, (x0, z0, x1, z1), prj2.P_CEILING, room, opacity=0)
            for lx in range(1, n - 1):
                for lz in range(1, n - 1):
                    if inner[lx, lz]:
                        name = "acqua_laguna" if world.lagoon[sx0 + lx, sz0 + lz] else "acqua_mare"
                        rot = walls.rot_for(sx0 + lx, sz0 + lz)
                        walls.set_floor(room.sectors[lx][lz], atlases, name, rot, blend=2)
                        walls.set_ceiling(wr.sectors[lx][lz], atlases, name, rot, blend=2)
                        if walt is not None:
                            for rm in (room.alt, walt):
                                sec = rm.sectors[lx][lz]
                                for face in ((prj2.F_FLOOR, prj2.F_FLOOR_TRI2) if rm is room.alt else (prj2.F_CEILING, prj2.F_CEILING_TRI2)):
                                    if sec.tex and face in sec.tex:
                                        del sec.tex[face]
                                    sec.set_invisible(face)

    # Horizontal portals and edges.
    for group in (terrain, water):
        for (i, j), room in group.items():
            sides = set()
            for d, (di, dj) in (("+x", (1, 0)), ("-x", (-1, 0)), ("+z", (0, 1)), ("-z", (0, -1))):
                if (i + di, j + dj) in group:
                    sides.add(d)
            for d in sides:
                other = group[i + {"+x": 1, "-x": -1}.get(d, 0), j + {"+z": 1, "-z": -1}.get(d, 0)]
                if d == "+x":
                    level.add_portal(room, (n - 1, 1, n - 1, n - 2), prj2.P_WALL_PX, other)
                elif d == "-x":
                    level.add_portal(room, (0, 1, 0, n - 2), prj2.P_WALL_NX, other)
                elif d == "+z":
                    level.add_portal(room, (1, n - 1, n - 2, n - 1), prj2.P_WALL_PZ, other)
                else:
                    level.add_portal(room, (1, 0, n - 2, 0), prj2.P_WALL_NZ, other)
            room.portal_sides = sides
            alt = getattr(room, "alt", None)
            if alt is not None:
                for d in sides:
                    other = group[i + {"+x": 1, "-x": -1}.get(d, 0), j + {"+z": 1, "-z": -1}.get(d, 0)]
                    area, pd = {"+x": ((n - 1, 1, n - 1, n - 2), prj2.P_WALL_PX), "-x": ((0, 1, 0, n - 2), prj2.P_WALL_NX),
                                "+z": ((1, n - 1, n - 2, n - 1), prj2.P_WALL_PZ), "-z": ((1, 0, n - 2, 0), prj2.P_WALL_NZ)}[d]
                    level.add_portal(alt, area, pd, other)
                alt.portal_sides = sides
            rock = getattr(world, "bed_wall", "roccia_mare")
            for rm in (room, alt):
                if rm is None:
                    continue
                if group is terrain:
                    hide_edges(rm, sides)
                else:
                    walls.texture_walls(rm, atlases, lambda r, wx, wz, d: (rock, None), portal_sides=sides)
    # Inverted flips: the base state is the dry one, the flipmap floods the tile (the content keeps placing
    # objects in the base rooms, so only the geometry, the room type and the portals change sides).
    for key in getattr(world, "flip_inverted", ()):
        for group in (terrain, water):
            rm = group.get(key)
            alt = getattr(rm, "alt", None) if rm is not None else None
            if alt is None:
                continue
            for attr in ("sectors", "room_type", "ambient", "objects", "meta", "tags"):
                a, b = getattr(rm, attr), getattr(alt, attr)
                setattr(rm, attr, b)
                setattr(alt, attr, a)
            alt.name = rm.name + "_PIENO"
    return terrain, water


INWARD = {"-x": "+x", "+x": "-x", "-z": "+z", "+z": "-z"}


def hide_edges(room, portal_sides):
    """Zone edges: hide the tall middle and ceiling faces of non-portal border walls."""
    n_x, n_z = room.nx, room.nz
    for side in ("-x", "+x", "-z", "+z"):
        if side in portal_sides:
            continue
        d = INWARD[side]
        for k in range(1, (n_z if side in ("-x", "+x") else n_x) - 1):
            x, z = {"-x": (0, k), "+x": (n_x - 1, k), "-z": (k, 0), "+z": (k, n_z - 1)}[side]
            s = room.sectors[x][z]
            s.set_invisible(prj2.F_WALL_MIDDLE[d])
            s.set_invisible(prj2.F_WALL_WS[d])
