"""Known good and bad answers per sample, with the score each must get, before any model is assessed."""

import json
import re

import pytest
import shapely

from validators import geo, rules, sources
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
    return json.loads(sources.path(f"dsfl/bag-amersfoort-sport-{name}").read_text(encoding="utf-8"))["features"]


def vendored(name: str) -> list[dict]:
    return json.loads(sources.path(f"dsfl/{name}").read_text(encoding="utf-8"))["features"]


def must_points(sample_id: str, features: list[dict]) -> list:
    """The point every map gets for a pand: inside it, as an agent that takes the pand's centre or its address would place it."""
    must = set(Case.load(TARGETS[sample_id]).expected["must"])
    return [shapely.geometry.shape(f["geometry"]).representative_point() for f in features if geo.feature_id(f) in must]


PANDEN = bag("panden.geojson")
MUST = set(Case.load(TARGETS["dsfl-04"]).expected["must"])
SPORT_POINTS = must_points("dsfl-04", PANDEN)
GESLOOPT = vendored("bag-amersfoort-gesloopt.geojson")
DEMOLISHED_POINTS = must_points("dsfl-03", GESLOOPT)
MUST_DEMOLISHED = Case.load(TARGETS["dsfl-03"]).expected["must"]
VOOR_1800 = vendored("bag-amersfoort-voor-1800-panden.geojson")
MUST_1800 = set(Case.load(TARGETS["dsfl-05"]).expected["must"])
HOMES_1800_POINTS = must_points("dsfl-05", VOOR_1800)
NO_HOME_POINTS = [shapely.geometry.shape(f["geometry"]).representative_point() for f in VOOR_1800 if f["id"] not in MUST_1800]
WELLS = vendored("bro-gmw-amersfoort-1km.geojson")
MUST_WELLS = Case.load(TARGETS["dsfl-07"]).expected["must"]
WELL_PLACES = {f["id"]: f["geometry"]["coordinates"] for f in WELLS}
SERIES_EXPECTED = Case.load(TARGETS["dsfl-08"]).expected
SERIES = {
    "points": [{"date": date, "value": value} for date, value in SERIES_EXPECTED["points"].items()],
    "unit": "m",
    "reference_plane": "NAP",
    "connect_gaps": False,
}
SECTION = {
    "arguments": {"modelId": "GEOTOP-v01r6s1-001", "points": [{"x": 153000, "y": 463000}, {"x": 157000, "y": 463000}]},
    "result": {
        "path": [{"x": 153000, "y": 463000}, {"x": 157000, "y": 463000}],
        "plot": {"modelId": "GEOTOP-v01r6s1-001", "colorBy": "unit", "pathLengthMetres": 4000, "formations": [{"rectangleCount": 211}]},
    },
    "image": True,
}
TRACE = {
    "arguments": {"modelId": "GEOTOP-v01r6s1-001", "x": 155000, "y": 463000},
    "result": {
        "location": {"x": 155000, "y": 463000},
        "column": {
            "modelId": "GEOTOP-v01r6s1-001",
            "verticalDatum": "NAP",
            "surfaceElevationNap": 4.369999885559082,
            "layers": [{"unitCode": "NUAAOP" if i < 4 else "NUBX", "top": 4.5 - i * 0.5, "base": 4 - i * 0.5} for i in range(109)],
        },
    },
}
STADHUISPLEIN = (5.38416472, 52.15671963)
METERS_PER_DEGREE_LON = 111_320 * 0.6097  # cos(52.157 degrees)
RIVER = (5.3792, 52.164)  # north of the center, on no pand: a place from another source


def shown(features: list[dict]) -> str:
    """The GeoJSON argument of show_on_map, as the quality scorer hands it to the rule."""
    return json.dumps({"type": "FeatureCollection", "features": features})


def point(lon: float, lat: float) -> dict:
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": {"name": "place"}}


CASES = [
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk", "type": "bassin"}), full()),
    ("imgeo-G04-03", as_json({"objecttype": "Overig bouwwerk", "type": "Bassin"}, fenced=False), full()),
    ("imgeo-G04-03", as_json({"objecttype": "Waterdeel", "type": "zwembad"}), full(0, 0.0, 1)),
    ("imgeo-G04-03", as_json({"objecttype": "Waterdeel", "type": "watervlakte"}), full(0, 0.0, 0)),
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk", "type": "zwembad"}), full(0, 0.5, 1)),
    ("imgeo-G04-03", as_json({"objecttype": "OverigBouwwerk"}), full(0, 0.0, 0, 0)),
    ("imgeo-G04-03", "An open-air pool is a Waterdeel.", full(0, 0.0, 0, 0)),
    ("dsfl-01", as_json({"decade": 1990}), full()),
    ("dsfl-01", as_json({"decade": 1990}, fenced=False), full()),
    # The runner-up decade.
    ("dsfl-01", as_json({"decade": 1980}), full(0, 0.0, 0)),
    ("dsfl-01", as_json({"decade": "1990s"}), full(0, 0.0, 0, 0)),
    ("dsfl-02", as_json({"part": "Vathorst"}), full()),
    ("dsfl-02", as_json({"part": "Vathorst-De Laak"}), full()),
    # De Hoef leads when counting verblijfsobjecten gevormd, which includes permits that have not started.
    ("dsfl-02", as_json({"part": "De Hoef"}), full(0, 0.0, 0)),
    ("dsfl-02", as_json({"part": "Eemkwartier"}), full(0, 0.0, 0)),
    ("dsfl-03", shown([point(p.x, p.y) for p in DEMOLISHED_POINTS]), full()),
    ("dsfl-03", shown(GESLOOPT), full()),
    # Only the first 1000 results of a query.
    ("dsfl-03", shown([point(p.x, p.y) for p in DEMOLISHED_POINTS[:1000]]), full(0, round(1000 / len(DEMOLISHED_POINTS), 4), 0)),
    # Panden that still exist, as the PDOK WFS returns them. 4 of the 78 lie within 15 m of a demolished pand (3 of them required ones); the other 74 match none.
    ("dsfl-03", shown([point(p.x, p.y) for p in SPORT_POINTS]), full(0, round(3 / len(MUST_DEMOLISHED), 4), 74)),
    ("dsfl-04", shown([point(p.x, p.y) for p in SPORT_POINTS]), full()),
    # Every pand of the extract as a polygon, one of them twice: mixed use may be shown, and a duplicate is not invented.
    ("dsfl-04", shown([*PANDEN, PANDEN[0]]), full()),
    # The verblijfsobjecten as points: each lies in its pand, so a map of verblijfsobjecten is a map of panden.
    ("dsfl-04", shown(bag("verblijfsobjecten.json")), full()),
    # Only the first results of a query.
    ("dsfl-04", shown([point(p.x, p.y) for p in SPORT_POINTS[:10]]), full(0, round(10 / len(MUST), 4), 0)),
    ("dsfl-04", shown([*(point(p.x, p.y) for p in SPORT_POINTS), point(*RIVER)]), full(0, 1.0, 1)),
    ("dsfl-04", shown([point(p.y, p.x) for p in SPORT_POINTS]), full(0, 0.0, len(MUST))),
    ("dsfl-04", shown([]), full(0, 0.0, 0)),
    ("dsfl-04", "", full(0, 0.0, 0, 0)),
    ("dsfl-04", "the sports halls of Amersfoort", full(0, 0.0, 0, 0)),
    ("dsfl-04", json.dumps({"type": "Polygon", "coordinates": "here"}), full(0, 0.0, 0, 0)),
    ("dsfl-05", shown([point(p.x, p.y) for p in HOMES_1800_POINTS]), full()),
    # Every old pand, churches and barns too: more than required, but all in the reference.
    ("dsfl-05", shown(VOOR_1800), full()),
    # Old panden without a home only.
    ("dsfl-05", shown([point(p.x, p.y) for p in NO_HOME_POINTS]), full(0, 0.0, 0)),
    ("dsfl-05", shown([point(p.y, p.x) for p in HOMES_1800_POINTS]), full(0, 0.0, len(MUST_1800))),
    ("dsfl-06", as_json({"value": 2.13, "unit": "m", "reference_plane": "NAP"}), full()),
    ("dsfl-06", as_json({"value": 2.134, "unit": "m", "reference_plane": "nap"}, fenced=False), full()),
    ("dsfl-06", as_json({"value": 2.14, "unit": "m", "reference_plane": "NAP"}), full(0, 0.6667, 0)),
    ("dsfl-06", as_json({"value": -3.48, "unit": "m", "reference_plane": "NAP"}), full(0, 0.6667, 0)),
    ("dsfl-06", as_json({"value": 2.13, "unit": "cm", "reference_plane": "maaiveld"}), full(0, 0.3333, 0)),
    ("dsfl-06", as_json({"value": "2.13", "unit": "m", "reference_plane": "NAP"}), full(0, 0.0, 0, 0)),
    ("dsfl-06", as_json({"value": 2.13}), full(0, 0.0, 0, 0)),
    ("dsfl-06", "De stand was 2,13 m NAP.", full(0, 0.0, 0, 0)),
    ("dsfl-07", shown([point(*WELL_PLACES[i]) for i in MUST_WELLS]), full()),
    # Every well of the search: the 44 outside the requested radius are invented.
    ("dsfl-07", shown(WELLS), full(0, 1.0, 44)),
    # The required wells and the removed well at 428 m, which is optional.
    ("dsfl-07", shown([point(*WELL_PLACES[i]) for i in [*MUST_WELLS, "GMW000000133351"]]), full()),
    # The required wells and a well outside the requested radius.
    ("dsfl-07", shown([point(*WELL_PLACES[i]) for i in [*MUST_WELLS, "GMW000000009371"]]), full(0, 1.0, 1)),
    # Coordinates rounded to six decimals, as an agent copies them: about 0.1 m.
    ("dsfl-07", shown([point(*(round(c, 6) for c in WELL_PLACES[i])) for i in MUST_WELLS]), full()),
    # Only the nearest 6.
    ("dsfl-07", shown([point(*WELL_PLACES[i]) for i in MUST_WELLS[:6]]), full(0, 0.5, 0)),
    ("dsfl-07", shown([*(point(*WELL_PLACES[i]) for i in MUST_WELLS), point(*STADHUISPLEIN)]), full(0, 1.0, 1)),
    ("dsfl-07", shown([point(*STADHUISPLEIN)]), full(0, 0.0, 1)),
    ("dsfl-07", shown([point(WELL_PLACES[i][1], WELL_PLACES[i][0]) for i in MUST_WELLS]), full(0, 0.0, len(MUST_WELLS))),
    # Two distinct places can be assigned to the twins even if both are nearer the same well.
    ("dsfl-07", shown([point(WELL_PLACES[i][0] + 3 / METERS_PER_DEGREE_LON, WELL_PLACES[i][1]) for i in MUST_WELLS]), full()),
    ("dsfl-07", shown([point(*WELL_PLACES[i]) for i in MUST_WELLS if i != "GMW000000009391"]), full(0, round(11 / 12, 4), 0)),
    ("dsfl-07", shown([point(WELL_PLACES[i][0] + 10 / METERS_PER_DEGREE_LON, WELL_PLACES[i][1]) for i in MUST_WELLS]), full(0, 0.0, len(MUST_WELLS))),
    ("dsfl-07", shown([point(*(round(c, 5) for c in WELL_PLACES[i])) for i in MUST_WELLS]), full()),
    ("dsfl-07", shown([]), full(0, 0.0, 0)),
    ("dsfl-08", json.dumps(SERIES), full()),
    ("dsfl-09", as_json({"surface": 4.37, "unit": "m", "reference_plane": "NAP", "top_unit": "NUAAOP", "next_unit": "NUBX"}), full()),
    ("dsfl-10", as_json({"lithoclass": "ZM", "probability": 0.62}), full()),
    ("dsfl-11", as_json({"present": True}), full()),
    ("dsfl-12", as_json({"available": False, "probability": None}), full()),
    ("dsfl-13", json.dumps(SECTION), full()),
    ("dsfl-14", json.dumps(TRACE), full()),
    ("dsfl-15", as_json({"line_of_sight_only": True, "proves_no_connection": False}), full()),
    ("dsfl-10", as_json({"lithoclass": "ZM", "probability": 0.78}), full(0, 0.5, 0)),
    ("dsfl-11", as_json({"present": False}), full(0, 0, 0)),
    ("dsfl-12", as_json({"available": True, "probability": 0.62}), full(0, 0, 1)),
    ("dsfl-15", as_json({"line_of_sight_only": True, "proves_no_connection": True}), full(0, 0.5, 0)),
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


def test_series_scores_dates_values_gaps_and_metadata():
    def assess(**changes):
        return rules.assess(json.dumps({**SERIES, **changes}), Case.load(TARGETS["dsfl-08"]))

    points = SERIES["points"]
    assert assess(points=points[1:]).score_value() == full(0, round(10 / 11, 4), 0)
    assert assess(points=[*points, {"date": "2023-01-21", "value": 3.0}]).score_value() == full(0, 1, 1)
    assert assess(points=[*points, points[-1]]).score_value() == full(0, 1, 1)
    assert assess(points=[{**p, "value": 2.9} if p["date"] == "2023-01-15" else p for p in points]).score_value() == full(0, round(10 / 11, 4), 1)
    assert assess(points=[{**p, "value": 50} if p["date"] == "2023-01-10" else p for p in points]).score_value() == full(0, round(10 / 11, 4), 0)
    assert assess(points=list(reversed(points))).score_value() == full(0, 1, 0)
    assert assess(unit="cm").score_value() == full(0, 1, 0)
    assert assess(reference_plane="maaiveld").score_value() == full(0, 1, 0)
    assert assess(connect_gaps=True).score_value() == full(0, 1, 0)
    assert assess(points=[{"date": "2023-02-30", "value": 2}]).score_value() == full(0, 0, 0, 0)
    assert assess(points=[{"date": "2023-01-10", "value": float("nan")}]).score_value() == full(0, 0, 0, 0)
    assert rules.assess("", Case.load(TARGETS["dsfl-08"])).score_value() == full(0, 0, 0, 0)


def test_subsurface_plot_and_trace_check_result_not_just_call():
    from copy import deepcopy

    section = Case.load(TARGETS["dsfl-13"])
    assert not rules.assess("", section).parseable
    for edit in (
        lambda d: d.update(image=False),
        lambda d: d["arguments"].update(modelId="REGIS-v02r2s3-001"),
        lambda d: d["result"]["plot"].update(pathLengthMetres=3999),
        lambda d: d["result"]["plot"].update(colorBy="lithoClass"),
        lambda d: d["result"]["plot"].update(formations=[]),
        lambda d: d["result"]["path"][0].update(y=463100),
    ):
        data = deepcopy(SECTION)
        edit(data)
        assert not rules.assess(json.dumps(data), section).correct
    trace = Case.load(TARGETS["dsfl-14"])
    for edit in (
        lambda d: d["arguments"].update(x=155001),
        lambda d: d["result"]["column"].update(verticalDatum="maaiveld"),
        lambda d: d["result"]["column"]["layers"].pop(),
        lambda d: d["result"]["column"]["layers"][3].update(base=1),
    ):
        data = deepcopy(TRACE)
        edit(data)
        assert not rules.assess(json.dumps(data), trace).correct


def test_point_map_can_score_a_zero_result_selection():
    original = Case.load(TARGETS["dsfl-07"])
    case = Case(original.sample_id, {**original.expected, "must": [], "optional": []}, original.directory)
    assert rules.assess(shown([]), case).score_value() == full()
    assert rules.assess(shown([point(*WELL_PLACES[MUST_WELLS[0]])]), case).score_value() == full(0, 1, 1)


def test_validators_never_import_inspect():
    offenders = [
        p.name
        for p in rules.TESTSETS_DIR.parent.joinpath("validators").glob("*.py")
        if re.search(r"^\s*(from|import) inspect_ai", p.read_text(encoding="utf-8"), re.M)
    ]
    assert offenders == []


def test_map_details_name_what_is_missing_and_flag_swapped_coordinates():
    case = Case.load(TARGETS["dsfl-04"])
    result = rules.assess(shown([point(p.y, p.x) for p in SPORT_POINTS]), case)
    assert (result.details["places"], result.details["swapped"], sorted(result.details["missing"])) == (len(MUST), len(MUST), sorted(MUST))
    result = rules.assess(shown([point(*RIVER)]), case)
    assert (result.details["unmatched"], result.details["swapped"]) == ([list(RIVER)], 0)
    result = rules.assess(shown([*PANDEN, point(*RIVER)]), case)
    assert result.details["shown"] == sorted(f["properties"]["identificatie"] for f in PANDEN)
