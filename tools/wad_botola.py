"""The hatch of the box room (static 236 of CdV_Decorazioni, 'botola_legno') had its two large faces on one side only:
from the roof one looked through it. Every face lying flat gets a twin turned the other way.
usage: wad_botola.py <in.wad2> <out.wad2> [static id]"""
import struct
import sys
import zlib

import wadtool as W

src, dst = sys.argv[1:3]
SID = int(sys.argv[3]) if len(sys.argv) > 3 else 236
raw = open(src, "rb").read()
ver = struct.unpack("<I", raw[4:8])[0]
top = W.load(src)
added = 0


def uleb(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v == 0:
            out.append(b)
            return bytes(out)
        out.append(b | 0x80)


def pack(items):
    return b"".join(W._chunk(c, p) for c, p in items) + b"\x00"


def polys(payload, V):
    global added
    out = []
    for c, p in W._chunks(payload, 0, len(payload)):
        out.append((c, p))
        if c != b"W2Uq2":
            continue
        o, idx = 0, []
        for _ in range(4):
            v, o = W._leb_u(p, o)
            idx.append(v)
        o_idx = o
        _, o = W._leb_u(p, o)
        _, o = W._leb_u(p, o)
        a, b, d = V[idx[0]], V[idx[1]], V[idx[2]]
        u = [b[j] - a[j] for j in range(3)]
        w = [d[j] - a[j] for j in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        if abs(n[1]) <= max(abs(n[0]), abs(n[2])):
            continue
        # after the texture index: the parent area (4 floats), then the four texture corners (8 floats)
        uv = [p[o + 16 + 8 * k:o + 16 + 8 * k + 8] for k in range(4)]
        new = b"".join(uleb(i) for i in reversed(idx)) + p[o_idx:o + 16] + b"".join(reversed(uv)) + p[o + 48:]
        out.append((c, new))
        added += 1
    return pack(out)


new_top = []
for cid, payload in top:
    if cid == b"W2Statics":
        kids = []
        for c2, p2 in W._chunks(payload, 0, len(payload)):
            i, q = W._leb_u(p2, 0)
            if i == SID:
                _, q = W._leb_u(p2, q)
                sub = []
                for c3, p3 in W._chunks(p2, q, len(p2)):
                    if c3 == b"W2Mesh":
                        md = W._chunks(p3, 0, len(p3))
                        V = [struct.unpack("<3f", pp[:12]) for cc, pp in W._chunks(dict(md)[b"W2VrtPos"], 0, len(dict(md)[b"W2VrtPos"]))]
                        p3 = pack([(c4, polys(p4, V) if c4 == b"W2Polys" else p4) for c4, p4 in md])
                    sub.append((c3, p3))
                p2 = p2[:q] + pack(sub)
            kids.append((c2, p2))
        payload = pack(kids)
    new_top.append((cid, payload))
body = pack(new_top)
with open(dst, "wb") as f:
    if ver & 0x80000000:
        data = zlib.compress(body, 9)
        f.write(b"WAD2" + struct.pack("<Ii", ver, len(data)) + data)
    else:
        f.write(b"WAD2" + struct.pack("<I", ver) + body)
print("faces added:", added)
