"""Place decoration statics (wad CdV_Decorazioni) on a terrain level, from OSM data and rules.

Sources, in order of reliability: OSM nodes (trees, benches, street lamps, bars and restaurants),
OSM areas (orchards -> olive groves, woods -> Aleppo pines, scrub -> prickly pear, helichrysum,
wild asparagus; pitches, parking, camp sites, parks, beaches), OSM roads (lamps along lit roads,
parked cars) and the coastline (moored boats). An optional per-level JSON of satellite points
(build/satellite/<Level>.json: {"trees": [[lat, lon, kind], ...], ...}) overrides the vegetation.

Gameplay safety: nothing within 3 sectors of a named object (Lara, enemies, levers, puzzle items,
doors...), of vertical links (holes) or of carved ramps/gates; nothing solid on roads except cars
at the kerb; nothing on building roofs.
"""
import json
import math
import os
import xml.etree.ElementTree as ET

import numpy as np

import world as W
from texturing import ROAD_WIDTH

ROOT = W.ROOT

S = {name: sid for sid, name in (
    (100, "FICO_INDIA_GRANDE"), (101, "FICO_INDIA_PICCOLO"), (102, "ELICRISO"), (103, "ELICRISO_GRUPPO"),
    (104, "ASPARAGO_SELVATICO"), (105, "ASPARAGO_ROVO"), (106, "PINO_ALEPPO_GRANDE"), (107, "PINO_ALEPPO_INCLINATO"),
    (108, "PINO_ALEPPO_GIOVANE"), (109, "ULIVO"), (110, "ULIVO_GIOVANE"), (111, "ULIVO_SECOLARE"),
    (112, "LAMPIONE_PIAZZA"), (113, "LAMPIONE_MURO"), (114, "LAMPIONE_STRADA"), (115, "LAMPIONE_LUNGOMARE"),
    (116, "PANCHINA"), (117, "VASO_BIANCO_FIORI"), (118, "VASO_BIANCO_PALMA"), (119, "VASO_BIANCO_ULIVO"),
    (120, "GIOCHI_SCIVOLO"), (121, "GIOCHI_ALTALENA"), (122, "GIOCHI_DONDOLO"), (123, "GIOCHI_MOLLA"),
    (124, "GIOCHI_CASTELLO"), (125, "FARO_CAMPO"), (126, "RECINZIONE_CAMPO"), (127, "PORTA_CALCIO"),
    (128, "GOZZO"), (129, "GOMMONE"), (130, "MOTOSCAFO"), (131, "BARCA_VELA"), (132, "BARCHETTA_SPIAGGIA"),
    (133, "AUTO_UTILITARIA_ROSSA"), (134, "AUTO_UTILITARIA_BIANCA"), (135, "AUTO_BERLINA_GRIGIA"),
    (136, "AUTO_SUV_BLU"), (137, "FURGONE_BIANCO"), (138, "CAMPER"), (139, "SCOOTER_ROSSO"),
    (140, "SCOOTER_CREMA"), (141, "BICICLETTA"), (142, "DEHORS_TAVOLO"), (143, "DEHORS_OMBRELLONE"),
    (144, "DEHORS_FIORIERA"), (145, "OMBRELLONE_SPIAGGIA"), (146, "AUTO_500_AZZURRA"), (147, "APE_PIAGGIO"))}
SOLID = {"FICO_INDIA_GRANDE", "FICO_INDIA_PICCOLO", "PINO_ALEPPO_GRANDE", "PINO_ALEPPO_INCLINATO",
         "PINO_ALEPPO_GIOVANE", "ULIVO", "ULIVO_GIOVANE", "ULIVO_SECOLARE"}
CARS = ["AUTO_UTILITARIA_ROSSA", "AUTO_UTILITARIA_BIANCA", "AUTO_BERLINA_GRIGIA", "AUTO_SUV_BLU", "FURGONE_BIANCO",
        "AUTO_500_AZZURRA", "APE_PIAGGIO"]
BOATS = ["GOZZO", "GOZZO", "GOMMONE", "MOTOSCAFO", "BARCA_VELA"]

_NODE_TAGS = None


def node_tags():
    global _NODE_TAGS
    if _NODE_TAGS is None:
        _NODE_TAGS = []
        for f in W.OSM:
            for n in ET.parse(f).getroot().iter("node"):
                tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
                if tags:
                    _NODE_TAGS.append((float(n.get("lat")), float(n.get("lon")), tags))
    return _NODE_TAGS


class Decorator:
    def __init__(self, ctx, seed=11):
        self.ctx = ctx
        self.w = ctx.world
        self.level = ctx.level
        self.r = np.random.default_rng(seed)
        self.count = {}
        self.taken = np.zeros((self.w.nx, self.w.nz), dtype=bool)
        self.blocked = np.zeros((self.w.nx, self.w.nz), dtype=bool)
        self.road = np.isin(self.w.mat, ["asfalto", "asfalto2"])
        self.walk = np.isin(self.w.mat, ["lastricato", "marciapiede", "castello_pav"])
        self._protect()

    # ----------------------------------------------------------------------------- safety
    def _protect(self):
        k = self.ctx.kit
        for name, (x, h, z, room) in k.names.items():
            cx, cz = int(x // 1024), int(z // 1024)
            self.blocked[max(0, cx - 3):cx + 4, max(0, cz - 3):cz + 4] = True
        for (x, z) in k.links:
            self.blocked[max(0, x - 2):x + 3, max(0, z - 2):z + 3] = True
        for extra in getattr(self.ctx, "decor_block", []):
            x0, z0, x1, z1 = extra
            self.blocked[x0:x1 + 1, z0:z1 + 1] = True

    def free(self, x, z, solid=True):
        x, z = int(x), int(z)
        if not (2 <= x < self.w.nx - 2 and 2 <= z < self.w.nz - 2):
            return False
        if self.blocked[x, z] or self.w.building_id[x, z] >= 0 or self.w.water[x, z] or not self.w.zone_mask[x, z]:
            return False
        if solid and (self.taken[x, z] or self.road[x, z]):
            return False
        try:
            self.ctx.terrain_room_at(x, z)
        except KeyError:
            return False
        return True

    # ----------------------------------------------------------------------------- placement
    def height(self, x, z):
        ix, iz = int(x), int(z)
        fx, fz = x - ix, z - iz
        f = self.w.floor[ix, iz]          # XnZp, XpZp, XpZn, XnZn
        top = f[0] * (1 - fx) + f[1] * fx
        bot = f[3] * (1 - fx) + f[2] * fx
        return bot * (1 - fz) + top * fz

    def put(self, name, x, z, rot=None, scale=1.0, y=None, solid=None, tint=None):
        ix, iz = int(x), int(z)
        room = self.ctx.terrain_room_at(ix, iz)
        h = self.height(x, z) if y is None else y
        rot = self.r.uniform(0, 360) if rot is None else rot
        pos = ((x - room.x) * 1024.0, float(h - room.y), (z - room.z) * 1024.0)
        self.level.add_static(room, S[name], pos, rot_y=rot, scale=scale)
        if solid if solid is not None else name in SOLID:
            self.taken[ix, iz] = True
        self.count[name] = self.count.get(name, 0) + 1

    def lat(self, la, lo):
        x, z = self.w.sector_of(la, lo)
        return x, z

    def area_mask(self, refs):
        return self.w.poly_mask(self.w.ring(refs))

    def scatter(self, mask, per_100m2, choices, jitter=0.45, solid=True, scale=(0.85, 1.15), avoid_slope=None):
        """Poisson-ish scatter: per_100m2 plants per 100 m2 (one sector = 4 m2)."""
        xs, zs = np.nonzero(mask)
        p = per_100m2 * 4.0 / 100.0
        names, weights = zip(*choices)
        weights = np.array(weights, float) / sum(weights)
        n = 0
        for x, z in zip(xs, zs):
            if self.r.random() > p or not self.free(x, z, solid):
                continue
            if avoid_slope is not None:
                f = self.w.floor[x, z]
                if f.max() - f.min() > avoid_slope:
                    continue
            name = names[self.r.choice(len(names), p=weights)]
            self.put(name, x + 0.5 + self.r.uniform(-jitter, jitter), z + 0.5 + self.r.uniform(-jitter, jitter),
                     scale=self.r.uniform(*scale))
            n += 1
        return n

    # ----------------------------------------------------------------------------- features
    def vegetation(self, sat=None):
        w = self.w
        if sat and sat.get("trees"):
            for la, lo, kind in sat["trees"]:
                x, z = self.lat(la, lo)
                if self.free(x, z):
                    self.put(kind, x, z, scale=self.r.uniform(0.85, 1.15))
        for wid, (refs, tags) in w.ways.items():
            if not refs or refs[0] != refs[-1]:
                continue
            kind = tags.get("landuse") or tags.get("natural")
            if kind not in ("orchard", "farmland", "wood", "scrub", "grassland", "meadow", "heath"):
                continue
            mask = self.area_mask(refs)
            if not mask.any():
                continue
            if kind == "orchard":
                self.grove(mask)
            elif kind == "farmland":
                self.scatter(mask, 0.6, [("ULIVO", 3), ("ULIVO_GIOVANE", 1), ("FICO_INDIA_GRANDE", 1)])
            elif kind == "wood":
                self.scatter(mask, 2.2, [("PINO_ALEPPO_GRANDE", 4), ("PINO_ALEPPO_INCLINATO", 2), ("PINO_ALEPPO_GIOVANE", 2),
                                         ("ASPARAGO_ROVO", 2)])
            elif kind == "scrub":
                self.scatter(mask, 2.2, [("FICO_INDIA_GRANDE", 1), ("FICO_INDIA_PICCOLO", 1), ("ELICRISO", 3),
                                         ("ELICRISO_GRUPPO", 2), ("ASPARAGO_SELVATICO", 3), ("ASPARAGO_ROVO", 1),
                                         ("PINO_ALEPPO_GIOVANE", 1)], solid=False)
            else:
                self.scatter(mask, 1.2, [("ELICRISO", 3), ("ELICRISO_GRUPPO", 1), ("ASPARAGO_SELVATICO", 2)], solid=False)
        for la, lo, tags in node_tags():
            if tags.get("natural") == "tree":
                x, z = self.lat(la, lo)
                if self.free(x, z):
                    self.put(self.r.choice(["ULIVO", "PINO_ALEPPO_GIOVANE", "ULIVO_GIOVANE"]), x, z)
        # Mediterranean scrub on untagged rocky slopes and around cliffs: sparse.
        rock = (w.mat == "roccia") | (w.mat == "macchia")
        self.scatter(rock, 0.7, [("FICO_INDIA_PICCOLO", 1), ("FICO_INDIA_GRANDE", 1), ("ELICRISO", 3), ("ASPARAGO_SELVATICO", 3)],
                     solid=False)
        dry = (w.mat == "erba_secca") | (w.mat == "terra")
        self.scatter(dry, 0.25, [("ELICRISO", 2), ("ASPARAGO_SELVATICO", 2), ("FICO_INDIA_PICCOLO", 1), ("ULIVO_GIOVANE", 1)],
                     solid=False, avoid_slope=1024)

    def grove(self, mask):
        """Olive grove: rows every 3 sectors (6 m), slight jitter, a few gaps and old trees."""
        xs, zs = np.nonzero(mask)
        off = self.r.integers(0, 3)
        for x, z in zip(xs, zs):
            if (x + off) % 3 or (z + off) % 3 or self.r.random() < 0.12 or not self.free(x, z):
                continue
            name = "ULIVO_SECOLARE" if self.r.random() < 0.1 else ("ULIVO_GIOVANE" if self.r.random() < 0.2 else "ULIVO")
            self.put(name, x + 0.5 + self.r.uniform(-0.25, 0.25), z + 0.5 + self.r.uniform(-0.25, 0.25),
                     scale=self.r.uniform(0.85, 1.1))

    def urban(self, centre=None, lungomare_road=None):
        """Benches, lamps, bars, parked cars, parks, pitches, parking, camp sites."""
        w = self.w
        for la, lo, tags in node_tags():
            x, z = self.lat(la, lo)
            if not (0 <= x < w.nx and 0 <= z < w.nz):
                continue
            if tags.get("amenity") == "bench":
                p = self.near_free(x, z, walk=True)
                if p:
                    self.put("PANCHINA", p[0], p[1], rot=self.face_road(*p))
            elif tags.get("highway") == "street_lamp":
                p = self.near_free(x, z, walk=True)
                if p:
                    self.put("LAMPIONE_PIAZZA", p[0], p[1], solid=True)
            elif tags.get("amenity") in ("bar", "cafe", "restaurant", "ice_cream", "fast_food"):
                self.dehors(x, z)
        for wid, (refs, tags) in w.ways.items():
            if not refs:
                continue
            closed = refs[0] == refs[-1]
            if closed and tags.get("leisure") == "pitch":
                self.pitch(self.area_mask(refs), tags)
            elif closed and tags.get("amenity") == "parking":
                self.parking(self.area_mask(refs))
            elif closed and tags.get("tourism") == "camp_site":
                self.camp(self.area_mask(refs))
            elif closed and tags.get("leisure") == "park":
                self.park(self.area_mask(refs))
            elif closed and tags.get("amenity") in ("restaurant", "cafe", "bar", "fast_food"):
                m = self.area_mask(refs)
                if m.any():
                    xs, zs = np.nonzero(m)
                    self.dehors(xs.mean(), zs.mean())
            elif tags.get("highway") in ROAD_WIDTH and tags.get("highway") not in ("motorway", "trunk", "path", "track", "footway", "steps"):
                if tags.get("tunnel") == "yes" or tags.get("bridge") in ("yes", "viaduct"):
                    continue
                self.road_side(refs, tags, centre, lungomare_road)

    def near_free(self, x, z, walk=False, r=3, solid=True):
        best = None
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cx, cz = int(x) + dx, int(z) + dz
                if not self.free(cx, cz, solid):
                    continue
                if walk and not (self.walk[cx, cz] or self.w.mat[cx, cz] in ("erba_secca", "terra")):
                    continue
                d = dx * dx + dz * dz
                if best is None or d < best[0]:
                    best = (d, cx + 0.5, cz + 0.5)
        return None if best is None else (best[1], best[2])

    def face_road(self, x, z):
        """Rotation (degrees) that turns +Z towards the nearest road sector."""
        ix, iz = int(x), int(z)
        best = None
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                cx, cz = ix + dx, iz + dz
                if 0 <= cx < self.w.nx and 0 <= cz < self.w.nz and self.road[cx, cz]:
                    d = dx * dx + dz * dz
                    if d and (best is None or d < best[0]):
                        best = (d, dx, dz)
        if best is None:
            return self.r.uniform(0, 360)
        return math.degrees(math.atan2(best[1], best[2]))

    def dehors(self, x, z):
        placed = 0
        for k in range(10):
            p = self.near_free(x + self.r.uniform(-3, 3), z + self.r.uniform(-3, 3), walk=True, r=2)
            if not p:
                continue
            name = "DEHORS_OMBRELLONE" if self.r.random() < 0.5 else "DEHORS_TAVOLO"
            self.put(name, p[0], p[1], rot=self.r.choice([0, 90, 180, 270]), solid=True)
            placed += 1
            if placed >= 4:
                break
        p = self.near_free(x, z, walk=True, r=4)
        if p and placed:
            self.put(self.r.choice(["SCOOTER_ROSSO", "SCOOTER_CREMA", "BICICLETTA", "DEHORS_FIORIERA"]), p[0], p[1],
                     rot=self.face_road(*p), solid=True)

    def pitch(self, mask, tags):
        if not mask.any():
            return
        xs, zs = np.nonzero(mask)
        x0, x1, z0, z1 = xs.min(), xs.max(), zs.min(), zs.max()
        edge = mask & ~np.roll(mask, 1, 0) | mask & ~np.roll(mask, -1, 0) | mask & ~np.roll(mask, 1, 1) | mask & ~np.roll(mask, -1, 1)
        for x, z in zip(*np.nonzero(edge)):
            if not self.free(x, z, solid=False):
                continue
            horiz = edge[x - 1, z] or edge[x + 1, z]
            self.put("RECINZIONE_CAMPO", x + 0.5, z + 0.5, rot=0.0 if horiz else 90.0, solid=True)
        for cx, cz in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
            if self.free(cx, cz, solid=False):
                rot = math.degrees(math.atan2((x0 + x1) / 2 - cx, (z0 + z1) / 2 - cz))
                self.put("FARO_CAMPO", cx + 0.5, cz + 0.5, rot=rot, solid=True)
        if tags.get("sport") == "soccer":
            if (x1 - x0) >= (z1 - z0):
                ends = (((x0 + 2), (z0 + z1) / 2, 270.0), ((x1 - 1), (z0 + z1) / 2, 90.0))
            else:
                ends = (((x0 + x1) / 2, z0 + 2, 180.0), ((x0 + x1) / 2, z1 - 1, 0.0))
            for gx, gz, rot in ends:
                if self.free(gx, gz, solid=False):
                    self.put("PORTA_CALCIO", gx + 0.5, gz + 0.5, rot=rot, solid=False)

    def parking(self, mask):
        xs, zs = np.nonzero(mask)
        for x, z in zip(xs, zs):
            if (x % 2) or (z % 3) or self.r.random() < 0.35 or not self.free(x, z, solid=False):
                continue
            self.put(self.r.choice(CARS), x + 0.5, z + 0.5, rot=self.r.choice([0.0, 180.0]) + self.r.uniform(-4, 4), solid=True)

    def camp(self, mask):
        xs, zs = np.nonzero(mask)
        for x, z in zip(xs, zs):
            if (x % 5) or (z % 4) or self.r.random() < 0.4 or not self.free(x, z):
                continue
            self.put("CAMPER" if self.r.random() < 0.7 else self.r.choice(CARS), x + 0.5, z + 0.5,
                     rot=self.r.uniform(0, 360), solid=True)
            if self.free(x + 2, z):
                self.put(self.r.choice(["PINO_ALEPPO_GIOVANE", "ULIVO_GIOVANE", "BICICLETTA"]), x + 2.5, z + 0.5)

    def park(self, mask):
        xs, zs = np.nonzero(mask)
        if len(xs) < 6:
            return
        cx, cz = xs.mean(), zs.mean()
        for name, dx, dz in (("GIOCHI_SCIVOLO", -2, -2), ("GIOCHI_ALTALENA", 2, -2), ("GIOCHI_MOLLA", -2, 2),
                             ("GIOCHI_DONDOLO", 2, 2), ("GIOCHI_CASTELLO", 0, 4)):
            p = self.near_free(cx + dx, cz + dz, r=2)
            if p and mask[int(p[0]), int(p[1])]:
                self.put(name, p[0], p[1], rot=self.r.choice([0, 90, 180, 270]), solid=True)
        for k in range(6):
            p = self.near_free(cx + self.r.uniform(-6, 6), cz + self.r.uniform(-6, 6), r=2)
            if p and mask[int(p[0]), int(p[1])]:
                self.put(self.r.choice(["PANCHINA", "VASO_BIANCO_FIORI", "VASO_BIANCO_PALMA", "VASO_BIANCO_ULIVO"]), p[0], p[1],
                         rot=self.r.choice([0, 90, 180, 270]), solid=True)

    def road_side(self, refs, tags, centre, lungomare_road):
        w = self.w
        line = w.ring(refs)
        half = ROAD_WIDTH[tags["highway"]] / 2.0
        name = tags.get("name", "")
        lung = lungomare_road is not None and name == lungomare_road
        in_centre = centre is not None
        step_lamp = 24.0 if not lung else 20.0
        lit = tags.get("lit") in ("yes", "24/7") or lung or tags["highway"] in ("primary", "secondary", "tertiary")
        dist = 0.0
        next_lamp = self.r.uniform(0, step_lamp)
        next_car = self.r.uniform(5, 20)
        side = 1
        for (xa, za), (xb, zb) in zip(line, line[1:]):
            seg = math.hypot(xb - xa, zb - za)
            if seg < 1e-6:
                continue
            ux, uz = (xb - xa) / seg, (zb - za) / seg
            nx, nz = -uz, ux
            t = 0.0
            while t < seg:
                x, z = xa + ux * t, za + uz * t
                sx, sz = (x - w.ox) / 2.0, (z - w.oz) / 2.0
                if lit and dist + t >= next_lamp:
                    next_lamp += step_lamp
                    side = -side
                    px, pz = sx + nx * side * (half / 2 + 0.6), sz + nz * side * (half / 2 + 0.6)
                    if centre is not None and math.hypot(sx - centre[0], sz - centre[1]) < centre[2]:
                        self.wall_lamp(sx, sz, nx * side, nz * side)
                    elif self.free(px, pz, solid=False):
                        rot = math.degrees(math.atan2(-nx * side, -nz * side))
                        self.put("LAMPIONE_LUNGOMARE" if lung else "LAMPIONE_STRADA", px, pz, rot=rot, solid=True)
                if dist + t >= next_car and tags["highway"] in ("residential", "tertiary", "unclassified", "living_street"):
                    next_car += self.r.uniform(8, 30)
                    s2 = self.r.choice([-1, 1])
                    px, pz = sx + nx * s2 * (half / 2 - 0.6), sz + nz * s2 * (half / 2 - 0.6)
                    if 0 <= int(px) < w.nx and 0 <= int(pz) < w.nz and self.road[int(px), int(pz)] and \
                            not self.blocked[int(px), int(pz)] and not self.taken[int(px), int(pz)] and self.r.random() < 0.55:
                        try:
                            self.ctx.terrain_room_at(int(px), int(pz))
                            rot = math.degrees(math.atan2(ux, uz)) + (180 if self.r.random() < 0.5 else 0)
                            pick = self.r.choice(CARS + ["SCOOTER_ROSSO", "SCOOTER_CREMA"])
                            self.put(pick, px, pz, rot=rot, solid=True)
                        except KeyError:
                            pass
                t += 2.0
            dist += seg

    def wall_lamp(self, sx, sz, nx, nz):
        """Historic centre: lantern on the facade next to the road (arm +Z towards the street)."""
        for k in range(1, 6):
            bx, bz = sx + nx * k, sz + nz * k
            ix, iz = int(bx), int(bz)
            if not (0 <= ix < self.w.nx and 0 <= iz < self.w.nz):
                return
            if self.w.building_id[ix, iz] >= 0:
                px, pz = sx + nx * (k - 0.52), sz + nz * (k - 0.52)
                if int(px) == ix and int(pz) == iz:
                    return
                if not self.free(px, pz, solid=False):
                    return
                rot = math.degrees(math.atan2(-nx, -nz))
                self.put("LAMPIONE_MURO", px, pz, rot=rot, solid=False)
                return

    def sea(self, count=30, near_beach=True):
        """Moored boats on the sea, 15-120 m from the shore, plus a few dinghies pulled up on the beach."""
        w = self.w
        sea = w.water & ~w.lagoon
        if not sea.any():
            return
        from scipy import ndimage
        dist = ndimage.distance_transform_edt(sea)
        cand = np.argwhere((dist > 8) & (dist < 60))
        self.r.shuffle(cand)
        placed = 0
        for x, z in cand:
            if placed >= count:
                break
            if self.taken[x - 3:x + 4, z - 3:z + 4].any() or self.blocked[x, z]:
                continue
            try:
                self.ctx.terrain_room_at(x, z)
            except KeyError:
                continue
            name = self.r.choice(BOATS)
            self.put(name, x + 0.5, z + 0.5, y=0, rot=self.r.uniform(0, 360), solid=True)
            self.taken[x - 3:x + 4, z - 3:z + 4] = True
            placed += 1
        beach = (w.mat == "ciottoli") & ~w.water
        shore = beach & ndimage.binary_dilation(sea, iterations=4)
        cand = np.argwhere(shore)
        self.r.shuffle(cand)
        n = 0
        for x, z in cand:
            if n >= count // 3:
                break
            if not self.free(x, z) or self.taken[x - 2:x + 3, z - 2:z + 3].any():
                continue
            # bow towards the sea
            d = np.argwhere(sea[x - 6:x + 7, z - 6:z + 7])
            if len(d) == 0:
                continue
            vx, vz = (d.mean(axis=0) - 6)
            self.put("BARCHETTA_SPIAGGIA", x + 0.5, z + 0.5, rot=math.degrees(math.atan2(vx, vz)), solid=True)
            self.taken[x - 2:x + 3, z - 2:z + 3] = True
            n += 1
        cand = np.argwhere(beach & ~shore)
        self.r.shuffle(cand)
        for x, z in cand[:count // 2]:
            if self.free(x, z, solid=False):
                self.put("OMBRELLONE_SPIAGGIA", x + 0.5, z + 0.5, solid=False)


def decorate(ctx, centre=None, lungomare_road=None, boats=0):
    d = Decorator(ctx)
    sat = None
    path = os.path.join(ROOT, "build", "satellite", ctx.key + ".json")
    if os.path.exists(path):
        sat = json.load(open(path))
    d.urban(centre=centre, lungomare_road=lungomare_road)
    d.vegetation(sat)
    if boats:
        d.sea(boats)
    total = sum(d.count.values())
    print("  decorations: %d statics %s" % (total, ", ".join("%s %d" % kv for kv in sorted(d.count.items()))))
    ctx.decor_counts = d.count
    return d
