# Coda di Volpe: quello che abbiamo imparato

Prontuario per partire subito con il prossimo episodio. Scritto a progetto chiuso (16 novembre 2026).
Tutto quello che c'è qui viene da errori fatti davvero o da codice letto nei sorgenti di TombEngine e Tomb Editor.

## 1. Come si lavora con Ed

- I test in gioco li fa Ed. Mai dire "risolto" senza che l'abbia visto lui: dire cosa è cambiato e cosa resta da provare.
- Ed modifica i `.prj2` a mano in Tomb Editor. Prima di toccare un file: ristagiarlo, controllare l'mtime, partire
  sempre dalla sua versione, fare un backup accanto al file (`backup\` per gli script), scrivere con la guardia mtime.
- Geometria nuova = texture su ogni faccia nuova, sempre. Una faccia senza texture lo obbliga a ricompilare e gli
  rompe il savegame. Prima di consegnare, renderizzare le stanze toccate (`DECOR=0 python3 tools/prj2_mesh.py ...`).
- Ogni ricompilazione di un livello invalida i savegame di quel livello: dirlo sempre, e preferire le correzioni
  solo-script quando bastano.
- Le prove del gioco si leggono nei log: `Engine\Logs\TENLog_*.txt`. Gli script scrivono righe `[CDV] f<frame> ...`
  per ogni evento (nemici, scene, altari, leve). Prima di ipotizzare, leggere l'ultimo log.
- Se il PC di Ed non offre una shell, si possono solo copiare file: i comandi (robocopy, zip) vanno dati come testo.
- Testo a schermo in inglese britannico, poco e solo per la trama; un testo mostrato una volta non si ripete.
- Gusto di Ed: luoghi veri e riconoscibili, mappe piccole e dense, niente ambienti vasti e vuoti, modelli realistici
  presi dal vero, musiche originali TR2/TR3 (niente colonne sonore custom), niente switch a muro brutti (porte a calcio).

## 2. Cose che NON funzionano (non riprovarle)

| Idea | Perché fallisce | Cosa usare |
|---|---|---|
| `Moveable:AttachObjCamera` per una scena lontana da Lara | Muove la camera solo nel frame della chiamata e non aggiorna la stanza della camera: la scena viene disegnata dalla stanza di Lara (vuoto nero) | Una camera fissa nel livello (`TeCamTen`, vedi `tools/sommersa_cam.py`), poi `cam:SetPosition`, `cam:SetRoomNumber`, `cam:Play(bersaglio)` a ogni frame |
| Scritte durante `View.FadeOut` | Il fade del motore copre anche le stringhe | Sprite nero `DisplaySprite` con priorità positiva (sta sotto le stringhe), poi `FadeIn` |
| `Sound.PlaySound(id, posizione lontana)` | Fuori portata, non si sente | Suonarlo su Lara (`CDV.Sfx`) |
| `Effects.MakeEarthquake(10..30)` | Dura 2-6 frame, ±n/2 unità: invisibile | Ripeterlo per più frame con forza 50-150 (`CDV.Quake`) |
| Far comparire un nemico "quando è fuori schermo, max 8 s" | Compare tardi e in vista | Nemici dietro una porta: subito all'apertura. Gli altri: subito se il punto non è inquadrato |
| Nemici che inseguono Lara ovunque e da subito | Arrivano da aree lontane troppo presto | Si accorgono di lei entro ~10 settori con linea di vista (o se feriti), mollano oltre ~20 |
| Scale da 4 click per nemici a piedi | Goon, cani, operai salgono 1 click e scendono 2 (LOT Basic) | Gradini da 1 click dove un nemico deve passare |
| Attese lunghe a schermo nero prima di crediti o scene | Il giocatore crede sia bloccato ed esce | Mai più di 2 secondi senza niente a schermo |
| Suoni non selezionati nel livello | Muti, solo un warning "Missing sound effect" nel log | Controllare `TeSelectedSounds` del prj2 prima di usare un id |
| Lasciare a galla un nemico d'acqua morto quando si svuota la stanza | Resta sospeso a mezz'aria | Posarlo sul pavimento con `Collision.Probe(...):GetFloorHeight()` |
| Fidarsi di una scena "che dovrebbe funzionare" | Tre tentativi sulla morte di Turi prima di leggere bene il sorgente | Leggere il sorgente TEN della funzione PRIMA di usarla, non dopo il primo fallimento |

## 3. Fatti del motore (TEN 2.0, letti nel sorgente)

- I timer degli script non vengono salvati: usarli solo per sequenze brevi. Lo stato vero va in `LevelVars`.
- Le zone di pathfinding dipendono dal flipmap; una porta chiusa rende muro i suoi settori. Nemici in stanze
  flippate possono non trovare la strada: serve un aiuto da script (traccia dei passi di Lara).
- `Creature:SetMood` forza l'umore finché non lo si rimette automatico. I goon col silenziatore sparano se hanno
  Lara davanti, in linea di vista, entro 8 settori.
- Flyby: flag 1 taglio, 4 loop, 16 nascondi Lara, 64 taglio a Lara, 128 taglio a camera; durata di un tratto
  circa 100/velocità frame.
- Animazioni di Lara utili: 134 incastro oggetto (click al frame 76), 131 chiave (click al 103), 425 raccolta da
  piedistallo basso (presa al frame 29). L'oggetto inserito deve comparire sul click, non prima.
- `DisplaySprite:Draw(priorità...)`: positiva = sotto le stringhe, negativa = sopra.
- Una camera fissa creata nel prj2 non ha bisogno di trigger: basta il nome Lua.

## 4. Formato prj2 (per patchare i livelli da script)

- Strumento base: `tools/prj2_patch.py` (carica, salva, oggetti, settori, aggiunta WAD). Verifica: `tools/prj2_check.py`.
- Chunk oggetti dopo un salvataggio di Tomb Editor: `TeMovTn3`, `TeStaTn3`, `TeFly3`, `TeCamTen`, `TeLig5`, `TePor2`.
- `edit_sectors` gestisce pavimento e facce, NON i chunk del soffitto: i settori-muro vanno copiati interi.
- Id oggetto nuovo = massimo esistente + 1. Stringhe = lunghezza int32 + UTF-8. Posizioni locali alla stanza, Y in su.
- File oltre ~25 MB non passano dalla copia diretta: inviarli come file e poi copiarli per identificativo.

## 5. Release

- Sviluppo in `C:\CodaDiVolpe`, release in `F:\OneDrive\TR_CodaDiVolpe`. Il `Gameflow.lua` di release è diverso
  (niente cheat, niente selezione livelli): non copiare mai quello di sviluppo.
- Lo zip della beta si sovrascrive sullo stesso file per non cambiare il link di condivisione.
- Blocco comandi completo: vedi `release/` e la fine di questo file.

```powershell
robocopy "C:\CodaDiVolpe\Engine\Data" "F:\OneDrive\TR_CodaDiVolpe\Engine\Data" Oliveri.ten Marinello.ten Tindari.ten Sommersa.ten title.ten
robocopy "C:\CodaDiVolpe\Engine\Scripts\Levels" "F:\OneDrive\TR_CodaDiVolpe\Engine\Scripts\Levels" Oliveri.lua Marinello.lua Tindari.lua Sommersa.lua Title.lua
robocopy "C:\CodaDiVolpe\Engine\Audio" "F:\OneDrive\TR_CodaDiVolpe\Engine\Audio" tr2_*.mp3 tr3_*.mp3 cdv_amb_*.mp3
Remove-Item "F:\OneDrive\TR_CodaDiVolpe\Engine\Logs","F:\OneDrive\TR_CodaDiVolpe\Engine\Save" -Recurse -Force -ErrorAction SilentlyContinue
Compress-Archive -Path "F:\OneDrive\TR_CodaDiVolpe" -DestinationPath "F:\OneDrive\CodaDiVolpe_beta.zip" -Force
```

## 6. Da dove ripartire per il prossimo episodio

1. Clonare questo repo: `tools/` contiene tutto (patch prj2, render di verifica, script Lua dei livelli con il
   framework `CDV`: zone, usi, drop, nemici, crediti, terremoti, flyby).
2. Riusare gli script dei livelli come base: il blocco `CDV` in testa a ogni `.lua` è lo stesso in tutti.
3. Decidere subito con Ed: mappa piccola per livello, percorso, enigmi, nemici e dove stanno le porte che li svegliano.
4. Costruire, renderizzare, consegnare un livello alla volta; Ed compila e prova; correggere leggendo il log.

## 7. Rimasto aperto alla chiusura

- Non confermati in gioco da Ed: scena della morte di Turi con la camera fissa, crediti finali sopra il nero,
  terremoti nuovi, urlo di morte (suono 482).
- Suoni mancanti segnalati nei log: 62 (Oliveri, Marinello, Sommersa), 11, 27, 37, 122 (Marinello).
- `title.ten` pesa circa 268 MB (livello titolo = stanze di tutti e quattro i livelli).
