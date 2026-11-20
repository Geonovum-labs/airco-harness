# airco-harness report

Logs: `logs/2026-11-20T15-10-36`. Runs: 8, of which with an error: 0, and at a limit: 0.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.11 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 1 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Skill used | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 32.0 |  | 1255985 | 819.1 | 811.3 | 0.4689 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 36.0 |  | 2873209 | 395.3 | 384.0 | 1.0938 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 47.0 |  | 861050 | 149.5 | 149.4 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 26.0 |  | 1889639 | 269.4 | 269.2 | 0.8262 |
| anthropic/claude-opus-5-5 | claude-code | 0 | 22.0 |  | 805572 | 350.4 | 350.0 | 0.5899 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 30.0 |  | 2063747 | 320.2 | 303.7 | 1.6081 |
| anthropic/claude-opus-5-5 | inspect | 0 | 13.0 |  | 264213 | 78.5 | 78.1 |  |
| anthropic/claude-opus-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 36.0 |  | 3256708 | 368.7 | 368.4 | 2.1853 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                          | dsfl-16     |
|:----------------------------|:------------|:---------------------------------|:------------|
| anthropic/claude-sonnet-5-5 | claude-code | 0                                | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                                | 0.00 / 0.11 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | claude-code | 0                                | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     | 0                                | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | inspect     | mcp-bgt-wijkenbuurten-subsurface | 1.00 / 1.00 |
