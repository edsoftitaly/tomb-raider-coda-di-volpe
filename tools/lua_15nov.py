"""15 Nov: captions shown once in the whole game; Oliveri without the block duplicated by lua_oliveri_interruttori2
and with a log of the rooms Lara walks through; Marinello without the opening flyby.

  lua_15nov.py <dir with Oliveri_j.lua, Marinello_g.lua, Tindari_g.lua, Sommersa_g.lua> -> *_k.lua / *_h.lua"""
import os
import sys

ONCE_OLD = '''    if text == nil or text == "" then return end
    if msg ~= nil then'''
ONCE_NEW = '''    if text == nil or text == "" then return end
    -- A caption is shown once in the whole game: once on screen it counts as read and never comes back.
    -- Remembered in GameVars (kept through levels and saved games) under a short key made from the text.
    local h = 5381
    for i = 1, #text do h = (h * 33 + text:byte(i)) % 2147483647 end
    local key = "c" .. h
    if GameVars.CDV_read == nil then GameVars.CDV_read = {} end
    if GameVars.CDV_read[key] then return end
    GameVars.CDV_read[key] = true
    if msg ~= nil then'''

ROOMLOG = '''
-- Diagnostics: every room Lara enters goes to the log with her position (to find where walls let her through).
local lastRoom = nil
CDV.Loop(function()
    local ok, name = pcall(function() return Lara:GetRoom():GetName() end)
    if ok and name ~= lastRoom then
        lastRoom = name
        local p = Lara:GetPosition()
        CDV.Log("ROOM " .. tostring(name) .. " at " .. p.x .. " " .. p.y .. " " .. p.z)
    end
end)
'''


def once(t):
    nl = "\r\n" if "\r\n" in t else "\n"
    old, new = ONCE_OLD.replace("\n", nl), ONCE_NEW.replace("\n", nl)
    assert t.count(old) == 1
    return t.replace(old, new)


def main():
    d = sys.argv[1]
    rd = lambda n: open(os.path.join(d, n), encoding="utf-8", newline="").read()
    wr = lambda n, t: open(os.path.join(d, n), "w", encoding="utf-8", newline="").write(t)

    t = rd("Oliveri_j.lua")
    nl = "\r\n" if "\r\n" in t else "\n"
    L = t.split(nl)
    head = "CDV.StartList = CDV.StartList or {}"
    idx = [i for i, l in enumerate(L) if l == head]
    intro = [i for i, l in enumerate(L) if "Oliveri, the dead of night" in l]
    assert len(intro) == 2 and len(idx) >= 3, (intro, idx)
    a = max(i for i in idx if i < intro[1])            # start of the second copy
    b = min(i for i in idx if i > intro[1])            # first line after it
    assert L[a:a + 60] == L[max(i for i in idx if i < intro[0]):][:60]
    print("Oliveri: dropping lines %d-%d" % (a + 1, b))
    L = L[:a] + L[b:]
    t = nl.join(L)
    assert t.count("Oliveri, the dead of night") == 1 and t.count("function CDV.PlugOff") == 1
    t = once(t).rstrip() + nl + ROOMLOG.replace("\n", nl)
    wr("Oliveri_k.lua", t)

    t = rd("Marinello_g.lua")
    line = "CDV.StartList[#CDV.StartList + 1] = function() CDV.Flyby(1) end"
    assert t.count(line) == 1
    t = t.replace(line, "-- (the opening flyby was removed on 15 Nov: the level starts with Lara in hand)")
    wr("Marinello_h.lua", once(t))
    for n in ("Tindari", "Sommersa"):
        wr(n + "_h.lua", once(rd(n + "_g.lua")))


if __name__ == "__main__":
    main()
