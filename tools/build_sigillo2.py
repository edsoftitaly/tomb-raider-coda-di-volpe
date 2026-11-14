"""CdV_Sigillo2.wad2: the Seal of the tonnara, less of a drawing and more of a thing (Ed, 14/11/2026).

A cast bronze seal: the tuna in relief over the waves, the legend TONNARA DI OLIVERI round it, a rope border, a raised
rim, a lug with a ring. The relief is a height map lit from the upper left, with verdigris in the hollows.

 505 PUZZLE_ITEM6   the Seal to pick up (lying, relief up)
 702                the Seal in its plate (sigillo_posto): upright, relief towards -z, same place and size as before

First in the wad list of Marinello: it takes the place of the 505 of CdV_Oggetti and of the 702 of CdV_Sigillo."""
import math
import os
import struct
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import build_objects as B
import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W
from decor.santuario_models import fface

M = G.M
OUT = os.path.join(B.WADS, "CdV_Sigillo2.wad2")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
S = 256
SS = 4


def _arc_text(mask, text, radius, centre_deg, size, spread):
    """Letters set round a circle, their feet towards the centre (top arc) of a 4x mask."""
    f = ImageFont.truetype(FONT, size * SS)
    n = len(text)
    c = S * SS / 2
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        a = centre_deg + (i - (n - 1) / 2.0) * spread
        g = Image.new("L", (size * SS * 2, size * SS * 2), 0)
        ImageDraw.Draw(g).text((size * SS, size * SS), ch, font=f, fill=255, anchor="mm")
        g = g.rotate(-a, resample=Image.BICUBIC)
        x = c + radius * SS * math.sin(math.radians(a))
        y = c - radius * SS * math.cos(math.radians(a))
        mask.paste(255, (int(x - g.width / 2), int(y - g.height / 2)), g)


def heightmap():
    c = S * SS / 2
    R = S * SS / 2 - 2 * SS
    yy, xx = np.mgrid[0:S * SS, 0:S * SS]
    r = np.hypot(xx - c, yy - c) / R
    ang = np.arctan2(yy - c, xx - c)
    H = np.zeros((S * SS, S * SS))
    # the field, slightly dished; the raised rim with its rope; a bead inside
    H += np.where(r < 0.80, 0.05 * (1 - (r / 0.8) ** 2), 0)
    rim = (r >= 0.86) & (r <= 1.0)
    H[rim] = 0.75 + 0.25 * np.sin(ang[rim] * 44 + (r[rim] - 0.86) * 46)
    bead = np.abs(r - 0.82) < 0.014
    H[bead] = 0.5 + 0.2 * np.sin(ang[bead] * 90)

    def blur(img, px):
        return np.asarray(img.filter(ImageFilter.GaussianBlur(px * SS)), dtype=np.float64) / 255.0
    # the tuna: a full, heavy body, drawn as a profile and rounded by blurring its mask twice
    body = Image.new("L", (S * SS, S * SS), 0)
    d = ImageDraw.Draw(body)

    def P(pts):
        return [(c + x * R, c + y * R) for x, y in pts]
    up = [(-0.50, 0.02), (-0.42, -0.07), (-0.28, -0.15), (-0.08, -0.19), (0.12, -0.17), (0.28, -0.11), (0.40, -0.04), (0.47, 0.0)]
    dn = [(0.40, 0.045), (0.28, 0.10), (0.10, 0.16), (-0.10, 0.17), (-0.30, 0.13), (-0.44, 0.07)]
    d.polygon(P(up + dn), fill=255)
    fins = Image.new("L", (S * SS, S * SS), 0)
    df = ImageDraw.Draw(fins)
    df.polygon(P([(0.45, 0.0), (0.60, -0.20), (0.56, -0.02), (0.60, 0.19)]), fill=255)                  # the lunate tail
    df.polygon(P([(-0.16, -0.18), (-0.06, -0.33), (0.02, -0.18)]), fill=255)                             # first dorsal
    df.polygon(P([(0.08, -0.17), (0.16, -0.30), (0.19, -0.14)]), fill=255)                               # second dorsal
    df.polygon(P([(0.06, 0.16), (0.15, 0.29), (0.18, 0.13)]), fill=255)                                  # anal
    for k in range(5):                                                                                    # the finlets
        x = 0.22 + k * 0.045
        df.polygon(P([(x, -0.125 + k * 0.017), (x + 0.02, -0.17 + k * 0.02), (x + 0.035, -0.115 + k * 0.017)]), fill=255)
        df.polygon(P([(x, 0.115 - k * 0.013), (x + 0.02, 0.155 - k * 0.016), (x + 0.035, 0.105 - k * 0.013)]), fill=255)
    df.polygon(P([(-0.24, 0.03), (-0.04, 0.10), (-0.20, 0.07)]), fill=255)                               # pectoral
    b1, b2 = blur(body, 5), blur(body, 1.2)
    H = np.maximum(H, np.where(b2 > 0.5, 0.25 + 0.75 * np.clip((b1 - 0.5) * 2.2, 0, 1), 0))
    H = np.maximum(H, blur(fins, 0.8) * 0.45)
    cut = Image.new("L", (S * SS, S * SS), 0)                                                            # engraved lines
    dc = ImageDraw.Draw(cut)
    dc.arc([c - 0.40 * R, c - 0.17 * R, c - 0.26 * R, c + 0.15 * R], -70, 70, fill=255, width=2 * SS)   # gill cover
    dc.line(P([(-0.26, -0.01), (0.0, -0.035), (0.30, -0.015), (0.44, 0.0)]), fill=255, width=SS)        # lateral line
    dc.line(P([(-0.50, 0.035), (-0.42, 0.04)]), fill=255, width=SS)                                      # mouth
    H -= blur(cut, 0.5) * 0.35
    eye = Image.new("L", (S * SS, S * SS), 0)
    de = ImageDraw.Draw(eye)
    ex, ey = c - 0.40 * R, c - 0.035 * R
    de.ellipse([ex - 0.028 * R, ey - 0.028 * R, ex + 0.028 * R, ey + 0.028 * R], fill=255)
    H += blur(eye, 0.4) * 0.3
    # the sea under it
    wav = Image.new("L", (S * SS, S * SS), 0)
    dw = ImageDraw.Draw(wav)
    for j, y0 in enumerate((0.33, 0.43, 0.52)):
        w = 0.60 - j * 0.13
        pts = [(x, y0 + 0.028 * math.sin(x * 22 + j * 2)) for x in np.linspace(-w, w, 60)]
        dw.line(P(pts), fill=255, width=3 * SS)
    H = np.maximum(H, blur(wav, 0.7) * 0.4)
    # the legend
    txt = Image.new("L", (S * SS, S * SS), 0)
    _arc_text(txt, "TONNARA DI OLIVERI", 87, 0, 19, 9.6)
    star = Image.new("L", (S * SS, S * SS), 0)
    ds = ImageDraw.Draw(star)
    for a in (118, 242):
        x, y = c + 87 * SS * math.sin(math.radians(a)), c - 87 * SS * math.cos(math.radians(a))
        ds.regular_polygon((x, y, 5 * SS), 4, rotation=45, fill=255)
    H = np.maximum(H, np.where(r < 0.80, blur(txt, 0.45) * 0.55, 0))
    H = np.maximum(H, blur(star, 0.4) * 0.5)
    return H, r


def relief():
    H, r = heightmap()
    rng = np.random.default_rng(1911)
    H = H + (rng.random(H.shape) - 0.5) * 0.02                           # the grain of the casting
    Hs = np.asarray(Image.fromarray(np.clip(H * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2 * SS)), dtype=np.float64) / 255
    gy, gx = np.gradient(H * 90.0)
    nx, ny, nz = -gx, -gy, np.ones_like(H) * SS
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    L = np.array([-0.55, -0.62, 0.56])
    L = L / np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    spec = np.clip(nx * L[0] * 0.6 + ny * L[1] * 0.6 + nz * 0.9, 0, 1) ** 24
    occl = np.clip(1.0 - (Hs - H) * 2.2, 0.35, 1.0)                      # the hollows are darker
    bronze = np.array([168, 116, 58], float)
    col = bronze[None, None] * (0.32 + 0.95 * diff[..., None]) * occl[..., None] + np.array([255, 226, 170])[None, None] * spec[..., None] * 0.55
    wear = np.clip((H - 0.72) * 3, 0, 1)                                  # the high points are rubbed bright
    col = col * (1 + 0.25 * wear[..., None])
    low = np.clip((Hs - H) * 5 + (0.18 - H) * 1.5, 0, 1)                  # verdigris where water stood
    blot = np.asarray(Image.fromarray((rng.random((S // 4, S // 4)) * 255).astype(np.uint8)).resize((S * SS, S * SS), Image.BICUBIC), dtype=np.float64) / 255
    pat = np.clip(low * (0.35 + 0.9 * blot), 0, 0.8)
    col = col * (1 - pat[..., None]) + np.array([74, 128, 104])[None, None] * pat[..., None] * (0.5 + 0.6 * diff[..., None])
    col = np.where((r > 1.0)[..., None], np.array([92, 62, 30])[None, None], col)
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize((S, S), Image.LANCZOS)
    a = np.zeros((S, S, 4))
    a[..., :3] = np.asarray(im, dtype=np.float64)
    a[..., 3] = 255
    return a


def back_tex():
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:64, 0:64]
    r = np.hypot(xx - 32, yy - 32)
    v = 0.75 + 0.12 * np.sin(r * 1.3) + (rng.random((64, 64)) - 0.5) * 0.2          # the turning marks of the lathe
    a = np.zeros((64, 64, 4))
    a[..., :3] = np.clip(np.array([150, 104, 54])[None, None] * v[..., None], 0, 255)
    a[..., 3] = 255
    return a


def sigillo(R=0.1, t=0.026, n=28):
    """Lying on the ground, relief up (+y), the top of the design towards +z."""
    m = G.Mesh()

    def ring(rr, y):
        return [np.array([rr * math.cos(2 * math.pi * k / n), y, rr * math.sin(2 * math.pi * k / n)]) for k in range(n + 1)]

    def uvp(p):
        return (0.5 + p[0] / (2 * R) * 0.985, 0.5 - p[2] / (2 * R) * 0.985)
    ri, yf, yr = R * 0.84, t - 0.004, t                                   # the field lies a little under the rim
    centre = np.array([0.0, yf + 0.0015, 0.0])
    a, b, o = ring(ri, yf), ring(R * 0.985, yr), ring(R, yr - 0.003)
    for k in range(n):
        fface(m, [centre, a[k], a[k + 1]], "sg_rilievo", np.array([0, 1.0, 0]), [uvp(centre), uvp(a[k]), uvp(a[k + 1])])
        fface(m, [a[k], b[k], b[k + 1], a[k + 1]], "sg_rilievo", np.array([0, 1.0, 0]), [uvp(a[k]), uvp(b[k]), uvp(b[k + 1]), uvp(a[k + 1])])
        fface(m, [b[k], o[k], o[k + 1], b[k + 1]], "sg_rilievo", np.array([0, 1.0, 0]), [uvp(b[k]), uvp(o[k]), uvp(o[k + 1]), uvp(b[k + 1])])
    B.rim(m, R, 0.003, yr - 0.003, "it_bronzo", n)
    lo, un = ring(R, 0.003), ring(R * 0.96, 0.0)
    c0 = np.array([0.0, 0.0, 0.0])
    for k in range(n):
        nn = (lo[k] + lo[k + 1]) / 2
        fface(m, [lo[k], un[k], un[k + 1], lo[k + 1]], "it_bronzo", np.array([nn[0], -R, nn[2]]))
        fface(m, [c0, un[k], un[k + 1]], "sg_dorso", np.array([0, -1.0, 0]),
              [(0.5, 0.5), (0.5 + 0.48 * math.cos(2 * math.pi * k / n), 0.5 + 0.48 * math.sin(2 * math.pi * k / n)),
               (0.5 + 0.48 * math.cos(2 * math.pi * (k + 1) / n), 0.5 + 0.48 * math.sin(2 * math.pi * (k + 1) / n))])
    # the lug at the top of the design, with its ring
    m.merge(G.box(0.03, t - 0.008, 0.022, "it_bronzo", center=(0, 0.004, R + 0.006), bottom=True))
    pts = [(0.022 * math.cos(q), t / 2, R + 0.036 + 0.022 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 11)]
    m.merge(G.tube(pts, [0.0045] * len(pts), "it_ferro", n=5))
    return m


def main():
    first = B.build_textures()
    pk = tex.Packer()
    pk.page = len(tex.pages) - 1
    pk.put("sg_rilievo", relief())
    pk.put("sg_dorso", back_tex())
    Image.fromarray(np.clip(relief()[..., :3], 0, 255).astype(np.uint8)).save(os.path.join(os.path.dirname(B.WADS), "foto", "sigillo_rilievo.png"))
    bone, ani = B._template()
    lying = B.remap_pages(sigillo(), first)
    # in the plate: upright, 1.25 times, its back on the plane z = 497, its middle 512 above the item
    placed = B.remap_pages(sigillo().transformed(s=(1.25, 1.25, 1.25), rx=-math.pi / 2, t=(0, 512.0, 497.0)), first)
    movs = []
    for mid, name, mesh in ((505, "Sigillo della tonnara", lying), (702, "Sigillo nella piastra", placed)):
        lo, hi = mesh.bbox()
        print(mid, name, len(mesh.f), [int(v) for v in lo], [int(v) for v in hi])
        mc, _ = W.mesh_chunk(mesh, name)
        movs.append(B.moveable(mid, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", B.anim_for(mesh, ani))]))
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "sigillo_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00") + W.parent("W2Statics")
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 14, 11, 40, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - Marinello: il Sigillo della tonnara in rilievo (PUZZLE_ITEM6 e il Sigillo nella piastra, 702)"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    top = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), [m for m, _ in wadtool.moveables(top)])


if __name__ == "__main__":
    main()
