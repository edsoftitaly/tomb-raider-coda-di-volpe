"""Scripted check of a v9 level (livello.py template) against the mock engine.

Usage: python3 scenario_v9.py Lungomare [Marinello ...]
Checks: the order puzzle (wrong order does nothing, right order opens gate 1), the item(s) on the device
open gate 2 (and not before), the exit does nothing while the leader lives and ends the level after.
"""
import importlib
import sys

import kit as K
import livello as L
import luatest
import zona as Z

D = "../build/levels/"


def run(key):
    mod = importlib.import_module("content_" + key.lower())
    spec = mod.SPEC
    names = luatest.load_names(D + key, key)
    t = luatest.Harness("%s%s/%s.lua" % (D, key, key), names)
    ok = True

    def check(cond, what):
        nonlocal ok
        print(("OK   " if cond else "FAIL ") + key + ": " + what)
        ok = ok and cond

    def ground(x, z):
        # the y the generator used (names hold placed objects; the props of the sequence are on the ground)
        return -names["lara_start"][1]

    def at_cell(x, z, y=None):
        t.at(((x + 0.5) * 1024, y if y is not None else ground(x, z), (z + 0.5) * 1024), 3)
        t.at((1024 * 30.5, 99999, 1024 * 30.5), 2)      # step away (no point is active)

    pts = [(x, z) for _, x, z, _ in spec["seq"]]
    G = -Z.u(L.G_M)
    # wrong order: 2nd, 1st, 3rd
    for x, z in (pts[1], pts[0], pts[2]):
        t.at(((x + 0.5) * 1024, G, (z + 0.5) * 1024), 3)
        t.at((1024 * 30.5, 99999, 1024 * 30.5), 2)
    check("cancello1" not in t.last("enable"), "wrong order keeps gate 1 shut")
    for x, z in pts:
        t.at(((x + 0.5) * 1024, G, (z + 0.5) * 1024), 3)
        t.at((1024 * 30.5, 99999, 1024 * 30.5), 2)
    check("cancello1" in t.last("enable"), "right order opens gate 1")
    check("cancello1_anta" in t.last("swing"), "gate 1 leaf swings")
    # the item(s) on the device
    items = spec["item"] if isinstance(spec["item"], tuple) else (spec["item"],)
    uses = [t.captured["uses"][i] for i in range(1, len(t.captured["uses"]) + 1)]
    u0 = [u for u in uses if u.id in ("chiave2", "astro_a")][0]
    dev = (u0.x, u0.y, u0.z)
    t.at(dev, 2)
    check("cancello2" not in t.last("enable"), "gate 2 shut before the item")
    for i, it in enumerate(items):
        t.H.give(t.item("PUZZLE_ITEM%d" % it))
        t.at(dev, 2)
        t.use("PUZZLE_ITEM%d" % it)
        t.H.tick(5)
        if i < len(items) - 1:
            check("cancello2" not in t.last("enable"), "one item of two is not enough")
    check("cancello2" in t.last("enable"), "the item(s) open gate 2")
    # the exit
    ex, ez = spec["exit"]
    n_end = len(t.last("end"))
    for name in names:
        if name.startswith(("nord", "centro", "sud")):
            t.H.kill(name)
    t.H.tick(3)
    end_y = None
    for zone in [t.captured["zones"][i] for i in range(1, len(t.captured["zones"]) + 1)]:
        if zone.id == "fine":
            end_y = zone.y
    t.at(((ex + 0.5) * 1024, end_y, (ez + 0.5) * 1024), 3)
    check(len(t.last("end")) == n_end, "no level end while the leader lives")
    t.at((1024 * 30.5, 99999, 1024 * 30.5), 2)
    t.H.kill("capo")
    t.H.tick(3)
    t.at(((ex + 0.5) * 1024, end_y, (ez + 0.5) * 1024), 3)
    t.H.tick(800)          # the finale of the last level ends after its epilogue
    check(len(t.last("end")) > n_end, "level ends at the exit after the leader: %s" % t.last("end")[-1:])
    # every zone and use runs without Lua errors
    luatest.smoke(D + key, key)
    print("OK   " + key + ": smoke test (every zone and use) without Lua errors")
    return ok


if __name__ == "__main__":
    good = all([run(k) for k in sys.argv[1:]])
    raise SystemExit(0 if good else 1)
