# Keuzes bij de omzetting XMI → NL-SBB

De standaardwaarden staan in `standaardkeuzes.yaml`. Ze zijn gekozen door de gebruiker bij de IMGeo 2.1-conversie (november 2026). Wijk per project af in `project.yaml`.

## Samenvatting (om aan de gebruiker voor te leggen)

1. **Wat wordt een begrip:**
   - objecttypen, datatypen, attributen en waarden uit waardelijsten worden allemaal `skos:Concept`
   - elke waardelijst wordt een `skos:Collection`
   - de scope is volledig: ook abstracte klassen, datatypen, generieke attributen en ongebruikte waardelijsten
2. **Waarden in meerdere waardelijsten:**
   - zelfde naam + zelfde definitie → één begrip, lid van meerdere collecties
   - definities die alleen in leestekens verschillen → samenvoegen
   - inhoudelijk andere definitie → splitsen in aparte begrippen (de gebruiker kiest de termen)
3. **Termen:**
   - camelCase wordt woorden in kleine letters; afkortingen blijven staan
   - attributen krijgen objecttype-context (`type bak`) waar de naam niet uniek is
   - de UML-naam wordt `altLabel`; `skos:notation` = `Klasse.attribuut`
4. **Relaties:**
   - generalisatie → `skos:broader` + `isothes:broaderGeneric`
   - attribuut `related` objecttype
   - waarde `related` het attribuut dat de lijst gebruikt (of het objecttype als dat attribuut niet in het model staat)
   - parent-tag van waarden → `broaderGeneric`
5. **URI's:** `{kader}/id/begrip/{Term}`, `{kader}/id/collectie/{Lijst}`, `{kader}/id/bron/{Sleutel}`.
6. **Extern:**
   - `dct:source` uit de tag *Herkomst definitie*
   - harmonisatierelaties naar NEN 3610:2011 en BAG
   - aliasnamen als `altLabel@en` waar de alias de voorkeursterm is
7. **Validatie:** NL-SBB 1.0.0 + extensie, mét externe kaders als context.

## Per onderdeel

| Sleutel | Standaard | Alternatieven | Wanneer afwijken |
|---|---|---|---|
| `kader.uri` / `titel` / `omschrijving` | – (verplicht) | | Altijd invullen |
| `uris.*` | patroon definities.geostandaarden.nl | Elk patroon met `{kader}` en `{naam}` | Ander publicatiedomein of URI-strategie |
| `stereotypen.waardelijst` / `datatype` | codeList, enumeration, … / dataType, union, … | Eigen stereotypen toevoegen | Het model gebruikt andere stereotypen (zie analyse "stereotypen") |
| `stereotypen.overslaan` | [] | Lijst | Bv. «Interface», «Union», hulpklassen |
| `scope.*` | alles `true` | `false` per onderdeel | Als de gebruiker bv. alleen objecttypen en waarden wil |
| `termen.naam_prefixen_verwijderen` | [] | bv. `["bgt-", "plus-"]` | Het model zet prefixen in namen (analyse "prefixen") |
| `termen.vast` | {} | UML-naam → term | Namen die niet omgezet mogen worden (`NEN3610ID`, `0dB`). Gaat vóór `term_tag` en alias, dus ook om dubbele termen op te lossen |
| `termen.term_tag` | `null` | Tagnaam, bv. `Term(NL)` | Het model zet de Nederlandse term in een tagged value (IMKL) |
| `termen.cijfers_scheiden` / `decimaalteken` | `false` / `,` | `true` | Namen met getallen: `golflengte12_5` → `golflengte 12,5` (IMGeluid) |
| `termen.samenstellingen` | {} | "a b" → "ab" | camelCase splitst een samenstelling (`gebouw installatie`) |
| `termen.woorden_behouden` | namen van informatiemodellen (IMGeo, IMKL, …) | Lijst | Woorden die niet gesplitst en niet in kleine letters gezet mogen worden (anders: `IMGeo-object` → *IM geo-object*) |
| `termen.alias_als_voorkeursterm` | [] | Stereotypen, of `["*"]` | De alias bevat de Nederlandse naam (IMGeo: ADEElement; MIM-modellen: `["*"]`). Geldt ook voor attributen en waarden |
| `termen.alias_naam_als_altlabel` | `en` | Taalcode of `null` | De UML-naam is geen Engelse term |
| `attributen.context_altijd` | type, naam, tekst, positie, hoek, fysiek voorkomen | Lijst | Generieke attribuutnamen in het model |
| `attributen.context_bij_dubbele_naam` | `true` | `false` | – |
| `attributen.prefix_term` | {} | `{"plus-": "plus "}` | Een prefix moet zichtbaar blijven in de term |
| `attributen.term_correcties` | {} | UML-naam → basisterm; `Klasse.attribuut` → volledige term | Typefouten in UML-namen; met `Klasse.attribuut` een onhandige contextterm in één klasse (geen contextregel). Bij een keuze-datatype («Keuze», alias 'afstand of geometrie van X') wordt de contextterm vanzelf 'afstand van X' |
| `attributen.notatie` | `{klasse}.{attribuut}` | Bv. `{attribuut}` | Alleen als attribuutnamen uniek zijn (anders dubbele codes) |
| `attributen.samenvoegen` | `naam_en_definitie` | `nooit` | De gebruiker wil per klasse een eigen attribuutbegrip |
| `waarden.samenvoegen` | `naam_en_definitie` | `nooit` | Eén begrip per waardelijst (zoals in het gepubliceerde IMGeo-kader; geeft dubbele voorkeurstermen) |
| `waarden.splitsingen` | {} | "waarde\|Lijst" → term | Verplicht bij gelijke naam en inhoudelijk andere definitie |
| `waarden.automatisch_splitsen` | `null` | Patroon, bv. `"{lijst} {waarde}"` | Veel conflicten van dezelfde soort, bv. codes 1–12 in meerdere lijsten (IMGeluid) |
| `waarden.zelfde_begrip` | [] | Waardenamen | Eén begrip ondanks kleine verschillen in formulering (IMEV: "gegeven in transitie") |
| `waarden.hernoem` | {} | waarde → term | Bv. `niet-bgt` → `niet-BGT-object` |
| `waarden.notatie_tag` | `null` | Tagnaam, bv. `Code` | Waarden hebben codes die als notatie moeten |
| `relaties.generalisatie` | `broaderGeneric` | `broader`, `geen` | – |
| `relaties.wortel` | `null` (klassen zonder superklasse = topbegrip) | UML-naam | Er is een basisklasse (`_CityObject`, `GeoObject`) |
| `relaties.zelfstandig` | [] | UML-namen | Klassen zonder superklasse die topbegrip moeten blijven |
| `relaties.externe_superklasse_op_naam` | `true` | `false` | – |
| `relaties.attribuut_objecttype` / `waarde_attribuut` | `related` | `geen` | `geen` geeft verweesde begrippen (SHACL-waarschuwing) |
| `relaties.gebruik` | {} + automatisch via attribuuttype | Lijst → [klasse, attribuut\|null] of `null` | Als attribuuttypen niet naar de lijst verwijzen (IMGeo: GenericName) |
| `bronnen.tag` / `mapping` | ["Herkomst definitie", herkomstDefinitie] / [] | Andere tag(s); regex-regels | Altijd een mapping maken voor de tagwaarden uit de analyse. Een URL als herkomst wordt een brondocument met `foaf:page` |
| `definities.sectie_definitie` / `sectie_toelichting` / `sectie_bron` / `sectie_negeren` | definitie/definition, toelichting/description, source/bron/herkomst, regels/name/… | Lijsten van koppen | Notities met koppen als `--Definitie--` (MIM-modellen). Zonder koppen telt de hele notitie als definitie |
| `definities.toelichting_tag` / `toelichting_negeer` | [Toelichting, toelichting] / standaardteksten uit het MIM-profiel | [] = uit | Toelichting → `skos:scopeNote` |
| `matches` | [] | {term, relatie, uri} | Na stap 5, met bevestiging van de gebruiker |
| `externe_kaders` | NEN 3610:2011 (bulk), BAG (per begrip) | Kaders toevoegen | Andere basismodellen of registraties |
| `validatie.met_externe_context` | `true` | `false` | – |
| `validatie.extensie_fallback` | kopie van de extensie in de GitHub-repository | URL | Alleen gebruikt als `shacl/` bij de installatie ontbreekt |
| `besloten` | [] | Codes van VRAAG-punten | Gezet door `bk.py overnemen`: het punt is beslist (ook als de standaard blijft) en telt niet meer als open vraag |
| `notities` | [] | Vrije tekst | Wie besloot wat en waarom; komt in het rapport. `bk.py zet ... --notitie` vult dit aan |

## Bekende aandachtspunten uit de IMGeo-conversie en de Geonovum-modellen (november 2026)

- **XMI 1.1** (EA "XMI/UML 1.3"): definities staan in tagged values (`documentation`, `description`), memo-tags in `XMI.extension/UML:Comment`. Enumeraties zijn `Class «enumeration»`. Getest: IMGeluid 3.1.1 XMI 1.1 en EAPX geven een gelijke inventaris.
- **Afgebroken bestanden**: de IMRO2012-XMI in het register is afgebroken (ongeldige XML). Gebruik dan het EAP-bestand.
- **access-parser** decodeert Access' *compressed unicode* niet (tekens als '–' en 'é' buiten Latin-1 worden \x13 e.d.); `inventaris_eap.py` vervangt die functie. Soms leest access-parser de `ea_guid` of een memoveld niet; het script gebruikt dan een id op Object_ID en meldt onleesbare definities bij naam.
- **MIM-stereotypen** (`Codelijst`, `Enumeratie`, `Gestructureerd datatype`, `Primitief datatype`, `Keuze`) staan in de standaardlijsten.
- **Waardelijsten zonder waarden** (extern beheerd, bv. IMKL) worden geen lege collectie; de attributen die ze gebruiken worden wel begrip.

- **EAP-bestanden** worden gelezen met `access-parser` 0.0.6. Die versie plakt bij lange memovelden de tekst van volgende records aan een definitie vast, door een fout in de afkapping van overflowrecords. `inventaris_eap.py` vervangt die functie. Test na een upgrade van `access-parser` opnieuw tegen een XMI-export.

- **EA-boundaries** staan als naamloze `uml:Class` in de XMI en worden genegeerd.
- **Externe superklassen** (CityGML) staan niet in de XMI. Hun namen komen uit de EA-connectoren. Een externe superklasse met dezelfde naam als een modelklasse (CityFurniture) wordt die modelklasse.
- **Definities met dubbel geëscapete entiteiten** (`&amp;ndash;`) worden twee keer ontsleuteld.
- **Harmonisatierelaties naar externe kaders** geven in een kale SHACL-run violations. Valideer daarom met context. Er komen geen kopieën van externe begrippen in het kader.
- **Matchtypen** zijn een inhoudelijk oordeel. Laat ze door een domeinexpert bevestigen, vooral `exactMatch`.
