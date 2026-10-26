"""Build the complete Coda di Volpe level: build/Oliveri/Oliveri.prj2 (+ textures, Lua script).

Usage: python3 build_level.py
"""
import json
import os
import shutil
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import prj2  # noqa: E402
import texturing  # noqa: E402
import walls  # noqa: E402
import world as W  # noqa: E402

ROOT = W.ROOT
LEVEL_NAME = "Oliveri"
OUT = os.path.join(ROOT, "build", LEVEL_NAME)
CASA = (38.1241474, 15.0599826)


def main():
    t0 = time.time()
    world = W.World()
    world.build_terrain()
    world.build_materials()
    print("world %dx%d sectors, %d buildings, water %d sectors (%.1fs)" % (
        world.nx, world.nz, len(world.buildings), int(world.water.sum()), time.time() - t0))

    atlas1 = json.load(open(os.path.join(ROOT, "build", "textures", "coda_atlas.json")))
    atlas2 = json.load(open(os.path.join(ROOT, "build", "textures", "coda_atlas2.json")))
    atlases = walls.Atlases([atlas1, atlas2])

    # House style: crema for the building at Via Amodeo 1.
    hx, hz = world.sector_of(*CASA)
    bi, bj = np.nonzero(world.building_id >= 0)
    k = ((bi - hx) ** 2 + (bj - hz) ** 2).argmin()
    casa_id = int(world.building_id[bi[k], bj[k]])
    world.casa_id = casa_id
    styles = texturing.building_styles(world.buildings, casa_id)
    texer = texturing.Texturer(atlas1, world.floor, world.mat, world.building_id, styles,
                               [b["base_m"] for b in world.buildings])

    level = prj2.Level()
    level.use_tombide_ten(LEVEL_NAME + ".ten")
    level.ambient = (0.6, 0.6, 0.6)
    for i, a in enumerate((atlas1, atlas2)):
        level.textures.append({"path": "$(LevelDirectory)\\textures\\coda_atlas%s.png" % ("" if i == 0 else "2"),
                               "footsteps": a["footsteps_64px"]})

    terrain, water = W.build_rooms(world, level, atlases, texer)
    print("rooms: %d terrain, %d water (%.1fs)" % (len(terrain), len(water), time.time() - t0))

    # Temporary start: street in front of the house.
    sx, sz = world.sector_of(38.1242438, 15.0599628)
    i, j = int(sx // W.N), int(sz // W.N)
    room = terrain[i, j]
    fy = world.floor[int(sx), int(sz)].mean() - room.y
    level.add_moveable(room, 0, ((sx - room.x) * 1024, float(fy), (sz - room.z) * 1024), rot_y=170.0, lua_name="lara_start")

    os.makedirs(os.path.join(OUT, "textures"), exist_ok=True)
    for f in ("coda_atlas.png", "coda_atlas2.png"):
        shutil.copy(os.path.join(ROOT, "build", "textures", f), os.path.join(OUT, "textures", f))
    size = level.save(os.path.join(OUT, LEVEL_NAME + ".prj2"))
    print("saved %.1f MB, %d rooms (%.1fs)" % (size / 1e6, len(level.rooms), time.time() - t0))
    return world, level, terrain, water


if __name__ == "__main__":
    main()
