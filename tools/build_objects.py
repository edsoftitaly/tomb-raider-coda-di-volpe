"""CdV_Oggetti.wad2: pickups that look like what their names say, the box-room key and lock, a house door.

- PUZZLE_ITEM1..8 (500-507): Diario bizantino, Chiave della terrazza, Mappa delle maree, Chiave del Casello,
  Conchiglia del canto, Sigillo della tonnara, Astro di Castore, Astro di Polluce.
- KEY_ITEM1 (548) Chiave del ripostiglio, KEY_HOLE1 (700) its lock plate on the wall.
- DOOR_TYPE1 (850): a painted wooden house door, with the animations of TR4 DOOR_TYPE3 (852).

Each pickup is one mesh with one bone and a one-frame animation built from the template of the old
items (identity rotation, keyframe bounding box = the mesh). The door keeps 852's bone and animations
and only swaps the mesh, inside the same local box, so it sits where the TR4 door sat.
Wad2 meshes are Y up, 512 units per metre, like the decoration statics.
"""
import math
import os
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W
from decor.geom import M
from decor.santuario_tex import from_img, tex as ntex, to_img

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WADS = os.path.join(ROOT, "assets", "wads")
OUT = os.path.join(WADS, "CdV_Oggetti.wad2")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


# ------------------------------------------------------------------------------ textures
def leather():
    im = to_img(ntex(128, 128, (110, 30, 30), 1, 0.25, 6))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, 121, 121], outline=(200, 160, 70), width=3)
    d.rectangle([14, 14, 113, 113], outline=(200, 160, 70), width=1)
    d.rectangle([58, 26, 70, 102], fill=(214, 172, 80))          # Byzantine cross
    d.rectangle([34, 50, 94, 62], fill=(214, 172, 80))
    d.rectangle([44, 80, 84, 88], fill=(214, 172, 80))
    for x, y in ((26, 26), (102, 26), (26, 102), (102, 102)):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(170, 40, 50))
    return from_img(im)


def pages():
    img = ntex(64, 64, (226, 214, 180), 2, 0.08)
    for y in range(0, 64, 3):
        img[y] *= 0.9
    return W.np.clip(np.concatenate([img, np.full((64, 64, 1), 255.0)], axis=2), 0, 255)


def tide_map():
    im = to_img(ntex(128, 128, (222, 200, 150), 3, 0.2, 10))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (128, 0), (128, 46), (90, 56), (60, 50), (30, 64), (0, 58)], fill=(110, 150, 170))
    d.line([(0, 58), (30, 64), (60, 50), (90, 56), (128, 46)], fill=(80, 60, 40), width=2)
    d.ellipse([52, 70, 74, 84], outline=(40, 70, 120), width=2)        # the Mergolo
    d.line([(56, 76), (70, 78)], fill=(170, 30, 30), width=2)
    d.line([(63, 70), (63, 84)], fill=(170, 30, 30), width=2)
    for y in range(92, 124, 7):
        d.line([(10, y), (60 + (y * 7) % 50, y)], fill=(90, 70, 50), width=1)
    d.polygon([(108, 70), (112, 84), (108, 98), (104, 84)], fill=(90, 60, 40))   # compass
    d.polygon([(94, 84), (108, 80), (122, 84), (108, 88)], fill=(90, 60, 40))
    return from_img(im)


def solid(color, seed, amount=0.15):
    return np.concatenate([ntex(64, 64, color, seed, amount, 8), np.full((64, 64, 1), 255.0)], axis=2)


def shell():
    im = to_img(ntex(128, 128, (236, 196, 176), 5, 0.1))
    d = ImageDraw.Draw(im)
    for k in range(10):
        d.arc([-60 + k * 6, -60 + k * 6, 188 - k * 6, 188 - k * 6], 0, 360, fill=(200, 130, 110), width=3)
    for x in range(0, 128, 10):
        d.line([(x, 0), (64, 128)], fill=(214, 160, 140), width=1)
    return from_img(im)


def seal():
    im = to_img(ntex(128, 128, (150, 104, 54), 6, 0.25, 6))
    d = ImageDraw.Draw(im)
    d.ellipse([4, 4, 124, 124], outline=(96, 64, 30), width=5)
    d.ellipse([14, 14, 114, 114], outline=(190, 140, 80), width=2)
    d.polygon([(30, 64), (54, 50), (84, 52), (98, 64), (84, 76), (54, 78)], fill=(96, 64, 30))   # tuna
    d.polygon([(98, 64), (112, 52), (110, 76)], fill=(96, 64, 30))
    d.ellipse([40, 58, 46, 64], fill=(200, 160, 100))
    f = ImageFont.truetype(FONT, 12)
    d.text((34, 90), "TONNARA", font=f, fill=(96, 64, 30))
    return from_img(im)


def star(color, seed):
    im = to_img(ntex(128, 128, color, seed, 0.15, 4))
    d = ImageDraw.Draw(im)
    for k in range(8):
        a = math.radians(k * 45)
        d.line([(64, 64), (64 + 60 * math.cos(a), 64 + 60 * math.sin(a))], fill=tuple(int(c * 0.75) for c in color), width=3)
    return from_img(im)


def lock_plate():
    im = to_img(ntex(64, 128, (196, 160, 80), 7, 0.12))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, 61, 125], outline=(140, 110, 50), width=3)
    d.ellipse([24, 44, 40, 60], fill=(20, 18, 16))
    d.polygon([(28, 54), (36, 54), (38, 80), (26, 80)], fill=(20, 18, 16))
    d.ellipse([28, 100, 36, 108], fill=(160, 130, 60))
    return from_img(im)


def door_leaf():
    im = to_img(ntex(128, 256, (232, 226, 210), 8, 0.06, 16))        # painted wood, white-cream
    d = ImageDraw.Draw(im)
    for y0 in (14, 136):
        d.rectangle([14, y0, 114, y0 + 106], outline=(196, 188, 170), width=4)
        d.rectangle([24, y0 + 10, 104, y0 + 96], outline=(214, 206, 190), width=2)
    return from_img(im)


def build_textures():
    tex.build()
    first = len(tex.pages)
    pk = tex.Packer()
    for name, img in (("it_cuoio", leather()), ("it_pagine", pages()), ("it_mappa", tide_map()),
                      ("it_ferro", solid((52, 50, 48), 11, 0.25)), ("it_ottone", solid((196, 158, 70), 12)),
                      ("it_conchiglia", shell()), ("it_bronzo_sigillo", seal()),
                      ("it_bronzo", solid((150, 104, 54), 13, 0.25)),
                      ("it_oro", star((226, 182, 70), 14)), ("it_argento", star((176, 196, 220), 15)),
                      ("it_rubino", solid((190, 30, 40), 16, 0.3)), ("it_zaffiro", solid((40, 80, 200), 17, 0.3)),
                      ("it_serratura", lock_plate()), ("it_porta", door_leaf()),
                      ("it_legno_bordo", solid((214, 206, 190), 18, 0.1))):
        pk.put(name, img)
    return first


# ------------------------------------------------------------------------------ meshes
def quad(m, pts, region, n, uv=None, double=False):
    from decor.santuario_models import fface
    fface(m, pts, region, n, uv, double=double)


def flat_disc(m, r, y, region, n=16, centre=(0.0, 0.0), down=False):
    from decor.santuario_models import fface
    cx, cz = centre
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = [np.array([cx, y, cz]), np.array([cx + r * math.cos(a0), y, cz + r * math.sin(a0)]),
               np.array([cx + r * math.cos(a1), y, cz + r * math.sin(a1)])]
        uv = [(0.5, 0.5), (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)), (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1))]
        fface(m, pts, region, np.array([0, -1.0 if down else 1.0, 0]), uv)


def rim(m, r, y0, y1, region, n=16, centre=(0.0, 0.0)):
    from decor.santuario_models import fface
    cx, cz = centre
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = np.array([cx + r * math.cos(a0), 0, cz + r * math.sin(a0)])
        p1 = np.array([cx + r * math.cos(a1), 0, cz + r * math.sin(a1)])
        nn = (p0 + p1) / 2 - np.array([cx, 0, cz])
        fface(m, [p0 + [0, y0, 0], p1 + [0, y0, 0], p1 + [0, y1, 0], p0 + [0, y1, 0]], region, nn,
              [(k / n, 1), ((k + 1) / n, 1), ((k + 1) / n, 0), (k / n, 0)])


def diario():
    m = G.Mesh()
    m.merge(G.box(0.26, 0.07, 0.34, "it_pagine", top="it_cuoio", bottom=True))
    m.merge(G.box(0.02, 0.07, 0.34, "it_cuoio", center=(-0.13, 0, 0)))      # spine
    return m


def key(region, size=1.0, ring_r=0.05):
    m = G.Mesh()
    s = size
    flat_disc(m, ring_r * s, 0.016 * s, region, 12, centre=(-0.1 * s, 0))
    rim(m, ring_r * s, 0, 0.016 * s, region, 12, centre=(-0.1 * s, 0))
    m.merge(G.box(0.2 * s, 0.016 * s, 0.022 * s, region, center=(0.03 * s, 0, 0)))
    m.merge(G.box(0.04 * s, 0.016 * s, 0.06 * s, region, center=(0.11 * s, 0, 0.03 * s)))
    m.merge(G.box(0.02 * s, 0.016 * s, 0.04 * s, region, center=(0.075 * s, 0, 0.025 * s)))
    return m


def mappa():
    m = G.Mesh()
    m.merge(G.box(0.36, 0.012, 0.26, "it_pagine", top="it_mappa"))
    m.merge(G.cylinder(0.025, 0.025, 0.26, "it_pagine", n=8, base=(0, 0, 0)).transformed(rx=math.pi / 2, t=(0.19 * M, 0.025 * M, -0.13 * M)))
    return m


def conchiglia():
    m = G.Mesh()
    m.merge(G.ellipsoid(0.11, 0.07, 0.17, "it_conchiglia", n=12, rings=6, center=(0, 0.07, 0), squash_bottom=0.5))
    m.merge(G.cylinder(0.06, 0.0, 0.12, "it_conchiglia", n=10, base=(0, 0, 0)).transformed(rx=math.pi / 2, t=(0, 0.08 * M, 0.12 * M)))
    return m


def sigillo():
    m = G.Mesh()
    flat_disc(m, 0.1, 0.03, "it_bronzo_sigillo", 20)
    flat_disc(m, 0.1, 0.0, "it_bronzo", 20, down=True)
    rim(m, 0.1, 0.0, 0.03, "it_bronzo", 20)
    m.merge(G.box(0.03, 0.05, 0.03, "it_bronzo", center=(0, 0.03, 0)))       # handle of the stamp
    return m


def astro(metal, gem):
    from decor.santuario_models import fface
    m = G.Mesh()
    pts = []
    for k in range(16):
        r = 0.15 if k % 2 == 0 else 0.065
        a = math.radians(k * 22.5)
        pts.append((r * math.cos(a), r * math.sin(a)))
    h = 0.035
    for k in range(16):
        (x0, z0), (x1, z1) = pts[k], pts[(k + 1) % 16]
        uv = [(0.5, 0.5), (0.5 + x0 / 0.3, 0.5 + z0 / 0.3), (0.5 + x1 / 0.3, 0.5 + z1 / 0.3)]
        fface(m, [np.array([0, h + 0.02, 0]), np.array([x0, h, z0]), np.array([x1, h, z1])], metal, np.array([0, 1.0, 0]), uv)
        fface(m, [np.array([0, 0, 0]), np.array([x0, 0, z0]), np.array([x1, 0, z1])], metal, np.array([0, -1.0, 0]), uv)
        nn = np.array([(z1 - z0), 0, -(x1 - x0)])
        if np.dot(nn, [x0 + x1, 0, z0 + z1]) < 0:
            nn = -nn
        fface(m, [np.array([x0, 0, z0]), np.array([x1, 0, z1]), np.array([x1, h, z1]), np.array([x0, h, z0])], metal, nn)
    m.merge(G.ellipsoid(0.035, 0.025, 0.035, gem, n=8, rings=4, center=(0, h + 0.03, 0)))
    return m


def serratura():
    """Lock plate on the wall face 1 m north of the item (TombEngine: Lara stands south of it facing north)."""
    m = G.Mesh()
    quad(m, [np.array([-0.06, 0.95, 0.97]), np.array([0.06, 0.95, 0.97]), np.array([0.06, 1.2, 0.97]), np.array([-0.06, 1.2, 0.97])],
         "it_serratura", np.array([0, 0, -1.0]), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.merge(G.box(0.12, 0.25, 0.02, "it_ottone", center=(0, 0.95, 0.985)))
    return m


def porta():
    """Two leaves in the local box of TR4 DOOR_TYPE3's mesh: x -2..0 m, z +-0.045, y -1.0..+1.3 m (the
    animation lifts it by 1 m, so it stands 2.3 m tall on the floor, as the frames' openings)."""
    m = G.Mesh()
    y0, y1, t = -1.0, 1.3, 0.045
    for x0, x1, flip in ((-2.0, -1.0, False), (-1.0, 0.0, True)):
        uv = [(1, 1), (0, 1), (0, 0), (1, 0)] if flip else [(0, 1), (1, 1), (1, 0), (0, 0)]
        quad(m, [np.array([x0, y0, t]), np.array([x1, y0, t]), np.array([x1, y1, t]), np.array([x0, y1, t])], "it_porta", np.array([0, 0, 1.0]), uv)
        quad(m, [np.array([x1, y0, -t]), np.array([x0, y0, -t]), np.array([x0, y1, -t]), np.array([x1, y1, -t])], "it_porta", np.array([0, 0, -1.0]), uv)
    for x, nx in ((-2.0, -1.0), (0.0, 1.0)):
        quad(m, [np.array([x, y0, -t]), np.array([x, y0, t]), np.array([x, y1, t]), np.array([x, y1, -t])], "it_legno_bordo", np.array([nx, 0, 0]))
    quad(m, [np.array([-2.0, y1, -t]), np.array([0.0, y1, -t]), np.array([0.0, y1, t]), np.array([-2.0, y1, t])], "it_legno_bordo", np.array([0, 1.0, 0]))
    m.merge(G.box(0.03, 0.03, 0.14, "it_ottone", center=(-1.12, 0.05, 0)))     # handle
    m.merge(G.box(0.03, 0.03, 0.14, "it_ottone", center=(-0.88, 0.05, 0)))
    return m


PICKUPS = {
    500: ("Diario bizantino", diario),
    501: ("Chiave della terrazza", lambda: key("it_ottone", 1.0)),
    502: ("Mappa delle maree", mappa),
    503: ("Chiave del Casello", lambda: key("it_ferro", 1.6, 0.06)),
    504: ("Conchiglia del canto", conchiglia),
    505: ("Sigillo della tonnara", sigillo),
    506: ("Astro di Castore", lambda: astro("it_oro", "it_rubino")),
    507: ("Astro di Polluce", lambda: astro("it_argento", "it_zaffiro")),
    548: ("Chiave del ripostiglio", lambda: key("it_ottone", 1.8, 0.06)),
    700: ("Serratura del ripostiglio", serratura),
}


# ------------------------------------------------------------------------------ wad assembly
def _template():
    top = wadtool.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "CdV_Oggetti_A.wad2"))
    for mid, p in wadtool.moveables(top):
        if mid == 500:
            _, q = wadtool._leb_u(p, 0)
            ch = dict(wadtool._chunks(p, q, len(p)))
            return ch[b"W2Bone2"], ch[b"W2Ani2"]
    raise SystemExit("template pickup 500 not found")


def _patch_vec(payload, key, vec, occurrence=0):
    i = -1
    for _ in range(occurrence + 1):
        i = payload.index(key, i + 1)
    j = i + len(key) + 1          # chunk id, then 1-byte size (12)
    return payload[:j] + struct.pack("<3f", *vec) + payload[j + 12:]


def anim_for(mesh, ani):
    lo, hi = mesh.bbox()
    ani = _patch_vec(ani, b"W2KfOffs", (0.0, 0.0, 0.0))
    ani = _patch_vec(ani, b"W2BBMin", tuple(lo))
    ani = _patch_vec(ani, b"W2BBMax", tuple(hi))
    ani = _patch_vec(ani, b"W2KfA", (0.0, 0.0, 0.0))
    return ani


def remap_pages(mesh, first):
    mesh.f = [(idx, px, page - first, blend, dbl) for idx, px, page, blend, dbl in mesh.f]
    return mesh


def moveable(mid, mesh_c, rest):
    body = W.leb(mid) + mesh_c + b"".join(rest) + b"\x00"
    return W.chunk("W2Moveable", body)


def main():
    first = build_textures()
    bone, ani = _template()
    movs = []
    for mid, (name, fn) in sorted(PICKUPS.items()):
        mesh = remap_pages(fn(), first)
        mc, _ = W.mesh_chunk(mesh, name)
        movs.append(moveable(mid, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", anim_for(mesh, ani))]))
    doors = wadtool.load(os.path.join(WADS, "TR4_Doors.wad2"))
    for mid, p in wadtool.moveables(doors):
        if mid != 852:
            continue
        _, q = wadtool._leb_u(p, 0)
        rest = [wadtool._chunk(c, pp) for c, pp in wadtool._chunks(p, q, len(p)) if c != b"W2Mesh"]
        mesh = remap_pages(porta(), first)
        mc, _ = W.mesh_chunk(mesh, "Porta di casa")
        movs.append(moveable(850, mc, rest))
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "oggetti_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00")
    body += W.parent("W2Statics")
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 10, 31, 9, 0, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - oggetti, chiave e serratura del ripostiglio, porta di casa"))
    body += b"\x00"
    import zlib
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    top = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), "moveables", [m for m, _ in wadtool.moveables(top)], "pages", len(pages))
    for i, p in enumerate(pages):
        Image.fromarray(np.clip(p, 0, 255).astype(np.uint8)).save(os.path.join(WADS, "..", "..", "build", "oggetti_%d.png" % i))


if __name__ == "__main__":
    main()
