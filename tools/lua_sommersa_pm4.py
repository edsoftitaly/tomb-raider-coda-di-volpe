#!/usr/bin/env python3
"""Sommersa.lua, 16 Nov 17:10.
1) Turi's death scene: Moveable:AttachObjCamera moves the camera only in the frame it is called (camera.cpp, ObjCamera ->
   MoveObjCamera; with ItemCameraOn the normal camera just returns) and its target only half the way: called once it left
   the view where it was. Now it is called every frame of the scene.
2) A dead shark stayed in mid-air when the cella was drained: it now drops to the floor (or out of sight if no floor)."""
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60])
    s = s.replace(a, b)

rep('''        stand:AttachObjCamera(0, m, 0)
        back = function()''', '''        stand:AttachObjCamera(0, m, 0)
        hold = function() pcall(function() stand:AttachObjCamera(0, m, 0) end) end   -- every frame: one call moves it once
        back = function()''')
rep('''    local back = nil
    pcall(function()
        local stand = CDV.M("squalo2")''', '''    local back, hold = nil, nil
    pcall(function()
        local stand = CDV.M("squalo2")''')
rep('''    CDV.After(180, function() if back then back() end end)
    pcall(function() TEN.Sound.PlaySound(479''', '''    pcall(function() TEN.Sound.PlaySound(479''')
rep('''        n = n + 1
        pcall(TEN.Input.ClearAllKeys)
        if n % 3 == 0 and m ~= nil and m:GetValid() then''', '''        n = n + 1
        pcall(TEN.Input.ClearAllKeys)
        if n < 180 then
            if hold then hold() end
        elseif n == 180 then
            if back then back() end
            CDV.Log("TURI scene: camera back to Lara")
        end
        if n % 3 == 0 and m ~= nil and m:GetValid() then''')
rep('''    else
        CDV.Disable("squalo")
        if CDV.Flag("leva_valve")''', '''    else
        for _, nm in ipairs({ "squalo", "squalo2", "squalo3" }) do
            local q = CDV.M(nm)
            if q ~= nil and q:GetValid() and q:GetHP() <= 0 then
                -- a dead one: with the water gone it lies on the floor, not in mid-air
                local ok, how = pcall(function()
                    local qp = q:GetPosition()
                    local fl = TEN.Collision.Probe(qp, q:GetRoomNumber()):GetFloorHeight()
                    if fl ~= nil and fl > qp.y then
                        q:SetPosition(TEN.Vec3(qp.x, fl - 100, qp.z), false)
                        return "on the floor, y " .. fl
                    end
                    q:SetPosition(TEN.Vec3(qp.x, qp.y + 30000, qp.z), false)
                    return "out of sight"
                end)
                CDV.Log("SHARK " .. nm .. " dead, water gone: " .. tostring(how))
            elseif nm == "squalo" then
                CDV.Disable("squalo")
            end
        end
        if CDV.Flag("leva_valve")''')
if crlf: s = s.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(s)
