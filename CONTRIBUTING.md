# Contributing to airco-harness

These agreements apply to everyone who changes code, data, or documentation. How the harness fits together is in [Architecture](docs/architecture.md).

## Language

Write code, documentation, and data in American English. Code includes the names of modules, functions, variables, and tests, the comments and docstrings, and the help texts of commands. Documentation is everything under `docs/`, the READMEs, and this file. Data includes the keys, prompts, and the report. A test question may be in Dutch, and then so are the answer keys it asks for. Commit messages are the exception: they stay in Dutch for now (see "Before a commit").

The content of BGT and IMGeo stays in Dutch, as the authentic model defines it, because the harness cannot change it. That covers the names of object types, attributes and domain lists, the domain values, the definitions, the catalog text, the MIM model, the concept register and the XML element names. It also covers the names that point at that content: answer keys such as `bgt-status`, and the file names of the vendored sources and of the catalog chapters. For example, sample `imgeo-G04-03` asks in Dutch which object type an open-air swimming pool is, with the answer keys `objecttype` (the MIM term) and `type`, and the expected answer `OverigBouwwerk` with `bassin`.

Use the glossary terms from the README, without synonyms. Do not use em dashes, en dashes, or curly quotes in text or code.

## Where code belongs

Put everything that sets a score in `validators/`. Code there never imports `inspect_ai`, and a test in `tests/test_rules.py` checks that. Put the tasks, tools, scorers, and commands that use or drive Inspect in `src/airco_harness/`.

Give a new command a function that builds its argument parser (usually `build_parser()`) and a line under `[project.scripts]` in `pyproject.toml`.

## Generated files

Do not edit these files by hand. Run the command next to each file and commit the result. A test fails when a file no longer matches its source or the code.

| File | Command |
| --- | --- |
| `sources/sources.lock.json` and `sources/` | `uv run airco-sources` |
| `reference-models/` | `uv run airco-refmodel` |

## Tests

```bash
uv run pytest -q
```

The suite needs no API keys, no network access and no Docker. Only a run with the agent `claude-code` needs Docker, and that is never part of the tests.

For a new sample, add a known good answer and at least one wrong answer to `tests/test_rules.py`, as [Test sets and scoring](docs/test-sets.md) describes. For a new rule or tool, add a test that checks its behavior against a literal expected outcome.

## Before a commit

1. Lint and format the code, then run the tests. The settings for ruff are in `pyproject.toml`.

	```bash
	uv run ruff check --fix src validators tests && uv run ruff format src validators tests
	uv run pytest -q
	```

2. Check the logs that you commit.

	```bash
	uv run airco-logcheck reports
	```

	Commit a log bundle only for a measurement the working group agreed on, or for a calibration run the docs refer to. A try-out stays in `logs/`, which git ignores: a bundle is 10 MB or more, and the repo is public.

3. Write the commit message in Dutch, with a short first line and below it what changes and why.

Commit locally, and push only after the project lead agrees. Treat every commit as public, because the repo is meant to be public from its first commit.

## Secrets and personal data

Put keys only in `.env`, which `.gitignore` lists. `model-costs.yaml` holds public list prices with their source and date, and is committed; budget figures of the project stay out of the repo. Use only public or synthetic test data. Run `airco-logcheck` on logs before you publish them.
