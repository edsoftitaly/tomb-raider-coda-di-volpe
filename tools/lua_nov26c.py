"""26 Nov, third pass: two more Stars per level (secrets 4 and 5), Oliveri's playable rectangle, 20 secrets in Gameflow.
usage: lua_nov26c.py <scripts/Levels dir> <Gameflow.lua> [<Gameflow_release.lua>]"""
import os
import re
import sys

d = sys.argv[1]
STARS = {
    "Marinello.lua": [(4, 11, 57, 2560, "ID.SMALLMEDI_ITEM"), (5, 5, 38, 512, "ID.SHOTGUN_AMMO1_ITEM")],
    "Sommersa.lua": [(4, 31, 37, -2048, "ID.SMALLMEDI_ITEM"), (5, 40, 19, 0, "ID.SHOTGUN_AMMO1_ITEM")],
    "Oliveri.lua": [(4, 52, 31, 4608, "ID.SMALLMEDI_ITEM"), (5, 24, 17, 1280, "ID.SHOTGUN_AMMO1_ITEM")],
    "Tindari.lua": [(4, 86, 57, 24576, "ID.SMALLMEDI_ITEM"), (5, 74, 67, 24576, "ID.SHOTGUN_AMMO1_ITEM")],
}
AREA = '''-- 26 Nov: the town is closed outside this rectangle (sectors x0, z0, x1, z1): the barriers of the Carabinieri stand on
-- its edge in the streets (nov26_extra.py); past them she is put back where she was.
CDV.AREA = { { 12, 3, 52, 33 } }
local areaLast = nil
CDV.Loop(function()
    local p = Lara:GetPosition()
    local X, Z = p.x / 1024, p.z / 1024
    for _, r in ipairs(CDV.AREA) do
        if X >= r[1] and X < r[3] + 1 and Z >= r[2] and Z < r[4] + 1 then
            areaLast = { p.x, p.z }
            return
        end
    end
    if areaLast == nil then return end
    Lara:SetPosition(TEN.Vec3(math.floor(areaLast[1]), p.y, math.floor(areaLast[2])), false)
    if not CDV.Flag("detto_recinto") then
        CDV.Flag("detto_recinto", true)
        CDV.Say("The Carabinieri have closed the streets beyond here.", 5)
    end
end)

'''
for name, stars in STARS.items():
    p = os.path.join(d, name)
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    assert "index = 4," not in s, name
    lines = s.split(nl)
    last = max(i for i, ln in enumerate(lines) if ln.startswith("CDV.Secret({"))
    add = ["-- 26 Nov: two more Stars (the reviews asked for more to look for)"]
    for idx, X, Z, y, give in stars:
        add.append('CDV.Secret({ index = %d, x = %d, y = %d, z = %d, r = 900, give = %s, text = "" })' % (idx, X * 1024 + 512, -y, Z * 1024 + 512, give))
    lines[last + 1:last + 1] = add
    s = nl.join(lines)
    if name == "Oliveri.lua":
        assert s.count("local HUNTERS = {") == 1 and "CDV.AREA" not in s
        s = s.replace("local HUNTERS = {", AREA.replace("\n", nl) + "local HUNTERS = {")
    open(p, "w", encoding="utf-8", newline="").write(s)
    print(name, "secrets 4 and 5")
for g in sys.argv[2:]:
    s = open(g, encoding="utf-8", newline="").read()
    assert s.count("Flow.SetTotalSecretCount(12)") == 1, g
    open(g, "w", encoding="utf-8", newline="").write(s.replace("Flow.SetTotalSecretCount(12)", "Flow.SetTotalSecretCount(20)"))
    print(os.path.basename(g), "20 secrets")
