"""Build the decoration wad: assets/wads/CdV_Decorazioni.wad2 (+ preview mesh JSON).

Usage: python3 build_decor.py [preview_dir]
"""
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decor import tex  # noqa: E402

tex.build()
from decor import models, wad2  # noqa: E402
from decor import santuario_models, santuario_interno_models, casa_models, marinello_models, mito_models, architravi_models  # noqa: E402,F401  (registers the sanctuary statics)
import wadtool  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "wads", "CdV_Decorazioni.wad2")


def verify(path, n_pages):
    top = wadtool.load(path)
    names = [c for c, _ in top]
    assert b"W2Statics" in names and b"W2Textures" in names
    tex_sizes = []
    for cid, p in top:
        if cid == b"W2Textures":
            for c2, p2 in wadtool._chunks(p, 0, len(p)):
                w, q = wadtool._leb_u(p2, 0)
                h, q = wadtool._leb_u(p2, q)
                data = dict(wadtool._chunks(p2, q, len(p2)))[b"W2TxtData"]
                assert len(data) == w * h * 4
                tex_sizes.append((w, h))
    count = 0
    for cid, p in top:
        if cid != b"W2Statics":
            continue
        for c2, p2 in wadtool._chunks(p, 0, len(p)):
            count += 1
            sid, q = wadtool._leb_u(p2, 0)
            fl, q = wadtool._leb_u(p2, q)
            ch = dict(wadtool._chunks(p2, q, len(p2)))
            mesh = dict(wadtool._chunks(ch[b"W2Mesh"], 0, len(ch[b"W2Mesh"])))
            nv = len(wadtool._chunks(mesh[b"W2VrtPos"], 0, len(mesh[b"W2VrtPos"])))
            nn = len(wadtool._chunks(mesh[b"W2VrtNorm"], 0, len(mesh[b"W2VrtNorm"])))
            assert nv == nn
            for pc, pp in wadtool._chunks(mesh[b"W2Polys"], 0, len(mesh[b"W2Polys"])):
                k = 4 if pc == b"W2Uq2" else 3
                q2 = 0
                ids = []
                for _ in range(k):
                    v, q2 = wadtool._leb_u(pp, q2)
                    ids.append(v)
                shine, q2 = wadtool._leb_u(pp, q2)
                page, q2 = wadtool._leb_u(pp, q2)
                assert all(i < nv for i in ids) and page < len(tex_sizes)
                vals = struct.unpack_from("<%df" % (4 + 2 * k), pp, q2)
                w, h = tex_sizes[page]
                us, vs = vals[4::2], vals[5::2]
                assert min(us) >= 0 and max(us) <= w and min(vs) >= 0 and max(vs) <= h
                assert max(us) - min(us) <= 256 and max(vs) - min(vs) <= 256
    return count, tex_sizes


def preview(statics, out_dir):
    """Mesh JSON for the three.js preview: models laid out on a grid."""
    pos, uv, tix = [], [], []
    labels = []
    cols = 8
    statics = list(statics)
    for k, (sid, name, mesh, coll, note) in enumerate(statics):
        ox, oz = (k % cols) * 16.0, (k // cols) * 16.0
        lo, hi = mesh.bbox()
        labels.append([name, ox, oz, (lo / 512.0).tolist(), (hi / 512.0).tolist()])
        for idx, px, page, blend, dbl in mesh.f:
            ps = [np.array(mesh.v[i]) / 512.0 for i in idx]
            tri = [(0, 1, 2)] + ([(0, 2, 3)] if len(ps) == 4 else [])
            for a, b, c in tri:
                for j in (a, b, c):
                    pos.extend([ps[j][0] + ox, ps[j][1], ps[j][2] + oz])
                    uv.extend([px[j][0] / 512.0, px[j][1] / 512.0])
                tix.append(page)
    json.dump({"pos": pos, "uv": uv, "tix": tix, "lara": None, "labels": labels}, open(os.path.join(out_dir, "mesh.json"), "w"))
    tex.save(out_dir)


def main():
    statics = models.build_all()
    notes = "Coda di Volpe - decorazioni\n" + "\n".join("%d %s: %s" % (s[0], s[1], s[4]) for s in statics)
    size = wad2.write(OUT, tex.pages, [(s[0], s[1], s[2], s[3]) for s in statics], notes)
    n, sizes = verify(OUT, len(tex.pages))
    print("wad2: %d statics, %d textures %s, %.1f MB raw, file %.1f MB" % (n, len(sizes), sizes, size / 1e6, os.path.getsize(OUT) / 1e6))
    for s in statics:
        print("  %d %-26s faces %4d" % (s[0], s[1], len(s[2].f)))
    with open(os.path.join(ROOT, "assets", "wads", "CdV_Decorazioni.txt"), "w") as f:
        f.write(notes + "\n")
    if len(sys.argv) > 1:
        preview(statics, sys.argv[1])
    return statics


if __name__ == "__main__":
    main()
