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
    # Small zones in a frame aligned with the main street (World(frame=...)): pivot lat, lon, angle, (u0, v0, u1, v1) m.
    "Oliveri":   {"title": "Prologo - Via Amodeo", "box": "frame",
                  "frame": (38.124132, 15.059829, -33.85, (-40.0, -40.0, 124.0, 40.0))},
    "Lungomare": {"title": "Il Lungomare", "box": "frame", "frame": (38.1300, 15.0548, 0.0, (0.0, 0.0, 118.0, 118.0))},
    "Marinello": {"title": "La maga dei laghetti", "box": "frame", "frame": (38.1420, 15.0515, 0.0, (0.0, 0.0, 236.0, 236.0))},
    "MarinelloB": {"title": "La maga dei laghetti (riserva, senza flipmap)", "box": "frame",
                   "frame": (38.1420, 15.0515, 0.0, (0.0, 0.0, 236.0, 236.0))},
    "Laghetti":  {"title": "I Laghetti", "box": "frame", "frame": (38.1420, 15.0515, 0.0, (0.0, 0.0, 118.0, 118.0))},
    "Tindari":   {"title": "Tindari", "box": "frame", "frame": (38.1412, 15.0454, 0.0, (0.0, 0.0, 176.0, 176.0))},
    "Sommersa":  {"title": "La meta' perduta", "box": None},
    "Collaudo":  {"title": "Collaudo (test)", "box": None},
    "Titolo":    {"title": "Coda di Volpe", "box": (38.1378, 15.0412, 38.1446, 15.0496), "ten": "title.ten"},
}
ORDER = ["Oliveri", "Marinello", "Tindari", "Collaudo", "MarinelloB", "Sommersa"]      # GDD v3: prologue + 3 levels
INDEX = {k: i + 1 for i, k in enumerate(ORDER)}   # Gameflow: 0 = title

# Full-screen videos (Engine\FMV\<name>.mp4) played when a level starts; missing files are skipped by the engine.
VIDEOS = {"Oliveri": "cdv_intro", "Lungomare": "cdv_02_lungomare", "Marinello": "cdv_03_marinello",
          "Laghetti": "cdv_04_laghetti", "Tindari": "cdv_05_tindari", "Sommersa": "cdv_06_sommersa"}

WADS = ["TombEngine.wad2"] + ["CodaDiVolpe\\%s.wad2" % w for w in (
    "CdV_Oggetti", "TR4_Baddy1", "TR4_Baddy2", "TR2_Doberman", "TR1_Rat", "TR4_Bat",
    "TEN_Wraith", "TR5_Lagoon_Witch", "TR2_Shark", "TR4_Skeleton", "TR4_Doors", "TR5_Floor_Trapdoor",
    "TR4_Lever_Switch", "TR4_Rolling_Ball", "TR1_Teeth_Spikes", "TEN_Fish_Emitter", "TEN_Firefly",
    # v10: TEN Resources (GPL, github.com/TombEngine/Resources)
    "TEN_Pushable_Object_Climbable", "TR4_Raising_Blocks", "TEN_Pole", "TR4_rope", "TEN_Search_Drawers",
    "TEN_Search_Cabinet", "TEN_Wall_Lever_Switch", "TEN_Small_Wall_Switch", "TR3_Fusebox_Switch",
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
    9: ("cdv_manovella", "Manovella"),
}
# Keys (KEY_ITEM n, opened with the native keyholes KEY_HOLE n).
KEYS = {1: ("cdv_chiave_ripostiglio", "Chiave del ripostiglio")}
# Inventory look of the objects of CdV_Oggetti.wad2 (build_objects.py): (y offset, scale, x rotation).
# The models are 0.1-0.4 m (100-200 units) and modelled lying flat, so they are scaled up and the flat ones
# tilted towards the ring camera (as the keys).
INV_LOOK = {1: (0, 1.6, -70), 2: (0, 2.0, -70), 3: (0, 1.6, -70), 4: (0, 2.0, -70), 5: (0, 1.8, -30),
            6: (0, 2.6, -70), 7: (0, 1.8, -70), 8: (0, 1.8, -70), 9: (0, 2.2, -70)}


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


ATLAS_NAMES = ["coda_atlas"] + ["coda_atlas%d" % i for i in range(2, 19)]


def macro_tiles(atlas_list):
    out = {}
    for i, a in enumerate(atlas_list):
        for name, (x0, y0, size) in a.get("macro", {}).items():
            out[name] = (i, x0, y0, size)
    return out


def extra_columns(atlas_list):
    out = {}
    for i, a in enumerate(atlas_list):
        if i == 0:
            continue
        for name, (x0, y0, x1, y1) in a.get("columns", {}).items():
            if name.startswith(("roccia_faccia", "rupe_faccia", "fac_", "t_", "g_", "c_")):
                out[name] = (i, x0, x1)
    return out


def load_atlases():
    out = []
    for name in ATLAS_NAMES:
        out.append(json.load(open(os.path.join(ROOT, "build", "textures", name + ".json"))))
    return out


def setup_textures(level, atlas_list):
    for i, a in enumerate(atlas_list):
        # One shared copy for every level (Levels\CdV_Textures): the atlases are 17 MB in all.
        level.textures.append({"path": "$(LevelDirectory)\\..\\CdV_Textures\\coda_atlas%s.png" % ("" if i == 0 else str(i + 1)),
                               "footsteps": a["footsteps_64px"]})


def build_terrain_level(key, content):
    t0 = time.time()
    if "frame" in LEVELS[key]:
        world = W.World(frame=LEVELS[key]["frame"])
    else:
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
                               [b["base_m"] for b in world.buildings], macro=macro_tiles(atlas_list), columns=extra_columns(atlas_list))

    texer.facade_cols = getattr(world, "facade_cols", {})
    texer.rock_prefix = getattr(world, "rock_prefix", "roccia_faccia")
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
    for f in [n + ".png" for n in ATLAS_NAMES]:
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
Flow.SetTotalSecretCount(10)
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
    # Night in town: no sunset horizon mesh, a dark blue sky layer with stars, and fog of the very same colour
    # that reaches full strength before the draw distance, so the ring of buildings and the street ends melt
    # into the night sky and the edge of the map is never seen.
    "Oliveri": {"track": "108", "fog": (16, 20, 36, 16, 36), "far": 40, "sky": (16, 20, 36), "stars": 2500},
    "Lungomare": {"track": "108", "fog": None, "far": 128},
    # Dawn mist over the sandbar: fog of the colour of the sky layer, full before the draw distance, so the sea and
    # the top of the cliff melt into it and the map has no visible end.
    "Marinello": {"track": "108", "fog": (196, 180, 170, 12, 30), "far": 34, "sky": (196, 180, 170), "stars": 0, "horizon": True},
    "Laghetti": {"track": "108", "fog": None, "far": 128},
    "Tindari": {"track": "108", "fog": (214, 170, 132, 18, 44), "far": 48, "sky": (214, 170, 132), "stars": 0, "horizon": True},
    "Sommersa": {"track": "108", "fog": (8, 30, 38, 8, 30), "far": 40, "sky": (8, 30, 38), "stars": 0},
    "Collaudo": {"track": "108", "fog": None, "far": 40},
    "MarinelloB": {"track": "108", "fog": (196, 180, 170, 12, 30), "far": 34, "sky": (196, 180, 170), "stars": 0, "horizon": True},
}


def write_gameflow(only=None):
    strings = ["    %s = { %s }," % (k, luagen.lua_str(name)) for k, name in list(ITEMS.values()) + list(KEYS.values())]
    strings += ["    cdv_level_%s = { %s }," % (k.lower(), luagen.lua_str(LEVELS[k]["title"])) for k in ORDER]
    objs = ["        TEN.Flow.InventoryItem(%s, ID.PUZZLE_ITEM%d, %d, %.2f, Rot(%d, 0, 0), Axis.Y, -1, Act.USE)," % (
        (luagen.lua_str(k), i) + INV_LOOK[i]) for i, (k, _) in ITEMS.items()]
    objs += ["        TEN.Flow.InventoryItem(%s, ID.KEY_ITEM%d, 0, 1.5, Rot(-70, 0, 0), Axis.Y, -1, Act.USE)," % (
        luagen.lua_str(k), i) for i, (k, _) in KEYS.items()]
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
        if lf.get("sky"):
            r, g, b = lf["sky"]
            if not lf.get("horizon"):
                block += "{k}.horizon1.enabled = false\n".format(k=k)
            block += "{k}.layer1 = TEN.Flow.SkyLayer(TEN.Color({r}, {g}, {b}), 2)\n".format(k=k, r=r, g=g, b=b)
            block += "{k}.starfield = TEN.Flow.Starfield({n})\n".format(k=k, n=lf.get("stars", 0))
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
        if key == "Oliveri":      # the trailer shots of the v6 levels point at the old map coordinates
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
