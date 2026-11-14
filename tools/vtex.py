"""Reads a Source 2 .vtex_c texture (the form of the CC0 ambientCG pack github.com/PatrickJnr/cc0-texture-pack)
and returns a PIL image of a chosen mip. Formats: DXT1, DXT5, RGBA8888, BC7, with LZ4-compressed mips."""
import struct
import sys

import lz4.block
import texture2ddecoder as t2d
from PIL import Image


def read(path, want=1024):
    b = open(path, "rb").read()
    block_off, nblocks = struct.unpack_from("<II", b, 8)
    pos = 8 + block_off
    data = None
    for i in range(nblocks):
        kind = b[pos:pos + 4]
        off, size = struct.unpack_from("<II", b, pos + 4)
        if kind == b"DATA":
            data = (pos + 4 + off, size)
        pos += 12
    d0, dsize = data
    ver, flags = struct.unpack_from("<HH", b, d0)
    w, h, depth, fmt, mips = struct.unpack_from("<HHHBB", b, d0 + 20)
    extra_off, extra_n = struct.unpack_from("<II", b, d0 + 32)
    comp = None
    p = d0 + 32 + extra_off
    for i in range(extra_n):
        typ, off, size = struct.unpack_from("<III", b, p)
        if typ == 4:       # compressed mip sizes
            q = p + 4 + off
            _, _, n = struct.unpack_from("<III", b, q)
            comp = list(struct.unpack_from("<%dI" % n, b, q + 12))
        p += 12
    bpb = {1: 8, 2: 16, 20: 16}

    def raw_size(lv):
        ww, hh = max(1, w >> lv), max(1, h >> lv)
        if fmt == 4:
            return ww * hh * 4
        return max(1, (ww + 3) // 4) * max(1, (hh + 3) // 4) * bpb[fmt]
    # mips are stored smallest first, at the end of the file
    sizes = [(comp[lv] if comp else raw_size(lv)) for lv in range(mips)]
    start = len(b) - sum(sizes)
    offs = {}
    for lv in range(mips - 1, -1, -1):
        offs[lv] = start
        start += sizes[lv]
    lv = 0
    while lv + 1 < mips and max(w, h) >> lv > want:
        lv += 1
    blob = b[offs[lv]:offs[lv] + sizes[lv]]
    if comp and sizes[lv] != raw_size(lv):
        blob = lz4.block.decompress(blob, uncompressed_size=raw_size(lv))
    ww, hh = max(1, w >> lv), max(1, h >> lv)
    if fmt == 4:
        return Image.frombytes("RGBA", (ww, hh), blob)
    dec = {1: t2d.decode_bc1, 2: t2d.decode_bc3, 20: t2d.decode_bc7}[fmt](blob, ww, hh)
    return Image.frombytes("RGBA", (ww, hh), dec, "raw", "BGRA")


if __name__ == "__main__":
    read(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else 1024).convert("RGB").save(sys.argv[2], quality=92)
