"""The lost half, script side of Ed's list of 16:31:
  1. the death of Turi 'a Vulpi is a scene: the camera goes down into the cella (flyby 2), Lara's hands are off
     the controls, he goes under in a cloud of bubbles
  2. the bats of the way out start one sector above the floor of their niches, not under the vault
  3. two more sharks in the cella when the spirits of the twins come
  4. the credits: the engine's fade blacked out the strings too (only a black screen was seen). The black is now a
     full-screen sprite under the strings, the fade is lifted, and every key is cleared while they run (no inventory)
  5. Turi throws fire at Lara when she is above him or out of his reach, with a clear line: a ball of flame every
     two seconds and a half, aimed at where she stands when it leaves

  lua_sommersa_pm.py <in.lua> <out.lua>"""
import sys

TURI = '''-- Turi 'a Vulpi throws fire when she is above him or out of his reach and he has a clear line: a ball of flame
-- aimed at where she stands when it leaves his hand (so it can be dodged). His death is a scene: flyby 2 in the
-- cella, the controls taken away, bubbles.
local balls, flameT = {}, 0
CDV.Loop(function()
    for i = #balls, 1, -1 do
        local b = balls[i]
        b.t = b.t + 1
        local k = b.t / b.n
        local x, y, z = b.x0 + (b.x1 - b.x0) * k, b.y0 + (b.y1 - b.y0) * k - math.sin(k * math.pi) * 260, b.z0 + (b.z1 - b.z0) * k
        pcall(function()
            TEN.Effects.EmitFire(TEN.Vec3(x, y, z), 2)
            TEN.Effects.EmitLight(TEN.Vec3(x, y, z), TEN.Color(255, 140, 40), 9, false, "cdv_fiamma_" .. i)
        end)
        if b.t >= b.n then
            table.remove(balls, i)
            for j = 1, 5 do
                pcall(function() TEN.Effects.EmitFire(TEN.Vec3(x + math.random(-150, 150), y - math.random(0, 200), z + math.random(-150, 150)), 3) end)
            end
            local lp = Lara:GetPosition()
            if (lp.x - x) ^ 2 + (lp.z - z) ^ 2 < 480 ^ 2 and math.abs((lp.y - 400) - y) < 800 and Lara:GetHP() > 0 then
                Lara:SetHP(math.max(0, Lara:GetHP() - 150))
                CDV.Log("FLAME hit")
            end
        end
    end
    if not CDV.Flag("turi_sveglio") or CDV.Flag("turi_morto") or CDV.Flag("acqua") then return end
    local m = CDV.M("turi")
    if m == nil or not m:GetValid() or not m:GetActive() or m:GetHP() <= 0 or Lara:GetHP() <= 0 then return end
    flameT = flameT + 1
    if flameT < 75 then return end
    local tp, lp = m:GetPosition(), Lara:GetPosition()
    local flat = math.sqrt((tp.x - lp.x) ^ 2 + (tp.z - lp.z) ^ 2)
    if (lp.y < tp.y - 768 or flat > 4 * 1024) and flat < 16 * 1024 then
        local clear = true
        pcall(function()
            clear = TEN.Util.HasLineOfSight(m:GetRoomNumber(), TEN.Vec3(tp.x, tp.y - 700, tp.z), TEN.Vec3(lp.x, lp.y - 500, lp.z)) ~= false
        end)
        if clear then
            flameT = 0
            local d = math.sqrt(flat * flat + (tp.y - lp.y) ^ 2)
            balls[#balls + 1] = { x0 = tp.x, y0 = tp.y - 700, z0 = tp.z, x1 = lp.x, y1 = lp.y - 400, z1 = lp.z, t = 0, n = math.max(14, math.floor(d / 120)) }
            if not CDV.Flag("turi_fuoco") then CDV.Flag("turi_fuoco", true); CDV.Log("FLAME first, " .. math.floor(d / 1024) .. " sectors") end
        end
    end
end)
CDV.Loop(function()
    if not CDV.Flag("turi_sveglio") or CDV.Flag("turi_scena") then return end
    local m = CDV.M("turi")
    local dead = CDV.Flag("turi_morto") == true or (m ~= nil and m:GetValid() and m:GetHP() <= 0)
    if not dead then return end
    CDV.Flag("turi_scena", true)
    CDV.Log("TURI dies: the scene")
    CDV.Flyby(2)
    pcall(function() TEN.Effects.MakeEarthquake(24) end)
    CDV.Say("Turi 'a Vulpi goes down with the temple he came to rob.", 6)
    local n = 0
    local function scene()
        n = n + 1
        pcall(TEN.Input.ClearAllKeys)
        if n % 3 == 0 and m ~= nil and m:GetValid() then
            pcall(function()
                local p = m:GetPosition()
                TEN.Effects.EmitAirBubble(TEN.Vec3(p.x + math.random(-220, 220), p.y - math.random(200, 800), p.z + math.random(-220, 220)), 28, 48)
            end)
        end
        if n < 190 then CDV.After(1, scene) end
    end
    scene()
end)

'''

OLD_FINE = '''        CDV.Flag("fuga_t", 0)
        pcall(function() TEN.View.FadeOut(0.4) end)
        CDV.After(210, function() CDV.Credits(1) end)
    end })
'''
NEW_FINE = '''        CDV.Flag("fuga_t", 0)
        CDV.CreditsLock = true                              -- from here on no key reaches the game (no inventory)
        pcall(function() TEN.View.FadeOut(0.4) end)
        CDV.After(210, function()
            CDV.CreditsOn = true                            -- the black sprite under the strings
            pcall(function() TEN.View.FadeIn(2) end)        -- the engine's fade would black out the strings too
            CDV.After(20, function() CDV.Credits(1) end)
        end)
    end })

local blackSprite = nil
CDV.Loop(function()
    if CDV.CreditsLock then pcall(TEN.Input.ClearAllKeys) end
    if not CDV.CreditsOn then return end
    pcall(function()
        if blackSprite == nil then
            blackSprite = TEN.View.DisplaySprite(TEN.Objects.ObjID.DEFAULT_SPRITES, 0, TEN.Vec2(50, 50), 0, TEN.Vec2(100, 100), TEN.Color(0, 0, 0))
        end
        blackSprite:Draw(1, TEN.View.AlignMode.CENTER, TEN.View.ScaleMode.STRETCH, TEN.Effects.BlendID.OPAQUE)
    end)
end)
'''
OLD_BATS = '''                CDV.After((i - 1) * 6, function() CDV.Enable("pip_f" .. i) end)
'''
NEW_BATS = '''                CDV.After((i - 1) * 6, function()
                    local bat = CDV.M("pip_f" .. i)                 -- one sector above the floor of the niche, not under the vault
                    if bat ~= nil and bat:GetValid() then
                        pcall(function() local q = bat:GetPosition(); bat:SetPosition(TEN.Vec3(q.x, -3972 - (i % 3) * 120, q.z), false) end)
                    end
                    CDV.Enable("pip_f" .. i)
                end)
'''
OLD_SHARK = '''            CDV.Enable("squalo")
            CDV.Say("Castor and Pollux, together'''
NEW_SHARK = '''            CDV.Enable("squalo")
            CDV.Enable("squalo2")                       -- the twins are not alone: two more in the flooded cella
            CDV.Enable("squalo3")
            CDV.Say("Castor and Pollux, together'''


def sub1(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:70])
    return t.replace(old, new)


def main():
    src, dst = sys.argv[1:3]
    s = open(src, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    t = s.replace("\r\n", "\n")
    assert "local balls, flameT" not in t
    t = sub1(t, OLD_FINE, NEW_FINE)
    t = sub1(t, OLD_BATS, NEW_BATS)
    t = sub1(t, OLD_SHARK, NEW_SHARK)
    t = sub1(t, 'CDV.Drop({ id = "polluce", enemy = "turi",', TURI + 'CDV.Drop({ id = "polluce", enemy = "turi",')
    t = sub1(t, '"turi", "squalo", ', '"turi", "squalo", "squalo2", "squalo3", ')
    t = sub1(t, "-- The end credits: one card after another over the black screen (strings are drawn over the fade), then the title.",
             "-- The end credits: one card after another over a black sprite (the engine's fade hides strings too), then the title.")
    open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl))
    print("Sommersa.lua ok")


if __name__ == "__main__":
    main()
