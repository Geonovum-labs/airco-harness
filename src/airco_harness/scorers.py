"""Thin Inspect wrappers around the scoring rules in validators/.

The scorers are named quality and source in the logs; source is also the score key it fills.
"""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse

from inspect_ai.model import ChatMessage, ContentToolUse
from inspect_ai.scorer import Score, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState

from validators import rules, source_check


def tool_uses(messages: list[ChatMessage]) -> list[dict]:
    """Every tool use in the conversation, in order, with its arguments, whether it failed and the error it gave.

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
            error = "no answer" if result is None else result.error.message if result.error is not None else None
            out.append({"tool": call.function, "arguments": call.arguments or {}, "failed": error is not None, "error": error, "server": False})
        if not isinstance(m.content, str):
            for block in m.content:
                if isinstance(block, ContentToolUse):
                    out.append(
                        {
                            "tool": block.name,
                            "arguments": _arguments(block),
                            "failed": bool(block.error),
                            "error": str(block.error) if block.error else None,
                            "server": True,
                        }
                    )
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


# A URL right after xmlns= in XML, or after PREFIX in SPARQL or Turtle, names a namespace; nothing is fetched from it.
NAMESPACE_BEFORE = re.compile(r"(?:xmlns(?::[\w-]+)?\s*=\s*\\?[\"']?|@?prefix\s+[\w-]*:\s*<)$", re.IGNORECASE)


def _urls(use: dict) -> list[str]:
    """The url argument of a fetch, or every URL in the shell command or code of a tool use except a namespace."""
    url = use["arguments"].get("url")
    if isinstance(url, str):
        return [url]
    code = " ".join(v for k, v in use["arguments"].items() if k in CODE_ARGUMENTS and isinstance(v, str))
    return [m[0].rstrip(".,;:)]}") for m in URL_IN_CODE.finditer(code) if not NAMESPACE_BEFORE.search(code[max(0, m.start() - 40) : m.start()])]


HTTP_STATUS = re.compile(r"\b(?:HTTP|status code)[: ]+([1-5]\d\d)\b")
# What a failed command prints when a request got an HTTP error: Python's urllib, requests, curl -f, and curl -w "%{http_code}".
# Only 4xx and 5xx: a failed command never turns into a retrieval that worked.
OUTPUT_STATUS = re.compile(
    r"HTTP Error ([45]\d\d)\b|\b([45]\d\d) (?:Client|Server) Error\b|returned error: ([45]\d\d)\b|^\s*(?:\w+:)?([45]\d\d)\s*$", re.MULTILINE
)


# A line such as "pdok:404" that a command printed with curl -w "pdok:%{http_code}": a label of the agent's own and a code.
LABELLED_STATUS = re.compile(r"^\s*([A-Za-z][\w.-]*):(\d{3})\s*$", re.MULTILINE)


def labelled_line(output: str, url: str) -> str | None:
    """The "label:code" line of a command's output whose label is part of the URL's host, as "pdok" of api.pdok.nl."""
    host = urllib.parse.urlsplit(url).netloc.lower()
    return next((m[0].strip() for m in LABELLED_STATUS.finditer(output) if m[1].lower() in host), None)


def _status(use: dict, url: str) -> int:
    """200 for a retrieval that worked; for one that failed, the HTTP status its error names, else 0.

    The fetch tool fails with "HTTP 404". A shell command or code prints its own errors. A "label:code" line whose
    label is part of the URL's host gives that URL's status; any other status in the output counts only when the
    command holds one URL, as with several it is not known which URL got it. A curl that got a 404 without -f still
    exits 0, so it counts as worked."""
    if not use["failed"]:
        return 200
    error = use["error"] or ""
    if use["tool"] in ("Bash", "code_execution"):
        line = labelled_line(error, url)
        if line:
            code = int(line.rsplit(":", 1)[1])
            return code if 400 <= code < 600 else 0
        if len(set(_urls(use))) != 1:
            return 0
        found = OUTPUT_STATUS.search(error)
        return int(next(g for g in found.groups() if g)) if found else 0
    found = HTTP_STATUS.search(error)
    return int(found[1]) if found else 0


def retrievals(messages: list[ChatMessage]) -> list[dict]:
    """Every web retrieval in the conversation: a tool use with a url argument, or a URL in a shell
    command or code that ran, as when an agent uses curl. A search is not a retrieval.
    A failed retrieval also carries its error, its HTTP status when known, and for a command with several URLs
    "shared", as its output is about all of them."""
    out = []
    for use in tool_uses(messages):
        urls = _urls(use)
        shared = len(set(urls)) > 1
        for url in urls:
            failed = {"error": use["error"], **({"shared": True} if shared else {})} if use["failed"] else {}
            out.append({"tool": use["tool"], "url": url, "status": _status(use, url), **failed})
    return out


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
