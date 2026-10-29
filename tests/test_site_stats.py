"""The site's statistics in assets/stats.js give what airco-report gives, run in node on the same runs."""

import json
import math
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from airco_harness import report

STATS = Path(__file__).resolve().parent.parent / "src" / "airco_harness" / "site" / "stats.js"
NODE = shutil.which("node")

SCRIPT = """
import {readFileSync} from "node:fs";
import {aggregate, costPerCorrect, groupBy, QUALITY, TRAJECTORY} from STATS;
const out = [];
for (const [key, group] of groupBy(JSON.parse(readFileSync(0, "utf-8")), r => [r.model, r.agent, r.variant].join("|"))) {
  const row = {key, cost_per_correct: costPerCorrect(group)};
  for (const metric of [...QUALITY, ...TRAJECTORY]) row[metric] = aggregate(group, metric);
  out.push(row);
}
console.log(JSON.stringify(out));
"""


def runs() -> pd.DataFrame:
    """Two samples, epochs that disagree, a failed run, a run at a limit without scores, and a group with one sample."""
    rows = []
    for model, sample, epoch, correct, complete, failed, limit in [
        ("a", "s1", 1, 1, 1.0, False, ""),
        ("a", "s1", 2, 0, 0.5, False, ""),
        ("a", "s2", 1, 0, 0.25, False, ""),
        ("a", "s2", 2, None, None, False, "cost"),
        ("a", "s2", 3, 1, 1.0, True, ""),
        ("b", "s1", 1, 1, 1.0, False, ""),
    ]:
        rows.append({"model": model, "agent": "inspect", "variant": "0", "sample": sample, "epoch": epoch, "failed": failed, "limit": limit,
                     "correct": correct, "complete": complete, "invented": 0, "parseable": 1, "source": 1 if model == "a" else 0,
                     "tool_calls": epoch, "tokens": 1000 * epoch, "total_time_s": 10.0, "working_time_s": 9.0, "cost": 0.1 * epoch})  # fmt: skip
    table = pd.DataFrame(rows)
    at_limit = table["limit"].ne("")
    table.loc[at_limit, report.QUALITY] = table.loc[at_limit, report.QUALITY].fillna(0)
    return table


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_site_statistics_equal_the_report(tmp_path):
    table = runs()
    script = tmp_path / "check.mjs"
    script.write_text(SCRIPT.replace("STATS", json.dumps(STATS.as_uri())), encoding="utf-8")
    records = json.loads(table.to_json(orient="records"))
    result = subprocess.run([NODE, str(script)], input=json.dumps(records), capture_output=True, text=True, check=True)
    site = {row["key"]: row for row in json.loads(result.stdout)}

    expected = report.summary(table)
    assert len(site) == len(expected)
    for _, r in expected.iterrows():
        row = site[f"{r['model']}|{r['agent']}|{r['variant']}"]
        for metric in report.QUALITY:
            assert row[metric]["mean"] == pytest.approx(r[metric]), metric
            assert (row[metric]["se"] is None) == math.isnan(r[f"{metric}_se"]), metric
            if row[metric]["se"] is not None:
                assert row[metric]["se"] == pytest.approx(r[f"{metric}_se"]), metric
        for metric in ("tool_calls", "tokens", "total_time_s"):
            assert row[metric]["mean"] == pytest.approx(r[metric]), metric
        assert (row["cost_per_correct"] is None) == math.isnan(r["cost_per_correct"])
        if row["cost_per_correct"] is not None:
            assert row["cost_per_correct"] == pytest.approx(r["cost_per_correct"])
