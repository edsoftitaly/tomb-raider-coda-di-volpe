"""Old TR4 .wad -> statics of a wad2 (TombEngine), after TombLib Tr4Wad.cs / Tr4WadOperations.cs.
Only the static meshes are taken (furniture packs); moveables, animations, sounds and sprites are skipped.
Usage: python3 wad_tr4.py out.wad2 first_id name=file.wad [name=file.wad ...]"""
import struct
import sys

import numpy as np

from decor import wad2


class M:
    def __init__(self):
        self.v, self.f = [], []


def read(path):
    d = open(path, "rb").read()
    p = [0]

    def u(fmt):
        vals = struct.unpack_from("<" + fmt, d, p[0])
        p[0] += struct.calcsize("<" + fmt)
        return vals if len(vals) > 1 else vals[0]

    version = u("i")
    texs = [u("BBHbBbB") for _ in range(u("I"))]            # x, y, page, flipX, w, flipY, h
    nbytes = u("I")
    raw = np.frombuffer(d, np.uint8, nbytes, p[0]).reshape(-1, 256, 3)
    p[0] += nbytes
    pages = []
    for k in range(raw.shape[0] // 256):
        rgb = raw[k * 256:(k + 1) * 256]
        a = np.where((rgb[..., 0] == 255) & (rgb[..., 1] == 0) & (rgb[..., 2] == 255), 0, 255).astype(np.uint8)
        pages.append(np.dstack([rgb, a]))
    pointers = [u("I") for _ in range(u("I"))]
    total = u("I") * 2
    start = p[0]
    meshes = {}
    while p[0] - start < total:
        off = p[0] - start
        u("hhhHH")
        verts = [u("hhh") for _ in range(u("H"))]
        nn = u("h")
        p[0] += (nn * 6 if nn > 0 else -nn * 2)
        polys, quads = [], 0
        for _ in range(u("H")):
            shape = u("H")
            idx = list(u("HHH")) + ([u("H")] if shape == 9 else [])
            tex, attr, _unk = u("HBB")
            quads += shape == 9
            polys.append((shape, idx, tex, attr))
        if quads % 2:
            p[0] += 2
        meshes[off] = (verts, polys)
    for size in (40, 6, 8, 2, 4, 2, 18):                     # animations, changes, dispatches, commands, links, frames, moveables
        n = u("I")
        p[0] += n * size
    statics = []
    for _ in range(u("I")):
        oid, ptr = u("IH")
        box = u("12h")
        u("H")
        statics.append((oid, meshes[pointers[ptr]], box[6:]))
    return version, texs, pages, statics


def convert(texs, mesh, page0):
    verts, polys = mesh
    m = M()
    m.v = [[float(x), float(-y), float(z)] for x, y, z in verts]
    for shape, idx, tex, attr in polys:
        if shape == 8:
            tid = tex & 0xFFF
        else:
            tid = tex if tex <= 0x7FFF else 0xFFFF - tex
        x, y, page, _fx, w, _fy, h = texs[tid]
        nw, ne, se, sw = (x + 0.5, y + 0.5), (x + w + 0.5, y + 0.5), (x + w + 0.5, y + h + 0.5), (x + 0.5, y + h + 0.5)
        flipped = (tex >> 15) & 1
        if shape == 9:
            uv = [ne, nw, sw, se] if flipped else [nw, ne, se, sw]
        else:
            tri = {0: (nw, ne, sw), 2: (ne, se, nw), 4: (se, sw, ne), 6: (sw, nw, se)}
            trf = {0: (ne, nw, se), 2: (nw, sw, ne), 4: (sw, se, nw), 6: (se, ne, sw)}
            uv = list((trf if flipped else tri)[(tex >> 12) & 7])
        m.f.append((tuple(idx), uv, page0 + page, 2 if attr & 1 else 0, False))
    return m


def main(out, first_id, items):
    pages, statics, notes, sid = [], [], [], first_id
    for item in items:
        name, path = item.split("=", 1)
        version, texs, pg, sts = read(path)
        for k, (oid, mesh, cb) in enumerate(sts):
            m = convert(texs, mesh, len(pages))
            coll = ((cb[0], -cb[3], cb[4]), (cb[1], -cb[2], cb[5]))
            lo = [min(c[i] for c in coll) for i in range(3)]
            hi = [max(c[i] for c in coll) for i in range(3)]
            n = name if len(sts) == 1 else "%s_%d" % (name, k + 1)
            P = np.array(m.v)
            size = (P.max(axis=0) - P.min(axis=0)) / 512.0
            print("%d %-22s old slot %2d  %3d faces  %.2f x %.2f x %.2f m  base y %.2f" % (sid, n, oid, len(m.f), size[0], size[1], size[2], P[:, 1].min() / 512))
            statics.append((sid, n, m, None if lo == hi else (tuple(lo), tuple(hi))))
            notes.append("%d %s (%s, slot %d)" % (sid, n, path.split("/")[-1], oid))
            sid += 1
        pages += pg
    wad2.write(out, pages, statics, "Belle Epoque Collection (Laras Levelbase Stuff), convertita da .wad\n" + "\n".join(notes))
    return notes


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3:])
