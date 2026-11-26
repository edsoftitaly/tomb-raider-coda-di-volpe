"""26 Nov, Marinello (after the reviews on TRCustoms and Aspide):
  - two slabs roof the Seal chamber (no dropping in from the walls)
  - iron rungs on the climbable wall of the secret roof
  - the net store: the block by the loft is RAISING_BLOCK2 (two sectors high) and the parapet of the loft goes from 11
    to 13 clicks. The crate alone (4 clicks) no longer reaches the loft; crate, then block, then loft.
usage: nov26_marinello.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P

src, dst = sys.argv[1:3]
head, top = P.load(src)
d = dict(top)
rooms = d[b"TeRooms"]
n = [0]


def block(room, cid, p):
    if cid in (b"TeMovTn3", b"TeMovTen2") and b"blocco_soppalco" in p:
        o, t = P.mov_type(p)
        assert t == 389, t
        n[0] += 1
        return p[:o] + struct.pack("<I", 390) + p[o + 4:]
    return p


rooms = P.map_objects(rooms, block)
assert n[0] == 1, n


def parapet(x, z, sec):
    if x == 8 and 18 <= z <= 22:
        assert sec["floor"] == [3328] * 4, sec["floor"]
        sec["floor"] = [3840] * 4
        if sec["fsplits"]:
            sec["fsplits"] = [[3840 if v == 3328 else v for v in sp] for sp in sec["fsplits"]]


rooms, k = P.edit_sectors(rooms, "T_02_01", parapet)
assert k == 5, k
# iron rungs (static 390, as in the last shaft) on the climbable wall of the roof with the Star: it was unmarked
import nov26_lib as L
tpl = L.template(rooms, "sta")
oid = L.max_oid(rooms) + 1
for i, y in enumerate((512.0, 2560.0, 3072.0)):
    rooms = P.add_objects(rooms, "T_02_01", [L.static_chunk(tpl, oid + i, 390, (11776.0, y, 11268.0), ry=180.0)])
# the Seal chamber was open to the sky: from the loft and the walls of the net store one could drop into it, take the
# Seal without the two levers and stay shut in. Two marble slabs (BRIDGE_FLAT of CdV_Oggetti) roof it at wall height.
mt = L.template(rooms, "mov")
for i, x in enumerate((2560.0, 3584.0)):
    rooms = P.add_objects(rooms, "T_02_01", [L.mov_chunk(mt, oid + 10 + i, 1340, (x, 4352.0, 26112.0), name="tetto_sigillo_%d" % (i + 1))])
P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
print("block -> RAISING_BLOCK2, parapet sectors raised:", k)
