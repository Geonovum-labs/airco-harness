"""Scoring rules: compare a model answer with the expected outcome of a sample.

Each rule fills four of the five score keys (`source` comes from the tool log, see
airco_harness.scorers). A rule never raises on a malformed answer: it reports
parseable 0 and correct 0 instead. Rules are selected by the "rule" key in a
case's expected.json: `fields` for a JSON answer, `map` for what the agent
showed on the map.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from jsonschema import validators

from . import answers, geo
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
    """`want` is a literal, or {"one_of": [...]} for alternatives."""
    return want["one_of"] if isinstance(want, dict) else [want]


def _invented_terms(values: list) -> list[str]:
    known = refmodel().all_terms

    def is_known(term: str) -> bool:
        t = normalize(term)
        return t in known or t.split(":")[-1] in known

    return sorted({v for v in values if isinstance(v, str) and not is_known(v)})


def rule_fields(answer: str, case: Case) -> Assessment:
    """Named fields, each with an expected value or alternatives; a wrong value in a term field that the reference model does not know is invented."""
    data, failure, details = _json_answer(answer, case)
    if failure:
        return failure
    fields: dict[str, object] = case.expected["expected"]
    wrong = {key: {"expected": want, "given": data.get(key)} for key, want in fields.items() if not any(_same(data.get(key), a) for a in _accepted(want))}
    term_values = [data.get(k) for k in case.expected.get("term_fields", []) if k in wrong]
    invented = _invented_terms(term_values)
    details |= {"wrong": wrong, "invented_terms": invented}
    complete = 1 - len(wrong) / len(fields)
    return Assessment(not wrong and not invented, complete, len(invented), True,
                      f"wrong: {sorted(wrong)}; invented: {invented}", details)  # fmt: skip


def rule_map(answer: str, case: Case) -> Assessment:
    """Places on the map, matched to the panden of the reference extract: every pand in `must`
    has to be on it, and a place that matches no pand of the extract is invented.

    `answer` is the GeoJSON the agent passed to show_on_map, or "" when it showed no map.
    """
    if not answer.strip():
        return unparseable("no map shown")
    try:
        places = geo.points(json.loads(answer))
    except ValueError as error:
        return unparseable(f"not GeoJSON: {error}")
    reference = geo.Reference.load(case.expected["reference"])
    tolerance = case.expected["tolerance_m"]
    matched = [(place, reference.nearest(place, tolerance)) for place in places]
    shown = {pand for _, pand in matched if pand}
    must = set(case.expected["must"])
    missing = sorted(must - shown)
    unmatched = [[round(place.x, 6), round(place.y, 6)] for place, pand in matched if pand is None]
    details = {"places": len(places), "missing": missing, "unmatched": unmatched,
               "swapped": sum(geo.swapped(place) for place, _ in matched)}  # fmt: skip
    complete = 1 - len(missing) / len(must)
    return Assessment(not missing and not unmatched, complete, len(unmatched), True,
                      f"{len(must) - len(missing)} of {len(must)} required panden shown; {len(unmatched)} places match no pand", details)  # fmt: skip


RULES: dict[str, Callable[[str, Case], Assessment]] = {"fields": rule_fields, "map": rule_map}


def assess(answer: str, case: Case) -> Assessment:
    return RULES[case.rule](answer, case)
