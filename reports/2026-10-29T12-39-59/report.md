# airco-harness report

Logs: `logs/2026-10-29T12-39-59`. Runs: 45, of which with an error: 0, and at a limit: 2.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 0.33 () | 0.42 () | 4.33 () | 1.00 () | 0.67 () |
| anthropic/claude-haiku-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.02 () | 0.00 () | 0.33 () | 0.00 () |
| anthropic/claude-haiku-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| anthropic/claude-opus-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-opus-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 1 | 3 | 0 | 0 | 0.67 () | 1.00 () | 0.33 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 1 | 3 | 0 | 0 | 1.00 () | 1.00 () | 0.00 () | 1.00 () | 1.00 () |
| anthropic/claude-sonnet-5-5 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-large-4 | inspect | 0 | 1 | 3 | 0 | 1 | 0.00 () | 0.01 () | 10.33 () | 0.67 () | 0.67 () |
| mistral/mistral-large-4 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-medium-2604 | inspect | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.01 () | 6.67 () | 1.00 () | 0.00 () |
| mistral/mistral-medium-2604 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |
| mistral/mistral-small-2603 | inspect | 0 | 1 | 3 | 0 | 1 | 0.00 () | 0.00 () | 4.00 () | 1.00 () | 0.00 () |
| mistral/mistral-small-2603 | model | 0 | 1 | 3 | 0 | 0 | 0.00 () | 0.00 () | 0.00 () | 0.00 () | 0.00 () |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 9.7 | 308475 | 178.7 | 172.4 | 0.0316 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 9.7 | 81115 | 81.7 | 81.7 |  |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 1617 | 9.2 | 9.2 |  |
| anthropic/claude-opus-5-5 | claude-code | 0 | 5.3 | 231531 | 162.5 | 141.2 | 0.5401 |
| anthropic/claude-opus-5-5 | inspect | 0 | 8.7 | 374959 | 166.1 | 166.0 | 0.8210 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 3406 | 29.3 | 29.2 |  |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 8.3 | 298221 | 142.4 | 123.6 | 0.3645 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 13.0 | 497916 | 137.2 | 137.0 | 0.4561 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 1687 | 12.8 | 12.7 |  |
| mistral/mistral-large-4 | inspect | 0 | 34.7 | 342181 | 312.8 | 188.5 |  |
| mistral/mistral-large-4 | model | 0 | 0.0 | 1267 | 13.5 | 13.4 |  |
| mistral/mistral-medium-2604 | inspect | 0 | 12.7 | 116449 | 61.5 | 61.4 |  |
| mistral/mistral-medium-2604 | model | 0 | 0.0 | 1329 | 12.3 | 12.2 |  |
| mistral/mistral-small-2603 | inspect | 0 | 6.3 | 108564 | 20.7 | 20.5 |  |
| mistral/mistral-small-2603 | model | 0 | 0.0 | 677 | 5.5 | 5.4 |  |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       |   Variant | dsfl-02     |
|:----------------------------|:------------|----------:|:------------|
| anthropic/claude-haiku-5-5  | claude-code |         0 | 0.33 / 0.42 |
| anthropic/claude-haiku-5-5  | inspect     |         0 | 0.00 / 0.02 |
| anthropic/claude-haiku-5-5  | model       |         0 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | claude-code |         0 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | inspect     |         0 | 1.00 / 1.00 |
| anthropic/claude-opus-5-5   | model       |         0 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code |         0 | 0.67 / 1.00 |
| anthropic/claude-sonnet-5-5 | inspect     |         0 | 1.00 / 1.00 |
| anthropic/claude-sonnet-5-5 | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-large-4     | inspect     |         0 | 0.00 / 0.01 |
| mistral/mistral-large-4     | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-medium-2604 | inspect     |         0 | 0.00 / 0.01 |
| mistral/mistral-medium-2604 | model       |         0 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | inspect     |         0 | 0.00 / 0.00 |
| mistral/mistral-small-2603  | model       |         0 | 0.00 / 0.00 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 1 | not parseable: no map shown | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 2 | not parseable: no map shown | overpass-api.de (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 2 | 7 of 61 required panden shown; 4 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other), overpass.openstreetmap.fr (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-02 | 3 | 3 of 61 required panden shown; 0 places match no pand | nominatim.openstreetmap.org (other), overpass-api.de (other) |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-02 | 3 | 8 of 61 required panden shown; 9 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other), overpass.openstreetmap.fr (other), lz4.overpass-api.de (other), service.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), www.opengis.net (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), www.opengis.net (other) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 1 places match no pand | service.pdok.nl (authoritative), api.pdok.nl (other), www.opengis.net (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 1 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), api.pdok.nl (other), www.opengis.net (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 2 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | api.pdok.nl (authoritative), service.pdok.nl (authoritative), www.opengis.net (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-02 | 3 | 61 of 61 required panden shown; 0 places match no pand | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 1 | 1 of 61 required panden shown; 14 places match no pand | www.sportbedrijfarnhem.nl (other), www.sporthal.nl (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 2 | not parseable: no map shown | geoforum.nl (other), api.pdok.nl (authoritative), geo.arnhem.nl (other), bag.basisregistraties.overheid.nl (authoritative), overpass-api.de (other), data.pdok.nl (other), bag2.basisregistraties.overheid.nl (other), data.labs.kadaster.nl (other), wouterbeek.github.io (other), lvbag.github.io (other) |
| mistral/mistral-large-4 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 3 | 0 of 61 required panden shown; 17 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), geo.arnhem.nl (other), service.pdok.nl (authoritative), www.bewegeninarnhem.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 1 | 0 of 61 required panden shown; 7 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), www.goudengids.nl (other), www.locaties.nl (other), sporthal.nl (other), papendal.nl (other), opendata.arnhem.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 2 | 1 of 61 required panden shown; 7 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other), www.goudengids.nl (other), www.sporthal.nl (other), www.locaties.nl (other) |
| mistral/mistral-medium-2604 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-medium-2604 | inspect | 0 | dsfl-02 | 3 | 0 of 61 required panden shown; 6 places match no pand | www.sportbedrijfarnhem.nl (other), www.sportinarnhem.nl (other) |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 1 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 1 | 0 of 61 required panden shown; 4 places match no pand | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 2 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 2 | 0 of 61 required panden shown; 4 places match no pand | nothing |
| mistral/mistral-small-2603 | model | 0 | dsfl-02 | 3 | not parseable: no map shown | nothing |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 3 | 0 of 61 required panden shown; 4 places match no pand | nothing |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| mistral/mistral-large-4 | inspect | 0 | dsfl-02 | 2 | token | 613099 |
| mistral/mistral-small-2603 | inspect | 0 | dsfl-02 | 2 | message | 272648 |
