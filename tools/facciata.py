"""Drawing kit for building facades painted as one elevation (metres, 128 px/m, drawn at 2x and reduced).

The wall is an orthographic elevation, so every line is straight by construction. Surfaces take their grain
from CC0 photographs (assets/tex_cc0, ambientCG); every element also writes its depth (metres out of the
wall plane, negative = recessed) into a relief map, from which the cast shadows (light from the upper left)
and the ambient occlusion are computed, so that frames, sills, reveals and cornices read as volumes.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
CC0 = os.path.join(HERE, "..", "assets", "tex_cc0")
PXM, SS = 128, 2
K = PXM * SS
_cache = {}


def fbm(h, w, scale, seed, octaves=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / 2 ** o))
        g = rng.random((h // s + 3, w // s + 3))
        out += amp * ndimage.zoom(g, s, order=1)[:h, :w]
        tot += amp
        amp *= 0.5
    return out / tot


def lum(name, metres):
    """Luminance of a CC0 photograph, mean 1, 1024 px of it covering `metres` on the wall; tileable."""
    key = (name, metres)
    if key not in _cache:
        im = Image.open(os.path.join(CC0, name + ".jpg")).convert("L")
        n = max(8, int(metres * K))
        a = np.asarray(im.resize((n, n), Image.LANCZOS)).astype(float)
        _cache[key] = a / a.mean()
    return _cache[key]


def rgbtex(name, metres):
    key = ("rgb", name, metres)
    if key not in _cache:
        n = max(8, int(metres * K))
        _cache[key] = np.asarray(Image.open(os.path.join(CC0, name + ".jpg")).convert("RGB").resize((n, n), Image.LANCZOS)).astype(float)
    return _cache[key]


class Facade:
    def __init__(self, wm, hm, seed=1):
        self.wm, self.hm = wm, hm
        self.W, self.H = int(round(wm * K)), int(round(hm * K))
        self.rgb = np.zeros((self.H, self.W, 3))
        self.relief = np.zeros((self.H, self.W))
        self.flat = np.zeros((self.H, self.W), bool)       # glass, metal: no plaster weathering
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    # --- coordinates: x from the left, y up from the street, metres
    def px(self, x, y):
        return x * K, self.H - y * K

    def box(self, x0, y0, x1, y1):
        return [int(round(x0 * K)), int(round(self.H - y1 * K)), int(round(x1 * K)) - 1, int(round(self.H - y0 * K)) - 1]

    def mask(self):
        m = Image.new("L", (self.W, self.H), 0)
        return m, ImageDraw.Draw(m)

    def m_rect(self, x0, y0, x1, y1):
        m, d = self.mask()
        d.rectangle(self.box(x0, y0, x1, y1), fill=255)
        return m

    def m_arch(self, x0, y0, x1, spring):
        """Opening with a round head: jambs up to `spring`, then a semicircle."""
        m, d = self.mask()
        r = (x1 - x0) / 2
        d.rectangle(self.box(x0, y0, x1, spring), fill=255)
        cx, cy = self.px((x0 + x1) / 2, spring)
        d.ellipse([cx - r * K, cy - r * K, cx + r * K - 1, cy + r * K - 1], fill=255)
        return m

    def tile(self, a, ox=0, oy=0):
        h, w = a.shape[:2]
        ys = (np.arange(self.H) + oy) % h
        xs = (np.arange(self.W) + ox) % w
        return a[ys][:, xs]

    def _fill(self, y0, y1, x0, x1, sub, color, tex, amp, relief, flat, metres, shade):
        col = np.ones((y1 - y0, x1 - x0, 3)) * np.array(color, float)
        if tex:
            g = lum(tex, metres)
            gy = (np.arange(y0, y1) + int(self.rng.integers(0, 4096))) % g.shape[0]
            gx = (np.arange(x0, x1) + int(self.rng.integers(0, 4096))) % g.shape[1]
            col *= (1 + amp * (g[gy][:, gx] - 1))[..., None]
        if shade is not None:
            col *= shade[..., None]
        if sub is None:
            self.rgb[y0:y1, x0:x1] = col
            if relief is not None:
                self.relief[y0:y1, x0:x1] = relief
            self.flat[y0:y1, x0:x1] = flat
        else:
            self.rgb[y0:y1, x0:x1][sub] = col[sub]
            if relief is not None:
                self.relief[y0:y1, x0:x1][sub] = relief
            self.flat[y0:y1, x0:x1][sub] = flat

    def paint(self, m, color, tex=None, amp=1.0, relief=None, flat=False, metres=2.0):
        """Fill the mask with a colour modulated by a photo grain."""
        bb = m.getbbox()
        if not bb:
            return
        x0, y0, x1, y1 = bb
        sub = np.asarray(m.crop(bb)) > 127
        self._fill(y0, y1, x0, x1, sub, color, tex, amp, relief, flat, metres, None)

    def rect(self, x0, y0, x1, y1, color, tex=None, amp=1.0, relief=None, flat=False, metres=2.0, shade=None):
        bx = self.box(x0, y0, x1, y1)
        a, b, c, d = max(0, bx[0]), max(0, bx[1]), min(self.W, bx[2] + 1), min(self.H, bx[3] + 1)
        if c <= a or d <= b:
            return
        self._fill(b, d, a, c, None, color, tex, amp, relief, flat, metres, shade)

    def mul(self, m, f):
        b = (np.asarray(m).astype(float) / 255.0) if isinstance(m, Image.Image) else m
        self.rgb *= (1 - b * (1 - f))[..., None]

    # --- elements
    def louvre(self, x0, y0, x1, y1, color, leaves=2, depth=-0.06, pitch=0.042):
        """Closed louvred shutters (persiane): stiles, rails and slats with a lit upper edge and a shadow line."""
        c = np.array(color, float)
        self.rect(x0, y0, x1, y1, c * 0.55, relief=depth - 0.02, flat=True)
        lw = (x1 - x0) / leaves
        for i in range(leaves):
            a, b = x0 + i * lw + 0.008, x0 + (i + 1) * lw - 0.008
            self.rect(a, y0 + 0.01, b, y1 - 0.01, c, tex="wood006", amp=0.25, relief=depth, flat=True)
            st = 0.06
            ia, ib, iy0, iy1 = a + st, b - st, y0 + 0.01 + st * 1.4, y1 - 0.01 - st
            mid = (iy0 + iy1) / 2
            for (s0, s1) in ((iy0, mid - st / 2), (mid + st / 2, iy1)) if (y1 - y0) > 1.3 else ((iy0, iy1),):
                self.rect(ia, s0, ib, s1, c * 0.5, relief=depth - 0.025, flat=True)
                y = s1
                while y - pitch > s0:
                    self.rect(ia, y - pitch * 0.30, ib, y, c * 1.16, relief=depth - 0.012, flat=True)
                    self.rect(ia, y - pitch * 0.78, ib, y - pitch * 0.30, c * 0.90, relief=depth - 0.018, flat=True)
                    y -= pitch
        self.rect(x0 + (x1 - x0) / 2 - 0.006, y0, x0 + (x1 - x0) / 2 + 0.006, y1, c * 0.35, relief=depth - 0.03, flat=True)

    def glass(self, x0, y0, x1, y1, depth=-0.12, tint=(26, 32, 40)):
        bx = self.box(x0, y0, x1, y1)
        yy, xx = np.mgrid[bx[1]:bx[3] + 1, bx[0]:bx[2] + 1]
        refl = 0.75 + 0.5 * np.clip(np.sin((xx + yy * 0.8) / (0.55 * K)) * 0.5 + 0.5, 0, 1) ** 3
        self.rect(x0, y0, x1, y1, tint, relief=depth, flat=True, shade=refl)

    def bars(self, x0, y0, x1, y1, nx, ny, color=(34, 32, 30), t=0.022, depth=0.03):
        for i in range(nx):
            x = x0 + (i + 0.5) * (x1 - x0) / nx
            self.rect(x - t / 2, y0, x + t / 2, y1, color, relief=depth, flat=True)
        for j in range(ny):
            y = y0 + (j + 0.5) * (y1 - y0) / ny
            self.rect(x0, y - t / 2, x1, y + t / 2, color, relief=depth, flat=True)

    def roller(self, x0, y0, x1, y1, color=(150, 152, 150), depth=-0.10, pitch=0.085):
        """Rolled-down steel shutter of a shop (serranda)."""
        c = np.array(color, float)
        self.rect(x0, y0, x1, y1, c * 0.6, tex="concrete035", amp=0.5, relief=depth, flat=True)
        y = y1
        while y - pitch > y0 + 0.1:
            self.rect(x0 + 0.05, y - pitch * 0.35, x1 - 0.05, y, c * 1.08, tex="concrete035", amp=0.6, relief=depth + 0.012, flat=True)
            self.rect(x0 + 0.05, y - pitch * 0.85, x1 - 0.05, y - pitch * 0.35, c * 0.86, tex="concrete035", amp=0.6, relief=depth + 0.006, flat=True)
            y -= pitch
        self.rect(x0 + 0.05, y0, x1 - 0.05, y0 + 0.1, c * 0.7, relief=depth + 0.02, flat=True)
        for x in (x0, x1 - 0.05):
            self.rect(x, y0, x + 0.05, y1, c * 0.55, relief=depth + 0.03, flat=True)
        self.rect((x0 + x1) / 2 - 0.05, y0 + 0.02, (x0 + x1) / 2 + 0.05, y0 + 0.08, (60, 60, 60), relief=depth + 0.03, flat=True)

    def ashlar(self, x0, y0, x1, y1, color, course=0.30, block=(0.45, 0.85), tex="plaster005", joint=0.012, relief=0.0, amp=0.9):
        """Squared stone blocks in courses, each block with its own tone, dark recessed joints."""
        c = np.array(color, float)
        self.rect(x0, y0, x1, y1, c * 0.45, relief=relief - 0.012)
        y, row = y0, 0
        while y < y1 - 1e-6:
            h = min(course, y1 - y)
            x = x0 - (self.rng.uniform(0, block[0]) if row % 2 else 0)
            while x < x1:
                w = self.rng.uniform(*block)
                a, b = max(x0, x) + joint / 2, min(x1, x + w) - joint / 2
                if b - a > 0.03:
                    tone = self.rng.normal(1.0, 0.06)
                    hue = np.array([1 + self.rng.normal(0, 0.02), 1.0, 1 - self.rng.normal(0, 0.03)])
                    self.rect(a, y + joint / 2, b, y + h - joint / 2, c * tone * hue, tex=tex, amp=amp, relief=relief, metres=1.6)
                x += w
            y += h
            row += 1

    # --- finishing
    def weather(self, grime=0.22, streaks=0.5, base=0.9):
        """Stains and dirt on everything that is not glass or metal: broad blotches, a splash zone at the foot of
        the wall, rain streaks under whatever projects (sills, cornices)."""
        H, W = self.H, self.W
        keep = ~self.flat
        blot = fbm(H, W, 1.6 * K, self.seed + 3)
        fine = fbm(H, W, 0.25 * K, self.seed + 4)
        f = 1 - grime * np.clip(blot * 1.5 - 0.45, 0, 1) - 0.08 * (fine - 0.5)
        rows = (H - np.arange(H)) / K                       # metres above the street
        splash = np.clip(1 - rows / base, 0, 1)[:, None] ** 1.5 * (0.55 + 0.9 * fbm(H, W, 0.5 * K, self.seed + 5))
        f *= 1 - 0.30 * np.clip(splash, 0, 1)
        # rain streaks: start under the lower edge of projecting elements
        edge = (self.relief > 0.03) & ~(np.roll(self.relief, -1, axis=0) > 0.03)
        edge[-1] = False
        src = edge * (self.rng.random((H, W)) < 0.02) * (fbm(H, W, 0.8 * K, self.seed + 9) > 0.45)
        st = np.zeros((H, W))
        L = int(0.9 * K)
        acc = src.astype(float)
        for i in range(1, L, 3):
            acc = np.roll(acc, 3, axis=0)
            acc[:3] = 0
            st += acc * (1 - i / L)
        st = ndimage.gaussian_filter(st, (6, 4.5))
        st = np.clip(st / (st.max() + 1e-9) * 3.0, 0, 1)
        f *= 1 - 0.20 * streaks * st
        tint = np.stack([f, f * (1 + 0.01 * (1 - f)), f * (1 + 0.03 * (1 - f))], axis=2)   # dirt is slightly cold
        self.rgb[keep] *= tint[keep]

    def shadows(self, strength=0.5, reach=0.5, ao=0.22):
        r = self.relief
        lit = np.ones(r.shape, bool)
        n = int(reach * K)
        for s in range(2, n, 2):                            # light from the upper left, about 45 degrees down
            sh = np.roll(np.roll(r, s, axis=0), int(s * 0.55), axis=1)
            sh[:s] = -9
            sh[:, :int(s * 0.55)] = -9
            lit &= ~(sh - r > s / K * 0.9)
        shadow = ndimage.gaussian_filter((~lit).astype(float), 2.5)
        occ = np.clip(ndimage.gaussian_filter(r, 0.05 * K) - r, 0, 0.1) / 0.1
        f = (1 - strength * shadow) * (1 - ao * occ)
        self.rgb *= np.stack([f, f, f * 1.0 + (1 - f) * 0.06], axis=2)

    def image(self):
        g = self.rng.normal(1.0, 0.018, (self.H, self.W))
        im = Image.fromarray(np.clip(self.rgb * g[..., None], 0, 255).astype(np.uint8))
        return im.resize((self.W // SS, self.H // SS), Image.LANCZOS)
