"""CdV_Arredi.wad2: the Belle Epoque furniture (converted from the old .wad files) re-posed as drop-in
replacements of the hand-made furniture of the house. Each piece is rotated by a multiple of 90 degrees, scaled
and moved inside its own mesh so that it stands exactly where the old model stood: same origin, same facing,
same footprint. The content then places it with the position and rotation of the old one."""
import json
import os

import numpy as np

import wad_tr4
from decor import tex

tex.build()
from decor import models, wad2  # noqa: E402
from decor import santuario_models, santuario_interno_models, casa_models, marinello_models, mito_models  # noqa: E402,F401

B = "/mnt/user-data/uploads/CodaDiVolpe/Assets/Wads/CodaDiVolpe/new_wads/LarasLevelbaseStuff_BelleEpoqueCollection/"
SRC = {"LETTO": ("bett1.WAD", 0), "COMO": ("kommode.WAD", 0), "COMODINO": ("nachttisch.WAD", 0), "POLTRONCINA": ("chair.WAD", 0),
       "TOELETTA": ("schminktisch.WAD", 0), "SGABELLO": ("schminktisch.WAD", 1), "ARMADIO": ("schrank.WAD", 0), "DIVANO": ("sofa.WAD", 0),
       "LAMPADA": ("stehlampe.WAD", 0), "CONSOLLE": ("wandtisch.WAD", 0), "TAVOLO": ("fruehstueckstisch.WAD", 0)}
# old model -> Belle Epoque piece
PAIRS = {"CASA_LETTO": "LETTO", "CASA_LETTINO": "LETTO", "CASA_COMODINO": "COMODINO", "CASA_ARMADIO": "ARMADIO", "CASA_DIVANO": "DIVANO",
         "CASA_TAVOLO": "TAVOLO", "CASA_MOBILE_TV": "COMO", "CASA_SCRIVANIA": "TOELETTA"}
EXTRA = {"AR_LAMPADA": ("LAMPADA", 0.62), "AR_POLTRONCINA": ("POLTRONCINA", 0.8), "AR_SGABELLO": ("SGABELLO", 0.8)}   # free-standing, scaled
FIRST_ID = 370
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "wads")


def hmap(P, n=6):
    lo, hi = P.min(axis=0), P.max(axis=0)
    size = np.maximum(hi - lo, 1e-6)
    g = np.zeros((n, n))
    ix = np.clip(((P[:, 0] - lo[0]) / size[0] * n).astype(int), 0, n - 1)
    iz = np.clip(((P[:, 2] - lo[2]) / size[2] * n).astype(int), 0, n - 1)
    np.maximum.at(g, (ix, iz), (P[:, 1] - lo[1]) / size[1])
    return g, size


def rot(P, k):
    Q = P.copy()
    for _ in range(k):
        Q = np.column_stack([Q[:, 2], Q[:, 1], -Q[:, 0]])
    return Q


def main():
    old = {s[1]: s[2] for s in models.build_all() if s[1] in PAIRS}
    pages, cache, statics, ids, notes = [], {}, [], {}, []
    for key, (fname, idx) in SRC.items():
        version, texs, pg, sts = wad_tr4.read(B + fname)
        cache[key] = wad_tr4.convert(texs, sts[idx][1], len(pages))
        pages += pg
    sid = FIRST_ID

    def emit(name, src, P):
        nonlocal sid
        m = wad_tr4.M()
        m.v = P.tolist()
        m.f = list(src.f)
        lo, hi = P.min(axis=0), P.max(axis=0)
        statics.append((sid, name, m, (tuple(lo), tuple(hi))))
        ids[name] = sid
        notes.append("%d %s" % (sid, name))
        sid += 1

    for cname, key in PAIRS.items():
        src = cache[key]
        C = np.array(old[cname].v)
        gc, sc = hmap(C)
        P0 = np.array(src.v)
        best = None
        for k in range(4):
            P = rot(P0, k)
            g, s = hmap(P)
            cost = np.abs(g - gc).mean() + 0.5 * abs(np.log((s[0] / s[2]) / (sc[0] / sc[2])))
            if best is None or cost < best[0]:
                best = (cost, k, P, s)
        cost, k, P, s = best
        if cname in ("CASA_ARMADIO", "CASA_MOBILE_TV", "CASA_COMODINO"):
            # front or back? The front carries the detail (doors, drawers, handles): the faces crowd on that side.
            ax = 0 if sc[0] < sc[2] else 2

            def lean(V, faces):
                cen = np.array([np.mean([V[i][ax] for i in f[0]]) for f in faces])
                return float(cen.mean() - (V[:, ax].min() + V[:, ax].max()) / 2) / float(V[:, ax].max() - V[:, ax].min())
            lo_, ln = lean(C, old[cname].f), lean(P, src.f)
            if abs(lo_) > 0.03 and abs(ln) > 0.03 and lo_ * ln < 0:
                k = (k + 2) % 4
                P = rot(P0, k)
                s = hmap(P)[1]
            print("   front check %s: old %+.2f new %+.2f -> rot %d" % (cname, lo_, ln, k * 90))
        scale = min(sc[1] / s[1], 1.15 * min(sc[0] / s[0], sc[2] / s[2]))
        if cname == "CASA_TAVOLO":
            scale = min(1.15 * sc[0] / s[0], 1.15 * sc[2] / s[2], 1.05 * sc[1] / s[1])
        elif cname in ("CASA_SCRIVANIA", "CASA_MOBILE_TV"):
            scale = min(1.15 * sc[0] / s[0], 1.15 * sc[2] / s[2], 1.6 * sc[1] / s[1])       # tops and chests: the footprint decides
        P = P * scale
        cc = (C.min(axis=0) + C.max(axis=0)) / 2
        pc = (P.min(axis=0) + P.max(axis=0)) / 2
        P = P + np.array([cc[0] - pc[0], C[:, 1].min() - P[:, 1].min(), cc[2] - pc[2]])
        size = (P.max(axis=0) - P.min(axis=0)) / 512
        print("%-16s <- %-9s rot %3d  scale %.2f  %.2f x %.2f x %.2f m (old %.2f x %.2f x %.2f)  cost %.2f" % (
            cname, key, k * 90, scale, size[0], size[1], size[2], sc[0] / 512, sc[1] / 512, sc[2] / 512, cost))
        emit("AR_" + cname, src, P)
    for name, (key, scale) in EXTRA.items():
        P = np.array(cache[key].v) * scale
        c = (P.min(axis=0) + P.max(axis=0)) / 2
        emit(name, cache[key], P - np.array([c[0], P[:, 1].min(), c[2]]))
    wad2.write(os.path.join(OUT, "CdV_Arredi.wad2"), pages, statics, "Arredi Belle Epoque (Laras Levelbase Stuff) al posto dei mobili della casa\n" + "\n".join(notes))
    json.dump(ids, open(os.path.join(OUT, "CdV_Arredi.json"), "w"), indent=1)
    return ids


if __name__ == "__main__":
    main()
