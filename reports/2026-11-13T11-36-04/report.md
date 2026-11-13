# airco-harness report

Logs: `logs/2026-11-13T11-36-04`. Runs: 135, of which with an error: 0, and at a limit: 17.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 3 | 9 | 0 | 1 | 0.44 (0.22) | 0.78 (0.11) | 0.33 (0.33) | 0.78 (0.11) | 0.78 (0.11) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 3 | 9 | 0 | 2 | 0.00 (0.00) | 0.11 (0.11) | 0.22 (0.22) | 0.22 (0.22) | 0.44 (0.22) |
| anthropic/claude-haiku-5-5 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 0 | 0.44 (0.29) | 0.88 (0.09) | 1.78 (1.78) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 3 | 9 | 0 | 0 | 0.56 (0.29) | 0.89 (0.11) | 0.44 (0.44) | 0.89 (0.11) | 0.67 (0.33) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 3 | 9 | 0 | 5 | 0.22 (0.22) | 0.44 (0.22) | 0.22 (0.22) | 0.44 (0.22) | 0.67 (0.33) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.33 (0.33) | 1.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | claude-code | 0 | 3 | 9 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.56 (0.56) | 1.00 (0.00) | 0.89 (0.11) |
| anthropic/claude-opus-5-5 | inspect | 0 | 3 | 9 | 0 | 1 | 0.67 (0.33) | 1.00 (0.00) | 0.56 (0.56) | 1.00 (0.00) | 0.78 (0.22) |
| anthropic/claude-opus-5-5 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 0 | 0.67 (0.33) | 1.00 (0.00) | 0.33 (0.33) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-small-2603 | inspect | 0 | 3 | 9 | 0 | 0 | 0.00 (0.00) | 0.12 (0.12) | 1.11 (1.11) | 0.67 (0.33) | 0.00 (0.00) |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 2 | 0.33 (0.33) | 0.65 (0.31) | 2.89 (2.89) | 0.89 (0.11) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | 0 | 3 | 9 | 0 | 2 | 0.00 (0.00) | 0.00 (0.00) | 0.78 (0.78) | 0.22 (0.22) | 0.11 (0.11) |
| mistral/mistral-medium-2604 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 0 | 0.33 (0.33) | 0.64 (0.32) | 5.33 (5.33) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-large-4 | inspect | 0 | 3 | 9 | 0 | 4 | 0.22 (0.11) | 0.44 (0.11) | 0.44 (0.44) | 0.44 (0.11) | 0.67 (0.33) |
| mistral/mistral-large-4 | inspect | mcp-groundwater-monitoring | 3 | 9 | 0 | 0 | 0.56 (0.29) | 0.80 (0.18) | 2.89 (2.89) | 1.00 (0.00) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 11.0 | 366966 | 342.1 | 215.7 | 0.0261 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 14.3 | 248578 | 47.2 | 46.9 |  |
| anthropic/claude-haiku-5-5 | inspect | mcp-groundwater-monitoring | 8.9 | 118349 | 110.3 | 109.6 | 0.0143 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 10.7 | 290500 | 316.2 | 304.2 | 0.2413 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 26.6 | 522987 | 119.5 | 117.4 | 1.1900 |
| anthropic/claude-sonnet-5-5 | inspect | mcp-groundwater-monitoring | 9.4 | 127551 | 104.9 | 103.5 | 0.1126 |
| anthropic/claude-opus-5-5 | claude-code | 0 | 6.3 | 188749 | 189.9 | 156.0 | 0.2419 |
| anthropic/claude-opus-5-5 | inspect | 0 | 10.0 | 347166 | 64.1 | 62.7 | 0.7416 |
| anthropic/claude-opus-5-5 | inspect | mcp-groundwater-monitoring | 8.8 | 114806 | 94.7 | 94.0 | 0.2937 |
| mistral/mistral-small-2603 | inspect | 0 | 6.9 | 83270 | 75.0 | 41.5 |  |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | 4.7 | 59411 | 126.0 | 80.5 | 0.0281 |
| mistral/mistral-medium-2604 | inspect | 0 | 16.9 | 271091 | 159.4 | 135.1 |  |
| mistral/mistral-medium-2604 | inspect | mcp-groundwater-monitoring | 6.7 | 24922 | 95.1 | 92.8 | 0.1351 |
| mistral/mistral-large-4 | inspect | 0 | 27.0 | 505598 | 400.6 | 374.0 | 3.1404 |
| mistral/mistral-large-4 | inspect | mcp-groundwater-monitoring | 10.3 | 60360 | 174.4 | 173.0 | 0.1819 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       | Variant                    | dsfl-06     | dsfl-07     | dsfl-08     |
|:----------------------------|:------------|:---------------------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code | 0                          | 0.67 / 0.67 | 0.00 / 1.00 | 0.67 / 0.67 |
| anthropic/claude-haiku-5-5  | inspect     | 0                          | 0.00 / 0.00 | 0.00 / 0.33 | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5  | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 0.69 | 0.33 / 0.94 |
| anthropic/claude-sonnet-5-5 | claude-code | 0                          | 1.00 / 1.00 | 0.00 / 1.00 | 0.67 / 0.67 |
| anthropic/claude-sonnet-5-5 | inspect     | 0                          | 0.67 / 0.67 | 0.00 / 0.67 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | claude-code | 0                          | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     | 0                          | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 1.00 | 1.00 / 1.00 |
| mistral/mistral-small-2603  | inspect     | 0                          | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.36 |
| mistral/mistral-small-2603  | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 0.03 | 0.00 / 0.91 |
| mistral/mistral-medium-2604 | inspect     | 0                          | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.91 |
| mistral/mistral-large-4     | inspect     | 0                          | 0.33 / 0.33 | 0.00 / 0.67 | 0.33 / 0.33 |
| mistral/mistral-large-4     | inspect     | mcp-groundwater-monitoring | 1.00 / 1.00 | 0.00 / 0.44 | 0.67 / 0.97 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other), www.dinoloket.nl (other), www.bro-productomgeving.nl (other), publiek.broservices.nl (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-07 | 2 | 0 of 12 required features shown; 1 places match no allowed feature | nominatim.openstreetmap.org (other), grondwaterstandkaart.nl (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-07 | 2 | 12 of 12 required features shown; 1 places match no allowed feature | nominatim.openstreetmap.org (other), www.dinoloket.nl (other), service.pdok.nl (other), api.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-07 | 3 | not parseable: no map shown | grondwaterstandkaart.nl (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | nominatim.openstreetmap.org (other), publiek.broservices.nl (authoritative), service.pdok.nl (other), api.pdok.nl (other), www.opengis.net (other) |
| anthropic/claude-haiku-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | 1 of 12 required features shown; 13 places match no allowed feature | nothing |
| anthropic/claude-haiku-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-07 | 2 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-07 | 2 | not parseable: no map shown | api.pdok.nl (other), www.pdok.nl (other), www.opengis.net (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-07 | 1 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other), publiek.broservices.nl (authoritative), www.broservices.nl (other), www.opengis.net (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-07 | 2 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-07 | 2 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other), publiek.broservices.nl (authoritative), www.broservices.nl (other), www.opengis.net (other) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other), publiek.broservices.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other), service.pdok.nl (other) |
| anthropic/claude-opus-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 12 of 12 required features shown; 1 places match no allowed feature | api.pdok.nl (other) |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-07 | 1 | 0 of 12 required features shown; 6 places match no allowed feature | grondwaterstandkaart.nl (other), www.pfaskaartnederland.nl (other), www.arcgis.com (other) |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-07 | 2 | 0 of 12 required features shown; 0 places match no allowed feature | grondwaterstandkaart.nl (other), www.pfaskaartnederland.nl (other) |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-07 | 3 | 0 of 12 required features shown; 4 places match no allowed feature | grondwaterstandkaart.nl (other), www.pfaskaartnederland.nl (other), www.dinoloket.nl (other) |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 1 of 12 required features shown; 12 places match no allowed feature | nothing |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 0 of 12 required features shown; 14 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-07 | 1 | not parseable: no map shown | www.dinoloket.nl (other) |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-07 | 2 | 0 of 12 required features shown; 3 places match no allowed feature | grondwaterstandkaart.nl (other), api.pdok.nl (other), data.overheid.nl (other) |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-07 | 3 | 0 of 12 required features shown; 4 places match no allowed feature | grondwaterstandkaart.nl (other) |
| mistral/mistral-medium-2604 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 0 of 12 required features shown; 18 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | 0 of 12 required features shown; 14 places match no allowed feature | nothing |
| mistral/mistral-medium-2604 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 0 of 12 required features shown; 16 places match no allowed feature | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-07 | 1 | not parseable: no map shown | api.pdok.nl (other), basisregistratieondergrond.nl (other) |
| mistral/mistral-large-4 | inspect | 0 | dsfl-07 | 2 | 12 of 12 required features shown; 2 places match no allowed feature | nominatim.openstreetmap.org (other), api.pdok.nl (other), epsg.io (other) |
| mistral/mistral-large-4 | inspect | 0 | dsfl-07 | 3 | 12 of 12 required features shown; 2 places match no allowed feature | api.pdok.nl (other), geodata.nationaalgeoregister.nl (other), nominatim.openstreetmap.org (other) |
| mistral/mistral-large-4 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | 12 of 12 required features shown; 1 places match no allowed feature | geodata.nationaalgeoregister.nl (other), nominatim.openstreetmap.org (other) |
| mistral/mistral-large-4 | inspect | mcp-groundwater-monitoring | dsfl-07 | 2 | 0 of 12 required features shown; 15 places match no allowed feature | nominatim.openstreetmap.org (other) |
| mistral/mistral-large-4 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | 4 of 12 required features shown; 10 places match no allowed feature | nothing |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-08 | 2 | token | 629768 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-08 | 2 | token | 605926 |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-08 | 3 | token | 600395 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-06 | 2 | token | 625357 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-07 | 2 | token | 644045 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-08 | 1 | token | 646797 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-08 | 2 | token | 637459 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-08 | 3 | token | 632215 |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-08 | 3 | token | 718226 |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | dsfl-07 | 1 | message | 215403 |
| mistral/mistral-small-2603 | inspect | mcp-groundwater-monitoring | dsfl-07 | 3 | message | 226350 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-06 | 2 | token | 650257 |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-08 | 2 | token | 635108 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-06 | 2 | token | 644053 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-06 | 3 | token | 664335 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-08 | 1 | token | 655286 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-08 | 3 | token | 746453 |
