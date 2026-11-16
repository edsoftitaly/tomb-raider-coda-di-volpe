"""Sommersa, the end (Ed, 16 Nov): two more boulders on the stairs of the way out (three lanes), ten bats under the
ceiling of the two side niches, and the four spirits of the twins in the gallery of the temple: two WRAITH1 (fire,
Castor) and two WRAITH2 (blue, Pollux). Both kinds die in water. The script (tools/lua_16nov.py) switches them on.

usage: sommersa_finale.py <Sommersa.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

BALL, BAT, WRAITH1, WRAITH2 = 383, 118, 268, 269


def mov(uid, typ, pos, rot, name, ocb=0):
    n = name.encode()
    # this level's objects are TeMovTen2 chunks (no four bytes of script id at the end, unlike TeMovTn3)
    return (b"TeMovTen2", P.prj2.leb(uid) + struct.pack("<3f", *pos) + struct.pack("<3f", rot, 0, 0) + b"\x7f"
            + struct.pack("<Ih", typ, ocb) + b"\0\0\0" + struct.pack("<3f", 1, 1, 1) + struct.pack("<i", len(n)) + n)


def main():
    src, dst = sys.argv[1:3]
    head, top = P.load(src)
    raw = P.raw_objects(src)
    names = set(o[5] for o in P.objects(src))
    assert "masso_fuga2" not in names, "already done"
    # the writer above must give back the boulder that is already there, byte for byte
    old = [(oc, op) for rn, oc, op in raw if b"masso_fuga" in op][0]
    assert mov(Reader(old[1]).leb(), BALL, (13824.0, 5120.0, 4608.0), 270.0, "masso_fuga") == old, "object layout changed"
    uid = [max(Reader(op).leb() for _, _, op in raw) + 1]

    def new(typ, pos, rot, name):
        uid[0] += 1
        return mov(uid[0] - 1, typ, pos, rot, name)

    fuga = [new(BALL, (13824.0, 5120.0, 3584.0), 270.0, "masso_fuga2"), new(BALL, (13824.0, 5120.0, 5632.0), 270.0, "masso_fuga3")]
    k = 0
    for cz, rot in ((2560.0, 0.0), (6656.0, 180.0)):                 # the two niches, south and north of the landing
        for dx, dz, dy in ((-280, -250, 0), (280, -250, 30), (0, 0, 60), (-280, 250, 20), (280, 250, 45)):
            k += 1
            fuga.append(new(BAT, (7680.0 + dx, 6546.0 - dy, cz + dz), rot, "pip_f%d" % k))
    galleria = [new(WRAITH1, (14848.0, 800.0, 9728.0), 0.0, "spirito_c1"), new(WRAITH1, (14848.0, 900.0, 2560.0), 0.0, "spirito_c2"),
                new(WRAITH2, (2560.0, 850.0, 2560.0), 0.0, "spirito_p1"), new(WRAITH2, (8704.0, 1000.0, 6656.0), 0.0, "spirito_p2")]
    rooms = dict(top)[b"TeRooms"]
    rooms = P.add_objects(rooms, "E_FUGA", fuga)
    rooms = P.add_objects(rooms, "U_GALLERIA", galleria)
    P.save(dst, head, [(c, rooms if c == b"TeRooms" else p) for c, p in top])
    print("added: 2 boulders, %d bats, 4 spirits" % k)


if __name__ == "__main__":
    main()
