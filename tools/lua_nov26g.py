"""26 Nov, after Ed's test. All four levels: an enemy walked to Lara by the script (CDV.Carry) stays on the floor (it was
lifted along her trail when she climbed: the man of the box room died between the box room and the roof); an enemy put
on her trail lands on the floor too. Oliveri: the duplicated blocks of the morning are removed (the sector mask never
worked: the old rectangle overwrote it), the closed area follows the three barriers Ed asked for, and the man with
the stick appears behind Lara when the box room key goes in.   usage: lua_nov26g.py <Level> <in.lua> <out.lua>"""
import sys

name, src, dst = sys.argv[1:4]
s = open(src, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")


def once(old, new, count=1):
    global s
    assert s.count(old) == count, (name, s.count(old), old[:60])
    s = s.replace(old, new)


if name == "Oliveri":
    a = s.index("-- 26 Nov: the town is closed outside the sectors marked")
    b = s.index("-- 26 Nov: the town is closed outside this rectangle")
    cut = s[a:b]
    assert cut.count("CDV.Carry = {}") == 1 and cut.count("CDV.TOUGH = ") == 1 and cut.count("CDV.AREA = {") == 1
    s = s[:a] + s[b:]
    once("""-- 26 Nov: the town is closed outside this rectangle (sectors x0, z0, x1, z1): the barriers of the Carabinieri stand on
-- its edge in the streets (nov26_extra.py); past them she is put back where she was.
CDV.AREA = { { 12, 3, 52, 33 } }""", """-- 26 Nov: the town is closed outside these rectangles (sectors x0, z0, x1, z1): the main street from the cross street
-- of the town hall to the line of the Carabinieri, and the blocks east of the cross street (house, roofs, lane,
-- courtyard). Barriers stand before the police cars and across the cross street, north and south of the main street
-- (nov26_oliveri3.py); past them she is put back where she was.
CDV.AREA = { { 13, 16, 20, 25 }, { 13, 17, 51, 24 }, { 21, 3, 51, 33 } }""")
    once("""        CDV.After(55, function()          -- the man inside comes alive as the door opens, not before
            CDV.Enable("ladro_ripostiglio")
            local m = CDV.M("ladro_ripostiglio")
            if m ~= nil and m:GetValid() then pcall(function() m:SetHP(70) end) end
        end)""", """        -- the man with the stick comes up behind her as the key goes in (Ed, 26 Nov)
        local m = CDV.M("ladro_ripostiglio")
        if m ~= nil and m:GetValid() then
            pcall(function() CDV.Behind(m) end)
            CDV.Enable("ladro_ripostiglio")
            pcall(function() m:SetHP(70) end)
        end""")
    once("local HUNTERS = {", """-- A moveable is put on the floor behind Lara: the newest point of her own trail on her level, one and a half to four
-- sectors away; failing that, a point straight behind her back. False when no floor is found: it stays where it is.
function CDV.Behind(m)
    local lp = Lara:GetPosition()
    local function try(x, y, z, room)
        local f = CDV.FloorAt(x, y, z, room)
        if f == nil or math.abs(f - lp.y) > 300 then return false end
        m:SetPosition(TEN.Vec3(math.floor(x), f, math.floor(z)), false)
        m:SetRoomNumber(room)
        m:SetRotation(TEN.Rotation(0, math.deg(math.atan(lp.x - x, lp.z - z)), 0))
        return true
    end
    for i = #trail, 1, -1 do
        local c = trail[i]
        local d = math.sqrt((c.x - lp.x) ^ 2 + (c.z - lp.z) ^ 2)
        if d >= 1536 and d <= 4096 and math.abs(c.y - lp.y) < 200 and try(c.x, c.y, c.z, c.room) then return true end
    end
    local yaw = math.rad(Lara:GetRotation().y)
    for _, d in ipairs({ 2048, 1536, 1024 }) do
        if try(lp.x - math.sin(yaw) * d, lp.y, lp.z - math.cos(yaw) * d, Lara:GetRoomNumber()) then return true end
    end
    return false
end

local HUNTERS = {""")

# every level: the floor under a point, nil when there is none (or the engine has no probe)
once("\nCDV.Carry = {}\n", """
function CDV.FloorAt(x, y, z, room)
    local f = nil
    pcall(function()
        local pr = TEN.Collision.Probe(TEN.Vec3(math.floor(x), math.floor(y) - 256, math.floor(z)), room)
        if pr:IsWall() ~= true then f = pr:GetFloorHeight() end
    end)
    return f
end
CDV.Carry = {}
""")
once("""                    local step = math.min(30, dist)
                    local ny = p.y + math.max(-40, math.min(40, ty - p.y))
                    pcall(function()
                        m:SetPosition(TEN.Vec3(math.floor(p.x + dx / dist * step), math.floor(ny), math.floor(p.z + dz / dist * step)))
                        m:SetRotation(TEN.Rotation(0, math.deg(math.atan(dx, dz)), 0))
                    end)""", """                    local step = math.min(30, dist)
                    local nx, nz = p.x + dx / dist * step, p.z + dz / dist * step
                    -- always on the floor: a step higher or lower than a click (she climbed, jumped, dropped) ends it
                    local f = CDV.FloorAt(nx, p.y, nz, m:GetRoomNumber())
                    if f == nil or math.abs(f - p.y) > 300 then
                        CDV.Carry[name], carryAt[name] = nil, nil
                    else
                        pcall(function()
                            m:SetPosition(TEN.Vec3(math.floor(nx), f, math.floor(nz)))
                            m:SetRotation(TEN.Rotation(0, math.deg(math.atan(dx, dz)), 0))
                        end)
                    end""")
once("""                    local c, cd = TrailPoint(lp, d - 1024)
                    if c ~= nil then""", """                    local c, cd = TrailPoint(lp, d - 1024)
                    local cf = c and CDV.FloorAt(c.x, c.y, c.z, c.room)
                    if c ~= nil and cf ~= nil and math.abs(cf - c.y) <= 64 then""")
open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print(name, "ok", len(s.splitlines()), "lines")
