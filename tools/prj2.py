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


class Sector:
    __slots__ = ("wall", "floor", "ceil", "fsplit", "csplit", "flags")

    def __init__(self, floor=(0, 0, 0, 0), ceil=(3072, 3072, 3072, 3072), wall=False):
        self.wall = wall          # True = solid wall sector
        self.floor = list(floor)  # heights XnZp, XpZp, XpZn, XnZn
        self.ceil = list(ceil)
        self.fsplit = False       # SplitDirectionIsXEqualsZ
        self.csplit = False
        self.flags = 0

    def encode(self, index):
        out = bytearray(struct.pack("<i", index))
        out += c_int(SEC_PROPS, (1 if self.wall else 0) | (self.flags << 2))
        out += chunk(SEC_FLOOR, leb(1 if self.fsplit else 0) + b"".join(leb(h) for h in self.floor))
        out += chunk(SEC_CEIL, leb(1 if self.csplit else 0) + b"".join(leb(h) for h in self.ceil))
        out += chunk(SEC_FLOOR_SUB, leb(0))
        out += chunk(SEC_CEIL_SUB, leb(0))
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
        self.room_type = 0        # 0 normal, 1 water (RoomType)
        self.reverb = 0
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
        self._obj_counter = 0

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
        """area = (x0, z0, x1, z1) in room-local sector coordinates."""
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
    def _settings(self):
        b = bytearray()
        b += c_str("TeFontTextureFilePath", "")
        b += c_str("TeSkyTextureFilePath", "")
        b += c_str("TeTr5ExtraSpritesFilePath", "")
        b += chunk("TeOldWadSoundPaths", chunk("TeOldWadSoundUpdateTag1_0_8") + END)
        b += c_str("TeGameDirectory", self.game_directory)
        b += c_str("TeGameLevelFilePath", self.game_level_path)
        b += c_str("TeGameExecutableFilePath", self.game_exe)
        b += c_int("TeGameVersion", GAME_TOMBENGINE)
        b += c_vec3("TeDefaultAmbientLight", self.ambient)
        b += c_int("TeSoundSystem", SOUND_SYSTEM_XML)
        b += c_int("TeLastRoom", 0)
        b += c_str("TenLuaScriptFile", self.lua_script)
        wads = b"".join(chunk("TeWad", c_str("TePath", w) + END) for w in self.wads)
        b += chunk("TeWads", wads + END)
        b += chunk("TeSoundsCatalogs", END)
        b += chunk("TeSelectedSounds", END)
        b += chunk("TeTextures", END)
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
        b += c_bool("TeNoPath", False)
        b += c_int("TeRoomType", r.room_type)
        b += c_int("TeRoomTypeStrength", 0)
        b += c_int("TeRoomLightEffect", 0)
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
