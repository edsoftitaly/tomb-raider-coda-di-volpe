"""Write a Wad2 containing only static meshes (format from TombLib Wad2Writer.cs).

Chunk = LEB128(id length) + id + LEB128(payload size) + payload. "WithChildren" chunks end their
child list with a 0 byte. Floats chunks (W2SphR) are doubles, vectors are float32.
Texture data is raw BGRA, 4 bytes per pixel; colour (255,0,255) is turned transparent by the loader,
real alpha is kept too.
"""
import math
import struct
import zlib

import numpy as np

TOMB_ENGINE = 18
SOUND_XML = 1


def leb(v):
    out = bytearray()
    v = int(v)
    while True:
        b = v & 0x7F
        v >>= 7
        if (v == 0 and not b & 0x40) or (v == -1 and b & 0x40):
            out.append(b)
            return bytes(out)
        out.append(b | 0x80)


def chunk(cid, payload):
    cid = cid.encode("ascii")
    return leb(len(cid)) + cid + leb(len(payload)) + payload


def parent(cid, *children, raw=b""):
    return chunk(cid, raw + b"".join(children) + b"\x00")


def c_int(cid, v):
    return chunk(cid, leb(v))


def c_bool(cid, v):
    return chunk(cid, b"\x01" if v else b"\x00")


def c_str(cid, s):
    return chunk(cid, s.encode("utf-8"))


def c_vec3(cid, v):
    return chunk(cid, struct.pack("<3f", *v))


def c_double(cid, v):
    return chunk(cid, struct.pack("<d", v))


def texture_chunk(img_rgba, name):
    h, w = img_rgba.shape[:2]
    a = np.clip(img_rgba, 0, 255).astype(np.uint8)
    bgra = a[..., [2, 1, 0, 3]].copy()
    # Fully transparent pixels: keep them magenta+alpha 0 so every loader treats them as holes.
    holes = a[..., 3] == 0
    bgra[holes] = (255, 0, 255, 0)
    return parent("W2Txt", c_str("W2TxtName", name), chunk("W2TxtData", bgra.tobytes()), raw=leb(w) + leb(h))


def mesh_chunk(mesh, name):
    pos, nrm, polys = [], [], []
    for idx, px, page, blend, dbl in mesh.f:
        p = [np.array(mesh.v[i]) for i in idx]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if len(p) == 4:
            n = n + np.cross(p[2] - p[0], p[3] - p[0])
        ln = np.linalg.norm(n)
        n = n / ln if ln > 1e-9 else np.array([0, 1.0, 0])
        base = len(pos)
        for q in p:
            pos.append(q)
            nrm.append(n)
        polys.append((list(range(base, base + len(p))), px, page, blend, dbl))
    P = np.array(pos)
    lo, hi = P.min(axis=0), P.max(axis=0)
    centre = (lo + hi) / 2
    radius = float(np.linalg.norm(P - centre, axis=1).max())
    poly_chunks = []
    for ids, px, page, blend, dbl in polys:
        us = [c[0] for c in px]
        vs = [c[1] for c in px]
        body = b"".join(leb(i) for i in ids) + leb(0) + leb(page)
        body += struct.pack("<4f", min(us), min(vs), max(us), max(vs))
        body += b"".join(struct.pack("<2f", u, v) for u, v in px)
        body += leb(blend) + (b"\x01" if dbl else b"\x00")
        poly_chunks.append(parent("W2Uq2" if len(ids) == 4 else "W2Tr2", raw=body))
    return parent(
        "W2Mesh",
        c_int("W2Index", 0),
        c_str("W2MeshName", name),
        parent("W2MeshSphere", c_vec3("W2SphC", centre), c_double("W2SphR", radius)),
        parent("W2BBox", c_vec3("W2BBMin", lo), c_vec3("W2BBMax", hi)),
        parent("W2VrtPos", *[c_vec3("W2Pos", q) for q in pos]),
        parent("W2VrtNorm", *[c_vec3("W2N", n) for n in nrm]),
        parent("W2VrtShd", *[c_vec3("W2VxCol", (0.5, 0.5, 0.5)) for _ in pos]),
        parent("W2VrtWghts"),
        parent("W2VrtAttr"),
        c_int("W2MeshLightType", 0),
        c_bool("W2MeshVisible", False),
        parent("W2Polys", *poly_chunks),
    ), (lo, hi)


def static_chunk(sid, name, mesh, coll):
    mc, (lo, hi) = mesh_chunk(mesh, name)
    if coll is None:
        cmin = cmax = (0.0, 0.0, 0.0)
    else:
        cmin, cmax = coll
    return parent(
        "W2Static2",
        mc,
        c_int("W2StaticAmbientLight", 128),
        c_bool("W2StaticShatter", False),
        c_int("W2StaticShatterSound", -1),
        parent("W2StaticVB", c_vec3("W2BBMin", lo), c_vec3("W2BBMax", hi)),
        # Tomb Editor compiles the box as Y1 = -Min.Y, Y2 = -Max.Y and TombEngine wants Y1 < Y2 (top first, as in a TR
        # level): so in the wad Min.Y is the TOP and Max.Y the bottom. Written the other way round the box reaches the
        # game upside down and the static does not collide at all (found on 20 Nov: no static of ours ever did).
        parent("W2StaticCB", c_vec3("W2BBMin", (cmin[0], max(cmin[1], cmax[1]), cmin[2])),
               c_vec3("W2BBMax", (cmax[0], min(cmin[1], cmax[1]), cmax[2]))),
        raw=leb(sid) + leb(0),
    )


def write(path, pages, statics, notes="", compress=True):
    body = c_int("W2SuggestedGameVersion", TOMB_ENGINE) + c_int("W2SoundSystem", SOUND_XML)
    body += parent("W2Textures", *[texture_chunk(p, "decor_%d.png" % i) for i, p in enumerate(pages)])
    body += parent("W2Sprites") + parent("W2SpriteSequences") + parent("W2Moveables")
    body += parent("W2Statics", *[static_chunk(*s) for s in statics])
    body += parent("W2Metadata", parent("W2Timestamp", raw=b"".join(leb(v) for v in (2026, 10, 27, 12, 0, 0))),
                   c_str("W2UserNotes", notes))
    body += b"\x00"
    with open(path, "wb") as f:
        if compress:
            data = zlib.compress(body, 9)
            f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)
        else:
            f.write(b"WAD2" + struct.pack("<I", 0) + body)
    return len(body)
