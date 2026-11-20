# airco-harness report

Logs: `logs/2026-11-20T17-33-31`. Runs: 24, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.00 (0.00) | 0.69 (0.15) | 1.67 (1.20) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.97 (0.03) | 0.67 (0.67) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.97 (0.03) | 0.67 (0.33) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.86 (0.14) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 1.00 (0.00) | 2.33 (1.20) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.89 (0.11) | 1.33 (1.33) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.67 (0.33) | 3.00 (2.52) | 1.00 (0.00) | 0.33 (0.33) |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 3 | 3 | 0 | 0 | 0.33 (0.33) | 0.92 (0.08) | 0.33 (0.33) | 1.00 (0.00) | 0.67 (0.33) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Skill used | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 0.3 |  | 66921 | 157.3 | 111.4 |  |
| anthropic/claude-haiku-5-5 | claude-code | skill-metadata+skill-mim | 0.3 | 0.00 | 67119 | 143.7 | 127.0 | 0.0202 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1.3 |  | 58797 | 19.8 | 19.5 | 0.0589 |
| anthropic/claude-haiku-5-5 | inspect | skill-metadata+skill-mim | 1.3 | 0.00 | 58532 | 22.7 | 22.6 | 0.0485 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 0.3 |  | 64117 | 150.6 | 116.6 | 0.2373 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 5.7 | 0.67 | 228450 | 200.0 | 175.6 | 0.5785 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 23.0 |  | 247185 | 72.8 | 72.6 | 0.9676 |
| anthropic/claude-sonnet-5-5 | inspect | skill-metadata+skill-mim | 24.3 | 1.00 | 360550 | 76.8 | 75.8 | 1.0192 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                  | dsfl-17     | dsfl-18     | dsfl-19     |
|:----------------------------|:------------|:-------------------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | 0                        | 0.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.58 |
| anthropic/claude-haiku-5-5  | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.92 |
| anthropic/claude-haiku-5-5  | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.92 |
| anthropic/claude-haiku-5-5  | inspect     | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.58 |
| anthropic/claude-sonnet-5-5 | claude-code | 0                        | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | claude-code | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.67 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                        | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | skill-metadata+skill-mim | 1.00 / 1.00 | 0.00 / 1.00 | 0.00 / 0.75 |
