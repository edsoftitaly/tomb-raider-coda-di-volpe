"""Scripted run of La meta' perduta (v2) against the mock engine: baths, cistern, gate, the two states, Turi, the escape."""
import sys

import luatest

D = sys.argv[1] if len(sys.argv) > 1 else "../build/levels/Sommersa"
ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


t = luatest.Harness(D + "/Sommersa.lua", luatest.load_names(D, "Sommersa"))
H = t.H


def zone(zid):
    z = [t.captured["zones"][i] for i in range(1, len(t.captured["zones"]) + 1) if t.captured["zones"][i].id == zid][0]
    t.at((z.x, z.y, z.z), 3)


def use_at(uid, item):
    u = [t.captured["uses"][i] for i in range(1, len(t.captured["uses"]) + 1) if t.captured["uses"][i].id == uid][0]
    t.at((u.x, u.y, u.z), 2); t.use(item); H.tick(60)


def obj(name):
    return t.lua.globals().TEN.Objects.GetMoveableByName(name).GetPosition(t.lua.globals().TEN.Objects.GetMoveableByName(name))


def altar():
    zone("tempio")
    u = [t.captured["uses"][i] for i in range(1, len(t.captured["uses"]) + 1) if t.captured["uses"][i].id == "altare2"][0]
    t.at((u.x, u.y, u.z), 2); H.press(); H.tick(100)


check(H.count(t.item("PUZZLE_ITEM7")) == 1, "Lara starts with the Astro di Castore")
check(sum(1 for v in t.last("show") if v.endswith("=false")) >= 4, "the four models to put are hidden at start")
zone("decumano"); H.tick(2)
check(H.active("h1") and H.active("h2"), "the men on the decumanus wake when Lara comes out of the water")
# the baths: the wheel floods them
p = obj("ruota_terme")
t.at((p.x, p.y + 620, p.z - 400), 2); H.press(); H.tick(300)
check(t.last("flip") == ["2"], "the wheel of the baths floods them: %s" % t.last("flip"))
H.press(); H.tick(300)
check(t.last("flip") == ["2"], "the wheel turns once")
check("porta_terme" not in t.last("enable"), "the gate of the loggia is shut without the cap")
H.give(t.item("PUZZLE_ITEM10")); H.tick(3)
check("porta_terme" in t.last("enable"), "with the Pileo di Castore the gate of the loggia opens")
# the cistern
zone("cisterna")
check(H.active("c1"), "the man of the cistern wakes")
t.at((36.5 * 1024, 0, 8.5 * 1024), 20)
check("tess_36_8" in t.last("shatter"), "a golden slab breaks under Lara")
t.at((34.5 * 1024, 0, 7.5 * 1024), 20)
check(len(t.last("shatter")) == 1, "a dark cap holds")
# the gate
use_at("pileo_c", "PUZZLE_ITEM10")
check("porta_tempio" not in t.last("enable"), "one cap does not open the temple")
H.give(t.item("PUZZLE_ITEM11"))
use_at("pileo_p", "PUZZLE_ITEM11")
check("porta_tempio" in t.last("enable"), "both caps open the temple")
# the temple
zone("tempio"); H.tick(2)
check(H.active("g1") and H.active("g2"), "the men in the cella wake")
altar()
check(t.last("flip") == ["2", "1"] and H.count(t.item("PUZZLE_ITEM7")) == 0, "Castore on the altar floods the cella: %s" % t.last("flip"))
check("squalo" in t.last("enable"), "the shark comes in with the sea")
H.setActive("leva_valve", True)
check("porta_valve" not in t.last("enable"), "under water the bronze doors stay shut")
t.captured["cdv"].Flag("leva_valve", True)
altar()
check(len(t.last("flip")) == 3 and "porta_valve" in t.last("enable") and H.count(t.item("PUZZLE_ITEM7")) == 1,
      "taking Castore back drains the cella and the doors open")
t.at((57.5 * 1024, 4096, 24.5 * 1024), 3)
check("turi" in t.last("enable"), "Turi wakes when Lara reaches the chamber on foot")
altar(); H.tick(130)
check(H.count(t.item("PUZZLE_ITEM8")) == 1, "flooding the cella drowns Turi and gives the Astro di Polluce")
zone("fine")
check(not t.last("end"), "no end before the two stars are on the altar")
use_at("altare2", "PUZZLE_ITEM8")
check("porta_fuga" in t.last("enable") and len(t.last("flip")) == 4, "both stars: the way out opens, the water stays (flips %d)" % len(t.last("flip")))
altar()
check(len(t.last("flip")) == 4, "the altar is dead during the escape")
zone("masso_fuga"); H.tick(3)
check("masso_fuga" in t.last("enable"), "the boulder starts")
zone("fine"); H.tick(260)
check(len(t.last("end")) == 1 and H.hp() > 0, "the game ends in the daylight")
H.tick(75 * 30)
check(H.hp() > 0, "the timer stops at the exit")
print("ALL OK" if ok else "SOME CHECKS FAILED")
