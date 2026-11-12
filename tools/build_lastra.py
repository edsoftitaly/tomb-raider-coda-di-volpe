"""CdV_Lastra.wad2: the marble slab of the Castor path (ANIMATING20 of CdV_Domus.wad2) as static 454 with NO collision.
As a moveable it got ObjectCollision (object_helper.cpp, InitAnimating) and pushed Lara off the pillars of T_02_02."""
import os
import struct
import zlib

import wadtool
from decor import wad2 as W

WADS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "wads")
SRC, OUT = os.path.join(WADS, "CdV_Domus.wad2"), os.path.join(WADS, "CdV_Lastra.wad2")


def vec(payload, key):
    i = payload.index(key) + len(key) + 1
    return struct.unpack("<3f", payload[i:i + 12])


def main():
    top = wadtool.load(SRC)
    tex = dict(top)[b"W2Textures"]
    p = dict(wadtool.moveables(top))[1219]
    _, q = wadtool._leb_u(p, 0)
    mesh = dict(wadtool._chunks(p, q, len(p)))[b"W2Mesh"]
    lo, hi = vec(mesh, b"W2BBMin"), vec(mesh, b"W2BBMax")
    print("lastra box", [round(v) for v in lo], [round(v) for v in hi])
    zero = (0.0, 0.0, 0.0)
    st = W.parent("W2Static2", wadtool._chunk(b"W2Mesh", mesh), W.c_int("W2StaticAmbientLight", 128),
                  W.c_bool("W2StaticShatter", False), W.c_int("W2StaticShatterSound", -1),
                  W.parent("W2StaticVB", W.c_vec3("W2BBMin", lo), W.c_vec3("W2BBMax", hi)),
                  W.parent("W2StaticCB", W.c_vec3("W2BBMin", zero), W.c_vec3("W2BBMax", zero)),
                  raw=W.leb(454) + W.leb(0))
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += wadtool._chunk(b"W2Textures", tex)
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences") + W.parent("W2Moveables")
    body += W.parent("W2Statics", st)
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 22, 30, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - lastra del percorso di Castore come statico 454 senza collisione"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    print(OUT, os.path.getsize(OUT), list(wadtool.statics(wadtool.load(OUT))))


main()
