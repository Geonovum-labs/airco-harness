"""A stdio MCP server with the bounded groundwater series contract, for tests."""

import inspect
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

server = MCPServer("stub-groundwater-monitoring", instructions="Call groundwater-monitoring.series.get for a level.")


def series_get(**kwargs) -> dict:
    """Return bounded observations for a GLD and an inclusive period."""
    return {"segments": [{"gldBroId": kwargs["gldBroId"], "values": [{"value": 2.13, "unit": "m", "referencePlane": "NAP"}]}],
            "window": {"from": kwargs.get("from"), "to": kwargs.get("to"), "total": 1, "returned": 1, "truncated": False}}


def series_get_signature(gldBroId: str, from_: Annotated[str | None, Field(alias="from")] = None, to: str | None = None) -> dict:
    pass


series_get.__signature__ = inspect.signature(series_get_signature)
server.tool(name="groundwater-monitoring.series.get")(series_get)


if __name__ == "__main__":
    server.run("stdio")
