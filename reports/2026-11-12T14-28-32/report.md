# airco-harness report

Logs: `reports/2026-11-12T14-28-32/logs/logs`. Runs: 135, of which with an error: 0, and at a limit: 17.

Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. A run at a limit counts with the scores it got, a run with an error is left out.

## Quality metrics per model and variant

| Model | Agent | Variant | Samples | Runs | Error | Limit | correct | complete | invented | parseable | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 5 | 15 | 0 | 6 | 0.07 (0.07) | 0.08 (0.06) | 0.20 (0.20) | 0.60 (0.24) | 0.20 (0.20) |
| anthropic/claude-haiku-5-5 | inspect | 0 | 5 | 15 | 0 | 1 | 0.20 (0.13) | 0.24 (0.12) | 2.40 (1.47) | 0.93 (0.07) | 0.00 (0.00) |
| anthropic/claude-haiku-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.20 (0.20) | 0.20 (0.20) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 5 | 15 | 0 | 4 | 0.20 (0.13) | 0.26 (0.12) | 4.93 (3.81) | 0.73 (0.19) | 0.20 (0.20) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 5 | 15 | 0 | 3 | 0.33 (0.21) | 0.36 (0.20) | 1.73 (0.78) | 0.80 (0.13) | 0.07 (0.07) |
| anthropic/claude-sonnet-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.27 (0.19) | 0.27 (0.19) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |
| anthropic/claude-opus-5-5 | claude-code | 0 | 5 | 15 | 0 | 2 | 0.33 (0.21) | 0.60 (0.17) | 0.47 (0.33) | 0.87 (0.13) | 0.40 (0.24) |
| anthropic/claude-opus-5-5 | inspect | 0 | 5 | 15 | 0 | 1 | 0.40 (0.24) | 0.70 (0.18) | 0.80 (0.72) | 0.93 (0.07) | 0.40 (0.24) |
| anthropic/claude-opus-5-5 | model | 0 | 5 | 15 | 0 | 0 | 0.40 (0.24) | 0.40 (0.24) | 0.00 (0.00) | 0.40 (0.24) | 0.00 (0.00) |

## Trajectory metrics and cost per model and variant

| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | 8.1 | 309969 | 258.7 | 250.2 | 0.3896 |
| anthropic/claude-haiku-5-5 | inspect | 0 | 8.5 | 164773 | 33.2 | 33.0 | 0.2060 |
| anthropic/claude-haiku-5-5 | model | 0 | 0.0 | 892 | 5.3 | 5.3 | 0.0021 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | 7.3 | 266490 | 288.5 | 283.6 | 1.0043 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | 32.6 | 333089 | 125.6 | 125.5 | 0.8014 |
| anthropic/claude-sonnet-5-5 | model | 0 | 0.0 | 1335 | 12.0 | 11.9 | 0.0487 |
| anthropic/claude-opus-5-5 | claude-code | 0 | 6.7 | 244422 | 186.0 | 185.5 | 1.1415 |
| anthropic/claude-opus-5-5 | inspect | 0 | 17.3 | 274341 | 172.9 | 172.7 | 1.4184 |
| anthropic/claude-opus-5-5 | model | 0 | 0.0 | 1368 | 14.6 | 14.5 | 0.0666 |

## `correct` / `complete` per sample (mean over epochs)

| Model                       | Agent       |   Variant | dsfl-01     | dsfl-02     | dsfl-03     | dsfl-04     | dsfl-05     |
|:----------------------------|:------------|----------:|:------------|:------------|:------------|:------------|:------------|
| anthropic/claude-haiku-5-5  | claude-code |         0 | 0.00 / 0.00 | 0.33 / 0.33 | 0.00 / 0.00 | 0.00 / 0.07 | 0.00 / 0.00 |
| anthropic/claude-haiku-5-5  | inspect     |         0 | 0.33 / 0.33 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.09 | 0.00 / 0.10 |
| anthropic/claude-haiku-5-5  | model       |         0 | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-sonnet-5-5 | claude-code |         0 | 0.33 / 0.33 | 0.67 / 0.67 | 0.00 / 0.00 | 0.00 / 0.04 | 0.00 / 0.26 |
| anthropic/claude-sonnet-5-5 | inspect     |         0 | 0.67 / 0.67 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.11 | 0.00 / 0.02 |
| anthropic/claude-sonnet-5-5 | model       |         0 | 0.33 / 0.33 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| anthropic/claude-opus-5-5   | claude-code |         0 | 1.00 / 1.00 | 0.67 / 0.67 | 0.00 / 0.29 | 0.00 / 0.13 | 0.00 / 0.93 |
| anthropic/claude-opus-5-5   | inspect     |         0 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.46 | 0.00 / 0.11 | 0.00 / 0.95 |
| anthropic/claude-opus-5-5   | model       |         0 | 1.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |

## Map questions per run

On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart.

| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (other), overpass-api.de (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 1 | 1 of 2745 required panden shown; 4 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 3 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-03 | 3 | 0 of 2745 required panden shown; 2 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 1 | 4 of 78 required panden shown; 0 places match no pand | nominatim.openstreetmap.org (other), photon.komoot.io (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 1 | 7 of 78 required panden shown; 2 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 2 | 6 of 78 required panden shown; 1 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), photon.komoot.io (other), geocoding.geo.admin.nl (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 2 | 7 of 78 required panden shown; 2 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-04 | 3 | 7 of 78 required panden shown; 2 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-04 | 3 | 8 of 78 required panden shown; 2 places match no pand | nominatim.openstreetmap.org (other), photon.komoot.io (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 1 | not parseable: no map shown | nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 1 | 28 of 195 required panden shown; 12 places match no pand | nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 2 | not parseable: no map shown | nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 2 | 15 of 195 required panden shown; 6 places match no pand | nl.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-haiku-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 3 | not parseable: no map shown | nl.wikipedia.org (other) |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 3 | 18 of 195 required panden shown; 6 places match no pand | nl.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 1 | not parseable: no map shown | www.destadamersfoort.nl (other), www.amersfoort.nl (other), amersfoort.nieuws.nl (other), www.hardnieuws.nl (other), www.amersfoorttoenennu.nl (other), eijva.nl (other), focusbv.com (other), www.rtvutrecht.nl (other), api.pdok.nl (other), www.habion.nl (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 2 | 1 of 2745 required panden shown; 10 places match no pand | regioonline.nl (other), www.amersfoorttoenennu.nl (other), nominatim.openstreetmap.org (other), www.habion.nl (other), www.destadamersfoort.nl (other), rtvutrecht.nl (other), photon.komoot.io (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 3 | not parseable: no map shown | api.pdok.nl (other), www.destadamersfoort.nl (other), www.oudtzwanenburg.nl (other), slopenensaneren.nl (other), nominatim.openstreetmap.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 3 | not parseable: no map shown | api.pdok.nl (authoritative), service.pdok.nl (authoritative) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 1 | 9 of 78 required panden shown; 4 places match no pand | www.google.com (other), duckduckgo.com (other), www.sporthal.nl (other), www.amersfoort.nl (other), sro.nl (other), www.oozo.nl (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 1 | 0 of 78 required panden shown; 6 places match no pand | nominatim.openstreetmap.org (other), overpass.kumi.systems (other), overpass-api.de (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 2 | 7 of 78 required panden shown; 1 places match no pand | sro.nl (other), overpass.kumi.systems (other), overpass-api.de (other), nominatim.openstreetmap.org (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 2 | 2 of 78 required panden shown; 9 places match no pand | nominatim.openstreetmap.org (other), api.pdok.nl (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-04 | 3 | 9 of 78 required panden shown; 0 places match no pand | www.google.com (other), duckduckgo.com (other), www.sporthal.nl (other), www.amersfoort.nl (other), sro.nl (other), photon.komoot.io (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-04 | 3 | 7 of 78 required panden shown; 0 places match no pand | nominatim.openstreetmap.org (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 1 | 4 of 195 required panden shown; 4 places match no pand | query.wikidata.org (other), www.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 1 | 76 of 195 required panden shown; 31 places match no pand | query.wikidata.org (other), www.wikidata.org (other), nl.wikipedia.org (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 2 | 5 of 195 required panden shown; 4 places match no pand | en.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 2 | 77 of 195 required panden shown; 28 places match no pand | overpass-api.de (other), nl.wikipedia.org (other) |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-05 | 3 | 4 of 195 required panden shown; 3 places match no pand | nl.wikipedia.org (other), en.wikipedia.org (other), query.wikidata.org (other) |
| anthropic/claude-sonnet-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 3 | not parseable: no map shown | query.wikidata.org (other), www.wikidata.org (other), overpass-api.de (other), overpass.kumi.systems (other), nl.wikipedia.org (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 1 | 2006 of 2745 required panden shown; 5 places match no pand | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), data.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 1 | not parseable: no map shown | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 2 | 1756 of 2745 required panden shown; 6 places match no pand | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 2 | not parseable: no map shown | service.pdok.nl (authoritative), api.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-03 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 3 | not parseable: no map shown | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 3 | 2376 of 2745 required panden shown; 5 places match no pand | service.pdok.nl (authoritative), api.labs.kadaster.nl (other), bag.basisregistraties.overheid.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 1 | 6 of 78 required panden shown; 0 places match no pand | overpass-api.de (other), overpass.kumi.systems (other), www.sro.nl (other), api.pdok.nl (other), sro.nl (other) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 1 | 7 of 78 required panden shown; 2 places match no pand | api.pdok.nl (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 2 | 10 of 78 required panden shown; 0 places match no pand | overpass-api.de (other), photon.komoot.io (other) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 2 | 10 of 78 required panden shown; 0 places match no pand | overpass.kumi.systems (other), nominatim.openstreetmap.org (other), www.google.com (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-04 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-04 | 3 | 10 of 78 required panden shown; 1 places match no pand | api.pdok.nl (other), sro.nl (other), amerena.nl (other) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-04 | 3 | 13 of 78 required panden shown; 0 places match no pand | overpass-api.de (other), nominatim.openstreetmap.org (other), overpass.kumi.systems (other), maps.mail.ru (other), overpass.private.coffee (other) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 1 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 1 | 192 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 1 | 181 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 2 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 2 | 189 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 2 | 181 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | model | 0 | dsfl-05 | 3 | not parseable: no map shown | nothing |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-05 | 3 | 175 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-05 | 3 | 181 of 195 required panden shown; 0 places match no pand | service.pdok.nl (authoritative) |

## Runs with an error or at a limit

| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |
| --- | --- | --- | --- | --- | --- | --- |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 1 | time | 567231 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 2 | token | 623954 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-03 | 3 | token | 606116 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 1 | token | 617935 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 2 | token | 627614 |
| anthropic/claude-haiku-5-5 | claude-code | 0 | dsfl-05 | 3 | token | 653814 |
| anthropic/claude-haiku-5-5 | inspect | 0 | dsfl-05 | 3 | token | 658925 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-01 | 2 | token | 651175 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 1 | token | 625064 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 1 | time | 574496 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 2 | message | 536407 |
| anthropic/claude-sonnet-5-5 | inspect | 0 | dsfl-03 | 3 | token | 624011 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-03 | 3 | message | 534001 |
| anthropic/claude-sonnet-5-5 | claude-code | 0 | dsfl-05 | 3 | token | 605835 |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 1 | token | 617279 |
| anthropic/claude-opus-5-5 | claude-code | 0 | dsfl-03 | 2 | token | 622331 |
| anthropic/claude-opus-5-5 | inspect | 0 | dsfl-03 | 3 | token | 660167 |
