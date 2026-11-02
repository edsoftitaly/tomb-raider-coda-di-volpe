"""Livello 0 - Collaudo (v10). One hall with a station per mechanic; only what passes here goes into the
levels. Every station has a sign (Lua zone) saying what to try and what should happen.

Hall 25 x 19 sectors, floor at 0, ceiling 4 m. House-local (x, z): x west -> east, z south -> north.
  A  pickups on the floor (row z = 3) and one on a table             - visible, upright, pickup animation,
                                                                        inventory view
  B  kick-door house (x 1-5, z 12-16)                                 - Action facing the door: kick + open
  C  lever house (x 7-11)                                             - floor lever opens the door
  D  twin levers house (x 13-17)                                      - both levers within 20 s
  E  pushable block -> plate -> raising block -> ledge (x 19-23)      - push/pull, trigger by Lua
  F  pool with an item on the bottom (x 1-6, z 5-8)                   - swim, dive, air bar, climb out
  G  rope over a gap (x 8-15, z 5-7)                                  - jump, grab, swing, let go
  H  pole to a high ledge (x 17-19, z 5-7)                            - climb pole
  I  monkey-swing ceiling (x 20-23, z 5-7)                            - jump up, hang, traverse
  J  rolling ball along z = 17, triggered at x 12                     - trap, run
  K  search drawers with a medikit (x 23, z 2)                        - search animation, item given
"""
import kit as K
from kit import CLICK

X0, Z0 = 10, 10
W, D = 25, 19
HEIGHT = 16 * CLICK          # 4 m
FLOOR = 0


def grid():
    g = [["." for _ in range(W)] for _ in range(D)]      # g[z][x]
    # houses B, C, D: wall rings x a..a+4, z 12..16, a one-sector doorway at x a+2, z 12
    for a in (1, 7, 13):
        for x in range(a, a + 5):
            for z in range(12, 17):
                if x in (a, a + 4) or z in (12, 16):
                    g[z][x] = "#"
        g[12][a + 2] = "."
    # E: a 7-click ledge along x 23, z 12..17; the raising block rises next to it at (22, 14)
    for z in range(12, 18):
        g[z][23] = "7"
    # G: two 8-click platforms with a gap for the rope
    # (TEN rope: fixed 24 x 128 = 3072 units from the ceiling; it hangs 1.5 sectors from each edge)
    for x in (8, 9, 10, 14, 15):
        for z in range(5, 8):
            g[z][x] = "8"
    # H: the high ledge reached by the pole
    for x in (18, 19):
        for z in range(5, 8):
            g[z][x] = "9"
    return g


def plan_rows(g):
    return ["".join(g[z]) for z in range(D - 1, -1, -1)]


def lua_kick(lua, name):
    """A kick door on a DOOR_TYPE1, as TEN's pushpull_kick_door.cpp does it for KICK_DOOR1 (no wad has that
    door): Lara idle, facing the door within 30 degrees and within 1 sector of the kick spot, Action ->
    she is put 917 units in front of the door (KickDoorPos), plays LA_DOOR_OPEN_KICK (315) and the door
    opens when the foot hits it."""
    lua.add('''CDV.Loop(function()
    if CDV.Flag("kick_%(n)s") then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) then return end
    if Lara:GetState() ~= 2 then return end
    local d = CDV.M("%(n)s")
    if d == nil or not d:GetValid() then return end
    local q = d:GetPosition()
    local face = (d:GetRotation().y + 180) %% 360
    local a = math.rad(face)
    local sx, sz = q.x - 917 * math.sin(a), q.z - 917 * math.cos(a)
    local p = Lara:GetPosition()
    if math.abs(p.y - q.y) > 200 or (p.x - sx) ^ 2 + (p.z - sz) ^ 2 > 600 ^ 2 then return end
    local dy = math.abs(((Lara:GetRotation().y - face) + 540) %% 360 - 180)
    if dy > 30 then return end
    CDV.Flag("kick_%(n)s", true)
    Lara:SetPosition(TEN.Vec3(math.floor(sx), q.y, math.floor(sz)), false)
    Lara:SetRotation(TEN.Rotation(0, face, 0))
    Lara:SetAnim(315)
    if CDV_DEBUG_KICK then
        for _, f in ipairs({1, 5, 15, 30}) do
            CDV.After(f, function() print(string.format("KICK f%%d anim %%d frame %%d state %%d", f, Lara:GetAnim(), Lara:GetFrame(), Lara:GetState())) end)
        end
    end
    CDV.After(22, function() CDV.Enable("%(n)s") end)
end)''' % {"n": name})


def build_standalone(ctx):
    k, lua = ctx.kit, ctx.lua
    lua.add('CDV_DEBUG_KICK = false')
    g = grid()
    hall = k.interior("COLLAUDO", plan_rows(g), X0, Z0, FLOOR, HEIGHT, "cementine", "soffitto", "intonaco_interno",
                      ambient=(0.55, 0.55, 0.55))
    R = hall.room

    def at(x, z):
        return X0 + x, Z0 + z

    def floor(x, z):
        s = hall.sector(*at(x, z))
        return FLOOR + int(sum(s.floor) / 4)

    def P(t, x, z, **kw):
        return k.place(t, *at(x, z), room=R, **kw)

    def sign(zid, x, z, text, r=1200):
        lua.zone(zid, k.lua_pos(*at(x, z), floor(x, z)), r=r, dy=1500, once=False, secs=7, text=text)

    P(K.LARA, 12, 1, rot=0.0, name="lara_start")
    lua.start('CDV.Say("Livello di collaudo: ogni postazione ha un cartello. Vai vicino e prova.", 6)')

    # A: every pickup on the floor, one on a table
    items = [K.PUZZLE_ITEM[i] for i in range(1, 10)] + [K.KEY_ITEM1, K.SMALLMEDI, K.BIGMEDI, K.SHOTGUN_ITEM,
                                                         K.SHOTGUN_AMMO1, K.UZI_AMMO, K.FLARE_ITEM]
    for i, t in enumerate(items):
        P(t, 2 + i, 3, name="ogg_%d" % i)
    k.prop("CASA_TAVOLO", X0 + 20.5, Z0 + 3.5, rot=0.0, h=0, room=R)
    # TEN takes from a plinth only within 511 units of the item (PlinthPickUpBounds): 0.28 m from the south end
    P(K.SMALLMEDI, 20, 3, h=410, ocb=K.OCB_PLINTH_LOW, dz=0.225, name="ogg_tavolo")
    sign("A", 9, 2, "A - Oggetti: ognuno deve stare dritto sul pavimento, raccolto con l'animazione, "
         "dritto e riconoscibile nell'inventario. Uno e' sul tavolo.")

    # B: kick door
    P(K.DOOR_TYPE1, 3, 11, rot=180.0, name="porta_calcio")
    lua_kick(lua, "porta_calcio")
    P(K.SHOTGUN_AMMO1, 3, 14)
    sign("B", 3, 10, "B - Porta da calciare: davanti alla porta, rivolta verso di lei, Azione. Lara la sfonda.")

    # C: floor lever opens the door
    P(K.DOOR_TYPE1, 9, 11, rot=180.0, name="porta_leva")
    P(K.LEVER_SWITCH, 9, 9, rot=0.0, name="leva1")
    lua.add('CDV.Loop(function() if not CDV.Flag("leva1_ok") and CDV.Pulled("leva1") then '
            'CDV.Flag("leva1_ok", true); CDV.Enable("porta_leva"); CDV.Say("La leva apre la porta.", 4) end end)')
    P(K.UZI_AMMO, 9, 14)
    sign("C", 8, 9, "C - Leva a terra: tirala, la porta della casetta si apre.")

    # D: two levers within 20 s
    P(K.DOOR_TYPE1, 15, 11, rot=180.0, name="porta_gemelle")
    P(K.LEVER_SWITCH, 13, 9, rot=0.0, name="leva2")
    P(K.LEVER_SWITCH, 21, 9, rot=0.0, name="leva3")
    lua.add('CDV.TwinLevers("gemelle", "leva2", "leva3", 600, "Una leva tirata: hai 20 secondi per l\'altra.", '
            '"Troppo tardi: la prima leva non tiene piu\'. Hai 20 secondi da adesso per l\'altra.", '
            'function() CDV.Enable("porta_gemelle"); CDV.Say("Le due leve insieme: la porta si apre.", 4) end)')
    P(K.BIGMEDI, 15, 14)
    sign("D", 17, 9, "D - Leve gemelle: tira le due leve (qui e piu' a est) a meno di 20 secondi l'una dall'altra.")

    # E: pushable block on the plate raises the block next to the ledge
    P(K.PUSHABLE, 20, 13, rot=0.0, name="blocco")
    k.prop("SCALA_PIANEROTTOLO", X0 + 20.5, Z0 + 15.5, rot=0.0, h=0, room=R)      # the plate, marked in marble
    P(K.RAISING_BLOCK1, 22, 14, rot=0.0, name="piattaforma")
    lua.add('''CDV.Loop(function()
    if CDV.Flag("piastra_ok") then return end
    local b = CDV.M("blocco")
    if b == nil or not b:GetValid() then return end
    local p = b:GetPosition()
    if math.floor(p.x / 1024) == %d and math.floor(p.z / 1024) == %d then
        CDV.Flag("piastra_ok", true); CDV.Enable("piattaforma"); CDV.Say("Il blocco e' sulla piastra: si alza la piattaforma.", 4)
    end
end)''' % at(20, 15))
    P(K.SHOTGUN_ITEM, 23, 16, h=7 * CLICK)
    sign("E", 19, 12, "E - Blocco: spingilo (Azione + avanti/indietro) sulla piastra di marmo. Si alza la piattaforma "
         "per salire sulla cengia.")

    # F: pool with a medikit on the bottom
    pool = [(x, z) for x in range(1, 7) for z in range(5, 9)]
    wplan = []
    for z in range(8, 4, -1):
        wplan.append("".join("." for x in range(1, 7)))
    water = k.interior("COLLAUDO_ACQUA", wplan, X0 + 1, Z0 + 5, FLOOR - 12 * CLICK, 12 * CLICK, "sabbia_fondo",
                       "soffitto", "roccia_mare", water=True, ambient=(0.4, 0.5, 0.55))
    k.water_surface(hall, water, [at(x, z) for x, z in pool], tex="acqua_mare")
    k.place(K.SMALLMEDI, *at(3, 6), room=water.room, h=FLOOR - 12 * CLICK)
    sign("F", 7, 6, "F - Vasca: tuffati, raccogli il medikit sul fondo, controlla la barra dell'aria, risali e esci.")

    # G: rope over the gap
    # the rope hangs a fixed 3072 from the ceiling: a 5 m ceiling over G puts its bottom level with the 2 m
    # platforms, so Lara grabs it above them, has twice the rope above her and swings clear of their sides
    for x in range(8, 16):
        for z in range(5, 8):
            hall.sector(*at(x, z)).ceil = [20 * CLICK] * 4
    P(K.ROPE, 12, 6, h=20 * CLICK - 64, name="corda")
    lua.start('CDV.Enable("corda")')      # TEN draws and collides a rope only once it is active (rope.cpp)
    sign("G", 9, 4, "G - Corda: salta con Azione, Avanti/Indietro per salire e scendere, Sprint per dondolare, Salto per lanciarti sull'altra piattaforma.")

    # H: pole
    # a TEN pole item is 1024 units tall and Lara climbs only while there is pole above her: stack them
    for i in range(3):
        P(K.POLEROPE, 17, 6, rot=90.0, h=i * 1024, name="palo%d" % i)
    P(K.FLARE_ITEM, 19, 6, h=9 * CLICK)
    sign("H", 17, 4, "H - Palo: arrampicati in cima e passa sulla cengia.")

    # I: monkey swing under a lower ceiling
    for x in range(20, 24):
        for z in range(5, 8):
            s = hall.sector(*at(x, z))
            s.ceil = [(z + 1) * CLICK] * 4      # rows z 5/6/7 at 6/7/8 clicks: which height can Lara grab
            s.flags |= 1      # SectorFlags.Monkey
    sign("I", 21, 4, "I - Soffitto con gli appigli a 6, 7 e 8 click (tre file): salta con Azione, aggrappati e attraversa.")

    # J: rolling ball along z = 17
    # TEN rolling ball (tr5_rollingball.cpp): pivot at its centre (radius 512) and it moves only by floor slope
    # or by its ItemFlags speed (x, z in 1/32 units per frame): lift it and push it west from Lua
    P(K.ROLLINGBALL, 21, 17, rot=270.0, h=512, name="masso")
    lua.zone("masso", k.lua_pos(*at(12, 17), 0), r=900, dy=1500,
             fn='CDV.Enable("masso")\nlocal b = CDV.M("masso")\nif b ~= nil then b:SetItemFlags(-800, 0) end',
             text="J - Il masso! Corri!")

    # K: search drawers with a medikit inside (same sector, as in the classic levels)
    P(K.SEARCH_DRAWERS, 23, 2, rot=270.0, name="cassettiera")
    P(K.SMALLMEDI, 23, 2, name="medi_cassetti")
    sign("K", 22, 2, "K - Cassettiera: davanti, Azione. Lara la fruga e trova un medikit.")

    for x, z in ((6, 3), (18, 3), (6, 14), (18, 14), (12, 8)):
        ctx.level.add_light(R, 0, ((x + 1.0) * 1024, HEIGHT - 300, (z + 1.0) * 1024), color=(1.0, 0.92, 0.8),
                            intensity=0.8, inner=2.0, outer=9.0)
    R.no_path = True
    ctx.notes += ["LIVELLO 0 - COLLAUDO", __doc__]
