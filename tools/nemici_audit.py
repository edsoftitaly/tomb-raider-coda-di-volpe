"""Audit of the enemies of a level: where each one stands, what wakes it (the zone, door or other event in the level
script that calls CDV.Enable on it), how far that is from Lara and whether she has a clear line to it at that moment
(= it would pop up in front of her), and whether it can walk to her from there with the engine's rules for its kind
(ground creatures: one click up, two clicks down; flyers and swimmers are not checked).

  nemici_audit.py <level.prj2> <level.lua>"""
import math
import re
import struct
import sys
from collections import deque

import appoggio
import prj2_patch as P
from prj2_check import Reader

GROUND = {152: "goon", 153: "goon", 154: "goon", 158: "worker", 172: "stick", 136: "dog", 115: "rat"}
OTHER = {118: "bat", 129: "shark", 268: "wraith", 269: "wraith", 289: "witch"}
STEP, DROP = 256 + 64, 512 + 64


def portals(path):
    """{room name: [(x0, z0, x1, z1, direction)]}"""
    out = {}
    for room, oc, op in P.raw_objects(path):
        if oc == b"TePor2":
            r = Reader(op)
            v = [r.leb() for _ in range(6)]
            d = op[r.s.tell()]
            out.setdefault(room, []).append((v[1], v[2], v[3], v[4], d))
    return out


def flags(path):
    _, top = P.load(path)
    out = {}
    for c, p in P.chunks(dict(top)[b"TeRooms"])[0]:
        r = Reader(p); r.leb(); r.leb()
        d = dict(P.chunks(p[r.s.tell():])[0])
        out[d[b"TeName"].decode()] = (d[b"TeNoPath"] != b"\x00", Reader(d[b"TeRoomType"]).leb(), b"TeAlternate" in d)
    return out


class World:
    def __init__(self, path, skip=lambda rn: False):
        self.rooms = appoggio.rooms_of(path)
        self.flags = flags(path)
        por = portals(path)
        self.cols = {}          # (X, Z) -> [(floor, ceil, room, walkable)]
        for rn, (nx, nz, pos, g) in self.rooms.items():
            if skip(rn):
                continue
            nopath, rtype, _ = self.flags[rn]
            fp = [(a, b, c, d) for a, b, c, d, k in por.get(rn, []) if k == 0]
            for (x, z), (props, fl, ce, _) in g.items():
                if x in (0, nx - 1) or z in (0, nz - 1) or props & 1 or fl is None or ce is None:
                    continue
                ce = [v + 65536 if v < 0 else v for v in ce]
                hole = any(a <= x <= c and b <= z <= d for a, b, c, d in fp)
                f = pos[1] + sum(fl) / 4.0
                self.cols.setdefault((int(pos[0]) + x, int(pos[2]) + z), []).append(
                    (f, pos[1] + min(ce), rn, not hole and not nopath and rtype == 0, max(fl) - min(fl)))

    def layer(self, x, y, z):
        """index of the surface under the point (the nearest floor at or below y + 300)"""
        best = None
        for i, (f, c, rn, walk, slope) in enumerate(self.cols.get((int(x // 1024), int(z // 1024)), [])):
            if f <= y + 300 and (best is None or f > self.cols[(int(x // 1024), int(z // 1024))][best][0]):
                best = i
        return best

    def reach(self, x, y, z, step=STEP, drop=DROP):
        start = (int(x // 1024), int(z // 1024))
        i = self.layer(x, y, z)
        if i is None:
            return set()
        seen = {(start, i)}
        q = deque(seen)
        while q:
            (cx, cz), i = q.popleft()
            f = self.cols[(cx, cz)][i][0]
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cx + dx, cz + dz)
                for j, (f2, c2, rn, walk, slope) in enumerate(self.cols.get(n, [])):
                    if not walk or (n, j) in seen or slope > 768:
                        continue
                    if -drop <= f2 - f <= step and c2 - max(f, f2) >= 700:
                        seen.add((n, j))
                        q.append((n, j))
        return seen

    def clear(self, a, b):
        """True when the straight line a -> b stays in the air of the rooms."""
        d = math.dist(a, b)
        n = max(2, int(d / 200))
        for k in range(1, n):
            p = [a[i] + (b[i] - a[i]) * k / n for i in range(3)]
            if not any(f - 10 <= p[1] <= c + 10 for f, c, rn, w, s in self.cols.get((int(p[0] // 1024), int(p[2] // 1024)), [])):
                return False
        return True


def wakers(lua, names):
    """{enemy: [(kind, text of the statement)]}"""
    s = open(lua, encoding="utf-8").read().replace("\r\n", "\n")
    blocks = re.split(r"\n(?=CDV\.|local |function |LevelFuncs)", s)
    out = {}
    for b in blocks:
        for n in re.findall(r'CDV\.Enable\("([^"]+)"\)', b):
            if n in names:
                out.setdefault(n, []).append(b)
        m = re.search(r'for _, \w+ in ipairs\(\{([^}]*)\}\) do CDV\.Enable', b)
        if m:
            for n in re.findall(r'"([^"]+)"', m.group(1)):
                if n in names:
                    out.setdefault(n, []).append(b)
    return out


def main():
    path, lua = sys.argv[1:3]
    w = World(path, skip=lambda rn: rn.endswith(("_PIENO", "_BUIO", "_ACQUA")) and False)
    obs = P.objects(path)
    wpos = {}
    for o in obs:
        rp = w.rooms[o[0]][2]
        if o[1] == "mov" and o[5]:
            wpos[o[5]] = (rp[0] * 1024 + o[3][0], rp[1] + o[3][1], rp[2] * 1024 + o[3][2], o[2], o[0])
    enemies = {n: v for n, v in wpos.items() if v[3] in GROUND or v[3] in OTHER}
    wk = wakers(lua, enemies)
    for n, (x, y, z, t, room) in sorted(enemies.items(), key=lambda kv: kv[1][4]):
        kind = GROUND.get(t) or OTHER.get(t)
        line = "%-16s %-7s %-16s" % (n, kind, room)
        blocks = wk.get(n)
        if not blocks:
            print(line, "NEVER ENABLED by name in the script (or enabled by a list)")
            continue
        for b in blocks:
            head = b.strip().split("\n")[0][:60]
            m = re.search(r"x = (-?\d+), y = (-?\d+), z = (-?\d+), r = (\d+)", b)
            trig = None
            if b.startswith("CDV.KickDoor"):
                d = re.match(r'CDV\.KickDoor\("([^"]+)"', b).group(1)
                if d in wpos:
                    trig = (wpos[d][0], wpos[d][1], wpos[d][2], 0, "door " + d)
            elif m and b.startswith(("CDV.Zone", "CDV.Use")):
                trig = (int(m.group(1)), -int(m.group(2)), int(m.group(3)), int(m.group(4)), "zone r %d" % int(m.group(4)))
            if trig is None:
                print(line, "woken by:", head)
                continue
            lx, ly, lz, r, what = trig
            dist = math.hypot(x - lx, z - lz)
            near = max(0.0, dist - r)
            # Lara anywhere on the edge of the zone nearest to the enemy: sample the centre and the near edge
            pts = [(lx, ly + 700, lz)]
            if r and dist > 1:
                pts.append((lx + (x - lx) / dist * min(r, dist - 600), ly + 700, lz + (z - lz) / dist * min(r, dist - 600)))
            seen = any(w.clear(p, (x, y + 700, z)) for p in pts)
            msg = "%s: %.1f sectors from her (%.1f from the zone edge), dy %+d, %s" % (
                what, dist / 1024, near / 1024, round((y - ly) / 256), "IN SIGHT" if seen else "hidden")
            if t in GROUND:
                reach = w.reach(x, y, z)
                li = w.layer(lx, ly, lz)
                ok = li is not None and ((int(lx // 1024), int(lz // 1024)), li) in reach
                msg += ", walks to her: %s (%d sectors reachable)" % ("yes" if ok else "NO", len(reach))
            print(line, msg)


if __name__ == "__main__":
    main()
