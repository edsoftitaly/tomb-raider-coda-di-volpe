"""Large seamless ground textures ("macro tiles") for the open terrain.

The old floor tiles were 256 px = one 2 m sector, so every material repeated every 2 m and the
ground showed a grid. Here each material is one seamless image covering n x n sectors
(2048 px = 16 sectors = 32 m, or 1024 px = 8 sectors = 16 m); every sector takes its own 256 px
square, chosen by its world position, so neighbouring sectors continue the same picture.

Writes build/textures/coda_atlas4.png ... coda_atlas8.png + .json with a "macro" section:
  macro[name] = [x0, y0, size_px]   (texture index = position in episode.load_atlases)
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gen_textures import FS, OUT, noise

PX_M = 128


def fbm(n, scale_px, octaves, seed):
    return noise(n, n, scale_px, octaves, seed)


def ridged(n, scale_px, octaves, seed):
    """Cracks / veins: thin dark lines where the noise crosses 0.5."""
    v = fbm(n, scale_px, octaves, seed)
    return 1.0 - np.clip(np.abs(v - 0.5) * 18.0, 0, 1)


def colorize(stops, t):
    """Piecewise-linear colour ramp; stops = [(t, (r, g, b)), ...]."""
    ts = np.array([s[0] for s in stops])
    cs = np.array([s[1] for s in stops], dtype=np.float64)
    out = np.empty(t.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(t, ts, cs[:, c])
    return out


def soft(v, th, w=0.07):
    """Soft threshold: 0 below th, 1 above th + w (smooth patch edges instead of hard blobs)."""
    t = np.clip((v - th) / w, 0, 1)
    return (t * t * (3 - 2 * t))[..., None]


def mix(img, m, color, amount):
    return img * (1 - m * amount) + np.array(color, dtype=np.float64) * (m * amount)


def speckle(n, density, seed):
    return np.random.default_rng(seed).random((n, n)) > 1.0 - density


def stamp_wrapped(draw, n, x, y, rx, ry, fill):
    """Ellipse drawn with wrap-around so the image stays seamless."""
    for dx in (-n, 0, n):
        for dy in (-n, 0, n):
            cx, cy = x + dx, y + dy
            if -rx <= cx <= n + rx and -ry <= cy <= n + ry:
                draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill)


def blades(n, count, seed, color, length=(6, 14)):
    """Short dry grass strokes, seamless."""
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = r.random() * n, r.random() * n
        a = r.uniform(-0.6, 0.6) - np.pi / 2
        L = r.uniform(*length)
        c = tuple(int(v * r.uniform(0.75, 1.2)) for v in color) + (int(r.uniform(90, 200)),)
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                d.line([(x + dx, y + dy), (x + dx + np.cos(a) * L * 0.3, y + dy + np.sin(a) * L)], fill=c, width=1)
    return im


def over(base, layer):
    a = np.asarray(layer, dtype=np.float64) / 255.0
    return base * (1 - a[..., 3:4]) + a[..., :3] * 255.0 * a[..., 3:4]


def ground(kind, n, seed):
    big = fbm(n, 900, 3, seed)            # ~7 m blotches
    mid = fbm(n, 180, 4, seed + 1)        # ~1.5 m
    fine = fbm(n, 24, 3, seed + 2)        # ~20 cm
    if kind == "erba_secca":
        t = 0.55 * big + 0.3 * mid + 0.15 * fine
        img = colorize([(0.0, (118, 104, 66)), (0.35, (152, 132, 84)), (0.6, (176, 154, 100)), (1.0, (196, 178, 128))], t)
        img = mix(img, soft(fbm(n, 300, 4, seed + 3) * 0.7 + mid * 0.3, 0.56, 0.12), (104, 112, 66), 0.4)
        img = mix(img, soft(fbm(n, 400, 4, seed + 4) * 0.8 + fine * 0.2, 0.64, 0.1), (130, 104, 78), 0.55)
        img = over(img, blades(n, n * n // 70, seed + 5, (120, 100, 60)))
        img = over(img, blades(n, n * n // 160, seed + 6, (214, 196, 140)))
    elif kind == "macchia":
        t = 0.5 * big + 0.35 * mid + 0.15 * fine
        img = colorize([(0.0, (70, 78, 44)), (0.5, (98, 104, 62)), (1.0, (140, 134, 86))], t)
        img = mix(img, soft(fbm(n, 350, 4, seed + 3) * 0.75 + fine * 0.25, 0.52, 0.12), (150, 128, 88), 0.6)
        img *= 1 - 0.4 * soft(fbm(n, 90, 4, seed + 4) * 0.7 + fine * 0.3, 0.6, 0.06)
        img = over(img, blades(n, n * n // 120, seed + 5, (78, 90, 48), (5, 10)))
    elif kind == "roccia":
        t = 0.45 * big + 0.35 * mid + 0.2 * fine
        img = colorize([(0.0, (96, 90, 82)), (0.5, (134, 124, 108)), (1.0, (172, 162, 146))], t)
        cr = ridged(n, 260, 4, seed + 3) * 0.6 + ridged(n, 70, 3, seed + 4) * 0.4
        img *= (1.0 - 0.45 * cr)[..., None]
        lichen = (fbm(n, 60, 3, seed + 5) > 0.7) & (big > 0.45)
        img[lichen] = img[lichen] * 0.6 + np.array([150, 150, 110]) * 0.4
        veg = (fbm(n, 220, 4, seed + 6) > 0.7) & (mid > 0.5)
        img[veg] = img[veg] * 0.5 + np.array([88, 96, 56]) * 0.5
    elif kind == "uliveto":
        t = 0.5 * big + 0.3 * mid + 0.2 * fine
        img = colorize([(0.0, (118, 92, 66)), (0.5, (148, 122, 88)), (1.0, (176, 152, 112))], t)
        y = np.arange(n)[:, None] * np.ones((1, n))
        furrow = 0.5 + 0.5 * np.sin(y / n * 2 * np.pi * 24 + mid * 3)   # 24 furrows per tile, seamless
        img *= (0.9 + 0.1 * furrow)[..., None]
        img = mix(img, soft(fbm(n, 260, 4, seed + 3) * 0.7 + fine * 0.3, 0.56, 0.1), (120, 124, 74), 0.5)
        img = over(img, blades(n, n * n // 200, seed + 4, (132, 120, 70)))
    elif kind == "terra":
        t = 0.5 * big + 0.3 * mid + 0.2 * fine
        img = colorize([(0.0, (102, 80, 60)), (0.5, (134, 106, 80)), (1.0, (164, 138, 108))], t)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(seed + 3)
        for _ in range(n * n // 900):
            g = int(r.uniform(130, 190))
            stamp_wrapped(d, n, r.random() * n, r.random() * n, r.uniform(1.5, 4), r.uniform(1.2, 3), (g, g - 8, g - 18))
        img = np.asarray(im, dtype=np.float64)
    elif kind == "sabbia":
        t = 0.45 * big + 0.35 * mid + 0.2 * fine
        img = colorize([(0.0, (158, 144, 120)), (0.5, (184, 170, 144)), (1.0, (206, 194, 168))], t)
        y = np.arange(n)[:, None] * np.ones((1, n))
        x = np.ones((n, 1)) * np.arange(n)[None, :]
        ripple = np.sin((y + 40 * np.sin(x / n * 2 * np.pi * 2)) / n * 2 * np.pi * 60 + big * 6)
        img *= (0.95 + 0.05 * ripple)[..., None]
        img[speckle(n, 0.04, seed + 4)] *= 0.8
    elif kind == "ciottoli":
        img = colorize([(0.0, (120, 116, 108)), (1.0, (160, 154, 144))], 0.6 * big + 0.4 * mid)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(seed + 3)
        for _ in range(n * n // 260):
            g = int(r.uniform(120, 215))
            tint = r.uniform(-12, 12)
            stamp_wrapped(d, n, r.random() * n, r.random() * n, r.uniform(4, 11), r.uniform(3, 8),
                          (int(g + tint), g, int(g - tint * 0.5)))
        im = im.filter(ImageFilter.SMOOTH)
        img = np.asarray(im, dtype=np.float64)
    elif kind == "asfalto":
        t = 0.35 * big + 0.25 * mid + 0.4 * np.random.default_rng(seed + 3).random((n, n))
        img = colorize([(0.0, (70, 70, 72)), (0.5, (90, 90, 92)), (1.0, (112, 112, 114))], t)
        cr = ridged(n, 300, 4, seed + 4)
        img *= (1.0 - 0.35 * cr * (big > 0.55))[..., None]
        img *= 1 - 0.15 * soft(fbm(n, 250, 3, seed + 5), 0.66, 0.1)
    else:
        raise ValueError(kind)
    return np.clip(img, 0, 255)


# (material, size px, footstep type). 2048 = 32 m period, 1024 = 16 m.
MACRO = [("erba_secca", 2048, "grass"), ("macchia", 2048, "grass"), ("roccia", 2048, "stone"),
         ("uliveto", 2048, "grass"), ("terra", 1024, "mud"), ("sabbia", 1024, "sand"),
         ("ciottoli", 1024, "gravel"), ("asfalto", 1024, "concrete")]
FIRST_INDEX = 3   # atlases 0..2 are coda_atlas, coda_atlas2, coda_atlas3


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = []   # list of (image, regions)
    small = []
    for k, (name, size, fs) in enumerate(MACRO):
        img = ground(name, size, 500 + 17 * k)
        if size == 2048:
            pages.append((img, {name: [0, 0, 2048, fs]}))
        else:
            small.append((name, img, fs))
    page = np.zeros((2048, 2048, 3))
    regs = {}
    for i, (name, img, fs) in enumerate(small):
        x0, y0 = (i % 2) * 1024, (i // 2) * 1024
        page[y0:y0 + 1024, x0:x0 + 1024] = img
        regs[name] = [x0, y0, 1024, fs]
    pages.append((page, regs))
    for p, (img, regs) in enumerate(pages):
        idx = FIRST_INDEX + p
        foot = np.full((32, 32), FS["stone"], dtype=int)
        for name, (x0, y0, size, fs) in regs.items():
            foot[y0 // 64:(y0 + size) // 64, x0 // 64:(x0 + size) // 64] = FS[fs]
        meta = {"px_per_m": PX_M, "size": 2048, "columns": {}, "tiles": {},
                "macro": {name: v[:3] for name, v in regs.items()}, "footsteps_64px": foot.tolist()}
        base = os.path.join(OUT, "coda_atlas%d" % (idx + 1))
        Image.fromarray(img.astype(np.uint8)).save(base + ".png", optimize=True)
        with open(base + ".json", "w") as f:
            json.dump(meta, f)
        print(base + ".png", list(regs))




def rock_faces(seed=900):
    """Seamless 16 m x 16 m rock face (2048 px): 8 columns of 2 m, continuous from one to the next.

    Used for cliffs (terraced steep terrain): column = world position along the wall, so a long
    cliff shows one continuous rock face that repeats only every 16 m.
    """
    n = 2048
    big = fbm(n, 700, 3, seed)
    mid = fbm(n, 160, 4, seed + 1)
    fine = fbm(n, 20, 3, seed + 2)
    t = 0.45 * big + 0.35 * mid + 0.2 * fine
    img = colorize([(0.0, (84, 78, 70)), (0.45, (122, 112, 98)), (0.75, (150, 140, 124)), (1.0, (178, 168, 150))], t)
    # Bedding planes, wavy and broken (not straight bricks).
    y = np.arange(n)[:, None] * np.ones((1, n))
    bed = np.sin((y + 90 * (big - 0.5) * 4 + 30 * mid) / n * 2 * np.pi * 9)
    img *= (1.0 - 0.18 * soft(bed * (mid > 0.45), 0.85, 0.1))
    # Vertical joints and fractures.
    cr = ridged(n, 300, 4, seed + 3) * 0.7 + ridged(n, 90, 3, seed + 4) * 0.3
    img *= (1.0 - 0.5 * cr)[..., None]
    # Light lichen on top faces and dark wet streaks.
    img = mix(img, soft(fbm(n, 80, 3, seed + 5), 0.66, 0.08), (168, 168, 132), 0.18)
    streak = fbm(n, 400, 3, seed + 6)
    x = np.ones((n, 1)) * np.arange(n)[None, :]
    vstreak = 0.5 + 0.5 * np.sin(x / n * 2 * np.pi * 23 + streak * 8)
    img *= (1.0 - 0.12 * soft(vstreak[..., None][..., 0] * streak, 0.45, 0.2))
    # Plants in cracks.
    img = mix(img, soft(fbm(n, 140, 4, seed + 7) * 0.6 + cr * 0.4, 0.62, 0.06), (82, 92, 54), 0.6)
    return np.clip(img, 0, 255)


def main_rock():
    img = rock_faces()
    idx = FIRST_INDEX + 5   # coda_atlas9
    cols = {"roccia_faccia_%d" % i: [i * 256, 0, (i + 1) * 256, 2048] for i in range(8)}
    meta = {"px_per_m": PX_M, "size": 2048, "columns": cols, "tiles": {}, "macro": {},
            "footsteps_64px": np.full((32, 32), FS["stone"], dtype=int).tolist()}
    base = os.path.join(OUT, "coda_atlas%d" % (idx + 1))
    Image.fromarray(img.astype(np.uint8)).save(base + ".png", optimize=True)
    with open(base + ".json", "w") as f:
        json.dump(meta, f)
    print(base + ".png")


if __name__ == "__main__":
    main()
    main_rock()
