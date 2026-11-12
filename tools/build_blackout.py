"""CdV_Blackout.wad2: the fuse of the prologue.

- PUZZLE_ITEM12 (511) Fusibile: a ceramic cartridge fuse with brass caps
- ANIMATING9 (1208): the same fuse, bigger, to show in the box once Lara has put it in
- static 448 QUADRO_ELETTRICO: the fuse box on the wall (front towards +z, base on the floor, box at 1.2-1.7 m)
"""
import os
import struct
import zlib

import build_objects as B
import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W

OUT = os.path.join(B.WADS, "CdV_Blackout.wad2")


def fusibile(s=1.0, upright=False):
    axis = "y" if upright else "x"
    m = G.Mesh()
    L, r = 0.16 * s, 0.022 * s
    if upright:
        m.merge(G.cylinder(r, r, L, "it_legno_bordo", n=10, base=(0, 0, 0)))
        m.merge(G.cylinder(r * 1.15, r * 1.15, L * 0.2, "it_ottone", n=10, base=(0, 0, 0)))
        m.merge(G.cylinder(r * 1.15, r * 1.15, L * 0.2, "it_ottone", n=10, base=(0, L * 0.8, 0)))
    else:
        m.merge(G.tube([(-L / 2, r, 0), (L / 2, r, 0)], [r, r], "it_legno_bordo", n=10))
        m.merge(G.tube([(-L / 2, r, 0), (-L * 0.3, r, 0)], [r * 1.15, r * 1.15], "it_ottone", n=10))
        m.merge(G.tube([(L * 0.3, r, 0), (L / 2, r, 0)], [r * 1.15, r * 1.15], "it_ottone", n=10))
    return m


def quadro():
    m = G.box(0.46, 0.56, 0.14, "it_ferro", center=(0, 1.2, 0.07))
    m.merge(G.box(0.40, 0.50, 0.02, "it_legno_bordo", center=(0, 1.23, 0.15)))          # the open door's inside panel
    for i, x in enumerate((-0.12, 0.0, 0.12)):                                           # two fuses in, one socket empty
        m.merge(G.box(0.06, 0.2, 0.03, "it_ferro", center=(x, 1.42, 0.17)))
        if i != 1:
            m.merge(G.cylinder(0.022, 0.022, 0.16, "it_ottone", n=8, base=(x, 1.44, 0.2)))
    m.merge(G.box(0.2, 0.05, 0.04, "it_rubino", center=(0, 1.28, 0.17)))                 # the main switch
    m.merge(G.box(0.05, 1.3, 0.05, "it_ferro", center=(0.18, 1.76, 0.03)))               # conduit up the wall
    return m


def main():
    first = B.build_textures()
    bone, ani = B._template()
    movs = []
    for mid, name, mesh in ((511, "Fusibile", fusibile()), (1208, "Fusibile (nel quadro)", fusibile(1.25, upright=True))):
        mesh = B.remap_pages(mesh, first)
        mc, _ = W.mesh_chunk(mesh, name)
        movs.append(B.moveable(mid, mc, [wadtool._chunk(b"W2Bone2", bone), wadtool._chunk(b"W2Ani2", B.anim_for(mesh, ani))]))
    q = B.remap_pages(quadro(), first)
    pages = tex.pages[first:]
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += W.parent("W2Textures", *[W.texture_chunk(p, "blackout_%d.png" % i) for i, p in enumerate(pages)])
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences")
    body += W.chunk("W2Moveables", b"".join(movs) + b"\x00")
    body += W.parent("W2Statics", W.static_chunk(448, "Quadro elettrico", q, None))
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 21, 0, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - prologo: fusibile (PUZZLE_ITEM12), fusibile nel quadro (ANIMATING9), quadro elettrico (statico 448)"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    top = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), [m for m, _ in wadtool.moveables(top)], list(wadtool.statics(top))[:3])


if __name__ == "__main__":
    main()
