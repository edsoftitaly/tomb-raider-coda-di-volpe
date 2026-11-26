"""The hatch of the box room (static 236 of CdV_Decorazioni, 'botola_legno'): a frame of four strips at y 0, open in
the middle, and behind it the board at y 31, drawn on one side only: from the frame side one looked through it. The
board (the one flat face as large as the whole hatch) gets the double sided flag, which Tomb Editor turns into a
second face when it compiles (Wad.cs, ConvertWadMesh). Nothing else changes, no face is added.
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
done = 0


def pack(items):
    return b"".join(W._chunk(c, p) for c, p in items) + b"\x00"


def polys(payload, V):
    global done
    xs = [v[0] for v in V]
    zs = [v[2] for v in V]
    full = (max(xs) - min(xs)) * (max(zs) - min(zs))
    out = []
    for c, p in W._chunks(payload, 0, len(payload)):
        if c == b"W2Uq2":
            o, idx = 0, []
            for _ in range(4):
                v, o = W._leb_u(p, o)
                idx.append(v)
            P = [V[i] for i in idx]
            flat = max(q[1] for q in P) - min(q[1] for q in P) < 1
            area = (max(q[0] for q in P) - min(q[0] for q in P)) * (max(q[2] for q in P) - min(q[2] for q in P))
            if flat and area > 0.95 * full and p[-2] == 0:
                p = p[:-2] + b"\x01" + p[-1:]
                done += 1
        out.append((c, p))
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
assert done == 1, done
body = pack(new_top)
with open(dst, "wb") as f:
    if ver & 0x80000000:
        data = zlib.compress(body, 9)
        f.write(b"WAD2" + struct.pack("<Ii", ver, len(data)) + data)
    else:
        f.write(b"WAD2" + struct.pack("<I", ver) + body)
print("faces made double sided:", done)
