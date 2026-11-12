"""The airco task: a test set on one variant with one agent, as an Inspect Task.

The harness measures the baseline: the question as a user asks it, to the agent
as the user has it. Variant 0 is the question alone; another variant adds a
publication form the agent can reach, such as an MCP server. Three agents answer it:
"model" is the model without a system prompt and without tools, the floor;
"inspect" is Inspect's own react() agent with its prompt, web search and a
fetch tool, the same for every model; "claude-code" is Claude Code with its
own prompt and tools, what a user has. In a test set with a map question, the
agents inspect and claude-code also get show_on_map, the map a user sees.
For a series question they also get plot_series.
"""

import os
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Literal, get_args

from dotenv import find_dotenv, load_dotenv
from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentPrompt, AgentState, AgentSubmit, agent, as_solver, react
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import GenerateConfig
from inspect_ai.tool import Tool, mcp_server_http, mcp_server_stdio, web_search

from . import dataset
from .models import register_costs
from .scorers import quality, source
from .tools import ProviderNamedTools, fetch, plot_series, show_on_map


@dataclass(frozen=True)
class Variant:
    """A form in which the standard is published: what the agent gets besides the question."""

    about: str
    # The MCP server the agent gets as tools: the command line of a stdio server, or the URL of a Streamable HTTP server.
    mcp: tuple[str, ...] | str | None = None
    # The samples the variant is made for: the default selection, which ids or tags override.
    tags: tuple[str, ...] = ()


# Revision ceec94f of 12 November 2026. The image is built for linux/amd64 only, and its default profile serves HTTP; prod speaks stdio.
GROUNDWATER_MONITORING_IMAGE = "ghcr.io/sjaakd/mcp-groundwater-monitoring@sha256:a9fba4c7f014ded600b172c9894b4e5d1ca5091c5cd15d99fc670f8d3a2c5127"
VARIANTS = {
    "0": Variant("The question alone: the agent finds the standard as it is published today, or not."),
    "mcp-groundwater-monitoring": Variant(
        "Variant 0 plus the groundwater monitoring MCP server on BRO data (github.com/sjaakd/mcp-groundwater-monitoring).",
        mcp=("docker", "run", "-i", "--rm", "--platform", "linux/amd64", "-e", "QUARKUS_PROFILE=prod", GROUNDWATER_MONITORING_IMAGE),
        tags=("bro",),
    ),
    "mcp-bag-ldproxy": Variant(
        "Variant 0 plus the MCP server of the BAG API on bag.ldproxy.net, which holds Amersfoort only (BAG extract of 8 October 2026).",
        mcp="https://bag.ldproxy.net/bag/mcp",
        tags=("bag",),
    ),
}
AgentName = Literal["model", "inspect", "claude-code"]
MAX_TOOL_OUTPUT = 48 * 1024
SANDBOX_COMPOSE = Path(__file__).parent / "sandbox" / "compose.yaml"


def takes(variant: str, agent: AgentName) -> bool:
    """Whether the agent can be given the variant's MCP server.

    The agent model has no tools. Claude Code reaches an HTTP server from its sandbox, but the sandbox cannot run a stdio server's container.
    """
    mcp = VARIANTS[variant].mcp
    return not mcp or agent == "inspect" or (agent == "claude-code" and isinstance(mcp, str))


def samples(testset: str, variant: str, ids: list[str] | None = None, tags: list[str] | None = None) -> MemoryDataset:
    """The samples a run of the variant takes: the ids or tags asked for, else those the variant is made for."""
    if ids is None and tags is None and VARIANTS[variant].tags:
        tags = list(VARIANTS[variant].tags)
    return dataset.load(testset, ids=ids, tags=tags)


def _agent(agent: AgentName, map_tool: bool, series_tool: bool, variant: Variant) -> Agent:
    if agent == "model":
        # No system prompt, no tools, no submit tool: the agent is done when the model stops calling tools, and its last message is the answer.
        return react(prompt=None, tools=[], submit=False)
    if agent == "inspect":
        # Inspect's defaults: its own system prompt and submit tool. web_search() uses the search of the model's own provider.
        tools = [web_search(), fetch(), *([show_on_map()] if map_tool else []), *([plot_series()] if series_tool else [])]
        if not variant.mcp:
            return react(tools=tools, submit=AgentSubmit(answer_only=True))
        # The MCP server comes on top of the tools of variant 0, so that the server is the one difference.
        return _with_mcp(tools, variant.mcp)
    from .claude_code import claude_code_agent

    return claude_code_agent(map_tool, series_tool, variant.mcp if isinstance(variant.mcp, str) else None)


def server_instructions(name: str, instructions: str | None) -> str | None:
    """The instructions of an MCP server as a client passes them to the model, verbatim, in the form Claude Code uses."""
    if not instructions:
        return None
    return f"# MCP Server Instructions\n\nThe following MCP servers have provided instructions for how to use their tools and resources:\n\n## {name}\n{instructions}"


@agent(name="react_with_mcp")
def _with_mcp(tools: list[Tool], mcp: tuple[str, ...] | str) -> Agent:
    """Inspect's react() with the tools and a server of its own per sample, connected for the whole sample, and the server's instructions in its prompt.
    Unconnected, every tool call would start the server anew."""

    async def execute(state: AgentState) -> AgentState:
        server = mcp_server_http(url=mcp) if isinstance(mcp, str) else mcp_server_stdio(command=mcp[0], args=list(mcp[1:]))
        async with server as connected:
            # Inspect keeps the initialize result in the session only; a server may explain its data there and nowhere else.
            session = connected._session
            prompt = AgentPrompt(instructions=server_instructions(session.server_info.name, session.instructions))
            return await react(prompt=prompt, tools=[*tools, ProviderNamedTools(server)], submit=AgentSubmit(answer_only=True))(state)

    return execute


def _setup(agent: AgentName):
    if agent != "claude-code":
        return None
    from .claude_code import claude_code_setup

    return claude_code_setup()


def _metadata(testset: str, variant: str, agent: AgentName) -> dict:
    """What a run used besides the code, which the git revision in the log identifies."""
    return {
        "harness": {"airco-harness": version("airco-harness"), "inspect-ai": version("inspect-ai")},
        "setup": 2 if agent == "claude-code" else 1,
        "agent": agent,
        "testset": {"name": testset, "version": dataset.manifest(testset)["version"]},
        "variant": variant,
        "variant_form": asdict(VARIANTS[variant]),
    }


@task
def airco(
    testset: str = dataset.DEFAULT_TESTSET,
    variant: str = "0",
    agent: AgentName = "model",
    ids: str | list[str] | None = None,
    tags: str | list[str] | None = None,
    model: str | None = None,
    message_limit: int = 60,
    token_limit: int = 600_000,
    time_limit: int = 900,
    cost_limit: float | None = 2.0,
) -> Task:
    """The test set on one variant of the publication form, with one agent.

    Args:
      testset: Test set under testsets/.
      variant: Variant: 0, the question alone; mcp-groundwater-monitoring (agent inspect) or mcp-bag-ldproxy (agents inspect and claude-code), variant 0 plus an MCP server.
      agent: model for the model without prompt or tools; inspect for Inspect's react() with web search and fetch; claude-code for Claude Code in a Docker sandbox.
      ids: Comma-separated sample ids; default the samples the variant is made for, all for variant 0.
      tags: Comma-separated tags; the samples with one of them.
      model: The model of this task, when the matrix pairs agents and models; otherwise the model comes from --model.
      message_limit: Message limit per run.
      token_limit: Token limit per run.
      time_limit: Time limit per run in seconds.
      cost_limit: Cost limit per run in dollars; none for no limit.
    """
    # On the command line -T variant=0 arrives as the YAML integer 0.
    variant = str(variant)
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; choose from {', '.join(VARIANTS)}")
    if agent not in get_args(AgentName):
        raise ValueError(f"unknown agent {agent!r}; choose from {', '.join(get_args(AgentName))}")
    if not takes(variant, agent):
        raise ValueError(f"the agent {agent} does not take the MCP server of variant {variant}")
    load_dotenv(find_dotenv(usecwd=True))
    register_costs()
    chosen = samples(testset, variant, ids=ids.split(",") if isinstance(ids, str) else ids, tags=tags.split(",") if isinstance(tags, str) else tags)
    if not len(chosen):
        raise ValueError(f"no samples of test set {testset} for variant {variant}; choose others with ids or tags")
    return Task(
        dataset=chosen,
        setup=_setup(agent),
        solver=as_solver(_agent(agent, dataset.asks_for_map(testset), dataset.asks_for_series(testset), VARIANTS[variant])),
        scorer=[quality(), source()],
        config=GenerateConfig(max_tool_output=MAX_TOOL_OUTPUT),
        # A path relative to the working directory, so that the log names no home directory.
        sandbox=("docker", os.path.relpath(SANDBOX_COMPOSE)) if agent == "claude-code" else None,
        model=model,
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
        cost_limit=cost_limit,
        version="0.1",
        metadata=_metadata(testset, variant, agent),
    )
