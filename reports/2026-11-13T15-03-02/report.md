# airco-harness report

Logs: `logs/2026-11-13T15-03-02`. Runs: 360, of which with an error: 0, and at a limit: 41.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 5 | 15 | 0 | 3 | 0.13 (0.08) | 0.24 (0.15) | 2.13 (1.82) | 0.80 (0.20) | 0.33 (0.21) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 0 | 0.87 (0.13) | 0.94 (0.06) | 0.00 (0.00) | 1.00 (0.00) | 0.53 (0.23) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 5 | 15 | 0 | 0 | 0.27 (0.16) | 0.29 (0.15) | 0.80 (0.43) | 0.87 (0.13) | 0.07 (0.07) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 0 | 0.93 (0.07) | 0.95 (0.05) | 0.00 (0.00) | 1.00 (0.00) | 0.60 (0.24) |
| anthropic/claude-haiku-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.13 (0.13) | 0.13 (0.13) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 5 | 15 | 0 | 3 | 0.13 (0.08) | 0.22 (0.07) | 0.67 (0.52) | 0.67 (0.21) | 0.27 (0.19) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 0 | 0.60 (0.24) | 0.66 (0.22) | 0.00 (0.00) | 0.93 (0.07) | 0.40 (0.24) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 5 | 15 | 0 | 1 | 0.33 (0.21) | 0.38 (0.19) | 65.07 (63.90) | 0.93 (0.07) | 0.20 (0.20) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 0 | 0.80 (0.20) | 0.87 (0.13) | 0.00 (0.00) | 1.00 (0.00) | 0.53 (0.23) |
| anthropic/claude-sonnet-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.27 (0.19) | 0.27 (0.19) | 0.00 (0.00) | 0.33 (0.21) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | claude-code | 0 | 5 | 15 | 0 | 3 | 0.40 (0.24) | 0.62 (0.22) | 0.13 (0.13) | 0.80 (0.20) | 0.60 (0.24) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | 5 | 15 | 0 | 1 | 0.73 (0.19) | 0.82 (0.12) | 0.00 (0.00) | 0.93 (0.07) | 0.40 (0.24) |
| anthropic/claude-opus-5-5 | inspect | 0 | 5 | 15 | 0 | 3 | 0.40 (0.16) | 0.48 (0.19) | 0.07 (0.07) | 0.80 (0.20) | 0.67 (0.18) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 1 | 0.80 (0.20) | 0.89 (0.11) | 0.00 (0.00) | 1.00 (0.00) | 0.40 (0.24) |
| anthropic/claude-opus-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.40 (0.24) | 0.40 (0.24) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| mistral/mistral-small-2603 | inspect | 0 | 5 | 15 | 0 | 2 | 0.00 (0.00) | 0.00 (0.00) | 2.47 (1.11) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 4 | 0.13 (0.13) | 0.15 (0.13) | 1.20 (1.04) | 0.73 (0.19) | 0.00 (0.00) |
| mistral/mistral-small-2603 | model | 0 | 5 | 15 | 0 | 0 | 0.20 (0.20) | 0.20 (0.20) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | 0 | 5 | 15 | 0 | 4 | 0.00 (0.00) | 0.00 (0.00) | 3.60 (1.99) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 4 | 0.20 (0.20) | 0.23 (0.19) | 0.13 (0.13) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | model | 0 | 5 | 15 | 0 | 0 | 0.20 (0.20) | 0.20 (0.20) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| mistral/mistral-large-4 | inspect | 0 | 5 | 15 | 0 | 9 | 0.27 (0.16) | 0.38 (0.14) | 4.33 (3.29) | 0.60 (0.16) | 0.40 (0.16) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 5 | 15 | 0 | 3 | 0.67 (0.15) | 0.75 (0.12) | 0.33 (0.33) | 0.80 (0.13) | 0.33 (0.21) |
| mistral/mistral-large-4 | model | 0 | 5 | 15 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 7.6 | 280517 | 344.3 | 311.5 | 0.1180 |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | 2.1 | 231194 | 87.5 | 84.7 | 0.0068 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 5.5 | 100286 | 22.0 | 21.7 | 0.1129 |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | 2.5 | 215717 | 31.8 | 31.5 | 0.0080 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 875 | 5.5 | 5.4 | 0.0031 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 8.1 | 219521 | 391.1 | 373.0 | 1.3436 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 2.5 | 230830 | 144.0 | 135.7 | 0.1310 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 22.4 | 309482 | 120.2 | 119.7 | 0.5641 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | 2.5 | 195543 | 50.6 | 50.0 | 0.1468 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 1341 | 12.2 | 11.9 | 0.0489 |
| anthropic/claude-opus-5-5 | claude-code | 0 | 8.8 | 268475 | 303.4 | 302.3 | 0.9877 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | 3.3 | 300338 | 108.8 | 107.5 | 0.2760 |
| anthropic/claude-opus-5-5 | inspect | 0 | 18.5 | 293435 | 175.3 | 174.5 | 0.8980 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | 3.4 | 280909 | 56.7 | 55.6 | 0.3147 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 1448 | 16.0 | 15.7 | 0.0706 |
| mistral/mistral-small-2603 | inspect | 0 | 4.4 | 85862 | 32.5 | 19.5 |  |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | 7.7 | 340256 | 105.3 | 59.8 | 0.3936 |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 281 | 2.9 | 2.5 | 0.0007 |
| mistral/mistral-medium-2604 | inspect | 0 | 7.0 | 202624 | 111.1 | 71.3 |  |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | 7.3 | 339879 | 89.2 | 84.4 | 2.6436 |
| mistral/mistral-medium-2604 | model | 0 | 0.0 | 376 | 3.6 | 3.1 | 0.0128 |
| mistral/mistral-large-4 | inspect | 0 | 40.3 | 402590 | 429.9 | 357.2 | 1.9322 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | 12.5 | 235240 | 145.8 | 142.1 | 0.5142 |
| mistral/mistral-large-4 | model | 0 | 0.0 | 1093 | 13.7 | 13.2 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant         | dsfl-01     | dsfl-02     | dsfl-03     | dsfl-04     | dsfl-05     |
|:----------------------------|:------------|:----------------|:------------|:------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | 0               | 0.00 / 0.00 | 0.33 / 0.33 | 0.00 / 0.00 | 0.00 / 0.08 | 0.33 / 0.79 |
| anthropic/claude-haiku-5-5  | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.33 / 0.72 | 1.00 / 1.00 |
| anthropic/claude-haiku-5-5  | inspect     | 0               | 0.67 / 0.67 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.09 | 0.00 / 0.05 |
| anthropic/claude-haiku-5-5  | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.67 / 0.75 | 1.00 / 1.00 |
| anthropic/claude-haiku-5-5  | model       | 0               | 0.00 / 0.00 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code | 0               | 0.33 / 0.33 | 0.33 / 0.33 | 0.00 / 0.00 | 0.00 / 0.09 | 0.00 / 0.35 |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.28 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     | 0               | 1.00 / 1.00 | 0.67 / 0.67 | 0.00 / 0.12 | 0.00 / 0.09 | 0.00 / 0.02 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.37 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | model       | 0               | 0.33 / 0.33 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | claude-code | 0               | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.14 | 0.00 / 0.95 |
| anthropic/claude-opus-5-5   | claude-code | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.44 | 0.67 / 0.67 |
| anthropic/claude-opus-5-5   | inspect     | 0               | 0.67 / 0.67 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.08 | 0.67 / 0.98 |
| anthropic/claude-opus-5-5   | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.44 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | model       | 0               | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | inspect     | 0               | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.02 |
| mistral/mistral-small-2603  | inspect     | mcp-bag-ldproxy | 0.00 / 0.00 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.09 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | model       | 0               | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect     | 0               | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.02 |
| mistral/mistral-medium-2604 | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.12 | 0.00 / 0.02 |
| mistral/mistral-medium-2604 | model       | 0               | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-large-4     | inspect     | 0               | 0.67 / 0.67 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.09 | 0.00 / 0.47 |
| mistral/mistral-large-4     | inspect     | mcp-bag-ldproxy | 1.00 / 1.00 | 1.00 / 1.00 | 0.33 / 0.33 | 0.67 / 0.75 | 0.33 / 0.67 |
| mistral/mistral-large-4     | model       | 0               | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 2 | not parseable: no map shown | api.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 3 | 0 of 2745 required features shown; 1 places match no allowed feature | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 3 | not parseable: no map shown | api.pdok.nl (authoritative), nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 1 | 7 of 78 required features shown; 2 places match no allowed feature | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 1 | 4 of 78 required features shown; 1 places match no allowed feature | nominatim.openstreetmap.org (other), overpass.kumi.systems (other), photon.komoot.io (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 2 | 6 of 78 required features shown; 2 places match no allowed feature | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 2 | 7 of 78 required features shown; 2 places match no allowed feature | overpass-api.de (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 3 | 7 of 78 required features shown; 2 places match no allowed feature | nominatim.openstreetmap.org (other), photon.komoot.io (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 3 | 7 of 78 required features shown; 1 places match no allowed feature | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other), overpass.private.coffee (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 1 | 1 of 195 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 1 | 78 of 195 required features shown; 28 places match no allowed feature | ckan.dataplatform.nl (other), nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 2 | 15 of 195 required features shown; 3 places match no allowed feature | nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 2 | 191 of 195 required features shown; 0 places match no allowed feature | api.pdok.nl (authoritative), monumentenregister.cultureelerfgoed.nl (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 3 | 13 of 195 required features shown; 2 places match no allowed feature | nl.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | api.pdok.nl (authoritative), service.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 19 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 71 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 78 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 1 | 488 of 2745 required features shown; 437 places match no allowed feature | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 3 | 475 of 2745 required features shown; 525 places match no allowed feature | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 3 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 1 | 6 of 78 required features shown; 1 places match no allowed feature | overpass-api.de (other), overpass.private.coffee (other), maps.mail.ru (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 1 | 7 of 78 required features shown; 2 places match no allowed feature | overpass-api.de (other), overpass.kumi.systems (other), nominatim.openstreetmap.org (other), geocode.maps.co (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 2 | 6 of 78 required features shown; 1 places match no allowed feature | overpass-api.de (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 2 | 7 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 3 | 9 of 78 required features shown; 1 places match no allowed feature | sro.nl (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 3 | 8 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 1 | 4 of 195 required features shown; 4 places match no allowed feature | query.wikidata.org (other), www.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 1 | 4 of 195 required features shown; 4 places match no allowed feature | query.wikidata.org (other), www.wikidata.org (other), overpass-api.de (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 2 | 4 of 195 required features shown; 4 places match no allowed feature | nl.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 2 | 5 of 195 required features shown; 4 places match no allowed feature | query.wikidata.org (other), www.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 3 | 4 of 195 required features shown; 3 places match no allowed feature | query.wikidata.org (other), www.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 3 | 194 of 195 required features shown; 0 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 22 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 26 of 78 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 22 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 26 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 22 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag2.basisregistraties.overheid.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 1 | not parseable: no map shown | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative), timeapi.io (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag2.basisregistraties.overheid.nl (other), bag.basisregistraties.overheid.nl (authoritative), localhost:8765 (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 3 | not parseable: no map shown | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 3 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 1 | 12 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), overpass.kumi.systems (other), nominatim.openstreetmap.org (other), www.google.com (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 1 | 4 of 78 required features shown; 1 places match no allowed feature | maps.mail.ru (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 2 | 13 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), overpass.kumi.systems (other), overpass.private.coffee (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 2 | 7 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), photon.komoot.io (other), overpass.osm.ch (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 3 | 8 of 78 required features shown; 2 places match no allowed feature | overpass-api.de (other), api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 3 | 7 of 78 required features shown; 0 places match no allowed feature | overpass-api.de (other), photon.komoot.io (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 1 | 181 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 1 | 181 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 2 | 181 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 3 | 192 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 1 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-03 | 3 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 1 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 2 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-04 | 3 | 34 of 78 required features shown; 0 places match no allowed feature | nothing |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-03 | 1 | 0 of 2745 required features shown; 3 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-03 | 2 | 1 of 2745 required features shown; 2 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-03 | 3 | 0 of 2745 required features shown; 3 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-04 | 1 | 0 of 78 required features shown; 6 places match no allowed feature | www.sportinkaart.nl (other), lokaaltotaal.nl (other), sro.nl (other) |
| mistral/mistral-small-2603 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-04 | 2 | 0 of 78 required features shown; 3 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-04 | 3 | 0 of 78 required features shown; 3 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-05 | 1 | 6 of 195 required features shown; 11 places match no allowed feature | nl.wikipedia.org (other), www.tijdvooramersfoort.nl (other) |
| mistral/mistral-small-2603 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-05 | 2 | 5 of 195 required features shown; 0 places match no allowed feature | nl.wikipedia.org (other), www.tijdvooramersfoort.nl (other) |
| mistral/mistral-small-2603 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-05 | 3 | 1 of 195 required features shown; 6 places match no allowed feature | nl.wikipedia.org (other), www.destadamersfoort.nl (other) |
| mistral/mistral-small-2603 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 0 of 2745 required features shown; 1 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 0 of 2745 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 0 of 2745 required features shown; 1 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 9 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 11 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 0 of 195 required features shown; 10 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 0 of 195 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 1 of 195 required features shown; 6 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-03 | 1 | 0 of 2745 required features shown; 3 places match no allowed feature | www.urbex.nl (other), www.dutchnews.nl (other), arquitecturaviva.com (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-03 | 2 | 0 of 2745 required features shown; 3 places match no allowed feature | www.urbex.nl (other), www.dutchnews.nl (other), arquitecturaviva.com (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-03 | 3 | 0 of 2745 required features shown; 1 places match no allowed feature | geslooptinamersfoort.wordpress.com (other), indebuurt.nl (other), www.urbex.nl (other), www.rtvutrecht.nl (other), www.de-alliantie.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-04 | 1 | 0 of 78 required features shown; 10 places match no allowed feature | www.lokaaltotaal.nl (other), sro.nl (other), www.sportinkaart.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-04 | 2 | 0 of 78 required features shown; 11 places match no allowed feature | www.lokaaltotaal.nl (other), sro.nl (other), www.sportinkaart.nl (other), www.tenderned.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-04 | 3 | 0 of 78 required features shown; 11 places match no allowed feature | www.lokaaltotaal.nl (other), sro.nl (other), www.sportinkaart.nl (other), www.tenderned.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-05 | 1 | 4 of 195 required features shown; 7 places match no allowed feature | nl.wikipedia.org (other), www.atlasobscura.com (other), tijdbalk-amersfoort.nl (other), historisch-amersfoort.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-05 | 2 | 1 of 195 required features shown; 4 places match no allowed feature | nl.wikipedia.org (other), www.atlasobscura.com (other), erfgoedbekeken.nl (other), historisch-amersfoort.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-05 | 3 | 4 of 195 required features shown; 4 places match no allowed feature | nl.wikipedia.org (other), historisch-amersfoort.nl (other), erfgoedbekeken.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | 0 of 2745 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 0 of 2745 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | 10 of 2745 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 11 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 5 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 11 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 0 of 195 required features shown; 2 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | 9 of 195 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 2 of 195 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-large-4 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 1 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| mistral/mistral-large-4 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), geodata.zuid-holland.nl (other), api.pdok.nl (authoritative), data.labs.kadaster.nl (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 3 | not parseable: no map shown | api.pdok.nl (authoritative) |
| mistral/mistral-large-4 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-04 | 1 | 5 of 78 required features shown; 7 places match no allowed feature | sro.nl (other), www.tenderned.nl (other), example.com (other), overpass-api.de (other), nominatim.openstreetmap.org (other), geocoding-api.open-meteo.com (other), photon.komoot.io (other), geodata.nationaalgeoregister.nl (other), httpbin.org (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-04 | 2 | 10 of 78 required features shown; 2 places match no allowed feature | sro.nl (other), www.lokaaltotaal.nl (other), www.tenderned.nl (other), nominatim.openstreetmap.org (other), photon.komoot.io (other), geocoding-api.open-meteo.com (other), overpass-api.de (other), geodata.nationaalgeoregister.nl (other), overpass.kumi.systems (other), overpass.private.coffee (other), overpass.osm.ch (other), overpass.nchc.org.tw (other), vymaps.com (other), overpass.openstreetmap.fr (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-04 | 3 | 5 of 78 required features shown; 5 places match no allowed feature | sro.nl (other), www.lokaaltotaal.nl (other), overpass-api.de (other), overpass.kumi.systems (other), nominatim.openstreetmap.org (other), overpass.private.coffee (other), photon.komoot.io (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-05 | 1 | not parseable: no map shown | query.wikidata.org (other), nl.wikipedia.org (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-05 | 2 | 195 of 195 required features shown; 23 places match no allowed feature | www.nationaalgeoregister.nl (other), service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| mistral/mistral-large-4 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-05 | 3 | 79 of 195 required features shown; 28 places match no allowed feature | nl.wikipedia.org (other), www.wikidata.org (other), query.wikidata.org (other), qlever.dev (other), qlever.cs.uni-freiburg.de (other), wikidata.demo.openlinksw.com (other), linkeddata.cultureelerfgoed.nl (other), services.rce.geovoorziening.nl (other), api.linkeddata.cultureelerfgoed.nl (other), query-main.wikidata.org (other), api.triplydb.com (other) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | 2745 of 2745 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | not parseable: no map shown | bag.ldproxy.net (authoritative) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 1 | 78 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 2 | 78 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-04 | 3 | 19 of 78 required features shown; 0 places match no allowed feature | nothing |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | 195 of 195 required features shown; 5 places match no allowed feature | bag.ldproxy.net (authoritative) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | not parseable: no map shown | bag.ldproxy.net (authoritative) |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | 195 of 195 required features shown; 0 places match no allowed feature | bag.ldproxy.net (authoritative) |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 1 | token | 603818 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 2 | token | 618247 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 3 | time | 541409 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 1 | time | 100019 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 2 | token | 604252 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 2 | time | 435532 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 3 | time | 321241 |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 1 | token | 614543 |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 1 | token | 623453 |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 2 | token | 674357 |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 2 | token | 847733 |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 3 | message | 543035 |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 3 | token | 660048 |
| anthropic/claude-opus-5-5 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 658867 |
| anthropic/claude-opus-5-5 | claude-code | mcp-bag-ldproxy | dsfl-05 | 2 | token | 631485 |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-04 | 1 | message | 253104 |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-05 | 1 | token | 613842 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-01 | 1 | token | 632091 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-01 | 2 | token | 652309 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-01 | 3 | token | 628370 |
| mistral/mistral-small-2603 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 650652 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-03 | 1 | token | 619851 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-03 | 2 | token | 602558 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-04 | 1 | token | 607063 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-05 | 3 | message | 576714 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 1 | token | 626340 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 626628 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 1 | token | 629507 |
| mistral/mistral-medium-2604 | inspect | mcp-bag-ldproxy | dsfl-05 | 2 | token | 647659 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-01 | 1 | token | 667959 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 1 | token | 677002 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 1 | time | 538248 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 2 | token | 656087 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-03 | 3 | token | 652346 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-04 | 1 | token | 640310 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-04 | 2 | token | 685619 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-05 | 1 | time | 96668 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-05 | 3 | time | 413573 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 2 | token | 670625 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-03 | 3 | token | 611417 |
| mistral/mistral-large-4 | inspect | mcp-bag-ldproxy | dsfl-05 | 3 | message | 413586 |
