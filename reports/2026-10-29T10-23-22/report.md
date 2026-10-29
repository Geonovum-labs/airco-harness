# airco-harness report

Logs: `logs/2026-10-29T10-23-22`. Runs: 15, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 0.67 () | 0.67 () | 0.00 () | 0.67 () | 0.33 () |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-haiku-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-small-2603 | inspect | 0 | 1 | 3 | 0 | 0 | 0.33 () | 0.33 () | 0.00 () | 0.33 () | 0.00 () |
| mistral/mistral-small-2603 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 2.0 | 78425 | 37.8 | 34.2 | 0.0071 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 2.0 | 34243 | 6.5 | 6.4 | 0.0030 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 537 | 3.4 | 3.4 |  |
| mistral/mistral-small-2603 | inspect | 0 | 3.3 | 28531 | 6.6 | 6.6 | 0.0062 |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 103 | 0.8 | 0.6 |  |

## `correct` per sample (mean over epochs)

| sample   |   ('anthropic/claude-haiku-5-5', 'claude-code', '0') |   ('anthropic/claude-haiku-5-5', 'inspect', '0') |   ('anthropic/claude-haiku-5-5', 'model', '0') |   ('mistral/mistral-small-2603', 'inspect', '0') |   ('mistral/mistral-small-2603', 'model', '0') |
|:---------|-----------------------------------------------------:|-------------------------------------------------:|-----------------------------------------------:|-------------------------------------------------:|-----------------------------------------------:|
| dsfl-01  |                                                 0.67 |                                                1 |                                              0 |                                             0.33 |                                              0 |
