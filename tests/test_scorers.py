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
        {"tool": "WebFetch", "url": "https://example.org/missing", "status": 0},
        {"tool": "WebFetch", "url": "https://example.org/unanswered", "status": 0},
    ]
    assert retrievals([]) == []
