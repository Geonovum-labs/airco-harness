# Test set dsfl

Questions for the Dataspace Fysieke Leefomgeving, as a citizen asks them about the environment: in plain words, without knowing which registration holds the answer. `dsfl-01` to `dsfl-05` are the questions of scenario 1, "Look back at my surroundings", from the deck "Use case questions" of the use case group (14 October 2026). All of them need the BAG. `dsfl-06` and `dsfl-07` are groundwater questions.

| Sample | Question | Rule |
| --- | --- | --- |
| `dsfl-01` | In which decade were most of the buildings in Amersfoort built? | `fields` |
| `dsfl-02` | In which part of Amersfoort is the most construction currently taking place? | `fields` |
| `dsfl-03` | Which buildings in Amersfoort were demolished in the last 10 years, on the map | `map` |
| `dsfl-04` | Where are the sports halls in Amersfoort, on the map | `map` |
| `dsfl-05` | Which houses in Amersfoort were built before 1800, on the map | `map` |
| `dsfl-06` | Wat was de gemiddelde grondwaterstand op 21 september 2026 in meetbuis 1 van peilbuis GMW000000009441? | `fields` |
| `dsfl-07` | Which groundwater monitoring wells are within 500 meters of Stadhuisplein 1, on the map | `map` |

The deck leaves the place open ("the city I live in", "the municipality") or names Vlaardingen. Every sample uses Amersfoort, so one municipality answers all seven. The deck wording of each BAG question is in the `note` of its `expected.json`, with the choices the sample makes where the question is open: a definition of "building", "construction" or "house", and a time window fixed at 12 November 2026.

The samples have `status: draft`; the working group has to approve each definition. The BAG answers come from the BAG 2.0 Extract of 8 October 2026, retrieved on 12 November 2026 through bag.ldproxy.net, which republishes the extract with its history. The PDOK WFS holds no demolished panden, so it cannot answer `dsfl-03`. `dsfl-04` uses the PDOK WFS. The files are in `sources/dsfl/` and recorded in `sources/sources.lock.json`; `tests/test_dsfl_sources.py` derives every expected answer from them again.

The BRO questions are a first check that the mechanism works, using the public BRO services at publiek.broservices.nl. Their `note` carries an "Origin" line instead of the deck wording. `dsfl-06` and `dsfl-07` use BRO files in `sources/dsfl/`: the characteristics search of the wells within 1 km of Stadhuisplein 1, the wells of that search as a GeoJSON derived from it (the lock records it as `derived`), and the series of one tube. The values of `dsfl-06` are provisional and have to be checked again before approval.

`dsfl-03`, `dsfl-04` and `dsfl-05` are scored with the rule `map` against a BAG extract in `sources/dsfl/`, and `dsfl-07` against the wells as points. The samples name no defect, because the defects G1 to G13 belong to the IMGeo test set note. The version is in `testset.json`.
