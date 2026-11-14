"""Painted and inlaid surfaces of the inside of the sanctuary of Tindari (14/11/2026).

Original work in the manner of the real church (Ed's photographs of 29/10 show a gilded lattice vault with
frescoed skies in shaped gold frames, gold-ground walls, a blue band with AVE MARIA GRATIA PLENA under the
drum): nothing is copied from the frescoes themselves. Marbles and wood take their grain from CC0
photographs (assets/tex_cc0, ambientCG). Everything is drawn at 4x and reduced.

Big pieces are cut into a grid of regions of at most 256 px (grid()), which the models lay side by side.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.spatial import cKDTree

CC0 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "tex_cc0")
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
GOLD, GOLD_D, GOLD_L = (204, 160, 72), (140, 100, 40), (244, 214, 130)
BLUE, RED, IVORY = (36, 58, 128), (150, 36, 34), (236, 226, 204)
GRIDS = {}          # name -> (nx, ny)


def photo(name, size, crop=None):
    im = Image.open(os.path.join(CC0, name + ".jpg")).convert("RGB")
    if crop:
        im = im.crop(crop)
    return np.asarray(im.resize((size, size), Image.LANCZOS)).astype(float)


def fbm(h, w, scale, seed, octaves=4):
    rng = np.random.default_rng(seed)
    out, amp, tot = np.zeros((h, w)), 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / 2 ** o))
        out += amp * ndimage.zoom(rng.random((h // s + 3, w // s + 3)), s, order=3)[:h, :w]
        tot += amp
        amp *= 0.5
    return out / tot


def marble(name, tint=None, size=256, gain=1.0, seed=0):
    a = photo(name, size)
    if tint is not None:
        g = a.mean(axis=2, keepdims=True) / a.mean()
        a = np.array(tint, float)[None, None] * (0.25 + 0.75 * g)
    return np.clip(a * gain, 0, 255)


def arr(im):
    return np.asarray(im.convert("RGB")).astype(float)


def down(a, w, h):
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)).astype(float)


# ------------------------------------------------------------------------------------ marble floors
def inlay(size, shapes, base):
    """shapes: list of (polygon points in 0..1, marble array). Drawn at 4x; a dark hairline joint around each."""
    S = size * 4
    out = np.asarray(Image.fromarray(base.astype(np.uint8)).resize((S, S), Image.LANCZOS)).astype(float)
    joints = Image.new("L", (S, S), 0)
    dj = ImageDraw.Draw(joints)
    for pts, mat in shapes:
        m = Image.new("L", (S, S), 0)
        p = [(x * S, y * S) for x, y in pts]
        ImageDraw.Draw(m).polygon(p, fill=255)
        mk = np.asarray(m) > 127
        big = np.asarray(Image.fromarray(mat.astype(np.uint8)).resize((S, S), Image.LANCZOS)).astype(float)
        out[mk] = big[mk]
        dj.line(p + [p[0]], fill=255, width=3)
    out *= (1 - 0.55 * np.asarray(joints.filter(ImageFilter.GaussianBlur(1.2))) / 255.0)[..., None]
    return down(out, size, size)


def floor_stars():
    """2 x 2 m: two by two octagons of black marble with an eight-pointed star of yellow Siena, red fillets."""
    white, black = marble("marble004", gain=0.97), marble("marble006", gain=1.25)
    yellow, red = marble("marble014", tint=(226, 190, 120)), marble("marble008", tint=(150, 50, 40))
    shapes = []
    for cx in (0.25, 0.75):
        for cy in (0.25, 0.75):
            def ring(r, n=8, rot=math.pi / 8):
                return [(cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]
            shapes.append((ring(0.232), red))
            shapes.append((ring(0.205), black))
            star = []
            for k in range(16):
                r = 0.185 if k % 2 == 0 else 0.078
                star.append((cx + r * math.cos(math.pi * k / 8), cy + r * math.sin(math.pi * k / 8)))
            shapes.append((star, yellow))
            shapes.append((ring(0.035, 8, 0), red))
    for c in (0.0, 0.5, 1.0):                                # small red squares where four octagons meet
        for e in (0.0, 0.5, 1.0):
            shapes.append(([(c - 0.045, e), (c, e - 0.045), (c + 0.045, e), (c, e + 0.045)], red))
    return inlay(256, shapes, white)


def floor_diamonds():
    white, black, red = marble("marble004", gain=0.97), marble("marble006", gain=1.25), marble("marble008", tint=(150, 50, 40))
    grey = marble("marble012", gain=0.95) if os.path.exists(os.path.join(CC0, "marble012.jpg")) else marble("marble004", gain=0.8)
    shapes = []
    for cx in (0.25, 0.75):
        for cy in (0.25, 0.75):
            q = 0.25
            shapes.append(([(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)], red))
            q = 0.222
            shapes.append(([(cx - q, cy - q), (cx + q, cy - q), (cx + q, cy + q), (cx - q, cy + q)], white))
            shapes.append(([(cx - 0.20, cy), (cx, cy - 0.20), (cx + 0.20, cy), (cx, cy + 0.20)], grey))
            shapes.append(([(cx - 0.13, cy), (cx, cy - 0.13), (cx + 0.13, cy), (cx, cy + 0.13)], black))
    return inlay(256, shapes, white)


# ------------------------------------------------------------------------------------ gold
def gilded(size=128, seed=3):
    n = fbm(size, size, 40, seed)
    a = np.array(GOLD, float)[None, None] * (0.82 + 0.36 * n[..., None])
    yy = np.linspace(0, 1, size)[:, None]
    a *= (1.08 - 0.16 * yy)[..., None]
    return np.clip(a, 0, 255)


def lattice(size=256, cells=4, ground=GOLD, line=GOLD_D, flower=RED, seed=5, dots=True):
    """Gold-ground diaper: a diagonal trellis with a small flower in every cell, as on the vault and the walls."""
    S = size * 4
    im = Image.new("RGB", (S, S), ground)
    d = ImageDraw.Draw(im)
    c = S / cells
    for k in range(-cells, 2 * cells + 1):
        d.line([(k * c, 0), (k * c + S, S)], fill=line, width=int(S / 110))
        d.line([(k * c, 0), (k * c - S, S)], fill=line, width=int(S / 110))
        d.line([(k * c + 5, 0), (k * c + S + 5, S)], fill=GOLD_L, width=2)
        d.line([(k * c + 5, 0), (k * c - S + 5, S)], fill=GOLD_L, width=2)
    for i in range(cells + 1):
        for j in range(2 * cells + 1):
            x, y = i * c + (c / 2 if j % 2 else 0), j * c / 2
            if j % 2 == 0:                                   # knots on the crossings
                d.ellipse([x - c * .07, y - c * .07, x + c * .07, y + c * .07], fill=GOLD_L, outline=line, width=3)
            elif dots:                                       # four-petalled flower in the cell
                for a in range(4):
                    px, py = x + math.cos(a * math.pi / 2) * c * .11, y + math.sin(a * math.pi / 2) * c * .11
                    d.ellipse([px - c * .075, py - c * .075, px + c * .075, py + c * .075], fill=flower)
                d.ellipse([x - c * .05, y - c * .05, x + c * .05, y + c * .05], fill=GOLD_L)
    a = down(arr(im), size, size)
    return np.clip(a * (0.86 + 0.28 * fbm(size, size, 64, seed)[..., None]), 0, 255)


def stucco(size=256, seed=8):
    """Ivory wall with a painted panel: a thin gold fillet and a faint marbled field."""
    S = size
    a = photo("plaster002", S) / photo("plaster002", S).mean() * np.array((232, 220, 192))
    a = np.clip(a, 0, 255)
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    return arr(im) * (0.94 + 0.12 * fbm(S, S, 80, seed)[..., None])


def coffers(size=256):
    """2 x 2 m of ceiling: four deep coffers with a gilded rosette on blue, cream ribs with gold fillets."""
    S = size * 4
    im = Image.new("RGB", (S, S), (226, 214, 186))
    d = ImageDraw.Draw(im)
    h = S // 2
    for i in (0, 1):
        for j in (0, 1):
            x, y = i * h, j * h
            steps = [(0.10, (150, 112, 50)), (0.13, GOLD), (0.16, (120, 100, 70)), (0.19, (196, 184, 158)), (0.24, (30, 46, 100)), (0.26, (40, 60, 124))]
            for f, col in steps:
                d.rectangle([x + f * h, y + f * h, x + h - f * h, y + h - f * h], fill=col)
            # shadow on the top and left inner faces of the recess (light from below)
            d.polygon([(x + .16 * h, y + .16 * h), (x + .84 * h, y + .16 * h), (x + .76 * h, y + .24 * h), (x + .24 * h, y + .24 * h)], fill=(120, 108, 86))
            d.polygon([(x + .16 * h, y + .16 * h), (x + .24 * h, y + .24 * h), (x + .24 * h, y + .76 * h), (x + .16 * h, y + .84 * h)], fill=(150, 138, 112))
            cx, cy = x + h / 2, y + h / 2
            for k in range(8):
                a = k * math.pi / 4
                px, py = cx + math.cos(a) * h * .11, cy + math.sin(a) * h * .11
                d.ellipse([px - h * .07, py - h * .07, px + h * .07, py + h * .07], fill=GOLD, outline=GOLD_D, width=3)
            d.ellipse([cx - h * .06, cy - h * .06, cx + h * .06, cy + h * .06], fill=GOLD_L, outline=GOLD_D, width=3)
    a = down(arr(im.filter(ImageFilter.GaussianBlur(1.5))), size, size)
    return np.clip(a * (0.9 + 0.2 * fbm(size, size, 50, 4)[..., None]), 0, 255)


# ------------------------------------------------------------------------------------ frescoes
def sky(S, seed, centre=(0.5, 0.45)):
    """A painted heaven: blue at the rim, a golden glory in the middle, banks of cloud lit from the glory."""
    yy, xx = np.mgrid[0:S, 0:S] / S
    r = np.hypot(xx - centre[0], yy - centre[1])
    glory = np.clip(1 - r / 0.62, 0, 1) ** 1.6
    blue = np.array((70, 118, 186.0))[None, None] * (1.05 - 0.45 * yy[..., None] * 0 - 0.25 * r[..., None])
    warm = np.array((255, 232, 170.0))[None, None]
    a = blue * (1 - glory[..., None]) + warm * glory[..., None]
    # rays
    ang = np.arctan2(yy - centre[1], xx - centre[0])
    rays = (np.sin(ang * 14 + fbm(S, S, S / 3, seed + 1) * 3) * 0.5 + 0.5) ** 3 * np.clip(1 - r / 0.75, 0, 1)
    a += 26 * rays[..., None] * np.array((1.0, 0.9, 0.6))
    # clouds: two layers of billows, denser away from the glory
    for k, (thr, scale) in enumerate(((0.54, S / 2.2), (0.60, S / 4.5))):
        n = fbm(S, S, scale, seed + 10 + k, 5)
        dens = np.clip((n - thr + 0.16 * np.clip(r - 0.12, 0, 1)) / 0.10, 0, 1)
        # shading: the side of a billow turned to the glory is light, the other side violet grey
        gy, gx = np.gradient(ndimage.gaussian_filter(n, S / 90))
        to_c = -(gx * (xx - centre[0]) + gy * (yy - centre[1])) / (r + 1e-3)
        lit = np.clip(0.55 + to_c * S * 0.9, 0, 1)
        cloud = np.array((250, 240, 222.0))[None, None] * lit[..., None] + np.array((172, 170, 192.0))[None, None] * (1 - lit[..., None])
        cloud = cloud * (1 - 0.35 * glory[..., None]) + warm * 0.35 * glory[..., None]
        a = a * (1 - dens[..., None]) + cloud * dens[..., None]
    return np.clip(a, 0, 255)


def dove(d, cx, cy, s, col=(255, 252, 240)):
    """The dove of the Holy Spirit seen from below, wings spread."""
    d.ellipse([cx - s * .10, cy - s * .28, cx + s * .10, cy + s * .22], fill=col)                       # body
    d.ellipse([cx - s * .07, cy - s * .40, cx + s * .07, cy - s * .24], fill=col)                       # head
    d.polygon([(cx, cy - s * .46), (cx - s * .02, cy - s * .40), (cx + s * .02, cy - s * .40)], fill=(230, 170, 60))
    for sg in (-1, 1):
        wing = [(cx + sg * s * .06, cy - s * .16), (cx + sg * s * .36, cy - s * .38), (cx + sg * s * .62, cy - s * .30),
                (cx + sg * s * .58, cy - s * .16), (cx + sg * s * .50, cy - s * .04), (cx + sg * s * .36, cy + s * .04), (cx + sg * s * .08, cy + s * .08)]
        d.polygon(wing, fill=col)
        for k in range(5):
            x0, y0 = cx + sg * s * (.20 + .08 * k), cy - s * (.24 + .02 * k)
            d.line([(x0, y0), (x0 + sg * s * .10, y0 + s * .26)], fill=(206, 200, 196), width=max(1, int(s * .012)))
    d.polygon([(cx - s * .09, cy + s * .16), (cx - s * .16, cy + s * .46), (cx, cy + s * .38), (cx + s * .16, cy + s * .46), (cx + s * .09, cy + s * .16)], fill=col)


def star_pts(cx, cy, r0, r1, n, rot=-math.pi / 2):
    return [(cx + (r0 if k % 2 == 0 else r1) * math.cos(rot + math.pi * k / n), cy + (r0 if k % 2 == 0 else r1) * math.sin(rot + math.pi * k / n)) for k in range(2 * n)]


def shaped(S, m=0.07):
    """Mixtilinear frame of a vault panel: a rectangle with rounded lobes on its four sides and cut corners."""
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    a, b = m * S, S - m * S
    k = 0.10 * S
    d.polygon([(a + k, a), (b - k, a), (b - k, a + k * .6), (b, a + k * .6), (b, b - k * .6), (b - k, b - k * .6), (b - k, b), (a + k, b),
               (a + k, b - k * .6), (a, b - k * .6), (a, a + k * .6), (a + k, a + k * .6)], fill=255)
    r = 0.20 * S
    for cx, cy in ((S / 2, a + k * .2), (S / 2, b - k * .2)):
        d.ellipse([cx - r, cy - r * .55, cx + r, cy + r * .55], fill=255)
    for cx, cy in ((a + k * .2, S / 2), (b - k * .2, S / 2)):
        d.ellipse([cx - r * .45, cy - r, cx + r * .45, cy + r], fill=255)
    return im


def fresco(kind, seed, size=512):
    """Vault panel: a heaven in a shaped gilded frame on the gold trellis. kind: 0 dove, 1 crown of twelve stars
    over the crescent, 2 radiant cross."""
    S = size * 2
    a = sky(S, seed)
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    cx, cy = S * 0.5, S * 0.45
    for rr, al in ((0.20, 60), (0.15, 90), (0.10, 140)):
        d.ellipse([cx - rr * S, cy - rr * S, cx + rr * S, cy + rr * S], fill=(255, 244, 200, al))
    if kind == 0:
        dove(d, cx, cy, S * 0.26)
    elif kind == 1:
        for k in range(12):
            an = 2 * math.pi * k / 12
            d.polygon(star_pts(cx + math.cos(an) * S * .17, cy + math.sin(an) * S * .17, S * .026, S * .011, 5), fill=(255, 236, 150, 255), outline=(190, 140, 50, 255))
        d.ellipse([cx - S * .085, cy - S * .085, cx + S * .085, cy + S * .085], fill=(250, 246, 230, 255))
        d.ellipse([cx - S * .085, cy - S * .125, cx + S * .085, cy + S * .045], fill=(255, 238, 190, 255))
    else:
        w = S * .022
        d.rectangle([cx - w, cy - S * .15, cx + w, cy + S * .17], fill=(255, 240, 170, 255), outline=(190, 140, 50, 255), width=3)
        d.rectangle([cx - S * .10, cy - S * .06 - w, cx + S * .10, cy - S * .06 + w], fill=(255, 240, 170, 255), outline=(190, 140, 50, 255), width=3)
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    a = arr(im)
    # the surface of a fresco: plaster grain, a few hairline cracks, brush-soft colour
    a *= (0.93 + 0.14 * fbm(S, S, 6, seed + 3, 2)[..., None]) * (0.95 + 0.1 * fbm(S, S, S / 4, seed + 4)[..., None])
    m = np.asarray(shaped(S)).astype(float) / 255
    ground = np.asarray(Image.fromarray(lattice(256, 4, seed=seed).astype(np.uint8)).resize((S // 2, S // 2), Image.LANCZOS)).astype(float)
    ground = np.tile(ground, (2, 2, 1))
    edge = ndimage.gaussian_filter(m, 1.0)
    inner = ndimage.binary_erosion(m > 0.5, iterations=int(S * 0.022)).astype(float)
    mid = ndimage.binary_erosion(m > 0.5, iterations=int(S * 0.011)).astype(float)
    out = ground * (1 - edge[..., None])
    # frame: a gold moulding, light on the outer half and dark on the inner half, with a red fillet
    frame_c = np.array(GOLD_L, float) * (m - mid)[..., None] + np.array(GOLD_D, float) * (mid - inner)[..., None]
    out = out + frame_c + a * inner[..., None]
    sh = np.clip(ndimage.gaussian_filter(np.roll(np.roll(m, 10, 0), 8, 1), 8) - m, 0, 1)
    out *= (1 - 0.45 * sh)[..., None]
    return down(out, size, size)


def dome_quarter(seed, size=512):
    """A quarter of the dome unrolled: u = angle (90 degrees), v = from the drum (bottom) to the oculus (top).
    Heaven with rings of cloud, brighter towards the lantern; a gilded rib on the left edge."""
    S = size * 2
    yy, xx = np.mgrid[0:S, 0:S] / S
    t = 1 - yy                                           # 0 at the drum, 1 at the oculus
    blue = np.array((84, 128, 190.0))
    warm = np.array((255, 236, 180.0))
    a = blue[None, None] * (1 - t[..., None] ** 1.1) + warm[None, None] * t[..., None] ** 1.1
    n = fbm(S, S, S / 3, seed, 5)
    n2 = np.concatenate([n[:, :S // 2], n[:, S // 2:][:, ::-1]], axis=1)
    band = np.exp(-((t - 0.30) / 0.16) ** 2) + 0.35 * np.exp(-((t - 0.62) / 0.08) ** 2)
    dens = np.clip((n - 0.62 + 0.30 * band) / 0.10, 0, 1)
    gy = np.gradient(ndimage.gaussian_filter(n, S / 80))[0]
    lit = np.clip(0.55 + gy * S * 0.8, 0, 1)             # lit from above (the lantern)
    cloud = np.array((250, 240, 224.0))[None, None] * lit[..., None] + np.array((156, 146, 172.0))[None, None] * (1 - lit[..., None])
    a = a * (1 - dens[..., None]) + cloud * dens[..., None]
    del n2
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    rng = np.random.default_rng(seed)
    for k in range(7):                                    # gold stars scattered in the blue near the drum
        x, y = rng.uniform(0.12, 0.92) * S, rng.uniform(0.80, 0.95) * S
        d.polygon(star_pts(x, y, S * .014, S * .006, 5), fill=(250, 226, 140, 255))
    a = arr(im.filter(ImageFilter.GaussianBlur(1.0)))
    a *= (0.93 + 0.14 * fbm(S, S, 6, seed + 3, 2)[..., None])
    rib = np.clip(1 - np.abs(xx - 0.0) / 0.035, 0, 1) + np.clip(1 - np.abs(xx - 1.0) / 0.035, 0, 1)
    ribc = np.array(GOLD, float)[None, None] * (0.8 + 0.4 * np.clip(1 - np.abs(xx - 0.012) / 0.02, 0, 1))[..., None]
    k = np.clip(rib * 3, 0, 1)[..., None]
    a = a * (1 - k) + ribc * k
    base = (yy > 0.965)[..., None]
    a = a * (1 - base) + np.array(GOLD_D, float)[None, None] * base
    return down(a, size, size)


# ------------------------------------------------------------------------------------ mosaic
def tesserae(img, cell=3.2, seed=0, grout=(70, 62, 52), jitter=0.10):
    """Turns a drawing (array at 4x the final size) into a mosaic at the final size: every tessera takes the
    colour under its centre with a little variation, a darker joint in between. cell = tessera in final px."""
    H4, W4 = img.shape[:2]
    H, W = H4 // 2, W4 // 2                               # work at 2x the final size
    src = down(img, W, H)
    rng = np.random.default_rng(seed)
    c = cell * 2
    gy, gx = np.mgrid[0:int(H / c) + 2, 0:int(W / c) + 2]
    pts = np.stack([(gx + 0.5 + (gy % 2) * 0.5) * c, (gy + 0.5) * c], axis=-1).reshape(-1, 2)
    pts += rng.normal(0, c * 0.13, pts.shape)
    tree = cKDTree(pts)
    yy, xx = np.mgrid[0:H, 0:W]
    dist, idx = tree.query(np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], axis=1), k=2)
    px = np.clip(pts[:, 0].astype(int), 0, W - 1)
    py = np.clip(pts[:, 1].astype(int), 0, H - 1)
    cols = src[py, px] * rng.normal(1.0, jitter, (len(pts), 1)) * (1 + rng.normal(0, 0.025, (len(pts), 3)))
    out = cols[idx[:, 0]].reshape(H, W, 3)
    g = np.clip(1 - (dist[:, 1] - dist[:, 0]) / 1.3, 0, 1).reshape(H, W)
    out = out * (1 - 0.8 * g[..., None]) + np.array(grout, float)[None, None] * 0.8 * g[..., None]
    return down(out, W // 2, H // 2)


def border(d, x0, y0, x1, y1, t, cols=(RED, IVORY, BLUE)):
    d.rectangle([x0, y0, x1, y1], fill=cols[0])
    d.rectangle([x0 + t * .28, y0 + t * .28, x1 - t * .28, y1 - t * .28], fill=cols[1])
    d.rectangle([x0 + t * .45, y0 + t * .45, x1 - t * .45, y1 - t * .45], fill=cols[2])
    n = int((x1 - x0) / (t * .9))
    for k in range(n):                                      # running lozenges on the blue band
        cx = x0 + t + (x1 - x0 - 2 * t) * (k + .5) / n
        for cy in (y0 + t * .72, y1 - t * .72):
            d.polygon([(cx - t * .2, cy), (cx, cy - t * .14), (cx + t * .2, cy), (cx, cy + t * .14)], fill=GOLD_L)
    n = int((y1 - y0) / (t * .9))
    for k in range(n):
        cy = y0 + t + (y1 - y0 - 2 * t) * (k + .5) / n
        for cx in (x0 + t * .72, x1 - t * .72):
            d.polygon([(cx - t * .14, cy), (cx, cy - t * .2), (cx + t * .14, cy), (cx, cy + t * .2)], fill=GOLD_L)
    d.rectangle([x0 + t, y0 + t, x1 - t, y1 - t], fill=GOLD)


def vine(d, x0, x1, yc, amp, s, flip=1):
    """A scroll of vine with leaves and roses along a wave."""
    pts = [(x, yc + flip * amp * math.sin((x - x0) / (x1 - x0) * math.pi * 3)) for x in np.linspace(x0, x1, 80)]
    d.line(pts, fill=(52, 96, 56), width=int(s * .035), joint="curve")
    for k in range(1, 12):
        x, y = pts[int(k * 79 / 12)]
        up = -1 if k % 2 else 1
        lx, ly = x + s * .05, y + up * s * .16
        d.line([(x, y), (lx, ly)], fill=(52, 96, 56), width=int(s * .02))
        if k % 3 == 0:
            for a in range(5):
                px, py = lx + math.cos(a * 1.257) * s * .055, ly + math.sin(a * 1.257) * s * .055
                d.ellipse([px - s * .05, py - s * .05, px + s * .05, py + s * .05], fill=(172, 44, 48))
            d.ellipse([lx - s * .035, ly - s * .035, lx + s * .035, ly + s * .035], fill=(236, 200, 110))
        else:
            d.polygon([(lx - s * .08, ly), (lx, ly - up * -s * .03 - s * .07), (lx + s * .10, ly + up * s * .02), (lx, ly + s * .07)], fill=(70, 128, 70))


def fleur(d, cx, cy, s, col=IVORY):
    d.ellipse([cx - s * .10, cy - s * .50, cx + s * .10, cy + s * .12], fill=col)
    for sg in (-1, 1):
        d.pieslice([cx + sg * s * .06 - s * .26, cy - s * .30, cx + sg * s * .06 + s * .26, cy + s * .22], 180 if sg < 0 else 270, 270 if sg < 0 else 360, fill=col)
        d.ellipse([cx + sg * s * .30 - s * .08, cy - s * .08, cx + sg * s * .30 + s * .08, cy + s * .10], fill=col)
    d.rectangle([cx - s * .22, cy + s * .12, cx + s * .22, cy + s * .19], fill=GOLD_L)
    d.polygon([(cx - s * .08, cy + s * .19), (cx + s * .08, cy + s * .19), (cx + s * .14, cy + s * .42), (cx, cy + s * .34), (cx - s * .14, cy + s * .42)], fill=col)


def mosaic_panel(kind, seed, w=512, h=256):
    """Gold-ground wall mosaic, 3.6 x 1.8 m: a blue medallion with a Marian emblem between scrolls of roses.
    0 monogram M crowned, 1 Stella Maris (star, sea, boat), 2 lilies, 3 radiant cross with alpha and omega."""
    W, H = w * 4, h * 4
    im = Image.new("RGB", (W, H), GOLD)
    d = ImageDraw.Draw(im)
    t = H * 0.085
    border(d, 0, 0, W - 1, H - 1, t)
    cx, cy, r = W / 2, H / 2, H * 0.36
    d.ellipse([cx - r * 1.08, cy - r * 1.08, cx + r * 1.08, cy + r * 1.08], fill=RED)
    d.ellipse([cx - r * 1.03, cy - r * 1.03, cx + r * 1.03, cy + r * 1.03], fill=IVORY)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 48, 112))
    d.ellipse([cx - r * .82, cy - r * .82, cx + r * .82, cy + r * .82], fill=BLUE)
    if kind == 0:
        f = ImageFont.truetype(SERIF, int(r * 1.05))
        d.text((cx, cy + r * .18), "M", font=f, fill=GOLD_L, anchor="mm", stroke_width=6, stroke_fill=GOLD_D)
        d.polygon([(cx - r * .32, cy - r * .36), (cx - r * .36, cy - r * .66), (cx - r * .18, cy - r * .50), (cx, cy - r * .74), (cx + r * .18, cy - r * .50),
                   (cx + r * .36, cy - r * .66), (cx + r * .32, cy - r * .36)], fill=GOLD_L, outline=GOLD_D)
        for k in range(12):
            an = 2 * math.pi * k / 12
            d.polygon(star_pts(cx + math.cos(an) * r * .91, cy + math.sin(an) * r * .91, r * .07, r * .03, 5), fill=IVORY)
    elif kind == 1:
        d.polygon(star_pts(cx, cy - r * .34, r * .34, r * .13, 8), fill=GOLD_L, outline=GOLD_D)
        for j in range(3):
            y = cy + r * (.38 + .16 * j)
            pts = [(x, y + r * .05 * math.sin((x - cx) / r * 9 + j)) for x in np.linspace(cx - r * .74, cx + r * .74, 60) if abs(x - cx) < r * (.78 - .14 * j)]
            d.line(pts, fill=(150, 196, 220) if j % 2 == 0 else IVORY, width=int(r * .06))
        d.polygon([(cx - r * .34, cy + r * .16), (cx + r * .34, cy + r * .16), (cx + r * .24, cy + r * .32), (cx - r * .24, cy + r * .32)], fill=(150, 90, 50))
        d.line([(cx, cy + r * .16), (cx, cy - r * .06)], fill=(150, 90, 50), width=int(r * .04))
        d.polygon([(cx + r * .03, cy - r * .04), (cx + r * .26, cy + r * .12), (cx + r * .03, cy + r * .12)], fill=IVORY)
    elif kind == 2:
        for dx, s, dy in ((-0.34, 0.62, 0.12), (0, 0.82, 0), (0.34, 0.62, 0.12)):
            fleur(d, cx + dx * r, cy + dy * r, r * s, IVORY if dx == 0 else GOLD_L)
    else:
        for k in range(24):
            an = 2 * math.pi * k / 24
            d.line([(cx + math.cos(an) * r * .2, cy + math.sin(an) * r * .2), (cx + math.cos(an) * r * (.74 if k % 2 else .6), cy + math.sin(an) * r * (.74 if k % 2 else .6))], fill=GOLD, width=int(r * .03))
        wv = r * .085
        d.rectangle([cx - wv, cy - r * .62, cx + wv, cy + r * .66], fill=GOLD_L, outline=GOLD_D, width=4)
        d.rectangle([cx - r * .42, cy - r * .22 - wv, cx + r * .42, cy - r * .22 + wv], fill=GOLD_L, outline=GOLD_D, width=4)
        f = ImageFont.truetype(SERIF, int(r * .34))
        d.text((cx - r * .52, cy + r * .30), "A", font=f, fill=IVORY, anchor="mm")
        d.text((cx + r * .52, cy + r * .30), "Ω", font=f, fill=IVORY, anchor="mm")
    for sg in (-1, 1):
        xa, xb = (t * 1.5, cx - r * 1.2) if sg < 0 else (cx + r * 1.2, W - t * 1.5)
        vine(d, xa, xb, cy, H * .17, H * .5, flip=sg)
    a = arr(im.filter(ImageFilter.GaussianBlur(1.0)))
    out = tesserae(a, cell=2.6, seed=seed)
    return np.clip(out * (0.9 + 0.2 * fbm(h, w, 90, seed + 1)[..., None]), 0, 255)


# ------------------------------------------------------------------------------------ stained glass
def glass(kind, seed, w=256, h=512, stone=(214, 202, 176)):
    """Round-headed leaded window, 1.5 x 3 m: coloured border, pale lozenge quarries, a medallion with an emblem.
    kind: 'croce', 'giglio', 'corona', 'stella8', 'calice', 'luna', 'stella', 'sole'."""
    W, H = w * 4, h * 4
    rng = np.random.default_rng(seed)
    lead = (18, 16, 16)
    im = Image.new("RGB", (W, H), lead)
    d = ImageDraw.Draw(im)
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    mx = W * 0.09
    r = W / 2 - mx
    dm.rectangle([mx, mx + r, W - mx, H - mx * 0.9], fill=255)
    dm.ellipse([mx, mx, W - mx, mx + 2 * r], fill=255)
    pale = [(214, 200, 140), (176, 204, 170), (170, 196, 214), (222, 214, 190), (200, 180, 120)]
    q = W / 7.0
    lw = int(W * .012)
    for i in range(-2, 9):                                  # lozenge quarries
        for j in range(-1, int(H / (q * .62)) + 2):
            cx, cy = (i + (j % 2) * .5) * q, j * q * .62
            c = np.array(pale[int(rng.integers(0, len(pale)))]) * rng.uniform(0.85, 1.08)
            d.polygon([(cx - q / 2 + lw, cy), (cx, cy - q * .62 + lw), (cx + q / 2 - lw, cy), (cx, cy + q * .62 - lw)], fill=tuple(int(v) for v in c))
    # border of alternating ruby and blue pieces following the outline
    inner = m.filter(ImageFilter.MinFilter(1 + 2 * int(W * .028)))
    for _ in range(2):
        inner = inner.filter(ImageFilter.MinFilter(1 + 2 * int(W * .014)))
    bm = np.asarray(m).astype(int) - np.asarray(inner).astype(int) > 127
    a = arr(im)
    yy, xx = np.mgrid[0:H, 0:W]
    ang_top = np.arctan2(yy - (mx + r), xx - W / 2)
    seg = np.where(yy < mx + r, (ang_top * r / (q * .8)).astype(int), ((yy - mx - r) / (q * .8)).astype(int) + 100 * (xx > W / 2))
    colb = np.where((seg % 2 == 0)[..., None], np.array((164, 30, 36))[None, None], np.array((36, 62, 150))[None, None]).astype(float)
    sgrad = np.abs(np.diff(seg, axis=0, prepend=seg[:1])) + np.abs(np.diff(seg, axis=1, prepend=seg[:, :1])) > 0
    sgrad = ndimage.binary_dilation(sgrad, iterations=max(1, lw // 2))
    a[bm] = colb[bm]
    a[bm & sgrad] = lead
    edge = ndimage.binary_dilation(np.asarray(inner) > 127, iterations=lw) & ~(np.asarray(inner) > 127)
    a[edge] = lead
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    # medallion
    cx, cy, R = W / 2, H * 0.44, W * 0.30
    ground = (150, 28, 36) if kind in ("luna", "stella", "sole", "croce", "calice") and kind != "luna" else (30, 54, 140)
    if kind in ("luna", "stella"):
        ground = (24, 44, 128)
    d.ellipse([cx - R - lw * 3, cy - R - lw * 3, cx + R + lw * 3, cy + R + lw * 3], fill=lead)
    d.ellipse([cx - R - lw * 2, cy - R - lw * 2, cx + R + lw * 2, cy + R + lw * 2], fill=(226, 190, 90))
    d.ellipse([cx - R + lw, cy - R + lw, cx + R - lw, cy + R - lw], fill=lead)
    d.ellipse([cx - R + lw * 2, cy - R + lw * 2, cx + R - lw * 2, cy + R - lw * 2], fill=ground)
    for k in range(8):                                      # leads dividing the ground
        an = math.pi * k / 4 + math.pi / 8
        d.line([(cx, cy), (cx + math.cos(an) * (R - lw * 2), cy + math.sin(an) * (R - lw * 2))], fill=lead, width=lw)
    white, gold = (244, 240, 224), (240, 200, 90)
    ol = dict(outline=lead, width=lw)
    if kind == "luna":
        d.ellipse([cx - R * .62, cy - R * .62, cx + R * .62, cy + R * .62], fill=white, **ol)
        d.ellipse([cx - R * .30, cy - R * .70, cx + R * .78, cy + R * .38], fill=ground, **ol)
        d.ellipse([cx - R * .27, cy - R * .67, cx + R * .75, cy + R * .35], fill=ground)
    elif kind == "stella":
        d.polygon(star_pts(cx, cy, R * .74, R * .30, 8), fill=white, outline=lead)
        d.line(star_pts(cx, cy, R * .74, R * .30, 8) + [star_pts(cx, cy, R * .74, R * .30, 8)[0]], fill=lead, width=lw)
        d.ellipse([cx - R * .14, cy - R * .14, cx + R * .14, cy + R * .14], fill=gold, **ol)
    elif kind == "sole":
        for k in range(16):
            an = 2 * math.pi * k / 16
            r1 = R * (.86 if k % 2 == 0 else .68)
            d.polygon([(cx + math.cos(an - .12) * R * .42, cy + math.sin(an - .12) * R * .42), (cx + math.cos(an) * r1, cy + math.sin(an) * r1),
                       (cx + math.cos(an + .12) * R * .42, cy + math.sin(an + .12) * R * .42)], fill=gold, outline=lead)
        d.ellipse([cx - R * .44, cy - R * .44, cx + R * .44, cy + R * .44], fill=(250, 214, 80), **ol)
    elif kind == "croce":
        wv = R * .13
        d.rectangle([cx - wv, cy - R * .70, cx + wv, cy + R * .74], fill=gold, **ol)
        d.rectangle([cx - R * .50, cy - R * .26 - wv, cx + R * .50, cy - R * .26 + wv], fill=gold, **ol)
    elif kind == "giglio":
        fleur(d, cx, cy, R * 1.3, white)
    elif kind == "corona":
        d.polygon([(cx - R * .56, cy + R * .30), (cx - R * .66, cy - R * .40), (cx - R * .30, cy - R * .04), (cx, cy - R * .56), (cx + R * .30, cy - R * .04),
                   (cx + R * .66, cy - R * .40), (cx + R * .56, cy + R * .30)], fill=gold, outline=lead)
        d.rectangle([cx - R * .56, cy + R * .30, cx + R * .56, cy + R * .46], fill=(250, 214, 80), **ol)
        for dx in (-.34, 0, .34):
            d.ellipse([cx + dx * R - R * .07, cy + R * .31, cx + dx * R + R * .07, cy + R * .45], fill=(170, 30, 40))
    elif kind == "stella8":
        d.polygon(star_pts(cx, cy, R * .70, R * .42, 6), fill=gold, outline=lead)
        d.polygon(star_pts(cx, cy, R * .36, R * .20, 6, rot=0), fill=white, outline=lead)
    else:   # calice
        d.pieslice([cx - R * .42, cy - R * .78, cx + R * .42, cy + R * .06], 0, 180, fill=gold, **ol)
        d.rectangle([cx - R * .06, cy - R * .34, cx + R * .06, cy + R * .40], fill=gold, **ol)
        d.ellipse([cx - R * .14, cy - R * .08, cx + R * .14, cy + R * .12], fill=gold, **ol)
        d.polygon([(cx - R * .40, cy + R * .58), (cx - R * .10, cy + R * .38), (cx + R * .10, cy + R * .38), (cx + R * .40, cy + R * .58)], fill=gold, outline=lead)
        d.ellipse([cx - R * .20, cy - R * .80, cx + R * .20, cy - R * .40], fill=white, **ol)
    # a small rosette under the medallion and one above
    for yy0, col in ((H * .80, (164, 30, 36)), (H * .135, (36, 62, 150))):
        d.polygon(star_pts(cx, yy0, W * .12, W * .085, 4, rot=0), fill=lead)
        d.polygon(star_pts(cx, yy0, W * .10, W * .068, 4, rot=0), fill=col)
        d.ellipse([cx - W * .03, yy0 - W * .03, cx + W * .03, yy0 + W * .03], fill=gold)
    # horizontal saddle bars
    for yb in (H * .245, H * .64, H * .90):
        d.rectangle([mx, yb - lw * .7, W - mx, yb + lw * .7], fill=lead)
    a = arr(im)
    # light through the glass: uneven, streaky, a little halation around the brightest pieces
    light = 0.72 + 0.5 * fbm(H, W, W / 2.5, seed + 2) + 0.12 * fbm(H, W, 10, seed + 3, 2)
    a *= light[..., None]
    glow = ndimage.gaussian_filter(a, (W * .02, W * .02, 0))
    a = np.maximum(a, a * 0.85 + glow * 0.25)
    mk = (np.asarray(m).astype(float) / 255)[..., None]
    st = photo("plaster002", 256)
    st = np.tile(st / st.mean() * np.array(stone, float), (H // 256 + 1, W // 256 + 1, 1))[:H, :W]
    # the splay of the opening: a darker band of stone around the glass
    spl = ndimage.gaussian_filter(np.asarray(m.filter(ImageFilter.MaxFilter(1 + 2 * int(W * .03)))).astype(float) / 255, 2)[..., None]
    st = st * (1 - 0.35 * spl)
    a = a * mk + st * (1 - mk)
    return down(a, w, h)


# ------------------------------------------------------------------------------------ the Black Madonna
def icon(w=256, h=512, seed=77):
    """The Madonna Nera enthroned with the Child, as a gold-ground mosaic in an arched niche, with the words
    NIGRA SUM SED FORMOSA at her feet."""
    W, H = w * 4, h * 4
    im = Image.new("RGB", (W, H), (120, 84, 40))
    d = ImageDraw.Draw(im)
    skin, skin_l, skin_d = (74, 48, 34), (112, 76, 54), (44, 28, 22)
    robe, robe_d, robe_l = (150, 30, 34), (96, 18, 24), (200, 70, 60)
    mantle, mantle_l = (28, 40, 96), (60, 84, 150)
    # niche: border, gold ground, arched top with a shell of rays
    border(d, 0, 0, W - 1, H - 1, W * .07)
    x0, x1, yb = W * .10, W * .90, H * .90
    rr = (x1 - x0) / 2
    d.rectangle([x0, H * .07 + rr, x1, yb], fill=GOLD)
    d.ellipse([x0, H * .07, x1, H * .07 + 2 * rr], fill=GOLD)
    cx = W / 2
    for k in range(13):
        an = math.pi + math.pi * k / 12
        d.line([(cx, H * .07 + rr), (cx + math.cos(an) * rr, H * .07 + rr + math.sin(an) * rr)], fill=GOLD_D, width=6)
    # throne
    d.rectangle([cx - W * .30, H * .40, cx + W * .30, yb], fill=(132, 84, 44))
    d.rectangle([cx - W * .27, H * .42, cx + W * .27, yb], fill=(170, 116, 60))
    for sx in (-1, 1):
        d.rectangle([cx + sx * W * .30 - W * .035, H * .34, cx + sx * W * .30 + W * .035, yb], fill=(120, 76, 40))
        d.ellipse([cx + sx * W * .30 - W * .05, H * .31, cx + sx * W * .30 + W * .05, H * .31 + W * .10], fill=GOLD_L, outline=GOLD_D, width=5)
    d.rectangle([cx - W * .34, yb - H * .035, cx + W * .34, yb], fill=(110, 70, 38))
    # halo and crown
    hy = H * .235
    d.ellipse([cx - W * .21, hy - W * .21, cx + W * .21, hy + W * .21], fill=GOLD_L, outline=RED, width=10)
    # mantle over the shoulders down to the knees, robe underneath
    d.polygon([(cx - W * .13, H * .27), (cx + W * .13, H * .27), (cx + W * .27, H * .46), (cx + W * .30, H * .70), (cx + W * .25, yb - H * .04),
               (cx - W * .25, yb - H * .04), (cx - W * .30, H * .70), (cx - W * .27, H * .46)], fill=mantle)
    d.polygon([(cx - W * .10, H * .33), (cx + W * .10, H * .33), (cx + W * .19, H * .62), (cx + W * .22, yb - H * .04), (cx - W * .22, yb - H * .04), (cx - W * .19, H * .62)], fill=robe)
    for k in range(-3, 4):                                   # folds of the robe
        xk = cx + k * W * .055
        d.line([(cx + k * W * .028, H * .50), (xk, yb - H * .045)], fill=robe_d if k % 2 else robe_l, width=7)
    for sx in (-1, 1):                                       # gold hem of the mantle
        d.line([(cx + sx * W * .13, H * .28), (cx + sx * W * .19, H * .62), (cx + sx * W * .22, yb - H * .045)], fill=GOLD_L, width=9)
        d.line([(cx + sx * W * .20, H * .40), (cx + sx * W * .27, H * .68)], fill=mantle_l, width=6)
    d.line([(cx - W * .22, yb - H * .045), (cx + W * .22, yb - H * .045)], fill=GOLD_L, width=10)
    # the veil framing the face, the face, the crown
    d.ellipse([cx - W * .135, hy - W * .16, cx + W * .135, hy + W * .17], fill=mantle)
    d.ellipse([cx - W * .135, hy - W * .16, cx + W * .135, hy + W * .17], outline=GOLD_L, width=6)
    fx0, fy0, fx1, fy1 = cx - W * .085, hy - W * .10, cx + W * .085, hy + W * .135
    d.ellipse([fx0, fy0, fx1, fy1], fill=skin)
    d.ellipse([cx - W * .075, hy - W * .08, cx + W * .01, hy + W * .10], fill=skin_l)      # light on one cheek
    d.ellipse([fx0, fy0, fx1, fy1], outline=skin_d, width=4)
    for sx in (-1, 1):
        ex = cx + sx * W * .036
        d.ellipse([ex - W * .022, hy - W * .012, ex + W * .022, hy + W * .012], fill=(236, 228, 210))
        d.ellipse([ex - W * .010, hy - W * .011, ex + W * .010, hy + W * .011], fill=(20, 14, 12))
        d.arc([ex - W * .030, hy - W * .040, ex + W * .030, hy + W * .010], 200, 340, fill=skin_d, width=5)
    d.line([(cx + W * .004, hy), (cx - W * .010, hy + W * .050), (cx + W * .012, hy + W * .055)], fill=skin_d, width=5)
    d.line([(cx - W * .024, hy + W * .084), (cx + W * .024, hy + W * .084)], fill=(120, 40, 40), width=6)
    d.polygon([(cx - W * .11, hy - W * .10), (cx - W * .13, hy - W * .23), (cx - W * .06, hy - W * .16), (cx, hy - W * .26), (cx + W * .06, hy - W * .16),
               (cx + W * .13, hy - W * .23), (cx + W * .11, hy - W * .10)], fill=GOLD, outline=GOLD_D)
    d.rectangle([cx - W * .11, hy - W * .115, cx + W * .11, hy - W * .085], fill=GOLD_L, outline=GOLD_D)
    for dx in (-.07, 0, .07):
        d.ellipse([cx + dx * W - W * .013, hy - W * .112, cx + dx * W + W * .013, hy - W * .088], fill=(170, 30, 40) if dx else (40, 90, 60))
    # the Child on her lap, facing us, blessing
    by = H * .47
    d.ellipse([cx - W * .085, by - W * .085, cx + W * .085, by + W * .085], fill=GOLD_L, outline=RED, width=7)
    d.line([(cx - W * .08, by), (cx + W * .08, by)], fill=RED, width=5)
    d.line([(cx, by - W * .08), (cx, by + W * .08)], fill=RED, width=5)
    d.polygon([(cx - W * .075, by + W * .05), (cx + W * .075, by + W * .05), (cx + W * .11, H * .68), (cx - W * .11, H * .68)], fill=(214, 176, 90))
    for k in (-1, 0, 1):
        d.line([(cx + k * W * .03, by + W * .08), (cx + k * W * .055, H * .675)], fill=(150, 110, 50), width=6)
    d.ellipse([cx - W * .048, by - W * .052, cx + W * .048, by + W * .058], fill=skin)
    d.ellipse([cx - W * .042, by - W * .045, cx + W * .006, by + W * .045], fill=skin_l)
    d.ellipse([cx - W * .048, by - W * .052, cx + W * .048, by + W * .058], outline=skin_d, width=3)
    for sx in (-1, 1):
        d.ellipse([cx + sx * W * .02 - W * .008, by - W * .008, cx + sx * W * .02 + W * .008, by + W * .008], fill=(20, 14, 12))
    d.line([(cx - W * .012, by + W * .03), (cx + W * .012, by + W * .03)], fill=(120, 40, 40), width=4)
    d.ellipse([cx + W * .085, H * .535, cx + W * .135, H * .575], fill=skin, outline=skin_d, width=3)       # blessing hand
    # her hands holding him
    d.ellipse([cx - W * .16, H * .575, cx - W * .06, H * .615], fill=skin, outline=skin_d, width=3)
    d.ellipse([cx + W * .05, H * .62, cx + W * .15, H * .66], fill=skin, outline=skin_d, width=3)
    # the words at her feet
    d.rectangle([W * .07, yb, W * .93, H * .955], fill=(30, 48, 112))
    f = ImageFont.truetype(SERIF, int(H * .026))
    d.text((cx, (yb + H * .955) / 2), "NIGRA SVM SED FORMOSA", font=f, fill=GOLD_L, anchor="mm")
    a = arr(im.filter(ImageFilter.GaussianBlur(1.2)))
    out = tesserae(a, cell=2.4, seed=seed, jitter=0.08)
    return np.clip(out * (0.9 + 0.2 * fbm(h, w, 100, seed + 1)[..., None]), 0, 255)


def inscription(k, w=256, h=32):
    """Quarter k of the band under the drum: gold capitals on blue."""
    text = "AVE MARIA  ✦  GRATIA PLENA  ✦  DOMINVS TECVM  ✦  BENEDICTA TV  ✦  "
    S = 4
    f = ImageFont.truetype(SERIF, int(h * S * .58))
    tw = int(f.getlength(text))
    im = Image.new("RGB", (tw, h * S), (30, 50, 120))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, tw, h * S * .12], fill=GOLD)
    d.rectangle([0, h * S * .88, tw, h * S], fill=GOLD)
    d.text((0, h * S * .5), text, font=f, fill=GOLD_L, anchor="lm", stroke_width=2, stroke_fill=GOLD_D)
    part = im.crop((k * tw // 4, 0, (k + 1) * tw // 4, h * S)).resize((w, h), Image.LANCZOS)
    return arr(part) * (0.9 + 0.2 * fbm(h, w, 40, k)[..., None])


# ------------------------------------------------------------------------------------ Ed's photographs (29/10/2026)
FOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "foto")
NAVE_HALF, N_ARC = 5.0, 8


def _foto(name):
    return Image.open(os.path.join(FOTO, name + ".jpg")).convert("RGB")


def vault_panel(kind):
    """One frescoed length of the nave vault seen from below, 512 px across (left = north) x 768 px along
    (top = towards the altar). 'a' is the photograph taken straight up; 'b' and 'c' put the frescoes of the
    other two photographs, straightened, on the same gold trellis between the same bands of sky."""
    W, H = 512, 768
    base = _foto("tindari_volta_a").resize((W, H), Image.LANCZOS)
    if kind == "a":
        return arr(base)
    x0, x1 = 64, 450                                        # the trellis field between the two bands of sky
    if kind == "b":
        src = _foto("tindari_volta_b")
        quad = (75, 143, 137, 548, 361, 548, 418, 143)      # upper left, lower left, lower right, upper right
        mid = src.transform((x1 - x0, H), Image.QUAD, quad, Image.BICUBIC)
    else:
        mid = _foto("tindari_volta_c").crop((140, 200, 380, 680)).resize((x1 - x0, H), Image.LANCZOS)
    mid = mid.filter(ImageFilter.UnsharpMask(2, 60, 2))
    base.paste(mid, (x0, 0))
    return arr(base)


def vault_slices(put, name, a):
    """Cuts a vault panel into the pieces the model uses: 8 arcs across (as wide as they look from below) x 3
    lengths along. name_k_j, k = arc from the south springing, j from the altar end."""
    H, W = a.shape[:2]
    zs = [-NAVE_HALF * math.cos(math.pi * k / N_ARC) for k in range(N_ARC + 1)]
    for k in range(N_ARC):
        pa, pb = (NAVE_HALF - zs[k + 1]) / (2 * NAVE_HALF) * W, (NAVE_HALF - zs[k]) / (2 * NAVE_HALF) * W
        ia, ib = int(round(pa)), max(int(round(pa)) + 8, int(round(pb)))
        ib = min(W, ib)
        ia = min(ia, ib - 8)
        for j in range(3):
            put("%s_%d_%d" % (name, k, j), rgba(a[j * H // 3:(j + 1) * H // 3, ia:ib]))


def dome_quarters():
    """The fresco of the dome, unrolled from the photograph taken from the crossing: four quarters, each 256 px
    of angle x 192 px from the cornice (bottom) to the lantern (top). The dome is seen at a slant, so the rings
    are ellipses whose centre slides from the cornice ring to the lantern."""
    from scipy.ndimage import map_coordinates
    src = np.asarray(_foto("tindari_cupola")).astype(float)
    C, O, ax, bx, ro = np.array((527.0, 222.0)), np.array((523.0, 137.0)), 166.0, 132.0, 0.30
    out = []
    for q in range(4):
        v, u = np.mgrid[0:192, 0:256]
        phi = (q + (u + 0.5) / 256) * math.pi / 2
        t = (1 - (v + 0.5) / 192) * 0.92 / 0.92               # 0 at the cornice, 1 at the rim of the lantern
        r = ro + (1 - ro) * np.cos(t * math.pi / 2)
        k = (r - ro) / (1 - ro)                                 # the centre of the ring slides from the lantern to C
        x = O[0] + k * (C[0] - O[0]) + r * ax * np.cos(phi)
        y = O[1] + k * (C[1] - O[1]) + r * bx * np.sin(phi)
        ch = [map_coordinates(src[..., c], [y, x], order=1, mode="nearest") for c in range(3)]
        im = Image.fromarray(np.clip(np.stack(ch, axis=2), 0, 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 50, 2))
        out.append(arr(im))
    # the half of the dome over the camera is too foreshortened in the photograph to be read: the far half, which
    # is seen well, is mirrored onto it
    out[2], out[3] = out[1][:, ::-1], out[0][:, ::-1]
    return out


def chapel_altar():
    """The altar of the side chapel (aedicule with the statue), from the photograph, above the altar table."""
    return arr(_foto("tindari_altare").crop((70, 95, 430, 525)).resize((432, 512), Image.LANCZOS))


# ------------------------------------------------------------------------------------ packing
def rgba(a):
    return np.concatenate([np.clip(a, 0, 255), np.full(a.shape[:2] + (1,), 255.0)], axis=2)


def grid(put, name, a, nx, ny):
    """Cuts a big piece into nx x ny regions name_i_j (i from the left, j from the top)."""
    H, W = a.shape[:2]
    GRIDS[name] = (nx, ny)
    for i in range(nx):
        for j in range(ny):
            put("%s_%d_%d" % (name, i, j), rgba(a[j * H // ny:(j + 1) * H // ny, i * W // nx:(i + 1) * W // nx]))


GLASS = ["croce", "giglio", "corona", "stella8", "calice"]


def build(put):
    put("in_stelle", rgba(floor_stars()))
    put("in_rombi", rgba(floor_diamonds()))
    put("in_marmo_rosso", rgba(marble("marble008", tint=(150, 46, 40))))
    put("in_marmo_rosa", rgba(marble("marble010", tint=(214, 160, 150))))
    put("in_oro", rgba(gilded()))
    put("in_giallo", rgba(lattice(256, 4, seed=5)))
    put("in_volta", rgba(lattice(256, 4, ground=(206, 170, 96), flower=(60, 80, 140), seed=6)))
    put("in_parete", rgba(stucco()))
    put("in_cassettoni", rgba(coffers()))
    for kind in "abc":                                     # the real vault and dome, from Ed's photographs
        vault_slices(put, "in_vp" + kind, vault_panel(kind))
    for q, a in enumerate(dome_quarters()):
        put("in_cupola%d" % q, rgba(a))
    grid(put, "in_altare_sc", chapel_altar(), 2, 2)
    for k in range(4):
        grid(put, "in_mosaico%d" % k, mosaic_panel(k, 50 + k), 2, 1)
    for k, kind in enumerate(GLASS):
        grid(put, "in_vetrata%d" % k, glass(kind, 60 + k), 1, 2)
    for s in ("luna", "stella", "sole"):
        grid(put, "in_vetrata_" + s, glass(s, 70), 1, 2)
    for k in range(4):
        put("in_scritta%d" % k, rgba(inscription(k)))
    wood = photo("wood006", 256)
    put("in_legno", rgba(wood[:128, :] * 0.9))
    grid(put, "in_icona", icon(), 1, 2)
