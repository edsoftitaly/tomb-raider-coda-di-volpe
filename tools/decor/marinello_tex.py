"""Textures of the Marinello props: photographic (ambientCG CC0, assets/tex_cc0) and drawn alpha cards."""
import os

import numpy as np
from PIL import Image, ImageDraw

from decor.tex import card, rgba, solid

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "tex_cc0")


def photo(name, size, tint=(1, 1, 1), gain=1.0, crop=512):
    im = Image.open(os.path.join(SRC, name + ".jpg")).convert("RGB").crop((0, 0, crop, crop)).resize(size, Image.LANCZOS)
    return rgba(np.clip(np.asarray(im, float) * gain * np.array(tint), 0, 255))


def reeds(d, w, h, r):
    """Arundo: stems fanning from the base, long leaves, a few plumes."""
    for k in range(46):
        x0 = w * (0.5 + r.uniform(-0.16, 0.16))
        top = h * r.uniform(0.04, 0.4)
        x1 = x0 + w * r.uniform(-0.38, 0.38)
        g = int(r.uniform(95, 150))
        col = (int(g * 0.82), g, int(g * 0.45), 255) if r.random() < 0.7 else (int(g * 1.2), int(g * 1.05), int(g * 0.55), 255)
        d.line([(x0, h), ((x0 + x1) / 2 + r.uniform(-6, 6), (h + top) / 2), (x1, top)], fill=col, width=int(r.uniform(3, 6)), joint="curve")
        for j in range(3):                                   # leaves
            t = r.uniform(0.25, 0.85)
            px, py = x0 + (x1 - x0) * t, h + (top - h) * t
            lx = px + r.choice([-1, 1]) * w * r.uniform(0.05, 0.13)
            d.line([(px, py), (lx, py - h * r.uniform(-0.02, 0.07))], fill=col, width=3)
        if r.random() < 0.3:                                 # plume
            d.ellipse([x1 - 7, top - 30, x1 + 7, top + 8], fill=(196, 178, 140, 255))


def net(w, h):
    a = np.zeros((h, w, 4))
    a[..., :3] = (58, 52, 44)
    a[..., 3] = 255
    for k in range(-h, w, 9):
        for y in range(h):
            for x in (k + y, k + h - y):
                if 0 <= x < w:
                    a[y, x, :3] = (150, 134, 104)
    return a


def build(pk):
    pk.put("m_wood", photo("planks004", (256, 256), gain=0.9))
    pk.put("m_wood_dark", photo("planks011", (128, 128), gain=0.8))
    pk.put("m_rock", photo("rock023", (256, 256), tint=(1.0, 0.97, 0.9)))
    pk.put("m_stone", photo("rocks004", (256, 256), tint=(1.0, 0.96, 0.88), gain=0.95))
    pk.put("m_rust", photo("rust002", (128, 128), gain=0.8))
    pk.put("m_tiles", photo("roofingtiles007", (256, 256)))
    pk.put("m_wreck", photo("planks011", (128, 128), tint=(0.62, 0.7, 0.56), gain=0.7))
    pk.put("m_canvas", solid(128, 128, (178, 166, 132), 61, 0.16, 24))
    pk.put("m_net", net(128, 128))
    pk.put("m_reed", card(256, 256, reeds, 62))
    pk.put("m_clay", solid(64, 64, (168, 104, 70), 63, 0.2))
    pk.put("m_rope", solid(32, 32, (176, 150, 104), 64, 0.25, 4))
    pk.put("m_ember", solid(32, 32, (236, 120, 40), 65, 0.4, 4))
    pk.put("m_float", solid(32, 32, (206, 96, 40), 66, 0.15))
    pk.put("m_iron", photo("rust002", (64, 64), tint=(0.5, 0.48, 0.5), gain=0.55))
