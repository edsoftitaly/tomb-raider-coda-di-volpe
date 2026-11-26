"""Which wads a level really needs: for every wad of its list, the objects it is the first to provide and how many of
them are placed in the level or named in its script.   wad_plan.py <level> ...  ->  dict used by wad_slim/prj2 trimming"""
import os, re, sys, json
import lv, prj2_patch as P

IDS = {}
for m in re.finditer(r"^\s*ID_(\w+)\s*(?:=\s*(\d+))?\s*,", open("/home/claude/ten/TombEngine/Objects/game_object_ids.h").read(), re.M):
    pass


def object_ids():
    out, n = {}, -1
    for line in open("/home/claude/ten/TombEngine/Objects/game_object_ids.h"):
        m = re.match(r"\s*ID_(\w+)\s*(?:=\s*(\w+))?\s*,", line)
        if not m:
            continue
        if m.group(2):
            v = m.group(2)
            n = int(v) if v.isdigit() else out.get(v.replace("ID_", ""), n + 1)
        else:
            n += 1
        out[m.group(1)] = n
    return out


def plan(level):
    prj = os.path.join(lv.LEVELS, level + ".prj2")
    lua = os.path.join(lv.LEVELS, "..", "scripts", "Levels", level + ".lua")
    names = object_ids()
    placed_m = {o[2] for o in P.objects(prj) if o[1] == "mov"}
    placed_s = {o[2] for o in P.objects(prj) if o[1] == "sta"}
    lua_m = set()
    if os.path.exists(lua):
        s = open(lua, encoding="utf-8").read()
        for m in re.finditer(r"\bID\.(\w+)|ObjID\.(\w+)", s):
            k = m.group(1) or m.group(2)
            if k in names:
                lua_m.add(names[k])
    seen_m, seen_s, out = set(), set(), []
    for w in lv.level_wads(prj):
        p = os.path.join(lv.WADS, w)
        if not os.path.exists(p):
            out.append((w, None, None, None, 0))
            continue
        mov, sta = lv.wad_ids(p)
        first_m = [i for i in mov if i not in seen_m]
        first_s = [i for i in sta if i not in seen_s]
        seen_m |= set(mov); seen_s |= set(sta)
        used_m = [i for i in first_m if i in placed_m or i in lua_m]
        used_s = [i for i in first_s if i in placed_s]
        out.append((w, used_m, used_s, (len(first_m), len(first_s)), os.path.getsize(p)))
    return out


if __name__ == "__main__":
    for level in sys.argv[1:]:
        print("==", level)
        for w, um, us, n, size in plan(level):
            if um is None:
                print("  %-34s (not in the repo)" % w)
            else:
                tag = "DROP" if not um and not us else ""
                print("  %-34s %5.1f MB  mov %d/%d  sta %d/%d  %s" % (w, size / 1e6, len(um), n[0], len(us), n[1], tag))
