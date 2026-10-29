"""The dataset of the site: every run of every committed measurement, read from the logs.

airco-pages writes it as data.json, and the pages filter, aggregate and compare
it in the browser (assets/stats.js). It is read from the logs rather than from
runs.csv, so a measurement made before a column existed still takes part, with
what its logs record. Pand geometry for map questions goes into a file per
reference extract, which a page fetches only when it draws a map.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd
from inspect_ai.analysis import SampleSummary, samples_df

from validators import sources

from . import report

QUALITY = ["correct", "complete", "invented", "parseable", "source"]
RUN_FIELDS = [
    "model",
    "agent",
    "variant",
    "sample",
    "epoch",
    "failed",
    "limit",
    *QUALITY,
    "cost",
    "tokens",
    "tool_calls",
    "total_time_s",
    "explanation",
    "hosts",
    "log",
]


def _clean(value: object) -> object:
    """JSON without NaN, which browsers refuse: a missing number is null."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _distinct(series: pd.Series) -> list:
    return sorted({v for v in series.dropna().tolist() if v != ""}, key=str)


def question(text: object) -> str:
    """The question as the agent got it. samples_df writes the input with its role, "user:" and a newline;
    a single user message loses that prefix, a conversation of several messages keeps its roles."""
    text = str(text or "").strip()
    single = re.fullmatch(r"user:\n(.*)", text, re.DOTALL)
    return single[1].strip() if single and not re.search(r"\n(?:user|assistant|system|tool):\n", single[1]) else text


def questions(log_dir: Path) -> dict[str, str]:
    """Per sample, the question of its first run in the logs."""
    df = samples_df(str(log_dir), columns=SampleSummary, quiet=True)
    return {sample: question(text) for sample, text in df.drop_duplicates("id")[["id", "input"]].itertuples(index=False)}


def reference_file(reference: str) -> str:
    """Where the site keeps the panden of a reference extract, relative to the site root."""
    return f"data/panden/{reference.replace('/', '__')}"


def panden(reference: str) -> dict:
    """The panden of an extract with their identificatie only, coordinates to 6 decimals (about 10 cm)."""

    def rounded(coordinates: list) -> list:
        return [rounded(c) for c in coordinates] if isinstance(coordinates[0], list) else [round(c, 6) for c in coordinates]

    features = json.loads(sources.path(reference).read_text(encoding="utf-8"))["features"]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"identificatie": f["properties"]["identificatie"]},
                "geometry": {"type": f["geometry"]["type"], "coordinates": rounded(f["geometry"]["coordinates"])},
            }  # fmt: skip
            for f in features
        ],
    }


def measurement(name: str, log_dir: Path) -> tuple[dict, list[dict], dict]:
    """One measurement: its facts, its runs, and the map questions among its samples."""
    table = report.runs(str(log_dir))
    shown = report.maps(str(log_dir)) or {"samples": {}, "runs": []}
    on_map = {(r["model"], r["agent"], r["variant"], r["sample"], r["epoch"]): r for r in shown["runs"]}
    runs = []
    for row in table.to_dict("records"):
        run = {"m": name, **{k: row[k] for k in RUN_FIELDS}}
        found = on_map.get((row["model"], row["agent"], row["variant"], row["sample"], row["epoch"]))
        if found:
            run["map"] = {k: found[k] for k in ("shown", "missing", "unmatched")}
        runs.append(run)
    facts = {
        "name": name,
        "testsets": _distinct(table["testset"]),
        "testset_versions": _distinct(table["testset"] + " " + table["testset_version"]),
        "commits": _distinct(table["commit"]),
        "limits": {key: _distinct(table[f"{key}_limit"]) for key in ("cost", "token", "message", "time")},
        "runs": len(table),
        "failed": int(table["failed"].sum()),
        "at_limit": int(table["limit"].ne("").sum()),
        "cost": float(table["cost"].sum()),
        "samples": _distinct(table["sample"]),
        "models": _distinct(table["model"]),
        "agents": _distinct(table["agent"]),
        "variants": _distinct(table["variant"]),
        "questions": questions(log_dir),
    }
    maps = {
        sample: {
            "must": e["must"],
            "optional": len(panden(e["reference"])["features"]) - len(e["must"]),
            "note": e["note"],
            "panden": reference_file(e["reference"]),
            "reference": e["reference"],
        }  # fmt: skip
        for sample, e in shown["samples"].items()
    }
    return facts, runs, maps


def dataset(measurement_dirs: list[Path]) -> dict:
    """All measurements, newest first, with their runs and the map questions of all samples."""
    out = {"measurements": [], "runs": [], "maps": {}}
    for d in measurement_dirs:
        facts, runs, maps = measurement(d.name, d / "logs" / "logs")
        out["measurements"].append(facts)
        out["runs"] += runs
        out["maps"] |= maps
    return _clean(out)


def write(data: dict, out: Path) -> None:
    (out / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for entry in data["maps"].values():
        target = out / entry["panden"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(panden(entry["reference"]), separators=(",", ":")), encoding="utf-8")
