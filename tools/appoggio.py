"""Audit: statics that do not rest on the floor under them, and roof pieces that do not reach the walls they lean on.

For every static of a level: bottom of its mesh (lowest vertex, scaled) at the height it is placed, against the floor
of the sector under its origin (lowest and highest corner). Prints the ones floating or sunk by more than TOL.

  appoggio.py <level.prj2> <wad dir> [tol]"""
import os
import re
import struct
import sys

import prj2_patch as P
import render_wad
from prj2_check import Reader


def model_names():
    out = {}
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decor")
    for f in os.listdir(d):
        if f.endswith(".py"):
            for m in re.finditer(r'@(?:model|furniture)\((\d+),\s*"([^"]+)",\s*"([^"]*)"', open(os.path.join(d, f), encoding="utf-8").read()):
                out[int(m.group(1))] = (m.group(2), m.group(3))
    return out


def rooms_of(path):
    _, top = P.load(path)
    out = {}
    for c, p in P.chunks(dict(top)[b"TeRooms"])[0]:
        r = Reader(p)
        nx, nz = r.leb(), r.leb()
        d = dict(P.chunks(p[r.s.tell():])[0])
        g = {}
        for sc, sp in P.chunks(d[b"TeSecs"])[0]:
            idx = struct.unpack_from("<i", sp, 0)[0]
            subs = P.chunks(sp[4:])[0]
            sub = dict(subs)
            props = Reader(sub[b"\x00"]).leb() if b"\x00" in sub else 0
            fl = ce = None
            if b"\x07" in sub:
                rr = Reader(sub[b"\x07"]); rr.leb(); fl = [rr.leb() for _ in range(4)]
            if b"\x08" in sub:
                rr = Reader(sub[b"\x08"]); rr.leb(); ce = [rr.leb() for _ in range(4)]
            sg = lambda v: [x - 65536 if x > 32767 else x for x in v] if v else None
            g[(idx % nx, idx // nx)] = (props, sg(fl), sg(ce), [k for k, _ in subs])
        out[d[b"TeName"].decode()] = (nx, nz, struct.unpack("<3f", d[b"TePos2"]), g)
    return out


def wads_of(path, wad_dir):
    _, top = P.load(path)
    names = [m.decode("latin1").split("\\")[-1] for m in re.findall(rb"[\w\\/.$() -]+\.wad2", dict(top)[b"TeSettings"])]
    stat = {}
    for n in names:
        f = os.path.join(wad_dir, n)
        if not os.path.exists(f):
            continue
        try:
            _, st = render_wad.load(f)
        except Exception as e:
            print("  (cannot read %s: %s)" % (n, e))
            continue
        for sid, (V, polys) in st.items():
            if sid not in stat and V:
                ys = [v[1] for v in V]
                xs = [v[0] for v in V]
                zs = [v[2] for v in V]
                stat[sid] = (min(ys), max(ys), min(xs), max(xs), min(zs), max(zs), n)
    return stat


def main():
    path, wad_dir = sys.argv[1:3]
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 24
    names = model_names()
    rooms = rooms_of(path)
    stat = wads_of(path, wad_dir)
    rows = []
    for o in P.objects(path):
        if o[1] != "sta":
            continue
        room, _, sid, (x, y, z), rot, name, ex = o
        nx, nz, pos, g = rooms[room]
        sx, sz = int(x // 1024), int(z // 1024)
        sec = g.get((sx, sz))
        near = [g.get((int((x + ax) // 1024), int((z + az) // 1024))) for ax in (-40, 0, 40) for az in (-40, 0, 40)]
        bb = stat.get(sid)
        nm = names.get(sid, ("?", ""))[0]
        if bb is None or sec is None:
            rows.append((room, sid, nm, name, x, y, z, None, "no mesh" if bb is None else "outside the room"))
            continue
        props, fl, ce, subs = sec
        sc = ex["scale"]
        lo, hi = bb[0] * sc, bb[1] * sc
        if props & 1 or fl is None:
            rows.append((room, sid, nm, name, x, y, z, None, "in a wall sector" if props & 1 else "no floor"))
            continue
        bottom = y + lo
        fls = [n[1] for n in near if n and not (n[0] & 1) and n[1]]
        fmin, fmax = min(min(f) for f in fls), max(max(f) for f in fls)
        gap = bottom - fmax if bottom > fmax + tol else (bottom - fmin if bottom < fmin - tol else 0)
        rows.append((room, sid, nm, name, x, y, z, gap, "floor %d..%d, bottom %d, mesh y %d..%d" % (fmin, fmax, bottom, lo, hi)))
    return rows


if __name__ == "__main__":
    rows = main()
    import collections
    c = collections.Counter()
    for r in rows:
        if r[7] is None or abs(r[7]) > 0:
            c[(r[1], r[2])] += 1
    print("statics:", len(rows), "to look at:", sum(c.values()))
    for (sid, nm), n in sorted(c.items(), key=lambda kv: -kv[1]):
        print("  %4d %-28s %d" % (sid, nm, n))
