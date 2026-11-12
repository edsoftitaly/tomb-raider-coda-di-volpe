"""Livello 3 - La meta' perduta (v2, 12/11/2026: the plan approved by Ed).

1 the sea cave under the well of Tindari, the camp of the tombaroli, the siphon
2 the fallen decumanus (hub): a Roman street half under water, at its east end the front of the temple of the
  Dioscuri and its black gate; the gate wants the two caps (pilei) of the twins
3 the baths (north): dry basin -> hypocaust -> the wheel floods everything (flipmap 2) -> up the shaft with the
  water -> Pileo di Castore
4 the house of the mosaic maker and the cistern (south): the mosaic of the house is the map of the slabs of the
  cistern; dark caps hold, golden caps break -> Pileo di Polluce
5 the temple: the Astro di Castore on the altar floods the cella (flipmap 1); lever on the east gallery reached
  by swimming, bronze doors on foot, Turi cannot be shot: he has to be drowned
6 both stars on the altar: the temple falls, 75 seconds: ladder, boulder, daylight
"""
import copy

import numpy as np

import content_marinello2 as M2
import kit as K
import prj2
import walls
from kit import CLICK

# first in the list: their slots win over the same ones in the other wads (BRIDGE_FLAT 1340 = the golden slab)
WADS_FIRST = ["CodaDiVolpe\\CdV_Tempio.wad2", "CodaDiVolpe\\CdV_Domus.wad2", "CodaDiVolpe\\CdV_Gemelli.wad2"]
F_TERME, F_TEMPIO = 2, 1
DEEP = -16 * CLICK
VOID = K.rect(49, 22, 57, 26)
ALTAR = (47, 28)
LEVER = (59, 29)
ESCAPE_FRAMES = 75 * 30
KEY_HOLE7 = 706
PILEO_C, PILEO_P = K.PUZZLE_ITEM[10], K.PUZZLE_ITEM[11]
SHOW_ASTRO_C, SHOW_ASTRO_P, SHOW_PILEO_C, SHOW_PILEO_P = 1204, 1205, 1206, 1207
GATE = (40, 24)
# the cistern: rows z 9..5, columns x 32..40. P = pillar (dark cap, holds), B = slab (golden cap, breaks)
LATTICE = {9: "..P.B.P..", 8: "..B.B.B..", 7: "P.P.B.P.P", 6: "B...B...B", 5: "P.B.P.B.P"}


HELPERS = '''-- A model that is shown only once Lara has put the thing there (with her "use" animation).
function CDV.Put(name)
    Lara:SetAnim(131)          -- LA_USE_KEY with state 42, as at the seal of Marinello
    Lara:SetState(42)
    CDV.After(45, function() CDV.ShowModel(name, true) end)
end
function CDV.Flyby(seq)
    CDV.Log("FLYBY " .. seq)
    pcall(function() TEN.View.PlayFlyby(seq) end)
end
-- A bronze wheel on a wall (KEY_HOLE7): Action in front of it, Lara turns it half a turn, then fn. ok() says
-- whether it can still be turned.
function CDV.Wheel(name, ok, fn)
    local busy = false
    CDV.Loop(function()
        if busy or not ok() then return end
        local m = CDV.M(name)
        if m == nil or not m:GetValid() then return end
        if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) or Lara:GetState() ~= 2 then return end
        local p, r0 = m:GetPosition(), m:GetRotation()
        local a = math.rad(r0.y)
        local sx, sz = p.x - math.sin(a) * 400, p.z - math.cos(a) * 400
        local lp = Lara:GetPosition()
        if (lp.x - sx) ^ 2 + (lp.z - sz) ^ 2 > 420 ^ 2 or math.abs(lp.y - (p.y + 620)) > 300 then return end
        if not CDV.HandsFree() then CDV.Holster() return end
        busy = true
        Lara:SetPosition(TEN.Vec3(math.floor(sx), lp.y, math.floor(sz)), false)
        Lara:SetRotation(TEN.Rotation(0, r0.y, 0))
        Lara:SetAnim(470)
        Lara:SetState(40)
        local f = 0
        local function step()
            f = f + 1
            if f > 40 and f <= 150 then
                pcall(function() m:SetRotation(TEN.Rotation(r0.x, r0.y, (r0.z + 180 * (f - 40) / 110) % 360)) end)
            end
            if f < 220 and (f < 152 or Lara:GetAnim() == 470) then CDV.After(1, step); return end
            busy = false
            fn()
        end
        CDV.After(1, step)
    end)
end'''


def rows(*r):
    assert len(set(len(x) for x in r)) == 1, [len(x) for x in r]
    return list(r)


def build_standalone(ctx):
    k, lua, L = ctx.kit, ctx.lua, ctx.level
    lua.add(HELPERS)
    log = []
    real_add = L.add_portal

    def add_portal(room, area, direction, other, opacity=0):
        log.append((room, area, direction, other, opacity))
        return real_add(room, area, direction, other, opacity=opacity)
    L.add_portal = add_portal
    cave = lambda *a, **kw: M2.cave(k, *a, **kw)      # noqa: E731

    # ================================================================ 1. the well and the sea cave
    p0 = cave("P0_POZZO", ["..", ".."], 3, 30, 0, 24 * CLICK, amb=(0.34, 0.38, 0.42), rough=0)
    a0 = cave("A0_GROTTA", rows("#....######", "......#####", ".......####", "........###", "..........#", "...........",
                                "...........", "...........", "#.........#", "##......###", "###....####"),
              2, 19, 0, 2560, seed=31, rough=448, amb=(0.3, 0.36, 0.4))
    a0w = cave("A0_ACQUA", ["..."] * 4, 9, 22, -2048, 2048, floor="g_bagnato", water=True, amb=(0.16, 0.36, 0.4))
    tun = cave("SIFONE", ["......."] * 2, 12, 23, -2048, 1536, floor="g_bagnato", water=True, amb=(0.12, 0.3, 0.36))
    k.link_wall(a0, p0, span=(3, 4))
    k.water_surface(a0, a0w, K.rect(9, 22, 11, 25))
    k.link_wall(a0w, tun, span=(23, 24))

    # ================================================================ 2. the fallen decumanus
    dw = cave("D_ACQUA", rows(".........", "..3......", ".........", ".....2...", ".........", "........2",
                              "...222555", "...222555", "...222555", ".........", "....3....", ".........",
                              "......2..", ".........", "........."),
              19, 17, -1792, 1792, floor="sabbia_fondo", wall="t_opera_muschio", water=True, amb=(0.14, 0.34, 0.4))
    d = cave("D_DECUMANO", rows("##..................##", "#....................#") + ["......................"] * 11
             + rows("#....................#", "##..................##"),
             19, 17, 0, 20 * CLICK, seed=7, rough=640, amb=(0.33, 0.37, 0.4))
    d.step_col = "t_opera"
    k.link_wall(tun, dw, span=(23, 24))
    k.water_surface(d, dw, K.rect(19, 17, 27, 31))
    # the street, the houses (blocks of masonry, broken at different heights), the front of the temple
    for x in range(28, 40):
        for z in (23, 24, 25):
            walls.set_floor(d.sector(x, z), k.atlases, "t_lastre_muschio" if x < 31 else "t_lastre", walls.rot_for(x, z))
    rng = np.random.default_rng(5)
    houses = [(29, 31, 27, 29), (33, 35, 27, 29), (37, 38, 27, 29), (29, 31, 19, 21), (33, 34, 19, 21), (38, 38, 19, 21)]
    for (x0, x1, z0, z1) in houses:
        top = int(rng.integers(12, 16)) * CLICK
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                s = d.sector(x, z)
                s.floor = [top - int(rng.integers(0, 4)) * CLICK] * 4          # broken walls, never low enough to climb
                walls.set_floor(s, k.atlases, "t_mattoni_pav", walls.rot_for(x, z))
    d.wall_cols = {}
    for z in range(20, 29):                                   # the temple front: marble, under a gable of rock
        if z != GATE[1]:
            s = d.sector(GATE[0], z)
            s.wall = True
            s.floor = [0] * 4
        d.wall_cols[(GATE[0], z)] = "t_marmo"
    d.sector(GATE[0], GATE[1]).ceil = [6 * CLICK] * 4          # the lintel over the gate
    for z in range(20, 29):
        d.wall_cols[(39, z)] = "t_marmo"
    gable = lambda zc: int(3072 + max(0.0, 4.5 - abs(zc - 24.5)) * 320) // 64 * 64       # noqa: E731
    for x in (38, 39):
        for z in range(20, 29):
            d.sector(x, z).ceil = [gable(z + 1), gable(z + 1), gable(z), gable(z)]
            d.sector(x, z).csplit = False
    sog = cave("G_SOGLIA", ["."], 41, 24, 0, 6 * CLICK, wall="t_marmo", floor="t_marmo_pav", ceil="t_volta", rough=0, amb=(0.34, 0.34, 0.36))
    pr = cave("G_PRONAO", rows("#..#", "....", "....", "....", "....", "....", "#..#"), 42, 21, 0, 12 * CLICK, wall="t_marmo",
              floor="t_marmo_pav", ceil="t_volta", rough=0, amb=(0.34, 0.35, 0.38))
    k.link_wall(d, sog, span=(24, 24))
    k.link_wall(sog, pr, span=(24, 24))

    # ================================================================ 3. the baths
    t1 = cave("T1_SPOGLIATOIO", ["....."] * 4, 30, 32, 0, 8 * CLICK, wall="t_mattoni", floor="t_mos_vuoto", ceil="t_volta", rough=0,
              amb=(0.34, 0.33, 0.32))
    t2 = cave("T2_FRIGIDARIO", ["........."] * 6, 28, 36, 0, 10 * CLICK, wall="t_marmo", floor="t_marmo_pav", ceil="t_volta", rough=0,
              amb=(0.36, 0.37, 0.4))
    t2v = cave("T2_VASCA", rows(".....", ".....", ".....", "..246"), 30, 37, -2048, 2048, wall="t_marmo", floor="t_marmo_scuro",
               ceil="t_volta", rough=0, amb=(0.3, 0.32, 0.36))
    ipo = cave("T3_IPOCAUSTO", rows(".#.#.#.#.", ".........", ".#.#.#.#.", ".........", ".#.#.#.#.", "........."), 28, 41, -2048, 5 * CLICK,
               wall="t_mattoni", floor="t_terra_battuta", ceil="t_mattoni_pav", rough=0, amb=(0.2, 0.19, 0.18))
    poz = cave("T4_POZZETTO", ["..."] * 3, 37, 44, -2048, 2048, wall="t_mattoni", floor="t_terra_battuta", ceil="t_volta", rough=0,
               amb=(0.24, 0.24, 0.26))
    bal = cave("T5_LOGGIA", ["..."] * 7, 37, 40, 0, 10 * CLICK, wall="t_marmo", floor="t_marmo_pav", ceil="t_volta", rough=0,
               amb=(0.36, 0.36, 0.38))
    k.link_wall(d, t1, span=(32, 32))
    k.link_wall(t1, t2, span=(32, 32))
    k.link_vertical(t2v, t2, K.rect(30, 37, 34, 40))
    k.link_wall(t2v, ipo, span=(32, 32))
    k.link_wall(ipo, poz, span=(45, 45))
    k.link_vertical(poz, bal, [(38, 45)])
    k.link_wall(t2, bal, span=(41, 41))

    # ================================================================ 4. the house of the mosaic maker, the cistern
    s1 = cave("S1_CASA", ["........."] * 6, 32, 11, 0, 8 * CLICK, wall="t_rosso", floor="t_mos_vuoto", ceil="t_tavole", rough=0,
              amb=(0.36, 0.33, 0.3))
    s3 = cave("S3_BOTTEGA", ["..."] * 3, 41, 12, 0, 6 * CLICK, wall="t_mattoni", floor="t_terra_battuta", ceil="t_tavole", rough=0,
              amb=(0.3, 0.28, 0.26))
    lat = []
    for z in (9, 8, 7, 6, 5):
        lat.append("".join("4" if c == "P" else "." for c in LATTICE[z]))
    s2 = cave("S2_CISTERNA", rows("444444444", *lat, "444444444", "444444444"), 32, 3, -1024, 14 * CLICK, wall="t_opera",
              floor="g_bagnato", ceil="t_volta", rough=0, amb=(0.3, 0.33, 0.36))
    s2.step_col = "t_opera_muschio"
    wlat = ["".join("#" if c == "P" else "." for c in LATTICE[z]) for z in (9, 8, 7, 6, 5)]
    s2w = cave("S2_ACQUA", rows(*wlat), 32, 5, -1024 - 1792, 1792, wall="t_opera_muschio", floor="g_bagnato", water=True,
               amb=(0.14, 0.32, 0.38))
    k.link_wall(d, s1, span=(36, 36))                # d is north of s1
    k.link_wall(s1, s3, span=(13, 13))
    k.link_wall(s2, s1, span=(36, 36))
    s2.sector(32, 9).floor = [0] * 4                 # the landing at the water's edge and its step, to climb back up
    s2.sector(33, 9).floor = [2 * CLICK] * 4
    pit = [(x, z) for z in (9, 8, 7, 6, 5) for i, x in enumerate(range(32, 41)) if LATTICE[z][i] != "P" and (x, z) not in ((32, 9), (33, 9))]
    for (x, z) in ((32, 9), (33, 9)):                # under the landing the cistern is rock
        s2w.sector(x, z).wall = True
    k.water_surface(s2, s2w, pit)
    for z in (10, 4, 3):
        for x in range(32, 41):
            walls.set_floor(s2.sector(x, z), k.atlases, "t_lastre", walls.rot_for(x, z))
    for z, row in LATTICE.items():
        for i, c in enumerate(row):
            x = 32 + i
            if c == "P":
                walls.set_floor(s2.sector(x, z), k.atlases, "t_mos_castore", 0)
            tile = "t_mos_castore" if c == "P" else "t_mos_polluce" if c == "B" else "t_mos_vuoto"
            walls.set_floor(s1.sector(x, z + 3), k.atlases, tile, 0)          # the same picture on the floor of the house

    # ================================================================ 5. the temple
    ring = "...#########..."
    u = cave("U_GALLERIA", [ring] * 3 + ["..............."] * 5 + [ring] * 3, 46, 19, 0, 11 * CLICK, wall="t_marmo", floor="t_marmo_pav",
             ceil="t_volta", amb=(0.36, 0.36, 0.4), rough=0)
    k.link_wall(pr, u, span=(23, 25))
    solid = "###############"
    hrows = [solid] * 3 + ["###.........#..", "###.........#..", "#..............", "###.........#..", "###.........#.."] + [solid] * 3
    h = cave("H_CELLA", hrows, 46, 19, DEEP, 15 * CLICK, wall="t_marmo", floor="t_marmo_scuro", ceil="t_volta",
             amb=(0.3, 0.3, 0.34), rough=0)
    for x in (47, 48):
        h.sector(x, 24).floor = [8 * CLICK] * 4                  # the alcove, half way up the west wall
    for x, cl in ((49, 15), (50, 11), (51, 7), (52, 3)):
        h.sector(x, 22).floor = [cl * CLICK] * 4                 # the stair: its top step is 1 click under the gallery
    k.link_vertical(h, u, VOID)
    for (wx, wz) in VOID:
        u.sector(wx, wz).ceil = [15 * CLICK] * 4
    for wx in range(50, 57):
        for wz in (23, 24, 25):
            name = "t_stella" if (wx, wz) == (53, 24) else "t_mos_castore" if wx < 53 and wz == 24 else "t_mos_polluce" if wx > 53 and wz == 24 else "t_mos_vuoto"
            walls.set_floor(h.sector(wx, wz), k.atlases, name, 0)
    for wz in (23, 24, 25):
        walls.set_floor(u.sector(47, wz), k.atlases, "t_mos_vuoto", 0)
        walls.set_floor(u.sector(59, wz), k.atlases, "t_mos_vuoto", 0)
    walls.set_floor(u.sector(ALTAR[0], ALTAR[1] - 1), k.atlases, "t_stella", 0)

    # ================================================================ 6. the way out: shaft, boulder gallery, daylight
    e = cave("E_FUGA", rows("##############", "######.#######", "..............", "..............", "..............",
                            "######.#######", "##############"), 61, 21, 0, 26 * CLICK, wall="t_opera", floor="t_lastre", ceil="g_soffitto",
             amb=(0.34, 0.33, 0.32), rough=0)
    LEDGE = 12 * CLICK
    for x in range(63, 75):
        for z in range(21, 28):
            s = e.sector(x, z)
            if not s.wall:
                rise = max(0, x - 70) * 2 * CLICK
                s.floor = [LEDGE + rise] * 4
                if x >= 71:
                    walls.set_floor(s, k.atlases, "sabbia", walls.rot_for(x, z))
    for z in (23, 24, 25):
        k.climb(62, z, "+x", room=e.room)
    k.link_wall(u, e, span=(24, 24))
    L.add_portal = real_add
    M2.shape(k, a0, protect=[(3, 29), (4, 29), (3, 28), (4, 28), (12, 23), (12, 24)])
    k.finish_interiors()

    # ================================================================ the flooded twins (two flipmaps)
    twins = {}

    def flood(flip, lowers, uppers):
        for it in lowers + uppers:
            rm = it.room
            alt = copy.deepcopy(rm)
            alt.name = rm.name + "_ACQUA"
            alt.index = None
            alt.objects = []
            alt.meta = []
            L.add_room(alt)
            rm.alternate = (flip, alt)
            twins[rm] = alt
        for it in lowers:
            twins[it.room].room_type = 3
            twins[it.room].ambient = (0.14, 0.34, 0.4)
        for up in uppers:
            ur = up.room
            for lo in lowers:
                lr = lo.room
                for (room, area, direction, other, opacity) in log:
                    if room is ur and other is lr and direction == prj2.P_FLOOR:
                        for lx in range(area[0], area[2] + 1):
                            for lz in range(area[1], area[3] + 1):
                                wx, wz = ur.x + lx, ur.z + lz
                                rot = walls.rot_for(wx, wz)
                                us = twins[ur].sectors[lx][lz]
                                hs = twins[lr].sectors[wx - lr.x][wz - lr.z]
                                for s, faces in ((us, (prj2.F_FLOOR, prj2.F_FLOOR_TRI2)), (hs, (prj2.F_CEILING, prj2.F_CEILING_TRI2))):
                                    for f in faces:
                                        if s.invisible:
                                            s.invisible.discard(f)
                                walls.set_floor(us, k.atlases, "acqua_scura", rot, blend=2)
                                walls.set_ceiling(hs, k.atlases, "acqua_scura", rot, blend=2)
        group = [it.room for it in lowers + uppers]
        for (room, area, direction, other, opacity) in log:
            if room in group:
                vertical = direction in (prj2.P_FLOOR, prj2.P_CEILING)
                real_add(twins[room], area, direction, other, opacity=2 if (vertical and other in group) else opacity)

    flood(F_TERME, [t2v, ipo, poz], [t2, bal])
    flood(F_TEMPIO, [h], [u])
    ur, hr = u.room, h.room

    # A flipmap swaps the whole room, statics included: whatever is put in a room with a twin goes in the twin too,
    # or the columns and the statues would vanish when the water comes.
    real_static = L.add_static

    def add_static(room, *args, **kw):
        r = real_static(room, *args, **kw)
        if room in twins:
            real_static(twins[room], *args, **kw)
        return r
    L.add_static = add_static

    def light(it, wx, wz, hh, color, intensity=0.8, inner=1.0, outer=5.0):
        M2.light(ctx, it, wx, wz, hh, color, intensity, inner, outer)
        if it.room in twins:
            rm = twins[it.room]
            L.add_light(rm, 0, ((wx - rm.x) * 1024.0, float(hh), (wz - rm.z) * 1024.0), color=color, intensity=intensity, inner=inner, outer=outer)

    def props(room, h0, items):
        for it in items:
            name, x, z, rot = it[:4]
            k.prop(name, x, z, rot=float(rot), h=h0, room=room, scale=it[4] if len(it) > 4 else 1.0)

    WARM, COLD, SEA = (1.0, 0.8, 0.5), (0.55, 0.7, 1.0), (0.4, 0.9, 0.95)

    def statua(room, h0, x, z, rot, pollux=False):
        """The twins of Tindari (CdV_Gemelli.wad2: 446 Castore, 447 Polluce), 4 m with their plinth, at a sector centre."""
        L.add_static(room, 447 if pollux else 446, ((x - room.x) * 1024.0, float(h0 - room.y), (z - room.z) * 1024.0), rot_y=float(rot))
        k.links.append((int(x), int(z)))

    statua(t2.room, 0, 29.5, 39.5, 90)
    statua(t2.room, 0, 35.5, 39.5, 270, True)
    statua(s2.room, 0, 34.5, 3.5, 0)
    statua(s2.room, 0, 38.5, 3.5, 0, True)
    statua(ur, 0, 46.5, 19.5, 45)
    statua(ur, 0, 60.5, 29.5, 225, True)
    statua(hr, DEEP, 49.5, 25.5, 90)
    statua(hr, DEEP, 57.5, 25.5, 270, True)
    statua(pr.room, 0, 43.5, 21.5, 0)
    statua(pr.room, 0, 43.5, 27.5, 180, True)

    # ---------------------------------------------------------------- 1
    k.place(K.LARA, 3, 30, room=p0.room, rot=180.0, name="lara_start")
    lua.start('if not CDV.Has(ID.PUZZLE_ITEM7) then TEN.Inventory.GiveItem(ID.PUZZLE_ITEM7, 1) end')
    light(p0, 4.0, 31.0, 5600, COLD, 0.9, 2.0, 12.0)
    light(a0, 10.5, 24.0, 300, SEA, 1.0, 1.5, 6.0)
    light(a0, 5.5, 21.5, 500, WARM, 0.9, 1.0, 5.0)
    props(a0.room, 0, [("STALAGMITE", 2.6, 26.5, 0, 1.1), ("STALAGMITE", 8.4, 20.6, 60, 0.9), ("STALAGMITE", 6.6, 28.4, 0, 0.7),
                       ("TENDA", 4.5, 21.6, 20), ("FALO", 6.2, 22.4, 0), ("CASSA_LEGNO", 3.4, 22.8, 10), ("CASSA_LEGNO", 3.3, 21.5, 80),
                       ("BOTTE", 7.5, 20.5, 0), ("FARO_CANTIERE", 7.6, 24.6, 100), ("RETI", 8.4, 26.4, 30), ("ANFORA", 2.6, 24.4, 0),
                       ("ANFORA", 3.1, 24.9, 50, 0.8), ("PALO_ORMEGGIO", 8.6, 23.5, 0), ("RELITTO", 10.5, 26.6, 250, 0.6)])
    M2.stalactites(k, a0, 14, 41)
    k.place(K.BADDY1, 6, 23, room=a0.room, rot=315.0, name="g0")
    k.place(K.SMALLMEDI, 3, 21, room=a0.room)
    k.place(K.SHOTGUN_AMMO1, 7, 21, room=a0.room)
    lua.zone("grotta", k.lua_pos(4, 27, 0), r=1500, dy=900, secs=7, fn='CDV.Enable("g0")',
             text="Le grotte marine sotto il capo. Il campo dei tombaroli: Turi è passato di qui.")
    k.place(K.BIGMEDI, 15, 23, room=tun.room, h=-2048)
    lua.secret(1, k.lua_pos(15, 23, -2048), r=900, text="Sul fondo del sifone c'era una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")

    # ---------------------------------------------------------------- 2
    light(d, 23.5, 24.5, 500, SEA, 1.1, 2.0, 9.0)
    light(d, 30.5, 24.5, 2600, COLD, 0.8, 3.0, 12.0)
    light(d, 38.0, 24.5, 1500, WARM, 1.2, 2.0, 8.0)
    light(d, 32.5, 30.5, 900, WARM, 0.7, 1.0, 5.0)
    light(d, 36.5, 18.0, 900, WARM, 0.7, 1.0, 5.0)
    light(pr, 44.0, 24.5, 1800, WARM, 0.8, 1.0, 6.0)
    props(d.room, 0, [("COLONNA_TEMPIO", 39.5, 21.6, 0, 0.5), ("COLONNA_TEMPIO", 39.5, 23.2, 0, 0.5), ("COLONNA_TEMPIO", 39.5, 25.8, 0, 0.5),
                      ("COLONNA_TEMPIO", 39.5, 27.4, 0, 0.5), ("PIEDISTALLO", 39.4, 23.75, 0), ("PIEDISTALLO", 39.4, 25.25, 0),
                      ("BRACIERE", 38.5, 22.5, 0), ("BRACIERE", 38.5, 26.5, 0),
                      ("COLONNA_ROTTA", 28.6, 22.5, 0), ("COLONNA_ROTTA", 31.5, 26.4, 40), ("ROCCHIO", 29.5, 25.6, 30), ("ROCCHIO", 34.4, 22.6, 80),
                      ("ROCCHIO", 30.4, 22.4, 10, 0.8), ("COLONNA", 32.5, 22.5, 0), ("COLONNA", 35.5, 26.4, 0), ("COLONNA", 36.5, 22.5, 0),
                      ("MACERIE", 28.5, 26.5, 0), ("MACERIE", 35.5, 21.6, 120), ("MACERIE", 36.6, 29.6, 200), ("ANFORA", 33.5, 26.4, 0),
                      ("ANFORA", 37.4, 26.5, 70, 0.8), ("TRAVI_CROLLATE", 30.5, 18.5, 30), ("RUDERE_ARCO", 28.5, 24.5, 90),
                      ("TRANSENNA", 37.5, 23.3, 90), ("FARO_CANTIERE", 37.4, 25.6, 60), ("CASSA_LEGNO", 36.5, 25.7, 15),
                      ("SCOGLIO", 28.4, 19.5, 0), ("SCOGLIO_GRANDE", 28.6, 29.6, 40, 0.7), ("STALAGMITE", 39.5, 18.5, 0), ("STALAGMITE", 29.5, 30.6, 0, 0.8)])
    props(dw.room, -1792, [("COLONNA_ROTTA", 21.5, 22.5, 0), ("COLONNA", 24.5, 26.5, 0), ("ROCCHIO", 22.5, 27.5, 40), ("ANFORA", 20.5, 20.5, 0),
                           ("ANFORA", 25.5, 19.5, 80), ("ANCORA", 23.5, 29.5, 30), ("RELITTO", 22.5, 19.5, 120), ("MACERIE", 26.5, 28.5, 0),
                           ("SCOGLIO", 20.5, 29.5, 0)])
    M2.stalactites(k, d, 22, 9)
    k.place(K.FISH_EMITTER, 23, 21, room=dw.room, h=-900)
    k.place(K.BADDY1, 36, 24, room=d.room, rot=270.0, name="h1")
    k.place(K.BADDY1, 34, 30, room=d.room, rot=225.0, name="h2")
    k.place(K.SMALLMEDI, 30, 19, room=d.room)
    k.place(K.SHOTGUN_AMMO1, 39, 30, room=d.room)
    lua.zone("decumano", k.lua_pos(27, 24, 0), r=1700, dy=900, secs=8, fn='CDV.Enable("h1")\nCDV.Enable("h2")\nCDV.Flyby(1)',
             text="Una strada romana, sotto il mare. In fondo, tra le colonne, un cancello.")
    # the gate of the temple and the two niches
    k.place(K.DOOR_TYPE4, GATE[0], GATE[1], room=d.room, rot=270.0, name="porta_tempio")
    k.place(SHOW_PILEO_C, 39, 23, room=d.room, h=_top("PIEDISTALLO"), dx=0.4, dz=0.75, name="pileo_c_posto")
    k.place(SHOW_PILEO_P, 39, 25, room=d.room, h=_top("PIEDISTALLO"), dx=0.4, dz=0.25, name="pileo_p_posto")
    gp = k.lua_pos(GATE[0] - 1, GATE[1], 0)
    for uid, item, model in (("pileo_c", "ID.PUZZLE_ITEM10", "pileo_c_posto"), ("pileo_p", "ID.PUZZLE_ITEM11", "pileo_p_posto")):
        lua.use(uid, item, gp, r=1300, dy=600, fn='CDV.Put("%s")\nCDV.Flag("%s", true)\nCDV.After(50, CDV.GateCheck)' % (model, uid))
    lua.add('''function CDV.GateCheck()
    if CDV.Flag("pileo_c") and CDV.Flag("pileo_p") and not CDV.Flag("tempio_aperto") then
        CDV.Flag("tempio_aperto", true)
        CDV.Enable("porta_tempio")
        CDV.Sfx(105)
        pcall(function() TEN.Effects.MakeEarthquake(16) end)
        CDV.Cue("cancello")
    else
        CDV.Sfx(114)
    end
end
CDV.Loop(function()
    if CDV.Flag("tempio_aperto") then return end
    local item = nil
    if CDV.Has(ID.PUZZLE_ITEM10) and not CDV.Flag("pileo_c") then item = ID.PUZZLE_ITEM10
    elseif CDV.Has(ID.PUZZLE_ITEM11) and not CDV.Flag("pileo_p") then item = ID.PUZZLE_ITEM11 end
    if item ~= nil then CDV.KeyPromptAt(%d, %d, %d, 1300, item, nil) end
end)''' % gp)
    lua.zone("cancello", gp, r=1100, dy=600, secs=6, need='not CDV.Flag("pileo_c") and not CDV.Flag("pileo_p")',
             text="Ai lati del cancello, due piedistalli vuoti.")

    # ---------------------------------------------------------------- 3
    light(t1, 32.5, 34.0, 1400, WARM, 0.7, 1.0, 5.0)
    light(t2, 32.5, 39.0, 2000, COLD, 0.9, 2.0, 8.0)
    light(t2v, 32.5, 39.0, -1200, SEA, 0.5, 1.0, 5.0)
    light(ipo, 32.5, 43.5, -1500, (1.0, 0.6, 0.3), 0.5, 1.0, 5.0)
    light(poz, 38.5, 45.5, -800, (1.0, 0.7, 0.4), 0.9, 1.0, 4.0)
    light(bal, 38.5, 43.0, 1800, WARM, 0.9, 1.0, 6.0)
    props(t1.room, 0, [("ANFORA", 30.5, 35.5, 0), ("ANFORA", 34.4, 35.4, 60), ("TAVOLACCIO", 30.6, 33.5, 90), ("MACERIE", 34.4, 32.6, 0)])
    props(t2.room, 0, [("COLONNA", 28.5, 36.5, 0), ("COLONNA", 36.5, 36.5, 0), ("COLONNA", 28.5, 41.5, 0), ("COLONNA", 36.5, 40.4, 0),
                       ("ANFORA", 29.5, 37.5, 0)])
    props(t2v.room, -2048, [("MACERIE", 31.5, 39.5, 0), ("ANFORA", 30.5, 37.5, 40)])
    props(ipo.room, -2048, [("MACERIE", 30.5, 45.5, 0), ("ANFORA", 34.5, 43.5, 0)])
    props(bal.room, 0, [("COLONNA", 37.5, 46.5, 0), ("COLONNA", 39.5, 46.5, 0), ("BRACIERE", 39.5, 42.5, 0)])
    k.place(KEY_HOLE7, 38, 46, room=poz.room, rot=0.0, h=-2048 + 620, dz=0.94, name="ruota_terme")
    for i, (x, z) in enumerate(((29, 45), (33, 43), (35, 45))):
        k.place(K.BIG_RAT, x, z, room=ipo.room, rot=180.0, h=-2048, name="topo%d" % i)
    k.place(PILEO_C, 38, 42, room=bal.room, name="pileo_castore")
    walls.set_floor(bal.sector(38, 42), k.atlases, "t_stella", 0)
    walls.set_floor(twins[bal.room].sectors[38 - bal.room.x][42 - bal.room.z], k.atlases, "t_stella", 0)
    k.place(K.DOOR_TYPE4, 37, 41, room=bal.room, rot=90.0, name="porta_terme")
    k.place(K.SMALLMEDI, 36, 46, room=ipo.room, h=-2048)
    lua.zone("terme", k.lua_pos(32, 37, 0), r=1500, dy=700, secs=6, text="Le terme. La vasca è asciutta.")
    lua.zone("ipocausto", k.lua_pos(32, 42, -2048), r=1100, dy=700, secs=6, need='not CDV.Flag("terme_acqua")',
             fn='CDV.Enable("topo0")\nCDV.Enable("topo1")\nCDV.Enable("topo2")')
    lua.add('''CDV.Wheel("ruota_terme", function() return not CDV.Flag("terme_acqua") end, function()
    CDV.Flag("terme_acqua", true)
    CDV.Sfx(105)
    pcall(function() TEN.Effects.MakeEarthquake(22) end)
    pcall(function() TEN.View.FadeOut(1.0) end)
    CDV.After(38, function()
        TEN.Flow.FlipMap(%d)
        CDV.Cue("terme_acqua")
        pcall(function() TEN.View.FadeIn(0.8) end)
    end)
end)
CDV.Loop(function()
    if not CDV.Flag("terme_porta") and CDV.Has(ID.PUZZLE_ITEM10) then
        CDV.Flag("terme_porta", true)
        CDV.Enable("porta_terme")
    end
end)''' % F_TERME)

    # ---------------------------------------------------------------- 4
    light(s1, 36.5, 13.5, 1500, WARM, 0.9, 1.5, 7.0)
    light(s3, 42.5, 13.5, 1100, WARM, 0.6, 1.0, 4.0)
    light(s2, 36.5, 7.5, 2600, COLD, 0.9, 3.0, 11.0)
    light(s2, 36.5, 3.6, 900, WARM, 1.0, 1.0, 5.0)
    light(s2w, 36.5, 7.5, -1800, SEA, 0.6, 2.0, 7.0)
    props(s1.room, 0, [("ANFORA", 32.5, 16.5, 0), ("ANFORA", 33.1, 16.4, 70, 0.8), ("TAVOLACCIO", 40.4, 15.5, 0), ("CASSA_LEGNO", 40.4, 11.6, 20),
                       ("BRACIERE", 32.5, 11.5, 0)])
    props(s3.room, 0, [("TAVOLACCIO", 43.4, 13.5, 90), ("ANFORA", 41.5, 14.5, 0), ("ANFORA", 43.5, 12.5, 40), ("BOTTE", 41.5, 12.5, 0)])
    props(s2.room, 0, [("COLONNA", 32.5, 10.5, 0), ("COLONNA", 40.5, 10.5, 0), ("COLONNA", 32.5, 3.5, 0), ("COLONNA", 40.5, 3.5, 0),
                       ("BRACIERE", 33.5, 3.5, 0), ("BRACIERE", 39.5, 3.5, 0), ("MACERIE", 39.5, 4.5, 0)])
    slabs = []
    for z, row in LATTICE.items():
        for i, c in enumerate(row):
            if c == "B":
                k.place(K.BRIDGE_FLAT, 32 + i, z, room=s2.room, h=0, name="tess_%d_%d" % (32 + i, z))
                slabs.append((32 + i, z))
    k.place(K.BADDY1, 38, 4, room=s2.room, rot=0.0, h=0, name="c1")
    k.place(PILEO_P, 36, 4, room=s2.room, h=0, name="pileo_polluce")
    walls.set_floor(s2.sector(36, 4), k.atlases, "t_stella", 0)
    k.place(K.BIGMEDI, 42, 14, room=s3.room)
    lua.secret(2, k.lua_pos(42, 14, 0), r=800, text="Nella bottega del mosaicista c'era una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    k.place(K.SHOTGUN_AMMO1, 33, 3, room=s2.room, h=0)
    lua.zone("cisterna", k.lua_pos(36, 10, 0), r=1000, dy=700, secs=6, fn='CDV.Enable("c1")', text="La cisterna. Berretti scuri, berretti d'oro.")
    lua.add('''local tessere = {}
CDV.Loop(function()
    local p = Lara:GetPosition()
    local sx, sz = math.floor(p.x / 1024), math.floor(p.z / 1024)
    if sx >= 32 and sx <= 40 and sz >= 5 and sz <= 9 and math.abs(p.y) < 48 then            -- standing on the lattice
        local key = sx .. "_" .. sz
        if tessere[key] == nil and not CDV.Flag("tess_" .. key) then
            local m = CDV.M("tess_" .. key)
            if m ~= nil and m:GetValid() then
                CDV.Flag("tess_" .. key, true)
                tessere[key] = 0
                CDV.Log("TESSERA " .. key)
                CDV.Sfx(105)
            end
        end
    end
    for key, t in pairs(tessere) do
        local m = CDV.M("tess_" .. key)
        if m == nil or not m:GetValid() then
            tessere[key] = nil
        elseif t < 12 then
            tessere[key] = t + 1
            pcall(function() m:SetRotation(TEN.Rotation(math.random(-3, 3), 0, math.random(-3, 3))) end)
        else
            tessere[key] = nil
            pcall(function() TEN.Effects.MakeEarthquake(10) end)
            pcall(function() m:ShatterMesh(0) end)
            pcall(function() m:Destroy() end)
        end
    end
end)''')

    # ---------------------------------------------------------------- 5
    k.prop("ALTARE_ASTRI", ALTAR[0] + 0.5, ALTAR[1] + 0.6, rot=0.0, h=0, room=ur)
    at = _top("ALTARE_ASTRI")
    k.place(SHOW_ASTRO_C, ALTAR[0], ALTAR[1], room=ur, h=at, dx=0.2, dz=0.6, name="astro_c_posto")
    k.place(SHOW_ASTRO_P, ALTAR[0], ALTAR[1], room=ur, h=at, dx=0.8, dz=0.6, name="astro_p_posto")
    props(ur, 0, [("BRACIERE", 46.5, 26.5, 0),
                  ("BRACIERE", 48.5, 29.5, 0), ("BRACIERE", 58.5, 19.5, 0), ("BRACIERE", 60.5, 21.5, 0), ("COLONNA_ROTTA", 48.5, 19.5, 0),
                  ("MACERIE", 59.5, 29.4, 0), ("COLONNA", 48.5, 21.5, 0), ("COLONNA", 48.5, 27.5, 0), ("COLONNA", 58.5, 21.5, 0),
                  ("COLONNA", 58.5, 27.5, 0), ("COLONNA", 46.5, 21.5, 0), ("COLONNA", 60.5, 27.5, 0)])
    props(pr.room, 0, [("COLONNA", 42.5, 21.5, 0), ("COLONNA", 42.5, 27.5, 0), ("COLONNA", 45.5, 22.4, 0), ("COLONNA", 45.5, 26.6, 0),
                       ("BRACIERE", 44.5, 22.5, 0), ("BRACIERE", 44.5, 26.5, 0)])
    light(u, 47.5, 27.5, 1700, WARM, 0.9, 1.0, 5.0)
    light(u, 59.5, 24.5, 1700, WARM, 0.8, 1.0, 5.0)
    light(u, 53.5, 24.5, 3300, COLD, 0.9, 2.0, 9.0)
    light(h, 53.5, 24.5, 2600, (0.5, 0.75, 0.9), 0.7, 2.0, 8.0)
    light(h, 59.5, 24.5, 1500, (1.0, 0.8, 0.45), 0.9, 1.0, 4.0)
    k.place(K.WALL_LEVER, LEVER[0], LEVER[1], room=ur, rot=0.0, name="leva_valve")
    k.place(K.DOOR_TYPE4, 60, 24, room=ur, rot=270.0, name="porta_fuga")
    k.place(K.DOOR_TYPE4, 57, 24, room=hr, rot=270.0, h=DEEP, name="porta_valve")
    k.place(K.BADDY1, 54, 25, room=hr, rot=270.0, h=DEEP, name="g1")
    k.place(K.BADDY1, 56, 23, room=hr, rot=270.0, h=DEEP, name="g2")
    k.place(K.BADDY2, 60, 24, room=hr, rot=270.0, h=DEEP, name="turi")
    k.place(K.SHARK, 54, 24, room=hr, rot=270.0, h=DEEP + 2000, name="squalo", invisible=True)
    k.place(K.BIGMEDI, 47, 24, room=hr, h=DEEP + 8 * CLICK)
    lua.secret(3, k.lua_pos(47, 24, DEEP + 8 * CLICK), r=900, text="Nella nicchia a metà parete c'era una Stella dei Dioscuri!", give="ID.SHOTGUN_AMMO1_ITEM")
    k.place(K.SHOTGUN_AMMO1, 59, 26, room=hr, h=DEEP)
    k.place(K.BIGMEDI, 60, 22, room=hr, h=DEEP)
    for x, z in ((50.5, 26.55), (53.5, 26.55), (56.5, 26.55), (54.5, 22.45), (56.5, 22.45)):
        k.prop("COLONNA_TEMPIO", x, z, rot=0.0, h=DEEP, room=hr)
    props(hr, DEEP, [("SARCOFAGO", 53.5, 25.6, 0), ("ANFORA", 50.5, 25.5, 30), ("ANFORA", 56.5, 22.5, 100), ("MACERIE", 55.5, 23.5, 0),
                     ("ANFORA", 59.5, 22.5, 0), ("ANFORA", 60.4, 26.4, 60)])
    lua.zone("tempio", k.lua_pos(47, 24, 0), r=1300, dy=600, secs=8, fn='CDV.Enable("g1")\nCDV.Enable("g2")',
             text="Il tempio dei Dioscuri. La cella è otto metri più in basso, e là sotto ci sono gli uomini di Turi.")
    ap = k.lua_pos(ALTAR[0], ALTAR[1] - 1, 0)
    lua.add('''local function Drown(name)
    local m = CDV.M(name)
    if m ~= nil and m:GetValid() and CDV.Active(name) and m:GetHP() > 0 then m:SetHP(0) return true end
    return false
end
local function SetWater(on)
    if (CDV.Flag("acqua") or false) == on then return end
    TEN.Flow.FlipMap(%d)
    CDV.Flag("acqua", on)
    if on then
        Drown("g1")
        Drown("g2")
        if CDV.Flag("turi_sveglio") and not CDV.Flag("turi_morto") then
            CDV.After(120, function()
                Drown("turi")
                CDV.Flag("turi_morto", true)
            end)
        end
        CDV.Enable("squalo")
    else
        CDV.Disable("squalo")
        if CDV.Flag("leva_valve") and not CDV.Flag("valve_aperte") then
            CDV.Flag("valve_aperte", true)
            CDV.Enable("porta_valve")
            CDV.Sfx(105)
            CDV.Say("In fondo alla cella, senza più il peso dell'acqua, le valve di bronzo si aprono.", 6)
        end
    end
end
-- The altar: Action puts the Astro di Castore in its socket (the sea comes in) or takes it back (it goes).
local altarBusy = false
CDV.Loop(function()
    if altarBusy or CDV.Flag("fuga") then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) or Lara:GetState() ~= 2 then return end
    if not CDV.Near(%d, %d, %d, 900, 500) then return end
    if not CDV.HandsFree() then CDV.Holster() return end
    local on = not CDV.Flag("acqua")
    if on and not CDV.Has(ID.PUZZLE_ITEM7) then return end
    altarBusy = true
    Lara:SetAnim(131)          -- LA_USE_KEY with state 42, as at the seal of Marinello
    Lara:SetState(42)
    CDV.After(45, function()
        if on then CDV.Take(ID.PUZZLE_ITEM7) else CDV.Give(ID.PUZZLE_ITEM7, 1) end
        CDV.ShowModel("astro_c_posto", on)
        CDV.Sfx(on and 105 or 114)
        pcall(function() TEN.Effects.MakeEarthquake(on and 20 or 8) end)
        pcall(function() TEN.View.FadeOut(1.4) end)
    end)
    CDV.After(80, function()
        SetWater(on)
        pcall(function() TEN.View.FadeIn(1.0) end)
        altarBusy = false
    end)
end)
CDV.Loop(function()
    -- the lever of the bronze doors, on the east gallery
    if not CDV.Flag("leva_valve") and CDV.Used("leva_valve") then
        CDV.Flag("leva_valve", true)
        CDV.Sfx(114)
    end
    -- Turi wakes when Lara reaches the chamber on foot
    if CDV.Flag("valve_aperte") and not CDV.Flag("turi_sveglio") and not CDV.Flag("acqua") and CDV.Near(%d, %d, %d, 1500, 700) then
        CDV.Flag("turi_sveglio", true)
        CDV.Enable("turi")
        local m = CDV.M("turi")
        if m ~= nil then m:SetHP(20000) end
        CDV.Cue("turi")
        CDV.Say("Turi 'a Vulpi, con l'Astro di Polluce al collo. Polluce è l'immortale: le pallottole non lo fermano.", 8)
    end
    -- the fall of the temple
    local t = CDV.Flag("fuga_t") or 0
    if t > 0 then
        t = t - 1
        CDV.Flag("fuga_t", t)
        if t %% 40 == 0 then pcall(function() TEN.Effects.MakeEarthquake(14) end) end
        if t == 0 then Lara:SetHP(0) end
    end
end)''' % ((F_TEMPIO,) + ap + k.lua_pos(57, 24, DEEP)))
    lua.drop("polluce", "turi", "ID.PUZZLE_ITEM8", "L'Astro di Polluce viene a galla da solo.")
    lua.use("altare2", "ID.PUZZLE_ITEM8", ap, r=1100, dy=600,
            text="Castore e Polluce, insieme dopo duemila anni. La volta comincia a cedere!",
            fn='CDV.Put("astro_p_posto")\nif CDV.Has(ID.PUZZLE_ITEM7) then CDV.Take(ID.PUZZLE_ITEM7) end\nCDV.ShowModel("astro_c_posto", true)\n'
               'if not CDV.Flag("acqua") then TEN.Flow.FlipMap(%d); CDV.Flag("acqua", true) end\n'
               'CDV.Flag("fuga", true)\nCDV.Flag("fuga_t", %d)\nCDV.Enable("porta_fuga")\nCDV.Enable("squalo")\nCDV.Sfx(105)' % (F_TEMPIO, ESCAPE_FRAMES))
    lua.add('CDV.Loop(function() if CDV.Has(ID.PUZZLE_ITEM8) then CDV.KeyPromptAt(%d, %d, %d, 1100, ID.PUZZLE_ITEM8, "use_altare2") end end)' % ap)

    # ---------------------------------------------------------------- 6
    k.place(K.ROLLINGBALL, 73, 24, room=e.room, rot=270.0, h=LEDGE + 6 * CLICK + 512, name="masso_fuga")
    lua.zone("masso_fuga", k.lua_pos(64, 24, LEDGE), r=900, dy=900, need='CDV.Flag("fuga")',
             fn='CDV.Enable("masso_fuga")\nCDV.Flag("masso_via", true)')
    lua.add('''CDV.Loop(function()
    if not CDV.Flag("masso_via") then return end
    local b = CDV.M("masso_fuga")
    if b ~= nil and b:GetValid() and b:GetPosition().x > %d then pcall(function() b:SetItemFlags(-1100, 0) end) end
end)''' % (63 * 1024 + 700))
    light(e, 62.0, 24.5, 1300, WARM, 0.6, 1.0, 4.0)
    light(e, 66.5, 24.5, LEDGE + 1500, WARM, 0.5, 1.0, 5.0)
    light(e, 73.5, 24.5, LEDGE + 3000, (1.0, 0.93, 0.8), 2.2, 3.0, 12.0)
    props(e.room, 0, [("MACERIE", 61.5, 25.5, 0), ("SCALA_CORDA", 62.95, 24.5, 90)])
    k.place(K.SMALLMEDI, 67, 26, room=e.room, h=LEDGE)
    lua.zone("fine", k.lua_pos(73, 24, LEDGE + 6 * CLICK), r=1200, dy=1200, need='CDV.Flag("fuga")',
             fn='CDV.Flag("fuga_t", 0)\npcall(function() TEN.View.FadeOut(0.4) end)\nCDV.After(200, function() CDV.End(0, 1) end)',
             text="Aria. Luce. L'alba sulla lingua di sabbia di Marinello, e in mano i due Astri dei Dioscuri.")

    # ---------------------------------------------------------------- flyby: the decumanus, towards the temple
    for n, (x, y, z) in enumerate(((21.0, 900, 22.0), (27.0, 1500, 26.5), (33.0, 1300, 24.5), (36.0, 1100, 24.5))):
        L.add_flyby(d.room, ((x - d.room.x) * 1024.0, float(y), (z - d.room.z) * 1024.0), 1, n, rot_y=90.0, speed=1.0, fov=80.0)

    lua.start('for _, n in ipairs({ "pileo_c_posto", "pileo_p_posto", "astro_c_posto", "astro_p_posto" }) do CDV.ShowModel(n, false) end')
    for it in (p0, a0, d, pr, sog, t1, t2, t2v, ipo, poz, bal, s1, s2, s3, u, h, e):
        it.room.no_path = False
    for alt in twins.values():
        alt.no_path = False
    ctx.notes += ["LIVELLO 3 - LA META' PERDUTA", __doc__]


def _top(name):
    """Height (units) of the top of a decoration static (decor/mito_models.py), to put something on it."""
    return {"PIEDISTALLO": 512, "ALTARE_ASTRI": 566}[name]
