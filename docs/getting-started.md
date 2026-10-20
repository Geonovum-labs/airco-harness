# Getting started: a first measurement without API keys

In this tutorial we run one sample against a small model on your own machine. Then we look at what the agent did, make a report, and rescore the run. You need no API keys. Allow half an hour, most of it for downloads.

We use Qwen3 0.6B through Ollama. That model is too small to answer the questions well, so pay attention to the path through the harness rather than the score.

## What you need

- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com). On macOS, install it with `brew install ollama`.

## Install the harness

1. Clone the repo and go into its folder.

	```bash
	git clone https://github.com/Geonovum-labs/airco-harness.git
	cd airco-harness
	```

2. Install the dependencies.

	```bash
	uv sync --all-extras
	```

3. Check the vendored source files.

	```bash
	uv run airco-sources --check
	```

	The last line is `9 of 9 files ok`.

4. Run the tests.

	```bash
	uv run pytest -q
	```

	The last line shows the number of passed tests and no `failed` or `skipped`.

## Start the local model

1. Start Ollama in a second terminal and leave that terminal open.

	```bash
	ollama serve
	```

2. In your first terminal, pull the model.

	```bash
	ollama pull qwen3:0.6b
	```

3. Create `.env`. The example values already point to Ollama at `http://localhost:11434/v1`. The local model has a price of 0 in `model-costs.yaml`, which every task needs because it has a cost limit.

	```bash
	cp .env.example .env
	```

## Run a first measurement

We run sample `imgeo-G04-03` with the agent `model`: the model gets the question and nothing else, no system prompt and no tools, and answers from what it knows. The sample asks, in Dutch, which object type an open-air swimming pool is in the BGT.

```bash
uv run inspect eval airco_harness/airco -T ids=imgeo-G04-03 --model openai-api/local/qwen3:0.6b --log-dir logs/first-measurement
```

If the model cannot be reached, Inspect stops with a connection error and the address it tried; check that Ollama is still running. After half a minute you see the five quality metrics:

```text
correct         complete         invented         parseable
mean     0.000  mean      0.000  mean      2.000  mean       1.000
stderr   0.000  stderr    0.000  stderr    0.000
source
mean    0.000
stderr  0.000
```

Your result can differ, because a small model answers differently each time. In this run the model answered `{"objecttype": "none", "type": "geospatial object"}`. The answer has the requested format, so `parseable` is 1, but neither value exists in the BGT, so `invented` is 2. The agent `model` has no tools, so `source` is 0. The right answer is OverigBouwwerk of type bassin.

## Look at what the agent did

```bash
uv run inspect view --log-dir logs/first-measurement
```

Inspect opens a viewer at `http://127.0.0.1:7575`. Open the run and go to the Messages tab. You see the question as the only input, and the answer. With the agent `claude-code` you would also see Claude Code's system prompt and every tool call with its result. Below the scores, each score key shows the explanation from the scoring rule. To stop the viewer, press Ctrl+C.

## Make a report

```bash
uv run airco-report logs/first-measurement
```

You see `1 run; logs/first-measurement/report/report.md`. Open that file. It has the quality metrics per model and variant, the trajectory metrics, and, when a run hit a limit or ended in an error, a table with the reason. A run at a limit counts as a wrong answer; [Architecture](architecture.md) explains why, under "Why the sample is the unit".

## Rescore the run

```bash
uv run airco-rescore logs/first-measurement/*.eval --out rescore
```

You see a line that ends in `5 of 5 scores equal within 0.0`. That means the scorers in this checkout give the same scores as during the run. `airco-rescore` starts no model and needs no keys.

## What you have now

You installed and tested the harness, connected a model, made a run, looked at the trajectory, made a report, and rescored the run. Git ignores `logs/` and `rescore/`.

To use real models and run all variants, follow [Running the harness](running.md). To see how the harness works, read [Architecture](architecture.md).
