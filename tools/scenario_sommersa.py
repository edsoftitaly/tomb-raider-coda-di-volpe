"""Scripted run of La meta' perduta against the mock engine: the two states, Turi, the timed escape."""
import luatest

KEY = "Sommersa"
D = "../build/levels/" + KEY
ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


def run(escape_in_time):
    t = luatest.Harness("%s/%s.lua" % (D, KEY), luatest.load_names(D, KEY))

    def zone(zid):
        z = [t.captured["zones"][i] for i in range(1, len(t.captured["zones"]) + 1) if t.captured["zones"][i].id == zid][0]
        t.at((z.x, z.y, z.z), 3)

    def altar():
        zone("altare"); t.H.tick(100); t.H.press(); t.H.tick(2)

    def use_at(uid, item):
        u = [t.captured["uses"][i] for i in range(1, len(t.captured["uses"]) + 1) if t.captured["uses"][i].id == uid][0]
        t.at((u.x, u.y, u.z), 2); t.use(item); t.H.tick(3)

    t.at((3.5 * 1024, 0, 15.5 * 1024), 3)
    if not escape_in_time:
        t.H.give(t.item("PUZZLE_ITEM8"))
        use_at("altare2", "PUZZLE_ITEM8")
        t.H.tick(75 * 30 + 5)
        check(t.H.hp() == 0, "the temple kills Lara when the 75 seconds run out")
        return
    check(t.H.count(t.item("PUZZLE_ITEM7")) == 1, "Lara starts with the Astro di Castore")
    zone("tempio"); t.H.tick(2)
    check(t.H.active("g1") and t.H.active("g2"), "the men in the cella wake when Lara enters the temple")
    altar()
    check(len(t.last("flip")) == 1 and not t.H.active("g1") or t.captured["cdv"] is not None, "Action at the altar floods the cella")
    check(len(t.last("flip")) == 1, "one flip for the flood: %s" % t.last("flip"))
    check("squalo" in t.last("enable"), "the shark comes in with the sea")
    t.H.pull("leva_valve"); t.H.tick(3)
    check("porta_valve" not in t.last("enable"), "the lever alone does not open the bronze doors under water")
    zone("valve"); t.H.tick(3)
    check("turi" not in t.last("enable"), "Turi sleeps while the doors are shut")
    altar()
    check(len(t.last("flip")) == 2 and "porta_valve" in t.last("enable"), "draining after the lever opens the doors")
    t.at((33.5 * 1024, 4096, 15.5 * 1024), 3)
    check("turi" in t.last("enable"), "Turi wakes when Lara reaches the chamber on foot")
    check(t.H.count(t.item("PUZZLE_ITEM8")) == 0, "Polluce is still Turi's")
    altar()
    t.H.tick(130)
    check(t.H.count(t.item("PUZZLE_ITEM8")) == 1, "flooding the cella drowns Turi and gives the Astro di Polluce")
    zone("fine")
    check(not t.last("end"), "no end before the two stars are on the altar")
    use_at("altare2", "PUZZLE_ITEM8")
    check("porta_fuga" in t.last("enable") and len(t.last("flip")) == 3, "both stars: the way out opens, the water stays (flips %d)" % len(t.last("flip")))
    altar()
    check(len(t.last("flip")) == 3, "the altar is dead during the escape")
    zone("masso_fuga")
    check(any(v.startswith("masso_fuga[0]=-800") for v in t.last("itemflags")), "the boulder rolls west along the gallery")
    zone("fine"); t.H.tick(260)
    check(len(t.last("end")) == 1 and t.H.hp() > 0, "the game ends in the daylight")
    t.H.tick(75 * 30)
    check(t.H.hp() > 0, "the timer stops at the exit")


run(True)
run(False)
print("ALL OK" if ok else "SOME CHECKS FAILED")
