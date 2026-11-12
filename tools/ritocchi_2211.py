"""Fixes of 12/11/2026, 22:11 (Ed's test):
 tindari <in> <out>         the 13 Castor slabs (moveable ANIMATING20, which collides) become statics 454 without collision
 suoni <in> <out>           adds to the selected sounds every sound the animations of CdV_Mafiosi.wad2 play
 oliveri <in> <out>         the two cars of the road block become Carabinieri cars (static 148) + suoni"""
import re
import struct
import sys

import prj2
import prj2_patch as P
import wadtool
from prj2_check import Reader

MAFIOSI = "/mnt/attach/outputs/cdv/CdV_Mafiosi.wad2"
USED = (115, 136, 152, 153, 154, 158, 172)


def goon_sounds():
    out = set()
    for mid, p in wadtool.moveables(wadtool.load(MAFIOSI)):
        if mid not in USED:
            continue
        for m in re.finditer(rb"\x06W2Cmd2", p):
            n, j = wadtool._leb_u(p, m.end())
            v, i = [], j
            for _ in range(3):
                x, i = wadtool._leb_u(p, i)
                v.append(x)
            if v[0] == 5:
                out.add(v[2] & 0xFFF)
    return out


def suoni(settings):
    items, _ = P.chunks(settings)
    d = dict(items)
    have = set(Reader(q).leb() for c, q in P.chunks(d[b"TeSelectedSounds"])[0])
    if not have:
        print("  lista suoni vuota: lasciata com'e'")
        return settings
    new = sorted(goon_sounds() - have)
    print("  suoni aggiunti:", new)
    body = P.pack([(b"TeSelSnd", wadtool._leb_enc(v)) for v in sorted(have | set(new))])
    return P.pack([(c, body if c == b"TeSelectedSounds" else p) for c, p in items])


def patch(src, dst, what):
    head, top = P.load(src)
    out = []
    for c, p in top:
        if c == b"TeSettings":
            if what == "tindari":
                p = P.add_wad(p, "CdV_Lastra.wad2")
            p = suoni(p)
        elif c == b"TeRooms":
            if what == "tindari":
                slabs = []

                def take(room, oc, op):
                    if oc.startswith(b"TeMov") and P.mov_type(op)[1] == 1219:
                        r = Reader(op)
                        r.leb()
                        k = r.s.tell()
                        slabs.append((room, op[:k] + op[k:k + 16] + struct.pack("<3f", 0, 0, 1) + b"\x7f"
                                      + struct.pack("<I", 454) + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, 0)))
                        return None
                    return op
                p = P.map_objects(p, take)
                kind = b"TeStaTn3" if any(oc == b"TeStaTn3" for _, oc, _ in P.raw_objects(src)) else b"TeStaTen2"
                for room in sorted(set(r for r, _ in slabs)):
                    p = P.add_objects(p, room, [(kind, q + (b"\0\0\0\0" if kind == b"TeStaTn3" else b"")) for r, q in slabs if r == room])
                print("  lastre convertite:", len(slabs), kind)
                assert len(slabs) == 13
            if what == "oliveri":
                n = [0]

                def car(room, oc, op):
                    if room == "T_01_00" and oc.startswith(b"TeSta"):
                        r = Reader(op)
                        r.leb()
                        k = r.s.tell()
                        x, y, z = struct.unpack("<3f", op[k:k + 12])
                        t = struct.unpack("<I", op[k + 29:k + 33])[0]
                        if t in (134, 136) and 23500 < x < 24500 and 20500 < z < 24000:
                            n[0] += 1
                            return op[:k + 29] + struct.pack("<I", 148) + op[k + 33:]
                    return op
                p = P.map_objects(p, car)
                print("  auto dei carabinieri:", n[0])
                assert n[0] == 2
        out.append((c, p))
    P.save(dst, head, out)


patch(sys.argv[2], sys.argv[3], sys.argv[1])
