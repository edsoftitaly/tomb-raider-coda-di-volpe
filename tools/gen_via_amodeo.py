"""Facades of Via Gaspare Amodeo in Oliveri, each painted as one straight elevation after the street
(Ed's photographs of 14/11/2026 used as reference for layout and colours; nothing is copied from them).

  casa()    Ed's house: 16 m x 9.5 m (8 sectors), door on the third sector.
  fronte()  the house opposite with the five switches, 10 m x 6.5 m (5 sectors) and the shop house next to it
            (12 m, 6 sectors): together 22 m, read from the viewer's left = the courtyard gate.

Output: Levels/CdV_Textures/cdv_via_amodeo_1.png (2048 x 2048: casa at y 0, columns 8-10 of fronte at y 1216)
        and cdv_via_amodeo_2.png (2048 x 1024: columns 0-7 of fronte at y 0).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

from facciata import Facade, K

GREEN = (38, 78, 58)
CREAM = (226, 212, 180)
STONE = (196, 170, 128)
# positions of the five switches on the wall opposite, metres from the left end (the gate): nothing is drawn there
SWITCH_X = [2.1875, 3.59375, 5.0, 6.40625, 7.8125]


def casa():
    f = Facade(16.0, 9.5, seed=11)
    f.rect(0, 0, 16, 9.5, CREAM, tex="plaster005", amp=0.55, metres=3.0)
    # plinth of light stone slabs with a thin dark brown stripe on top
    x = 0.0
    while x < 16:
        w = 1.0
        f.rect(x + 0.006, 0, x + w - 0.006, 0.86, np.array((222, 214, 196)) * f.rng.normal(1, 0.03), tex="marble014", amp=0.8, relief=0.025)
        x += w
    f.rect(0, 0.86, 16, 0.95, (92, 58, 40), tex="wood006", amp=0.3, relief=0.035)
    # floor slabs: first floor (the 3D balcony hangs here) and the terrace of the second floor
    f.rect(0, 3.12, 16, 3.24, (214, 204, 182), tex="plaster005", amp=0.5, relief=0.10)
    f.rect(0, 6.22, 16, 6.40, (222, 214, 196), tex="plaster005", amp=0.5, relief=0.16)
    f.rect(0, 6.16, 16, 6.22, (200, 190, 168), tex="plaster005", amp=0.5, relief=0.08)
    f.rect(0, 9.28, 16, 9.5, (222, 214, 196), tex="plaster005", amp=0.5, relief=0.14)
    f.rect(0, 9.20, 16, 9.28, (200, 190, 168), tex="plaster005", amp=0.5, relief=0.07)

    def window(cx, y0, y1, w=1.1, sill=True):
        f.rect(cx - w / 2 - 0.05, y0 - 0.02, cx + w / 2 + 0.05, y1 + 0.05, (212, 202, 178), tex="plaster005", amp=0.4, relief=0.012)
        f.rect(cx - w / 2, y0, cx + w / 2, y1, (30, 30, 28), relief=-0.10, flat=True)
        f.louvre(cx - w / 2 + 0.01, y0 + 0.01, cx + w / 2 - 0.01, y1 - 0.01, GREEN)
        if sill:
            f.rect(cx - w / 2 - 0.10, y0 - 0.07, cx + w / 2 + 0.10, y0, (206, 200, 186), tex="marble014", amp=0.8, relief=0.07)

    for cx in (1.25, 3.15, 7.9, 10.4, 13.0):
        window(cx, 1.05, 2.60)                              # ground floor
        window(cx, 3.24, 5.62, w=1.2, sill=False)           # French windows on the balcony
    for cx in (3.15, 7.9, 10.4):
        window(cx, 6.40, 8.55, w=1.15, sill=False)          # second floor, on the terrace
    window(14.9, 7.25, 8.45, w=0.9)

    # the front door: aluminium, bronze and gold, with a slatted transom
    cx, w, h = 5.0, 1.30, 2.22
    f.rect(cx - w / 2 - 0.10, 0, cx + w / 2 + 0.10, h + 0.72, (150, 120, 92), tex="marble014", amp=0.9, relief=0.03)
    f.rect(cx - w / 2, 0, cx + w / 2, h + 0.62, (58, 38, 26), relief=-0.14, flat=True)
    y = h + 0.60
    while y > h + 0.08:                                    # transom slats
        f.rect(cx - w / 2 + 0.03, y - 0.05, cx + w / 2 - 0.03, y, (112, 74, 48), tex="wood006", amp=0.3, relief=-0.11, flat=True)
        y -= 0.075
    gold, dark = (196, 162, 100), (30, 24, 20)
    for i in (0, 1):
        a = cx - w / 2 + 0.03 + i * (w / 2 - 0.015)
        b = a + w / 2 - 0.045
        f.rect(a, 0.04, b, h, (92, 60, 40), tex="wood006", amp=0.3, relief=-0.12, flat=True)
        f.glass(a + 0.05, 0.10, b - 0.05, h - 0.06, depth=-0.15, tint=dark)
        t = 0.035

        def bar(x0, y0, x1, y1):
            f.rect(a + x0, y0, a + x1, y1, gold, tex="plaster005", amp=0.25, relief=-0.125, flat=True)
        lw = b - a
        for (u0, v0, u1, v1) in ((0.10, 0.18, lw - 0.10, h - 0.14), (0.20, 0.50, lw - 0.20, h - 0.46)):   # nested frames
            bar(u0, v0, u1, v0 + t); bar(u0, v1 - t, u1, v1); bar(u0, v0, u0 + t, v1); bar(u1 - t, v0, u1, v1)
        bar(lw / 2 - t / 2, 0.10, lw / 2 + t / 2, 0.50)
        bar(lw / 2 - t / 2, h - 0.46, lw / 2 + t / 2, h - 0.06)
        for v in (0.82, 1.14, 1.46):
            bar(0.05, v, 0.20, v + t); bar(lw - 0.20, v, lw - 0.05, v + t)
        bar(0.20 + t, 1.0, lw - 0.20 - t, 1.0 + t); bar(0.20 + t, 1.30, lw - 0.20 - t, 1.30 + t)
        hx = b - 0.09 if i == 0 else a + 0.05
        f.rect(hx, 0.95, hx + 0.04, 1.20, (214, 188, 130), relief=-0.09, flat=True)
    f.rect(cx - w / 2 - 0.16, 0, cx + w / 2 + 0.16, 0.10, (190, 184, 170), tex="marble014", amp=0.8, relief=0.09)   # step
    # small things on the wall: intercom, house number, small high window, vents, conduit
    f.rect(cx + w / 2 + 0.28, 1.30, cx + w / 2 + 0.40, 1.52, (176, 176, 170), relief=0.02, flat=True)
    f.rect(cx + w / 2 + 0.30, 1.40, cx + w / 2 + 0.38, 1.50, (40, 40, 40), relief=0.022, flat=True)
    f.rect(cx - w / 2 - 0.42, 1.66, cx - w / 2 - 0.26, 1.80, (236, 234, 226), relief=0.01, flat=True)
    f.rect(cx - 0.55, 4.86, cx + 0.55, 5.36, (206, 198, 176), tex="plaster005", amp=0.4, relief=0.02)
    f.glass(cx - 0.48, 4.92, cx + 0.48, 5.30, depth=-0.08, tint=(32, 40, 52))
    f.rect(cx - 0.012, 4.92, cx + 0.012, 5.30, (70, 60, 50), relief=-0.05, flat=True)
    for vx, vy in ((6.6, 2.05), (11.7, 1.3), (14.6, 2.3), (9.2, 4.6)):
        f.rect(vx, vy, vx + 0.09, vy + 0.09, (36, 34, 32), relief=-0.03, flat=True)
    f.rect(15.72, 0.95, 15.80, 9.2, (170, 150, 120), tex="concrete035", amp=0.6, relief=0.07, flat=True)    # downpipe
    for yb in (1.6, 3.6, 5.6, 7.6):
        f.rect(15.70, yb, 15.82, yb + 0.04, (120, 104, 84), relief=0.08, flat=True)
    f.rect(6.30, 3.0, 6.325, 3.12, (60, 60, 60), relief=0.02, flat=True)
    f.weather(grime=0.20)
    # the long balcony (a 3D object) keeps the wall under it in shade
    rows = (f.H - np.arange(f.H)) / K
    under = np.clip(1 - (3.12 - rows) / 0.9, 0, 1) * (rows < 3.12)
    f.rgb *= (1 - 0.30 * under ** 1.5)[:, None, None]
    f.shadows()
    return f.image()


def arched_door(f, cx, w, spring, color, fan=False, surround=(206, 184, 146)):
    r = w / 2
    s = 0.10
    f.paint(f.m_arch(cx - r - s, 0, cx + r + s, spring), surround, tex="plaster005", amp=0.8, relief=0.035, metres=1.6)
    # the voussoirs of the arch and the joints of the jambs
    px, py = f.px(cx, spring)
    for k in range(1, 10):
        a = math.pi * k / 10
        m, d = f.mask()
        d.line([px + math.cos(a) * r * K, py - math.sin(a) * r * K, px + math.cos(a) * (r + s) * K, py - math.sin(a) * (r + s) * K], fill=255, width=3)
        f.paint(m, np.array(surround) * 0.55, relief=0.02)
    for y in np.arange(0.32, spring, 0.32):
        for side in (-1, 1):
            x0 = cx + side * r if side > 0 else cx - r - s
            f.rect(x0, y - 0.006, x0 + s, y + 0.006, np.array(surround) * 0.55, relief=0.02)
    f.paint(f.m_arch(cx - r, 0, cx + r, spring), (24, 20, 18), relief=-0.16, flat=True)
    c = np.array(color, float)
    top = spring if fan else spring + r
    leaf = f.m_arch(cx - r + 0.02, 0.03, cx + r - 0.02, spring) if not fan else f.m_rect(cx - r + 0.02, 0.03, cx + r - 0.02, spring - 0.03)
    f.paint(leaf, c, tex="wood006", amp=0.55, relief=-0.13, flat=True, metres=1.2)
    # panels of the two leaves
    lw = r - 0.02
    for i in (0, 1):
        a = cx - r + 0.02 + i * lw
        for (y0, y1) in ((0.18, 0.75), (0.85, min(1.75, spring - 0.12))):
            f.rect(a + 0.07, y0, a + lw - 0.07, y1, c * 0.62, relief=-0.15, flat=True)
            f.rect(a + 0.10, y0 + 0.03, a + lw - 0.10, y1 - 0.03, c * 0.9, tex="wood006", amp=0.55, relief=-0.14, flat=True, metres=1.2)
    f.rect(cx - 0.008, 0.03, cx + 0.008, top - 0.02 if not fan else spring - 0.03, c * 0.35, relief=-0.15, flat=True)
    f.rect(cx + 0.04, 1.02, cx + 0.07, 1.14, (150, 130, 90), relief=-0.10, flat=True)
    if fan:                                                # fanlight with a radial iron grille
        m, d = f.mask()
        d.pieslice([px - (r - 0.02) * K, py - (r - 0.02) * K, px + (r - 0.02) * K, py + (r - 0.02) * K], 180, 360, fill=255)
        f.paint(m, (22, 26, 32), relief=-0.14, flat=True)
        m, d = f.mask()
        for k in range(1, 8):
            a = math.pi * k / 8
            d.line([px, py, px + math.cos(a) * (r - 0.02) * K, py - math.sin(a) * (r - 0.02) * K], fill=255, width=5)
        d.arc([px - r * 0.45 * K, py - r * 0.45 * K, px + r * 0.45 * K, py + r * 0.45 * K], 180, 360, fill=255, width=5)
        f.paint(m, (48, 42, 38), relief=-0.11, flat=True)
        f.rect(cx - r + 0.02, spring - 0.03, cx + r - 0.02, spring + 0.02, c * 0.6, relief=-0.11, flat=True)
    f.rect(cx - r - s - 0.03, 0, cx + r + s + 0.03, 0.09, (170, 160, 140), tex="plaster005", amp=0.8, relief=0.09)


def fronte():
    f = Facade(22.0, 6.5, seed=23)
    # ---------- the house with the switches: 0-10 m
    f.rect(0, 0, 10, 6.5, (232, 208, 140), tex="plaster005", amp=0.55, metres=3.0)
    f.ashlar(0, 0, 10, 3.18, STONE)
    f.ashlar(0, 0, 10, 0.45, np.array(STONE) * 0.86, course=0.45, block=(0.7, 1.2), relief=0.03)
    for x0 in (0.0, 9.62):                                 # corner pilasters
        f.ashlar(x0, 0.45, x0 + 0.38, 3.18, np.array(STONE) * 1.06, course=0.30, block=(0.5, 0.5), relief=0.035)
        f.rect(x0, 3.42, x0 + 0.38, 5.95, (226, 204, 144), tex="plaster005", amp=0.55, relief=0.035)
    f.rect(0, 3.18, 10, 3.30, (204, 184, 148), tex="plaster005", amp=0.8, relief=0.11)      # string course
    f.rect(0, 3.30, 10, 3.42, (190, 170, 134), tex="plaster005", amp=0.8, relief=0.05)
    f.rect(0, 5.95, 10, 6.07, (214, 196, 150), tex="plaster005", amp=0.7, relief=0.06)      # cornice
    f.rect(0, 6.07, 10, 6.22, (222, 206, 164), tex="plaster005", amp=0.7, relief=0.16)
    eave(f, 0, 10, 6.22)
    doors = [(2.89, (104, 78, 56), False), (4.30, (62, 48, 40), True), (5.70, (112, 52, 44), True), (7.11, (96, 40, 36), False)]
    for cx, col, fan in doors:
        arched_door(f, cx, 0.80, 1.95, col, fan)
    for cx in (1.17, 8.83):                                # barred windows of the ground floor
        f.rect(cx - 0.47, 1.02, cx + 0.47, 2.42, (208, 188, 150), tex="plaster005", amp=0.8, relief=0.04)
        f.rect(cx - 0.52, 0.95, cx + 0.52, 1.03, (200, 180, 144), tex="plaster005", amp=0.8, relief=0.08)
        f.rect(cx - 0.35, 1.10, cx + 0.35, 2.30, (26, 24, 22), relief=-0.16, flat=True)
        f.rect(cx - 0.33, 1.12, cx + 0.33, 2.28, (70, 56, 44), tex="wood006", amp=0.5, relief=-0.13, flat=True)
        f.glass(cx - 0.27, 1.18, cx - 0.02, 2.22, depth=-0.15)
        f.glass(cx + 0.02, 1.18, cx + 0.27, 2.22, depth=-0.15)
        f.bars(cx - 0.35, 1.10, cx + 0.35, 2.30, 5, 4, depth=-0.02)
    # upper floor: two small windows and two French windows with a balcony each, grey stone frames
    grey = (176, 172, 162)
    for cx, w, y0, y1 in ((1.17, 0.70, 4.25, 5.55), (8.83, 0.70, 4.25, 5.55), (2.89, 0.95, 3.42, 5.60), (7.11, 0.95, 3.42, 5.60)):
        f.rect(cx - w / 2 - 0.14, y0 - (0.0 if y0 < 3.5 else 0.10), cx + w / 2 + 0.14, y1 + 0.14, grey, tex="plaster005", amp=0.8, relief=0.045)
        f.rect(cx - w / 2 - 0.20, y1 + 0.14, cx + w / 2 + 0.20, y1 + 0.22, np.array(grey) * 1.05, tex="plaster005", amp=0.8, relief=0.10)
        if y0 > 3.5:
            f.rect(cx - w / 2 - 0.20, y0 - 0.16, cx + w / 2 + 0.20, y0 - 0.08, np.array(grey) * 1.05, tex="plaster005", amp=0.8, relief=0.10)
        f.rect(cx - w / 2, y0, cx + w / 2, y1, (24, 22, 20), relief=-0.16, flat=True)
        f.rect(cx - w / 2 + 0.02, y0 + 0.02, cx + w / 2 - 0.02, y1 - 0.02, (66, 46, 36), tex="wood006", amp=0.5, relief=-0.13, flat=True)
        lw = w / 2 - 0.02
        n = 3 if y1 - y0 > 2 else 2
        for i in (0, 1):
            a = cx - w / 2 + 0.02 + i * lw
            ph = (y1 - y0 - 0.04 - 0.07 * (n + 1)) / n
            for j in range(n):
                yb = y0 + 0.02 + 0.07 + j * (ph + 0.07)
                f.glass(a + 0.06, yb, a + lw - 0.06, yb + ph, depth=-0.15, tint=(30, 34, 40))
        f.rect(cx - 0.008, y0 + 0.02, cx + 0.008, y1 - 0.02, (36, 26, 20), relief=-0.12, flat=True)
    f.rect(4.92, 2.45, 5.08, 2.60, (232, 230, 220), relief=0.012, flat=True)      # house number tile
    f.rect(0.40, 0.45, 0.47, 5.95, (150, 140, 126), tex="concrete035", amp=0.6, relief=0.07, flat=True)       # downpipe

    # ---------- the shop house: 10-22 m, white above, red shop front below, shutters down for the night
    f.rect(10, 0, 22, 6.5, (232, 230, 222), tex="plaster005", amp=0.5, metres=3.0)
    f.rect(10, 0, 22, 3.05, (168, 44, 40), tex="plaster005", amp=0.6, metres=3.0)
    f.rect(10, 0, 22, 0.30, (112, 36, 34), tex="plaster005", amp=0.6, relief=0.02)
    f.rect(10, 2.62, 22, 3.05, (150, 36, 34), tex="plaster005", amp=0.5, relief=0.03)      # fascia above the shutters
    f.rect(10, 3.05, 22, 3.17, (224, 222, 214), tex="plaster005", amp=0.5, relief=0.12)
    f.rect(10, 6.05, 22, 6.25, (226, 224, 216), tex="plaster005", amp=0.5, relief=0.14)
    eave(f, 10, 22, 6.25)
    f.rect(10.0, 0, 10.06, 6.05, (150, 148, 140), relief=-0.03)                            # joint between the houses
    for cx in (12.0, 16.0, 20.0):
        f.roller(cx - 1.25, 0, cx + 1.25, 2.62)
    for cx in (14.0, 18.0):
        f.rect(cx - 0.55, 0, cx + 0.55, 2.35, (120, 30, 30), relief=0.02)
        f.rect(cx - 0.47, 0, cx + 0.47, 2.27, (24, 20, 18), relief=-0.14, flat=True)
        f.rect(cx - 0.45, 0.03, cx + 0.45, 2.25, (226, 224, 216), relief=-0.11, flat=True)
        f.glass(cx - 0.37, 1.0, cx + 0.37, 2.15, depth=-0.13, tint=(34, 38, 44))
        f.rect(cx - 0.37, 0.12, cx + 0.37, 0.90, (206, 204, 196), relief=-0.12, flat=True)
        f.rect(cx + 0.30, 1.0, cx + 0.34, 1.14, (120, 120, 116), relief=-0.09, flat=True)
    for cx in (12.0, 15.0, 17.0, 20.0):                   # French windows with white louvred shutters
        f.rect(cx - 0.62, 3.17, cx + 0.62, 5.62, (214, 212, 204), tex="plaster005", amp=0.4, relief=0.015)
        f.rect(cx - 0.55, 3.17, cx + 0.55, 5.55, (30, 30, 28), relief=-0.10, flat=True)
        f.louvre(cx - 0.54, 3.18, cx + 0.54, 5.54, (224, 222, 212))
    f.rect(21.80, 0.3, 21.88, 6.05, (170, 168, 160), tex="concrete035", amp=0.6, relief=0.07, flat=True)
    f.weather(grime=0.24)
    rows = (f.H - np.arange(f.H)) / K
    under = np.clip(1 - (3.05 - rows) / 1.1, 0, 1) * (rows < 3.05)       # under the awnings of the shop
    cols = (np.arange(f.W) / K > 10.0)
    f.rgb *= (1 - 0.32 * under[:, None] ** 1.5 * cols[None, :])[..., None]
    f.shadows()
    return f.image()


def eave(f, x0, x1, y):
    """Terracotta roof tiles (coppi) seen end-on along the eave, with the gutter shadow below."""
    f.rect(x0, y, x1, f.hm, (150, 86, 60), tex="roofingtiles007", amp=0.5, relief=0.22, metres=1.5)
    n = int(round((x1 - x0) / 0.20))
    for i in range(n):
        a = x0 + i * (x1 - x0) / n
        tone = f.rng.normal(1.0, 0.08)
        m, d = f.mask()
        bx = f.box(a + 0.01, y + 0.02, a + (x1 - x0) / n - 0.01, y + 0.26)
        d.pieslice([bx[0], bx[1], bx[2], bx[3] + (bx[3] - bx[1])], 180, 360, fill=255)
        f.paint(m, np.array((186, 108, 76)) * tone, tex="plaster005", amp=0.8, relief=0.26)
        m, d = f.mask()
        bx = f.box(a + 0.045, y + 0.02, a + (x1 - x0) / n - 0.045, y + 0.17)
        d.pieslice([bx[0], bx[1], bx[2], bx[3] + (bx[3] - bx[1])], 180, 360, fill=255)
        f.paint(m, (46, 30, 24), relief=0.20, flat=True)


def main(out):
    a, b = casa(), fronte()
    assert a.size == (2048, 1216) and b.size == (2816, 832), (a.size, b.size)
    p1 = Image.new("RGB", (2048, 2048), (0, 0, 0))
    p1.paste(a, (0, 0))
    p1.paste(b.crop((2048, 0, 2816, 832)), (0, 1216))
    p2 = Image.new("RGB", (2048, 1024), (0, 0, 0))
    p2.paste(b.crop((0, 0, 2048, 832)), (0, 0))
    p1.save(os.path.join(out, "cdv_via_amodeo_1.png"), optimize=True)
    p2.save(os.path.join(out, "cdv_via_amodeo_2.png"), optimize=True)
    a.save(os.path.join(out, "_casa.png"))
    b.save(os.path.join(out, "_fronte.png"))


if __name__ == "__main__":
    main(sys.argv[1])
