"""Reachability audit of Marinello on the built world: walking (steps up to 1 click, climbs up to 4, slopes under
3 clicks), the lake dry or full, doors shut or open. Usage: python3 audit_marinello.py"""
import sys
from collections import deque

import numpy as np

import content_marinello as C
import episode as E

ctx = E.build_terrain_level("Marinello", C)
w = ctx.world
nx, nz = w.nx, w.nz
H = w.floor.astype(float).mean(axis=2)
slope = w.floor.max(axis=2) - w.floor.min(axis=2)
bed = -w.depth * 512.0
DOORS = {"rais": (61, 40), "reti": (65, 46), "guardiano": (66, 58), "sigillo": (61, 55), "cancello": (28, 45)}
ok = True


def check(c, what):
    global ok
    print(("OK   " if c else "FAIL ") + what)
    ok = ok and c


def reach(start, dry, open_doors, climb=1792):     # 7 clicks: the most Lara grabs with a jump
    h = np.where(w.lagoon & dry, bed, H)
    blocked = {v for k, v in DOORS.items() if k not in open_doors}
    blocked.add((28, 46))                                  # the palisade beside the gate
    seen = {start}
    q = deque([start])
    while q:
        x, z = q.popleft()
        for a, b in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
            if not (1 <= a < nx - 1 and 1 <= b < nz - 1) or (a, b) in seen or (a, b) in blocked:
                continue
            sea = w.water[a, b] and not (w.lagoon[a, b] and dry)
            here_sea = w.water[x, z] and not (w.lagoon[x, z] and dry)
            if sea:
                if a > 91 or b > 86 or (a < 34 and b > 72):
                    continue                               # the current
                good = True
            elif here_sea:
                good = h[a, b] <= 256                      # out of the water onto a low bank
            else:
                good = h[a, b] - h[x, z] <= climb and slope[a, b] < 768
            if good:
                seen.add((a, b))
                q.append((a, b))
    return seen


start = (78, 49)
r0 = reach(start, dry=False, open_doors=set())
for name, cell in (("kick spot rais", (60, 40)), ("kick spot reti", (65, 45)), ("kick spot guardiano", (65, 58)),
                   ("sluice", (58, 46)), ("seal chamber door", (60, 55)), ("gate of the pass", (29, 45)), ("tower ladder foot", (71, 41))):
    check(cell in r0, "%s reachable from the jetty" % name)
check((64, 40) not in r0 and (65, 50) not in r0 and (69, 58) not in r0, "houses shut until their doors are kicked")
check((63, 55) not in r0, "seal chamber shut")
check(not any(x < 27 and 36 <= z <= 58 and not w.water[x, z] and H[x, z] < 3 * 512 for x, z in r0), "west clearing sealed (gate, rocks, current)")
check(max(H[x, z] for x, z in r0 if not w.water[x, z]) < 4.6 * 512, "no wall top or cliff terrace reachable: max %.1f m" % (max(H[x, z] for x, z in r0 if not w.water[x, z]) / 512))
r1 = reach(start, dry=False, open_doors={"rais", "reti", "guardiano"})
walk = reach(start, dry=True, open_doors=set(DOORS), climb=256)
for name, cell in (("sluice", (58, 46)), ("lever 1", (39, 45)), ("lever 2", (49, 45)), ("Sigillo", (63, 55)), ("gate", (29, 45)), ("end", (20, 46))):
    check(cell in walk, "%s reached on foot, no climbing" % name)
for name, cell in (("shotgun table", (64, 40)), ("crate", (66, 49)), ("slab", (64, 51)), ("drawers", (69, 59))):
    check(cell in r1, "%s reachable once the door is kicked" % name)
check((69, 52) not in r1, "loft not reachable without the raising block (9 clicks)")
r2 = reach(start, dry=True, open_doors={"rais", "reti", "guardiano"})
for cell in C.LEVERS:
    check((cell[0], cell[1] - 1) in r2, "lever at %s reachable on the dry bed" % (cell,))
far = max(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a in C.LEVERS for b in C.LEVERS)
check(far <= 12, "levers %d sectors apart: about %d s at a run (20 s allowed)" % (far, far * 1024 // 1500 + 2))
r3 = reach(start, dry=True, open_doors={"rais", "reti", "guardiano", "sigillo", "cancello"})
check((63, 55) in r3 and (20, 46) in r3, "Sigillo and level end reachable at the end")
# distances along the route (sectors)
route = [(78, 49), (60, 40), (65, 45), (58, 46), (44, 45), (60, 55), (29, 45), (20, 46)]
total = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(route, route[1:]))
check(total < 190, "main route %d sectors (%d m): about %d min of walking in all" % (total, total * 2, total * 1024 // 1500 // 60 + 1))
print("ALL OK" if ok else "SOMETHING FAILED")
sys.exit(0 if ok else 1)
