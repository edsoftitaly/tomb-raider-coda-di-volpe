"""Atlases 13-16: photographic textures (ambientCG, CC0) for Marinello - floors as seamless macro tiles,
the cliff of Tindari as one continuous 16 x 16 m face, the walls of the tonnara as height-registered columns.

Sources are seamless 1024 px scans in assets/tex_cc0. Every macro is the scan tiled, colour graded to the
level palette and modulated by a low-frequency tileable stain, so that the 4 m repeat does not read.
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "tex_cc0")
OUT = os.path.join(ROOT, "build", "textures")
S = 2048
FS = {"mud": 0, "sand": 2, "gravel": 3, "stone": 6, "grass": 10, "concrete": 11, "marble": 9, "wood": 7, "metal": 8}


def src(name, size=512):
    im = Image.open(os.path.join(SRC, name + ".jpg")).convert("RGB").resize((size, size), Image.LANCZOS)
    return np.asarray(im, dtype=np.float64)


def tnoise(n, cells, seed, octaves=3):
    """Tileable value noise n x n in 0..1."""
    rng = np.random.default_rng(seed)
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = rng.random((c, c))
        g = np.concatenate([g, g[:1]], 0)
        g = np.concatenate([g, g[:, :1]], 1)
        x = np.linspace(0, c, n, endpoint=False)
        i = x.astype(int)
        f = x - i
        f = f * f * (3 - 2 * f)
        a = g[np.ix_(i, i)] * (1 - f)[:, None] + g[np.ix_(i + 1, i)] * f[:, None]
        b = g[np.ix_(i, i + 1)] * (1 - f)[:, None] + g[np.ix_(i + 1, i + 1)] * f[:, None]
        out += amp * (a * (1 - f)[None, :] + b * f[None, :])
        tot += amp
        amp *= 0.5
    return out / tot


def grade(img, tint=(1.0, 1.0, 1.0), gain=1.0, sat=1.0, contrast=1.0):
    g = img.mean(axis=2, keepdims=True)
    out = g + (img - g) * sat
    m = out.mean()
    out = m + (out - m) * contrast
    return np.clip(out * gain * np.array(tint), 0, 255)


def macro(name, size, seed, stain=0.14, scan=512, **kw):
    """size px macro: the scan (at `scan` px) tiled, graded, with a tileable large stain (period = the macro)."""
    t = grade(src(name, scan), **kw)
    reps = size // scan
    img = np.tile(t, (reps, reps, 1))
    n = tnoise(size, 3, seed)
    img *= (1.0 - stain) + 2 * stain * n[:, :, None]
    return np.clip(img, 0, 255)


def blend(a, b, mask):
    return a * (1 - mask[:, :, None]) + b * mask[:, :, None]


def save(idx, atlas, regions, foot):
    regions["footsteps_64px"] = foot.tolist()
    Image.fromarray(np.clip(atlas, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "coda_atlas%d.png" % idx))
    json.dump(regions, open(os.path.join(OUT, "coda_atlas%d.json" % idx), "w"))
    print("ok coda_atlas%d" % idx, sorted(list(regions["macro"]) + list(regions["columns"]) + list(regions["tiles"])))


def new():
    return np.zeros((S, S, 3)), {"px_per_m": 128, "size": S, "columns": {}, "tiles": {}, "macro": {}}, \
        np.full((S // 64, S // 64), FS["stone"], dtype=int)


def put(atlas, regions, foot, name, img, x0, y0, fs):
    size = img.shape[0]
    atlas[y0:y0 + size, x0:x0 + size] = img
    regions["macro"][name] = [x0, y0, size]
    foot[y0 // 64:(y0 + size) // 64, x0 // 64:(x0 + size) // 64] = FS[fs]


def floors():
    # 13: the four big grounds of the sandbar
    a, r, f = new()
    sand = macro("ground034", 1024, 1, tint=(0.93, 0.90, 0.84), gain=0.92, sat=0.75)
    put(a, r, f, "m_sabbia", sand, 0, 0, "sand")
    wet = macro("ground034", 1024, 2, tint=(0.80, 0.79, 0.76), gain=0.84, sat=0.6, contrast=0.85)      # the same sand, wet
    put(a, r, f, "m_battigia", wet, 1024, 0, "sand")
    put(a, r, f, "m_fango", macro("ground031", 1024, 3, tint=(0.86, 0.84, 0.76), gain=0.95, contrast=1.1), 0, 1024, "mud")
    scrub = macro("ground013", 1024, 4, tint=(0.98, 1.0, 0.86), gain=0.95)
    put(a, r, f, "m_macchia", blend(scrub, sand, np.clip((tnoise(1024, 4, 9) - 0.62) * 5, 0, 1)), 1024, 1024, "grass")
    save(13, a, r, f)
    # 14: pebbles, sea bed, and the small ones
    a, r, f = new()
    put(a, r, f, "m_ciottoli", macro("rocks022", 1024, 5, tint=(0.92, 0.90, 0.86), gain=0.9, sat=0.6), 0, 0, "gravel")
    put(a, r, f, "m_fondale", macro("ground043", 1024, 6, tint=(0.62, 0.86, 0.80), gain=1.25, sat=0.6), 1024, 0, "sand")
    small = [("m_selciato", "pavingstones009", dict(gain=0.95, sat=0.8), "stone"),
             ("m_muro_cima", "rocks004", dict(gain=0.72, sat=0.7), "stone", 256),
             ("m_tavole", "planks004", dict(gain=0.9), "wood"),
             ("m_terra", "ground012", dict(tint=(1.0, 0.95, 0.85), gain=1.0), "mud"),
             ("m_cotto", "pavingstones021", dict(gain=0.92, sat=0.85), "stone"),
             ("m_tegole", "roofingtiles007", dict(gain=1.05), "stone"),
             ("m_roccia", "rock023", dict(tint=(1.0, 0.97, 0.9), gain=1.05), "stone"),
             ("m_erba", "ground037", dict(tint=(0.95, 0.95, 0.8), gain=0.85, sat=0.7), "grass")]
    for k, item in enumerate(small):
        name, s_, kw, fs = item[:4]
        put(a, r, f, name, macro(s_, 512, 20 + k, stain=0.08, scan=item[4] if len(item) > 4 else 512, **kw),
            (k % 4) * 512, 1024 + (k // 4) * 512, fs)
    save(14, a, r, f)


def cliff():
    """15: the rupe - 16 m wide x 16 m tall, tileable both ways: grey strata, ochre bands, dark seeps, scrub."""
    a, r, f = new()
    grey = np.tile(grade(src("rock023"), tint=(1.0, 0.97, 0.90), gain=1.0, contrast=1.1), (4, 4, 1))
    ochre = np.tile(grade(src("rock003"), tint=(1.0, 0.93, 0.78), gain=0.95), (4, 4, 1))
    pale = np.tile(grade(src("rock021"), gain=0.9, sat=0.8), (4, 4, 1))
    n1, n2, n3 = tnoise(S, 3, 31), tnoise(S, 5, 32), tnoise(S, 2, 33)
    # horizontal banding: stretch the noise along x
    bands = np.repeat(tnoise(S, 6, 34)[:, ::8], 8, axis=1)
    img = blend(grey, ochre, np.clip((bands * 0.7 + n1 * 0.3 - 0.5) * 4, 0, 1))
    img = blend(img, pale, np.clip((n2 - 0.6) * 4, 0, 1) * 0.7)
    # vertical dark seeps
    seep = np.repeat(tnoise(S, 16, 35)[::16, :], 16, axis=0)
    img *= 1.0 - 0.28 * np.clip((seep - 0.62) * 5, 0, 1)[:, :, None]
    img *= (0.84 + 0.32 * n3)[:, :, None]
    scrub = np.tile(grade(src("moss001"), gain=0.7, sat=0.8), (4, 4, 1))
    img = blend(img, scrub, np.clip((tnoise(S, 9, 36) * 0.6 + tnoise(S, 24, 37) * 0.4 - 0.66) * 9, 0, 1) * 0.85)
    a[:] = np.clip(img, 0, 255)
    for k in range(8):
        r["columns"]["rupe_faccia_%d" % k] = [k * 256, 0, (k + 1) * 256, S]
    save(15, a, r, f)


def window(col, y_sill, w=96, h=150, kind="buio"):
    """A window opening in a 256 px wide column; y measured in px from the bottom (128 px = 1 m)."""
    x0 = (256 - w) // 2
    y1 = S - y_sill
    y0 = y1 - h
    frame = np.array([92, 84, 72.0])
    col[y0 - 8:y1 + 8, x0 - 8:x0 + w + 8] = col[y0 - 8:y1 + 8, x0 - 8:x0 + w + 8] * 0.55 + frame * 0.45
    if kind == "buio":
        g = np.linspace(0.04, 0.16, h)[:, None, None]
        col[y0:y1, x0:x0 + w] = np.array([40, 44, 50.0]) * (g * 4)
        col[y0:y1, x0 + w // 2 - 3:x0 + w // 2 + 3] = (58, 50, 40)          # the rotten mullion
        col[y0 + h // 2 - 3:y0 + h // 2 + 3, x0:x0 + w] = (58, 50, 40)
    else:                                                                 # shutters, weathered green
        wood = grade(src("planks002", 256), tint=(0.55, 0.78, 0.62), gain=0.7)
        col[y0:y1, x0:x0 + w] = wood[:h, :w]
        col[y0:y1, x0 + w // 2 - 2:x0 + w // 2 + 2] *= 0.4
        for yy in range(y0 + 6, y1, 12):
            col[yy:yy + 2, x0:x0 + w] *= 0.6


def walls():
    """16: the tonnara - 8 columns, 256 px = 2 m wide, 16 m tall, ground at the bottom. Every mask is periodic
    over 256 px in x, so any column continues into any other column beside it without a seam."""
    a, r, f = new()
    st = grade(src("rocks004", 256), tint=(1.0, 0.96, 0.88), gain=0.95, sat=0.8)      # the scan = 2 m: stones of 20-30 cm
    stone = np.tile(st, (8, 1, 1))
    white = np.tile(grade(src("paintedplaster006"), tint=(1.0, 0.97, 0.9), gain=0.92), (4, 1, 1))[:, :256]
    yellow = np.tile(grade(src("paintedplaster018"), tint=(1.0, 0.92, 0.75), gain=0.9, sat=0.8), (4, 1, 1))[:, :256]
    blocks = np.tile(grade(src("bricks024"), tint=(1.0, 0.95, 0.84), gain=0.9), (4, 1, 1))[:, :256]
    molo = np.tile(grade(src("concrete005"), gain=0.9), (4, 1, 1))[:, :256]
    y = (np.arange(S)[::-1] / 128.0)[:, None]                 # metres above ground per row
    nx = np.tile(tnoise(256, 3, 51), (8, 1))                   # periodic in x and (every 2 m) in y
    ny = np.repeat(tnoise(S, 5, 52)[:, :1], 256, axis=1)       # varies with height only
    n = 0.6 * nx + 0.4 * ny

    def weather(col, plaster=None):
        """Plaster fallen off low down and in patches, damp and moss at the base, soot under the top."""
        if plaster is not None:
            keep = np.clip((y - 0.7 - 1.6 * n) * 2.2, 0, 1)                    # gone below 0.7-2.3 m
            keep *= 1 - np.clip((nx * 0.5 + ny * 0.5 - 0.66) * 9, 0, 1)        # and in patches higher up
            col = blend(col, plaster, keep)
        damp = np.clip(1.25 - y / 1.0, 0, 1) * (0.45 + n)
        col = col * (1 - 0.38 * np.clip(damp, 0, 1))[:, :, None]
        mm = np.clip(damp - 0.72, 0, 1) * 0.65
        col = col * (1 - mm[:, :, None]) + np.array([70, 84, 48.0]) * mm[:, :, None]
        return col * (0.9 + 0.2 * ny)[:, :, None]

    def with_window(col, kind):
        col = col.copy()
        window(col, 140, w=120, h=172, kind=kind)
        return col

    cols = {}
    cols["fac_ton_pietra"] = weather(stone.copy())
    cols["fac_ton_pietra_fin"] = with_window(cols["fac_ton_pietra"], "buio")
    cols["fac_ton_bianco"] = weather(stone.copy(), white)
    cols["fac_ton_bianco_fin"] = with_window(cols["fac_ton_bianco"], "persiana")
    cols["fac_ton_giallo"] = weather(stone.copy(), yellow)
    cols["fac_ton_giallo_fin"] = with_window(cols["fac_ton_giallo"], "buio")
    cols["fac_ton_blocchi"] = weather(blocks.copy())
    cols["fac_ton_molo"] = weather(molo.copy())
    for k, (name, img) in enumerate(cols.items()):
        a[:, k * 256:(k + 1) * 256] = img
        r["columns"][name] = [k * 256, 0, (k + 1) * 256, S]
    save(16, a, r, f)


if __name__ == "__main__":
    floors()
    cliff()
    walls()
