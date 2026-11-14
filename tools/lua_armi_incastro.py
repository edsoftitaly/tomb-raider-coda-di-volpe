"""Every installed level script (Ed, 14/11/2026):

1. with a weapon in her hands Lara does not work doors, locks or devices: nothing happens (no more «she puts the
   pistols away and does it»), a short line tells why
2. the «insert» animation (LA_USE_PUZZLE, 134) for things that are fitted into something. It crashed because its
   frame 80 runs flip effect 13 (Puzzle -> DoPuzzle, Objects/Generic/puzzles_keys.cpp), which reads the item Lara is
   «interacting» with: there is none when a script starts the animation. CDV.PuzzleAnim() never lets frame 80 be the
   current one (it jumps from 77-79 to 81).

usage: lua_armi_incastro.py <in.lua> <out.lua>"""
import re
import sys

HELPERS = '''
-- With a weapon in her hands Lara does not work doors, locks or devices (Ed, 14/11): nothing happens.
local armedSaid = -1000
local armedClock = 0
function CDV.Armed()
    if armedClock - armedSaid > 240 then
        armedSaid = armedClock
        CDV.Say("Con le armi in mano non si può: prima nella fondina.", 3)
    end
end

-- The «insert» animation (LA_USE_PUZZLE, 134, state 43). Its frame 80 runs flip effect 13 (Puzzle), which crashes
-- when no puzzle hole of the engine is involved: that frame is skipped. Her item flag 0 (the animation the engine
-- would jump to at the end) is kept at zero.
function CDV.PuzzleAnim()
    pcall(function() Lara:SetItemFlags(0, 0) end)
    Lara:SetAnim(134)
    Lara:SetState(43)
    local n = 0
    local function guard()
        n = n + 1
        if n > 400 or Lara:GetAnim() ~= 134 then return end
        local f = Lara:GetFrame()
        if f >= 77 and f <= 80 then
            if not pcall(function() Lara:SetFrame(81) end) or Lara:GetFrame() ~= 81 then
                Lara:SetAnim(103)          -- no frame 81 in this Lara: stand, rather than reach frame 80
                Lara:SetState(2)
                return
            end
        end
        CDV.After(1, guard)
    end
    guard()
end
'''


def patch(s):
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    assert "function CDV.Armed" not in s, "already patched"
    # helpers after CDV.Holster
    m = re.search(r"function CDV\.Holster\(\)\n.*?\nend\n", s, re.S)
    s = s[:m.end()] + HELPERS + s[m.end():]
    n1 = s.count("if armed then CDV.Holster() return end")
    s = s.replace("if armed then CDV.Holster() return end", "if armed then CDV.Armed() return end")
    n2 = s.count("if not CDV.HandsFree() then CDV.Holster() return end")
    s = s.replace("if not CDV.HandsFree() then CDV.Holster() return end", "if not CDV.HandsFree() then CDV.Armed() return end")
    # an item chosen in the inventory with a weapon drawn: refused
    m = re.search(r"    if not CDV\.HandsFree\(\) then\n        for _, u in ipairs\(uses\) do\n            if item == u\.item then.*?\n        end\n    end\n", s, re.S)
    assert m and "CDV.Holster()" in m.group(0), "UseItem block"
    s = s[:m.start()] + ('    if not CDV.HandsFree() then\n        for _, u in ipairs(uses) do\n            if item == u.item then          -- weapon in hand: refused\n'
                         '                TEN.Inventory.ClearUsedItem()\n                CDV.Armed()\n                return\n            end\n        end\n    end\n') + s[m.end():]
    # the kick
    k = s.index("function CDV.KickDoor(")
    a = "        if Lara:GetState() ~= 2 then return end\n"
    j = s.index(a, k)
    s = s[:j + len(a)] + "        if not CDV.HandsFree() then CDV.Armed() return end\n" + s[j + len(a):]
    # the clock of CDV.Armed
    a = "function CDV.Tick()\n"
    assert s.count(a) == 1
    s = s.replace(a, a + "    armedClock = armedClock + 1\n")
    # the insert animation
    n3 = 0
    if "function CDV.InsertItem(fn, mid)" in s:
        a = "    local anim = CDV.USE_PUZZLE_ANIM and 134 or 131\n    Lara:SetAnim(anim)\n    Lara:SetState(CDV.USE_PUZZLE_ANIM and 43 or 42)\n"
        assert s.count(a) == 1
        s = s.replace("function CDV.InsertItem(fn, mid)", "function CDV.InsertItem(fn, mid, key)          -- key = true: a key is turned (131), not a thing fitted in (134)")
        s = s.replace(a, "    local anim = (CDV.USE_PUZZLE_ANIM and not key) and 134 or 131\n    if anim == 134 then CDV.PuzzleAnim() else Lara:SetAnim(131); Lara:SetState(42) end\n")
        s, c = re.subn(r"(?m)^CDV\.USE_PUZZLE_ANIM = false[^\n]*", "CDV.USE_PUZZLE_ANIM = true           -- 134 with its frame 80 skipped (CDV.PuzzleAnim)", s)
        assert c == 1
        n3 += 1
    a = "        Lara:SetAnim(131)          -- LA_USE_KEY. Not 134 (use puzzle): its state crashes the game on its last frame.\n        Lara:SetState(42)\n"
    if a in s:                                                  # the Seal of Marinello
        s = s.replace(a, "        CDV.PuzzleAnim()           -- the insert animation, frame 80 skipped\n")
        b = "(waited < 20 or Lara:GetAnim() == 131)"
        assert s.count(b) == 1
        s = s.replace(b, "(waited < 20 or Lara:GetAnim() == 134)")
        n3 += 1
    print("  holster->armed: %d + %d, insert animation: %d" % (n1, n2, n3))
    return s.replace("\n", nl)


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8", newline="").read()
    open(sys.argv[2], "w", encoding="utf-8", newline="").write(patch(src))
