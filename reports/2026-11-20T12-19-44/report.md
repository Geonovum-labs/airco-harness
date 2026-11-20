# airco-harness report

Logs: `logs/2026-11-20T12-19-44`. Runs: 8, of which with an error: 0, and at a limit: 1.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.11 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.22 () | 0.00 () | 1.00 () | 1.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 40.0 | 1696452 | 965.8 | 965.3 |  |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 36.0 | 1614477 | 260.2 | 252.6 |  |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 92.0 | 5182809 | 429.6 | 429.0 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 23.0 | 1679041 | 241.5 | 241.4 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 19.0 | 676319 | 481.8 | 476.4 |  |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 18.0 | 2480525 | 698.0 | 691.9 |  |
| anthropic/claude-opus-5-5 | inspect | 0 | 19.0 | 487354 | 112.6 | 112.1 |  |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 19.0 | 1824674 | 187.0 | 186.9 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                          | dsfl-16     |
|:----------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-sonnet-5-5 | claude-code | 0                                | 0.00 / 0.22 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |
| anthropic/claude-opus-5-5   | claude-code | 0                                | 0.00 / 0.22 |
| anthropic/claude-opus-5-5   | claude-code | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |
| anthropic/claude-opus-5-5   | inspect     | 0                                | 0.00 / 0.11 |
| anthropic/claude-opus-5-5   | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.22 |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-16 | 1 | token | 5182809 |
