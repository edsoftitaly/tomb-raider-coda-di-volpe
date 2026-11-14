"""Oliveri, the trapdoor again (Ed, 14/11/2026, 11:28):
- the key of the padlock is on a new, tougher man inside the box room: ladro_ripostiglio, MP_WITH_STICK (172), who comes
  alive when the door of the box room opens
- the padlock is a static of its own (459): when Lara turns the key it falls to the floor, then the chain comes down
  and lies in a heap (449)

usage: oliveri_botola2.py <Oliveri.prj2> <Oliveri.lua> <out.prj2> <out.lua>   (the .lua already through lua_armi_incastro.py)"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

CHAIN = (1750.0, 0.0, 3066.0)                       # room units of CASA_RIPOSTIGLIO (27, 4352, 27)
LOCK = (1750.0, 647.0, 3036.0)
HEAP = (1750.0, 0.0, 2990.0)
WX, WZ, FLOOR = 27 * 1024 + 1750, 27 * 1024 + 3066, -4352


def sta(uid, typ, pos, name):
    n = name.encode()
    return (b"TeStaTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<4f", 0, 0, 0, 1) + b"\x7f" + struct.pack("<I", typ)
            + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, len(n)) + n + b"\0\0\0\0")


def mov(uid, typ, pos, rot, ocb, name):
    n = name.encode()
    return (b"TeMovTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<3f", rot, 0, 0) + b"\x7f" + struct.pack("<Ih", typ, ocb)
            + b"\0\0\0" + struct.pack("<3f", 1, 1, 1) + struct.pack("<i", len(n)) + n + b"\0\0\0\0")


def patch_prj2(src, dst):
    head, top = P.load(src)
    d = dict(top)
    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = list(range(max(used) + 1, max(used) + 20))
    names = [op for rn, oc, op in P.raw_objects(src)]
    assert any(b"catena_botola" in p for p in names) and not any(b"ladro_ripostiglio" in p for p in names)
    rooms = d[b"TeRooms"]
    for room, suf in (("CASA_RIPOSTIGLIO", ""), ("CASA_RIPOSTIGLIO_BUIO", "_buio")):
        rooms = P.add_objects(rooms, room, [sta(ids.pop(0), 459, LOCK, "lucchetto_botola" + suf), sta(ids.pop(0), 449, HEAP, "catena_terra" + suf)])
    rooms = P.add_objects(rooms, "CASA_RIPOSTIGLIO", [mov(ids.pop(0), 172, (2300.0, 0.0, 2100.0), 270.0, 0, "ladro_ripostiglio")])
    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])


OLD_START = "-- The padlock of the trapdoor:"
OLD_END = "-- The diary: the lookout carries it"
NEW = '''-- The padlock of the trapdoor: a chain hangs from the trapdoor down the north wall of the box room, to a padlock at
-- hand height. Its key is on the man with the stick who waits inside the box room. Until it is open a hidden bridge
-- plugs the hole in the roof. When the key turns the padlock falls to the floor and the chain comes down in a heap.
CDV.StartList = CDV.StartList or {}
CDV.StartList[#CDV.StartList + 1] = function() CDV.HideModel("tappo_botola") end
CDV.Start = function() for _, f in ipairs(CDV.StartList) do f() end end
CDV.Drop({ id = "chiave_lucchetto", enemy = "ladro_ripostiglio", item = ID.PUZZLE_ITEM14, text = "L'uomo col bastone aveva in tasca una chiavetta da lucchetto." })
local function St2(n)
    local ok, st = pcall(TEN.Objects.GetStaticByName, n)
    if ok and st ~= nil then return st end
    return nil
end
local function Each(base, fn)
    for _, suf in ipairs({ "", "_buio" }) do
        local st = St2(base .. suf)
        if st ~= nil then pcall(fn, st) end
    end
end
local LOCK_FLOOR = %(floor)d - 9
local function PadlockDown()          -- the final state: padlock on the floor, chain in a heap
    Each("lucchetto_botola", function(st)
        local p = st:GetPosition()
        st:SetPosition(TEN.Vec3(p.x, LOCK_FLOOR, %(z)d - 110))
        st:SetRotation(TEN.Rotation(90, 0, 25))
    end)
    Each("catena_botola", function(st) st:Disable() end)
    Each("catena_terra", function(st) st:Enable() end)
end
local function PadlockFall(fn)
    local f, y0 = 0, nil
    local function step()
        f = f + 1
        if f <= 15 then                                   -- the padlock: free fall, turning over
            Each("lucchetto_botola", function(st)
                local p = st:GetPosition()
                y0 = y0 or p.y
                local y = math.min(LOCK_FLOOR, y0 + 3 * f * f)
                st:SetPosition(TEN.Vec3(p.x, y, p.z - 5))
                st:SetRotation(TEN.Rotation(6 * f, 0, 1.7 * f))
            end)
        elseif f == 16 then
            CDV.Sfx(114)
        elseif f <= 36 then                               -- then the chain runs down
            local k = f - 16
            Each("catena_botola", function(st)
                local p = st:GetPosition()
                st:SetPosition(TEN.Vec3(p.x, p.y + 9 * k, p.z))
            end)
        else
            PadlockDown()
            if fn then fn() end
            return
        end
        CDV.After(1, step)
    end
    CDV.After(1, step)
end
CDV.StartList[#CDV.StartList + 1] = function()
    if CDV.Done("use_lucchetto_botola") then PadlockDown() else Each("catena_terra", function(st) st:Disable() end) end
end
CDV.Use({ id = "lucchetto_botola", item = ID.PUZZLE_ITEM14, x = %(x)d, y = %(floor)d, z = %(z)d, r = 1500, dy = 600, consume = true, fn = function()
        local lp = Lara:GetPosition()
        Lara:SetPosition(TEN.Vec3(%(x)d, lp.y, %(z)d - 400), false)          -- in front of the padlock, facing the wall
        Lara:SetRotation(TEN.Rotation(0, 0, 0))
        CDV.InsertItem(nil, function()                    -- a key is turned: animation 131; the padlock goes at frame 40
            PadlockFall(function()
                local m = CDV.M("tappo_botola")
                if m ~= nil and m:GetValid() then pcall(function() m:Destroy() end) end
                CDV.Log("PADLOCK open")
                CDV.Say("Il lucchetto cade e la catena viene giù. La botola è libera.", 5)
            end)
        end, true)
    end })
CDV.Loop(function() CDV.KeyPromptAt(%(x)d, %(floor)d, %(z)d, 1500, ID.PUZZLE_ITEM14, "use_lucchetto_botola") end)
CDV.Zone({ id = "lucchetto_chiuso", x = %(x)d, y = %(floor)d, z = %(z)d, r = 1200, dy = 600, once = false, text = "La botola è chiusa da una catena col lucchetto, lì sul muro.", secs = 5, need = function() return not CDV.Done("use_lucchetto_botola") and not CDV.Has(ID.PUZZLE_ITEM14) and CDV.Dead("ladro_ripostiglio") end })

''' % {"x": WX, "z": WZ, "floor": FLOOR}

DOOR_OLD = '        CDV.InsertKey("serratura_ripostiglio", "porta_ripostiglio")\n'
DOOR_NEW = '''        CDV.InsertKey("serratura_ripostiglio", "porta_ripostiglio")
        CDV.After(55, function()          -- the man inside comes alive as the door opens, not before
            CDV.Enable("ladro_ripostiglio")
            local m = CDV.M("ladro_ripostiglio")
            if m ~= nil and m:GetValid() then pcall(function() m:SetHP(70) end) end
        end)
'''


def patch_lua(src, dst):
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    assert "function CDV.InsertItem(fn, mid, key)" in s, "run lua_armi_incastro.py first"
    a, b = s.index(OLD_START), s.index(OLD_END)
    assert "tappo_botola" in s[a:b] and s[a:b].count("CDV.Use(") == 1
    s = s[:a] + NEW + s[b:]
    assert s.count(DOOR_OLD) == 1
    s = s.replace(DOOR_OLD, DOOR_NEW)
    old = 'La chiave ce l\'ha uno dei ladri.'
    open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))


patch_prj2(sys.argv[1], sys.argv[3])
patch_lua(sys.argv[2], sys.argv[4])
