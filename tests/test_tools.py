"""The fetch tool against a local web server and bad input, and the agent inspect end to end with a scripted model."""

import asyncio
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.tool import ToolError

from airco_harness import tools
from airco_harness.tasks import airco
from validators import sources

ANSWER = json.dumps({"objecttype": "OverigBouwwerk", "type": "bassin"})
MAP_DOCUMENT: dict[str, bytes] = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/redirect":
            self.send_response(301)
            self.send_header("Location", "/page")
            self.end_headers()
            return
        body, kind, status = {
            "/page": (b"<html><body><h1>Title</h1><p>bgt-status: <em>bestaand</em></p></body></html>", "text/html", 200),
            "/long": (b"x" * 50_000, "text/plain", 200),
            "/missing": (b"gone", "text/plain", 404),
            "/map": (MAP_DOCUMENT.get("body", b"{}"), "application/json", 200),
            "/notjson": (b"<html>no</html>", "text/html", 200),
        }.get(path, (b"not found", "text/plain", 404))
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def call(url, start=0):
    return asyncio.run(tools.fetch()(url=url, start=start))


def test_fetch_gives_markdown_follows_redirects_and_pages(server):
    assert call(f"{server}/page") == "# Title\n\nbgt-status: *bestaand*"
    assert call(f"{server}/redirect") == "# Title\n\nbgt-status: *bestaand*"
    first = call(f"{server}/long")
    assert first.endswith("[characters 0-40000 of 50000; continue with start=40000]")
    assert len(call(f"{server}/long", start=40000)) == 10000


def test_fetch_errors_are_tool_errors(server):
    for url in ("file:///etc/hosts", "http://[::1", "http://example.org/\npath"):
        with pytest.raises(ToolError, match="only valid http and https URLs"):
            call(url)
    with pytest.raises(ToolError, match="HTTP 404"):
        call(f"{server}/missing")
    with pytest.raises(ToolError, match="ConnectError"):
        call("http://127.0.0.1:9/")


def test_page_and_text_helpers():
    assert tools.page("abcdef", -50, 3) == "abc\n\n[characters 0-3 of 6; continue with start=3]"
    assert tools.as_text(b"", "text/html") == ""
    assert tools.as_text(b"{}", "application/json") == "{}"
    assert tools.as_text(b"\x00\x01", "image/png") == "[binary content: image/png, 2 bytes]"
    assert tools.fetchable("https://docs.geostandaarden.nl/imgeo/catalogus/bgt/#x") == "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/"


def test_agent_inspect_fetches_and_submits(tmp_path, server):
    """Inspect's prompt and submit tool, the fetch in the conversation, and source 1 for the page it read."""
    page = f"{server}/page"
    steps = [ModelOutput.for_tool_call("mockllm/model", "fetch", {"url": page}), ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": ANSWER})]
    [log] = eval(airco(agent="inspect", ids="imgeo-G04-03"), model=get_model("mockllm/model", custom_outputs=steps), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    assert sample.messages[0].role == "system" and "submit" in sample.messages[0].text
    assert [m.role for m in sample.messages[1:]] == ["user", "assistant", "tool", "assistant"]
    assert (sample.output.completion, sample.scores["quality"].value["correct"]) == (ANSWER, 1)
    assert (log.eval.metadata["agent"], log.eval.metadata["setup"]) == ("inspect", 1)
    assert sample.scores["source"].metadata["retrieved"] == {page: "other"}


def test_show_on_map_counts_the_places_and_rejects_what_is_not_geojson():
    show = tools.show_on_map()
    square = {"type": "Polygon", "coordinates": [[[5.9, 51.9], [5.91, 51.9], [5.91, 51.91], [5.9, 51.9]]]}
    collection = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": square, "properties": {}}, {"type": "Feature", "geometry": None}]}
    assert asyncio.run(show(geojson=collection)) == "1 places shown on the map."
    for bad in ({"type": "FeatureCollection"}, {"type": "Point", "coordinates": "here"}, {"features": []}):
        with pytest.raises(ToolError):
            asyncio.run(show(geojson=bad))


def test_show_on_map_url_errors_are_tool_errors(server):
    show = tools.show_on_map()
    point = {"type": "Point", "coordinates": [5.9, 51.98]}
    for arguments in (
        {"geojson": point, "url": f"{server}/map"},
        {},
        {"url": f"{server}/missing"},
        {"url": f"{server}/notjson"},
        {"url": "file:///etc/passwd"},
    ):
        with pytest.raises(ToolError):
            asyncio.run(show(**arguments))


def test_show_on_map_url_is_recorded_in_the_store_and_rescore_does_not_fetch_again(tmp_path):
    from airco_harness import dataset

    must = json.loads((dataset.TESTSETS_DIR / "dsfl/samples/dsfl-04/expected.json").read_text(encoding="utf-8"))["must"]
    panden = json.loads(sources.path("dsfl/bag-amersfoort-sport-panden.geojson").read_text(encoding="utf-8"))["features"]
    geojson = {"type": "FeatureCollection", "features": [f for f in panden if f["properties"]["identificatie"] in must]}
    body = json.dumps(geojson).encode()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_port}/map"
    MAP_DOCUMENT["body"] = body
    try:
        steps = [
            ModelOutput.for_tool_call("mockllm/model", "show_on_map", {"url": url}),
            ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de kaart."}),
        ]
        [log] = eval(
            airco(testset="dsfl", agent="inspect", ids="dsfl-04"),
            model=get_model("mockllm/model", custom_outputs=steps),
            log_dir=str(tmp_path),
            display="none",
        )
    finally:
        httpd.shutdown()
        httpd.server_close()
        MAP_DOCUMENT.clear()
    [sample] = log.samples
    assert sample.messages[3].role == "tool" and sample.messages[3].text == f"{len(must)} places shown on the map."
    assert "FeatureCollection" not in sample.messages[3].text
    assert sample.store["show_on_map"] == {url: geojson}
    expected = {"correct": 1, "complete": 1.0, "invented": 0, "parseable": 1}
    assert sample.scores["quality"].value == expected
    rescored = subprocess.run(["airco-rescore", log.location, "--out", str(tmp_path / "rescore")], capture_output=True, text=True)
    assert rescored.returncode == 0, rescored.stdout + rescored.stderr


def test_agent_inspect_gets_show_on_map_only_in_a_test_set_with_a_map_question(tmp_path):
    """The map of the right panden is the answer for dsfl-04, whatever the agent submits."""
    from airco_harness import dataset

    must = json.loads((dataset.TESTSETS_DIR / "dsfl/samples/dsfl-04/expected.json").read_text(encoding="utf-8"))["must"]
    panden = json.loads(sources.path("dsfl/bag-amersfoort-sport-panden.geojson").read_text(encoding="utf-8"))["features"]
    geojson = {"type": "FeatureCollection", "features": [f for f in panden if f["properties"]["identificatie"] in must]}
    steps = [
        ModelOutput.for_tool_call("mockllm/model", "show_on_map", {"geojson": geojson}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de kaart."}),
    ]
    [log] = eval(
        airco(testset="dsfl", agent="inspect", ids="dsfl-04"), model=get_model("mockllm/model", custom_outputs=steps), log_dir=str(tmp_path), display="none"
    )
    [sample] = log.samples
    assert sample.messages[3].role == "tool" and sample.messages[3].text == f"{len(must)} places shown on the map."
    assert sample.scores["quality"].value == {"correct": 1, "complete": 1.0, "invented": 0, "parseable": 1}
    assert dataset.asks_for_map("dsfl") and not dataset.asks_for_map("imgeo")


def test_plot_series_validates_and_agent_scores_the_call_not_the_answer(tmp_path):
    from airco_harness import dataset

    expected = json.loads((dataset.TESTSETS_DIR / "dsfl/samples/dsfl-08/expected.json").read_text(encoding="utf-8"))
    data = {
        "points": [{"date": date, "value": value} for date, value in expected["points"].items()],
        "unit": "m",
        "reference_plane": "NAP",
        "connect_gaps": False,
    }
    plot = tools.plot_series()
    assert asyncio.run(plot(data=data)) == "11 daily entries shown in the plot."
    with pytest.raises(ToolError):
        asyncio.run(plot(data={**data, "points": [{"date": "2023-02-30", "value": 1}]}))
    steps = [
        ModelOutput.for_tool_call("mockllm/model", "plot_series", {"data": data}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de grafiek."}),
    ]
    [log] = eval(
        airco(testset="dsfl", agent="inspect", ids="dsfl-08"),
        model=get_model("mockllm/model", custom_outputs=steps),
        log_dir=str(tmp_path),
        display="none",
    )
    [sample] = log.samples
    assert sample.scores["quality"].value == {"correct": 1, "complete": 1.0, "invented": 0, "parseable": 1}
    assert dataset.asks_for_series("dsfl") and not dataset.asks_for_series("imgeo")
