"""26 Nov, second pass: tougher men and dogs in all four levels (hit points x K at the start of the level), and
Tindari's playable ground cut to three rectangles (the same as the fence put by nov26_tindari.py).
usage: lua_nov26b.py <scripts/Levels dir>"""
import os
import sys

d = sys.argv[1]
TOUGH = {
    "Oliveri.lua": (1.3, ["cane1", "cane2", "palo", "ladro_chiave", "ladro_terra", "ladro_primo", "ladro_ripostiglio"]),
    "Marinello.lua": (1.6, ["t1", "t2", "t3", "t4", "t5", "t6", "t_chiave", "c1", "c2"]),
    "Tindari.lua": (1.7, ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "c1", "c2", "c3", "b1", "b2", "b3"]),
    "Sommersa.lua": (1.8, ["g0", "g1", "g2", "h1", "h2", "c1"]),
}
AREA = '''-- 26 Nov: the playable ground is three rectangles (sectors: x0, z0, x1, z1): the theatre; camp, compound and basilica;
-- sanctuary and belvedere. The fence of the dig stands on their edge (nov26_tindari.py); where she gets past it all the
-- same (a jump from high ground) she is put back where she was.
CDV.AREA = { { 26, 58, 66, 92 }, { 60, 20, 122, 90 }, { 118, 42, 168, 78 } }
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
        CDV.Say("Nothing out there but thistles. The dig is fenced for a reason.", 5)
    end
end)

'''
for name, (k, names) in TOUGH.items():
    p = os.path.join(d, name)
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    assert "CDV.TOUGH" not in s and s.count("local HUNTERS = {") == 1, name
    block = '''-- 26 Nov: the fights were too easy (reviews). Men and dogs start with more hit points.
CDV.TOUGH = %s
CDV.StartList[#CDV.StartList + 1] = function()
    for _, n in ipairs({ %s }) do
        local m = CDV.M(n)
        if m ~= nil and m:GetValid() then pcall(function() m:SetHP(math.floor(m:GetHP() * CDV.TOUGH)) end) end
    end
end

''' % (k, ", ".join('"%s"' % n for n in names))
    if name == "Tindari.lua":
        block = AREA + block
    s = s.replace("local HUNTERS = {", block.replace("\n", nl) + "local HUNTERS = {")
    open(p, "w", encoding="utf-8", newline="").write(s)
    print(name, "x", k, len(names), "enemies")
