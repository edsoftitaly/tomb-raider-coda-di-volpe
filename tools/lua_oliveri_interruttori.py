"""Oliveri.lua, 14/11/2026 13:42 (Ed):
- the five gate switches can be pulled down and back up: a native switch stays ITEM_ACTIVE after its first use
  when no trigger resets it (generic_switch.cpp: SwitchCollision wants ITEM_NOT_ACTIVE), so the script frees it
  once Lara has finished;
- the lookout and his music only once the gate is open;
- no music sting for the two dogs.
usage: lua_oliveri_interruttori.py <Oliveri.lua> <out>"""
import sys

s = open(sys.argv[1], encoding="utf-8").read()
old = """    local t = CDV.Flag("int_t") or 0
    if t > 0 then"""
new = """    local t = CDV.Flag("int_t") or 0
    -- a switch that has been used is set free again, so that a second Action pulls it back
    if t == 0 and not (SWITCH_STATES[Lara:GetState()] or SWITCH_ANIMS[Lara:GetAnim()]) then
        for i = 1, 5 do
            local m = CDV.M("int_" .. i)
            if m ~= nil and m:GetValid() then
                pcall(function()
                    local free = TEN.Objects.MoveableStatus.INACTIVE
                    if m:GetStatus() ~= free then m:SetStatus(free); CDV.Log("SWITCH " .. i .. " free") end
                end)
            end
        end
    end
    if t > 0 then"""
assert s.count(old) == 1
s = s.replace(old, new)
old = 'CDV.Zone({ id = "cortile", x = 44544, y = -1280, z = 11776, r = 8000, dy = 3000, once = true, text = "There he is, their lookout, with the diary under his arm.", secs = 6, fn = function()'
assert s.count(old) == 1
s = s.replace(old, old.replace("secs = 6, fn", 'secs = 6, need = function() return CDV.Flag("cancello_aperto") == true end, fn'))
old = '    via = "cdv_agguato",                    -- i cani\n'
assert s.count(old) == 1
s = s.replace(old, '    -- via (i cani): nessuna musica, per scelta di Ed (14/11)\n')
open(sys.argv[2], "w", encoding="utf-8", newline="").write(s)
