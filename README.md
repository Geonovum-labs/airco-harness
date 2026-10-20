# Test Harness for AI Ready Standaarden

This project is the test harness for the [AI Ready Standaarden project](https://geonovum-labs.github.io/airco/). It measures whether agents do better with an AI-ready publication form of a standard than with the current publication.

## Usage

You need [uv](https://docs.astral.sh/uv/). Run everything from the repo root.

```bash
# 1. Install, check the source files, and run the tests. No keys needed.
uv sync --all-extras && uv run airco-sources --check && uv run pytest

# 2. One sample against one cheap model, to check the key and the logging
uv run inspect eval airco_harness/airco -T ids=imgeo-G04-03 -T cost_limit=0.05 --model anthropic/claude-haiku-5-5

# 3. Full matrix plus report; the matrix is named after its start time
uv run airco-matrix --models anthropic/claude-haiku-5-5,mistral/mistral-small-2603 --epochs 3
uv run airco-report logs/<start time> --out reports/<start time>

# 4. The same with all three agents: the model alone, Inspect's agent, and Claude Code in a Docker sandbox
uv run airco-matrix --models anthropic/claude-haiku-5-5 --agents model,inspect,claude-code --epochs 3
```

Steps 2 and 3 need keys in `.env`; the prices per model are in `model-costs.yaml`. `airco-matrix` first shows the number of runs and the maximum cost, and with paid models it starts only with `--yes`. Every command describes its options with `--help`; `[project.scripts]` in `pyproject.toml` lists the commands.

## Documentation

- [Getting started](docs/getting-started.md): a first measurement with a local model and no API keys, from installation to rescoring
- [Running the harness](docs/running.md): keys and prices, the agents, the matrix, the report, publishing, rescoring and repeating runs
- [Test sets and scoring](docs/test-sets.md): the sample format, the scoring rules, and how to add a sample or a test set
- [Reference model](docs/reference-model.md): how the MIM model of IMGeo becomes MIM-XML and SKOS
- [Architecture](docs/architecture.md): the parts, the path of a run, the variants, what a log records, and the design decisions
- [Contributing](CONTRIBUTING.md): working agreements for people who change the code

## Glossary

The terms come from the tooling note. The code and the documentation use them in this sense, without synonyms.

| Term | Meaning in this harness |
| --- | --- |
| Harness | The test harness: this repo, which runs the test set, scores it and logs it. The agent harness is the wrapper around the model |
| Setup | Setup 1 is the harness's own agent loop: the agent `model` or the agent `inspect`. Setup 2 is a real CLI agent, Claude Code. Setup 3 (an IDE or chat assistant) is not in the harness yet |
| Variant | A form in which the standard is published. The assessment framework defines the forms later; for now there is only variant 0, the standard as it is published today, which the agent finds or not |
| Agent | What answers the question: `model`, the model without prompt or tools; `inspect`, Inspect's own agent with web search and fetch (both setup 1); or `claude-code`, Claude Code with its own prompt and tools (setup 2) |
| Publication form | What the agent gets of the standard; on variant 0 nothing beyond what it finds itself |
| Test set | A folder under `testsets/` with samples for one purpose, such as `imgeo` |
| Sample | One test question with its expected outcome, a folder `testsets/<name>/samples/<id>/` |
| Run | One sample on one variant with one model, once |
| Epoch | One repetition of all runs |
| Scorer | The scoring function in Inspect: `quality` and `source` |
| Scoring rule | The rule a scorer applies to a sample; for now only `fields` |
| Metric | A measured value per run: five quality metrics, defined in [Test sets and scoring](docs/test-sets.md), and three trajectory metrics, listed in [Running the harness](docs/running.md) |
| Defect | A publication defect from the test set note, G1 to G13 |
| Vendored | Copied into the repo byte for byte, with origin and checksum, such as the source files in `sources/` |

## Layout

| Folder | Contents |
| --- | --- |
| `sources/` | Source files of the standards, with origin and checksum in `sources.lock.json` |
| `testsets/` | One folder per test set with `testset.json` and a folder per sample in `samples/`; the shared sample schema and the allowlist for `source` |
| `reference-models/` | One folder per standard with the reference model in MIM-XML and the codelists in SKOS |
| `validators/` | Everything that sets a score, without Inspect: scoring rules, reference model, sources |
| `src/airco_harness/` | The Inspect-specific code: task, tools, scorers, matrix, report, rescoring |
| `reports/` | One folder per measurement with the report and the log bundle, published at [geonovum-labs.github.io/airco-harness](https://geonovum-labs.github.io/airco-harness/) |
| `.github/` | The workflow that publishes the measurements to GitHub Pages |
| `tests/` | Tests, without API keys |
| `docs/` | Documentation |

## Background

The decisions come from four working notes by ModelDesk, dated 9 October 2026, in Dutch and not in this repo. They are the tooling note (requirements C1 to C12, acceptance conditions), the approach note (setups, sprint plan), the test set note (variants, task types, sample schema, defects), and the cost note (models, analysis plan).

## License

EUPL-1.2. See `LICENSE`.
