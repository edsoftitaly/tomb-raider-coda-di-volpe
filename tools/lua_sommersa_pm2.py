"""The lost half, Ed's corrections of 16:46.

  - the death of Turi: the fixed flyby of the cella did not show him (Lara is at the altar, he may be anywhere).
    The camera is now put a sector and a half from him, wherever he is, on a side with a clear line, looking at
    him (Moveable:AttachObjCamera on a shark that is not in the water yet, used as a camera stand); the flyby stays
    as the fallback
  - Turi's fire: the roar of the flame when it leaves (SFX 563) and a shout of his (737, 477, 496 in turn), a
    burst (368) where it lands
  - Turi climbs after her: while she is in the cella or on its stairs her steps are remembered, and when he has
    not come closer for three seconds he is put on them, behind her and out of sight (the engine alone cannot take
    him up steps of four clicks)
  - taking the Star of Castor back from the altar is a pickup (Lara's animation 425, from a low pedestal), not the
    insert animation

  lua_sommersa_pm2.py <in.lua> <out.lua>"""
import sys

OLD_SCENE = '''    CDV.Flyby(2)
    pcall(function() TEN.Effects.MakeEarthquake(24) end)
'''
NEW_SCENE = '''    -- the camera: a sector and a half from him, on a side with a clear line, a little above, looking at him.
    -- Its stand is a shark that is not in the water yet (nothing else in a script can hold a camera).
    local back = nil
    pcall(function()
        local stand = CDV.M("squalo2")
        if m == nil or not m:GetValid() or stand == nil or not stand:GetValid() or stand:GetActive() then return end
        local p = m:GetPosition()
        local home, homeRoom = stand:GetPosition(), stand:GetRoomNumber()
        local spot = nil
        for k = 0, 7 do
            local a = k * math.pi / 4
            local c = TEN.Vec3(math.floor(p.x + math.sin(a) * 1500), p.y - 1000, math.floor(p.z + math.cos(a) * 1500))
            local ok, los = pcall(function() return TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(p.x, p.y - 600, p.z), c) end)
            if ok and los == true then spot = c; break end
        end
        if spot == nil then return end
        stand:SetPosition(spot, false)
        stand:SetRoomNumber(m:GetRoomNumber())
        stand:AttachObjCamera(0, m, 0)
        back = function()
            pcall(TEN.View.ResetObjCamera)
            pcall(function() stand:SetPosition(home, false); stand:SetRoomNumber(homeRoom) end)
        end
        CDV.Log("TURI scene: camera at " .. spot.x .. " " .. spot.y .. " " .. spot.z)
    end)
    if back == nil then CDV.Flyby(2) end
    CDV.After(180, function() if back then back() end end)
    pcall(function() TEN.Sound.PlaySound(479, m:GetPosition()) end)
    pcall(function() TEN.Effects.MakeEarthquake(24) end)
'''
OLD_LAUNCH = '''            balls[#balls + 1] = { x0 = tp.x, y0 = tp.y - 700, z0 = tp.z, x1 = lp.x, y1 = lp.y - 400, z1 = lp.z, t = 0, n = math.max(14, math.floor(d / 120)) }
'''
NEW_LAUNCH = OLD_LAUNCH + '''            flameN = flameN + 1
            pcall(function() TEN.Sound.PlaySound(563, tp) end)                                   -- the roar of the flame
            pcall(function() TEN.Sound.PlaySound(({ 737, 477, 496 })[flameN % 3 + 1], tp) end)   -- and his shout
'''
OLD_BURST = '''            local lp = Lara:GetPosition()
            if (lp.x - x) ^ 2 + (lp.z - z) ^ 2 < 480 ^ 2'''
NEW_BURST = '''            pcall(function() TEN.Sound.PlaySound(368, TEN.Vec3(math.floor(x), math.floor(y), math.floor(z))) end)
            local lp = Lara:GetPosition()
            if (lp.x - x) ^ 2 + (lp.z - z) ^ 2 < 480 ^ 2'''
CLIMB = '''-- Turi climbs after her. While she is in the cella or on its stairs her steps are remembered; when he has not come
-- closer for three seconds he is put on them, behind her and out of sight. (The engine alone cannot take a man
-- of his kind up steps of four clicks.)
local turiTrail, turiStuck, turiLast, turiFrame = {}, 0, nil, 0
CDV.Loop(function()
    turiFrame = turiFrame + 1
    if turiFrame % 30 ~= 0 then return end
    if not CDV.Flag("turi_sveglio") or CDV.Flag("turi_morto") or CDV.Flag("acqua") or Lara:GetHP() <= 0 then return end
    local m = CDV.M("turi")
    if m == nil or not m:GetValid() or not m:GetActive() or m:GetHP() <= 0 then return end
    local lp, tp = Lara:GetPosition(), m:GetPosition()
    local st = Lara:GetState()
    local ok, room = pcall(function() return Lara:GetRoom():GetName() end)
    if ok and type(room) == "string" and room:sub(1, 7) == "H_CELLA" and (st == 0 or st == 1 or st == 2) then
        turiTrail[#turiTrail + 1] = { x = lp.x, y = lp.y, z = lp.z, room = Lara:GetRoomNumber() }
        if #turiTrail > 30 then table.remove(turiTrail, 1) end
    end
    local d = Dist(tp, lp)
    if d > 3 * 1024 and d > (turiLast or d) - 256 then turiStuck = turiStuck + 1 else turiStuck = 0 end
    turiLast = d
    if turiStuck < 3 or PointOnScreen(tp) then return end
    for i = #turiTrail - 2, 1, -1 do
        local c = turiTrail[i]
        local cd = Dist(c, lp)
        if cd >= 2 * 1024 and cd < d - 512 and not PointOnScreen(c) then
            local moved = pcall(function()
                m:SetPosition(TEN.Vec3(c.x, c.y, c.z), false)
                m:SetRoomNumber(c.room)
                m:SetRotation(TEN.Rotation(0, math.deg(math.atan(lp.x - c.x, lp.z - c.z)), 0))
            end)
            CDV.Log("TURI " .. (moved and "climbs after her, " or "could not be moved, ") .. math.floor(cd / 1024) .. " sectors behind")
            turiStuck, turiLast = 0, cd
            return
        end
    end
end)

'''
PICK = '''-- A thing taken from a low pedestal: Lara's own pickup (LA_PICKUP_PEDESTAL_LOW, 425, state 39). mid() when her hand
-- closes on it (frame 29, where the animation has its pickup command), fn() at the end.
function CDV.PickItem(fn, mid)
    Lara:SetAnim(425)
    Lara:SetState(39)
    local n = 0
    local function wait()
        n = n + 1
        if mid and (n >= 36 or (Lara:GetAnim() == 425 and Lara:GetFrame() >= 29)) then
            mid()
            mid = nil
        end
        if n < 240 and (n < 20 or Lara:GetAnim() == 425) then CDV.After(1, wait); return end
        if mid then mid() end
        if fn then fn() end
    end
    CDV.After(1, wait)
end
'''
OLD_ALTAR = '''    CDV.Log("ALTAR Castor " .. (on and "set" or "taken back"))
    CDV.InsertItem(function()
'''
NEW_ALTAR = '''    CDV.Log("ALTAR Castor " .. (on and "set" or "taken back"))
    ;(on and CDV.InsertItem or CDV.PickItem)(function()              -- set: the insert; taken back: a pickup
'''


def sub1(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:70])
    return t.replace(old, new)


def main():
    src, dst = sys.argv[1:3]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    assert "function CDV.PickItem" not in t
    t = sub1(t, OLD_SCENE, NEW_SCENE)
    t = sub1(t, OLD_LAUNCH, NEW_LAUNCH)
    t = sub1(t, OLD_BURST, NEW_BURST)
    t = sub1(t, "local balls, flameT = {}, 0\n", "local balls, flameT, flameN = {}, 0, 0\n")
    t = sub1(t, OLD_ALTAR, NEW_ALTAR)
    t = sub1(t, "function CDV.Flyby(seq)\n", PICK + "function CDV.Flyby(seq)\n")
    t = sub1(t, "local HUNTERS = {", CLIMB + "local HUNTERS = {")
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("Sommersa.lua ok")


if __name__ == "__main__":
    main()
