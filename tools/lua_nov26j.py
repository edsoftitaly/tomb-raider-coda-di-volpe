"""26 Nov 13:40, Oliveri. The man with the stick is switched on when the box room door is open, not before: until
then the sector under the door is a blocked box, and his kind loses 20 hit points a frame on one (tr3_mp_stick.cpp).
The street is closed one sector further east, where Ed moved the barriers.   usage: lua_nov26j.py <in> <out>"""
import sys

src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")


def once(a, b):
    global s
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)


once("""        CDV.After(55, function()          -- the man inside comes alive as the door opens, not before
            CDV.Enable("ladro_ripostiglio")
            local m = CDV.M("ladro_ripostiglio")""", """        local tries = 0
        local function wake()             -- the man inside comes alive once the door is open, not before
            tries = tries + 1
            local door = CDV.M("porta_ripostiglio")
            if tries < 400 and (door == nil or not door:GetActive()) then CDV.After(1, wake); return end
            if tries < 1000 then tries = 1000; CDV.After(15, wake); return end      -- the leaf has swung
            CDV.Enable("ladro_ripostiglio")
            local m = CDV.M("ladro_ripostiglio")""")
once("""                if n < 40 then CDV.After(15, watch) end
            end
            watch()
        end)""", """                if n < 40 then CDV.After(15, watch) end
            end
            watch()
        end
        wake()""")
once("CDV.AREA = { { 13, 16, 20, 25 }, { 13, 17, 51, 24 }, { 21, 3, 51, 33 } }", "CDV.AREA = { { 13, 16, 20, 25 }, { 13, 17, 52, 24 }, { 21, 3, 52, 33 } }")
open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
