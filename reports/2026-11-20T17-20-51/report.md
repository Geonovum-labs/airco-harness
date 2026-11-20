# airco-harness report

Logs: `logs/2026-11-20T17-20-51`. Runs: 24, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.00 (0.00) | 0.33 (0.19) | 6.33 (2.91) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.44 (0.29) | 8.00 (7.02) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.44 (0.29) | 4.33 (2.60) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.44 (0.29) | 5.33 (3.93) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.44 (0.29) | 5.67 (4.26) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.64 (0.18) | 2.00 (1.00) | 1.00 (0.00) | 0.33 (0.33) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.44 (0.29) | 7.00 (3.61) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.78 (0.22) | 3.33 (1.67) | 1.00 (0.00) | 0.33 (0.33) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Skill used | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 0.7 |  | 72767 | 98.0 | 77.0 |  |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 0.3 | 0.00 | 59346 | 101.9 | 90.3 | 0.0073 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 0.7 |  | 34322 | 16.0 | 15.9 | 0.0338 |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 0.7 | 0.00 | 44381 | 17.7 | 17.6 | 0.0344 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 0.3 |  | 55454 | 121.8 | 93.2 | 0.1598 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 4.3 | 0.67 | 178848 | 151.7 | 133.4 | 0.6421 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 3.7 |  | 38441 | 24.6 | 24.5 | 0.2220 |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 18.3 | 1.00 | 282853 | 96.2 | 93.3 | 0.8873 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                  | dsfl-17     | dsfl-18     | dsfl-19     |
|:----------------------------|:------------|:-------------------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | 0                        | 0.00 / 0.67 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-haiku-5-5  | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-haiku-5-5  | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-haiku-5-5  | inspect     | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-sonnet-5-5 | claude-code | 0                        | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.42 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 |
| anthropic/claude-sonnet-5-5 | inspect     | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.33 |
