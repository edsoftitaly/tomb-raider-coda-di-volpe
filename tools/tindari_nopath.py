"""Tindari: terrain rooms with no enemy in them or next door are excluded from pathfinding (TeNoPath), which is
what the compiler spends its time on at "Building pathfinding data". Enemies stand in T_01_02, T_02_01, T_02_02,
T_03_01, T_04_01 and in the BASILICA: those rooms and their four neighbours keep their boxes.
usage: tindari_nopath.py <Tindari.prj2> <out>"""
import sys

import prj2_patch as P
from prj2_check import Reader

OFF = ["T_00_00", "T_00_01", "T_00_03", "T_01_00", "T_03_03", "T_04_03", "T_05_00", "T_05_02", "T_05_03",
       "T_06_00", "T_06_01", "T_06_02", "T_06_03"]
head, top = P.load(sys.argv[1])
rooms, _ = P.chunks(dict(top)[b"TeRooms"])
done = []
for k, (c, p) in enumerate(rooms):
    r = Reader(p)
    r.leb(), r.leb()
    h = p[:r.s.tell()]
    items, _ = P.chunks(p[r.s.tell():])
    name = dict(items)[b"TeName"].decode()
    if name in OFF:
        assert dict(items)[b"TeNoPath"] == b"\x00", name
        rooms[k] = (c, h + P.pack([(a, b"\x01" if a == b"TeNoPath" else b) for a, b in items]))
        done.append(name)
assert sorted(done) == sorted(OFF), done
P.save(sys.argv[2], head, [(c, P.pack(rooms) if c == b"TeRooms" else p) for c, p in top])
print("excluded:", len(done))
