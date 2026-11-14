"""Oliveri.lua, 14/11/2026 13:46 (Ed): the gate code is judged on where the five levers really are (CDV.Pulled:
the state of the switch item against the one it had at the start), not on a count of the pulls, so a wrong lever
put back up no longer spoils the code. usage: lua_oliveri_interruttori2.py <Oliveri.lua> <out>"""
import sys

s = open(sys.argv[1], encoding="utf-8").read()
a = s.index('    if CDV.Flag("cancello_aperto") then return end\n    for i = 1, 5 do\n        if CDV.Used("int_" .. i) then')
b = s.index("CDV.StartList = CDV.StartList or {}")
new = '''    if CDV.Flag("cancello_aperto") then return end
    local busy = SWITCH_STATES[Lara:GetState()] or SWITCH_ANIMS[Lara:GetAnim()]
    local ok = true
    for i = 1, 5 do
        if CDV.Used("int_" .. i) then CDV.Flag("int_t", 50) end          -- judge when Lara has finished with the switch
        if CDV.Pulled("int_" .. i) ~= GATE_CODE[i] then ok = false end   -- where the lever really is
    end
    local t = CDV.Flag("int_t") or 0
    if t > 0 then
        t = t - 1
        CDV.Flag("int_t", t)
    end
    if t > 0 or busy then return end
    -- a switch that has been used is set free again, so that a second Action pulls it back
    for i = 1, 5 do
        local m = CDV.M("int_" .. i)
        if m ~= nil and m:GetValid() then
            pcall(function()
                local free = TEN.Objects.MoveableStatus.INACTIVE
                if m:GetStatus() ~= free then
                    m:SetStatus(free)
                    CDV.Log("SWITCH " .. i .. " free, pulled " .. tostring(CDV.Pulled("int_" .. i)))
                end
            end)
        end
    end
    if ok then GateOpen() end
end)

'''
s = s[:a] + new + s[b:]
open(sys.argv[2], "w", encoding="utf-8", newline="").write(s)
