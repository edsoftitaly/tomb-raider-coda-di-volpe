import luatest
import content_laghetti as L
import content_tindari as T


def P(wx, wz, h):
    return ((wx + 0.5) * 1024, -h, (wz + 0.5) * 1024)


def zone(t, zid):
    zs = t.captured["zones"]
    for i in range(1, len(zs) + 1):
        if zs[i].id == zid:
            return (zs[i].x, zs[i].y, zs[i].z)
    raise KeyError(zid)


ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


# Laghetti: tonnara order.
D = "../build/levels/Laghetti"
t = luatest.Harness(D + "/Laghetti.lua", luatest.load_names(D, "Laghetti"))
check(t.H.count(t.item("PUZZLE_ITEM3")) == 1, "tide map given at start if missing")
for name in ("camera_levante", "camera_ponente"):
    t.at(zone(t, name), 3)
check(t.last("air") == ["300"], "wrong order drains air")
check("rete_morte" not in t.last("enable"), "door shut after wrong order")
for name in ("camera_levante", "camera_tramontana", "camera_ponente"):
    t.at(zone(t, name), 3)
check("rete_morte" in t.last("enable"), "door opens with levante, tramontana, ponente")
t.at(zone(t, "agguato"), 3)
check("banda0" not in t.last("enable"), "no ambush before the seal")
t.at(zone(t, "fine"), 3)
check(not t.last("end"), "no exit without the seal")
t.H.give(t.item("PUZZLE_ITEM6"))
t.at(zone(t, "agguato"), 3)
check(all(("banda%d" % i) in t.last("enable") for i in range(5)), "ambush on the west shore after the seal")
t.at(zone(t, "fine"), 3)
check(t.last("end") == ["5:1"], "exit to Tindari with the seal")

# Tindari: twin levers and crypt order.
D = "../build/levels/Tindari"
t = luatest.Harness(D + "/Tindari.lua", luatest.load_names(D, "Tindari"))
t.H.tick(1)
t.H.pull("leva_basilica")
t.H.tick(3)
check("botola_teatro" not in t.last("enable"), "one lever is not enough")
t.H.pull("leva_torre")
t.H.tick(3)
check("botola_teatro" in t.last("enable"), "both levers open the theatre trapdoor")
for key in ("luna", "sole"):
    t.H.pull("leva_" + key); t.H.tick(2); t.H.pull("leva_" + key); t.H.tick(2)
check("porta_astro" not in t.last("enable"), "wrong crypt order keeps the niche shut")
check("ratto_extra0" in t.last("enable") and "ratto_extra1" in t.last("enable"), "wrong crypt order releases rats")
for key in ("luna", "stella", "sole"):
    t.H.pull("leva_" + key); t.H.tick(2); t.H.pull("leva_" + key); t.H.tick(2)
check("porta_astro" in t.last("enable"), "luna, stella, sole opens the niche")
t.at(zone(t, "discesa"), 3)
check(not t.last("end"), "no exit to the sea without the Astro")
t.H.give(t.item("PUZZLE_ITEM7"))
t.at(zone(t, "astro"), 3)
check("porta_mare" in t.last("enable") and "donna_villa0" in t.last("enable"), "Astro opens the sea passage and wakes the spirits")
t.at(zone(t, "discesa"), 3)
check(t.last("end") == ["6:1"], "the passage to the sea ends the level towards Sommersa")

# Sommersa: witch, Turi, altar.
D = "../build/levels/Sommersa"
t = luatest.Harness(D + "/Sommersa.lua", luatest.load_names(D, "Sommersa"))
t.at(zone(t, "strega"), 3)
t.H.kill("donna_villa"); t.H.tick(3)
check("porta_tempio" in t.last("enable"), "witch death opens the temple")
t.H.kill("turi"); t.H.tick(3)
check(t.H.count(t.item("PUZZLE_ITEM8")) == 1, "Turi drops the Astro di Polluce")
uses = t.captured["uses"]
u = uses[1]
t.at((u.x, u.y, u.z), 1)
t.use("PUZZLE_ITEM8")
t.H.tick(760)
check(t.last("end") == ["nil:nil"], "final sequence ends the game")
print("ALL OK" if ok else "SOME FAILED")
