"""Sound check of a level: every sound the animations of the objects placed in it (and of Lara) can play must be
among the level's selected sounds, or the engine stays silent there ("Missing sound effect N" in the log).

  suoni_check.py <level.prj2> <wad dir> <TombEngine.wad2> <catalog json> [out.prj2]

Prints what is missing; with out.prj2 adds the missing ids that have samples in the catalog. Sounds played by the
engine itself, not by an animation, are listed in ENGINE (taken from the TombEngine source for the objects in use)."""
import json
import os
import re
import struct
import sys

import prj2_patch as P
import wadtool
from prj2_check import Reader

ENGINE = {66: "falling block crumble", 67: "falling block land", 143: "body slam", 70: "MP stick hit",
          221: "gate (script)", 114: "padlock (script)"}


def anim_sounds(payload):
    out = set()
    for m in re.finditer(rb"\x06W2Cmd2", payload):
        n, j = wadtool._leb_u(payload, m.end())
        v, i = [], j
        for _ in range(3):
            x, i = wadtool._leb_u(payload, i)
            v.append(x)
        if v[0] == 5:
            out.add(v[2] & 0xFFF)
    return out


def main():
    src, wad_dir, lara_wad, cat_path = sys.argv[1:5]
    cat = json.load(open(cat_path))
    head, top = P.load(src)
    d = dict(top)
    settings = d[b"TeSettings"]
    wads = [m.decode("latin1").split("\\")[-1] for m in re.findall(rb"[\w\\/.$() -]+\.wad2", settings)]
    placed = set(o[2] for o in P.objects(src) if o[1] == "mov")
    need = {}
    seen = set()
    for name in wads:
        path = lara_wad if name == "TombEngine.wad2" else os.path.join(wad_dir, name)
        if not os.path.exists(path):
            print("  (wad not at hand: %s)" % name)
            continue
        for mid, p in wadtool.moveables(wadtool.load(path)):
            if mid in seen:
                continue
            seen.add(mid)
            if mid in placed or (name == "TombEngine.wad2" and mid < 60):
                for s in anim_sounds(p):
                    need.setdefault(s, set()).add(mid)
    for s in ENGINE:
        need.setdefault(s, set()).add(-1)
    items, _ = P.chunks(settings)
    sel = dict(items)[b"TeSelectedSounds"]
    have = set(Reader(q).leb() for c, q in P.chunks(sel)[0])
    missing = sorted(s for s in need if s not in have)
    add = [s for s in missing if cat.get(str(s), ["", []])[1]]
    print("%s: %d selected, %d needed, missing %d" % (os.path.basename(src), len(have), len(need), len(missing)))
    for s in missing:
        n, sm = cat.get(str(s), ["?", []])
        print("   %4d %-34s %s  objects %s" % (s, n, "" if sm else "(no sample in the catalog)", sorted(need[s])[:6]))
    if len(sys.argv) > 5 and add:
        body = P.pack([(b"TeSelSnd", wadtool._leb_enc(v)) for v in sorted(have | set(add))])
        settings2 = P.pack([(c, body if c == b"TeSelectedSounds" else p) for c, p in items])
        P.save(sys.argv[5], head, [(c, settings2 if c == b"TeSettings" else p) for c, p in top])
        print("   added", add)
    return add


if __name__ == "__main__":
    main()
