"""CdV_Codice.wad2: the code of the gate of the courtyard in the prologue (Ed, 14/11/2026).

 455 COMPUTER_LAB          desk with the computer of the workshop, the screen (towards +x) reads 33 2D 32 2D 35
 457 COMPUTER_LAB_SPENTO   the same with the screen off, for the dark twin of the room
 458 CATENA_BOTOLA         the chain from the trapdoor of the box room down a wall at +z (3.5 m to 1.42 m)
 459 LUCCHETTO_BOTOLA      its padlock, a static of its own so that the script can let it fall
 449 CATENA_A_TERRA        the chain in a heap on the floor
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


def _screen(d_im, box, on):
    """The tube: green phosphor with the code, or off."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGBA", (w, h), (3, 16, 8, 255) if on else (17, 22, 19, 255))
    d = ImageDraw.Draw(im)
    if on:
        small, big = ImageFont.truetype(MONO, 11), ImageFont.truetype(MONO, 22)

        def write(t):
            t.text((8, 8), "A>TYPE CANCELLO.DAT", font=small, fill=(70, 230, 120, 255))
            t.text((w // 2, h // 2 + 2), CODE, font=big, fill=(150, 255, 180, 255), anchor="mm")
            t.text((8, h - 34), "A>", font=small, fill=(70, 230, 120, 255))
            t.rectangle([24, h - 33, 31, h - 22], fill=(70, 230, 120, 255))
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        write(ImageDraw.Draw(g))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(2.5)))
        d = ImageDraw.Draw(im)
        write(d)
        for y in range(0, h, 2):
            d.line([0, y, w, y], fill=(0, 0, 0, 60))
    else:
        d.ellipse([w // 6, h // 8, w // 2, h // 2], fill=(27, 34, 30, 255))
    d_im.paste(im, (x0, y0))


PLA, PLA_D, PLA_L, DARK = (188, 184, 170, 255), (150, 146, 134, 255), (212, 208, 196, 255), (38, 38, 40, 255)


def t_monitor(on):
    w, h = 256, 208
    im = Image.new("RGBA", (w, h), PLA)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=PLA_D, width=2)
    d.rounded_rectangle([20, 16, w - 21, h - 40], radius=10, fill=(22, 22, 23, 255), outline=PLA_D, width=3)     # the recess
    _screen(im, [30, 24, w - 30, h - 48], on)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([29, 23, w - 30, h - 48], radius=12, outline=(12, 12, 12, 255), width=3)
    for i, x in enumerate((176, 196, 216)):                                                                     # contrast, brightness, mains
        d.ellipse([x - 6, h - 30, x + 6, h - 18], fill=PLA_L, outline=PLA_D)
        d.line([x, h - 24, x + (i - 1) * 3, h - 29], fill=(60, 60, 60, 255))
    d.ellipse([22, h - 27, 28, h - 21], fill=(60, 230, 90, 255) if on else (40, 60, 44, 255))
    for x in range(40, 150, 6):                                                                                 # the loudspeaker slots
        d.line([x, h - 28, x, h - 20], fill=PLA_D)
    return arr(im)


def t_case():
    w, h = 256, 80
    im = Image.new("RGBA", (w, h), PLA)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=PLA_D, width=2)
    d.rectangle([8, 8, 118, h - 9], fill=DARK)                                                                  # two 5.25 inch drives, side by side
    d.line([63, 8, 63, h - 9], fill=(70, 70, 74, 255), width=2)
    for x0 in (12, 68):
        d.rectangle([x0, 34, x0 + 46, 38], fill=(8, 8, 9, 255))                                                 # the slot
        d.rectangle([x0 + 18, 28, x0 + 30, 44], fill=(58, 58, 62, 255), outline=(12, 12, 12, 255))              # the latch
        d.ellipse([x0 + 2, 54, x0 + 7, 59], fill=(210, 40, 30, 255))
    for y in range(14, h - 12, 5):                                                                              # the air intake
        d.line([130, y, 206, y], fill=PLA_D, width=2)
    d.rectangle([216, 14, 244, 30], fill=(206, 60, 40, 255), outline=(90, 30, 20, 255))                         # mains switch
    d.rectangle([216, 30, 244, 32], fill=(120, 30, 20, 255))
    d.ellipse([226, 44, 234, 52], fill=(60, 230, 90, 255))
    d.rectangle([214, 60, 246, 66], fill=(200, 202, 206, 255), outline=PLA_D)                                   # a blank nameplate
    return arr(im)


def t_keyboard():
    w, h = 256, 96
    im = Image.new("RGBA", (w, h), PLA)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=PLA_D, width=2)
    d.rectangle([6, 6, w - 7, 16], fill=(96, 100, 110, 255))                                                    # the strip of function keys
    for c in range(12):
        d.rectangle([10 + c * 17, 8, 23 + c * 17, 14], fill=PLA_L, outline=(70, 72, 80, 255))
    keyw = 13
    for r in range(5):
        y = 22 + r * 14
        n = 14 if r < 4 else 0
        for c in range(n):
            x = 8 + r * 3 + c * keyw
            col = (214, 150, 60, 255) if (r, c) == (2, 0) else PLA_L
            d.rectangle([x, y, x + keyw - 2, y + 11], fill=col, outline=PLA_D)
            d.line([x + 2, y + 2, x + keyw - 4, y + 2], fill=(236, 233, 224, 255))
        if r == 4:
            d.rectangle([44, y, 150, y + 11], fill=PLA_L, outline=PLA_D)                                        # the space bar
            for c in (0, 1, 2, 12, 13):
                x = 8 + c * keyw
                d.rectangle([x, y, x + keyw - 2, y + 11], fill=PLA_L, outline=PLA_D)
    for r in range(5):                                                                                          # the numeric pad
        for c in range(4):
            x, y = 200 + c * 13, 22 + r * 14
            d.rectangle([x, y, x + 11, y + 11], fill=PLA_L, outline=PLA_D)
    return arr(im)


def t_vents():
    w, h = 64, 64
    im = Image.new("RGBA", (w, h), PLA)
    d = ImageDraw.Draw(im)
    for y in range(10, 40, 5):
        d.line([8, y, w - 9, y], fill=PLA_D, width=2)
    return arr(im)


def t_chain():
    w, h = 32, 64
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y0 in (0, 32):
        d.rounded_rectangle([9, y0 + 1, 22, y0 + 22], radius=6, outline=(120, 124, 130, 255), width=4)      # a link, face on
        d.rounded_rectangle([10, y0 + 2, 21, y0 + 21], radius=6, outline=(190, 194, 200, 255), width=1)
        d.rectangle([14, y0 + 18, 17, y0 + 36], fill=(100, 104, 110, 255))                                   # the next one, edge on
        d.line([15, y0 + 18, 15, y0 + 36], fill=(170, 174, 180, 255))
    return arr(im)


def t_padlock():
    w, h = 64, 64
    im = Image.new("RGBA", (w, h), (176, 138, 60, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(110, 84, 34, 255), width=3)
    d.rectangle([4, 4, w - 5, 10], fill=(214, 180, 96, 255))
    d.ellipse([26, 24, 38, 36], fill=(40, 34, 24, 255))
    d.rectangle([30, 32, 34, 48], fill=(40, 34, 24, 255))
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


def textures():
    pk = tex.Packer()
    pk.put("cd_schermo", t_monitor(True))
    pk.put("cd_spento", t_monitor(False))
    pk.put("cd_tasti", t_keyboard())
    pk.put("cd_case", t_case())
    pk.put("cd_griglie", t_vents())
    pk.put("cd_catena", t_chain())
    pk.put("cd_lucchetto", t_padlock())
    for n in range(1, 6):
        pk.put("cd_n%d" % n, t_number(n))
    pk.put("cd_beige", noisy(64, 64, PLA[:3], 1, 0.05))
    pk.put("cd_cavo", noisy(16, 16, (120, 118, 110), 5, 0.2))
    pk.put("cd_carta", noisy(32, 32, (232, 230, 220), 6, 0.05))
    pk.put("cd_legno", noisy(64, 64, (112, 78, 46), 2, 0.3))
    pk.put("cd_ferro", noisy(32, 32, (74, 76, 80), 3, 0.2))
    pk.put("cd_scuro", noisy(32, 32, (40, 40, 42), 4, 0.2))


def computer(screen):
    """A mid-Eighties office PC of our own design on its desk: the front towards +x (the viewer's right is +z)."""
    import math
    m = G.Mesh()
    top = 0.76
    m.merge(G.box(0.76, 0.04, 1.4, "cd_legno", center=(0, top - 0.04, 0)))
    for x in (-0.34, 0.34):
        for z in (-0.65, 0.65):
            m.merge(G.box(0.05, top - 0.04, 0.05, "cd_ferro", center=(x, 0, z)))
    m.merge(G.box(0.03, 0.45, 1.3, "cd_legno", center=(-0.35, 0.2, 0)))                 # the back panel
    m.merge(G.box(0.5, 0.5, 0.42, "cd_legno", center=(-0.1, 0.2, -0.46)))               # the drawers
    for y in (0.24, 0.42, 0.6):
        m.merge(G.box(0.012, 0.02, 0.14, "cd_ferro", center=(0.156, y, -0.46)))
    zc = 0.18
    # the system unit
    cw, ch, cd_, cx = 0.50, 0.15, 0.40, -0.14
    m.merge(G.box(cd_, ch, cw, "cd_beige", top="cd_griglie", center=(cx, top, zc)))
    fx = cx + cd_ / 2 + 0.003
    rectf(m, V(fx, top, zc - cw / 2), V(0, 0, 1), UP, cw, ch, "cd_case", V(1, 0, 0), tile=None)
    # the monitor on its swivel foot
    my = top + ch
    m.merge(G.cylinder(0.14, 0.12, 0.03, "cd_beige", n=14, base=(cx + 0.02, my, zc)))
    m.merge(G.cylinder(0.08, 0.08, 0.035, "cd_beige", n=10, base=(cx + 0.02, my + 0.03, zc)))
    by = my + 0.065
    mw, mh = 0.40, 0.325
    m.merge(G.box(0.13, mh, mw, "cd_beige", center=(cx + 0.125, by, zc)))               # the front frame
    m.merge(G.box(0.24, mh - 0.07, mw - 0.08, "cd_beige", top="cd_griglie", center=(cx - 0.06, by + 0.035, zc)))    # the back of the tube
    rectf(m, V(cx + 0.19 + 0.003, by, zc - mw / 2), V(0, 0, 1), UP, mw, mh, screen, V(1, 0, 0), tile=None)
    # the keyboard, its coiled lead back to the unit
    kx, kw, kd = 0.24, 0.47, 0.18
    m.merge(G.box(kd, 0.022, kw, "cd_beige", center=(kx, top, zc)))
    rectf(m, V(kx + kd / 2, top + 0.024, zc - kw / 2), V(0, 0, 1), V(-1, 0, 0), kw, kd, "cd_tasti", V(0, 1, 0), tile=None)
    pts = [(kx - kd / 2, top + 0.012, zc + 0.2)]
    for i in range(1, 14):
        t = i / 14.0
        pts.append((kx - kd / 2 - 0.02 - 0.012 * (i % 2), top + 0.012 + 0.012 * ((i + 1) % 2), zc + 0.2 + 0.11 * t))
    pts.append((fx, top + 0.03, zc + 0.3))
    m.merge(G.tube(pts, [0.006] * len(pts), "cd_cavo", n=4))
    # what a workshop leaves on a desk: a box of floppies, listings, a pen
    m.merge(G.box(0.16, 0.06, 0.2, "cd_scuro", center=(0.05, top, -0.42)))
    m.merge(G.box(0.14, 0.004, 0.14, "cd_scuro", center=(0.2, top, -0.2)).transformed(ry=0.3, t=(0, 0, 0)))
    for i in range(3):
        m.merge(G.box(0.3, 0.004, 0.22, "cd_carta", center=(0.0, top + 0.004 * i, 0.0)).transformed(ry=0.12 * i - 0.1, t=(0.1 * M, 0, -0.52 * M + i * 6)))
    m.merge(G.tube([(0.27, top + 0.006, -0.3), (0.2, top + 0.006, -0.42)], [0.005, 0.005], "cd_ferro", n=4))
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


LOW = 1.42                # where the chain ends and the padlock hangs (m)


def catena():
    """Origin on the floor under the hook: the chain hangs 6 cm off a wall at +z down to 1.42 m. The padlock is
    another static (459), so that it can fall."""
    m = G.Mesh()
    z, top, low = -0.06, 3.5, LOW
    n = int(round((top - low) / 0.26))
    for k in range(n):
        y0, y1 = low + (top - low) * k / n, low + (top - low) * (k + 1) / n
        for (ax, az) in ((0.035, 0.0), (0.0, 0.035)):                      # two crossed strips, each seen from both sides
            pts = [((-ax) * M, y1 * M, (z - az) * M), (ax * M, y1 * M, (z + az) * M), (ax * M, y0 * M, (z + az) * M), ((-ax) * M, y0 * M, (z - az) * M)]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
            m.face(pts, "cd_catena", uv=uv, blend=1)
            m.face(pts[::-1], "cd_catena", uv=uv[::-1], blend=1)
    m.merge(G.box(0.05, 0.04, 0.05, "cd_ferro", center=(0, top - 0.02, -0.035)))        # the eye in the ceiling
    m.merge(G.box(0.12, 0.05, 0.03, "cd_ferro", center=(0, low - 0.26, -0.015)))        # the staple in the wall
    return m, None


def lucchetto():
    """The padlock, origin in the middle of its body: it hangs from the chain (body 0.19 m under LOW) and falls."""
    m = G.Mesh()
    m.merge(G.box(0.085, 0.1, 0.035, "cd_lucchetto", center=(0, -0.05, 0), bottom=True))
    for x in (-0.026, 0.026):
        m.merge(G.cylinder(0.008, 0.008, 0.1, "cd_ferro", n=5, base=(x, 0.05, 0), top_cap=False))
    m.merge(G.box(0.07, 0.016, 0.016, "cd_ferro", center=(0, 0.14, 0)))
    return m, None


def catena_a_terra():
    """The chain once it has come down: a small heap of links on the floor."""
    import math
    m = G.Mesh()
    for i, (a, r, y) in enumerate(((0.0, 0.16, 0.012), (1.1, 0.13, 0.02), (2.3, 0.15, 0.028), (0.6, 0.09, 0.036), (1.8, 0.07, 0.044), (2.8, 0.11, 0.016))):
        dx, dz = math.cos(a) * r, math.sin(a) * r
        px, pz = -math.sin(a) * 0.035, math.cos(a) * 0.035
        pts = [((-dx - px) * M, y * M, (-dz - pz) * M), ((dx - px) * M, y * M, (dz - pz) * M), ((dx + px) * M, y * M, (dz + pz) * M), ((-dx + px) * M, y * M, (-dz + pz) * M)]
        uv = [(0, 0), (0, 1), (1, 1), (1, 0)]
        m.face(pts, "cd_catena", uv=uv, blend=1)
        m.face(pts[::-1], "cd_catena", uv=uv[::-1], blend=1)
    return m, None


def main():
    textures()
    statics = []
    for sid, name, fn in ((455, "COMPUTER_LAB", lambda: computer("cd_schermo")), (456, "NUMERI_INTERRUTTORI", numeri),
                          (457, "COMPUTER_LAB_SPENTO", lambda: computer("cd_spento")), (458, "CATENA_BOTOLA", catena), (459, "LUCCHETTO_BOTOLA", lucchetto), (449, "CATENA_A_TERRA", catena_a_terra)):
        mesh, coll = fn()
        lo, hi = mesh.bbox()
        print(sid, name, len(mesh.f), [int(v) for v in lo], [int(v) for v in hi])
        statics.append((sid, name, mesh, coll))
    W.write(OUT, tex.pages, statics, notes="Coda di Volpe - prologo: computer del laboratorio con il codice del cancello (455, 457), numeri degli interruttori (456)")
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
