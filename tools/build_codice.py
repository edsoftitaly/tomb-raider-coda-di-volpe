"""CdV_Codice.wad2: the code of the gate of the courtyard in the prologue (Ed, 14/11/2026).

 455 COMPUTER_LAB          desk with the computer of the workshop, the screen (towards +x) reads 33 2D 32 2D 35
 457 COMPUTER_LAB_SPENTO   the same with the screen off, for the dark twin of the room
 456 NUMERI_INTERRUTTORI   five enamel plates 1-5 on a wall facing +z, over the five small switches (pitch 720 units),
                           1 on the viewer's left
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from decor import geom as G
from decor import tex
from decor import wad2 as W
from decor.santuario_models import UP, V, rectf

M = G.M
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "wads", "CdV_Codice.wad2")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
CODE = "33 2D 32 2D 35"
PITCH = 720.0 / M


def arr(im):
    return np.asarray(im.convert("RGBA"), dtype=np.float64).copy()


def noisy(w, h, color, seed, amount=0.2):
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 4))
    a[..., :3] = np.clip(np.array(color, float)[None, None] * (1 + (rng.random((h, w, 1)) - 0.5) * amount), 0, 255)
    a[..., 3] = 255
    return a


def t_screen(on):
    w, h = 256, 192
    im = Image.new("RGBA", (w, h), (4, 14, 8, 255) if on else (16, 20, 18, 255))
    d = ImageDraw.Draw(im)
    if on:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        small, big = ImageFont.truetype(MONO, 15), ImageFont.truetype(MONO, 27)
        for dr in (gd, None):
            t = dr or d
            t.text((14, 16), "C:\\CANCELLO>", font=small, fill=(60, 220, 110, 255))
            t.text((w // 2, 96), CODE, font=big, fill=(120, 255, 160, 255), anchor="mm")
            t.rectangle([14, 150, 26, 166], fill=(60, 220, 110, 255))
            if dr is not None:
                im.alpha_composite(g.filter(ImageFilter.GaussianBlur(3)))
                d = ImageDraw.Draw(im)
        for y in range(0, h, 3):                                       # scan lines
            d.line([0, y, w, y], fill=(0, 0, 0, 70))
    else:
        d.ellipse([40, 20, 150, 90], fill=(26, 32, 29, 255))           # a dull reflection
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, outline=(150, 146, 132, 255), width=6)
    return arr(im)


def t_number(n):
    s = 64
    im = Image.new("RGBA", (s, s), (226, 224, 214, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, s - 3, s - 3], outline=(30, 40, 90, 255), width=3)
    d.text((s // 2, s // 2 + 1), str(n), font=ImageFont.truetype(MONO, 44), fill=(24, 34, 84, 255), anchor="mm")
    for x, y in ((7, 7), (s - 8, 7), (7, s - 8), (s - 8, s - 8)):
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(110, 110, 112, 255))
    return arr(im)


def t_keys():
    w, h = 128, 48
    im = Image.new("RGBA", (w, h), (196, 190, 172, 255))
    d = ImageDraw.Draw(im)
    for r in range(4):
        for c in range(15):
            d.rectangle([6 + c * 8, 6 + r * 9, 12 + c * 8, 13 + r * 9], fill=(226, 222, 208, 255), outline=(120, 116, 104, 255))
    return arr(im)


def textures():
    pk = tex.Packer()
    pk.put("cd_schermo", t_screen(True))
    pk.put("cd_spento", t_screen(False))
    pk.put("cd_tasti", t_keys())
    for n in range(1, 6):
        pk.put("cd_n%d" % n, t_number(n))
    pk.put("cd_beige", noisy(64, 64, (198, 192, 174), 1, 0.08))
    pk.put("cd_legno", noisy(64, 64, (112, 78, 46), 2, 0.3))
    pk.put("cd_ferro", noisy(32, 32, (74, 76, 80), 3, 0.2))
    pk.put("cd_scuro", noisy(32, 32, (40, 40, 42), 4, 0.2))


def computer(screen):
    m = G.Mesh()
    top = 0.76
    m.merge(G.box(0.62, 0.04, 1.3, "cd_legno", center=(0, top - 0.04, 0)))
    for x in (-0.27, 0.27):
        for z in (-0.6, 0.6):
            m.merge(G.box(0.05, top - 0.04, 0.05, "cd_ferro", center=(x, 0, z)))
    m.merge(G.box(0.03, 0.45, 1.2, "cd_legno", center=(-0.28, 0.2, 0)))                 # the back panel
    m.merge(G.box(0.42, 0.11, 0.44, "cd_beige", center=(-0.06, top, 0.1)))              # the case, lying flat
    m.merge(G.box(0.004, 0.02, 0.14, "cd_scuro", center=(0.151, top + 0.05, 0.2)))      # the floppy slot
    m.merge(G.box(0.40, 0.36, 0.42, "cd_beige", center=(-0.07, top + 0.13, 0.1)))       # the monitor
    m.merge(G.box(0.14, 0.02, 0.2, "cd_beige", center=(-0.07, top + 0.11, 0.1)))
    x = -0.07 + 0.2 + 0.003
    rectf(m, V(x, top + 0.16, 0.1 - 0.18), V(0, 0, 1), UP, 0.36, 0.29, screen, V(1, 0, 0), tile=None)
    m.merge(G.box(0.17, 0.025, 0.44, "cd_beige", top="cd_tasti", center=(0.2, top, 0.1)))   # the keyboard
    m.merge(G.box(0.09, 0.03, 0.06, "cd_beige", center=(0.2, top, 0.42)))               # the mouse
    for i, (dx, dz) in enumerate(((0.0, -0.42), (0.12, -0.5), (-0.1, -0.5))):           # papers and manuals
        m.merge(G.box(0.22, 0.03 + 0.02 * i, 0.3, "cd_beige" if i else "cd_scuro", center=(dx, top, dz)))
    lo, hi = m.bbox()
    return m, ((lo[0], 0.0, lo[2]), (hi[0], top * M, hi[2]))


def numeri():
    m = G.Mesh()
    for n in range(1, 6):
        cx = (n - 3) * PITCH * -1.0                      # the viewer looks at -z: his left is +x, so 1 is at +x
        rectf(m, V(cx + 0.15, 2.0, 0.012), V(-1, 0, 0), UP, 0.3, 0.3, "cd_n%d" % n, V(0, 0, 1), tile=None)
        m.merge(G.box(0.03, 0.42, 0.02, "cd_ferro", center=(cx, 2.3, 0.012)))          # the conduit down to the switch
    m.merge(G.box(7.9, 0.04, 0.03, "cd_ferro", center=(1.1, 2.72, 0.016)))     # and along the wall to the gate
    return m, None


def main():
    textures()
    statics = []
    for sid, name, fn in ((455, "COMPUTER_LAB", lambda: computer("cd_schermo")), (456, "NUMERI_INTERRUTTORI", numeri),
                          (457, "COMPUTER_LAB_SPENTO", lambda: computer("cd_spento"))):
        mesh, coll = fn()
        lo, hi = mesh.bbox()
        print(sid, name, len(mesh.f), [int(v) for v in lo], [int(v) for v in hi])
        statics.append((sid, name, mesh, coll))
    W.write(OUT, tex.pages, statics, notes="Coda di Volpe - prologo: computer del laboratorio con il codice del cancello (455, 457), numeri degli interruttori (456)")
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
