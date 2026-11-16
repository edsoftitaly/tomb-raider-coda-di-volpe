"""Enemies and the camera, third version (16 Nov, after Ed's run of 15:00: the log showed walkers switched on
"after 8 s on screen", i.e. popping up late and in full view, and the man behind the kicked gate missing).

  - an enemy woken by a door (kicked or unlocked) is switched on at once, as before: it is behind the door
  - any other walker: if the place where it stands is not on screen, switched on there. If it is on screen it is
    put on Lara's trail, behind her and out of sight, and switched on there; with no such place for two seconds
    (start of a level) it is switched on where it stands
  - the hunt: a walker that has not come closer for four seconds is put on her trail - gunmen too (the two on the
    rim of the drained Mergolo stood there with a clear line and never came down)

Marinello: the roof of the way out gives way as soon as she is through the gate; the three boulders come abreast
(no stepping between them), roll to the gate, break up when at rest; two new niches near the gate (prj2 side:
marinello_nicchie.py). The two levers of the lake bed: when the ten seconds are over the lever springs back.

  lua_nemici3.py <level> <in.lua> <out.lua>"""
import re
import sys

BLOCK = '''-- Enemies and the camera (tools/lua_nemici3.py). Lara's trail: where she stood on solid ground, once a second.
-- A walker woken by a door is switched on at once. Any other is switched on where it stands when that place is not
-- on screen, otherwise on her trail, behind her. One that is awake and has not come closer for four seconds is put
-- on her trail too. Those waiting are in LevelVars, so a saved game does not lose them.
local WALKERS = { %(walkers)s }
local BY_DOOR = { %(doors)s }
local SIGHT = %(sight)d * 1024
local EnableNow = CDV.Enable
local trail, trailFrame, stuck = {}, 0, {}
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
local function PutOnTrail(m, c, lp)
    return pcall(function()
        m:SetPosition(TEN.Vec3(c.x, c.y, c.z), false)
        m:SetRoomNumber(c.room)
        m:SetRotation(TEN.Rotation(0, math.deg(math.atan(lp.x - c.x, lp.z - c.z)), 0))
    end)
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
            elseif not PointOnScreen(m:GetPosition()) then
                w[name] = nil
                EnableNow(name)
                CDV.Log("ENEMY " .. name .. " in, out of sight")
            else
                local c, cd = TrailPoint(lp, 1e9)
                if c ~= nil then
                    w[name] = nil
                    PutOnTrail(m, c, lp)
                    EnableNow(name)
                    CDV.Log("ENEMY " .. name .. " in behind her, " .. math.floor(cd / 1024) .. " sectors back on her trail")
                elseif t >= 60 then
                    w[name] = nil
                    EnableNow(name)
                    CDV.Log("ENEMY " .. name .. " in where it stands, in sight (no place behind her)")
                else
                    w[name] = t + 1
                end
            end
        end
    end
    if trailFrame %% 30 ~= 0 or Lara:GetHP() <= 0 then return end
    local st = Lara:GetState()
    if st == 0 or st == 1 or st == 2 then
        trail[#trail + 1] = { x = lp.x, y = lp.y, z = lp.z, room = Lara:GetRoomNumber() }
        if #trail > 40 then table.remove(trail, 1) end
    end
    for name, _ in pairs(WALKERS) do
        local m = CDV.M(name)
        if m ~= nil and m:GetValid() and m:GetActive() and m:GetHP() > 0 then
            local p = m:GetPosition()
            local d = Dist(p, lp)
            local s = stuck[name] or { d = d, n = 0 }
            stuck[name] = s
            if d > 5 * 1024 and d > s.d - 256 then s.n = s.n + 1 else s.n = 0 end
            s.d = d
            if s.n >= 4 and not PointOnScreen(p) then
                local c, cd = TrailPoint(lp, d - 1024)
                if c ~= nil then
                    local ok = PutOnTrail(m, c, lp)
                    CDV.Log("HUNT " .. name .. (ok and " put on her trail, " or " could not be moved, ") .. math.floor(cd / 1024) .. " sectors behind")
                    s.n, s.d = 0, cd
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

OLD_LEVERS_START = "function CDV.TwinLevers(id, a, b, frames, msgFirst, msgLate, fn)\n"
NEW_LEVERS = '''function CDV.TwinLevers(id, a, b, frames, msgFirst, msgLate, fn)
    local rest = {}
    CDV.Loop(function()
        if CDV.Flag(id .. "_ok") then return end
        local now = (CDV.Flag(id .. "_t") or 0) + 1
        CDV.Flag(id .. "_t", now)
        for _, n in ipairs({a, b}) do
            local m = CDV.M(n)
            if m ~= nil and m:GetValid() then
                local t0 = CDV.Flag(id .. "_e_" .. n)
                local used = CDV.Used(n)
                if not t0 and rest[n] == nil and not used then
                    rest[n] = { anim = m:GetAnim(), state = m:GetState() }          -- the lever as it stands unpulled
                end
                if t0 and now - t0 > frames then                                    -- time is up: it springs back
                    CDV.Flag(id .. "_e_" .. n, false)
                    if rest[n] ~= nil then
                        pcall(function() m:SetAnim(rest[n].anim); m:SetState(rest[n].state) end)
                    end
                    pcall(function() m:SetStatus(TEN.Objects.MoveableStatus.INACTIVE) end)
                    CDV.Log("LEVER " .. n .. " back, time up")
                    CDV.Say(msgLate, 5)
                elseif used then
                    CDV.Rearm(n)
                    local other = (n == a) and b or a
                    local to = CDV.Flag(id .. "_e_" .. other)
                    if to and now - to <= frames then
                        CDV.Flag(id .. "_ok", true)
                        fn()
                        return
                    end
                    CDV.Flag(id .. "_e_" .. n, now)
                    CDV.Say(msgFirst, 4)
                end
            end
        end
    end)
end
'''


def sub1(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:80])
    return t.replace(old, new)


def main():
    level, src, dst = sys.argv[1:4]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    sight, walkers, doors = DATA[level]
    a = t.index("-- Enemies come from behind.")
    b = t.index("local HUNTERS = {")
    block = BLOCK % {"walkers": ", ".join('["%s"] = true' % n for n in walkers), "doors": ", ".join('["%s"] = true' % n for n in doors), "sight": sight}
    t = t[:a] + block + t[b:]
    if level == "Marinello":
        a = t.index(OLD_LEVERS_START)
        b = t.index("\nend\n", t.index("    end)\n", a)) + len("\nend\n")
        t = t[:a] + NEW_LEVERS + t[b:]
        t = sub1(t, "Too late: the chain has stopped. Ten seconds, again, to reach the second lever.", "Too late: the chain stops and the lever springs back.")
        t = sub1(t, 'CDV.Zone({ id = "masso_g", x = 19968, y = 1024, z = 41472, r = 700,', 'CDV.Zone({ id = "masso_g", x = 19968, y = 1024, z = 32768, r = 500,')
        t = sub1(t, '''        for i, name in ipairs({ "masso_g", "masso_g2", "masso_g3" }) do
            CDV.ShowModel(name, true)
''', '''        for i, name in ipairs({ "masso_g", "masso_g2", "masso_g3" }) do
            local b0 = CDV.M(name)                 -- the three abreast, at the far end: no stepping between them
            if b0 ~= nil and b0:GetValid() then
                pcall(function() local q0 = b0:GetPosition(); b0:SetPosition(TEN.Vec3(q0.x, -476, 45568), false) end)
            end
            CDV.ShowModel(name, true)
''')
        t = sub1(t, "if n > 400 or q.z < 30720 + 2300 then", "if n > 400 or q.z < 30720 + 1300 then")
        t = sub1(t, 'if stopped == 3 then CDV.Log("BOULDERS at rest"); CDV.After(30, function() CDV.Cue("dopo_massi") end) end',
                 '''if stopped == 3 then
                        CDV.Log("BOULDERS at rest")
                        CDV.After(30, function() CDV.Cue("dopo_massi") end)
                        CDV.After(45, function()           -- they break up against the gate: the way back stays open
                            for _, bn in ipairs({ "masso_g", "masso_g2", "masso_g3" }) do
                                local bb = CDV.M(bn)
                                if bb ~= nil and bb:GetValid() then
                                    pcall(function() bb:ShatterMesh(0) end)
                                    pcall(function() bb:Destroy() end)
                                end
                            end
                            CDV.Sfx(67)
                        end)
                    end''')
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print(level, "ok")


if __name__ == "__main__":
    main()
