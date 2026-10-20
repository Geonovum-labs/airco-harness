"""The fetch tool against a local web server and bad input, and the agent inspect end to end with a scripted model."""

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.tool import ToolError

from airco_harness import tools
from airco_harness.tasks import airco

ANSWER = json.dumps({"objecttype": "OverigBouwwerk", "type": "bassin"})


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
