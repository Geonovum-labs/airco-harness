"""Known good and bad answers per sample, with the score each must get, before any model is assessed."""

import json
import re

import pytest

from validators import rules
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
