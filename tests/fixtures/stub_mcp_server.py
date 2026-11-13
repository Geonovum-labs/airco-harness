"""A stdio MCP server with one tool named like those of the groundwater monitoring server, for tests."""

from mcp.server.mcpserver import MCPServer

server = MCPServer("stub-groundwater-monitoring", instructions="Call groundwater-monitoring.series.get for a level.")


@server.tool(name="groundwater-monitoring.series.get")
def series_get(gld: str, date: str) -> str:
    """The level of a groundwater level series on a day, in meters relative to NAP."""
    return f"{gld} {date}: 2.13 m NAP"


if __name__ == "__main__":
    server.run("stdio")
