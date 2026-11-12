"""CdV_Tempio.wad2: the things of La meta' perduta that are not in CdV_Oggetti.

- PUZZLE_ITEM10 (509) Pileo di Castore (bronze), PUZZLE_ITEM11 (510) Pileo di Polluce (gold): the caps of the twins.
- ANIMATING5..8 (1204-1207): the same four things as fixed models to show on the altar and in the niches of the
  gate once Lara has put them there (hidden and shown from Lua, they are not pickups).
"""
import os
import struct
import zlib

import numpy as np

import build_objects as B
import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W

OUT = os.path.join(B.WADS, "CdV_Tempio.wad2")


def pileo(metal, gem, s=1.0):
    m = G.Mesh()
    m.merge(G.cylinder(0.125 * s, 0.135 * s, 0.03 * s, metal, n=12))                                   # brim
    m.merge(G.cylinder(0.118 * s, 0.085 * s, 0.11 * s, metal, n=12, base=(0, 0.03 * s, 0), top_cap=False))
    m.merge(G.cylinder(0.085 * s, 0.02 * s, 0.12 * s, metal, n=12, base=(0, 0.14 * s, 0)))            # the egg-shaped crown
    m.merge(G.ellipsoid(0.03 * s, 0.03 * s, 0.03 * s, gem, n=8, rings=4, center=(0, 0.275 * s, 0)))   # the star on top
    return m


ITEMS = {
    509: ("Pileo di Castore", lambda: pileo("it_bronzo", "it_rubino")),
    510: ("Pileo di Polluce", lambda: pileo("it_oro", "it_zaffiro")),
    1204: ("Astro di Castore (altare)", lambda: B.astro("it_oro", "it_rubino")),
    1205: ("Astro di Polluce (altare)", lambda: B.astro("it_argento", "it_zaffiro")),
    1206: ("Pileo di Castore (nicchia)", lambda: pileo("it_bronzo", "it_rubino", 1.5)),
    1207: ("Pileo di Polluce (nicchia)", lambda: pileo("it_oro", "it_zaffiro", 1.5)),
}


def main():
    first = B.build_textures()
    bone, ani = B._template()
    movs = []
    for mid, (name, fn) in sorted(ITEMS.items()):
        mesh = B.remap_pages(fn(), first)
        mc, _ = W.mesh_chunk(mesh, name)
        movs.append(B.moveable(mid, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", B.anim_for(mesh, ani))]))
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "tempio_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00")
    body += W.parent("W2Statics")
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 20, 0, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - La meta' perduta: i pilei dei gemelli, gli astri e i pilei da mostrare"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    top = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), "moveables", [m for m, _ in wadtool.moveables(top)], "pages", len(pages))


if __name__ == "__main__":
    main()
