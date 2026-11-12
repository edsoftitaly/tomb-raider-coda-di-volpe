"""Oliveri, touch-ups in place on Ed's file (12/11/2026 evening). Nothing is regenerated.

- the two side walls (CASA_PORTA_LATO) that were missing at the door hall -> laundry and at the door laundry -> WC
- the crank on the winch of the yard gate: moveable 703 of CdV_Sigillo.wad2 (the one of Marinello), hidden until
  Lara puts it there; the wad is added to the level
- faces without a texture (prj2_fill)

usage: oliveri_ritocchi.py <Oliveri.prj2> <out.prj2>"""
import struct
import subprocess
import sys

import prj2
import prj2_patch as P
from prj2_check import Reader

src, dst = sys.argv[1], sys.argv[2]
raw = P.raw_objects(src)
next_id = max(Reader(p).leb() for _, _, p in raw) + 1


def clone_static(room, x, z, rot):
    """A copy of the CASA_PORTA_LATO of the entrance hall with the same turn, somewhere else."""
    global next_id
    for name, c, p in raw:
        if name == "CASA_INGRESSO" and c == b"TeStaTn3":
            r = Reader(p)
            r.leb()
            o = r.s.tell()
            px, py, pz, ry = struct.unpack("<4f", p[o:o + 16])
            if struct.unpack("<I", p[o + 29:o + 33])[0] == 255 and ry == rot:
                body = prj2.leb(next_id) + struct.pack("<4f", x, py, z, ry) + p[o + 16:]
                next_id += 1
                return (c, body)
    raise SystemExit("no CASA_PORTA_LATO to copy")


def moveable(type_id, pos, rot, name):
    global next_id
    body = prj2.leb(next_id) + struct.pack("<6f", pos[0], pos[1], pos[2], rot, 0.0, 0.0) + b"\x7f"
    body += struct.pack("<I", type_id) + struct.pack("<h", 0) + bytes(3) + struct.pack("<3f", 1.0, 1.0, 1.0)
    body += prj2.utf8(name) + bytes(4)
    next_id += 1
    return (b"TeMovTn3", body)


head, top = P.load(src)
top = list(top)
d = dict(top)
have = set(P.objects(src)[i][5] for i in range(len(P.objects(src))))
rooms = d[b"TeRooms"]
sides = {(o[0], round(o[3][0]), round(o[3][2])) for o in P.objects(src) if o[1] == "sta" and o[2] == 255}
for room, x, z, rot in (("CASA_DISIMPEGNO", 1024, 3200, 0.0), ("CASA_DISIMPEGNO", 1024, 3968, 0.0),
                        ("CASA_LAVANDERIA", 1152, 1024, 90.0), ("CASA_LAVANDERIA", 1920, 1024, 90.0)):
    if (room, x, z) not in sides:
        rooms = P.add_objects(rooms, room, [clone_static(room, float(x), float(z), rot)])
        print("side wall", room, x, z)
if "manovella_posta" not in have:
    # the winch (static 245) is at local (12800, 0, 17408) of T_01_00, its socket 538 up and 113 out towards +z
    rooms = P.add_objects(rooms, "T_01_00", [moveable(703, (12800.0, 556.0, 17408.0 + 150.0), 180.0, "manovella_posta")])
    print("crank on the winch")
items, _ = P.chunks(d[b"TeSettings"])
wads, _ = P.chunks(dict(items)[b"TeWads"])
if not any(b"CdV_Sigillo.wad2" in wp for _, wp in wads):
    like = [(wc, wp) for wc, wp in wads if b"CdV_Oggetti.wad2" in wp][0]
    wads.append((like[0], like[1].replace(b"CdV_Oggetti.wad2", b"CdV_Sigillo.wad2")))
    items = [(c, P.pack(wads) if c == b"TeWads" else p) for c, p in items]
    print("wad CdV_Sigillo.wad2")
top = [(c, P.pack(items) if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top]
P.save(dst + ".tmp", head, top)
print(subprocess.run([sys.executable, "prj2_fill.py", dst + ".tmp", dst], capture_output=True, text=True).stdout)
