"""26 Nov, Ed: "stop improvising, fix the enemies as it is supposed to be". The scripts no longer move enemies or force
their mood: no walk to Lara (CDV.Carry), no "put on her trail", no SetMood(ATTACK). The engine decides, as in
box.cpp: a violent creature (goons, workers, dogs, the man with the stick) attacks whenever Lara's box is in its
zone and wanders when it is not. What stays in the scripts: an enemy is switched on out of sight (Ed, 12 Nov), the
hit points, bats flagged as hurt.   usage: lua_nov26h.py <Level> <in.lua> <out.lua>"""
import re
import sys

name, src, dst = sys.argv[1:4]
s = open(src, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")

# 1. the hunt loop: awareness stays (log only), the stuck counter and the teleport go
a = s.index("            if CDV.Aware[name] then\n                local s = stuck[name] or { d = d, n = 0 }")
end_mark = "        else\n            stuck[name] = nil\n        end\n"
b = s.index(end_mark, a)
assert "put on her trail" in s[a:b] and s[a:b].count("CDV.Loop") == 0
s = s[:a] + "        end\n" + s[b + len(end_mark):]

# 2. the carry loop goes; CDV.FloorAt stays (Oliveri uses it)
a = s.index("\nCDV.Carry = {}\n")
b = s.index("\n-- 26 Nov: the fights were too easy")
assert s[a:b].count("CDV.Loop(function()") == 1 and s[a:b].rstrip().endswith("end)")
s = s[:a] + "\n" + s[b:]
s = s.replace("""-- 26 Nov: nobody stays behind. A man or a dog that has noticed her and is not getting any closer (a doorway it will
-- not cross, a step, a corner) is walked to her by the script, along her own trail, until it is within reach.
""", "-- The floor under a point (nil: none, or a wall).\n")
s = re.sub(r"\nCDV\.CarryOk = function\(name, p, lp\) return [^\n]*", "", s)
assert "CDV.Carry" not in s, [l for l in s.split("\n") if "CDV.Carry" in l][:3]

# 3. the mood is the engine's own
old = """                if WALKERS[name] and not CDV.Aware[name] then
                    -- it has not seen her: the engine's own mood (never forced). One that gave up is let go.
                    if CDV.Aware[name] == false then c:SetMood(TEN.Objects.MoodType.AUTO or TEN.Objects.MoodType.BORED) end
                else
                    c:SetMood(TEN.Objects.MoodType.ATTACK)
                end
"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, """                -- the engine's own mood: a mood forced by an older script (a savegame) is released
                if TEN.Objects.MoodType.AUTO ~= nil then c:SetMood(TEN.Objects.MoodType.AUTO) end
""")
open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print(name, "ok", len(s.split("\n")), "lines; SetPosition on m left:", s.count("m:SetPosition("))
