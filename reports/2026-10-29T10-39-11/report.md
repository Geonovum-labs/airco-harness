# airco-harness report

Logs: `reports/2026-10-29T10-39-11/logs/logs`. Runs: 45, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 0.67 () | 0.67 () | 0.00 () | 0.67 () | 0.33 () |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-haiku-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.67 () |
| anthropic/claude-sonnet-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-small-2603 | inspect | 0 | 1 | 3 | 0 | 0 | 0.33 () | 0.33 () | 0.00 () | 0.33 () | 0.00 () |
| mistral/mistral-small-2603 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-medium-2604 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| mistral/mistral-medium-2604 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-large-4 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| mistral/mistral-large-4 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 2.7 | 98538 | 43.6 | 39.1 | 0.0079 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 2.0 | 31079 | 5.4 | 5.3 | 0.0034 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 458 | 2.7 | 2.6 |  |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 3.0 | 100076 | 70.6 | 48.5 | 0.1114 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 10.3 | 92913 | 22.8 | 22.8 | 0.0886 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 566 | 5.5 | 5.5 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 4.3 | 152950 | 76.5 | 60.5 | 0.2087 |
| anthropic/claude-opus-5-5 | inspect | 0 | 3.3 | 23955 | 14.2 | 14.2 | 0.0567 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 716 | 7.7 | 7.6 |  |
| mistral/mistral-small-2603 | inspect | 0 | 3.3 | 33975 | 7.0 | 7.0 | 0.0086 |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 110 | 0.8 | 0.7 |  |
| mistral/mistral-medium-2604 | inspect | 0 | 4.0 | 21530 | 22.7 | 22.7 | 0.0123 |
| mistral/mistral-medium-2604 | model | 0 | 0.0 | 95 | 0.7 | 0.6 |  |
| mistral/mistral-large-4 | inspect | 0 | 8.0 | 31205 | 29.3 | 29.2 | 0.0073 |
| mistral/mistral-large-4 | model | 0 | 0.0 | 1231 | 12.9 | 12.8 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       |   Variant | dsfl-01     |
|:----------------------------|:------------|----------:|:------------|
| anthropic/claude-haiku-5-5  | claude-code |         0 | 0.67 / 0.67 |
| anthropic/claude-haiku-5-5  | inspect     |         0 | 1.00 / 1.00 |
| anthropic/claude-haiku-5-5  | model       |         0 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code |         0 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     |         0 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | model       |         0 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | claude-code |         0 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     |         0 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | inspect     |         0 | 0.33 / 0.33 |
| mistral/mistral-small-2603  | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect     |         0 | 1.00 / 1.00 |
| mistral/mistral-medium-2604 | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-large-4     | inspect     |         0 | 1.00 / 1.00 |
| mistral/mistral-large-4     | model       |         0 | 0.00 / 0.00 |
