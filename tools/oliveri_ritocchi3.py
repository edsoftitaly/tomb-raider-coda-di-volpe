"""Oliveri, fourth round on Ed's file (12/11/2026, 21:45):
- the three pictures of the house become Ed's photographs (statics 450-452 of CdV_Quadri.wad2), a fourth one (453)
  goes in the first small bedroom; the dark twins of the rooms get the same
- the trapdoor to the roof has a padlock: its key (PUZZLE_ITEM14) lies on the thief of the living room, who drops
  it; a hidden bridge plugs the hole until the padlock is open
usage: oliveri_ritocchi3.py <Oliveri.prj2> <out.prj2>"""
import struct
import sys

import prj2
import prj2_patch as P
from prj2_check import Reader

src, dst = sys.argv[1], sys.argv[2]
head, top = P.load(src)
d = dict(top)
objs = P.objects(src)
next_id = [max(Reader(p).leb() for _, _, p in P.raw_objects(src)) + 1]
PIC = {"CASA_DISIMPEGNO": 450, "CASA_SOGGIORNO": 451, "CASA_CAMERA": 452}
model = []


def oid():
    next_id[0] += 1
    return next_id[0] - 1


def soff(p):
    r = Reader(p)
    r.leb()
    return r.s.tell()


def pictures(room, oc, op):
    if oc != b"TeStaTn3":
        return op
    o = soff(op)
    if struct.unpack("<I", op[o + 29:o + 33])[0] != 214:
        return op
    if room == "CASA_CAMERA":
        model.append(op)
    return op[:o + 29] + struct.pack("<I", PIC[room.replace("_BUIO", "")]) + op[o + 33:]


def moveable(type_id, pos, name):
    body = prj2.leb(oid()) + struct.pack("<6f", pos[0], pos[1], pos[2], 0.0, 0.0, 0.0) + b"\x7f"
    body += struct.pack("<I", type_id) + struct.pack("<h", 0) + bytes(3) + struct.pack("<3f", 1.0, 1.0, 1.0)
    return (b"TeMovTn3", body + prj2.utf8(name) + bytes(4))


rooms = P.map_objects(d[b"TeRooms"], pictures)
if model and not any(o[1] == "sta" and o[2] == 453 for o in objs):
    p = model[0]
    o = soff(p)
    n = struct.unpack("<i", p[o + 47:o + 51])[0]
    for room in ("CASA_CAMERETTA1", "CASA_CAMERETTA1_BUIO"):
        body = prj2.leb(oid()) + struct.pack("<4f", 1034.0, 0.0, 1536.0, 0.0) + p[o + 16:o + 29] + struct.pack("<I", 453)
        rooms = P.add_objects(rooms, room, [(b"TeStaTn3", body + p[o + 33:o + 47] + struct.pack("<i", 0) + p[o + 51 + n:])])
    print("pictures: 3 changed, 1 added")
names = {o[5] for o in objs}
thief = [o for o in objs if o[5] == "ladro_primo"][0]
if "chiave_lucchetto" not in names:
    rooms = P.add_objects(rooms, thief[0], [moveable(513, thief[3], "chiave_lucchetto")])
    rooms = P.add_objects(rooms, "T_00_00", [moveable(1340, (28.5 * 1024, 4864.0, 29.5 * 1024), "tappo_botola")])
    print("padlock: key on", thief[5], "in", thief[0], "- plug under the trapdoor")
settings = P.add_wad(d[b"TeSettings"], "CdV_Quadri.wad2", first=True)
P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])
