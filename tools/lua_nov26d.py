"""26 Nov, fourth pass (Ed: more puzzles, a boss fight worth playing, every enemy comes after her).
  all four   an enemy that has noticed her and is not getting closer is walked to her along her trail (CDV.Carry);
             it also notices her within 2.5 sectors without seeing her
  Marinello  the net store is barred: a tally board of three pegs beside the door, the order in the ledger of the rais
  Sommersa   Turi in rounds: when he staggers there are 35 seconds to set the Star of Castor, or he recovers
usage: lua_nov26d.py <scripts/Levels dir>"""
import os
import sys

d = sys.argv[1]


def patch(name, pairs):
    p = os.path.join(d, name)
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    for a, b in pairs:
        a, b = a.replace("\n", nl), b.replace("\n", nl)
        assert s.count(a) == 1, (name, s.count(a), a[:80])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)
    print(name, len(pairs), "changes")


CARRY = '''-- 26 Nov: nobody stays behind. A man or a dog that has noticed her and is not getting any closer (a doorway it will
-- not cross, a step, a corner) is walked to her by the script, along her own trail, until it is within reach.
CDV.Carry = {}
local carryAt = {}
CDV.Loop(function()
    if Lara:GetHP() <= 0 then return end
    local lp = Lara:GetPosition()
    for name, on in pairs(CDV.Carry) do
        local m = CDV.M(name)
        if not on or m == nil or not m:GetValid() or not m:GetActive() or m:GetHP() <= 0 then
            CDV.Carry[name], carryAt[name] = nil, nil
        else
            local p = m:GetPosition()
            local flat = math.sqrt((p.x - lp.x) ^ 2 + (p.z - lp.z) ^ 2)
            if (flat < 1300 and math.abs(p.y - lp.y) < 600) or flat > LEASH then
                CDV.Carry[name], carryAt[name] = nil, nil
            else
                local tx, ty, tz = lp.x, lp.y, lp.z
                local clear = false
                pcall(function()
                    clear = TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(p.x, p.y - 700, p.z), TEN.Vec3(lp.x, lp.y - 700, lp.z)) == true
                end)
                if not clear and #trail > 0 then
                    local k = nil
                    for i = 1, #trail do if trail[i] == carryAt[name] then k = i end end
                    if k == nil then                     -- start from the point of her trail nearest to him
                        local best = nil
                        for i = 1, #trail do
                            local cd = (trail[i].x - p.x) ^ 2 + (trail[i].z - p.z) ^ 2
                            if best == nil or cd < best then best, k = cd, i end
                        end
                    end
                    local c = trail[k]
                    if (c.x - p.x) ^ 2 + (c.z - p.z) ^ 2 < 220 ^ 2 and k < #trail then k = k + 1; c = trail[k] end
                    carryAt[name] = c
                    tx, ty, tz = c.x, c.y, c.z
                end
                local dx, dz = tx - p.x, tz - p.z
                local dist = math.sqrt(dx * dx + dz * dz)
                if dist > 1 then
                    local step = math.min(30, dist)
                    local ny = p.y + math.max(-40, math.min(40, ty - p.y))
                    pcall(function()
                        m:SetPosition(TEN.Vec3(math.floor(p.x + dx / dist * step), math.floor(ny), math.floor(p.z + dz / dist * step)))
                        m:SetRotation(TEN.Rotation(0, math.deg(math.atan(dx, dz)), 0))
                    end)
                end
            end
        end
    end
end)

'''
HUNT = [(
    '''                if sees then
                    CDV.Aware[name] = true''',
    '''                if not sees and flat < 2560 and math.abs(p.y - lp.y) < 1024 then sees = true end      -- 26 Nov: she is heard
                if sees then
                    CDV.Aware[name] = true'''), (
    '''                if d > 5 * 1024 and d > s.d - 256 then s.n = s.n + 1 else s.n = 0 end
                s.d = d''',
    '''                if d > 1536 and d > s.d - 256 then s.n = s.n + 1 else s.n = 0 end
                s.d = d
                if s.n >= 2 and d <= 6 * 1024 and not CDV.Carry[name] and (CDV.CarryOk == nil or CDV.CarryOk(name, p, lp)) then   -- 26 Nov: near and not coming
                    CDV.Carry[name] = true
                    CDV.Log("HUNT " .. name .. " walked to her, " .. math.floor(d / 1024) .. " sectors away")
                end'''), (
    '''-- 26 Nov: the fights were too easy (reviews). Men and dogs start with more hit points.''',
    CARRY + '''-- 26 Nov: the fights were too easy (reviews). Men and dogs start with more hit points.''')]

# never through a gate that is still shut: who may be walked to her, level by level
OK = {
    "Oliveri.lua": 'CDV.CarryOk = function(name, p, lp) return name ~= "palo" or CDV.Flag("cancello_aperto") == true end',
    "Tindari.lua": 'CDV.CarryOk = function(name, p, lp) return (p.x > 108 * 1024) == (lp.x > 108 * 1024) end      -- the long wall',
    "Marinello.lua": 'CDV.CarryOk = function(name, p, lp) return (p.x > 30 * 1024) == (lp.x > 30 * 1024) or CDV.Done("use_lucchetto") end      -- the ridge and its gate',
}


def ok_line(name):
    return [("CDV.Carry = {}\nlocal carryAt = {}", "CDV.Carry = {}\n" + OK[name] + "\nlocal carryAt = {}")]


patch("Oliveri.lua", HUNT + ok_line("Oliveri.lua"))
patch("Tindari.lua", HUNT + ok_line("Tindari.lua"))
patch("Marinello.lua", HUNT + [(
    '''CDV.KickDoor("porta_reti", nil, "B")''',
    '''-- 26 Nov: the net store is no longer kicked open. Three pegs (small wall switches tacca_1..3) on the wall east of
-- its door make the tally board: the second and the third turned, the first left alone, as the ledger of the rais says.
local TALLY = { false, true, true }
CDV.Loop(function()
    if CDV.Flag("aperta_porta_reti") then return end
    local ok = true
    for i = 1, 3 do
        local n = "tacca_" .. i
        if CDV.Used(n) then
            CDV.Rearm(n)
            CDV.Flag(n, not (CDV.Flag(n) == true))
            CDV.Flag("tacca_t", 50)
        end
        if (CDV.Flag(n) == true) ~= TALLY[i] then ok = false end
    end
    local t = CDV.Flag("tacca_t") or 0
    if t > 0 then
        CDV.Flag("tacca_t", t - 1)
        if t == 1 then
            if ok then
                CDV.Flag("aperta_porta_reti", true)
                CDV.Enable("porta_reti")
                CDV.Sfx(105)
                CDV.Say("The bar lifts. The net store is open.", 5)
            elseif not CDV.Flag("tacca_detto") then
                CDV.Flag("tacca_detto", true)
                CDV.Say("Nothing. The rais kept the order of the pegs in his ledger.", 6)
            end
        end
    end
end)
CDV.Zone({ id = "reti_sbarrato", x = 67072, y = -512, z = 47616, r = 1500, dy = 900, once = true, text = "The net store is barred from inside. Beside the door, a tally board with three pegs.", secs = 7, need = function() return not CDV.Flag("aperta_porta_reti") end })'''), (
    '''The two levers of the Seal lie on the lake bed.'"''',
    '''The two levers of the Seal lie on the lake bed. Net store tally: leave the first peg, turn the second and the third.'"''')] + ok_line("Marinello.lua"))

patch("Sommersa.lua", HUNT + [(
    '''                if w >= TURI_WOUNDS then
                    CDV.Flag("turi_ferito", true)
                    CDV.Sfx(105)
                    CDV.Say("He staggers and the Star of Pollux flickers. Now: the altar!", 7)''',
    '''                if w >= TURI_WOUNDS then
                    CDV.Flag("turi_ferito", true)
                    CDV.Flag("turi_ferito_t", TURI_WINDOW)
                    CDV.Flag("turi_round", (CDV.Flag("turi_round") or 0) + 1)
                    CDV.Sfx(105)
                    CDV.Quake(20)
                    CDV.Say("He staggers and the Star of Pollux flickers. Thirty-five seconds: the altar!", 7)'''), (
    '''local turiHP = nil
local TURI_WOUNDS = 240''',
    '''local turiHP = nil
local TURI_WOUNDS = 240
local TURI_WINDOW = 35 * 30                       -- frames she has to set the Star of Castor once he staggers
-- the rounds: his Star flickers for TURI_WINDOW frames; if the Star of Castor is not on the altar by then he recovers
-- and has to be wounded again (half the wounds stay)
CDV.Loop(function()
    if not CDV.Flag("turi_ferito") or CDV.Flag("acqua") or CDV.Flag("turi_morto") then return end
    local t = (CDV.Flag("turi_ferito_t") or TURI_WINDOW) - 1
    CDV.Flag("turi_ferito_t", t)
    if t == 15 * 30 then CDV.Say("Fifteen seconds.", 3) end
    if t == 5 * 30 then CDV.Say("Five.", 2) end
    if t <= 0 then
        CDV.Flag("turi_ferito", false)
        CDV.Flag("turi_danni", math.floor(TURI_WOUNDS / 2))
        CDV.Quake(12)
        CDV.Say("Too slow: the Star of Pollux burns again. Wound him once more.", 6)
        CDV.Log("TURI recovers, round " .. tostring(CDV.Flag("turi_round")))
    end
end)''')])
