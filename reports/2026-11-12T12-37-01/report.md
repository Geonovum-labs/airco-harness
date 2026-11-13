# airco-harness report

Logs: `reports/2026-11-12T12-37-01/logs/logs`. Runs: 90, of which with an error: 0, and at a limit: 5.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 2 | 6 | 0 | 1 | 0.17 (0.17) | 0.43 (0.35) | 4.00 (4.00) | 0.83 (0.17) | 0.17 (0.17) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 2 | 6 | 0 | 0 | 0.17 (0.17) | 0.45 (0.33) | 0.67 (0.67) | 0.83 (0.17) | 0.17 (0.17) |
| anthropic/claude-haiku-5-5 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 2 | 6 | 0 | 1 | 0.83 (0.17) | 0.83 (0.17) | 0.00 (0.00) | 0.83 (0.17) | 1.00 (0.00) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 2 | 6 | 0 | 1 | 0.67 (0.00) | 0.93 (0.04) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) |
| anthropic/claude-sonnet-5-5 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | claude-code | 0 | 2 | 6 | 0 | 0 | 1.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) |
| anthropic/claude-opus-5-5 | inspect | 0 | 2 | 6 | 0 | 0 | 1.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) |
| anthropic/claude-opus-5-5 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-small-2603 | inspect | 0 | 2 | 6 | 0 | 0 | 0.17 (0.17) | 0.17 (0.17) | 2.00 (2.00) | 0.67 (0.33) | 0.00 (0.00) |
| mistral/mistral-small-2603 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | inspect | 0 | 2 | 6 | 0 | 0 | 0.50 (0.50) | 0.51 (0.49) | 4.50 (4.50) | 1.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-medium-2604 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| mistral/mistral-large-4 | inspect | 0 | 2 | 6 | 0 | 2 | 0.67 (0.33) | 0.67 (0.33) | 0.00 (0.00) | 0.67 (0.33) | 0.50 (0.50) |
| mistral/mistral-large-4 | model | 0 | 2 | 6 | 0 | 0 | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 7.5 | 261356 | 312.5 | 287.6 | 0.1062 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 7.5 | 66923 | 64.6 | 64.0 | 0.1114 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 1064 | 6.5 | 6.0 |  |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 10.2 | 328501 | 229.7 | 207.3 | 0.3636 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 14.3 | 340734 | 92.3 | 91.8 | 0.4359 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 1222 | 10.3 | 10.2 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 6.7 | 223063 | 149.2 | 148.0 | 0.3654 |
| anthropic/claude-opus-5-5 | inspect | 0 | 8.3 | 164293 | 83.4 | 83.3 | 0.4106 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 1896 | 17.6 | 17.1 |  |
| mistral/mistral-small-2603 | inspect | 0 | 2.7 | 19272 | 7.7 | 7.6 | 0.0092 |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 304 | 3.1 | 2.6 |  |
| mistral/mistral-medium-2604 | inspect | 0 | 7.7 | 59484 | 39.1 | 25.9 | 0.1271 |
| mistral/mistral-medium-2604 | model | 0 | 0.0 | 674 | 5.9 | 5.4 |  |
| mistral/mistral-large-4 | inspect | 0 | 18.8 | 318661 | 275.2 | 269.9 | 0.6706 |
| mistral/mistral-large-4 | model | 0 | 0.0 | 1406 | 17.3 | 16.8 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       |   Variant | dsfl-01     | dsfl-02     |
|:----------------------------|:------------|----------:|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code |         0 | 0.33 / 0.78 | 0.00 / 0.08 |
| anthropic/claude-haiku-5-5  | inspect     |         0 | 0.33 / 0.78 | 0.00 / 0.12 |
| anthropic/claude-haiku-5-5  | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code |         0 | 1.00 / 1.00 | 0.67 / 0.67 |
| anthropic/claude-sonnet-5-5 | inspect     |         0 | 0.67 / 0.89 | 0.67 / 0.98 |
| anthropic/claude-sonnet-5-5 | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | claude-code |         0 | 1.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     |         0 | 1.00 / 1.00 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | inspect     |         0 | 0.33 / 0.33 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect     |         0 | 1.00 / 1.00 | 0.00 / 0.01 |
| mistral/mistral-medium-2604 | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |
| mistral/mistral-large-4     | inspect     |         0 | 1.00 / 1.00 | 0.33 / 0.33 |
| mistral/mistral-large-4     | model       |         0 | 0.00 / 0.00 | 0.00 / 0.00 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 1 | 10 of 61 required panden shown; 16 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other), overpass.openstreetmap.fr (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 1 | 17 of 61 required panden shown; 0 places match no pand | api.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 2 | not parseable: no map shown | service.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 2 | not parseable: no map shown | overpass.osm.ch (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 3 | 4 of 61 required panden shown; 8 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), maps.mail.ru (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 3 | 5 of 61 required panden shown; 4 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 1 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | api.pdok.nl (other), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 3 | 57 of 61 required panden shown; 0 places match no pand | api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 1 | 0 of 61 required panden shown; 4 places match no pand | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 2 | 0 of 61 required panden shown; 4 places match no pand | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 3 | 0 of 61 required panden shown; 4 places match no pand | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 1 | 1 of 61 required panden shown; 6 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), www.goudengids.nl (other), www.sporthal.nl (other), arnhem.aqqo.com (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 2 | 0 of 61 required panden shown; 15 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), www.goudengids.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 3 | 1 of 61 required panden shown; 6 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), www.goudengids.nl (other), www.sporthal.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 1 | not parseable: no map shown | service.pdok.nl (authoritative), geo.arnhem.nl (other), www.arcgis.com (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), nominatim.openstreetmap.org (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 3 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (other), geo.arnhem.nl (other), opendata-arnhem.hub.arcgis.com (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 2 | token | 660706 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 1 | token | 658361 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 2 | token | 681860 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 1 | token | 642066 |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 3 | token | 664649 |
