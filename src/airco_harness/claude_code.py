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
variant's HTTP MCP servers are configured in Claude Code itself, which passes their
instructions to the model as it does for a user. It reaches them through the
recording proxy of mcpwire, on the host at host.docker.internal. For a series question, plot_series is bridged as mcp__plot__plot_series.

A variant's skills go into the project's .claude/skills, each skill directory
whole, as a user copies it there. Inspect SWE's own skills option copies only
SKILL.md, scripts/, references/ and assets/, and a skill can point at other files.
"""

from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.agent import Agent, BridgedToolsSpec
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.tool import MCPServerConfigHTTP
from inspect_ai.util import sandbox
from inspect_swe import claude_code

from .tools import plot_series, show_on_map

# Pinned so that a run names the version it used; raise it on purpose, with a note in the log bundle.
CLAUDE_CODE_VERSION = "2.1.304"
WORKDIR = "/workspace"
SETTINGS = {"skipWebFetchPreflight": True}


@solver
def claude_code_setup(skills: list[Path] | None = None) -> Solver:
    """Before the agent starts: an empty working directory with the project settings Claude Code needs behind the bridge, and the skills."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        await sandbox().exec(["mkdir", "-p", f"{WORKDIR}/.claude"])
        await sandbox().write_file(f"{WORKDIR}/.claude/settings.json", json.dumps(SETTINGS))
        for skill in skills or []:
            for file in sorted(f for f in skill.rglob("*") if f.is_file()):
                await sandbox().write_file(f"{WORKDIR}/.claude/skills/{skill.name}/{file.relative_to(skill).as_posix()}", file.read_bytes())
        return state

    return solve


def claude_code_agent(map_tool: bool = False, series_tool: bool = False, mcp_servers: list[tuple[str, str]] | None = None) -> Agent:
    """Claude Code with the bridged tools and the HTTP MCP servers, each (name, URL from the sandbox)."""
    bridged = []
    if map_tool:
        bridged.append(BridgedToolsSpec(name="map", tools=[show_on_map()]))
    if series_tool:
        bridged.append(BridgedToolsSpec(name="plot", tools=[plot_series()]))
    mcp = [MCPServerConfigHTTP(type="http", name=name, url=url) for name, url in mcp_servers or []] or None
    return claude_code(version=CLAUDE_CODE_VERSION, permission_mode="bypassPermissions", cwd=WORKDIR, bridged_tools=bridged or None, mcp_servers=mcp)
