"""Generic texturing for enclosed rooms (interiors, caves, water rooms).

Wall sectors own the faces towards their open neighbours (TombLib RoomGeometry): a floor part
(wall floor down to neighbour floor), a middle part and a ceiling part (wall ceiling up to the
neighbour ceiling). Every face must fit in 256 x 256 px (2 m at 128 px/m), so wall sectors get
their floor/ceiling at a mid height plus extra floor/ceiling splits every 2 m.
"""
import numpy as np

import prj2
from texturing import DIRS, h32, wall_order

M = 512
SEG = 1024
PX = 128 * 255.5 / 256.0  # 2 m = 255.5 px
SIZE = 2048


class Atlases:
    def __init__(self, atlases):
        self.a = atlases  # list of atlas json dicts, index = texture index in the level

    def find(self, name):
        for i, a in enumerate(self.a):
            if name in a["columns"]:
                return i, "col", a["columns"][name]
            if name in a["tiles"]:
                return i, "tile", a["tiles"][name]
        raise KeyError(name)

    def tile_coords(self, name, rot=0):
        i, kind, (x0, y0, x1, y1) = self.find(name)
        q = [(x0 + 0.5, y0 + 0.5), (x1 - 0.5, y0 + 0.5), (x1 - 0.5, y1 - 0.5), (x0 + 0.5, y1 - 0.5)]
        r = rot % 4
        return i, q[r:] + q[:r]

    def vertical(self, name, world, ref=None):
        """world = heights (m) of TL, TR, BR, BL. Returns (texture index, coords)."""
        i, kind, (x0, y0, x1, y1) = self.find(name)
        if kind == "tile":
            lo, hi = min(world), max(world)
            span = max(hi - lo, 1e-6)
            v = [y1 - 0.5 - (h - lo) / span * min(255.0, span * PX) for h in world]
            return i, wall_order([(x0 + 0.5, v[0]), (x1 - 0.5, v[1]), (x1 - 0.5, v[2]), (x0 + 0.5, v[3])])
        if ref is None:
            lo = min(world[2], world[3])
            ref = lo - (lo % 14.0)
        v = [SIZE - 0.5 - (h - ref) * PX for h in world]
        if max(v) - min(v) > 255.5:
            vmax = max(v)
            span = max(v) - min(v)
            v = [vmax - (vmax - y) * 255.0 / span for y in v]
        v = [float(np.clip(y, 0.5, SIZE - 0.5)) for y in v]
        return i, wall_order([(x0 + 0.5, v[0]), (x1 - 0.5, v[1]), (x1 - 0.5, v[2]), (x0 + 0.5, v[3])])


def floor_face_coords(f, split, coords):
    """Floor or ceiling coords for a sector, handling quad/triangle layouts (see RoomGeometry)."""
    tl, tr, br, bl = coords
    xnzp, xpzp, xpzn, xnzn = f
    if xpzp - xpzn == xnzp - xnzn and xpzp - xnzp == xpzn - xnzn:
        return [(0, [tl, tr, br, bl])]
    if split:
        return [(0, [tr, br, bl, bl]), (1, [bl, tl, tr, tr])]
    return [(0, [tl, tr, br, br]), (1, [br, bl, tl, tl])]


def set_floor(sector, atlases, name, rot=0, blend=0):
    ti, coords = atlases.tile_coords(name, rot)
    for k, c in floor_face_coords(sector.floor, sector.fsplit, coords):
        sector.set_tex(prj2.F_FLOOR if k == 0 else prj2.F_FLOOR_TRI2, c, ti, blend)


def set_ceiling(sector, atlases, name, rot=0, blend=0):
    ti, coords = atlases.tile_coords(name, rot)
    for k, c in floor_face_coords(sector.ceil, sector.csplit, coords):
        sector.set_tex(prj2.F_CEILING if k == 0 else prj2.F_CEILING_TRI2, c, ti, blend)


def _is_open(room, x, z):
    if x <= 0 or z <= 0 or x >= room.nx - 1 or z >= room.nz - 1:
        return False
    return not room.sectors[x][z].wall


def texture_walls(room, atlases, column_fn, portal_sides=(), invisible=False, open_portals_only=False):
    """Prepare and texture all wall sectors of a room that face open sectors.

    column_fn(room, wx, wz, d) -> (column name, ref height in metres or None).
    portal_sides: subset of {"-x", "+x", "-z", "+z"}; border sectors on those sides are portals
    and are skipped. invisible=True hides the faces (zone edges).
    """
    n_x, n_z = room.nx, room.nz
    for x in range(n_x):
        for z in range(n_z):
            w = room.sectors[x][z]
            border = x in (0, n_x - 1) or z in (0, n_z - 1)
            if (x in (0, n_x - 1)) and (z in (0, n_z - 1)):
                continue
            if border:
                side = "-x" if x == 0 else "+x" if x == n_x - 1 else "-z" if z == 0 else "+z"
                if side in portal_sides and (not open_portals_only or not w.wall):
                    continue
            elif not w.wall:
                continue
            opens = []
            for d, (oi, pi, (dx, dz)) in DIRS.items():
                if _is_open(room, x + dx, z + dz):
                    opens.append((d, room.sectors[x + dx][z + dz]))
            if not opens:
                continue
            fmax = max(max(s.floor) for _, s in opens)
            fmin = min(min(s.floor) for _, s in opens)
            cmin = min(min(s.ceil) for _, s in opens)
            cmax = max(max(s.ceil) for _, s in opens)
            mid = min(fmax + SEG, cmin) if cmin > fmax else fmax
            mid = int(round(mid / 64.0)) * 64
            w.floor = [mid] * 4
            w.ceil = [mid] * 4
            w.fsplits = [[mid - SEG * k] * 4 for k in range(1, 9) if mid - SEG * k > fmin]
            w.csplits = [[mid + SEG * k] * 4 for k in range(1, 9) if mid + SEG * k < cmax]
            for d, s in opens:
                oi, pi, _ = DIRS[d]
                if invisible:
                    for k in range(9):
                        w.set_invisible(prj2.f_wall_floor(d, k))
                        w.set_invisible(prj2.f_wall_ceiling(d, k))
                    w.set_invisible(prj2.F_WALL_MIDDLE[d])
                    continue
                col, ref = column_fn(room, room.x + x, room.z + z, d)
                world = lambda hs: [(h + room.y) / M for h in hs]  # noqa: E731
                nbf = (s.floor[pi[0]], s.floor[pi[1]])
                nbc = (s.ceil[pi[0]], s.ceil[pi[1]])
                # Floor part.
                tops = [(w.floor[oi[0]], w.floor[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in w.fsplits]
                for k, top in enumerate(tops):
                    bot = nbf
                    if k + 1 < len(tops) and tops[k + 1][0] >= nbf[0] and tops[k + 1][1] >= nbf[1]:
                        bot = tops[k + 1]
                    if top[0] <= bot[0] and top[1] <= bot[1]:
                        continue
                    ti, c = atlases.vertical(col, world([top[0], top[1], bot[1], bot[0]]), ref)
                    w.set_tex(prj2.f_wall_floor(d, k), c, ti)
                # Middle part.
                lo = (max(w.floor[oi[0]], nbf[0]), max(w.floor[oi[1]], nbf[1]))
                hi = (min(w.ceil[oi[0]], nbc[0]), min(w.ceil[oi[1]], nbc[1]))
                if hi[0] > lo[0] or hi[1] > lo[1]:
                    ti, c = atlases.vertical(col, world([hi[0], hi[1], lo[1], lo[0]]), ref)
                    w.set_tex(prj2.F_WALL_MIDDLE[d], c, ti)
                # Ceiling part.
                bots = [(w.ceil[oi[0]], w.ceil[oi[1]])] + [(sp[oi[0]], sp[oi[1]]) for sp in w.csplits]
                for k, bot in enumerate(bots):
                    top = nbc
                    if k + 1 < len(bots) and bots[k + 1][0] <= nbc[0] and bots[k + 1][1] <= nbc[1]:
                        top = bots[k + 1]
                    if bot[0] >= top[0] and bot[1] >= top[1]:
                        continue
                    ti, c = atlases.vertical(col, world([top[0], top[1], bot[1], bot[0]]), ref)
                    w.set_tex(prj2.f_wall_ceiling(d, k), c, ti)


def rot_for(wx, wz):
    return h32("rot", wx, wz) % 4
