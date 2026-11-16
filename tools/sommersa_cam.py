"""The lost half: a fixed camera "cam_turi" in the cella. The script moves it near Turi 'a Vulpi when he dies and
plays it on him (Camera:Play), so where it stands in the editor does not matter.

  sommersa_cam.py <in.prj2> <out.prj2>"""
import struct
import sys

import prj2_patch as P
from prj2_check import Reader

ROOM = "H_CELLA"
POS = (8.5 * 1024, 2600.0, 6.5 * 1024)      # room-local, Y up


def main():
    src, dst = sys.argv[1:3]
    raw = P.raw_objects(src)
    assert not any(oc.startswith(b"TeCam") for _, oc, _ in raw), "already done"
    next_id = max(Reader(op).leb() for _, _, op in raw) + 1
    name = b"cam_turi"
    # Prj2Writer, CameraInstance (TombEngine): id, position, LEB -1, locked, move timer, name
    body = P.prj2.leb(next_id) + struct.pack("<3f", *POS) + P.prj2.leb(-1) + b"\x00\x00" + struct.pack("<i", len(name)) + name
    head, top = P.load(src)
    P.save(dst, head, [(c, P.add_objects(p, ROOM, [(b"TeCamTen", body)]) if c == b"TeRooms" else p) for c, p in top])
    print("camera cam_turi added to", ROOM, "id", next_id)


if __name__ == "__main__":
    main()
