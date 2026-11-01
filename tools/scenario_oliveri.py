"""Scripted check of the Oliveri v6 logic against the mock engine."""
import luatest

D = "../build/levels/Oliveri"


def run():
    names = luatest.load_names(D, "Oliveri")
    t = luatest.Harness(D + "/Oliveri.lua", names)
    ok = True

    def check(cond, what):
        nonlocal ok
        print(("OK   " if cond else "FAIL ") + what)
        ok = ok and cond

    t.H.kill("ladro_chiave")
    t.H.tick(2)
    check(t.H.count(t.item("KEY_ITEM1")) == 1, "box-room key dropped by ladro_chiave")
    x, y, z, _ = names["serratura_ripostiglio"]
    t.at((x, -y, z))
    t.use("KEY_ITEM1")
    check("131" in t.last("anim"), "Lara plays the use-key animation")
    t.H.tick(50)
    check("porta_ripostiglio" in t.last("enable"), "the key opens the box-room door")
    t.H.tick(45)
    check(t.H.count(t.item("KEY_ITEM1")) == 0, "key consumed")
    t.H.give(t.item("PUZZLE_ITEM9"))
    t.at((43520, -1280, 16896))
    t.use("PUZZLE_ITEM9")
    check("blocco_cancello" in t.last("enable"), "the crank opens the courtyard gate")
    t.H.tick(60)
    check("cancello_cortile" in t.last("swing"), "the gate leaf swings")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
