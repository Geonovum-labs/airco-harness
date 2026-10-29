"""The site for GitHub Pages, built from bundles of real logs from a scripted mock model."""

import json
from pathlib import Path

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from airco_harness import pages, report
from airco_harness.tasks import airco
from validators import sources

GOOD = json.dumps({"objecttype": "OverigBouwwerk", "type": "bassin"})


def strict(path: Path) -> dict:
    """JSON as a browser reads it: NaN and Infinity are errors."""

    def refuse(constant):
        raise ValueError(f"{constant} in {path.name}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=refuse)


def imgeo_measurement(reports: Path, name: str = "2026-10-19T21-45-03") -> Path:
    log_dir = reports / name / "logs" / "logs"
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", GOOD)])
    eval(airco(ids="imgeo-G04-03", cost_limit=None), model=model, log_dir=str(log_dir), display="none")
    return log_dir


def test_site_has_an_overview_a_comparison_and_a_dashboard_and_viewer_per_measurement(tmp_path):
    reports = tmp_path / "reports"
    imgeo_measurement(reports)
    (reports / "not-a-measurement").mkdir()

    rows = pages.build(reports, tmp_path / "site")

    site = tmp_path / "site"
    assert [(r["name"], r["models"], r["runs"], r["variants"], r["agents"], r["testset_versions"]) for r in rows] == [
        ("2026-10-19T21-45-03", ["mockllm/model"], 1, ["0"], ["model"], ["imgeo 0.3"])
    ]
    data = strict(site / "data.json")
    [run] = data["runs"]
    assert (run["m"], run["sample"], run["correct"], run["log"].endswith(".eval"), "map" in run, run["retrieved"]) == (
        "2026-10-19T21-45-03",
        "imgeo-G04-03",
        1.0,
        True,
        False,
        [],
    )
    assert data["measurements"][0]["limits"]["cost"] == [] and "commits" in data["measurements"][0]
    # The question as the agent got it, without the role that samples_df puts in front.
    assert data["measurements"][0]["questions"]["imgeo-G04-03"].startswith("Een openluchtzwembad")
    for page, kind in [("index.html", "overview"), ("compare.html", "compare"), ("2026-10-19T21-45-03/report.html", "measurement")]:
        shell = (site / page).read_text(encoding="utf-8")
        assert f'data-page="{kind}"' in shell and 'assets/app.js"' in shell and "plot@0.6.17" in shell, page
    assert 'data-measurement="2026-10-19T21-45-03"' in (site / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")
    assert {p.name for p in (site / "assets").iterdir()} >= {"app.js", "stats.js", "map.js", "style.css"}
    viewer = site / "2026-10-19T21-45-03" / "viewer"
    assert (viewer / "index.html").exists() and len(list((viewer / "logs").glob("*.eval"))) == 1
    assert str(tmp_path) not in (viewer / "index.html").read_text(encoding="utf-8") and str(tmp_path) not in (site / "data.json").read_text(encoding="utf-8")
    assert (site / ".nojekyll").exists()


def test_site_without_measurements_has_an_empty_dataset(tmp_path):
    assert pages.build(tmp_path / "none", tmp_path / "site") == []
    assert strict(tmp_path / "site" / "data.json") == {"measurements": [], "runs": [], "maps": {}}


def test_measurements_are_newest_first(tmp_path):
    for name in ("2026-10-19T21-45-03", "2026-11-02T09-00-00"):
        d = tmp_path / name / "logs" / "logs"
        d.mkdir(parents=True)
        (d / "x.eval").write_bytes(b"")
    assert [m.name for m in pages.measurements(tmp_path)] == ["2026-11-02T09-00-00", "2026-10-19T21-45-03"]
    assert pages.measurements(Path(tmp_path / "missing")) == []


def test_a_map_question_carries_its_map_and_only_its_dashboard_loads_the_map_libraries(tmp_path):
    """The run shows the required panden and one place in the river; the dataset carries both, and the pand geometry is a file of its own."""
    reports = tmp_path / "reports"
    imgeo_measurement(reports)
    name = "2026-10-29T12-10-00"
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
        log_dir=str(reports / name / "logs" / "logs"),
        display="none",
    )

    pages.build(reports, tmp_path / "site")

    site = tmp_path / "site"
    data = strict(site / "data.json")
    [run] = [r for r in data["runs"] if r["m"] == name]
    assert (run["agent"], len(run["map"]["shown"]), run["map"]["missing"], run["map"]["unmatched"]) == ("inspect", len(must), [], [[5.905, 51.976]])
    entry = data["maps"]["dsfl-02"]
    assert entry["must"] == must and entry["optional"] == len(panden) - len(must) and entry["note"].startswith("The question is ambiguous on purpose")
    assert len(strict(site / entry["panden"])["features"]) == len(panden)
    assert "proj4leaflet" in (site / name / "report.html").read_text(encoding="utf-8")
    assert "leaflet" not in (site / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")


def test_retrieved_urls_are_parsed_with_their_class_for_the_popover():
    from airco_harness.sitedata import retrieved

    text = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections?f=json (authoritative); https://nominatim.openstreetmap.org/search?q=a;b (other)"
    assert retrieved(text) == [
        {"url": "https://api.pdok.nl/kadaster/bag/ogc/v2/collections?f=json", "class": "authoritative"},
        {"url": "https://nominatim.openstreetmap.org/search?q=a;b", "class": "other"},
    ]
    assert retrieved("") == retrieved(None) == []


def test_a_question_loses_only_the_role_of_a_single_user_message():
    from airco_harness.sitedata import question

    assert question("user:\nVind alle gebouwen met sportfunctie in Arnhem.\n") == "Vind alle gebouwen met sportfunctie in Arnhem."
    conversation = "system:\nJe bent een assistent.\n\nuser:\nVind de gebouwen.\n"
    assert question(conversation) == conversation.strip()
    assert question(None) == ""
