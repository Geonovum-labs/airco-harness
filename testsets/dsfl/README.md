# Test set dsfl

Questions for the Dataspace Fysieke Leefomgeving, as a citizen asks them about the environment: in plain words, without knowing which registration holds the answer.

| Sample | Question | Sources |
| --- | --- | --- |
| `dsfl-01` | Building year, energy label and floor area of an office in Arnhem | BAG, EP-Online |
| `dsfl-02` | All buildings with a sports function in Arnhem, on the map | BAG |

The samples have `status: draft`. The expected answer of `dsfl-01` comes from the live registrations on the date in `expected.json`, so its values are checked again before approval. `dsfl-02` is scored with the rule `map` against a BAG extract in `sources/dsfl/`; which panden it requires is for the working group to approve. The samples name no defect, because the defects G1 to G13 belong to the IMGeo test set note. The version is in `testset.json`.
