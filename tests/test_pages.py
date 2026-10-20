"""The site for GitHub Pages, built from a bundle of real logs from a scripted mock model."""

import json
from pathlib import Path

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from airco_harness import pages, report
from airco_harness.tasks import airco

GOOD = json.dumps({"objecttype": "OverigBouwwerk", "type": "bassin"})


def test_site_lists_each_measurement_with_report_and_viewer(tmp_path):
    reports = tmp_path / "reports"
    log_dir = reports / "2026-10-19T21-45-03" / "logs" / "logs"
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", GOOD)])
    eval(airco(ids="imgeo-G04-03", cost_limit=None), model=model, log_dir=str(log_dir), display="none")
    table = report.runs(str(log_dir))
    table.to_csv(reports / "2026-10-19T21-45-03" / "runs.csv", index=False)
    (reports / "2026-10-19T21-45-03" / "report.md").write_text(report.markdown(table, "logs/x"), encoding="utf-8")
    (reports / "not-a-measurement").mkdir()

    rows = pages.build(reports, tmp_path / "site")

    assert [(r["name"], r["models"], r["runs"], r["variants"], r["agents"]) for r in rows] == [("2026-10-19T21-45-03", ["mockllm/model"], 1, ["0"], ["model"])]
    index = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert 'href="2026-10-19T21-45-03/report.html"' in index and 'href="2026-10-19T21-45-03/viewer/"' in index
    assert "19 October 2026, 21:45" in index and '<span class="chip">mockllm/model</span>' in index
    assert "<table" in (tmp_path / "site" / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")
    viewer = tmp_path / "site" / "2026-10-19T21-45-03" / "viewer"
    assert (viewer / "index.html").exists() and len(list((viewer / "logs").glob("*.eval"))) == 1
    assert str(tmp_path) not in (viewer / "index.html").read_text(encoding="utf-8")
    assert (tmp_path / "site" / ".nojekyll").exists()


def test_site_without_measurements_says_so(tmp_path):
    assert pages.build(tmp_path / "none", tmp_path / "site") == []
    assert "No measurements yet" in (tmp_path / "site" / "index.html").read_text(encoding="utf-8")


def test_measurements_are_newest_first(tmp_path):
    for name in ("2026-10-19T21-45-03", "2026-11-02T09-00-00"):
        d = tmp_path / name / "logs" / "logs"
        d.mkdir(parents=True)
        (d / "x.eval").write_bytes(b"")
    assert [m.name for m in pages.measurements(tmp_path)] == ["2026-11-02T09-00-00", "2026-10-19T21-45-03"]
    assert pages.measurements(Path(tmp_path / "missing")) == []
