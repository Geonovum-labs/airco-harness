# airco-harness report

Logs: `logs/2026-11-20T15-56-31`. Runs: 8, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 0.00 () | 0.67 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.11 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Skill used | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 42.0 |  | 1956955 | 1021.4 | 1020.7 | 0.5974 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 25.0 |  | 2133805 | 410.3 | 398.5 | 0.9375 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 42.0 |  | 1004752 | 186.1 | 186.0 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 17.0 |  | 1273841 | 291.6 | 291.3 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 23.0 |  | 708398 | 513.4 | 495.0 | 0.5336 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 23.0 |  | 1361999 | 378.6 | 350.3 | 1.5560 |
| anthropic/claude-opus-5-5 | inspect | 0 | 23.0 |  | 391327 | 79.9 | 79.8 |  |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 22.0 |  | 1509032 | 348.2 | 348.0 | 1.5321 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                          | dsfl-16     |
|:----------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-sonnet-5-5 | claude-code | 0                                | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 0.00 / 0.67 |
| anthropic/claude-opus-5-5   | claude-code | 0                                | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     | 0                                | 0.00 / 0.11 |
| anthropic/claude-opus-5-5   | inspect     | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
