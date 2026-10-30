"""The Inspect scorer wrappers, run through a real eval with fixed answers and no model calls."""

import json

from inspect_ai import Task, eval
from inspect_ai.model import ChatMessageAssistant, ChatMessageTool, ModelOutput
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.tool import ToolCall, ToolCallError

from airco_harness import dataset
from airco_harness.scorers import quality, retrievals, source

# Two copies of the one sample: a right answer from the adopted catalog, and the answer cheap models give after also reading the working draft.
ANSWERS = {
    "right": '```json\n{"objecttype": "OverigBouwwerk", "type": "bassin"}\n```',
    "wrong": '{"objecttype": "Waterdeel", "type": "zwembad"}',
}
RETRIEVALS = {
    "right": [("https://docs.geostandaarden.nl/imgeo/catalogus/bgt/", None)],
    "wrong": [("https://geonovum.github.io/IMGeo-dev/catalogus/bgt/", None), ("https://docs.geostandaarden.nl/imgeo/catalogus/bgt/", None)],
}


def fetch_messages(urls: list[tuple[str, str | None]], tool: str = "WebFetch") -> list:
    """An assistant turn that calls a web tool per URL, and the tool's answers, as Claude Code's conversation looks in the log."""
    calls = [ToolCall(id=f"call-{i}", function=tool, arguments={"url": url, "prompt": "read"}) for i, (url, _) in enumerate(urls)]
    results = [
        ChatMessageTool(
            content="page text" if error is None else "", tool_call_id=f"call-{i}", function=tool, error=ToolCallError("unknown", error) if error else None
        )
        for i, (_, error) in enumerate(urls)
    ]
    return [ChatMessageAssistant(content="", tool_calls=calls), *results]


@solver
def fixed_answer():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.messages.extend(fetch_messages(RETRIEVALS[state.sample_id]))
        state.output = ModelOutput.from_content("mockllm/model", ANSWERS[state.sample_id])
        return state

    return solve


def run_eval(tmp_path):
    [sample] = dataset.load(ids=["imgeo-G04-03"])
    task = Task(dataset=[sample.model_copy(update={"id": name}) for name in ANSWERS], solver=fixed_answer(), scorer=[quality(), source()])
    [log] = eval(task, model="mockllm/model", log_dir=str(tmp_path), display="none")
    return log


def test_scores_land_in_the_log_per_sample(tmp_path):
    log = run_eval(tmp_path)
    assert log.status == "success"
    scores = {s.id: {name: sc.value for name, sc in s.scores.items()} for s in log.samples}
    assert scores == {
        "right": {"quality": {"correct": 1, "complete": 1.0, "invented": 0, "parseable": 1}, "source": {"source": 1}},
        "wrong": {"quality": {"correct": 0, "complete": 0.0, "invented": 1, "parseable": 1}, "source": {"source": 0}},
    }


def test_metrics_per_key(tmp_path):
    log = run_eval(tmp_path)
    metrics = {f"{s.name}.{m}": round(v.value, 4) for s in log.results.scores for m, v in s.metrics.items()}
    assert metrics["correct.mean"] == 0.5
    assert metrics["invented.mean"] == 0.5
    assert metrics["source.mean"] == 0.5


def test_source_explains_which_urls_it_saw(tmp_path):
    log = run_eval(tmp_path)
    sample = next(s for s in log.samples if s.id == "wrong")
    assert json.loads(json.dumps(sample.scores["source"].metadata))["retrieved"] == {
        "https://geonovum.github.io/IMGeo-dev/catalogus/bgt/": "non_authoritative",
        "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/": "authoritative",
    }


def test_server_side_tools_count_as_tool_uses_and_a_server_fetch_as_a_retrieval():
    """Anthropic and Mistral run web search, and Anthropic web fetch and code execution, on their own servers; Inspect keeps them as content blocks."""
    from inspect_ai.model import ContentToolUse

    from airco_harness.scorers import tool_uses

    page = "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/"
    blocks = [
        ContentToolUse(tool_type="web_search", id="s1", name="web_search", arguments='{"query": "BGT zwembad"}', result="results"),
        ContentToolUse(tool_type="web_search", id="f1", name="web_fetch", arguments=json.dumps({"url": page}), result="page"),
        ContentToolUse(tool_type="code_execution", id="c1", name="code_execution", arguments="not json", result="", error="failed"),
    ]
    messages = [ChatMessageAssistant(content=blocks), *fetch_messages([("https://example.org/", None)])]
    uses = tool_uses(messages)
    assert [(u["tool"], u["server"], u["failed"]) for u in uses] == [
        ("web_search", True, False),
        ("web_fetch", True, False),
        ("code_execution", True, True),
        ("WebFetch", False, False),
    ]
    assert retrievals(messages) == [{"tool": "web_fetch", "url": page, "status": 200}, {"tool": "WebFetch", "url": "https://example.org/", "status": 200}]


def test_retrievals_are_the_url_tool_calls_with_their_outcome():
    page = "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/"
    messages = fetch_messages([(page, None), ("https://example.org/missing", "404 Not Found")])
    messages.append(ChatMessageAssistant(content="", tool_calls=[ToolCall(id="call-x", function="Bash", arguments={"command": "ls"})]))
    messages.append(
        ChatMessageAssistant(content="", tool_calls=[ToolCall(id="call-y", function="WebFetch", arguments={"url": "https://example.org/unanswered"})])
    )
    assert retrievals(messages) == [
        {"tool": "WebFetch", "url": page, "status": 200},
        {"tool": "WebFetch", "url": "https://example.org/missing", "status": 0, "error": "404 Not Found"},
        {"tool": "WebFetch", "url": "https://example.org/unanswered", "status": 0, "error": "no answer"},
    ]
    assert retrievals([]) == []


def test_the_map_is_the_last_show_on_map_call_that_succeeded():
    from airco_harness.scorers import map_shown

    def call(i: int, name: str, geojson: object, error: str | None = None) -> list:
        return [
            ChatMessageAssistant(content="", tool_calls=[ToolCall(id=f"map-{i}", function=name, arguments={"geojson": geojson})]),
            ChatMessageTool(content="", tool_call_id=f"map-{i}", function=name, error=ToolCallError("unknown", error) if error else None),
        ]

    first, second = {"type": "FeatureCollection", "features": []}, {"type": "Point", "coordinates": [5.9, 51.98]}
    assert map_shown(fetch_messages([("https://example.org/", None)])) == ""
    assert map_shown([*call(0, "show_on_map", first), *call(1, "mcp__map__show_on_map", second)]) == json.dumps(second)
    assert map_shown([*call(0, "show_on_map", first), *call(1, "show_on_map", "not geojson", "invalid")]) == json.dumps(first)
    assert map_shown(call(0, "mcp__map__show_on_map", json.dumps(second))) == json.dumps(second)


def test_a_url_in_a_shell_command_or_code_that_ran_is_a_retrieval():
    """Claude Code often fetches with curl or a script in Bash; the URLs in the command count, as the command ran."""
    bag = "https://api.pdok.nl/kadaster/bag/ogc/v2/collections/pand/items?f=json&limit=5"
    command = f'cd /tmp && curl -s "{bag}" | head; echo "(see https://www.pdok.nl/)."'
    messages = [
        ChatMessageAssistant(content="", tool_calls=[ToolCall(id="b1", function="Bash", arguments={"command": command, "description": "x"})]),
        ChatMessageTool(content="ok", tool_call_id="b1", function="Bash"),
        ChatMessageAssistant(content="", tool_calls=[ToolCall(id="b2", function="Bash", arguments={"command": "curl https://example.org/down"})]),
        ChatMessageTool(content="", tool_call_id="b2", function="Bash", error=ToolCallError("unknown", "exit 7")),
        ChatMessageAssistant(content="", tool_calls=[ToolCall(id="b3", function="Read", arguments={"file_path": "/tmp/notes-https://x"})]),
        ChatMessageTool(content="", tool_call_id="b3", function="Read"),
    ]
    assert retrievals(messages) == [
        {"tool": "Bash", "url": bag, "status": 200},
        {"tool": "Bash", "url": "https://www.pdok.nl/", "status": 200},
        {"tool": "Bash", "url": "https://example.org/down", "status": 0, "error": "exit 7"},
    ]


def test_a_failed_retrieval_keeps_the_http_status_its_tool_names():
    """The fetch tool fails with "HTTP 404"; a network error has no status; a shell command names none per URL."""
    calls = [("f1", "fetch", {"url": "https://example.org/gone"}, "HTTP 404"), ("f2", "fetch", {"url": "https://example.org/secret"}, "HTTP 401"),
             ("f3", "fetch", {"url": "https://example.org/far"}, "ConnectError: All connection attempts failed"),
             ("b1", "Bash", {"command": "curl https://example.org/x"}, "Exit code 22 HTTP 404")]  # fmt: skip
    messages = []
    for call_id, tool, arguments, error in calls:
        messages.append(ChatMessageAssistant(content="", tool_calls=[ToolCall(id=call_id, function=tool, arguments=arguments)]))
        messages.append(ChatMessageTool(content="", tool_call_id=call_id, function=tool, error=ToolCallError("unknown", error)))
    assert [(r["url"].rsplit("/", 1)[-1], r["status"]) for r in retrievals(messages)] == [("gone", 404), ("secret", 401), ("far", 0), ("x", 0)]


def test_a_status_in_the_output_of_a_failed_command_counts_only_for_a_command_with_one_url():
    traceback = "Exit code 1\nTraceback (most recent call last):\n  ...\nurllib.error.HTTPError: HTTP Error 400: Bad Request"
    calls = [("p1", {"command": "python3 - <<EOF\nurlopen('https://service.pdok.nl/lv/bag/wfs/v2_0?'+q)\nEOF"}, traceback),
             ("c1", {"command": 'curl -s -w "%{http_code}" "https://service.pdok.nl/lv/bag/wfs/v2_0?x=1"'}, "Exit code 1\n400\n<?xml ...>"),
             ("c2", {"command": "curl -f https://example.org/a"}, "Exit code 22\ncurl: (22) The requested URL returned error: 404"),
             ("c3", {"command": "curl https://example.org/b ; curl https://example.org/c"}, "Exit code 7\npdok:404\noverpass:000"),
             ("c4", {"command": "curl https://example.org/d"}, "Exit code 7\ncurl: (7) Failed to connect"),
             ("c5", {"command": 'curl -w "%{http_code}" https://example.org/e | jq .x'}, "Exit code 5\n200\njq: error")]  # fmt: skip
    messages = []
    for call_id, arguments, error in calls:
        messages.append(ChatMessageAssistant(content="", tool_calls=[ToolCall(id=call_id, function="Bash", arguments=arguments)]))
        messages.append(ChatMessageTool(content="", tool_call_id=call_id, function="Bash", error=ToolCallError("unknown", error)))
    assert [r["status"] for r in retrievals(messages)] == [400, 400, 404, 0, 0, 0, 0]


def test_a_namespace_in_a_command_is_not_a_retrieval():
    command = (
        'curl -G "https://service.pdok.nl/lv/bag/wfs/v2_0" --data-urlencode '
        '\'FILTER=<Filter xmlns="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"/>\' ; '
        "curl --data-urlencode 'query=PREFIX bag: <https://bag.basisregistraties.overheid.nl/def/bag#> SELECT ?s' https://bag.basisregistraties.overheid.nl/sparql"
    )
    messages = [ChatMessageAssistant(content="", tool_calls=[ToolCall(id="b1", function="Bash", arguments={"command": command})]),
                ChatMessageTool(content="ok", tool_call_id="b1", function="Bash")]  # fmt: skip
    assert [r["url"] for r in retrievals(messages)] == ["https://service.pdok.nl/lv/bag/wfs/v2_0", "https://bag.basisregistraties.overheid.nl/sparql"]


def test_a_labelled_status_line_belongs_to_the_url_whose_host_has_the_label():
    """curl -w "pdok:%{http_code}" for two URLs: each URL gets its own line; 000 is no connection, so no status."""
    command = (
        'curl -w "pdok:%{http_code}" "https://api.pdok.nl/lv/bag/ogc/v2/collections" ; curl -w "overpass:%{http_code}" "https://overpass-api.de/api/status"'
    )
    messages = [ChatMessageAssistant(content="", tool_calls=[ToolCall(id="b1", function="Bash", arguments={"command": command})]),
                ChatMessageTool(content="", tool_call_id="b1", function="Bash", error=ToolCallError("unknown", "Exit code 7\npdok:404\noverpass:000"))]  # fmt: skip
    assert [(r["url"].split("/")[2], r["status"], r.get("shared")) for r in retrievals(messages)] == [("api.pdok.nl", 404, True), ("overpass-api.de", 0, True)]
