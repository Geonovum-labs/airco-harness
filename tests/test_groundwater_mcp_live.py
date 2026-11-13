"""Opt-in live MCP contract smoke test; requires a packaged server and public BRO access."""

import asyncio
import json
import os
from pathlib import Path

import pytest
from dotenv import find_dotenv, load_dotenv
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from airco_harness import tasks

pytestmark = pytest.mark.skipif(os.environ.get("AIRCO_GROUNDWATER_MCP_LIVE") != "1", reason="live BRO MCP smoke test is opt-in")


def test_real_tube_bounded_series_and_plot(tmp_path, monkeypatch):
    load_dotenv(find_dotenv(usecwd=True))
    jar = os.environ.get("AIRCO_GROUNDWATER_MCP_JAR")
    if not jar:
        pytest.fail("Set AIRCO_GROUNDWATER_MCP_JAR to the updated packaged server")
    monkeypatch.setenv("AIRCO_GROUNDWATER_MCP_JAR", jar)
    command = tasks.variant_form("mcp-groundwater-monitoring").mcp
    plot_dir = tmp_path / "plots"
    args = [*command[1:2], f"-Dgroundwater-monitoring.plot.directory={plot_dir}", *command[2:]]

    async def exercise():
        async with stdio_client(StdioServerParameters(command=command[0], args=args)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = {t.name for t in (await session.list_tools()).tools}
                assert {"groundwater-monitoring.series.get", "groundwater-monitoring.series.daily", "groundwater-monitoring.series.plot"} <= names

                async def call(name, arguments, error=False):
                    result = await session.call_tool(f"groundwater-monitoring.series.{name}", arguments)
                    assert result.is_error is error
                    assert len(result.content) == 1 and result.content[0].type == "text"
                    payload = json.loads(result.content[0].text)
                    assert payload == result.structured_content
                    return payload

                tube = {"wellBroId": "GMW000000024250", "tubeNumber": 1}
                broad = await call("daily", {**tube, "from": "2026-01-01", "to": "2026-10-29"})
                assert broad["window"]["total"] > 90
                assert broad["window"]["returned"] == len(broad["daily"]["days"]) == 90
                assert broad["window"]["truncated"] is True
                narrow = await call("daily", {**tube, "from": "2026-10-01", "to": "2026-10-29"})
                assert narrow["window"]["truncated"] is False
                days = narrow["daily"]["days"]
                assert narrow["window"]["returned"] == len(days) > 0
                assert all("2026-10-01" <= day["date"] <= "2026-10-29" for day in days)
                assert narrow["daily"]["method"] == "noon-closest-priority-v1"
                gld = days[-1]["sourceGldBroId"]
                raw = await call("get", {"gldBroId": gld, "from": "2026-10-01", "to": "2026-10-29"})
                assert raw["window"]["truncated"] is True
                assert raw["window"]["total"] > 500
                assert raw["window"]["returned"] == sum(len(segment["values"]) for segment in raw["segments"]) == 500
                single = await call("get", {"gldBroId": gld, "from": days[-1]["date"], "to": days[-1]["date"]})
                assert single["window"]["truncated"] is False
                assert single["window"]["returned"] == sum(len(segment["values"]) for segment in single["segments"]) > 0
                for period in ({"from": "not-a-date"}, {"from": "2026-10-29", "to": "2026-10-01"}):
                    assert (await call("daily", {**tube, **period}, error=True))["code"] == "INVALID_PERIOD"
                plot = await call("plot", {**tube, "from": "2026-01-01", "to": "2026-10-29"})
                assert plot["dayCount"] > 90
                assert "2026-01-01" <= plot["firstDate"] <= plot["lastDate"] <= "2026-10-29"
                assert Path(plot["path"]).is_file()

    asyncio.run(exercise())


def test_inspect_reads_actual_server_text_content(tmp_path):
    load_dotenv(find_dotenv(usecwd=True))
    if not os.environ.get("AIRCO_GROUNDWATER_MCP_JAR"):
        pytest.fail("Set AIRCO_GROUNDWATER_MCP_JAR to the updated packaged server")
    arguments = {"wellBroId": "GMW000000024250", "tubeNumber": 1, "from": "2026-10-01", "to": "2026-10-29"}
    outputs = [
        ModelOutput.for_tool_call("mockllm/model", "groundwater-monitoring_series_daily", arguments),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Smoke test"}),
    ]
    task = tasks.airco(testset="dsfl", variant="mcp-groundwater-monitoring", agent="inspect", ids="dsfl-07")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=outputs), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    [message] = [message for message in sample.messages if message.role == "tool"]
    assert message.error is None
    payload = json.loads(message.text)
    assert payload["daily"]["wellBroId"] == arguments["wellBroId"]
    assert payload["window"]["truncated"] is False
