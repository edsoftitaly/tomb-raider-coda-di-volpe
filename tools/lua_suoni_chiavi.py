"""Installed level scripts (Ed, 14/11/2026, 12:18):

1. the cue of a used item (CDV.MUSIC use_*) no longer starts with Lara's animation: it waits for the animation to
   end (key 131, insert 134, valve 470). Gates no longer play the «mechanism» track: the sound of a metal gate
   opening (221, TR4_Metal_Gate_Open) when the gate starts to move.
2. a key or a device is only used with Lara standing still on the ground (state 2): Action in mid jump did it in the
   air.
3. Marinello: the crank of the winch turned the wrong way; the sound of the great sluice starts with the flyby
   that shows it.

usage: lua_suoni_chiavi.py <in.lua> <out.lua>"""
import re
import sys

HELPERS = '''
-- The cue of a used item waits for Lara's animation to end (key 131, insert 134, valve 470), unless the level plays
-- it itself at its own moment (CDV.CUE_MANUAL).
CDV.CUE_MANUAL = CDV.CUE_MANUAL or {}
CDV.GATE_SFX = 221          -- TR4_Metal_Gate_Open
local USE_ANIMS = { [131] = true, [134] = true, [470] = true }
function CDV.CueAfterAnim(id)
    if CDV.MUSIC[id] == nil or CDV.CUE_MANUAL[id] then return end
    local n = 0
    local function wait()
        n = n + 1
        if n < 300 and (n < 25 or USE_ANIMS[Lara:GetAnim()]) then CDV.After(1, wait); return end
        CDV.Cue(id)
    end
    CDV.After(1, wait)
end
function CDV.GateSound()
    CDV.Sfx(CDV.GATE_SFX)
end
'''


def sub1(s, old, new, count=1):
    assert s.count(old) == count, (old[:60], s.count(old))
    return s.replace(old, new)


def patch(s):
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    assert "function CDV.CueAfterAnim" not in s, "already patched"
    m = re.search(r"\nfunction CDV\.End\(", s)
    s = s[:m.start()] + "\n" + HELPERS.rstrip("\n") + "\n" + s[m.start():]
    s = sub1(s, '                CDV.Cue("use_" .. u.id)\n', '                CDV.CueAfterAnim("use_" .. u.id)\n')
    # on the ground only
    a = "    if not CDV.Has(item) then return end\n    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) then return end\n    local lock = CDV.M(lockName)\n"
    s = sub1(s, a, a.replace("    local lock", "    if Lara:GetState() ~= 2 then return end          -- standing still, on the ground\n    local lock"))
    a = "    if not CDV.Near(x, y, z, r, 700) then return end\n    if not CDV.Has(item) then return end\n"
    s = sub1(s, a, a + "    if Lara:GetState() ~= 2 then return end          -- standing still, on the ground\n")
    a = "    local item = again or TEN.Inventory.GetUsedItem()\n"
    s = sub1(s, a, a + '''    if Lara:GetState() ~= 2 then                     -- in the air, running, climbing: nothing is used
        for _, u in ipairs(uses) do
            if item == u.item then TEN.Inventory.ClearUsedItem() return end
        end
    end
''')
    done = []
    # ---- Oliveri: the courtyard gate
    a = '    CDV.Flag("cancello_aperto", true)\n    CDV.Cue("use_argano")\n'
    if a in s:
        s = s.replace(a, '    CDV.Flag("cancello_aperto", true)\n    CDV.GateSound()\n')
        done.append("oliveri gate")
    # ---- Marinello
    a = '        CDV.InsertSeal("chiavistello", "sigillo_posto", function()\n            CDV.Enable("cancello_canneto")\n'
    if a in s:
        s = s.replace(a, '        CDV.InsertSeal("chiavistello", "sigillo_posto", function()\n            CDV.GateSound()\n            CDV.Enable("cancello_canneto")\n')
        s = sub1(s, '    use_lucchetto = "cdv_meccanismo",       -- Sigillo nella piastra\n', "")
        s = sub1(s, "(r0.z + 1080 * t) % 360", "(r0.z - 1080 * t) % 360")
        s = sub1(s, "        if f == 110 then CDV.Flyby(2) end\n",
                 '        if f == 110 then CDV.Flyby(2) end\n        if f == 116 then CDV.Cue("use_chiusa2") end          -- the sea coming in, with the pictures of it\n')
        s = sub1(s, "CDV.CUE_MANUAL = CDV.CUE_MANUAL or {}\n", 'CDV.CUE_MANUAL = CDV.CUE_MANUAL or {}\nCDV.CUE_MANUAL["use_chiusa2"] = true          -- played by CDV.OpenSluice when the flyby starts\n')
        done.append("marinello seal gate, crank, sluice")
    # ---- Tindari
    a = "        CDV.After(110, function() CDV.Enable(\"grata_cripto\") end)\n"
    if a in s:
        s = s.replace(a, '        CDV.After(110, function() CDV.GateSound(); CDV.Enable("grata_cripto") end)\n')
        s = sub1(s, '    use_grata = "cdv_meccanismo",           -- la chiave nel cancello del criptoportico\n', "")
        done.append("tindari grata")
    # ---- Sommersa
    a = '        CDV.Enable("porta_tempio")\n        CDV.Sfx(105)\n'
    if a in s:
        s = s.replace(a, '        CDV.Enable("porta_tempio")\n        CDV.GateSound()\n')
        done.append("sommersa temple gate")
    print("  ", done)
    return s.replace("\n", nl)


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8", newline="").read()
    open(sys.argv[2], "w", encoding="utf-8", newline="").write(patch(src))
