"""Oliveri, 14/11/2026: the two houses of Via Amodeo painted after the real ones, and Italian tiles in the house.

  python3 oliveri_facciate.py Oliveri.prj2 out.prj2

- Ed's house (south wall z = 25, world x 25-32) and the wall opposite (z = 16, T_01_00 x 12..2: the house
  with the five switches, then the shop house) take the elevations of gen_via_amodeo.py, one 256 px column
  per sector; the switches stand on the stone piers between the arched doors.
- Balconies under the two French windows opposite and at the west end of Ed's long balcony, two more
  air-conditioner motors on Ed's ground floor; the motors that would hang over the new windows move.
- Floors of the house: gen_pavimenti.py, one 256 px square per sector.
"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

T1 = "$(LevelDirectory)\\..\\CdV_Textures\\cdv_via_amodeo_1.png"
T2 = "$(LevelDirectory)\\..\\CdV_Textures\\cdv_via_amodeo_2.png"
TP = "$(LevelDirectory)\\..\\CdV_Textures\\cdv_pavimenti.png"
SLOT = 256        # px per sector on cdv_pavimenti.png (1024 x 512), like every other room texture of the level
FLOORS = {"INGRESSO": 0, "DISIMPEGNO": 0, "CANTINA": 1, "LAB": 1, "DISPENSA": 1, "SOGGIORNO": 2, "GALLERIA": 2, "RIPOSTIGLIO": 2,
          "CAMERA": 3, "CAMERETTA1": 3, "CAMERETTA2": 3, "CUCINA": 4, "BAGNO": 5, "WC": 5, "LAVANDERIA": 5}


def sta(uid, typ, pos, rot=0.0):
    return (b"TeStaTn3", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<4f", rot, 0, 0, 1) + b"\x7f" + struct.pack("<I", typ)
            + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, 0) + b"\0\0\0\0")


def quad(u0, v0, u1, v1):
    return [(u0, v1), (u0, v0), (u1, v0), (u1, v1)]         # bl, tl, tr, br as the viewer sees the wall


def main(src, dst):
    head, top = P.load(src)
    d = dict(top)
    settings, i1 = P.add_texture(d[b"TeSettings"], T1)
    settings, i2 = P.add_texture(settings, T2)
    settings, ip = P.add_texture(settings, TP)
    rooms = d[b"TeRooms"]
    n = {"casa": 0, "fronte": 0, "pav": 0}

    def street(rn, lx, lz, f):
        wx = lx + (30 if rn == "T_01_00" else 0)
        if lz == 25 and 25 <= wx <= 32 and (lx <= 30 if rn == "T_00_00" else lx >= 1):                    # Ed's house: faces of the -z side, top to bottom
            col = wx - 25
            vs = [0, 256, 512, 768, 1024, 1216]
            for k, face in enumerate((1, 6, 30, 40, 50)):
                assert face in f, (rn, lx, face)
                f[face] = (quad(col * 256, vs[k], col * 256 + 255, vs[k + 1] - (1 if k == 4 else 0)), f[face][1], i1)
            n["casa"] += 1
        if rn == "T_01_00" and lz == 16 and 2 <= lx <= 12:  # opposite: +z side, the viewer's left is the high x
            col = 12 - lx
            vs = [0, 256, 512, 768, 832]
            tex, u, v = (i2, col * 256, 0) if col < 8 else (i1, (col - 8) * 256, 1216)
            for k, face in enumerate((0, 5, 29, 39)):
                assert face in f, (rn, lx, face)
                f[face] = (quad(u, v + vs[k], u + 255, v + vs[k + 1] - (1 if k == 3 else 0)), f[face][1], tex)
            n["fronte"] += 1
    rooms, _ = P.edit_room(rooms, lambda r: r in ("T_00_00", "T_01_00"), street)

    def floor(rn, lx, lz, f):
        key = rn[5:].replace("_BUIO", "")
        if 25 in f and f[25][2] in (1, 2):
            slot = FLOORS[key]
            pts = f[25][0]
            us, vs = [p[0] for p in pts], [p[1] for p in pts]
            u0, v0 = (slot % 4) * SLOT, (slot // 4) * SLOT
            new = [(u0 + (SLOT - 1 if p[0] > min(us) + 100 else 0), v0 + (SLOT - 1 if p[1] > min(vs) + 100 else 0)) for p in pts]
            assert len(set(new)) >= 3, pts
            f[25] = (new, f[25][1], ip)
            n["pav"] += 1
    rooms, _ = P.edit_room(rooms, lambda r: r.startswith("CASA_"), floor)

    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = list(range(max(used) + 1, max(used) + 20))
    moved = []

    def move(room, oc, op):                                # motors on the wall opposite that would cover a window
        if oc == b"TeStaTn3" and room == "T_01_00":
            r = Reader(op)
            r.leb()
            k = r.s.tell()
            x, y, z = struct.unpack_from("<3f", op, k)
            typ = struct.unpack_from("<I", op, k + 29)[0]
            if typ == 238 and abs(z - 17408) < 1:
                nx = {8495: 7830.0, 9828: None, 10870: 10752.0}.get(int(x), x)
                moved.append((int(x), nx))
                if nx is None:
                    return None
                return op[:k] + struct.pack("<3f", nx, y, z) + op[k + 12:]
        return op
    rooms = P.map_objects(rooms, move)
    print("motors:", moved)
    # balconies of the two French windows opposite (wall u = 2.89 m and 7.11 m from x = 13312)
    add1 = [sta(ids.pop(0), 225, (13312 - 2.89 * 512, 1638.0, 17408.0), 0.0), sta(ids.pop(0), 225, (13312 - 7.11 * 512, 1638.0, 17408.0), 0.0)]
    rooms = P.add_objects(rooms, "T_01_00", add1)
    add0 = [sta(ids.pop(0), 224, (25.5 * 1024, 1638.0, 25600.0), 180.0),
            sta(ids.pop(0), 238, (25 * 1024 + 6.45 * 512, 1180.0, 25600.0), 180.0),
            sta(ids.pop(0), 238, (25 * 1024 + 11.7 * 512, 1180.0, 25600.0), 180.0)]
    rooms = P.add_objects(rooms, "T_00_00", add0)
    print(n)
    assert n["casa"] == 8 and n["fronte"] == 11, n
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
