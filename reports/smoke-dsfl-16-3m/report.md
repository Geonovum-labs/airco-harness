# airco-harness report

Logs: `logs/smoke-dsfl-16-3m`. Runs: 4, of which with an error: 0, and at a limit: 2.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-haiku-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 19.0 | 724131 | 783.8 | 783.6 |  |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 33.0 | 2045820 | 291.4 | 286.7 |  |
| anthropic/claude-haiku-5-5 | inspect | 0 | 9.0 | 121791 | 26.0 | 25.9 |  |
| anthropic/claude-haiku-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 13.0 | 685285 | 122.8 | 122.8 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                      | Agent       | Variant                          | dsfl-16     |
|:---------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-haiku-5-5 | claude-code | 0                                | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5 | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.00 |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-16 | 1 | message | 724131 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | dsfl-16 | 1 | message | 2045820 |
