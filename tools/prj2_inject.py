"""Add object chunks to one room of a hand-edited .prj2 without touching anything else.

inject(edited_path, room_name, [chunk bytes without oid...], out_path): every new object gets an id above the
file's highest, the room's TeObjects chunk and all its ancestors get their sizes rewritten.
"""
import struct
import sys

from prj2_splice import Prj2, enc


def rebuild(E, repl):
    """repl: {start: (end, new_bytes)} spans of E.d to replace; rewrites the sizes of enclosing chunks."""
    encl = [c for c in E.heads if any(c["ps"] <= h and e <= c["pe"] and not (c["h"] == h) for h, (e, _) in repl.items())]

    def emit(a, b):
        out = bytearray()
        p = a
        items = [("c", c["h"], c) for c in encl if a <= c["h"] and c["pe"] <= b and not (c["h"] == a - 0)]
        items += [("r", h, v) for h, v in repl.items() if a <= h and v[0] <= b]
        items.sort(key=lambda t: (t[1], 0 if t[0] == "r" else 1))
        for kind, st, it in items:
            if st < p:
                continue
            out += E.d[p:st]
            if kind == "r":
                out += it[1]
                p = it[0]
            else:
                child = emit(it["ps"], it["pe"])
                out += E.d[it["h"]:it["sz0"]] + enc(len(child)) + child
                p = it["pe"]
        out += E.d[p:b]
        return bytes(out)
    return emit(0, len(E.d))


def max_oid(E):
    m = 0
    for r in E.rooms():
        for o in E.object_chunks(r["h"], r["pe"]):
            m = max(m, E.leb(o["ps"])[0])
    return m


def inject(E, room_name, objects, patches=()):
    """objects: list of (chunk id bytes, payload after the oid). patches: [(abs offset, bytes)] same-size edits."""
    d = bytearray(E.d)
    for off, b in patches:
        d[off:off + len(b)] = b
    E.d = bytes(d)
    room = next(r for r in E.rooms() if r["name"] == room_name)
    obj = next(c for c in E.heads if c["id"] == b"TeObjects" and room["h"] <= c["h"] < room["pe"])
    oid = max_oid(E) + 1
    extra = bytearray()
    for cid, payload in objects:
        body = enc(oid) + payload
        extra += enc(len(cid)) + cid + enc(len(body)) + body
        oid += 1
    body = E.d[obj["ps"]:obj["pe"]]
    assert body[-1] == 0, "TeObjects must end with the 0 terminator"
    newbody = body[:-1] + bytes(extra) + b"\x00"
    newchunk = E.d[obj["h"]:obj["sz0"]] + enc(len(newbody)) + newbody
    return rebuild(E, {obj["h"]: (obj["pe"], newchunk)})
