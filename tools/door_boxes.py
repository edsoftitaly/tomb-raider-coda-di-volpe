"""Doors and pathfinding, the way Tomb Editor and TombEngine mean it.

Read in the sources: the compiler joins two boxes only when the whole stretch they share is open
(PathfindingDecompiled.cs, Dec_TestOverlap*): a room behind a doorway one sector wide is a zone of its own and no
enemy ever crosses the threshold. The classic answer is a Box sector under the door: a 1 x 1 box whose edge is the
doorway. The engine blocks every such box at load (level.cpp, LoadBoxes) and a door frees the one it stands on when
it opens (generic_doors.cpp, d2.box).

For every door object: its own sector S and the sector D1 one block ahead of it (yaw 0: -Z, 180: +Z, 90: -X,
270: +X). When D1 is the room's border with a wall portal, S gets the Box flag, in the room and in its flip twin.
  door_boxes.py <in.prj2> <out.prj2>      (report only when out is '-')"""
import pickle
import struct
import sys

import enemy_zones as EZ
import nov26_lib as L
import prj2_mesh as M
import prj2_patch as P

IDS = pickle.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "object_ids.pkl"), "rb"))
DOORS = {v for k, v in IDS.items() if "DOOR_TYPE" in k or k in ("ID_KICK_DOOR1", "ID_KICK_DOOR2", "ID_KICK_DOOR3", "ID_KICK_DOOR4", "ID_PUSHPULL_DOOR1", "ID_PUSHPULL_DOOR2")}
src, dst = sys.argv[1:3]
head, top = P.load(src)
rooms_p = dict(top)[b"TeRooms"]
rooms, _ = M.read_rooms(src)
byname = {r["name"]: r for r in rooms}
zs = EZ.Zones(src)
found = []


def see(room, cid, p):
    if cid == b"TeMovTn3":
        _, o = L._leb_at(p)
        x, y, z, ry = struct.unpack("<4f", p[o:o + 16])
        rest = p[o + 24:]
        _, o2 = L._leb_at(rest)
        t = struct.unpack("<I", rest[o2:o2 + 4])[0]
        r2 = rest[o2 + 4:]
        n = struct.unpack("<i", r2[17:21])[0]
        if t in DOORS:
            found.append((room, r2[21:21 + n].decode("utf-8", "replace"), t, x, y, z, ry))
    return p


P.map_objects(rooms_p, see)
todo = {}
for room, name, t, x, y, z, ry in sorted(found):
    r = byname[room]
    lx, lz = int(x // 1024), int(z // 1024)
    yaw = round(ry) % 360
    dx, dz = {0: (0, -1), 180: (0, 1), 90: (-1, 0), 270: (1, 0)}.get(yaw, (1, 0))
    ax, az = lx + dx, lz + dz
    base = EZ.ALT and next((room[:-len(a)] for a in EZ.ALT if room.endswith(a)), room)
    border = ax in (0, r["nx"] - 1) or az in (0, r["nz"] - 1)
    portal = zs.wallp.get((base, ax, az))
    own = r["sectors"].get((lx, lz), {})
    inside = 1 <= lx <= r["nx"] - 2 and 1 <= lz <= r["nz"] - 2 and not own.get("wall")
    has = bool(own.get("flags", 0) & 2)
    verdict = "ok: Box on its sector" if (border and portal and inside) else "NOT STANDARD (left alone)"
    print("%-28s %-18s sector (%d,%d) yaw %3d ahead (%d,%d) %s%s -> %s%s" % (name or "?", room, lx, lz, yaw, ax, az, "border " if border else "inside ", ("portal to " + portal) if portal else "no portal", verdict, " (already)" if has else ""))
    if border and portal and inside and not has:
        for a in ("",) + tuple(EZ.ALT):
            if base + a in byname:
                todo.setdefault(base + a, set()).add((lx, lz))
if dst != "-":
    n = 0
    for rn, secs in todo.items():
        def fn(lx, lz, sec, secs=secs):
            if (lx, lz) in secs:
                sec["props"] |= 2 << 2
        rooms_p, d = P.edit_sectors(rooms_p, rn, fn)
        n += d
    P.save(dst, head, [(c, rooms_p if c == b"TeRooms" else p) for c, p in top])
    print("Box flag set on", n, "sectors in", len(todo), "rooms")
