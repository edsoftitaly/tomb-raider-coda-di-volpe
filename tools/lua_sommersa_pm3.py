"""The lost half, 16:54: Turi's fire was silent (the sounds were played where he stands, too far to be heard) and
balls already in the air still hit Lara after his death. The sounds are now played at Lara's ears (CDV.Sfx) and the
balls go out when he dies or the sea comes in.

  lua_sommersa_pm3.py <in.lua> <out.lua>"""
import sys

SUBS = [
    ('''            pcall(function() TEN.Sound.PlaySound(563, tp) end)                                   -- the roar of the flame
            pcall(function() TEN.Sound.PlaySound(({ 737, 477, 496 })[flameN % 3 + 1], tp) end)   -- and his shout
''', '''            CDV.Sfx(563)                                         -- the roar of the flame
            CDV.Sfx(({ 737, 477, 496 })[flameN % 3 + 1])         -- and his shout
'''),
    ('''            pcall(function() TEN.Sound.PlaySound(368, TEN.Vec3(math.floor(x), math.floor(y), math.floor(z))) end)
''', '''            CDV.Sfx(105)                                         -- it bursts
'''),
    ('''local balls, flameT, flameN = {}, 0, 0
CDV.Loop(function()
''', '''local balls, flameT, flameN = {}, 0, 0
CDV.Loop(function()
    if #balls > 0 and (CDV.Flag("turi_morto") or CDV.Flag("acqua")) then balls = {} end       -- he is gone: so is his fire
'''),
]


def main():
    src, dst = sys.argv[1:3]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    for old, new in SUBS:
        assert t.count(old) == 1, old[:60]
        t = t.replace(old, new)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("Sommersa.lua ok")


if __name__ == "__main__":
    main()
