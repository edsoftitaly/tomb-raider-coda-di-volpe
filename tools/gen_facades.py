"""Facade columns for the Via Amodeo buildings (coda_atlas10, coda_atlas11): 2 m x 16 m strips at 128 px/m.

Each column is one vertical slice of a real facade, bottom = street level, drawn after Street View
(31/10/2026): Ed's house (cream, brown base band, green shutters, art deco door, long balcony, set-back
top floor), the narrow pink house, the cream house with terracotta balconies, the white corner house,
the pizzeria-rosticceria with its red front, and plain side walls. Procedural drawing only.

Storey lines (metres above the street): ground 0-3.3, first 3.3-6.3, second 6.3-9.5.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

from gen_ground import FS, OUT, fbm

PX = 128
W, H = 256, 2048
CREAM, PINK, WHITE, BEIGE = (226, 212, 176), (218, 160, 148), (232, 230, 222), (214, 196, 160)
GREEN, BROWN_SH, TERRACOTTA = (58, 98, 70), (120, 84, 56), (196, 112, 78)


def y(m):
    """metres above the street -> image row."""
    return int(round(H - 1 - m * PX))


def plaster(color, seed, dirt=True):
    base = np.ones((H, W, 3)) * np.array(color, float)
    noise = fbm(H, 60, 4, seed)[:H, :W]
    img = base * (0.94 + 0.1 * noise[..., None])
    if dirt:   # grime: darker near the ground and under the sills
        g = np.clip(1 - (np.arange(H)[::-1] / (PX * 1.2)), 0, 1)[:, None, None]
        img *= 1 - 0.12 * g
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def realism(im, p0, seed):
    """Weathering and depth pass over a drawn column: p0 = the bare plaster before the details.

    Detail mask (frames, shutters, glass, cornices) -> soft drop shadow down-right on the plaster (light
    from the upper left, like the street lamps and the moon), an inner shadow under the top edge of the
    openings, rain streaks under every sill and cornice, faint glass reflections, cracks, and grain.
    """
    from scipy import ndimage
    rng = np.random.default_rng(seed)
    a = np.asarray(im).astype(float)
    b = np.asarray(p0).astype(float)
    mask = (np.abs(a - b).sum(axis=2) > 12)
    # 1) drop shadow of every relief element on the wall
    sh = np.zeros(mask.shape)
    sh[6:, 5:] = mask[:-6, :-5]
    sh = ndimage.gaussian_filter(sh, 3.0) * (~mask)
    a *= (1 - 0.32 * sh)[..., None]
    # 2) inner shadow at the top of openings (reveals): element pixels with an element-free row above
    dark = (a.mean(axis=2) < 110) & mask
    top_edge = dark & ~np.roll(dark, 1, axis=0)
    reveal = ndimage.gaussian_filter(ndimage.binary_dilation(top_edge, structure=np.ones((14, 1)), origin=(-6, 0)).astype(float), 2.0)
    a *= (1 - 0.35 * reveal * dark)[..., None]
    # 3) rain streaks below the bottom edges of light elements (sills, cornices)
    bottom = mask & ~np.roll(mask, -1, axis=0)
    streak = np.zeros(mask.shape)
    cols = np.nonzero(bottom.any(axis=0))[0]
    for x in cols:
        for y0 in np.nonzero(bottom[:, x])[0]:
            if rng.random() < 0.10:
                n = int(rng.integers(20, 90))
                streak[y0 + 1:y0 + 1 + n, x] += np.linspace(1, 0, len(streak[y0 + 1:y0 + 1 + n, x]))
    streak = ndimage.gaussian_filter(streak, (6, 1.6)) * (~mask)
    a *= (1 - 0.3 * np.clip(streak, 0, 1))[..., None]
    # 4) glass: a cool diagonal reflection on the dark panes
    glass = mask & (np.abs(a[..., 2] - a[..., 0]) > 12) & (a.mean(axis=2) < 90)
    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
    refl = 0.5 + 0.5 * np.sin((xx + yy * 0.7) / 23.0)
    a[glass] += (np.array([28, 34, 44]) * refl[glass][:, None])
    # 5) a few hairline cracks in the plaster
    for _ in range(int(rng.integers(2, 5))):
        x, y_ = float(rng.integers(10, mask.shape[1] - 10)), float(rng.integers(200, mask.shape[0] - 200))
        ang = rng.uniform(math.pi * 0.35, math.pi * 0.65)
        for _ in range(int(rng.integers(40, 140))):
            ang += rng.normal(0, 0.35)
            x += math.cos(ang) * 1.6
            y_ += math.sin(ang) * 1.6
            xi, yi = int(x), int(y_)
            if 0 <= xi < mask.shape[1] and 0 <= yi < mask.shape[0] and not mask[yi, xi]:
                a[yi, xi] *= 0.72
    # 6) broad weathering + grain
    weather = fbm(mask.shape[0], 140, 3, seed + 7)[:mask.shape[0], :mask.shape[1]]
    a *= (0.97 + 0.05 * weather)[..., None]
    a *= rng.normal(1.0, 0.025, mask.shape)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def band(d, m0, m1, color):
    d.rectangle([0, y(m1), W, y(m0)], fill=color)


def cornice(d, m, color=(236, 232, 222), h=0.18):
    d.rectangle([0, y(m + h), W, y(m)], fill=color)
    d.line([(0, y(m) + 1), (W, y(m) + 1)], fill=(150, 140, 120), width=3)


def shutter_panel(d, x0, x1, top, bot, color, slats=True):
    d.rectangle([x0, top, x1, bot], fill=color)
    if slats:
        dark = tuple(int(c * 0.72) for c in color)
        for yy in range(top + 6, bot - 4, 9):
            d.line([(x0 + 4, yy), (x1 - 4, yy + 2)], fill=dark, width=2)
    d.rectangle([x0, top, x1, bot], outline=tuple(int(c * 0.6) for c in color), width=2)


def window(d, m0, m1, shutters=GREEN, open_=True, frame=(236, 232, 222), width=1.2, sill=True, glass=(40, 50, 66)):
    """Window centred in the column, from m0 to m1 metres."""
    cx = W // 2
    hw = int(width * PX / 2)
    top, bot = y(m1), y(m0)
    d.rectangle([cx - hw - 10, top - 10, cx + hw + 10, bot], fill=frame)
    if open_:
        d.rectangle([cx - hw, top, cx + hw, bot], fill=glass)
        d.line([(cx, top), (cx, bot)], fill=frame, width=5)
        d.line([(cx - hw, (top + bot) // 2), (cx + hw, (top + bot) // 2)], fill=frame, width=4)
        if shutters:
            sw = hw // 2 + 6
            shutter_panel(d, cx - hw - 12 - sw, cx - hw - 12, top, bot, shutters)
            shutter_panel(d, cx + hw + 12, cx + hw + 12 + sw, top, bot, shutters)
    else:
        shutter_panel(d, cx - hw, cx, top, bot, shutters)
        shutter_panel(d, cx, cx + hw, top, bot, shutters)
    if sill:
        d.rectangle([cx - hw - 18, bot, cx + hw + 18, bot + 12], fill=(206, 202, 192))


def roller_window(d, m0, m1, color=BROWN_SH, frame=(220, 214, 200), width=1.2):
    cx, hw = W // 2, int(width * PX / 2)
    top, bot = y(m1), y(m0)
    d.rectangle([cx - hw - 8, top - 8, cx + hw + 8, bot], fill=frame)
    d.rectangle([cx - hw, top, cx + hw, bot], fill=color)
    for yy in range(top + 4, bot, 7):
        d.line([(cx - hw, yy), (cx + hw, yy)], fill=tuple(int(c * 0.78) for c in color), width=2)
    d.rectangle([cx - hw - 14, bot, cx + hw + 14, bot + 10], fill=(206, 202, 192))


def artdeco_door(d):
    cx, hw = W // 2, int(0.8 * PX)
    top, bot = y(2.9), y(0)
    d.rectangle([cx - hw - 14, top - 14, cx + hw + 14, bot], fill=(214, 206, 186))
    d.rectangle([cx - hw, top, cx + hw, bot], fill=(52, 44, 34))
    d.rectangle([cx - hw + 6, top + 6, cx + hw - 6, top + 60], fill=(74, 88, 96))
    for k in range(-4, 5):
        d.line([(cx, top + 58), (cx + k * 18, top + 10)], fill=(52, 44, 34), width=3)
    for leaf in (0, 1):
        x0 = cx - hw + 8 + leaf * hw
        for r in range(4):
            yy = top + 80 + r * 64
            d.polygon([(x0 + hw // 2 - 4, yy), (x0 + hw - 14, yy + 28), (x0 + hw // 2 - 4, yy + 56), (x0 + 6, yy + 28)],
                      outline=(176, 150, 96), width=3)
            d.ellipse([x0 + hw // 2 - 10, yy + 22, x0 + hw // 2 + 2, yy + 34], fill=(186, 158, 100))
    d.line([(cx, top + 66), (cx, bot)], fill=(30, 24, 18), width=3)


def plain_door(d, color=(236, 236, 230), width=1.1, height=2.4):
    cx, hw = W // 2, int(width * PX / 2)
    top, bot = y(height), y(0)
    d.rectangle([cx - hw - 10, top - 10, cx + hw + 10, bot], fill=(206, 200, 186))
    d.rectangle([cx - hw, top, cx + hw, bot], fill=color)
    d.rectangle([cx - hw + 14, top + 14, cx + hw - 14, top + int(height * PX * 0.55)], fill=(150, 170, 186))
    d.ellipse([cx + hw - 26, (top + bot) // 2, cx + hw - 16, (top + bot) // 2 + 10], fill=(160, 150, 120))


def drainpipe(d, x=40):
    d.rectangle([x, y(9.6), x + 16, y(0)], fill=(150, 96, 58))
    d.rectangle([x + 4, y(9.6), x + 8, y(0)], fill=(190, 130, 84))
    for m in (1.2, 3.6, 6.0, 8.4):
        d.rectangle([x - 8, y(m), x + 24, y(m) + 6], fill=(60, 50, 40))


def base_band(d, color=(110, 84, 62), m=0.65):
    band(d, 0, m, color)
    d.line([(0, y(m)), (W, y(m))], fill=(80, 60, 44), width=3)


def ed_house(kind):
    """Ed's house: cream, brown band, green shutters; long balcony on the 1st floor (French windows), top floor
    set back behind a terrace (only the parapet line shows on this plane)."""
    im = plaster(CREAM, 11)
    d = ImageDraw.Draw(im)
    base_band(d)
    if kind == "porta":
        artdeco_door(d)
    elif kind in ("finestra", "tubo"):
        window(d, 0.95, 2.55)
    cornice(d, 3.2)
    if kind in ("finestra", "porta"):
        window(d, 3.35, 5.75, open_=False, width=1.15, sill=False)
    cornice(d, 6.2)
    if kind in ("finestra", "porta"):
        window(d, 6.9, 8.6, width=1.0)
    cornice(d, 9.35, h=0.25)
    # the drainpipe of the "tubo" column is a climbable static (CASA_PLUVIALE), not painted
    return im


def pink_house(kind):
    im = plaster(PINK, 21)
    d = ImageDraw.Draw(im)
    band(d, 0, 0.4, (176, 120, 110))
    if kind == "porta":
        plain_door(d)
    else:
        roller_window(d, 0.9, 2.5)
    cornice(d, 3.2, color=(240, 236, 230))
    window(d, 3.35, 5.7, shutters=(214, 214, 206), width=1.1, sill=False)
    cornice(d, 6.2, color=(240, 236, 230))
    window(d, 6.8, 8.7, shutters=(214, 214, 206), width=1.0)
    cornice(d, 9.35, color=(240, 236, 230), h=0.25)
    return im


def orange_house(kind):
    im = plaster((226, 214, 186), 31)
    d = ImageDraw.Draw(im)
    band(d, 0, 0.5, (190, 176, 150))
    if kind == "porta":
        plain_door(d, color=(150, 104, 64))
    else:
        roller_window(d, 0.9, 2.5, color=(176, 120, 76))
    cornice(d, 3.2)
    roller_window(d, 3.4, 5.8, color=(196, 128, 80), width=1.0)
    cornice(d, 6.2)
    roller_window(d, 6.8, 8.9, color=(196, 128, 80), width=1.0)
    cornice(d, 9.35, h=0.25)
    return im


def white_corner(kind):
    im = plaster(WHITE, 41)
    d = ImageDraw.Draw(im)
    band(d, 0, 0.5, (196, 192, 180))
    if kind == "porta":
        plain_door(d, color=(96, 70, 50))
    else:
        window(d, 0.9, 2.5)
    cornice(d, 3.3)
    window(d, 4.0, 5.9)
    cornice(d, 6.6, h=0.3)
    return im


def pizzeria(kind):
    im = plaster(BEIGE, 51)
    d = ImageDraw.Draw(im)
    if kind == "vetrina":
        d.rectangle([0, y(3.0), W, y(0)], fill=(176, 40, 36))
        d.rectangle([24, y(2.6), W - 24, y(0.5)], fill=(60, 66, 74))
        for xx in (24 + (W - 48) // 3, 24 + 2 * (W - 48) // 3):
            d.line([(xx, y(2.6)), (xx, y(0.5))], fill=(176, 40, 36), width=6)
        d.rectangle([24, y(0.5), W - 24, y(0)], fill=(140, 30, 28))
    else:
        d.rectangle([0, y(3.0), W, y(0)], fill=(176, 40, 36))
        plain_door(d, color=(70, 70, 76), width=1.2, height=2.5)
    cornice(d, 3.2)
    window(d, 3.6, 5.8, shutters=(150, 96, 60), width=1.0, sill=False)
    cornice(d, 6.3, h=0.3)
    return im


GENERIC = {
    # name: (plaster, shutter kind, shutter colour, base band colour)
    "ocra": ((214, 178, 120), "roller", (150, 110, 70), (160, 130, 96)),
    "bianca": ((232, 230, 222), "shutter", (58, 98, 70), (190, 186, 176)),
    "grigia": ((196, 192, 186), "roller", (210, 206, 196), (150, 146, 140)),
    "crema": ((228, 214, 182), "shutter", (110, 70, 44), (176, 150, 116)),
}


def generic(variant, ground):
    """Ordinary 1960s-80s palazzina of the town: five storeys of 3.1 m, windows with roller blinds or
    shutters, concrete balcony slabs every other column, ground floor door / window / garage."""
    plaster_c, kind, sh, band_c = GENERIC[variant]
    im = plaster(plaster_c, 70 + len(variant))
    d = ImageDraw.Draw(im)
    band(d, 0, 0.6, band_c)
    if ground == "porta":
        plain_door(d, color=(120, 90, 60) if variant != "bianca" else (70, 60, 50), height=2.5)
    elif ground == "garage":
        cx, hw = W // 2, int(1.0 * PX)
        d.rectangle([cx - hw, y(2.6), cx + hw, y(0)], fill=(150, 150, 146))
        for yy in range(y(2.6) + 4, y(0), 8):
            d.line([(cx - hw, yy), (cx + hw, yy)], fill=(110, 110, 108), width=3)
    else:
        if kind == "roller":
            roller_window(d, 0.9, 2.5, color=sh, width=1.1)
        else:
            window(d, 0.9, 2.5, shutters=sh, width=1.1)
    for k in range(1, 5):
        base = 3.1 * k
        cornice(d, base - 0.1, color=tuple(min(255, c + 14) for c in plaster_c), h=0.12)
        if kind == "roller":
            roller_window(d, base + 0.8, base + 2.4, color=sh, width=1.1)
        else:
            window(d, base + 0.8, base + 2.4, shutters=sh, width=1.0, open_=(k % 2 == 1))
    cornice(d, 15.6, h=0.3)
    return im


def plain_side(color, seed):
    im = plaster(color, seed)
    d = ImageDraw.Draw(im)
    for m in (3.2, 6.2, 9.35):
        cornice(d, m, color=tuple(min(255, c + 12) for c in color), h=0.12)
    return im


def _real(fn, seed):
    """Run a builder with realism(): plaster() is recorded so the pass knows the bare wall."""
    def build():
        global plaster
        orig = plaster
        rec = {}

        def rec_plaster(color, seed_, dirt=True):
            im = orig(color, seed_, dirt)
            rec["p0"] = im.copy()
            return im
        plaster = rec_plaster
        try:
            im = fn()
        finally:
            plaster = orig
        return realism(im, rec["p0"], seed)
    return build


COLUMNS_RAW = [
    ("fac_casa_finestra", lambda: ed_house("finestra")), ("fac_casa_porta", lambda: ed_house("porta")),
    ("fac_casa_piena", lambda: ed_house("piena")), ("fac_casa_tubo", lambda: ed_house("tubo")),
    ("fac_rosa_porta", lambda: pink_house("porta")), ("fac_rosa_finestra", lambda: pink_house("finestra")),
    ("fac_arancio_porta", lambda: orange_house("porta")), ("fac_arancio_finestra", lambda: orange_house("finestra")),
    ("fac_bianco_porta", lambda: white_corner("porta")), ("fac_bianco_finestra", lambda: white_corner("finestra")),
    ("fac_pizzeria_vetrina", lambda: pizzeria("vetrina")), ("fac_pizzeria_porta", lambda: pizzeria("porta")),
    ("fac_lato_crema", lambda: plain_side(CREAM, 61)), ("fac_lato_rosa", lambda: plain_side(PINK, 62)),
    ("fac_lato_beige", lambda: plain_side(BEIGE, 63)), ("fac_lato_bianco", lambda: plain_side(WHITE, 64)),
]
COLUMNS_RAW += [("fac_gen_%s_%s" % (v, g), (lambda v=v, g=g: generic(v, g)))
                for v in ("ocra", "bianca", "grigia", "crema") for g in ("finestra", "porta")]
COLUMNS = [(n, _real(f, 100 + i)) for i, (n, f) in enumerate(COLUMNS_RAW)]


def main(first_index=9):
    """Writes coda_atlas10/11/12.png (atlas list indices 9, 10, 11)."""
    pages = [COLUMNS[:8], COLUMNS[8:16], COLUMNS[16:24]]
    for p, cols in enumerate(pages):
        img = Image.new("RGB", (2048, 2048), (0, 0, 0))
        meta_cols = {}
        for i, (name, fn) in enumerate(cols):
            img.paste(fn(), (i * W, 0))
            meta_cols[name] = [i * W, 0, (i + 1) * W, H]
        meta = {"px_per_m": PX, "size": 2048, "columns": meta_cols, "tiles": {}, "macro": {},
                "footsteps_64px": np.full((32, 32), FS["stone"], dtype=int).tolist()}
        base = os.path.join(OUT, "coda_atlas%d" % (first_index + 1 + p))
        img.save(base + ".png", optimize=True)
        with open(base + ".json", "w") as f:
            json.dump(meta, f)
        print(base + ".png")


if __name__ == "__main__":
    main()
