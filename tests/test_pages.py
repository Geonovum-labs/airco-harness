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


def test_a_measurement_with_a_map_question_gets_a_map_page_on_the_brt_in_rd(tmp_path):
    """The run shows the required panden and one place in the river; the map page carries both, and the report links to it."""
    from validators import sources

    name = "2026-10-29T12-10-00"
    log_dir = tmp_path / "reports" / name / "logs" / "logs"
    must = json.loads((report.rules.TESTSETS_DIR / "dsfl/samples/dsfl-02/expected.json").read_text(encoding="utf-8"))["must"]
    panden = json.loads(sources.path("dsfl/bag-arnhem-sport-panden.geojson").read_text(encoding="utf-8"))["features"]
    river = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [5.905, 51.976]}, "properties": {}}
    geojson = {"type": "FeatureCollection", "features": [f for f in panden if f["properties"]["identificatie"] in must] + [river]}
    steps = [
        ModelOutput.for_tool_call("mockllm/model", "show_on_map", {"geojson": geojson}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de kaart."}),
    ]
    eval(
        airco(testset="dsfl", agent="inspect", ids="dsfl-02", cost_limit=None),
        model=get_model("mockllm/model", custom_outputs=steps),
        log_dir=str(log_dir),
        display="none",
    )
    table = report.runs(str(log_dir))
    table.to_csv(log_dir.parent.parent / "runs.csv", index=False)
    (log_dir.parent.parent / "report.md").write_text(report.markdown(table, "logs/x"), encoding="utf-8")
    shown = report.maps(str(log_dir))
    (log_dir.parent.parent / "maps.json").write_text(json.dumps(shown), encoding="utf-8")

    [run] = shown["runs"]
    assert (run["agent"], len(run["shown"]), run["missing"], run["unmatched"]) == ("inspect", len(must), [], [[5.905, 51.976]])
    pages.build(tmp_path / "reports", tmp_path / "site")
    page = (tmp_path / "site" / name / "report.html").read_text(encoding="utf-8")
    assert "brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992" in page and "proj4leaflet" in page
    data = json.loads(page.split('<script type="application/json" id="maps-data">')[1].split("</script>")[0])
    assert data["runs"] == shown["runs"] and len(data["samples"]["dsfl-02"]["panden"]["features"]) == len(panden)
    # The map sits between the heading of the section of map questions and its table, which the script reads.
    section = page.split('<h2 id="maps-heading">Map questions per run</h2>')[1]
    assert section.index('id="map"') < section.index('<div id="maps"></div><div class="tablewrap">')
    assert 'href="#maps-heading"' in page and not (tmp_path / "site" / name / "maps.html").exists()


def test_a_measurement_without_map_questions_has_no_map(tmp_path):
    test_site_lists_each_measurement_with_report_and_viewer(tmp_path)
    page = (tmp_path / "site" / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")
    assert "leaflet" not in page and "maps-heading" not in page
    assert report.maps(str(tmp_path / "reports" / "2026-10-19T21-45-03" / "logs" / "logs")) is None
