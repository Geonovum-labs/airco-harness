# Test set dsfl

Questions for the Dataspace Fysieke Leefomgeving, as a citizen asks them about the environment: in plain words, without knowing which registration holds the answer. The five samples are the questions of scenario 1, "Look back at my surroundings", from the deck "Use case questions" of the use case group (14 October 2026). All of them need the BAG.

| Sample | Question | Rule |
| --- | --- | --- |
| `dsfl-01` | In which decade were most of the buildings in Amersfoort built? | `fields` |
| `dsfl-02` | In which part of Amersfoort is the most construction currently taking place? | `fields` |
| `dsfl-03` | Which buildings in Amersfoort were demolished in the last 10 years, on the map | `map` |
| `dsfl-04` | Where are the sports halls in Amersfoort, on the map | `map` |
| `dsfl-05` | Which houses in Amersfoort were built before 1800, on the map | `map` |

The deck leaves the place open ("the city I live in", "the municipality") or names Vlaardingen. Every sample uses Amersfoort, so one municipality answers all five. The deck wording of each question is in the `note` of its `expected.json`, with the choices the sample makes where the question is open: a definition of "building", "construction" or "house", and a time window fixed at 12 November 2026.

The samples have `status: draft`; the working group has to approve each definition. The expected answers come from the BAG 2.0 Extract of 8 October 2026, retrieved on 12 November 2026 through bag.ldproxy.net, which republishes the extract with its history. The PDOK WFS holds no demolished panden, so it cannot answer `dsfl-03`. `dsfl-04` uses the PDOK WFS. The files are in `sources/dsfl/` and recorded in `sources/sources.lock.json`; `tests/test_dsfl_sources.py` derives every expected answer from them again.

`dsfl-03`, `dsfl-04` and `dsfl-05` are scored with the rule `map` against a BAG extract in `sources/dsfl/`. The samples name no defect, because the defects G1 to G13 belong to the IMGeo test set note. The version is in `testset.json`.
