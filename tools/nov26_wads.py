"""26 Nov: lighter levels. For each level: the wads that give it nothing leave its list; the big ones it uses only in
part (1.5 MB and over) are replaced by a copy with just its objects and their textures (<wad>_<Level>.wad2, made by
wad_slim.py). TombEngine.wad2 is never touched; wads without objects of their own (sprites, the rope) stay; so does
anything named in the level script or in Gameflow.lua.
usage: nov26_wads.py <Level> <in.prj2> <out.prj2> <dir for the slim wads> [noslim]"""
import os
import re
import sys

import lv
import prj2_patch as P
import wad_plan as WP
import wad_slim as S

level, src, dst, outdir = sys.argv[1:5]
noslim = len(sys.argv) > 5
names = WP.object_ids()
gf = open(os.path.join(lv.LEVELS, "..", "scripts", "Gameflow.lua"), encoding="utf-8").read() if os.path.exists(os.path.join(lv.LEVELS, "..", "scripts", "Gameflow.lua")) else ""
extra = {names[k] for k in re.findall(r"ObjID\.(\w+)|ID\.(\w+)", gf) for k in k if k in names}
plan = WP.plan(level)
drop, ren = set(), {}
for w, um, us, n, size in plan:
    if um is None or w == "TombEngine.wad2":
        continue
    mov, sta = lv.wad_ids(os.path.join(lv.WADS, w))
    um = sorted(set(um) | {i for i in mov if i in extra})
    if not mov and not sta:
        continue
    if not um and not us:
        drop.add(w)
    elif not noslim and size >= 1_500_000 and (len(um) < len(mov) or len(us) < len(sta)):
        new = "%s_%s.wad2" % (w[:-5], level)
        S.slim(os.path.join(lv.WADS, w), os.path.join(outdir, new), set(us), set(um))
        ren[w] = new
head, top = P.load(src)
d = dict(top)
items, _ = P.chunks(d[b"TeSettings"])
wads, _ = P.chunks(dict(items)[b"TeWads"])
keep = []
for wc, wp in wads:
    m = re.search(rb"([\w \-\.()]+\.wad2)", wp)
    name = m.group(1).decode("latin1") if m else ""
    if name in drop:
        continue
    if name in ren:
        wp = P.pack([(k, v.replace(name.encode(), ren[name].encode())) for k, v in P.chunks(wp)[0]])
    keep.append((wc, wp))
settings = P.pack([(c, P.pack(keep) if c == b"TeWads" else p) for c, p in items])
P.save(dst, head, [(c, settings if c == b"TeSettings" else p) for c, p in top])
print(level, "wads", len(wads), "->", len(keep), " dropped", len(drop), " slim", ren)
