"""Texture pages for the decoration statics (RGBA 512 x 512, alpha 0 = transparent).

Every region is addressed by name: REG[name] = (page, x0, y0, x1, y1). Regions are at most 256 px
on each side so a single polygon never spans more than 256 px (safe for every TE/TEN packer).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_textures import noise  # noqa: E402

P = 512
pages = []
REG = {}


class Packer:
    """Shelf packer over 512 x 512 pages."""

    def __init__(self):
        self.page = -1
        self.x = self.y = self.h = 0
        self.new_page()

    def new_page(self):
        pages.append(np.zeros((P, P, 4), dtype=np.float64))
        self.page += 1
        self.x = self.y = self.h = 0

    def put(self, name, img):
        h, w = img.shape[:2]
        assert w <= 256 and h <= 256, name
        if self.x + w > P:
            self.x, self.y, self.h = 0, self.y + self.h, 0
        if self.y + h > P:
            self.new_page()
        pages[self.page][self.y:self.y + h, self.x:self.x + w] = img
        REG[name] = (self.page, self.x, self.y, self.x + w, self.y + h)
        self.x += w
        self.h = max(self.h, h)


def rgba(rgb, a=255.0):
    rgb = np.asarray(rgb, dtype=np.float64)
    out = np.zeros(rgb.shape[:2] + (4,))
    out[..., :3] = rgb
    out[..., 3] = a
    return out


def solid(w, h, color, seed=0, amount=0.12, scale=16):
    n = noise(h, w, scale, 3, seed)
    c = np.array(color, dtype=np.float64)
    return rgba(np.clip(c[None, None] * (1 + (n[..., None] - 0.5) * amount), 0, 255))


def bark(w, h, color, seed, ridges=7):
    n = noise(h, w, 16, 4, seed)
    x = np.linspace(0, ridges * 2 * math.pi, w)[None, :]
    r = 0.75 + 0.25 * np.sin(x + n * 6)
    img = np.array(color, float)[None, None] * (r * (0.8 + 0.4 * n))[..., None]
    return rgba(np.clip(img, 0, 255))


def card(w, h, draw_fn, seed):
    """Draw foliage on a transparent card with PIL at 2x and downsample (crisp alpha edges)."""
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    draw_fn(d, w * 2, h * 2, np.random.default_rng(seed))
    im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float64)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return a


def pine_needles(d, w, h, r):
    # Dense umbrella clump of needles, darker underneath.
    for _ in range(3200):
        x, y = r.uniform(0.05, 0.95) * w, r.uniform(0.15, 0.95) * h
        dx, dy = x - w / 2, (y - h * 0.55) / 0.7
        if dx * dx + dy * dy > (w * 0.47) ** 2:
            continue
        ang = r.uniform(0, 2 * math.pi)
        ln = r.uniform(8, 20)
        shade = 0.45 + 0.55 * (1 - y / h)
        c = (int(70 * shade + r.integers(0, 25)), int(105 * shade + r.integers(0, 30)), int(60 * shade), 255)
        d.line([x, y, x + math.cos(ang) * ln, y + math.sin(ang) * ln], fill=c, width=3)


def olive_leaves(d, w, h, r):
    for _ in range(3600):
        x, y = r.uniform(0.04, 0.96) * w, r.uniform(0.04, 0.96) * h
        dx, dy = x - w / 2, y - h / 2
        if dx * dx + dy * dy > (w * 0.48) ** 2 * (1 - 0.0):
            continue
        ang = r.uniform(0, math.pi)
        ln = r.uniform(8, 14)
        silver = r.random() < 0.4
        c = (150, 160, 140, 255) if silver else (int(r.integers(70, 95)), int(r.integers(95, 115)), 60, 255)
        x2, y2 = x + math.cos(ang) * ln, y + math.sin(ang) * ln
        d.line([x, y, x2, y2], fill=c, width=4)
    for _ in range(6):   # a few olives
        x, y = r.uniform(0.2, 0.8) * w, r.uniform(0.3, 0.8) * h
        d.ellipse([x, y, x + 5, y + 6], fill=(45, 50, 30, 255))


def helichrysum(d, w, h, r):
    base = h * 0.98
    for _ in range(160):
        x0 = w / 2 + r.normal(0, w * 0.12)
        x1 = w / 2 + r.normal(0, w * 0.3)
        y1 = base - r.uniform(0.35, 0.9) * h
        d.line([x0, base, x1, y1], fill=(150, 160, 145, 255), width=3)
        if r.random() < 0.5:
            d.ellipse([x1 - 7, y1 - 6, x1 + 7, y1 + 6], fill=(225, 190, 40, 255))
            d.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill=(240, 210, 70, 255))


def asparagus(d, w, h, r):
    base = h * 0.98
    for _ in range(70):
        x0 = w / 2 + r.normal(0, w * 0.08)
        ang = r.uniform(-1.2, 1.2) - math.pi / 2
        ln = r.uniform(0.4, 0.95) * h
        pts = [(x0, base)]
        x, y = x0, base
        for k in range(8):
            ang += r.normal(0, 0.2)
            x += math.cos(ang) * ln / 8
            y += math.sin(ang) * ln / 8
            pts.append((x, y))
        d.line(pts, fill=(60, 75, 40, 255), width=2)
        for (px, py) in pts[2:]:
            for _ in range(6):
                a2 = r.uniform(0, 2 * math.pi)
                d.line([px, py, px + math.cos(a2) * 9, py + math.sin(a2) * 9], fill=(70, 110, 45, 255), width=2)


def grass_pot(d, w, h, r):
    base = h * 0.98
    for _ in range(220):
        x0 = w / 2 + r.normal(0, w * 0.15)
        x1 = x0 + r.normal(0, w * 0.18)
        y1 = base - r.uniform(0.4, 0.98) * h
        g = int(r.integers(90, 140))
        d.line([x0, base, x1, y1], fill=(50, g, 40, 255), width=3)
    for _ in range(18):
        x, y = w / 2 + r.normal(0, w * 0.2), base - r.uniform(0.4, 0.9) * h
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(200, 60, 120, 255))


def palm_frond(d, w, h, r):
    # A single frond seen from above/side: central rib with leaflets.
    for k in range(40):
        t = k / 40
        x, y = w * 0.05 + t * w * 0.9, h * 0.5 + math.sin(t * 2.5) * h * 0.08
        ln = (1 - abs(t - 0.4)) * h * 0.42
        for s in (-1, 1):
            d.line([x, y, x + w * 0.05, y + s * ln], fill=(70, 115, 50, 255), width=4)
    d.line([w * 0.05, h * 0.5, w * 0.95, h * 0.5 + math.sin(2.5) * h * 0.08], fill=(110, 120, 70, 255), width=5)


def opuntia_pad(w, h, seed):
    n = noise(h, w, 16, 3, seed)
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3))
    img[...] = np.array([92, 128, 70.0]) * (0.85 + 0.3 * n[..., None])
    # areoles: small pale dots on a grid
    rr = np.random.default_rng(seed)
    for _ in range(40):
        x, y = rr.integers(4, w - 4), rr.integers(4, h - 4)
        img[y - 1:y + 2, x - 1:x + 2] = (205, 200, 150)
    edge = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    img *= (1.05 - 0.25 * np.clip(edge, 0, 1))[..., None]
    return rgba(img)


def stripes(w, h, c1, c2, n=8, vertical=True):
    img = np.zeros((h, w, 3))
    for i in range(n):
        c = c1 if i % 2 == 0 else c2
        if vertical:
            img[:, i * w // n:(i + 1) * w // n] = c
        else:
            img[i * h // n:(i + 1) * h // n, :] = c
    return rgba(img)


def chainlink(w, h):
    a = np.zeros((h, w, 4))
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx + yy) % 12 < 2) | ((xx - yy) % 12 < 2)
    a[m] = (150, 155, 150, 255)
    a[:4] = a[-4:] = (110, 115, 110, 255)
    return a


def hull(w, h, top, band, bottom, seed):
    img = solid(w, h, top, seed, 0.08)
    img[int(h * 0.15):int(h * 0.27), :, :3] = band
    img[int(h * 0.62):, :, :3] = bottom
    img[: int(h * 0.05), :, :3] = (90, 60, 40)   # gunwale
    return img


def car_body(w, h, color, seed):
    img = solid(w, h, color, seed, 0.06, 32)
    img[int(h * 0.48):int(h * 0.5), :, :3] *= 0.7    # door line
    return img


def build():
    pk = Packer()
    # --- vegetation (alpha cards first, they are the biggest) ---
    pk.put("pine_card", card(256, 192, pine_needles, 1))
    pk.put("olive_card", card(256, 256, olive_leaves, 2))
    pk.put("heli_card", card(128, 128, helichrysum, 3))
    pk.put("asp_card", card(128, 128, asparagus, 4))
    pk.put("grass_card", card(128, 128, grass_pot, 5))
    pk.put("frond", card(256, 64, palm_frond, 6))
    pk.put("opuntia", opuntia_pad(128, 128, 7))
    pk.put("pine_bark", bark(64, 256, (110, 80, 60), 8, 9))
    pk.put("olive_bark", bark(64, 256, (105, 100, 85), 9, 5))
    fruit = solid(32, 32, (190, 70, 60), 10, 0.2)
    pk.put("fruit", fruit)
    # --- urban ---
    pk.put("iron", solid(64, 64, (32, 34, 33), 11, 0.15))
    pk.put("iron_green", solid(64, 64, (40, 70, 55), 12, 0.15))
    pk.put("lamp_glass", solid(64, 64, (255, 236, 170), 13, 0.05))
    pk.put("white_plaster", solid(128, 128, (236, 234, 228), 14, 0.08, 32))
    pk.put("concrete", solid(64, 64, (165, 162, 155), 15, 0.18))
    pk.put("wood_slats", stripes(128, 64, (150, 105, 65), (95, 65, 40), 8, vertical=False))
    pk.put("soil", solid(64, 64, (90, 65, 45), 16, 0.3))
    pk.put("galv", solid(64, 64, (175, 180, 182), 17, 0.1))
    pk.put("chainlink", chainlink(128, 128))
    for name, c in (("red", (200, 45, 40)), ("yellow", (230, 190, 40)), ("blue", (40, 90, 190)),
                    ("green", (60, 150, 70)), ("orange", (230, 120, 30))):
        pk.put("plastic_" + name, solid(32, 32, c, 18, 0.05))
    pk.put("rubber", solid(32, 32, (28, 28, 30), 19, 0.1))
    pk.put("sand", solid(64, 64, (205, 185, 140), 20, 0.2))
    pk.put("goal_net", chainlink(64, 64))
    # --- vehicles ---
    for name, c in (("car_red", (170, 25, 30)), ("car_white", (230, 230, 228)), ("car_blue", (35, 60, 120)),
                    ("car_silver", (165, 170, 175)), ("car_green", (60, 90, 70)), ("scooter_red", (190, 30, 35)),
                    ("scooter_cream", (225, 215, 185))):
        pk.put(name, car_body(128, 64, c, 21))
    glass = solid(64, 32, (40, 55, 65), 22, 0.1)
    glass[4:8, :, :3] = (120, 140, 150)
    pk.put("glass", glass)
    pk.put("tyre", solid(32, 32, (25, 25, 25), 23, 0.1))
    lights = np.zeros((16, 64, 4))
    lights[..., 3] = 255
    lights[:, :16, :3] = (250, 245, 220)
    lights[:, 16:48, :3] = (60, 60, 62)
    lights[:, 48:, :3] = (200, 30, 25)
    pk.put("lights", lights)
    camper = solid(128, 64, (235, 233, 225), 24, 0.05)
    camper[24:30, :, :3] = (150, 120, 70)
    camper[32:35, :, :3] = (90, 70, 50)
    pk.put("camper", camper)
    # --- boats and beach ---
    pk.put("hull_gozzo", hull(128, 64, (238, 236, 228), (40, 90, 160), (170, 50, 40), 25))
    pk.put("hull_motor", hull(128, 64, (240, 240, 238), (25, 35, 60), (60, 60, 70), 26))
    pk.put("rib_tube", solid(64, 32, (95, 98, 100), 27, 0.1))
    pk.put("deck_wood", stripes(128, 64, (170, 125, 80), (140, 100, 60), 10, vertical=True))
    pk.put("sail", solid(128, 128, (242, 240, 232), 28, 0.04))
    pk.put("umbrella_bar", stripes(128, 64, (240, 238, 230), (40, 100, 70), 8))
    pk.put("umbrella_beach", stripes(128, 64, (240, 238, 230), (40, 90, 170), 8))
    pk.put("cloth", solid(64, 64, (240, 238, 232), 29, 0.05))
    pk.put("chair_alu", solid(32, 32, (170, 172, 175), 30, 0.1))
    # --- Santuario di Tindari ---
    pk.new_page()
    from decor import santuario_tex
    santuario_tex.build(pk)
    pk.new_page()
    from decor import casa_tex
    casa_tex.build(pk)
    return pages, REG


def save(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, p in enumerate(pages):
        im = Image.fromarray(np.clip(p, 0, 255).astype(np.uint8), "RGBA")
        path = os.path.join(out_dir, "decor_%d.png" % i)
        im.save(path)
        paths.append(path)
    return paths


if __name__ == "__main__":
    build()
    print(len(pages), "pages", len(REG), "regions")
    print(save(sys.argv[1] if len(sys.argv) > 1 else "/tmp"))
