"""Oliveri: the gate of the courtyard opens with a code instead of the crank (Ed, 14/11/2026).

usage: oliveri_codice.py <Oliveri.prj2> <Oliveri.lua> <out.prj2> <out.lua>

- out: the crank pickup (PUZZLE_ITEM9) in the lab, the crank on the winch (manovella_posta) and the winch (static 245)
- in: five small wall switches int_1..int_5 (SWITCH_TYPE2, OCB 1) on the wall right of the gate, 1 nearest the gate,
  with the number plates (static 456); the computer in the lab (455; 457, screen off, in the dark twin)
- Lua: the gate opens when 2, 3 and 5 are on and 1 and 4 off. The screen reads 33 2D 32 2D 35."""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

SW_X = [12192.0, 11472.0, 10752.0, 10032.0, 9312.0]          # int_1 .. int_5, room units of T_01_00
SW_Z, WALL_Z = 17920.0, 17408.0


def mov(uid, typ, pos, rot, ocb, name):
    n = name.encode()
    return (b"TeMovTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<3f", rot, 0, 0) + b"\x7f" + struct.pack("<Ih", typ, ocb)
            + b"\0\0\0" + struct.pack("<3f", 1, 1, 1) + struct.pack("<i", len(n)) + n + b"\0\0\0\0")


def sta(uid, typ, pos, rot=0.0):
    return (b"TeStaTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<4f", rot, 0, 0, 1) + b"\x7f" + struct.pack("<I", typ)
            + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, 0) + b"\0\0\0\0")


def patch_prj2(src, dst):
    head, top = P.load(src)
    d = dict(top)
    settings = P.add_wad(d[b"TeSettings"], "CdV_Codice.wad2")
    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = list(range(max(used) + 1, max(used) + 40))
    gone = []

    def drop(room, oc, op):
        if oc == b"TeMovTn3":
            t = P.mov_type(op)[1]
            if (room.startswith("CASA_LAB") and t == 508) or b"manovella_posta" in op:
                gone.append((room, t))
                return None
        if oc == b"TeStaTn3" and room == "T_01_00":
            r = Reader(op)
            r.leb()
            k = r.s.tell()
            if struct.unpack("<I", op[k + 29:k + 33])[0] == 245:
                gone.append((room, 245))
                return None
        return op
    rooms = P.map_objects(d[b"TeRooms"], drop)
    print("removed:", gone)
    assert sorted(t for _, t in gone) == [245, 508, 703], gone
    objs = [mov(ids.pop(0), 801, (x, 0.0, SW_Z), 180.0, 1, "int_%d" % (i + 1)) for i, x in enumerate(SW_X)]
    objs.append(sta(ids.pop(0), 456, (SW_X[2], 0.0, WALL_Z)))
    rooms = P.add_objects(rooms, "T_01_00", objs)
    rooms = P.add_objects(rooms, "CASA_LAB", [sta(ids.pop(0), 455, (1190.0, 0.0, 2150.0))])
    rooms = P.add_objects(rooms, "CASA_LAB_BUIO", [sta(ids.pop(0), 457, (1190.0, 0.0, 2150.0))])
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])


OLD_START = 'CDV.Use({ id = "argano", item = ID.PUZZLE_ITEM9'
OLD_END = 'CDV.Zone({ id = "cortile",'
NEW = '''-- The gate of the courtyard: five small switches on the wall, numbered 1 to 5. The computer in the workshop shows
-- 33 2D 32 2D 35 (ASCII in hexadecimal): the gate opens with 2, 3 and 5 on and 1 and 4 off.
local GATE_CODE = { false, true, true, false, true }
local function GateOpen()
    CDV.Flag("cancello_aperto", true)
    CDV.Cue("use_argano")
    CDV.Swing("cancello_cortile", "y", 90, 50)
    CDV.After(32, function()          -- the passage is free when the gate is three quarters open
        CDV.Enable("blocco_cancello")
        local m = CDV.M("blocco_cancello")
        if m ~= nil and m:GetValid() then pcall(function() m:SetCollidable(false) end) end
        CDV.Log("GATE free")
    end)
end
CDV.Loop(function()
    if CDV.Flag("cancello_aperto") then return end
    for i = 1, 5 do
        if CDV.Used("int_" .. i) then
            CDV.Flag("int_on_" .. i, not CDV.Flag("int_on_" .. i))
            CDV.Flag("int_t", 50)          -- judge when Lara has finished with the switch
            CDV.Log("SWITCH " .. i .. " " .. tostring(CDV.Flag("int_on_" .. i)))
        end
    end
    local t = CDV.Flag("int_t") or 0
    if t > 0 then
        t = t - 1
        CDV.Flag("int_t", t)
        if t == 0 then
            local ok = true
            for i = 1, 5 do
                if (CDV.Flag("int_on_" .. i) == true) ~= GATE_CODE[i] then ok = false end
            end
            if ok then GateOpen() end
        end
    end
end)

CDV.StartList = CDV.StartList or {}
CDV.Start = function() for _, f in ipairs(CDV.StartList) do f() end end

CDV.Zone({ id = "cancello_chiuso", x = 44544, y = -1280, z = 17920, r = 1300, dy = 900, once = false, text = "Il cancello del cortile è chiuso. Lo comandano i cinque interruttori numerati sul muro, lì a destra.", secs = 6, need = function() return not CDV.Flag("cancello_aperto") end })

CDV.Zone({ id = "computer_lab", x = 32160, y = -1280, z = 26726, r = 700, dy = 500, once = false, text = "Sullo schermo: 33 2D 32 2D 35", secs = 6, need = function() return not CDV.Flag("cancello_aperto") end })

'''


def patch_lua(src, dst):
    s = open(src, encoding="utf-8", newline="").read()
    a, b = s.index(OLD_START), s.index(OLD_END)
    old = s[a:b]
    assert old.count("manovella") >= 3 and "CDV.StartList" in old, old[:200]
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s[:a] + NEW.replace("\n", nl) + s[b:]
    assert "PUZZLE_ITEM9" not in s and 'Done("use_argano")' not in s
    open(dst, "w", encoding="utf-8", newline="").write(s)


patch_prj2(sys.argv[1], sys.argv[3])
patch_lua(sys.argv[2], sys.argv[4])
