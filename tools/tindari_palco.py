"""Tindari: the stage of the Azrael concert in the arena of the theatre (Ed, 14/11/2026).

usage: tindari_palco.py <Tindari.prj2> <out.prj2> <out cdv_palco.png>

- T_01_02: the deck is geometry (Lara walks on it): sectors x 6-13, z 24-28 up two clicks, a one-click step along both
  sides (x 5 and x 14); deck and skirt from the new texture cdv_palco.png
- the statics 460-469 of CdV_Concerto.wad2 (build_concerto.py), all with rotation 0: the audience is at -z
- t4 and t5 stay where they were, now on the deck; the dog c3 moves to the front of the stage (the drums took its place)"""
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

import prj2_fill
import prj2_patch as P
import fill
from prj2_check import Reader

ROOM = "T_01_02"
X0, X1, Z0, Z1 = 6, 13, 24, 28
BASE, DECK, STEP = 512, 1024, 768
CX, CZ = (X0 + X1 + 1) * 512.0, (Z0 + Z1 + 1) * 512.0          # centre of the deck, room units
TEX = "$(LevelDirectory)\\..\\CdV_Textures\\cdv_palco.png"
M = 512.0


def texture(path):
    im = Image.new("RGB", (256, 128), (24, 24, 26))
    rng = np.random.default_rng(14)
    a = np.asarray(im, dtype=np.float64).copy()
    a *= 1 + (rng.random((128, 256, 1)) - 0.5) * 0.35
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 127], outline=(12, 12, 13))                       # deck: plywood panels, 2 x 1 m
    d.line([0, 64, 127, 64], fill=(12, 12, 13))
    for x, y in ((6, 6), (121, 6), (6, 58), (121, 58), (6, 70), (121, 70), (6, 121), (121, 121)):
        d.point([x, y], fill=(90, 90, 96))
    for i in range(14):                                                        # tape marks and scuffs
        x, y = int(rng.integers(8, 110)), int(rng.integers(8, 118))
        d.line([x, y, x + int(rng.integers(4, 16)), y + int(rng.integers(-2, 3))], fill=(44, 44, 48))
    for x in range(128, 256):                                                  # skirt: pleated black cloth
        f = 0.55 + 0.45 * abs(((x - 128) % 16) - 8) / 8.0
        d.line([x, 7, x, 127], fill=tuple(int(c * f) for c in (26, 26, 29)))
    d.rectangle([128, 0, 255, 6], fill=(150, 154, 162))                        # the aluminium edge of the deck
    d.line([128, 6, 255, 6], fill=(70, 72, 78))
    im.save(path)


DECK_UV = [(0.5, 0.5), (127.5, 0.5), (127.5, 127.5), (0.5, 127.5)]
SKIRT_UV = [(128.5, 127.5), (128.5, 0.5), (255.5, 0.5), (255.5, 127.5)]         # bl, tl, tr, br


def sta(uid, sid, x, y, z):
    return (b"TeStaTen2", P.prj2.leb(uid) + struct.pack("<3f", x, y, z) + struct.pack("<4f", 0, 0, 0, 1) + b"\x7f"
            + struct.pack("<I", sid) + struct.pack("<3f", 1, 1, 1) + struct.pack("<hi", 0, 0))


def main(src, dst, png):
    texture(png)
    head, top = P.load(src)
    d = dict(top)
    settings, ti = P.add_texture(d[b"TeSettings"], TEX)
    settings = P.add_wad(settings, "CdV_Concerto.wad2")

    def raise_floor(lx, lz, sec):
        if Z0 <= lz <= Z1 and X0 - 1 <= lx <= X1 + 1:
            assert not sec["props"] & 3 and set(sec["floor"]) == {BASE}, (lx, lz, sec["floor"])
            h = DECK if X0 <= lx <= X1 else STEP
            sec["floor"] = [h] * 4
            sec["fsplits"] = []
            sec["faces"] = {25: (DECK_UV, 0, ti)}
    rooms, n = P.edit_sectors(d[b"TeRooms"], ROOM, raise_floor)
    print("sectors raised:", n, "texture", ti)

    moved = []

    def enemies(room, oc, op):
        if room != ROOM or not oc.startswith(b"TeMov"):
            return op
        r = Reader(op)
        r.leb()
        k = r.s.tell()
        x, y, z = struct.unpack("<3f", op[k:k + 12])
        name = P.mov_type(op)
        if X0 * 1024 <= x < (X1 + 1) * 1024 and Z0 * 1024 <= z < (Z1 + 1) * 1024:
            if abs(x - CX) < 1500 and z > CZ:                # where the drum riser goes
                x, z = CX, Z0 * 1024 + 900.0
            moved.append((name, x, z))
            return op[:k] + struct.pack("<3f", x, float(DECK), z) + op[k + 12:]
        return op
    rooms = P.map_objects(rooms, enemies)
    print("on the deck:", moved)

    ids = [x for x in range(9000, 9100)]
    used = set()
    for rn, oc, op in P.raw_objects(src):
        try:
            used.add(Reader(op).leb())
        except Exception:
            pass
    ids = [i for i in range(max(used) + 1, max(used) + 100)]
    objs = []

    def put(sid, dx, dy, dz):
        objs.append(sta(ids.pop(0), sid, CX + dx * M, DECK + dy * M, CZ + dz * M))
    for sx in (-7.5, 7.5):
        for sz in (-4.5, 4.5):
            put(460, sx, 0, sz)
    put(461, 0, 0, 0)
    put(468, 0, 0.5, 4.25)                    # banner, under the rear truss
    put(462, 0, 0, 2.6)                       # drums
    put(463, -3.3, 0, 3.6)                    # audience left: Ed
    put(464, 3.3, 0, 3.6)                     # audience right: Andy
    put(465, 5.4, 0, 1.2)                     # Mik's keyboard
    put(466, 5.9, 0, 0.55)                    # his microphone
    put(466, 0, 0, -3.6)                      # the singer's
    for x in (-4.6, -1.2, 1.2, 4.6):
        put(467, x, 0, -4.4)
    put(467, 4.3, 0, 0.2)
    for sx in (-6.6, 6.6):
        put(469, sx, 5.5, -4.95)
    rooms = P.add_objects(rooms, ROOM, objs)
    print("statics placed:", len(objs))
    P.save(dst, head, [(c, settings if c == b"TeSettings" else rooms if c == b"TeRooms" else p) for c, p in top])

    # the sides of the deck and of the steps: every wall face the new heights ask for takes the skirt
    model = [r for r in prj2_fill.model(dst) if r.name == ROOM]
    before = {(lx, lz): set(model[0].sectors[lx][lz].tex) for lx in range(model[0].nx) for lz in range(model[0].nz)}

    class L:
        rooms = model
    fill.fill_missing(L)
    added = {}
    for (lx, lz), old in before.items():
        new = set(model[0].sectors[lx][lz].tex) - old
        if new:
            assert X0 - 2 <= lx <= X1 + 2 and Z0 - 1 <= lz <= Z1 + 1, (lx, lz, new)
            added[(lx, lz)] = new
    head, top = P.load(dst)

    def skirt(lx, lz, faces):
        for f in added.get((lx, lz), ()):
            assert fill._kind(f) == "w", (lx, lz, f)
            faces[f] = (SKIRT_UV, 0, ti)
    rp, done = P.edit_room(dict(top)[b"TeRooms"], lambda rn: rn == ROOM, lambda rn, lx, lz, f: skirt(lx, lz, f))
    P.save(dst, head, [(c, rp if c == b"TeRooms" else p) for c, p in top])
    print("skirt faces:", sum(len(v) for v in added.values()), "in", done, "sectors", sorted(added.items())[:4])


main(*sys.argv[1:4])
