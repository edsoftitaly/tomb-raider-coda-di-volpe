"""Where the engine lets each enemy walk: the pathfinding zones as Tomb Editor builds them (Pathfinding.cs,
PathfindingDecompiled.cs) and TombEngine uses them (lot.cpp, box.cpp), sector by sector.

  box height = average of the four floor corners; a sector with a 3 click gradient is a slope (no land enemy);
  NotWalkable sectors and walls are out; a floor portal is followed down to the floor below; two neighbouring
  sectors are in the same zone when their heights differ by 1 click at most (LotType Basic, Skeleton, Blockable) or
  by 1 sector at most (LotType Human and its variants). A violent creature attacks only while Lara's box is in its
  zone. Doors are taken as open.

  enemy_zones.py <level.prj2> [flip suffix ...]      -> one line per enemy: zone size, rooms, what stops it"""
import collections
import pickle
import sys

import prj2_mesh as M
import prj2_patch as P
from prj2_check import Reader

HUMAN = ("Human", "HumanPlusJump", "HumanPlusJumpAndMonkey", "Spider", "Ape", "SnowmobileGun")
ALT = ("_PIENO", "_ASCIUTTO", "_BUIO", "_ACQUA2", "_ALT")


class Zones:
    def __init__(self, prj, flip=()):
        rooms, _ = M.read_rooms(prj)
        names = {r["name"] for r in rooms}
        self.rooms = {}
        for r in rooms:
            n = r["name"]
            suf = next((a for a in ALT if n.endswith(a)), "")
            if suf:
                if suf in flip:
                    self.rooms[n[:-len(suf)]] = r
            elif not any((n + a) in names and a in flip for a in ALT):
                self.rooms[n] = r
        _, topc = P.load(prj)
        idx, raw = {}, []
        self.nopath = set()          # rooms excluded from pathfinding: no boxes, a wall to every enemy
        for c, p in P.chunks(dict(topc)[b"TeRooms"])[0]:
            r0 = Reader(p)
            r0.leb(), r0.leb()
            dd = dict(P.chunks(p[r0.s.tell():])[0])
            nm = dd.get(b"TeName", b"").decode("utf-8", "replace")
            if b"TeI" in dd:
                idx[Reader(dd[b"TeI"]).leb()] = nm
            if dd.get(b"TeNoPath", b"\x00") != b"\x00":
                self.nopath.add(nm)
            for oc, op in P.chunks(dd.get(b"TeObjects", b"\x00"))[0]:
                if oc == b"TePor2":
                    rr = Reader(op)
                    rr.leb()
                    a = [rr.leb() for _ in range(4)]
                    adj = rr.leb()
                    raw.append((nm, a, adj, op[rr.s.tell()]))

        def base(n):
            suf = next((a for a in ALT if n.endswith(a)), "")
            return n[:-len(suf)] if suf else n
        self.wallp, self.floorp = {}, {}          # (room, lx, lz) -> adjoining room (base name)
        for nm, a, adj, d in raw:
            if adj not in idx or base(nm) not in self.rooms or self.rooms[base(nm)]["name"] != nm:
                continue
            for x in range(a[0], a[2] + 1):
                for z in range(a[1], a[3] + 1):
                    if d == 0:
                        self.floorp[(base(nm), x, z)] = base(idx[adj])
                    elif d >= 2:
                        self.wallp[(base(nm), x, z)] = base(idx[adj])
        self.wet = lambda n: (n.startswith("W_") or "ACQUA" in n)

    def sector(self, room, wx, wz):
        """the floor an enemy stands on over world column (wx, wz) seen from `room`: (room, lx, lz, sector) or None"""
        for _ in range(8):
            r = self.rooms.get(room)
            if r is None or r["name"] in self.nopath:
                return None
            px, py, pz = r["pos"]
            lx, lz = wx - int(px), wz - int(pz)
            s = r["sectors"].get((lx, lz))
            if s is None:
                return None
            if (room, lx, lz) in self.wallp and (lx in (0, r["nx"] - 1) or lz in (0, r["nz"] - 1)):
                room = self.wallp[(room, lx, lz)]
                continue
            if s["wall"] or lx in (0, r["nx"] - 1) or lz in (0, r["nz"] - 1):
                return None
            if (room, lx, lz) in self.floorp:
                room = self.floorp[(room, lx, lz)]
                continue
            return (room, lx, lz, s)
        return None

    def info(self, node):
        room, lx, lz, s = node
        py = self.rooms[room]["pos"][1]
        c = [v + py for v in s["floor"]]
        g = [abs(c[i] - c[(i + 1) % 4]) >= 768 for i in range(4)]
        slope = sum(g) >= 2
        return sum(c) / 4.0, slope or bool(s.get("flags", 0) & 128) or self.wet(self.rooms[room]["name"])

    def zone(self, room, wx, wz, step):
        st = self.sector(room, wx, wz)
        if st is None:
            return None, None
        key = lambda n: n[:3]
        seen, todo, walls = {key(st): st}, [st], collections.Counter()
        while todo:
            n = todo.pop()
            h, _ = self.info(n)
            r = self.rooms[n[0]]
            X, Z = n[1] + int(r["pos"][0]), n[2] + int(r["pos"][2])
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                m = self.sector(n[0], X + dx, Z + dz)
                if m is None or key(m) in seen:
                    continue
                h2, bad = self.info(m)
                if bad:
                    walls[("slope, water or not walkable", m[0], X + dx, Z + dz)] += 1
                    continue
                if abs(h2 - h) > step:
                    if abs(h2 - h) <= 1024:
                        walls[("step of %.1f clicks" % (abs(h2 - h) / 256.0), m[0], X + dx, Z + dz)] += 1
                    continue
                seen[key(m)] = m
                todo.append(m)
        return seen, walls


if __name__ == "__main__":
    import nov26_lib as L
    pass
    import movs
    LOT = pickle.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "enemy_lot.pkl"), "rb"))
    prj, flip = sys.argv[1], set(sys.argv[2:])
    zs = Zones(prj, flip)
    out, _ = movs.movs(prj)
    print("rooms excluded from pathfinding:", sorted(zs.nopath) or "none")
    for t, nm, room, x, y, z, ocb, _ in sorted(out, key=lambda o: o[1]):
        if t not in LOT or not LOT[t][2]:
            continue
        name, lot, _ = LOT[t]
        if lot not in HUMAN and lot not in ("Basic", "Skeleton", "Blockable") or "FISH" in name or "BOSS" in name:
            continue
        base = next((room[:-len(a)] for a in ALT if room.endswith(a)), room)
        seen, walls = zs.zone(base, int(x), int(z), 1024 if lot in HUMAN else 256)
        if seen is None:
            print("%-22s %-20s %-6s %s (%d,%d) NOT ON A FLOOR OF THIS STATE" % (nm, name[3:], lot, room, x, z))
            continue
        rooms = collections.Counter(k[0] for k in seen)
        print("%-22s %-20s %-6s (%d,%d) y%-6d zone %4d: %s" % (nm, name[3:], lot, x, z, y, len(seen), ", ".join("%s %d" % kv for kv in rooms.most_common(7))))
        if len(seen) < 300:
            for k in sorted(walls)[:6]:
                print("        stopped by %s into %s (%d,%d)" % k)
