#!/usr/bin/env python3
"""Earthquakes that can be seen. Effects.MakeEarthquake(n) sets Camera.bounce = -n, which the engine brings back by 5
a frame while shaking the camera target by +-n/2 units (camera.cpp, CalculateBounce): the 10..30 used so far lasted
2..6 frames of a few units. CDV.Quake(n) keeps the old numbers as a scale: strength n*5 (150 at most, the engine's
own default is 100) held for n*2 frames, then the engine's own decay.

  lua_terremoti.py <Level.lua> ..."""
import re, sys
HELPER = '''-- An earthquake that can be seen: strength s*5 (150 at most) held for s*2 frames, then the engine lets it die away.
function CDV.Quake(s)
    local n, str = s * 2, math.min(150, s * 5)
    local function go()
        pcall(function() TEN.Effects.MakeEarthquake(str) end)
        n = n - 1
        if n > 0 then CDV.After(1, go) end
    end
    go()
end

'''
for p in sys.argv[1:]:
    s = open(p, encoding="utf-8", newline="").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    assert "function CDV.Quake" not in s, "already done"
    s, n = re.subn(r"pcall\(function\(\) TEN\.Effects\.MakeEarthquake\(([^()]+)\) end\)", r"CDV.Quake(\1)", s)
    assert "MakeEarthquake" not in s, "a call in another form"
    a = "local function TimersTick()"
    assert s.count(a) == 1
    s = s.replace(a, HELPER + a)
    if crlf: s = s.replace("\n", "\r\n")
    open(p, "w", encoding="utf-8", newline="").write(s)
    print(p, n, "calls")
