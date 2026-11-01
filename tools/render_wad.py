"""Render static meshes straight from a .wad2 (what Tomb Editor loads): python3 render_wad.py file.wad2 id[,id] out_prefix"""
import json, os, struct, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wadtool

D = "/home/claude/vrender"


def load(path):
    top = wadtool.load(path)
    pages, stat = [], {}
    for cid, p in top:
        if cid == b"W2Textures":
            for c2, p2 in wadtool._chunks(p, 0, len(p)):
                w, q = wadtool._leb_u(p2, 0)
                h, q = wadtool._leb_u(p2, q)
                data = dict(wadtool._chunks(p2, q, len(p2)))[b"W2TxtData"]
                a = np.frombuffer(data, np.uint8).reshape(h, w, 4)[..., [2, 1, 0, 3]]
                pages.append(a)
        if cid == b"W2Statics":
            for c2, p2 in wadtool._chunks(p, 0, len(p)):
                sid, q = wadtool._leb_u(p2, 0)
                fl, q = wadtool._leb_u(p2, q)
                ch = dict(wadtool._chunks(p2, q, len(p2)))
                mesh = dict(wadtool._chunks(ch[b"W2Mesh"], 0, len(ch[b"W2Mesh"])))
                V = [struct.unpack_from("<3f", pp, 0) for _, pp in wadtool._chunks(mesh[b"W2VrtPos"], 0, len(mesh[b"W2VrtPos"]))]
                polys = []
                for pc, pp in wadtool._chunks(mesh[b"W2Polys"], 0, len(mesh[b"W2Polys"])):
                    k = 4 if pc == b"W2Uq2" else 3
                    q2 = 0
                    ids = []
                    for _ in range(k):
                        v, q2 = wadtool._leb_u(pp, q2)
                        ids.append(v)
                    shine, q2 = wadtool._leb_u(pp, q2)
                    page, q2 = wadtool._leb_u(pp, q2)
                    vals = struct.unpack_from("<%df" % (4 + 2 * k), pp, q2)
                    polys.append((ids, page, list(zip(vals[4::2], vals[5::2]))))
                stat[sid] = (V, polys)
    return pages, stat


def main():
    path, ids, out = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], sys.argv[3]
    pages, stat = load(path)
    for i, pg in enumerate(pages):
        Image.fromarray(pg).save(os.path.join(D, "decor_%d.png" % i))
    names = []
    for sid in ids:
        V, polys = stat[sid]
        pos, uv, tix = [], [], []
        for ids_, page, uvs in polys:
            ps = [np.array(V[i]) / 512.0 for i in ids_]
            tris = [(0, 1, 2)] + ([(0, 2, 3)] if len(ps) == 4 else [])
            for a, b, c in tris:
                for j in (c, b, a):
                    pos.extend(ps[j].tolist())
                    uv.extend([uvs[j][0] / 512.0, uvs[j][1] / 512.0])
                tix.append(page)
        order = sorted(range(len(tix)), key=lambda i: tix[i])
        json.dump({"pos": [v for i in order for v in pos[i * 9:(i + 1) * 9]], "uv": [v for i in order for v in uv[i * 6:(i + 1) * 6]],
                   "tix": [tix[i] for i in order], "npages": len(pages)}, open(os.path.join(D, "mesh.json"), "w"))
        P = np.array(V) / 512.0
        lo, hi = P.min(0), P.max(0)
        L, H = hi[2] - lo[2], hi[1]
        d = max(L, H * 1.6) * 1.3
        views = {"w%d_a" % sid: [d * 0.7, H * 0.8, d * 0.7, 0, H * 0.4, 0], "w%d_b" % sid: [-d * 0.75, H * 0.8, -d * 0.7, 0, H * 0.4, 0],
                 "w%d_c" % sid: [-d * 0.6, H * 0.9, d * 0.8, 0, H * 0.4, 0], "w%d_d" % sid: [0.3, H * 0.75, d * 0.9, 0, H * 0.5, 0]}
        subprocess.run(["node", "shot.js", json.dumps(views)], cwd=D, capture_output=True, text=True)
        for n in views:
            os.replace(os.path.join(D, n + ".png"), out + n + ".png")
        names += list(views)
    ims = [Image.open(out + n + ".png").resize((480, 270)) for n in names]
    cols = 4
    sheet = Image.new("RGB", (480 * cols, 270 * ((len(ims) + cols - 1) // cols)))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
    sheet.save(out + "wadsheet.png")
    print(out + "wadsheet.png")


main()
