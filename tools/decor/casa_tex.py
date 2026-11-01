"""Procedural textures for Ed's house in Via Gaspare Amodeo (exterior from Street View, interior furnishings).

Exterior: cream plaster, brown base band, windows with green shutters, French windows on the balcony,
patterned metal art-deco street door, iron railings, drainpipe. Interior: woods, fabrics, tiles,
appliances, books, rugs, a painting, papers scattered by the thieves. All drawn here.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from decor.santuario_tex import from_img, tex, to_img
from decor.tex import rgba

CREAM = (226, 212, 176)
GREEN = (58, 98, 70)
BROWN = (110, 84, 62)


def plaster(seed=1):
    return rgba(tex(256, 256, CREAM, seed, 0.1, 48))


def base_band(seed=2):
    img = tex(256, 128, BROWN, seed, 0.18, 12)
    return rgba(img)


def window_shutters(seed=3, lit=False):
    """Window with open green shutters on cream (128 x 160 = 2.0 x 2.5 m incl. frame and sill)."""
    im = to_img(tex(128, 160, CREAM, seed, 0.1, 32))
    d = ImageDraw.Draw(im)
    glass = (250, 214, 130) if lit else (34, 44, 62)
    d.rectangle([36, 26, 92, 132], fill=(236, 232, 222))
    d.rectangle([42, 32, 86, 126], fill=glass)
    d.line([(64, 32), (64, 126)], fill=(236, 232, 222), width=3)
    d.line([(42, 78), (86, 78)], fill=(236, 232, 222), width=3)
    for x0 in (6, 94):     # shutters folded against the wall
        d.rectangle([x0, 26, x0 + 28, 132], fill=GREEN)
        for y in range(32, 128, 6):
            d.line([(x0 + 3, y), (x0 + 25, y + 2)], fill=(40, 72, 52), width=2)
    d.rectangle([30, 132, 98, 140], fill=(214, 210, 200))
    d.rectangle([30, 18, 98, 26], fill=(214, 210, 200))
    return from_img(im)


def french_window(seed=4):
    """Balcony door with green shutters (128 x 192 = 2.0 x 3.0 m)."""
    im = to_img(tex(128, 192, CREAM, seed, 0.1, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([36, 14, 92, 192], fill=(236, 232, 222))
    d.rectangle([42, 20, 86, 192], fill=(40, 48, 62))
    d.line([(64, 20), (64, 192)], fill=(236, 232, 222), width=3)
    for y in (70, 120):
        d.line([(42, y), (86, y)], fill=(236, 232, 222), width=3)
    for x0 in (6, 94):
        d.rectangle([x0, 14, x0 + 28, 192], fill=GREEN)
        for y in range(20, 188, 6):
            d.line([(x0 + 3, y), (x0 + 25, y + 2)], fill=(40, 72, 52), width=2)
    return from_img(im)


def artdeco_door(seed=5):
    """The street door: dark metal with geometric art-deco pattern, glass fanlight (128 x 256 = 1.6 x 3.2 m)."""
    im = to_img(tex(128, 256, CREAM, seed, 0.1, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 0, 120, 256], fill=(214, 206, 186))
    d.rectangle([16, 8, 112, 256], fill=(46, 44, 40))
    d.rectangle([20, 12, 108, 56], fill=(70, 86, 96))          # fanlight
    for x in range(26, 108, 14):
        d.line([(64, 54), (x, 14)], fill=(46, 44, 40), width=2)
    for leaf in (0, 1):
        x0 = 20 + leaf * 46
        d.rectangle([x0, 62, x0 + 42, 250], outline=(120, 110, 86), width=2)
        for k in range(4):
            y = 74 + k * 44
            d.polygon([(x0 + 21, y), (x0 + 38, y + 18), (x0 + 21, y + 36), (x0 + 4, y + 18)], outline=(150, 136, 98), width=2)
            d.ellipse([x0 + 17, y + 14, x0 + 25, y + 22], fill=(160, 144, 100))
    d.rectangle([60, 150, 68, 160], fill=(180, 160, 110))
    return from_img(im)


def shop_shutter(seed=6):
    """Garage / shop roller shutter on the ground floor (128 x 128 = 2.4 x 2.4 m)."""
    im = to_img(tex(128, 128, CREAM, seed, 0.1, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, 120, 128], fill=(150, 150, 146))
    for y in range(10, 128, 6):
        d.line([(8, y), (120, y)], fill=(118, 118, 114), width=2)
    return from_img(im)


def drainpipe(seed=7):
    """Cream wall with a vertical copper drainpipe and brackets (128 x 128 = 2 x 2 m), climbable strip."""
    im = to_img(tex(128, 128, CREAM, seed, 0.1, 32))
    d = ImageDraw.Draw(im)
    d.rectangle([56, 0, 72, 128], fill=(150, 96, 58))
    d.rectangle([60, 0, 64, 128], fill=(190, 130, 84))
    for y in (20, 84):
        d.rectangle([48, y, 80, y + 6], fill=(60, 50, 40))
    return from_img(im)


def pergola_wood(seed=8):
    return rgba(tex(64, 64, (128, 90, 56), seed, 0.25, 6))


def cane_mat(seed=9):
    """Reed mat over the pergola (alpha gaps)."""
    img = np.zeros((128, 128, 4))
    for x in range(0, 128, 4):
        c = 180 + (x * 37 % 30)
        img[:, x:x + 3, :3] = (c, c - 30, c - 90)
        img[:, x:x + 3, 3] = 255
    return img


# ------------------------------------------------------------------------- interior
def wood(seed, color, grain=40):
    img = tex(128, 128, color, seed, 0.15, 8)
    x = np.linspace(0, grain, 128)[None, :]
    n = np.asarray(tex(128, 128, (1, 1, 1), seed + 1, 1.0, 16))[..., 0]
    img *= (0.92 + 0.08 * np.sin(x + n * 3))[..., None]
    return rgba(np.clip(img, 0, 255))


def fabric(seed, color, check=None):
    img = tex(128, 128, color, seed, 0.1, 4)
    if check:
        for i in range(0, 128, 16):
            img[i:i + 3] = check
            img[:, i:i + 3] = check
    return rgba(img)


def bedspread(seed=20):
    im = to_img(tex(128, 128, (200, 196, 230), seed, 0.08, 6))
    d = ImageDraw.Draw(im)
    for y in range(8, 128, 24):
        for x in range(8 + (12 if (y // 24) % 2 else 0), 128, 24):
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(120, 110, 170))
    d.rectangle([0, 0, 128, 6], fill=(120, 110, 170))
    return from_img(im)


def books(seed=21):
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (128, 128), (96, 66, 40))
    d = ImageDraw.Draw(im)
    for shelf in range(4):
        y0, y1 = shelf * 32 + 4, shelf * 32 + 28
        x = 2
        while x < 124:
            w = int(r.integers(4, 9))
            h = int(r.integers(14, 24))
            c = tuple(int(v) for v in r.choice([(140, 40, 40), (40, 70, 120), (60, 100, 60), (190, 170, 120), (90, 60, 100), (30, 30, 30)]))
            d.rectangle([x, y1 - h, x + w - 1, y1], fill=c)
            x += w + 1
        d.rectangle([0, y1, 128, y1 + 4], fill=(120, 84, 50))
    return from_img(im)


def tiles_kitchen(seed=22):
    im = Image.new("RGB", (128, 128), (236, 236, 230))
    d = ImageDraw.Draw(im)
    for y in range(0, 128, 16):
        for x in range(0, 128, 16):
            if (x // 16 + y // 16) % 2:
                d.rectangle([x, y, x + 15, y + 15], fill=(70, 130, 170))
            d.rectangle([x, y, x + 15, y + 15], outline=(200, 200, 196))
    return from_img(im)


def appliance(seed=23):
    """Fridge front: white, door split, handle (64 x 128)."""
    im = to_img(tex(64, 128, (232, 232, 228), seed, 0.04))
    d = ImageDraw.Draw(im)
    d.line([(0, 44), (64, 44)], fill=(170, 170, 166), width=2)
    d.rectangle([52, 14, 56, 36], fill=(150, 150, 150))
    d.rectangle([52, 54, 56, 92], fill=(150, 150, 150))
    return from_img(im)


def hob(seed=24):
    im = Image.new("RGB", (128, 64), (30, 30, 32))
    d = ImageDraw.Draw(im)
    for cx, cy, r in ((30, 20, 12), (30, 46, 10), (96, 20, 10), (96, 46, 12)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(90, 90, 90), width=3)
    d.rectangle([56, 4, 72, 60], fill=(200, 200, 196))     # sink
    return from_img(im)


def cabinet(seed=25):
    im = to_img(tex(128, 64, (214, 200, 170), seed, 0.06))
    d = ImageDraw.Draw(im)
    for x in (0, 64):
        d.rectangle([x + 3, 3, x + 61, 61], outline=(160, 144, 110), width=2)
        d.rectangle([x + 28, 10, x + 36, 13], fill=(120, 120, 120))
    return from_img(im)


def ceramic(seed=26):
    return rgba(tex(64, 64, (244, 244, 240), seed, 0.04))


def tv_screen(seed=27):
    im = Image.new("RGB", (128, 72), (20, 20, 22))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, 124, 68], fill=(28, 34, 46))
    return from_img(im)


def rug(seed=28):
    im = to_img(tex(128, 128, (150, 50, 46), seed, 0.1, 6))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 122, 122], outline=(220, 190, 120), width=4)
    d.rectangle([18, 18, 110, 110], outline=(40, 50, 90), width=3)
    d.polygon([(64, 30), (98, 64), (64, 98), (30, 64)], outline=(220, 190, 120), width=3)
    d.ellipse([54, 54, 74, 74], fill=(40, 50, 90))
    return from_img(im)


def painting(seed=29):
    """A seascape: the Tindari cape over the Marinello lagoons at sunset, framed (128 x 96)."""
    w, h = 128, 96
    y = np.linspace(0, 1, h)[:, None, None]
    sky = np.array((250, 170, 90)) * (1 - y) + np.array((120, 90, 140)) * y
    img = np.repeat(sky, w, axis=1)
    im = to_img(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 56, w, h], fill=(40, 80, 120))
    d.polygon([(60, 56), (90, 22), (110, 30), (128, 40), (128, 56)], fill=(70, 60, 50))
    d.rectangle([92, 16, 98, 24], fill=(240, 230, 210))      # the sanctuary on top
    d.polygon([(20, 60), (60, 58), (80, 62), (30, 64)], fill=(220, 200, 150))   # the sandbar
    d.rectangle([0, 0, w - 1, h - 1], outline=(170, 130, 60), width=6)
    return from_img(im)


def papers(seed=30):
    r = np.random.default_rng(seed)
    img = np.zeros((128, 128, 4))
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(9):
        cx, cy = r.uniform(16, 112, 2)
        a = r.uniform(0, math.pi)
        pts = [(cx + 14 * math.cos(a + t) - 0, cy + 18 * math.sin(a + t)) for t in (0.6, 2.5, 3.7, 5.6)]
        d.polygon(pts, fill=(240, 236, 224, 255))
        d.line(pts[:2], fill=(120, 120, 140, 255), width=1)
    img = np.asarray(im, float)
    return img


def curtain(seed=31):
    img = tex(64, 128, (226, 214, 190), seed, 0.06)
    x = np.linspace(0, 10 * math.pi, 64)[None, :]
    img *= (0.88 + 0.12 * np.sin(x))[..., None]
    return rgba(np.clip(img, 0, 255))


def night_window(seed=32):
    """Window seen from inside at night: dark blue glass, white frame, closed slats (128 x 160)."""
    im = Image.new("RGB", (128, 160), (236, 232, 222))
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 118, 150], fill=(20, 28, 52))
    d.line([(64, 10), (64, 150)], fill=(236, 232, 222), width=4)
    d.line([(10, 80), (118, 80)], fill=(236, 232, 222), width=4)
    for y in range(14, 148, 8):     # shutter slats behind, with moonlight through
        d.line([(12, y), (116, y + 2)], fill=(40, 56, 80), width=2)
    return from_img(im)


def door_leaf(seed=33):
    im = to_img(tex(64, 128, (150, 100, 60), seed, 0.12, 8))
    d = ImageDraw.Draw(im)
    for y0 in (8, 68):
        d.rectangle([8, y0, 56, y0 + 52], outline=(110, 72, 42), width=3)
    d.ellipse([50, 62, 56, 68], fill=(200, 180, 110))
    return from_img(im)


def railing_col(color, seed=40):
    """Balcony railing, transparent between the bars (128 x 64 = 2 x 1 m)."""
    img = np.zeros((64, 128, 4))
    img[..., :3] = color
    img[0:5, :, 3] = 255
    img[58:64, :, 3] = 255
    for x in range(0, 128, 9):
        img[:, x:x + 3, 3] = 255
    for x in range(4, 128, 18):          # small scrolls
        img[20:44, x:x + 2, 3] = 255
    return img


def awning(seed=41):
    im = Image.new("RGB", (128, 64), (176, 36, 32))
    d = ImageDraw.Draw(im)
    for x in range(0, 128, 16):
        d.rectangle([x, 0, x + 7, 64], fill=(196, 52, 44))
    for x in range(0, 128, 16):
        d.polygon([(x, 54), (x + 8, 64), (x + 16, 54)], fill=(150, 30, 26))
    return from_img(im)


def scaffold_net(seed=42):
    """Green-white construction mesh on scaffolding (alpha holes)."""
    img = np.zeros((128, 128, 4))
    img[..., :3] = (214, 222, 214)
    img[..., 3] = 200
    for k in range(0, 128, 4):
        img[k:k + 1, :, 3] = 255
        img[:, k:k + 1, 3] = 255
    img[:, :, 3][(np.indices((128, 128)).sum(0) % 6) == 0] = 0
    return img


def fruit(seed=43):
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (128, 64), (120, 84, 52))
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, yy = r.integers(0, 128), r.integers(0, 64)
        c = tuple(int(v) for v in r.choice([(220, 120, 30), (200, 40, 30), (240, 200, 60), (90, 150, 50)]))
        d.ellipse([x - 4, yy - 4, x + 4, yy + 4], fill=c)
    return from_img(im)


def _font(size):
    from PIL import ImageFont
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def bin_plastic(color, seed):
    """Wheelie bin side: moulded plastic with ribs, a sticker and grime."""
    r = np.random.default_rng(seed)
    a = np.ones((128, 128, 3)) * np.array(color, float)
    a *= (0.92 + 0.08 * r.random((128, 128)))[..., None]
    for x in range(10, 128, 22):
        a[:, x:x + 3] *= 0.8
    a[:14] *= 0.7
    a[100:] *= np.linspace(1, 0.75, 28)[:, None, None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([44, 40, 84, 66], fill=(236, 236, 230))
    d.text((49, 45), "RSU", fill=(30, 30, 30), font=_font(14))
    return from_img(im)


def ac_unit(seed=50):
    im = Image.new("RGB", (128, 96), (222, 222, 216))
    d = ImageDraw.Draw(im)
    d.ellipse([12, 10, 84, 82], fill=(70, 72, 74))
    for k in range(0, 72, 7):
        d.line([(12, 10 + k), (84, 10 + k)], fill=(150, 150, 146), width=2)
    d.rectangle([92, 20, 120, 76], outline=(170, 170, 164), width=2)
    d.line([(0, 95), (128, 95)], fill=(120, 110, 96), width=3)
    return from_img(im)


def laundry(seed=51):
    """Clothes on a line (alpha): shirts, towels, sheets in the colours of a Sicilian balcony."""
    r = np.random.default_rng(seed)
    img = np.zeros((128, 256, 4))
    x = 4
    while x < 240:
        w = int(r.integers(26, 56))
        h = int(r.integers(50, 120))
        col = r.choice([(236, 234, 226), (200, 60, 50), (60, 100, 170), (240, 200, 70), (120, 170, 120), (230, 140, 170)])
        w = min(w, 256 - x)
        h = min(h, 126)
        img[2:2 + h, x:x + w, :3] = col
        img[2:2 + h, x:x + w, :3] *= (0.85 + 0.15 * np.sin(np.arange(w) / 4.0))[None, :, None]
        img[2:2 + h, x:x + w, 3] = 255
        img[0:3, x - 2:x + w + 2, :3] = (40, 40, 40)
        img[0:3, x - 2:x + w + 2, 3] = 255
        x += w + int(r.integers(4, 14))
    img[0:2, :, :3] = (50, 50, 50)
    img[0:2, :, 3] = 255
    return img


def blade_sign(kind):
    im = Image.new("RGB", (128, 128), (20, 40, 110) if kind == "tabacchi" else (20, 130, 60))
    d = ImageDraw.Draw(im)
    if kind == "tabacchi":
        d.rectangle([6, 6, 121, 121], outline=(240, 240, 240), width=4)
        d.text((40, 18), "T", fill=(250, 250, 250), font=_font(84))
    else:
        d.rectangle([0, 0, 127, 127], fill=(10, 30, 16))
        d.rectangle([48, 14, 80, 114], fill=(60, 230, 110))
        d.rectangle([14, 48, 114, 80], fill=(60, 230, 110))
    return from_img(im)


def street_plaque(seed=52):
    r = np.random.default_rng(seed)
    a = np.ones((64, 160, 3)) * 232 * (0.95 + 0.05 * r.random((64, 160)))[..., None]
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, 156, 60], outline=(40, 40, 40), width=2)
    d.text((14, 8), "VIA GASPARE", fill=(20, 20, 20), font=_font(18))
    d.text((34, 32), "AMODEO", fill=(20, 20, 20), font=_font(20))
    return from_img(im)


def cable(seed=53):
    return from_img(Image.new("RGB", (16, 16), (18, 18, 20)))


def argano_front(seed=54):
    """Front of the shutter winch box: galvanised door, yellow-black edge, hex socket, label."""
    im = Image.new("RGB", (96, 128), (168, 172, 176))
    d = ImageDraw.Draw(im)
    for k in range(0, 96 + 128, 12):          # hazard border
        d.line([(k, 0), (k - 128, 128)], fill=(30, 30, 30), width=5)
    d.rectangle([0, 0, 95, 127], outline=(220, 180, 30), width=7)
    d.rectangle([10, 10, 85, 117], fill=(176, 180, 184), outline=(110, 112, 116), width=2)
    d.rectangle([22, 16, 74, 34], fill=(236, 234, 226))
    d.text((48, 25), "ARGANO", fill=(20, 20, 20), font=_font(11), anchor="mm")
    d.ellipse([33, 48, 63, 78], fill=(40, 40, 42))
    d.regular_polygon((48, 63, 9), 6, fill=(150, 150, 150))
    d.text((48, 98), "MANOVELLA", fill=(30, 30, 30), font=_font(9), anchor="mm")
    a = np.asarray(im).astype(float) * (1 + np.random.default_rng(seed).normal(0, 0.03, (128, 96)))[..., None]
    return from_img(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def build(pk):
    put = pk.put
    put("ca_argano", argano_front())
    put("ca_argano_lato", from_img(Image.new("RGB", (16, 16), (150, 154, 158))))
    put("ca_intonaco", plaster())
    put("ca_zoccolo", base_band())
    put("ca_finestra", window_shutters())
    put("ca_finestra_luce", window_shutters(13, lit=True))
    put("ca_portafinestra", french_window())
    put("ca_portone", artdeco_door())
    put("ca_saracinesca", shop_shutter())
    put("ca_grondaia", drainpipe())
    put("ca_pergola", pergola_wood())
    put("ca_canne", cane_mat())
    put("ca_noce", wood(40, (110, 70, 40)))
    put("ca_rovere", wood(41, (186, 146, 98)))
    put("ca_divano", fabric(42, (60, 90, 130)))
    put("ca_sedia", fabric(43, (150, 60, 50)))
    put("ca_coperta", bedspread())
    put("ca_lenzuolo", fabric(44, (236, 234, 226)))
    put("ca_libri", books())
    put("ca_piastrelle", tiles_kitchen())
    put("ca_frigo", appliance())
    put("ca_fornelli", hob())
    put("ca_mobile", cabinet())
    put("ca_ceramica", ceramic())
    put("ca_tv", tv_screen())
    put("ca_tappeto", rug())
    put("ca_quadro", painting())
    put("ca_carte", papers())
    put("ca_tenda", curtain())
    put("ca_finestra_notte", night_window())
    put("ca_porta", door_leaf())
    put("ca_ringhiera_verde", railing_col((48, 96, 86)))
    put("ca_ringhiera_nera", railing_col((34, 34, 36)))
    put("ca_ringhiera_arancio", railing_col((176, 98, 64)))
    put("ca_tenda_rossa", awning())
    put("ca_rete", scaffold_net())
    put("ca_frutta", fruit())
    put("ca_bidone_verde", bin_plastic((46, 110, 62), 60))
    put("ca_bidone_grigio", bin_plastic((92, 96, 100), 61))
    put("ca_condizionatore", ac_unit())
    put("ca_panni", laundry())
    put("ca_insegna_tabacchi", blade_sign("tabacchi"))
    put("ca_insegna_farmacia", blade_sign("farmacia"))
    put("ca_targa_via", street_plaque())
    put("ca_cavo", cable())
