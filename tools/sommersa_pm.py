"""The lost half, 16 Nov afternoon (objects only, no geometry):
  - two more sharks in the flooded cella (squalo2, squalo3), switched on by the script when the spirits of the
    twins come
  - a flyby (sequence 2, four cameras in the cella) for the death of Turi 'a Vulpi

  sommersa_pm.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
import tindari_pm as TP
from prj2_check import Reader
from titolo_flyby import fly, CUT_PAN

ROOM = "H_CELLA"
SHARKS = [("squalo2", (6.5 * 1024, 2100.0, 5.5 * 1024)), ("squalo3", (11.5 * 1024, 1700.0, 7.5 * 1024))]
CUT_TO_LARA = 64
# local position, yaw (90 = east), pitch
CAMS = [((4.6 * 1024, 3300.0, 4.5 * 1024), 80.0, -28.0), ((5.8 * 1024, 3100.0, 5.2 * 1024), 86.0, -27.0),
        ((7.0 * 1024, 2900.0, 6.0 * 1024), 90.0, -26.0), ((8.0 * 1024, 2750.0, 6.5 * 1024), 90.0, -25.0)]


def main():
    src, dst = sys.argv[1:3]
    raw = P.raw_objects(src)
    names = [TP.name_of(op) for _, oc, op in raw if oc in (b"TeMovTn3", b"TeMovTen2")]
    assert "squalo2" not in names, "already done"
    next_id = max(Reader(op).leb() for _, _, op in raw) + 1
    shark = [(oc, op) for room, oc, op in raw if oc in (b"TeMovTn3", b"TeMovTen2") and TP.name_of(op) == "squalo"][0]
    fly_id = [oc for _, oc, _ in raw if oc.startswith(b"TeFly")][0]
    assert fly_id == b"TeFly3", fly_id
    new = []
    for name, pos in SHARKS:
        new.append((shark[0], TP.rename(shark[1], name, pos, next_id)))
        next_id += 1
    for k, (pos, yaw, pitch) in enumerate(CAMS):
        flags = (CUT_PAN | CUT_TO_LARA) if k == 0 else 0
        new.append((b"TeFly3", P.prj2.leb(next_id) + fly(pos, yaw, pitch, k, speed=1.6, flags=flags, seq=2)))
        next_id += 1
    head, top = P.load(src)
    P.save(dst, head, [(c, P.add_objects(p, ROOM, new) if c == b"TeRooms" else p) for c, p in top])
    print("two sharks and the flyby of Turi's end added to", ROOM)


if __name__ == "__main__":
    main()
