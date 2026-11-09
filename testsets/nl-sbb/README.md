# Test set nl-sbb

Questions that ask an agent to describe the concepts of an information model following [NL-SBB](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/), the Dutch standard for describing concepts. The test set is the first that compares variant 0 with variant `skill`, in which Claude Code has the agent skill [geonovum-uml2-nl-sbb](https://github.com/fterpstra/skill-uml2-nl-sbb) in its project folder.

| Sample | Question | Input |
| --- | --- | --- |
| `nl-sbb-01` | Convert the UML model of IMGeo 2.2 to an NL-SBB concept scheme, validate it with SHACL, and report the counts | `IMGeo.xmi` in the working directory |

The sample gives the agent a file, so only the agent `claude-code` has its input; the agents `model` and `inspect` get the question without the file. A run takes up to an hour and several hundred messages, so `testset.json` sets higher limits per run than the default.

The expected counts come from the scripts of the skill, run without a model on the vendored XMI. Two answers are right, because the example the skill offers splits two values with different definitions per code list into fewer concepts than the script proposals do; see `expected.json`. The score checks the counts, not the concept scheme itself or the quality of the review; the log holds what the agent did.

The sample has `status: draft`. The version is in `testset.json`.
