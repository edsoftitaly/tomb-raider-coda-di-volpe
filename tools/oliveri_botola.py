"""Oliveri: the padlock of the trapdoor made visible and its key made sure (Ed, 14/11/2026: «la botola non si riesce
ad aprire»).

usage: oliveri_botola.py <Oliveri.prj2> <Oliveri.lua> <out.prj2> <out.lua>

- the chain with the padlock (static 458, CdV_Codice.wad2) hangs on the north wall of the box room, in the room and in
  its dark twin (catena_botola, catena_botola_buio); it goes when the padlock is open
- the key no longer depends on the engine dropping a carried pickup: the pickup chiave_lucchetto is out, and the key
  comes to Lara when ladro_primo dies (CDV.Drop, as for the key of the box room, which is known to work)
- Lara is put in front of the padlock before she uses the key"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

CHAIN = (1750.0, 0.0, 3066.0)                       # room units of CASA_RIPOSTIGLIO (27, 4352, 27)
WX, WZ = 27 * 1024 + 1750, 27 * 1024 + 3066


def sta(uid, typ, pos, name):
    n = name.encode()
    return (b"TeStaTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<4f", 0, 0, 0, 1) + b"\x7f" + struct.pack("<I", typ)
            + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, len(n)) + n + b"\0\0\0\0")


def patch_prj2(src, dst):
    head, top = P.load(src)
    d = dict(top)
    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = list(range(max(used) + 1, max(used) + 10))
    gone = []

    def drop(room, oc, op):
        if oc == b"TeMovTn3" and b"chiave_lucchetto" in op:
            gone.append(room)
            return None
        return op
    rooms = P.map_objects(d[b"TeRooms"], drop)
    assert gone == ["CASA_SOGGIORNO"], gone
    rooms = P.add_objects(rooms, "CASA_RIPOSTIGLIO", [sta(ids.pop(0), 458, CHAIN, "catena_botola")])
    rooms = P.add_objects(rooms, "CASA_RIPOSTIGLIO_BUIO", [sta(ids.pop(0), 458, CHAIN, "catena_botola_buio")])
    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])


OLD_START = "-- The padlock of the trapdoor:"
OLD_END = "-- The diary: the lookout carries it"
NEW = '''-- The padlock of the trapdoor: a chain hangs from the trapdoor down the north wall of the box room, to a padlock at
-- hand height. Its key is on the thief of the living room. Until it is open a hidden bridge plugs the hole in the roof.
CDV.StartList = CDV.StartList or {}
CDV.StartList[#CDV.StartList + 1] = function() CDV.HideModel("tappo_botola") end
CDV.Start = function() for _, f in ipairs(CDV.StartList) do f() end end
CDV.Drop({ id = "chiave_lucchetto", enemy = "ladro_primo", item = ID.PUZZLE_ITEM14, text = "Il ladro aveva in tasca una chiavetta da lucchetto." })
local function ChainOff()
    for _, n in ipairs({ "catena_botola", "catena_botola_buio" }) do
        local ok, st = pcall(TEN.Objects.GetStaticByName, n)
        if ok and st ~= nil then
            if not pcall(function() st:Disable() end) then pcall(function() st:SetScale(0.001) end) end
        end
    end
end
CDV.StartList[#CDV.StartList + 1] = function() if CDV.Done("use_lucchetto_botola") then ChainOff() end end
CDV.Use({ id = "lucchetto_botola", item = ID.PUZZLE_ITEM14, x = %(x)d, y = -4352, z = %(z)d, r = 1500, dy = 600, consume = true, fn = function()
        local lp = Lara:GetPosition()
        Lara:SetPosition(TEN.Vec3(%(x)d, lp.y, %(z)d - 400), false)          -- in front of the padlock, facing the wall
        Lara:SetRotation(TEN.Rotation(0, 0, 0))
        CDV.InsertItem(function()
            ChainOff()
            local m = CDV.M("tappo_botola")
            if m ~= nil and m:GetValid() then pcall(function() m:Destroy() end) end
            CDV.Log("PADLOCK open")
            CDV.Say("Il lucchetto cede e la catena viene giù. La botola è libera.", 5)
        end)
    end })
CDV.Loop(function() CDV.KeyPromptAt(%(x)d, -4352, %(z)d, 1500, ID.PUZZLE_ITEM14, "use_lucchetto_botola") end)
CDV.Zone({ id = "lucchetto_chiuso", x = %(x)d, y = -4352, z = %(z)d, r = 1200, dy = 600, once = false, text = "La botola è chiusa da una catena col lucchetto, lì sul muro. La chiave ce l'avrà uno di loro.", secs = 5, need = function() return not CDV.Done("use_lucchetto_botola") and not CDV.Has(ID.PUZZLE_ITEM14) end })
CDV.Zone({ id = "lucchetto_chiave", x = %(x)d, y = -4352, z = %(z)d, r = 1200, dy = 600, once = true, text = "Il lucchetto della botola è lì sul muro, in fondo alla catena. (Azione per usare la chiave.)", secs = 5, need = function() return not CDV.Done("use_lucchetto_botola") and CDV.Has(ID.PUZZLE_ITEM14) end })

''' % {"x": WX, "z": WZ}


def patch_lua(src, dst):
    s = open(src, encoding="utf-8", newline="").read()
    a, b = s.index(OLD_START), s.index(OLD_END)
    assert "tappo_botola" in s[a:b] and s[a:b].count("CDV.Use(") == 1
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s[:a] + NEW.replace("\n", nl) + s[b:]
    open(dst, "w", encoding="utf-8", newline="").write(s)


patch_prj2(sys.argv[1], sys.argv[3])
patch_lua(sys.argv[2], sys.argv[4])
