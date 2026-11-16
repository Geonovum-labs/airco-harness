"""Opt-in MCP contract smoke test for a locally packaged virtual-heads server."""

import asyncio
import os
from pathlib import Path

import pytest
from dotenv import find_dotenv, load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = pytest.mark.skipif(
    os.environ.get("AIRCO_VIRTUAL_GROUNDWATER_HEADS_MCP_LIVE") != "1",
    reason="live virtual groundwater heads MCP smoke test is opt-in",
)


def test_server_exposes_estimation_tools_and_project_resources():
    load_dotenv(find_dotenv(usecwd=True))
    jar = os.environ.get("AIRCO_VIRTUAL_GROUNDWATER_HEADS_MCP_JAR")
    if not jar or not Path(jar).is_file():
        pytest.fail("Set AIRCO_VIRTUAL_GROUNDWATER_HEADS_MCP_JAR to the packaged server JAR")
    command = StdioServerParameters(
        command="java",
        args=["-Dstdout.encoding=UTF-8", "-jar", str(Path(jar).resolve())],
    )

    async def exercise():
        async with stdio_client(command) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                required_tools = {
                    "virtual-groundwater-heads.analysis.common-dynamics",
                    "virtual-groundwater-heads.analysis.residual-dynamics",
                    "virtual-groundwater-heads.estimate.series",
                    "virtual-groundwater-heads.estimate.plot",
                    "virtual-groundwater-heads.meteo.stresses",
                    "virtual-groundwater-heads.series.tfn",
                    "virtual-groundwater-heads.tubes.geotop-confinement",
                    "virtual-groundwater-heads.tubes.select",
                    "virtual-groundwater-heads.tubes.subsurface",
                }
                assert required_tools <= tools.keys()

                estimate_schema = tools["virtual-groundwater-heads.estimate.series"].input_schema
                assert {
                    "x",
                    "y",
                    "crs",
                    "depthOfInterestMetresBelowGroundLevel",
                    "radiusMetres",
                    "candidateFilterDepthInterval",
                } <= estimate_schema["properties"].keys()
                assert "candidateFilterDepthInterval" in estimate_schema["required"]

                resources = {resource.uri for resource in (await session.list_resources()).resources}
                assert {
                    "groundwater://project/scope",
                    "groundwater://project/information-model",
                    "groundwater://methods/estimation",
                } <= resources
                information_model = await session.read_resource("groundwater://project/information-model")
                assert "VirtualHeadEstimate" in information_model.contents[0].text

    asyncio.run(exercise())
