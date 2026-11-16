"""Scoring rules: compare a model answer with the expected outcome of a sample.

Each rule fills four of the five score keys (`source` comes from the tool log, see
airco_harness.scorers). A rule never raises on a malformed answer: it reports
parseable 0 and correct 0 instead. Rules are selected by the "rule" key in a
case's expected.json: `fields` for a JSON answer, `map` for what the agent
showed on the map, `series` for data passed to a plot, and `section` and
`trace` for selected properties of subsurface tool results.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from jsonschema import validators

from . import answers, geo, series
from .refmodel import ReferenceModel, normalize

TESTSETS_DIR = Path(__file__).resolve().parent.parent / "testsets"


@dataclass(frozen=True)
class Assessment:
    correct: bool
    complete: float
    invented: int
    parseable: bool
    explanation: str
    details: dict = field(default_factory=dict)

    def score_value(self) -> dict[str, int | float]:
        return {
            "correct": int(self.correct),
            "complete": round(self.complete, 4),
            "invented": self.invented,
            "parseable": int(self.parseable),
        }


def unparseable(reason: str, details: dict | None = None) -> Assessment:
    return Assessment(False, 0.0, 0, False, f"not parseable: {reason}", details or {})


@dataclass(frozen=True)
class Case:
    """Expected outcome of one sample, read from testsets/<name>/samples/<id>/."""

    sample_id: str
    expected: dict
    directory: Path

    @classmethod
    def load(cls, target: str) -> Case:
        """`target` is relative to testsets/, as the sample target that dataset.load sets."""
        file = TESTSETS_DIR / target
        return cls(file.parent.name, json.loads(file.read_text(encoding="utf-8")), file.parent)

    @property
    def rule(self) -> str:
        return self.expected["rule"]

    def answer_schema(self) -> dict | None:
        name = self.expected.get("answer_schema")
        return json.loads((self.directory / name).read_text(encoding="utf-8")) if name else None


@cache
def refmodel() -> ReferenceModel:
    return ReferenceModel.load()


def _json_answer(answer: str, case: Case) -> tuple[object | None, Assessment | None, dict]:
    """The JSON object in the answer that conforms to the answer schema, or the assessment that says why there is none."""
    try:
        data = json.loads(answers.json_text(answer))
    except ValueError:
        return None, unparseable("no JSON"), {}
    schema = case.answer_schema() or {"type": "object"}
    errors = sorted(f"{e.json_path}: {e.message}" for e in validators.validator_for(schema)(schema).iter_errors(data))
    details = {"schema_errors": errors}
    if errors:
        return None, unparseable("JSON does not match the answer schema", details), details
    return data, None, details


def _same(answer: object, expected: object) -> bool:
    if isinstance(expected, bool) or isinstance(answer, bool):
        return answer is expected
    if isinstance(expected, (int, float)) and isinstance(answer, (int, float)):
        return answer == expected
    return normalize(str(answer)) == normalize(str(expected))


def _accepted(want: object) -> list[object]:
    """`want` is a literal, alternatives, or a numeric value with tolerance."""
    return want["one_of"] if isinstance(want, dict) and "one_of" in want else [want]


def _matches(answer: object, want: object) -> bool:
    if isinstance(want, dict) and "tolerance" in want:
        return isinstance(answer, (int, float)) and not isinstance(answer, bool) and abs(answer - want["value"]) <= want["tolerance"]
    return _same(answer, want)


def _invented_terms(values: list) -> list[str]:
    known = refmodel().all_terms

    def is_known(term: str) -> bool:
        t = normalize(term)
        return t in known or t.split(":")[-1] in known

    return sorted({v for v in values if isinstance(v, str) and not is_known(v)})


def rule_fields(answer: str, case: Case) -> Assessment:
    """Named fields, with optional known-term and explicitly invented-value checks."""
    data, failure, details = _json_answer(answer, case)
    if failure:
        return failure
    fields: dict[str, object] = case.expected["expected"]
    wrong = {key: {"expected": want, "given": data.get(key)} for key, want in fields.items() if not any(_matches(data.get(key), a) for a in _accepted(want))}
    term_values = [data.get(k) for k in case.expected.get("term_fields", []) if k in wrong]
    invented = _invented_terms(term_values)
    invented_fields = [key for key in case.expected.get("invented_fields", []) if key in wrong]
    details |= {"wrong": wrong, "invented_terms": invented, "invented_fields": invented_fields}
    complete = 1 - len(wrong) / len(fields)
    return Assessment(not wrong and not invented and not invented_fields, complete, len(invented) + len(invented_fields), True,
                      f"wrong: {sorted(wrong)}; invented: {invented}; invented fields: {invented_fields}", details)  # fmt: skip


def rule_map(answer: str, case: Case) -> Assessment:
    """Places on the map, matched to the features of the reference extract.

    `answer` is the GeoJSON the agent passed to show_on_map, or that the map loaded from its url, or "" when it showed no map.
    """
    if not answer.strip():
        return unparseable("no map shown")
    try:
        places = geo.points(json.loads(answer))
    except ValueError as error:
        return unparseable(f"not GeoJSON: {error}")
    reference = geo.Reference.load(case.expected["reference"])
    tolerance = case.expected["tolerance_m"]
    must = set(case.expected["must"])
    if "optional" in case.expected:
        identifiers = reference.assign_points(places, tolerance, must | set(case.expected["optional"]))
    else:
        identifiers = [reference.nearest(place, tolerance) for place in places]
    matched = list(zip(places, identifiers))
    shown = {identifier for _, identifier in matched if identifier}
    missing = sorted(must - shown)
    unmatched = [[round(place.x, 6), round(place.y, 6)] for place, identifier in matched if identifier is None]
    details = {"places": len(places), "shown": sorted(shown), "missing": missing, "unmatched": unmatched,
               "swapped": sum(geo.swapped(place) for place, _ in matched)}  # fmt: skip
    complete = 1 - len(missing) / len(must) if must else 1.0
    return Assessment(not missing and not unmatched, complete, len(unmatched), True,
                      f"{len(must) - len(missing)} of {len(must)} required features shown; {len(unmatched)} places match no allowed feature", details)  # fmt: skip


def rule_series(answer: str, case: Case) -> Assessment:
    """Score the daily values and gaps passed to the plot, not its rendered image."""
    if not answer.strip():
        return unparseable("no plot shown")
    try:
        data = json.loads(answer)
    except ValueError:
        return unparseable("no JSON plot data")
    error = series.validate(data)
    if error:
        return unparseable(error)
    wanted = case.expected["points"]
    tolerance = case.expected["tolerance"]
    by_date = {}
    extras = []
    for point in data["points"]:
        date, value = point["date"], point["value"]
        if date in by_date or date not in wanted:
            extras.append(date)
        else:
            by_date[date] = value
    missing, wrong, filled_gaps = [], [], []
    for date, value in wanted.items():
        if date not in by_date:
            missing.append(date)
        elif value is None:
            if by_date[date] is not None:
                filled_gaps.append(date)
        elif not _matches(by_date[date], {"value": value, "tolerance": tolerance}):
            wrong.append(date)
    dates = [point["date"] for point in data["points"]]
    ordered = dates == sorted(dates)
    metadata_wrong = [key for key in ("unit", "reference_plane", "connect_gaps") if not _same(data[key], case.expected[key])]
    matched = len(wanted) - len(missing) - len(wrong) - len(filled_gaps)
    invented = len(extras) + len(filled_gaps)
    details = {"missing": missing, "wrong": wrong, "filled_gaps": filled_gaps, "extra": extras, "metadata_wrong": metadata_wrong, "ordered": ordered}
    complete = matched / len(wanted) if wanted else 1.0
    correct = not missing and not wrong and not invented and not metadata_wrong and ordered
    return Assessment(
        correct,
        complete,
        invented,
        True,
        f"{matched} of {len(wanted)} days match; {invented} invented; metadata wrong: {metadata_wrong}; ordered: {ordered}",
        details,
    )


def _tool_payload(answer: str) -> tuple[dict | None, Assessment | None]:
    try:
        data = json.loads(answer)
    except ValueError:
        return None, unparseable("no successful tool result")
    if not isinstance(data, dict) or not isinstance(data.get("arguments"), dict) or not isinstance(data.get("result"), dict):
        return None, unparseable("malformed tool result")
    return data, None


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _geojson_positions(value: object, kind: str) -> list | None:
    if not isinstance(value, dict) or value.get("type") != kind:
        return None
    coordinates = value.get("coordinates")
    positions = [coordinates] if kind == "Point" else coordinates
    if not isinstance(positions, list) or not positions:
        return None
    if kind == "LineString" and not 2 <= len(positions) <= 50:
        return None
    if any(
        not isinstance(p, list) or len(p) != 2 or not all(_number(c) for c in p) or not -180 <= p[0] <= 180 or not -90 <= p[1] <= 90
        for p in positions
    ):
        return None
    return positions


def _rd_path(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(p, dict) and _number(p.get("x")) and _number(p.get("y")) for p in value)


def _same_rd_path(actual: list, expected: list) -> bool:
    return len(actual) == len(expected) and all(abs(a[k] - b[k]) <= 0.05 for a, b in zip(actual, expected) for k in ("x", "y"))


def _georeferenced_positions(result: dict, positions: list) -> list | None:
    reference = result.get("georeference")
    if not isinstance(reference, dict) or not _rd_path(reference.get("modelPositions")):
        return None
    inputs = reference.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != len(positions) or len(reference["modelPositions"]) != len(positions):
        return None
    if any(
        not isinstance(p, dict)
        or any(not _number(p.get(k)) or abs(p[k] - coordinate) > 1e-8 for k, coordinate in zip(("longitude", "latitude"), coordinates))
        for p, coordinates in zip(inputs, positions)
    ):
        return None
    return reference["modelPositions"]


def rule_section(answer: str, case: Case) -> Assessment:
    """Assess the requested plot call and its metadata; the plot is not a paged section."""
    data, failure = _tool_payload(answer)
    if failure:
        return failure
    args, envelope = data["arguments"], data["result"]
    positions = _geojson_positions(args.get("path"), "LineString")
    result = envelope.get("result")
    if positions is None or not isinstance(result, dict):
        return unparseable("malformed GeoJSON section plot")
    model_positions = _georeferenced_positions(envelope, positions)
    plot, path = result.get("plot"), result.get("path")
    if not isinstance(plot, dict) or not _rd_path(path) or len(path) < 2 or model_positions is None:
        return unparseable("malformed section plot")
    if not _number(plot.get("pathLengthMetres")):
        return unparseable("malformed section path or length")
    want = case.expected
    endpoints = want["path"]["coordinates"]
    formations = plot.get("formations")
    checks = {
        "path": all(abs(a - b) <= 1e-8 for p, q in zip((positions[0], positions[-1]), endpoints) for a, b in zip(p, q))
        and _same_rd_path(path, model_positions)
        and _same_rd_path([path[0], path[-1]], want["model_path"])
        and all(abs(p["y"] - want["model_path"][0]["y"]) <= 0.05 for p in path)
        and all(a["x"] <= b["x"] for a, b in zip(path, path[1:])),
        "model": args.get("modelId") == plot.get("modelId") == want["model_id"],
        "color": args.get("colorBy", "unit") == plot.get("colorBy") == want["color_by"],
        "length": abs(plot["pathLengthMetres"] - want["length_m"]) <= 0.01,
        "image": data.get("image") is True,
        "geometry": isinstance(formations, list)
        and any(isinstance(f, dict) and _number(f.get("rectangleCount")) and f["rectangleCount"] > 0 for f in formations),
    }
    wrong = [key for key, ok in checks.items() if not ok]
    return Assessment(not wrong, (len(checks) - len(wrong)) / len(checks), 0, True, f"section checks failed: {wrong}", {"wrong": wrong})


def rule_trace(answer: str, case: Case) -> Assessment:
    """Assess the returned column's location, upper units and extent, not a rendered Appelboor."""
    data, failure = _tool_payload(answer)
    if failure:
        return failure
    args, envelope = data["arguments"], data["result"]
    positions = _geojson_positions(args.get("point"), "Point")
    result = envelope.get("result")
    if positions is None or not isinstance(result, dict):
        return unparseable("malformed GeoJSON trace")
    model_positions = _georeferenced_positions(envelope, positions)
    if model_positions is None or not _rd_path([result.get("location")]):
        return unparseable("malformed trace georeference or location")
    column = result.get("column")
    if not isinstance(column, dict) or not isinstance(column.get("layers"), list):
        return unparseable("malformed trace")
    layers = column["layers"]
    if not layers or any(
        not isinstance(layer, dict) or not isinstance(layer.get("unitCode"), str) or not _number(layer.get("top")) or not _number(layer.get("base"))
        for layer in layers
    ):
        return unparseable("malformed trace layers")
    distinct = [layer["unitCode"] for i, layer in enumerate(layers) if i == 0 or layer["unitCode"] != layers[i - 1]["unitCode"]]
    want = case.expected
    checks = {
        "location": all(abs(a - b) <= 1e-8 for a, b in zip(positions[0], want["location"]["coordinates"]))
        and _same_rd_path([result["location"]], model_positions)
        and _same_rd_path(model_positions, [want["model_location"]]),
        "model": args.get("modelId") == column.get("modelId") == want["model_id"],
        "surface": _matches(column.get("surfaceElevationNap"), {"value": want["surface"], "tolerance": want["surface_tolerance"]}),
        "datum": column.get("verticalDatum") == "NAP",
        "units": distinct[: len(want["top_units"])] == want["top_units"],
        "extent": len(layers) == want["layer_count"]
        and layers[-1]["base"] == want["bottom"]
        and all(a["base"] == b["top"] for a, b in zip(layers, layers[1:])),
    }
    wrong = [key for key, ok in checks.items() if not ok]
    return Assessment(not wrong, (len(checks) - len(wrong)) / len(checks), 0, True, f"trace checks failed: {wrong}", {"wrong": wrong})


RULES: dict[str, Callable[[str, Case], Assessment]] = {
    "fields": rule_fields,
    "map": rule_map,
    "series": rule_series,
    "section": rule_section,
    "trace": rule_trace,
}


def assess(answer: str, case: Case) -> Assessment:
    return RULES[case.rule](answer, case)
