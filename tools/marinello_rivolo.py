"""Marinello: the trickle in the channel of the big sluice (Ed, 14/11/2026). See build_rivolo.py.

usage: marinello_rivolo.py <Marinello.prj2> <Marinello.lua> <out.prj2> <out.lua>"""
import re
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

X, Y = 12800.0, 168.0                 # room units of T_00_01 (0, 0, 30): the bed of the channel is at 128
Z_MONTE, Z_VASCA, Z_VALLE = 29184.0, 27136.0, 25088.0
ROOM_Z = 30 * 1024


def sta(uid, typ, pos, name):
    n = name.encode()
    return (b"TeStaTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<4f", 0, 0, 0, 1) + b"\x7f" + struct.pack("<I", typ)
            + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, len(n)) + n + b"\0\0\0\0")


def patch_prj2(src, dst):
    head, top = P.load(src)
    d = dict(top)
    settings = P.add_wad(d[b"TeSettings"], "CdV_Rivolo.wad2")
    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = list(range(max(used) + 1, max(used) + 20))
    rooms = d[b"TeRooms"]
    for room, suf in (("T_00_01", ""), ("T_00_01_PIENO", "_pieno")):
        objs = [sta(ids.pop(0), 472, (X, Y, Z_MONTE), "rivolo_monte" + suf), sta(ids.pop(0), 474, (X, Y, Z_VALLE), "rivolo_valle" + suf)]
        if not suf:
            objs.append(sta(ids.pop(0), 473, (X, Y, Z_VASCA), "rivolo_vasca"))
        rooms = P.add_objects(rooms, room, objs)
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])


LOOP_OLD = re.compile(r"local canalRun, canalTick = 0, 0\nCDV\.Loop\(function\(\).*?\nend\)\n", re.S)
LOOP_NEW = '''local canalRun = 0
-- The trickle in the channel (statics of CdV_Rivolo.wad2, in the room and in its flooded twin): upstream of the gate it
-- is always there, downstream once the sluice is open. The sheets slide one tile (512) towards the lake and jump back.
local RIV = { monte = %(zm)d, valle = %(zv)d }
local function Riv(name, fn)
    for _, suf in ipairs({ "", "_pieno" }) do
        local ok, st = pcall(TEN.Objects.GetStaticByName, "rivolo_" .. name .. suf)
        if ok and st ~= nil then pcall(fn, st) end
    end
end
local function RivState()
    local open = CDV.Flag("canale_pieno") == true
    Riv("valle", function(st) if open then st:Enable() else st:Disable() end end)
    Riv("vasca", function(st) if open then st:Disable() else st:Enable() end end)
end
CDV.StartList = CDV.StartList or {}
CDV.StartList[#CDV.StartList + 1] = RivState
CDV.Loop(function()
    canalRun = (canalRun + 14) %% 512
    Riv("monte", function(st) st:SetPosition(TEN.Vec3(%(x)d, %(y)d, RIV.monte - canalRun)) end)
    if CDV.Flag("canale_pieno") or CDV.Flag("canale_apre") then
        Riv("valle", function(st) st:SetPosition(TEN.Vec3(%(x)d, %(y)d, RIV.valle - canalRun)) end)
    end
end)
''' % {"x": int(X), "y": -int(Y), "zm": int(Z_MONTE) + ROOM_Z, "zv": int(Z_VALLE) + ROOM_Z}

WATER_OLD = re.compile(r"        if w0 ~= nil and f >= 120 then\n.*?\n        end\n", re.S)
WATER_NEW = '''        if f == 150 then                -- the gate is a third of the way up: the water runs under it, down to the lake
            CDV.Flag("canale_apre", true)
            Riv("valle", function(st) st:Enable() end)
            Riv("vasca", function(st) st:Disable() end)
        end
'''
FLAG_OLD = re.compile(r"            if w0 ~= nil then +-- from now on the water stays: see the loop below\n.*?\n            end\n", re.S)
FLAG_NEW = '''            CDV.Flag("canale_pieno", true)          -- from now on the water runs downstream too
            RivState()
'''
GHOST_OLD = 'CDV.StartList[#CDV.StartList + 1] = function() if not CDV.Flag("canale_pieno") then CDV.Ghost("acqua_canale") end end'
GHOST_NEW = 'CDV.StartList[#CDV.StartList + 1] = function() CDV.Ghost("acqua_canale") end          -- the old sheet: never shown again'


def patch_lua(src, dst):
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    for rx, new in ((LOOP_OLD, LOOP_NEW), (WATER_OLD, WATER_NEW), (FLAG_OLD, FLAG_NEW)):
        assert len(rx.findall(s)) == 1, rx.pattern[:40]
        s = rx.sub(lambda m: new, s)
    assert s.count(GHOST_OLD) == 1
    s = s.replace(GHOST_OLD, GHOST_NEW)
    open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))


patch_prj2(sys.argv[1], sys.argv[3])
patch_lua(sys.argv[2], sys.argv[4])
