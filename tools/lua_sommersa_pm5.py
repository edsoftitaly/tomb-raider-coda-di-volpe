#!/usr/bin/env python3
"""Sommersa.lua, 16 Nov 17:30.
1) Turi's death: the object camera cannot work here (MoveObjCamera keeps the room of the camera it had, so the view was
   drawn from the altar's room: the void in Ed's screenshot). Now a fixed camera of the level, "cam_turi"
   (tools/sommersa_cam.py), is moved near him with its room set, and played on him every frame (Camera:Play).
   His death cry is played at Lara (at his place it is too far to be heard).
2) Credits: they began 7.7 s after the black screen (Ed quit after 6). Now the first card comes 2 s after the fade."""
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60])
    s = s.replace(a, b)

a = s.index("    -- the camera: a sector and a half from him, on a side with a clear line")
b = s.index("    pcall(function() TEN.Sound.PlaySound(479, m:GetPosition()) end)")
s = s[:a] + '''    -- the camera: the level's fixed camera "cam_turi", put a sector and a half from him on a side with a clear line,
    -- a little above, in his room, and played on him every frame of the scene.
    local back, hold = nil, nil
    local okc, why = pcall(function()
        if m == nil or not m:GetValid() then return "no Turi" end
        local cam = TEN.Objects.GetCameraByName("cam_turi")
        if cam == nil then return "no camera cam_turi in this build of the level" end
        local p = m:GetPosition()
        local spot = nil
        for k = 0, 7 do
            local a = k * math.pi / 4
            local c = TEN.Vec3(math.floor(p.x + math.sin(a) * 1500), p.y - 1000, math.floor(p.z + math.cos(a) * 1500))
            local ok, los = pcall(function() return TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(p.x, p.y - 600, p.z), c) end)
            if ok and los == true then spot = c; break end
        end
        if spot == nil then spot = TEN.Vec3(p.x + 300, p.y - 1400, p.z + 300) end
        cam:SetPosition(spot)
        cam:SetRoomNumber(m:GetRoomNumber())
        hold = function() pcall(function() cam:Play(m) end) end
        hold()
        return "camera at " .. spot.x .. " " .. spot.y .. " " .. spot.z .. " room " .. m:GetRoomNumber()
    end)
    CDV.Log("TURI scene: " .. tostring(why))
''' + s[b:]
rep("    pcall(function() TEN.Sound.PlaySound(479, m:GetPosition()) end)\n",
    "    CDV.Sfx(479)                                             -- his death cry, at Lara: at his place it is too far to hear\n"
    "    CDV.After(8, function() CDV.Sfx(482) end)\n")
rep('''            if back then back() end
            CDV.Log("TURI scene: camera back to Lara")''', '''            CDV.Log("TURI scene: camera back to Lara")''')

rep('''        pcall(function() TEN.View.FadeOut(0.4) end)
        CDV.After(210, function()''', '''        pcall(function() TEN.View.FadeOut(1.5) end)
        CDV.After(28, function()''')
rep("            CDV.After(20, function() CDV.Credits(1) end)", "            CDV.After(30, function() CDV.Credits(1) end)")
rep('''        blackSprite:Draw(1, TEN.View.AlignMode.CENTER, TEN.View.ScaleMode.STRETCH, TEN.Effects.BlendID.OPAQUE)
    end)''', '''        blackSprite:Draw(1, TEN.View.AlignMode.CENTER, TEN.View.ScaleMode.STRETCH, TEN.Effects.BlendID.OPAQUE)
    end)
    if not CDV.CreditsSaid then CDV.CreditsSaid = true; CDV.Log("CREDITS black screen on, sprite " .. tostring(blackSprite ~= nil)) end''')
rep('''            CDV.Log("TURI scene: camera back to Lara")''', '''            CDV.SceneOn = false
            CDV.Log("TURI scene: camera back to Lara")''')
rep('''    CDV.Log("TURI scene: " .. tostring(why))''', '''    CDV.Log("TURI scene: " .. tostring(why))
    CDV.SceneOn = true''')
rep('''need = function() return CDV.Flag("acqua") == true and CDV.Has(ID.PUZZLE_ITEM8) end })''', '''need = function() return CDV.Flag("acqua") == true and CDV.Has(ID.PUZZLE_ITEM8) and not CDV.SceneOn end })''')
if crlf: s = s.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(s)
