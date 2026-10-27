"""Minimal writer for Tomb Editor .prj2 projects (TombEngine target).

Ported from TombLib/LevelData/IO/Prj2Writer.cs, Prj2Chunks.cs, ChunkWriter.cs and
LEB128.cs (https://github.com/TombEngine/Tomb-Editor). Only the subset needed to build
terrain-based levels is implemented: settings, rooms, sectors, portals, moveables,
statics and lights.

Units follow Tomb Editor: 1 sector = 1024 units (about 2 m), 1 click = 256 units.
X grows east, Z grows north, Y grows up. Sector heights are relative to Room.y.
"""
import struct

MAGIC = b"PRJ2"

# Game versions (TRVersion.Game)
GAME_TOMBENGINE = 18
SOUND_SYSTEM_XML = 1

# Portal directions (PortalDirection)
P_FLOOR, P_CEILING, P_WALL_PZ, P_WALL_NZ, P_WALL_PX, P_WALL_NX = range(6)

# Sector edge order used by Prj2 (SectorEdge): XnZp, XpZp, XpZn, XnZn
SECTOR_SIZE = 1024
CLICK = 256

# Light types (LightType)
LIGHT_POINT, LIGHT_SHADOW, LIGHT_SPOT, LIGHT_EFFECT, LIGHT_SUN, LIGHT_FOG = range(6)


def leb(value):
    """Signed LEB128, identical to TombLib.IO.LEB128.Write(stream, value)."""
    out = bytearray()
    value = int(value)
    while True:
        byte = value & 0x7F
        value >>= 7
        if (value == 0 and not byte & 0x40) or (value == -1 and byte & 0x40):
            out.append(byte)
            return bytes(out)
        out.append(byte | 0x80)


def cid(name):
    if isinstance(name, bytes):
        return name
    return name.encode("ascii")


def chunk(name, payload=b""):
    i = cid(name)
    return leb(len(i)) + i + leb(len(payload)) + payload


END = b"\x00"


def c_int(name, v):
    return chunk(name, leb(v))


def c_bool(name, v):
    return chunk(name, b"\x01" if v else b"\x00")


def c_str(name, s):
    return chunk(name, (s or "").encode("utf-8"))


def c_vec3(name, v):
    return chunk(name, struct.pack("<3f", *v))


def f32(*v):
    return struct.pack("<%df" % len(v), *v)


def utf8(s):
    b = (s or "").encode("utf-8")
    return struct.pack("<i", len(b)) + b


# Sector chunk ids are single raw bytes.
SEC_PROPS = bytes([0])
SEC_FLOOR = bytes([7])
SEC_CEIL = bytes([8])
SEC_FLOOR_SUB = bytes([9])
SEC_CEIL_SUB = bytes([10])
TEX_LEVEL2 = bytes([18])
TEX_INVISIBLE = bytes([17])

# SectorFace ids (TombLib SectorFace)
F_WALL_QA = {"+z": 0, "-z": 1, "-x": 2, "+x": 3}
F_WALL_WS = {"+z": 15, "-z": 16, "-x": 17, "+x": 18}
F_WALL_MIDDLE = {"+z": 10, "-z": 11, "-x": 12, "+x": 13}
_DIR_ORDER = {"+z": 0, "-z": 1, "-x": 2, "+x": 3}


def f_wall_ceiling(d, segment):
    """Face id of the ceiling-part wall segment: 0 = WS, 1 = Ceiling2 ... 8 = Ceiling9."""
    if segment == 0:
        return F_WALL_WS[d]
    if segment == 1:
        return 20 + _DIR_ORDER[d]
    return 34 + (segment - 2) * 10 + _DIR_ORDER[d]


def f_wall_floor(d, segment):
    """Face id of the floor-part wall segment: 0 = QA, 1 = Floor2 ... 8 = Floor9."""
    if segment == 0:
        return F_WALL_QA[d]
    if segment == 1:
        return 5 + _DIR_ORDER[d]
    return 29 + (segment - 2) * 10 + _DIR_ORDER[d]
F_FLOOR, F_FLOOR_TRI2, F_CEILING, F_CEILING_TRI2 = 25, 26, 27, 28


class Sector:
    __slots__ = ("wall", "floor", "ceil", "fsplit", "csplit", "flags", "tex", "invisible", "fsplits", "csplits")

    def __init__(self, floor=(0, 0, 0, 0), ceil=(3072, 3072, 3072, 3072), wall=False):
        self.wall = wall          # True = solid wall sector
        self.floor = list(floor)  # heights XnZp, XpZp, XpZn, XnZn
        self.ceil = list(ceil)
        self.fsplit = False       # SplitDirectionIsXEqualsZ
        self.csplit = False
        self.flags = 0
        self.tex = None           # {face: ((u,v) x4, texture_index)}
        self.invisible = None     # set of faces
        self.fsplits = []         # extra floor splits, each 4 heights (XnZp, XpZp, XpZn, XnZn), descending
        self.csplits = []         # extra ceiling splits, ascending

    def set_tex(self, face, coords, texture=0, blend=0, double_sided=False):
        """blend = TombLib BlendMode (0 Normal, 2 Additive, 11 AlphaBlend)."""
        if self.tex is None:
            self.tex = {}
        self.tex[face] = (coords, texture, (1 if double_sided else 0) | (blend << 1))

    def set_invisible(self, face):
        if self.invisible is None:
            self.invisible = set()
        self.invisible.add(face)

    def encode(self, index):
        out = bytearray(struct.pack("<i", index))
        out += c_int(SEC_PROPS, (1 if self.wall else 0) | (self.flags << 2))
        out += chunk(SEC_FLOOR, leb(1 if self.fsplit else 0) + b"".join(leb(h) for h in self.floor))
        out += chunk(SEC_CEIL, leb(1 if self.csplit else 0) + b"".join(leb(h) for h in self.ceil))
        out += chunk(SEC_FLOOR_SUB, leb(len(self.fsplits)) + b"".join(leb(h) for sp in self.fsplits for h in sp))
        out += chunk(SEC_CEIL_SUB, leb(len(self.csplits)) + b"".join(leb(h) for sp in self.csplits for h in sp))
        if self.tex:
            for face, (coords, texture, mode) in self.tex.items():
                us = [c[0] for c in coords]
                vs = [c[1] for c in coords]
                body = leb(face) + f32(*[v for c in coords for v in c])
                body += f32(min(us), min(vs), max(us), max(vs)) + leb(mode) + leb(texture)
                out += chunk(TEX_LEVEL2, body)
        if self.invisible:
            for face in self.invisible:
                out += c_int(TEX_INVISIBLE, face)
        out += END
        return chunk("TeS", bytes(out))


class Room:
    def __init__(self, name, nx, nz, x=0, y=0, z=0):
        assert nx >= 3 and nz >= 3
        self.name = name
        self.nx, self.nz = nx, nz
        self.x, self.y, self.z = x, y, z  # x, z in sectors; y in units
        self.sectors = [[Sector() for _ in range(nz)] for _ in range(nx)]
        for xx in range(nx):
            for zz in range(nz):
                if xx in (0, nx - 1) or zz in (0, nz - 1):
                    self.sectors[xx][zz].wall = True
        self.ambient = (0.5, 0.5, 0.5)
        self.outside = False
        self.horizon = False
        self.no_lensflare = False
        self.room_type = 0        # RoomType: 0 Normal, 1 Rain, 2 Snow, 3 Water, 4 Quicksand
        self.light_effect = 1     # RoomLightEffect: 0 None, 1 Default (editor default)
        self.reverb = 0
        self.no_path = False      # exclude from enemy pathfinding (huge terrain rooms stall the compiler)
        self.tags = []
        self.objects = []         # encoded object chunks (callables taking id maps)
        self.index = None
        self.alternate = None     # (group, Room)

    def sector(self, x, z):
        return self.sectors[x][z]


class Level:
    def __init__(self):
        self.rooms = []
        self.ambient = (0.5, 0.5, 0.5)
        self.wads = []
        self.textures = []
        self.lua_script = ""
        self.game_directory = ""
        self.game_level_path = ""
        self.game_exe = ""
        self.script_directory = ""
        self.wad_sound_paths = []
        self.sound_catalogs = []
        self._obj_counter = 0
        self.settings_template = None   # list of raw settings sub-chunks from a TombIDE .prj2

    def use_tombide_ten(self, data_file, wads=("TombEngine.wad2",)):
        """Same settings TombIDE writes for a TEN level in <project>/Levels/<name>/<name>.prj2."""
        root = "$(LevelDirectory)\\..\\.."
        self.game_directory = root + "\\Engine"
        self.game_exe = root + "\\Engine\\Bin\\x64\\TombEngine.exe"
        self.script_directory = root + "\\Engine\\Scripts"
        self.game_level_path = root + "\\Engine\\Data\\" + data_file
        self.lua_script = "$(ScriptDirectory)\\Levels\\$(LevelName).lua"
        self.wad_sound_paths = [root + "\\Sounds"]
        self.sound_catalogs = ["$(EditorDirectory)\\Catalogs\\TEN Sound Catalogs\\TEN_ALL_SOUNDS.xml"]
        self.wads = [root + "\\Assets\\Wads\\" + w for w in wads]

    def use_settings_from(self, path):
        """Reuse game, script, sound and wad settings from a .prj2 created by TombIDE.

        Every settings sub-chunk is copied verbatim except textures, which are generated here.
        """
        data = open(path, "rb").read()
        assert data[:4] == MAGIC, "not a prj2 file"
        pos = 8
        out = []

        def read_leb(p):
            result, shift = 0, 0
            while True:
                b = data[p]
                p += 1
                result |= (b & 0x7F) << shift
                shift += 7
                if not b & 0x80:
                    if result & (1 << (shift - 1)):
                        result -= 1 << shift
                    return result, p

        while True:
            idlen, pos = read_leb(pos)
            if idlen == 0:
                break
            cid = data[pos:pos + idlen]
            pos += idlen
            size, pos = read_leb(pos)
            if cid == b"TeSettings":
                p, end = pos, pos + size
                while p < end:
                    start = p
                    l2, p = read_leb(p)
                    if l2 == 0:
                        break
                    c2 = data[p:p + l2]
                    p += l2
                    s2, p = read_leb(p)
                    p += s2
                    if c2 not in (b"TeTextures", b"TeDefaultTextures"):
                        out.append((c2, data[start:p]))
                self.settings_template = out
                return [c.decode("ascii", "replace") for c, _ in out]
            pos += size
        raise ValueError("no settings chunk found")

    def add_room(self, room):
        room.index = len(self.rooms)
        self.rooms.append(room)
        if room.index >= 1024:
            raise ValueError("Tomb Editor allows at most 1024 rooms")
        return room

    def _next_obj(self):
        self._obj_counter += 1
        return self._obj_counter - 1

    # Objects -------------------------------------------------------------
    def add_portal(self, room, area, direction, other, opacity=0):
        """area = (x0, z0, x1, z1) in room-local sector coordinates.
        opacity: 0 None, 1 SolidFaces, 2 TraversableFaces (textured portal faces are drawn, e.g. water)."""
        def enc(oid=self._next_obj()):
            body = leb(oid) + b"".join(leb(v) for v in area) + leb(other.index)
            body += bytes([direction, opacity, 0])
            body += chunk("TePorMirror", bytes(5))
            body += END
            return chunk("TePor2", body)
        room.objects.append(enc)

    def add_moveable(self, room, type_id, pos, rot_y=0.0, ocb=0, lua_name=""):
        """pos = room-local units (x, y, z)."""
        def enc(oid=self._next_obj()):
            body = leb(oid) + f32(*pos) + f32(rot_y, 0.0, 0.0) + leb(-1)
            body += struct.pack("<I", type_id) + struct.pack("<h", ocb)
            body += b"\x00\x00" + b"\x00" + f32(1.0, 1.0, 1.0) + utf8(lua_name)
            return chunk("TeMovTen2", body)
        room.objects.append(enc)

    def add_static(self, room, type_id, pos, rot_y=0.0, scale=1.0, ocb=0, lua_name=""):
        def enc(oid=self._next_obj()):
            body = leb(oid) + f32(*pos) + f32(rot_y, 0.0, 0.0, scale) + leb(-1)
            body += struct.pack("<I", type_id) + f32(1.0, 1.0, 1.0) + struct.pack("<h", ocb) + utf8(lua_name)
            return chunk("TeStaTen2", body)
        room.objects.append(enc)

    def add_light(self, room, ltype, pos, color=(1.0, 1.0, 1.0), intensity=0.5,
                  inner=1.0, outer=5.0, rot_y=0.0, rot_x=0.0, inner_angle=20.0, outer_angle=25.0):
        """inner/outer ranges are in sectors, like the editor."""
        def enc(oid=self._next_obj()):
            body = leb(oid) + leb(ltype) + f32(*pos) + f32(rot_y, rot_x, intensity)
            body += f32(*color) + f32(inner, outer, inner_angle, outer_angle)
            # Enabled, ObstructedByRoomGeometry, DynamicallyUsed, StaticallyUsed, UsedForImportedGeometry
            body += bytes([1, 1, 1, 1, 1]) + bytes([0]) + bytes([0])  # Quality default, CastDynamicShadows
            return chunk("TeLig5", body)
        room.objects.append(enc)

    # Serialization -------------------------------------------------------
    def _textures_chunk(self):
        texs = bytearray()
        for i, t in enumerate(self.textures):
            fs = t.get("footsteps")  # rows (y) of columns (x), 64 px cells
            body = c_int("TeI", i) + c_str("TePath", t["path"]) + c_str("TeTextureCustomBumpmapPath", "")
            body += c_bool("Te512C", False) + c_bool("TeMagentaR", True)
            if fs:
                h, w = len(fs), len(fs[0])
                body += chunk("TeTextureSounds", struct.pack("<ii", w, h) + bytes(v for row in fs for v in row))
                body += chunk("TeTextureBumpmaps", struct.pack("<ii", w, h) + bytes(w * h))
            body += END
            texs += chunk("TeLvlTexture", body)
        return chunk("TeTextures", bytes(texs) + END)

    def _settings(self):
        if self.settings_template is not None:
            b = bytearray()
            for cid, raw in self.settings_template:
                if cid == b"TeGameVersion":
                    b += c_int("TeGameVersion", GAME_TOMBENGINE)
                else:
                    b += raw
            b += self._textures_chunk()
            b += END
            return chunk("TeSettings", bytes(b))
        b = bytearray()
        b += c_str("TeFontTextureFilePath", "")
        b += c_str("TeSkyTextureFilePath", "")
        b += c_str("TeTr5ExtraSpritesFilePath", "")
        sp = b"".join(chunk("TeOldWadSoundPath", c_str("TePath", w) + END) for w in self.wad_sound_paths)
        b += chunk("TeOldWadSoundPaths", chunk("TeOldWadSoundUpdateTag1_0_8") + sp + END)
        if self.script_directory:
            b += c_str("TeScriptDirectory", self.script_directory)
        # Game paths and the Lua script are left to Tomb Editor defaults unless set.
        if self.game_directory:
            b += c_str("TeGameDirectory", self.game_directory)
        if self.game_level_path:
            b += c_str("TeGameLevelFilePath", self.game_level_path)
        if self.game_exe:
            b += c_str("TeGameExecutableFilePath", self.game_exe)
        b += c_int("TeGameVersion", GAME_TOMBENGINE)
        b += c_vec3("TeDefaultAmbientLight", self.ambient)
        b += c_int("TeSoundSystem", SOUND_SYSTEM_XML)
        b += c_int("TeLastRoom", 0)
        if self.lua_script:
            b += c_str("TenLuaScriptFile", self.lua_script)
        wads = b"".join(chunk("TeWad", c_str("TePath", w) + END) for w in self.wads)
        b += chunk("TeWads", wads + END)
        cats = b"".join(chunk("TeSoundsCatalog", c_str("TeSoundsCatalogPath", c) + END) for c in self.sound_catalogs)
        b += chunk("TeSoundsCatalogs", cats + END)
        b += chunk("TeSelectedSounds", END)
        b += self._textures_chunk()
        b += chunk("TeImportedGeometries", END)
        b += chunk("TeAnimatedTextureSets", END)
        b += chunk("TeGlobalEventSets", END)
        b += chunk("TeVolumeEventSets", END)
        b += END
        return chunk("TeSettings", bytes(b))

    def _room(self, r):
        b = bytearray(leb(r.nx) + leb(r.nz))
        b += c_int("TeI", r.index)
        b += c_str("TeName", r.name)
        b += c_vec3("TePos2", (float(r.x), float(r.y), float(r.z)))
        b += chunk("TeTags", " ".join(r.tags).encode("utf-8"))
        secs = bytearray()
        for z in range(r.nz):
            for x in range(r.nx):
                secs += r.sectors[x][z].encode(x + z * r.nx)
        b += chunk("TeSecs", bytes(secs) + END)
        b += c_vec3("TeAmbient", r.ambient)
        b += c_bool("TeCold", False)
        b += c_bool("TeNoCaustics", False)
        b += c_bool("TeDmg", False)
        b += c_bool("TeHorizon", r.horizon)
        b += c_bool("TeOutside", r.outside)
        b += c_bool("TeNoLens", r.no_lensflare)
        b += c_bool("TeNoPath", r.no_path)
        b += c_int("TeRoomType", r.room_type)
        b += c_int("TeRoomTypeStrength", 0)
        b += c_int("TeRoomLightEffect", r.light_effect)
        b += c_int("TeRoomLightEffectStrength2", 1)
        b += c_int("TeReverb", r.reverb)
        b += c_int("TeRoomLightInt", 0)
        b += c_bool("TeLocked", False)
        b += c_bool("TeHidden", False)
        if r.alternate is not None:
            group, other = r.alternate
            b += chunk("TeAlternate", c_int("TeGroup", group) + c_int("TeRoom", other.index) + END)
        b += chunk("TeObjects", b"".join(enc() for enc in r.objects) + END)
        b += END
        return chunk("TeRoom", bytes(b))

    def save(self, path):
        data = bytearray(MAGIC + struct.pack("<I", 0))
        data += self._settings()
        data += chunk("TeRooms", b"".join(self._room(r) for r in self.rooms) + END)
        data += END
        with open(path, "wb") as f:
            f.write(data)
        return len(data)
