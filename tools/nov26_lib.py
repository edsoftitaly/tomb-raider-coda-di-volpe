"""Helpers of 26 Nov for patching a .prj2 in place: new statics and moveables copied from one already in the level."""
import struct

import prj2
import prj2_mesh as M
import prj2_patch as P
from prj2_check import Reader


def _leb_at(p, o=0):
    r = Reader(p[o:])
    v = r.leb()
    return v, o + r.s.tell()


def max_oid(rooms_payload):
    best = [0]

    def see(room, cid, p):
        if cid.startswith(b"Te") and len(p) > 2:
            try:
                best[0] = max(best[0], _leb_at(p)[0])
            except Exception:
                pass
        return p
    P.map_objects(rooms_payload, see)
    return best[0]


def template(rooms_payload, kind):
    """payload of one existing static ('sta') or moveable ('mov') without a script name"""
    found = []

    def see(room, cid, p):
        if not found:
            if kind == "sta" and cid == b"TeStaTn3":
                found.append((cid, p))
            if kind == "mov" and cid == b"TeMovTn3":
                found.append((cid, p))
        return p
    P.map_objects(rooms_payload, see)
    return found[0]


def static_chunk(tpl, oid, type_id, pos, ry=0.0, scale=1.0):
    cid, p = tpl
    _, o = _leb_at(p)
    body = prj2.leb(oid) + struct.pack("<7f", pos[0], pos[1], pos[2], ry, 0.0, 0.0, scale)
    rest = p[o + 28:]
    _, o2 = _leb_at(rest)
    rest2 = rest[o2 + 4:]                      # after the type
    n = struct.unpack("<i", rest2[14:18])[0]
    tail = rest2[18 + n:]
    return (cid, body + rest[:o2] + struct.pack("<I", type_id) + rest2[:14] + struct.pack("<i", 0) + tail)


def mov_chunk(tpl, oid, type_id, pos, ry=0.0, name="", ocb=0):
    cid, p = tpl
    _, o = _leb_at(p)
    body = prj2.leb(oid) + struct.pack("<6f", pos[0], pos[1], pos[2], ry, 0.0, 0.0)
    rest = p[o + 24:]
    _, o2 = _leb_at(rest)
    rest2 = rest[o2 + 4:]
    n = struct.unpack("<i", rest2[2 + 3 + 12:2 + 3 + 12 + 4])[0]
    tail = rest2[2 + 3 + 12 + 4 + n:]
    nm = name.encode("utf-8")
    return (cid, body + rest[:o2] + struct.pack("<I", type_id) + struct.pack("<h", ocb) + rest2[2:17] + struct.pack("<i", len(nm)) + nm + tail)


def room_of(rooms, X, Z, y=None):
    """(room dict, local x, local z) of the interior sector over a world column; with y, the room whose span holds it"""
    best = None
    for r in rooms:
        px, py, pz = r["pos"]
        lx, lz = X - int(px), Z - int(pz)
        if 1 <= lx <= r["nx"] - 2 and 1 <= lz <= r["nz"] - 2 and (lx, lz) in r["sectors"]:
            if any(r.get("name", "").endswith(a) for a in ("_PIENO", "_ASCIUTTO", "_BUIO")):
                continue
            s = r["sectors"][(lx, lz)]
            f = max(s.get("floor", [0])) + py
            if y is None or abs(f - y) < 600:
                if best is None or (y is not None and abs(f - y) < abs(best[3] - y)):
                    best = (r, lx, lz, f)
    return best
