"""CdV_Scavi.wad2: PUZZLE_ITEM13 (512), the key of the padlock on the gate of the Roman house of Tindari."""
import os
import struct
import zlib

import build_objects as B
import wadtool
from decor import tex
from decor import wad2 as W

OUT = os.path.join(B.WADS, "CdV_Scavi.wad2")


def main():
    first = B.build_textures()
    bone, ani = B._template()
    mesh = B.remap_pages(B.key("it_bronzo", 1.2), first)
    mc, _ = W.mesh_chunk(mesh, "Chiave degli scavi")
    movs = [B.moveable(512, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", B.anim_for(mesh, ani))])]
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "scavi_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00") + W.parent("W2Statics")
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 21, 30, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - Tindari: Chiave degli scavi (PUZZLE_ITEM13)"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    print(OUT, os.path.getsize(OUT), [m for m, _ in wadtool.moveables(wadtool.load(OUT))])


main()
