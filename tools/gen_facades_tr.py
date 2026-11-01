"""Facade columns from real TR2 material (Ed's C:\\CodaDiVolpe\\AdditionalTextures) laid out as Sicilian
buildings.

v2 (01/11/2026). The first version pasted whole TR2 tiles one per storey: Venetian panels, gold and black
ironwork and an orange plaster that read as a chessboard. Now the TR2 sheets only give the *material*
(plaster grain, lava stone, wood of the doors, louvred shutters and stone window frames, cut tight around
the element), every colour is re-mapped to the palette of the real buildings of Via Amodeo, and the layout
(plinth, storey bands, windows centred on the 2 m sector, sills, doors with stone surround, roller shutters)
is drawn to measure. The weathering pass of gen_facades.realism() adds shadows, streaks and cracks.

Same column names and atlas layout as gen_facades.py: coda_atlas10/11/12, 2 m x 16 m strips at 128 px/m,
bottom = street level, so adjacent sectors of a building join (storeys and windows at fixed heights).
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gen_facades import realism
from gen_ground import FS, OUT, fbm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TR2 = os.path.join(ROOT, "assets", "tr2")
PX = 128
W, H = 256, 2048

_sheets = {}


def sheet(name):
    if name not in _sheets:
        _sheets[name] = np.asarray(Image.open(os.path.join(TR2, name + ".tga")).convert("RGB")).astype(float)
    return _sheets[name]


def crop(name, x0, y0, x1, y1):
    return sheet(name)[y0:y1, x0:x1].copy()


def resize(a, w, h):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
    return np.asarray(im).astype(float)


def lum(a):
    return a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11


def remap(a, dark, light, contrast=1.0):
    """Luminance of `a` mapped onto the ramp dark -> light (keeps the TR2 grain, drops its hue)."""
    l = lum(a)
    lo, hi = np.percentile(l, 3), np.percentile(l, 97)
    t = np.clip((l - lo) / max(1.0, hi - lo), 0, 1)
    t = np.clip(0.5 + (t - 0.5) * contrast, 0, 1)[..., None]
    return np.array(dark, float) * (1 - t) + np.array(light, float) * t


def y(m):
    return int(round(H - m * PX))


def paste(dst, src, x, m_bottom):
    """Paste array `src` with its bottom edge at m_bottom metres, left edge at pixel x (clipped)."""
    h, w = src.shape[:2]
    y1 = y(m_bottom)
    y0 = y1 - h
    sy0, sx0 = max(0, -y0), max(0, -x)
    y0c, x0c = max(0, y0), max(0, x)
    y1c, x1c = min(H, y1), min(W, x + w)
    if y1c > y0c and x1c > x0c:
        dst[y0c:y1c, x0c:x1c] = src[sy0:sy0 + (y1c - y0c), sx0:sx0 + (x1c - x0c)]


def centred(dst, src, m_bottom):
    paste(dst, src, (W - src.shape[1]) // 2, m_bottom)


# ---------------------------------------------------------------- materials

def plaster(color, seed):
    """Venetian plaster grain (venice.tga 11,1 and 3,0 alternated and flipped), recoloured, with a
    low-frequency mottle that wraps horizontally so neighbouring columns join."""
    t1 = crop("venice", 64, 11 * 64, 128, 12 * 64)
    tiles = [t1, t1[:, ::-1], t1[::-1], t1[::-1, ::-1]]
    col = np.zeros((H, W, 3))
    r = np.random.default_rng(seed)
    for k in range(H // 256):
        t = resize(tiles[(k + int(r.integers(0, 4))) % 4], 128, 256)
        col[k * 256:(k + 1) * 256] = np.concatenate([t, t[:, ::-1]], axis=1)   # mirrored halves: the
        # column's left and right edges are the same pixels, so neighbouring sectors join without seams
    from scipy import ndimage
    l = ndimage.gaussian_filter(lum(col), 1.6)
    g = l / l.mean()
    g = 1 + (g - 1) * 0.4                                     # TR2 grain and scribbles are strong; soften
    m = fbm(H, 90, 4, seed)[:H, :W]
    m = 0.5 * (m + m[:, ::-1])                                # mirror-symmetric -> wraps across columns
    c = np.array(color, float)
    return c[None, None, :] * g[..., None] * (0.93 + 0.12 * m[..., None])


def stone(color_dark, color_light, w_m, h_m, seed=0):
    """Lava stone / limestone ashlar from venice 19,2, recoloured."""
    t = crop("venice", 128, 19 * 64, 192, 20 * 64)
    reps = max(1, int(round(w_m / 1.0)))
    big = np.concatenate([t if k % 2 == 0 else t[:, ::-1] for k in range(reps)], axis=1)
    a = resize(big, w_m * PX, h_m * PX)
    return remap(a, color_dark, color_light, 0.8)


def wood_door(dark, light, w_m, h_m):
    """Panelled two-leaf door from house 12,2 (2 x 3 panels), recoloured."""
    t = crop("house", 2 * 64, 12 * 64, 3 * 64, 13 * 64)
    from scipy import ndimage
    a = resize(t, w_m * PX, h_m * PX)
    a = ndimage.gaussian_filter(a, (1.2, 1.2, 0))
    return remap(a, dark, light, 0.85)


def louvred_window(w_m, h_m, shutter=(52, 84, 60), frame=(222, 216, 200), open_=False, glass=(30, 36, 46)):
    """Louvred shutters in a stone frame, cut from the venice 13,1 / 14,1 window. Closed: both leaves of
    louvres. Open: dark glass with the frame mullion, the leaves folded against the frame (thin strips)."""
    a = np.concatenate([crop("venice", 64, 13 * 64, 128, 14 * 64), crop("venice", 64, 14 * 64, 128, 15 * 64)], axis=0)
    a = a[36:120, 11:54]                                       # 43 x 84: frame + leaves
    inner = np.zeros(a.shape[:2], bool)
    inner[3:78, 3:40] = True
    out = remap(a, tuple(c * 0.55 for c in frame), frame, 0.9)
    sh = remap(a, tuple(c * 0.45 for c in shutter), tuple(min(255, c * 1.35) for c in shutter), 1.2)
    out[inner] = sh[inner]
    out = resize(out, w_m * PX, h_m * PX)
    if open_:
        fw = int(0.09 * PX)
        out[fw:-fw, fw:-fw] = glass
        mid = out.shape[1] // 2
        out[fw:-fw, mid - 3:mid + 3] = np.array(frame) * 0.8
        out[int(out.shape[0] * 0.33):int(out.shape[0] * 0.33) + 5, fw:-fw] = np.array(frame) * 0.8
    return out


def open_leaves(dst, w_m, h_m, m_bottom, shutter, leaf_m=0.36):
    """The two leaves of an open louvred window, folded flat against the wall on both sides."""
    a = np.concatenate([crop("venice", 64, 13 * 64, 128, 14 * 64), crop("venice", 64, 14 * 64, 128, 15 * 64)], axis=0)
    leaf = a[39:114, 14:31]
    leaf = remap(leaf, tuple(c * 0.45 for c in shutter), tuple(min(255, c * 1.35) for c in shutter), 1.2)
    leaf = resize(leaf, leaf_m * PX, h_m * PX * 0.96)
    leaf[:, :3] *= 0.6
    leaf[:, -3:] *= 0.6
    gap = int(0.04 * PX)
    x_l = (W - int(w_m * PX)) // 2 - gap - leaf.shape[1]
    x_r = (W + int(w_m * PX)) // 2 + gap
    paste(dst, leaf, x_l, m_bottom + h_m * 0.02)
    paste(dst, leaf[:, ::-1], x_r, m_bottom + h_m * 0.02)


def stone_window(w_m, h_m, frame=(206, 200, 186), blind=None, blind_frac=0.45):
    """Stone-framed window from venice 17,2 (dark panes), optionally with a roller blind half down."""
    a = crop("venice", 2 * 64 + 2, 17 * 64, 3 * 64 - 2, 17 * 64 + 60)
    out = resize(a, w_m * PX, h_m * PX)
    h, w = out.shape[:2]
    dark = np.zeros((h, w), bool)
    dark[int(h * 0.07):int(h * 0.87), int(w * 0.2):int(w * 0.8)] = True      # the panes inside the stone frame
    fr = remap(out, tuple(c * 0.62 for c in frame), frame, 0.7)
    gl = remap(out, (14, 16, 22), (50, 56, 68), 1.0)
    out = np.where(dark[..., None], gl, fr)
    if blind is not None:
        fx, fy = int(0.2 * w_m * PX), int(0.07 * h_m * PX)
        y1 = fy + int((int(h * 0.8)) * blind_frac)
        for yy in range(fy, y1):
            t = ((yy - fy) % 10) / 9.0
            out[yy, fx:-fx] = np.array(blind) * (0.72 + 0.34 * (1 - abs(t - 0.35) * 1.5))
        out[y1:y1 + 5, fx:-fx] = np.array(blind) * 0.45
    return out


def roller_shutter(w_m, h_m, color=(150, 150, 146), seed=0):
    """Garage / shop roller shutter: ribbed galvanised steel, rusty foot, dark box on top."""
    w, h = int(w_m * PX), int(h_m * PX)
    a = np.zeros((h, w, 3)) + np.array(color, float)
    yy = np.arange(h)[:, None]
    rib = 0.82 + 0.25 * np.abs(np.sin(yy / 6.5 * np.pi))
    a *= rib[..., None]
    n = fbm(max(h, w), 40, 3, seed)[:h, :w]
    a *= (0.92 + 0.12 * n)[..., None]
    rust = np.clip((yy[:, 0] - h * 0.8) / (h * 0.2), 0, 1)[:, None] * (n > 0.45)
    a = a * (1 - 0.4 * rust[..., None]) + np.array([120, 70, 40]) * 0.4 * rust[..., None]
    a[:int(0.18 * PX)] = np.array(color) * 0.55
    a[:, :6] *= 0.6
    a[:, -6:] *= 0.6
    return a


def iron_grille(a, x0, y0, x1, y1, color=(34, 32, 30), step=16):
    a[y0:y1, x0:x0 + 4] = color
    a[y0:y1, x1 - 4:x1] = color
    for x in range(x0 + step, x1 - 4, step):
        a[y0:y1, x - 2:x + 2] = color
    for yy in (y0 + 6, (y0 + y1) // 2, y1 - 8):
        a[yy:yy + 4, x0:x1] = color


def band(a, m0, m1, color, seed=0, grain=None):
    """Horizontal band of the full column width (plinth, marcapiano)."""
    h = y(m0) - y(m1)
    if grain is None:
        b = np.zeros((h, W, 3)) + np.array(color, float)
    else:
        b = resize(grain, W, h)
    a[y(m1):y(m0)] = b[:h, :W]


def marcapiano(a, m, color, h=0.16):
    """Storey band: lighter strip with a shadow line under it and a highlight on top."""
    c = np.array(color, float)
    a[y(m + h):y(m)] = np.minimum(255, c * 1.08)
    a[y(m + h):y(m + h) + 2] = np.minimum(255, c * 1.2)
    a[y(m):y(m) + 4] = c * 0.62
    a[y(m) + 4:y(m) + 10] *= 0.85


def sill(a, m, w_m, color=(212, 206, 192)):
    w = int(w_m * PX)
    x0 = (W - w) // 2
    a[y(m) - 4:y(m) + 8, x0:x0 + w] = color
    a[y(m) + 8:y(m) + 11, x0:x0 + w] = np.array(color) * 0.6


def surround(a, m0, m1, w_m, color=(96, 92, 88), thick=0.18):
    """Stone door / shop surround (lava stone)."""
    w = int((w_m + 2 * thick) * PX)
    s = stone(tuple(c * 0.6 for c in color), color, w_m + 2 * thick, m1 - m0 + thick)
    centred(a, s, m0)


def fanlight(w_m, h_m, frame=(40, 34, 28)):
    w, h = int(w_m * PX), int(h_m * PX)
    a = np.zeros((h, w, 3)) + np.array([26, 30, 38], float)
    a[:, :5] = a[:, -5:] = frame
    a[:5] = a[-5:] = frame
    cx = w // 2
    for k in range(-3, 4):
        x = cx + k * w // 8
        a[:, max(0, x - 2):x + 2] = frame
    return a


def downpipe(a, x, m_top, color=(150, 100, 64)):
    a[y(m_top):, x:x + 14] = color
    a[y(m_top):, x + 3:x + 6] = np.minimum(255, np.array(color) * 1.3)
    a[y(m_top):, x + 11:x + 14] = np.array(color) * 0.6
    for m in np.arange(1.2, m_top, 2.4):
        a[y(m):y(m) + 6, x - 6:x + 20] = (60, 52, 44)


# ---------------------------------------------------------------- buildings

def finish(a, p0, seed):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    p = Image.fromarray(np.clip(p0, 0, 255).astype(np.uint8))
    out = realism(im, p, seed)
    return out.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))


CREAM, PINK, WHITE, BEIGE, OCHRE, GREY = (222, 206, 170), (214, 162, 150), (226, 224, 216), (208, 192, 160), (206, 168, 112), (186, 182, 174)
GREEN_SH, BROWN_SH, WHITE_SH = (52, 86, 62), (112, 78, 52), (208, 206, 198)
LAVA = (92, 88, 84)


def ed_house(kind, seed=11):
    """Ed's house: cream plaster, brown base band, green shutters; French windows on the long balcony of the
    1st floor, windows on the 2nd; the art deco portone in a lava stone surround."""
    a = plaster(CREAM, seed)
    p0 = a.copy()
    band(a, 0, 0.65, None, grain=stone((70, 52, 40), (126, 96, 72), 2.0, 0.65))
    a[y(0.65):y(0.65) + 3] = (64, 48, 36)
    if kind == "porta":
        surround(a, 0, 2.75, 1.5, LAVA)
        centred(a, wood_door((40, 28, 18), (112, 80, 52), 1.5, 2.1), 0)
        centred(a, fanlight(1.5, 0.55), 2.1)
    elif kind in ("finestra", "tubo"):
        centred(a, louvred_window(1.05, 1.6, GREEN_SH, open_=True), 0.95)
        sill(a, 0.95, 1.35)
        iron_grille(a, (W - int(1.05 * PX)) // 2, y(2.55), (W + int(1.05 * PX)) // 2, y(0.95))
    marcapiano(a, 3.2, CREAM)
    if kind != "piena":
        centred(a, louvred_window(1.1, 2.3, GREEN_SH, open_=False), 3.4)     # French window on the balcony
    marcapiano(a, 6.2, CREAM)
    if kind != "piena":
        centred(a, louvred_window(1.0, 1.7, GREEN_SH, open_=True), 6.95)
        open_leaves(a, 1.0, 1.7, 6.95, GREEN_SH)
        sill(a, 6.95, 1.3)
    marcapiano(a, 9.3, CREAM, h=0.24)
    return finish(a, p0, seed)


def pink_house(kind, seed=21):
    a = plaster(PINK, seed)
    p0 = a.copy()
    band(a, 0, 0.45, None, grain=stone((120, 96, 90), (186, 160, 150), 2.0, 0.45))
    if kind == "porta":
        surround(a, 0, 2.5, 1.1, (196, 190, 180))
        centred(a, wood_door((70, 50, 36), (150, 112, 80), 1.1, 2.4), 0)
    else:
        centred(a, stone_window(1.1, 1.6, (232, 228, 220), blind=(214, 210, 200), blind_frac=0.5), 0.9)
        sill(a, 0.9, 1.4)
    marcapiano(a, 3.2, (236, 230, 224))
    centred(a, louvred_window(1.1, 2.3, WHITE_SH, frame=(236, 232, 226)), 3.4)
    marcapiano(a, 6.2, (236, 230, 224))
    centred(a, louvred_window(1.0, 1.75, WHITE_SH, frame=(236, 232, 226), open_=True), 6.9)
    open_leaves(a, 1.0, 1.75, 6.9, WHITE_SH)
    sill(a, 6.9, 1.3)
    marcapiano(a, 9.3, (236, 230, 224), h=0.24)
    return finish(a, p0, seed)


def orange_house(kind, seed=31):
    """Cream house with terracotta roller blinds and balconies."""
    a = plaster((220, 206, 176), seed)
    p0 = a.copy()
    band(a, 0, 0.5, None, grain=stone((120, 110, 94), (190, 178, 156), 2.0, 0.5))
    blind = (176, 104, 70)
    if kind == "porta":
        surround(a, 0, 2.55, 1.2, (190, 182, 166))
        centred(a, wood_door((76, 50, 30), (160, 110, 66), 1.2, 2.45), 0)
    else:
        centred(a, stone_window(1.15, 1.6, blind=blind), 0.9)
        sill(a, 0.9, 1.45)
    marcapiano(a, 3.2, (220, 206, 176))
    centred(a, stone_window(1.1, 2.3, blind=blind, blind_frac=0.55), 3.4)
    marcapiano(a, 6.2, (220, 206, 176))
    centred(a, stone_window(1.1, 2.3, blind=blind, blind_frac=0.3), 6.5)
    marcapiano(a, 9.3, (220, 206, 176), h=0.24)
    return finish(a, p0, seed)


def white_corner(kind, seed=41):
    a = plaster(WHITE, seed)
    p0 = a.copy()
    band(a, 0, 0.5, None, grain=stone((130, 126, 120), (196, 192, 184), 2.0, 0.5))
    if kind == "porta":
        surround(a, 0, 2.45, 1.1, LAVA)
        centred(a, wood_door((40, 32, 26), (100, 80, 62), 1.1, 2.35), 0)
    else:
        centred(a, louvred_window(1.05, 1.55, GREEN_SH, open_=True), 0.95)
        sill(a, 0.95, 1.35)
        iron_grille(a, (W - int(1.05 * PX)) // 2, y(2.5), (W + int(1.05 * PX)) // 2, y(0.95))
    marcapiano(a, 3.3, WHITE)
    centred(a, louvred_window(1.0, 1.75, GREEN_SH), 4.1)
    sill(a, 4.1, 1.3)
    marcapiano(a, 6.6, WHITE, h=0.28)
    return finish(a, p0, seed)


def pizzeria(kind, seed=51):
    """Pizzeria-rosticceria: red painted ground floor, aluminium shop window lit from inside, door."""
    a = plaster(BEIGE, seed)
    p0 = a.copy()
    red = plaster((168, 44, 38), seed + 1)
    a[y(3.0):] = red[y(3.0):]
    if kind == "vetrina":
        w, h = int(1.8 * PX), int(2.2 * PX)
        g = np.zeros((h, w, 3))
        yy = np.linspace(0, 1, h)[:, None, None]
        g[:] = np.array([96, 70, 40]) * (1 - yy) + np.array([60, 44, 30]) * yy    # warm interior
        g[:, :8] = g[:, -8:] = (176, 176, 172)
        g[:8] = g[-8:] = (176, 176, 172)
        g[:, w // 2 - 4:w // 2 + 4] = (176, 176, 172)
        centred(a, g, 0.55)
        a[y(0.55):, (W - w) // 2:(W + w) // 2] = np.array([130, 34, 30])
    else:
        surround(a, 0, 2.5, 1.2, (150, 150, 148))
        g = np.zeros((int(2.4 * PX), int(1.2 * PX), 3)) + np.array([70, 56, 40])
        g[:, :8] = g[:, -8:] = (176, 176, 172)
        g[:8] = (176, 176, 172)
        g[:, g.shape[1] // 2 - 3:g.shape[1] // 2 + 3] = (176, 176, 172)
        centred(a, g, 0)
    marcapiano(a, 3.2, BEIGE)
    centred(a, louvred_window(1.0, 2.2, BROWN_SH), 3.5)
    marcapiano(a, 6.3, BEIGE, h=0.28)
    return finish(a, p0, seed)


GENERIC = {
    # plaster, window kind, shutter / blind colour, plinth (dark, light)
    "ocra": (OCHRE, "blind", (150, 108, 72), ((96, 80, 60), (160, 140, 110))),
    "bianca": (WHITE, "louvre", GREEN_SH, ((110, 106, 100), (176, 172, 164))),
    "grigia": (GREY, "blind", (206, 202, 192), ((80, 78, 76), (140, 138, 134))),
    "crema": (CREAM, "louvre", BROWN_SH, ((100, 86, 66), (170, 150, 120))),
}


def generic(variant, ground, seed=70):
    """Ordinary palazzina of the town: storeys of 3.1 m, louvred shutters or roller blinds, a stone plinth,
    the ground floor with the door (lava stone surround), a barred window or a garage shutter."""
    pc, kind, sh, pl = GENERIC[variant]
    seed += len(variant) * 3 + (7 if ground == "porta" else 0)
    a = plaster(pc, seed)
    p0 = a.copy()
    band(a, 0, 0.6, None, grain=stone(pl[0], pl[1], 2.0, 0.6))
    a[y(0.6):y(0.6) + 3] = np.array(pl[0]) * 0.8
    if ground == "porta":
        surround(a, 0, 2.6, 1.3, LAVA)
        centred(a, wood_door((44, 32, 22), (120, 88, 58), 1.3, 2.6), 0)
    elif ground == "garage":
        surround(a, 0, 2.7, 1.8, (150, 146, 140), thick=0.12)
        centred(a, roller_shutter(1.8, 2.7, seed=seed), 0)
    else:
        if kind == "louvre":
            centred(a, louvred_window(1.05, 1.6, sh, open_=True), 1.0)
        else:
            centred(a, stone_window(1.1, 1.6, blind=sh, blind_frac=0.4), 1.0)
        sill(a, 1.0, 1.35)
        iron_grille(a, (W - int(1.1 * PX)) // 2, y(2.6), (W + int(1.1 * PX)) // 2, y(1.0))
    for k in range(1, 5):
        base = 3.1 * k
        marcapiano(a, base - 0.12, pc, h=0.12)
        if kind == "louvre":
            centred(a, louvred_window(1.0, 1.7, sh, open_=(k % 2 == 1)), base + 0.8)
            if k % 2 == 1:
                open_leaves(a, 1.0, 1.7, base + 0.8, sh)
        else:
            centred(a, stone_window(1.05, 1.7, blind=sh, blind_frac=(0.25, 0.6, 0.4, 0.75)[k - 1]), base + 0.8)
        sill(a, base + 0.8, 1.3)
    marcapiano(a, 15.5, pc, h=0.3)
    return finish(a, p0, seed)


def plain_side(color, seed, storeys=(3.2, 6.2, 9.3)):
    a = plaster(color, seed)
    p0 = a.copy()
    band(a, 0, 0.5, None, grain=stone(tuple(c * 0.5 for c in color), tuple(c * 0.85 for c in color), 2.0, 0.5))
    for m in storeys:
        marcapiano(a, m, color, h=0.12)
    return finish(a, p0, seed)


COLUMNS = [
    ("fac_casa_finestra", lambda: ed_house("finestra")), ("fac_casa_porta", lambda: ed_house("porta")),
    ("fac_casa_piena", lambda: ed_house("piena")), ("fac_casa_tubo", lambda: ed_house("tubo")),
    ("fac_rosa_porta", lambda: pink_house("porta")), ("fac_rosa_finestra", lambda: pink_house("finestra")),
    ("fac_arancio_porta", lambda: orange_house("porta")), ("fac_arancio_finestra", lambda: orange_house("finestra")),
    ("fac_bianco_porta", lambda: white_corner("porta")), ("fac_bianco_finestra", lambda: white_corner("finestra")),
    ("fac_pizzeria_vetrina", lambda: pizzeria("vetrina")), ("fac_pizzeria_porta", lambda: pizzeria("porta")),
    ("fac_lato_crema", lambda: plain_side(CREAM, 61)), ("fac_lato_rosa", lambda: plain_side(PINK, 62)),
    ("fac_lato_beige", lambda: plain_side(BEIGE, 63)), ("fac_lato_bianco", lambda: plain_side(WHITE, 64)),
]
for v in ("ocra", "bianca", "grigia", "crema"):
    COLUMNS.append(("fac_gen_%s_finestra" % v, lambda v=v: generic(v, "finestra")))
    COLUMNS.append(("fac_gen_%s_porta" % v, lambda v=v: generic(v, "porta")))


def main(first_index=9, only=None):
    pages = [COLUMNS[:8], COLUMNS[8:16], COLUMNS[16:24]]
    out = {}
    for p, cols in enumerate(pages):
        img = Image.new("RGB", (2048, 2048), (0, 0, 0))
        meta_cols = {}
        for i, (name, fn) in enumerate(cols):
            col = fn()
            out[name] = col
            img.paste(col, (i * W, 0))
            meta_cols[name] = [i * W, 0, (i + 1) * W, H]
        meta = {"px_per_m": PX, "size": 2048, "columns": meta_cols, "tiles": {}, "macro": {},
                "footsteps_64px": np.full((32, 32), FS["stone"], dtype=int).tolist()}
        base = os.path.join(OUT, "coda_atlas%d" % (first_index + 1 + p))
        img.save(base + ".png", optimize=True)
        with open(base + ".json", "w") as f:
            json.dump(meta, f)
        print(base + ".png")
    return out


if __name__ == "__main__":
    main()
