# airco-harness report

Logs: `logs/2026-11-20T11-07-23`. Runs: 4, of which with an error: 0, and at a limit: 1.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 52.0 | 2288227 | 1661.1 | 1660.2 |  |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 52.0 | 2510018 | 315.9 | 313.1 |  |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 51.0 | 984597 | 172.0 | 172.0 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 46.0 | 3546983 | 304.1 | 304.0 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                          | dsfl-16     |
|:----------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-sonnet-5-5 | claude-code | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-16 | 1 | message | 2288227 |
