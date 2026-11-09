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
Claude Code through the bridge as the MCP tool mcp__map__show_on_map.

On the variant "skill", the setup also puts an agent skill in the project
folder .claude/skills/, where Claude Code finds it as a user's project skill
would be found. The skill files are vendored in sources/skills/ with a checksum.
"""

from __future__ import annotations

import json

from inspect_ai.agent import Agent, BridgedToolsSpec
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox
from inspect_swe import claude_code

from validators import sources

from .tools import show_on_map

# Pinned so that a run names the version it used; raise it on purpose, with a note in the log bundle.
CLAUDE_CODE_VERSION = "2.1.304"
WORKDIR = "/workspace"
SETTINGS = {"skipWebFetchPreflight": True}


def skill_files() -> dict[str, bytes]:
    """The files of the skill of the variant "skill", by their path in the sandbox."""
    target = f"{WORKDIR}/.claude/skills/{sources.SKILL_NAME}"
    return {f"{target}/{name}": file.read_bytes() for name, file in sources.skill_files().items()}


@solver
def claude_code_setup(with_skill: bool = False) -> Solver:
    """Before the agent starts: the working directory with the project settings Claude Code needs behind the bridge, and on the variant skill the skill."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        await sandbox().exec(["mkdir", "-p", f"{WORKDIR}/.claude"])
        await sandbox().write_file(f"{WORKDIR}/.claude/settings.json", json.dumps(SETTINGS))
        if with_skill:
            for target, content in skill_files().items():
                await sandbox().write_file(target, content)
        return state

    return solve


def claude_code_agent(map_tool: bool = False) -> Agent:
    bridged = [BridgedToolsSpec(name="map", tools=[show_on_map()])] if map_tool else None
    return claude_code(version=CLAUDE_CODE_VERSION, permission_mode="bypassPermissions", cwd=WORKDIR, bridged_tools=bridged)
