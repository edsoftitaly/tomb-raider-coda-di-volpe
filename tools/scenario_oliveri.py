"""Scripted playthrough of the Oliveri level logic against the mock engine."""
import luatest
import content_oliveri as C

D = "../build/levels/Oliveri"


def P(wx, wz, h):
    return ((wx + 0.5) * 1024, -h, (wz + 0.5) * 1024)


def run():
    names = luatest.load_names(D, "Oliveri")
    t = luatest.Harness(D + "/Oliveri.lua", names)
    ok = True

    def check(cond, what):
        nonlocal ok
        print(("OK   " if cond else "FAIL ") + what)
        ok = ok and cond

    F1 = C.G0 + C.H0
    F2 = F1 + C.H1
    t.at(P(*C.F2_HOLE, F1))
    check("ladro_primo" in t.last("enable"), "thug on first floor wakes up")
    t.at(P(*C.F1_HOLE, C.G0))
    check("ladro_chiave" in t.last("enable") and "ladro_terra" in t.last("enable"), "ground floor thugs wake up")
    check(t.H.count(t.item("PUZZLE_ITEM2")) == 0, "no key before the kill")
    t.H.kill("ladro_chiave")
    t.H.tick(2)
    check(t.H.count(t.item("PUZZLE_ITEM2")) == 1, "key dropped by ladro_chiave")
    t.at(P(*C.ROOF_HATCH, F2))
    t.use("PUZZLE_ITEM2")
    check("botola_tetto" in t.last("enable"), "roof trapdoor opens with the key")
    check(t.H.count(t.item("PUZZLE_ITEM2")) == 0, "key consumed")
    # Saia levers: wrong combination first.
    t.H.tick(1)
    t.H.pull("leva_castore")
    t.H.pull("leva_polluce")
    t.H.tick(3)
    check("cancello_saia" not in t.last("enable"), "gate stays closed with Polluce lit")
    t.H.pull("leva_tindaro")
    t.H.tick(3)
    check("cancello_saia" not in t.last("enable"), "gate stays closed with all three lit")
    t.H.pull("leva_polluce")
    t.H.tick(3)
    check("cancello_saia" in t.last("enable"), "gate opens: Castore + Tindaro, Polluce off")
    # Castle
    t.at(P(41, 36, C.YARD_H))
    check("capo_ladri" in t.last("enable"), "boss in the courtyard")
    # E3 requires the diary.
    roof = 24768
    t.at(P(*C.E3_SPOT, roof))
    t.use("PUZZLE_ITEM1")
    check(not t.last("end"), "no level end without the diary")
    t.H.give(t.item("PUZZLE_ITEM1"))
    t.use("PUZZLE_ITEM1")
    t.H.tick(250)
    check(t.last("end") == ["2:1"], "level ends towards Lungomare (2:1)")
    print("secrets so far:", t.last("secret"))
    return ok


if __name__ == "__main__":
    run()
