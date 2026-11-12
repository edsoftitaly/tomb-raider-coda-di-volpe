"""Oliveri, third round on Ed's file (12/11/2026, 21:15):
- the thieves do not walk on the stair sectors any more (Box flag: they climbed the sides and went through the panels)
- the diary (PUZZLE_ITEM1) lies on the lookout: the engine makes him carry it and drop it where he dies
- a road block east of the yard gate, so that the only way left is west, to the town hall
usage: oliveri_ritocchi2.py <Oliveri.prj2> <out.prj2>"""
import struct
import sys

import prj2
import prj2_patch as P
from prj2_check import Reader

src, dst = sys.argv[1], sys.argv[2]
head, top = P.load(src)
top = list(top)
rooms = dict(top)[b"TeRooms"]
objs = P.objects(src)
raw = P.raw_objects(src)
next_id = [max(Reader(p).leb() for _, _, p in raw) + 1]
BOX = 2 << 2


def oid():
    next_id[0] += 1
    return next_id[0] - 1


def stairs(lx, lz, s):
    if (s["props"] & 3) == 0 and (max(s["floor"]) > 0 or (2 <= lx <= 4 and 1 <= lz <= 2)):
        s["props"] |= BOX


for name in ("CASA_INGRESSO", "CASA_DISIMPEGNO", "CASA_GALLERIA", "CASA_INGRESSO_BUIO", "CASA_DISIMPEGNO_BUIO", "CASA_GALLERIA_BUIO"):
    rooms, n = P.edit_sectors(rooms, name, stairs)
    print(name, "stair sectors closed to the thieves:", n)

palo = [o for o in objs if o[5] == "palo"][0]
if not any(o[5] == "diario_palo" for o in objs):
    body = prj2.leb(oid()) + struct.pack("<6f", palo[3][0], palo[3][1], palo[3][2], 0.0, 0.0, 0.0) + b"\x7f"
    body += struct.pack("<I", 500) + struct.pack("<h", 0) + bytes(3) + struct.pack("<3f", 1.0, 1.0, 1.0) + prj2.utf8("diario_palo") + bytes(4)
    rooms = P.add_objects(rooms, palo[0], [(b"TeMovTn3", body)])
    print("diary on the lookout, room", palo[0], [round(v) for v in palo[3]])

if not any(o[1] == "sta" and o[2] == 333 for o in objs):
    like = [p for n, c, p in raw if n == "T_01_00" and c == b"TeStaTn3"][0]
    r = Reader(like)
    r.leb()
    o = r.s.tell()
    nlen = struct.unpack("<i", like[o + 47:o + 51])[0]

    def static(type_id, x, z, rot):
        b = prj2.leb(oid()) + struct.pack("<4f", x, 0.0, z, rot) + like[o + 16:o + 29] + struct.pack("<I", type_id)
        return (b"TeStaTn3", b + like[o + 33:o + 47] + struct.pack("<i", 0) + like[o + 51 + nlen:])
    # world x 51.5, z 17.5 .. 24.5 = local of T_01_00 (origin x 30, z 0): orange barriers across the street, a car behind
    block = [static(333, 21.5 * 1024, (z + 0.5) * 1024, 90.0) for z in range(17, 25)]
    block.append(static(136, 23.6 * 1024, 20.6 * 1024, 100.0))
    block.append(static(134, 23.4 * 1024, 23.2 * 1024, 80.0))
    rooms = P.add_objects(rooms, "T_01_00", block)
    print("road block:", len(block), "statics")
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
