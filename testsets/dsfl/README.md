# Test set dsfl

Questions for the Dataspace Fysieke Leefomgeving, as a citizen asks them about the environment: in plain words, without knowing which registration holds the answer. `dsfl-01` to `dsfl-05` are the questions of scenario 1, "Look back at my surroundings", from the deck "Use case questions" of the use case group (14 October 2026). All of them need the BAG. `dsfl-06` to `dsfl-08` are groundwater questions. `dsfl-16` combines the BGT and GeoTOP per buurt; see [Water accumulation per buurt](#water-accumulation-per-buurt).

| Sample | Question | Rule |
| --- | --- | --- |
| `dsfl-01` | In which decade were most of the buildings in Amersfoort built? | `fields` |
| `dsfl-02` | In which part of Amersfoort is the most construction currently taking place? | `fields` |
| `dsfl-03` | Which buildings in Amersfoort were demolished in the last 10 years, on the map | `map` |
| `dsfl-04` | Where are the sports halls in Amersfoort, on the map | `map` |
| `dsfl-05` | Which houses in Amersfoort were built before 1800, on the map | `map` |
| `dsfl-06` | Wat was de gemiddelde grondwaterstand op 21 september 2026 in meetbuis 1 van peilbuis GMW000000009441? | `fields` |
| `dsfl-07` | Which groundwater monitoring wells are within 500 meters of Stadhuisplein 1, on the map | `map` |
| `dsfl-08` | Maak een grafiek van de dagelijkse gemiddelde grondwaterstand in meetbuis 1 van GMW000000009441 van 10 tot en met 20 januari 2023 | `series` |
| `dsfl-09` | Surface elevation and upper GeoTOP units | `fields` |
| `dsfl-10` | Most probable lithoclass in a GeoTOP voxel | `fields` |
| `dsfl-11` | Eem formation in REGIS | `fields` |
| `dsfl-12` | Lithoclass probabilities absent from REGIS | `fields` |
| `dsfl-13` | GeoTOP cross-section picture | `section` |
| `dsfl-14` | GeoTOP vertical column for an Appelboor | `trace` |
| `dsfl-15` | Limits of line-of-sight evidence for confinement | `fields` |
| `dsfl-16` | Buurten most sensitive to water accumulation | `ranking` |
| `dsfl-17` | Welke BGT objecten kunnen verhard zijn? | `fields` with a list |
| `dsfl-18` | Welke soorten verharding in de BGT beinvloeden wateraccumulatie? | `fields` with a list |
| `dsfl-19` | Hoe bepaal ik met de BGT de oppervlakte van de fysieke objecten die relevant zijn voor wateraccumulatie? | `fields` with a list |

The deck leaves the place open ("the city I live in", "the municipality") or names Vlaardingen. Every sample uses Amersfoort. The deck wording of each BAG question is in the `note` of its `expected.json`, with the choices the sample makes where the question is open: a definition of "building", "construction" or "house", and a time window fixed at 12 November 2026.

The samples have `status: draft`; the working group has to approve each definition. The BAG answers come from the BAG 2.0 Extract of 8 October 2026, retrieved on 12 November 2026 through bag.ldproxy.net, which republishes the extract with its history. The PDOK WFS holds no demolished panden, so it cannot answer `dsfl-03`. `dsfl-04` uses the PDOK WFS. The files are in `sources/dsfl/` and recorded in `sources/sources.lock.json`; `tests/test_dsfl_sources.py` derives every expected answer from them again.

The BRO questions are a first check that the mechanism works, using the public BRO services at publiek.broservices.nl. Their `note` carries an "Origin" line instead of the deck wording. The BRO files in `sources/dsfl/` include the characteristics search of the wells within 1 km of Stadhuisplein 1, the wells of that search as a GeoJSON derived from it (the lock records it as `derived`), and the series of one tube. The values of `dsfl-06` and `dsfl-08` are provisional and have to be checked again before approval.

`dsfl-03`, `dsfl-04` and `dsfl-05` are scored with the rule `map` against a BAG extract in `sources/dsfl/`, and `dsfl-07` against the wells as points. The samples name no defect, because the defects G1 to G13 belong to the IMGeo test set note. The version is in `testset.json`.

## Paving in the BGT

`dsfl-17` to `dsfl-19`, tagged `verharding`, ask what the BGT says about paving, naming the BGT but no dataset or place: which object types can be paved, which kinds of paving affect water accumulation, and how to get the area of the relevant objects. They are made to compare an agent without skills with the same agent with the metadata skill and the MIM skill together (variant `skill-metadata+skill-mim`); the first is the example question of the metadata skill. Each asks its question alone and the JSON format afterwards (`format` in `sample.json`), because the format line in the question made Claude Code answer from memory without loading a skill. The format request refers only to the agent's own words, and the object types or kinds of paving in the JSON must be named in its answer before that request (`grounded_fields`). Their standard is `imgeo-2.2`, so the IMGeo and BGT catalogs count as a source. The expected answers come from the IMGeo 2.2 reference model, and `tests/test_dsfl_sources.py` derives them again; the choices below are a draft of 20 November 2026 for the working group.

- **Can be paved.** The object types whose `bgt-fysiekVoorkomen` can be gesloten verharding, open verharding or half verhard: Wegdeel, OndersteunendWegdeel and OnbegroeidTerreindeel.
- **Affects water accumulation.** Gesloten verharding, open verharding and half verhard. A finer IMGeo plus value under one of them, such as asfalt or tegels, is allowed; onverhard is wrong. That a kind of paving affects water accumulation is a hydrological judgment, which the BGT does not record.
- **Area.** The object types of `dsfl-17` and Pand, whose roof is paved surface as `dsfl-16` counts it, selected on `fysiekVoorkomen`, with the area from the geometry: no object type has an area attribute.

## Subsurface models

`dsfl-09` to `dsfl-15` are seven draft questions about GeoTOP and REGIS at RD (155000, 463000). Their local reference bundle is version `2026-11`; its manifest SHA-256 and model identifiers are in `testset.json`. The bundle is distributed separately and is not included in this repository. A manifest hash identifies the manifest; verifying the files themselves requires checking their checksums against it.

The cross-section is scored from the successful `section-plot` call and its JSON and PNG result, not by inspecting the picture. That tool produces a complete plot and has no pagination; `section` is a different, paginated data tool. The vertical-column question scores a `trace` result, not an Appelboor drawing, because the server does not draw one. The scores check selected properties, not all cells or the geological interpretation.

The harness connects the subsurface server only in variant `mcp-bgt-wijkenbuurten-subsurface`, for `dsfl-16`. It does not attribute the server's calls as an authoritative source or report response-size metrics. The reference values and the server's behavior need review before approving the samples. The current image (revision `cb6b5d6`, version `1.0.13`) takes a WGS84 point and puts the column under `result`, unlike the trace these samples were written for; at RD (155000, 463000) it gives a surface of 3.80 m NAP where `dsfl-09` expects 4.37.

### Selecting questions with tags

Use `--testset dsfl --tags bag,groundwater` with `airco-matrix` to run the existing eight questions without the subsurface drafts. Use `--tags subsurface` to select the eight subsurface questions, `dsfl-09` to `dsfl-16`. Tags select any matching sample: `bro` includes both groundwater and subsurface questions. A DSFL run without a tag or id filter includes all nineteen samples.

The groundwater MCP variant defaults to the `groundwater` tag, so it still selects only `dsfl-06` to `dsfl-08`. Variant `mcp-bgt-wijkenbuurten-subsurface` selects `dsfl-16` by its tag `bgt` and gives it the BGT, the CBS buurten and the subsurface server; [Running](../../docs/running.md) says how to start that server. No variant serves `dsfl-09` to `dsfl-15` yet. Tags select questions; they do not launch a server. The tool-dependent subsurface samples cannot pass without their server; the `fields` samples can still be parseable without tools.

## Water accumulation per buurt

`dsfl-16` asks which CBS buurten in Amersfoort have the largest paved share, and how far the lithology of the upper 5 m in GeoTOP adds to their sensitivity to water accumulation after heavy rain. The agent ranks the buurten by paved share and gives for the top three the paved share, the share of GeoTOP voxels with P(klei) > 5% and a score. The question says to use the geometry of the CBS buurten and to count only open and closed paving. It does not define the score, so the score is not checked. It is scored with the rule `ranking` ([Test sets and scoring](../../docs/test-sets.md#the-rule-ranking)). The readings below are a draft of 20 November 2026 for the working group:

- **Buurt.** The CBS Wijk- en Buurtkaart 2026, as bag.ldproxy.net/wijkenbuurten serves it: 145 buurten in Amersfoort.
- **Paved share.** The area of current BGT panden and of wegdelen with gesloten or open verharding at ground level, clipped to the buurt by the `clip` of the aggregation process of bag.ldproxy.net/bgt, over the area of the buurt. Half verhard, such as the track bed of the Spooremplacement, does not count.
- **Clay share.** Of each GeoTOP v01r6s1 column whose 100 m cell centre lies in the buurt, the upper 10 voxels (5 m from the top of the column); the share of those voxels with kans op klei (lithoclass K) above 5%. Kleiig zand (KZ) does not count.

| Rank | Buurt | Paved | Clay |
| --- | --- | --- | --- |
| 1 | Hof | 0.762 | 0 |
| 2 | Winkelcentrum Vathorst | 0.712 | 0 |
| 3 | Smallepad e.o. | 0.710 | 0 |
| 4 | Stadhuisplein | 0.706 | 0 |

Winkelcentrum Vathorst and Smallepad e.o. lie within 0.002 of each other, so ranks 2 and 3 accept both in either order. Three runs on 20 November that clipped the same way found these three in this order. The server fails on the clipped wegdelen of Watervogelbuurt (HTTP 500); its panden alone give 0.189 and its wegdelen unclipped 0.429, far below the top three. None of the most paved buurten has a voxel with P(klei) > 5%, with 10 voxels or 9, so the lithology does not add to their sensitivity. Clay above 5% occurs in 68 of the 145 buurten; Isselt-Oost has the largest share.

Since version 1.0.13 the subsurface MCP has the tool `area-summary`, which gives the share of voxels above a probability in a polygon and a depth band in one call. Before it the server answered per point or line only: a buurt of 50 columns took 50 traces, Amersfoort about 6,400. The expected clay shares come from the OPeNDAP server at dinodata.nl, which serves the same GeoTOP version: at the centroids of Isselt-Oost, Schuilenburg-Zuid, De Baken and Laakse Tuinen its kans_2 equals the server's P(K) in each of the upper 10 voxels.

The buurten (in RD and in WGS84), the clipped BGT areas per buurt and the clay probabilities of the upper 12 voxels of each column are in `sources/dsfl/` and recorded in `sources/sources.lock.json`; the GeoTOP block (25 MB) is reduced at fetch time and not kept. `tests/test_dsfl_sources.py` derives the ranking and the values again.
