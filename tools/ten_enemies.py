"""Each ground enemy against the pathfinding data really compiled into the .ten: the zone of the box it stands on
and how much ground that zone holds.   ten_enemies.py <level.prj2> <level.ten> [door names to look at...]"""
import collections
import pickle
import sys

import movs
import ten_boxes

LOT = pickle.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "enemy_lot.pkl"), "rb"))
HUMAN = ("Human", "HumanPlusJump", "HumanPlusJumpAndMonkey", "Spider", "Ape", "SnowmobileGun")
prj, ten = sys.argv[1:3]
r = ten_boxes.load(ten)
B = r["boxes"]


def box_at(x, y, z):
    best = None
    for i, b in enumerate(B):
        if b[2] <= x < b[3] and b[0] <= z < b[1]:
            d = abs(-b[4] - y)
            if best is None or d < best[0]:
                best = (d, i)
    return best[1] if best and best[0] < 600 else None


def area(zone, zid):
    return sum((B[i][1] - B[i][0]) * (B[i][3] - B[i][2]) for i in range(len(B)) if zone[i] == zid)


out, _ = movs.movs(prj)
print("boxes", len(B), " blockable (blocked until a door opens them):", sum(1 for b in B if b[6] & 0x8000))
for t, nm, room, x, y, z, ocb, _ in sorted(out, key=lambda o: o[1]):
    if t not in LOT or not LOT[t][2] or LOT[t][1] not in HUMAN + ("Basic", "Skeleton", "Blockable") or "FISH" in LOT[t][0]:
        continue
    zt = "Human" if LOT[t][1] in HUMAN else "Basic"
    i = box_at(int(x), y, int(z))
    if i is None:
        print("%-20s %-20s (%d,%d) y%d  NO BOX under it" % (nm, LOT[t][0][3:], x, z, y))
        continue
    for flip in (0, 1):
        zone = r["zones"][flip][zt]
        a = area(zone, zone[i])
        if flip == 0 or a != a0:
            print("%-20s %-20s (%d,%d) y%-6d box %4d %s zone of %5d sectors%s%s" % (nm, LOT[t][0][3:], x, z, y, i, zt, a, " (flipped)" if flip else "", "   <-- SHUT IN" if a < 60 else ""))
        a0 = a
