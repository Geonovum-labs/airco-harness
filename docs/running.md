# Running the harness

How to connect a model, choose the agent, run the matrix, publish a log bundle, and rescore or repeat runs. [Getting started](getting-started.md) walks through one run with a local model first.

## Connect a model

A model needs a key in `.env`, which `.gitignore` lists, and a price in `model-costs.yaml`, which is committed. Choose the model for each run with `--model <provider>/<model>`, with a provider name from Inspect.

1. Put the key in `.env`.

	| Provider | Variable in `.env` | Example for `--model` |
	| --- | --- | --- |
	| Anthropic | `ANTHROPIC_API_KEY` | `anthropic/claude-haiku-5-5` |
	| OpenAI | `OPENAI_API_KEY` | `openai/gpt-6-luna` |
	| Google | `GOOGLE_API_KEY` | `google/gemini-3.8-flash` |
	| Mistral | `MISTRAL_API_KEY` | `mistral/mistral-small-2603` |
	| OpenAI-compatible endpoint, such as vLLM at Kadaster | `KADASTER_BASE_URL`, `KADASTER_API_KEY` | `openai-api/kadaster/<model-name>` |
	| Local Ollama | `LOCAL_BASE_URL`, `LOCAL_API_KEY` | `openai-api/local/<model-name>` |

	For `openai-api/<service>/...`, Inspect reads `<SERVICE>_BASE_URL` and `<SERVICE>_API_KEY`, with the service name in capital letters. If the endpoint needs no key, set any value, because Inspect refuses to start without one.

2. Check that `model-costs.yaml` has the model with its current list price, in dollars per million tokens; the header names the sources and the date the prices were read. Without a price, a task with `cost_limit` refuses to start with `cost_limit requires cost data for all models`, and the report cannot compute the cost per correct answer. For a local model or your own GPU, set 0 or an agreed rate. Commit a price change before the run, so that the log's commit holds the prices it was costed with.

	Inspect knows one price per model. For a model that charges more above a prompt length, enter the higher price: the cost limit then never stops a run too late, and the reported cost of that model is an upper bound.

3. Run one sample with a low cost limit, to check the key, the endpoint and the logging.

	```bash
	uv run inspect eval airco_harness/airco -T ids=imgeo-G04-03 -T cost_limit=0.05 --model anthropic/claude-haiku-5-5
	```

The harness uses no model grader. If you add one, give it a role with `required=True`, so that Inspect does not silently fall back to the model under test, and choose a model other than the one under test.

## Choose the agent

The harness measures the baseline: the question as a user asks it, to the agent as the user has it. Three agents answer it, chosen with `-T agent=` for a task or `--agents` for the matrix, which takes any of them.

| Agent | What it is | Setup |
| --- | --- | --- |
| `model` (default) | The model alone: no system prompt, no tools. It answers from what it knows, and its last message is the answer. The floor | 1 |
| `inspect` | Inspect's own `react()` agent, with Inspect's system prompt and submit tool, the `web_search()` tool of Inspect and a `fetch` tool of the harness. The same loop for every model, so models compare on equal terms | 1 |
| `claude-code` | Claude Code with its own system prompt and tools, in a Docker sandbox. It searches and reads the web as it would for a user | 2 |

`claude-code` runs on Anthropic models only. Through the bridge it can be served by another model, but Claude Code is built for Claude, and in the calibration runs Mistral Small 4 behind it never touched a tool, so such a run measures nothing; the matrix skips those pairs and says so. The different Claude models behind Claude Code are the comparison that makes sense there. `inspect` is the agent that puts every model on equal terms.

`inspect` searches with the search function of the model's own provider (Anthropic, OpenAI, Google and Mistral have one), so it needs no extra key. A model whose provider has none needs an external search provider and its key; see Inspect's documentation of `web_search()`.

`claude-code` needs Docker running on the machine. Inspect starts one container per sample from `src/airco_harness/sandbox/compose.yaml`, Inspect SWE installs Claude Code in it, and every model call Claude Code makes goes through Inspect, so the log holds the whole conversation including the pages Claude Code read, the limits apply, and the cost is logged. Two things in that setup are deliberate. The container has the network on, where Inspect's default sandbox has none, because Claude Code has to reach the web. And Claude Code's WebFetch preflight, a call to Anthropic that asks whether a domain is safe, is switched off in the sandbox's project settings, because behind the bridge that call cannot reach Anthropic and every WebFetch would fail; a user behind a proxy switches it off the same way. What Claude Code does outside the conversation, such as writing a file, is not in the log. The model under test is the eval model: Claude Code's requests for any Claude model are routed to it.

Claude Code sends a system prompt of tens of thousands of tokens per call, so a run costs more than with the agent `model`, and `message_limit` counts two messages per tool call. The defaults of 60 messages, 600,000 tokens, 900 seconds and $0.50 are a starting point; the report shows which limits a measurement hit.

## Run the matrix

The matrix runs a test set across variants, models and epochs with one agent, as one Inspect `eval_set`, and produces a log bundle. A matrix against paid models costs money, so run one only after the project lead approves it. During development, run Claude Haiku 5.5 and Mistral Small 4 only; the working group settles the models per measurement.

1. Show the number of runs and the maximum cost.

	```bash
	uv run airco-matrix --models anthropic/claude-haiku-5-5,mistral/mistral-small-2603 --epochs 3
	```

	With paid models, the command stops after these lines:

	```text
	1 samples x 2 agent-model pairs x 3 epochs = 6 runs (1 variants, 1 agents, 2 models)
	at most 6 x 0.50 = 3.00 dollars for paid models
	paid models anthropic/claude-haiku-5-5, mistral/mistral-small-2603: rerun with --yes to start
	```

	The matrix runs the test set `imgeo` unless you add `--testset <name>`. `--agents model,inspect,claude-code` runs all agents in one matrix, so that one bundle holds the whole measurement; `--variants`, `--ids` and `--cost-limit` narrow it down; `--help` lists all options.

2. Commit first, so that the log records a commit that holds everything the run used. Then start the matrix with the same command plus `--yes`. The matrix is named after its start time, such as `2026-10-19T21-06-14`, so that bundles sort by time; `--name` overrides that. The logs go to `logs/<name>/` and the log bundle to `reports/<name>/logs/`.

An `eval_set` resumes an interrupted matrix: run the same command again with `--name` set to the name of the interrupted one, and it skips the runs that finished. A matrix with other models, variants or samples needs its own name, because Inspect refuses a log folder with different task parameters (`PrerequisiteError`).

For a single task, use Inspect directly. Every task parameter is a `-T` option:

```bash
uv run inspect eval airco_harness/airco -T agent=claude-code -T ids=imgeo-G04-03 --model <model>
```

## Make the report and publish

```bash
uv run airco-report logs/<name> --out reports/<name>
uv run airco-logcheck reports/<name>
```

With `--out`, the report goes next to the bundle: `reports/<name>/report.md`, and `reports/<name>/runs.csv` with one line per run. Without `--out`, it goes to `logs/<name>/report/`, outside git.

The report averages each sample over its epochs first, then takes the mean and standard error over samples. A run that hit a limit counts with the scores it got, 0 where it got none, because the agent did not answer. A run that ended in an error is left out of the averages, because the harness failed. Both kinds are listed under "Runs with an error or at a limit" with their reason.

`runs.csv` has these columns, in this order:

| Column | Content |
| --- | --- |
| `model`, `variant`, `sample`, `epoch` | The run |
| `task`, `defect` | From the sample |
| `failed`, `limit`, `reason` | `failed` is `True` for a run with an error; `limit` names the limit a run hit; `reason` holds either |
| `tool_calls` | Tool uses in the conversation, as the `source` scorer counted them: the agent's own tool calls and the tools the model's provider ran on its servers, such as a web search |
| `tokens`, `tokens_input`, `tokens_output`, `tokens_cache_read`, `tokens_cache_write`, `tokens_reasoning` | Token counts |
| `total_time_s`, `working_time_s` | Time in seconds, the second without waiting for a provider limit |
| `cost` | Dollars, as Inspect logged them from the prices in `model-costs.yaml`; empty for a model without a price |
| `retrieved` | The URLs the agent retrieved with success, each with its class for `source`, joined with `; ` |
| `hosts` | The hosts of those URLs, each once with its class, joined with `, ` |
| `rule` | The scoring rule of the sample, such as `fields` or `map` |
| `explanation` | What the rule found, such as the wrong fields or how many required panden the map shows |
| `correct`, `complete`, `invented`, `parseable`, `source` | The quality metrics |

For a test set with a map question, `airco-report` also writes `maps.json`: per run of that question, which panden of the BAG extract the map showed, which required panden it missed, and the places on no pand, with the expected outcome of the sample.

`airco-logcheck` searches the logs for keys, e-mail addresses and home directories. If it finds something, it exits with code 1: publish nothing and find the cause. An email address that an agent read on a web page, such as the contact address of a sports club, is not a leak of ours but still personal data: `airco-logcheck --mask-emails reports/<name>` replaces each one with `[email removed]` in the logs and then scans again. The scores do not change; `airco-rescore` confirms that. Then commit `reports/<name>/`. Keep `logs/` out of git; the bundle holds the same `.eval` files, and `.gitignore` leaves out the viewer files of the bundle.

**GitHub Pages.** Every push to `main` runs `.github/workflows/pages.yml`, which runs `airco-logcheck` again, builds the site with `airco-pages` and deploys it. The site has an index of all committed measurements, newest first, and per measurement the report as HTML and the Inspect viewer. A measurement with a `maps.json` also gets a page Maps: each run's map on the BRT achtergrondkaart of PDOK in RD (EPSG:28992), with the panden coloured by what the run did with them. The page draws with Leaflet and Proj4Leaflet; NL Maps (nlmaps.nl) offers the BRT only in Web Mercator. To look at it before you push:

```bash
uv run airco-pages && python3 -m http.server -d site
```

The site is built from git and is not committed; `.gitignore` lists `site/`. The repository needs GitHub Pages switched on once, with "GitHub Actions" as the source, under Settings, Pages.

## Rescore and repeat runs

An independent assessor can check runs from the log without help from the builder. Rescoring needs no API keys; repeating runs needs keys for the models you repeat.

Set up a clean checkout and check it:

```bash
git clone https://github.com/Geonovum-labs/airco-harness.git && cd airco-harness
uv sync --all-extras && uv run airco-sources --check && uv run pytest -q
```

**Rescore.** A log bundle is in `reports/<name>/logs/`, with the logs in `logs/logs/*.eval`.

```bash
uv run airco-rescore reports/<name>/logs/logs/*.eval --out rescore
```

For each log, the command prints how many scores equal the original, followed by every difference as `(sample, epoch, scorer, key): old -> new`. If a score differs by more than `--tolerance` (default 0), it exits with code 1. To judge the runs without knowing the original scores, look at them in the viewer first.

A warning on stderr means that your checkout is not at the commit of the run, or that the run or your checkout has uncommitted changes. The test set, the reference model, the scorers and the sources are all in git, so a score difference can then come from such a change. The commit of the run is in the log under `eval.revision`. Copy the logs outside the repo, check out that commit, and rescore the copies.

**View a run.** `uv run inspect view --log-dir reports/<name>/logs/logs` opens a viewer at `http://127.0.0.1:7575`. For each run it shows the question, every model call, every tool call with its result, and the scores with their explanation. The Info tab shows the model, the commit and the task metadata.

**Repeat.** Models are not deterministic, and the web changes, so a new run does not have to match the original. It must use the same agent, the same test set and the same limits; the log names them in `eval.metadata` and `eval.task_args`.

```bash
uv run airco-matrix --models <model> --agents <agent> --ids <sample-id> --epochs 1 --name repeat
uv run airco-report logs/repeat
```

The working group settles the margin within which a new run counts as close enough.
