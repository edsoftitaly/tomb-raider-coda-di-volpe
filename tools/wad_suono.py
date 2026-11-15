"""Change one animation sound of one moveable in a wad2 (uncompressed), in place in the bytes.
usage: wad_suono.py <in.wad2> <out.wad2> <moveable id> <old sound> <new sound>"""
import re
import sys

import wadtool

src, out = sys.argv[1:3]
mid, old, new = (int(v) for v in sys.argv[3:6])
raw = open(src, "rb").read()
done = 0
for m_id, pl in wadtool.moveables(wadtool.load(src)):
    if m_id != mid:
        continue
    assert raw.count(pl) == 1
    base = raw.index(pl)
    b = bytearray(pl)
    for m in re.finditer(rb"\x06W2Cmd2", pl):
        n, j = wadtool._leb_u(pl, m.end())
        kind, i = wadtool._leb_u(pl, j)
        _, i2 = wadtool._leb_u(pl, i)
        v, i3 = wadtool._leb_u(pl, i2)
        if kind == 5 and (v & 0xFFF) == old:
            enc = wadtool._leb_enc((v & ~0xFFF) | new)
            assert len(enc) == i3 - i2, "different length"
            b[i2:i3] = enc
            done += 1
    raw = raw[:base] + bytes(b) + raw[base + len(pl):]
open(out, "wb").write(raw)
print("moveable %d: sound %d -> %d in %d commands" % (mid, old, new, done))
