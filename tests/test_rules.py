"""Known good and bad answers per sample, with the score each must get, before any model is assessed."""

import json
import re

import pytest
import shapely

from validators import rules, sources
from validators.rules import Case

TARGETS = {p.parent.name: p.relative_to(rules.TESTSETS_DIR).as_posix() for p in rules.TESTSETS_DIR.glob("*/samples/*/expected.json")}
SAMPLES = set(TARGETS)


def score(sample_id: str, answer: str) -> dict:
    return rules.assess(answer, Case.load(TARGETS[sample_id])).score_value()


def full(correct=1, complete=1.0, invented=0, parseable=1) -> dict:
    return {"correct": correct, "complete": complete, "invented": invented, "parseable": parseable}


def as_json(obj: dict, fenced: bool = True) -> str:
    body = json.dumps(obj, ensure_ascii=False)
    return f"Here is the answer:\n```json\n{body}\n```" if fenced else body


def bag(name: str) -> list[dict]:
    return json.loads(sources.path(f"dsfl/bag-arnhem-sport-{name}").read_text(encoding="utf-8"))["features"]


PANDEN = bag("panden.geojson")
MUST = set(Case.load(TARGETS["dsfl-02"]).expected["must"])
# The point every map gets for a pand: inside it, as an agent that takes the pand's centre or its address would place it.
MUST_POINTS = [shapely.geometry.shape(f["geometry"]).representative_point() for f in PANDEN if f["properties"]["identificatie"] in MUST]
RIVER = (5.905, 51.976)  # in the Rijn, on no pand: a place from another source


def shown(features: list[dict]) -> str:
    """The GeoJSON argument of show_on_map, as the quality scorer hands it to the rule."""
    return json.dumps({"type": "FeatureCollection", "features": features})


def point(lon: float, lat: float) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": {"name": "sporthal"}}


CASES = [
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk", "type": "bassin"}), full()),
    ("imgeo-G04-03", as_json({"objecttype": "Overig bouwwerk", "type": "Bassin"}, fenced=False), full()),
    ("imgeo-G04-03", as_json({"objecttype": "Waterdeel", "type": "zwembad"}), full(0, 0.0, 1)),
    ("imgeo-G04-03", as_json({"objecttype": "Waterdeel", "type": "watervlakte"}), full(0, 0.0, 0)),
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk", "type": "zwembad"}), full(0, 0.5, 1)),
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk"}), full(0, 0.0, 0, 0)),
    ("imgeo-G04-03", "An open-air pool is a Waterdeel.", full(0, 0.0, 0, 0)),
    ("dsfl-01", as_json({"year_built": 1999, "energy_label": "A+", "floor_area_m2": 6921}), full()),
    ("dsfl-01", as_json({"year_built": 1999, "energy_label": "a+", "floor_area_m2": 6921.0}, fenced=False), full()),
    # The area of the thermal zone in EP-Online is not the floor area.
    ("dsfl-01", as_json({"year_built": 1999, "energy_label": "A+", "floor_area_m2": 6630.96}), full(0, 0.6667, 0)),
    ("dsfl-01", as_json({"year_built": 2000, "energy_label": "A", "floor_area_m2": 7000}), full(0, 0.0, 0)),
    ("dsfl-01", as_json({"year_built": "1999", "energy_label": "A+", "floor_area_m2": 6921}), full(0, 0.0, 0, 0)),
    ("dsfl-02", shown([point(p.x, p.y) for p in MUST_POINTS]), full()),
    # Every pand of the extract as a polygon, one of them twice: mixed use may be shown, and a duplicate is not invented.
    ("dsfl-02", shown([*PANDEN, PANDEN[0]]), full()),
    # The verblijfsobjecten as points: each lies in its pand, so a map of verblijfsobjecten is a map of panden.
    ("dsfl-02", shown(bag("verblijfsobjecten.json")), full()),
    # Only the first results of a query.
    ("dsfl-02", shown([point(p.x, p.y) for p in MUST_POINTS[:10]]), full(0, round(10 / len(MUST), 4), 0)),
    ("dsfl-02", shown([*(point(p.x, p.y) for p in MUST_POINTS), point(*RIVER)]), full(0, 1.0, 1)),
    ("dsfl-02", shown([point(p.y, p.x) for p in MUST_POINTS]), full(0, 0.0, len(MUST))),
    ("dsfl-02", shown([]), full(0, 0.0, 0)),
    ("dsfl-02", "", full(0, 0.0, 0, 0)),
    ("dsfl-02", "the sports halls of Arnhem", full(0, 0.0, 0, 0)),
    ("dsfl-02", json.dumps({"type": "Polygon", "coordinates": "here"}), full(0, 0.0, 0, 0)),
]


@pytest.mark.parametrize(("sample_id", "answer", "expected"), CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASES)])
def test_rule_scores(sample_id, answer, expected):
    assert score(sample_id, answer) == expected


def test_every_sample_has_a_known_good_answer():
    assert {c[0] for c in CASES if c[2] == full()} == SAMPLES


def test_rules_are_repeatable():
    sample_id, answer, _ = CASES[2]
    case = Case.load(TARGETS[sample_id])
    first, second = rules.assess(answer, case), rules.assess(answer, case)
    assert (first.score_value(), first.explanation, first.details) == (second.score_value(), second.explanation, second.details)


def test_validators_never_import_inspect():
    offenders = [
        p.name
        for p in rules.TESTSETS_DIR.parent.joinpath("validators").glob("*.py")
        if re.search(r"^\s*(from|import) inspect_ai", p.read_text(encoding="utf-8"), re.M)
    ]
    assert offenders == []


def test_map_details_name_what_is_missing_and_flag_swapped_coordinates():
    case = Case.load(TARGETS["dsfl-02"])
    result = rules.assess(shown([point(p.y, p.x) for p in MUST_POINTS]), case)
    assert (result.details["places"], result.details["swapped"], sorted(result.details["missing"])) == (len(MUST), len(MUST), sorted(MUST))
    result = rules.assess(shown([point(*RIVER)]), case)
    assert (result.details["unmatched"], result.details["swapped"]) == ([list(RIVER)], 0)
