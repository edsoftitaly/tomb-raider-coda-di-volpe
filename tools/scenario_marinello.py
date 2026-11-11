"""Scripted run of Marinello (livello 1 intero) against the mock engine: the whole puzzle chain, in order and out of order.
Usage: python3 scenario_marinello.py [MarinelloB]"""
import sys

import luatest

KEY = sys.argv[1] if len(sys.argv) > 1 else "Marinello"
D = "../build/levels/" + KEY
names = luatest.load_names(D, KEY)
t = luatest.Harness("%s/%s.lua" % (D, KEY), names)
ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


def use_at(uid, item):
    u = [t.captured["uses"][i] for i in range(1, len(t.captured["uses"]) + 1) if t.captured["uses"][i].id == uid][0]
    t.at((u.x, u.y, u.z), 2)
    t.use(item)
    t.H.tick(3)


def zone(zid):
    z = [t.captured["zones"][i] for i in range(1, len(t.captured["zones"]) + 1) if t.captured["zones"][i].id == zid][0]
    t.at((z.x, z.y, z.z), 3)


far = (10 * 1024, 0, 100 * 1024)
t.at(far, 3)
# nothing opens by itself
check("porta_sigillo" not in t.last("enable") and "cancello_canneto" not in t.last("enable"), "doors shut at the start")
# sluice without the crank
use_at("chiusa", "PUZZLE_ITEM6")
check(not t.last("flip") and not t.H.active("t3"), "the sluice ignores the wrong item")
# crate on the slab raises the block
check("blocco_soppalco" not in t.last("enable"), "block down before the crate is on the slab")
t.H.put("cassa_reti", 64.5 * 1024, -512, 51.5 * 1024)
t.H.tick(3)
check("blocco_soppalco" in t.last("enable"), "crate on the slab raises the block")
# the crank drains the lake
t.H.give(t.item("PUZZLE_ITEM9"))
use_at("chiusa", "PUZZLE_ITEM9")
if KEY == "Marinello":
    check(t.last("flip") == ["1"], "the crank flips the lake (group 1), once: %s" % t.last("flip"))
t.H.tick(150)
check("t3" in t.last("enable") and "t4" in t.last("enable"), "two more men come after the lake drains")
use_at("chiusa", "PUZZLE_ITEM9")
check(len(t.last("flip")) <= 1, "the sluice cannot be used twice")
# twin levers: late, then in time
t.at(far, 2)
t.H.pull("leva_fondo_0"); t.H.tick(700)
t.H.pull("leva_fondo_1"); t.H.tick(5)
check("porta_sigillo" not in t.last("enable"), "levers 23 s apart: the seal chamber stays shut")
t.H.tick(100); t.H.pull("leva_fondo_0"); t.H.tick(5)
check("porta_sigillo" in t.last("enable"), "second try within 20 s opens the seal chamber")
# the gate
use_at("lucchetto", "PUZZLE_ITEM9")
check("cancello_canneto" not in t.last("enable"), "the gate ignores the crank")
t.H.give(t.item("PUZZLE_ITEM6"))
use_at("lucchetto", "PUZZLE_ITEM6")
check("cancello_canneto" in t.last("enable"), "the Sigillo opens the gate")
# ---- part 2: the Lago Verde
zone("canneto"); t.H.tick(3)
check("t5" in t.last("enable") and "t6" in t.last("enable"), "the men of the reed bed wake beyond the gate")
use_at("chiusa2", "PUZZLE_ITEM6")
check(t.last("flip").count("2") == 0, "the great sluice ignores the wrong item")
t.H.give(t.item("PUZZLE_ITEM4"))
use_at("chiusa2", "PUZZLE_ITEM4")
if KEY == "Marinello":
    check(t.last("flip").count("2") == 1, "the key floods the Lago Verde (group 2), once: %s" % t.last("flip"))
use_at("chiusa2", "PUZZLE_ITEM4")
check(t.last("flip").count("2") <= 1, "the great sluice cannot be used twice")
# ---- the song: wrong order first, then right
cdv = t.captured["cdv"]
alt = {1: (2, 27), 2: (8, 27), 3: (2, 23), 4: (8, 23), 5: (5, 22)}


def blow(n):
    x, z = alt[n]
    t.at(((x + 0.5) * 1024, -512, (z + 0.5) * 1024), 2)
    t.H.press()


for n in (3, 1, 2):
    blow(n)
check("pip_c0" in t.last("enable") and "porta_canto" not in t.last("enable"), "a wrong note wakes the bats and resets the song")
for n in (3, 1, 4, 2):
    blow(n)
check("porta_canto" not in t.last("enable"), "four notes are not enough")
blow(5)
check("porta_canto" in t.last("enable"), "the five shells in the order of the scratches open the passage")
blow(3)
check(t.last("enable").count("porta_canto") == 1, "the song is solved once")
# ---- the spirit
t.at((11.5 * 1024, -512, 25.5 * 1024), 5)
check("maga" not in t.last("enable"), "the spirit sleeps until the Astro is taken")
t.H.give(t.item("PUZZLE_ITEM7")); t.H.tick(3)
check("maga" in t.last("enable"), "taking the Astro di Castore wakes the spirit")
t.H.tick(200)
check("porta_uscita" not in t.last("enable"), "the way out stays shut while the spirit lives")
zone("uscita")
check(not t.last("end"), "no level end before the spirit is gone")
t.at((16.5 * 1024, 1100, 25.5 * 1024), 250)
check("porta_uscita" in t.last("enable"), "8 s in the pool end the spirit and open the way out")
zone("masso_g")
check(any(v.startswith("masso_g[1]=-800") for v in t.last("itemflags")), "the boulder rolls south along the gallery")
zone("uscita")
check(len(t.last("end")) == 1, "the level ends in the daylight: %s" % t.last("end"))
# the sea current
t.at((60 * 1024, 0, 95 * 1024), 2)
check(any("corrente" in s for s in t.last("say")), "the current turns Lara back far from the shore")
print("ALL OK" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
