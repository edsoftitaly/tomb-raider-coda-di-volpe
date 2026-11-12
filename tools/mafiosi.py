"""The men of Turi with the faces of the Venice gang (MadDerek's remastered skinned models for TombEngine, the wad
Ed chose: CdV_Mafiosi.wad2 = "Skinned Models Venice.wad2").

Every Baddy 1 becomes a GOON_SILENCER1 or 2 (in turn), every Baddy 2 a GOON_SILENCER3, the bosses named on the
command line a WORKER_DUAL_REVOLVER. These are Tomb Raider 2 enemies: they do not know AI_GUARD, once switched on
they come for Lara. So the guards of tools/guardie.py are taken away again, and the zones that switch men on are
made much wider instead: the men are on their way when Lara first sees them, they do not appear in front of her.

usage: mafiosi.py <level.prj2> <level.lua> <out.prj2> <out.lua> [boss name ...]"""
import re
import struct
import sys

import prj2_patch as P

SIL1, SIL2, SIL3, BOSS, AI_GUARD = 152, 153, 154, 158, 1040
MARK = "-- Guards: the men of the zones are on their feet from the start (tools/guardie.py)."


def main():
    src, lua_src, dst, lua_dst = sys.argv[1:5]
    bosses = set(sys.argv[5:])
    head, top = P.load(src)
    d = dict(top)
    names = {}
    for o in P.objects(src):
        if o[1] == "mov" and o[2] in (174, 175):
            names[(o[0], round(o[3][0]), round(o[3][2]), o[5])] = o
    turn = [0]
    men = set()

    def fn(room, oc, op):
        if oc not in (b"TeMovTn3", b"TeMovTen2"):
            return op
        o, t = P.mov_type(op)
        if t == AI_GUARD:
            return None
        if t not in (174, 175):
            return op
        n = struct.unpack("<i", op[o + 21:o + 25])[0]
        name = op[o + 25:o + 25 + n].decode("utf-8", "replace")
        men.add(name)
        if name in bosses:
            new = BOSS
        elif t == 174:
            new = (SIL1, SIL2)[turn[0] % 2]
            turn[0] += 1
        else:
            new = SIL3
        return op[:o] + struct.pack("<I", new) + op[o + 4:]
    rooms = P.map_objects(d[b"TeRooms"], fn)
    settings = P.add_wad(d[b"TeSettings"], "CdV_Mafiosi.wad2")
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])
    raw = open(lua_src, "rb").read()
    lua = raw.decode("utf-8").replace("\r\n", "\n")
    if MARK in lua:
        i = lua.index(MARK)
        j = lua.index("CDV.Start = function()", i)
        j = lua.index("\n", j) + 1
        lua = lua[:i] + lua[j:].lstrip("\n")
    lines = lua.split("\n")
    k = 0
    wide = 0
    while k < len(lines):
        if lines[k].startswith("CDV.Zone("):
            e = k
            while not lines[e].rstrip().endswith("})"):
                e += 1
            block = "\n".join(lines[k:e + 1])
            who = re.findall(r'CDV\.Enable\("([^"]+)"\)', block)
            if any(w in men for w in who) and "CDV.Teleport" not in block and "-- wide" not in lines[k]:
                m = re.search(r"r = (\d+), dy = (\d+)", lines[k])
                if m:
                    r = min(max(int(int(m.group(1)) * 2.5), 8000), 24000)
                    lines[k] = lines[k].replace(m.group(0), "r = %d, dy = %d" % (max(r, int(m.group(1))), int(m.group(2)) * 2), 1)
                    wide += 1
            k = e
        k += 1
    lua = "\n".join(lines)
    open(lua_dst, "wb").write((lua.replace("\n", "\r\n") if b"\r\n" in raw else lua).encode("utf-8"))
    print(src.split("/")[-1], "men:", len(men), "zones widened:", wide)


main()
