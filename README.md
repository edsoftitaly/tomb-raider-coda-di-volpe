# Tomb Raider: Coda di Volpe

Avventura custom di Tomb Raider in un unico grande livello, ambientata a Oliveri e Tindari (Messina) in scala reale. Motore: **TombEngine (TEN)**, editor: Tomb Editor.

Il design document completo è in [`docs/GDD.md`](docs/GDD.md).

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
