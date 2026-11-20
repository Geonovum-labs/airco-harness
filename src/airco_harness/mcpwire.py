"""A recording proxy between an agent and its MCP servers over Streamable HTTP.

Claude Code's MCP client runs in its sandbox and logs nothing of the protocol, so the harness puts this proxy
between every agent and its HTTP servers and keeps one record per JSON-RPC message the client sent: the
protocol version the request carried (the MCP-Protocol-Version header, the 2026 _meta key, or for initialize the
version the client asked for), the version the server agreed to, the client and its session, the HTTP status, the
time until the response ended, its size, an error, and what went in and out: the message as sent and the server's
answer to it, each up to BODY_CHARS characters. It also sees the calls of Claude Code's subagents, which the
conversation does not show. Responses pass through as they arrive, so a server's stream of events works as
without the proxy.
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import time
from collections.abc import Iterable

import anyio
from aiohttp import ClientConnectionError, ClientSession, ClientTimeout, web
from multidict import CIMultiDict

PROTOCOL_HEADER = "mcp-protocol-version"
SESSION_HEADER = "mcp-session-id"
META_PROTOCOL = "io.modelcontextprotocol/protocolVersion"
META_CLIENT = "io.modelcontextprotocol/clientInfo"
META_SERVER = "io.modelcontextprotocol/serverInfo"
# Headers that belong to one connection, or that aiohttp sets itself. Upstream bodies arrive decompressed.
HOP_BY_HOP = {"host", "content-length", "transfer-encoding", "connection", "keep-alive", "accept-encoding", "content-encoding", "upgrade", "te", "trailer"}
PARSED_BYTES = 8_000_000  # A response is read for its records up to this size; it always passes through whole.
BODY_CHARS = 64_000  # Of each message sent and each answer, the log keeps this much; a longer one also keeps its length.
# Docker's default address pools (172.17.0.0/16 and up) and the network of Docker Desktop's VM.
DOCKER_NETWORKS = (ipaddress.ip_network("172.16.0.0/12"), ipaddress.ip_network("192.168.65.0/24"))


def messages(body: bytes, content_type: str) -> list[dict]:
    """The JSON-RPC messages of a body: a JSON object or batch, or the data of each event of an SSE stream."""
    text = body.decode("utf-8", "replace")
    if "text/event-stream" not in content_type:
        return _json_messages(text)
    found = []
    for event in text.replace("\r\n", "\n").split("\n\n"):
        found.extend(_json_messages("\n".join(line[5:].lstrip() for line in event.split("\n") if line.startswith("data:"))))
    return found


def _json_messages(text: str) -> list[dict]:
    try:
        value = json.loads(text)
    except ValueError:
        return []
    return [m for m in (value if isinstance(value, list) else [value]) if isinstance(m, dict)]


def _session(value: str | None) -> str | None:
    return hashlib.sha256(value.encode()).hexdigest()[:8] if value else None


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _body(key: str, text: str) -> dict:
    """A message as the record keeps it: the text up to BODY_CHARS, and its full length when it was longer."""
    return {key: text[:BODY_CHARS], **({f"{key}_chars": len(text)} if len(text) > BODY_CHARS else {})}


def sent(server: str, http_method: str, headers: dict[str, str], body: list[dict]) -> list[dict]:
    """A record per message the client sent, or one for a request without messages, such as a GET for the event stream."""
    lowered = {k.lower(): v for k, v in headers.items()}
    out = []
    for message in body or [{}]:
        params = _dict(message.get("params"))
        meta = _dict(params.get("_meta"))
        method = message.get("method") or ("response" if "result" in message or "error" in message else http_method)
        record = {"server": server, "http": http_method, "method": method, "id": message.get("id")}
        if method == "tools/call":
            record["tool"] = params.get("name")
        protocol = lowered.get(PROTOCOL_HEADER) or meta.get(META_PROTOCOL) or (params.get("protocolVersion") if method == "initialize" else None)
        client = {k: v for k, v in _dict(params.get("clientInfo") if method == "initialize" else meta.get(META_CLIENT)).items() if k in ("name", "version")}
        record |= {k: v for k, v in (("protocol", protocol), ("client", client), ("session", _session(lowered.get(SESSION_HEADER)))) if v}
        if message:
            record |= _body("sent", json.dumps(message, ensure_ascii=False))
        out.append(record)
    return out


def answered(records: list[dict], status: int, headers: dict[str, str], body: Iterable[dict], ms: float, size: int, raw: str = "") -> list[dict]:
    """The records with what the server answered to each: its answer, the agreed version for a handshake, an error, the
    HTTP status. An answer that is no JSON-RPC message, such as an error page, is kept as raw text for a request that expected one."""
    responses = {m["id"]: m for m in body if "id" in m and ("result" in m or "error" in m)}
    new_session = _session({k.lower(): v for k, v in headers.items()}.get(SESSION_HEADER))
    out = []
    for record in records:
        record = {**record, "status": status, "ms": round(ms), "bytes": size}
        response = responses.get(record.get("id")) if record.get("id") is not None else None
        result = _dict(response.get("result")) if response else {}
        if response:
            record |= _body("received", json.dumps(response, ensure_ascii=False))
        elif raw.strip() and record.get("id") is not None:
            record |= _body("received", raw)
        if response and "error" in response:
            record["error"] = str(_dict(response["error"]).get("message") or response["error"])[:300]
        if record["method"] == "initialize" and result:
            record |= {"agreed": result.get("protocolVersion"), "server_info": result.get("serverInfo")}
            if new_session:
                record["session"] = new_session
        if record["method"] == "server/discover" and result:
            record |= {"supported": result.get("supportedVersions"), "server_info": _dict(result.get("_meta")).get(META_SERVER)}
        if record["method"] == "tools/call" and result.get("isError"):
            text = next((c.get("text") for c in result.get("content") or [] if isinstance(c, dict) and c.get("text")), "tool error")
            record["error"] = str(text)[:300]
        if status >= 400 and "error" not in record:
            record["error"] = f"HTTP {status}"
        record.pop("id", None)
        out.append({k: v for k, v in record.items() if v is not None})
    return out


def applied(record: dict) -> str | None:
    """The protocol version a message went under: for initialize the one the server agreed to, which the client asked for
    in the same message; for the others the one the request carried."""
    return record.get("agreed") if record["method"] == "initialize" else record.get("protocol")


def traffic(records: list[dict]) -> list[dict]:
    """Per server: the protocol versions its messages went under, how client and server settled on one, the client,
    and how many sessions, requests, tool calls and errors there were, with the server's time for the tool calls in ms."""
    out: dict[str, dict] = {}
    for record in records:
        server = out.setdefault(
            record["server"], {"server": record["server"], "protocols": [], "sessions": set(), "requests": 0, "tool_calls": 0, "errors": 0, "ms": 0}
        )
        server["requests"] += 1
        version = applied(record)
        if version and version not in server["protocols"]:
            server["protocols"].append(version)
        if record["method"] in ("initialize", "server/discover") and "handshake" not in server:
            server["handshake"] = {"method": record["method"], **{k: record[k] for k in ("protocol", "agreed", "supported") if k in record}}
        if record.get("client") and "client" not in server:
            server["client"] = " ".join(str(record["client"].get(k, "")) for k in ("name", "version")).strip()
        if record.get("session"):
            server["sessions"].add(record["session"])
        if record["method"] == "tools/call":
            server["tool_calls"] += 1
            server["ms"] += record.get("ms", 0)
        server["errors"] += "error" in record
    return [{**s, "sessions": len(s["sessions"])} for s in out.values()]


def protocols(summary: list[dict]) -> str:
    """`server version` for each server and protocol version of a run, from its traffic(), as a column of the report."""
    return ", ".join(f"{s['server']} {version}" for s in summary for version in s["protocols"])


def _trusted(peer: str | None) -> bool:
    """Whether a connection may use the proxy: from this host, or from a Docker container (the default address pools and
    Docker Desktop's network), as the proxy listens on every interface for a sandbox."""
    try:
        address = ipaddress.ip_address((peer or "").split("%")[0])
    except ValueError:
        return False
    return address.is_loopback or any(address in network for network in DOCKER_NETWORKS)


class McpRecorder:
    """The proxy for one sample: http://<host>:<port>/<name> forwards to the URL of server <name>.

    Bind it to 0.0.0.0 for an agent in a Docker sandbox, which reaches the host at host.docker.internal; it then answers
    only this host and Docker containers. Leaving it first ends the requests still open, so that their records are in
    `records` when it has left, even under cancellation."""

    def __init__(self, servers: dict[str, str], bind: str = "127.0.0.1"):
        self.servers = servers
        self.bind = bind
        self.records: list[dict] = []
        self.port = 0
        self._open: set[asyncio.Task] = set()

    def url(self, name: str, host: str = "127.0.0.1") -> str:
        return f"http://{host}:{self.port}/{name}"

    async def __aenter__(self) -> McpRecorder:
        self._client = ClientSession(timeout=ClientTimeout(total=None, connect=30), auto_decompress=True)
        app = web.Application(client_max_size=64 * 1024 * 1024)
        app.router.add_route("*", "/{name}{tail:.*}", self._forward)
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.bind, 0)
        await site.start()
        self.port = site._server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc) -> None:
        with anyio.CancelScope(shield=True):
            try:
                for task in self._open:
                    task.cancel()
                await asyncio.gather(*self._open, return_exceptions=True)
                await self._runner.cleanup()
            finally:
                await self._client.close()

    async def _forward(self, request: web.Request) -> web.StreamResponse:
        name = request.match_info["name"]
        if not _trusted(request.remote):
            return web.Response(status=403, text=f"the MCP proxy answers this host and Docker containers only, not {request.remote}")
        if name not in self.servers:
            return web.Response(status=404, text=f"no MCP server {name}")
        task = asyncio.current_task()
        self._open.add(task)
        target = self.servers[name] + request.match_info["tail"] + (f"?{request.query_string}" if request.query_string else "")
        body = await request.read()
        headers = CIMultiDict((k, v) for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP)
        records = sent(name, request.method, dict(request.headers), messages(body, request.headers.get("Content-Type", "application/json")))
        started = time.monotonic()
        for record in records:
            record["at"] = round(time.time(), 3)
        status, response_headers, kept, size, failure = 502, CIMultiDict(), bytearray(), 0, None
        try:
            async with self._client.request(request.method, target, headers=headers, data=body or None, allow_redirects=False) as upstream:
                status, response_headers = upstream.status, CIMultiDict(upstream.headers)
                response = web.StreamResponse(status=status, headers=CIMultiDict((k, v) for k, v in upstream.headers.items() if k.lower() not in HOP_BY_HOP))
                await response.prepare(request)
                async for chunk in upstream.content.iter_any():
                    size += len(chunk)
                    if len(kept) < PARSED_BYTES:
                        kept.extend(chunk)
                    await response.write(chunk)
                await response.write_eof()
                return response
        except ClientConnectionError as e:
            # The server could not be reached, or broke off its answer: the agent gets the cause, as without the proxy.
            failure = f"{type(e).__name__}: {e}"
            if status == 502:
                return web.Response(status=502, text=f"MCP server {name} at {self.servers[name]}: {failure}")
            raise
        finally:
            self._open.discard(task)
            parsed = messages(bytes(kept), response_headers.get("Content-Type", "")) if size <= PARSED_BYTES else []
            raw = bytes(kept).decode("utf-8", "replace") if not parsed else ""
            done = answered(records, status, dict(response_headers), parsed, (time.monotonic() - started) * 1000, size, raw)
            self.records.extend({**r, "error": failure} if failure else r for r in done)
