"""The site for GitHub Pages, built from bundles of real logs from a scripted mock model."""

import json
import time
from pathlib import Path

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from airco_harness import pages, report, sitedata
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
        assert '<a class="repo" href="https://github.com/Geonovum-labs/airco-harness"' in shell.split("</header>")[0], page
    assert 'data-measurement="2026-10-19T21-45-03"' in (site / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")
    assert {p.name for p in (site / "assets").iterdir()} >= {"app.js", "stats.js", "map.js", "style.css"}
    viewer = site / "2026-10-19T21-45-03" / "viewer"
    assert (viewer / "index.html").exists() and len(list((viewer / "logs").glob("*.eval"))) == 1
    assert str(tmp_path) not in (viewer / "index.html").read_text(encoding="utf-8") and str(tmp_path) not in (site / "data.json").read_text(encoding="utf-8")
    assert (site / ".nojekyll").exists()


def test_site_without_measurements_has_an_empty_dataset(tmp_path):
    assert pages.build(tmp_path / "none", tmp_path / "site") == []
    assert strict(tmp_path / "site" / "data.json") == {"measurements": [], "runs": [], "maps": {}}


def test_measurements_are_newest_first_by_the_start_in_their_logs_not_by_name(tmp_path):
    reports = tmp_path / "reports"
    imgeo_measurement(reports, "smoke-earlier")
    time.sleep(1.1)  # eval.created has whole seconds
    imgeo_measurement(reports, "2026-10-19T21-45-03")
    shown = pages.build(reports, tmp_path / "site")
    assert [m["name"] for m in shown] == ["2026-10-19T21-45-03", "smoke-earlier"]
    assert shown[0]["started"] > shown[1]["started"] and shown[0]["started"].endswith("+00:00")
    assert [m["name"] for m in strict(tmp_path / "site" / "data.json")["measurements"]] == ["2026-10-19T21-45-03", "smoke-earlier"]
    assert pages.measurements(Path(tmp_path / "missing")) == []


def test_a_map_question_carries_its_map_and_only_its_dashboard_loads_the_map_libraries(tmp_path):
    """The run shows the required panden and one place in the river; the dataset carries both, and the pand geometry is a file of its own."""
    reports = tmp_path / "reports"
    imgeo_measurement(reports)
    name = "2026-10-29T12-10-00"
    must = json.loads((report.rules.TESTSETS_DIR / "dsfl/samples/dsfl-04/expected.json").read_text(encoding="utf-8"))["must"]
    panden = json.loads(sources.path("dsfl/bag-amersfoort-sport-panden.geojson").read_text(encoding="utf-8"))["features"]
    river = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [5.3792, 52.164]},
        "properties": {"name": "Roeivereniging", "sport": {"type": "roeien"}},
    }
    geojson = {"type": "FeatureCollection", "features": [f for f in panden if f["properties"]["identificatie"] in must] + [river]}
    steps = [
        ModelOutput.for_tool_call("mockllm/model", "show_on_map", {"geojson": geojson}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de kaart."}),
    ]
    eval(
        airco(testset="dsfl", agent="inspect", ids="dsfl-04", cost_limit=None),
        model=get_model("mockllm/model", custom_outputs=steps),
        log_dir=str(reports / name / "logs" / "logs"),
        display="none",
    )

    pages.build(reports, tmp_path / "site")

    site = tmp_path / "site"
    data = strict(site / "data.json")
    [run] = [r for r in data["runs"] if r["m"] == name]
    assert (run["agent"], len(run["map"]["shown"]), run["map"]["missing"], run["map"]["unmatched"]) == ("inspect", len(must), [], [[5.3792, 52.164]])
    # What the agent said per place: matched to its pand by the scorer's rule, the river on none, the details as text.
    places = run["map"]["places"]
    assert {p["pand"] for p in places if p["pand"]} == set(must)
    assert [p["details"] for p in places if not p["pand"]] == [{"name": "Roeivereniging", "sport": '{"type": "roeien"}'}]
    entry = data["maps"][f"{name}/dsfl-04"]
    assert entry["must"] == must and entry["optional"] == len(panden) - len(must) and entry["note"].startswith("Deck wording: Where are the sports halls")
    assert len(strict(site / entry["panden"])["features"]) == len(panden)
    assert "proj4leaflet" in (site / name / "report.html").read_text(encoding="utf-8")
    assert "leaflet" not in (site / "2026-10-19T21-45-03" / "report.html").read_text(encoding="utf-8")


def test_a_map_is_drawn_against_the_question_its_sample_id_meant_at_the_commit_of_the_log(tmp_path):
    """dsfl-02 asked for the sports buildings in Arnhem at the commits of these two measurements, and means another question now."""
    names = ["2026-11-12T12-37-01", "2026-10-29T12-39-59"]
    arnhem = "dsfl/bag-arnhem-sport-panden.geojson"

    data = sitedata.dataset([sitedata.measurement(name, pages.ROOT / "reports" / name / "logs" / "logs") for name in names])
    sitedata.write(data, tmp_path)

    entries = {key: data["maps"][key] for key in (f"{name}/dsfl-02" for name in names)}
    assert {key: (e["reference"], len(e["must"])) for key, e in entries.items()} == {key: (arnhem, 61) for key in entries}
    assert {key: e["commit"] for key, e in entries.items()} == {f"{names[0]}/dsfl-02": "cc195ec", f"{names[1]}/dsfl-02": "2bb2843"}
    for e in entries.values():
        assert len(strict(tmp_path / e["panden"])["features"]) == len(e["must"]) + e["optional"]
    # The site matches each place to a pand again; it has to find the panden the scorer found when it scored the run.
    drawn = [r for r in data["runs"] if r.get("map")]
    assert drawn and all(f"{r['m']}/{r['sample']}" in data["maps"] for r in drawn)
    assert all({p["pand"] for p in r["map"]["places"] if p["pand"]} == set(r["map"]["shown"]) for r in drawn)
    assert any(r["map"]["shown"] for r in drawn)


def test_point_map_places_use_the_same_assignment_and_allowed_selection_as_scoring():
    from inspect_ai.model import ChatMessageAssistant, ChatMessageTool
    from inspect_ai.tool import ToolCall

    expected = json.loads((report.rules.TESTSETS_DIR / "dsfl/samples/dsfl-07/expected.json").read_text(encoding="utf-8"))
    wells = json.loads(sources.path(expected["reference"]).read_text(encoding="utf-8"))["features"]
    chosen = {"GMW000000009391", "GMW000000046914", "GMW000000009371"}
    collection = {"type": "FeatureCollection", "features": [f for f in wells if f["id"] in chosen]}
    messages = [
        ChatMessageAssistant(content="", tool_calls=[ToolCall(id="map", function="show_on_map", arguments={"geojson": collection})]),
        ChatMessageTool(content="ok", tool_call_id="map", function="show_on_map"),
    ]
    config = {**expected, "commit": "", "allowed_optional": expected["optional"]}
    places = sitedata.places(messages, config, {})
    assert {p["pand"] for p in places} == {"GMW000000009391", "GMW000000046914", None}


def test_a_question_loses_only_the_role_of_a_single_user_message():
    from airco_harness.sitedata import question

    assert question("user:\nVind alle gebouwen met sportfunctie in Amersfoort.\n") == "Vind alle gebouwen met sportfunctie in Amersfoort."
    conversation = "system:\nJe bent een assistent.\n\nuser:\nVind de gebouwen.\n"
    assert question(conversation) == conversation.strip()
    assert question(None) == ""


def test_a_failed_retrieval_reaches_the_site_with_its_http_status(tmp_path):
    """The agent fetches a page that is gone and one it may not read; the site lists both with their status."""
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(404 if self.path == "/gone" else 401)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    steps = [
        ModelOutput.for_tool_call("mockllm/model", "fetch", {"url": f"{base}/gone"}),
        ModelOutput.for_tool_call("mockllm/model", "fetch", {"url": f"{base}/secret"}),
        ModelOutput.for_tool_call("mockllm/model", "fetch", {"url": f"{base}/gone"}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": GOOD}),
    ]
    log_dir = tmp_path / "reports" / "2026-10-30T09-00-00" / "logs" / "logs"
    try:
        eval(
            airco(agent="inspect", ids="imgeo-G04-03", cost_limit=None),
            model=get_model("mockllm/model", custom_outputs=steps),
            log_dir=str(log_dir),
            display="none",
        )
    finally:
        server.shutdown()

    pages.build(tmp_path / "reports", tmp_path / "site")

    [run] = strict(tmp_path / "site" / "data.json")["runs"]
    assert [(e["url"].rsplit("/", 1)[-1], e["status"], e["error"], e["times"]) for e in run["errors"]] == [
        ("gone", 404, "HTTP 404", 2),
        ("secret", 401, "HTTP 401", 1),
    ]
    assert run["retrieved"] == []


def test_the_error_line_is_the_one_that_says_why():
    from airco_harness.sitedata import error_line

    assert (
        error_line("Exit code 1\nTraceback (most recent call last):\n  File x\nurllib.error.HTTPError: HTTP Error 400: Bad Request")
        == "urllib.error.HTTPError: HTTP Error 400: Bad Request"
    )
    assert error_line("Exit code 7\ncurl: (7) Failed to connect to overpass-api.de port 443") == "curl: (7) Failed to connect to overpass-api.de port 443"
    output = "Exit code 7\npdok:404\noverpass:000"
    assert error_line(output, "https://overpass-api.de/api/status", shared=True) == "overpass:000"
    assert error_line(output, "https://api.pdok.nl/lv/bag/ogc/v2/collections", shared=True) == "pdok:404"
    assert error_line("Exit code 1\nTraceback ...\nValueError: x", "https://a.example/", shared=True) == ""
    assert error_line("HTTP 404") == "HTTP 404"
    assert error_line("") == ""


def test_the_questions_of_a_measurement_are_listed_in_sample_order():
    """The logs hold the runs in the order they finished; the measurement of 13 November 2026 lists dsfl-05 first."""
    logs = Path(__file__).parent.parent / "reports" / "2026-11-13T09-33-45" / "logs"
    assert list(sitedata.questions(logs)) == [f"dsfl-0{n}" for n in range(1, 6)]


def test_a_build_from_the_cache_reads_no_log_and_gives_the_same_site(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    log_dir = imgeo_measurement(reports)
    cache = tmp_path / "cache"
    pages.build(reports, tmp_path / "cold", cache)
    (cache / "stale").mkdir()

    def reread(*args):
        raise AssertionError("the logs were read again")

    monkeypatch.setattr(sitedata, "measurement", reread)
    monkeypatch.setattr(pages, "bundle", reread)
    pages.build(reports, tmp_path / "warm", cache)

    def files(site: Path) -> dict[str, bytes]:
        return {p.relative_to(site).as_posix(): p.read_bytes() for p in site.rglob("*") if p.is_file()}

    assert files(tmp_path / "warm") == files(tmp_path / "cold")
    assert [e.name.split("-")[:3] for e in cache.iterdir()] == [["2026", "10", "19T21"]]
    (log_dir / "notes.txt").write_text("a changed log folder", encoding="utf-8")
    with pytest.raises(AssertionError, match="read again"):
        pages.build(reports, tmp_path / "again", cache)


def test_the_model_calls_of_a_run_reach_its_measurement_with_their_tokens_and_tools(tmp_path):
    """Each model call of the run in a file of its own run, not in data.json: tokens and tools, what it read for the first time and what it wrote."""
    from inspect_ai.model import ModelUsage

    steps = [
        ModelOutput.for_tool_call("mockllm/model", "fetch", {"url": "http://127.0.0.1:9/nothing"}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": GOOD}),
    ]
    usages = [ModelUsage(input_tokens=1200, input_tokens_cache_read=0, input_tokens_cache_write=800, output_tokens=40, total_tokens=2040),
              ModelUsage(input_tokens=300, input_tokens_cache_read=2000, input_tokens_cache_write=0, output_tokens=25, total_tokens=2325)]  # fmt: skip
    for step, usage in zip(steps, usages):
        step.usage = usage
    log_dir = tmp_path / "reports" / "2026-11-19T12-00-00" / "logs" / "logs"
    eval(
        airco(agent="inspect", ids="imgeo-G04-03", cost_limit=None),
        model=get_model("mockllm/model", custom_outputs=steps),
        log_dir=str(log_dir),
        display="none",
    )

    pages.build(tmp_path / "reports", tmp_path / "site")

    [run] = strict(tmp_path / "site" / "data.json")["runs"]
    assert "calls" not in run and run["model_calls"] == 2
    first, second = strict(tmp_path / "site" / "2026-11-19T12-00-00" / sitedata.calls_file(run))
    assert [(c["tokens"], c["price"], c["tools"], c["stop"]) for c in (first, second)] == [
        ([1200, 0, 800, 40], 0.0, [{"kind": "builtin", "name": "fetch"}], "tool_calls"),
        ([300, 2000, 0, 25], 0.0, [{"kind": "harness", "name": "submit"}], "tool_calls"),
    ]
    assert sum(sum(c["tokens"]) for c in (first, second)) == run["tokens"]
    assert first["output"]["tool_calls"] == [{"tool": {"kind": "builtin", "name": "fetch"}, "text": '{"url": "http://127.0.0.1:9/nothing"}'}]
    assert [m["role"] for m in first["new"]][-1] == "user" and first["new"][-1]["text"].startswith("Een openluchtzwembad")
    [result] = second["new"]
    assert (result["role"], result["tool"]) == ("tool", {"kind": "builtin", "name": "fetch"}) and result["text"]
    assert second["messages"] == first["messages"] + 2 and first["event"] != second["event"]
    assert (first["side"], second["side"]) == (False, False)
    for call in (first, second):
        definitions = sum(call["definitions"]["tokens"])
        assert 0 < definitions <= sum(call["tokens"][:3]) and call["definitions"]["tokens"][3] == 0 and call["definitions"]["price"] == 0.0
        assert call["definitions"]["exact"] is False, "without tool-tokens.json the count is an estimate"
    viewer = (tmp_path / "site" / "2026-11-19T12-00-00" / "viewer" / "logs" / run["log"]).exists()
    assert viewer, "the event ids point into the log the viewer bundles"


@pytest.mark.parametrize(
    ("name", "servers", "with_mcp", "tool"),
    [
        ("mcp__bgt__process_aggregate-features", [], True, {"kind": "mcp", "server": "bgt", "name": "process_aggregate-features"}),
        ("mcp__subsurface-models__subsurface-models_trace", [], True, {"kind": "mcp", "server": "subsurface-models", "name": "trace"}),
        ("mcp__map__show_on_map", [], False, {"kind": "harness", "name": "show_on_map"}),
        ("subsurface-models_trace", ["bgt", "subsurface-models"], True, {"kind": "mcp", "server": "subsurface-models", "name": "trace"}),
        ("process_aggregate-features", ["bgt"], True, {"kind": "mcp", "name": "process_aggregate-features"}),
        ("fetch", ["bgt"], True, {"kind": "builtin", "name": "fetch"}),
        ("Bash", ["bgt"], True, {"kind": "builtin", "name": "Bash"}),
        ("Skill", [], False, {"kind": "skill", "name": "Skill"}),
        ("process_aggregate-features", [], False, {"kind": "builtin", "name": "process_aggregate-features"}),
    ],
)
def test_a_tool_is_an_mcp_servers_a_skill_the_harnesss_or_the_agents_own(name, servers, with_mcp, tool):
    assert sitedata.tool_kind(name, servers, with_mcp) == tool


def test_the_servers_of_a_run_come_from_its_variant_in_every_form_the_logs_have_had():
    form = {"mcp": [{"name": "bgt", "url": "https://bag.ldproxy.net/bgt/mcp"}, {"name": "subsurface-models", "url": "http://localhost:18082/mcp"}]}
    assert sitedata.mcp_servers({"variant_form": form}) == (["bgt", "subsurface-models"], True)
    assert sitedata.mcp_servers({"variant_form": {"mcp": "https://bag.ldproxy.net/bag/mcp"}}) == (["bag"], True)
    assert sitedata.mcp_servers({"variant_form": {"mcp": ["docker", "run", "image"]}}) == ([], True)
    assert sitedata.mcp_servers({"variant_form": {"mcp": None}}) == ([], False)


def test_a_tool_set_is_read_from_the_request_with_its_attachments_and_keyed_whatever_its_order():
    from types import SimpleNamespace

    from airco_harness import tooltokens

    long = "a" * 32
    tools = [{"name": "fetch", "description": f"attachment://{'0' * 32}", "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}}}]
    event = SimpleNamespace(call=SimpleNamespace(request={"tools": tools}))
    [tool] = tooltokens.tools_of(event, {"0" * 32: f'Fetch a "page" {long}'})
    assert tool["description"] == f'Fetch a "page" {long}'
    reordered = [{"input_schema": tool["input_schema"], "description": tool["description"], "name": "fetch"}]
    assert tooltokens.key("anthropic/claude-haiku-5-5", [tool]) == tooltokens.key("anthropic/claude-haiku-5-5", reordered)
    assert tooltokens.tools_of(SimpleNamespace(call=None), {}) is None


def test_a_runs_mcp_messages_go_to_their_own_file_and_its_protocol_per_server_into_the_data():
    from airco_harness import mcpwire

    records = [
        {"server": "bgt", "http": "POST", "method": "server/discover", "protocol": "2026-07-28", "client": {"name": "claude-code", "version": "2.1.304"},
         "supported": ["2026-07-28"], "at": 100.0, "status": 200, "ms": 30, "bytes": 900},
        {"server": "bgt", "http": "POST", "method": "tools/call", "tool": "process_aggregate-features", "protocol": "2026-07-28", "at": 102.5,
         "status": 200, "ms": 1200, "bytes": 5000, "error": "too many objects"},
    ]  # fmt: skip
    run = {"m": "2026-11-20T14-00-00", "log": "x.eval", "sample": "dsfl-16", "epoch": 1, "calls": [], "mcp": mcpwire.traffic(records),
           "mcp_messages": sitedata.mcp_messages(records)}  # fmt: skip
    data = sitedata.dataset([({"name": run["m"]}, [run], {})])
    [shown] = data["runs"]
    assert "mcp_messages" not in shown
    assert shown["mcp"] == [{"server": "bgt", "protocols": ["2026-07-28"], "sessions": 0, "requests": 2, "tool_calls": 1, "errors": 1, "ms": 1200,
                             "handshake": {"method": "server/discover", "protocol": "2026-07-28", "supported": ["2026-07-28"]}, "client": "claude-code 2.1.304"}]  # fmt: skip
    assert data["calls"][run["m"]][sitedata.mcp_file(run)] == [
        {"s": 0.0, "server": "bgt", "method": "server/discover", "status": 200, "ms": 30, "bytes": 900, "protocol": "2026-07-28"},
        {"s": 2.5, "server": "bgt", "method": "tools/call", "tool": "process_aggregate-features", "status": 200, "ms": 1200, "bytes": 5000,
         "error": "too many objects", "protocol": "2026-07-28"},
    ]  # fmt: skip
    assert mcpwire.protocols(mcpwire.traffic(records)) == "bgt 2026-07-28"


def test_the_site_shows_the_start_of_a_long_mcp_message_and_its_length():
    received = "y" * (sitedata.MCP_SHOWN_CHARS + 10)
    [shown] = sitedata.mcp_messages([{"server": "s", "method": "tools/call", "at": 1.0, "sent": "{}", "received": received, "received_chars": 70_000}])
    assert (shown["sent"], len(shown["received"]), shown["received_chars"]) == ("{}", sitedata.MCP_SHOWN_CHARS, 70_000) and "sent_chars" not in shown
