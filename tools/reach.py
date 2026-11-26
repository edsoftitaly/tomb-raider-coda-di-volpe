"""Where Lara can get to, sector by sector (an over-generous model of her moves: what it calls unreachable is
unreachable, what it calls reachable has to be looked at).

World = columns (X, Z) in sectors. Each column holds the interior sectors of the rooms over it; a room whose
ceiling touches the floor of the room above is joined to it (water under air, a shaft). A node is (X, Z, floor).
Moves from a node: walk (up 1 click, down any), vault (up to 4), jump and grab (up to 7), jumps over one, two and
three sectors, swimming, climbable walls, falling. Closed doors and solid statics stop her.

  World(prj, flip=set of room-name suffixes in force, closed=set of object names that block their sector)
"""
import collections
import math

import lv
import prj2_mesh as M
import prj2_patch as P

CL = 256
ALT = ("_PIENO", "_ASCIUTTO", "_BUIO", "_ACQUA2", "_ALT")
LARA_H = 762


class World:
    def __init__(self, prj, flip=(), closed=(), water=None, solid_extra=(), step_extra=()):
        self.prj = prj
        rooms, _ = M.read_rooms(prj)
        self.rooms = rooms
        names = {r.get("name", "") for r in rooms}
        use = []
        for r in rooms:
            n = r.get("name", "")
            base, suf = n, ""
            for a in ALT:
                if n.endswith(a):
                    base, suf = n[:-len(a)], a
            if suf:                                   # an alternate room: in force only when its suffix is flipped
                if suf in flip:
                    use.append(r)
            else:
                if not any((n + a) in names and a in flip for a in ALT):
                    use.append(r)
        self.use = use
        # which rooms are joined by a portal (no walking from a room into the one beside it through solid rock)
        from prj2_check import Reader
        _, topc = P.load(prj)
        idx, pors = {}, []
        for c, p in P.chunks(dict(topc)[b"TeRooms"])[0]:
            r0 = Reader(p)
            r0.leb(), r0.leb()
            dd = dict(P.chunks(p[r0.s.tell():])[0])
            nm = dd.get(b"TeName", b"").decode("utf-8", "replace")
            if b"TeI" in dd:
                idx[Reader(dd[b"TeI"]).leb()] = nm
            for oc, op in P.chunks(dd.get(b"TeObjects", b"\x00"))[0]:
                if oc == b"TePor2":
                    rr = Reader(op)
                    rr.leb()
                    [rr.leb() for _ in range(4)]
                    pors.append((nm, rr.leb()))
        def base(nm):
            for a_ in ALT:
                if nm.endswith(a_):
                    return nm[:-len(a_)]
            return nm
        self.base = base
        self.linked = set()
        for nm, adj in pors:
            if adj in idx:
                self.linked.add((base(nm), base(idx[adj])))
                self.linked.add((base(idx[adj]), base(nm)))
        self.cols = collections.defaultdict(list)     # (X, Z) -> [dict(floor, ceil, lo, hi, room, flags, water)]
        for r in use:
            px, py, pz = r["pos"]
            n = r.get("name", "")
            wet = (n.startswith("W_") or "ACQUA" in n) and not n.endswith("_ASCIUTTO")
            if water is not None:
                wet = water(n, wet)
            for (x, z), s in r["sectors"].items():
                if x in (0, r["nx"] - 1) or z in (0, r["nz"] - 1) or s["wall"]:
                    continue
                f = [v + py for v in s.get("floor", [0] * 4)]
                c = [v + py for v in s.get("ceil", [0] * 4)]
                self.cols[(int(px) + x, int(pz) + z)].append(
                    dict(lo=min(f), hi=max(f), ceil=min(c), cmax=max(c), room=n, flags=s.get("flags", 0), water=wet,
                         lx=x, lz=z))
        # join the spaces stacked on one column: the upper one has no floor of its own there
        self.nodes = {}                               # (X, Z, k) -> dict
        for key, lst in self.cols.items():
            lst.sort(key=lambda d: d["lo"])
            spaces = []
            for d in lst:
                if spaces and abs(spaces[-1]["ceil"] - d["lo"]) <= 2 and abs(spaces[-1]["cmax"] - d["hi"]) <= 2 and \
                        any((self.base(ra), self.base(d["room"])) in self.linked for ra in spaces[-1]["rooms"]):
                    sp = spaces[-1]
                    sp["surface"] = d["lo"] if sp["water"] and not d["water"] else sp.get("surface")
                    sp["ceil"], sp["cmax"] = d["ceil"], d["cmax"]
                    sp["rooms"].append(d["room"])
                    sp["parts"].append((d["room"], d["lo"], d["cmax"]))
                    sp["flags"] |= d["flags"]
                    if not d["water"] and not sp["water"]:
                        pass
                else:
                    sp = dict(d)
                    sp["rooms"] = [d["room"]]
                    sp["parts"] = [(d["room"], d["lo"], d["cmax"])]
                    sp["surface"] = d["ceil"] if d["water"] else None
                    spaces.append(sp)
            for k, sp in enumerate(spaces):
                self.nodes[(key[0], key[1], k)] = sp
        self.bycol = collections.defaultdict(list)
        for (X, Z, k), sp in self.nodes.items():
            self.bycol[(X, Z)].append((X, Z, k))
        # objects
        self.objs = []
        st = lv.level_statics(prj)
        roompos = {r.get("name", ""): r["pos"] for r in rooms}
        inuse = {r.get("name", "") for r in use}
        self.solid = []                               # world boxes of solid statics (x1, y1, z1, x2, y2, z2)
        for room, kind, t, pos, ry, name, ex in P.objects(prj):
            if room not in inuse:
                continue
            px, py, pz = roompos[room]
            w = (pos[0] + px * 1024, pos[1] + py, pos[2] + pz * 1024)
            self.objs.append(dict(room=room, kind=kind, type=t, pos=w, ry=ry, name=name, ex=ex))
            if kind == "sta" and t in st:
                cb = st[t][2]
                if any(abs(v) > 0.5 for v in cb):
                    sc = ex.get("scale", 1.0) or 1.0
                    a = math.radians(ry)
                    xs, zs = [], []
                    for cx in (cb[0], cb[3]):
                        for cz in (cb[2], cb[5]):
                            xs.append(w[0] + (cx * math.cos(a) + cz * math.sin(a)) * sc)
                            zs.append(w[2] + (-cx * math.sin(a) + cz * math.cos(a)) * sc)
                    y1, y2 = sorted((cb[1] * sc, cb[4] * sc))
                    self.solid.append((min(xs), w[1] + y1, min(zs), max(xs), w[1] + y2, max(zs), t))
        self.poles = collections.defaultdict(list)    # column -> [(foot y, top y)]
        pp = collections.defaultdict(list)
        for o in self.objs:
            if o["kind"] == "mov" and o["type"] == 365:
                pp[(int(o["pos"][0] // 1024), int(o["pos"][2] // 1024))].append(o["pos"][1])
        for kcol, ys in pp.items():
            self.poles[kcol].append((min(ys), max(ys) + 1024))
        self.sgrid = collections.defaultdict(list)    # column -> solids near it
        for sb in self.solid:
            for gx in range(int((sb[0] - 150) // 1024), int((sb[3] + 150) // 1024) + 1):
                for gz in range(int((sb[2] - 150) // 1024), int((sb[5] + 150) // 1024) + 1):
                    self.sgrid[(gx, gz)].append(sb)
        self.closed = set()
        for o in self.objs:
            if o["name"] in closed:
                self.closed.add((int(o["pos"][0] // 1024), int(o["pos"][2] // 1024), round(o["pos"][1])))
        self.extra_solid = set(solid_extra)
        self.steps = {}                               # (X, Z) -> extra height a pushable or raised block gives there
        for X, Z, h in step_extra:
            self.steps[(X, Z)] = h

    # ------------------------------------------------------------------------------------------------ helpers
    def node_at(self, x, y, z):
        """the node whose space holds the world point"""
        best = None
        for n in self.bycol.get((int(x // 1024), int(z // 1024)), []):
            sp = self.nodes[n]
            if sp["lo"] - 300 <= y <= sp["cmax"] + 1:
                if best is None or abs(sp["lo"] - y) < abs(self.nodes[best]["lo"] - y):
                    best = n
        return best

    def joined(self, sp, sq):
        for ra in sp["rooms"]:
            for rb in sq["rooms"]:
                if self.base(ra) == self.base(rb) or (self.base(ra), self.base(rb)) in self.linked:
                    return True
        return False

    def sill(self, sp, sq):
        """lowest height at which the two spaces really open onto each other (each room of a stack has its own span)"""
        best = None
        for ra, la, ca in sp["parts"]:
            for rb, lb, cb in sq["parts"]:
                if self.base(ra) == self.base(rb) or (self.base(ra), self.base(rb)) in self.linked:
                    v = max(la, lb)
                    if min(ca, cb) > v and (best is None or v < best):
                        best = v
        return best

    def near(self, sp, sq):
        if self.joined(sp, sq):
            return True
        ra = {self.base(x) for x in sp["rooms"]}
        rb = {self.base(x) for x in sq["rooms"]}
        la = {b for (a, b) in self.linked if a in ra}
        lb = {b for (a, b) in self.linked if a in rb}
        return bool(la & lb)

    def stand(self, n):
        sp = self.nodes[n]
        return sp["hi"] + self.steps.get((n[0], n[1]), 0)

    def steep(self, n):
        sp = self.nodes[n]
        return sp["hi"] - sp["lo"] >= 3 * CL

    def blocked_edge(self, a, b, y):
        """a solid static or a closed door between the centres of two neighbouring columns at height y..y+LARA_H"""
        ax, az = a[0] * 1024 + 512, a[1] * 1024 + 512
        bx, bz = b[0] * 1024 + 512, b[1] * 1024 + 512
        for (cx, cz, cy) in self.closed:
            if (cx, cz) in ((a[0], a[1]), (b[0], b[1])) and cy - 300 <= y <= cy + 1100:
                return True
        if (b[0], b[1]) in self.extra_solid or (a[0], a[1]) in self.extra_solid:
            return True
        near = self.sgrid.get((a[0], a[1]), []) + self.sgrid.get((b[0], b[1]), [])
        for (x1, y1, z1, x2, y2, z2, t) in near:
            if y2 <= y + 200 or y1 >= y + LARA_H:      # she steps over 200, passes under what is above her head
                continue
            # does the segment a->b meet the box grown by her radius?
            r = 100
            for i in range(1, 8):
                px = ax + (bx - ax) * i / 8.0
                pz = az + (bz - az) * i / 8.0
                if x1 - r < px < x2 + r and z1 - r < pz < z2 + r:
                    # a narrow thing in a wide sector can be walked round: only count it if it spans the passage
                    wide = (x2 - x1) if a[0] == b[0] else (z2 - z1)
                    if a[0] != b[0] and a[1] != b[1]:
                        wide = max(x2 - x1, z2 - z1)
                    if wide + 2 * r >= 824:
                        return True
        return False

    # ------------------------------------------------------------------------------------------------- moves
    def moves(self, n):
        X, Z, k = n
        sp = self.nodes[n]
        h = self.stand(n)
        out = []
        wet = sp["water"] and sp["surface"] is not None
        surf = sp["surface"] if wet else None
        deep = wet and surf - sp["lo"] > 3 * CL
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if not dx and not dz:
                    continue
                for m in self.bycol.get((X + dx, Z + dz), []):
                    sq = self.nodes[m]
                    if not self.joined(sp, sq):
                        continue
                    g = self.stand(m)
                    qwet = sq["water"] and sq["surface"] is not None
                    if dx and dz:                      # diagonal: both side columns must be open at this height
                        ok = True
                        for sx, sz in ((dx, 0), (0, dz)):
                            side = [self.nodes[q] for q in self.bycol.get((X + sx, Z + sz), [])]
                            if not any(s2["lo"] <= max(h, g) + CL and s2["cmax"] >= max(h, g) + LARA_H for s2 in side):
                                ok = False
                        if not ok:
                            continue
                    top = max(sp["cmax"], sq["cmax"])
                    if wet and qwet:                   # swimming from water to water: the two bodies must overlap
                        if min(surf, sq["surface"]) > max(sp["lo"], sq["lo"]):
                            out.append(m)
                        continue
                    y_from = surf - 0 if deep else h
                    if not (dx and dz):
                        sl = self.sill(sp, sq)
                        if sl is None:
                            continue
                        if sl > max(g, y_from) + 1:    # the opening is higher than both floors: she has to get up to it
                            if sl - y_from > (2 * CL if deep else 7.5 * CL):
                                continue
                    rise = g - y_from
                    if qwet and not wet:               # into water: she must be able to get over the brim
                        rise = min(rise, sq["surface"] - y_from) if sq["surface"] > g else rise
                        rise = min(rise, 0) if sq["lo"] <= h + CL else rise
                    limit = 2 * CL if deep else 7.5 * CL   # out of deep water: a low brim only; TEN's auto-jump takes ledges up to 7.5 clicks
                    if dx and dz:
                        limit = min(limit, CL)
                    if rise > limit:
                        continue
                    # headroom: where she arrives and over the edge
                    if sq["cmax"] - g < 3 * CL and not qwet:
                        continue
                    if rise > 0 and sp["cmax"] < g + 2 * CL and top < g + 2 * CL:
                        continue
                    if g + 2 * CL > sq["cmax"] + 1 and not qwet:
                        continue
                    if not (sq["lo"] < sp["cmax"] and sp["lo"] < sq["cmax"]) and rise <= 0:
                        continue                       # the two spaces do not meet
                    if self.blocked_edge((X, Z), (X + dx, Z + dz), max(y_from, g)):
                        continue
                    out.append(m)
        # climbable walls: flags on this sector let her go up (or down) the side: reach any node of the next column
        fl = sp["flags"]
        for bit, (dx, dz) in ((256, (0, 1)), (512, (0, -1)), (1024, (1, 0)), (2048, (-1, 0))):
            if fl & bit:
                for m in self.bycol.get((X + dx, Z + dz), []):
                    out.append(m)
                for m in self.bycol.get((X, Z), []):       # and the other landings of the same shaft
                    out.append(m)
        for (pc, ptop) in self.poles.get((X, Z), []):  # a pole: up it and off it, onto anything lower within three sectors
            if abs(pc - h) < 1500:
                for ddx in range(-3, 4):
                    for ddz in range(-3, 4):
                        for m in self.bycol.get((X + ddx, Z + ddz), []):
                            if self.stand(m) <= ptop + CL and self.nodes[m]["cmax"] >= max(self.stand(m), h) + 3 * CL:
                                out.append(m)
        if fl & 1:                                     # monkey bars: along the flagged sectors
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for m in self.bycol.get((X + dx, Z + dz), []):
                    out.append(m)
        # jumps over gaps (not from deep water)
        if not deep:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                for dist, up in ((2, 5 * CL), (3, 2 * CL), (4, -3 * CL)):
                    if (dx and dz) and dist > 2:
                        continue
                    ok = True
                    if dx and dz:                      # a diagonal jump: every corner it cuts must be open air
                        for i in range(1, dist + 1):
                            for cx, cz in ((X + dx * i, Z + dz * (i - 1)), (X + dx * (i - 1), Z + dz * i)):
                                side = [self.nodes[q] for q in self.bycol.get((cx, cz), [])]
                                if not any(s2["hi"] <= h + CL and s2["cmax"] >= h + 4 * CL for s2 in side):
                                    ok = False
                                if any((cx, cz) == (c[0], c[1]) and c[2] - 300 <= h <= c[2] + 1100 for c in self.closed):
                                    ok = False
                    for i in range(1, dist):
                        mids = [self.nodes[q] for q in self.bycol.get((X + dx * i, Z + dz * i), [])]
                        if not any(s2["hi"] <= h + CL and s2["cmax"] >= h + 4 * CL for s2 in mids):
                            ok = False
                        if self.blocked_edge((X + dx * (i - 1), Z + dz * (i - 1)), (X + dx * i, Z + dz * i), h + 300):
                            ok = False
                    if not ok:
                        break
                    for m in self.bycol.get((X + dx * dist, Z + dz * dist), []):
                        sq = self.nodes[m]
                        g = self.stand(m)
                        sl = self.sill(sp, sq)
                        if sl is None:                 # not the same space: only through a room that opens onto both
                            ok2 = False
                            for i in range(1, dist):
                                for q in self.bycol.get((X + dx * i, Z + dz * i), []):
                                    s3 = self.nodes[q]
                                    s1 = self.sill(sp, s3)
                                    if s1 is not None and s1 <= h + 2 * CL and self.sill(s3, sq) is not None:
                                        ok2 = True
                            if not ok2:
                                continue
                        elif sl > h + up + 2 * CL:
                            continue
                        if g - h <= up and sq["cmax"] - g >= 3 * CL and sq["cmax"] >= h + 3 * CL and sq["lo"] < sp["cmax"]:
                            if not self.blocked_edge((X + dx * (dist - 1), Z + dz * (dist - 1)), (X + dx * dist, Z + dz * dist), max(h, g)):
                                out.append(m)
        return out

    def reach(self, start, banned=()):
        seen = {start}
        todo = [start]
        banned = set(banned)
        while todo:
            n = todo.pop()
            for m in self.moves(n):
                if m not in seen and (m[0], m[1]) not in banned:
                    seen.add(m)
                    todo.append(m)
        return seen

    def find(self, name):
        for o in self.objs:
            if o["name"] == name:
                return o
        return None

    def where(self, name, dy=0):
        o = self.find(name)
        return self.node_at(o["pos"][0], o["pos"][1] + dy, o["pos"][2]) if o else None

    def named(self):
        return [o for o in self.objs if o["name"]]


def path(w, start, goal, banned=()):
    """shortest list of nodes from start to goal (BFS), or None"""
    prev = {start: None}
    q = collections.deque([start])
    banned = set(banned)
    while q:
        n = q.popleft()
        if n == goal:
            out = []
            while n is not None:
                out.append(n)
                n = prev[n]
            return out[::-1]
        for m in w.moves(n):
            if m not in prev and (m[0], m[1]) not in banned:
                prev[m] = n
                q.append(m)
    return None


def show_path(w, p, only_hops=True):
    """print the path, keeping only the steps that are not plain walking"""
    last = None
    for i, n in enumerate(p):
        h = w.stand(n)
        sp = w.nodes[n]
        if last is not None:
            dh = (h - w.stand(last)) / CL
            dist = max(abs(n[0] - last[0]), abs(n[1] - last[1]))
            wet = sp["water"] and sp["surface"] is not None
            lw = w.nodes[last]["water"] and w.nodes[last]["surface"] is not None
            plain = dist == 1 and -2 <= dh <= 1 and not wet and not lw
            if not only_hops or not plain:
                print("   %3d (%d,%d)->(%d,%d) %-16s dist %d  %+5.1f clicks  to y %d%s" % (
                    i, last[0], last[1], n[0], n[1], sp["rooms"][-1][:16], dist, dh, h, "  WATER" if wet else ""))
        last = n
