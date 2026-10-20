"""Known good and bad answers per sample, with the score each must get, before any model is assessed."""

import json
import re

import pytest

from validators import rules
from validators.rules import Case

SAMPLES = {p.name for p in (rules.TESTSETS_DIR / "imgeo" / "samples").iterdir()}


def score(sample_id: str, answer: str) -> dict:
    return rules.assess(answer, Case.load(f"imgeo/samples/{sample_id}/expected.json")).score_value()


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
]


@pytest.mark.parametrize(("sample_id", "answer", "expected"), CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASES)])
def test_rule_scores(sample_id, answer, expected):
    assert score(sample_id, answer) == expected


def test_every_sample_has_a_known_good_answer():
    assert {c[0] for c in CASES if c[2] == full()} == SAMPLES


def test_rules_are_repeatable():
    sample_id, answer, _ = CASES[2]
    case = Case.load(f"imgeo/samples/{sample_id}/expected.json")
    first, second = rules.assess(answer, case), rules.assess(answer, case)
    assert (first.score_value(), first.explanation, first.details) == (second.score_value(), second.explanation, second.details)


def test_validators_never_import_inspect():
    offenders = [
        p.name
        for p in rules.TESTSETS_DIR.parent.joinpath("validators").glob("*.py")
        if re.search(r"^\s*(from|import) inspect_ai", p.read_text(encoding="utf-8"), re.M)
    ]
    assert offenders == []
