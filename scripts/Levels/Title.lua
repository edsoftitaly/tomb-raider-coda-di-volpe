-- Title: a flight over the places of the adventure (flyby sequence 0 of the title level, started by the engine).
-- The rooms of every place keep a prefix in their name (O_ Oliveri, M_ Marinello, T_ Tindari, S_ the lost half):
-- when the camera cuts to another place, sky, fog and stars become the ones of that level.

local PLACES = {
    O_ = { sky = { 16, 20, 36 },    fog = { 16, 36 },  stars = 2500, horizon = false },
    M_ = { sky = { 196, 180, 170 }, fog = { 12, 30 },  stars = 0,    horizon = true },
    T_ = { sky = { 214, 170, 132 }, fog = { 50, 125 }, stars = 0,    horizon = true },
    S_ = { sky = { 8, 30, 38 },     fog = { 8, 30 },   stars = 0,    horizon = false },
}
local current = nil

local function Apply(p)
    local lvl = TEN.Flow.GetCurrentLevel()
    local c = TEN.Color(p.sky[1], p.sky[2], p.sky[3])
    pcall(function() lvl.fog = TEN.Flow.Fog(c, p.fog[1], p.fog[2]) end)
    pcall(function() lvl.layer1 = TEN.Flow.SkyLayer(c, 2) end)
    pcall(function() lvl.starfield = TEN.Flow.Starfield(p.stars) end)
    pcall(function() lvl.horizon1.enabled = p.horizon end)
end

local function Place()
    local ok, name = pcall(function() return TEN.View.GetCameraRoom():GetName() end)
    if not ok or type(name) ~= "string" then return end
    local key = name:sub(1, 2)
    if PLACES[key] ~= nil and key ~= current then
        current = key
        Apply(PLACES[key])
    end
end

LevelFuncs.OnStart = function() current = nil; Apply(PLACES.O_) end
LevelFuncs.OnLoad = function() end
LevelFuncs.OnSave = function() end
LevelFuncs.OnLoop = function() Place() end
LevelFuncs.OnEnd = function() end
