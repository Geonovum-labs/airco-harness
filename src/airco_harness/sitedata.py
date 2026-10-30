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
from inspect_ai.log import read_eval_log

from validators import source_check, sources

from . import report, scorers

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


ERROR_LINE = re.compile(r"^(?:[\w.]+(?:Error|Exception)\b.*|curl: \(\d+\).*|.*returned error: .*)$")


def error_line(output: str) -> str:
    """The line that says why a retrieval failed: the final exception of a traceback, or curl's error, else the first line.
    A shell command's output starts with "Exit code n", which says only that it failed."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    telling = [line for line in lines if ERROR_LINE.match(line)]
    if telling:
        return telling[-1][:200]
    rest = [line for line in lines if not re.fullmatch(r"Exit code \d+", line)]
    return (rest[0] if rest else lines[0] if lines else "")[:200]


def retrievals(log_dir: Path) -> dict[tuple[str, str, int], dict[str, list[dict]]]:
    """Per run (log file, sample, epoch), what it retrieved, read from the conversation with the harness's current rules:
    "retrieved", the URLs that worked with their class for source, and "errors", the ones that failed with their HTTP
    status when known and the line that says why. A log scored under older rules therefore shows what they would find
    now; its source score is the one in the log."""
    out: dict[tuple[str, str, int], dict[str, list[dict]]] = {}
    for path in sorted(log_dir.glob("*.eval")):
        for sample in read_eval_log(str(path)).samples or []:
            standard = (sample.metadata or {}).get("standard", "")
            ok: dict[str, dict] = {}
            failed: dict[tuple, dict] = {}
            for r in scorers.retrievals(sample.messages):
                if 200 <= r["status"] < 300:
                    ok.setdefault(r["url"], {"url": r["url"], "class": source_check.classify(r["url"], standard) if standard else "other"})
                    continue
                output = (r.get("error") or "").strip()
                error = error_line(output)
                entry = {"url": r["url"], "status": r["status"] or None, "error": error, "tool": r["tool"], "times": 0}
                if output and output != error:
                    entry["output"] = output[:1500]
                failed.setdefault((r["url"], r["status"], error), entry)["times"] += 1
            out[(path.name, str(sample.id), sample.epoch)] = {"retrieved": list(ok.values()), "errors": list(failed.values())}
    return out


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
    fetched = retrievals(log_dir)
    runs = []
    for row in table.to_dict("records"):
        run = {"m": name, **{k: row[k] for k in RUN_FIELDS}, **fetched.get((row["log"], row["sample"], row["epoch"]), {"retrieved": [], "errors": []})}
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
