"""16 Nov (Ed, after the full playthrough).

Marinello: the spirits of Donna Villa's pool come one at a time, in a fixed order that does not depend on where Lara
happens to be: a spirit comes out, it dies when Lara is in the water (anywhere in it), its shark is let into the
pool, the next spirit comes when Lara is back on dry ground. A music cue "dopo_massi" when the boulders have stopped.

Sommersa: a cap goes on the pedestal Lara stands at and the gate opens when her hand comes away from the second one;
Lara is put in front of the pedestal / of the socket of the altar before she moves; once Turi is dead the Star of
Castor cannot be taken back; the Star of Pollux sets off the end only when the animation is over; then four spirits
in turn (two of Castor, two of Pollux, all dying in water), the door of the way out, three boulders one after the
other and the bats of the niches.

  lua_16nov.py <dir> Marinello_i.lua:Marinello_j.lua Sommersa_j.lua:Sommersa_k.lua"""
import os
import sys

SPIRITS = r'''
-- Lara in the water: swimming under it or on it (her state), or standing in a room of water.
local WATER_STATES = { [13] = true, [17] = true, [18] = true, [33] = true, [34] = true, [35] = true, [44] = true,
    [47] = true, [48] = true, [49] = true }
function CDV.InWater()
    if WATER_STATES[Lara:GetState()] then return true end
    local ok, w = pcall(function() return Lara:GetRoom():GetFlag(TEN.Objects.RoomFlagID.WATER) end)
    return ok and w == true
end

-- Spirits that come one at a time. c = { id, names = {...}, colors = {{r, g, b}...}, start = function -> bool,
-- gone = function(k), done = function() }. Spirit k comes out; it dies when Lara has been in the water for a second
-- and a half with it out (the engine only kills a wraith when the camera is under water, which is why it used to
-- depend on where Lara was); the next one comes when she has been out of the water for a second and a half, or
-- after ten seconds anyway. Nothing here depends on where in the room Lara is.
function CDV.Spirits(c)
    local P = c.id
    CDV.Loop(function()
        if CDV.Flag(P .. "_fine") or not c.start() then return end
        local k = CDV.Flag(P .. "_k") or 0
        local out = CDV.Flag(P .. "_fuori") == true
        local t = (CDV.Flag(P .. "_t") or 0) + 1
        local wet = CDV.InWater()
        if not out then
            local dry = wet and 0 or ((CDV.Flag(P .. "_asciutta") or 0) + 1)
            CDV.Flag(P .. "_asciutta", dry)
            if (k == 0 and t > (c.first or 30)) or (k > 0 and (dry >= 45 or t > 300)) then
                k = k + 1
                local name = c.names[k]
                CDV.ShowModel(name, true)
                CDV.Enable(name)
                local m = CDV.M(name)
                local col = c.colors[k]
                if m ~= nil and m:GetValid() then
                    local q = m:GetPosition()
                    CDV.Glow({ { q.x, q.y, q.z } }, col[1], col[2], col[3], 50, 20)      -- it comes out of the stone
                end
                CDV.Sfx(184)
                CDV.Log("SPIRIT " .. P .. " " .. k .. " out")
                CDV.Flag(P .. "_k", k)
                CDV.Flag(P .. "_fuori", true)
                CDV.Flag(P .. "_acqua", 0)
                t = 0
            end
        else
            local name = c.names[k]
            local w = (CDV.Flag(P .. "_acqua") or 0) + (wet and 1 or 0)
            CDV.Flag(P .. "_acqua", w)
            local m = CDV.M(name)
            local q = (m ~= nil and m:GetValid()) and m:GetPosition() or Lara:GetPosition()
            local dead = t > 60 and not CDV.Active(name)          -- the engine put it out by itself
            if not dead and t > 60 and w >= 45 then
                CDV.Disable(name)
                dead = true
            end
            if dead then
                local col = c.colors[k]
                CDV.ShowModel(name, false)
                CDV.Glow({ { q.x, q.y, q.z } }, col[1], col[2], col[3], 40, 24)
                CDV.Sfx(105)
                CDV.Log("SPIRIT " .. P .. " " .. k .. " gone, water frames " .. w .. ", out for " .. t)
                CDV.Flag(P .. "_fuori", false)
                CDV.Flag(P .. "_asciutta", 0)
                t = 0
                if c.gone then c.gone(k) end
                if k >= #c.names then
                    CDV.Flag(P .. "_fine", true)
                    CDV.Log("SPIRITS " .. P .. " all gone")
                    if c.done then c.done() end
                end
            end
        end
        CDV.Flag(P .. "_t", t)
    end)
end
'''

MAR_NEW = SPIRITS + r'''
-- Donna Villa and her four sisters: awake when the Star of Castor is taken, one at a time. Each one that dies lets
-- a beast into the pool: Lara has to get out, and the next spirit comes for her on dry ground.
CDV.Loop(function()
    if CDV.Flag("maga_sveglia") or not CDV.Has(ID.PUZZLE_ITEM7) then return end
    CDV.Flag("maga_sveglia", true)
    CDV.Track("tr3_42_look_out_2")
    CDV.Log("SPIRITS awake")
    CDV.Say("The Star is yours, but Donna Villa is awake, and not alone. Bullets do nothing: that fire only dies in water.", 9)
end)
CDV.Spirits({ id = "maga", names = { "maga", "maga2", "maga3", "maga4", "maga5" }, first = 45,
    colors = { { 255, 120, 40 }, { 255, 120, 40 }, { 255, 120, 40 }, { 255, 120, 40 }, { 255, 120, 40 } },
    start = function() return CDV.Flag("maga_sveglia") == true end,
    gone = function(k)
        CDV.ShowModel("bestia_acqua" .. k, true)
        CDV.Enable("bestia_acqua" .. k)
        if k == 1 then CDV.Say("The water put it out, and woke something in the pool. Out, before the next one comes.", 7) end
    end,
    done = function()
        CDV.Flag("maga_morta", true)
        CDV.Enable("porta_uscita")
        CDV.Say("The last spirit is gone. A way out opens in the far wall.", 8)
    end })

'''

SOM_PILEI = r'''-- The two pedestals of the gate. A cap goes on the pedestal Lara is standing at, whichever cap it is: she is put
-- in front of it, facing it, and the gate opens when her hand comes away from the second cap.
local PEDS = { { x = 40345, z = 24320 }, { x = 40345, z = 25856 } }          -- right and left, looking at the gate
local CAPS = { { item = ID.PUZZLE_ITEM10, model = "pileo_c_posto", flag = "pileo_c" },
    { item = ID.PUZZLE_ITEM11, model = "pileo_p_posto", flag = "pileo_p" } }
local function PedAt()               -- the free pedestal Lara stands in front of, or nil
    local p = Lara:GetPosition()
    local best, bd = nil, 1e12
    for k, ped in ipairs(PEDS) do
        local dx, dz = p.x - ped.x, p.z - ped.z
        local d = dx * dx + dz * dz
        if not CDV.Flag("ped_" .. k) and dx < 60 and dx > -900 and math.abs(dz) < 640 and math.abs(p.y) < 300 and d < bd then
            best, bd = k, d
        end
    end
    return best
end
local pedBusy = false
local function PlaceCap(cap)
    local k = PedAt()
    if k == nil then return end
    local ped = PEDS[k]
    pedBusy = true
    CDV.Flag("ped_" .. k, true)
    local m = CDV.M(cap.model)
    if m ~= nil and m:GetValid() then
        pcall(function() local q = m:GetPosition(); m:SetPosition(TEN.Vec3(ped.x, q.y, ped.z)) end)
    end
    local lp = Lara:GetPosition()
    Lara:SetPosition(TEN.Vec3(ped.x - 325, lp.y, ped.z), false)
    Lara:SetRotation(TEN.Rotation(0, 90, 0))
    CDV.Log("CAP " .. cap.flag .. " on pedestal " .. k)
    CDV.InsertItem(function()
        pedBusy = false
        CDV.Flag(cap.flag, true)
        CDV.GateCheck()
    end, function() CDV.ShowModel(cap.model, true) end)
end
for _, cap in ipairs(CAPS) do
    CDV.Use({ id = cap.flag, item = cap.item, x = 40345, y = 0, z = 25088, r = 1500, dy = 600, consume = true,
        need = function() return not pedBusy and PedAt() ~= nil end, fn = function() PlaceCap(cap) end })
end

function CDV.GateCheck()
    if CDV.Flag("pileo_c") and CDV.Flag("pileo_p") and not CDV.Flag("tempio_aperto") then
        CDV.Flag("tempio_aperto", true)
        CDV.Enable("porta_tempio")
        CDV.GateSound()
        pcall(function() TEN.Effects.MakeEarthquake(16) end)
        CDV.Cue("cancello")
        CDV.Log("GATE of the temple open")
    end
end
CDV.Loop(function()
    if CDV.Flag("tempio_aperto") or pedBusy then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) or Lara:GetState() ~= 2 then return end
    if PedAt() == nil then return end
    local item = nil
    if CDV.Has(ID.PUZZLE_ITEM10) and not CDV.Flag("pileo_c") then item = ID.PUZZLE_ITEM10
    elseif CDV.Has(ID.PUZZLE_ITEM11) and not CDV.Flag("pileo_p") then item = ID.PUZZLE_ITEM11 end
    if item == nil then return end
    if not CDV.HandsFree() then CDV.Armed() return end
    TEN.Inventory.SetFocusedItem(item)
end)

'''

SOM_ALTAR = r'''-- The altar of the Stars (two sockets, Castor's on the left). Lara is put in front of the socket, facing it.
local ALTAR_Z, SOCKET_C, SOCKET_P = 28833, 48332, 48947
local altarBusy = false
local function AtAltar()
    local p = Lara:GetPosition()
    return math.abs(p.x - 48640) < 760 and p.z > 28000 and p.z < 28960 and math.abs(p.y) < 300
end
local function FaceAltar(x)
    local lp = Lara:GetPosition()
    Lara:SetPosition(TEN.Vec3(x, lp.y, ALTAR_Z), false)
    Lara:SetRotation(TEN.Rotation(0, 0, 0))
end
-- Castor's Star: Action sets it (the sea comes in) or takes it back (it goes). Once Turi is dead, or his Star is in
-- Lara's hands, it has fused with the altar and stays there.
local function CastorFused() return CDV.Flag("turi_morto") == true or CDV.Has(ID.PUZZLE_ITEM8) end
CDV.Loop(function()
    if altarBusy or CDV.Flag("fuga") then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) or Lara:GetState() ~= 2 then return end
    if not AtAltar() then return end
    local on = not CDV.Flag("acqua")
    if on and not CDV.Has(ID.PUZZLE_ITEM7) then return end
    if not on and CastorFused() then return end
    if not CDV.HandsFree() then CDV.Armed() return end
    altarBusy = true
    FaceAltar(SOCKET_C)
    CDV.Log("ALTAR Castor " .. (on and "set" or "taken back"))
    CDV.InsertItem(function()
        CDV.Sfx(238)
        pcall(function() TEN.Effects.MakeEarthquake(on and 20 or 8) end)
        pcall(function() TEN.View.FadeOut(1.4) end)
        CDV.After(35, function()
            SetWater(on)
            pcall(function() TEN.View.FadeIn(1.0) end)
            if on and not CDV.Flag("detto_acqua") then
                CDV.Flag("detto_acqua", true)
                CDV.Say("The sea fills the cella. While the Star stays on the altar, so does the water.", 6)
            end
            altarBusy = false
        end)
    end, function()
        if on then CDV.Take(ID.PUZZLE_ITEM7) else CDV.Give(ID.PUZZLE_ITEM7, 1) end
        CDV.ShowModel("astro_c_posto", on)
    end)
end)
'''

SOM_END = r'''CDV.Zone({ id = "saldo", x = 48640, y = 0, z = 28160, r = 1200, dy = 500, once = true, text = "The Star of Castor has fused with the altar. The other socket is still empty.", secs = 6, need = function() return CDV.Flag("acqua") == true and CDV.Has(ID.PUZZLE_ITEM8) end })

-- The Star of Pollux in the second socket: nothing happens until Lara's hand comes away. Then the vault begins to
-- give way and the spirits of the twins come, one at a time; the door of the way out opens when the last is gone.
CDV.CUE_MANUAL["use_altare2"] = true
CDV.Use({ id = "altare2", item = ID.PUZZLE_ITEM8, x = 48640, y = 0, z = 28480, r = 900, dy = 400, consume = true,
    need = function() return not altarBusy and AtAltar() and CDV.Flag("acqua") == true end, fn = function()
        altarBusy = true
        FaceAltar(SOCKET_P)
        CDV.Log("ALTAR Pollux set")
        CDV.InsertItem(function()
            altarBusy = false
            CDV.Flag("fuga", true)
            CDV.Sfx(105)
            pcall(function() TEN.Effects.MakeEarthquake(30) end)
            CDV.Cue("use_altare2")
            CDV.Enable("squalo")
            CDV.Say("Castor and Pollux, together after two thousand years. The vault is giving way, and the twins are not alone!", 8)
        end, function() CDV.ShowModel("astro_p_posto", true) end)
    end })

CDV.Loop(function()
    if CDV.Flag("fuga") or altarBusy or not CDV.Has(ID.PUZZLE_ITEM8) then return end
    if not TEN.Input.IsKeyHit(TEN.Input.ActionID.ACTION) or Lara:GetState() ~= 2 then return end
    if not AtAltar() or not CDV.Flag("acqua") then return end
    if not CDV.HandsFree() then CDV.Armed() return end
    TEN.Inventory.SetFocusedItem(ID.PUZZLE_ITEM8)
end)

CDV.Spirits({ id = "gemelli", names = { "spirito_c1", "spirito_c2", "spirito_p1", "spirito_p2" }, first = 75,
    colors = { { 255, 120, 40 }, { 255, 120, 40 }, { 70, 150, 255 }, { 70, 150, 255 } },
    start = function() return CDV.Flag("fuga") == true end,
    gone = function(k)
        if k == 1 then CDV.Say("Fire that only dies in water, like Donna Villa's.", 5) end
    end,
    done = function()
        CDV.Enable("porta_fuga")
        CDV.GateSound()
        CDV.Flag("fuga_t", 2250)
        CDV.Say("The last spirit is gone and the bronze door gives. Run!", 6)
    end })
-- while the spirits are out the ground shakes, but the vault holds
CDV.Loop(function()
    if not CDV.Flag("fuga") or CDV.Flag("gemelli_fine") then return end
    local n = (CDV.Flag("fuga_scossa") or 0) + 1
    CDV.Flag("fuga_scossa", n)
    if n % 60 == 0 then pcall(function() TEN.Effects.MakeEarthquake(10) end) end
end)

-- The way out: three boulders down the stairs, one lane each, one after the other; then the bats of the niches.
local MASSI = { { "masso_fuga", 15 }, { "masso_fuga2", 40 }, { "masso_fuga3", 65 } }        -- name, frames of delay
local BATS = 10
CDV.Zone({ id = "masso_fuga", x = 66048, y = -3072, z = 25088, r = 900, dy = 900, once = true, text = "Into the niches!", secs = 4, need = function() return CDV.Flag("fuga") end, fn = function()
        for i, b in ipairs(MASSI) do
            CDV.After(b[2], function()
                CDV.ShowModel(b[1], true)
                CDV.Enable(b[1])
                local n = 0
                local function push()                 -- on flat ground the engine slows a ball down: it gets its speed back
                    n = n + 1
                    local m = CDV.M(b[1])
                    if m == nil or not m:GetValid() then return end
                    local q = m:GetPosition()
                    if n % 30 == 1 then CDV.Log("BOULDER " .. i .. " x " .. math.floor(q.x) .. " y " .. math.floor(q.y)) end
                    if n > 400 or q.x < 65212 then return end
                    pcall(function() m:SetItemFlags(-2400, 0); m:SetItemFlags(0, 1) end)
                    CDV.After(1, push)
                end
                push()
            end)
        end
        CDV.After(190, function()
            CDV.Log("BATS out of the niches")
            for i = 1, BATS do
                CDV.After((i - 1) * 6, function() CDV.Enable("pip_f" .. i) end)
            end
        end)
    end })

'''


def between(t, a, b):
    """(start, end) of the text from the first a to the b that follows it (b left out)."""
    i = t.index(a)
    j = t.index(b, i)
    return i, j


def one(t, a):
    assert t.count(a) == 1, (t.count(a), a[:60])


def marinello(t):
    a = 'CDV.Loop(function()\n    if CDV.Flag("maga_morta") then return end'
    b = 'CDV.Zone({ id = "masso_g"'
    one(t, a), one(t, b)
    i, j = between(t, a, b)
    t = t[:i] + MAR_NEW.lstrip("\n") + t[j:]
    # the cue after the boulders
    a = "                if n > 400 or q.z < 30720 + 2300 then return end\n"
    one(t, a)
    t = t.replace(a, '''                if n > 400 or q.z < 30720 + 2300 then
                    -- this one has come to rest; the cue of the calm after them when the last one has
                    local stopped = (CDV.Flag("massi_fermi") or 0) + 1
                    CDV.Flag("massi_fermi", stopped)
                    if stopped == 3 then CDV.Log("BOULDERS at rest"); CDV.After(30, function() CDV.Cue("dopo_massi") end) end
                    return
                end
''')
    a = '    scala = "tr3_08_long_way_up",'
    one(t, a)
    # Ed, 16/11 10:33: "Long Way Up" belongs after the boulders, not on the ladder
    t = t.replace(a, '    dopo_massi = "tr3_08_long_way_up",           -- when the three boulders have come to rest\n'
                  '    -- scala: no cue of its own any more, the music of the way up starts after the boulders (Ed, 16/11)')
    return t


def sommersa(t):
    # the caps
    a, b = 'CDV.Use({ id = "pileo_c"', 'CDV.Zone({ id = "cancello"'
    one(t, a), one(t, b)
    i, j = between(t, a, b)
    t = t[:i] + SOM_PILEI + t[j:]
    # the altar
    a = "-- The altar: Action puts the Astro di Castore"
    b = "CDV.Loop(function()\n    -- the lever of the bronze doors"
    one(t, a), one(t, b)
    i, j = between(t, a, b)
    t = t[:i] + SPIRITS.lstrip("\n") + "\n" + SOM_ALTAR + t[j:]
    # Pollux, the end
    a, b = 'CDV.Use({ id = "altare2"', 'CDV.Zone({ id = "fine"'
    one(t, a), one(t, b)
    i, j = between(t, a, b)
    t = t[:i] + SOM_END + t[j:]
    # the countdown starts with the door, not with the Star
    a = '''        if t % 40 == 0 then pcall(function() TEN.Effects.MakeEarthquake(14) end) end'''
    one(t, a)
    # the models hidden at the start
    a = '''    for _, n in ipairs({ "pileo_c_posto", "pileo_p_posto", "astro_c_posto", "astro_p_posto" }) do CDV.ShowModel(n, false) end'''
    one(t, a)
    t = t.replace(a, a + '''
    for _, n in ipairs({ "masso_fuga", "masso_fuga2", "masso_fuga3", "spirito_c1", "spirito_c2", "spirito_p1", "spirito_p2" }) do CDV.ShowModel(n, false) end''')
    assert "SetWater(on)" in t and t.index("local function SetWater") < t.index("SOCKET_C")
    return t


def main():
    d = sys.argv[1]
    for pair in sys.argv[2:]:
        src, dst = pair.split(":")
        raw = open(os.path.join(d, src), encoding="utf-8", newline="").read()
        crlf = "\r\n" in raw
        t = raw.replace("\r\n", "\n")
        t = marinello(t) if src.startswith("Marinello") else sommersa(t)
        open(os.path.join(d, dst), "w", encoding="utf-8", newline="").write(t.replace("\n", "\r\n") if crlf else t)
        print(src, "->", dst)


if __name__ == "__main__":
    main()
