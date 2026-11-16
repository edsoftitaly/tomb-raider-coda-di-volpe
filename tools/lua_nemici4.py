"""Enemies and the camera, fourth version (16 Nov, 16:16). Ed: enemies of far-away areas came for Lara too soon.

A walker now hunts only once it has seen her: Lara within SEE sectors with a clear line (or it has been hurt). Until
then the engine's own mood rules it (no forced attack, no moving along her trail). Once it has seen her it keeps
after her - forced attack, and put on her trail behind her when it stops getting closer - as long as she is within
LEASH sectors; beyond that it gives up until it sees her again. Nobody is moved when it is switched on any more:
out of the picture at once, in the picture after two seconds at most, always where it stands.

  lua_nemici4.py <level> <in.lua> <out.lua>"""
import sys

BLOCK = '''-- Enemies and the camera (tools/lua_nemici4.py).
-- Switching on: a walker woken by a door comes in at once; any other at once when the place where it stands is not
-- on screen, otherwise as soon as the camera looks away, two seconds at most. Always where it stands.
-- The hunt: a walker hunts once it has seen her (within SEE sectors with a clear line, or hurt). From then on it
-- is kept in attack mood and, when it stops getting closer, put on her trail behind her and out of sight - as
-- long as she is within LEASH sectors. Beyond that it gives up until it sees her again.
local WALKERS = { %(walkers)s }
local BY_DOOR = { %(doors)s }
local SIGHT = %(sight)d * 1024
local SEE, LEASH = %(see)d * 1024, %(leash)d * 1024
local EnableNow = CDV.Enable
local trail, trailFrame, stuck, lastHP = {}, 0, {}, {}
CDV.Aware = {}
local function PointOnScreen(p)
    local ok, seen = pcall(function()
        local cp, ct = TEN.View.GetCameraPosition(), TEN.View.GetCameraTarget()
        local fx, fz, dx, dz = ct.x - cp.x, ct.z - cp.z, p.x - cp.x, p.z - cp.z
        local d, fl = math.sqrt(dx * dx + dz * dz), math.sqrt(fx * fx + fz * fz)
        if d > SIGHT then return false end
        if d > 1 and fl > 1 and (fx * dx + fz * dz) / (fl * d) < 0.42 then return false end      -- more than 65 degrees off
        local ok2, los = pcall(function()
            return TEN.Util.HasLineOfSight(TEN.View.GetCameraRoom():GetRoomNumber(), cp, TEN.Vec3(p.x, p.y - 700, p.z))
        end)
        if ok2 and los == false then return false end
        return true
    end)
    return ok and seen
end
local function Dist(a, b) return math.sqrt((a.x - b.x) ^ 2 + (a.z - b.z) ^ 2) + math.abs(a.y - b.y) end
-- the newest point of the trail at least three seconds old, three sectors or more from her, nearer than `within`
local function TrailPoint(lp, within)
    for i = #trail - 3, 1, -1 do
        local c = trail[i]
        local cd = Dist(c, lp)
        if cd >= 3 * 1024 and cd < within and not PointOnScreen(c) then return c, cd end
    end
    return nil
end
function CDV.Enable(name)
    local m = CDV.M(name)
    if not WALKERS[name] or BY_DOOR[name] or m == nil or not m:GetValid() or m:GetActive() then return EnableNow(name) end
    if not PointOnScreen(m:GetPosition()) then
        CDV.Log("ENEMY " .. name .. " in, out of sight")
        return EnableNow(name)
    end
    if LevelVars.CDV_wait == nil then LevelVars.CDV_wait = {} end
    if LevelVars.CDV_wait[name] == nil then LevelVars.CDV_wait[name] = 0 end
end
CDV.Loop(function()
    trailFrame = trailFrame + 1
    local lp = Lara:GetPosition()
    local w = LevelVars.CDV_wait
    if w ~= nil then
        for name, t in pairs(w) do
            local m = CDV.M(name)
            if m == nil or not m:GetValid() then
                w[name] = nil
            elseif t >= 60 or not PointOnScreen(m:GetPosition()) then
                w[name] = nil
                EnableNow(name)
                CDV.Log("ENEMY " .. name .. (t >= 60 and " in after 2 s, in sight" or " in, out of sight"))
            else
                w[name] = t + 1
            end
        end
    end
    if trailFrame %% 30 ~= 0 or Lara:GetHP() <= 0 then return end
    local st = Lara:GetState()
    if st == 0 or st == 1 or st == 2 then
        trail[#trail + 1] = { x = lp.x, y = lp.y, z = lp.z, room = Lara:GetRoomNumber() }
        if #trail > 40 then table.remove(trail, 1) end
    end
    if LevelVars.CDV_aware == nil then LevelVars.CDV_aware = {} end
    CDV.Aware = LevelVars.CDV_aware
    for name, _ in pairs(WALKERS) do
        local m = CDV.M(name)
        if m ~= nil and m:GetValid() and m:GetActive() and m:GetHP() > 0 then
            local p = m:GetPosition()
            local flat = math.sqrt((p.x - lp.x) ^ 2 + (p.z - lp.z) ^ 2)
            local d = flat + math.abs(p.y - lp.y)
            local hp = m:GetHP()
            if not CDV.Aware[name] then
                local sees = false
                if lastHP[name] ~= nil and hp < lastHP[name] then
                    sees = true
                elseif flat < SEE and math.abs(p.y - lp.y) < 4 * 1024 then
                    pcall(function()
                        sees = TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(p.x, p.y - 700, p.z), TEN.Vec3(lp.x, lp.y - 700, lp.z)) == true
                    end)
                end
                if sees then
                    CDV.Aware[name] = true
                    CDV.Log("HUNT " .. name .. " has seen her, " .. math.floor(d / 1024) .. " sectors away")
                end
            elseif d > LEASH then
                CDV.Aware[name] = false
                stuck[name] = nil
                CDV.Log("HUNT " .. name .. " gives up, " .. math.floor(d / 1024) .. " sectors away")
            end
            lastHP[name] = hp
            if CDV.Aware[name] then
                local s = stuck[name] or { d = d, n = 0 }
                stuck[name] = s
                if d > 5 * 1024 and d > s.d - 256 then s.n = s.n + 1 else s.n = 0 end
                s.d = d
                if s.n >= 4 and not PointOnScreen(p) then
                    local c, cd = TrailPoint(lp, d - 1024)
                    if c ~= nil then
                        local ok = pcall(function()
                            m:SetPosition(TEN.Vec3(c.x, c.y, c.z), false)
                            m:SetRoomNumber(c.room)
                            m:SetRotation(TEN.Rotation(0, math.deg(math.atan(lp.x - c.x, lp.z - c.z)), 0))
                        end)
                        CDV.Log("HUNT " .. name .. (ok and " put on her trail, " or " could not be moved, ") .. math.floor(cd / 1024) .. " sectors behind")
                        s.n, s.d = 0, cd
                    end
                end
            end
        else
            stuck[name] = nil
        end
    end
end)

'''
DATA = {
    "Oliveri": (36, ["cane1", "cane2", "ladro_chiave", "ladro_primo", "ladro_ripostiglio", "ladro_terra", "palo"], ["ladro_terra", "ladro_primo", "ladro_ripostiglio"]),
    "Marinello": (30, ["c1", "c2", "t1", "t2", "t3", "t4", "t5", "t6", "t_chiave"], ["t_chiave"]),
    "Tindari": (60, ["b1", "b2", "b3", "c1", "c2", "c3", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"], ["t6"]),
    "Sommersa": (30, ["c1", "g0", "g1", "g2", "h1", "h2"], []),
}
SEE, LEASH = 10, 20
OLD_MOOD = "                c:SetMood(TEN.Objects.MoodType.ATTACK)\n"
NEW_MOOD = '''                if WALKERS[name] and not CDV.Aware[name] then
                    -- it has not seen her: the engine's own mood (never forced). One that gave up is let go.
                    if CDV.Aware[name] == false then c:SetMood(TEN.Objects.MoodType.AUTO or TEN.Objects.MoodType.BORED) end
                else
                    c:SetMood(TEN.Objects.MoodType.ATTACK)
                end
'''


def main():
    level, src, dst = sys.argv[1:4]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    sight, walkers, doors = DATA[level]
    a = t.index("-- Enemies and the camera (tools/lua_nemici")
    b = t.index("local HUNTERS = {")
    t = t[:a] + BLOCK % {"walkers": ", ".join('["%s"] = true' % n for n in walkers), "doors": ", ".join('["%s"] = true' % n for n in doors),
                         "sight": sight, "see": SEE, "leash": LEASH} + t[b:]
    if NEW_MOOD not in t:
        assert t.count(OLD_MOOD) == 1
        t = t.replace(OLD_MOOD, NEW_MOOD)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print(level, "ok")


if __name__ == "__main__":
    main()
