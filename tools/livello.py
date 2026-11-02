"""The v9 template for levels 2-6: a compact 62 x 62 sector zone (about 120 x 120 m) in three bands.

    z 43..59  NORTH   start; an order puzzle (step by three landmarks in the right order) opens gate 1
    z 41..42  wall 1  (6 m, across the whole zone and the water) with gate 1 at x = GATE1
    z 23..40  MIDDLE  the item of the level (dropped by an enemy, under water or on a climbable pillar),
                      used on a device beside gate 2
    z 21..22  wall 2  with gate 2 at x = GATE2
    z  2..20  SOUTH   the leader of the gang; the level ends at the exit once he is dead

Only mechanics already proven in game at Oliveri: the courtyard gate (CANCELLO + DOOR_TYPE1 opened by
CDV.Enable), an item used on a device (Action opens the inventory on it), climbable walls, Lua zones,
drops and secrets. A tall rock ring hides the edge of the map. Gates are approached from +z, as at
Oliveri (the door at rotation 0 closes the sector south of it).
"""
import kit as K
import zona as Z
from kit import CLICK

G_M = 2.0
WALL_M = 6.0
RING_M = 16.0
WALL1, WALL2 = (41, 42), (21, 22)
GZ1, GZ2 = 43, 23


def frame(lat, lon):
    return (lat, lon, 0.0, (0.0, 0.0, 118.0, 118.0))


def paint_base(world, spec):
    P = Z.Painter(world, G_M)
    P.ring(RING_M)
    P.w.mat[2:60, 2:60] = spec.get("mat", "terra")
    spec["paint"](P)
    for (z0, z1), px in ((WALL1, spec["gate1"]), (WALL2, spec["gate2"])):
        if spec.get("walls", "rock") == "rock":     # a cliff band with a cut for the gate
            P.rock(2, px - 1, z0, z1, G_M + WALL_M)
            P.rock(px + 1, 59, z0, z1, G_M + WALL_M)
        else:                                      # a row of houses (town levels)
            P.block("muro_%d" % z0, 2, px - 1, z0, z1, G_M + WALL_M)
            P.block("muro_%d_e" % z0, px + 1, 59, z0, z1, G_M + WALL_M)
        P.ground(px, px, z0, z1, G_M, "lastricato")
        P.ground(px - 1, px + 1, z1 + 1, z1 + 2, G_M, "lastricato")      # the landing in front of the gate
        P.ground(px - 1, px + 1, z0 - 2, z0 - 1, G_M, "lastricato")      # and behind it
    world.zona = P
    return P


def place_seq(ctx, spec):
    k, lua = ctx.kit, ctx.lua
    G = Z.u(G_M)
    pts = []
    for model, x, z, rot in spec["seq"]:
        k.prop(model, x + 0.5, z + 0.5, rot=rot, h=ctx.ground(x, z))
        pts.append(k.lua_pos(x, z, ctx.ground(x, z)))
    g1 = spec["gate1"]
    Z.gate(ctx, g1, GZ1, G, "cancello1")
    lua.sequence("ordine", pts, 1100, spec["seq_step"], spec["seq_bad"], spec["seq_done"], Z.open_gate_fn("cancello1"))
    lua.zone("cancello1_chiuso", k.lua_pos(g1, GZ1, G), r=1300, dy=900, once=False, secs=7,
             need='not CDV.Flag("ordine_done")', text=spec["seq_hint"])


def place_item_gate(ctx, spec):
    """Gate 2 opens when the item (or both items, spec["item"] = (a, b)) is used on the device beside it."""
    k, lua = ctx.kit, ctx.lua
    G = Z.u(G_M)
    g2 = spec["gate2"]
    Z.gate(ctx, g2, GZ2, G, "cancello2")
    items = spec["item"] if isinstance(spec["item"], tuple) else (spec["item"],)
    dx, dz = spec.get("device_at", (g2 - 0.5, GZ2))
    k.prop(spec.get("device", "ARGANO"), dx, dz, rot=spec.get("device_rot", 0.0), h=G)
    p = k.lua_pos(int(dx), int(dz), G, dx=dx - int(dx), dz=dz - int(dz))
    r = spec.get("device_r", 1300)
    opened = Z.open_gate_fn("cancello2")
    if len(items) == 1:
        a = items[0]
        lua.use("chiave2", "ID.PUZZLE_ITEM%d" % a, p, r=r, dy=900, text=spec["device_text"], fn=opened)
        lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, %d, ID.PUZZLE_ITEM%d, "use_chiave2") end)' % (p[0], p[1], p[2], r - 200, a))
        done = 'CDV.Done("use_chiave2")'
        have = "CDV.Has(ID.PUZZLE_ITEM%d)" % a
    else:
        a, b = items
        # either item first: the first one is set in place (flag), the second one opens the gate
        for uid, it, other in (("astro_a", a, b), ("astro_b", b, a)):
            lua.use(uid, "ID.PUZZLE_ITEM%d" % it, p, r=r, dy=900,
                    text=spec["device_half"], fn='CDV.Flag("posati", (CDV.Flag("posati") or 0) + 1)\n'
                    'if CDV.Flag("posati") == 2 then CDV.Say(%s, 8)\n%s\nend' % (repr_lua(spec["device_text"]), opened.replace("\n", "\n    ")))
            lua.add('CDV.Loop(function() CDV.KeyPromptAt(%d, %d, %d, %d, ID.PUZZLE_ITEM%d, "use_%s") end)' % (p[0], p[1], p[2], r - 200, it, uid))
        done = '(CDV.Flag("posati") == 2)'
        have = "(CDV.Has(ID.PUZZLE_ITEM%d) or CDV.Has(ID.PUZZLE_ITEM%d))" % (a, b)
    lua.zone("cancello2_senza", k.lua_pos(g2, GZ2, G), r=1300, dy=900, once=False, secs=7,
             need='not %s and not %s' % (done, have), text=spec["gate2_hint"])
    lua.zone("cancello2_con", k.lua_pos(g2, GZ2, G), r=1300, dy=900, once=False, secs=6,
             need='not %s and %s' % (done, have), text=spec.get("gate2_have", "Ce l'ho. Davanti al congegno accanto al cancello, Azione."))


def place_end(ctx, spec, next_index):
    k, lua = ctx.kit, ctx.lua
    bx, bz = k.spot(*spec["boss"])
    k.place(K.BADDY2, bx, bz, rot=0.0, name="capo")
    for i, (t, x, z) in enumerate(spec.get("south_enemies", [])):
        k.place(t, *k.spot(x, z), rot=0.0, name="sud%d" % i)
    lua.zone("sud", k.lua_pos(spec["gate2"], GZ2 - 4, Z.u(G_M)), r=2600, dy=2000,
             fn="\n".join(['CDV.Enable("capo")'] + ['CDV.Enable("sud%d")' % i for i in range(len(spec.get("south_enemies", [])))]),
             text=spec["south_text"])
    ex, ez = spec["exit"]
    h = ctx.ground(ex, ez)
    lua.zone("fine", k.lua_pos(ex, ez, h), r=1800, dy=2500, need='CDV.Dead("capo")', fn=spec.get("end_fn", "CDV.End(%d, 1)" % (next_index or 0)),
             text=spec["end_text"])
    lua.zone("fine_no", k.lua_pos(ex, ez, h), r=1800, dy=2500, once=False, secs=5, need='not CDV.Dead("capo")',
             text=spec["end_no"])


def place_common(ctx, spec):
    """Enemies of the north and middle bands (enabled by zones), pickups, secrets."""
    k, lua = ctx.kit, ctx.lua
    for band, (zx, zz) in (("nord", spec["north_zone"]), ("centro", (spec["gate1"], GZ1 - 4))):
        group = spec.get(band + "_enemies", [])
        for i, (t, x, z) in enumerate(group):
            k.place(t, *k.spot(x, z), rot=180.0, name="%s%d" % (band, i))
        if group:
            lua.zone(band, k.lua_pos(zx, zz, ctx.ground(zx, zz)), r=3000, dy=2500,
                     fn="\n".join('CDV.Enable("%s%d")' % (band, i) for i in range(len(group))),
                     text=spec.get(band + "_text"))
    for t, x, z in spec.get("pickups", []):
        k.place(t, *k.spot(x, z))
    for idx, (x, z, h_m, text) in spec.get("secrets", {}).items():
        h = Z.u(h_m) if h_m is not None else ctx.ground(x, z)
        lua.secret(idx, k.lua_pos(x, z, h), r=900, text=text, give="ID.SMALLMEDI_ITEM")


def start(ctx, spec):
    k, lua = ctx.kit, ctx.lua
    sx, sz = k.spot(*spec["start"])
    k.place(K.LARA, sx, sz, rot=180.0, name="lara_start")
    k.place(K.LARA_START_POS, sx, sz, ocb=1)
    lua.start('CDV.Say(%s, 8)' % repr_lua(spec["start_text"]))


def repr_lua(s):
    import luagen
    return luagen.lua_str(s)


def build(ctx, spec, next_index):
    ctx.decor_block = [(0, 0, 62, 62)]      # no random decoration: every prop is placed on purpose
    start(ctx, spec)
    place_seq(ctx, spec)
    place_item_gate(ctx, spec)
    place_common(ctx, spec)
    place_end(ctx, spec, next_index)
    if "extra" in spec:
        spec["extra"](ctx)
    for model, x, z, rot in spec.get("props", []):
        ctx.kit.prop(model, x, z, rot=rot, h=ctx.ground(int(x), int(z)))
    for x, z, r in spec.get("lights", []):
        room = ctx.kit.room_at(int(x), int(z))
        ctx.level.add_light(room, 0, ((x - room.x) * 1024, ctx.ground(int(x), int(z)) + 1600 - room.y, (z - room.z) * 1024),
                            color=(1.0, 0.82, 0.6), intensity=0.6, inner=1.5, outer=r)
    # the zone is small: enemies may chase Lara anywhere on land, so every terrain room gets pathfinding
    for rm in ctx.level.rooms:
        if rm.name.startswith("T_"):
            rm.no_path = False
    ctx.notes += spec["notes"]
