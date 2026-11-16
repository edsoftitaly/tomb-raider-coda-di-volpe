"""Enemies always come for Lara (Ed, 16 Nov: "ad ogni costo, sempre, indipendentemente da quanto distano").

In the engine an enemy that is switched on decides by itself whether to attack, stalk, flee or stand about
(GetCreatureMood, Game/control/box.cpp): dogs, bats and rats lose interest beyond three sectors, and every kind goes
idle when it has been hit and cannot reach Lara. TEN 2.0 lets a script fix the mood (Objects.Creature:SetMood). Every
ten frames each enemy of the level that is active and alive is put on ATTACK; the bats are also marked as hurt by
Lara, which is what makes a hanging bat let go whatever the distance.

What a script cannot do: walk an enemy through a room that has no pathfinding boxes, or wake one that the level has
not switched on yet (they are switched on by zone, so that nobody moves about behind a closed door).

  lua_caccia.py <level.prj2> <in.lua> <out.lua>"""
import sys

import prj2_patch as P

# creatures placed in the four levels (game_object_ids.h)
CREATURES = {118: "BAT", 129: "SHARK", 136: "DOBERMAN", 152: "GOON_SILENCER1", 153: "GOON_SILENCER2", 154: "GOON_SILENCER3",
             158: "WORKER_DUAL_REVOLVER", 172: "MP_WITH_STICK"}
MARK = "-- Every enemy that is on its feet comes for Lara"
BLOCK = MARK + ''', however far away she is (tools/lua_caccia.py).
local HUNTERS = { %s }
local HUNT_BATS = { %s }
local huntFrame, huntSaid = 0, false
CDV.Loop(function()
    huntFrame = huntFrame + 1
    if huntFrame %% 10 ~= 0 or Lara:GetHP() <= 0 then return end
    for _, name in ipairs(HUNTERS) do
        local m = CDV.M(name)
        if m ~= nil and m:GetValid() and m:GetActive() and m:GetHP() > 0 then
            local ok = pcall(function()
                local c = TEN.Objects.Creature(m)
                c:SetMood(TEN.Objects.MoodType.ATTACK)
                if HUNT_BATS[name] then c:SetHurtByPlayer(true) end
            end)
            if not huntSaid then
                huntSaid = true
                CDV.Log(ok and ("HUNT on, first " .. name) or "HUNT not available in this engine build")
            end
        end
    end
end)

'''


def main():
    prj, src, dst = sys.argv[1:4]
    ids = dict(CREATURES)
    for o in P.objects(prj):          # BIG_RAT and whatever else: taken by name of the slot below
        pass
    men, bats = [], []
    for o in P.objects(prj):
        if o[1] == "mov" and o[5] and (o[2] in ids or o[5].startswith("topo")):
            men.append(o[5])
            if o[2] == 118:
                bats.append(o[5])
    raw = open(src, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    t = raw.replace("\r\n", "\n")
    assert MARK not in t, "already done"
    a = "if CDV_TEST ~= nil then CDV_TEST(CDV, zones, uses) end"
    assert t.count(a) == 1
    block = BLOCK % (", ".join('"%s"' % n for n in men), ", ".join('["%s"] = true' % n for n in bats))
    t = t.replace(a, block + a)
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", "\r\n") if crlf else t)
    print(prj.split("/")[-1], "enemies:", len(men), "bats:", len(bats))


if __name__ == "__main__":
    main()
