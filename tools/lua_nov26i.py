"""26 Nov 13:15. Oliveri: the man with the stick died at once when put behind Lara in the gallery (cause not found in
the sources; the log of that run stops before the key). He is switched on where he stood alive in every earlier
run: inside the box room, 55 frames after the key. His first 20 seconds are written to the log.
usage: lua_nov26i.py <in.lua> <out.lua>"""
import sys

src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")
old = """        -- the man with the stick comes up behind her as the key goes in (Ed, 26 Nov)
        local m = CDV.M("ladro_ripostiglio")
        if m ~= nil and m:GetValid() then
            pcall(function() CDV.Behind(m) end)
            CDV.Enable("ladro_ripostiglio")
            pcall(function() m:SetHP(70) end)
        end"""
new = """        CDV.After(55, function()          -- the man inside comes alive as the door opens, not before
            CDV.Enable("ladro_ripostiglio")
            local m = CDV.M("ladro_ripostiglio")
            if m ~= nil and m:GetValid() then pcall(function() m:SetHP(70) end) end
            local n = 0
            local function watch()            -- his first 20 seconds, for the log
                n = n + 1
                pcall(function()
                    local p, lp = m:GetPosition(), Lara:GetPosition()
                    CDV.Log(string.format("STICK hp %d active %s at %d %d %d room %s | lara %d %d %d", m:GetHP(), tostring(m:GetActive()),
                        p.x, p.y, p.z, m:GetRoom():GetName(), lp.x, lp.y, lp.z))
                end)
                if n < 40 then CDV.After(15, watch) end
            end
            watch()
        end)"""
assert s.count(old) == 1
s = s.replace(old, new)
open(dst, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
