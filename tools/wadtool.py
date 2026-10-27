"""Minimal Wad2 utilities: list objects, keep/rename moveable slots (e.g. PUZZLE_ITEM1 -> PUZZLE_ITEM5).

Wad2 = 'WAD2' + uint32 version (bit 31 = zlib payload) + chunk stream (see TombLib ChunkReader/Wad2Loader).
A chunk is LEB128(id length), id, LEB128(size), payload. Moveables live in W2Moveables/W2Moveable, whose
payload starts with LEB128(slot id) followed by sub-chunks; only that id is rewritten.

Usage: python3 wadtool.py list file.wad2
"""
import struct
import sys
import zlib


def _leb_u(d, p):
    r = s = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7F) << s
        s += 7
        if not b & 0x80:
            return r, p


def _leb_enc(v):
    """Signed LEB128 (TombLib LEB128.Write(long)); slot ids are positive so this is plain."""
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if (v == 0 and not b & 0x40) or (v == -1 and b & 0x40):
            out.append(b)
            return bytes(out)
        out.append(b | 0x80)


def _chunks(d, p, end):
    out = []
    while p < end:
        n, p = _leb_u(d, p)
        if n == 0:
            break
        cid = d[p:p + n]
        p += n
        size, p = _leb_u(d, p)
        out.append((cid, d[p:p + size]))
        p += size
    return out


def _chunk(cid, payload):
    return _leb_enc(len(cid)) + cid + _leb_enc(len(payload)) + payload


def load(path):
    d = open(path, "rb").read()
    assert d[:4] == b"WAD2", "not a wad2"
    ver = struct.unpack("<I", d[4:8])[0]
    if ver & 0x80000000:
        n = struct.unpack("<i", d[8:12])[0]
        d = zlib.decompress(d[12:12 + n])
    else:
        d = d[8:]
    return _chunks(d, 0, len(d))


def moveables(top):
    for cid, payload in top:
        if cid == b"W2Moveables":
            for c2, p2 in _chunks(payload, 0, len(payload)):
                if c2 == b"W2Moveable":
                    mid, _ = _leb_u(p2, 0)
                    yield mid, p2


def statics(top):
    for cid, payload in top:
        if cid == b"W2Statics":
            for c2, p2 in _chunks(payload, 0, len(payload)):
                if c2 in (b"W2Static", b"W2Static2"):
                    sid, _ = _leb_u(p2, 0)
                    yield sid


def remap(src, dst, mapping, keep_statics=True):
    """mapping: {old moveable id: new id or list of ids}; moveables not in mapping are dropped."""
    top = load(src)
    out = bytearray()
    for cid, payload in top:
        if cid == b"W2Moveables":
            body = bytearray()
            for c2, p2 in _chunks(payload, 0, len(payload)):
                if c2 != b"W2Moveable":
                    body += _chunk(c2, p2)
                    continue
                mid, p = _leb_u(p2, 0)
                if mid not in mapping:
                    continue
                targets = mapping[mid] if isinstance(mapping[mid], (list, tuple)) else [mapping[mid]]
                for new_id in targets:
                    body += _chunk(c2, _leb_enc(new_id) + p2[p:])
            body += b"\x00"
            out += _chunk(cid, bytes(body))
        elif cid == b"W2Statics" and not keep_statics:
            out += _chunk(cid, b"\x00")
        else:
            out += _chunk(cid, payload)
    out += b"\x00"
    data = zlib.compress(bytes(out), 9)
    with open(dst, "wb") as f:
        f.write(b"WAD2" + struct.pack("<Ii", 0x80000000, len(data)) + data)


if __name__ == "__main__":
    if sys.argv[1] == "list":
        top = load(sys.argv[2])
        print("moveables:", [m for m, _ in moveables(top)], "statics:", list(statics(top)))
