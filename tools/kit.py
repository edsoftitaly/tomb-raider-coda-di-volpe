"""Level-building kit: object placement, interiors from ASCII plans, vertical links, triggers, Lua.

Coordinates: world sector (wx, wz) as in world.World; heights in Tomb Editor units (1 click = 256,
1 sector = 1024 = 2 m), absolute (room.y + local). In TombEngine scripts Y points down, so Lua
positions are (x, -h, z).
"""
import numpy as np

import prj2
import walls
from texturing import DIRS

CLICK = prj2.CLICK
SECTOR = 1024

# Slot ids (Tomb Editor TombEngine catalog).
LARA, MOTORBIKE = 0, 65
CROW, BIG_RAT, BAT, SHARK, DOG, DOBERMAN = 105, 116, 118, 129, 131, 136
BADDY1, BADDY2, SKELETON = 174, 175, 255
WRAITH1, WRAITH2, WRAITH3, LAGOON_WITCH = 268, 269, 270, 289
TEETH_SPIKES, FLAME_EMITTER, FLAME_EMITTER2, FLAME_EMITTER3 = 341, 359, 360, 361
FLOOR_TRAPDOOR1, ROLLINGBALL, RAISING_BLOCK1 = 378, 383, 389
CEILING_TRAPDOOR1 = 380
KEY_ITEM1, KEY_HOLE1, DOOR_TYPE1 = 548, 700, 850
SEARCH_OBJECT4, PUSHABLE = 420, 436
PUZZLE_ITEM = {i: 499 + i for i in range(1, 17)}
SWITCH_TYPE2, AIRLOCK_SWITCH, WALL_SWITCH1, LEVER_SWITCH, SHOOT_SWITCH1 = 801, 820, 821, 827, 816
DOOR_TYPE3, DOOR_TYPE4, DOOR_TYPE5, UNDERWATER_DOOR1 = 852, 853, 854, 890
PISTOLS_AMMO, UZI_ITEM, UZI_AMMO, SHOTGUN_ITEM, SHOTGUN_AMMO1 = 951, 952, 953, 954, 955
REVOLVER_ITEM, REVOLVER_AMMO = 957, 958
BIGMEDI, SMALLMEDI, FLARE_ITEM = 978, 979, 983
LARA_START_POS, AI_FOLLOW = 1048, 1044
FISH_EMITTER, FIREFLY_EMITTER, BATS_EMITTER, RATS_EMITTER = 114, 1089, 132, 133
EARTHQUAKE = 1024

OBJ_NAMES = {v: k for k, v in list(globals().items()) if k.isupper() and isinstance(v, int)}

# Trigger types / target types.
T_TRIGGER, T_PAD, T_SWITCH, T_KEY, T_PICKUP, T_HEAVY, T_ANTIPAD, T_COMBAT, T_DUMMY, T_ANTI = range(10)
TT_OBJECT, TT_FINISH = 0, 7

ENEMIES = {BADDY1, BADDY2, DOG, DOBERMAN, BIG_RAT, BAT, CROW, SKELETON, WRAITH1, WRAITH2, WRAITH3,
           LAGOON_WITCH, SHARK}


class Interior:
    """An axis-aligned room built from an ASCII plan (top row = north = highest z)."""

    def __init__(self, room, plan, x0, z0, floor_h, anchors):
        self.room = room
        self.plan = plan
        self.x0, self.z0 = x0, z0        # world sector of the first interior cell
        self.floor_h = floor_h           # absolute height of the base floor (units)
        self.anchors = anchors           # letter -> (wx, wz)

    def local(self, wx, wz):
        return wx - self.room.x, wz - self.room.z

    def sector(self, wx, wz):
        lx, lz = self.local(wx, wz)
        return self.room.sectors[lx][lz]


class Kit:
    def __init__(self, ctx):
        self.ctx = ctx
        self.level = ctx.level
        self.atlases = ctx.atlases
        self.names = {}          # Lua name -> (x, h, z) absolute units, room name
        self.interiors = []
        self.pathfinding_rooms = set()
        self.links = []          # world cells of vertical links (holes): kept free of decorations

    # ------------------------------------------------------------------ placement
    def room_at(self, wx, wz):
        return self.ctx.terrain_room_at(wx, wz)

    def spot(self, wx, wz, r=8, flat=192, taken=None):
        """Nearest walkable outdoor sector to (wx, wz): not a building, not water, nearly flat, room interior."""
        w = self.ctx.world
        taken = taken if taken is not None else getattr(self, "_taken", set())
        self._taken = taken
        best = None
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                x, z = int(wx) + dx, int(wz) + dz
                if not (2 <= x < w.nx - 2 and 2 <= z < w.nz - 2) or (x, z) in taken:
                    continue
                if w.building_id[x, z] >= 0 or w.water[x, z] or not w.zone_mask[x, z]:
                    continue
                if getattr(w, "terraced", None) is not None and w.terraced[x, z]:
                    continue
                f = w.floor[x, z]
                if f.max() - f.min() > flat:
                    continue
                if (x - 1) % 30 == 29 or (z - 1) % 30 == 29:
                    pass
                try:
                    room = self.room_at(x, z)
                except KeyError:
                    continue
                d = dx * dx + dz * dz
                if best is None or d < best[0]:
                    best = (d, x, z)
        if best is None and r < 24:
            return self.spot(wx, wz, r=r * 2, flat=flat * 2, taken=taken)
        assert best is not None, "no walkable spot near %s" % ((wx, wz),)
        taken.add((best[1], best[2]))
        return best[1], best[2]

    def floor_at(self, room, wx, wz):
        s = room.sectors[int(wx) - room.x][int(wz) - room.z]
        return room.y + int(np.mean(s.floor))

    def place(self, type_id, wx, wz, room=None, h=None, rot=0.0, ocb=0, name="", dx=0.5, dz=0.5,
              code_bits=0, invisible=False):
        """Place a moveable at the centre (or dx, dz fraction) of world sector (wx, wz)."""
        wx, wz = int(wx), int(wz)
        room = room or self.room_at(wx, wz)
        lx, lz = wx - room.x, wz - room.z
        assert 1 <= lx < room.nx - 1 and 1 <= lz < room.nz - 1, "%s at %s outside room %s" % (
            OBJ_NAMES.get(type_id, type_id), (wx, wz), room.name)
        s = room.sectors[lx][lz]
        assert not s.wall, "%s at %s inside a wall of %s" % (OBJ_NAMES.get(type_id, type_id), (wx, wz), room.name)
        if h is None:
            h = room.y + int(np.mean(s.floor))
        pos = (lx * SECTOR + dx * SECTOR, float(h - room.y), lz * SECTOR + dz * SECTOR)
        oid = self.level.add_moveable(room, type_id, pos, rot_y=rot, ocb=ocb, lua_name=name,
                                      code_bits=code_bits, invisible=invisible)
        if name:
            self.names[name] = ((wx + dx) * SECTOR, h, (wz + dz) * SECTOR, room.name)
        if type_id in ENEMIES:
            room.no_path = False
            self.pathfinding_rooms.add(room.name)
        return oid

    def trigger(self, wx, wz, room=None, trig_type=T_TRIGGER, target=None, target_type=TT_OBJECT, timer=0,
                code_bits=0x1F, one_shot=False, extra=0, size=(1, 1)):
        wx, wz = int(wx), int(wz)
        room = room or self.room_at(wx, wz)
        lx, lz = wx - room.x, wz - room.z
        area = (lx, lz, lx + size[0] - 1, lz + size[1] - 1)
        return self.level.add_trigger(room, area, trig_type, target_type, target, timer=timer, extra=extra,
                                      code_bits=code_bits, one_shot=one_shot)

    def prop(self, name, wx, wz, rot=0.0, h=None, scale=1.0, room=None):
        """A decoration static (CdV_Decorazioni) placed by content: clues, cover, set dressing."""
        from decorate import S as DECOR_IDS
        if name not in DECOR_IDS:
            from decor import santuario_models, santuario_interno_models, casa_models  # noqa: F401  (registers the sanctuary and house pieces)
            from decor.models import MODELS
            DECOR_IDS = dict(DECOR_IDS, **{n: sid for sid, n, _, _ in MODELS})
        room = room or self.room_at(wx, wz)
        lx, lz = int(wx) - room.x, int(wz) - room.z
        if h is None:
            h = room.y + int(np.mean(room.sectors[lx][lz].floor))
        pos = ((wx - room.x) * SECTOR, float(h - room.y), (wz - room.z) * SECTOR)
        self.level.add_static(room, DECOR_IDS[name], pos, rot_y=rot, scale=scale)
        self.links.append((int(wx), int(wz)))   # keep random decorations away from it

    def lua_pos(self, wx, wz, h, dx=0.5, dz=0.5):
        return ((wx + dx) * SECTOR, -h, (wz + dz) * SECTOR)

    # ------------------------------------------------------------------ interiors
    def interior(self, name, plan, x0, z0, floor_h, height, floor_tex, ceil_tex, wall_col,
                 water=False, ambient=(0.45, 0.42, 0.4), raise_map=None, tags=("interno",)):
        """Build a room from an ASCII plan.

        plan rows from north (top) to south; columns west to east; one char per sector:
          '#' wall, '.' floor, '1'..'9' floor raised by N clicks, 'A'..'Z' floor anchor,
          'a'..'z' anchor on a 2-click crate.
        (x0, z0) = world sector of the south-west interior cell (plan's last row, first column).
        """
        rows = [r for r in plan]
        h_cells = len(rows)
        w_cells = max(len(r) for r in rows)
        rows = [r.ljust(w_cells, "#") for r in rows]
        room = prj2.Room(name, w_cells + 2, h_cells + 2, x=x0 - 1, y=floor_h, z=z0 - 1)
        room.ambient = ambient
        room.tags = list(tags)
        if water:
            room.room_type = 3
        anchors = {}
        for r_i, row in enumerate(rows):
            lz = h_cells - r_i
            for c_i, ch in enumerate(row):
                lx = c_i + 1
                s = room.sectors[lx][lz]
                s.ceil = [height] * 4
                if ch == "#":
                    s.wall = True
                    s.floor = [0] * 4
                    continue
                s.wall = False
                rise = 0
                if ch.isdigit():
                    rise = int(ch) * CLICK
                elif ch.isupper():
                    anchors[ch] = (x0 + c_i, z0 + lz - 1)
                elif ch.islower():
                    rise = 2 * CLICK
                    anchors[ch] = (x0 + c_i, z0 + lz - 1)
                s.floor = [rise] * 4
        for lx in range(room.nx):
            for lz in range(room.nz):
                s = room.sectors[lx][lz]
                if s.wall:
                    s.ceil = [height] * 4
        self.level.add_room(room)
        it = Interior(room, rows, x0, z0, floor_h, anchors)
        it.floor_tex, it.ceil_tex, it.wall_col = floor_tex, ceil_tex, wall_col
        it.portal_sides = set()
        self.interiors.append(it)
        return it

    def finish_interiors(self):
        """Texture every interior (after all portals are known)."""
        for it in self.interiors:
            room = it.room
            for lx in range(1, room.nx - 1):
                for lz in range(1, room.nz - 1):
                    s = room.sectors[lx][lz]
                    if s.wall:
                        continue
                    rot = walls.rot_for(room.x + lx, room.z + lz)
                    if s.tex is None or prj2.F_FLOOR not in s.tex:
                        walls.set_floor(s, self.atlases, it.floor_tex, rot)
                    if s.tex is None or prj2.F_CEILING not in s.tex:
                        walls.set_ceiling(s, self.atlases, it.ceil_tex, rot)
            self.texture_steps(it)
            col = it.wall_col
            walls.texture_walls(room, self.atlases, lambda r, wx, wz, d: (col, None),
                                portal_sides=it.portal_sides)

    def texture_steps(self, it):
        """Vertical faces between open sectors of different floor height (crates, steps)."""
        room = it.room
        for lx in range(1, room.nx - 1):
            for lz in range(1, room.nz - 1):
                s = room.sectors[lx][lz]
                if s.wall:
                    continue
                for d, (oi, pi, (dx, dz)) in DIRS.items():
                    o = room.sectors[lx + dx][lz + dz]
                    if o.wall or lx + dx in (0, room.nx - 1) or lz + dz in (0, room.nz - 1):
                        continue
                    top = (s.floor[oi[0]], s.floor[oi[1]])
                    bot = (o.floor[pi[0]], o.floor[pi[1]])
                    if top[0] <= bot[0] and top[1] <= bot[1]:
                        continue
                    hs = [(v + room.y) / 512.0 for v in (top[0], top[1], bot[1], bot[0])]
                    ti, c = self.atlases.vertical(it.wall_col, hs)
                    s.set_tex(prj2.F_WALL_QA[d], c, ti)
                # Ceiling steps: the lower ceiling owns the face up to the neighbour's ceiling.
                for d, (oi, pi, (dx, dz)) in DIRS.items():
                    o = room.sectors[lx + dx][lz + dz]
                    if o.wall or lx + dx in (0, room.nx - 1) or lz + dz in (0, room.nz - 1):
                        continue
                    bot = (s.ceil[oi[0]], s.ceil[oi[1]])
                    top = (o.ceil[pi[0]], o.ceil[pi[1]])
                    if bot[0] >= top[0] and bot[1] >= top[1]:
                        continue
                    hs = [(v + room.y) / 512.0 for v in (top[0], top[1], bot[1], bot[0])]
                    ti, c = self.atlases.vertical(it.wall_col, hs)
                    s.set_tex(prj2.F_WALL_WS[d], c, ti)

    # ------------------------------------------------------------------ portals
    def link_vertical(self, lower, upper, cells, opacity=0):
        """Floor portal in `upper`, ceiling portal in `lower`, over world cells (list of (wx, wz)).

        Heights: the lower room's ceiling at those cells becomes the upper room's floor there.
        """
        cells = sorted(set((int(a), int(b)) for a, b in cells))
        self.links.extend(cells)
        xs = [c[0] for c in cells]
        zs = [c[1] for c in cells]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        assert len(cells) == (x1 - x0 + 1) * (z1 - z0 + 1), "vertical link cells must form a rectangle"
        lo_room = lower.room if isinstance(lower, Interior) else lower
        up_room = upper.room if isinstance(upper, Interior) else upper
        for wx, wz in cells:
            ls = lo_room.sectors[wx - lo_room.x][wz - lo_room.z]
            us = up_room.sectors[wx - up_room.x][wz - up_room.z]
            assert not ls.wall and not us.wall, "vertical link through a wall at %s" % ((wx, wz),)
            for rm, (lx, lz) in ((lo_room, (wx - lo_room.x, wz - lo_room.z)), (up_room, (wx - up_room.x, wz - up_room.z))):
                assert 1 <= lx < rm.nx - 1 and 1 <= lz < rm.nz - 1, "vertical link on border of %s" % rm.name
            h_abs = up_room.y + int(np.mean(us.floor))
            ls.ceil = [h_abs - lo_room.y] * 4
            us.floor = [h_abs - up_room.y] * 4
        self.level.add_portal(lo_room, (x0 - lo_room.x, z0 - lo_room.z, x1 - lo_room.x, z1 - lo_room.z),
                              prj2.P_CEILING, up_room, opacity=opacity)
        self.level.add_portal(up_room, (x0 - up_room.x, z0 - up_room.z, x1 - up_room.x, z1 - up_room.z),
                              prj2.P_FLOOR, lo_room, opacity=opacity)

    def link_wall(self, a, b, span=None):
        """Wall portal between two interiors that overlap by two columns/rows (TR adjacency).

        span = (lo, hi) world coordinates along the shared border to limit the opening (default: all).
        """
        ra, rb = a.room, b.room
        if ra.x + ra.nx - 2 == rb.x:      # b east of a
            pa, pb, axis = ("+x", "-x", "x")
        elif rb.x + rb.nx - 2 == ra.x:
            return self.link_wall(b, a, span)
        elif ra.z + ra.nz - 2 == rb.z:    # b north of a
            pa, pb, axis = ("+z", "-z", "z")
        elif rb.z + rb.nz - 2 == ra.z:
            return self.link_wall(b, a, span)
        else:
            raise ValueError("rooms %s and %s are not adjacent" % (ra.name, rb.name))
        if axis == "x":
            z0 = max(ra.z, rb.z) + 1
            z1 = min(ra.z + ra.nz, rb.z + rb.nz) - 2
            if span:
                z0, z1 = max(z0, span[0]), min(z1, span[1])
            self.level.add_portal(ra, (ra.nx - 1, z0 - ra.z, ra.nx - 1, z1 - ra.z), prj2.P_WALL_PX, rb)
            self.level.add_portal(rb, (0, z0 - rb.z, 0, z1 - rb.z), prj2.P_WALL_NX, ra)
            for z in range(z0, z1 + 1):
                for rm, lx, other, olx in ((ra, ra.nx - 1, rb, 1), (rb, 0, ra, ra.nx - 2)):
                    sec, src = rm.sectors[lx][z - rm.z], other.sectors[olx][z - other.z]
                    sec.wall = False
                    sec.floor = [v + other.y - rm.y for v in src.floor]
                    sec.ceil = [v + other.y - rm.y for v in src.ceil]
        else:
            x0 = max(ra.x, rb.x) + 1
            x1 = min(ra.x + ra.nx, rb.x + rb.nx) - 2
            if span:
                x0, x1 = max(x0, span[0]), min(x1, span[1])
            self.level.add_portal(ra, (x0 - ra.x, ra.nz - 1, x1 - ra.x, ra.nz - 1), prj2.P_WALL_PZ, rb)
            self.level.add_portal(rb, (x0 - rb.x, 0, x1 - rb.x, 0), prj2.P_WALL_NZ, ra)
            for x in range(x0, x1 + 1):
                for rm, lz, other, olz in ((ra, ra.nz - 1, rb, 1), (rb, 0, ra, ra.nz - 2)):
                    sec, src = rm.sectors[x - rm.x][lz], other.sectors[x - other.x][olz]
                    sec.wall = False
                    sec.floor = [v + other.y - rm.y for v in src.floor]
                    sec.ceil = [v + other.y - rm.y for v in src.ceil]
        a.portal_sides.add(pa)
        b.portal_sides.add(pb)

    def water_surface(self, air, water, cells, tex="acqua_scura"):
        """Visible water surface between an air room (above) and a water room, over a rectangle."""
        ar = air.room if isinstance(air, Interior) else air
        wr = water.room if isinstance(water, Interior) else water
        cells = [(x, z) for x, z in cells
                 if not ar.sectors[x - ar.x][z - ar.z].wall and not wr.sectors[x - wr.x][z - wr.z].wall]
        xs = [c[0] for c in cells]
        zs = [c[1] for c in cells]
        x0, z0 = min(xs), min(zs)
        mask = np.zeros((max(xs) - x0 + 1, max(zs) - z0 + 1), dtype=bool)
        for x, z in cells:
            mask[x - x0, z - z0] = True
        from world import rectangles
        for (a, b, c, d) in rectangles(mask):
            self.link_vertical(water, air, rect(x0 + a, z0 + b, x0 + c, z0 + d), opacity=2)
        for wx, wz in cells:
            rot = walls.rot_for(wx, wz)
            walls.set_floor(ar.sectors[wx - ar.x][wz - ar.z], self.atlases, tex, rot, blend=2)
            walls.set_ceiling(wr.sectors[wx - wr.x][wz - wr.z], self.atlases, tex, rot, blend=2)

    def lever_spot(self, wx, wz, r=10):
        """Flat outdoor sector with flat, level neighbours north and south (floor levers are pushed from both sides)."""
        w = self.ctx.world
        taken = getattr(self, "_taken", set())
        self._taken = taken
        best = None
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                x, z = int(wx) + dx, int(wz) + dz
                cells = [(x, z - 1), (x, z), (x, z + 1)]
                if any(w.building_id[c] >= 0 or w.water[c] or c in taken for c in cells):
                    continue
                fs = [w.floor[c] for c in cells]
                if max(f.max() - f.min() for f in fs) > 128 or max(f.mean() for f in fs) - min(f.mean() for f in fs) > 128:
                    continue
                d = dx * dx + dz * dz
                if best is None or d < best[0]:
                    best = (d, x, z)
        assert best is not None, "no lever spot near %s" % ((wx, wz),)
        for c in ((best[1], best[2] - 1), (best[1], best[2]), (best[1], best[2] + 1)):
            taken.add(c)
        return best[1], best[2]

    def wall_spot(self, wx, wz, r=10, flat=192):
        """Walkable outdoor sector next to a building/raised block: returns (x, z, lever rotation)."""
        w = self.ctx.world
        best = None
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                x, z = int(wx) + dx, int(wz) + dz
                if w.building_id[x, z] >= 0 or w.water[x, z]:
                    continue
                f = w.floor[x, z]
                if f.max() - f.min() > flat:
                    continue
                for d, (ox, oz), rot in (("+z", (0, 1), 180.0), ("-z", (0, -1), 0.0), ("+x", (1, 0), 270.0), ("-x", (-1, 0), 90.0)):
                    nf = w.floor[x + ox, z + oz]
                    if nf.min() - f.max() >= 4 * CLICK:
                        dd = dx * dx + dz * dz
                        if best is None or dd < best[0]:
                            best = (dd, x, z, rot)
        assert best is not None, "no wall spot near %s" % ((wx, wz),)
        return best[1], best[2], best[3]

    def climb(self, wx, wz, direction, room=None):
        """Climbable wall on side `direction` (+x, -x, +z, -z) of the walkable sector (wx, wz)."""
        room = room or self.room_at(wx, wz)
        flag = {"+z": 256, "-z": 512, "+x": 1024, "-x": 2048}[direction]
        room.sectors[wx - room.x][wz - room.z].flags |= flag


# ---------------------------------------------------------------------- terrain editing (prepare)
def flatten(world, cells, h=None, mat=None):
    """Set the terrain floor of world cells to one height (units); default = rounded mean."""
    cells = [(int(x), int(z)) for x, z in cells]
    if h is None:
        h = int(round(np.mean([world.floor[x, z].mean() for x, z in cells]) / 64.0)) * 64
    for x, z in cells:
        world.floor[x, z, :] = h
        world.floor_terrain[x, z, :] = h
        if mat:
            world.mat[x, z] = mat
    return h


def rect(x0, z0, x1, z1):
    return [(x, z) for x in range(min(x0, x1), max(x0, x1) + 1) for z in range(min(z0, z1), max(z0, z1) + 1)]


def ramp(world, cells, axis, a0, a1, h0, h1, mat="lastricato"):
    """Linear ramp over cells: height h0 at coordinate a0 to h1 at a1 along axis 'x' or 'z'.

    Corner heights follow the corner coordinate, so the surface is continuous; every sector tilts
    by (h1 - h0) / (a1 - a0) per sector, which must stay within 2 clicks (no sliding).
    """
    slope = (h1 - h0) / float(a1 - a0)
    assert abs(slope) <= 2 * CLICK + 1, "ramp too steep: %.0f units per sector" % slope
    for x, z in cells:
        # corners XnZp, XpZp, XpZn, XnZn
        cs = [(x, z + 1), (x + 1, z + 1), (x + 1, z), (x, z)]
        for k, (cx, cz) in enumerate(cs):
            a = cx if axis == "x" else cz
            t = min(max((a - a0) / float(a1 - a0), 0.0), 1.0)
            v = int(round((h0 + (h1 - h0) * t) / 64.0)) * 64
            world.floor[x, z, k] = v
            world.floor_terrain[x, z, k] = v
        world.building_id[x, z] = -1
        world.water[x, z] = False
        if mat:
            world.mat[x, z] = mat


# ---------------------------------------------------------------------- validation
def validate(level, names):
    """Static gameplay checks on the in-memory level. Returns a list of problems."""
    problems = []
    rooms = level.rooms
    for rm in rooms:
        for m in rm.meta:
            if m[0] == "moveable":
                _, t, pos, name, oid, ocb = m
                lx, lz = int(pos[0] // SECTOR), int(pos[2] // SECTOR)
                s = rm.sectors[lx][lz]
                fl = int(np.mean(s.floor))
                cl = int(np.mean(s.ceil))
                if s.wall:
                    problems.append("%s %s in a wall (%s)" % (OBJ_NAMES.get(t, t), name, rm.name))
                    continue
                if t in (BAT, FLAME_EMITTER, FLAME_EMITTER2, FLAME_EMITTER3, FIREFLY_EMITTER, FISH_EMITTER,
                         SHARK, LAGOON_WITCH, CROW, WRAITH1, WRAITH2, WRAITH3) or rm.room_type == 3:
                    continue
                if abs(pos[1] - fl) > 300:
                    problems.append("%s %s floats/buried: y %d floor %d (%s)" % (OBJ_NAMES.get(t, t), name, pos[1], fl, rm.name))
                if cl - fl < 3 * CLICK and not rm.outside:
                    problems.append("%s %s: only %d units of headroom (%s)" % (OBJ_NAMES.get(t, t), name, cl - fl, rm.name))
            elif m[0] == "trigger":
                _, area, tt, tgt_type, tgt = m
                for x in range(area[0], area[2] + 1):
                    for z in range(area[1], area[3] + 1):
                        if rm.sectors[x][z].wall:
                            problems.append("trigger on a wall sector in %s at %s" % (rm.name, (x, z)))
    return problems
