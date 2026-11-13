"""Claude Code as the agent under test, through Inspect SWE.

Claude Code runs in the Docker sandbox of the sample with its own system
prompt and tools, as a user has it. Inspect SWE copies a pinned version of the
Claude Code binary into the sandbox and routes every model call through
Inspect's agent bridge, so the conversation, the limits and the cost land in
the log like those of any other agent. Claude Code's requests for a Claude
model are served by the eval model, whichever provider it is from.

Behind the bridge, Claude Code's WebFetch first asks api.anthropic.com whether a
domain is safe, and that call cannot reach Anthropic, so every WebFetch failed
with "Unable to verify if domain ... is safe to fetch". The project settings
in the working directory switch that preflight off, which is what a user with
a proxy does too.

In a test set with a map question, show_on_map runs on the host and reaches
Claude Code through the bridge as the MCP tool mcp__map__show_on_map. A
variant's HTTP MCP server is configured in Claude Code itself, which reaches it
from the sandbox and passes the server's instructions to the model as it does
for a user.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

from inspect_ai.agent import Agent, BridgedToolsSpec
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.tool import MCPServerConfigHTTP
from inspect_ai.util import sandbox
from inspect_swe import claude_code

from .tools import show_on_map

# Pinned so that a run names the version it used; raise it on purpose, with a note in the log bundle.
CLAUDE_CODE_VERSION = "2.1.304"
WORKDIR = "/workspace"
SETTINGS = {"skipWebFetchPreflight": True}


@solver
def claude_code_setup() -> Solver:
    """Before the agent starts: an empty working directory with the project settings Claude Code needs behind the bridge."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        await sandbox().exec(["mkdir", "-p", f"{WORKDIR}/.claude"])
        await sandbox().write_file(f"{WORKDIR}/.claude/settings.json", json.dumps(SETTINGS))
        return state

    return solve


def claude_code_agent(map_tool: bool = False, mcp_url: str | None = None) -> Agent:
    bridged = [BridgedToolsSpec(name="map", tools=[show_on_map()])] if map_tool else None
    mcp = [MCPServerConfigHTTP(type="http", name=server_name(mcp_url), url=mcp_url)] if mcp_url else None
    return claude_code(version=CLAUDE_CODE_VERSION, permission_mode="bypassPermissions", cwd=WORKDIR, bridged_tools=bridged, mcp_servers=mcp)


def server_name(url: str) -> str:
    """The name a user would give the server: the first segment of its path, such as bag for https://bag.ldproxy.net/bag/mcp."""
    return urlparse(url).path.strip("/").split("/")[0]
