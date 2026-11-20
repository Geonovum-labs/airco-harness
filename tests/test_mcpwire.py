"""The recording proxy between an agent and its MCP servers, against a fake server that answers as Streamable HTTP does."""

import asyncio
import json
import time

from aiohttp import ClientSession, web

from airco_harness.mcpwire import McpRecorder, messages


async def _fake_server(request: web.Request) -> web.StreamResponse:
    message = await request.json()
    method = message.get("method")
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "fake", "version": "1.2.3"}}
        return web.json_response({"jsonrpc": "2.0", "id": message["id"], "result": result}, headers={"Mcp-Session-Id": "session-1"})
    if method == "notifications/initialized":
        return web.Response(status=202)
    # A tool call answers as an event stream, with a progress notification before the result.
    response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
    await response.prepare(request)
    await response.write(b'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress","params":{}}\n\n')
    failed = message["params"]["name"] == "broken"
    result = {"content": [{"type": "text", "text": "no such buurt" if failed else "ok"}], "isError": failed}
    await response.write(f"event: message\ndata: {json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': result})}\n\n".encode())
    await response.write_eof()
    return response


async def _run_through_proxy() -> tuple[list[dict], list[str]]:
    app = web.Application()
    app.router.add_post("/mcp", _fake_server)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    upstream = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}/mcp"
    bodies = []
    try:
        async with McpRecorder({"fake": upstream}) as recorder, ClientSession() as client:
            url = recorder.url("fake")
            initialize = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-11-25", "clientInfo": {"name": "agent", "version": "9"}},
            }
            async with client.post(url, json=initialize) as r:
                session = r.headers["Mcp-Session-Id"]
                bodies.append(await r.text())
            headers = {"MCP-Protocol-Version": "2025-06-18", "Mcp-Session-Id": session}
            async with client.post(url, json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=headers) as r:
                bodies.append(await r.text())
            for i, tool in enumerate(["trace", "broken"], 2):
                call = {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": tool, "arguments": {}}}
                async with client.post(url, json=call, headers=headers) as r:
                    bodies.append(await r.text())
            return recorder.records, bodies
    finally:
        await runner.cleanup()


def test_the_proxy_records_each_message_with_its_protocol_version_and_passes_the_answers_through():
    records, bodies = asyncio.run(_run_through_proxy())
    assert [(r["method"], r.get("tool"), r.get("protocol"), r["status"]) for r in records] == [
        ("initialize", None, "2025-11-25", 200),
        ("notifications/initialized", None, "2025-06-18", 202),
        ("tools/call", "trace", "2025-06-18", 200),
        ("tools/call", "broken", "2025-06-18", 200),
    ]
    initialize, _, trace, broken = records
    # The client asked for 2025-11-25; the server agreed to 2025-06-18, and every later request carries that.
    assert (initialize["agreed"], initialize["client"], initialize["server_info"]["version"]) == ("2025-06-18", {"name": "agent", "version": "9"}, "1.2.3")
    assert initialize["session"] == trace["session"] == broken["session"]
    assert "error" not in trace and broken["error"] == "no such buurt"
    assert all(r["server"] == "fake" and r["bytes"] == len(b.encode()) for r, b in zip(records, bodies))
    # The event stream reaches the client unchanged: the notification before the result.
    assert [m.get("method") or m["result"]["content"][0]["text"] for m in messages(bodies[2].encode(), "text/event-stream")] == ["notifications/progress", "ok"]
    # What went in and out: each message as sent, and the server's answer to it, not the notification before it.
    assert json.loads(trace["sent"])["params"]["name"] == "trace" and json.loads(trace["received"])["result"]["content"][0]["text"] == "ok"
    assert json.loads(initialize["received"])["result"]["protocolVersion"] == "2025-06-18" and "received" not in records[1]


def test_a_long_message_is_cut_and_keeps_its_length():
    from airco_harness.mcpwire import BODY_CHARS, answered

    long = {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "x" * BODY_CHARS}]}}
    [record] = answered([{"server": "s", "http": "POST", "method": "tools/call", "id": 1}], 200, {}, [long], 5, 70_000)
    assert len(record["received"]) == BODY_CHARS and record["received_chars"] == len(json.dumps(long))
    [page] = answered([{"server": "s", "http": "POST", "method": "tools/call", "id": 2}], 502, {}, [], 5, 20, raw="<html>Bad gateway</html>")
    assert (page["received"], page["error"]) == ("<html>Bad gateway</html>", "HTTP 502")


def test_a_2026_request_carries_its_version_in_meta_and_an_unknown_server_is_refused():
    from airco_harness.mcpwire import sent

    stateless = {"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}}}
    [record] = sent("bgt", "POST", {}, [stateless])
    assert (record["method"], record["protocol"], json.loads(record["sent"])) == ("tools/list", "2026-07-28", stateless)

    async def refused() -> int:
        async with McpRecorder({}) as recorder, ClientSession() as client:
            async with client.post(recorder.url("bgt"), json=stateless) as r:
                return r.status

    assert asyncio.run(refused()) == 404


async def _with_upstream(handler, scenario):
    """Run scenario(recorder, client, upstream URL) against a fake server with one handler for every path."""
    app = web.Application()
    app.router.add_route("*", "/mcp", handler)
    runner = web.AppRunner(app, shutdown_timeout=0.1)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        recorder = McpRecorder({"fake": f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}/mcp"})
        async with ClientSession() as client:
            async with recorder:
                result = await scenario(recorder, client)
                leaving = time.monotonic()
            # The proxy leaves at once, also with a request still open.
            assert time.monotonic() - leaving < 5
            return recorder.records, result
    finally:
        await runner.cleanup()


def test_an_answer_with_lowercase_headers_is_read_and_repeated_headers_pass_through():
    """A server behind an HTTP/2 proxy, or on Netty, writes header names in lowercase; this one writes raw HTTP to be sure."""
    body = b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18"}}\n\n'

    async def raw_server(reader, writer):
        while (await reader.readline()) not in (b"\r\n", b""):
            pass
        head = b"HTTP/1.1 200 OK\r\ncontent-type: text/event-stream\r\nset-cookie: a=1\r\nset-cookie: b=2\r\n"
        writer.write(head + f"content-length: {len(body)}\r\nconnection: close\r\n\r\n".encode() + body)
        await writer.drain()
        writer.close()

    async def scenario():
        server = await asyncio.start_server(raw_server, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server, McpRecorder({"raw": f"http://127.0.0.1:{port}/mcp"}) as recorder, ClientSession() as client:
            async with client.post(recorder.url("raw"), json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) as r:
                cookies = r.headers.getall("Set-Cookie")
        return recorder.records, cookies

    [record], cookies = asyncio.run(scenario())
    assert record["agreed"] == "2025-06-18" and json.loads(record["received"])["id"] == 1
    assert cookies == ["a=1", "b=2"]


def test_an_unreachable_server_gives_the_agent_the_cause_and_the_record_an_error():
    async def scenario():
        async with McpRecorder({"gone": "http://127.0.0.1:9/mcp"}) as recorder, ClientSession() as client:
            async with client.post(recorder.url("gone"), json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) as r:
                return recorder.records, r.status, await r.text()

    records, status, text = asyncio.run(scenario())
    assert status == 502 and "MCP server gone" in text and "ClientConnectorError" in text
    assert records[0]["status"] == 502 and records[0]["error"].startswith("ClientConnectorError")


def test_a_stream_still_open_when_the_proxy_closes_is_in_the_records():
    async def handler(request):
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await response.prepare(request)
        await response.write(b": open\n\n")
        await asyncio.sleep(60)
        return response

    async def scenario(recorder, client):
        response = await client.get(recorder.url("fake"), headers={"MCP-Protocol-Version": "2025-06-18"})
        await response.content.readline()
        return response

    records, _ = asyncio.run(_with_upstream(handler, scenario))
    assert [(r["method"], r["protocol"], r["status"]) for r in records] == [("GET", "2025-06-18", 200)]


def test_the_proxy_answers_this_host_and_docker_containers_only():
    from airco_harness.mcpwire import _trusted

    assert all(_trusted(peer) for peer in ("127.0.0.1", "::1", "172.17.0.2", "192.168.65.1"))
    assert not any(_trusted(peer) for peer in ("192.168.1.20", "10.0.0.5", None, "unix"))
