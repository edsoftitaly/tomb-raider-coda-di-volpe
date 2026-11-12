"""Sommersa.prj2 for Ed's disk: the generated level with the sound list of an installed level (the generator
leaves it empty). usage: sommersa_prj2.py <generated .prj2> <installed .prj2 with sounds> <out>"""
import sys

import prj2_patch as P

_, mt = P.load(sys.argv[2])
ms = dict(P.chunks(dict(mt)[b"TeSettings"])[0])
h, t = P.load(sys.argv[1])
items, _ = P.chunks(dict(t)[b"TeSettings"])
items = [(c, ms[c] if c in (b"TeSelectedSounds", b"TeSoundsCatalogs") else p) for c, p in items]
P.save(sys.argv[3], h, [(c, P.pack(items) if c == b"TeSettings" else p) for c, p in t])
