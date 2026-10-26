# TOMB RAIDER: CODA DI VOLPE
Game Design Document, v0.2 (26 ottobre 2026)

## 1. Vincoli di progetto (decisi con Ed)
- **Un unico livello**, durata target circa **2 ore**.
- **Scala reale**: i luoghi hanno le loro dimensioni vere. Si riduce l'area d'azione, non la scala.
- **Passaggio obbligato**: Via Gaspare Amodeo 1, Oliveri (casa vacanze di Ed). OSM: civico 1 a 38.12415 N, 15.05998 E, centro storico, a circa 60 m da Piazza 24 Maggio.
- **Tono**: avventura TR classica con componente **soprannaturale**. Enigmi non banali.
- **Asset**: si parte dai WAD standard di TR4 The Last Revelation. WAD custom ammessi se realistici.
- **Audio**: lo produce Ed a valle, nessun vincolo in fase di design.
- **Engine**: da decidere tra TRNG (come Cavassa) e TombEngine (TEN). Vedi par. 7.

## 2. Convenzione di scala (da validare con un test in-engine)
- 1 settore (1024 unità) = **2 m**; 1 click (256 unità) = **50 cm**.
- Test di validazione: Lara accanto alla porta d'ingresso e al balcone della casa di Via Amodeo, modellati con le misure reali.
- Il DTM SITR ha passo 2 m: **un campione di quota per vertice di settore**, senza ricampionamento.

## 3. Area d'azione (scala reale)
| Zona | Contenuto | Ingombro | Settori (2 m) |
|---|---|---|---|
| A. Oliveri centro | Casa Via Amodeo 1, Piazza 24 Maggio, Municipio, San Giuseppe, Via Saia Interna, Castello | ~464 x 512 m | ~232 x 256 |
| B. Strada costiera | Stazione Oliveri-Tindari, Contrada Marinello, fino al Casello FS (sezione in moto) | ~630 x 891 m (corridoio) | corridoio stradale |
| C. Marinello e laghetti | Casello FS, Grotta di Donna Villa (ingressi N e S), cinque laghetti, lingua di sabbia, Lago Mergolo della Tonnara | ~718 x 1269 m | ~359 x 635 |
| D. Rupe e Tindari | Sentiero Coda di Volpe, Santuario, Basilica, Torre tardo-romana/bizantina, Teatro Greco, Rocca Femmina (280 m), Galleria Madonna del Tindari | ~771 x 1002 m | ~385 x 501 |

Il percorso giocabile dentro ogni zona è più stretto del suo ingombro. Fuori dal percorso, terreno a bassa densità come fondale.

**Escluse**: Falcone, Sant'Anna, viadotti A20, mulino SP105, statua del Rais (fuori zona). Il loro ruolo narrativo passa ad altri luoghi.

## 4. Storia

### Il mito di partenza (leggende reali)
1. **Tyndaris dimezzata**: secondo Plinio il Vecchio metà della città greca franò in mare.
2. **La Madonna Nera**: la statua arrivò via nave dall'Oriente. La nave, bloccata nella baia, ripartì solo dopo averla sbarcata.
3. **I Laghetti di Marinello**: una bambina cade dalla rupe, il mare si ritira e la lingua di sabbia la salva.
4. **Donna Villa**: la maga della grotta che attirava i marinai col canto.

### Il twist
Sulla nave c'erano anche **gli Astri dei Dioscuri**, due dischi di bronzo greci dedicati a Castore e Polluce (Tindari prende il nome dal loro padre Tindaro). Insieme comandano le maree. I monaci li separarono: Castore in terra, Polluce in mare. La lingua di sabbia è l'ultima volta che qualcuno li ha usati. Donna Villa è la custode che i Greci legarono alla metà sommersa della città.

### Personaggi
- **Lara**: in vacanza nella casa di Via Amodeo, ha con sé un diario bizantino recuperato a Messina.
- **Turi "'a Vulpi"**: tombarolo, ex tonnaroto, base nel Casello FS. Vuole gli Astri per venderli.
- **Donna Villa**: soprannaturale, custode della Tindari sommersa. Il suo canto è una meccanica di gioco.

## 5. Flusso del livello (target 2 h)

| # | Luogo | Evento | Gameplay | Min |
|---|---|---|---|---|
| 1 | **Casa Via Amodeo 1** (notte) | La banda della Volpe irrompe per il diario | Tutorial in interni a scala reale: tre piani, balconi continui, terrazza coperta. Fuga dai balconi | 10 |
| 2 | Tetti e vicoli, Piazza 24 Maggio | Inseguimento nel centro storico | Tetti, Vico Barresi, Municipio, San Giuseppe | 8 |
| 3 | **Via Saia Interna, la Saia sotterranea** | Il vecchio canale passa sotto il centro | **Enigma idraulico** (E1) | 10 |
| 4 | **Castello di Oliveri** | Cisterna e mura sopra la Galleria Castello | **Enigma dei Gemelli** (E2) | 10 |
| 5 | **Ritorno alla casa** | Di giorno, la casa è il primo "santuario" | **Il diario e la terrazza** (E3), passaggio obbligato n. 2 | 5 |
| 6 | Strada costiera | Moto (oggetto standard TR4) fino a Marinello, inseguita dalla banda | Sezione a veicolo | 7 |
| 7 | **Casello FS** | Base della Volpe | Assalto, recupero della mappa delle maree | 8 |
| 8 | **Laghetti di Marinello** | La marea come meccanica (flipmap) | **Enigma delle maree** (E4) | 12 |
| 9 | **Tonnara al Mergolo** | Reti sommerse | **Enigma della tonnara** (E5) | 8 |
| 10 | **Grotta di Donna Villa** | Ingresso N, uscita S | **Il canto** (E6), prima apparizione di Donna Villa | 10 |
| 11 | **Sentiero Coda di Volpe** | Risalita della rupe, circa 270 m di dislivello | Arrampicata, vento | 7 |
| 12 | **Santuario** | Zona di quiete, nessun combattimento | **Lettura dall'alto** (E7) | 4 |
| 13 | **Tyndaris**: Basilica, Torre, Teatro | Parco archeologico | **I Dioscuri** (E8) e **la cavea** (E9). Astro di Castore | 12 |
| 14 | **Rocca Femmina** al tramonto | Donna Villa si rivela | Scontro soprannaturale. Lara si tuffa dalla rupe | 4 |
| 15 | **Grotte marine di Capo Tindari e Tindari sommersa** | La metà perduta della città | Subacqueo e sacche d'aria, Astro di Polluce, finale con la Volpe | 10 |
| Fine | La lingua di sabbia all'alba | Gli Astri uniti, il mare si ritira | Cinematica | 1 |

## 6. Enigmi (bozza)
- **E1, Saia**: tre chiuse distribuiscono l'acqua tra il canale e la cisterna del castello. Serve un livello esatto: troppo poco e la cassa galleggiante non arriva alla sporgenza, troppo e allaga il passaggio di uscita. Si risolve leggendo i segni di piena incisi sui muri.
- **E2, Castello**: due specchi spingibili sui camminamenti vanno allineati per proiettare la luce lunare (Castore e Polluce, costellazione dei Gemelli) attraverso una feritoia. La posizione si deduce dal diario e dalle stelle visibili nello skybox.
- **E3, Casa**: il diario contiene una griglia. Va sovrapposta al pavimento a mattonelle (texture dalla foto di Ed) e alla vista dalla terrazza: rivela il punto della costa dove la Volpe scava.
- **E4, Maree**: la mappa delle maree della Volpe permette di alternare alta e bassa marea. Con la bassa si cammina sulla barra, con l'alta si nuota tra i laghi. C'è una finestra a tempo prima del ritorno della marea: servono due cambi nell'ordine giusto.
- **E5, Tonnara**: le camere di rete sommerse si aprono solo nell'ordine del percorso del tonno fino alla "camera della morte". L'ordine sbagliato chiude Lara dentro e l'aria finisce.
- **E6, Il canto**: nella grotta la voce di Donna Villa indica il passaggio giusto con eco e panning. Le diramazioni sbagliate portano a trappole. Gli indizi visivi esistono ma sono scarsi: è un enigma audio vero.
- **E7, Santuario**: dal belvedere la lingua di sabbia, vista dall'alto, disegna un segno che indica l'ingresso della città sommersa. Si risolve osservando, senza interazioni distruttive.
- **E8, Dioscuri**: due meccanismi gemelli, uno nella Basilica e uno nella Torre, vanno attivati a pochi secondi l'uno dall'altro. Serve un percorso ottimizzato tra i due.
- **E9, Cavea**: nel Teatro Greco tre pietre risonanti vanno colpite nell'ordine in cui la cavea ne restituisce l'eco. Si risolve con l'audio di Ed.

## 7. Engine: **TombEngine (TEN)**, deciso il 26/10/2026
- Mappa senza limiti di dimensione dichiarati e scripting Lua nativo, utile per E4, E6 ed E8.
- WAD di partenza: standard TR4, convertiti per TEN. WAD custom ammessi se realistici.

## 8. Dati e pipeline
- OSM: Oliveri.osm e Tindari.osm (ricevuti).
- **DTM ricevuto**: MDT 2 m SITR (volo ATA 2007-2008), GeoTIFF float32, EPSG:3004 (Gauss-Boaga Est), 1080 x 1630 px, bbox 3004: 2523300, 4219000, 2525460, 4222260. Valore -9999 = nodata, solo nell'angolo NE in mare; mare e lagune a 0.
  - Link di download (testato il 26/10, funziona dal browser di Ed): `https://map.sitr.regione.sicilia.it/gis/services/modelli_digitali/mdt_2008/ImageServer/WCSServer?service=WCS&version=1.0.0&request=GetCoverage&coverage=1&crs=EPSG:3004&bbox=2523300,4219000,2525460,4222260&resx=2&resy=2&format=GeoTIFF`
  - **Il workspace di Claude è temporaneo**: Ed conserva il .tif e lo riallega a ogni nuova sessione di build.
- Quote reali (DTM): casa Via Amodeo 1: 2,6 m; Piazza 24 Maggio: 3,2 m; castello: 40 m; Casello FS: 7 m; Lago Mergolo: 0,3 m; Coda di Volpe (contrada): 118 m; Santuario: 277 m; Teatro: 269 m; Basilica: 269 m; Torre: 281 m; Rocca Femmina: 285 m.
- Pipeline: DTM, poi heightmap per zona, poi stanze TEN. Il framework di Cavassa non è recuperabile: il repo GitHub contiene solo la release e la chat ricevuta il 26/10 parla di pubblicazione e packaging. **La pipeline va riscritta da zero**: scrittura diretta dei file .prj2, portando in Python `TombLib/LevelData/IO/Prj2Writer.cs` (open source, repo TombEngine/Tomb-Editor). Vincoli verificati nel sorgente: `MaxNumberOfRooms = 1024`, `SectorSizeUnit = 1024`, `FullClickHeight = 256`, stanza di default 20x20 settori.
- Packaging finale (dalla chat di Cavassa): layout TombIDE, con PLAY.exe e README nella cartella principale e il gioco in `Engine\`. Le FMV si aggiungono a mano. La release va su GitHub.
- **Riferimenti visivi**: le foto di Ed come riferimento e come base per le texture. Google Street View solo come riferimento, poi texture ridisegnate "dritte".
  - Metodo: il 3D di Street View non si carica nel Chrome di Ed, quindi si prende il panoid dall'URL di Maps e si aprono le miniature statiche `streetviewpixels-pa.clients6.google.com/v1/thumbnail?...&panoid=ID&yaw=GRADI&pitch=GRADI` (pitch negativo = guarda in alto).
  - Panoid utili: casa Via Amodeo 1 `LBrxAtnBjKAv3zCTnF09_w` (yaw 170 facciata, 260 incrocio); Piazza 24 Maggio `55ey_Rex0qxNdPtx8i4dkQ`; Via Saia Interna `g9wMCN4n14RTHTu8L8Dm4g` (yaw 330); SP106 sotto il castello `inXpgTzs21EHgpIEb-oT5g`; inizio del sentiero Coda di Volpe: photosphere utente (sterrato con alberi).
  - Osservazioni: la casa è un edificio d'angolo color crema con fascia marrone alla base, persiane verdi, balconi in ferro battuto e porta verde a vetri sul lato dell'incrocio (con STOP). Via Saia Interna è un vicolo largo circa 3 m con balconi sporgenti, intonaco chiaro e muri grezzi: perfetto in scala reale. In Piazza 24 Maggio c'è un edificio rosa con balconi a mensola e la targa della piazza. Sotto il castello la SP106 ha fichi d'India e il cavalcavia dell'A20.

## 9. Donna Villa: la leggenda (fonti: balarm.it)
- È una maga o sirena: deforme, ma capace di apparire come una bellissima ragazza. Col canto attirava i marinai di passaggio, anche per le loro monete.
- Le vittime finivano in un **pozzo profondo** dentro la grotta. Secondo alcune versioni le sue ossa ne coprono le pareti, e i **graffi** sui muri sarebbero della sua rabbia quando veniva respinta. Si parla di un **tesoro** nascosto.
- La grotta: sulla rupe a circa **70 m** sopra il mare, sopra i laghetti. Ha stalattiti, stalagmiti e colonne. Un foro nella volta, che i locali chiamano **"il balcone"**, è da dove lei spiava le prede. Dall'ingresso si vedono le Eolie, Milazzo e Capo Calavà. Il sentiero di salita parte, secondo l'articolo, dalla Rocca Femmina.
- Dato reale da sfruttare: le ossa appartengono a un **cervide estinto in Sicilia**, e i graffi sono probabilmente erosione di molluschi di quando la grotta era a livello del mare.
- Uso in gioco: il pozzo diventa la trappola di E6. Il balcone è l'uscita verso la parete: Lara esce dal foro e prosegue in arrampicata. La voce del tesoro spiega perché la Volpe è lì. Le ossa di cervo sono un dettaglio da lore per un segreto. **Attenzione**: i nodi OSM "Grotta entrata Nord/Sud" sono a 8-13 m di quota, mentre la grotta della leggenda è a circa 70 m. Va verificato quale sia la vera Donna Villa: in gioco si può usare la grotta bassa come accesso e collegarla a quella alta.

## 10. Riferimenti fotografici ricevuti
Laghetti con canneto e pino davanti alla rupe; santuario da varie distanze (cupola dorata, basilica nuova con campanile, vecchio santuario-fortezza su sperone, cipresso, antenne); Capo Tindari dal mare con grotte al livello dell'acqua; spiaggia di Marinello in ciottoli con barche alla fonda; lingua di sabbia al tramonto; Oliveri dalla spiaggia con colline; uliveti con tralicci e Rocca Novara sullo sfondo; Eolie all'orizzonte da un punto rialzato vicino alla ferrovia; facciata della casa di Via Amodeo (tre piani, persiane verdi, balconi in ferro, terrazza coperta); texture di marciapiede a mattonelle; acqua turchese.

## 11. Stato della costruzione
- **Repo**: `github.com/edsoftitaly/tomb-raider-coda-di-volpe` (dati, generatori, build). È la fonte di verità tra una sessione e l'altra.
- **26/10/2026, Zona A generata**: `build/zona_A.prj2`, 330 x 300 settori (660 x 600 m), 110 stanze 32x32 con 398 portali, 658 edifici OSM estrusi, castello sulla rupe a 40 m, Lara davanti a Via Amodeo 1 (edificio OSM way/233746690, 38 settori, tetto di default a 9,5 m). Passa il checker. **Da verificare aprendolo in Tomb Editor.**
- Prossimi passi: apertura in Tomb Editor e feedback; altezze reali degli edifici chiave; interni della casa e del castello; texture.
