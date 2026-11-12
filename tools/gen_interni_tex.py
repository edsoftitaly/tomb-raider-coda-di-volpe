"""Atlases 17-18: photographic textures (ambientCG, CC0) for the enclosed rooms of the adventure - the cave of
Donna Villa, the Roman houses, cisterns and crypt of Tindari, the temple of the Dioscuri.

17: floor/ceiling tiles, 256 px = 2 m.   18: wall columns, 256 px wide, periodic every 2 m in height (rooms sit
at any height, so nothing here is registered to the ground).
"""
import numpy as np
from PIL import Image, ImageDraw

from gen_marinello_tex import FS, S, blend, grade, new, save, src, tnoise


def tile(a, r, f, k, name, img, fs):
    x0, y0 = (k % 8) * 256, (k // 8) * 256
    a[y0:y0 + 256, x0:x0 + 256] = img[:256, :256]
    r["tiles"][name] = [x0, y0, x0 + 256, y0 + 256]
    r["macro"][name] = [x0, y0, 256]          # usable on terrain too (one tile per sector)
    f[y0 // 64:y0 // 64 + 4, x0 // 64:x0 // 64 + 4] = FS[fs]


def slabs(base, n, seed, joint=0.45, jitter=0.1):
    """n x n paving slabs cut into a seamless photo: darker joints, each slab its own shade."""
    rng = np.random.default_rng(seed)
    out = base.copy()
    step = 256 // n
    for i in range(n):
        for j in range(n):
            out[i * step:(i + 1) * step, j * step:(j + 1) * step] *= 1 + rng.uniform(-jitter, jitter)
    for i in range(n):
        out[i * step:i * step + 2, :] *= joint
        out[:, i * step:i * step + 2] *= joint
        out[i * step + 2:i * step + 3, :] *= 1.12
        out[:, i * step + 2:i * step + 3] *= 1.12
    return np.clip(out, 0, 255)


def mosaic(draw_fn, seed, ground=(206, 192, 160)):
    """A mosaic panel: the drawing is sampled on a grid of 8 px tesserae, each with its own shade, grout between."""
    rng = np.random.default_rng(seed)
    im = Image.new("RGB", (256, 256), ground)
    d = ImageDraw.Draw(im)
    draw_fn(d)
    px = np.asarray(im, float)
    out = np.zeros((256, 256, 3))
    for i in range(32):
        for j in range(32):
            c = px[i * 8 + 4, j * 8 + 4] * rng.uniform(0.86, 1.1)
            out[i * 8:(i + 1) * 8, j * 8:(j + 1) * 8] = c
    out[::8, :] *= 0.62
    out[:, ::8] *= 0.62
    wear = tnoise(256, 4, seed + 1)
    out *= (0.82 + 0.3 * wear)[:, :, None]
    return np.clip(out, 0, 255)


def border(d, col):
    d.rectangle([8, 8, 247, 247], outline=col, width=8)
    d.rectangle([24, 24, 231, 231], outline=col, width=8)


def star(d, cx, cy, r, col, points=8):
    pts = []
    for k in range(points * 2):
        a = np.pi * k / points - np.pi / 2
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + np.cos(a) * rr, cy + np.sin(a) * rr))
    d.polygon(pts, fill=col)


def pileus(col, starcol):
    """The cap of a Dioscurus (a tall egg-shaped felt cap) with his star above it."""
    def fn(d):
        border(d, col)
        d.pieslice([72, 88, 184, 300], 180, 360, fill=col)
        d.rectangle([64, 192, 192, 208], fill=col)
        star(d, 128, 66, 26, starcol)
    return fn


def tiles():
    a, r, f = new()
    rock = grade(src("ground012", 256), tint=(0.95, 0.93, 0.9), gain=0.85, contrast=1.15)
    wet = grade(src("rock038", 256), tint=(0.7, 0.82, 0.84), gain=0.7, contrast=1.2)
    roof = grade(src("rock022", 256), tint=(0.9, 0.88, 0.86), gain=0.7)
    pav = grade(src("bricks008", 256), tint=(1.0, 0.94, 0.8), gain=1.0)
    lime = grade(src("ground034", 256), tint=(1.0, 0.97, 0.9), gain=0.95, sat=0.7)
    moss = grade(src("moss001", 256), gain=0.7)
    mm = np.clip((tnoise(256, 3, 31) - 0.5) * 6, 0, 1)
    brick = grade(src("pavingstones021", 256), tint=(1.0, 0.92, 0.84), gain=0.9)
    plaster = grade(src("ground033", 256), tint=(0.95, 0.93, 0.88), gain=0.8, sat=0.6)
    planks = grade(src("planks016", 256), gain=0.72)
    earth = grade(src("ground029", 256), tint=(0.95, 0.88, 0.76), gain=0.7)
    bronze = grade(src("rust002", 256), tint=(0.62, 0.8, 0.66), gain=1.6, sat=0.7)
    k = 0
    for name, img, fs in (
            ("g_pav", rock, "stone"), ("g_soffitto", roof, "stone"), ("g_bagnato", wet, "stone"),
            ("t_lastre", pav, "stone"), ("t_lastre_muschio", blend(pav, moss, mm * 0.8), "stone"),
            ("t_marmo_pav", slabs(lime * 1.05, 2, 3, joint=0.6, jitter=0.05), "marble"), ("t_mattoni_pav", brick, "stone"),
            ("t_mos_castore", mosaic(pileus((52, 46, 44), (140, 60, 40)), 11), "marble"),
            ("t_mos_polluce", mosaic(pileus((196, 140, 42), (232, 196, 80)), 12), "marble"),
            ("t_mos_vuoto", mosaic(lambda d: border(d, (120, 70, 50)), 13), "marble"),
            ("t_stella", mosaic(lambda d: (border(d, (60, 70, 110)), star(d, 128, 128, 84, (214, 170, 60))), 14, ground=(40, 48, 84)), "marble"),
            ("t_volta", plaster, "concrete"), ("t_tavole", planks, "wood"), ("t_bronzo", bronze, "metal"),
            ("t_terra_battuta", earth, "mud"), ("t_marmo_scuro", slabs(lime * 0.5, 4, 5, joint=0.5), "marble")):
        tile(a, r, f, k, name, img, fs)
        k += 1
    save(17, a, r, f)


def column(img256):
    return np.tile(img256[:256, :256], (8, 1, 1))


def courses(base, h, w, seed, joint=0.4, jitter=0.1, bevel=True):
    """Ashlar masonry drawn into a photo: courses h px high, blocks w px long, half-offset, periodic in 256 px."""
    rng = np.random.default_rng(seed)
    out = base.copy()
    for ci, y in enumerate(range(0, 256, h)):
        off = (w // 2) if ci % 2 else 0
        for x in range(-off, 256, w):
            shade = 1 + rng.uniform(-jitter, jitter)
            xs = np.arange(x, x + w) % 256
            out[y:y + h, xs] *= shade
            out[y:y + h, (x % 256):(x % 256) + 2] *= joint
            if bevel:
                out[y:y + h, ((x + 2) % 256):((x + 2) % 256) + 1] *= 1.15
        out[y:y + 2, :] *= joint
        if bevel:
            out[y + 2:y + 3, :] *= 1.15
    return np.clip(out, 0, 255)


def scratches(col, seed):
    """The marks of Donna Villa's fingers: groups of five long grooves, raked downwards."""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (256, S), 0)
    d = ImageDraw.Draw(im)
    for g in range(9):
        y0 = 40 + g * 225 + int(rng.uniform(-20, 20))
        x0 = int(rng.uniform(40, 120))
        lean = rng.uniform(-30, 30)
        for fgr in range(5):
            x = x0 + fgr * 22 + rng.uniform(-3, 3)
            ln = rng.uniform(110, 170) - abs(fgr - 2) * 14
            d.line([(x, y0 + abs(fgr - 2) * 9), (x + lean, y0 + ln)], fill=255, width=7)
    m = np.asarray(im, float) / 255.0
    lit = np.roll(m, 3, axis=1)
    out = col * (1 - 0.72 * m[:, :, None])
    out += 46 * np.clip(lit - m, 0, 1)[:, :, None]
    return np.clip(out, 0, 255)


def walls():
    a, r, f = new()
    rock = grade(src("rock023", 256), tint=(0.9, 0.88, 0.86), gain=0.72, contrast=1.15)
    lime = grade(src("bricks008", 256), tint=(1.0, 0.93, 0.78), gain=1.05)
    moss = grade(src("moss001", 256), gain=0.6)
    mm = np.clip((tnoise(256, 3, 41) - 0.48) * 5, 0, 1)
    brick = grade(src("pavingstones021", 256), tint=(1.0, 0.9, 0.82), gain=0.85)
    red = grade(src("ground033", 256), tint=(0.78, 0.27, 0.2), gain=0.8, sat=0.9, contrast=1.6)
    scuff = np.clip((tnoise(256, 5, 42) - 0.66) * 6, 0, 1)
    red = blend(red, grade(src("paintedplaster006", 256), gain=0.6), scuff * 0.5)
    cist = grade(src("concrete005", 256), tint=(0.7, 0.82, 0.74), gain=0.6)
    cist[100:106, :] *= 0.6
    cist[200:204, :] *= 0.7
    opera = lime
    cols = {
        "g_parete": column(rock),
        "g_graffi": scratches(column(rock), 7),
        "t_opera": column(opera),
        "t_opera_muschio": column(blend(opera, moss, mm * 0.85)),
        "t_mattoni": column(brick),
        "t_rosso": column(red),
        "t_marmo": column(grade(src("bricks024", 256), tint=(1.0, 0.97, 0.9), gain=0.95)),
        "c_cisterna": column(cist),
    }
    for k, (name, img) in enumerate(cols.items()):
        a[:, k * 256:(k + 1) * 256] = img
        r["columns"][name] = [k * 256, 0, (k + 1) * 256, S]
    save(18, a, r, f)


if __name__ == "__main__":
    tiles()
    walls()


def sanctuary():
    """Atlas 19: the walls of the sanctuary of Tindari, registered to the ground (128 px per metre, the ground at
    the bottom of the 16 m column): pale ashlar with pink courses, arched windows, three portals, a rose window."""
    a, r, f = new()
    stone = np.tile(grade(src("bricks024", 256), tint=(1.0, 0.95, 0.85), gain=1.0), (8, 1, 1))
    pink = np.tile(grade(src("bricks024", 256), tint=(1.0, 0.78, 0.7), gain=0.95), (8, 1, 1))
    base = stone.copy()
    for m in range(0, 16, 2):                                  # a pink course every 2 m
        y1 = S - m * 128
        base[max(y1 - 40, 0):y1] = pink[max(y1 - 40, 0):y1]
    base[S - 110:S] *= 0.82                                    # the plinth

    def paint(fn):
        im = Image.fromarray(base.astype(np.uint8))
        d = ImageDraw.Draw(im)
        Y = lambda m: S - int(m * 128)                         # noqa: E731

        def arch(x0, x1, y0m, y1m, fill, frame=(150, 118, 96), w=10):
            rad = (x1 - x0) // 2
            top = Y(y1m)
            d.rectangle([x0 - w, top + rad, x1 + w, Y(y0m)], fill=frame)
            d.pieslice([x0 - w, top - w, x1 + w, top + 2 * rad + w], 180, 360, fill=frame)
            d.rectangle([x0, top + rad, x1, Y(y0m)], fill=fill)
            d.pieslice([x0, top, x1, top + 2 * rad], 180, 360, fill=fill)
        fn(d, Y, arch)
        return np.asarray(im, float)

    glass, wood, dark = (38, 52, 70), (74, 48, 30), (24, 22, 26)

    def finestra(d, Y, arch):
        arch(84, 172, 4.4, 7.6, glass)
        d.line([128, Y(4.4), 128, Y(7.2)], fill=(150, 118, 96), width=5)

    def torre(d, Y, arch):
        arch(104, 152, 3.6, 6.2, dark, w=7)
        arch(104, 152, 8.0, 10.4, dark, w=7)
        arch(60, 196, 11.6, 14.6, dark, w=12)                   # the belfry
        d.rectangle([60, Y(11.9), 196, Y(11.6)], fill=(150, 118, 96))

    def portale(d, Y, arch):
        arch(36, 220, 0.0, 5.2, wood, w=14)
        d.line([128, Y(0), 128, Y(4.2)], fill=(40, 26, 18), width=5)
        for yy in (1.0, 2.2, 3.4):
            d.line([44, Y(yy), 212, Y(yy)], fill=(52, 34, 22), width=3)
        cy = Y(9.0)
        d.ellipse([128 - 104, cy - 104, 128 + 104, cy + 104], fill=(150, 118, 96))
        d.ellipse([128 - 88, cy - 88, 128 + 88, cy + 88], fill=glass)
        for k in range(8):
            an = np.pi * k / 4
            d.line([128, cy, 128 + np.cos(an) * 88, cy + np.sin(an) * 88], fill=(190, 160, 110), width=5)
        d.ellipse([128 - 20, cy - 20, 128 + 20, cy + 20], fill=(200, 160, 70))

    def portalino(d, Y, arch):
        arch(64, 192, 0.0, 3.6, wood, w=10)
        d.line([128, Y(0), 128, Y(3.0)], fill=(40, 26, 18), width=4)
        arch(96, 160, 6.2, 8.4, glass, w=8)

    def tamburo(d, Y, arch):
        arch(92, 164, 11.2, 13.2, glass, w=8)

    for k, (name, fn) in enumerate((("fac_sant_muro", lambda d, Y, arch: None), ("fac_sant_finestra", finestra), ("fac_sant_torre", torre),
                                    ("fac_sant_portale", portale), ("fac_sant_portalino", portalino), ("fac_sant_tamburo", tamburo))):
        a[:, k * 256:(k + 1) * 256] = paint(fn)
        r["columns"][name] = [k * 256, 0, (k + 1) * 256, S]
    save(19, a, r, f)


if __name__ == "__main__":
    sanctuary()
