# airco-harness report

Logs: `logs/2026-11-19T14-37-25`. Runs: 4, of which with an error: 0, and at a limit: 4.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 1 | 1 | 0 | 1 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 1.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 22.0 | 672786 | 173.2 | 173.0 |  |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | 22.0 | 2772539 | 322.7 | 318.1 |  |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 87.0 | 2971883 | 337.4 | 337.2 |  |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | 28.0 | 3013428 | 286.2 | 285.8 |  |

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
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-16 | 1 | message | 672786 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-16 | 1 | message | 2971883 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bgt-wijkenbuurten-subsurface | dsfl-16 | 1 | message | 2772539 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bgt-wijkenbuurten-subsurface | dsfl-16 | 1 | token | 3013428 |
