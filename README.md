# Tomb Raider: Coda di Volpe

Avventura custom di Tomb Raider in quattro livelli, ambientata a Oliveri, Marinello e Tindari (Messina). Motore: **TombEngine 2.0 (TEN)**, editor: Tomb Editor / TombIDE.

Ideata, scritta e diretta da **Edoardo Napoli**. Beta tester: Low, Attila, Marco, Dario e Antonio.

## Stato: beta 1 (16 novembre 2026)

| # | Livello | File | Script |
|---|---|---|---|
| - | Titolo | `levels/Title.prj2` | `scripts/Levels/Title.lua` |
| 1 | Oliveri - Via Amodeo | `levels/Oliveri.prj2` | `scripts/Levels/Oliveri.lua` |
| 2 | Marinello - The witch of the lagoons | `levels/Marinello.prj2` | `scripts/Levels/Marinello.lua` |
| 3 | Tindari | `levels/Tindari.prj2` | `scripts/Levels/Tindari.lua` |
| 4 | The lost half (La metà sommersa) | `levels/Sommersa.prj2` | `scripts/Levels/Sommersa.lua` |

I `.prj2` in `levels/` sono quelli da cui è stata compilata la beta (salvati da Tomb Editor il 16/11), gli script quelli in `Engine\Scripts` della stessa data.

- `scripts/Gameflow.lua`: versione di sviluppo (`CDV_RELEASE = false`: fly cheat e selezione livello attivi).
- `scripts/Gameflow_release.lua`: versione pubblicata (`CDV_RELEASE = true`: niente fly cheat, niente selezione livello).
- `assets/wads/`: tutti i wad usati dai livelli (manca solo `TombEngine.wad2`, che arriva con TombIDE). `CdV_Turi.wad2` è il boss finale, `CdV_Mafiosi.wad2` la banda (modelli di MadDerek).
- `assets/titolo/`: logo, schermata di caricamento, texture del livello titolo, `TombEngine.trproj`.
- `assets/foto/oliveri/`: fotografie di Edoardo Napoli usate nel prologo (`tools/intro_video.py`).
- `release/README.txt`: il README che accompagna il gioco.

Non sono nel repository, per dimensione o perché non sono nostri: l'eseguibile e i file del motore, i livelli compilati (`.ten`), il video del prologo (`Engine/FMV/cdv_intro.mp4`, si rigenera con `tools/intro_video.py`) e le musiche di Tomb Raider II e III (Nathan McCree) in `Engine/Audio`.

### Com'è fatta la release

Cartella con `PLAY.exe` e `Engine/` (`Bin`, `Shaders`, `Scripts` con `Gameflow_release.lua` rinominato `Gameflow.lua`, `Data/*.ten`, `Audio`, `Fmv`, `Screens`, `Textures`), senza `Logs` e `Save`. Lo zip si scarica dalla pagina [Releases](../../releases).

### Strumenti aggiunti il 15 e 16 novembre

`lua_15nov.py`, `lua_16nov.py`, `lua_colonne.py`, `lua_caccia.py`, `lua_titoli_coda.py` (script dei livelli); `sommersa_finale.py`, `prj2_nopath.py`, `prj2_copia_suoni.py`, `appoggio.py`, `appoggio_fix.py` (livelli); `wad_suono.py`, `turi.py` (wad); `titolo_foto.py`, `intro_video.py` (titolo e prologo); `suoni_check.py` (controllo suoni).

## Crediti

- Ideazione, storia e regia: Edoardo Napoli
- Fotografie di Oliveri, Marinello e Tindari: Edoardo Napoli
- Beta tester: Low, Attila, Marco, Dario e Antonio.
- Modelli della banda: MadDerek
- Musiche da Tomb Raider II e III: Nathan McCree
- TombEngine e Tomb Editor; costruzione dei livelli e script con Claude

Avventura amatoriale, gratuita e non in vendita. Tomb Raider e Lara Croft appartengono ai rispettivi proprietari.

Il design document è in [`docs/GDD.md`](docs/GDD.md). Quanto segue descrive la pipeline con cui è nato il primo livello dai dati reali.

## Struttura

| Cartella | Contenuto |
|---|---|
| `data/dtm/` | DTM SITR Regione Siciliana, 2 m (volo ATA 2007-2008), GeoTIFF EPSG:3004 |
| `data/osm/` | Estratti OpenStreetMap di Oliveri e Tindari |
| `tools/` | Generatori Python dei progetti Tomb Editor |
| `build/` | Progetti `.prj2` generati, anteprime e report |
| `docs/` | Design document |

## Pipeline

1. `tools/gen_zone.py <zona>` legge DTM e OSM e genera `build/zona_<zona>.prj2`:
   - terreno reale a 2 m per settore, con le quote del DTM sugli angoli dei settori e un passo di 12,5 cm;
   - edifici OSM estrusi come blocchi solidi e scalabili;
   - stanze 32x32 settori collegate da portali, come le crea Tomb Editor quando divide una stanza;
   - Lara davanti alla casa di Via Gaspare Amodeo 1 (zona A).
2. `tools/prj2_check.py <file>` rilegge il .prj2 con le stesse regole del loader di Tomb Editor: chunk letti per intero, settori completi, portali con controparte.
3. `tools/preview_zone.py <zona>` disegna l'anteprima dall'alto.
4. `tools/gen_textures.py` genera l'atlas `build/textures/coda_atlas.png` (2048 px, 128 px/m): facciate, pietra, roccia e 16 pavimenti con i rispettivi suoni dei passi. `tools/texturing.py` assegna i materiali: strade OSM, marciapiedi, uso del suolo, roccia sui pendii, facciate per stile, soffitti invisibili.
5. `tools/prj2_mesh.py` + `tools/render/` ricostruiscono la geometria dal .prj2 e fanno un render di verifica con three.js.

**Il livello pronto per TombIDE è `build/Oliveri/`**: copia `Oliveri.prj2` e la cartella `textures` in `C:\CodaDiVolpe\Levels\Oliveri\`. Le impostazioni (motore, script, suoni, WAD `Assets\Wads\TombEngine.wad2`) sono le stesse che scrive TombIDE. Lo script del livello è in `scripts/Levels/Oliveri.lua`.

`tools/prj2.py` è il writer `.prj2`, portato in Python da `Prj2Writer.cs` di [Tomb Editor](https://github.com/TombEngine/Tomb-Editor).

### Convenzioni
- 1 settore = 1024 unità = 2 m; 1 click = 256 unità = 50 cm.
- X verso est, Z verso nord, Y verso l'alto. Origine di ogni zona riportata nel report JSON (coordinate EPSG:3004).
- Le altezze degli edifici sono di default (OSM non le riporta): 9,5 m per gli edifici generici, 12,5 m per i condomini, 8 m per il castello sopra la rupe. Vanno corrette caso per caso.

### Requisiti
Python 3 con `numpy`, `rasterio`, `pyproj`, `matplotlib`.

## Crediti dati
- Mappe © OpenStreetMap contributors, ODbL.
- DTM: Regione Siciliana, Assessorato del Territorio e dell'Ambiente, S.I.T.R.
