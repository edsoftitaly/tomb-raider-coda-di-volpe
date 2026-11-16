"""Marinello, the keeper's house: the search drawers (SEARCH_OBJECT2 of TEN_Search_Drawers.wad2) are only the two
drawers; the chest they slide out of is a second moveable of the same wad, ANIMATING1, to be put on the same spot.
It was missing, so the drawer came out of thin air. Adds it (same position and rotation).

  cassetti_mobile.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

SEARCH_OBJECT2, ANIMATING1 = 418, 1200
NAME = "cassetti_guardiano"


def main():
    src, dst = sys.argv[1:3]
    raw = P.raw_objects(src)
    ids, found = [], None
    for room, oc, op in raw:
        ids.append(Reader(op).leb())
        if oc in (b"TeMovTn3", b"TeMovTen2"):
            o, t = P.mov_type(op)
            if t == ANIMATING1:
                print("already there:", room)
                return
            if t == SEARCH_OBJECT2 and NAME.encode() in op:
                found = (room, oc, op)
    assert found, "drawers not found"
    room, oc, op = found
    r = Reader(op)
    r.leb()
    start = r.s.tell()
    o, _ = P.mov_type(op)
    body = bytearray(op[start:])
    o -= start
    body[o:o + 4] = struct.pack("<I", ANIMATING1)
    # name: int32 length + utf-8, after type (4), ocb (2), three flag bytes and the colour (12)
    q = o + 4 + 2 + 3 + 12
    n = struct.unpack_from("<i", body, q)[0]
    new_name = b"cassetti_mobile"
    body[q:q + 4 + n] = struct.pack("<i", len(new_name)) + new_name
    new = (oc, P.prj2.leb(max(ids) + 1) + bytes(body))
    head, top = P.load(src)
    top = [(c, P.add_objects(p, room, [new]) if c == b"TeRooms" else p) for c, p in top]
    P.save(dst, head, top)
    print("chest (ANIMATING1) added in", room, "id", max(ids) + 1)


if __name__ == "__main__":
    main()
