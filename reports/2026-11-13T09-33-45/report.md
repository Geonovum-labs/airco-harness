# airco-harness report

Logs: `logs/2026-11-13T09-33-45`. Runs: 90, of which with an error: 0, and at a limit: 32.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.40 (0.24) | 0.45 (0.23) | 0.00 (0.00) | 0.67 (0.21) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 4 | 0.53 (0.23) | 0.64 (0.20) | 9.60 (9.60) | 0.93 (0.07) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 5 | 0.33 (0.21) | 0.45 (0.17) | 23.40 (23.40) | 0.87 (0.13) | 0.07 (0.07) |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 7 | 0.20 (0.20) | 0.22 (0.20) | 9.07 (6.34) | 0.87 (0.08) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 4 | 0.07 (0.07) | 0.09 (0.06) | 0.00 (0.00) | 0.67 (0.15) | 0.00 (0.00) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 6 | 0.60 (0.24) | 0.69 (0.20) | 0.13 (0.13) | 0.80 (0.13) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 2.0 | 636116 | 37.8 | 37.7 | 0.0738 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 3.1 | 407836 | 62.3 | 62.1 | 0.5690 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 3.0 | 474352 | 83.3 | 82.7 | 1.8992 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 4.1 | 490975 | 56.3 | 50.9 | 0.3745 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 2.7 | 393537 | 109.1 | 108.6 | 9.0142 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 4.3 | 423972 | 162.6 | 141.8 | 1.0204 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent   | Variant         | dsfl-01     | dsfl-02     | dsfl-03     | dsfl-04     | dsfl-05     |
|:----------------------------|:--------|:----------------|:------------|:------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | inspect | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.23 | 0.00 / 0.01 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.31 | 0.67 / 0.89 |
| anthropic/claude-opus-5-5   | inspect | mcp-bag-ldproxy | 1.00 / 1.00 | 0.67 / 0.67 | 0.00 / 0.01 | 0.00 / 0.38 | 0.00 / 0.20 |
| mistral/mistral-small-2603  | inspect | mcp-bag-ldproxy | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.08 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 0.33 / 0.33 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.12 | 0.00 / 0.01 |
| mistral/mistral-large-4     | inspect | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.04 | 1.00 / 1.00 | 0.00 / 0.42 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 16 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 3 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 20 of 2745 required panden shown; 47 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 13 of 2745 required panden shown; 97 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 131 of 195 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 10 of 2745 required panden shown; 124 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 28 of 2745 required panden shown; 103 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 31 of 2745 required panden shown; 124 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 22 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 34 of 78 required panden shown; 0 places match no pand | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 117 of 195 required panden shown; 0 places match no pand | bag.ldproxy.net (authoritative) |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 0 of 2745 required panden shown; 10 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 0 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 10 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 6 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 0 of 78 required panden shown; 101 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 13 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 0 of 195 required panden shown; 15 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 0 of 195 required panden shown; 10 places match no pand | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 5 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 5 of 2745 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 11 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 5 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 11 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 2 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 1 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 1 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 362 of 2745 required panden shown; 2 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 78 of 78 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 86 of 195 required panden shown; 0 places match no pand | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 158 of 195 required panden shown; 0 places match no pand | nothing |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 2265586 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 676167 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 2080846 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 922041 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 625903 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 637039 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 620069 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 686229 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 808364 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 760920 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 697943 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 753350 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 683898 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 1045432 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 706555 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-02 | 2 | token | 605958 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 623254 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 783245 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | token | 650626 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | token | 644742 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 617116 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 663870 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-02 | 1 | token | 817266 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-02 | 3 | token | 694519 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 634959 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 696451 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 982283 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 957635 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 936290 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 650981 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 605872 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | token | 622748 |
