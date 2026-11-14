"""On-screen text of the installed scripts in British English, cut down to what the plot needs (Ed, 14/11/2026).

- every caption is translated or dropped ("" = no caption: the zone, its music cue and its function stay)
- CDV.Say wraps long lines itself (46 characters), lifts a caption of several lines so that it stays on screen, draws
  a little smaller, and shows nothing for an empty text
- item and level names in Gameflow.lua

usage: lua_inglese.py level <in.lua> <out.lua>      lua_inglese.py gameflow <in.lua> <out.lua>"""
import re
import sys

T = {
    # ---------------------------------------------------------------- common
    "Con le armi in mano non si può: prima nella fondina.": "Holster your weapons first.",
    "La porta è chiusa. (Mettiti di fronte e premi Azione: Lara la apre con un calcio.)": "Face the door and press Action to kick it open.",
    "Hai trovato una Stella dei Dioscuri!": "",
    # ---------------------------------------------------------------- Oliveri
    "Uno degli uomini della Volpe! Cercano il diario bizantino.": "One of the Fox's men. They're after the Byzantine diary.",
    "Oliveri, notte fonda. La luce è saltata, e dal piano di sotto arrivano rumori: qualcuno è entrato in casa.":
        "Oliveri, the dead of night. The power is out, and there are noises downstairs: someone has broken in.",
    "Su questo piano, dietro le porte, qualcuno sta frugando dappertutto.": "",
    "Il tombarolo aveva addosso la chiave del ripostiglio. Del diario, però, nessuna traccia: se l'è preso il capo.":
        "The box room key. No diary, though: their boss must have it.",
    "Il portone è sbarrato dall'esterno. Non resta che la botola del ripostiglio, quella che dà sul tetto.":
        "The front door is barred from outside. The only way out is the hatch in the box room, up to the roof.",
    "La serratura scatta: il ripostiglio è aperto.": "",
    "La cabina armadio è chiusa a chiave, e da lì si sale sul tetto. La chiave ce l'ha uno dei ladri.":
        "Locked. One of the thieves must have the key.",
    "Basta una spinta e la botola si apre.": "",
    "Dal tetto si vede il mare: una barca a luci spente si stacca dalla riva e punta su Marinello. Il diario è con loro. Da qui non si scende: bisogna passare dai tetti dei vicini, verso est.":
        "A boat with no lights is pulling away towards Marinello. The way down is over the neighbours' roofs, to the east.",
    "Il cancello del cortile è chiuso. Lo comandano i cinque interruttori numerati sul muro, lì a destra.":
        "The courtyard gate is shut. Five numbered switches on the wall control it.",
    "Sullo schermo: 33 2D 32 2D 35": "On the screen: 33 2D 32 2D 35",
    "Eccolo, il palo della banda. Sotto il braccio ha il diario bizantino.": "There he is, their lookout, with the diary under his arm.",
    "Dietro i bidoni del cortile c'era una Stella dei Dioscuri!": "",
    "Sui tetti dei vicini c'era una Stella dei Dioscuri!": "",
    "I cani della banda! E intanto il palo è scappato in cortile, dietro il cancello.":
        "Their dogs! And the lookout has run into the courtyard, behind the gate.",
    "Il diario è di nuovo mio, ma senza l'ultima pagina: quella è sulla barca, ormai al largo. Ci si rivede all'alba, a Marinello.":
        "The diary is mine again, but its last page is on that boat. Marinello, then, at dawn.",
    "Prima devo sistemare il palo della banda: è in cortile, dietro il cancello.": "Not yet: the lookout is in the courtyard, behind the gate.",
    "L'uomo col bastone aveva in tasca una chiavetta da lucchetto.": "A small padlock key.",
    "Il lucchetto cade e la catena viene giù. La botola è libera.": "",
    "La botola è chiusa da una catena col lucchetto, lì sul muro.": "The hatch is chained and padlocked.",
    "Il diario è rimasto a terra, in cortile, dov'è caduto il palo.": "The diary is still in the courtyard, where the lookout fell.",
    "Il diario bizantino! Ma l'ultima pagina è strappata. Sirene: i carabinieri chiudono la via. Resta libero solo il fondo, verso il municipio.":
        "The Byzantine diary, its last page torn out. Sirens: the Carabinieri have sealed the street. Only the town hall end is open.",
    "La porta del laboratorio ha la serratura elettrica: senza corrente non si apre.": "The workshop door has an electric lock. No power, no way in.",
    "La luce torna. In fondo all'ingresso scatta la serratura del laboratorio.": "The lights are back. The workshop lock clicks open.",
    "Il quadro elettrico: è saltato un fusibile. In cantina ce n'è di scorta.": "The fuse box: a fuse has blown. There are spares in the cellar.",
    # ---------------------------------------------------------------- Marinello
    "Marinello, all'alba. La barca dei tombaroli è passata di qui: la vecchia tonnara non è deserta come sembra.":
        "Marinello, dawn. The grave robbers' boat came this way: the old tuna fishery is not as deserted as it looks.",
    "C'è qualcuno di guardia. E ha un cane.": "",
    "Il registro del rais, anno 1911: «A paratoia chiusa, il Mergolo si riempie in una notte. La manovella sta nel magazzino delle reti, sul soppalco. Il sigillo è sotto chiave: le due leve sono rimaste sul fondo, murate nei cippi.»":
        "The rais's ledger, 1911: 'The crank is in the net store, up in the loft. The two levers of the Seal lie on the lake bed.'",
    "Sotto il peso della cassa la lastra cede: accanto al soppalco, un blocco sale dal pavimento. Da lì si può saltare e aggrapparsi.":
        "The slab sinks under the crate. By the loft, a block rises from the floor.",
    "Un altro, dal soppalco!": "",
    "Nel pavimento c'è una lastra di pietra con un anello di ferro. E lì vicino, una cassa che si può spingere.":
        "A stone slab with an iron ring, set in the floor. And a crate that can be pushed.",
    "La manovella si innesta nell'argano e comincia a girare. Fuori la paratoia si alza: con un boato, il Mergolo si svuota in mare.":
        "The winch turns. Outside, the sluice lifts and the Mergolo empties into the sea.",
    "Il boato li ha messi in allarme: ne arrivano altri dal canneto.": "",
    "L'argano che comanda la paratoia del Mergolo. All'ingranaggio manca la manovella.": "The winch of the Mergolo sluice. Its crank is missing.",
    "Le due catene tirano insieme: su, alla tonnara, si apre la camera del sigillo.":
        "Both chains pull together. Up at the fishery, the Seal chamber opens.",
    "Il fondo del Mergolo: un relitto, delle anfore e due leve di ferro incrostate, lontane l'una dall'altra.":
        "The bed of the Mergolo: a wreck, amphorae, and two iron levers, far apart.",
    "Una porta di ferro senza serratura. Due catene escono dal muro e scendono verso il lago.":
        "An iron door with no lock. Two chains run from the wall down to the lake.",
    "Il Sigillo si incastra a pressione nell'incavo della piastra. Uno scatto, e il cancello del canneto si apre.":
        "The Seal presses home. A click, and the gate to the reed bed opens.",
    "Di qui si passa al canneto e al Lago Verde. Accanto al cancello c'è una piastra di ferro con un incavo rotondo: sul fondo è inciso il tonno della tonnara.":
        "The way to the reed bed and the Green Lake. By the gate, an iron plate with a round recess: a tuna is engraved in it.",
    "In alto, nella rupe, si apre una bocca scura: la grotta di Donna Villa. La scala di corda è spezzata: ci sarà pure un'altra via.":
        "High in the cliff, a dark mouth: Donna Villa's cave. The rope ladder is broken. There must be another way up.",
    "In cima alla torre di vedetta c'era una Stella dei Dioscuri!": "",
    "Sul fondo, sotto il pontile, c'era una Stella dei Dioscuri!": "",
    "Oltre il cancello, il canneto. Il Lago Verde è ridotto a una conca di fango secco.": "The Green Lake is a bowl of dry mud.",
    "Il capoposto dei tombaroli aveva al collo la Chiave del Casello.": "Their foreman had the Sluice House Key round his neck.",
    "Il registro della salina: «Aperta la chiusa grande, il mare riempie il Lago Verde fino alla cengia della maga. Le donne ci salivano a nuoto, per portarle le conchiglie.»":
        "The salt works ledger: 'With the great sluice open, the sea fills the Green Lake up to the witch's ledge.'",
    "La chiave apre il casello e il volante gira. Il mare entra dal canale: il Lago Verde si riempie fin sotto la rupe.":
        "The wheel turns. The sea pours in: the Green Lake fills to the foot of the cliff.",
    "Il casello della chiusa grande è chiuso a chiave. Dietro la grata si vede il volante della paratoia.":
        "The great sluice house is locked. Behind the grille, the wheel of the gate.",
    "La chiusa grande: il casello è lassù, sulla spalla di pietra. Ci si arriva da un palo di ferro: salta e arrampicati.":
        "The sluice house is up on the stone shoulder. An iron pole leads there: jump and climb.",
    "Nella stiva del relitto del Lago Verde c'era una Stella dei Dioscuri!": "",
    "Cinque metri sopra il fango, una cengia nella rupe e, dietro, un buco nero. Troppo in alto: qui ci vorrebbe l'acqua.":
        "Five metres above the mud, a ledge in the cliff and a black hole behind it. Too high: this needs water.",
    "La cengia della maga. Dietro si apre un inghiottitoio: in basso si sente scorrere l'acqua. Da qui non si torna indietro.":
        "The witch's ledge. Behind it, a sinkhole. There is no way back from here.",
    "Sotto la rupe l'aria è fredda e sa di sale. Sulle pareti, lunghi graffi paralleli: sembrano lasciati da delle dita.": "",
    "Cinque altari, cinque conchiglie spente.": "Five altars, five silent shells.",
    "Il laghetto di Donna Villa. Al di là dell'acqua, su un piedistallo, una stella di bronzo: l'Astro di Castore.":
        "Donna Villa's pool. Across the water, on a pedestal, a bronze star: the Star of Castor.",
    "L'Astro è tuo, ma Donna Villa si è svegliata, e non è sola. Le armi non le fanno nulla: quel fuoco si spegne solo nell'acqua.":
        "The Star is yours, but Donna Villa is awake, and not alone. Bullets do nothing: that fire only dies in water.",
    "L'ultimo spirito si spegne nell'acqua con un urlo. Nella parete di fondo si apre l'uscita.": "The last spirit is gone. A way out opens in the far wall.",
    "Il soffitto cede: un masso! Riparati nelle nicchie, ai lati!": "The roof is giving way. Into the niches!",
    "In fondo alla galleria, pioli di ferro salgono nel buio. Lassù, la luce: Tindari.": "Iron rungs climb into the dark. Up there, daylight: Tindari.",
    "Al largo la corrente è troppo forte: meglio restare vicino a riva.": "The current is too strong out here. Stay close to the shore.",
    "La leva scatta e una catena scorre sotto il fango. Hai 20 secondi per tirare l'altra.":
        "The lever clicks and a chain runs under the mud. Twenty seconds to pull the other.",
    "Troppo tardi: la catena si è fermata. Da adesso hai altri 20 secondi per raggiungere la seconda leva.":
        "Too late: the chain has stopped. Twenty seconds, again, to reach the second lever.",
    # ---------------------------------------------------------------- Tindari
    "Tindari, primo pomeriggio. A ovest il teatro, a est, sul capo, il santuario: Turi è lassù.":
        "Tindari, early afternoon. The theatre to the west; to the east, on the headland, the sanctuary. Turi is up there.",
    "L'accampamento dei tombaroli. Hanno recintato gli scavi, e il capocantiere è sceso al teatro con le chiavi: laggiù a ovest, oltre il decumano.":
        "The grave robbers' camp. They have fenced off the dig, and the foreman has taken the keys down to the theatre, to the west.",
    "Il decumano. In fondo, a est, un muro chiude la strada verso il santuario.": "At the far end, to the east, a wall blocks the road to the sanctuary.",
    "Il teatro greco. I Romani ne fecero un'arena: e nell'arena c'è il capocantiere di Turi, con i suoi.":
        "The Greek theatre. Turi's foreman is down in the arena, with his men.",
    "In cima alla cavea, sotto il portico c'era una Stella dei Dioscuri!": "",
    "Una casa romana: l'atrio con la vasca, le stanze dipinte.": "",
    "Nel tablino, un riquadro di mosaico e un'iscrizione: «Castore, il mortale, calca la terra. Polluce cammina tra gli dei.»":
        "A mosaic panel and an inscription: 'Castor, the mortal, treads the earth. Pollux walks among the gods.'",
    "Il peristilio: il colonnato, il giardino.": "",
    "Dietro le anfore della casa romana c'era una Stella dei Dioscuri!": "",
    "Un intero pavimento di berretti, scuri e dorati.": "A whole floor of caps, dark and golden.",
    "La chiave gira nel cancello del criptoportico.": "",
    "Un cancello di ferro chiuso a chiave.": "An iron gate, locked.",
    "La basilica: ne restano i pilastri e gli archi. Nel pavimento, una scala scende nel buio.": "The basilica. In the floor, a stair leads down into the dark.",
    "Il criptoportico. Il pavimento è crollato per due campate, ma dalla volta pende una fune.":
        "The floor has fallen in, but a rope hangs from the vault.",
    "Tra le macerie, sotto la fune, c'era una Stella dei Dioscuri!": "",
    "La piazza del santuario. Gli uomini di Turi la tengono.": "",
    "Il ciglio del promontorio. Laggiù, la lingua di sabbia e i laghetti di Marinello: di lì sono salita.": "",
    "Il santuario della Madonna Nera. Il portale di bronzo è socchiuso: dentro c'è luce.":
        "The sanctuary of the Black Madonna. The bronze door is ajar: there is light inside.",
    "La ruota non gira. Al centro c'è un incavo vuoto, a forma di stella.": "The wheel will not turn. At its centre, an empty star-shaped socket.",
    "Il cancello in fondo alla cripta si apre.": "The gate at the end of the crypt opens.",
    "Le luci sopra il cancello si spengono.": "The lights over the gate go out.",
    "La cripta dei gemelli: due statue, una ruota di bronzo accanto al cancello.": "The crypt of the twins: two statues, and a bronze wheel beside the gate.",
    "Tre righe in latino, incise nel marmo.": "",
    "Il pozzo scende alle cisterne e ancora più giù, fino alle grotte marine sotto il capo. Turi è passato di qui.":
        "The shaft goes down to the sea caves under the headland. Turi went this way.",
    "Il capocantiere aveva al collo la chiave degli scavi.": "The foreman had the key to the dig.",
    "Catena e lucchetto. La chiave ce l'ha il capocantiere, giù al teatro: a ovest.": "Chained and padlocked. The foreman has the key, down at the theatre.",
    "La basilica della Madonna Nera. Gli uomini di Turi la stanno mettendo a soqquadro.": "",
    "«Nigra sum sed formosa.» La Madonna Nera, sopra l'altare. Dietro, qualcosa luccica.":
        "'Nigra sum sed formosa.' The Black Madonna, above the altar. Something glints behind her.",
    "L'Astro di Castore. Il suo posto è giù, nella cripta.": "The Star of Castor. It belongs down in the crypt.",
    # ---------------------------------------------------------------- Sommersa
    "Le grotte marine sotto il capo. Il campo dei tombaroli: Turi è passato di qui.": "The sea caves under the headland. Turi came this way.",
    "Sul fondo del sifone c'era una Stella dei Dioscuri!": "",
    "Una strada romana, sotto il mare. In fondo, tra le colonne, un cancello.": "A Roman street, under the sea. At the far end, between the columns, a gate.",
    "Ai lati del cancello, due piedistalli vuoti.": "Either side of the gate, an empty pedestal.",
    "Le terme. La vasca è asciutta.": "The baths. The pool is dry.",
    "L'acqua sale nel pozzetto: su, verso la loggia.": "The water is rising: up, to the loggia.",
    "Nella bottega del mosaicista c'era una Stella dei Dioscuri!": "",
    "La cisterna. Berretti scuri, berretti d'oro.": "The cistern. Dark caps, golden caps.",
    "Nella nicchia a metà parete c'era una Stella dei Dioscuri!": "",
    "Il tempio dei Dioscuri. La cella è otto metri più in basso, e là sotto ci sono gli uomini di Turi.":
        "The temple of the Dioscuri. The cella lies eight metres below, and Turi's men are down there.",
    "L'altare degli Astri: due incavi a stella, e canali di pietra che scendono verso il mare. Azione per posare l'Astro di Castore.":
        "The altar of the Stars: two star-shaped sockets. Press Action to set the Star of Castor.",
    "In fondo alla cella, senza più il peso dell'acqua, le valve di bronzo si aprono.":
        "With the weight of the water gone, the bronze doors at the end of the cella open.",
    "Il mare riempie la cella. Finché l'Astro resta sull'altare, l'acqua resta.": "The sea fills the cella. While the Star stays on the altar, so does the water.",
    "Laggiù si sbloccano le valve di bronzo. Ma con tutta quell'acqua addosso non si apriranno mai.":
        "Down below, the bronze doors unlock. But they will never open against all that water.",
    "Turi 'a Vulpi, con l'Astro di Polluce al collo. Polluce è l'immortale: le pallottole non lo fermano.":
        "Turi 'a Vulpi, the Star of Pollux round his neck. Pollux is the immortal one: bullets will not stop him.",
    "L'Astro di Polluce viene a galla da solo.": "The Star of Pollux floats up by itself.",
    "Castore e Polluce, insieme dopo duemila anni. La volta comincia a cedere!": "Castor and Pollux, together after two thousand years. The vault is giving way!",
    "Aria. Luce. L'alba sulla lingua di sabbia di Marinello, e in mano i due Astri dei Dioscuri.":
        "Air. Light. Dawn over the sand spit of Marinello, and both Stars of the Dioscuri in hand.",
}

NAMES = {
    "Diario bizantino": "Byzantine Diary", "Chiave della terrazza": "Terrace Key", "Mappa delle maree": "Tide Chart",
    "Chiave del Casello": "Sluice House Key", "Conchiglia del canto": "Singing Shell", "Sigillo della tonnara": "Seal of the Tonnara",
    "Astro di Castore": "Star of Castor", "Astro di Polluce": "Star of Pollux", "Manovella": "Crank", "Fusibile": "Fuse",
    "Chiave degli scavi": "Dig Site Key", "Chiave del lucchetto": "Padlock Key", "Pileo di Castore": "Cap of Castor",
    "Pileo di Polluce": "Cap of Pollux", "Chiave del ripostiglio": "Box Room Key", "Prologo - Via Amodeo": "Prologue - Via Amodeo",
    "La maga dei laghetti": "The Witch of the Lakes", "La metà perduta": "The Lost Half",
}

SAY_OLD = re.compile(r"function CDV\.Say\(text, seconds\)\n.*?\nend\n", re.S)
SAY_NEW = '''-- Captions: British English, only what the plot needs. Long text is broken into lines of at most CDV.WRAP characters
-- (so that nothing is cut at the sides) and a caption of several lines is lifted so that it stays on screen.
CDV.WRAP = 46
function CDV.Wrap(text, width)
    local lines, line = {}, ""
    for word in tostring(text):gmatch("%S+") do
        if #line > 0 and #line + 1 + #word > width then
            lines[#lines + 1] = line
            line = word
        else
            line = (#line > 0) and (line .. " " .. word) or word
        end
    end
    if #line > 0 then lines[#lines + 1] = line end
    return table.concat(lines, "\\n"), #lines
end
function CDV.Say(text, seconds)
    if RIP.attivo then return end
    if text == nil or text == "" then return end
    if msg ~= nil then
        TEN.Strings.HideString(msg)
    end
    local wrapped, n = CDV.Wrap(text, CDV.WRAP)
    local x, y = TEN.Util.PercentToScreen(50, 86 - 4.2 * math.max(1, n))
    msg = TEN.Strings.DisplayString(wrapped, TEN.Vec2(x, y), 0.8, TEN.Color(255, 244, 214), false,
        { TEN.Strings.DisplayStringOption.CENTER, TEN.Strings.DisplayStringOption.SHADOW })
    TEN.Strings.ShowString(msg, seconds or 6)
end
'''
STR = re.compile(r'"((?:[^"\\]|\\.)*)"')


def level(s):
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    assert len(SAY_OLD.findall(s)) == 1
    s = SAY_OLD.sub(lambda m: SAY_NEW, s, count=1)
    n = 0
    for it, en in T.items():
        a = '"' + it + '"'
        if a in s:
            n += s.count(a)
            s = s.replace(a, '"' + en + '"')
    left = []
    for line in s.split("\n"):
        if re.search(r'\btext = "|\bfail = "|CDV\.Say\("|TwinLevers\(', line):
            for m in STR.finditer(line):
                t = m.group(1)
                if len(t) > 12 and " " in t and t not in T.values():
                    left.append(t)
    print("  captions replaced:", n, "| left in Italian:", len(left))
    for t in left:
        print("    ??", t[:110])
    return s.replace("\n", nl), left


def gameflow(s):
    n = 0
    for it, en in NAMES.items():
        a = '{ "' + it + '" }'
        if a in s:
            s = s.replace(a, '{ "' + en + '" }')
            n += 1
    print("  names replaced:", n)
    return s


if __name__ == "__main__":
    src = open(sys.argv[2], encoding="utf-8", newline="").read()
    if sys.argv[1] == "level":
        out, left = level(src)
        assert not left
    else:
        out = gameflow(src)
    open(sys.argv[3], "w", encoding="utf-8", newline="").write(out)
