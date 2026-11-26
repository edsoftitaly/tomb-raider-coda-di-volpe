"""The pathfinding data of a compiled level, read back from the .ten (Specific/level.cpp: LoadLevel, LoadBoxes):
boxes, overlaps and zones, found in the second data block by their shape.
  ten_boxes.py <level.ten>             -> pickle next to /tmp/r/<name>_boxes.pkl and a summary
  import: load(path) -> dict(boxes=[(xmin, xmax, zmin, zmax, height, overlap, flags)], overlaps, zones[flip][type])"""
import pickle
import struct
import sys

import lz4.block

ZONES = ("Skeleton", "Basic", "Water", "Amphibious", "Human", "Flyer")


def blocks(path):
    f = open(path, "rb")
    f.read(16)
    out = []
    while True:
        h = f.read(16)
        if len(h) < 16:
            break
        usize, csize = struct.unpack("<qq", h)
        out.append((usize, f.read(csize)))
    return out


def decompress(usize, data):
    n = struct.unpack_from("<I", data, 0)[0]
    o, parts = 4, []
    for _ in range(n):
        u, c = struct.unpack_from("<II", data, o)
        o += 8
        parts.append(lz4.block.decompress(data[o:o + c], uncompressed_size=u))
        o += c
    return b"".join(parts)


def load(path):
    bl = blocks(path)
    d = decompress(*bl[1])
    # the box array: a count, then count records of 7 ints with xmin < xmax <= 512, zmin < zmax <= 512
    best = None
    o = 0
    mv = memoryview(d)
    while True:
        o = d.find(b"\x00\x00", o + 1)          # cheap anchor: counts are small ints
        if o < 0 or o > len(d) - 64:
            break
        s = o - 2
        if s < 0:
            continue
        n = struct.unpack_from("<i", d, s)[0]
        if not (20 <= n <= 60000) or s + 4 + n * 28 > len(d):
            continue
        ok = True
        for k in (0, 1, 2, n // 2, n - 1):
            a = struct.unpack_from("<4I3i", d, s + 4 + k * 28)
            if not (a[0] < a[1] <= 600 and a[2] < a[3] <= 600 and -200000 < a[4] < 200000 and (a[6] & ~0xC600) == 0 and -1 <= a[5] < 10 ** 7):
                ok = False
                break
        if ok:
            ok = all((lambda a: a[0] < a[1] <= 600 and a[2] < a[3] <= 600)(struct.unpack_from("<4I", d, s + 4 + k * 28)) for k in range(n))
        if ok:
            best = (s, n)
            break
    assert best, "box array not found"
    s, n = best
    boxes = [struct.unpack_from("<4I3i", d, s + 4 + k * 28) for k in range(n)]
    o = s + 4 + n * 28
    no = struct.unpack_from("<i", d, o)[0]
    overlaps = [struct.unpack_from("<2i", d, o + 4 + k * 8) for k in range(no)]
    o += 4 + no * 8
    nz = struct.unpack_from("<i", d, o)[0]
    o += 4
    zones = []
    for i in range(2):
        g = {}
        for j in range(nz):
            g[ZONES[j] if j < len(ZONES) else j] = struct.unpack_from("<%di" % n, d, o)
            o += 4 * n
        zones.append(g)
    return dict(boxes=boxes, overlaps=overlaps, zones=zones)


if __name__ == "__main__":
    r = load(sys.argv[1])
    print("boxes", len(r["boxes"]), "overlaps", len(r["overlaps"]), "zone groups", list(r["zones"][0]))
    print("blockable boxes:", sum(1 for b in r["boxes"] if b[6] & 0x8000))
    pickle.dump(r, open("/tmp/r/" + sys.argv[1].split("/")[-1].split(".")[0] + "_boxes.pkl", "wb"))
