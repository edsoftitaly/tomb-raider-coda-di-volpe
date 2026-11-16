"""Oliveri: the opening caption and the first cue ("inizio") were started in OnStart together with the prologue video,
so the cue played under the music of the video and the caption was gone before the level was on screen.
They now wait for the video to be over (View.IsVideoPlaying), then for half a second.

  lua_dopo_video.py <Oliveri.lua in> <out>"""
import sys

OLD_SAY = '''CDV.StartList[#CDV.StartList + 1] = function()
    CDV.Say("Oliveri, the dead of night. The power is out, and there are noises downstairs: someone has broken in.", 7)
end'''
OLD_CUE = '''CDV.StartList[#CDV.StartList + 1] = function() CDV.Cue("inizio") end'''
NEW = '''-- What opens the level waits for the prologue video to be over: started with it, the cue played under its music.
function CDV.AfterVideo(fn)
    local n = 0
    local function wait()
        n = n + 1
        local playing = false
        pcall(function() playing = TEN.View.IsVideoPlaying() end)
        if n < 15 or (playing and n < 30 * 150) then CDV.After(1, wait); return end
        fn()
    end
    CDV.After(1, wait)
end
CDV.StartList[#CDV.StartList + 1] = function()
    CDV.AfterVideo(function()
        CDV.Cue("inizio")
        CDV.Say("Oliveri, the dead of night. The power is out, and there are noises downstairs: someone has broken in.", 7)
    end)
end'''


def main():
    src, dst = sys.argv[1:3]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    assert t.count(OLD_SAY) == 1 and t.count(OLD_CUE) == 1
    t = t.replace(OLD_SAY, NEW).replace(OLD_CUE + "\n", "")
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("opening caption and cue moved after the video")


if __name__ == "__main__":
    main()
