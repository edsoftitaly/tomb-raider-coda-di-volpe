"""16 Nov, afternoon. Script side of Ed's list:

  all levels   an enemy that walks is never switched on while the place where it stands is on screen: CDV.Enable
               waits until the camera looks elsewhere or a wall is in between (8 s at most), so they come from behind
  Oliveri, Sommersa   CDV.InsertItem: the thing put in place appears on the click of the animation (frame 76 of
               the insert, 103 of the key), not after a fixed 40 frames
  Marinello    the roof of the way out gives way when Lara is five sectors further in (no stepping back to the door)
  Tindari      the mosaic of the domus: new list of the tiles that fall (given by tindari_pm.py) and they fall at
               once; spikes of the cryptoporticus switched on, nobody walks out of that pit either

  lua_16nov_pm.py <level> <in.lua> <out.lua> [tiles.json]"""
import json
import re
import sys

OLD_MID = "        if n == 40 and mid then mid() end\n"
NEW_MID = """        if mid and (n >= (anim == 134 and 82 or 109) or (Lara:GetAnim() == anim and Lara:GetFrame() >= (anim == 134 and 76 or 103))) then
            mid()          -- on the click of the animation (its sound command), not before
            mid = nil
        end
"""

BEHIND = '''-- Enemies come from behind. One that walks is not switched on while the place where it stands is on screen
-- (in front of the camera, within the fog, nothing in between): CDV.Enable waits for the camera to look elsewhere,
-- eight seconds at most. The ones waiting are in LevelVars, so a saved game does not lose them.
local WALKERS = { %(names)s }
local SIGHT = %(sight)d * 1024
local EnableNow = CDV.Enable
local function OnScreen(m)
    local ok, seen = pcall(function()
        local cp, ct, p = TEN.View.GetCameraPosition(), TEN.View.GetCameraTarget(), m:GetPosition()
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
function CDV.Enable(name)
    local m = CDV.M(name)
    if not WALKERS[name] or m == nil or not m:GetValid() or m:GetActive() then return EnableNow(name) end
    if LevelVars.CDV_wait == nil then LevelVars.CDV_wait = {} end
    if LevelVars.CDV_wait[name] == nil then LevelVars.CDV_wait[name] = 0 end
end
CDV.Loop(function()
    local w = LevelVars.CDV_wait
    if w == nil then return end
    for name, t in pairs(w) do
        local m = CDV.M(name)
        if m == nil or not m:GetValid() then
            w[name] = nil
        elseif t >= 240 or not OnScreen(m) then
            w[name] = nil
            EnableNow(name)
            CDV.Log("ENEMY " .. name .. (t >= 240 and " in after 8 s on screen" or " in, out of sight"))
        else
            w[name] = t + 1
        end
    end
end)

'''
WALKERS = {
    "Oliveri": (36, ["cane1", "cane2", "ladro_chiave", "ladro_primo", "ladro_ripostiglio", "ladro_terra", "palo"]),
    "Marinello": (30, ["c1", "c2", "t1", "t2", "t3", "t4", "t5", "t6", "t_chiave"]),
    "Tindari": (60, ["b1", "b2", "b3", "c1", "c2", "c3", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]),
    "Sommersa": (30, ["c1", "g0", "g1", "g2", "h1", "h2"]),          # Turi makes his own entrance
}


def sub1(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:70])
    return t.replace(old, new)


def main():
    level, src, dst = sys.argv[1:4]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    sight, names = WALKERS[level]
    block = BEHIND % {"names": ", ".join('["%s"] = true' % n for n in names), "sight": sight}
    t = sub1(t, "local HUNTERS = {", block + "local HUNTERS = {")
    if OLD_MID in t:
        t = sub1(t, OLD_MID, NEW_MID)
        a = t.index(NEW_MID) + len(NEW_MID)
        b = t.index("        if fn then fn() end", a)
        t = t[:b] + "        if mid then mid() end\n" + t[b:]
    if level == "Marinello":
        t = sub1(t, 'CDV.Zone({ id = "masso_g", x = 19968, y = 1024, z = 36352, r = 900,', 'CDV.Zone({ id = "masso_g", x = 19968, y = 1024, z = 41472, r = 700,')
    if level == "Tindari":
        d = json.load(open(sys.argv[4]))
        keys = d["tiles"]
        lst = ", ".join('"%s"' % k for k in keys)
        t, n = re.subn(r'for _, k in ipairs\(\{ "77_79"[^}]*\}\) do CDV\.Enable\("punte_" \.\. k\) end',
                       'for _, k in ipairs({ %s }) do CDV.Enable("punte_" .. k) end\n    for _, k in ipairs({ %s }) do CDV.Enable("punte_cripto_" .. k) end'
                       % (lst, ", ".join('"%s"' % k for k in d["cripto"])), t)
        assert n == 1
        t, n = re.subn(r'local WRONG = \{[^}]*\}', "local WRONG = { %s }" % ", ".join('["%s"] = true' % k for k in keys), t)
        assert n == 1
        t = sub1(t, "        elseif t < 14 then                                           -- it shakes under her feet",
                 "        elseif t < 4 then                                            -- it shakes under her feet, and is gone")
        x0, x1, z0, z1, floor = d["pit"]
        t = sub1(t, 'CDV.Zone({ id = "mosaico", ', '''-- the pit of the cryptoporticus: the spikes kill by themselves; should they ever fail, nobody walks out of it
CDV.Loop(function()
    local p = Lara:GetPosition()
    local sx, sz = math.floor(p.x / 1024), math.floor(p.z / 1024)
    if sx >= %d and sx <= %d and sz >= %d and sz <= %d and p.y > %d - 96 and Lara:GetHP() > 0 then
        local n = (CDV.Flag("fossa_cripto") or 0) + 1
        CDV.Flag("fossa_cripto", n)
        if n > 45 then Lara:SetHP(0) end
    end
end)

CDV.Zone({ id = "mosaico", ''' % (x0, x1, z0, z1, -floor))
        # the secret that lay on the bottom of that pit: now on the far ledge, in the corner
        t = sub1(t, 'CDV.Secret({ index = 2, x = 105984, y = -18944, z = 58880, r = 900,', 'CDV.Secret({ index = 2, x = 107008, y = -20992, z = 60928, r = 600,')
        t = sub1(t, 'text = "The floor has fallen in, but a rope hangs from the vault."', 'text = "The floor has fallen in, onto iron spikes. A rope hangs from the vault."')
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print(level, "ok")


if __name__ == "__main__":
    main()
