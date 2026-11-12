"""Oliveri, 12/11/2026 night: the blackout with the fuse and the roofs to jump, in place on Ed's file.

Blackout: every room of the house gets a dark twin (flipmap 1: no lamp, almost no ambient light); the level starts
flipped. Fuse (PUZZLE_ITEM12) in the cellar, fuse box (static 448) in the entrance hall; the fuse in the box flips
back. Roofs: two gaps cut in the row of flat roofs east of the house (x 34-35 and 40-41, z 25-30, down to 13
clicks), the drainpipe moved from the house front (25, 24) to the far end (44, 24).

usage: oliveri_blackout_tetti.py <Oliveri.prj2> <out.prj2>"""
import struct
import subprocess
import sys

import prj2
import prj2_patch as P
from prj2_check import Reader

src, dst = sys.argv[1], sys.argv[2]
head, top = P.load(src)
top = list(top)
d = dict(top)
rooms = d[b"TeRooms"]
next_id = [max(Reader(p).leb() for _, _, p in P.raw_objects(src)) + 1]
ROOF, LOW = 19 * 256, 13 * 256
GAPS = (34, 35, 40, 41)
PLAIN = (11, 512.0, 768.0)                      # texture index and u range of the blank side wall of the tall block


def oid():
    next_id[0] += 1
    return next_id[0] - 1


def spos(p):
    """(offset of the position, x, y, z, rot) of a static or moveable chunk payload."""
    r = Reader(p)
    r.leb()
    o = r.s.tell()
    return (o,) + struct.unpack("<4f", p[o:o + 16])


def stype(p):
    o = spos(p)[0]
    return struct.unpack("<I", p[o + 29:o + 33])[0]


def static_like(p, x=None, y=None, z=None, rot=None, type_id=None):
    """A copy of a TeStaTn3 payload with a new id, no Lua name and what is given changed."""
    o, px, py, pz, ry = spos(p)
    n = struct.unpack("<i", p[o + 47:o + 51])[0]
    body = prj2.leb(oid()) + struct.pack("<4f", px if x is None else x, py if y is None else y, pz if z is None else z,
                                         ry if rot is None else rot) + p[o + 16:o + 29]
    body += struct.pack("<I", stype(p) if type_id is None else type_id) + p[o + 33:o + 47] + struct.pack("<i", 0) + p[o + 51 + n:]
    return body


def moveable(type_id, pos, rot, name):
    body = prj2.leb(oid()) + struct.pack("<6f", pos[0], pos[1], pos[2], rot, 0.0, 0.0) + b"\x7f"
    body += struct.pack("<I", type_id) + struct.pack("<h", 0) + bytes(3) + struct.pack("<3f", 1.0, 1.0, 1.0)
    return body + prj2.utf8(name) + bytes(4)


def segs(floor, fsplits, nbr):
    tops = [floor] + [s[0] for s in fsplits]
    for i, t in enumerate(tops):
        bot = nbr
        if i + 1 < len(tops) and tops[i + 1] >= nbr:
            bot = tops[i + 1]
        if t > bot:
            yield i, t, bot


def plain(top, bot):
    v = lambda h: 834.0 - (h - LOW) / 1024.0 * 256.0          # noqa: E731
    return ([(PLAIN[1], v(bot)), (PLAIN[1], v(top)), (PLAIN[2], v(top)), (PLAIN[2], v(bot))], 0, PLAIN[0])


# ------------------------------------------------------------------------------------------------ the roofs
def t0100(lx, lz, s):
    wx, wz = lx + 30, lz
    if wx in GAPS and 25 <= wz <= 30:
        old = list(segs(s["floor"][0], s["fsplits"], 0)) if wz == 25 else []
        oldf = dict(s["faces"])
        for k in range(10):
            for dname in ("+z", "-z", "-x", "+x"):
                s["faces"].pop(prj2.f_wall_floor(dname, k), None)
        s["floor"] = [LOW] * 4
        s["fsplits"] = [sp for sp in s["fsplits"] if sp[0] < LOW]
        for i, t, b in (segs(LOW, s["fsplits"], 0) if wz == 25 else ()):       # the street front, cut lower
            for j, ot, ob in old:
                f = oldf.get(prj2.f_wall_floor("-z", j))
                if f and ot >= t and ob <= b:
                    (u0, vb), (_, vt), (u1, _), _ = f[0]
                    v = lambda h: vb + (vt - vb) * (h - ob) / float(ot - ob)        # noqa: E731
                    s["faces"][prj2.f_wall_floor("-z", i)] = ([(u0, v(b)), (u0, v(t)), (u1, v(t)), (u1, v(b))], f[1], f[2])
    elif 25 <= wz <= 30 and (wx + 1 in GAPS or wx - 1 in GAPS):                  # the walls of the gaps
        dname = "+x" if wx + 1 in GAPS else "-x"
        for i, t, b in segs(s["floor"][0], s["fsplits"], LOW):
            s["faces"][prj2.f_wall_floor(dname, i)] = plain(t, b)
    if (wx, wz) == (44, 24):
        s["props"] |= 256 << 2                                                    # climbable towards +z: the drainpipe


def t0101(lx, lz, s):
    wx, wz = lx + 30, lz + 30
    if wx in GAPS and wz == 30:
        s["floor"] = [LOW] * 4                                                   # the border keeps a copy of the tile to the south
    elif wx in GAPS and wz == 31:
        f0 = s["floor"][0]
        if f0 > ROOF and not any(sp[0] == ROOF for sp in s["fsplits"]):
            s["fsplits"] = sorted(s["fsplits"] + [[ROOF] * 4], key=lambda sp: -sp[0])
        for i, t, b in segs(f0, s["fsplits"], LOW):
            if t <= ROOF:
                s["faces"][prj2.f_wall_floor("-z", i)] = plain(t, b)


def t0000(lx, lz, s):
    if (lx, lz) == (25, 24):
        s["props"] &= 3                                                           # no drainpipe on the house front any more


for name, fn in (("T_01_00", t0100), ("T_01_01", t0101), ("T_00_00", t0000)):
    rooms, n = P.edit_sectors(rooms, name, fn)
    print(name, "sectors changed", n)

pipe, fence = [], []


def objs(room, oc, op):
    if oc != b"TeStaTn3":
        return op
    o, x, y, z, ry = spos(op)
    t = stype(op)
    if room == "T_00_00":
        if t == 223:
            pipe.append(op)
            return None
        if t == 126 and abs(x - 25088) < 2 and abs(z - 26112) < 2:
            fence.append(op)
    if room == "T_01_00":
        if t == 126 and abs(z - 26112) < 2 and round(x) in (4608, 5632, 10752, 11776):
            return op[:o + 4] + struct.pack("<f", float(LOW)) + op[o + 8:]         # the railing goes down with the roof
        if t == 126 and abs(z - 26112) < 2 and round(x) == 14848:
            return None                                                           # the way to the drainpipe
        if t == 126 and abs(x - 3072) < 40 and round(z) in (28672, 29696):
            return None                                                           # a way out of the house roof, to the east
        if t == 238 and abs(x - 11540) < 80 and y > 3500:
            return op[:o + 4] + struct.pack("<f", 2304.0) + op[o + 8:]             # an air conditioner that would hang in the air
    return op


rooms = P.map_objects(rooms, objs)
assert len(pipe) == 1 and len(fence) == 1, (len(pipe), len(fence))
rooms = P.add_objects(rooms, "T_00_00", [(b"TeStaTn3", static_like(fence[0], x=26112.0))])
rooms = P.add_objects(rooms, "T_01_00", [(b"TeStaTn3", static_like(pipe[0], x=14848.0))])

# ------------------------------------------------------------------------------------------------ the blackout
lato = [p for n, c, p in P.raw_objects(src) if n == "CASA_INGRESSO" and c == b"TeStaTn3" and stype(p) == 255][0]
rooms = P.add_objects(rooms, "CASA_INGRESSO", [(b"TeStaTn3", static_like(lato, x=1536.0, y=0.0, z=4090.0, rot=180.0, type_id=448)),
                                               (b"TeMovTn3", moveable(1208, (1536.0, 737.0, 3988.0), 180.0, "fusibile_posto"))])
rooms = P.add_objects(rooms, "CASA_CANTINA", [(b"TeMovTn3", moveable(511, (1400.0, 0.0, 1500.0), 0.0, "fusibile"))])

rl, _ = P.chunks(rooms)
last = 0
parsed = []
for c, p in rl:
    r = Reader(p)
    r.leb(), r.leb()
    h = p[:r.s.tell()]
    items, _ = P.chunks(p[r.s.tell():])
    last = max(last, Reader(dict(items)[b"TeI"]).leb())
    parsed.append((c, h, items))
out = []
twins = []
for c, h, items in parsed:
    name = dict(items)[b"TeName"].decode()
    if not name.startswith("CASA_"):
        out.append((c, h + P.pack(items)))
        continue
    last += 1
    alt, base = [], []
    for c2, p2 in items:
        if c2 == b"TeObjects":
            keep = []
            for oc, op in P.chunks(p2)[0]:
                rr = Reader(op)
                rr.leb()
                rest = op[rr.s.tell():]
                if oc == b"TePor2":
                    keep.append((oc, prj2.leb(oid()) + rest))
                elif oc == b"TeStaTn3":
                    keep.append((oc, static_like(op)))
            alt.append((c2, P.pack(keep)))
            base.append((b"TeAlternate", prj2.c_int("TeGroup", 1) + prj2.c_int("TeRoom", last) + prj2.END))
            base.append((c2, p2))
            continue
        base.append((c2, p2))
        alt.append((c2, prj2.leb(last) if c2 == b"TeI" else (name + "_BUIO").encode() if c2 == b"TeName"
                    else struct.pack("<3f", 0.05, 0.055, 0.09) if c2 == b"TeAmbient" else p2))
    out.append((c, h + P.pack(base)))
    twins.append((c, h + P.pack(alt)))
rooms = P.pack(out + twins)
print("dark twins:", len(twins))

items, _ = P.chunks(d[b"TeSettings"])
wads, _ = P.chunks(dict(items)[b"TeWads"])
if not any(b"CdV_Blackout.wad2" in wp for _, wp in wads):
    wc, wp = [(wc, wp) for wc, wp in wads if b"CdV_Oggetti.wad2" in wp][0]
    sub = [(k, v.replace(b"CdV_Oggetti.wad2", b"CdV_Blackout.wad2")) for k, v in P.chunks(wp)[0]]
    wads.insert(0, (wc, P.pack(sub)))
    items = [(c, P.pack(wads) if c == b"TeWads" else p) for c, p in items]
top = [(c, P.pack(items) if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top]
P.save(dst + ".tmp", head, top)
print(subprocess.run([sys.executable, "prj2_fill.py", dst + ".tmp", dst], capture_output=True, text=True).stdout)
