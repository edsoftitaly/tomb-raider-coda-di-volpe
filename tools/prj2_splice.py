"""Splice rooms from a generated .prj2 into a hand-edited one.

Usage: python3 prj2_splice.py edited.prj2 generated.prj2 out.prj2 PREFIX[,PREFIX...]

Every TeRoom of `edited` whose name starts with one of the prefixes is replaced by the room with the same
name (and the same index) from `generated`; everything else of `edited` (other rooms, objects, texture
and wad lists, settings) is kept byte for byte. Object ids of the spliced rooms are moved above the
highest id of `edited`, so they never clash. All enclosing chunk sizes are rewritten.
"""
import re
import sys


class Prj2:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        self.heads = self._heads()

    def leb(self, p):
        d = self.d
        r = s = 0
        while True:
            b = d[p]
            p += 1
            r |= (b & 0x7F) << s
            s += 7
            if not b & 0x80:
                if b & 0x40:
                    r -= 1 << s
                return r, p

    def _heads(self):
        out = []
        for m in re.finditer(rb"Te[A-Za-z0-9]{1,40}", self.d):
            s = m.start()
            if s == 0 or self.d[s - 1] != len(m.group()):
                continue
            try:
                size, ps = self.leb(m.end())
            except IndexError:
                continue
            if size < 0 or ps + size > len(self.d):
                continue
            out.append(dict(h=s - 1, id=m.group(), sz0=m.end(), ps=ps, pe=ps + size))
        return out

    def rooms(self):
        rs = [c for c in self.heads if c["id"] == b"TeRoom"]
        for r in rs:
            nm = next(c for c in self.heads if c["id"] == b"TeName" and r["ps"] <= c["h"] < r["pe"])
            r["name"] = self.d[nm["ps"]:nm["pe"]].decode()
        return rs

    def object_chunks(self, lo, hi):
        """Object chunks (direct children of TeObjects) inside [lo, hi)."""
        out = []
        for ob in self.heads:
            if ob["id"] == b"TeObjects" and lo <= ob["h"] < hi:
                p = ob["ps"]
                while p < ob["pe"]:
                    n, q = self.leb(p)
                    if n == 0:
                        break
                    cid = self.d[q:q + n]
                    q += n
                    size, q2 = self.leb(q)
                    out.append(dict(h=p, id=cid, sz0=q, ps=q2, pe=q2 + size))
                    p = q2 + size
        return out


def enc(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if (v == 0 and not b & 0x40) or (v == -1 and b & 0x40):
            out.append(b)
            return bytes(out)
        out.append(b | 0x80)


def rewrite_room(src, room, shift):
    """Bytes of `room` from `src` with every object id + shift (sizes of its chunks rewritten)."""
    objs = src.object_chunks(room["h"], room["pe"])
    obj_parents = [c for c in src.heads if c["id"] == b"TeObjects" and room["h"] <= c["h"] < room["pe"]]

    def emit(a, b, top):
        out = bytearray()
        p = a
        items = sorted([c for c in top if a <= c["h"] and c["pe"] <= b], key=lambda c: c["h"])
        for c in items:
            if c["h"] < p:
                continue
            out += src.d[p:c["h"]]
            if c in objs:
                oid, q = src.leb(c["ps"])
                body = enc(oid + shift) + src.d[q:c["pe"]]
            else:
                body = emit(c["ps"], c["pe"], [o for o in objs if c["ps"] <= o["h"] < c["pe"]])
            out += src.d[c["h"]:c["sz0"]] + enc(len(body)) + body
            p = c["pe"]
        out += src.d[p:b]
        return bytes(out)

    # the room chunk itself, with its TeObjects children rebuilt
    body = emit(room["ps"], room["pe"], obj_parents)
    return src.d[room["h"]:room["sz0"]] + enc(len(body)) + body


def main():
    ed, gen, out_path, prefixes = sys.argv[1], sys.argv[2], sys.argv[3], tuple(sys.argv[4].split(","))
    E, Gn = Prj2(ed), Prj2(gen)
    er, gr = E.rooms(), Gn.rooms()
    assert [r["name"] for r in er] == [r["name"] for r in gr], "room lists differ"
    max_oid = 0
    for r in er:
        for o in E.object_chunks(r["h"], r["pe"]):
            max_oid = max(max_oid, E.leb(o["ps"])[0])
    min_gen = min((Gn.leb(o["ps"])[0] for r in gr for o in Gn.object_chunks(r["h"], r["pe"])), default=0)
    shift = max_oid + 1 - min_gen + 1000
    repl = {}
    for a, b in zip(er, gr):
        if a["name"].startswith(prefixes):
            repl[a["h"]] = (a["pe"], rewrite_room(Gn, b, shift))
    # rebuild edited file: replace room spans, fix the sizes of the chunks enclosing them
    encl = [c for c in E.heads if c["id"] != b"TeRoom" and any(c["ps"] <= h and e <= c["pe"] for h, (e, _) in repl.items())]

    def emit(a, b):
        out = bytearray()
        p = a
        items = [("c", c["h"], c) for c in encl if a <= c["h"] and c["pe"] <= b]
        items += [("r", h, v) for h, v in repl.items() if a <= h and v[0] <= b]
        items.sort(key=lambda t: t[1])
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

    new = emit(0, len(E.d))
    open(out_path, "wb").write(new)
    print("replaced %d rooms, id shift %d, %d -> %d bytes" % (len(repl), shift, len(E.d), len(new)))


if __name__ == "__main__":
    main()
