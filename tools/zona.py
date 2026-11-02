"""Hand-designed compact zones for levels 2-6 (v9): the whole terrain of a frame world is painted here,
nothing comes from the map. Same pipeline as Oliveri (prepare -> terrain/water rooms), only proven
mechanics in content (see the content modules).

Units: sectors for x/z (1 sector = 2 m), metres for heights unless a name ends in _u (TR units).
Sea level is 0; land is painted at absolute heights in metres.
"""
import numpy as np

import kit as K
from kit import CLICK

M = 512


def u(h_m):
    """Metres -> units, rounded to a click."""
    return int(round(h_m * M / CLICK)) * CLICK


class Painter:
    def __init__(self, world, ground_m):
        self.w = world
        self.G = u(ground_m)
        w = world
        w.water[:, :] = False
        w.lagoon[:, :] = False
        w.depth[:, :] = 0.0
        w.floor[:, :, :] = self.G
        w.floor_terrain[:, :, :] = self.G
        w.building_id[:, :] = -1
        w.buildings = []
        w.mat[:, :] = "terra"
        self.taken = np.zeros((w.nx, w.nz), bool)

    def rect(self, x0, x1, z0, z1):
        m = np.zeros((self.w.nx, self.w.nz), bool)
        m[max(0, x0):x1 + 1, max(0, z0):z1 + 1] = True
        return m

    def ground(self, x0, x1, z0, z1, h_m, mat):
        m = self.rect(x0, x1, z0, z1)
        h = u(h_m)
        self.w.floor[m] = h
        self.w.floor_terrain[m] = h
        self.w.mat[m] = mat
        self.w.water[m] = False
        self.w.depth[m] = 0.0
        return h

    def water(self, x0, x1, z0, z1, depth_m, lagoon=False):
        m = self.rect(x0, x1, z0, z1)
        self.w.water[m] = True
        self.w.lagoon[m] = lagoon
        self.w.depth[m] = depth_m
        self.w.floor[m] = 0
        self.w.floor_terrain[m] = 0
        self.w.mat[m] = "sabbia"
        self.w.building_id[m] = -1

    def pool(self, x0, x1, z0, z1, depth_m, lagoon=False, mat="sabbia"):
        """Water with a stepped shore all round: 0.25, 0.75, 1.25, 1.75 m terraces (steps of 1 click, which
        Lara climbs without a step animation; she walks out of the water onto the first one)."""
        g = self.G
        for d, h_m in ((4, 1.75), (3, 1.25), (2, 0.75), (1, 0.25)):
            m = self.rect(x0 - d, x1 + d, z0 - d, z1 + d)
            m &= self.w.floor[:, :, 0] > int(h_m * M)
            m &= ~self.w.water
            m[:2, :] = m[-2:, :] = False
            m[:, :2] = m[:, -2:] = False
            h = min(g, int(round(h_m * M / 128.0)) * 128)
            self.w.floor[m] = h
            self.w.floor_terrain[m] = h
            self.w.mat[m] = mat
        self.water(x0, x1, z0, z1, depth_m, lagoon)

    def block(self, name, x0, x1, z0, z1, top_m, base_m=None):
        """A building (or a cliff, a wall): solid up to top_m, walkable roof."""
        m = self.rect(x0, x1, z0, z1)
        bid = len(self.w.buildings)
        self.w.building_id[m] = bid
        top = u(top_m)
        self.w.floor[m] = top
        self.w.floor_terrain[m] = top
        self.w.mat[m] = "terrazza"
        self.w.water[m] = False
        self.w.depth[m] = 0.0
        base = base_m if base_m is not None else self.G / M
        self.w.buildings.append({"id": name, "tags": {"building": "yes"}, "sectors": int(m.sum()),
                                 "ground_m": base, "base_m": base, "roof_m": top / M})
        return bid

    def rock(self, x0, x1, z0, z1, top_m):
        """Natural rock mass (no facade): terrain, rock texture."""
        return self.ground(x0, x1, z0, z1, top_m, "roccia")

    def ramp_x(self, x0, x1, z0, z1, h0_m, h1_m, mat="lastricato"):
        """Walkable ramp along x from height h0 (at x0's west edge) to h1 (at x1's east edge), max 2 clicks/sector."""
        return K.ramp(self.w, K.rect(x0, z0, x1, z1), "x", x0, x1 + 1, u(h0_m), u(h1_m), mat=mat)

    def ramp_z(self, x0, x1, z0, z1, h0_m, h1_m, mat="lastricato"):
        return K.ramp(self.w, K.rect(x0, z0, x1, z1), "z", z0, z1 + 1, u(h0_m), u(h1_m), mat=mat)

    def ring(self, top_m, width=2, name="anello"):
        """Tall rock ring all round the frame: no visible map edge (sea sides get the same, as cliffs)."""
        w = self.w
        nx, nz = w.nx, w.nz
        for (x0, x1, z0, z1) in ((0, width - 1, 0, nz - 1), (nx - width, nx - 1, 0, nz - 1),
                                 (0, nx - 1, 0, width - 1), (0, nx - 1, nz - width, nz - 1)):
            m = self.rect(x0, x1, z0, z1)
            h = u(top_m)
            w.floor[m] = h
            w.floor_terrain[m] = h
            w.mat[m] = "roccia"
            w.water[m] = False
            w.depth[m] = 0.0


def gate(ctx, px, gz, h, name):
    """The courtyard gate of Oliveri, proven in game: an iron leaf (static CANCELLO, hinged at px) on the
    z edge gz of a one-sector passage along z, and an invisible-to-the-eye blocker: the TEN door DOOR_TYPE1
    at (px, gz), rotation 0, closes the sector (px, gz - 1) until CDV.Enable opens it."""
    k = ctx.kit
    k.prop("CANCELLO", px + 0.02, gz, rot=0.0, h=h, lua_name=name + "_anta")
    k.place(K.DOOR_TYPE1, px, gz, rot=0.0, name=name, h=h)


def open_gate_fn(name):
    return 'CDV.Enable("%s")\nCDV.Swing("%s_anta", "y", 90, 50)' % (name, name)


def device(ctx, uid, item, model, x, z, h, rot, text, fn, hint_need=None, r=1300):
    """An item used on a device (the winch of Oliveri, proven): the model on the wall, Action in front of it
    opens the inventory on the item, the use runs fn."""
    k, lua = ctx.kit, ctx.lua
    k.prop(model, x, z, rot=rot, h=h)
    p = k.lua_pos(int(x), int(z), h, dx=x - int(x), dz=z - int(z))
    lua.use(uid, item, p, r=r, dy=900, text=text, fn=fn)
    lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, %d, %s, "use_%s") end)' % (p[0], p[1], p[2], r - 200, item, uid))
    return p
