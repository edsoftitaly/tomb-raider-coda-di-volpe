"""26 Nov, Oliveri: the rectangle of this morning becomes a mask of sectors (nov26_oliveri_mask.json): she cannot leave
the house, the roof route, the street to the gate, the courtyard and the street to the town hall end. Secret 4 moves.
usage: lua_nov26f.py <scripts/Levels dir>"""
import json
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(here, "nov26_oliveri_mask.json")))
mask = {tuple(c) for c in D["mask"]}
x0, x1 = min(c[0] for c in mask), max(c[0] for c in mask)
z0, z1 = min(c[1] for c in mask), max(c[1] for c in mask)
rows = ",\n".join('    [%d] = "%s"' % (z, "".join("o" if (x, z) in mask else "." for x in range(x0, x1 + 1))) for z in range(z1, z0 - 1, -1))
p = os.path.join(sys.argv[1], "Oliveri.lua")
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
a = s.index("-- 26 Nov: the town is closed outside this rectangle")
b = s.index("-- 26 Nov: nobody stays behind.")
new = '''-- 26 Nov: the town is closed outside the sectors marked "o" (rows by z, first column x = %d; nov26_oliveri2.py): the
-- house, the roofs from the hatch to the Star and down to the street, the street to the gate, the lane and the
-- courtyard, the main street west to the town hall end. Barriers of the Carabinieri stand on every street edge;
-- past them, and anywhere else over the roofs, she is put back where she was.
CDV.AREA_X0 = %d
CDV.AREA = {
%s
}
local areaLast = nil
CDV.Loop(function()
    local p = Lara:GetPosition()
    local row = CDV.AREA[math.floor(p.z / 1024)]
    local k = math.floor(p.x / 1024) - CDV.AREA_X0 + 1
    if row ~= nil and k >= 1 and string.sub(row, k, k) == "o" then
        areaLast = { p.x, p.z }
        return
    end
    if areaLast == nil then return end
    Lara:SetPosition(TEN.Vec3(math.floor(areaLast[1]), p.y, math.floor(areaLast[2])), false)
    local id = (p.y < -3000) and "detto_tetti" or "detto_recinto"
    if not CDV.Flag(id) then
        CDV.Flag(id, true)
        CDV.Say((p.y < -3000) and "No way on over the roofs from here." or "The Carabinieri have closed the street. Not that way.", 5)
    end
end)

''' % (x0, x0, rows)
s = s[:a] + new.replace("\n", nl) + s[b:]
old = 'CDV.Secret({ index = 4, x = 53760, y = -4608, z = 32256, r = 900, give = ID.SMALLMEDI_ITEM, text = "" })'
assert s.count(old) == 1
X, Z, y = D["stella_4"]
s = s.replace(old, 'CDV.Secret({ index = 4, x = %d, y = %d, z = %d, r = 900, give = ID.SMALLMEDI_ITEM, text = "" })' % (X * 1024 + 512, -int(y), Z * 1024 + 512))
open(p, "w", encoding="utf-8", newline="").write(s)
print("Oliveri.lua: mask", len(mask), "sectors, x", x0, x1, "z", z0, z1)
