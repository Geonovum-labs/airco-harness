# airco-harness report

Logs: `reports/2026-10-20T10-18-34/logs/logs`. Runs: 45, of which with an error: 0, and at a limit: 1.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.67 () |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.67 () |
| anthropic/claude-haiku-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.33 () | 1.33 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 0.67 () | 0.67 () | 0.33 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.67 () |
| anthropic/claude-sonnet-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.33 () |
| anthropic/claude-opus-5-5 | model | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| mistral/mistral-small-2603 | inspect | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 1.67 () | 1.00 () | 0.00 () |
| mistral/mistral-small-2603 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 1.33 () | 1.00 () | 0.00 () |
| mistral/mistral-medium-2604 | inspect | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.17 () | 1.67 () | 1.00 () | 0.00 () |
| mistral/mistral-medium-2604 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 2.00 () | 1.00 () | 0.00 () |
| mistral/mistral-large-4 | inspect | 0 | 1 | 3 | 0 | 1 | 0.67 () | 0.67 () | 0.00 () | 0.67 () | 0.33 () |
| mistral/mistral-large-4 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 1.00 () | 1.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 2.3 | 135829 | 63.2 | 51.3 | 0.0105 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 2.7 | 66045 | 8.6 | 8.5 | 0.0058 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 1574 | 8.0 | 7.9 |  |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 0.7 | 50387 | 51.7 | 38.8 | 0.0906 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 7.7 | 81195 | 28.3 | 28.3 | 0.0790 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 1725 | 15.2 | 15.1 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 0.0 | 22174 | 58.5 | 28.6 | 0.0833 |
| anthropic/claude-opus-5-5 | inspect | 0 | 3.7 | 30703 | 17.9 | 17.8 | 0.0787 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 520 | 6.9 | 6.8 | 0.0086 |
| mistral/mistral-small-2603 | inspect | 0 | 0.0 | 2365 | 2.4 | 2.3 |  |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 104 | 1.0 | 0.9 |  |
| mistral/mistral-medium-2604 | inspect | 0 | 0.0 | 1146 | 1.4 | 1.3 |  |
| mistral/mistral-medium-2604 | model | 0 | 0.0 | 105 | 1.1 | 1.0 |  |
| mistral/mistral-large-4 | inspect | 0 | 12.7 | 266073 | 404.0 | 200.8 | 0.4738 |
| mistral/mistral-large-4 | model | 0 | 0.0 | 1244 | 57.5 | 57.4 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       |   Variant | imgeo-G04-03   |
|:----------------------------|:------------|----------:|:---------------|
| anthropic/claude-haiku-5-5  | claude-code |         0 | 1.00 / 1.00    |
| anthropic/claude-haiku-5-5  | inspect     |         0 | 1.00 / 1.00    |
| anthropic/claude-haiku-5-5  | model       |         0 | 0.00 / 0.33    |
| anthropic/claude-sonnet-5-5 | claude-code |         0 | 0.67 / 0.67    |
| anthropic/claude-sonnet-5-5 | inspect     |         0 | 1.00 / 1.00    |
| anthropic/claude-sonnet-5-5 | model       |         0 | 0.00 / 0.00    |
| anthropic/claude-opus-5-5   | claude-code |         0 | 1.00 / 1.00    |
| anthropic/claude-opus-5-5   | inspect     |         0 | 1.00 / 1.00    |
| anthropic/claude-opus-5-5   | model       |         0 | 1.00 / 1.00    |
| mistral/mistral-small-2603  | inspect     |         0 | 0.00 / 0.00    |
| mistral/mistral-small-2603  | model       |         0 | 0.00 / 0.00    |
| mistral/mistral-medium-2604 | inspect     |         0 | 0.00 / 0.17    |
| mistral/mistral-medium-2604 | model       |         0 | 0.00 / 0.00    |
| mistral/mistral-large-4     | inspect     |         0 | 0.67 / 0.67    |
| mistral/mistral-large-4     | model       |         0 | 0.00 / 0.00    |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| mistral/mistral-large-4 | inspect | 0 | imgeo-G04-03 | 3 | cost | 423735 |
