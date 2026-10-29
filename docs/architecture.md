# Architecture of the harness

The harness has to answer one question. Does a different publication form of a standard help an agent more than the current publication? A measurement answers it only if everything except the publication form stays the same, and only if someone else can check it. Those two requirements explain most of the choices below. For now the harness measures the baseline: how agents do with the standard as it is published today.

## Three parts of the repo

**Data.** The source files are in `sources/`, the reference models in `reference-models/`, and the test sets in `testsets/`. Each of these has a folder per standard or, for test sets, per test set. All of it is in git, with a checksum per file. Names, values and text from BGT and IMGeo stay in Dutch, as the standard defines them. Everything the harness adds is in English.

**Core.** `validators/` holds everything that sets a score: the scoring rules, the code that builds and reads the reference model, and the code that fetches sources. No file in it imports Inspect.

**Inspect-specific code.** `src/airco_harness/` turns the core into a measurement in Inspect. It has the task, the agents, the thin scorers around the rules, the matrix, the report, the rescoring, the log check and the site.

The split comes from the tooling note. Inspect depends on one maintainer and changes fast. If Inspect turns out to be the wrong choice, the core moves to another harness. That move means redoing the task, the agents and the logs, but not the test set or the rules.

## The path of a run

1. `airco()` in `src/airco_harness/tasks.py` builds the task for one test set, one variant and one agent. It loads the samples and writes the test set, the variant and the agent to the task metadata.
2. For each sample, Inspect starts the agent with the question as the user message. The agent `model` is `react()` without a system prompt, without tools and without a submit tool, so the model answers and is done. The agent `inspect` is `react()` as Inspect ships it, with Inspect's `web_search()` and the harness's `fetch`. The agent `claude-code` is Claude Code in a Docker sandbox, with its own prompt and tools; its model calls go through Inspect.
3. The last assistant message is the answer. The scorer `quality` applies the rule from `expected.json`, and the scorer `source` classifies the URLs of the tool calls in the conversation against the allowlist.
4. Inspect writes the log. `airco-report` reads the logs through `inspect_ai.analysis`, `airco-rescore` rescores the runs, `airco-logcheck` checks the logs before publication, and `airco-pages` builds the site.

## The variants and the agents

A variant is a form in which the standard is published. Which forms there will be, and how many, is for the assessment framework to define. For now there is one variant, 0: the standard as it is published today, and the agent finds it or not.

What differs is the agent, because the baseline is what a user gets from the agent the user has:

| Agent | What answers | Setup |
| --- | --- | --- |
| `model` | The model alone. No system prompt, no tools. The floor: what the model knows from its training | 1 |
| `inspect` | Inspect's own agent, with Inspect's prompt, web search and fetch. The same loop for every model, so a model that Claude Code is not built for still gets a fair agent | 1 |
| `claude-code` | Claude Code, with its own system prompt and tools, so it can search the web and read the catalog as it would for a user. Anthropic models only, because it is built for them | 2 |

Earlier versions of the harness had more: variant 0a, where the harness handed the agent the URLs of the catalogs and a `fetch` tool with a recording for repeat runs, and two trial forms (the catalogs as markdown per chapter, and the MIM model as MIM-XML and SKOS). They were taken out on 20 October 2026, because the forms are not defined yet and handing the URLs is already an intervention. They are archived in the project's working notes, outside this repo.

## Why the harness has no system prompt of its own

An agent depends as much on its agent harness as on its model. With the same model, a different system prompt, different tools or different context management gives a different result. A system prompt written by the harness would therefore be a third thing under test, next to the model and the publication. The agent `model` has none, and Inspect's own default additions to the prompt of `react()` are switched off for it, so the conversation is the question and the answer. The agent `inspect` has Inspect's prompt, unchanged, as the one neutral reference that every model gets alike; it stands for no user. Claude Code brings its own prompt, and that prompt is part of what is measured, because it is what a user has.

## Why sources are in git

A third party has to get the same score, even if the source changes in the meantime. For the 2020 catalogs, the server of docs.geostandaarden.nl reports a modification date of 16 October 2026, so the files change even when the standard does not. The repo therefore holds the source files the reference model is built from, each with a checksum. The MIM XSD and the schemas it imports are in the repo too, so validation needs no network. `airco-sources` fetches them and records origin and sha256 in `sources/sources.lock.json`; `airco-sources --check` verifies the files on disk.

This costs space in the repo and leaves a license question open, because the Geonovum repos that the files come from have no license file. The cost is worth paying. Without vendored sources, nobody can check whether a later rescore used the same reference model.

What an agent read on the web is in the log, as the content of its tool calls, so rescoring sees what the agent saw. A repeat run sees the live web, which may have changed; that is accepted, because models are not deterministic either.

## Why answers are JSON

A free-text answer needs a model grader, and a model grader can be influenced. So the samples ask for a JSON answer with fixed keys and a schema per question. `correct` is then a comparison and not a judgment, and rescoring always gives the same result.

That has a price. The question reads less like a user's question, and a model that misses the format gets `parseable` 0 instead of a score for its content. For a proof of concept that has to show repeatability, determinism weighs more. A model grader can come later, as a second metric for open explanations.

A question that asks to show something on the map is the exception: a citizen asks it as a citizen would, with no format. The agents `inspect` and `claude-code` then get the tool `show_on_map`, the map a chat app offers, and the answer is the GeoJSON of the last successful call. The rule `map` matches its places to the panden of a vendored BAG extract, so the score is still a comparison. Only a test set with such a question gets the tool, so the tools of the other test sets stay as they were.

## Why the sample is the unit

Epochs on the same sample are not new observations. They ask the same question again. So `airco-report` first averages each sample over its epochs, and then takes the mean and the standard error over the samples. At three epochs, a calculation over single runs would make the standard error smaller by a factor of about the square root of 3 (1.7), and differences would look stronger than they are.

A run that hits a limit gave no answer, so it counts as a wrong answer, with the scores Inspect gave it and 0 where it gave none. Leaving such runs out would flatter a model that loops instead of answering. A run that ends in an error is the harness or the connection failing, so it is counted separately and left out of the averages. The working group confirms this agreement before the baseline measurement.

## What a log records

Inspect writes one `.eval` file per task and model, with the conversation, every event and the scores. It also records the git commit of the checkout and whether the checkout had uncommitted changes, under `eval.revision`. Everything a run depends on is in git: the test set, the reference model, the agent code, the scorers and the sources. So the commit identifies all of it, and a run has to be made from a committed checkout. `airco-rescore` warns when the checkout is not at the commit of the run, or when the run or the checkout has uncommitted changes.

Besides that, `eval.metadata` holds the versions of `airco-harness` and `inspect-ai`, the setup (1 for the agents of the harness, 2 for Claude Code), the agent, the name and version of the test set, and the variant. For Claude Code, what it did outside the conversation, such as writing a file in its sandbox, is not in the log.

## What the harness does not do yet

The harness covers one standard. A second standard needs its sources in `SOURCES` in `validators/sources.py`, a section in `testsets/sources-allowlist.json`, a reference model, and changes where the code assumes IMGeo: `validators/refmodel.py` reads the IMGeo MIM model and the BGT and IMGeo catalogs, and `rules.refmodel()` loads the IMGeo reference model. A standard without a MIM model, such as NL-SBB, needs another source of known terms.

Other variants come once the assessment framework defines them. A new variant is a name in `VARIANTS` in `tasks.py`, a publication form the agent can reach, and tests. Inspect's `skill()` writes to a sandbox and crashes without one; an MCP server can be passed to an agent as a tool.

No model grader is enabled yet. Setup 3 (IDE and chat assistants) is not in the harness; other CLI agents than Claude Code are not either, although Inspect SWE offers Codex CLI and Gemini CLI the same way.
