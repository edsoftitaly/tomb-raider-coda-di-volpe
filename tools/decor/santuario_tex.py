"""Procedural textures for the Basilica Santuario di Tindari (v2, from Ed's photos and Street View).

Exterior: facade and tower in pink ashlar with white-grey marble pilasters and cornices, gold/blue
mosaics; nave sides in orange plaster with white pilasters, blind arches with blue oculi and
rectangular windows; dome drum orange, dome in golden glazed tiles; convent in beige plaster.
Interior: pink marble columns with white bases and gilded capitals, star/octagon marble floor in the
central aisle, diamond floor in the aisles, red marble dado, mosaic panels, painted vault, stained glass.

Nothing is copied from photographs: every image is drawn here. 2 x 2 m tiles = 256 px (128 px/m).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from decor.tex import noise, rgba

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
PINK = (196, 128, 118)
PINK_LIGHT = (214, 156, 144)
MARBLE = (226, 224, 216)
MARBLE_SHADE = (176, 172, 162)
ORANGE = (214, 128, 72)
GOLD = (214, 172, 70)
BLUE = (44, 86, 160)
BEIGE = (214, 204, 182)


def tex(w, h, base, seed, amount=0.14, scale=24):
    n = noise(h, w, scale, 4, seed) * 0.7 + noise(h, w, 4, 2, seed + 1) * 0.3
    return np.clip(np.array(base, float)[None, None] * (1 + (n[..., None] - 0.5) * amount), 0, 255)


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def from_img(im, alpha=None):
    a = np.asarray(im.convert("RGB"), float)
    return rgba(a) if alpha is None else np.concatenate([a, alpha[..., None]], axis=2)


# ------------------------------------------------------------------------------------ exterior
def ashlar_pink(seed=1):
    """2 x 2 m of pink stone blocks, 25 cm courses, blocks 50-70 cm, thin light joints."""
    r = np.random.default_rng(seed)
    img = tex(256, 256, PINK, seed, 0.10)
    for row in range(8):
        y0 = row * 32
        x = -r.integers(0, 60)
        while x < 256:
            w = int(r.integers(60, 92))
            shade = r.uniform(0.86, 1.12)
            tint = np.array([1.0, r.uniform(0.92, 1.06), r.uniform(0.92, 1.08)])
            a, b = max(0, x), min(256, x + w)
            if a < b:
                img[y0:y0 + 32, a:b] *= shade * tint
                img[y0:y0 + 32, a:a + 2] = (226, 206, 196)
            x += w
        img[y0:y0 + 2] = (226, 206, 196)
    return rgba(np.clip(img, 0, 255))


def marble(seed=2, base=MARBLE, veins=True):
    img = tex(256, 256, base, seed, 0.08, 40)
    if veins:
        v = noise(256, 256, 48, 5, seed + 3)
        line = np.clip(1 - np.abs(v - 0.5) * 30, 0, 1)
        img *= (1 - 0.18 * line)[..., None]
    return rgba(img)


def plaster_orange(seed=3):
    img = tex(256, 256, ORANGE, seed, 0.12, 64)
    stain = noise(256, 256, 96, 3, seed + 1)
    img *= (0.94 + 0.08 * stain)[..., None]
    return rgba(img)


def plaster_beige(seed=4):
    img = tex(256, 256, BEIGE, seed, 0.12, 64)
    return rgba(img)


def stone_fort(seed=5):
    """Old fortified masonry: irregular blocks, grey-beige."""
    r = np.random.default_rng(seed)
    img = tex(256, 256, (184, 174, 156), seed, 0.18, 16)
    im = to_img(img)
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y = r.integers(0, 256), r.integers(0, 256)
        w, h = r.integers(20, 50), r.integers(12, 26)
        c = int(r.uniform(140, 200))
        d.rectangle([x, y, x + w, y + h], outline=(c - 40, c - 44, c - 50))
    return rgba(np.asarray(im, float))


def tiles(seed, color, hi, rows=10, cols=11):
    """Glazed canal tiles in rows (the slope runs along the image's vertical axis)."""
    n = noise(256, 256, 32, 3, seed)
    img = np.zeros((256, 256, 3))
    r = np.random.default_rng(seed)
    rh, cw = 256 / rows, 256 / cols
    for row in range(rows):
        y0 = int(row * rh)
        for col in range(cols + 1):
            x0 = int(col * cw + (cw / 2 if row % 2 else 0) - cw / 2)
            shade = r.uniform(0.86, 1.1)
            for x in range(max(0, x0), min(256, int(x0 + cw))):
                t = (x - x0) / cw
                curve = math.sin(t * math.pi)
                c = np.array(color) * (0.68 + 0.42 * curve) * shade
                c = c + (np.array(hi) - c) * max(0, curve - 0.82) * 3
                img[y0:int(y0 + rh) + 1, x] = c
        img[y0:y0 + 2] *= 0.6
    img *= (0.94 + 0.12 * n)[..., None]
    return rgba(np.clip(img, 0, 255))


def roof_grey(seed=6):
    return tiles(seed, (150, 146, 150), (190, 188, 192), rows=12, cols=14)


def gold_tiles(seed=7):
    return tiles(seed, (210, 168, 60), (250, 226, 140), rows=12, cols=12)


def coppi(seed=8):
    return tiles(seed, (176, 92, 60), (210, 140, 104))


def blind_arch(seed=9):
    """Lower order of the nave sides: arched recess with a blue oculus, white frame, orange wall.

    128 x 256 px for a bay 2.8 m wide and 6 m tall (recess 2.0 m wide)."""
    im = to_img(tex(128, 256, ORANGE, seed, 0.12, 48))
    d = ImageDraw.Draw(im)
    # white frame (archivolt and jambs)
    d.rectangle([14, 92, 114, 256], fill=(226, 222, 212))
    d.ellipse([14, 40, 114, 140], fill=(226, 222, 212))
    # recess, lighter plaster
    d.rectangle([24, 92, 104, 256], fill=(232, 186, 140))
    d.ellipse([24, 50, 104, 130], fill=(232, 186, 140))
    # oculus with blue stained glass
    d.ellipse([34, 100, 94, 160], fill=(226, 222, 212))
    d.ellipse([40, 106, 88, 154], fill=(40, 80, 150))
    for k in range(8):
        a = math.radians(k * 45)
        d.line([(64, 130), (64 + 22 * math.cos(a), 130 + 22 * math.sin(a))], fill=(120, 160, 210), width=2)
    d.ellipse([58, 124, 70, 136], fill=(200, 170, 80))
    # sill
    d.rectangle([10, 240, 118, 256], fill=(210, 206, 196))
    return from_img(im)


def window_rect(seed=10):
    """Upper order: rectangular window, white frame, on orange (128 x 128 px = 1.4 x 1.4 m)."""
    im = to_img(tex(128, 128, ORANGE, seed, 0.12, 48))
    d = ImageDraw.Draw(im)
    d.rectangle([24, 14, 104, 114], fill=(226, 222, 212))
    d.rectangle([34, 24, 94, 104], fill=(52, 70, 104))
    d.line([(64, 24), (64, 104)], fill=(160, 170, 190), width=3)
    d.line([(34, 64), (94, 64)], fill=(160, 170, 190), width=3)
    return from_img(im)


def oculus_orange(seed=11):
    """Round blue window with white ring, on orange (128 px = 1.6 m)."""
    im = to_img(tex(128, 128, ORANGE, seed, 0.12, 48))
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, 120, 120], fill=(226, 222, 212))
    d.ellipse([22, 22, 106, 106], fill=(38, 74, 140))
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(64, 64), (64 + 40 * math.cos(a), 64 + 40 * math.sin(a))], fill=(120, 150, 200), width=2)
    d.ellipse([54, 54, 74, 74], fill=(220, 190, 90))
    return from_img(im)


def arch_window_orange(seed=12):
    """Arched window (dome drum, transept) with white frame, on orange (128 x 256)."""
    im = to_img(tex(128, 256, ORANGE, seed, 0.12, 48))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 80, 108, 250], fill=(226, 222, 212))
    d.ellipse([20, 36, 108, 124], fill=(226, 222, 212))
    d.rectangle([32, 80, 96, 240], fill=(46, 62, 96))
    d.ellipse([32, 48, 96, 112], fill=(46, 62, 96))
    for y in range(90, 240, 24):
        d.line([(32, y), (96, y)], fill=(130, 140, 160), width=2)
    d.line([(64, 52), (64, 240)], fill=(130, 140, 160), width=2)
    return from_img(im)


def bronze_door(seed=13, arched=True):
    """Bronze door with relief panels; arched top on pink stone (128 x 256 = 3 x 6 m)."""
    im = to_img(tex(128, 256, PINK, seed, 0.1))
    d = ImageDraw.Draw(im)
    # marble surround
    d.rectangle([6, 64, 122, 256], fill=MARBLE)
    d.ellipse([6, 6, 122, 122], fill=MARBLE)
    n = noise(256, 128, 12, 3, seed + 1)
    bronze = np.array((96, 76, 46), float)[None, None] * (0.75 + 0.5 * n[..., None])
    door = to_img(bronze)
    m = Image.new("L", (128, 256), 0)
    dm = ImageDraw.Draw(m)
    dm.rectangle([18, 64, 110, 256], fill=255)
    dm.ellipse([18, 18, 110, 110], fill=255)
    im.paste(door, (0, 0), m)
    d = ImageDraw.Draw(im)
    for leaf in (0, 1):
        x0 = 22 + leaf * 45
        for r_ in range(4):
            y0 = 80 + r_ * 42
            d.rectangle([x0, y0, x0 + 40, y0 + 36], outline=(160, 128, 74), width=2)
            d.ellipse([x0 + 14, y0 + 6, x0 + 26, y0 + 18], fill=(150, 120, 70))
            d.rectangle([x0 + 16, y0 + 18, x0 + 24, y0 + 32], fill=(140, 112, 64))
    d.line([(64, 64), (64, 256)], fill=(40, 30, 18), width=2)
    return from_img(im)


def bronze_door_big(seed=13, w=512, h=1024):
    """The bronze doors of the sanctuary, 3.2 x 6.4 m, drawn at twice the size and cut in 2 x 4 regions
    (tn_porta_i_j): an arch of white marble on the pink stone, a lunette with rays, two leaves of five relief
    panels each, studs, ring handles; the relief is shaded from its own height map (light from the upper left),
    with green in the hollows as on old bronze. (No photograph of the real doors: this is a likeness.)"""
    S = 2
    W, H = w * S, h * S
    r = np.random.default_rng(seed)
    stone = tex(W, H, PINK, seed, 0.12, 60)
    im = to_img(stone)
    d = ImageDraw.Draw(im)
    # marble surround: jambs and a round arch, with a moulding line
    mx, top = int(W * 0.045), int(W * 0.045)
    rad = W / 2 - mx
    marble = tex(W, H, MARBLE, seed + 2, 0.10, 90)
    mm = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mm)
    dm.rectangle([mx, top + rad, W - mx, H], fill=255)
    dm.ellipse([mx, top, W - mx, top + 2 * rad], fill=255)
    im.paste(to_img(marble), (0, 0), mm)
    # the bronze: height map first
    bx = int(W * 0.14)
    brad = W / 2 - bx
    btop = top + int(W * 0.095)
    hm = Image.new("L", (W, H), 0)
    dh = ImageDraw.Draw(hm)
    mask = Image.new("L", (W, H), 0)
    dk = ImageDraw.Draw(mask)
    dk.rectangle([bx, btop + brad, W - bx, H], fill=255)
    dk.ellipse([bx, btop, W - bx, btop + 2 * brad], fill=255)
    dh.rectangle([bx, btop + brad, W - bx, H], fill=110)
    dh.ellipse([bx, btop, W - bx, btop + 2 * brad], fill=110)
    cx = W / 2
    y_spring = btop + brad
    # lunette: rays from a small sun, a rim
    for k in range(13):
        a0 = math.pi * (k + 0.5) / 13
        x1, y1 = cx - math.cos(a0) * brad * 0.92, y_spring - math.sin(a0) * brad * 0.92
        dh.line([(cx, y_spring - 8), (x1, y1)], fill=170, width=int(W * 0.012))
    dh.pieslice([cx - brad * 0.3, y_spring - brad * 0.3, cx + brad * 0.3, y_spring + brad * 0.3], 180, 360, fill=200)
    dh.rectangle([bx, y_spring - int(W * 0.012), W - bx, y_spring + int(W * 0.03)], fill=190)      # transom
    # two leaves, five panels each
    y0, y1 = y_spring + int(W * 0.05), H - int(W * 0.03)
    gap = int(W * 0.012)
    lw = (W - 2 * bx - gap) / 2
    for leaf in (0, 1):
        x0 = bx + leaf * (lw + gap)
        dh.rectangle([x0, y0, x0 + lw, y1], fill=140)                    # the leaf stands out of the frame
        ph = (y1 - y0) / 5
        for k in range(5):
            px0, py0 = x0 + lw * 0.12, y0 + ph * k + ph * 0.10
            px1, py1 = x0 + lw * 0.88, y0 + ph * (k + 1) - ph * 0.10
            dh.rectangle([px0, py0, px1, py1], fill=95)                   # sunk field
            dh.rectangle([px0, py0, px1, py1], outline=205, width=int(W * 0.008))    # raised moulding
            pcx, pcy = (px0 + px1) / 2, (py0 + py1) / 2
            ww, hh = (px1 - px0), (py1 - py0)
            if k % 2 == 0:                                               # a cross on rays
                dh.rectangle([pcx - ww * 0.05, pcy - hh * 0.34, pcx + ww * 0.05, pcy + hh * 0.34], fill=215)
                dh.rectangle([pcx - ww * 0.26, pcy - hh * 0.14, pcx + ww * 0.26, pcy - hh * 0.04], fill=215)
            else:                                                        # an eight-pointed star in a ring
                dh.ellipse([pcx - ww * 0.30, pcy - ww * 0.30, pcx + ww * 0.30, pcy + ww * 0.30], outline=190, width=int(W * 0.008))
                pts = []
                for q in range(16):
                    rr = ww * (0.24 if q % 2 == 0 else 0.10)
                    pts.append((pcx + rr * math.cos(math.pi * q / 8), pcy + rr * math.sin(math.pi * q / 8)))
                dh.polygon(pts, fill=220)
        for k in range(6):                                               # studs on the rails
            sy = y0 + ph * k
            for fx in (0.06, 0.5, 0.94):
                sx = x0 + lw * fx
                rr = W * 0.011
                if y0 + 4 < sy < y1 - 4:
                    dh.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=235)
    # ring handles
    for sgn in (-1, 1):
        hx, hy = cx + sgn * W * 0.05, y0 + (y1 - y0) * 0.52
        rr = W * 0.028
        dh.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], outline=240, width=int(W * 0.009))
        dh.ellipse([hx - rr * 0.35, hy - rr * 1.35, hx + rr * 0.35, hy - rr * 0.65], fill=240)
    hmap = np.asarray(hm.filter(ImageFilter.GaussianBlur(S * 1.6)), float)
    gy, gx = np.gradient(hmap)
    light = np.clip(0.5 - (gx + gy) * 0.035, 0.15, 1.25)                   # lit from the upper left
    n1 = noise(H, W, 40, 4, seed + 5)
    n2 = noise(H, W, 6, 2, seed + 6)
    base = np.array((104, 78, 44), float)[None, None] * (0.80 + 0.35 * n1[..., None]) * (0.92 + 0.16 * n2[..., None])
    hollow = np.clip((120 - hmap) / 60.0, 0, 1)[..., None] * (0.5 + 0.5 * n1[..., None])
    base = base * (1 - 0.45 * hollow) + np.array((58, 96, 80), float)[None, None] * 0.45 * hollow          # verdigris in the hollows
    bronze = np.clip(base * (0.55 + 0.9 * light[..., None]), 0, 255)
    edge = np.clip((hmap - 200) / 40.0, 0, 1)[..., None]
    bronze = np.clip(bronze + edge * np.array((60, 46, 20), float)[None, None], 0, 255)                     # rubbed high points
    im.paste(to_img(bronze), (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.line([(cx, y_spring + int(W * 0.03)), (cx, H)], fill=(18, 14, 10), width=max(2, int(W * 0.006)))
    # soft shadow of the arch on the door, and of the door on the sill
    a = np.asarray(im, float)
    sh = np.asarray(mask.filter(ImageFilter.GaussianBlur(S * 6)), float) / 255.0
    inner = np.asarray(mask, float) / 255.0
    a *= (1 - 0.35 * (inner * (1 - sh)))[..., None] ** 1.0
    out = to_img(a).resize((w, h), Image.LANCZOS)
    return np.asarray(out, float)


def mosaic_band(seed=14):
    """Archivolt mosaic: gold tesserae with blue and red figures, 256 x 64 (one straight band)."""
    r = np.random.default_rng(seed)
    img = np.zeros((64, 256, 3))
    for y in range(0, 64, 4):
        for x in range(0, 256, 4):
            g = np.array(GOLD) * r.uniform(0.85, 1.15)
            img[y:y + 4, x:x + 4] = g
    im = to_img(img)
    d = ImageDraw.Draw(im)
    for k in range(6):   # stylised angels / saints
        cx = 22 + k * 42
        d.ellipse([cx - 7, 12, cx + 7, 26], fill=(236, 210, 180))
        d.polygon([(cx - 14, 60), (cx, 26), (cx + 14, 60)], fill=tuple(int(v) for v in r.choice([(50, 90, 170), (170, 50, 50), (240, 240, 240)])))
        d.polygon([(cx - 6, 24), (cx - 22, 18), (cx - 8, 38)], fill=(240, 236, 220))
        d.polygon([(cx + 6, 24), (cx + 22, 18), (cx + 8, 38)], fill=(240, 236, 220))
    d.rectangle([0, 0, 256, 3], fill=MARBLE)
    d.rectangle([0, 60, 256, 64], fill=MARBLE)
    return from_img(im)


def trifora(seed=15):
    """Large three-light arched window of the facade (128 x 256)."""
    im = Image.new("RGB", (128, 256), MARBLE)
    d = ImageDraw.Draw(im)
    d.rectangle([4, 64, 124, 256], fill=(40, 58, 96))
    d.ellipse([4, 4, 124, 124], fill=(40, 58, 96))
    r = np.random.default_rng(seed)
    for y in range(20, 256, 10):
        for x in range(8, 124, 10):
            if r.random() < 0.3:
                d.rectangle([x, y, x + 8, y + 8], fill=tuple(int(v) for v in r.choice(
                    [(70, 100, 170), (170, 60, 60), (200, 170, 80), (80, 140, 120), (220, 220, 230)])))
    for x in (44, 84):
        d.rectangle([x - 4, 40, x + 4, 256], fill=MARBLE)
    return from_img(im)


def madonna_panel(seed=16):
    """Mosaic panel of the Madonna for the tower front (128 x 256): stylised figure on gold."""
    r = np.random.default_rng(seed)
    img = np.zeros((256, 128, 3))
    for y in range(0, 256, 4):
        for x in range(0, 128, 4):
            img[y:y + 4, x:x + 4] = np.array(GOLD) * r.uniform(0.85, 1.15)
    im = to_img(img)
    d = ImageDraw.Draw(im)
    d.ellipse([46, 46, 82, 82], fill=(250, 220, 120))          # halo
    d.ellipse([54, 54, 74, 76], fill=(90, 66, 50))             # dark face (Madonna Nera)
    d.polygon([(64, 70), (24, 232), (104, 232)], fill=(40, 70, 150))    # blue mantle
    d.polygon([(64, 84), (44, 200), (84, 200)], fill=(170, 40, 40))     # red robe
    d.ellipse([58, 110, 74, 126], fill=(90, 66, 50))           # child
    d.rectangle([0, 0, 128, 6], fill=MARBLE)
    d.rectangle([0, 250, 128, 256], fill=MARBLE)
    d.rectangle([0, 0, 6, 256], fill=MARBLE)
    d.rectangle([122, 0, 128, 256], fill=MARBLE)
    return from_img(im)


def tympanum(seed=17):
    """Pediment filling: gold mosaic with a white cross and garland (256 x 128, triangle used)."""
    r = np.random.default_rng(seed)
    img = np.zeros((128, 256, 3))
    for y in range(0, 128, 4):
        for x in range(0, 256, 4):
            img[y:y + 4, x:x + 4] = np.array((150, 190, 170)) * r.uniform(0.85, 1.12)
    im = to_img(img)
    d = ImageDraw.Draw(im)
    d.rectangle([122, 50, 134, 118], fill=(240, 236, 226))
    d.rectangle([104, 66, 152, 76], fill=(240, 236, 226))
    for k in range(10):
        d.ellipse([30 + k * 20, 100, 44 + k * 20, 114], fill=(200, 170, 80))
    return from_img(im)


def frieze(seed=18, text="AVE MARIA"):
    im = to_img(tex(256, 64, (230, 206, 140), seed, 0.1))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 28)
    tw = d.textlength(text, font=f)
    d.text(((256 - tw) / 2 + 1, 17), text, font=f, fill=(150, 120, 60))
    d.text(((256 - tw) / 2, 16), text, font=f, fill=(96, 72, 30))
    for x in range(8, 60, 12):
        d.ellipse([x, 26, x + 8, 34], fill=(190, 160, 90))
        d.ellipse([256 - x - 8, 26, 256 - x, 34], fill=(190, 160, 90))
    d.rectangle([0, 0, 256, 4], fill=MARBLE)
    d.rectangle([0, 60, 256, 64], fill=MARBLE)
    return from_img(im)


def belfry(seed=19):
    """Arched bell opening on pink ashlar (128 x 256 = 1.6 x 3.2 m)."""
    base = ashlar_pink(seed)[:256, :128, :3]
    im = to_img(base)
    d = ImageDraw.Draw(im)
    d.rectangle([20, 70, 108, 256], fill=MARBLE)
    d.ellipse([20, 26, 108, 114], fill=MARBLE)
    d.rectangle([30, 70, 98, 256], fill=(26, 26, 30))
    d.ellipse([30, 36, 98, 104], fill=(26, 26, 30))
    d.polygon([(50, 130), (78, 130), (88, 180), (40, 180)], fill=(110, 90, 50))
    d.line([(64, 70), (64, 130)], fill=(60, 60, 60), width=3)
    return from_img(im)


def cornice(seed=20):
    img = tex(256, 64, MARBLE, seed, 0.08)
    prof = [1.1, 1.1, 1.05, 0.72, 0.8, 1.05, 1.08, 1.0, 0.68, 0.92, 1.08, 1.06, 1.0, 0.95, 0.82, 0.62]
    for i, p in enumerate(prof):
        img[i * 4:(i + 1) * 4] *= p
    return rgba(np.clip(img, 0, 255))


def railing(seed=21):
    """Iron railing, transparent between the bars (256 x 64 = 2 x 1 m)."""
    img = np.zeros((64, 256, 4))
    img[..., :3] = (36, 38, 40)
    img[0:5, :, 3] = 255
    img[58:64, :, 3] = 255
    for x in range(0, 256, 16):
        img[:, x:x + 3, 3] = 255
    return img


def convent_bay(seed=22):
    """Convent window bay (128 x 128 = 3 x 3 m): window with shutters and a small balcony."""
    im = to_img(tex(128, 128, BEIGE, seed, 0.12, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 24, 88, 100], fill=(70, 74, 80))
    d.rectangle([28, 24, 40, 100], fill=(120, 116, 104))
    d.rectangle([88, 24, 100, 100], fill=(120, 116, 104))
    d.rectangle([22, 100, 106, 106], fill=(200, 196, 186))
    for x in range(24, 106, 8):
        d.line([(x, 82), (x, 100)], fill=(40, 40, 42), width=2)
    d.line([(22, 82), (106, 82)], fill=(40, 40, 42), width=3)
    return from_img(im)


def convent_arcade(seed=23):
    """Convent upper loggia: arched opening (128 x 128)."""
    im = to_img(tex(128, 128, BEIGE, seed, 0.12, 40))
    d = ImageDraw.Draw(im)
    d.rectangle([24, 56, 104, 128], fill=(66, 64, 60))
    d.ellipse([24, 16, 104, 96], fill=(66, 64, 60))
    d.rectangle([20, 116, 108, 128], fill=(200, 196, 186))
    return from_img(im)


def segreteria_door(seed=24):
    """Arched door/window of the low building on the square (128 x 256 = 1.8 x 3.6 m)."""
    im = to_img(tex(128, 256, ORANGE, seed, 0.1, 48))
    d = ImageDraw.Draw(im)
    d.rectangle([16, 80, 112, 256], fill=(226, 222, 212))
    d.ellipse([16, 32, 112, 128], fill=(226, 222, 212))
    d.rectangle([28, 80, 100, 256], fill=(70, 82, 92))
    d.ellipse([28, 44, 100, 116], fill=(70, 82, 92))
    for y in range(90, 250, 30):
        d.line([(28, y), (100, y)], fill=(150, 160, 168), width=2)
    return from_img(im)


def solar(seed=25):
    """Solar panel (128 x 64 = 2 x 1 m): dark blue cells, aluminium frame."""
    im = Image.new("RGB", (128, 64), (190, 192, 196))
    d = ImageDraw.Draw(im)
    for y in range(3, 61, 10):
        for x in range(3, 125, 10):
            d.rectangle([x, y, x + 8, y + 8], fill=(30, 44, 86))
    return from_img(im)


def roof_flat(seed=26):
    img = tex(256, 256, (150, 140, 128), seed, 0.2, 20)
    return rgba(img)


# ------------------------------------------------------------------------------------ interior
def floor_stars(seed=30):
    """Central aisle: octagons with eight-pointed stars, red and white marble (2 x 2 m)."""
    im = to_img(tex(256, 256, (232, 228, 220), seed, 0.06, 40))
    d = ImageDraw.Draw(im)
    for cy in (64, 192):
        for cx in (64, 192):
            pts = [(cx + 60 * math.cos(math.radians(22.5 + 45 * k)), cy + 60 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
            d.polygon(pts, fill=(150, 64, 56))
            pts = [(cx + 52 * math.cos(math.radians(22.5 + 45 * k)), cy + 52 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
            d.polygon(pts, fill=(36, 36, 40))
            star = []
            for k in range(16):
                rr = 46 if k % 2 == 0 else 20
                a = math.radians(k * 22.5)
                star.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
            d.polygon(star, fill=(222, 200, 150))
    return from_img(im)


def floor_diamonds(seed=31):
    """Aisles: white marble squares with red borders and black diamonds (2 x 2 m)."""
    im = to_img(tex(256, 256, (236, 234, 228), seed, 0.06, 40))
    d = ImageDraw.Draw(im)
    for oy in (0, 128):
        for ox in (0, 128):
            d.rectangle([ox + 4, oy + 4, ox + 124, oy + 124], outline=(156, 60, 52), width=10)
            d.polygon([(ox + 64, oy + 26), (ox + 102, oy + 64), (ox + 64, oy + 102), (ox + 26, oy + 64)], fill=(34, 40, 38))
    return from_img(im)


def marble_red(seed=32):
    img = tex(256, 256, (164, 70, 62), seed, 0.1, 32)
    v = noise(256, 256, 40, 5, seed + 2)
    line = np.clip(1 - np.abs(v - 0.5) * 22, 0, 1)
    img = img * (1 - 0.3 * line[..., None]) + np.array((236, 220, 210)) * (0.3 * line[..., None])
    return rgba(np.clip(img, 0, 255))


def marble_pink(seed=33):
    img = tex(256, 256, (214, 168, 150), seed, 0.08, 32)
    v = noise(256, 256, 28, 5, seed + 2)
    line = np.clip(1 - np.abs(v - 0.5) * 26, 0, 1)
    img *= (1 - 0.2 * line)[..., None]
    return rgba(np.clip(img, 0, 255))


def gilded(seed=34):
    img = tex(64, 64, (206, 166, 76), seed, 0.25, 6)
    return rgba(img)


def wall_yellow(seed=35):
    """Gilded yellow wall with small red stars (side chapels), 2 x 2 m."""
    im = to_img(tex(256, 256, (226, 186, 96), seed, 0.1, 40))
    d = ImageDraw.Draw(im)
    for y in range(16, 256, 48):
        for x in range(16 + (24 if (y // 48) % 2 else 0), 256, 48):
            pts = []
            for k in range(8):
                rr = 7 if k % 2 == 0 else 3
                a = math.radians(k * 45)
                pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
            d.polygon(pts, fill=(176, 70, 52))
    return from_img(im)


def coffers(seed=36):
    """Coffered ceiling, cream and gold (2 x 2 m)."""
    im = to_img(tex(256, 256, (232, 222, 196), seed, 0.06))
    d = ImageDraw.Draw(im)
    for oy in (0, 128):
        for ox in (0, 128):
            d.rectangle([ox + 10, oy + 10, ox + 118, oy + 118], fill=(214, 196, 150))
            d.rectangle([ox + 24, oy + 24, ox + 104, oy + 104], fill=(196, 170, 110))
            d.ellipse([ox + 54, oy + 54, ox + 74, oy + 74], fill=(232, 200, 90))
    return from_img(im)


def fresco(seed, kind="vault"):
    """A painted scene: sky, clouds, a central figure and a crowd (256 x 256), golden frame."""
    r = np.random.default_rng(seed)
    h, w = 256, 256
    y = np.linspace(0, 1, h)[:, None]
    sky = np.array((250, 236, 190)) * (1 - y[..., None]) + np.array((150, 190, 226)) * y[..., None]
    img = np.repeat(sky, w, axis=1)
    cl = noise(h, w, 40, 4, seed) > 0.55
    img[cl] = img[cl] * 0.4 + np.array((250, 248, 240)) * 0.6
    im = to_img(img)
    d = ImageDraw.Draw(im)
    d.ellipse([108, 30, 148, 70], fill=(255, 236, 160))             # glory
    d.polygon([(128, 52), (100, 140), (156, 140)], fill=(40, 70, 150))   # Madonna mantle
    d.polygon([(128, 64), (112, 130), (144, 130)], fill=(180, 50, 50))
    d.ellipse([120, 44, 136, 60], fill=(230, 200, 170))
    for k in range(14):   # angels and the crowd below
        x = r.uniform(20, 236)
        yy = r.uniform(60, 120) if k < 6 else r.uniform(170, 236)
        col = tuple(int(v) for v in r.choice([(180, 60, 50), (60, 90, 160), (220, 200, 120), (120, 90, 70), (240, 236, 226)]))
        d.ellipse([x - 6, yy - 6, x + 6, yy + 6], fill=(226, 196, 164))
        d.polygon([(x - 10, yy + 26), (x, yy + 4), (x + 10, yy + 26)], fill=col)
    d.rectangle([0, 0, w - 1, h - 1], outline=(200, 164, 70), width=8)
    return from_img(im)


def mosaic_panel(seed):
    """Side aisle mosaic (Mysteries of the Rosary), 256 x 128, stylised, framed."""
    r = np.random.default_rng(seed)
    img = np.zeros((128, 256, 3))
    for y in range(0, 128, 3):
        for x in range(0, 256, 3):
            base = np.array((120, 140, 160)) if y < 70 else np.array((150, 120, 90))
            img[y:y + 3, x:x + 3] = base * r.uniform(0.85, 1.15)
    im = to_img(img)
    d = ImageDraw.Draw(im)
    for k in range(7):
        x = 24 + k * 34 + r.uniform(-6, 6)
        col = tuple(int(v) for v in r.choice([(170, 50, 50), (50, 80, 160), (220, 200, 120), (240, 236, 226), (90, 120, 70)]))
        d.ellipse([x - 7, 40, x + 7, 54], fill=(226, 196, 164))
        d.polygon([(x - 13, 112), (x, 52), (x + 13, 112)], fill=col)
    d.rectangle([0, 0, 255, 127], outline=(206, 170, 80), width=6)
    return from_img(im)


def stained_saint(seed, symbol=None):
    """Stained-glass window with a saint, or a symbol (luna / stella / sole) - 128 x 256."""
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (128, 256), (40, 40, 44))
    d = ImageDraw.Draw(im)
    for y in range(0, 256, 14):
        for x in range(0, 128, 14):
            d.rectangle([x + 1, y + 1, x + 13, y + 13], fill=tuple(int(v) for v in r.choice(
                [(60, 90, 170), (70, 130, 180), (180, 160, 80), (90, 140, 110), (160, 60, 60)])))
    if symbol is None:
        d.ellipse([46, 40, 82, 76], fill=(250, 220, 110))
        d.ellipse([54, 46, 74, 70], fill=(230, 196, 164))
        d.polygon([(64, 70), (34, 220), (94, 220)], fill=tuple(int(v) for v in r.choice([(170, 40, 40), (40, 80, 170), (60, 140, 90)])))
    elif symbol == "luna":
        d.ellipse([28, 70, 100, 142], fill=(240, 236, 200))
        d.ellipse([46, 62, 118, 134], fill=(40, 60, 120))
    elif symbol == "stella":
        pts = []
        for k in range(16):
            rr = 40 if k % 2 == 0 else 16
            a = math.radians(k * 22.5 - 90)
            pts.append((64 + rr * math.cos(a), 110 + rr * math.sin(a)))
        d.polygon(pts, fill=(250, 230, 120))
    elif symbol == "sole":
        d.ellipse([36, 82, 92, 138], fill=(250, 200, 70))
        for k in range(12):
            a = math.radians(k * 30)
            d.line([(64 + 30 * math.cos(a), 110 + 30 * math.sin(a)), (64 + 48 * math.cos(a), 110 + 48 * math.sin(a))],
                   fill=(250, 200, 70), width=5)
    m = Image.new("L", (128, 256), 0)
    dm = ImageDraw.Draw(m)
    dm.rectangle([6, 60, 122, 256], fill=255)
    dm.ellipse([6, 4, 122, 120], fill=255)
    out = Image.new("RGB", (128, 256), (200, 190, 170))
    out.paste(im, (0, 0), m)
    return from_img(out)


def inscription(seed=37, text="AVE MARIA GRATIA PLENA DOMINUS TECUM"):
    """Gold letters on blue, 256 x 32 (repeated around the dome base)."""
    im = Image.new("RGB", (256, 32), (40, 70, 140))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 14)
    words = text.split()
    i = seed % len(words)
    s = " ".join(words[i:] + words[:i])
    d.text((4, 8), s, font=f, fill=(226, 196, 110))
    d.rectangle([0, 0, 256, 2], fill=(206, 170, 80))
    d.rectangle([0, 29, 256, 32], fill=(206, 170, 80))
    return from_img(im)


def wood_pew(seed=38):
    img = tex(128, 64, (110, 68, 40), seed, 0.25, 6)
    x = np.linspace(0, 40, 128)[None, :]
    img *= (0.9 + 0.1 * np.sin(x + noise(64, 128, 8, 2, seed)[..., None][..., 0] * 4))[..., None]
    return rgba(np.clip(img, 0, 255))


def icon_madonna(seed=39):
    """The icon of the Madonna Nera on the throne: dark faces, golden mantle (128 x 256)."""
    im = Image.new("RGB", (128, 256), (200, 160, 70))
    d = ImageDraw.Draw(im)
    d.ellipse([34, 6, 94, 66], fill=(250, 220, 120))          # crown / halo
    d.polygon([(64, 40), (16, 250), (112, 250)], fill=(214, 176, 80))   # golden mantle
    d.polygon([(64, 70), (36, 250), (92, 250)], fill=(130, 40, 40))
    d.ellipse([50, 30, 78, 62], fill=(44, 34, 30))             # dark face
    d.ellipse([56, 100, 74, 118], fill=(44, 34, 30))           # child
    d.polygon([(64, 112), (48, 170), (80, 170)], fill=(220, 190, 100))
    return from_img(im)


def build(pk):
    put = pk.put
    put("tn_ashlar", ashlar_pink())
    put("tn_marmo", marble())
    put("tn_intonaco", plaster_orange())
    put("tn_beige", plaster_beige())
    put("tn_forte", stone_fort())
    put("tn_tetto", roof_grey())
    put("tn_oro", gold_tiles())
    put("tn_coppi", coppi())
    put("tn_arco_cieco", blind_arch())
    put("tn_finestra", window_rect())
    put("tn_oculo", oculus_orange())
    put("tn_finestra_arco", arch_window_orange())
    put("tn_porta", bronze_door())
    door = bronze_door_big()
    for i in range(2):
        for j in range(4):
            put("tn_porta_%d_%d" % (i, j), rgba(door[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256]))
    put("tn_mosaico", mosaic_band())
    put("tn_trifora", trifora())
    put("tn_madonna", madonna_panel())
    put("tn_timpano", tympanum())
    put("tn_fregio", frieze())
    put("tn_cella", belfry())
    put("tn_cornice", cornice())
    put("tn_ringhiera", railing())
    put("tn_convento", convent_bay())
    put("tn_loggia_conv", convent_arcade())
    put("tn_portone_seg", segreteria_door())
    put("tn_solare", solar())
    put("tn_lastrico", roof_flat())
    from decor import santuario_arte          # the inside of the church, redone on 14/11/2026
    santuario_arte.build(put)
