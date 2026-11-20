"""The dataset of the site: every run of every committed measurement, read from the logs.

airco-pages writes it as data.json, and the pages filter, aggregate and compare
it in the browser (assets/stats.js). It is read from the logs rather than from
runs.csv, so a measurement made before a column existed still takes part, with
what its logs record. A map question is drawn against its expected outcome and
reference extract at the commit its log records, since a sample id can mean
another question at another commit. Pand geometry goes into a file per reference
extract and commit, which a page fetches only when it draws a map.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from inspect_ai.analysis import SampleSummary, samples_df
from inspect_ai.log import read_eval_log
from inspect_ai.model import ModelUsage, compute_model_cost

from validators import geo, source_check, sources

from . import mcpwire, report, scorers, tooltokens
from .models import Price, load_prices
from .tools import MAP_STORE

QUALITY = ["correct", "complete", "invented", "parseable", "source"]
RUN_FIELDS = [
    "model",
    "agent",
    "variant",
    "sample",
    "epoch",
    "failed",
    "limit",
    *QUALITY,
    "cost",
    "tokens",
    "tool_calls",
    "skills",
    "skill_used",
    "total_time_s",
    "explanation",
    "mcp_server",
    "mcp_protocol",
    "log",
]


def _clean(value: object) -> object:
    """JSON without NaN, which browsers refuse: a missing number is null."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _distinct(series: pd.Series) -> list:
    return sorted({v for v in series.dropna().tolist() if v != ""}, key=str)


def question(text: object) -> str:
    """The question as the agent got it. samples_df writes the input with its role, "user:" and a newline;
    a single user message loses that prefix, a conversation of several messages keeps its roles."""
    text = str(text or "").strip()
    single = re.fullmatch(r"user:\n(.*)", text, re.DOTALL)
    return single[1].strip() if single and not re.search(r"\n(?:user|assistant|system|tool):\n", single[1]) else text


def questions(log_dir: Path) -> dict[str, str]:
    """Per sample in id order, the question of its first run in the logs."""
    df = samples_df(str(log_dir), columns=SampleSummary, quiet=True).drop_duplicates("id").sort_values("id")
    return {sample: question(text) for sample, text in df[["id", "input"]].itertuples(index=False)}


ERROR_LINE = re.compile(r"^(?:[\w.]+(?:Error|Exception)\b.*|curl: \(\d+\).*|.*returned error: .*)$")


def error_line(output: str, url: str = "", shared: bool = False) -> str:
    """The line that says why a retrieval failed: a "label:code" line of this URL, the final exception of a traceback,
    or curl's error, else the first line. A shell command's output starts with "Exit code n", which says only that it
    failed. For a command with several URLs, only a line labelled for this URL; the rest is about the command."""
    own = scorers.labelled_line(output, url) if url else None
    if own:
        return own
    if shared:
        return ""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    telling = [line for line in lines if ERROR_LINE.match(line)]
    if telling:
        return telling[-1][:200]
    rest = [line for line in lines if not re.fullmatch(r"Exit code \d+", line)]
    return (rest[0] if rest else lines[0] if lines else "")[:200]


DETAILS = 12  # properties per place
DETAIL_CHARS = 300


def details(properties: object) -> dict[str, str]:
    """What the agent said about a place: the properties of its GeoJSON feature as text, the first DETAILS of them."""
    if not isinstance(properties, dict):
        return {}
    text = {}
    for key, value in list(properties.items())[:DETAILS]:
        if value is None or value == "":
            continue
        shown = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        text[str(key)[:60]] = shown[:DETAIL_CHARS]
    return text


def places(messages: list, expected: dict, maps: dict) -> list[dict]:
    """Every place the agent showed with show_on_map: where it put it, the reference feature it matched
    (by the same rule as the scorer, else null), and its details."""
    shown = scorers.map_shown(messages, maps)
    try:
        collection = json.loads(shown) if shown else None
    except ValueError:
        return []
    features = collection.get("features") if isinstance(collection, dict) and collection.get("type") == "FeatureCollection" else [collection]
    reference = geo.Reference.load(expected["reference"], expected["commit"])
    out = []
    all_points = []
    for feature in features or []:
        if not isinstance(feature, dict):
            continue
        try:
            points = geo.points(feature)
        except ValueError:
            continue
        info = details(feature.get("properties"))
        for point in points:
            all_points.append(point)
            out.append({"lon": round(point.x, 6), "lat": round(point.y, 6), "details": info})
    if "allowed_optional" in expected:
        identifiers = reference.assign_points(all_points, expected["tolerance_m"], set(expected["must"]) | set(expected["allowed_optional"]))
    else:
        identifiers = [reference.nearest(point, expected["tolerance_m"]) for point in all_points]
    for place, identifier in zip(out, identifiers):
        place["pand"] = identifier
    return out


CALL_TEXT = 600  # characters of a message or of the arguments of a tool call
# Tokens per character of the JSON of a call's tool definitions, for an estimate where tool-tokens.json has no count.
# Anthropic's count_tokens gave 0.36 to 0.48 for the function tools of measurement smoke-dsfl-16-3m (19 November 2026),
# but a provider's own tools, such as its web search, cost thousands of tokens in a few characters: a rough estimate.
TOKENS_PER_TOOL_CHAR = 0.42
# The harness's own tools, which Claude Code reaches through a bridge named mcp__map or mcp__plot; and the inspect agent's.
HARNESS_TOOLS = {"show_on_map", "plot_series", "submit"}
AGENT_TOOLS = {"web_search", "fetch"}


def tool_kind(name: str, servers: list[str], with_mcp: bool) -> dict:
    """What a tool is: an MCP server's (with the server's name when it is known), a skill, the harness's, or the agent's own.

    Claude Code names an MCP tool mcp__<server>__<tool>. The inspect agent names it as the server does, with dots made
    underscores, which often starts with the server's name; one that does not, and is none of the agent's own tools, is
    an MCP tool of an unnamed server when the run had a server. The agents' own tools are capitalized in Claude Code."""
    if m := re.fullmatch(r"mcp__(.+?)__(.+)", name):
        server, tool = m[1], m[2]
        if tool in HARNESS_TOOLS:
            return {"kind": "harness", "name": tool}
        rest = tool[len(server) :].lstrip("._") if tool.startswith(server) else ""
        return {"kind": "mcp", "server": server, "name": rest or tool}
    if name in HARNESS_TOOLS:
        return {"kind": "harness", "name": name}
    if name == "Skill":
        return {"kind": "skill", "name": "Skill"}
    for server in servers:
        if name.startswith(server) and name[len(server) : len(server) + 1] in (".", "_"):
            return {"kind": "mcp", "server": server, "name": name[len(server) + 1 :]}
    if with_mcp and name not in AGENT_TOOLS and not name[:1].isupper():
        return {"kind": "mcp", "name": name}
    return {"kind": "builtin", "name": name}


def mcp_servers(metadata: dict) -> tuple[list[str], bool]:
    """The names of the MCP servers a run's variant gave, and whether it gave any, from the log's variant_form."""
    mcp = (metadata.get("variant_form") or {}).get("mcp")
    if isinstance(mcp, str):
        return [mcp.rstrip("/").split("/")[-2]] if "/" in mcp else [], True
    if isinstance(mcp, list) and mcp and isinstance(mcp[0], dict):
        return [s["name"] for s in mcp if s.get("name")], True
    return [], bool(mcp)


CALL_OUTPUT = 2000  # characters of what the model wrote


ATTACHMENT = re.compile(r"attachment://([0-9a-f]{32})")


def _clip(text: str, limit: int, attachments: dict[str, str]) -> dict:
    """The text, cut at `limit` characters, with its full length when it was cut. A log keeps a long or repeated text
    once, as an attachment, and refers to it from where it occurs; every reference is resolved first."""
    text = ATTACHMENT.sub(lambda m: attachments.get(m[1], m[0]), text)
    return {"text": text[:limit], "chars": len(text)} if len(text) > limit else {"text": text}


def _message(message, attachments: dict[str, str], kind) -> dict:
    """A message new in the call's input: its role, the tool it answers and what that tool is, and its text or error, clipped."""
    error = getattr(message, "error", None)
    text = error.message if error else message.text
    function = getattr(message, "function", None)
    return {"role": message.role, "tool": kind(function) if function else None, **_clip(text, CALL_TEXT, attachments)}


def tool_definitions(tokens: int, exact: bool, usage: ModelUsage, price: Price | None) -> dict:
    """The estimated tokens of a call's tool definitions, split as the provider billed them, and their price.

    The definitions open the prompt, so they are the first part a cache holds: they count as cache read as far as the
    call read from the cache, then as cache write, then as new input; [new input, cache read, cache write, output]."""
    read = min(tokens, usage.input_tokens_cache_read or 0)
    write = min(tokens - read, usage.input_tokens_cache_write or 0)
    rest = min(tokens - read - write, usage.input_tokens)
    part = ModelUsage(input_tokens=rest, input_tokens_cache_read=read, input_tokens_cache_write=write, output_tokens=0, total_tokens=rest + read + write)
    if price is None:
        return {"tokens": [rest, read, write, 0], "price": None, "exact": exact}
    prompt = usage.input_tokens + (usage.input_tokens_cache_read or 0) + (usage.input_tokens_cache_write or 0)
    rates = price.long_prompt if price.long_prompt and prompt > price.long_prompt.above else price
    return {"tokens": [rest, read, write, 0], "price": round(compute_model_cost(rates.cost(), part, price.cache_ttl(usage)), 6), "exact": exact}


def model_calls(
    events: list, prices: dict[str, Price], attachments: dict[str, str] | None = None, counts: dict | None = None, servers: tuple[list[str], bool] = ([], False)
) -> list[dict]:
    """Per model call of one run, in order: its event id (for the viewer), when it started and how long it took, why it
    stopped, how many messages and tool definitions it read, its tokens [new input, cache read, cache write, output] and
    exact price as the report counts it (null without a price), the messages new in its input, and its output.
    A message is new when no earlier call read it, by its id; the model's own earlier output is left out. A call whose
    conversation starts with another message than the first call's is "side": a separate conversation, such as the one
    Claude Code's web search runs."""
    calls, seen, attachments, counts = [], set(), attachments or {}, counts or {}
    kind = lambda name: tool_kind(name, *servers)  # noqa: E731
    # A log keeps the request of a model call for the first calls only; a later call with the same tools, by name, has their count.
    by_names: dict[tuple, dict] = {}
    main = None
    for event in events:
        if event.event != "model" or not event.output or not event.output.usage:
            continue
        usage, price = event.output.usage, prices.get(event.model)
        first = event.input[0].id if event.input else None
        main = main or first
        new = [m for m in event.input if (m.id or id(m)) not in seen]
        seen |= {m.id or id(m) for m in event.input}
        message = event.output.message
        tool_calls = (message.tool_calls or []) if message else []
        sent = tooltokens.tools_of(event, attachments)
        names = (event.model, tuple(t.name for t in event.tools))
        counted = counts.get(tooltokens.key(event.model, sent)) if sent else by_names.get(names)
        if sent and counted:
            by_names[names] = counted
        estimate = (
            round(TOKENS_PER_TOOL_CHAR * len(json.dumps(sent, ensure_ascii=False)))
            if sent
            else round(TOKENS_PER_TOOL_CHAR * sum(len(t.model_dump_json(exclude_none=True)) for t in event.tools))
        )
        calls.append({
            "event": event.uuid,
            "start": event.timestamp.isoformat() if event.timestamp else None,
            "seconds": round(event.working_time if event.working_time is not None else event.output.time or 0, 2),
            "stop": event.output.stop_reason,
            "messages": len(event.input),
            "tool_definitions": len(event.tools),
            "definitions": tool_definitions(counted["tokens"] if counted else estimate, counted is not None, usage, price),
            "tokens": [usage.input_tokens, usage.input_tokens_cache_read or 0, usage.input_tokens_cache_write or 0, usage.output_tokens],
            "price": round(price.call(usage, price.cache_ttl(usage)), 6) if price else None,
            "tools": [_called(c, kind) for c in tool_calls],
            "side": first != main,
            "new": [_message(m, attachments, kind) for m in new if m.role != "assistant"],
            "output": {**_clip(message.text if message else "", CALL_OUTPUT, attachments),
                       "tool_calls": [{"tool": _called(c, kind), **_clip(json.dumps(c.arguments, ensure_ascii=False), CALL_TEXT, attachments)} for c in tool_calls]},
        })  # fmt: skip
    return calls


def _called(call, kind) -> dict:
    """What a tool call called; for Claude Code's Skill tool, the skill it named."""
    tool = kind(call.function)
    if tool["kind"] == "skill":
        arguments = call.arguments or {}
        tool["name"] = str(arguments.get("skill") or arguments.get("command") or "Skill")
    return tool


def conversations(log_dir: Path, map_samples: dict[str, dict]) -> dict[tuple[str, str, int], dict[str, list]]:
    """Per run (log file, sample, epoch), what the conversation shows, read with the harness's current rules:
    "retrieved", the URLs that worked with their class for source; "errors", the ones that failed with their HTTP
    status when known and the line that says why; and for a map question "places", what the agent put on the map,
    matched to the reference extract at the commit of the log. A log scored under older retrieval rules therefore
    shows what they would find now; its scores are the ones in the log. "calls" are its model calls (model_calls)."""
    out: dict[tuple[str, str, int], dict[str, list]] = {}
    prices = load_prices()
    counts = tooltokens.read(log_dir.parent.parent)
    for path in sorted(log_dir.glob("*.eval")):
        log = read_eval_log(str(path))
        servers = mcp_servers(log.eval.metadata or {})
        for sample in log.samples or []:
            standard = (sample.metadata or {}).get("standard", "")
            ok: dict[str, dict] = {}
            failed: dict[tuple, dict] = {}
            for r in scorers.retrievals(sample.messages):
                if 200 <= r["status"] < 300:
                    ok.setdefault(r["url"], {"url": r["url"], "class": source_check.classify(r["url"], standard) if standard else "other"})
                    continue
                output = (r.get("error") or "").strip()
                error = error_line(output, r["url"], r.get("shared", False))
                entry = {"url": r["url"], "status": r["status"] or None, "error": error, "tool": r["tool"], "times": 0}
                if output and output != error:
                    entry["output"] = output[:1500]
                failed.setdefault((r["url"], r["status"], error), entry)["times"] += 1
            run = {
                "retrieved": list(ok.values()),
                "errors": list(failed.values()),
                "calls": model_calls(sample.events, prices, sample.attachments, counts, servers),
            }
            records = sample.store.get("mcp_calls")
            if records:
                run["mcp"] = sample.store.get("mcp_traffic") or mcpwire.traffic(records)
                run["mcp_messages"] = mcp_messages(records)
            if str(sample.id) in map_samples:
                run["places"] = places(sample.messages, map_samples[str(sample.id)], sample.store.get(MAP_STORE, {}))
            out[(path.name, str(sample.id), sample.epoch)] = run
    return out


def reference_file(reference: str, commit: str) -> str:
    """Where the site keeps the panden of a reference extract at a commit, relative to the site root."""
    return f"data/panden/{commit or 'working-tree'}/{reference.replace('/', '__')}"


def panden(reference: str, commit: str) -> dict:
    """The panden of an extract at a commit with their identificatie only, coordinates to 6 decimals (about 10 cm)."""

    def rounded(coordinates: list) -> list:
        return [rounded(c) for c in coordinates] if isinstance(coordinates[0], list) else [round(c, 6) for c in coordinates]

    features = json.loads(sources.read(sources.path(reference), commit))["features"]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"identificatie": geo.feature_id(f)},
                "geometry": {"type": f["geometry"]["type"], "coordinates": rounded(f["geometry"]["coordinates"])},
            }  # fmt: skip
            for f in features
        ],
    }


def started(log_dir: Path) -> str:
    """When the measurement began: the earliest creation time in its log headers, in UTC, so that two compare as strings.
    The log file names hold the same time, but with the sign of the UTC offset written as a dash."""
    created = [datetime.fromisoformat(read_eval_log(str(path), header_only=True).eval.created) for path in log_dir.glob("*.eval")]
    return min(created).astimezone(UTC).isoformat()


def measurement(name: str, log_dir: Path) -> tuple[dict, list[dict], dict]:
    """One measurement: its facts, its runs, and the map questions among its samples, keyed "<measurement>/<sample>"."""
    table = report.runs(str(log_dir))
    shown = report.maps(str(log_dir)) or {"samples": {}, "runs": []}
    on_map = {(r["model"], r["agent"], r["variant"], r["sample"], r["epoch"]): r for r in shown["runs"]}
    fetched = conversations(log_dir, shown["samples"])
    runs = []
    for row in table.to_dict("records"):
        seen = fetched.get((row["log"], row["sample"], row["epoch"]), {})
        run = {"m": name, **{k: row[k] for k in RUN_FIELDS}, "retrieved": seen.get("retrieved", []), "errors": seen.get("errors", [])}
        run["calls"] = seen.get("calls", [])
        if "mcp" in seen:
            run["mcp"], run["mcp_messages"] = seen["mcp"], seen["mcp_messages"]
        found = on_map.get((row["model"], row["agent"], row["variant"], row["sample"], row["epoch"]))
        if found:
            run["map"] = {k: found[k] for k in ("shown", "missing", "unmatched")} | {"places": seen.get("places", [])}
        runs.append(run)
    facts = {
        "name": name,
        "started": started(log_dir),
        "testsets": _distinct(table["testset"]),
        "testset_versions": _distinct(table["testset"] + " " + table["testset_version"]),
        "commits": _distinct(table["commit"]),
        "limits": {key: _distinct(table[f"{key}_limit"]) for key in ("cost", "token", "message", "time")},
        "runs": len(table),
        "failed": int(table["failed"].sum()),
        "at_limit": int(table["limit"].ne("").sum()),
        "cost": float(table["cost"].sum()),
        "samples": _distinct(table["sample"]),
        "models": _distinct(table["model"]),
        "agents": _distinct(table["agent"]),
        "variants": _distinct(table["variant"]),
        "questions": questions(log_dir),
    }
    maps = {
        f"{name}/{sample}": {
            "must": e["must"],
            "optional": len(e["allowed_optional"]) if "allowed_optional" in e else len(panden(e["reference"], e["commit"])["features"]) - len(e["must"]),
            **({"allowed_optional": e["allowed_optional"]} if "allowed_optional" in e else {}),
            "note": e["note"],
            "panden": reference_file(e["reference"], e["commit"]),
            "reference": e["reference"],
            "commit": e["commit"],
        }  # fmt: skip
        for sample, e in shown["samples"].items()
    }
    return facts, runs, maps


MCP_SHOWN_CHARS = 4_000  # Of each message sent and each answer, the site shows this much; the log keeps more.


def _shown(record: dict, key: str) -> dict:
    """A message as the site shows it: its start, and its full length when that is longer than the start."""
    text = record.get(key)
    if text is None:
        return {}
    length = record.get(f"{key}_chars", len(text))
    return {key: text[:MCP_SHOWN_CHARS], **({f"{key}_chars": length} if length > MCP_SHOWN_CHARS else {})}


def mcp_messages(records: list[dict]) -> list[dict]:
    """Every MCP message of a run as the site lists it: seconds since the first, server, method, tool, the protocol
    version it went under, HTTP status, the server's time in ms, the size of the answer, an error, and the start of
    what went in and out."""
    first = min((r["at"] for r in records if "at" in r), default=0)
    keep = ("server", "method", "tool", "status", "ms", "bytes", "error")
    return [
        {
            "s": round(r.get("at", first) - first, 1),
            **{k: r[k] for k in keep if k in r},
            "protocol": mcpwire.applied(r),
            **_shown(r, "sent"),
            **_shown(r, "received"),
        }
        for r in records
    ]


def mcp_file(run: dict) -> str:
    """Where the site keeps a run's MCP messages, relative to its measurement's folder, as app.js builds the path."""
    return f"mcp/{Path(run['log']).stem}/{run['sample']}-{run['epoch']}.json"


def calls_file(run: dict) -> str:
    """Where the site keeps a run's model calls, relative to its measurement's folder, as app.js builds the path."""
    return f"calls/{Path(run['log']).stem}/{run['sample']}-{run['epoch']}.json"


def dataset(parts: list[tuple[dict, list[dict], dict]]) -> dict:
    """All measurements, newest first, with their runs and the map questions of each, from what measurement() gives.
    The model calls and MCP messages of the runs go into "calls", per measurement and file, so that data.json stays small."""
    out = {"measurements": [], "runs": [], "maps": {}, "calls": {}}
    for facts, runs, maps in parts:
        out["measurements"].append(facts)
        for run in runs:
            out["calls"].setdefault(run["m"], {})[calls_file(run)] = run.get("calls", [])
            if "mcp_messages" in run:
                out["calls"][run["m"]][mcp_file(run)] = run["mcp_messages"]
            out["runs"].append({k: v for k, v in run.items() if k not in ("calls", "mcp_messages")} | {"model_calls": len(run.get("calls", []))})
        out["maps"] |= maps
    return _clean(out)


def write(data: dict, out: Path) -> None:
    """data.json, and per run its model calls (calls_file) and MCP messages (mcp_file), which a page fetches only when it shows the run."""
    shown = {k: v for k, v in data.items() if k != "calls"}
    (out / "data.json").write_text(json.dumps(shown, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for name, files in data.get("calls", {}).items():
        for file, calls in files.items():
            target = out / name / file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(calls, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for entry in data["maps"].values():
        target = out / entry["panden"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(panden(entry["reference"], entry["commit"]), separators=(",", ":")), encoding="utf-8")
