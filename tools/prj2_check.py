"""Strict reader for .prj2 files, mirroring TombLib Prj2Loader / ChunkReader.

Used to validate generated projects without Windows: every chunk must be read exactly
to its declared size, known chunk ids only, and the room/portal graph must be consistent.
Usage: python3 prj2_check.py file.prj2
"""
import io
import os
import struct
import sys


TEX_SIZE = int(os.environ.get("PRJ2_TEX_SIZE", "2048"))


class Reader:
    def __init__(self, data):
        self.s = io.BytesIO(data)
        self.errors = []

    def leb(self):
        result, shift = 0, 0
        while True:
            b = self.s.read(1)[0]
            result |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                break
        if shift < 64 and result & (1 << (shift - 1)):
            result -= 1 << shift
        return result

    def raw(self, n):
        d = self.s.read(n)
        if len(d) != n:
            raise EOFError
        return d

    def i32(self):
        return struct.unpack("<i", self.raw(4))[0]

    def u32(self):
        return struct.unpack("<I", self.raw(4))[0]

    def i16(self):
        return struct.unpack("<h", self.raw(2))[0]

    def f(self, n=1):
        v = struct.unpack("<%df" % n, self.raw(4 * n))
        return v if n > 1 else v[0]

    def ustr(self):
        n = self.i32()
        return self.raw(n).decode("utf-8")

    def chunks(self, handler, where):
        while True:
            idlen = self.leb()
            if idlen == 0:
                return
            cid = self.raw(idlen)
            size = self.leb()
            start = self.s.tell()
            ok = handler(cid, size)
            used = self.s.tell() - start
            if not ok:
                self.errors.append("unrecognized chunk %r in %s" % (cid, where))
                self.s.seek(start + size)
            elif used != size:
                self.errors.append("chunk %r in %s: read %d of %d" % (cid, where, used, size))
                self.s.seek(start + size)


def check(path):
    data = open(path, "rb").read()
    r = Reader(data)
    assert r.raw(4) == b"PRJ2", "bad magic"
    assert r.u32() == 0, "unsupported chunk version"
    info = {"rooms": [], "settings": {}}

    def settings(cid, size):
        if cid in (b"TeGameVersion", b"TeSoundSystem", b"TeLastRoom"):
            info["settings"][cid.decode()] = r.leb()
        elif cid == b"TeDefaultAmbientLight":
            r.f(3)
        elif cid in (b"TeOldWadSoundPaths", b"TeWads", b"TeSoundsCatalogs", b"TeSelectedSounds",
                     b"TeTextures", b"TeImportedGeometries", b"TeAnimatedTextureSets",
                     b"TeGlobalEventSets", b"TeVolumeEventSets"):
            def inner(c2, s2):
                if c2 == b"TeOldWadSoundUpdateTag1_0_8":
                    return True
                if c2 == b"TeLvlTexture":
                    def lt(c3, s3):
                        if c3 in (b"TeTextureSounds", b"TeTextureBumpmaps"):
                            w, h = r.i32(), r.i32()
                            r.raw(w * h)
                            info["settings"]["texgrid"] = (w, h)
                        else:
                            r.raw(s3)
                        return True
                    r.chunks(lt, "TeLvlTexture")
                    info["settings"]["textures"] = info["settings"].get("textures", 0) + 1
                    return True
                if c2 in (b"TeWad", b"TeOldWadSoundPath", b"TeSoundsCatalog"):
                    r.chunks(lambda c3, s3: bool(r.raw(s3)) or True, "TeWad")
                    return True
                return False
            r.chunks(inner, cid.decode())
        else:
            r.raw(size)  # strings
        return True

    def room_chunk(cid, size):
        room = {"objects": [], "portals": []}
        room["nx"], room["nz"] = r.leb(), r.leb()
        seen = set()

        def sectors(c3, s3):
            if c3 != b"TeS":
                return False
            pos = r.i32()
            assert 0 <= pos < room["nx"] * room["nz"], "sector index out of range"
            assert pos not in seen, "duplicate sector"
            seen.add(pos)

            def sec(c4, s4):
                if c4 == b"\x00":
                    r.leb()
                elif c4 in (b"\x07", b"\x08"):
                    r.leb()
                    hs = [r.leb() for _ in range(4)]
                    room.setdefault("hmin", min(hs))
                    room["hmin"] = min(room["hmin"], min(hs))
                    room["hmax"] = max(room.get("hmax", -1 << 60), max(hs))
                elif c4 == b"\x12":
                    face = r.leb(); tc = r.f(8); r.f(4); r.leb(); tex = r.leb()
                    assert 0 <= face < 99 and tex >= 0, "bad texture face"
                    # Same rule as TombLib TextureArea.QuadCoordsOutOfBounds / TriangleCoordsOutOfBounds.
                    pts = [(tc[i], tc[i + 1]) for i in range(0, 8, 2)]
                    if pts[2] == pts[3] or face in (25, 26, 27, 28):
                        tri = pts[:3]
                        quad_or_tri = [tri] if pts[2] == pts[3] else [tri, pts]
                    else:
                        quad_or_tri = [pts]
                    for poly in quad_or_tri:
                        us = [p[0] for p in poly]; vs = [p[1] for p in poly]
                        if min(us) < 0 or min(vs) < 0 or max(us) > TEX_SIZE or max(vs) > TEX_SIZE or \
                                max(us) - min(us) > 256 or max(vs) - min(vs) > 256:
                            r.errors.append("texture out of bounds: room %s face %d %s" % (room.get("name"), face, pts))
                            break
                    room["textured"] = room.get("textured", 0) + 1
                elif c4 == b"\x11":
                    r.leb()
                    room["invisible"] = room.get("invisible", 0) + 1
                elif c4 in (b"\x09", b"\x0a"):
                    n = r.leb()
                    for _ in range(4 * n):
                        r.leb()
                else:
                    return False
                return True
            r.chunks(sec, "sector")
            return True

        def objects(c3, s3):
            oid = r.leb()
            if c3 == b"TePor2":
                area = [r.leb() for _ in range(4)]
                adj = r.leb()
                direction, opacity, effect = r.raw(3)
                r.chunks(lambda c4, s4: c4 == b"TePorMirror" and bool(r.raw(5)), "portal")
                room["portals"].append((area, adj, direction))
            elif c3 == b"TeMovTen2":
                pos = r.f(3); r.f(3); r.leb(); t = r.u32(); r.i16(); r.raw(3); r.f(3); r.ustr()
                room["objects"].append(("moveable", t, pos))
            elif c3 == b"TeStaTen2":
                pos = r.f(3); r.f(4); r.leb(); t = r.u32(); r.f(3); r.i16(); r.ustr()
                room["objects"].append(("static", t, pos))
            elif c3 == b"TeLig5":
                t = r.leb(); pos = r.f(3); r.f(3); r.f(3); r.f(4); r.raw(7)
                room["objects"].append(("light", t, pos))
            else:
                return False
            return True

        def props(c2, s2):
            if c2 == b"TeI":
                room["index"] = r.leb()
            elif c2 == b"TeName":
                room["name"] = r.raw(s2).decode("utf-8")
            elif c2 == b"TePos2":
                room["pos"] = r.f(3)
            elif c2 == b"TeTags":
                r.raw(s2)
            elif c2 == b"TeSecs":
                r.chunks(sectors, "TeSecs")
            elif c2 in (b"TeAmbient",):
                r.f(3)
            elif c2 in (b"TeCold", b"TeNoCaustics", b"TeDmg", b"TeHorizon", b"TeOutside", b"TeNoLens",
                        b"TeNoPath", b"TeLocked", b"TeHidden"):
                r.raw(1)
            elif c2 in (b"TeRoomType", b"TeRoomTypeStrength", b"TeRoomLightEffect",
                        b"TeRoomLightEffectStrength2", b"TeReverb", b"TeRoomLightInt"):
                r.leb()
            elif c2 == b"TeAlternate":
                r.chunks(lambda c3, s3: c3 in (b"TeGroup", b"TeRoom") and (r.leb() is not None), "alt")
            elif c2 == b"TeObjects":
                r.chunks(objects, "TeObjects")
            else:
                return False
            return True

        r.chunks(props, "TeRoom")
        if len(seen) != room["nx"] * room["nz"]:
            r.errors.append("room %s: %d of %d sectors" % (room.get("name"), len(seen), room["nx"] * room["nz"]))
        info["rooms"].append(room)
        return True

    def top(cid, size):
        if cid == b"TeSettings":
            r.chunks(settings, "TeSettings")
            return True
        if cid == b"TeRooms":
            r.chunks(lambda c, s: c == b"TeRoom" and room_chunk(c, s), "TeRooms")
            return True
        return False

    r.chunks(top, "file")
    if r.s.tell() != len(data):
        r.errors.append("trailing bytes: %d" % (len(data) - r.s.tell()))

    # Portal graph: each wall portal must have a matching opposite portal.
    opposite = {2: 3, 3: 2, 4: 5, 5: 4, 0: 1, 1: 0}
    rooms = {rm["index"]: rm for rm in info["rooms"]}
    for rm in info["rooms"]:
        for area, adj, d in rm["portals"]:
            other = rooms.get(adj)
            if other is None:
                r.errors.append("portal to missing room %d" % adj)
                continue
            if not any(a2 == rm["index"] and d2 == opposite[d] for _, a2, d2 in other["portals"]):
                r.errors.append("room %d portal dir %d to %d has no counterpart" % (rm["index"], d, adj))
    return info, r.errors


if __name__ == "__main__":
    info, errors = check(sys.argv[1])
    print("settings:", info["settings"])
    print("rooms:", len(info["rooms"]), "portals:", sum(len(r["portals"]) for r in info["rooms"]),
          "objects:", sum(len(r["objects"]) for r in info["rooms"]),
          "textured faces:", sum(r.get("textured", 0) for r in info["rooms"]),
          "invisible faces:", sum(r.get("invisible", 0) for r in info["rooms"]))
    for e in errors[:30]:
        print("ERROR:", e)
    print("OK" if not errors else "%d errors" % len(errors))
    sys.exit(1 if errors else 0)
