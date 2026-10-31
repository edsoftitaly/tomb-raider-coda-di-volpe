"""Run a generated level script against a mock TombEngine API (lupa) and play scripted scenarios.

The mock records what the script does (Enable/Disable, messages, items, secrets, EndLevel) so the
puzzle logic can be tested without the engine. Moveable names must exist (from the .names.json the
builder writes next to the script), otherwise the test fails: this catches typos in Lua names.
"""
import json
import sys

import lupa

MOCK = r'''
local names, log = ...
TEN = { Objects = {}, Inventory = {}, Strings = {}, Util = {}, View = {}, Flow = {}, Sound = {}, Logic = {} }
local ids = {}
local n = 1
for _, k in ipairs({"PUZZLE_ITEM1","PUZZLE_ITEM2","PUZZLE_ITEM3","PUZZLE_ITEM4","PUZZLE_ITEM5","PUZZLE_ITEM6",
                    "PUZZLE_ITEM7","PUZZLE_ITEM8","SMALLMEDI_ITEM","BIGMEDI_ITEM","SHOTGUN_AMMO1_ITEM","UZI_AMMO_ITEM",
                    "FLARE_INV_ITEM","PISTOLS_AMMO_ITEM","REVOLVER_AMMO_ITEM"}) do ids[k] = n; n = n + 1 end
TEN.Objects.ObjID = ids
TEN.Vec2 = function(x, y) return { x = x, y = y } end
TEN.Vec3 = function(x, y, z) return { x = x, y = y, z = z } end
TEN.Color = function(r, g, b) return { r = r, g = g, b = b } end
TEN.Rotation = function(x, y, z) return { x = x, y = y, z = z } end
TEN.Strings.DisplayStringOption = { CENTER = 1, SHADOW = 2 }
TEN.Strings.DisplayString = function(text) return { text = text } end
TEN.Strings.ShowString = function(s) log("say", s.text) end
TEN.Strings.HideString = function() end
TEN.Util.PercentToScreen = function() return 0, 0 end
TEN.View.FadeOut = function() end
TEN.View.FadeIn = function() end
TEN.View.CameraType = { NORMAL = 0, FLYBY = 4 }
TEN.View.GetCameraType = function() return 0 end
TEN.View.PlayFlyby = function(n) CDV_LOG_FLYBY = n end
TEN.View.PlayVideo = function(name) CDV_LOG_VIDEO = name end
TEN.Flow.EndLevel = function(i, p) log("end", tostring(i) .. ":" .. tostring(p)) end
TEN.Flow.AddSecret = function(i) log("secret", tostring(i)) end
TEN.Sound.PlaySound = function() end
local objs = {}
local function newMov(name)
    local m = { name = name, active = false, valid = true, hp = 10, state = 1 }
    function m:GetState() return self.state end
    function m:Enable() self.active = true; log("enable", self.name) end
    function m:SetStatus(st) self.status = st; log("status", self.name .. "=" .. tostring(st)) end
    function m:Disable() self.active = false; log("disable", self.name) end
    function m:GetActive() return self.active end
    function m:GetValid() return self.valid end
    function m:GetHP() return self.hp end
    function m:SetPosition(p) log("teleport", self.name) end
    function m:SetRoomNumber() end
    function m:SetRotation() end
    function m:SetAir(v) log("air", tostring(v)) end
    return m
end
for name, _ in pairs(names) do objs[name] = newMov(name) end
TEN.Objects.MoveableStatus = { INACTIVE = "INACTIVE", ACTIVE = "ACTIVE", DEACTIVATED = "DEACTIVATED", INVISIBLE = "INVISIBLE" }
TEN.Objects.GetMoveableByName = function(name)
    if objs[name] == nil then error("unknown moveable name " .. tostring(name)) end
    return objs[name]
end
TEN.Objects.GetRoomByName = function(name)
    return { GetRoomNumber = function() return 1 end }
end
local inv, used = {}, nil
TEN.Inventory.GetItemCount = function(i) return inv[i] or 0 end
TEN.Inventory.GiveItem = function(i, c) inv[i] = (inv[i] or 0) + (c or 1); log("give", tostring(i)) end
TEN.Inventory.TakeItem = function(i, c) inv[i] = (inv[i] or 0) - (c or 1); log("take", tostring(i)) end
TEN.Inventory.GetUsedItem = function() return used end
TEN.Inventory.ClearUsedItem = function() used = nil; log("cleared", "") end
LevelVars = {}
LevelFuncs = {}
local pos = { x = 0, y = 0, z = 0 }
Lara = newMov("Lara")
function Lara:GetPosition() return { x = pos.x, y = pos.y, z = pos.z } end
local H = {}
function H.move(x, y, z) pos.x, pos.y, pos.z = x, y, z end
function H.use(i) used = i; LevelFuncs.OnUseItem(); used = nil end
function H.tick(k) for _ = 1, (k or 1) do LevelFuncs.OnLoop() end end
function H.kill(name) objs[name].hp = 0; objs[name].valid = false end
function H.setActive(name, v) objs[name].active = v end
function H.active(name) return objs[name].active end
function H.pull(name) objs[name].state = 1 - objs[name].state end
function H.count(i) return inv[i] or 0 end
function H.give(i) inv[i] = (inv[i] or 0) + 1 end
return H
'''


class Harness:
    def __init__(self, script_path, names, preload=None):
        self.lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        for mod, code in (preload or {}).items():
            self.lua.execute("package.preload[%r] = function() %s end" % (mod, code))
        self.events = []
        tbl = self.lua.table_from({n: True for n in names})
        self.H = self.lua.execute(MOCK, tbl, lambda kind, val: self.events.append((kind, val)))
        src = open(script_path, encoding="utf-8").read()
        self.captured = {}

        def hook(cdv, zones, uses):
            self.captured["cdv"], self.captured["zones"], self.captured["uses"] = cdv, zones, uses
        self.lua.globals().CDV_TEST = hook
        self.lua.execute(src)
        self.lua.globals().LevelFuncs.OnStart()
        self.ids = self.lua.globals().TEN.Objects.ObjID

    def item(self, name):
        return self.ids[name]

    def at(self, p, frames=2):
        self.H.move(p[0], p[1], p[2])
        self.H.tick(frames)

    def use(self, item_name):
        self.H.use(self.item(item_name))

    def last(self, kind):
        return [v for k, v in self.events if k == kind]


def smoke(level_dir, key):
    """Visit every zone and try every item use; report Lua errors and what happened."""
    names = load_names(level_dir, key)
    t = Harness("%s/%s.lua" % (level_dir, key), names)
    zones = t.captured["zones"]
    uses = t.captured["uses"]
    for i in range(1, len(zones) + 1):
        z = zones[i]
        t.at((z.x, z.y, z.z), 2)
    for i in range(1, len(uses) + 1):
        u = uses[i]
        for j in range(1, 9):
            t.H.give(t.item("PUZZLE_ITEM%d" % j))
        t.at((u.x, u.y, u.z), 1)
        t.H.use(u.item)
    for n in names:
        t.H.kill(n) if n.startswith(("ladro", "guard", "turi", "donna", "capo")) else None
    t.H.tick(800)
    return t


def load_names(level_dir, key):
    return json.load(open("%s/%s.names.json" % (level_dir, key)))


if __name__ == "__main__" and sys.argv[1] == "smoke":
    for key in sys.argv[2:]:
        t = smoke("../build/levels/" + key, key)
        kinds = {}
        for k, v in t.events:
            kinds.setdefault(k, []).append(v)
        print("%-10s zones %d uses %d | enable %d say %d give %d secret %s end %s" % (
            key, len(t.captured["zones"]), len(t.captured["uses"]), len(kinds.get("enable", [])),
            len(kinds.get("say", [])), len(kinds.get("give", [])), sorted(set(kinds.get("secret", []))), kinds.get("end")))
    sys.exit(0)

if __name__ == "__main__":
    lvl = sys.argv[1]
    import importlib
    mod = importlib.import_module("scenario_" + lvl.lower())
    ok = mod.run()
    sys.exit(0 if ok else 1)
