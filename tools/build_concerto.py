"""CdV_Concerto.wad2: the stage of the Azraël concert in the arena of the theatre of Tindari (Ed, 14/11/2026).

Everything is modelled as it stands in the level: the audience is at -z (the cavea), so fronts face -z and every
static is placed with rotation 0. Metres, origin on the deck.

 460 TORRE_AMERICANA   truss tower, 6 m (collision)
 461 TETTO_AMERICANE   the roof: perimeter and middle truss with the lamps, 15 x 9 m at 5.6-6 m
 462 BATTERIA          drum riser with the kit and the throne (collision)
 463 STACK_SINISTRO    guitar stack, black with a silver panel (collision)
 464 STACK_DESTRO      guitar stack, black with a gold panel (collision)
 465 TASTIERA          88-key workstation on an X stand (collision)
 466 ASTA_MICROFONO    boom stand with its microphone, the boom towards +z (the player)
 467 WEDGE             stage monitor, the grille towards +z
 468 STENDARDO         the backdrop banner, 10 x 5 m (the logo comes from assets/foto/azrael_logo.png when it is there)
 469 LINE_ARRAY        six hung elements, origin at the rigging point
 470 STACK_BASSO       bass stack: valve head on an 8 x 10 cabinet (collision)

No maker's name or badge is drawn on amplifiers and keyboard.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from decor import geom as G
from decor import tex
from decor import wad2 as W
from decor.santuario_models import UP, V, fface, rectf

M = G.M
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "wads", "CdV_Concerto.wad2")
LOGO = os.path.join(ROOT, "assets", "foto", "azrael_logo.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
BAN_W, BAN_H = 10.0, 5.0


def arr(im):
    a = np.asarray(im.convert("RGBA"), dtype=np.float64).copy()
    return a


def noisy(w, h, color, seed, amount=0.25):
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 4))
    a[..., :3] = np.clip(np.array(color, float)[None, None] * (1 + (rng.random((h, w, 1)) - 0.5) * amount), 0, 255)
    a[..., 3] = 255
    return a


def t_truss():
    w, h, s = 128, 64, 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lit, mid, dark = (214, 218, 224, 255), (168, 173, 180, 255), (104, 108, 116, 255)
    for (a, b) in (((0, 6), (64, 58)), ((64, 58), (128, 6))):                       # the diagonals
        d.line([a[0] * s, a[1] * s, b[0] * s, b[1] * s], fill=mid, width=5 * s)
        d.line([a[0] * s, (a[1] - 1) * s, b[0] * s, (b[1] - 1) * s], fill=lit, width=2 * s)
    for y in (0, h - 9):                                                           # the two chords
        d.rectangle([0, y * s, w * s, (y + 9) * s], fill=mid)
        d.rectangle([0, (y + 1) * s, w * s, (y + 3) * s], fill=lit)
        d.rectangle([0, (y + 7) * s, w * s, (y + 9) * s], fill=dark)
    return arr(im.resize((w, h), Image.LANCZOS))


def _stencil(im, box, strength=0.8):
    """The band's own logo printed on a cabinet (as bands do on their backline); nothing if the file is not there."""
    if not os.path.exists(LOGO):
        return
    logo = Image.open(LOGO).convert("RGB")
    w, h = box[2] - box[0], box[3] - box[1]
    r = min(w / float(logo.width), h / float(logo.height))
    logo = logo.resize((max(1, int(logo.width * r)), max(1, int(logo.height * r))), Image.LANCZOS)
    a = logo.convert("L").point(lambda v: int(min(255, v * 1.6) * strength))
    im.paste(logo, (box[0] + (w - logo.width) // 2, box[1] + (h - logo.height) // 2), a)


def _cloth(d, box, base, line):
    d.rectangle(box, fill=base)
    for y in range(box[1] + 1, box[3], 2):
        d.line([box[0] + 1, y, box[2] - 1, y], fill=line)
    for x in range(box[0] + 1, box[2], 4):
        d.line([x, box[1] + 1, x, box[3] - 1], fill=tuple(int((a + b) / 2) for a, b in zip(base[:3], line[:3])) + (255,))


def _corners(d, w, h, c=(120, 122, 128, 255), n=14):
    for cx, cy in ((2, 2), (w - n - 3, 2), (2, h - n - 3), (w - n - 3, h - n - 3)):
        d.rounded_rectangle([cx, cy, cx + n, cy + n], radius=4, fill=c, outline=(40, 40, 44, 255))


def t_cab(logo=True):
    s = 256
    im = Image.new("RGBA", (s, s), (13, 13, 14, 255))
    d = ImageDraw.Draw(im)
    _cloth(d, [14, 14, s - 15, s - 15], (30, 30, 32, 255), (20, 20, 22, 255))
    for cx in (74, 182):
        for cy in (74, 182):
            d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], outline=(42, 42, 46, 255), width=3)
            d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], outline=(34, 34, 37, 255), width=2)
            d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(22, 22, 24, 255), outline=(40, 40, 44, 255))
    d.rectangle([9, 9, s - 10, s - 10], outline=(196, 196, 200, 255), width=2)       # white piping
    d.rectangle([12, 12, s - 13, s - 13], outline=(8, 8, 9, 255), width=2)
    _corners(d, s, s)
    if logo:
        _stencil(im, [48, 96, 208, 160])
    return arr(im)


def t_cab8():
    w, h = 128, 232
    im = Image.new("RGBA", (w, h), (13, 13, 14, 255))
    d = ImageDraw.Draw(im)
    _cloth(d, [8, 8, w - 9, h - 9], (70, 74, 82, 255), (54, 58, 66, 255))
    for i in range(4):
        for cx in (38, 90):
            cy = 36 + i * 53
            d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=(48, 51, 58, 255), width=2)
            d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(52, 56, 64, 255))
    d.rectangle([4, 4, w - 5, h - 5], outline=(160, 162, 168, 255), width=2)
    d.line([8, h // 2, w - 9, h // 2], fill=(20, 20, 22, 255), width=3)             # the bar across the baffle
    _corners(d, w, h, n=9)
    _stencil(im, [20, 12, 108, 50], 0.9)
    return arr(im)


def t_head(panel, knob, glow=(255, 96, 24), text=(20, 20, 22, 255)):
    w, h = 256, 96
    im = Image.new("RGBA", (w, h), (13, 13, 14, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([10, 9, w - 11, 46], fill=(8, 8, 9, 255))                           # behind the grille: the valves, lit
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for cx in (88, 112, 144, 168):
        gd.ellipse([cx - 9, 18, cx + 9, 52], fill=glow + (150,))
        gd.ellipse([cx - 3, 26, cx + 3, 46], fill=(255, 210, 140, 220))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(4)).crop((0, 0, w, h)))
    d = ImageDraw.Draw(im)
    d.rectangle([10, 47, w - 11, 52], fill=(13, 13, 14, 255))
    for x in range(12, w - 11, 5):                                                  # the steel grille
        d.line([x, 9, x, 46], fill=(64, 64, 68, 255))
    for y in range(12, 46, 5):
        d.line([10, y, w - 11, y], fill=(48, 48, 52, 255))
    d.rectangle([10, 9, w - 11, 46], outline=(90, 90, 96, 255))
    d.rectangle([10, 54, w - 11, 86], fill=panel)
    d.line([10, 54, w - 11, 54], fill=tuple(min(255, c + 40) for c in panel[:3]) + (255,))
    for i in range(10):
        cx = 34 + i * 17
        d.ellipse([cx - 6, 62, cx + 6, 74], fill=knob, outline=(6, 6, 6, 255))
        d.line([cx, 68, cx + (i % 3 - 1) * 3, 63], fill=(230, 230, 230, 255))
        d.line([cx - 5, 79, cx + 5, 79], fill=text)
    d.ellipse([16, 65, 22, 71], fill=(20, 20, 20, 255), outline=(140, 140, 146, 255))           # input
    d.rectangle([w - 46, 60, w - 34, 78], fill=(26, 26, 28, 255), outline=(6, 6, 6, 255))       # standby
    d.rectangle([w - 30, 60, w - 18, 78], fill=(230, 40, 28, 255), outline=(6, 6, 6, 255))      # mains, lit
    d.ellipse([w - 56, 66, w - 52, 70], fill=(60, 255, 80, 255))
    _corners(d, w, h, n=9)
    return arr(im)


def t_fusto(base, seed, lug=True):
    """Shell: sparkle lacquer with the chrome lugs; wraps once around the drum."""
    w, h = 256, 64
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3))
    a[:] = np.array(base, float)
    a *= 0.75 + 0.5 * np.sin(np.linspace(0, 4 * math.pi, w))[None, :, None] ** 2          # highlights round the shell
    sp = rng.random((h, w)) > 0.93
    a[sp] = np.minimum(255, a[sp] * 2.2 + 40)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    if lug:
        for i in range(8):
            x = 16 + i * 32
            d.rounded_rectangle([x - 4, 18, x + 4, 46], radius=3, fill=(196, 200, 208, 255), outline=(70, 72, 78, 255))
            d.line([x, 0, x, 18], fill=(170, 174, 182, 255), width=2)
            d.line([x, 46, x, h], fill=(170, 174, 182, 255), width=2)
            d.line([x - 2, 22, x - 2, 42], fill=(250, 250, 252, 255))
    return arr(im)


def t_radiale(stops):
    """For the triangle fans of discs: row 0 is the centre, the last row the rim."""
    w, h = 16, 64
    a = np.zeros((h, w, 4))
    a[..., 3] = 255
    for y in range(h):
        t = y / float(h - 1)
        for k in range(len(stops) - 1):
            (t0, c0), (t1, c1) = stops[k], stops[k + 1]
            if t0 <= t <= t1:
                f = (t - t0) / max(1e-6, t1 - t0)
                a[y, :, :3] = np.array(c0) * (1 - f) + np.array(c1) * f
    return a


def t_piatto():
    a = t_radiale([(0, (236, 206, 120)), (0.16, (214, 176, 84)), (0.2, (150, 116, 44)), (0.24, (206, 168, 78)), (1, (182, 142, 58))])
    for y in range(18, 64, 3):                                                     # the lathing
        a[y, :, :3] *= 0.86
    a[-2:, :, :3] *= 1.25
    return np.clip(a, 0, 255)


def t_kicklogo():
    s = 128
    im = Image.new("RGBA", (s, s), (12, 12, 14, 255))          # opaque: the square sits inside the head
    d = ImageDraw.Draw(im)
    if os.path.exists(LOGO):
        _stencil(im, [2, 26, s - 3, s - 27], 1.0)
    return arr(im)


def t_grille(w, h, horn=False):
    im = Image.new("RGBA", (w, h), (18, 18, 20, 255))
    d = ImageDraw.Draw(im)
    for y in range(4, h - 4, 3):
        for x in range(4 + (y // 3 % 2) * 2, w - 4, 4):
            d.point([x, y], fill=(52, 52, 56, 255))
    if horn:
        d.rectangle([w // 2 - 18, 6, w // 2 + 18, h - 7], fill=(10, 10, 11, 255), outline=(46, 46, 50, 255))
    d.rectangle([1, 1, w - 2, h - 2], outline=(60, 60, 64, 255))
    return arr(im)


def t_keys():
    w, h = 256, 64
    im = Image.new("RGBA", (w, h), (34, 36, 40, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([96, 5, 150, 24], fill=(120, 170, 190, 255), outline=(10, 10, 10, 255))      # the display
    for i in range(8):                                                                         # the sliders
        d.rectangle([22 + i * 8, 6, 24 + i * 8, 24], fill=(12, 12, 13, 255))
        d.rectangle([20 + i * 8, 10 + (i * 5) % 9, 26 + i * 8, 13 + (i * 5) % 9], fill=(190, 190, 195, 255))
    for i in range(16):                                                                        # the buttons
        d.rectangle([160 + (i % 8) * 10, 7 + (i // 8) * 10, 166 + (i % 8) * 10, 13 + (i // 8) * 10], fill=(70, 74, 82, 255))
    d.ellipse([8, 8, 16, 16], fill=(60, 62, 68, 255))
    d.rectangle([4, 30, w - 5, h - 4], fill=(236, 234, 226, 255))                             # 52 white keys
    n = 52
    kw = (w - 8) / float(n)
    for i in range(n + 1):
        x = 4 + i * kw
        d.line([x, 30, x, h - 4], fill=(120, 120, 118, 255))
    for i in range(n - 1):
        if (i % 7) in (1, 4):                                                                  # no black key after B and E (from A)
            continue
        x = 4 + (i + 1) * kw
        d.rectangle([x - 1.6, 30, x + 1.6, 48], fill=(14, 14, 16, 255))
    return arr(im)


def t_banner():
    """1024 x 512: the logo of the band if Ed has given the file, otherwise the name set in type on black."""
    w, h = 1024, 512
    im = Image.new("RGBA", (w, h), (8, 8, 10, 255))
    d = ImageDraw.Draw(im)
    if os.path.exists(LOGO):
        logo = Image.open(LOGO).convert("RGBA")
        r = min((w - 36) / float(logo.width), (h - 36) / float(logo.height))
        logo = logo.resize((int(logo.width * r), int(logo.height * r)), Image.LANCZOS)
        im.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2))
    else:
        f = ImageFont.truetype(FONT, 215)
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((w // 2, h // 2 - 10), "AZRAËL", font=f, fill=(190, 20, 24, 255), anchor="mm")
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(im)
        d.text((w // 2 + 4, h // 2 - 6), "AZRAËL", font=f, fill=(60, 8, 10, 255), anchor="mm")
        d.text((w // 2, h // 2 - 10), "AZRAËL", font=f, fill=(226, 226, 230, 255), anchor="mm")
    d.rectangle([8, 8, w - 9, h - 9], outline=(60, 120, 200, 255) if os.path.exists(LOGO) else (150, 18, 22, 255), width=4)
    for x in range(40, w, 118):                                                    # the eyelets
        for y in (22, h - 23):
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(150, 150, 156, 255))
    return arr(im)


def textures():
    pk = tex.Packer()
    ban = t_banner()
    for j in range(2):
        for i in range(4):
            pk.put("co_ban_%d_%d" % (i, j), ban[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256])
    pk.put("co_keys", t_keys())
    pk.put("co_cab", t_cab())
    pk.put("co_truss", t_truss())
    pk.put("co_cab8", t_cab8())
    pk.put("co_head_b", t_head((22, 24, 28, 255), (30, 30, 32, 255), glow=(255, 140, 40), text=(210, 210, 214, 255)))
    pk.put("co_head_s", t_head((34, 36, 40, 255), (16, 16, 18, 255), glow=(255, 40, 30), text=(200, 200, 206, 255)))
    pk.put("co_head_g", t_head((198, 162, 86, 255), (212, 176, 96, 255)))
    pk.put("co_pa", t_grille(128, 48, horn=True))
    pk.put("co_wedge", t_grille(128, 64))
    pk.put("co_nero", noisy(64, 64, (22, 22, 24), 1))
    pk.put("co_moquette", noisy(64, 64, (34, 34, 38), 2, 0.5))
    pk.put("co_alu", noisy(32, 32, (178, 182, 190), 3, 0.12))
    pk.put("co_cromo", noisy(32, 32, (150, 156, 166), 4, 0.3))
    pk.put("co_fusto", t_fusto((16, 44, 150), 5))
    pk.put("co_rullante", t_fusto((150, 156, 166), 9))
    pk.put("co_kicklogo", t_kicklogo())
    pk.put("co_testa", t_radiale([(0, (238, 236, 226)), (0.82, (232, 230, 220)), (0.9, (196, 194, 186)), (1, (214, 212, 204))]))
    pk.put("co_nera", t_radiale([(0, (12, 12, 14)), (0.9, (16, 16, 18)), (1, (40, 40, 44))]))
    pk.put("co_pelle", noisy(32, 32, (226, 222, 206), 6, 0.06))
    pk.put("co_piatto", t_piatto())
    for name, c in (("co_par_r", (255, 60, 40)), ("co_par_b", (60, 110, 255)), ("co_par_y", (255, 210, 90)), ("co_par_v", (190, 70, 255))):
        pk.put(name, noisy(16, 16, c, 8, 0.05))


# ------------------------------------------------------------------------------------ pieces
def truss(m, p0, p1, sec=0.4, seg=0.8):
    """Square box truss between two points (metres): four lattice sides, alpha tested, each drawn on both faces."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    d = (p1 - p0) / L
    a = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    b = np.cross(d, a)
    b /= np.linalg.norm(b)
    a = np.cross(b, d)
    n = max(1, int(round(L / seg)))
    for k in range(n):
        q0, q1 = p0 + d * (L * k / n), p0 + d * (L * (k + 1) / n)
        for u, v in ((a, b), (b, a), (-a, b), (-b, a)):
            o = u * sec / 2
            w = v * sec / 2
            pts = [(q0 + o + w) * M, (q1 + o + w) * M, (q1 + o - w) * M, (q0 + o - w) * M]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
            m.face(pts, "co_truss", uv=uv, blend=1)                 # both windings: seen from outside and through the lattice
            m.face(pts[::-1], "co_truss", uv=uv[::-1], blend=1)


def front(m, cx, y0, w, h, z, region):
    """A textured rectangle facing the audience (-z), read the right way round from the cavea."""
    rectf(m, V(cx - w / 2, y0, z), V(1, 0, 0), UP, w, h, region, V(0, 0, -1), tile=None)


def torre():
    m = G.box(0.9, 0.06, 0.9, "co_alu", center=(0, 0, 0))
    truss(m, (0, 0.06, 0), (0, 6.0, 0))
    return m, ((-140.0, 0.0, -140.0), (140.0, 3072.0, 140.0))


def tetto():
    m = G.Mesh()
    y = 5.8
    for z in (-4.5, 0.0, 4.5):
        truss(m, (-7.5, y, z), (7.5, y, z))
    for x in (-7.5, 7.5):
        truss(m, (x, y, -4.5), (x, y, 4.5))
    cols = ["co_par_r", "co_par_b", "co_par_y", "co_par_v"]
    k = 0
    for z in (-4.5, 0.0):                                                          # the lamps, under the front and middle truss
        for i in range(10):
            x = -6.3 + i * 1.4
            m.merge(G.box(0.26, 0.3, 0.3, "co_nero", center=(x, y - 0.56, z)))
            front(m, x, y - 0.53, 0.22, 0.24, z - 0.152, cols[k % 4])
            m.merge(G.box(0.03, 0.08, 0.03, "co_nero", center=(x, y - 0.27, z)))
            k += 1
    return m, None


def cab(m, x, y, z, w=0.76, h=0.76, d=0.36):
    m.merge(G.box(w, h, d, "co_nero", center=(x, y, z)))
    front(m, x, y, w, h, z - d / 2 - 0.004, "co_cab")


def stack(head):
    m = G.Mesh()
    cab(m, 0, 0, 0)
    cab(m, 0, 0.76, 0)
    m.merge(G.box(0.72, 0.28, 0.26, "co_nero", center=(0, 1.52, 0)))
    front(m, 0, 1.52, 0.72, 0.28, -0.134, head)
    m.merge(G.box(0.2, 0.03, 0.04, "co_nero", center=(0, 1.80, 0)))                # the handle
    lo, hi = m.bbox()
    return m, ((lo[0], 0.0, lo[2]), (hi[0], hi[1], hi[2]))


def stack_basso():
    m = G.box(0.66, 1.22, 0.41, "co_nero", center=(0, 0, 0))
    front(m, 0, 0, 0.66, 1.22, -0.209, "co_cab8")
    m.merge(G.box(0.61, 0.29, 0.33, "co_nero", center=(0, 1.22, 0)))
    front(m, 0, 1.22, 0.61, 0.29, -0.169, "co_head_b")
    lo, hi = m.bbox()
    return m, ((lo[0], 0.0, lo[2]), (hi[0], hi[1], hi[2]))


def disco(*args, **kw):
    """G.disc drawn on both faces (heads and cymbals are seen from above and from below)."""
    m = G.disc(*args, **kw)
    m.f = [(idx, px, page, blend, False) for idx, px, page, blend, dbl in m.f]
    m.f += [(idx[::-1], px[::-1], page, blend, False) for idx, px, page, blend, dbl in m.f]
    return m


def tamburo(r, depth, pos=(0, 0, 0), rx=0.0, shell="co_fusto", logo=False, n=16):
    """A drum along +y in its own frame (batter head on top), then tilted by rx and moved (metres)."""
    m = G.cylinder(r, r, depth, shell, n=n, top_cap=False)
    for y in (0.0, depth - 0.028):                                                 # the hoops
        m.merge(G.cylinder(r + 0.012, r + 0.012, 0.028, "co_cromo", n=n, base=(0, y, 0), top_cap=False))
    m.merge(disco(r + 0.004, "co_nera" if logo else "co_testa", center=(0, depth + 0.002, 0), n=n))
    m.merge(disco(r + 0.004, "co_testa", center=(0, -0.002, 0), n=n))
    if logo:
        q = r * 0.69
        rectf(m, V(-q, depth + 0.006, -q), V(1, 0, 0), V(0, 0, 1), 2 * q, 2 * q, "co_kicklogo", V(0, 1, 0), tile=None)
    return m.transformed(rx=rx, t=(pos[0] * M, pos[1] * M, pos[2] * M))


def treppiede(m, x, z, y0, y1, r=0.013, spread=0.3):
    m.merge(G.cylinder(r + 0.004, r + 0.004, min(0.55, y1 - y0), "co_cromo", n=6, base=(x, y0 + 0.02, z), top_cap=False))
    m.merge(G.cylinder(r, r, y1 - y0, "co_cromo", n=6, base=(x, y0, z), top_cap=False))
    for a in (0.5, 2.6, 4.7):
        m.merge(G.tube([(x, y0 + 0.34, z), (x + math.cos(a) * spread, y0 + 0.015, z + math.sin(a) * spread)], [0.011, 0.011], "co_cromo", n=4))
        m.merge(G.tube([(x, y0 + 0.12, z), (x + math.cos(a) * spread * 0.55, y0 + 0.16, z + math.sin(a) * spread * 0.55)], [0.007, 0.007], "co_cromo", n=4))


def piatto(m, r, c, tilt=0.0, ry=0.0, china=False):
    """A cymbal: bow and bell, the felt and the wing nut."""
    cone = -0.035 if china else 0.035
    m.merge(disco(r, "co_piatto", center=c, n=18, cone=cone, tilt=tilt, ry=ry))
    m.merge(G.cylinder(0.014, 0.01, 0.04, "co_nero", n=5, base=(c[0], c[1] + (0.0 if china else 0.03), c[2])))


def asta_piatto(m, base, r, c, h, tilt=0.0, ry=0.0, china=False):
    """Boom stand: tripod at base (x, z) on the riser, the boom up to the cymbal at c."""
    top = (base[0], c[1] - 0.22, base[1])
    treppiede(m, base[0], base[1], h, top[1])
    m.merge(G.tube([top, (c[0], c[1] - 0.01, c[2])], [0.009, 0.009], "co_cromo", n=5))
    m.merge(G.box(0.045, 0.045, 0.045, "co_nero", center=(top[0], top[1] - 0.02, top[2])))
    piatto(m, r, c, tilt, ry, china)


def pedale(m, x, z, h):
    m.merge(G.box(0.11, 0.02, 0.32, "co_cromo", center=(x, h, z)))
    m.merge(G.box(0.09, 0.012, 0.26, "co_nero", center=(x, h + 0.02, z)).transformed(rx=0.0))
    for dx in (-0.06, 0.06):
        m.merge(G.cylinder(0.008, 0.008, 0.2, "co_cromo", n=4, base=(x + dx, h, z - 0.15), top_cap=False))
    m.merge(G.tube([(x, h + 0.2, z - 0.15), (x, h + 0.33, z - 0.21)], [0.006, 0.006], "co_cromo", n=4))
    m.merge(G.cylinder(0.022, 0.022, 0.05, "co_testa", n=6, base=(x, h + 0.31, z - 0.22)))


def batteria():
    """Double bass drum kit on its riser: the audience at -z, the drummer on the throne at +z."""
    h = 0.4
    m = G.box(3.0, h, 2.4, "co_nero", top="co_moquette", center=(0, 0, 0))
    m.merge(G.box(3.04, 0.04, 2.44, "co_alu", center=(0, h - 0.06, 0)))
    m.merge(G.box(3.04, 0.03, 2.44, "co_alu", center=(0, 0.0, 0)))
    kr, kd = 0.28, 0.46
    for x in (-0.43, 0.43):                                                        # the two bass drums
        m.merge(tamburo(kr, kd, (x, h + kr + 0.03, -0.2), rx=-math.pi / 2, logo=True, n=18))
        for sx in (-1, 1):                                                         # the spurs
            m.merge(G.tube([(x + sx * 0.2, h + 0.2, -0.58), (x + sx * 0.36, h + 0.01, -0.68)], [0.009, 0.009], "co_cromo", n=4))
        pedale(m, x, 0.02, h)
    # rack toms on a stand between the bass drums, tilted to the drummer
    ty = h + 0.82
    m.merge(tamburo(0.13, 0.2, (-0.22, ty, -0.34), rx=0.42))
    m.merge(tamburo(0.155, 0.23, (0.2, ty - 0.02, -0.36), rx=0.42))
    treppiede(m, 0.0, -0.3, h, ty + 0.02, r=0.016, spread=0.24)
    for x in (-0.14, 0.12):
        m.merge(G.tube([(0, ty, -0.3), (x, ty + 0.06, -0.3)], [0.009, 0.009], "co_cromo", n=4))
    # floor toms on their legs
    for x, z, r, d in ((0.86, 0.3, 0.205, 0.4), (1.16, -0.16, 0.18, 0.36)):
        m.merge(tamburo(r, d, (x, h + 0.26, z)))
        for a in (0.3, 2.4, 4.5):
            m.merge(G.cylinder(0.008, 0.008, 0.52, "co_cromo", n=4, base=(x + math.cos(a) * (r + 0.02), h, z + math.sin(a) * (r + 0.02)), top_cap=False))
    # snare on its stand
    m.merge(tamburo(0.178, 0.14, (-0.36, h + 0.56, 0.28), rx=0.08, shell="co_rullante"))
    treppiede(m, -0.36, 0.28, h, h + 0.55, spread=0.24)
    # hi-hat
    treppiede(m, -0.86, 0.2, h, h + 0.98, spread=0.26)
    piatto(m, 0.178, (-0.86, h + 0.9, 0.2))
    m.merge(disco(0.178, "co_piatto", center=(-0.86, h + 0.885, 0.2), n=18, cone=-0.03))
    m.merge(G.box(0.09, 0.02, 0.26, "co_cromo", center=(-0.86, h, 0.42)))
    # cymbals: two crashes, a splash, the ride and a china
    asta_piatto(m, (-0.98, -0.62), 0.23, (-0.78, h + 1.38, -0.5), h, tilt=0.22, ry=0.4)
    asta_piatto(m, (0.92, -0.72), 0.24, (0.66, h + 1.44, -0.56), h, tilt=0.22, ry=-0.5)
    asta_piatto(m, (0.0, -0.86), 0.13, (0.0, h + 1.2, -0.62), h, tilt=0.3)
    asta_piatto(m, (1.26, 0.34), 0.27, (0.72, h + 1.02, 0.02), h, tilt=0.3, ry=-0.9)
    asta_piatto(m, (1.3, -0.62), 0.23, (1.24, h + 1.5, -0.3), h, tilt=0.35, ry=-1.2, china=True)
    # the throne
    m.merge(G.cylinder(0.028, 0.028, 0.46, "co_cromo", n=6, base=(0, h, 0.72), top_cap=False))
    m.merge(G.cylinder(0.18, 0.17, 0.1, "co_nero", n=14, base=(0, h + 0.46, 0.72), cap="co_moquette"))
    for a in (0.5, 2.6, 4.7):
        m.merge(G.tube([(0, h + 0.24, 0.72), (math.cos(a) * 0.27, h + 0.012, 0.72 + math.sin(a) * 0.27)], [0.012, 0.012], "co_cromo", n=4))
    return m, ((-1.5 * M, 0.0, -1.2 * M), (1.5 * M, 1.6 * M, 1.2 * M))


def tastiera():
    m = G.Mesh()
    w, d, y = 1.46, 0.4, 0.92
    for x in (-0.38, 0.38):                                                        # the X stand
        m.merge(G.tube([(x, 0.02, -0.3), (x, y, 0.22)], [0.016, 0.016], "co_nero", n=4))
        m.merge(G.tube([(x, 0.02, 0.3), (x, y, -0.22)], [0.016, 0.016], "co_nero", n=4))
    for z in (-0.3, 0.3):
        m.merge(G.tube([(-0.42, 0.02, z), (0.42, 0.02, z)], [0.018, 0.018], "co_nero", n=4))
    m.merge(G.box(w, 0.11, d, "co_nero", center=(0, y, 0)))
    # the top: the keys on the side of the player, who stands at +z and looks at the audience
    rectf(m, V(w / 2, y + 0.113, d / 2), V(-1, 0, 0), V(0, 0, -1), w, d, "co_keys", V(0, 1, 0), tile=None)
    return m, ((-w / 2 * M, 0.0, -0.3 * M), (w / 2 * M, (y + 0.12) * M, 0.3 * M))


def asta():
    m = G.Mesh()
    for a in (0.5, 2.6, 4.7):
        m.merge(G.tube([(0, 0.3, 0), (math.cos(a) * 0.33, 0.01, math.sin(a) * 0.33)], [0.011, 0.011], "co_nero", n=4))
    m.merge(G.cylinder(0.013, 0.013, 1.42, "co_cromo", n=5, base=(0, 0.02, 0), top_cap=False))
    m.merge(G.tube([(0, 1.36, -0.22), (0, 1.5, 0.3), (0, 1.56, 0.52)], [0.009, 0.009, 0.009], "co_cromo", n=4))
    m.merge(G.box(0.05, 0.05, 0.05, "co_nero", center=(0, 1.415, 0)))                             # the clamp
    m.merge(G.tube([(0, 1.555, 0.5), (0, 1.585, 0.63)], [0.017, 0.021], "co_nero", n=6))          # the microphone
    m.merge(G.ellipsoid(0.03, 0.03, 0.03, "co_cromo", n=6, rings=4, center=(0, 1.59, 0.655)))
    return m, None


def wedge():
    m = G.Mesh()
    hw = 0.3
    A, B, C, D, E = (-0.22, 0.0), (0.24, 0.0), (0.24, 0.1), (-0.04, 0.36), (-0.22, 0.36)     # (z, y) profile
    def P(x, q):
        return V(x, q[1], q[0])
    fface(m, [P(hw, C), P(-hw, C), P(-hw, D), P(hw, D)], "co_wedge", V(0, 0.73, 0.68))        # the grille, to the player
    fface(m, [P(-hw, A), P(hw, A), P(hw, E), P(-hw, E)], "co_nero", V(0, 0, -1))
    fface(m, [P(-hw, E), P(hw, E), P(hw, D), P(-hw, D)], "co_nero", V(0, 1, 0))
    fface(m, [P(-hw, B), P(hw, B), P(hw, C), P(-hw, C)], "co_nero", V(0, 0, 1))
    for x, n in ((hw, V(1, 0, 0)), (-hw, V(-1, 0, 0))):
        fface(m, [P(x, A), P(x, B), P(x, C), P(x, D)], "co_nero", n)
        fface(m, [P(x, A), P(x, D), P(x, E)], "co_nero", n)
    return m, None


def stendardo():
    m = G.Mesh()
    tw, th = BAN_W / 4, BAN_H / 2
    for j in range(2):
        for i in range(4):
            o = V(-BAN_W / 2 + i * tw, BAN_H - (j + 1) * th, 0)
            rectf(m, o, V(1, 0, 0), UP, tw, th, "co_ban_%d_%d" % (i, j), V(0, 0, -1), tile=None)
    rectf(m, V(BAN_W / 2, 0, 0.02), V(-1, 0, 0), UP, BAN_W, BAN_H, "co_nero", V(0, 0, 1), tile=None)      # the back
    m.merge(G.tube([(-BAN_W / 2 - 0.1, BAN_H + 0.03, 0), (BAN_W / 2 + 0.1, BAN_H + 0.03, 0)], [0.03, 0.03], "co_alu", n=5))
    m.merge(G.tube([(-BAN_W / 2 - 0.1, -0.03, 0), (BAN_W / 2 + 0.1, -0.03, 0)], [0.03, 0.03], "co_alu", n=5))
    return m, None


def line_array():
    m = G.Mesh()
    m.merge(G.box(1.0, 0.1, 0.5, "co_alu", center=(0, -0.1, 0)))                   # the bumper
    y, z, ang = -0.1, 0.0, 0.0
    for i in range(6):
        e = G.box(1.1, 0.36, 0.5, "co_nero", center=(0, -0.36, 0), bottom=True)
        front(e, 0, -0.36, 1.1, 0.36, -0.254, "co_pa")
        ang += math.radians(2 + i * 1.5)
        m.merge(e.transformed(rx=ang, t=(0, y * M, z * M)))
        y -= 0.37 * math.cos(ang)
        z += 0.37 * math.sin(ang)
    for x in (-0.3, 0.3):                                                          # the chains to the truss
        m.merge(G.cylinder(0.012, 0.012, 0.5, "co_cromo", n=4, base=(x, 0, 0), top_cap=False))
    return m, None


MODELS = [(460, "TORRE_AMERICANA", torre), (461, "TETTO_AMERICANE", tetto), (462, "BATTERIA", batteria),
          (463, "STACK_SINISTRO", lambda: stack("co_head_s")), (464, "STACK_DESTRO", lambda: stack("co_head_g")),
          (465, "TASTIERA", tastiera), (466, "ASTA_MICROFONO", asta), (467, "WEDGE", wedge), (468, "STENDARDO", stendardo),
          (469, "LINE_ARRAY", line_array), (470, "STACK_BASSO", stack_basso)]


def main():
    textures()
    statics = []
    for sid, name, fn in MODELS:
        mesh, coll = fn()
        lo, hi = mesh.bbox()
        print(sid, name, len(mesh.f), "faces", [int(v) for v in lo], [int(v) for v in hi])
        statics.append((sid, name, mesh, coll))
    W.write(OUT, tex.pages, statics, notes="Coda di Volpe - Tindari: il palco del concerto degli Azrael nell'arena (statici 460-469)")
    print(OUT, os.path.getsize(OUT), len(tex.pages), "pages", "logo:", os.path.exists(LOGO))


if __name__ == "__main__":
    main()
