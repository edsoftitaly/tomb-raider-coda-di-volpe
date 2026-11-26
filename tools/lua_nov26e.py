"""26 Nov: Tindari, the pegs of the dig house. Three small wall switches (piolo_1..3) on the wall east of the door:
the first and the third turned free the bolt; only then does the Dig Site Key go in. The order is chalked in the theatre.
usage: lua_nov26e.py <scripts/Levels dir>"""
import os
import sys

p = os.path.join(sys.argv[1], "Tindari.lua")
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"


def rep(a, b):
    global s
    a, b = a.replace("\n", nl), b.replace("\n", nl)
    assert s.count(a) == 1, (s.count(a), a[:70])
    s = s.replace(a, b)


rep('''CDV.Use({ id = "lucchetto", item = ID.PUZZLE_ITEM13, x = 83456, y = -24832, z = 52736, r = 1500, dy = 800, consume = true, near = "porta_casa", fn = function()''',
    '''-- 26 Nov: the pegs. A chain runs from three iron pegs to the bolt of the door: first and third turned, it drops.
local PEGS = { true, false, true }
CDV.Loop(function()
    if CDV.Flag("tavola_ok") then return end
    local ok = true
    for i = 1, 3 do
        local n = "piolo_" .. i
        if CDV.Used(n) then
            CDV.Rearm(n)
            CDV.Flag(n, not (CDV.Flag(n) == true))
            CDV.Flag("piolo_t", 50)
        end
        if (CDV.Flag(n) == true) ~= PEGS[i] then ok = false end
    end
    local t = CDV.Flag("piolo_t") or 0
    if t > 0 then
        CDV.Flag("piolo_t", t - 1)
        if t == 1 then
            if ok then
                CDV.Flag("tavola_ok", true)
                CDV.Sfx(105)
                CDV.Say("The chain drops from the bolt. Now the door only wants its key.", 6)
            elseif not CDV.Flag("piolo_detto") then
                CDV.Flag("piolo_detto", true)
                CDV.Say("The chain holds. Someone at the theatre must know the order of the pegs.", 6)
            end
        end
    end
end)
CDV.Zone({ id = "pioli_casa", x = 83456, y = -24832, z = 52224, r = 1800, dy = 800, once = true, text = "The house in the dig: a keyhole, and three iron pegs with a chain to the bolt.", secs = 7, need = function() return not CDV.Flag("tavola_ok") end })
CDV.Zone({ id = "pioli_indizio", x = 39424, y = -25088, z = 86528, r = 2600, dy = 1500, once = true, text = "Chalked on the stage wall: 'Dig house: first peg and third.'", secs = 8 })

CDV.Use({ id = "lucchetto", item = ID.PUZZLE_ITEM13, x = 83456, y = -24832, z = 52736, r = 1500, dy = 800, consume = true, near = "porta_casa", need = function() return CDV.Flag("tavola_ok") == true end, fn = function()''')
rep('''    if CDV.Done("use_lucchetto") or not CDV.Has(ID.PUZZLE_ITEM13) then return end
    local m = CDV.M("porta_casa")''',
    '''    if CDV.Done("use_lucchetto") or not CDV.Has(ID.PUZZLE_ITEM13) or not CDV.Flag("tavola_ok") then return end
    local m = CDV.M("porta_casa")''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("Tindari.lua: pegs")
