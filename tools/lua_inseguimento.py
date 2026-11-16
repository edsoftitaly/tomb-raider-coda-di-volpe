"""Enemies that walk follow Lara wherever she goes, engine path or not.

The engine only lets a creature walk where its own pathfinding reaches (one click up and two down for a goon or a
dog, four for the man with the stick), and Ed sees enemies that stay put when she leaves their room. So the script
keeps Lara's trail (where she stood on solid ground, once a second) and an enemy that is awake, alive and has not
come any closer for four seconds is put on that trail behind her - only on a point of the trail that is not on
screen, and only while the enemy itself is not on screen. A gunman who has her in his sights (clear line, within
eight sectors) is left where he is: he is shooting. Every move goes to the log.

Marinello: ten seconds between the two levers of the lake bed instead of twenty.

  lua_inseguimento.py <level> <in.lua> <out.lua>"""
import sys

BLOCK = '''-- The hunt goes on wherever she goes. Lara's trail: where she stood on solid ground, once a second. A walker that is
-- awake and has not come closer for four seconds is put on the trail behind her, out of sight (tools/lua_inseguimento.py).
local MELEE = { %(melee)s }
local trail, trailFrame, stuck = {}, 0, {}
local function PointOnScreen(p)
    local ok, seen = pcall(function()
        local cp, ct = TEN.View.GetCameraPosition(), TEN.View.GetCameraTarget()
        local fx, fz, dx, dz = ct.x - cp.x, ct.z - cp.z, p.x - cp.x, p.z - cp.z
        local d, fl = math.sqrt(dx * dx + dz * dz), math.sqrt(fx * fx + fz * fz)
        if d > SIGHT then return false end
        if d > 1 and fl > 1 and (fx * dx + fz * dz) / (fl * d) < 0.42 then return false end
        local ok2, los = pcall(function()
            return TEN.Util.HasLineOfSight(TEN.View.GetCameraRoom():GetRoomNumber(), cp, TEN.Vec3(p.x, p.y - 700, p.z))
        end)
        if ok2 and los == false then return false end
        return true
    end)
    return ok and seen
end
CDV.Loop(function()
    trailFrame = trailFrame + 1
    if trailFrame %% 30 ~= 0 or Lara:GetHP() <= 0 then return end
    local lp = Lara:GetPosition()
    local st = Lara:GetState()
    if st == 0 or st == 1 or st == 2 then
        trail[#trail + 1] = { x = lp.x, y = lp.y, z = lp.z, room = Lara:GetRoomNumber() }
        if #trail > 40 then table.remove(trail, 1) end
    end
    for name, _ in pairs(WALKERS) do
        local m = CDV.M(name)
        if m ~= nil and m:GetValid() and m:GetActive() and m:GetHP() > 0 then
            local p = m:GetPosition()
            local d = math.sqrt((p.x - lp.x) ^ 2 + (p.z - lp.z) ^ 2) + math.abs(p.y - lp.y)
            local s = stuck[name] or { d = d, n = 0 }
            stuck[name] = s
            if d > 5 * 1024 and d > s.d - 256 then s.n = s.n + 1 else s.n = 0 end
            s.d = d
            if s.n >= 4 and not PointOnScreen(p) then
                local aiming = false
                if not MELEE[name] and d < 8 * 1024 then
                    pcall(function()
                        aiming = TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(p.x, p.y - 700, p.z), TEN.Vec3(lp.x, lp.y - 700, lp.z)) == true
                    end)
                end
                if not aiming then
                    for i = #trail - 3, 1, -1 do                       -- the newest point at least three seconds old
                        local c = trail[i]
                        local cd = math.sqrt((c.x - lp.x) ^ 2 + (c.z - lp.z) ^ 2) + math.abs(c.y - lp.y)
                        if cd >= 3 * 1024 and cd < d - 1024 and not PointOnScreen(c) then
                            local ok = pcall(function()
                                m:SetPosition(TEN.Vec3(c.x, c.y, c.z), false)
                                m:SetRoomNumber(c.room)
                                m:SetRotation(TEN.Rotation(0, math.deg(math.atan(lp.x - c.x, lp.z - c.z)), 0))
                            end)
                            CDV.Log("HUNT " .. name .. (ok and " put on her trail, " or " could not be moved, ") .. math.floor(cd / 1024) .. " sectors behind")
                            s.n, s.d = 0, cd
                            break
                        end
                    end
                end
            end
        else
            stuck[name] = nil
        end
    end
end)

'''
MELEE = {"Oliveri": ["cane1", "cane2", "ladro_ripostiglio"], "Marinello": ["c1", "c2"], "Tindari": ["c1", "c2", "c3"], "Sommersa": []}


def main():
    level, src, dst = sys.argv[1:4]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    assert t.count("local HUNTERS = {") == 1 and "local WALKERS = {" in t and "local trail, trailFrame" not in t
    t = t.replace("local HUNTERS = {", BLOCK % {"melee": ", ".join('["%s"] = true' % n for n in MELEE[level])} + "local HUNTERS = {")
    if level == "Marinello":
        for old, new in (('CDV.TwinLevers("fondo", "leva_fondo_0", "leva_fondo_1", 600,', 'CDV.TwinLevers("fondo", "leva_fondo_0", "leva_fondo_1", 300,'),
                         ("Twenty seconds to pull the other.", "Ten seconds to pull the other."),
                         ("Twenty seconds, again, to reach the second lever.", "Ten seconds, again, to reach the second lever.")):
            assert t.count(old) == 1, old
            t = t.replace(old, new)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print(level, "ok")


if __name__ == "__main__":
    main()
