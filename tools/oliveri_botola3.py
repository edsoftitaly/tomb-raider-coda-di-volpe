"""Oliveri, the trapdoor, third pass (Ed, 14/11/2026 11:56: the padlock falls before the key has turned, and the hatch
does not open when Lara climbs).

- the padlock is released 108 frames into the key animation (131): the sound of the lock is at its frame 103
- the plug of the hole (the hidden bridge tappo_botola) is moved out of the way and then destroyed, as soon as the
  padlock is open and again when the hatch opens
- the hatch no longer waits for a narrow zone at the top of the ladder: it opens as soon as Lara, in the column of the
  hatch, is 450 units above the floor of the box room

usage: oliveri_botola3.py <Oliveri.lua> <out.lua>"""
import re
import sys

ZONE = re.compile(r'CDV\.Zone\(\{ id = "botola", .*?\n    end \}\)\n', re.S)
ZONE_NEW = '''-- The hatch: once the padlock is off it opens as soon as Lara is on the ladder under it (450 units off the floor).
function CDV.PlugOff()
    local m = CDV.M("tappo_botola")
    if m == nil or not m:GetValid() then return end
    pcall(function() local p = m:GetPosition(); m:SetPosition(TEN.Vec3(p.x, p.y - 3000, p.z)) end)   -- off the hole first
    pcall(function() m:Destroy() end)
end
CDV.Loop(function()
    if CDV.Flag("botola_aperta") or not CDV.Done("use_lucchetto_botola") then return end
    local p = Lara:GetPosition()
    if math.abs(p.x - 29184) < 700 and math.abs(p.z - 30208) < 700 and p.y < -4352 - 450 then
        CDV.Flag("botola_aperta", true)
        CDV.PlugOff()
        CDV.Swing("botola_legno", "z", 75, 30)
        CDV.Log("HATCH open, Lara y " .. p.y)
    end
end)
'''
USE_OLD = re.compile(r'        CDV\.InsertItem\(nil, function\(\) +-- a key is turned.*?\n        end, true\)\n', re.S)
USE_NEW = '''        CDV.InsertItem(nil, nil, true)                    -- a key is turned: animation 131, its lock sounds at frame 103
        CDV.After(108, function()                         -- only then does the padlock let go
            PadlockFall(function()
                CDV.PlugOff()
                CDV.Log("PADLOCK open")
            end)
        end)
'''

s = open(sys.argv[1], encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")
for rx, new in ((ZONE, ZONE_NEW), (USE_OLD, USE_NEW)):
    assert len(rx.findall(s)) == 1, rx.pattern[:30]
    s = rx.sub(lambda m: new, s)
open(sys.argv[2], "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
