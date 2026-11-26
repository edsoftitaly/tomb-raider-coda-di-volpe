"""A copy of a .wad2 with only the wanted statics and moveables, and the textures nobody uses any more emptied (a 4x4
texture in their place: the numbering of the textures does not change, so no mesh has to be touched).
  wad_slim.py <in.wad2> <out.wad2> <static ids, comma|-> <moveable ids, comma|->     ('-' keeps them all)"""
import re
import struct
import sys
import zlib

import wadtool as W

POLY = re.compile(rb"\x05W2(?:Uq2|Tr2)")


def used_textures(payload):
    out = set()
    for m in POLY.finditer(payload):
        quad = payload[m.start() + 3:m.start() + 6] == b"Uq2"
        q = m.end()
        size, q = W._leb_u(payload, q)
        end = q + size
        try:
            for _ in range(4 if quad else 3):
                _, q = W._leb_u(payload, q)
            _, q = W._leb_u(payload, q)
            t, q = W._leb_u(payload, q)
            if q <= end:
                out.add(t)
        except Exception:
            pass
    return out


def slim(src, dst, keep_s=None, keep_m=None):
    raw = open(src, "rb").read()
    ver = struct.unpack("<I", raw[4:8])[0]
    top = W.load(src)
    used, new = set(), []
    stats = {}
    for cid, payload in top:
        if cid in (b"W2Statics", b"W2Moveables"):
            keep = keep_s if cid == b"W2Statics" else keep_m
            kids = []
            for c2, p2 in W._chunks(payload, 0, len(payload)):
                i = W._leb_u(p2, 0)[0]
                if keep is None or i in keep:
                    kids.append((c2, p2))
                    used |= used_textures(p2)
            stats[cid] = len(kids)
            payload = b"".join(W._chunk(c, p) for c, p in kids) + b"\x00"
        new.append((cid, payload))
    out = []
    blank = 0
    for cid, payload in new:
        if cid == b"W2Textures":
            tx = []
            for k, (c2, p2) in enumerate(W._chunks(payload, 0, len(payload))):
                if k not in used:
                    w, q = W._leb_u(p2, 0)
                    h, q = W._leb_u(p2, q)
                    sub = W._chunks(p2, q, len(p2))
                    body = W._leb(4) + W._leb(4) if hasattr(W, "_leb") else bytes([4, 4])
                    for c3, p3 in sub:
                        body += W._chunk(c3, bytes(64) if c3 == b"W2TxtData" else p3)
                    p2 = body + b"\x00"
                    blank += 1
                tx.append((c2, p2))
            stats["textures"] = (len(tx), blank)
            payload = b"".join(W._chunk(c, p) for c, p in tx) + b"\x00"
        out.append((cid, payload))
    body = b"".join(W._chunk(c, p) for c, p in out) + b"\x00"
    with open(dst, "wb") as f:
        if ver & 0x80000000:
            data = zlib.compress(body, 9)
            f.write(b"WAD2" + struct.pack("<Ii", ver, len(data)) + data)
        else:
            f.write(b"WAD2" + struct.pack("<I", ver) + body)
    return stats


if __name__ == "__main__":
    a = sys.argv
    ks = None if a[3] == "-" else {int(v) for v in a[3].split(",") if v}
    km = None if a[4] == "-" else {int(v) for v in a[4].split(",") if v}
    print(slim(a[1], a[2], ks, km))
