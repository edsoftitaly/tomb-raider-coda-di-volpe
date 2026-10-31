# Coda di Volpe – Ripartenza da zero (v7)

Data: 31/10/2026. Stato: progetto, nessun livello ancora costruito.

## 1. Perché si riparte

Errori della v6, verificati giocando:
- Il livello era generato da script con stanze a griglia (camere da 2 m di profondità, arredi incastrati, telecamera che finiva dentro gli armadi).
- Le meccaniche native erano piazzate a tentativi:
  - la botola non era raggiungibile;
  - la serratura non rispondeva;
  - non c'era un bordo per aggrapparsi alla botola.
- Le texture erano generiche e i tetti piatti e vuoti.
- La strada era una striscia senza un punto d'interesse vero.

## 2. Cosa premiano i livelli con i voti più alti (TRLE.net / trcustoms)

Fonti: le recensioni TRLE di "Arms Race" (TEN, 9.08) e di "Heavenly Fallout" (7.63), più l'indice del tutorial ufficiale TEN.

| Aspetto | Premiato | Penalizzato |
|---|---|---|
| Gameplay | Meccaniche che aprono strade nuove, enigmi vari, progressione che si "apre" a poco a poco | Linearità totale, enigmi con una sola soluzione e senza indizi |
| Texture | Set coerente e unico per ambiente | Set mescolati, superfici grandi con la stessa texture ripetuta |
| Luce | Contrasto, zone leggibili anche al buio | Luce piatta |
| Oggetti | Oggetti d'inventario e nemici su misura | Arredo statico scarso |
| Struttura | Salvataggi e medikit ben distribuiti, segreti che non rompono il livello | Fine livello raggiungibile per sbaglio |
| Tecnica | Prestazioni stabili | Troppe luci dinamiche (lag in TEN) |

Durata attesa per un livello singolo apprezzato: 30–60 minuti.

## 3. Regole di costruzione da qui in avanti

1. **Un livello alla volta.** Non si passa al successivo finché il precedente non è giocato da inizio a fine sul PC di Ed, senza aiuti di test.
2. **Pianta prima, geometria dopo.** Per ogni livello va approvata una pianta quotata, con ogni stanza misurata su riferimenti reali: foto di Ed, Street View e satellite (solo come riferimento, mai come texture).
3. **Misure da Tomb Raider, non da catasto.** Si parte dalle dimensioni reali, poi si arrotondano ai blocchi (1 blocco = 2 m) e ai click.
   - Stanze principali di almeno 3×3 blocchi.
   - Corridoi di 1 blocco, mai stanze profonde 1 blocco.
   - Soffitti di 4–6 click.
4. **Ogni meccanica nativa ha una scheda di prova.** La scheda riporta posizione, rotazione e distanze richieste dal codice TEN (serrature, botole, porte, leve) e ha un test in gioco dedicato.
5. **Texture.** Un solo set per livello, da 256 px per blocco, con variazione e senza ripetizioni visibili.
   - Bordi, zoccolini e cornici sulle superfici grandi.
   - Niente texture stirate o in diagonale.
6. **Luce.** La luce cotta nella stanza fa il grosso del lavoro.
   - Pochi punti luce caldi (lampioni, finestre) contro un ambiente blu notte.
   - Nessuna luce dinamica superflua.
7. **Arredo urbano denso dove guarda il giocatore.** Auto, motorini, cassonetti, insegne, fili elettrici, vasi, panni stesi, persiane, citofoni, cartelli.
8. **Indizi.** Ogni enigma ha almeno un indizio visivo e una riga di diario o di dialogo.
9. **Salvataggi e risorse.** Medikit e munizioni dopo ogni scontro, nessun vicolo cieco.

## 4. Livello 1 – Oliveri, notte (rifatto)

### 4.1 Area reale rappresentata

- Casa di Ed, tre piani più la terrazza.
- Via Gaspare Amodeo, dalla casa all'incrocio con Via Stesicoro.
- Un cortile interno.
- Un tratto di lungomare con vista sul promontorio di Tindari illuminato, sullo sfondo.

### 4.2 Percorso (35–45 minuti)

1. **Camera da letto, 2° piano.** Lara si sveglia per i rumori. La stanza è vera (4×3 blocchi): letto, armadio, finestra sulla via. Dalla finestra si vede un ladro in strada che fa il palo.
2. **Scale e 1° piano.** Un ladro nel soggiorno: primo scontro. Medikit in cucina.
3. **Piano terra.** Il portone è sbarrato da fuori con una catena: lo si vede dall'interno.
   - Il secondo ladro lascia la **chiave del ripostiglio**.
   - Segreto 1 nella dispensa.
4. **Ripostiglio, 2° piano.**
   - La chiave apre la porta: serratura nativa con trigger chiave, provata in gioco.
   - Dentro, una scala a pioli a muro (climb) porta alla botola.
   - La botola si spinge da sotto, quindi niente salto da un gradino.
5. **Terrazza.**
   - Antenne, serbatoi, panni stesi e la vista sul paese.
   - Un salto sul tetto del vicino porta al segreto 2.
   - Si scende dal pluviale e dai balconi (sporgenze) fino in strada.
6. **Via Amodeo.**
   - Cani randagi.
   - Il palo scappa verso l'incrocio.
   - Il cancello del cortile si apre con una leva nascosta dietro il furgone, e l'indizio è un faro della moto che illumina la leva.
7. **Cortile.** Un enigma a due leve, pompa dell'acqua e cancello, con un orologio da sistemare. Segreto 3.
8. **Incrocio con Via Stesicoro.** Scontro con il palo. Raccolta la pagina del diario, inizia la sequenza di fine livello.

### 4.3 Oggetti d'inventario (modelli su misura)

| Oggetto | Dove | A cosa serve |
|---|---|---|
| Chiave del ripostiglio | Ladro al piano terra | Serratura del ripostiglio |
| Manovella | Cortile | Pompa dell'acqua |
| Pagina del diario | Palo | Fine livello |

### 4.4 Set di texture

- Intonaco: crema, rosa e ocra, con macchie d'umido.
- Persiane verdi.
- Basoli di pietra lavica.
- Marciapiede in pietra di Comiso.
- Ringhiere in ferro battuto.
- Tegole e lastrico solare.
- Interni: maiolica e parquet.

Tutte disegnate da riferimento, nessuna copiata da Google.

## 5. Criteri di consegna (tutti obbligatori)

- [ ] Livello completato da inizio a fine sul PC di Ed, senza file di test.
- [ ] Ogni meccanica (serratura, scala, botola, pluviale, leve, cancello, fine) provata in gioco e documentata con uno screenshot.
- [ ] Nessuna texture mancante, stirata o in diagonale, controllata stanza per stanza.
- [ ] Luce con contrasto, nessuna zona illeggibile.
- [ ] Tre segreti raggiungibili, nessuno che porti alla fine per sbaglio.
- [ ] Nessun crash né avviso di script nel log di TEN.

## 6. Livelli 2–6

Stessa procedura, uno alla volta, ognuno con pianta e criteri propri: Lungomare, Marinello, Laghetti, Tindari, Città sommersa. I livelli vecchi sul PC vengono archiviati, non cancellati, nel momento in cui il nuovo livello 1 li sostituisce.
