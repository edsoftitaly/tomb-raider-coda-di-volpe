"""Procedural texture atlas for Coda di Volpe (2048 x 2048, 128 px per metre).

Layout (columns of 256 px = one 2 m sector wide):
  col 0..5   facades and vertical surfaces, 2048 px tall = 16 m, bottom = ground level
  col 6..7   floor tiles 256 x 256 (16 tiles)
Colours are taken from Ed's photos of Oliveri and Street View references.
Writes build/textures/coda_atlas.png and build/textures/coda_atlas.json (regions + footsteps).
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "textures")
PX_M = 128
S = 2048
COL = 256
rng = np.random.default_rng(1991)

# Footstep types (TombLib TextureFootStep.Type)
FS = {"mud": 0, "sand": 2, "gravel": 3, "stone": 6, "grass": 10, "concrete": 11, "marble": 9}


def noise(h, w, scale, octaves=4, seed=None):
    """Tileable value noise in [0, 1]."""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale * 2 ** o)), max(2, int(w / scale * 2 ** o))
        g = r.random((gh, gw))
        g = np.pad(g, 2, mode="wrap")
        im = Image.fromarray((g * 255).astype(np.uint8)).resize(((gw + 4) * w // gw, (gh + 4) * h // gh), Image.BICUBIC)
        a = np.asarray(im, dtype=np.float64) / 255.0
        oy, ox = 2 * h // gh, 2 * w // gw
        out += amp * a[oy:oy + h, ox:ox + w]
        tot += amp
        amp *= 0.5
    return out / tot


def tint(base, n, amount):
    base = np.array(base, dtype=np.float64)
    return np.clip(base[None, None, :] * (1.0 + (n[..., None] - 0.5) * amount), 0, 255)


def plaster(h, w, color, seed):
    n = noise(h, w, 64, 5, seed) * 0.7 + noise(h, w, 8, 2, seed + 1) * 0.3
    img = tint(color, n, 0.22)
    # Weathering streaks below sills and at the base.
    streak = noise(h, w, 256, 3, seed + 2)
    img *= (0.93 + 0.07 * streak)[..., None]
    return img


def rect(img, x0, y0, x1, y1, color):
    img[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = color


def shutters(img, x0, y0, w, h, color, slats=True):
    rect(img, x0 - 4, y0 - 6, x0 + w + 4, y0, (200, 195, 185))            # lintel
    rect(img, x0 - 6, y0 + h, x0 + w + 6, y0 + h + 8, (205, 200, 190))    # sill
    rect(img, x0, y0, x0 + w, y0 + h, np.array(color) * 0.75)
    half = w // 2
    for sx in (x0, x0 + half):
        rect(img, sx + 2, y0 + 2, sx + half - 2, y0 + h - 2, color)
        if slats:
            for yy in range(y0 + 6, y0 + h - 4, 7):
                rect(img, sx + 4, yy, sx + half - 4, yy + 2, np.array(color) * 0.62)


def railing(img, x0, x1, y_floor, color=(25, 28, 26)):
    rect(img, x0, y_floor - 3, x1, y_floor + 10, (190, 185, 175))         # balcony slab edge
    top = y_floor - int(1.0 * PX_M)
    rect(img, x0, top, x1, top + 4, color)
    for xx in range(x0 + 4, x1 - 2, 12):
        rect(img, xx, top, xx + 3, y_floor - 3, color)


def facade(style, windows, seed):
    """One 256 x 2048 column. Storeys every 3.2 m from the bottom."""
    st = {
        "crema": dict(wall=(214, 198, 168), band=(122, 88, 64), shut=(46, 84, 62)),
        "rosa": dict(wall=(222, 170, 158), band=(150, 140, 132), shut=(120, 82, 58)),
        "bianco": dict(wall=(228, 222, 206), band=(160, 150, 135), shut=(52, 74, 92)),
    }[style]
    img = plaster(S, COL, st["wall"], seed)
    storey = int(3.2 * PX_M)
    # Base plinth and brown band, as on the house in Via Amodeo.
    rect(img, 0, S - int(0.45 * PX_M), COL, S, np.array(st["band"]) * 0.9)
    rect(img, 0, S - int(0.62 * PX_M), COL, S - int(0.55 * PX_M), st["band"])
    for k in range(0, 5):
        floor_y = S - k * storey                       # pixel row of this storey's floor
        if windows:
            w, h = int(1.05 * PX_M), int(1.45 * PX_M)
            x0 = (COL - w) // 2
            y0 = floor_y - int(0.95 * PX_M) - h
            if k == 0:
                y0 = floor_y - int(2.3 * PX_M)
                h = int(2.15 * PX_M) - int(0.15 * PX_M)
            shutters(img, x0, y0, w, h, st["shut"])
            if k >= 1:
                railing(img, 0, COL, floor_y)
        else:
            # String course between storeys.
            if k >= 1:
                rect(img, 0, floor_y - 4, COL, floor_y + 4, np.array(st["wall"]) * 0.9)
    # Roof parapet line every storey top is covered by the cut; add drip stains.
    stains = noise(S, COL, 32, 3, seed + 9)
    img *= (1.0 - 0.08 * (stains > 0.7))[..., None]
    return img


def stone_wall(seed, color=(150, 132, 108)):
    img = np.zeros((S, COL, 3))
    n = noise(S, COL, 32, 4, seed)
    img[:] = tint(color, n, 0.35)
    im = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    y = 0
    while y < S:
        hh = int(r.integers(26, 48))
        x = -int(r.integers(0, 40))
        while x < COL:
            ww = int(r.integers(36, 90))
            shade = int(r.integers(-28, 22))
            c = tuple(int(np.clip(v + shade, 0, 255)) for v in color)
            d.rectangle([x + 2, y + 2, x + ww - 2, y + hh - 2], fill=c)
            x += ww
        y += hh
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64)
    a *= (0.85 + 0.3 * noise(S, COL, 16, 3, seed + 3))[..., None]
    return np.clip(a, 0, 255)


def rock(seed, color=(128, 118, 104)):
    n = noise(S, COL, 96, 6, seed)
    strata = (np.sin(np.linspace(0, 60, S))[:, None] * 0.5 + 0.5) * 0.25
    img = tint(color, n * 0.8 + strata, 0.6)
    veg = noise(S, COL, 48, 4, seed + 5) > 0.68
    img[veg] = img[veg] * 0.45 + np.array([70, 85, 45]) * 0.55
    return img


def tile(kind, seed):
    T = 256
    if kind == "asfalto":
        img = tint((88, 88, 90), noise(T, T, 16, 4, seed) * 0.6 + rng.random((T, T)) * 0.4, 0.35)
    elif kind == "marciapiede":
        # Grey square tiles 20 cm with dark joints, as in Ed's photo.
        img = tint((150, 140, 132), noise(T, T, 64, 4, seed), 0.25)
        step = int(0.2 * PX_M)
        for i in range(0, T, step):
            img[i:i + 2, :] *= 0.62
            img[:, i:i + 2] *= 0.62
    elif kind == "lastricato":
        img = tint((168, 160, 146), noise(T, T, 32, 4, seed), 0.3)
        for i in range(0, T, 64):
            img[i:i + 3, :] *= 0.6
        for j in range(0, T, 32):
            off = 32 if (j // 32) % 2 else 0
            for i in range(0, T, 64):
                img[i:i + 64, (j + off) % T:(j + off) % T + 3] *= 0.6
    elif kind == "erba_secca":
        n = noise(T, T, 24, 5, seed)
        img = tint((168, 146, 92), n, 0.5)
        blades = rng.random((T, T)) > 0.86
        img[blades] *= 0.7
        green = noise(T, T, 64, 3, seed + 1) > 0.62
        img[green] = img[green] * 0.6 + np.array([92, 110, 60]) * 0.4
    elif kind == "terra":
        img = tint((132, 104, 78), noise(T, T, 32, 5, seed), 0.45)
        pebbles = rng.random((T, T)) > 0.985
        img[pebbles] = [170, 160, 145]
    elif kind == "roccia":
        img = tint((134, 124, 108), noise(T, T, 48, 6, seed), 0.6)
    elif kind == "terrazza":
        img = tint((176, 168, 156), noise(T, T, 48, 4, seed), 0.2)
        for i in range(0, T, 64):
            img[i:i + 2, :] *= 0.75
            img[:, i:i + 2] *= 0.75
    elif kind == "ciottoli":
        img = tint((150, 146, 140), noise(T, T, 8, 3, seed), 0.5)
    elif kind == "macchia":
        n = noise(T, T, 20, 5, seed)
        img = tint((96, 104, 62), n, 0.7)
        dry = noise(T, T, 48, 3, seed + 2) > 0.55
        img[dry] = img[dry] * 0.5 + np.array([160, 138, 90]) * 0.5
    elif kind == "uliveto":
        img = tint((150, 128, 90), noise(T, T, 32, 5, seed), 0.45)
        green = noise(T, T, 40, 4, seed + 4) > 0.6
        img[green] = img[green] * 0.5 + np.array([108, 118, 76]) * 0.5
    elif kind == "sabbia":
        img = tint((178, 164, 140), noise(T, T, 16, 4, seed) * 0.5 + rng.random((T, T)) * 0.5, 0.3)
    elif kind == "rosa_piena":
        img = plaster(T, T, (222, 170, 158), seed)
    elif kind == "bianco_piena":
        img = plaster(T, T, (228, 222, 206), seed)
    elif kind == "castello_pav":
        img = tint((150, 136, 112), noise(T, T, 24, 5, seed), 0.45)
    else:
        img = np.full((T, T, 3), 128.0)
    return img


FACADES = [("crema_finestre", lambda: facade("crema", True, 11)),
           ("crema_piena", lambda: facade("crema", False, 12)),
           ("rosa_finestre", lambda: facade("rosa", True, 13)),
           ("bianco_finestre", lambda: facade("bianco", True, 14)),
           ("pietra_castello", lambda: stone_wall(15)),
           ("roccia_parete", lambda: rock(16))]
TILES = [("asfalto", "concrete"), ("marciapiede", "stone"), ("lastricato", "stone"), ("erba_secca", "grass"),
         ("terra", "mud"), ("roccia", "stone"), ("terrazza", "concrete"), ("ciottoli", "gravel"),
         ("macchia", "grass"), ("uliveto", "grass"), ("sabbia", "sand"), ("castello_pav", "stone"),
         ("asfalto2", "concrete"), ("erba_secca2", "grass"), ("rosa_piena", "stone"), ("bianco_piena", "stone")]


def main():
    os.makedirs(OUT, exist_ok=True)
    atlas = np.zeros((S, S, 3))
    regions = {"px_per_m": PX_M, "size": S, "columns": {}, "tiles": {}}
    footsteps = np.full((S // 64, S // 64), FS["stone"], dtype=int)
    for i, (name, fn) in enumerate(FACADES):
        atlas[:, i * COL:(i + 1) * COL] = fn()
        regions["columns"][name] = [i * COL, 0, (i + 1) * COL, S]
    for k, (name, fs) in enumerate(TILES):
        cx, cy = 6 * COL + (k % 2) * COL, (k // 2) * COL
        atlas[cy:cy + COL, cx:cx + COL] = tile(name.rstrip("2"), 100 + k)
        regions["tiles"][name] = [cx, cy, cx + COL, cy + COL]
        footsteps[cy // 64:(cy + COL) // 64, cx // 64:(cx + COL) // 64] = FS[fs]
    regions["footsteps_64px"] = footsteps.tolist()
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "coda_atlas.png"))
    with open(os.path.join(OUT, "coda_atlas.json"), "w") as f:
        json.dump(regions, f)
    print("ok", os.path.join(OUT, "coda_atlas.png"))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Atlas 2: interiors, caves, underwater, ruins.

def blocks(seed, color, bw=(60, 140), bh=(40, 70), joint=0.55, rough=0.35, moss=0.0, waterline=None):
    img = np.zeros((S, COL, 3))
    img[:] = tint(color, noise(S, COL, 32, 4, seed), rough)
    r = np.random.default_rng(seed)
    y = 0
    while y < S:
        hh = int(r.integers(*bh))
        x = -int(r.integers(0, bw[0]))
        img[y:y + 3, :] *= joint
        while x < COL:
            ww = int(r.integers(*bw))
            shade = 1.0 + r.uniform(-0.12, 0.10)
            img[y + 3:y + hh, max(0, x + 3):max(0, x + ww)] *= shade
            if 0 <= x < COL:
                img[y:y + hh, x:x + 3] *= joint
            x += ww
        y += hh
    if moss:
        m = noise(S, COL, 24, 4, seed + 7) > (1.0 - moss)
        img[m] = img[m] * 0.5 + np.array([70, 90, 50]) * 0.5
    if waterline is not None:
        y0 = S - int(waterline * PX_M)
        img[y0:, :] *= 0.72
        img[y0:, :, 2] *= 1.05
    return np.clip(img, 0, 255)


def interior_plaster(seed):
    img = plaster(S, COL, (232, 226, 210), seed)
    # Dado: tiled band up to 1.1 m, typical of Sicilian houses.
    h = int(1.1 * PX_M)
    band = tint((176, 150, 120), noise(h, COL, 16, 3, seed + 3), 0.2)
    for i in range(0, COL, 32):
        band[:, i:i + 2] *= 0.7
    for j in range(0, h, 32):
        band[j:j + 2, :] *= 0.7
    img[S - h:] = band
    img[S - h - 6:S - h] = (120, 95, 70)
    return img


def cave_rock(seed, color=(88, 80, 72)):
    n = noise(S, COL, 64, 6, seed)
    img = tint(color, n, 0.8)
    flow = noise(S, COL, 8, 2, seed + 1)
    streaks = (np.sin(np.linspace(0, 300, COL))[None, :] * 0.5 + 0.5) * (flow > 0.55)
    img *= (1.0 - 0.15 * streaks)[..., None]
    wet = noise(S, COL, 32, 3, seed + 2) > 0.7
    img[wet] *= 0.75
    return np.clip(img, 0, 255)


def sea_rock(seed):
    img = cave_rock(seed, (70, 92, 90))
    algae = noise(S, COL, 20, 4, seed + 4) > 0.6
    img[algae] = img[algae] * 0.5 + np.array([60, 100, 60]) * 0.5
    return img


def tile2(kind, seed):
    T = 256
    if kind == "cementine":
        img = np.zeros((T, T, 3))
        base = tint((205, 196, 178), noise(T, T, 32, 3, seed), 0.15)
        img[:] = base
        c = (150, 70, 55)
        for ty in range(0, T, 64):
            for tx in range(0, T, 64):
                yy, xx = np.mgrid[0:64, 0:64]
                d = np.abs(yy - 31.5) + np.abs(xx - 31.5)
                m = (d > 18) & (d < 26)
                img[ty:ty + 64, tx:tx + 64][m] = c
                img[ty:ty + 2, tx:tx + 64] *= 0.8
                img[ty:ty + 64, tx:tx + 2] *= 0.8
    elif kind == "parquet":
        img = tint((150, 105, 65), noise(T, T, 64, 3, seed), 0.25)
        for j in range(0, T, 32):
            img[:, j:j + 2] *= 0.6
            off = (j // 32) % 3 * 50
            for i in range((off % 128), T, 128):
                img[i:i + 2, j:j + 32] *= 0.6
    elif kind == "soffitto":
        img = plaster(T, T, (236, 232, 220), seed)
    elif kind == "grotta_pav":
        img = tint((96, 88, 78), noise(T, T, 24, 6, seed), 0.7)
    elif kind == "sabbia_fondo":
        img = tint((168, 160, 128), noise(T, T, 16, 5, seed), 0.35)
        ripples = (np.sin(np.linspace(0, 40, T))[:, None] * 0.5 + 0.5) * 0.12
        img *= (1.0 - ripples)[..., None]
    elif kind == "posidonia":
        img = tint((60, 96, 60), noise(T, T, 12, 5, seed), 0.8)
    elif kind == "mosaico":
        img = np.zeros((T, T, 3))
        r = np.random.default_rng(seed)
        pal = np.array([[230, 220, 200], [40, 40, 40], [170, 60, 40], [200, 170, 90]])
        for y in range(0, T, 8):
            for x in range(0, T, 8):
                yy, xx = y - 128, x - 128
                ring = int(np.hypot(yy, xx) / 24) % 4
                img[y:y + 7, x:x + 7] = pal[ring] * r.uniform(0.85, 1.05)
    elif kind == "lastre_greche":
        img = tint((178, 160, 128), noise(T, T, 48, 5, seed), 0.35)
        for i in (0, 128):
            img[i:i + 3, :] *= 0.55
        for j in (0, 96, 192):
            img[:, j:j + 3] *= 0.55
    elif kind == "pietra_bagnata":
        img = tint((92, 98, 96), noise(T, T, 32, 5, seed), 0.5)
    elif kind == "grata":
        img = np.full((T, T, 3), (255, 0, 255), dtype=np.float64)  # magenta = transparent
        for i in range(0, T, 32):
            img[i:i + 6, :] = (60, 58, 55)
            img[:, i:i + 6] = (60, 58, 55)
    elif kind == "tavole":
        img = tint((120, 92, 64), noise(T, T, 64, 4, seed), 0.3)
        for j in range(0, T, 40):
            img[:, j:j + 3] *= 0.5
    elif kind == "cemento":
        img = tint((150, 148, 142), noise(T, T, 32, 4, seed), 0.25)
    elif kind == "rete":
        img = np.full((T, T, 3), (255, 0, 255), dtype=np.float64)
        for i in range(0, T, 16):
            img[i:i + 2, :] = (110, 98, 70)
            img[:, i:i + 2] = (110, 98, 70)
    elif kind == "soffitto_roccia":
        img = tint((80, 74, 68), noise(T, T, 32, 6, seed), 0.7)
    elif kind == "muschio":
        img = tint((84, 104, 64), noise(T, T, 16, 5, seed), 0.5)
    elif kind == "intonaco_liscio":
        img = plaster(T, T, (232, 226, 210), seed)
    else:
        img = np.full((T, T, 3), 128.0)
    return img


COLUMNS2 = [("intonaco_interno", lambda: interior_plaster(21)),
            ("pietra_viva", lambda: blocks(22, (140, 124, 100), moss=0.05)),
            ("roccia_grotta", lambda: cave_rock(23)),
            ("canale_saia", lambda: blocks(24, (150, 140, 118), bw=(50, 90), bh=(30, 45), moss=0.12, waterline=0.8)),
            ("opera_greca", lambda: blocks(25, (196, 172, 128), bw=(110, 200), bh=(50, 64), joint=0.6, rough=0.25)),
            ("roccia_mare", lambda: sea_rock(26))]
TILES2 = [("cementine", "marble"), ("parquet", "wood"), ("soffitto", "concrete"), ("grotta_pav", "stone"),
          ("sabbia_fondo", "sand"), ("posidonia", "grass"), ("mosaico", "marble"), ("lastre_greche", "stone"),
          ("pietra_bagnata", "stone"), ("grata", "metal"), ("tavole", "wood"), ("cemento", "concrete"),
          ("rete", "metal"), ("soffitto_roccia", "stone"), ("muschio", "grass"), ("intonaco_liscio", "concrete")]
FS.update({"wood": 7, "metal": 8})


def main2():
    atlas = np.zeros((S, S, 3))
    regions = {"px_per_m": PX_M, "size": S, "columns": {}, "tiles": {}}
    footsteps = np.full((S // 64, S // 64), FS["stone"], dtype=int)
    for i, (name, fn) in enumerate(COLUMNS2):
        atlas[:, i * COL:(i + 1) * COL] = fn()
        regions["columns"][name] = [i * COL, 0, (i + 1) * COL, S]
    for k, (name, fs) in enumerate(TILES2):
        cx, cy = 6 * COL + (k % 2) * COL, (k // 2) * COL
        atlas[cy:cy + COL, cx:cx + COL] = tile2(name, 200 + k)
        regions["tiles"][name] = [cx, cy, cx + COL, cy + COL]
        footsteps[cy // 64:(cy + COL) // 64, cx // 64:(cx + COL) // 64] = FS[fs]
    for name, (x0, y0, x1, y1) in regions["columns"].items():
        footsteps[:, x0 // 64:x1 // 64] = FS["stone"]
    regions["footsteps_64px"] = footsteps.tolist()
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "coda_atlas2.png"))
    with open(os.path.join(OUT, "coda_atlas2.json"), "w") as f:
        json.dump(regions, f)
    print("ok", os.path.join(OUT, "coda_atlas2.png"))


T = COL


# Atlas 3 (1024 x 1024, 16 tiles): water surfaces (additive blend) and gameplay surfaces.
def water(seed, deep, light):
    n = noise(T, T, 32, 5, seed)
    yy, xx = np.mgrid[0:T, 0:T] / T * 2 * np.pi
    caust = (np.sin(xx * 3 + n * 4) * np.sin(yy * 3 - n * 4)) ** 8
    img = np.array(deep, float)[None, None, :] * (0.8 + 0.4 * n[..., None])
    return img + np.array(light, float)[None, None, :] * caust[..., None]


def tile3(kind, seed):
    if kind == "acqua_mare":
        return water(seed, (14, 46, 70), (40, 70, 70))
    if kind == "acqua_laguna":
        return water(seed, (22, 62, 52), (40, 70, 50))
    if kind == "acqua_scura":
        return water(seed, (10, 22, 24), (16, 28, 26))
    if kind == "porta_legno":
        img = tint((96, 62, 36), noise(T, T, 64, 4, seed), 0.3)
        for j in range(0, T, 64):
            img[:, j:j + 4] *= 0.5
        img[20:28, :] *= 0.5
        img[T - 28:T - 20, :] *= 0.5
        return img
    if kind == "ferro":
        img = tint((70, 72, 74), noise(T, T, 24, 5, seed), 0.35)
        for i in range(16, T, 64):
            for j in range(16, T, 64):
                img[i:i + 6, j:j + 6] = (40, 40, 42)
        return img
    if kind == "ruggine":
        return tint((120, 66, 36), noise(T, T, 16, 6, seed), 0.6)
    if kind == "maiolica":
        img = np.zeros((T, T, 3))
        yy, xx = np.mgrid[0:64, 0:64] - 31.5
        r = np.hypot(yy, xx)
        motif = np.where(r < 12, 1, np.where(np.abs(np.abs(yy) - np.abs(xx)) < 4, 2, 0))
        pal = np.array([[236, 230, 212], [210, 160, 40], [40, 80, 150]])
        for y in range(0, T, 64):
            for x in range(0, T, 64):
                img[y:y + 64, x:x + 64] = pal[motif]
                img[y:y + 64, x:x + 2] = img[y:y + 2, x:x + 64] = (150, 150, 140)
        return img
    if kind == "pietra_lavica":
        return tint((62, 60, 58), noise(T, T, 12, 6, seed), 0.45)
    if kind == "stella_dioscuri":
        img = tint((150, 128, 90), noise(T, T, 32, 5, seed), 0.3)
        yy, xx = np.mgrid[0:T, 0:T] - 127.5
        ang = np.arctan2(yy, xx)
        r = np.hypot(yy, xx)
        star = r < 40 + 60 * np.abs(np.cos(4 * ang)) ** 6
        img[star] = img[star] * 0.4 + np.array([210, 170, 60]) * 0.6
        img[(r > 110) & (r < 118)] *= 0.5
        return img
    if kind == "tegole":
        img = tint((168, 84, 52), noise(T, T, 32, 4, seed), 0.3)
        for i in range(0, T, 32):
            img[i:i + 4, :] *= 0.55
        return img
    if kind == "tela":
        return tint((190, 178, 150), noise(T, T, 4, 3, seed), 0.15)
    if kind == "affresco":
        img = plaster(T, T, (200, 160, 120), seed)
        img[: T // 3] = img[: T // 3] * 0.5 + np.array([60, 90, 140]) * 0.5
        return img
    return np.full((T, T, 3), 128.0)


TILES3 = [("acqua_mare", "sand"), ("acqua_laguna", "sand"), ("acqua_scura", "stone"), ("porta_legno", "wood"),
          ("ferro", "metal"), ("ruggine", "metal"), ("maiolica", "marble"), ("pietra_lavica", "stone"),
          ("stella_dioscuri", "stone"), ("tegole", "stone"), ("tela", "concrete"), ("affresco", "concrete")]


def main3():
    S3 = 1024
    atlas = np.zeros((S3, S3, 3))
    regions = {"px_per_m": PX_M, "size": S3, "columns": {}, "tiles": {}}
    footsteps = np.full((S3 // 64, S3 // 64), FS["stone"], dtype=int)
    for k, (name, fs) in enumerate(TILES3):
        cx, cy = (k % 4) * COL, (k // 4) * COL
        atlas[cy:cy + COL, cx:cx + COL] = tile3(name, 300 + k)
        regions["tiles"][name] = [cx, cy, cx + COL, cy + COL]
        footsteps[cy // 64:(cy + COL) // 64, cx // 64:(cx + COL) // 64] = FS[fs]
    regions["footsteps_64px"] = footsteps.tolist()
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "coda_atlas3.png"))
    with open(os.path.join(OUT, "coda_atlas3.json"), "w") as f:
        json.dump(regions, f)
    print("ok", os.path.join(OUT, "coda_atlas3.png"))


if __name__ == "__main__":
    main3()
