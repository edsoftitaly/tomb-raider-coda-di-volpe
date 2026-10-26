"""Generate a Tomb Editor (.prj2, TombEngine) terrain block for one zone of Coda di Volpe.

Real scale: 1 sector = 2 m = 1024 units, DTM SITR 2 m (EPSG:3004) sampled at sector corners.
Buildings come from OpenStreetMap footprints, extruded as solid blocks you can climb on.
The zone is tiled in rooms of (N+2) x (N+2) sectors with stride N, as Tomb Editor does when
splitting rooms: neighbouring rooms overlap by two sectors and share wall portals.

Usage: python3 gen_zone.py A   (zones are defined in ZONES below)
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from matplotlib.path import Path
from pyproj import Transformer

sys.path.insert(0, os.path.dirname(__file__))
import prj2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DTM = os.path.join(ROOT, "data", "dtm", "dtm_2m_3004.tif")
OSM = [os.path.join(ROOT, "data", "osm", f) for f in ("Oliveri.osm", "Tindari.osm")]

M = 512            # units per metre (1024 units = 2 m)
QUANT = 64         # height quantization: 1/4 click = 12.5 cm
ROOM_N = 30        # interior sectors per room side
HEADROOM = 12 * prj2.CLICK  # ceiling above the highest floor of a room

# Zone boxes (lat_min, lon_min, lat_max, lon_max) and points of interest.
ZONES = {
    "A": {"name": "Oliveri centro", "box": (38.1212, 15.0555, 38.1262, 15.0625)},
    "C": {"name": "Marinello e laghetti", "box": (38.1338, 15.0478, 38.1452, 15.0560)},
    "D": {"name": "Rupe e Tindari", "box": (38.1372, 15.0390, 38.1462, 15.0478)},
}
POI = {
    "casa_amodeo_1": (38.1241474, 15.0599826),
    "lara_start": (38.1242438, 15.0599628),   # street in front of the house (Street View point)
}

# Default heights (m) when OSM has no building:levels / height.
DEFAULT_HEIGHT = {"apartments": 12.5, "church": 12.0, "civic": 9.5, "house": 7.0, "yes": 9.5,
                  "roof": 3.5, "garage": 3.0, "castle": 8.0}
LEVEL_HEIGHT = 3.2

to3004 = Transformer.from_crs(4326, 3004, always_xy=True)


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


def ring_xy(refs, nodes):
    pts = [nodes[r] for r in refs if r in nodes]
    return [to3004.transform(lo, la) for la, lo in pts]


def building_height(tags):
    if "height" in tags:
        try:
            return float(tags["height"].split()[0])
        except ValueError:
            pass
    if "building:levels" in tags:
        try:
            return float(tags["building:levels"]) * LEVEL_HEIGHT + 1.0
        except ValueError:
            pass
    if tags.get("historic") == "castle":
        return DEFAULT_HEIGHT["castle"]
    return DEFAULT_HEIGHT.get(tags.get("building", "yes"), DEFAULT_HEIGHT["yes"])


def build(zone_key):
    zone = ZONES[zone_key]
    la0, lo0, la1, lo1 = zone["box"]
    ds = rasterio.open(DTM)
    dtm = ds.read(1).astype(np.float64)
    dtm[dtm < -100] = 0.0  # nodata in the sea corner

    # Corner grid aligned with DTM pixel centres.
    x0, z0 = to3004.transform(lo0, la0)
    x1, z1 = to3004.transform(lo1, la1)
    col0 = int(math.floor((x0 - ds.bounds.left) / 2.0))
    col1 = int(math.ceil((x1 - ds.bounds.left) / 2.0))
    row_top = int(math.floor((ds.bounds.top - z1) / 2.0))
    row_bot = int(math.ceil((ds.bounds.top - z0) / 2.0))
    nsx = -(-(col1 - col0) // ROOM_N) * ROOM_N   # interior sectors, rounded up to ROOM_N
    nsz = -(-(row_bot - row_top) // ROOM_N) * ROOM_N
    # World sectors run from -1 to nsx (border ring), corners from -1 to nsx+1.
    corner_cols = np.arange(col0 - 1, col0 + nsx + 2)
    corner_rows = np.arange(row_top + nsz + 1, row_top - 2, -1)  # z grows north = rows decrease
    corner_cols = np.clip(corner_cols, 0, dtm.shape[1] - 1)
    corner_rows = np.clip(corner_rows, 0, dtm.shape[0] - 1)
    H = dtm[np.ix_(corner_rows, corner_cols)].T   # H[cx, cz], cx/cz offset by +1
    origin_x = ds.bounds.left + 1.0 + 2.0 * (col0 - 1)        # metres, corner (-1, -1)
    origin_z = ds.bounds.top - 1.0 - 2.0 * (row_top + nsz + 1)

    def world_to_sector(x, z):
        return (x - origin_x) / 2.0 - 1.0, (z - origin_z) / 2.0 - 1.0

    # Floor heights per sector corner (units), sector index offset by +1.
    nwx, nwz = nsx + 2, nsz + 2
    floor = np.zeros((nwx, nwz, 4), dtype=np.int64)
    # Edge order XnZp, XpZp, XpZn, XnZn
    floor[:, :, 0] = (H[:-1, 1:] * M)
    floor[:, :, 1] = (H[1:, 1:] * M)
    floor[:, :, 2] = (H[1:, :-1] * M)
    floor[:, :, 3] = (H[:-1, :-1] * M)
    floor = (np.round(floor / QUANT) * QUANT).astype(np.int64)

    # Buildings.
    nodes, ways, rels = load_osm()
    gx, gz = np.meshgrid(np.arange(nwx), np.arange(nwz), indexing="ij")
    centres = np.stack([origin_x + 2.0 * gx + 1.0, origin_z + 2.0 * gz + 1.0], axis=-1).reshape(-1, 2)
    building_id = np.full(nwx * nwz, -1, dtype=np.int64)
    roof = np.zeros(nwx * nwz)
    buildings = []

    def add_building(outer, inners, tags, ident):
        if len(outer) < 3:
            return
        p = Path(outer)
        bb = p.get_extents()
        if bb.x1 < origin_x or bb.x0 > origin_x + 2 * (nwx + 1) or bb.y1 < origin_z or bb.y0 > origin_z + 2 * (nwz + 1):
            return
        inside = p.contains_points(centres)
        for ring in inners:
            if len(ring) >= 3:
                inside &= ~Path(ring).contains_points(centres)
        if not inside.any():
            return
        idx = np.nonzero(inside)[0]
        cx, cz = idx // nwz, idx % nwz
        ground = floor[cx, cz].max() / M
        top = ground + building_height(tags)
        bid = len(buildings)
        building_id[idx] = bid
        roof[idx] = top
        buildings.append({"id": ident, "tags": tags, "sectors": int(len(idx)), "ground_m": round(float(ground), 2),
                          "roof_m": round(float(top), 2)})

    for wid, (refs, tags) in ways.items():
        if "building" in tags and refs and refs[0] == refs[-1]:
            add_building(ring_xy(refs, nodes), [], tags, "way/" + wid)
    for members, tags in rels:
        if "building" in tags or tags.get("historic") == "castle":
            outers = [ring_xy(ways[ref][0], nodes) for t, ref, role in members if t == "way" and role == "outer" and ref in ways]
            inners = [ring_xy(ways[ref][0], nodes) for t, ref, role in members if t == "way" and role == "inner" and ref in ways]
            for o in outers:
                add_building(o, inners, tags, "relation")

    building_id = building_id.reshape(nwx, nwz)
    roof = roof.reshape(nwx, nwz)
    is_b = building_id >= 0
    floor[is_b] = (np.round(roof[is_b] * M / QUANT) * QUANT).astype(np.int64)[:, None]

    # Rooms.
    level = prj2.Level()
    level.ambient = (0.6, 0.6, 0.6)
    nrx, nrz = nsx // ROOM_N, nsz // ROOM_N
    grid = {}
    for i in range(nrx):
        for j in range(nrz):
            # Room covers world sectors [i*N-1, i*N+N] -> array index +1.
            sx0, sz0 = i * ROOM_N, j * ROOM_N
            block = floor[sx0:sx0 + ROOM_N + 2, sz0:sz0 + ROOM_N + 2]
            y = int(math.floor(block.min() / prj2.CLICK)) * prj2.CLICK
            ceil = int(block.max()) - y + HEADROOM
            room = prj2.Room("%s_%02d_%02d" % (zone_key, i, j), ROOM_N + 2, ROOM_N + 2,
                             x=sx0 - 1, y=y, z=sz0 - 1)
            room.outside = True
            room.horizon = True
            room.ambient = level.ambient
            room.tags = ["zona" + zone_key, "terreno"]
            for lx in range(ROOM_N + 2):
                for lz in range(ROOM_N + 2):
                    s = room.sectors[lx][lz]
                    f = block[lx, lz] - y
                    s.floor = [int(v) for v in f]
                    s.ceil = [ceil] * 4
                    # Split along the flatter diagonal.
                    s.fsplit = abs(int(f[0]) - int(f[2])) < abs(int(f[1]) - int(f[3]))
            grid[i, j] = level.add_room(room)

    for (i, j), room in grid.items():
        n = ROOM_N + 2
        if (i + 1, j) in grid:
            other = grid[i + 1, j]
            level.add_portal(room, (n - 1, 1, n - 1, n - 2), prj2.P_WALL_PX, other)
            level.add_portal(other, (0, 1, 0, n - 2), prj2.P_WALL_NX, room)
        if (i, j + 1) in grid:
            other = grid[i, j + 1]
            level.add_portal(room, (1, n - 1, n - 2, n - 1), prj2.P_WALL_PZ, other)
            level.add_portal(other, (1, 0, n - 2, 0), prj2.P_WALL_NZ, room)

    # Lara in front of Via Gaspare Amodeo 1 (zone A only).
    report = {"zone": zone_key, "name": zone["name"], "sectors": [nsx, nsz], "rooms": len(level.rooms),
              "size_m": [nsx * 2, nsz * 2], "origin_3004": [origin_x, origin_z], "buildings": len(buildings)}
    la, lo = POI["lara_start"]
    sx, sz = world_to_sector(*to3004.transform(lo, la))
    if 0 <= sx < nsx and 0 <= sz < nsz:
        i, j = int(sx // ROOM_N), int(sz // ROOM_N)
        room = grid[i, j]
        lx, lz = sx - room.x, sz - room.z
        fy = floor[int(sx) + 1, int(sz) + 1].mean() - room.y
        # Face south-east towards the house door (rotation in degrees, 0 = +Z).
        level.add_moveable(room, 0, (lx * 1024, float(fy), lz * 1024), rot_y=170.0, lua_name="lara_start")
        report["lara"] = {"room": room.name, "local_sector": [round(lx, 2), round(lz, 2)], "floor_m": round((fy + room.y) / M, 2)}
        la_h, lo_h = POI["casa_amodeo_1"]
        hx, hz = world_to_sector(*to3004.transform(lo_h, la_h))
        bid = building_id[int(hx) + 1, int(hz) + 1] if building_id[int(hx) + 1, int(hz) + 1] >= 0 else None
        report["casa"] = buildings[bid] if bid is not None else "civico 1 sul bordo dell'edificio"

    out_dir = os.path.join(ROOT, "build")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "zona_%s.prj2" % zone_key)
    report["bytes"] = level.save(path)
    with open(os.path.join(out_dir, "zona_%s_report.json" % zone_key), "w") as f:
        json.dump({"report": report, "buildings": buildings}, f, indent=1, ensure_ascii=False)
    np.save(os.path.join(out_dir, "zona_%s_floor.npy" % zone_key), floor)
    np.save(os.path.join(out_dir, "zona_%s_buildings.npy" % zone_key), building_id)
    return report


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else "A"), indent=1, ensure_ascii=False))
