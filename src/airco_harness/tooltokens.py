"""The tokens of the tool definitions a model call sent, counted exactly once per tool set.

A provider reports a call's input as a whole. The tool definitions are the difference between the token count of a
request with them and without them, which Anthropic's count_tokens gives for free; it includes the text the provider
adds for tools, such as its own web search tool. airco-report writes the counts of a measurement's tool sets to
tool-tokens.json beside its report, and the site reads them from there. Other providers have no such count.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from inspect_ai.log import read_eval_log

FILE = "tool-tokens.json"
PROBE = [{"role": "user", "content": "x"}]
ATTACHMENT = re.compile(r"attachment://([0-9a-f]{32})")


def tools_of(event, attachments: dict[str, str]) -> list | None:
    """The tool definitions of a model call as its request sent them, with the log's attachments resolved."""
    request = (event.call.request if event.call else None) or {}
    if not request.get("tools"):
        return None
    text = ATTACHMENT.sub(lambda m: json.dumps(attachments.get(m[1], m[0]))[1:-1], json.dumps(request["tools"], ensure_ascii=False))
    return json.loads(text)


def key(model: str, tools: list) -> str:
    """The key of a tool set for a model in tool-tokens.json."""
    return hashlib.sha256(f"{model}\0{json.dumps(tools, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}".encode()).hexdigest()[:24]


def count(log_dir: Path, client) -> dict[str, dict]:
    """Per tool set of an Anthropic model in the logs: the model, the number of tools and their tokens."""
    counts: dict[str, dict] = {}
    for path in sorted(Path(log_dir).glob("*.eval")):
        for sample in read_eval_log(str(path)).samples or []:
            for event in sample.events:
                tools = tools_of(event, sample.attachments) if event.event == "model" else None
                if not tools or not event.model.startswith("anthropic/") or key(event.model, tools) in counts:
                    continue
                model = event.call.request.get("model") or event.model.split("/", 1)[1]
                with_tools = client.messages.count_tokens(model=model, messages=PROBE, tools=tools).input_tokens
                without = client.messages.count_tokens(model=model, messages=PROBE).input_tokens
                counts[key(event.model, tools)] = {"model": event.model, "tools": len(tools), "tokens": with_tools - without}
    return counts


def write(log_dir: Path, out: Path) -> None:
    """Count the tool sets of the logs into out/tool-tokens.json; without an Anthropic key, leave it as it is."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"no ANTHROPIC_API_KEY: {FILE} not counted; the site estimates tool definitions from their length")
        return
    import anthropic

    counts = count(log_dir, anthropic.Anthropic())
    if counts:
        (out / FILE).write_text(json.dumps(counts, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{len(counts)} tool set{'' if len(counts) == 1 else 's'} counted; {out / FILE}")


def read(report_dir: Path) -> dict[str, dict]:
    file = report_dir / FILE
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}
