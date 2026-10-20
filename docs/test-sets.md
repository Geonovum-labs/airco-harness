# Test sets and scoring

A test set is a folder under `testsets/` with questions for one purpose. Each question is a sample with an expected outcome, and a scoring rule compares the agent's answer with it. This page describes the format, the rules, and how to add a sample or a test set.

## Format

| File | Content |
| --- | --- |
| `testsets/<name>/testset.json` | `purpose`, `version` and `date` of the test set |
| `testsets/<name>/samples/<id>/sample.json` | The question and its metadata, following `testsets/sample.schema.json`. The folder name is the sample id |
| `testsets/<name>/samples/<id>/expected.json` | The scoring rule and the expected outcome |
| `testsets/<name>/samples/<id>/answer.schema.json` | For a JSON answer, the JSON Schema (draft 2020-12) of the answer |
| `testsets/sample.schema.json` | JSON Schema of a sample, shared by all test sets |
| `testsets/sources-allowlist.json` | Per standard, which fetched URLs count as an authoritative source |

The sample id is `<name>-G<nn>-<nn>`, where `<name>` is the short name of the standard, such as `imgeo-G04-03`. `sample.json` has these fields:

| Field | Content |
| --- | --- |
| `defect` | `G1` to `G13`, a publication defect from the test set note |
| `task` | Task type, one of the values in `sample.schema.json`, such as `lookup` or `classify` |
| `standard` | Standard with version, such as `imgeo-2.2`. The allowlist for `source` uses the same name |
| `input` | The question to the agent, with the requested answer format. It may be in Dutch, and then so are the answer keys |
| `metadata.status` | `draft`, `approved` or `withdrawn` |
| `metadata.hypothesis` | Why the question may fail |
| `metadata.expected_variant` | The hypothesis of the test set note: the lowest variant on which the question is expected to pass. Which variants there will be is not defined yet; 0 is the standard as published today |
| `metadata.location` | Where the answer is found |
| `metadata.absence` | `true` if the right answer is that something does not exist |
| `metadata.also_defect`, `metadata.exploration_question` | Optional. A second defect the question touches, and the exploration question it comes from |

`expected.json` always has `rule`, the name of the scoring rule, and may have `answer_schema` (the file name of the answer schema), `source` (where the expected answer comes from) and `note` (for the reviewer). The other keys depend on the rule.

Choose a test set with `-T testset=<name>` or `airco-matrix --testset <name>`; the default is `imgeo`. Each run records the name and version of its test set, and the git commit of the checkout.

## Scoring

For each sample, the scorer `quality` applies the scoring rule from `expected.json` and fills `correct`, `complete`, `invented` and `parseable`. The scorer `source` fills `source` from the tool calls. Both are in `validators/` and run without Inspect, so rescoring needs no model.

| Key | Meaning |
| --- | --- |
| `correct` | The answer is right and invents nothing |
| `complete` | The share of the expected content that the answer contains |
| `invented` | The number of names or values in the answer that do not exist |
| `parseable` | The answer can be read in the requested format |
| `source` | The agent used an authoritative source |

**Reading the answer.** A rule takes the first JSON code block in the answer, otherwise the first code block, otherwise the whole text, and then the text from the first `{` or `[` to the last `}` or `]`. `parseable` is 1 if that is valid JSON that conforms to `answer.schema.json`. Otherwise all four keys are 0 and scoring stops. A bad answer never makes a rule raise an error.

**Comparing.** Text compares after normalization: Unicode NFKC, every dash as `-`, single spaces, lower case. Numbers compare as numbers and booleans as booleans.

**Known terms.** A term is known if the reference model has it as the name of an object type, data type, attribute, type of an attribute, domain list or domain value, or if a published catalog lists it as a domain value. A namespace prefix such as `tra:` does not count.

### The rule `fields`

Each field of the answer has an expected value.

| `expected.json` | Content |
| --- | --- |
| `expected` | For each field, a value, or `{"one_of": [...]}` for alternatives |
| `term_fields` | Optional. Fields in which a value that differs from the expected one must be a known term |

`complete` is the share of fields that match. `invented` is the number of differing values in `term_fields` that are not a known term, and `correct` is 1 only if everything matches and nothing is invented.

For example, `imgeo-G04-03` expects `objecttype` OverigBouwwerk (or Overig bouwwerk) and `type` bassin. The answer Waterdeel with zwembad gets `complete` 0 and `invented` 1: Waterdeel is a known term, zwembad is not.

### The scorer `source`

`source` is 1 if at least one successful retrieval (status 200 to 299) is authoritative and none is non-authoritative. A retrieval is a tool use in the conversation with a `url` argument: the `fetch` tool of the agent `inspect`, Claude Code's WebFetch, or a web fetch that the model's provider runs on its own servers, which Inspect keeps as a content block of the assistant message. It counts as successful when the tool answered without an error. A search, such as WebSearch or a provider's web search, is not a retrieval: an agent that answers from search results alone gets 0, and so does the agent `model`, which has no tools. Whether a search result should count as a source is for the working group to settle. A URL is `non_authoritative` if it matches a pattern in that list of the allowlist, otherwise `authoritative` if it matches that list, otherwise `other`, which does not count.

## Add a sample

Every new sample gets `status: draft` until the reviewer of the standard approves it. The example adds `imgeo-G04-04` to the test set `imgeo`.

1. Choose the defect and the task type, and a scoring rule. Where you can, ask for a JSON answer with fixed keys, so the score stays deterministic. Derive the expected answer from the vendored sources in `sources/`, not from the live publication, and write down where you found it.

2. Create `testsets/imgeo/samples/imgeo-G04-04/` with `sample.json`:

	```json
	{"defect": "G4", "task": "classify", "standard": "imgeo-2.2", "input": "... Antwoord met alleen een JSON-object met de sleutels \"objecttype\" en \"aantal\".", "metadata": {"status": "draft", "hypothesis": "...", "expected_variant": 4, "location": "BGT catalog 10.1.3", "absence": false}}
	```

3. Write `expected.json` in the same folder, and `answer.schema.json` for a JSON answer:

	```json
	{"rule": "fields", "expected": {"objecttype": "Wegdeel", "aantal": 1}, "term_fields": ["objecttype"], "answer_schema": "answer.schema.json", "source": "BGT catalog 10.1.3"}
	```

4. Prove the scorer before you score a model. Add a known good answer to `CASES` in `tests/test_rules.py` with `full()` as the expected score, and at least one wrong answer that looks like a mistake an agent could make, with the score it must get. Then run the tests.

	```bash
	uv run pytest -q tests/test_testset.py tests/test_rules.py
	```

	`test_every_sample_has_a_known_good_answer` fails until every sample has a good answer that scores `full()`.

5. Run the sample once on the two development models, on every variant, to see that an agent can answer it and that the scorer reads the answer. This costs a few cents.

	```bash
	uv run airco-matrix --models anthropic/claude-haiku-5-5,mistral/mistral-small-2603 --ids <sample-id> --epochs 1 --name smoke-<sample-id> --yes
	uv run airco-report logs/smoke-<sample-id>
	```

	A sample that every model answers correctly on every variant does not separate the variants. Keep it only if it covers a defect no other sample covers.

6. If needed, raise the version in `testset.json` and update the test set's `README.md`.

## Add a test set

Make a new test set when questions serve another purpose than an existing set, such as a regression set or the questions for CompliancePush.

1. Create `testsets/<name>/samples/` and write `testsets/<name>/testset.json`:

	```json
	{"purpose": "...", "version": "0.1", "date": "2026-11-02"}
	```

2. Add samples as above. To reuse a sample of another test set, copy its folder. Every sample names its standard; for now that must be `imgeo-2.2`, because the publication forms and the reference model exist only for IMGeo. [Architecture](architecture.md) lists what another standard needs.

3. Run the tests and then the test set with `-T testset=<name>` or `--testset <name>`.
