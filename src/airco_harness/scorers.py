"""Thin Inspect wrappers around the scoring rules in validators/.

The scorers are named quality and source in the logs; source is also the score key it fills.
"""

from __future__ import annotations

import asyncio
import json
import re

from inspect_ai.model import ChatMessage, ContentToolUse
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState

from validators import rules, source_check


def tool_uses(messages: list[ChatMessage]) -> list[dict]:
    """Every tool use in the conversation, in order, with its arguments and whether it failed.

    Two kinds: a tool call the agent makes (fetch, Claude Code's WebFetch), answered by a tool
    message; and a tool the model's provider runs on its own servers (Anthropic's and Mistral's
    web search, Anthropic's web fetch and code execution), which Inspect keeps as a content
    block of the assistant message. What an agent does outside the conversation is not here.
    """
    results = {m.tool_call_id: m for m in messages if m.role == "tool"}
    out = []
    for m in messages:
        if m.role != "assistant":
            continue
        for call in m.tool_calls or []:
            result = results.get(call.id)
            out.append({"tool": call.function, "arguments": call.arguments or {}, "failed": result is None or result.error is not None, "server": False})
        if not isinstance(m.content, str):
            for block in m.content:
                if isinstance(block, ContentToolUse):
                    out.append({"tool": block.name, "arguments": _arguments(block), "failed": bool(block.error), "server": True})
    return out


def _arguments(block: ContentToolUse) -> dict:
    arguments = block.arguments
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except ValueError:
            return {}
    return arguments if isinstance(arguments, dict) else {}


def map_shown(messages: list[ChatMessage]) -> str:
    """The GeoJSON of the last show_on_map call that succeeded, as JSON text, or "" when the agent showed no map.
    The last call counts because a new call replaces the map. Claude Code names the tool mcp__map__show_on_map."""
    shown = [u["arguments"].get("geojson") for u in tool_uses(messages) if u["tool"].endswith("show_on_map") and not u["failed"]]
    if not shown:
        return ""
    return shown[-1] if isinstance(shown[-1], str) else json.dumps(shown[-1], ensure_ascii=False)


URL_IN_CODE = re.compile(r"https?://[^\s'\"<>`|\\]+")
CODE_ARGUMENTS = ("command", "code")  # Claude Code's Bash, a provider's code execution


def _urls(use: dict) -> list[str]:
    """The url argument of a fetch, or every URL in the shell command or code of a tool use."""
    url = use["arguments"].get("url")
    if isinstance(url, str):
        return [url]
    code = " ".join(v for k, v in use["arguments"].items() if k in CODE_ARGUMENTS and isinstance(v, str))
    return [u.rstrip(".,;:)]}") for u in URL_IN_CODE.findall(code)]


def retrievals(messages: list[ChatMessage]) -> list[dict]:
    """Every web retrieval in the conversation: a tool use with a url argument, or a URL in a shell
    command or code that ran, as when an agent uses curl. A search is not a retrieval."""
    return [{"tool": use["tool"], "url": url, "status": 0 if use["failed"] else 200} for use in tool_uses(messages) for url in _urls(use)]


@scorer(name="quality", metrics={"correct": [mean(), stderr()], "complete": [mean(), stderr()], "invented": [mean(), stderr()], "parseable": [mean()]})
def quality():
    """correct, complete, invented and parseable from the rule named in the sample's expected.json.
    The answer is the last message, or for the rule map, what the agent showed on the map."""

    async def score(state: TaskState, target: Target) -> Score:
        case = rules.Case.load(target.text)
        answer = map_shown(state.messages) if case.rule == "map" else state.output.completion
        result = await asyncio.to_thread(rules.assess, answer, case)
        return Score(value=result.score_value(), answer=answer, explanation=result.explanation, metadata={"rule": case.rule, **result.details})

    return score


@scorer(name="source", metrics={"source": [mean(), stderr()]})
def source():
    """source from the retrievals in the conversation, against the allowlist of the sample's standard."""

    async def score(state: TaskState, target: Target) -> Score:
        uses = tool_uses(state.messages)
        value, details = source_check.assess(retrievals(state.messages), state.metadata["standard"])
        tools = {"tool_calls": len(uses), "tools": sorted({u["tool"] for u in uses})}
        return Score(value={"source": value}, explanation=f"retrieved: {details['retrieved']}", metadata={**details, **tools})

    return score


BY_NAME = {"quality": quality, "source": source}
