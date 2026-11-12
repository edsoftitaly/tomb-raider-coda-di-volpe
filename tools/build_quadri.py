"""CdV_Quadri.wad2: the pictures of the house of Via Amodeo, from Ed's own photographs (assets/foto): statics
450-453, same size and anchor as CASA_QUADRO (214), so they take its place one for one. Also PUZZLE_ITEM14 (513),
the key of the padlock of the trapdoor."""
import os
import struct
import zlib

import numpy as np
from PIL import Image, ImageDraw

import build_objects as B
import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W
from decor.santuario_models import UP, V, rectf

FOTO = os.path.join(os.path.dirname(B.WADS), "foto")
OUT = os.path.join(B.WADS, "CdV_Quadri.wad2")
PICS = [(450, "quadro_1_santuario.jpg", "Quadro: il santuario di Tindari sul colle"),
        (451, "quadro_2_cupola_tramonto.jpg", "Quadro: la cupola al tramonto"),
        (452, "quadro_3_golfo.jpg", "Quadro: il golfo dall'alto"),
        (453, "quadro_4_barca.jpg", "Quadro: la barca")]


def framed(path):
    w, h, b = 256, 192, 13
    im = Image.open(path).convert("RGB")
    iw, ih = w - 2 * b, h - 2 * b
    r = iw / float(ih)
    pw, ph = im.size
    if pw / float(ph) > r:
        cw = int(ph * r)
        im = im.crop(((pw - cw) // 2, 0, (pw - cw) // 2 + cw, ph))
    else:
        ch = int(pw / r)
        im = im.crop((0, (ph - ch) // 2, pw, (ph - ch) // 2 + ch))
    im = im.resize((iw, ih), Image.LANCZOS)
    out = Image.new("RGB", (w, h), (58, 38, 22))
    d = ImageDraw.Draw(out)
    d.rectangle([2, 2, w - 3, h - 3], outline=(96, 66, 36), width=3)          # the wooden frame, a lighter bead
    d.rectangle([b - 3, b - 3, w - b + 2, h - b + 2], fill=(168, 140, 78))    # gilt slip
    out.paste(im, (b, b))
    a = np.zeros((h, w, 4))
    a[..., :3] = np.asarray(out, dtype=np.float64)
    a[..., 3] = 255
    return a


def main():
    first = B.build_textures()
    pk = tex.Packer()
    pk.page = len(tex.pages) - 1
    statics = []
    for sid, f, name in PICS:
        pk.put("quadro_%d" % sid, framed(os.path.join(FOTO, f)))
    for sid, f, name in PICS:
        m = G.Mesh()
        rectf(m, V(0.02, 1.3, 0.6), V(0, 0, -1), UP, 1.2, 0.9, "quadro_%d" % sid, V(1, 0, 0), tile=None)
        statics.append(W.static_chunk(sid, name, B.remap_pages(m, first), None))
    bone, ani = B._template()
    key = B.remap_pages(B.key("it_ferro", 0.9), first)
    mc, _ = W.mesh_chunk(key, "Chiave del lucchetto")
    movs = [B.moveable(513, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", B.anim_for(key, ani))])]
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "quadri_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00") + W.parent("W2Statics", *statics)
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 22, 0, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - prologo: quadri dalle foto di Ed (450-453), chiave del lucchetto (PUZZLE_ITEM14)"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    top = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), [m for m, _ in wadtool.moveables(top)], list(wadtool.statics(top))[:6])


main()
