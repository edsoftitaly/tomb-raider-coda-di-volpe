"""Top-down planning map of a built level (sector grid, heights, decor, named objects).

Usage: python3 map_level.py Level [out.png] [scale]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import prj2_mesh as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def heightmap(key):
    path = os.path.join(ROOT, "build", "levels", key, key + ".prj2")
    rooms, objects = P.read_rooms(path)
    sx = max(int(r["pos"][0]) + r["nx"] for r in rooms)
    sz = max(int(r["pos"][2]) + r["nz"] for r in rooms)
    h = np.full((sx, sz), np.nan)
    for rm in rooms:
        if not rm["name"].startswith("T_"):
            continue
        rx, ry, rz = rm["pos"]
        for (x, z), s in rm["sectors"].items():
            if s["wall"] or "floor" not in s:
                continue
            h[int(rx) + x, int(rz) + z] = ry + sum(s["floor"]) / 4.0
    return h, rooms, P.read_rooms.statics


def render(key, out, scale=3):
    h, rooms, statics = heightmap(key)
    nx, nz = h.shape
    hv = np.nan_to_num(h, nan=0.0) / 512.0  # metres
    gx, gz = np.gradient(hv)
    shade = np.clip(0.75 - 0.35 * gx - 0.35 * gz, 0.2, 1.0)
    rgb = np.zeros((nx, nz, 3))
    t = np.clip(hv / max(1.0, np.nanmax(hv)), 0, 1)
    rgb[..., 0] = 0.55 + 0.35 * t
    rgb[..., 1] = 0.55 + 0.25 * t
    rgb[..., 2] = 0.40 + 0.20 * t
    rgb *= shade[..., None]
    from scipy.ndimage import minimum_filter
    bld = (hv - minimum_filter(hv, size=9)) > 2.5
    rgb[bld] = (0.75, 0.35, 0.3)
    sea = (hv <= 0.05)
    rgb[sea] = (0.25, 0.45, 0.65)
    rgb[np.isnan(h)] = (0.1, 0.1, 0.1)
    # image: x to the right, z upwards (north up)
    img = (np.transpose(rgb, (1, 0, 2))[::-1] * 255).astype(np.uint8)
    im = Image.fromarray(img).resize((nx * scale, nz * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    Y = lambda z: (nz - z) * scale  # noqa: E731
    for x in range(0, nx, 10):
        d.line([(x * scale, 0), (x * scale, nz * scale)], fill=(255, 255, 255) if x % 50 == 0 else (90, 90, 90), width=1)
        if x % 50 == 0:
            d.text((x * scale + 2, 2), str(x), fill=(255, 255, 0))
    for z in range(0, nz, 10):
        d.line([(0, Y(z)), (nx * scale, Y(z))], fill=(255, 255, 255) if z % 50 == 0 else (90, 90, 90), width=1)
        if z % 50 == 0:
            d.text((2, Y(z) + 2), str(z), fill=(255, 255, 0))
    col = {range(100, 106): (230, 200, 60), range(106, 112): (30, 110, 30), range(112, 116): (255, 255, 255),
           range(128, 133): (255, 80, 80), range(133, 142): (80, 160, 255)}
    for st in statics:
        c = next((v for k, v in col.items() if st["type"] in k), (200, 120, 200))
        rx, ry, rz = st["room"]["pos"]
        x, z = (rx * 1024 + st["pos"][0]) / 1024, (rz * 1024 + st["pos"][2]) / 1024
        d.ellipse([x * scale - 1, Y(z) - 1, x * scale + 1, Y(z) + 1], fill=c)
    names = os.path.join(ROOT, "build", "levels", key, key + ".names.json")
    if os.path.exists(names):
        for n, v in json.load(open(names)).items():
            x, z = v[0] / 1024, v[2] / 1024
            d.rectangle([x * scale - 2, Y(z) - 2, x * scale + 2, Y(z) + 2], fill=(255, 0, 0))
            d.text((x * scale + 4, Y(z) - 6), n, fill=(255, 220, 220))
    im.save(out)
    return out


if __name__ == "__main__":
    key = sys.argv[1]
    print(render(key, sys.argv[2] if len(sys.argv) > 2 else "/tmp/map_%s.png" % key,
                 int(sys.argv[3]) if len(sys.argv) > 3 else 3))
