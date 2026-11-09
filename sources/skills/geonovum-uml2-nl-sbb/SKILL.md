---
name: geonovum-uml2-nl-sbb
description: "Zet een UML-informatiemodel in XMI (Enterprise Architect of andere UML-tools) of een Enterprise Architect-bestand (.eap, .eapx, .qea, .qeax, ook in een .zip) om naar een begrippenkader volgens NL-SBB (SKOS, Turtle). Objecttypen, attributen en waarden uit waardelijsten worden begrippen, waardelijsten worden collecties. Gebruik deze skill bij vragen als 'zet deze XMI om naar een begrippenkader', 'maak NL-SBB/SKOS-begrippen van dit UML-model', 'XMI naar SKOS', 'EAP naar begrippenkader' of 'begrippen uit een informatiemodel halen', ook als NL-SBB niet genoemd wordt. Eén script (bk.py) doet alle vaste stappen en zegt steeds wat de volgende stap is."
license: EUPL-1.2
allowed-tools: "Bash(python3 *) Bash(cd *) Bash(curl *) Bash(unzip *) Bash(cat *) Bash(sed *) Bash(grep *)"
metadata:
  nl.gov.status: concept
  nl.gov.review-by: "2027-05-08"
  nl.gov.source: https://docs.geostandaarden.nl/nl-sbb/nl-sbb/
  nl.gov.category: informatiemodellen
  nl.gov.tags: nl-sbb, skos, begrippenkader, uml, xmi, enterprise-architect, mim, informatiemodel, shacl
  nl.gov.bundle: geonovum-uml2-nl-sbb
  nl.gov.previous-name: xmi-begrippenkader
  nl.gov.generated-with: generatieve AI
---

> **Status: concept.** Deze skill is een hulpmiddel en geen officieel product van Geonovum. Een begrippenkader dat met deze skill is gemaakt, voldoet niet vanzelf aan NL-SBB: de publicatie van [NL-SBB](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/) en het SHACL-profiel in het [register](https://register.geostandaarden.nl/) zijn leidend, en de definities blijven die van het bronmodel. Overheidsorganisaties die generatieve AI inzetten dienen te voldoen aan het [Overheidsbreed standpunt voor de inzet van generatieve AI](https://open.overheid.nl/documenten/bc03ce31-0cf1-4946-9c94-e934a62ebe73/file). Zie ook de [disclaimer](https://github.com/fterpstra/skill-uml2-nl-sbb/blob/main/DISCLAIMER.md).

# XMI / EAP → NL-SBB-begrippenkader

## De drie regels

1. **Het script doet het werk, jij volgt het.** Draai `bk.py status`. Doe precies wat achter `VOLGENDE STAP:` staat. Draai daarna weer `bk.py status`. Herhaal tot er `KLAAR` staat.
2. **Compleetheid gaat boven snelheid.** Werk grote lijsten in delen af: één reviewdeel (25 begrippen) tegelijk, één beslispunt tegelijk. Sla nooit iets over en vat niets samen dat je niet gelezen hebt. Duurt een commando lang (validatie kan 10+ minuten duren): wacht, breek niet af en gebruik geen `timeout`.
3. **Je schrijft nooit zelf Turtle.** Alle keuzes gaan in `project.yaml`, bij voorkeur via `bk.py zet` of `bk.py overnemen`. Daarna maakt `bk.py genereer` het kader opnieuw.

## Zo roep je het script aan

`SKILL` is de map van deze skill. Werk in een eigen werkmap (bv. naast het modelbestand) en draai alles vanuit die map:

```bash
cd <werkmap>
python3 "SKILL/scripts/bk.py" status
```

Zet het pad tussen aanhalingstekens als er spaties in staan. Het script vindt zelf de `.venv` in de werkmap. Ontbreken de Python-pakketten, dan zegt `status` dat je `bk.py setup` moet draaien.

## Lezen: nooit hele grote bestanden

- Lees `werk/inventaris.json` en `uit/kader.ttl` **niet**. Zoek een element op met `bk.py toon <naam>` of `bk.py toon Klasse.attribuut`.
- Lees beslispunten met `bk.py vraag <nr>` (maximaal 40 details per keer; het script zegt hoe je de rest ziet).
- Lees een reviewdeel (`review/deel-NNN.md`, ongeveer 150 regels) wel **helemaal** voordat je oordeelt.
- Elk ander bestand: lees in stukken van hoogstens 200 regels.

## Wanneer je de gebruiker iets vraagt

Leg deze momenten voor, als keuzevraag met opties als dat kan; één onderwerp per vraag:

| Moment | Wat je voorlegt |
|---|---|
| `start` toont een packageboom | Welke package(s)? Stel het informatiemodel zelf voor. Ingesloten basismodellen (NEN 3610, GML, ISO, MIM) laat je weg, tenzij zo'n model zelf het om te zetten model is. |
| `start` noemt een voorbeeld | Mag het ingevulde voorbeeld (`voorbeelden/<naam>.yaml`) gebruikt worden? Zo ja: `bk.py voorbeeld <naam>`. |
| eerste `analyseer` | Eén keer: de standaardkeuzes (zie `references/keuzes.md`, "Samenvatting"). Vraag of ze goed zijn. |
| elk VRAAG-punt (`bk.py vraag <nr>`) | Het scriptvoorstel als eerste optie, "standaard houden" als tweede. |
| review met oordeel `term` | De betere termen, vóór je ze met `bk.py zet` vastlegt. |
| matches | De lijst uit `bk.py matches klaar`, vóór `--overnemen`. |
| optionele modules | `matches`, `vergelijk`, `bronnen`: alleen als de gebruiker dat wil. |

Antwoord van de gebruiker vastleggen:

- voorstel overnemen: `bk.py overnemen <code>`
- standaard houden: `bk.py overnemen <code> --standaard`
- iets anders: `bk.py zet <sleutel.pad> '<waarde>' --notitie '<wie/waarom>'`

Daarna: `bk.py analyseer` en `bk.py status`.

**Geen gebruiker beschikbaar** (je werkt zelfstandig)?
- Noemt `start` een voorbeeld, gebruik het dan: `bk.py voorbeeld <naam>`. Het voorbeeld bevat beoordeelde keuzes; noem het als aanname.
- Neem de overige scriptvoorstellen over: `bk.py overnemen --alle`. Keuzes die al in `project.yaml` staan (uit het voorbeeld of van de gebruiker) blijven staan. `--standaard` betekent: dit punt bewust op de standaardwaarde laten.
- Schrijf elke aanname als één regel in `werk/aannames.md` ("- wortel: voorstel overgenomen, niet bevestigd"). Het rapport neemt dat bestand over.
- Voer termcorrecties uit de review niet zelf door. Ze staan in `reports/review.md` en de gebruiker beslist erover.

## Voorbeelden van `bk.py zet`

```bash
bk.py zet kader.uri 'http://definities.geostandaarden.nl/imkl'
bk.py zet termen.vast.Appurtenance 'INSPIRE-leidingelement' --notitie 'dubbele term met Leidingelement'
bk.py zet attributen.term_correcties.hoogteligging 'hoogteligging'   # attribuutterm corrigeren (alle klassen)
bk.py zet 'attributen.term_correcties[Windturbine.aantal]' 'aantal windturbines'   # één klasse, volledige term
bk.py zet relaties.gebruik.TypeBak '[Bak, type]'                      # waardelijst aan attribuut koppelen
bk.py zet relaties.gebruik.Overig 'null'                               # bewust niet koppelen
bk.py zet termen.alias_als_voorkeursterm '["*"]'
bk.py zet 'termen.vast[gt5]' 'GT5'                                      # sleutel met punt of dubbele punt: tussen [ ]
bk.py zet 'termen.vast[recreatie: camping]' 'camping'                   # waardenaam met leestekens: ook tussen [ ]
bk.py zet kader.omschrijving 'Begrippen uit IMGeo 2.2: objecttypen en waarden'   # dubbele punt in tekst mag
```

Na elke `zet` controleert het script `project.yaml` (sleutels, klasse- en attribuutnamen, regexen). Een `FOUT:` herstel je met een nieuwe `zet`, voordat je verdergaat.

## De review (stap voor stap)

`bk.py review` verdeelt alle begrippen in delen van 25 (`review/deel-001.md`, …) en geeft per begrip **signalen** van het script, bijvoorbeeld "definitie begint met de term" of "afkorting in term". Per deel:

1. Lees het hele deel.
2. Geef elk begrip precies één oordeel:
   - `ok`: term en definitie zijn in orde.
   - `term`: de omzetting van de UML-naam is fout. Zet de betere term in de opmerking.
   - `definitie`: de brondefinitie is vaag, circulair of identiek aan een andere. Dit wordt een advies aan de beheerder van het UML-model; herschrijf de definitie niet.
   - `twijfel`: leg in de opmerking uit waarom.
3. Vul de oordelen in met één commando, één regel per begrip:

   ```bash
   bk.py oordeel <<'EOF'
   0001 ok
   0002 definitie | "middel zware" is een spelfout voor middelzwaar
   0003 term | wegdeel GPP -> wegdeel geluidproductieplafond
   0004 ok | signaal "afkorting" is terecht: GPP is de vaste afkorting in het model
   EOF
   ```

   Een reeks mag ook, voor hoogstens 25 begrippen die je allemaal gelezen hebt en die echt hetzelfde oordeel krijgen: `0101-0112 ok | zelfde patroon "klasse N", definities kloppen`.

   Opmerkingen zijn verplicht:
   - bij elk oordeel behalve `ok`;
   - ook bij `ok` als het script een signaal gaf. Leg dan uit waarom het signaal niet terecht is.
4. Het script toont de voortgang en het volgende deel. Ga door tot alle delen compleet zijn, en draai dan `bk.py review klaar`.

Bij een leesteken in de term geeft het signaal soms een voorstel, zoals `leesteken in term (voorstel: 'camping')`. Dat is een hint: neem het over in je `term`-oordeel als het klopt, of schrijf een betere term.

Moet het kader opnieuw gegenereerd worden (bv. na een termcorrectie)? Draai dan `bk.py review --opnieuw`. Oordelen van begrippen met dezelfde definitie neemt het script over; je beoordeelt alleen wat veranderd is. De nummers kunnen dan verschuiven; verwijs naar een begrip met zijn `id:` (vast, uit de URI).

Wat is een `term`-oordeel, en wat niet:
- Wel: een fout in de omzetting van de naam, zoals een verkeerde splitsing of een Engelse UML-naam zonder alias.
- Niet: een term met objecttype-context, zoals *naam bedrijf*. Die context zet het script bewust, als dezelfde attribuutnaam in meerdere klassen een andere betekenis heeft.

Toets bij elk begrip:
- de termconventies (zelfstandig naamwoord, enkelvoud, kleine letters, geen afkortingen of leestekens);
- of de definitie het begrip beschrijft en niet alleen de term herhaalt;
- of de definitie past bij de soort (objecttype, attribuut of waarde).

Is de NL-SBB-reviewskill (`nl-sbb`) beschikbaar? Gebruik die dan als achtergrond voor de oordelen.

## Rapport

`bk.py rapport` schrijft `reports/rapport.md` met alle cijfers. Jij vult alleen de sectie **Conclusie** in (3–6 zinnen), met uitsluitend cijfers uit het rapport. Noem altijd:
- LET OP-meldingen van `start`, zoals onleesbare memovelden;
- keuzes die zonder bevestiging zijn gemaakt (`werk/aannames.md`);
- de belangrijkste SHACL-violations en reviewbevindingen. Meldt de samenvatting "waarvan N violations door match-doelen die … geen skos:Concept zijn", dan was een extern kader niet bereikbaar: noem dat als oorzaak, niet als fout in het kader.

Wil je meer in het rapport, zoals de doorgevoerde termcorrecties? Schrijf dat in `werk/rapport-aanvulling.md` (Markdown, met eigen `##`-koppen) en draai `bk.py rapport` opnieuw. Bewerk `reports/rapport.md` zelf alleen in de Conclusie: `bk.py rapport` schrijft het bestand steeds opnieuw.

## Alle commando's

| Commando | Doet |
|---|---|
| `status` | Noemt de volgende stap. Draai dit na elke stap. |
| `setup` | Maakt `.venv` in de werkmap en installeert de pakketten. |
| `start <bestand> [--package P] [--zonder P]` | Maakt de inventaris uit XMI 1.1/2.x, EAP, EAPX, QEA of ZIP. Bij dubbele packagenamen geef je een pad: `Ouder/Kind`. |
| `voorbeeld <naam>` | Kopieert `voorbeelden/<naam>.yaml` naar `project.yaml`. `start` noemt het voorbeeld als het bij het bestand past. |
| `analyseer` | Maakt de beslispunten: INFO (alleen noemen), VRAAG (beslissen), BESLOTEN. |
| `vraag <nr>` | Toont één beslispunt met details en scriptvoorstel. |
| `overnemen <code…> \| --alle [--standaard]` | Zet scriptvoorstel(len) in `project.yaml`. |
| `zet <pad> '<yaml>' [--notitie T]` | Zet één keuze in `project.yaml` en controleert die. |
| `controleer` | Controleert `project.yaml`. |
| `toon <naam>` | Zoekt een klasse, waardelijst of attribuut op. |
| `genereer` | Maakt `uit/kader.ttl`, `uit/termen.tsv` en `uit/beslissingen.md`. |
| `valideer` | SHACL tegen NL-SBB 1.0.0 + extensie (run A kaal, run B met externe context). |
| `review [--opnieuw]` / `oordeel` / `review klaar` | Review in delen; oordelen invullen; compleetheid controleren en samenvoegen. |
| `matches` / `oordeel --matches` / `matches klaar [--overnemen]` | Optioneel: externe matches in delen (relatie per kandidaat). |
| `vergelijk <url>` / `bronnen` | Optioneel: vergelijking met een gepubliceerd kader (naar `uit/vergelijking.txt` en `.csv`, komt in het rapport); bronnencontrole. |
| `rapport` | Schrijft `reports/rapport.md`. |

De losse scripts (`inventaris.py`, `genereer.py` enz.) zijn er nog voor gevorderd gebruik; `bk.py` roept ze aan.

## Achtergrond (alleen lezen als het nodig is)

- `references/keuzes.md`: elke keuze met de standaard, de alternatieven en wanneer je afwijkt, plus bekende valkuilen (XMI 1.1, afgebroken bestanden, access-parser, MIM).
- `standaardkeuzes.yaml`: de standaarden zelf. Wijzig dit bestand alleen als de gebruiker een standaard blijvend wil veranderen.
- `voorbeelden/*.yaml`: ingevulde `project.yaml`-bestanden (IMGeo, IMGeluid, IMEV, IMKL, IMRO, NEN 3610).
- MIM-modellen (stereotypen als «Objecttype», «Codelijst»): de alias is meestal de Nederlandse naam, dus `alias_als_voorkeursterm: ["*"]`. Notities met koppen (`--Definitie--`) splitst het script zelf.

## Oplevering

- `uit/kader.ttl`, `uit/termen.tsv`, `uit/beslissingen.md`
- `project.yaml`
- `reports/`: SHACL, review en rapport

Vertel de gebruiker welke keuzes zijn voorgesteld en welke bevestigd, en dat de nieuwe URI's (nog) niet resolven.
