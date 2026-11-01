"""Three-way merge of the statics of some rooms: keep the hand edits made in Tomb Editor, take everything else
from a new generation.

Usage: python3 prj2_merge3.py old_gen.prj2 edited.prj2 new_gen.prj2 out.prj2 PREFIX[,PREFIX...]

old_gen = the generated file the edits started from (rebuild it from the commit that produced it),
edited  = the hand-edited file (Tomb Editor saves statics as TeStaTn3, the generator as TeStaTen2),
new_gen = the new generation (its rooms, sectors, portals, lights and moveables are kept as they are).

For every room of new_gen whose name starts with a prefix (the rooms must have the same name in all three
files and the same sectors in old_gen and edited - checked), the statics become
    edited - (old_gen - new_gen) + (new_gen - old_gen)
i.e. what Ed added, moved or removed stays so, what the generator changed since old_gen comes in. Statics are
matched by (type, position, rotation, scale). Statics taken from `edited` get fresh object ids. Every
other room of new_gen is left byte for byte. The project settings (TeSettings: wad and texture lists, editor
options) are taken from `edited`, so wads Ed loaded by hand stay loaded.
"""
import struct
import sys
from collections import Counter

from prj2_inject import max_oid
from prj2_splice import Prj2, enc


def rebuild_tree(P, repl, parents):
    """Replace spans {start: (end, bytes)} of P.d; `parents` = the chunks that enclose them (known exactly,
    not guessed: the heuristic header scan can see false headers in binary data), whose sizes get rewritten."""
    def emit(a, b):
        out = bytearray()
        p = a
        items = [("r", h, v) for h, v in repl.items() if a <= h and v[0] <= b]
        items += [("c", c["h"], c) for c in parents if a <= c["h"] and c["pe"] <= b and (c["h"], c["pe"]) != (a, b)]
        items.sort(key=lambda t: (t[1], 0 if t[0] == "c" else 1))
        for kind, st, it in items:
            if st < p:
                continue
            out += P.d[p:st]
            if kind == "r":
                out += it[1]
                p = it[0]
            else:
                child = emit(it["ps"], it["pe"])
                out += P.d[it["h"]:it["sz0"]] + enc(len(child)) + child
                p = it["pe"]
        out += P.d[p:b]
        return bytes(out)
    return emit(0, len(P.d))

STATIC_IDS = (b"TeStaTen2", b"TeStaTn3")


def statics(P, room):
    """[(key, chunk id, body after the oid)] of the static chunks of a room."""
    out = []
    for o in P.object_chunks(room["h"], room["pe"]):
        if o["id"] not in STATIC_IDS:
            continue
        _, q = P.leb(o["ps"])
        body = P.d[q:o["pe"]]
        x, y, z, ry, _, _, sc = struct.unpack_from("<7f", body, 0)
        neg, q2 = P.leb(q + 28)
        t = struct.unpack_from("<I", P.d, q2)[0]
        key = (t, round(x), round(y), round(z), round(ry % 360.0, 1) % 360.0, round(sc, 2))
        out.append((key, o["id"], body))
    return out


def merge(old_path, ed_path, new_path, out_path, prefixes):
    O, Ed, N = Prj2(old_path), Prj2(ed_path), Prj2(new_path)
    orooms = {r["name"]: r for r in O.rooms()}
    erooms = {r["name"]: r for r in Ed.rooms()}
    oid = max(max_oid(N), max_oid(Ed)) + 1
    repl = {}
    parents = [c for c in N.heads if c["id"] == b"TeRooms"][:1]
    report = []
    for room in N.rooms():
        name = room["name"]
        if not name.startswith(prefixes):
            continue
        so = statics(O, orooms[name])
        se = statics(Ed, erooms[name])
        sn = statics(N, room)
        co, cn = Counter(k for k, _, _ in so), Counter(k for k, _, _ in sn)
        removed_by_gen = co - cn
        added_by_gen = cn - co
        keep = []
        drop = Counter(removed_by_gen)
        for k, cid, body in se:
            if drop[k] > 0:
                drop[k] -= 1
                continue
            keep.append((cid, body))
        add = Counter(added_by_gen)
        for k, cid, body in sn:
            if add[k] > 0:
                add[k] -= 1
                keep.append((cid, body))
        ce = Counter(k for k, _, _ in se)
        report.append("%s: Ed %+d statics vs old generation, generator -%d +%d, result %d" % (
            name, sum(ce.values()) - sum(co.values()), sum(removed_by_gen.values()), sum(added_by_gen.values()), len(keep)))
        # rebuild the room's TeObjects: every non-static object of the new generation, then the merged statics
        obj = next(c for c in N.heads if c["id"] == b"TeObjects" and room["h"] <= c["h"] < room["pe"])
        parents.append(room)
        body = bytearray()
        for o in N.object_chunks(room["h"], room["pe"]):
            if o["id"] in STATIC_IDS:
                continue
            body += N.d[o["h"]:o["pe"]]
        for cid, b in keep:
            payload = enc(oid) + b
            oid += 1
            body += enc(len(cid)) + cid + enc(len(payload)) + payload
        body += b"\x00"
        repl[obj["h"]] = (obj["pe"], N.d[obj["h"]:obj["sz0"]] + enc(len(body)) + bytes(body))
    ns = [c for c in N.heads if c["id"] == b"TeSettings"]
    es = [c for c in Ed.heads if c["id"] == b"TeSettings"]
    if ns and es:
        repl[ns[0]["h"]] = (ns[0]["pe"], Ed.d[es[0]["h"]:es[0]["pe"]])
        report.append("TeSettings from the edited file")
    data = rebuild_tree(N, repl, parents)
    with open(out_path, "wb") as f:
        f.write(data)
    return report


if __name__ == "__main__":
    for line in merge(*sys.argv[1:5], tuple(sys.argv[5].split(","))):
        print(line)
