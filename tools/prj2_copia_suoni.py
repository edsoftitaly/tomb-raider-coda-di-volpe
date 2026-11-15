"""Copy the selected sounds (TeSelectedSounds) of one level into another. Tindari had none selected at all: every
animation sound of Lara and of the enemies was missing there.
usage: prj2_copia_suoni.py <from.prj2> <to.prj2> <out.prj2>"""
import sys

import prj2_patch as P

_, top_a = P.load(sys.argv[1])
sel = dict(P.chunks(dict(top_a)[b"TeSettings"])[0])[b"TeSelectedSounds"]
head, top = P.load(sys.argv[2])
items, _ = P.chunks(dict(top)[b"TeSettings"])
settings = P.pack([(c, sel if c == b"TeSelectedSounds" else p) for c, p in items])
P.save(sys.argv[3], head, [(c, settings if c == b"TeSettings" else p) for c, p in top])
print("selected sounds copied:", len(P.chunks(sel)[0]))
