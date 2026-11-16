"""Tindari, 16 Nov afternoon.

1. Cryptoporticus: the gap under the rope was two sectors with a step in it (jumped, or simply walked through).
   Now five sectors (99..103), eight clicks deep, no step, teeth spikes on the whole bottom; the rope hangs in the
   middle of it.
2. Domus, the mosaic of the caps: the safe floor was a wide path one could walk. Now eight single pillars a
   standing jump apart (two ways round, west and east), a column in the middle that stops any run through, and
   every other sector is a tile that falls onto spikes.

  tindari_pm.py <in.prj2> <out.prj2> <tiles.json>"""
import copy
import json
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

# ---- domus (room T_02_02 at 60, 60): world sectors
OX, OZ = 60, 60
GRID = [(x, z) for z in range(79, 84) for x in range(77, 86)]
PILLARS = [(81, 79), (79, 79), (83, 79), (79, 81), (83, 81), (79, 83), (81, 83), (83, 83)]
BLOCK = (81, 81)
PU = [(1024.0, 1281.0), (1024.0, 1026.0), (1280.0, 1026.0), (1280.0, 1281.0)]      # upper half of a pillar side
PL = [(1024.0, 1536.0), (1024.0, 1281.0), (1280.0, 1281.0), (1280.0, 1536.0)]      # lower half
# ---- cryptoporticus (room U_CRIPTOPORTICO at 93, 56): local sectors
PIT_X, PIT_Z = range(6, 11), range(1, 4)
CX, CZ, CY = 93, 56, 18944


def rename(op, name, pos=None, new_id=None, static=False):
    r = Reader(op)
    r.leb()
    a = r.s.tell()
    body = bytearray(op[a:])
    if pos is not None:
        body[0:12] = struct.pack("<3f", *pos)
    r.raw(28 if static else 24)
    r.leb()
    r.raw(4 + 12 + 2 if static else 4 + 2 + 3 + 12)
    q = r.s.tell() - a
    n = struct.unpack_from("<i", body, q)[0]
    if name is not None:
        nb = name.encode()
        body[q:q + 4 + n] = struct.pack("<i", len(nb)) + nb
    head = op[:a] if new_id is None else P.prj2.leb(new_id)
    return head + bytes(body)


def name_of(op, static=False):
    r = Reader(op)
    r.leb()
    r.raw(28 if static else 24)
    r.leb()
    r.raw(4 + 12 + 2 if static else 4 + 2 + 3 + 12)
    return r.raw(struct.unpack("<i", r.raw(4))[0]).decode("utf-8", "replace")


def main():
    src, dst, out_json = sys.argv[1:4]
    head, top = P.load(src)
    rooms = dict(top)[b"TeRooms"]
    raw = P.raw_objects(src)
    next_id = [max(Reader(op).leb() for _, _, op in raw) + 1]

    # ------------------------------------------------------------------ domus: sectors
    secs = {}
    P.edit_sectors(rooms, "T_02_02", lambda x, z, s: secs.__setitem__((x + OX, z + OZ), copy.deepcopy(s)))
    old_pillars = {k for k in GRID if secs[k]["floor"][0] == 2048}
    pit_face = secs[(80, 79)]["faces"][25]
    top_face = secs[(81, 79)]["faces"][25]
    wall_n = secs[(83, 84)]                           # north wall over a pit sector: faces down to the bottom

    def domus(x, z, s):
        k = (x + OX, z + OZ)
        if k in PILLARS:
            s["floor"] = [2048] * 4
            s["fsplits"] = [[1024] * 4]
            s["faces"] = {25: top_face}
            for d in range(4):
                s["faces"][d] = (PU, 0, 17)
                s["faces"][d + 5] = (PL, 0, 17)
        elif k == BLOCK:
            s["floor"] = [4096] * 4
            s["fsplits"] = [[3072] * 4, [2048] * 4, [1024] * 4]
            s["faces"] = {25: secs[(76, 81)]["faces"][25]}
            for d in range(4):
                for face, uv in ((d, PU), (d + 5, PL), (29 + d, PU), (39 + d, PL)):
                    s["faces"][face] = (uv, 0, 17)
        elif k in GRID:
            s["floor"] = [0] * 4
            s["fsplits"] = []
            s["faces"] = {25: s["faces"][25] if k not in old_pillars else pit_face}
        elif k == (80, 84):                           # the wall north of a pillar that is now pit
            s["fsplits"] = copy.deepcopy(wall_n["fsplits"])
            for f in (1, 6, 30, 40, 50):
                s["faces"][f] = wall_n["faces"][f]
    rooms, n1 = P.edit_sectors(rooms, "T_02_02", domus)

    # ------------------------------------------------------------------ domus: tiles, spikes, golden caps
    tiles = [k for k in GRID if k not in PILLARS and k != BLOCK]
    have = {}
    proto = {}
    caps = []
    for room, oc, op in raw:
        if room != "T_02_02":
            continue
        if oc == b"TeMovTn3":
            nm = name_of(op)
            if nm.startswith(("tess_", "punte_")):
                have[nm] = op
                proto.setdefault(nm.split("_")[0], (oc, op))
        elif oc == b"TeStaTn3":
            r = Reader(op); r.leb(); r.raw(28); r.leb()
            if struct.unpack("<I", r.raw(4))[0] == 454:
                caps.append(op)
    cap_slots = list(PILLARS)
    used = [0]

    def objs(room, oc, op):
        if room != "T_02_02":
            return op
        if oc == b"TeMovTn3":
            nm = name_of(op)
            if nm.startswith(("tess_", "punte_")):
                x, z = map(int, nm.split("_")[1:])
                return op if (x, z) in tiles else None
        if oc == b"TeStaTn3" and op in caps:
            if used[0] >= len(cap_slots):
                return None
            x, z = cap_slots[used[0]]
            used[0] += 1
            r = Reader(op); r.leb(); a = r.s.tell()
            y = struct.unpack_from("<f", op, a + 4)[0]
            return op[:a] + struct.pack("<3f", (x - OX + 0.5) * 1024, y, (z - OZ + 0.5) * 1024) + op[a + 12:]
        return op
    rooms = P.map_objects(rooms, objs)
    assert used[0] == len(PILLARS), used
    new = []
    for x, z in tiles:
        for kind, y in (("tess", 2048.0), ("punte", 0.0)):
            nm = "%s_%d_%d" % (kind, x, z)
            if nm not in have:
                oc, op = proto[kind]
                new.append((oc, rename(op, nm, ((x - OX + 0.5) * 1024, y, (z - OZ + 0.5) * 1024), next_id[0])))
                next_id[0] += 1
    rooms = P.add_objects(rooms, "T_02_02", new)

    # ------------------------------------------------------------------ cryptoporticus
    csec = {}
    P.edit_sectors(rooms, "U_CRIPTOPORTICO", lambda x, z, s: csec.__setitem__((x, z), copy.deepcopy(s)))

    def cripto(x, z, s):
        if x in PIT_X and x != 9 and (z in PIT_Z or z in (0, 4)):
            s.update(copy.deepcopy(csec[(9, z)]))
        elif x == 5 and z in PIT_Z:                   # the west edge: its side down to the bottom, as the east edge has
            s["fsplits"] = [[1024] * 4]
            s["faces"][3] = csec[(11, z)]["faces"][2]
            s["faces"][8] = csec[(11, z)]["faces"][7]
    rooms, n2 = P.edit_sectors(rooms, "U_CRIPTOPORTICO", cripto)

    def rope(room, oc, op):
        if room == "U_CRIPTOPORTICO" and oc == b"TeMovTn3" and name_of(op) == "fune_cripto":
            r = Reader(op); r.leb(); a = r.s.tell()
            x, y, z = struct.unpack_from("<3f", op, a)
            return op[:a] + struct.pack("<3f", 8.5 * 1024, y, z) + op[a + 12:]
        return op
    rooms = P.map_objects(rooms, rope)
    spikes, keys = [], []
    for x in PIT_X:
        for z in PIT_Z:
            k = "%d_%d" % (CX + x, CZ + z)
            keys.append(k)
            spikes.append((proto["punte"][0], rename(proto["punte"][1], "punte_cripto_" + k, ((x + 0.5) * 1024, 0.0, (z + 0.5) * 1024), next_id[0])))
            next_id[0] += 1
    rooms = P.add_objects(rooms, "U_CRIPTOPORTICO", spikes)

    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
    json.dump({"tiles": ["%d_%d" % k for k in tiles], "cripto": keys,
               "pit": [CX + PIT_X[0], CX + PIT_X[-1], CZ + PIT_Z[0], CZ + PIT_Z[-1], CY]}, open(out_json, "w"))
    print("domus: %d sectors, %d tiles (%d new objects); cryptoporticus: %d sectors, %d spikes" % (n1, len(tiles), len(new), n2, len(spikes)))


if __name__ == "__main__":
    main()
