"""Render start / middle / end frames of every trailer shot of a level (three.js preview).

Usage: python3 preview_shots.py Level out_dir
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = "/home/claude/render"


def catmull(ps, t):
    """Catmull-Rom through ps (end points repeated), t in [0, 1]."""
    n = len(ps) - 1
    if n == 0:
        return ps[0]
    f = min(t * n, n - 1e-6)
    i = int(f)
    u = f - i
    p0, p1, p2, p3 = ps[max(i - 1, 0)], ps[i], ps[i + 1], ps[min(i + 2, n)]
    return [0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u +
                   (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u * u * u) for k in range(3)]


def main(key, out_dir, title=False):
    d = os.path.join(ROOT, "build", "levels", key)
    shots = json.load(open(os.path.join(d, key + ".shots.json")))
    subprocess.run(["python3", os.path.join(ROOT, "tools", "prj2_mesh.py"), os.path.join(d, key + ".prj2"),
                    os.path.join(RENDER, "mesh.json")], check=True, stdout=subprocess.DEVNULL)
    views = {}
    for s in shots:
        pos = [c["pos"] for c in s["cams"]]
        look = [c["look"] for c in s["cams"]]
        for j, t in enumerate((0.0, 0.5, 1.0)):
            p, l = catmull(pos, t), catmull(look, t)
            views["shot_%d_%d" % (s["seq"], j)] = [p[0] / 512, p[1] / 512, p[2] / 512, l[0] / 512, l[1] / 512, l[2] / 512]
    subprocess.run(["node", "shot.js", json.dumps(views), "?sea=1"], cwd=RENDER, check=True, stdout=subprocess.DEVNULL)
    os.makedirs(out_dir, exist_ok=True)
    W, H = 480, 270
    sheet = Image.new("RGB", (W * 3, (H + 20) * len(shots)), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for r, s in enumerate(shots):
        dr.text((6, r * (H + 20) + 4), "%s - seq %d: %s" % (key, s["seq"], s["name"]), fill=(255, 230, 120))
        for j in range(3):
            im = Image.open(os.path.join(RENDER, "shot_%d_%d.png" % (s["seq"], j))).resize((W, H))
            sheet.paste(im, (j * W, r * (H + 20) + 20))
    out = os.path.join(out_dir, "shots_%s.png" % key)
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
