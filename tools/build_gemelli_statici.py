"""CdV_Gemelli.wad2: the statues of the twins of Tindari (pushables 393/394 of CdV_Domus.wad2, modelled from
Ed's photo) as plain statics 446 (Castore) and 447 (Polluce), to dress other levels with. Same meshes, same
texture pages: only the container changes."""
import os
import struct
import zlib

import wadtool
from decor import wad2 as W

WADS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "wads")
SRC, OUT = os.path.join(WADS, "CdV_Domus.wad2"), os.path.join(WADS, "CdV_Gemelli.wad2")
IDS = {393: (446, "Statua di Castore"), 394: (447, "Statua di Polluce")}


def vec(payload, key):
    i = payload.index(key) + len(key) + 1
    return struct.unpack("<3f", payload[i:i + 12])


def main():
    top = wadtool.load(SRC)
    tex = dict(top)[b"W2Textures"]
    statics = []
    for mid, p in wadtool.moveables(top):
        if mid not in IDS:
            continue
        _, q = wadtool._leb_u(p, 0)
        mesh = dict(wadtool._chunks(p, q, len(p)))[b"W2Mesh"]
        lo, hi = vec(mesh, b"W2BBMin"), vec(mesh, b"W2BBMax")
        sid, name = IDS[mid]
        print(sid, name, "box", [round(v) for v in lo], [round(v) for v in hi])
        w = min(hi[0] - lo[0], hi[2] - lo[2]) * 0.35
        cmin, cmax = (-w, lo[1], -w), (w, hi[1], w)
        statics.append(W.parent("W2Static2", wadtool._chunk(b"W2Mesh", mesh), W.c_int("W2StaticAmbientLight", 128),
                                W.c_bool("W2StaticShatter", False), W.c_int("W2StaticShatterSound", -1),
                                W.parent("W2StaticVB", W.c_vec3("W2BBMin", lo), W.c_vec3("W2BBMax", hi)),
                                W.parent("W2StaticCB", W.c_vec3("W2BBMin", cmin), W.c_vec3("W2BBMax", cmax)),
                                raw=W.leb(sid) + W.leb(0)))
    body = W.c_int("W2SuggestedGameVersion", W.TOMB_ENGINE) + W.c_int("W2SoundSystem", W.SOUND_XML)
    body += wadtool._chunk(b"W2Textures", tex)
    body += W.parent("W2Sprites") + W.parent("W2SpriteSequences") + W.parent("W2Moveables")
    body += W.parent("W2Statics", *statics)
    body += W.parent("W2Metadata", W.parent("W2Timestamp", raw=b"".join(W.leb(v) for v in (2026, 11, 12, 20, 30, 0))),
                     W.c_str("W2UserNotes", "Coda di Volpe - le statue dei gemelli di Tindari come statici (446 Castore, 447 Polluce)"))
    body += b"\x00"
    data = zlib.compress(body, 9)
    with open(OUT, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
    t2 = wadtool.load(OUT)
    print(OUT, os.path.getsize(OUT), "statics", list(wadtool.statics(t2))[:4])


main()
