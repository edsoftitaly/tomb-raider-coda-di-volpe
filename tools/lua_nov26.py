"""26 Nov: script changes after the reviews (TRCustoms, Aspide). Works on the four level scripts in place.
  all      a kick door opens from either side: nobody stays shut in behind one
  Marinello  the sea is closed north of z 72 and east of x 84 (no way round the ridge); the net store has two steps
  Sommersa   Turi has to be fought: the Star of Castor goes back on the altar only after TURI_WOUNDS points of damage
usage: lua_nov26.py <scripts/Levels dir>"""
import os
import sys

d = sys.argv[1]


def patch(name, pairs):
    p = os.path.join(d, name)
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    for a, b in pairs:
        a, b = a.replace("\n", nl), b.replace("\n", nl)
        assert s.count(a) == 1, (name, s.count(a), a[:70])
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)
    print(name, len(pairs), "changes")


KICK = ('''        local sx, sz = q.x - back * math.sin(a), q.z - back * math.cos(a)
        if (p.x - sx) ^ 2 + (p.z - sz) ^ 2 > 520 ^ 2 then return end
''', '''        local sx, sz = q.x - back * math.sin(a), q.z - back * math.cos(a)
        if (p.x - sx) ^ 2 + (p.z - sz) ^ 2 > 520 ^ 2 then
            -- 26 Nov: the other side too, so that nobody stays shut in behind a door that opened from one side only
            if side == "B" then back, face = 917, yaw else back, face = 109, (yaw + 180) % 360 end
            sx, sz = q.x - back * math.sin(a), q.z - back * math.cos(a)
            if (p.x - sx) ^ 2 + (p.z - sz) ^ 2 > 520 ^ 2 then return end
        end
''')

for n in ("Tindari.lua",):   # Oliveri has its own older KickDoor (doors inside the house): left as it is
    patch(n, [KICK])

patch("Marinello.lua", [KICK, (
    '''        CDV.Say("The slab sinks under the crate. By the loft, a block rises from the floor.", 7)''',
    '''        CDV.Say("The slab sinks under the crate. By the loft, a tall block rises from the floor.", 7)'''), (
    '''CDV.TwinLevers("fondo", "leva_fondo_0", "leva_fondo_1",''',
    '''-- 26 Nov: the block by the loft is two sectors high: too much from the floor. The crate, free again once the block
-- is up, makes the step. Said once, when she stands by the block.
CDV.Zone({ id = "blocco_alto", x = 69120, y = -512, z = 51712, r = 1300, dy = 900, once = true, text = "Too high to reach from the floor. The crate would make a step.", secs = 6, need = function() return CDV.Flag("piastra_reti") == true end })

-- 26 Nov: the sea is not a way round. North of the head of the ridge and far out to the east the current takes her
-- back: no swimming round the rock into the reed bed, no open water with nothing in it.
local SEA_Z, SEA_X = 72 * 1024, 84 * 1024
CDV.Loop(function()
    local p = Lara:GetPosition()
    if p.z <= SEA_Z and p.x <= SEA_X then return end
    Lara:SetPosition(TEN.Vec3(math.min(p.x, SEA_X), p.y, math.min(p.z, SEA_Z)), false)
    if not CDV.Flag("detto_corrente") then
        CDV.Flag("detto_corrente", true)
        CDV.Say("The current is too strong out here. There is no way round by sea.", 6)
    end
end)

CDV.TwinLevers("fondo", "leva_fondo_0", "leva_fondo_1",''')])

patch("Sommersa.lua", [KICK, (
    '''    if on and CDV.Flag("valve_aperte") and not CDV.Flag("turi_sveglio") then
        if not CDV.Flag("detto_astro_fermo") then
            CDV.Flag("detto_astro_fermo", true)
            CDV.Say("Not yet. The bronze doors are open: see what waits in the cella first.", 5)
        end
        return
    end
''', '''    if on and CDV.Flag("valve_aperte") and not CDV.Flag("turi_ferito") then
        if not CDV.Flag("turi_sveglio") then
            if not CDV.Flag("detto_astro_fermo") then
                CDV.Flag("detto_astro_fermo", true)
                CDV.Say("Not yet. The bronze doors are open: see what waits in the cella first.", 5)
            end
        elseif (CDV.Flag("detto_astro_forte") or 0) < 2 then
            CDV.Flag("detto_astro_forte", (CDV.Flag("detto_astro_forte") or 0) + 1)
            CDV.Say("The Star will not hold while the Star of Pollux burns so bright. Wound him first.", 6)
        end
        return
    end
'''), (
    '''CDV.Loop(function()
    -- the lever of the bronze doors, on the east gallery''',
    '''-- 26 Nov: the fight has to be fought. Every wound is counted (he heals at once: Pollux is immortal); when they add
-- up to TURI_WOUNDS his Star flickers, and only then does the Star of Castor go back on the altar.
local turiHP = nil
local TURI_WOUNDS = 240
CDV.Loop(function()
    -- the lever of the bronze doors, on the east gallery'''), (
    '''            -- the Star of Pollux: while the cella is dry nothing kills him
            if not CDV.Flag("acqua") and m:GetHP() > 0 and m:GetHP() < 20000 then''',
    '''            local hp = m:GetHP()
            if turiHP ~= nil and hp > 0 and hp < turiHP and not CDV.Flag("acqua") and not CDV.Flag("turi_ferito") then
                local w = (CDV.Flag("turi_danni") or 0) + (turiHP - hp)
                CDV.Flag("turi_danni", w)
                if w >= TURI_WOUNDS / 2 and not CDV.Flag("turi_meta") then
                    CDV.Flag("turi_meta", true)
                    CDV.Say("He bleeds like any man, for a moment. Keep at it.", 5)
                end
                if w >= TURI_WOUNDS then
                    CDV.Flag("turi_ferito", true)
                    CDV.Sfx(105)
                    CDV.Say("He staggers and the Star of Pollux flickers. Now: the altar!", 7)
                    CDV.Log("TURI wounded enough: " .. w)
                end
            end
            turiHP = hp
            -- the Star of Pollux: while the cella is dry nothing kills him
            if not CDV.Flag("acqua") and m:GetHP() > 0 and m:GetHP() < 20000 then'''), (
    '''                if phase == 2 then m:SetHP(30000) end
            end
        end
    end
    -- his fire sets Lara alight''',
    '''                if phase == 2 then m:SetHP(30000); turiHP = 30000 end
            end
        end
    end
    -- his fire sets Lara alight'''), (
    '''Pollux is the immortal one: bullets will not stop him.", 8)''',
    '''Pollux is the immortal one: bullets will not kill him. But they hurt.", 8)''')])
