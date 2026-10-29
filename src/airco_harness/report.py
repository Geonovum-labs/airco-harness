"""Report per model and variant from the Inspect logs, on inspect_ai.analysis.

    uv run airco-report logs/try                          # writes logs/try/report/
    uv run airco-report logs/<name> --out reports/<name>  # next to the bundle, to publish

The unit of analysis is the sample: per model and variant, each metric is first
averaged over the epochs of a sample, then the mean and standard error are
taken over samples, as Inspect does. A run that hit a limit did not answer, so
it counts with the scores Inspect gave it, 0 where it gave none; a run with an
error is the harness failing, so it is counted separately and left out of the
metrics. Tool calls are counted from the tool messages in the conversation.
For a question answered on a map, the report adds a line per run: what the
rule found on the map, and the hosts the agent retrieved from; the site draws
each map from the logs (maps() gives what it needs).
Cost per correct answer is the cost of all runs, failed ones included, over the
number of correct runs; the cost is what Inspect logged from the prices in
model-costs.yaml during the run.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
from pathlib import Path

import pandas as pd
from inspect_ai.analysis import EvalInfo, EvalModel, EvalTask, SampleColumn, SampleSummary, messages_df, samples_df

from validators import rules

QUALITY = ["correct", "complete", "invented", "parseable", "source"]
TRAJECTORY = ["tool_calls", "tokens", "total_time_s", "working_time_s"]
TOKEN_FIELDS = {
    "tokens_input": "input_tokens",
    "tokens_output": "output_tokens",
    "tokens_cache_read": "input_tokens_cache_read",
    "tokens_cache_write": "input_tokens_cache_write",
    "tokens_reasoning": "reasoning_tokens",
}
MAP_NOTE = "On the site, the dashboard of this measurement draws each run on the BRT achtergrondkaart."
SCORERS = {"score_quality": ["correct", "complete", "invented", "parseable"], "score_source": ["source"]}


def _usage(model_usage: object) -> dict:
    return json.loads(model_usage) if isinstance(model_usage, str) else {}


def _cost(model_usage: object) -> float:
    """Dollars Inspect logged for the run; NaN when a model had no price."""
    costs = [u.get("total_cost") for u in _usage(model_usage).values()]
    return float("nan") if any(c is None for c in costs) else float(sum(costs))


RETRIEVED = SampleColumn("retrieved", path="scores.source.metadata.retrieved", full=True)
# The source scorer counts every tool use, including the tools a provider runs on its own servers, which leave no tool message.
TOOL_CALLS = SampleColumn("tool_calls_scored", path="scores.source.metadata.tool_calls", full=True)
RULE = SampleColumn("rule", path="scores.quality.metadata.rule", full=True)
EXPLANATION = SampleColumn("explanation", path="scores.quality.explanation", full=True)
DETAILS = SampleColumn("details", path="scores.quality.metadata", full=True)


def _classes(value: object) -> dict:
    return json.loads(value) if isinstance(value, str) else value if isinstance(value, dict) else {}


def _retrieved(value: object) -> str:
    """The URLs the agent fetched with success and their class, as the source scorer recorded them: `url (class)` joined with `; `."""
    return "; ".join(f"{url} ({cls})" for url, cls in _classes(value).items())


def _hosts(value: object) -> str:
    """The hosts of the retrieved URLs, each once with its class, in the order of first retrieval: `host (class)` joined with `, `."""
    hosts = {}
    for url, cls in _classes(value).items():
        hosts.setdefault(urllib.parse.urlsplit(url).netloc, cls)
    return ", ".join(f"{host} ({cls})" for host, cls in hosts.items())


def _token_sum(model_usage: object, field: str) -> int:
    return int(sum(u.get(field) or 0 for u in _usage(model_usage).values()))


def _scored_tool_calls(df: pd.DataFrame) -> pd.Series:
    """The tool uses the source scorer counted, when the log has them; older logs fall back to the tool messages."""
    if "tool_calls_scored" not in df:
        return pd.Series(float("nan"), index=df.index)
    return pd.to_numeric(df["tool_calls_scored"], errors="coerce")


def _tool_calls(messages: pd.DataFrame) -> pd.Series:
    if not len(messages):
        return pd.Series(dtype=int)
    return messages[messages["role"] == "tool"].groupby("sample_id").size()


def _testset_version(metadata: object) -> str:
    """The test set version the task wrote into the eval metadata; empty for a log from before it did."""
    meta = json.loads(metadata) if isinstance(metadata, str) else metadata if isinstance(metadata, dict) else {}
    return str((meta.get("testset") or {}).get("version", ""))


def _column(df: pd.DataFrame, name: str, default: object = "") -> pd.Series:
    return df[name] if name in df else pd.Series(default, index=df.index)


def runs(log_dir: str) -> pd.DataFrame:
    """One row per run (sample x epoch x variant x agent x model) with the quality and trajectory metrics,
    and what a comparison between measurements has to hold fixed: the test set and its version, the commit and the limits."""
    df = samples_df(log_dir, columns=EvalInfo + EvalModel + EvalTask + SampleSummary + [RETRIEVED, TOOL_CALLS, RULE, EXPLANATION], quiet=True)
    if not len(df):
        raise FileNotFoundError(f"no samples in .eval logs under {log_dir}")
    error = df["error"].fillna("").astype(str) if "error" in df else pd.Series("", index=df.index)
    limit = df["limit"].fillna("").astype(str) if "limit" in df else pd.Series("", index=df.index)
    messages = messages_df(log_dir, quiet=True)
    out = pd.DataFrame(
        {
            "model": df["model"],
            "variant": df["task_arg_variant"].astype(str),
            "agent": df["task_arg_agent"].astype(str) if "task_arg_agent" in df else "model",
            "sample": df["id"],
            "epoch": df["epoch"],
            "task": df.get("metadata_task"),
            "defect": df.get("metadata_defect"),
            "failed": error.ne(""),
            "limit": limit,
            "reason": (error + " " + limit).str.strip(),
            "tool_calls": _scored_tool_calls(df).fillna(df["sample_id"].map(_tool_calls(messages))).fillna(0).astype(int),
            "tokens": df["total_tokens"],
            **{name: df["model_usage"].map(lambda u, f=field: _token_sum(u, f)) for name, field in TOKEN_FIELDS.items()},
            "total_time_s": df["total_time"],
            "working_time_s": df["working_time"],
            "cost": df["model_usage"].map(_cost),
            "retrieved": df["retrieved"].map(_retrieved) if "retrieved" in df else pd.Series("", index=df.index),
            "hosts": df["retrieved"].map(_hosts) if "retrieved" in df else pd.Series("", index=df.index),
            "rule": df["rule"].fillna("") if "rule" in df else pd.Series("", index=df.index),
            "explanation": df["explanation"].fillna("") if "explanation" in df else pd.Series("", index=df.index),
            "testset": _column(df, "task_arg_testset").fillna("").astype(str),
            "testset_version": _column(df, "metadata").map(_testset_version),
            "commit": _column(df, "git_commit").fillna("").astype(str),
            **{f"{name}_limit": pd.to_numeric(_column(df, f"task_arg_{name}_limit", None), errors="coerce") for name in ("cost", "token", "message", "time")},
            "log": _column(df, "log").map(lambda path: Path(str(path)).name),
        }
    )
    for column, keys in SCORERS.items():
        values = df[column].map(lambda v: json.loads(v) if isinstance(v, str) else {}) if column in df else pd.Series([{}] * len(df), index=df.index)
        for key in keys:
            out[key] = values.map(lambda d, k=key: d.get(k)).astype(float)
    at_limit = out["limit"].ne("")
    out.loc[at_limit, QUALITY] = out.loc[at_limit, QUALITY].fillna(0)
    return out.sort_values(["model", "variant", "sample", "epoch"]).reset_index(drop=True)


def maps(log_dir: str) -> dict | None:
    """What every completed run of a map question showed, with the expected outcome of its sample, for the maps of the site; None without map questions."""
    df = samples_df(log_dir, columns=EvalInfo + EvalModel + EvalTask + SampleSummary + [RULE, EXPLANATION, DETAILS], quiet=True)
    if "rule" not in df:
        return None
    done = df[df["rule"].eq("map") & df["error"].fillna("").astype(str).eq("")] if "error" in df else df[df["rule"].eq("map")]
    if not len(done):
        return None
    samples, runs = {}, []
    for r in done.sort_values(["model", "id", "epoch"]).itertuples():
        expected = rules.Case.load(r.target).expected
        samples[r.id] = {key: expected[key] for key in ("reference", "must", "tolerance_m")}
        details = json.loads(r.details) if isinstance(r.details, str) else r.details
        runs.append(
            {
                "model": r.model,
                "agent": str(getattr(r, "task_arg_agent", "model")),
                "variant": str(r.task_arg_variant),
                "sample": r.id,
                "epoch": int(r.epoch),
                "explanation": r.explanation,
                **{key: details.get(key, []) for key in ("shown", "missing", "unmatched")},
            }
        )
    return {"samples": samples, "runs": runs}


def _mean_se(per_sample: pd.Series) -> tuple[float, float]:
    s = per_sample.dropna()
    if not len(s):
        return float("nan"), float("nan")
    return float(s.mean()), float(s.std(ddof=1) / math.sqrt(len(s))) if len(s) > 1 else float("nan")


def summary(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, agent, variant), group in table.groupby(["model", "agent", "variant"]):
        done = group[~group["failed"]]
        per_sample = done.groupby("sample")[QUALITY + TRAJECTORY].mean()
        row = {
            "model": model,
            "agent": agent,
            "variant": variant,
            "samples": group["sample"].nunique(),
            "runs": len(group),
            "failed": int(group["failed"].sum()),
            "limit": int(group["limit"].ne("").sum()),
        }
        for metric in QUALITY:
            row[metric], row[f"{metric}_se"] = _mean_se(per_sample[metric])
        for metric in TRAJECTORY:
            row[metric] = _mean_se(per_sample[metric])[0]
        correct = done["correct"].sum()
        cost = group["cost"]
        row["cost_per_correct"] = float(cost.sum() / correct) if correct and cost.notna().all() else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def _fmt(value: object, digits: int = 2) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def markdown(table: pd.DataFrame, log_dir: str) -> str:
    s = summary(table)
    lines = [
        "# airco-harness report",
        "",
        f"Logs: `{log_dir}`. Runs: {len(table)}, of which with an error: {int(table['failed'].sum())}, and at a limit: {int(table['limit'].ne('').sum())}.",
        "",
        "Per model and variant: first the mean over the epochs of each sample, then the mean over the samples; the standard error over the samples in parentheses. "
        "A run at a limit counts with the scores it got, a run with an error is left out.",
        "",
        "## Quality metrics per model and variant",
        "",
        "| Model | Agent | Variant | Samples | Runs | Error | Limit | " + " | ".join(QUALITY) + " |",
        "| --- | --- | --- | --- | --- | --- | --- | " + " | ".join("---" for _ in QUALITY) + " |",
    ]
    for _, r in s.iterrows():
        cells = [f"{_fmt(r[m])} ({_fmt(r[m + '_se'])})" for m in QUALITY]
        lines.append(
            f"| {r['model']} | {r['agent']} | {r['variant']} | {r['samples']} | {r['runs']} | {r['failed']} | {r['limit']} | " + " | ".join(cells) + " |"
        )
    lines += [
        "",
        "## Trajectory metrics and cost per model and variant",
        "",
        "| Model | Agent | Variant | Tool calls | Tokens | Total time (s) | Working time (s) | Cost per correct answer ($) |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, r in s.iterrows():
        lines.append(
            f"| {r['model']} | {r['agent']} | {r['variant']} | {_fmt(r['tool_calls'], 1)} | {_fmt(r['tokens'], 0)} | "
            f"{_fmt(r['total_time_s'], 1)} | {_fmt(r['working_time_s'], 1)} | {_fmt(r['cost_per_correct'], 4)} |"
        )
    lines += ["", "## `correct` / `complete` per sample (mean over epochs)", "", _per_sample(table), ""]
    map_runs = table[~table["failed"] & table["rule"].eq("map")]
    if len(map_runs):
        lines += [
            "## Map questions per run",
            "",
            MAP_NOTE,
            "",
            "| Model | Agent | Variant | Sample | Epoch | On the map | Retrieved from |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        lines += [f"| {r.model} | {r.agent} | {r.variant} | {r.sample} | {r.epoch} | {r.explanation} | {r.hosts or 'nothing'} |" for r in map_runs.itertuples()]
        lines.append("")
    failed = table[table["failed"] | table["limit"].ne("")]
    if len(failed):
        lines += [
            "## Runs with an error or at a limit",
            "",
            "| Model | Agent | Variant | Sample | Epoch | Reason | Tokens |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        lines += [f"| {r.model} | {r.agent} | {r.variant} | {r.sample} | {r.epoch} | {r.reason[:120]} | {_fmt(r.tokens, 0)} |" for r in failed.itertuples()]
        lines.append("")
    return "\n".join(lines)


def _per_sample(table: pd.DataFrame) -> str:
    """correct and complete side by side: a question that is rarely fully right, such as a map, still shows how far each agent got."""
    done = table[~table["failed"]]
    if not len(done):
        return "no completed runs"
    rows = ["model", "agent", "variant"]
    correct = done.pivot_table(index=rows, columns="sample", values="correct", aggfunc="mean")
    complete = done.pivot_table(index=rows, columns="sample", values="complete", aggfunc="mean")
    cells = correct.combine(complete, lambda a, b: a.map(_fmt).str.cat(b.map(_fmt), sep=" / "))
    return cells.reset_index().rename(columns={"model": "Model", "agent": "Agent", "variant": "Variant"}).to_markdown(index=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-report", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log_dir", help="folder with .eval logs")
    parser.add_argument("--out", default=None, help="output folder; default report/ inside log_dir")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        table = runs(args.log_dir)
    except FileNotFoundError as error:
        build_parser().error(str(error))
    out = Path(args.out or Path(args.log_dir) / "report")
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "runs.csv", index=False)
    (out / "report.md").write_text(markdown(table, args.log_dir), encoding="utf-8")
    print(f"{len(table)} run{'' if len(table) == 1 else 's'}; {out / 'report.md'}")
