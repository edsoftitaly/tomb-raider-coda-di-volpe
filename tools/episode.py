"""Coda di Volpe episode: six TombEngine levels, each a real-scale piece of the map (< 800 m).

Usage: python3 episode.py [level ...]      (default: all)
Each level is written to build/levels/<Name>/<Name>.prj2 with its textures folder.
Level content (interiors, objects, triggers, Lua) lives in content_<name>.py modules.
"""
import importlib
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
OUT = os.path.join(ROOT, "build", "levels")

# Level boxes: (lat_min, lon_min, lat_max, lon_max). All under 800 m per side.
LEVELS = {
    "Oliveri":   {"title": "Oliveri", "box": (38.1214, 15.0552, 38.1278, 15.0612)},
    "Lungomare": {"title": "Il Lungomare", "box": (38.1272, 15.0508, 38.1340, 15.0590)},
    "Marinello": {"title": "Marinello", "box": (38.1336, 15.0482, 38.1404, 15.0566)},
    "Laghetti":  {"title": "I Laghetti", "box": (38.1388, 15.0474, 38.1456, 15.0562)},
    "Tindari":   {"title": "Tindari", "box": (38.1370, 15.0418, 38.1438, 15.0502)},
    "Sommersa":  {"title": "La Citta' Sommersa", "box": None},
}
ORDER = ["Oliveri", "Lungomare", "Marinello", "Laghetti", "Tindari", "Sommersa"]


class Ctx:
    """Everything a content module needs to add rooms, objects and triggers."""

    def __init__(self, key, world, level, atlases, terrain, water):
        self.key = key
        self.world = world
        self.level = level
        self.atlases = atlases
        self.terrain = terrain
        self.water = water
        self.lua = []          # extra Lua lines for the level script
        self.notes = []        # walkthrough notes

    # Coordinates
    def sector(self, lat, lon):
        return self.world.sector_of(lat, lon)

    def ground(self, wx, wz):
        """Terrain floor (units, absolute) at world sector (wx, wz)."""
        return int(self.world.floor[int(wx), int(wz)].mean())

    def terrain_room_at(self, wx, wz):
        i, j = int(wx // W.N), int(wz // W.N)
        if (i, j) in self.terrain:
            return self.terrain[i, j]
        raise KeyError("no terrain room at %s" % ((wx, wz),))

    def local(self, room, wx, wz, y_abs):
        return ((wx - room.x) * 1024.0, float(y_abs - room.y), (wz - room.z) * 1024.0)


def build_terrain_level(key):
    t0 = time.time()
    la0, lo0, la1, lo1 = LEVELS[key]["box"]
    zones = {key: [(la0, lo0), (la0, lo1), (la1, lo1), (la1, lo0)]}
    world = W.World(zones)
    world.build_terrain()
    world.build_materials()

    atlas1 = json.load(open(os.path.join(ROOT, "build", "textures", "coda_atlas.json")))
    atlas2 = json.load(open(os.path.join(ROOT, "build", "textures", "coda_atlas2.json")))
    atlas3 = json.load(open(os.path.join(ROOT, "build", "textures", "coda_atlas3.json")))
    atlases = walls.Atlases([atlas1, atlas2, atlas3])

    casa = (38.1241474, 15.0599826)
    hx, hz = world.sector_of(*casa)
    casa_id = None
    if 0 <= hx < world.nx and 0 <= hz < world.nz:
        bi, bj = np.nonzero(world.building_id >= 0)
        k = ((bi - hx) ** 2 + (bj - hz) ** 2).argmin()
        casa_id = int(world.building_id[bi[k], bj[k]])
    world.casa_id = casa_id
    styles = texturing.building_styles(world.buildings, casa_id)
    texer = texturing.Texturer(atlas1, world.floor, world.mat, world.building_id, styles,
                               [b["base_m"] for b in world.buildings])

    level = prj2.Level()
    level.use_tombide_ten(key + ".ten")
    level.ambient = (0.6, 0.6, 0.6)
    for i, a in enumerate((atlas1, atlas2, atlas3)):
        level.textures.append({"path": "$(LevelDirectory)\\textures\\coda_atlas%s.png" % ("" if i == 0 else str(i + 1)),
                               "footsteps": a["footsteps_64px"]})
    terrain, water = W.build_rooms(world, level, atlases, texer)
    print("%s: %dx%d sectors, %d terrain + %d water rooms (%.1fs)" % (
        key, world.nx, world.nz, len(terrain), len(water), time.time() - t0))
    return Ctx(key, world, level, atlases, terrain, water)


def default_start(ctx):
    """Lara on dry land near the middle of the level (for terrain tests)."""
    w = ctx.world
    cx, cz = w.nx // 2, w.nz // 2
    best = None
    for r in range(0, max(w.nx, w.nz)):
        for wx in range(max(1, cx - r), min(w.nx - 1, cx + r + 1)):
            for wz in (cz - r, cz + r):
                if 1 <= wz < w.nz - 1 and not w.water[wx, wz] and w.building_id[wx, wz] < 0 and w.zone_mask[wx, wz]:
                    try:
                        ctx.terrain_room_at(wx, wz)
                    except KeyError:
                        continue
                    best = (wx, wz)
                    break
            if best:
                break
        if best:
            break
    wx, wz = best
    room = ctx.terrain_room_at(wx, wz)
    room.no_path = False  # at least one room with pathfinding boxes
    ctx.level.add_moveable(room, 0, ctx.local(room, wx + 0.5, wz + 0.5, ctx.ground(wx, wz)), lua_name="lara_start")


def save(ctx):
    out = os.path.join(OUT, ctx.key)
    os.makedirs(os.path.join(out, "textures"), exist_ok=True)
    for f in ("coda_atlas.png", "coda_atlas2.png", "coda_atlas3.png"):
        shutil.copy(os.path.join(ROOT, "build", "textures", f), os.path.join(out, "textures", f))
    size = ctx.level.save(os.path.join(out, ctx.key + ".prj2"))
    write_lua(ctx, out)
    print("%s saved: %.1f MB, %d rooms" % (ctx.key, size / 1e6, len(ctx.level.rooms)))
    return size


LUA_TEMPLATE = """-- Coda di Volpe - script del livello {title} (TombEngine).
-- Va in C:\\CodaDiVolpe\\Engine\\Scripts\\Levels\\{key}.lua  (generato da tools/episode.py)

{body}

-- Called when entering a level, either after leveljump, new game or loading game
LevelFuncs.OnStart = function()
{on_start}
end

-- Called after loading from a save
LevelFuncs.OnLoad = function() end

-- Called after saving game
LevelFuncs.OnSave = function() end

-- Called on every frame of the game
LevelFuncs.OnLoop = function()
{on_loop}
end

-- Called when level is ended, either after leveljump, quitting to title or loading game
LevelFuncs.OnEnd = function() end
"""


def write_lua(ctx, out):
    lua = getattr(ctx, "lua_parts", {})
    text = LUA_TEMPLATE.format(title=LEVELS[ctx.key]["title"], key=ctx.key,
                               body="\n".join(ctx.lua) if ctx.lua else "-- (nessuna logica extra)",
                               on_start="\n".join(lua.get("start", [])),
                               on_loop="\n".join(lua.get("loop", [])))
    with open(os.path.join(out, ctx.key + ".lua"), "w", newline="\r\n") as f:
        f.write(text)


GAMEFLOW_HEAD = """-- Coda di Volpe - Gameflow.lua (generato da tools/episode.py)
-- Va in C:\\CodaDiVolpe\\Engine\\Scripts\\Gameflow.lua

Flow.SetIntroImagePath("Screens\\\\intro.jpg")
Flow.SetTotalSecretCount(12)
Flow.EnablePointFilter(false)
Flow.EnableLoadSave(true)
Flow.EnableFlyCheat(true)      -- sviluppo: da disattivare per la release
Flow.EnableLaraInTitle(false)
Flow.EnableLevelSelect(true)   -- sviluppo: comodo per provare i singoli livelli
Flow.EnableMassPickup(true)

--------------------------------------------------

title = Level.new()
title.ambientTrack = "108"
title.levelFile = "Data\\\\title.ten"
title.scriptFile = "Scripts\\\\Levels\\\\title.lua"
title.loadScreenFile = "Screens\\\\main.png"
Flow.AddLevel(title)
"""


def write_gameflow(only=None):
    parts = [GAMEFLOW_HEAD]
    for k in ORDER:
        if only is not None and k not in only:
            continue
        if not os.path.exists(os.path.join(OUT, k, k + ".prj2")):
            continue  # level not generated yet: keep it out of the level select
        parts.append('''
--------------------------------------------------

{k} = TEN.Flow.Level()
{k}.nameKey = "{k}"
{k}.scriptFile = "Scripts\\\\Levels\\\\{k}.lua"
{k}.ambientTrack = "108"
{k}.horizon1.enabled = true
{k}.levelFile = "Data\\\\{k}.ten"
{k}.loadScreenFile = "Screens\\\\loading.png"
{k}.farView = 128 -- distanza di visibilita' in settori (128 = 256 m)
TEN.Flow.AddLevel({k})
'''.format(k=k))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "Gameflow.lua"), "w", newline="\r\n") as f:
        f.write("".join(parts))


def build(key):
    try:
        content = importlib.import_module("content_" + key.lower())
    except ImportError:
        content = None
    if LEVELS[key]["box"] is None:
        ctx = content.build_standalone(key) if content else None
    else:
        ctx = build_terrain_level(key)
        if content:
            content.build(ctx)
        else:
            default_start(ctx)
    if ctx is not None:
        save(ctx)
    return ctx


if __name__ == "__main__":
    for k in (sys.argv[1:] or ORDER):
        build(k)
    write_gameflow()
