# airco-harness report

Logs: `reports/2026-11-13T10-14-18/logs/logs`. Runs: 135, of which with an error: 0, and at a limit: 49.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.60 (0.24) | 0.60 (0.24) | 0.00 (0.00) | 0.60 (0.24) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.40 (0.24) | 0.52 (0.21) | 0.00 (0.00) | 0.73 (0.19) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.40 (0.24) | 0.47 (0.23) | 0.00 (0.00) | 0.60 (0.24) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.47 (0.23) | 0.53 (0.20) | 0.00 (0.00) | 0.67 (0.21) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.33 (0.21) | 0.43 (0.19) | 0.00 (0.00) | 0.60 (0.24) | 0.13 (0.13) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 5 | 0.33 (0.21) | 0.46 (0.17) | 0.93 (0.93) | 0.73 (0.16) | 0.07 (0.07) |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 4 | 0.20 (0.20) | 0.21 (0.20) | 2.47 (1.67) | 0.87 (0.08) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 5 | 0.07 (0.07) | 0.10 (0.07) | 0.00 (0.00) | 0.53 (0.20) | 0.00 (0.00) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 5 | 0.60 (0.24) | 0.60 (0.24) | 2.47 (2.47) | 0.73 (0.16) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | 3.1 | 470683 | 84.8 | 73.6 | 0.0806 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 2.3 | 561794 | 46.8 | 46.6 | 0.2662 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 3.3 | 451492 | 79.0 | 70.7 | 0.2805 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 2.6 | 462897 | 66.1 | 66.0 | 0.8616 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | 3.0 | 440483 | 81.7 | 74.8 | 0.6186 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 2.5 | 474432 | 79.1 | 78.8 | 2.1795 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 3.1 | 428340 | 54.4 | 53.6 | 0.3294 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 2.3 | 401964 | 93.4 | 92.9 | 9.1969 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 5.5 | 437663 | 186.3 | 165.5 | 1.0459 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant         | dsfl-01     | dsfl-02     | dsfl-03     | dsfl-04     | dsfl-05     |
|:----------------------------|:------------|:----------------|:------------|:------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5  | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.24 | 0.00 / 0.33 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.37 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.33 | 0.33 / 0.33 |
| anthropic/claude-opus-5-5   | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.47 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 0.67 / 0.67 | 0.00 / 0.01 | 0.00 / 0.38 | 0.00 / 0.22 |
| mistral/mistral-small-2603  | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.06 | 0.00 / 0.01 |
| mistral/mistral-medium-2604 | inspect     | mcp-bag-ldproxy | 0.33 / 0.33 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.16 | 0.00 / 0.01 |
| mistral/mistral-large-4     | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.01 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 158 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 37 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 22 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 22 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 57 of 2745 required panden shown; 14 places match no pand | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 22 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 43 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 127 of 195 required panden shown; 0 places match no pand | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 3 of 2745 required panden shown; 7 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 0 of 2745 required panden shown; 19 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 14 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 0 of 78 required panden shown; 1 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 0 of 195 required panden shown; 10 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 3 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 4 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 10 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 11 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 16 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 11 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 1 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 1 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 1 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 27 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 6 of 195 required panden shown; 37 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 772369 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | token | 701776 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 2016997 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | token | 695323 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 679426 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | token | 709487 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 634997 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | token | 714730 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 676375 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | token | 692735 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 772973 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | token | 699686 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 737480 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | token | 693527 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 688702 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | token | 604029 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 668982 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | token | 719166 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 1285630 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | token | 687237 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 735800 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | token | 686992 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 601170 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | token | 689970 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 813400 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | token | 688085 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 1107516 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | token | 685908 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | token | 690902 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 697279 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | token | 688169 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 699708 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | token | 690261 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 711052 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | token | 688167 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-02 | 1 | token | 608562 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | token | 661599 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 664925 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 666557 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-02 | 1 | token | 692042 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-02 | 2 | token | 693221 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-02 | 3 | token | 691942 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 639603 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 743104 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 978473 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 950125 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 939407 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 600177 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 759857 |
