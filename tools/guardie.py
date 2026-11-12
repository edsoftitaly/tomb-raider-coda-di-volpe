"""Enemies that stand guard instead of appearing in front of Lara.

The men (Baddy 1 and 2) that a zone of the script switches on get an AI_GUARD object on their own spot and are
switched on at the start of the level: they are already there, standing, when Lara first sees them, and move
when she comes near or shoots. Men switched on by a door being kicked, dogs, rats and bats are left as they are.

usage: guardie.py <level.prj2> <level.lua> <out.prj2> <out.lua>     (out names may be '-' to only list)"""
import re
import struct
import sys

import prj2
import prj2_patch as P
from prj2_check import Reader

AI_GUARD, MEN = 1040, (174, 175)
MARK = "-- Guards: the men of the zones are on their feet from the start (tools/guardie.py)."


def zone_names(lua):
    names, inside = [], False
    for line in lua.split("\n"):
        if line.startswith("CDV.Zone("):
            inside = True
        if inside:
            names += re.findall(r'CDV\.Enable\("([^"]+)"\)', line)
            if line.rstrip().endswith("})"):
                inside = False
    return list(dict.fromkeys(names))


def main():
    src, lua_src, dst, lua_dst = sys.argv[1:5]
    raw = open(lua_src, "rb").read()
    lua = raw.decode("utf-8").replace("\r\n", "\n")
    objs = P.objects(src)
    by_name = {o[5]: o for o in objs if o[1] == "mov" and o[5]}
    guards = {(o[0], round(o[3][0]), round(o[3][2])) for o in objs if o[1] == "mov" and o[2] == AI_GUARD}
    men = [n for n in zone_names(lua) if n in by_name and by_name[n][2] in MEN]
    print("guards:", men)
    if dst == "-":
        return
    head, top = P.load(src)
    rooms = dict(top)[b"TeRooms"]
    nid = max(Reader(p).leb() for _, _, p in P.raw_objects(src)) + 1
    for n in men:
        room, _, _, pos, rot = by_name[n][:5]
        if (room, round(pos[0]), round(pos[2])) in guards:
            continue
        body = prj2.leb(nid) + struct.pack("<6f", pos[0], pos[1], pos[2], rot, 0.0, 0.0) + b"\x7f"
        body += struct.pack("<I", AI_GUARD) + struct.pack("<h", 0) + bytes(3) + struct.pack("<3f", 1.0, 1.0, 1.0) + prj2.utf8("") + bytes(4)
        rooms = P.add_objects(rooms, room, [(b"TeMovTn3", body)])
        nid += 1
    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
    if MARK not in lua:
        code = MARK + "\nCDV.StartList = CDV.StartList or {}\nCDV.StartList[#CDV.StartList + 1] = function()\n"
        code += "    for _, n in ipairs({ %s }) do CDV.Enable(n) end\nend\n" % ", ".join('"%s"' % n for n in men)
        code += "CDV.Start = function() for _, f in ipairs(CDV.StartList) do f() end end\n\n"
        assert lua.count("-- Playtest hook:") == 1
        lua = lua.replace("-- Playtest hook:", code + "-- Playtest hook:")
    open(lua_dst, "wb").write((lua.replace("\n", "\r\n") if b"\r\n" in raw else lua).encode("utf-8"))


main()
