"""Scripted run of Tindari against the mock engine and a reachability audit of its terrain."""
import collections

import numpy as np

import content_tindari as C
import episode
import luatest
import world as W

KEY = "Tindari"
D = "../build/levels/" + KEY
t = luatest.Harness("%s/%s.lua" % (D, KEY), luatest.load_names(D, KEY))
ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


def zone(zid):
    z = [t.captured["zones"][i] for i in range(1, len(t.captured["zones"]) + 1) if t.captured["zones"][i].id == zid][0]
    t.at((z.x, z.y, z.z), 3)


def press_at(zid):
    zone(zid)
    t.H.press()


t.at((16.5 * 1024, -12288, 17.5 * 1024), 3)
check(not any(b in t.last("enable") for b in ("blocco_a", "blocco_b", "blocco_c", "porta_pozzo")), "nothing moves at the start")
press_at("argano1_hint")
check("blocco_a" in t.last("enable"), "winch 1 raises the first block")
press_at("argano1_hint")
check(t.last("enable").count("blocco_a") == 1, "a winch works once")
# the mosaic: a safe walk costs nothing, a wrong tile costs health once per tile
y = -12288
for z, xs in C.SAFE.items():
    for x in sorted(xs):
        t.at(((x + 0.5) * 1024, y, (z + 0.5) * 1024), 2)
check(t.H.hp() == 1000, "the path of Castore's caps is safe")
t.at((23.5 * 1024, y, 52.5 * 1024), 5)
check(t.H.hp() == 660, "a wrong tile hurts once, however long Lara stands on it (%d)" % t.H.hp())
t.at((23.5 * 1024, y - 600, 53.5 * 1024), 3)
check(t.H.hp() == 660, "a jump over the tiles does not hurt")
t.at((23.5 * 1024, y, 53.5 * 1024), 2)
check(t.H.hp() == 320, "the next wrong tile hurts again")
press_at("argano2_hint")
press_at("argano3_hint")
check("blocco_b" in t.last("enable") and "blocco_c" in t.last("enable"), "winches 2 and 3 raise their blocks")
# the crypt
zone("pozzo")
check(not t.last("end"), "no level end before the twins stand on their stars")
t.H.put("statua_castore", 64.5 * 1024, 0, 50.5 * 1024); t.H.tick(3)
check("porta_pozzo" not in t.last("enable"), "one twin is not enough")
t.H.put("statua_polluce", 68.5 * 1024, 0, 46.5 * 1024); t.H.tick(3)
check("porta_pozzo" in t.last("enable"), "both twins on their stars open the well")
zone("pozzo")
check(len(t.last("end")) == 1, "the level ends at the well")

# ---- reachability on the built terrain
w = W.World(frame=episode.LEVELS[KEY]["frame"]); w.build_terrain(); w.build_materials(); C.prepare(w)
H = w.floor.max(axis=2).astype(int)
info = w.tindari


def reach(blocks, door=False, climb=1792):
    h = H.copy()
    for b in blocks:
        x, z = C.BLOCKS[b]
        h[x, z] += 1024
    seen = {(16, 17)}
    q = collections.deque(seen)
    while q:
        x, z = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = x + dx, z + dz
            if not (1 <= a < w.nx - 1 and 1 <= b < w.nz - 1) or (a, b) in seen or info["drop"][a, b]:
                continue
            if (a, b) == (26, 43) and not door:
                continue
            if h[a, b] - h[x, z] <= climb:
                seen.add((a, b)); q.append((a, b))
    return seen


PU, TU = int(C.P * 512), int(C.T * 512)
r0 = reach("")
check(not any(H[c] > PU for c in r0), "without the machine nothing above the plateau is reachable (max %.1f m)" % (max(H[c] for c in r0) / 512))
check((54, 26) in r0 and (26, 42) in r0 and (40, 50) in r0, "orchestra, house door and basilica reachable from the start")
check((26, 46) not in r0, "the Roman house is shut until its door is kicked")
check((26, 57) in reach("", door=True), "winch 2 reachable through the house")
ra = reach("a")
check((54, 30) in ra and (54, 31) not in ra, "block A: the stage, not the second tier")
rb = reach("ab")
check((54, 31) in rb and (54, 32) not in rb, "blocks A+B: the second tier, not the top")
rc = reach("abc")
check((61, 32) in rc and C.CPIT[1] in rc and (70, 60) in rc, "all three blocks: the terrace, the crypt stairs, the belvedere")
check(max(H[c] for c in rc) <= TU, "nothing above the terrace is reachable")
print("ALL OK" if ok else "SOME CHECKS FAILED")
