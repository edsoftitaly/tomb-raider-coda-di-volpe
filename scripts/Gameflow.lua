-- Coda di Volpe - Gameflow.lua (generato da tools/episode.py)
-- Va in C:\CodaDiVolpe\Engine\Scripts\Gameflow.lua

-- ============ IMPOSTAZIONI (cambiare solo queste tre righe) ============
local CDV_RELEASE = false     -- true per la versione da pubblicare: niente fly cheat, niente selezione livello
local CDV_SCHERMATE = false   -- true quando ci sono Screens\cdv_oliveri.jpg ... cdv_sommersa.jpg (schermate di caricamento)
local CDV_LOGO = nil          -- es. "FMV\\cdv_logo.mp4": video all'avvio del gioco, prima del titolo
-- ======================================================================

Flow.SetIntroImagePath("Screens\\intro.jpg")
if CDV_LOGO then Flow.SetIntroVideoPath(CDV_LOGO) end
Flow.SetTotalSecretCount(10)
Flow.EnablePointFilter(false)
Flow.EnableLoadSave(true)
Flow.EnableFlyCheat(not CDV_RELEASE)
Flow.EnableLaraInTitle(false)
Flow.EnableLevelSelect(not CDV_RELEASE)
Flow.EnableMassPickup(true)

local function Schermata(name)
    if CDV_SCHERMATE then return "Screens\\cdv_" .. name .. ".jpg" end
    return "Screens\\loading.png"
end

-- Nomi degli oggetti e dei livelli (si sommano a Strings.lua).
TEN.Flow.SetStrings({
    cdv_diario = { "Byzantine Diary" },
    cdv_chiave_terrazza = { "Terrace Key" },
    cdv_mappa_maree = { "Tide Chart" },
    cdv_chiave_casello = { "Sluice House Key" },
    cdv_conchiglia = { "Singing Shell" },
    cdv_sigillo = { "Seal of the Tonnara" },
    cdv_astro_castore = { "Star of Castor" },
    cdv_astro_polluce = { "Star of Pollux" },
    cdv_manovella = { "Crank" },
    cdv_fusibile = { "Fuse" },
    cdv_chiave_scavi = { "Dig Site Key" },
    cdv_chiave_lucchetto = { "Padlock Key" },
    cdv_pileo_castore = { "Cap of Castor" },
    cdv_pileo_polluce = { "Cap of Pollux" },
    cdv_chiave_ripostiglio = { "Box Room Key" },
    cdv_level_oliveri = { "Prologue - Via Amodeo" },
    cdv_level_marinello = { "The Witch of the Lakes" },
    cdv_level_tindari = { "Tindari" },
    cdv_level_sommersa = { "The Lost Half" },
})

local function CdvObjects()
    local Rot, Axis, Act, ID = TEN.Rotation, TEN.Flow.RotationAxis, TEN.Flow.ItemAction, TEN.Objects.ObjID
    return {
        TEN.Flow.InventoryItem("cdv_diario", ID.PUZZLE_ITEM1, 0, 1.60, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_chiave_terrazza", ID.PUZZLE_ITEM2, 0, 2.00, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_mappa_maree", ID.PUZZLE_ITEM3, 0, 1.60, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_chiave_casello", ID.PUZZLE_ITEM4, 0, 2.00, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_conchiglia", ID.PUZZLE_ITEM5, 0, 1.80, Rot(-30, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_sigillo", ID.PUZZLE_ITEM6, 0, 2.60, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_astro_castore", ID.PUZZLE_ITEM7, 0, 1.80, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_astro_polluce", ID.PUZZLE_ITEM8, 0, 1.80, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_manovella", ID.PUZZLE_ITEM9, 0, 2.20, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_fusibile", ID.PUZZLE_ITEM12, 0, 2.60, Rot(-60, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_chiave_scavi", ID.PUZZLE_ITEM13, 0, 2.00, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_chiave_lucchetto", ID.PUZZLE_ITEM14, 0, 2.00, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_pileo_castore", ID.PUZZLE_ITEM10, 0, 1.80, Rot(-15, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_pileo_polluce", ID.PUZZLE_ITEM11, 0, 1.80, Rot(-15, 0, 0), Axis.Y, -1, Act.USE),
        TEN.Flow.InventoryItem("cdv_chiave_ripostiglio", ID.KEY_ITEM1, 0, 1.5, Rot(-70, 0, 0), Axis.Y, -1, Act.USE),
    }
end

--------------------------------------------------

title = Level.new()
title.ambientTrack = "tr3_01_laras_theme"          -- Tomb Raider III, the theme of the titles
title.levelFile = "Data\\title.ten"
title.scriptFile = "Scripts\\Levels\\title.lua"
title.loadScreenFile = "Screens\\main.png"
title.farView = 130                                -- the flight goes over Tindari too
title.horizon1.enabled = false
title.layer1 = TEN.Flow.SkyLayer(TEN.Color(16, 20, 36), 2)   -- Title.lua changes sky and fog place by place
title.starfield = TEN.Flow.Starfield(2500)
title.fog = TEN.Flow.Fog(TEN.Color(16, 20, 36), 16, 36)
Flow.AddLevel(title)

--------------------------------------------------

Oliveri = TEN.Flow.Level()
Oliveri.nameKey = "cdv_level_oliveri"
Oliveri.scriptFile = "Scripts\\Levels\\Oliveri.lua"
Oliveri.ambientTrack = "cdv_amb_oliveri"
Oliveri.horizon1.enabled = true
Oliveri.levelFile = "Data\\Oliveri.ten"
Oliveri.loadScreenFile = Schermata("oliveri")
Oliveri.farView = 40
Oliveri.objects = CdvObjects()
Oliveri.horizon1.enabled = false
Oliveri.layer1 = TEN.Flow.SkyLayer(TEN.Color(16, 20, 36), 2)
Oliveri.starfield = TEN.Flow.Starfield(2500)
Oliveri.fog = TEN.Flow.Fog(TEN.Color(16, 20, 36), 16, 36)
TEN.Flow.AddLevel(Oliveri)

--------------------------------------------------

Marinello = TEN.Flow.Level()
Marinello.nameKey = "cdv_level_marinello"
Marinello.scriptFile = "Scripts\\Levels\\Marinello.lua"
Marinello.ambientTrack = "cdv_amb_marinello"
Marinello.horizon1.enabled = true
Marinello.levelFile = "Data\\Marinello.ten"
Marinello.loadScreenFile = Schermata("marinello")
Marinello.farView = 34
Marinello.objects = CdvObjects()
Marinello.layer1 = TEN.Flow.SkyLayer(TEN.Color(196, 180, 170), 2)
Marinello.starfield = TEN.Flow.Starfield(0)
Marinello.fog = TEN.Flow.Fog(TEN.Color(196, 180, 170), 12, 30)
TEN.Flow.AddLevel(Marinello)

--------------------------------------------------

Tindari = TEN.Flow.Level()
Tindari.nameKey = "cdv_level_tindari"
Tindari.scriptFile = "Scripts\\Levels\\Tindari.lua"
Tindari.ambientTrack = "cdv_amb_tindari"
Tindari.horizon1.enabled = true
Tindari.levelFile = "Data\\Tindari.ten"
Tindari.loadScreenFile = Schermata("tindari")
Tindari.farView = 130
Tindari.objects = CdvObjects()
Tindari.layer1 = TEN.Flow.SkyLayer(TEN.Color(214, 170, 132), 2)
Tindari.starfield = TEN.Flow.Starfield(0)
Tindari.fog = TEN.Flow.Fog(TEN.Color(214, 170, 132), 50, 125)
TEN.Flow.AddLevel(Tindari)

--------------------------------------------------

Sommersa = TEN.Flow.Level()
Sommersa.nameKey = "cdv_level_sommersa"
Sommersa.scriptFile = "Scripts\\Levels\\Sommersa.lua"
Sommersa.ambientTrack = "cdv_amb_sommersa"
Sommersa.horizon1.enabled = false
Sommersa.levelFile = "Data\\Sommersa.ten"
Sommersa.loadScreenFile = Schermata("sommersa")
Sommersa.farView = 40
Sommersa.objects = CdvObjects()
Sommersa.horizon1.enabled = false
Sommersa.layer1 = TEN.Flow.SkyLayer(TEN.Color(8, 30, 38), 2)
Sommersa.starfield = TEN.Flow.Starfield(0)
Sommersa.fog = TEN.Flow.Fog(TEN.Color(8, 30, 38), 8, 30)
TEN.Flow.AddLevel(Sommersa)
