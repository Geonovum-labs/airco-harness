# airco-harness report

Logs: `logs/2026-11-20T16-10-37`. Runs: 24, of which with an error: 0, and at a limit: 1.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.89 (0.11) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 1.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.33 (0.33) |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 1 | 0.33 (0.33) | 0.67 (0.33) | 0.00 (0.00) | 0.67 (0.33) | 0.67 (0.33) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Skill used | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 0.7 |  | 53897 | 53.4 | 44.5 | 0.0322 |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 0.3 | 0.00 | 39030 | 72.5 | 60.7 | 0.0083 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 2.0 |  | 33574 | 7.5 | 7.5 | 0.0357 |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 1.7 | 0.00 | 36870 | 8.4 | 8.3 | 0.0504 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 0.0 |  | 22928 | 44.3 | 37.3 | 0.0557 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 0.0 | 0.00 | 23316 | 67.1 | 53.5 | 0.0182 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 10.7 |  | 103905 | 26.1 | 26.0 | 0.1540 |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 26.7 | 0.67 | 416425 | 80.3 | 78.0 | 1.0392 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                  | dsfl-17     | dsfl-18     | dsfl-19     |
|:----------------------------|:------------|:-------------------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.67 |
| anthropic/claude-haiku-5-5  | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-haiku-5-5  | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-haiku-5-5  | inspect     | skill-metadata+skill-mim | 0.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | claude-code | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.00 |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | dsfl-19 | 1 | token | 787005 |
