"""The end credits of the adventure (Ed, 16 Nov): cards over the black screen at the end of La meta' sommersa, while the
end titles play; then back to the title. Ed as the author of it all, Low and Attila as beta testers.

  lua_titoli_coda.py <Sommersa in.lua> <out.lua>"""
import sys

OLD = '''        pcall(function() TEN.View.FadeOut(0.4) end)
        CDV.After(200, function() CDV.End(0, 1) end)
'''
NEW = '''        pcall(function() TEN.View.FadeOut(0.4) end)
        CDV.After(210, function() CDV.Credits(1) end)
'''
BLOCK = '''
-- The end credits: one card after another over the black screen (strings are drawn over the fade), then the title.
-- Each card: a small line, then the names.
local CREDITS = {
    { "A Tomb Raider adventure", "CODA DI VOLPE" },
    { "Conceived, written and directed by", "EDOARDO NAPOLI" },
    { "Photographs of Oliveri, Marinello and Tindari", "EDOARDO NAPOLI" },
    { "Beta testers", "DARIO", "LOW", "ATTILA", "MARCO", "ANTONIO" },
    { "Models of the gang", "MADDEREK" },
    { "Music from Tomb Raider II and III", "NATHAN McCREE" },
    { "Made with TombEngine and Tomb Editor", "Level building and scripting with CLAUDE" },
    { "A fan adventure, free and not for sale.", "Tomb Raider and Lara Croft belong to their owners." },
    { "Oliveri, Sicily", "THANK YOU FOR PLAYING" },
}
local CARD = 140           -- frames a card stays (4.7 s)
function CDV.Credits(i)
    local card = CREDITS[i]
    if card == nil then
        CDV.After(45, function() CDV.End(0, 1) end)
        return
    end
    CDV.Log("CREDITS card " .. i)
    local opts = { TEN.Strings.DisplayStringOption.CENTER, TEN.Strings.DisplayStringOption.SHADOW }
    local y = 46 - 4 * #card
    for k, line in ipairs(card) do
        local big = k > 1
        local x, py = TEN.Util.PercentToScreen(50, y)
        local s = TEN.Strings.DisplayString(line, TEN.Vec2(x, py), big and 1.25 or 0.8,
            big and TEN.Color(255, 226, 150) or TEN.Color(255, 244, 214), false, opts)
        TEN.Strings.ShowString(s, (CARD - 14) / 30)
        y = y + (big and 9 or 7)
    end
    CDV.After(CARD, function() CDV.Credits(i + 1) end)
end
'''


def main():
    src, dst = sys.argv[1:3]
    raw = open(src, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    assert t.count(OLD) == 1 and "CDV.Credits" not in t
    t = t.replace(OLD, NEW)
    a = "CDV.StartList = CDV.StartList or {}\nCDV.StartList[#CDV.StartList + 1] = function()\n    for _, n in ipairs({ \"pileo_c_posto\""
    assert t.count(a) == 1
    t = t.replace(a, BLOCK.lstrip("\n") + "\n" + a)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", "\r\n") if crlf else t)
    print("credits added")


if __name__ == "__main__":
    main()
