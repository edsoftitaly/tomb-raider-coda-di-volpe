"""Small readers shared by the audits of 26 Nov (the tools of 20 Nov were lost with the old container)."""
import os, re, struct
import prj2_patch as P, wadtool as W
WADS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wads")
LEVELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "levels")


def level_wads(prj):
    raw = open(prj, "rb").read()
    out = []
    for m in re.finditer(rb"[\w \-\.\\/$:()]+?\.wad2", raw):
        n = os.path.basename(m.group(0).decode("latin1").replace("\\", "/"))
        if n not in out:
            out.append(n)
    return out


def wad_ids(path):
    mov, sta = [], {}
    for cid, pl in W.load(path):
        if cid == b"W2Moveables":
            for c2, p2 in W._chunks(pl, 0, len(pl)):
                mov.append(W._leb_u(p2, 0)[0])
        elif cid == b"W2Statics":
            for c2, p2 in W._chunks(pl, 0, len(pl)):
                sid, q = W._leb_u(p2, 0)
                _, q = W._leb_u(p2, q)
                d = dict(W._chunks(p2, q, len(p2)))

                def bb(name):
                    dd = dict(W._chunks(d[name], 0, len(d[name])))
                    return struct.unpack("<3f", dd[b"W2BBMin"][:12]) + struct.unpack("<3f", dd[b"W2BBMax"][:12])
                sta[sid] = (bb(b"W2StaticVB"), bb(b"W2StaticCB"))
    return mov, sta


def level_statics(prj):
    """static id -> (wad, visibility box, collision box) with the first wad that has it winning, as in the editor."""
    out = {}
    for w in level_wads(prj):
        p = os.path.join(WADS, w)
        if not os.path.exists(p):
            continue
        for sid, v in wad_ids(p)[1].items():
            out.setdefault(sid, (w,) + v)
    return out
