"""CdV_Rivolo.wad2: the trickle of water in the channel of the big sluice of Marinello (Ed, 14/11/2026).

The water was one sheet 420 units over the bed, higher than the banks upstream, and only shown once the sluice was
open. Now: a shallow trickle 40 units over the bed (the script puts it there), always there upstream of the gate, and
downstream once the gate is up. Flat sheets of 512-unit tiles (the script slides them one tile and back: the water
runs), additive and double sided, with the water texture of CdV_Chiusa.wad2. Flow towards -z.

 472 RIVOLO_MONTE   from inside the dam block to the mouth on the sea, with a lip going down at the mouth
 473 RIVOLO_VASCA   between the dam and the gate (still)
 474 RIVOLO_VALLE   from inside the dam block to the lake
"""
import os
import struct

import numpy as np

import wadtool
from decor import geom as G
from decor import tex
from decor import wad2 as W

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = "/mnt/user-data/uploads/CodaDiVolpe/Assets/Wads/CodaDiVolpe/CdV_Chiusa.wad2"
OUT = os.path.join(ROOT, "assets", "wads", "CdV_Rivolo.wad2")
HW = 500.0


def water_tile():
    d = dict(wadtool.load(SRC))
    for c2, p2 in wadtool._chunks(d[b"W2Textures"], 0, len(d[b"W2Textures"])):
        w, q = wadtool._leb_u(p2, 0)
        h, q = wadtool._leb_u(p2, q)
        data = dict(wadtool._chunks(p2, q, len(p2)))[b"W2TxtData"]
        a = np.frombuffer(data, np.uint8).reshape(h, w, 4)[..., [2, 1, 0, 3]].astype(np.float64)
        return a[256:384, 64:192].copy()
    raise SystemExit("no texture")


def sheet(z0, z1, lip=False):
    """Tiles of 512 from z0 to z1 (units, multiples of 512), y = 0."""
    m = G.Mesh()
    z = z0
    while z < z1 - 1:
        y0 = y1 = 0.0
        if lip and z + 512 >= z1:
            y1 = -170.0                                   # the last tile goes down to the sea
        pts = [(-HW, y1, z + 512), (HW, y1, z + 512), (HW, y0, z), (-HW, y0, z)]
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        m.face(pts, "rv_acqua", uv=uv, blend=2)
        m.face(pts[::-1], "rv_acqua", uv=uv[::-1], blend=2)
        z += 512
    return m


def main():
    pk = tex.Packer()
    pk.put("rv_acqua", water_tile())
    statics = [(472, "RIVOLO_MONTE", sheet(-1024, 9216, lip=True), None),
               (473, "RIVOLO_VASCA", sheet(-1024, 512), None),
               (474, "RIVOLO_VALLE", sheet(-3584, 3584), None)]
    for sid, name, mesh, _ in statics:
        lo, hi = mesh.bbox()
        print(sid, name, len(mesh.f), [int(v) for v in lo], [int(v) for v in hi])
    W.write(OUT, tex.pages, statics, notes="Coda di Volpe - Marinello: il rivolo nel canale della chiusa grande (statici 472-474)")
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
