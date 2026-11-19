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
from contextlib import AsyncExitStack
from dataclasses import asdict, dataclass, replace
from importlib.metadata import version
from pathlib import Path
from typing import Literal, get_args

from dotenv import find_dotenv, load_dotenv
from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentPrompt, AgentState, AgentSubmit, agent, as_solver, react
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import Generate, Solver, TaskState, chain, solver
from inspect_ai.tool import Tool, mcp_server_http, mcp_server_stdio, web_search
from inspect_ai.util import store

from . import dataset
from .models import register_costs
from .scorers import quality, source
from .tools import ProviderNamedTools, fetch, plot_series, show_on_map


@dataclass(frozen=True)
class McpServer:
    """An MCP server a variant adds: the command line of a stdio server, or the URL of a Streamable HTTP server.
    The name is the one a user would give it; Claude Code puts it before the server's tool names, as in mcp__<name>__<tool>."""

    name: str
    url: str = ""
    command: tuple[str, ...] = ()
    # The URL from Claude Code's sandbox, for a server that runs on the host.
    sandbox_url: str = ""
    # For a server that runs on the host: the image it runs, pinned by digest, and the serverInfo.version that image reports.
    # A server that reports another version fails the run, so a run never meets an image other than the one named here.
    image: str = ""
    version: str = ""


def host_server(name: str, url: str, image: str, version: str) -> McpServer:
    """A server that runs on the host from a pinned image. Claude Code reaches it from its sandbox at host.docker.internal."""
    return McpServer(name, url=url, sandbox_url=url.replace("localhost", "host.docker.internal"), image=image, version=version)


def url_variable(server: McpServer) -> str:
    """The environment variable that moves a host server, such as AIRCO_SUBSURFACE_MODELS_URL."""
    return f"AIRCO_{server.name.upper().replace('-', '_')}_URL"


@dataclass(frozen=True)
class Variant:
    """A form in which the standard is published: what the agent gets besides the question."""

    about: str
    # The MCP servers the agent gets as tools, on top of the tools of variant 0.
    mcp: tuple[McpServer, ...] = ()
    # The samples the variant is made for: the default selection, which ids or tags override.
    tags: tuple[str, ...] = ()


# The two servers of github.com/sjaakd serve HTTP only, for linux/amd64, so they run on the host; docs/running.md has the docker run commands.
# Revision 74482ac of 19 November 2026.
GROUNDWATER_MONITORING_IMAGE = "ghcr.io/sjaakd/mcp-groundwater-monitoring@sha256:13ba5702da61d81e76421061e52f3ef416f43d7f390667c8a036282fdf4bf9d0"
# Revision caed3d4 of 19 November 2026, with the GeoTOP and REGIS tiles of Amersfoort in the image.
SUBSURFACE_MODELS_IMAGE = "ghcr.io/sjaakd/mcp-subsurface-models@sha256:40af69780274dcc5c4b8c4ce99cf4b540c07ac72bb241127911954cf8466b6ae"
VARIANTS = {
    "0": Variant("The question alone: the agent finds the standard as it is published today, or not."),
    "mcp-groundwater-monitoring": Variant(
        "Variant 0 plus the groundwater monitoring MCP server on BRO data (github.com/sjaakd/mcp-groundwater-monitoring).",
        mcp=(host_server("groundwater-monitoring", "http://localhost:18081/mcp", GROUNDWATER_MONITORING_IMAGE, "1.0.9"),),
        tags=("groundwater",),
    ),
    "mcp-bag-ldproxy": Variant(
        "Variant 0 plus the MCP server of the BAG API on bag.ldproxy.net, which holds Amersfoort only (BAG extract of 8 October 2026).",
        mcp=(McpServer("bag", url="https://bag.ldproxy.net/bag/mcp"),),
        tags=("bag",),
    ),
    "mcp-bgt-wijkenbuurten-subsurface": Variant(
        "Variant 0 plus the MCP servers of the BGT and the CBS wijken en buurten on bag.ldproxy.net (Amersfoort) and the subsurface models MCP server "
        "(github.com/sjaakd/mcp-subsurface-models) with the Amersfoort extract of GeoTOP and REGIS in its image, running on the host.",
        mcp=(
            McpServer("bgt", url="https://bag.ldproxy.net/bgt/mcp"),
            McpServer("wijkenbuurten", url="https://bag.ldproxy.net/wijkenbuurten/mcp"),
            host_server("subsurface-models", "http://localhost:18082/mcp", SUBSURFACE_MODELS_IMAGE, "1.0.10"),
        ),
        tags=("bgt",),
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
    return not mcp or agent == "inspect" or (agent == "claude-code" and all(server.url for server in mcp))


def samples(testset: str, variant: str, ids: list[str] | None = None, tags: list[str] | None = None) -> MemoryDataset:
    """The samples a run of the variant takes: the ids or tags asked for, else those the variant is made for."""
    if ids is None and tags is None and VARIANTS[variant].tags:
        tags = list(VARIANTS[variant].tags)
    return dataset.load(testset, ids=ids, tags=tags)


def variant_form(variant: str) -> Variant:
    """The variant with a host server moved to the URL in its variable, read after .env is loaded."""
    form = VARIANTS[variant]
    moved = {s.name: os.environ.get(url_variable(s), "").strip() for s in form.mcp if s.image}
    servers = tuple(host_server(s.name, moved[s.name], s.image, s.version) if moved.get(s.name) else s for s in form.mcp)
    return replace(form, mcp=servers)


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

    return claude_code_agent(map_tool, series_tool, [(server.name, server.sandbox_url or server.url) for server in variant.mcp])


def server_instructions(servers: list[tuple[str, str | None]]) -> str | None:
    """The instructions of the MCP servers, by server name, as a client passes them to the model, verbatim, in the form Claude Code uses."""
    sections = [f"## {name}\n{instructions}" for name, instructions in servers if instructions]
    if not sections:
        return None
    return "# MCP Server Instructions\n\nThe following MCP servers have provided instructions for how to use their tools and resources:\n\n" + "\n\n".join(
        sections
    )


def record_mcp_servers(servers: tuple[McpServer, ...], infos: list) -> None:
    """Put the serverInfo of each initialize result in the sample store, so that the log says which server versions the run met.
    A server that reports another version than its pinned one raises, and Inspect fails the sample."""
    for server, info in zip(servers, infos):
        if server.version and info.version != server.version:
            raise RuntimeError(f"MCP server {server.name} at {server.url} reports version {info.version}, not {server.version} of {server.image}")
    store().set("mcp_server", [{"name": info.name, "title": info.title, "version": info.version} for info in infos])


def _connect(server: McpServer):
    return mcp_server_http(url=server.url) if server.url else mcp_server_stdio(command=server.command[0], args=list(server.command[1:]))


@solver
def probe_mcp_servers(servers: tuple[McpServer, ...]) -> Solver:
    """Record the server versions from the host, because Claude Code connects from its sandbox and the log would not know them.
    An unreachable server raises, and Inspect fails the sample, as the agent would not reach the server either."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        async with AsyncExitStack() as stack:
            connected = [await stack.enter_async_context(_connect(server)) for server in servers]
            record_mcp_servers(servers, [c._session.server_info for c in connected])
        return state

    return solve


@agent(name="react_with_mcp")
def _with_mcp(tools: list[Tool], mcp: tuple[McpServer, ...]) -> Agent:
    """Inspect's react() with the tools and servers of its own per sample, connected for the whole sample, and the servers' instructions in its prompt.
    Unconnected, every tool call would start a server anew."""

    async def execute(state: AgentState) -> AgentState:
        async with AsyncExitStack() as stack:
            connected = [await stack.enter_async_context(_connect(server)) for server in mcp]
            # Inspect keeps the initialize result in the session only; a server may explain its data there and nowhere else.
            sessions = [c._session for c in connected]
            record_mcp_servers(mcp, [s.server_info for s in sessions])
            prompt = AgentPrompt(instructions=server_instructions([(s.server_info.name, s.instructions) for s in sessions]))
            sources = [ProviderNamedTools(c) for c in connected]
            return await react(prompt=prompt, tools=[*tools, *sources], submit=AgentSubmit(answer_only=True))(state)

    return execute


def _setup(agent: AgentName, form: Variant):
    if agent != "claude-code":
        return None
    from .claude_code import claude_code_setup

    if form.mcp:
        return chain(claude_code_setup(), probe_mcp_servers(form.mcp))
    return claude_code_setup()


def _metadata(testset: str, variant: str, agent: AgentName, form: Variant) -> dict:
    """What a run used besides the code, which the git revision in the log identifies."""
    return {
        "harness": {"airco-harness": version("airco-harness"), "inspect-ai": version("inspect-ai")},
        "setup": 2 if agent == "claude-code" else 1,
        "agent": agent,
        "testset": {"name": testset, "version": dataset.manifest(testset)["version"]},
        "variant": variant,
        "variant_form": asdict(form),
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
      variant: Variant: 0, the question alone; mcp-groundwater-monitoring, mcp-bag-ldproxy or mcp-bgt-wijkenbuurten-subsurface (agents inspect and claude-code), variant 0 plus MCP servers.
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
    form = variant_form(variant)
    chosen = samples(testset, variant, ids=ids.split(",") if isinstance(ids, str) else ids, tags=tags.split(",") if isinstance(tags, str) else tags)
    if not len(chosen):
        raise ValueError(f"no samples of test set {testset} for variant {variant}; choose others with ids or tags")
    return Task(
        dataset=chosen,
        setup=_setup(agent, form),
        solver=as_solver(_agent(agent, dataset.asks_for_map(testset), dataset.asks_for_series(testset), form)),
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
        metadata=_metadata(testset, variant, agent, form),
    )
