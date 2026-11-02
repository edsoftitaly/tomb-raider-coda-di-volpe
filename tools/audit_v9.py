"""Reachability audit of a v9 level on the painted terrain (no engine): walking steps up at most 1.5
clicks, drops any height, swims in water and climbs out onto ground at most 1 click above the surface;
`climbs` lists sectors from which a climbable wall leads up to a given sector.

Checks that the north band cannot reach the middle or the south with the gates shut, that the middle
cannot reach the south with gate 2 shut, and that the start, devices, items, pickups, secrets and the
exit are all reachable once the gates are open.
Usage: python3 audit_v9.py Lungomare [...]
"""
import importlib
import sys
from collections import deque

import numpy as np

import episode as E
import livello as L
import world as W

STEP = 768           # climb-up onto ledges up to 3 clicks (Action); steps under 1.5 clicks are walked
OUT_OF_WATER = 256


def load(key):
    mod = importlib.import_module("content_" + key.lower())
    w = W.World(frame=E.LEVELS[key]["frame"])
    w.build_terrain()
    w.build_materials()
    mod.prepare(w)
    return mod, w


def reach(w, start, shut, climbs):
    h = w.floor.mean(axis=2)
    seen = {start}
    q = deque([start])
    while q:
        x, z = q.popleft()
        nb = [(x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)] + climbs.get((x, z), [])
        for nx, nz in nb:
            if not (1 <= nx < w.nx - 1 and 1 <= nz < w.nz - 1) or (nx, nz) in seen or (nx, nz) in shut:
                continue
            a, b = h[x, z], h[nx, nz]
            if (nx, nz) in climbs.get((x, z), []):
                ok = True
            elif w.water[nx, nz]:
                ok = w.water[x, z] or a >= 0              # into the water from anywhere
            elif w.water[x, z]:
                ok = b <= OUT_OF_WATER
            else:
                ok = b - a <= STEP
            if ok:
                seen.add((nx, nz))
                q.append((nx, nz))
    return seen


def run(key):
    mod, w = load(key)
    s = mod.SPEC
    g1, g2 = s["gate1"], s["gate2"]
    gates1 = {(g1, z) for z in L.WALL1}
    gates2 = {(g2, z) for z in L.WALL2}
    climbs = s.get("climbs", {})
    ok = True

    def check(c, what):
        nonlocal ok
        print(("OK   " if c else "FAIL ") + key + ": " + what)
        ok = ok and c

    st = tuple(s["start"])
    r0 = reach(w, st, gates1 | gates2, climbs)
    check(not any(z <= 40 for _, z in r0), "north band sealed while gate 1 is shut")
    check((g1, L.GZ1) in r0, "gate 1 reachable from the start")
    for _, x, z, _ in s["seq"]:
        near = any((x + dx, z + dz) in r0 for dx in (-1, 0, 1) for dz in (-1, 0, 1))
        check(near, "sequence landmark at %s reachable" % ((x, z),))
    r1 = reach(w, st, gates2, climbs)
    check(not any(z <= 20 for _, z in r1), "south band sealed while gate 2 is shut")
    check((g2, L.GZ2) in r1, "gate 2 and its device reachable")
    for p in s.get("item_cells", []):
        check(tuple(p) in r1, "item at %s reachable" % (tuple(p),))
    r2 = reach(w, st, set(), climbs)
    check(tuple(s["exit"]) in r2, "exit reachable")
    for idx, (x, z, _, _) in s.get("secrets", {}).items():
        check((x, z) in r2, "secret %d reachable" % idx)
    for t, x, z in s.get("pickups", []):
        near = any((x + dx, z + dz) in r2 for dx in range(-3, 4) for dz in range(-3, 4))
        check(near, "pickup near %s reachable" % ((x, z),))
    # nothing climbs onto the band walls or the ring from the playable area
    h = w.floor.mean(axis=2)
    top = max(h[x, z] for x, z in r2)
    check(top < L.Z.u(L.G_M + L.WALL_M) - 600, "no reachable sector near wall height (max %.1f m)" % (top / 512.0))
    return ok


if __name__ == "__main__":
    good = all([run(k) for k in sys.argv[1:]])
    raise SystemExit(0 if good else 1)
