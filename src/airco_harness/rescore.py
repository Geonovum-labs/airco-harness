"""Rescore logs with the scorers named in them, and compare the new scores with the logged ones.

    uv run airco-rescore reports/x/logs/logs/run.eval --out rescore/

inspect score without --scorer cannot find our scorers again: the log stores
them without package prefix. airco-rescore maps them back to airco_harness
and passes the recorded options. It warns on stderr when this checkout is not
the commit the run was made at, or when the run or this checkout has
uncommitted changes, and exits 1 when any score differs by more than the
tolerance.
"""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

from inspect_ai import score
from inspect_ai.log import EvalLog, read_eval_log, write_eval_log

from . import scorers as airco_scorers

ScoreKey = tuple[str, int, str, str]


def scores_of(log: EvalLog) -> dict[ScoreKey, object]:
    out: dict[ScoreKey, object] = {}
    for sample in log.samples or []:
        for scorer, sc in (sample.scores or {}).items():
            values = sc.value if isinstance(sc.value, dict) else {scorer: sc.value}
            for key, value in values.items():
                out[(str(sample.id), sample.epoch, scorer, key)] = value
    return out


def _differs(a: object, b: object, tolerance: float) -> bool:
    numbers = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b))
    if not numbers:
        return a != b
    if math.isnan(a) or math.isnan(b):
        return not (math.isnan(a) and math.isnan(b))
    return abs(a - b) > tolerance


def compare_scores(a: dict[ScoreKey, object], b: dict[ScoreKey, object], tolerance: float = 0.0) -> list[str]:
    if not a:
        return ["the original log has no scores to compare"]
    problems = [f"missing in rescore: {k}" for k in sorted(a.keys() - b.keys())]
    problems += [f"only in rescore: {k}" for k in sorted(b.keys() - a.keys())]
    problems += [f"{k}: {a[k]} -> {b[k]}" for k in sorted(a.keys() & b.keys()) if _differs(a[k], b[k], tolerance)]
    return problems


def rescore(log: EvalLog, out_dir: str, name: str) -> tuple[EvalLog, str]:
    rebuilt = [airco_scorers.BY_NAME[spec.name.split("/")[-1]](**(spec.options or {})) for spec in log.eval.scorers or []]
    # Our scorers call no model; mockllm keeps a third party from needing the keys of the scored model.
    rescored = score(log, rebuilt, model="mockllm/model", action="overwrite", display="none", copy=True)
    target = Path(out_dir) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    write_eval_log(rescored, str(target))
    return rescored, str(target)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def warn_on_drift(path: str, log: EvalLog) -> None:
    """Warn when the test set, reference model, scorers or sources may differ from the run: all of them are in git."""
    revision = log.eval.revision
    if revision is None:
        print(f"{path}: the log records no git commit, so a change since the run cannot be ruled out", file=sys.stderr)
        return
    if revision.dirty:
        print(f"{path}: the run was made with uncommitted changes, which the commit {revision.commit} does not show", file=sys.stderr)
    head = _git("rev-parse", "HEAD")
    if not head.startswith(revision.commit):
        print(f"{path}: the run was made at commit {revision.commit}, this checkout is at {head[:7]}; a score difference can come from that", file=sys.stderr)
    if _git("status", "--porcelain"):
        print(f"{path}: this checkout has uncommitted changes; a score difference can come from that", file=sys.stderr)


def _report(path: str, a: dict, b: dict, problems: list[str], tolerance: float) -> None:
    equal = sum(1 for k in a if k in b and not _differs(a[k], b[k], tolerance))
    print(f"{path}: {equal} of {len(a)} scores equal within {tolerance}")
    for p in problems:
        print(f"  {p}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-rescore", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logs", nargs="+", help=".eval logs to rescore")
    parser.add_argument("--out", default="rescore", help="folder for the rescored logs")
    parser.add_argument("--tolerance", type=float, default=0.0, help="allowed absolute difference per score key")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    failed = False
    for path in args.logs:
        log = read_eval_log(path)
        warn_on_drift(path, log)
        original = scores_of(log)
        rescored, _ = rescore(log, args.out, Path(path).name)
        new = scores_of(rescored)
        problems = compare_scores(original, new, args.tolerance)
        _report(path, original, new, problems, args.tolerance)
        failed |= bool(problems)
    sys.exit(1 if failed else 0)
