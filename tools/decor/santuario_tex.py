"""Procedural textures for the Santuario di Tindari statics (128 px per metre where it matters).

Billiemi stone is a light grey limestone; roof slopes are blue glazed ceramic (sources in santuario.py).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from decor.tex import noise, rgba

STONE = (204, 199, 188)        # Billiemi, light grey-beige
STONE_DARK = (168, 162, 150)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def _stone(w, h, seed, base=STONE, amount=0.16):
    n = noise(h, w, 24, 4, seed) * 0.7 + noise(h, w, 4, 2, seed + 1) * 0.3
    return np.clip(np.array(base, float)[None, None] * (1 + (n[..., None] - 0.5) * amount), 0, 255)


def ashlar(seed=1):
    """2 x 2 m of smooth ashlar: courses of 50 cm, blocks 1 m, fine joints."""
    img = _stone(256, 256, seed)
    for y in range(0, 256, 64):
        img[y:y + 2] *= 0.82
        off = 0 if (y // 64) % 2 else 64
        for x in range(off, 256 + 128, 128):
            img[y:y + 64, max(0, x - 1):min(256, x + 1)] *= 0.84
    return rgba(img)


def rustic(seed=2):
    """2 x 2 m of rusticated blocks (bugnato): 50 cm courses, chamfered, deep joints."""
    img = _stone(256, 256, seed, STONE_DARK, 0.22)
    for row in range(4):
        y0 = row * 64
        off = 0 if row % 2 else 64
        for x0 in range(-128 + off, 256, 128):
            x1 = x0 + 128
            for t in range(6):   # chamfer: lighter top/left, darker bottom/right
                a, b = max(0, x0 + t), min(256, x1 - t)
                if a < b:
                    img[y0 + t, a:b] *= 1.10 - t * 0.01
                    img[y0 + 63 - t, a:b] *= 0.80 + t * 0.02
                if 0 <= x0 + t < 256:
                    img[y0 + t:y0 + 64 - t, x0 + t] *= 1.06
                if 0 <= x1 - 1 - t < 256:
                    img[y0 + t:y0 + 64 - t, x1 - 1 - t] *= 0.84
            if 0 <= x0 < 256:
                img[y0:y0 + 64, x0:x0 + 3] *= 0.55
        img[y0:y0 + 3] *= 0.55
    return rgba(np.clip(img, 0, 255))


def tiles(seed=3, color=(36, 92, 168), hi=(110, 170, 225)):
    """2 x 2 m of glazed canal tiles in rows (slope runs along v)."""
    n = noise(256, 256, 32, 3, seed)
    img = np.zeros((256, 256, 3))
    r = np.random.default_rng(seed)
    for row in range(10):
        y0 = int(row * 25.6)
        for col in range(11):
            x0 = col * 24 + (12 if row % 2 else 0) - 12
            shade = r.uniform(0.82, 1.12)
            for x in range(max(0, x0), min(256, x0 + 24)):
                t = (x - x0) / 24.0
                curve = math.sin(t * math.pi)          # convex tile
                c = np.array(color) * (0.65 + 0.45 * curve) * shade
                c = c + (np.array(hi) - c) * max(0, curve - 0.85) * 3   # glaze highlight
                img[y0:y0 + 26, x] = c
        img[y0:y0 + 2] *= 0.6
    img *= (0.92 + 0.16 * n)[..., None]
    return rgba(np.clip(img, 0, 255))


def coppi(seed=4):
    return tiles(seed, (168, 92, 62), (205, 140, 105))


def plaster(seed=5, color=(214, 192, 148)):
    n = noise(256, 256, 64, 5, seed)
    img = np.array(color, float)[None, None] * (0.9 + 0.2 * n[..., None])
    stain = noise(256, 256, 96, 3, seed + 1) > 0.66
    img[stain] *= 0.9
    return rgba(np.clip(img, 0, 255))


def cornice(seed=6):
    """Moulding seen from the front: 50 cm tall strip, 2 m wide."""
    img = _stone(256, 64, seed)
    prof = [1.15, 1.15, 1.1, 0.7, 0.75, 1.05, 1.05, 1.0, 0.65, 0.9, 1.1, 1.1, 1.0, 0.95, 0.8, 0.6]
    for i, p in enumerate(prof):
        img[i * 4:(i + 1) * 4] *= p
    return rgba(np.clip(img, 0, 255))


def bronze_door(seed=7):
    """Two bronze leaves with 4 x 2 relief panels each (160 x 256 px)."""
    w, h = 160, 256
    n = noise(h, w, 16, 3, seed)
    img = np.array((112, 82, 46), float)[None, None] * (0.75 + 0.5 * n[..., None])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for leaf in range(2):
        lx = leaf * 80
        d.rectangle([lx + 2, 2, lx + 77, 253], outline=(70, 50, 28), width=3)
        for r in range(4):
            for c in range(2):
                x0, y0 = lx + 8 + c * 34, 10 + r * 61
                d.rectangle([x0, y0, x0 + 30, y0 + 54], outline=(150, 118, 70), width=2)
                d.ellipse([x0 + 9, y0 + 12, x0 + 21, y0 + 26], fill=(150, 120, 74))    # a small figure
                d.rectangle([x0 + 11, y0 + 26, x0 + 19, y0 + 46], fill=(140, 110, 66))
    d.line([(80, 0), (80, 256)], fill=(40, 28, 16), width=2)
    return rgba(np.asarray(im, float))


def oculus(seed=8):
    """Round window: stone frame, tracery and dark stained glass on stone background."""
    im = Image.fromarray(np.clip(_stone(256, 256, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 250, 250], fill=(150, 145, 134))
    d.ellipse([22, 22, 234, 234], fill=(185, 180, 168))
    d.ellipse([34, 34, 222, 222], fill=(42, 52, 78))
    r = np.random.default_rng(seed)
    for k in range(12):   # glass colours between the spokes
        a0, a1 = k * 30, k * 30 + 30
        col = tuple(int(v) for v in r.choice([(60, 70, 140), (140, 50, 50), (170, 140, 60), (50, 110, 90)]))
        d.pieslice([40, 40, 216, 216], a0 + 2, a1 - 2, fill=col)
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(128, 128), (128 + 94 * math.cos(a), 128 + 94 * math.sin(a))], fill=(185, 180, 168), width=6)
    d.ellipse([98, 98, 158, 158], fill=(185, 180, 168))
    d.ellipse([110, 110, 146, 146], fill=(200, 170, 80))
    return rgba(np.asarray(im, float))


def frieze(text="AVE MARIA", seed=9):
    """Frieze with the inscription, 256 x 48 px (about 6 m x 1.1 m)."""
    im = Image.fromarray(np.clip(_stone(256, 48, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 30)
    tw = d.textlength(text, font=f)
    d.text(((256 - tw) / 2 + 1, 9), text, font=f, fill=(120, 112, 100))
    d.text(((256 - tw) / 2, 8), text, font=f, fill=(70, 64, 56))
    d.line([(0, 2), (256, 2)], fill=(150, 145, 134), width=2)
    d.line([(0, 45), (256, 45)], fill=(150, 145, 134), width=2)
    return rgba(np.asarray(im, float))


def star(seed=10):
    """Eight-pointed star in relief on stone (128 px = 1.6 m medallion)."""
    im = Image.fromarray(np.clip(_stone(128, 128, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([4, 4, 124, 124], outline=(150, 145, 134), width=4)
    pts = []
    for k in range(16):
        a = math.pi / 2 + k * math.pi / 8
        rr = 54 if k % 2 == 0 else 24
        pts.append((64 + rr * math.cos(a), 64 - rr * math.sin(a)))
    d.polygon([(x + 2, y + 2) for x, y in pts], fill=(140, 134, 122))
    d.polygon(pts, fill=(222, 218, 208))
    return rgba(np.asarray(im, float))


def monofora(seed=11):
    """Single-light arched bell opening with a bell (128 x 256 px, about 1.4 x 3.2 m)."""
    im = Image.fromarray(np.clip(_stone(128, 256, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 70, 108, 252], fill=(24, 24, 28))
    d.ellipse([20, 26, 108, 114], fill=(24, 24, 28))
    d.rectangle([14, 64, 20, 252], fill=(170, 165, 152))
    d.rectangle([108, 64, 114, 252], fill=(170, 165, 152))
    d.polygon([(46, 120), (82, 120), (92, 178), (36, 178)], fill=(120, 96, 50))    # bell
    d.ellipse([34, 170, 94, 186], fill=(100, 80, 40))
    d.line([(64, 70), (64, 120)], fill=(60, 60, 60), width=3)
    d.rectangle([14, 240, 114, 252], fill=(160, 155, 142))
    return rgba(np.asarray(im, float))


def clock(seed=12):
    """Clock in a blind oculus (128 px)."""
    im = Image.fromarray(np.clip(_stone(128, 128, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([6, 6, 122, 122], fill=(150, 145, 134))
    d.ellipse([14, 14, 114, 114], fill=(236, 232, 220))
    for k in range(12):
        a = math.radians(k * 30)
        d.line([(64 + 40 * math.sin(a), 64 - 40 * math.cos(a)), (64 + 48 * math.sin(a), 64 - 48 * math.cos(a))],
               fill=(30, 30, 30), width=4 if k % 3 == 0 else 2)
    d.line([(64, 64), (64, 30)], fill=(25, 25, 25), width=4)     # 12:15
    d.line([(64, 64), (90, 66)], fill=(25, 25, 25), width=5)
    return rgba(np.asarray(im, float))


def tall_window(seed=13):
    """Tall arched stained-glass window with stone surround (128 x 256 px)."""
    im = Image.fromarray(np.clip(_stone(128, 256, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([22, 60, 106, 246], fill=(150, 145, 134))
    d.ellipse([22, 18, 106, 102], fill=(150, 145, 134))
    d.rectangle([30, 60, 98, 240], fill=(46, 58, 86))
    d.ellipse([30, 26, 98, 94], fill=(46, 58, 86))
    r = np.random.default_rng(seed)
    for y in range(40, 240, 14):
        for x in range(32, 98, 11):
            if r.random() < 0.35:
                d.rectangle([x, y, x + 9, y + 12], fill=tuple(int(v) for v in r.choice(
                    [(70, 80, 150), (150, 60, 60), (180, 150, 70), (60, 120, 100)])))
    d.line([(64, 30), (64, 240)], fill=(150, 145, 134), width=3)
    return rgba(np.asarray(im, float))


def niche(seed=14):
    im = Image.fromarray(np.clip(_stone(128, 256, seed), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(12):   # concave shading
        c = int(150 - k * 7)
        d.rectangle([20 + k * 2, 64, 108 - k * 2, 240], fill=(c, c - 4, c - 12))
        d.ellipse([20 + k * 2, 20 + k * 2, 108 - k * 2, 108 - k * 2], fill=(c, c - 4, c - 12))
    d.rectangle([14, 236, 114, 252], fill=(176, 171, 160))
    return rgba(np.asarray(im, float))


def marble(seed=15):
    return rgba(_stone(64, 128, seed, (232, 230, 224), 0.08))


def old_portal(seed=16):
    """Old sanctuary portal: stone frame, keystone dated 1598, wooden door (128 x 256 px)."""
    im = Image.fromarray(np.clip(_stone(128, 256, seed, (196, 182, 156), 0.2), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([28, 76, 100, 254], fill=(92, 62, 40))
    d.ellipse([28, 40, 100, 112], fill=(92, 62, 40))
    for y in range(80, 254, 16):
        d.line([(30, y), (98, y)], fill=(70, 46, 30), width=1)
    d.line([(64, 76), (64, 254)], fill=(60, 40, 26), width=2)
    for k in range(9):   # voussoirs
        a = math.radians(180 + k * 22.5)
        d.line([(64 + 36 * math.cos(a), 76 + 36 * math.sin(a)), (64 + 52 * math.cos(a), 76 + 52 * math.sin(a))],
               fill=(150, 138, 116), width=2)
    d.rectangle([52, 18, 76, 42], fill=(205, 192, 168), outline=(150, 138, 116))
    f = ImageFont.truetype(FONT, 9)
    d.text((54, 25), "1598", font=f, fill=(80, 70, 56))
    return rgba(np.asarray(im, float))


def arcade(seed=17):
    """One loggia bay seen from outside: two half pilasters and an arch, opening transparent.

    256 x 256 px for a bay 4.75 m wide and 5.5 m tall (alpha 0 inside the arch)."""
    st = np.clip(_stone(256, 256, seed), 0, 255).astype(np.uint8)
    im = Image.fromarray(st).convert("RGBA")
    m = Image.new("L", (256, 256), 255)
    d = ImageDraw.Draw(m)
    d.rectangle([30, 120, 226, 256], fill=0)
    d.ellipse([30, 22, 226, 218], fill=0)
    im.putalpha(m)
    a = np.asarray(im, float).copy()
    a[..., 3] = np.where(a[..., 3] > 128, 255, 0)
    dd = ImageDraw.Draw(im)
    return a


def balusters(seed=18):
    """Balustrade, 2 m x 1 m (256 x 128), transparent between balusters."""
    img = np.zeros((128, 256, 4))
    st = _stone(256, 128, seed)
    img[..., :3] = st
    img[0:16, :, 3] = 255                          # handrail
    img[112:128, :, 3] = 255                       # base
    for x0 in range(8, 256, 32):
        for y in range(16, 112):
            t = (y - 16) / 96.0
            hw = 6 + 5 * math.sin(t * math.pi) ** 2 + (3 if 0.15 < t < 0.2 else 0)
            img[y, max(0, int(x0 + 8 - hw)):int(x0 + 8 + hw), 3] = 255
    return img


def build(pk):
    pk.put("sp_pietra", ashlar())
    pk.put("sp_bugnato", rustic())
    pk.put("sp_tegole", tiles())
    pk.put("sp_coppi", coppi())
    pk.put("sp_intonaco", plaster())
    pk.put("sp_oculo", oculus())
    pk.put("sp_arcata", arcade())
    pk.put("sp_cornice", cornice())
    pk.put("sp_fregio", frieze())
    pk.put("sp_balaustra", balusters())
    pk.put("sp_porta", bronze_door())
    pk.put("sp_monofora", monofora())
    pk.put("sp_finestra", tall_window())
    pk.put("sp_nicchia", niche())
    pk.put("vs_portale", old_portal())
    pk.put("sp_stella", star())
    pk.put("sp_orologio", clock())
    pk.put("sp_marmo", marble())
