"""Build the delivery zip: everything to extract over C:\\CodaDiVolpe."""
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build", "levels")
ORDER = ["Oliveri", "Lungomare", "Marinello", "Laghetti", "Tindari", "Sommersa"]
PROJECT = "C:\\CodaDiVolpe"

LEGGIMI = r"""TOMB RAIDER - CODA DI VOLPE  (episodio completo, 6 livelli, TombEngine)
==========================================================================

NOVITA' DELLA v4
- Santuario di Tindari modellato: basilica con facciata a capanna tra due campanili (orologio e monofore),
  portale bugnato con le porte in bronzo e San Pietro e San Paolo nelle nicchie, oculo, frontone AVE MARIA,
  tetti e cupola in ceramica azzurra, loggia nord di 76 m sui laghetti, santuario antico con il portale
  del 1598. Il title level ora gira intorno alla basilica.
- Terreno: texture grandi senza giunte (si ripetono ogni 16-32 m invece di 2 m), rupi a gradoni di roccia
  invece dei pendii con la texture stirata.
- Percorsi: i Laghetti passano da circa 1,3 km a circa 250 m (niente andata e ritorno), Tindari finisce
  nella cripta con un cunicolo verso il mare (niente corsa di 470 m alla Rocca).
- Incontri in piu' sui tratti lunghi (Oliveri, Lungomare, Marinello, Laghetti), imboscata ai Laghetti,
  topi se si sbaglia l'ordine delle leve nella cripta, meno soluzioni scritte a schermo.

INSTALLAZIONE
1. Estrai lo zip DENTRO C:\CodaDiVolpe e sovrascrivi tutto. Vengono aggiunti/sostituiti:
   - Levels\<livello>\<livello>.prj2 + textures   (i 6 livelli di Tomb Editor)
   - Levels\Titolo\Titolo.prj2                      (nuovo title level: Capo Tindari sui Laghetti, diventa Data\title.ten)
   - Engine\Scripts\CdvRiprese.lua                  (interruttore della modalita' riprese)
   - Engine\FMV\LEGGIMI_VIDEO.txt                    (nomi dei video che il gioco cerca)
   - Presentazione\                                  (readme inglese per TRLE.net e anteprime delle inquadrature)
   - Assets\Wads\CodaDiVolpe\*.wad2                 (nemici, porte, leve, oggetti: libreria ufficiale TombEngine/Resources)
   - Engine\Scripts\Gameflow.lua                     (6 livelli, nomi degli oggetti, 12 segreti)
   - Engine\Scripts\Levels\<livello>.lua             (logica di enigmi, nemici, messaggi, segreti, fine livello)
2. Doppio clic su COMPILA_TUTTO.bat: lancia Tomb Editor (C:\Tomb Editor) in modalita' batch e compila
   i sei livelli + il titolo uno dopo l'altro in Engine\Data. Ci mette qualche minuto per livello.
   In alternativa: apri ogni .prj2 in Tomb Editor e premi F5.
3. Avvia da TombIDE (Play) o con Engine\Bin\x64\TombEngine.exe. Dal menu: Nuova partita, oppure Selezione livello.

NOTE
- Fly cheat e selezione livello sono attivi per i test (Gameflow.lua: EnableFlyCheat / EnableLevelSelect).
- Ogni livello parte anche da solo: gli oggetti che arrivano dal livello prima vengono dati in automatico se mancano.
- La soluzione completa e' in SOLUZIONE.txt.
- Audio: le tracce ambientali sono quelle di default (108). Voce di Donna Villa, eco della grotta e musiche sono da fare.

DECORAZIONI (CdV_Decorazioni.wad2, 46 statici, ID 100-145, texture procedurali)
- Vegetazione: fico d'india (2), elicriso (2), asparago selvatico (2), pino d'Aleppo (3), ulivo (3).
- Citta': lampioni (piazza, a muro, stradale, lungomare a due bracci), panchina, vasi bianchi giganti
  (fiori, palma, ulivo), parco giochi (scivolo, altalena, dondolo, molla, castello), campi sportivi
  (torre faro, recinzione, porta da calcio), dehors (tavolo con sedie, ombrellone, fioriera).
- Mare: gozzo, gommone, motoscafo, barca a vela, barchetta in secca, ombrellone da spiaggia.
- Veicoli: 4 auto, furgone, camper, 2 scooter, bicicletta.
- Sono gia' piazzati in tutti i livelli (2.800-5.500 per livello) secondo la mappa: uliveti a filari
  ogni 6 m, pinete, macchia sui pendii rocciosi, auto nei parcheggi e lungo le strade, camper nei
  campeggi, dehors davanti a bar e ristoranti, barche ormeggiate al largo e in secca sulla spiaggia.
  Le zone degli enigmi (rampe, cancelli, leve, teatro) sono lasciate libere.
- Alberi, lampioni, veicoli e arredi hanno collisione; cespugli ed elicriso no (Lara ci passa attraverso).
- Se il gioco rallenta, dimmelo e abbasso la densita' della vegetazione.

PRESENTAZIONE E VIDEO
- Modalita' riprese: in Engine\Scripts\CdvRiprese.lua metti attivo = true. In ogni livello partono da sole
  le inquadrature (flyby 1, 2, 3...) senza messaggi e con Lara nascosta: le registri con OBS.
  Le telecamere sono normali flyby di Tomb Editor: le puoi spostare e ritoccare (Speed, FOV) a mano.
- Video: metti i file in Engine\FMV con i nomi di LEGGIMI_VIDEO.txt. Se manca un video il gioco va avanti.
- Per la release: in Gameflow.lua CDV_RELEASE = true (niente fly cheat e selezione livello),
  CDV_SCHERMATE = true quando hai le schermate di caricamento, CdvRiprese attivo = false.

COSE DA GUARDARE PER PRIME IN GIOCO (non le ho potute provare nel motore)
- Leve a pavimento (Saia, Basilica, Torre, cripta): si spingono da sud e si riportano indietro da nord.
- Le casse sotto i buchi nei soffitti: salto + aggrappo per risalire (casa, cisterna, Saia, cripta, grotta).
- La porta del Casello FS e' "magica": entrando nella porta a sud Lara viene portata dentro (dissolvenza).
- Il camino del balcone nella grotta: muro scalabile verso est.
- Se un nemico resta fermo, e' perche' esce dalla stanza in cui ha il pathfinding (il terreno ne e' escluso apposta:
  il compilatore si bloccava al 48%).
"""


def bat():
    return ("@echo off\r\n"
            "rem Compila tutti i livelli di Coda di Volpe con Tomb Editor (modalita' batch).\r\n"
            "copy /Y \"%~dp0compila_livelli.xml\" \"%TEMP%\\cdv_compila.xml\" >nul\r\n"
            "start \"\" /wait \"C:\\Tomb Editor\\TombEditor.exe\" \"%TEMP%\\cdv_compila.xml\"\r\n"
            "echo Fatto. Controlla i file .ten in Engine\\Data.\r\n"
            "pause\r\n")


RIPRESE = """-- Modalita' riprese di Coda di Volpe (per registrare trailer, intro e screenshot).
-- attivo = true : all'inizio di ogni livello partono da sole le inquadrature (flyby 1, 2, 3...),
--                 senza messaggi a schermo e senza video. Lara e' nascosta durante le inquadrature.
-- ciclo  = true : finita l'ultima, ricomincia dalla prima.
-- solo   = 2    : solo l'inquadratura numero 2 (nil = tutte).
-- Ricordarsi di rimettere attivo = false prima di creare l'archivio per TRLE.net!
return { attivo = false, ciclo = false, solo = nil }
"""

FMV = """Cartella dei video di Coda di Volpe (TombEngine li cerca qui: mp4, mkv, mov o avi).
Se un file manca il gioco va avanti lo stesso (scrive solo un avviso nel log).

cdv_intro.mp4         intro della storia, all'inizio di Oliveri (non quando si carica un salvataggio)
cdv_02_lungomare.mp4  apertura del livello 2 (facoltativo)
cdv_03_marinello.mp4  apertura del livello 3 (facoltativo)
cdv_04_laghetti.mp4   apertura del livello 4 (facoltativo)
cdv_05_tindari.mp4    apertura del livello 5 (facoltativo)
cdv_06_sommersa.mp4   apertura del livello 6 (facoltativo)
cdv_finale.mp4        finale, dopo l'ultimo messaggio della Citta' Sommersa, prima dei titoli del motore
cdv_logo.mp4          logo all'avvio del gioco: si attiva in Gameflow.lua (CDV_LOGO)

Il giocatore puo' saltare il video con il tasto Deselect o Look.
Formato consigliato: H.264 + AAC, 1920x1080, 30 fps.
"""


def xml():
    files = "\n".join("    <string>%s\\Levels\\%s\\%s.prj2</string>" % (PROJECT, k, k) for k in ORDER + ["Titolo"])
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<BatchCompileList xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n  <Files>\n%s\n  </Files>\n</BatchCompileList>\n' % files)


def main(out):
    sol = ["TOMB RAIDER - CODA DI VOLPE: SOLUZIONE", "=" * 40, ""]
    for k in ORDER:
        sol += open(os.path.join(B, k, "soluzione.txt")).read().splitlines()
    sol += ["", "I 12 segreti sono le Stelle dei Dioscuri: 3 a Oliveri, 2 sul Lungomare, 1 a Marinello, 2 ai Laghetti,",
            "2 a Tindari, 2 nella Citta' Sommersa."]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for k in ORDER:
            d = os.path.join(B, k)
            z.write(os.path.join(d, k + ".prj2"), "Levels/%s/%s.prj2" % (k, k))
            for f in sorted(os.listdir(os.path.join(d, "textures"))):
                z.write(os.path.join(d, "textures", f), "Levels/%s/textures/%s" % (k, f))
            z.write(os.path.join(d, k + ".lua"), "Engine/Scripts/Levels/%s.lua" % k)
        d = os.path.join(B, "Titolo")
        z.write(os.path.join(d, "Titolo.prj2"), "Levels/Titolo/Titolo.prj2")
        for f in sorted(os.listdir(os.path.join(d, "textures"))):
            z.write(os.path.join(d, "textures", f), "Levels/Titolo/textures/%s" % f)
        z.write(os.path.join(B, "Gameflow.lua"), "Engine/Scripts/Gameflow.lua")
        z.writestr("Engine/Scripts/CdvRiprese.lua", RIPRESE.replace("\n", "\r\n"))
        z.writestr("Engine/FMV/LEGGIMI_VIDEO.txt", FMV.replace("\n", "\r\n"))
        pres = os.path.join(ROOT, "build", "presentazione")
        if os.path.isdir(pres):
            for f in sorted(os.listdir(pres)):
                z.write(os.path.join(pres, f), "Presentazione/" + f)
        wd = os.path.join(ROOT, "assets", "wads")
        for f in sorted(os.listdir(wd)):
            if f.endswith(".png"):
                continue
            z.write(os.path.join(wd, f), "Assets/Wads/CodaDiVolpe/" + f)
        z.writestr("LEGGIMI.txt", LEGGIMI.replace("\n", "\r\n"))
        z.writestr("SOLUZIONE.txt", "\r\n".join(sol) + "\r\n")
        z.writestr("COMPILA_TUTTO.bat", bat())
        z.writestr("compila_livelli.xml", xml())
    print(out, "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main(sys.argv[1])
