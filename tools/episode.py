"""Coda di Volpe episode: six TombEngine levels, each a real-scale piece of the map (< 800 m).

Usage: python3 episode.py [level ...]      (default: all)
Each level is written to build/levels/<Name>/<Name>.prj2 with its textures and Lua script.
Level content (interiors, objects, triggers, Lua) lives in content_<name>.py modules:
  prepare(world)  optional, edits terrain arrays before rooms are built (paths, gates, holes)
  build(ctx)      adds rooms, objects, triggers and the level script
  build_standalone(ctx) for levels without terrain (Sommersa)
"""
import importlib
import json
import os
import shutil
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import kit as K  # noqa: E402
import luagen  # noqa: E402
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
    "Tindari":   {"title": "Tindari", "box": (38.1378, 15.0412, 38.1446, 15.0496)},
    "Sommersa":  {"title": "La Citta' Sommersa", "box": None},
    "Titolo":    {"title": "Coda di Volpe", "box": (38.1378, 15.0412, 38.1446, 15.0496), "ten": "title.ten"},
}
ORDER = ["Oliveri", "Lungomare", "Marinello", "Laghetti", "Tindari", "Sommersa"]
INDEX = {k: i + 1 for i, k in enumerate(ORDER)}   # Gameflow: 0 = title

# Full-screen videos (Engine\FMV\<name>.mp4) played when a level starts; missing files are skipped by the engine.
VIDEOS = {"Oliveri": "cdv_intro", "Lungomare": "cdv_02_lungomare", "Marinello": "cdv_03_marinello",
          "Laghetti": "cdv_04_laghetti", "Tindari": "cdv_05_tindari", "Sommersa": "cdv_06_sommersa"}

WADS = ["TombEngine.wad2"] + ["CodaDiVolpe\\%s.wad2" % w for w in (
    "CdV_Oggetti_A", "CdV_Oggetti_B", "TR4_Baddy1", "TR4_Baddy2", "TR2_Doberman", "TR1_Rat", "TR4_Bat",
    "TEN_Wraith", "TR5_Lagoon_Witch", "TR2_Shark", "TR4_Skeleton", "TR4_Doors", "TR5_Floor_Trapdoor",
    "TR4_Lever_Switch", "TR4_Rolling_Ball", "TR1_Teeth_Spikes", "TEN_Fish_Emitter", "TEN_Firefly",
    "CdV_Decorazioni")]

# Puzzle items: slot -> (Strings key, Italian name). Same slots in every level (inventory carries over).
ITEMS = {
    1: ("cdv_diario", "Diario bizantino"),
    2: ("cdv_chiave_terrazza", "Chiave della terrazza"),
    3: ("cdv_mappa_maree", "Mappa delle maree"),
    4: ("cdv_chiave_casello", "Chiave del Casello"),
    5: ("cdv_conchiglia", "Conchiglia del canto"),
    6: ("cdv_sigillo", "Sigillo della tonnara"),
    7: ("cdv_astro_castore", "Astro di Castore"),
    8: ("cdv_astro_polluce", "Astro di Polluce"),
}


class Ctx:
    """Everything a content module needs to add rooms, objects and triggers."""

    def __init__(self, key, world, level, atlases, terrain, water):
        self.key = key
        self.world = world
        self.level = level
        self.atlases = atlases
        self.terrain = terrain
        self.water = water
        self.kit = K.Kit(self)
        self.lua = luagen.LuaLevel(LEVELS[key]["title"], key)
        self.notes = []        # walkthrough lines

    def sector(self, lat, lon):
        x, z = self.world.sector_of(lat, lon)
        return int(x), int(z)

    def ground(self, wx, wz):
        """Terrain floor (units, absolute) at world sector (wx, wz)."""
        return int(self.world.floor[int(wx), int(wz)].mean())

    def terrain_room_at(self, wx, wz):
        i, j = (int(wx) - 1) // W.N, (int(wz) - 1) // W.N
        if (i, j) in self.terrain:
            return self.terrain[i, j]
        raise KeyError("no terrain room at %s" % ((wx, wz),))

    def water_room_at(self, wx, wz):
        i, j = (int(wx) - 1) // W.N, (int(wz) - 1) // W.N
        return self.water.get((i, j))


def make_level():
    level = prj2.Level()
    level.ambient = (0.6, 0.6, 0.6)
    return level


def load_atlases():
    out = []
    for name in ("coda_atlas", "coda_atlas2", "coda_atlas3"):
        out.append(json.load(open(os.path.join(ROOT, "build", "textures", name + ".json"))))
    return out


def setup_textures(level, atlas_list):
    for i, a in enumerate(atlas_list):
        level.textures.append({"path": "$(LevelDirectory)\\textures\\coda_atlas%s.png" % ("" if i == 0 else str(i + 1)),
                               "footsteps": a["footsteps_64px"]})


def build_terrain_level(key, content):
    t0 = time.time()
    la0, lo0, la1, lo1 = LEVELS[key]["box"]
    world = W.World({key: [(la0, lo0), (la0, lo1), (la1, lo1), (la1, lo0)]})
    world.build_terrain()
    world.build_materials()
    if content is not None and hasattr(content, "prepare"):
        content.prepare(world)

    atlas_list = load_atlases()
    atlases = walls.Atlases(atlas_list)
    casa = (38.1241474, 15.0599826)
    hx, hz = world.sector_of(*casa)
    casa_id = None
    if 0 <= hx < world.nx and 0 <= hz < world.nz:
        bi, bj = np.nonzero(world.building_id >= 0)
        k = ((bi - hx) ** 2 + (bj - hz) ** 2).argmin()
        casa_id = int(world.building_id[bi[k], bj[k]])
    world.casa_id = casa_id
    styles = texturing.building_styles(world.buildings, casa_id)
    texer = texturing.Texturer(atlas_list[0], world.floor, world.mat, world.building_id, styles,
                               [b["base_m"] for b in world.buildings])

    level = make_level()
    level.use_tombide_ten(LEVELS[key].get("ten", key + ".ten"), wads=WADS)
    setup_textures(level, atlas_list)
    terrain, water = W.build_rooms(world, level, atlases, texer)
    print("%s: %dx%d sectors, %d terrain + %d water rooms (%.1fs)" % (
        key, world.nx, world.nz, len(terrain), len(water), time.time() - t0))
    return Ctx(key, world, level, atlases, terrain, water)


def save(ctx):
    out = os.path.join(OUT, ctx.key)
    os.makedirs(os.path.join(out, "textures"), exist_ok=True)
    for f in ("coda_atlas.png", "coda_atlas2.png", "coda_atlas3.png"):
        shutil.copy(os.path.join(ROOT, "build", "textures", f), os.path.join(out, "textures", f))
    size = ctx.level.save(os.path.join(out, ctx.key + ".prj2"))
    with open(os.path.join(out, ctx.key + ".lua"), "w", newline="\r\n") as f:
        f.write(ctx.lua.text())
    with open(os.path.join(out, ctx.key + ".names.json"), "w") as f:
        json.dump(ctx.kit.names, f, indent=0)
    import shots
    shots.save(ctx, out)
    if ctx.notes:
        with open(os.path.join(out, "soluzione.txt"), "w") as f:
            f.write("\n".join(ctx.notes) + "\n")
    print("%s saved: %.1f MB, %d rooms, pathfinding in %d rooms" % (
        ctx.key, size / 1e6, len(ctx.level.rooms), sum(1 for r in ctx.level.rooms if not r.no_path)))
    return size


GAMEFLOW_HEAD = """-- Coda di Volpe - Gameflow.lua (generato da tools/episode.py)
-- Va in C:\\CodaDiVolpe\\Engine\\Scripts\\Gameflow.lua

-- ============ IMPOSTAZIONI (cambiare solo queste tre righe) ============
local CDV_RELEASE = false     -- true per la versione da pubblicare: niente fly cheat, niente selezione livello
local CDV_SCHERMATE = false   -- true quando ci sono Screens\\cdv_oliveri.jpg ... cdv_sommersa.jpg (schermate di caricamento)
local CDV_LOGO = nil          -- es. "FMV\\\\cdv_logo.mp4": video all'avvio del gioco, prima del titolo
-- ======================================================================

Flow.SetIntroImagePath("Screens\\\\intro.jpg")
if CDV_LOGO then Flow.SetIntroVideoPath(CDV_LOGO) end
Flow.SetTotalSecretCount(12)
Flow.EnablePointFilter(false)
Flow.EnableLoadSave(true)
Flow.EnableFlyCheat(not CDV_RELEASE)
Flow.EnableLaraInTitle(false)
Flow.EnableLevelSelect(not CDV_RELEASE)
Flow.EnableMassPickup(true)

local function Schermata(name)
    if CDV_SCHERMATE then return "Screens\\\\cdv_" .. name .. ".jpg" end
    return "Screens\\\\loading.png"
end

-- Nomi degli oggetti e dei livelli (si sommano a Strings.lua).
TEN.Flow.SetStrings({
%s
})

local function CdvObjects()
    local Rot, Axis, Act, ID = TEN.Rotation, TEN.Flow.RotationAxis, TEN.Flow.ItemAction, TEN.Objects.ObjID
    return {
%s
    }
end

--------------------------------------------------

title = Level.new()
title.ambientTrack = "108"
title.levelFile = "Data\\\\title.ten"
title.scriptFile = "Scripts\\\\Levels\\\\title.lua"
title.loadScreenFile = "Screens\\\\main.png"
Flow.AddLevel(title)
"""

LEVEL_FLOW = {
    "Oliveri": {"track": "108", "fog": None, "far": 96},
    "Lungomare": {"track": "108", "fog": None, "far": 128},
    "Marinello": {"track": "108", "fog": None, "far": 128},
    "Laghetti": {"track": "108", "fog": None, "far": 128},
    "Tindari": {"track": "108", "fog": None, "far": 160},
    "Sommersa": {"track": "108", "fog": (20, 60, 70, 6, 24), "far": 40},
}


def write_gameflow(only=None):
    strings = ["    %s = { %s }," % (k, luagen.lua_str(name)) for k, name in ITEMS.values()]
    strings += ["    cdv_level_%s = { %s }," % (k.lower(), luagen.lua_str(LEVELS[k]["title"])) for k in ORDER]
    objs = ["        TEN.Flow.InventoryItem(%s, ID.PUZZLE_ITEM%d, 0, 0.5, Rot(0, 0, 0), Axis.Y, -1, Act.USE)," % (
        luagen.lua_str(k), i) for i, (k, _) in ITEMS.items()]
    parts = [GAMEFLOW_HEAD % ("\n".join(strings), "\n".join(objs))]
    for k in ORDER:
        if only is not None and k not in only:
            continue
        if not os.path.exists(os.path.join(OUT, k, k + ".prj2")):
            continue  # level not generated yet: keep it out of the level select
        lf = LEVEL_FLOW[k]
        block = """
--------------------------------------------------

{k} = TEN.Flow.Level()
{k}.nameKey = "cdv_level_{lk}"
{k}.scriptFile = "Scripts\\\\Levels\\\\{k}.lua"
{k}.ambientTrack = "{track}"
{k}.horizon1.enabled = {hz}
{k}.levelFile = "Data\\\\{k}.ten"
{k}.loadScreenFile = Schermata("{lk}")
{k}.farView = {far}
{k}.objects = CdvObjects()
""".format(k=k, lk=k.lower(), track=lf["track"], far=lf["far"], hz="false" if k == "Sommersa" else "true")
        if lf["fog"]:
            r, g, b, mn, mx = lf["fog"]
            block += "{k}.fog = TEN.Flow.Fog(TEN.Color({r}, {g}, {b}), {mn}, {mx})\n".format(k=k, r=r, g=g, b=b, mn=mn, mx=mx)
        block += "TEN.Flow.AddLevel({k})\n".format(k=k)
        parts.append(block)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "Gameflow.lua"), "w", newline="\r\n") as f:
        f.write("".join(parts))


def build(key):
    content = importlib.import_module("content_" + key.lower())
    if LEVELS[key]["box"] is None:
        level = make_level()
        level.use_tombide_ten(key + ".ten", wads=WADS)
        atlas_list = load_atlases()
        setup_textures(level, atlas_list)
        ctx = Ctx(key, None, level, walls.Atlases(atlas_list), {}, {})
        content.build_standalone(ctx)
    else:
        ctx = build_terrain_level(key, content)
        content.build(ctx)
        import shots
        shots.place_level(ctx, key)
        import decorate
        decorate.decorate(ctx, **getattr(content, "DECOR", {}))
    ctx.lua.video = VIDEOS.get(key)
    ctx.kit.finish_interiors()
    probs = K.validate(ctx.level, ctx.kit.names)
    for pr in probs:
        print("  CHECK:", pr)
    save(ctx)
    return ctx


if __name__ == "__main__":
    for k in (sys.argv[1:] or ORDER):
        build(k)
    write_gameflow()
