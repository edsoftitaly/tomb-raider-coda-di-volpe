"""Geometry of the house staircase: one-sector flights (2 x 2 m, rising 1 m), landings, railings.

Shared by the decoration statics (flights drawn over an invisible sector ramp) and by the TEN bridge
moveables in CdV_Oggetti.wad2 (flights and landings that float over the stair well).

Local frame of a flight: origin at the centre of the sector, the flight rises toward +x, y = 0 at the
high end (x = +1 m) and y = -1 m at the low end (x = -1 m). The walking plane is y = (x - 1) / 2: that is
what the engine collides with (sector ramp, or BRIDGE_TILT2: box top at the high end, 2 clicks per sector).
Six steps of 33 x 16.7 cm; every tread sits on the plane at its own centre, so the feet never sink or
float by more than half a riser (8 cm).
"""
from decor import geom as G
from decor.santuario_models import UP, V, fface

N_STEPS = 6
RUN = 2.0 / N_STEPS
RISE = 1.0 / N_STEPS
HW = 0.99                   # half width of the treads (1 cm inside the sector edge: no z-fighting)


def plane(x):
    return (x - 1.0) / 2.0


def steps(m, tread, riser=None, hw=HW):
    """The six marble steps; each block reaches one riser below the plane, so its sides show the
    stepped profile above whatever is under it (the plastered ramp or the stringer)."""
    riser = riser or tread
    for i in range(N_STEPS):
        x0, x1 = -1.0 + i * RUN, -1.0 + (i + 1) * RUN
        top = -1.0 + (i + 0.5) * RISE
        bot = plane(x0) - RISE
        # tread with a 2 cm nosing over the riser below
        fface(m, [V(x0 - 0.02, top, -hw), V(x1, top, -hw), V(x1, top, hw), V(x0 - 0.02, top, hw)], tread, UP,
              uv=[(0, 0), (1, 0), (1, 0.18), (0, 0.18)])
        fface(m, [V(x0 - 0.02, top - 0.03, -hw), V(x0 - 0.02, top - 0.03, hw), V(x0 - 0.02, top, hw), V(x0 - 0.02, top, -hw)],
              tread, V(-1, 0, 0), uv=[(0, 0.2), (1, 0.2), (1, 0.23), (0, 0.23)])
        fface(m, [V(x0, bot, -hw), V(x0, bot, hw), V(x0, top - 0.03, hw), V(x0, top - 0.03, -hw)], riser, V(-1, 0, 0),
              uv=[(0, 0.3), (1, 0.3), (1, 0.42), (0, 0.42)])
        for z, nz in ((-hw, -1.0), (hw, 1.0)):
            fface(m, [V(x0, bot, z), V(x1, bot, z), V(x1, top, z), V(x0, top, z)], tread, V(0, 0, nz),
                  uv=[(0, 0.5), (0.3, 0.5), (0.3, 0.62), (0, 0.62)])


def flight_static(tread="tn_marmo"):
    m = G.Mesh()
    steps(m, tread)
    return m


def flight_bridge(tread, plaster, stringer=None, depth=0.5):
    """A self-supporting flight: steps, a plastered soffit `depth` below the plane (the engine's ceiling
    under a tilted bridge is 1 click = 0.5 m under its plane), stringers on both sides, end caps."""
    stringer = stringer or plaster
    m = G.Mesh()
    steps(m, tread)
    xa, xb = -0.98, 0.98
    ya, yb = plane(xa), plane(xb)
    # soffit
    fface(m, [V(xa, ya - depth, -1.0), V(xb, yb - depth, -1.0), V(xb, yb - depth, 1.0), V(xa, ya - depth, 1.0)],
          plaster, V(0.45, -1, 0), uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    # stringers: from the soffit to a little above the plane, 1 cm outside the steps
    for z, nz in ((-1.0, -1.0), (1.0, 1.0)):
        fface(m, [V(xa, ya - depth, z), V(xb, yb - depth, z), V(xb, yb + 0.06, z), V(xa, ya + 0.06, z)], stringer,
              V(0, 0, nz), uv=[(0, 1), (1, 1), (1, 0), (0, 0)])
    # end caps (the soffit meets the landing slab or the floor above)
    for x, y, nx in ((xa, ya, -1.0), (xb, yb, 1.0)):
        fface(m, [V(x, y - depth, -1.0), V(x, y - depth, 1.0), V(x, y - 0.02, 1.0), V(x, y - 0.02, -1.0)], plaster,
              V(nx, 0, 0), uv=[(0, 1), (1, 1), (1, 0), (0, 0)])
    return m


def landing(tread, plaster, thick=0.2, hw=1.0):
    """Flat landing slab, one sector, top at y = 0."""
    m = G.Mesh()
    fface(m, [V(-hw, 0, -hw), V(hw, 0, -hw), V(hw, 0, hw), V(-hw, 0, hw)], tread, UP, uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    fface(m, [V(-hw, -thick, -hw), V(-hw, -thick, hw), V(hw, -thick, hw), V(hw, -thick, -hw)], plaster, -UP,
          uv=[(0, 0), (1, 0), (1, 1), (0, 1)])
    for a, b, n in (((-hw, -hw), (hw, -hw), V(0, 0, -1)), ((hw, -hw), (hw, hw), V(1, 0, 0)),
                    ((hw, hw), (-hw, hw), V(0, 0, 1)), ((-hw, hw), (-hw, -hw), V(-1, 0, 0))):
        fface(m, [V(a[0], -thick, a[1]), V(b[0], -thick, b[1]), V(b[0], 0, b[1]), V(a[0], 0, a[1])], tread, n,
              uv=[(0, 0.5), (1, 0.5), (1, 0.6), (0, 0.6)])
    return m


def railing(m, grille, wood, rise=1.0, h=0.95, length=2.0):
    """Iron balustrade with a walnut handrail along local x, centred on the origin; the base rises by `rise`
    over `length` (0 = horizontal) and passes through y = 0 at x = 0."""
    x0, x1 = -length / 2, length / 2
    y0, y1 = -rise / 2, rise / 2
    fface(m, [V(x0, y0, 0), V(x1, y1, 0), V(x1, y1 + h, 0), V(x0, y0 + h, 0)], grille, V(0, 0, -1),
          uv=[(0, 1), (1, 1), (1, 0), (0, 0)], double=True, blend=1)
    m.merge(G.tube([(x0 - 0.03, y0 + h + 0.03, 0), (x1 + 0.03, y1 + h + 0.03, 0)], [0.035, 0.035], wood, n=6))
    for x in (x0 + 0.04, x1 - 0.04):
        y = y0 + (y1 - y0) * (x - x0) / length
        m.merge(G.box(0.05, h + 0.03, 0.05, wood, center=(x, y, 0)))
    return m
