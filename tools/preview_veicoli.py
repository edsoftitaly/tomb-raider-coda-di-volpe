"""Preview of the vehicle statics: python3 preview_veicoli.py key[,key...] out_prefix (renders 4 views each)."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decor import tex
tex.build()
from decor import veicoli
import numpy as np
D = "/home/claude/vrender"
keys = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "all" else list(veicoli.VEHICLES)
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/veh"
def render(k):
    pos, uv, tix = [], [], []
    m = veicoli.model_mesh(k)
    lo, hi = m.bbox()
    for idx, px, page, blend, dbl in m.f:
        ps = [np.array(m.v[i]) / 512.0 for i in idx]
        tris = [(0, 1, 2)] + ([(0, 2, 3)] if len(ps) == 4 else [])
        for a, b, c in tris:
            for j in (c, b, a):     # TombLib winding -> three.js CCW
                pos.extend([ps[j][0], ps[j][1], ps[j][2]])
                uv.extend([px[j][0] / 512.0, px[j][1] / 512.0])
            tix.append(page)
    order = sorted(range(len(tix)), key=lambda i: tix[i])
    P = [pos[i * 9:(i + 1) * 9] for i in order]
    U = [uv[i * 6:(i + 1) * 6] for i in order]
    T = [tix[i] for i in order]
    json.dump({"pos": [v for t in P for v in t], "uv": [v for t in U for v in t], "tix": T, "npages": len(tex.pages)},
              open(os.path.join(D, "mesh.json"), "w"))
    lo, hi = lo / 512.0, hi / 512.0
    L = hi[2] - lo[2]
    H = hi[1]
    d = max(L, H * 1.6) * 1.3
    views = {k + "_a": [d * 0.7, H * 0.95, d * 0.7, 0, H * 0.4, 0], k + "_b": [-d * 0.75, H * 0.8, -d * 0.7, 0, H * 0.4, 0],
             k + "_c": [d * 1.1, H * 0.5, 0.0, 0, H * 0.45, 0], k + "_d": [0.4, H * 1.1, d * 0.75, 0, H * 0.45, 0]}
    r = subprocess.run(["node", "shot.js", json.dumps(views)], cwd=D, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-800:])
    for name in views:
        os.replace(os.path.join(D, name + ".png"), out + name + ".png")
    return list(views)


from PIL import Image
for i, pg in enumerate(tex.pages):
    Image.fromarray(np.clip(pg, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(D, "decor_%d.png" % i))
names = []
for k in keys:
    names += render(k)
ims = [Image.open(out + n + ".png").resize((640, 360)) for n in names]
cols = 4
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (640 * cols, 360 * rows))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
sheet.save(out + "sheet.png")
print(out + "sheet.png")
