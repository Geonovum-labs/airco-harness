# airco-harness report

Logs: `logs/2026-11-19T15-00-13`. Runs: 4, of which with an error: 0, and at a limit: 3.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 33.0 | 1586590 | 677.6 | 677.4 |  |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 32.0 | 5078544 | 336.4 | 332.5 |  |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 122.0 | 5089757 | 412.1 | 411.8 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 41.0 | 5182442 | 358.9 | 358.6 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                          | dsfl-16     |
|:----------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-sonnet-5-5 | claude-code | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.00 |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-16 | 1 | token | 5089757 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | dsfl-16 | 1 | token | 5182442 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | dsfl-16 | 1 | token | 5078544 |
