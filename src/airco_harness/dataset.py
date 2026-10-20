"""A test set from testsets/<name>/ as Inspect samples.

A test set folder holds testset.json (purpose, version, date) and a folder
samples/<id>/ per sample, with sample.json, expected.json and, for a JSON
answer, answer.schema.json. The folder name is the sample id. Each sample
names its standard, and a test set may mix standards.
"""

from __future__ import annotations

import json

from inspect_ai.dataset import MemoryDataset, Sample

from validators.rules import TESTSETS_DIR

DEFAULT_TESTSET = "imgeo"


def testsets() -> list[str]:
    return sorted(p.parent.name for p in TESTSETS_DIR.glob("*/testset.json"))


def manifest(testset: str) -> dict:
    return json.loads((TESTSETS_DIR / testset / "testset.json").read_text(encoding="utf-8"))


def records(testset: str) -> list[dict]:
    """The sample.json of each sample in id order, with the id from the folder name."""
    if testset not in testsets():
        raise ValueError(f"unknown test set {testset!r}; choose from {', '.join(testsets())}")
    files = sorted((TESTSETS_DIR / testset / "samples").glob("*/sample.json"))
    return [{"id": f.parent.name, **json.loads(f.read_text(encoding="utf-8"))} for f in files]


def standards(testset: str) -> list[str]:
    return sorted({r["standard"] for r in records(testset)})


def load(testset: str = DEFAULT_TESTSET, ids: list[str] | None = None) -> MemoryDataset:
    """Samples of a test set, or of the ids in it."""
    rows = records(testset)
    if ids is not None:
        ids = [i.strip() for i in ids if i.strip()]
        unknown = sorted(set(ids) - {r["id"] for r in rows})
        if unknown:
            raise ValueError(f"unknown sample ids: {', '.join(unknown)}")
    samples = [
        Sample(
            id=r["id"],
            input=r["input"],
            target=f"{testset}/samples/{r['id']}/expected.json",
            metadata={"defect": r["defect"], "task": r["task"], "standard": r["standard"], **r["metadata"]},
        )
        for r in rows
        if ids is None or r["id"] in ids
    ]
    return MemoryDataset(samples, name=f"test-set-{testset}")
