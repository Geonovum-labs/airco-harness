"""The airco task: a test set on one variant with one agent, as an Inspect Task.

The harness measures the baseline: the question as a user asks it, to the agent
as the user has it. Variant 0 is the question alone; another variant adds a
publication form the agent can reach, such as an MCP server or a skill, and
variants join with a plus, as in mcp-dsfl-context+skill-metadata. Three agents answer it:
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

import yaml
from dotenv import find_dotenv, load_dotenv
from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentPrompt, AgentState, AgentSubmit, agent, as_solver, react
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import Generate, Solver, TaskState, chain, solver
from inspect_ai.tool import Skill, Tool, mcp_server_http, mcp_server_stdio, skill, web_search
from inspect_ai.util import store

from . import dataset, mcpwire, pinned
from .mcpwire import McpRecorder
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
    # For a server that runs on the host: the image it runs, pinned by digest, and the serverInfo.version that image reports.
    # A server that reports another version fails the run, so a run never meets an image other than the one named here.
    image: str = ""
    version: str = ""
    # For a server whose image holds neither its configuration nor its data: the repository and commit that do.
    config: str = ""


def host_server(name: str, url: str, image: str, version: str, config: str = "") -> McpServer:
    """A server that runs on the host from a pinned image. Claude Code reaches it through the recording proxy, also on the host."""
    return McpServer(name, url=url, image=image, version=version, config=config)


def url_variable(server: McpServer) -> str:
    """The environment variable that moves a host server, such as AIRCO_SUBSURFACE_MODELS_URL."""
    return f"AIRCO_{server.name.upper().replace('-', '_')}_URL"


@dataclass(frozen=True)
class AgentSkill:
    """A skill a variant adds: the directory at `path` in github.com/<repository> at `commit`, fetched into .skills/ when a task needs it.
    A skill can point at directories next to its own, such as ../mim-core/; `beside` names them, and they are installed beside it."""

    repository: str
    commit: str
    path: str
    beside: tuple[str, ...] = ()

    @property
    def directories(self) -> list[Path]:
        """The skill's directory and those beside it, in the checkout of its commit; each is installed under its own name."""
        root = pinned.checkout(self.repository, self.commit, ".skills")
        return [root / self.path, *(root / name for name in self.beside)]

    def _skill_md(self) -> tuple[dict, str]:
        _, frontmatter, instructions = (self.directories[0] / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
        return yaml.safe_load(frontmatter), instructions.lstrip("\n")

    def installed(self) -> list[tuple[str, Path]]:
        """Each directory with the name it is installed under: the skill's under the name in its frontmatter, as the Agent Skills
        specification requires and Claude Code needs to find it, the directories beside it under their own. The MIM skill's
        directory is mim-interpret and its name geonovum-mim-interpret; ../mim-core/ still resolves beside it."""
        skill, *beside = self.directories
        return [(self._skill_md()[0]["name"], skill), *((d.name, d) for d in beside)]

    def for_inspect(self) -> Skill:
        """The skill as Inspect's skill tool takes it, from its SKILL.md as it is. Inspect reads a directory only when the
        name in its frontmatter is the directory's name, which the MIM skill's is not."""
        meta, instructions = self._skill_md()
        return Skill(name=meta["name"], description=meta["description"], instructions=instructions)


@dataclass(frozen=True)
class Variant:
    """A form in which the standard is published: what the agent gets besides the question."""

    about: str
    # The MCP servers the agent gets as tools, on top of the tools of variant 0.
    mcp: tuple[McpServer, ...] = ()
    # The skills the agent gets, on top of what it has in variant 0.
    skills: tuple[AgentSkill, ...] = ()
    # The samples the variant is made for: the default selection, which ids or tags override.
    tags: tuple[str, ...] = ()


# The two servers of github.com/sjaakd serve HTTP only, for linux/amd64, so they run on the host; docs/running.md has the docker run commands.
# Revision bc4a2a3 of 20 November 2026.
GROUNDWATER_MONITORING_IMAGE = "ghcr.io/sjaakd/mcp-groundwater-monitoring@sha256:0f4bd731e90fc2fcf29f0a221f93aa74d5b6c0d40d08a54adff07735a38577ee"
# Revision cb6b5d6 of 20 November 2026, with the GeoTOP and REGIS tiles of Amersfoort in the image.
SUBSURFACE_MODELS_IMAGE = "ghcr.io/sjaakd/mcp-subsurface-models@sha256:806d7ff5d58dab50c445dd7f1a4a1208e6b785eadcb759b589f7f66c48b36a2c"
# The servers of bag.ldproxy.net, run on the host from the ldproxy data directory of github.com/cportele/dsfl-ai at tag v0.2.0 (20 November 2026),
# with its dump of Amersfoort; airco-servers starts it. The ldproxy image is the tag aird-261120140038 that the repository names, by digest.
# From v0.1 only the image changed: the configuration, and so the serverInfo.version of each API, and the dump are the same.
DSFL_AI_REPOSITORY = "cportele/dsfl-ai"
DSFL_AI_COMMIT = "eb1d4450a9012c4f4221f05790b63cf69d3c130e"
DSFL_AI_CONFIG = f"https://github.com/{DSFL_AI_REPOSITORY}/tree/v0.2.0 ({DSFL_AI_COMMIT})"
LDPROXY_IMAGE = "iide/ldproxy@sha256:0af53a560fe4bfed814ac0f0f3935378afbd0605de5d184516d8146c4063b22e"
LDPROXY_DB_IMAGE = "imresamu/postgis@sha256:b5766ee720aca09c61b9a868abefbf273348a4b90ad4cf146b4f8c9ac85d48e4"


def ldproxy_server(name: str, version: str) -> McpServer:
    """An API of the ldproxy on the host; its serverInfo.version is the date of its configuration in the repository (yymmddHHMMSS)."""
    return host_server(name, f"http://localhost:7080/{name}/mcp", LDPROXY_IMAGE, version, DSFL_AI_CONFIG)


# The two skill repositories have no tags; each is pinned at a commit. The metadata skill at main of 20 November 2026.
METADATA_SKILL = AgentSkill("Bakkej/skills-metadata", "42902c7267227f229dd7778ce499b9fc27133900", "skills/metadata")
# The MIM skill at the head of branch cursor/add-experimental-model-catalog (pull request 1) of 19 November 2026, which adds an experimental
# model catalog and the MIM ambiguities to mim-core. Its README says to copy mim-interpret together with mim-core, which the skill reads as ../mim-core/.
MIM_SKILL = AgentSkill("Geonovum-labs/skills-mim", "34c66ee83bc9a3c234512787ea56a74501949232", "mim-interpret", beside=("mim-core",))
VARIANTS = {
    "0": Variant("The question alone: the agent finds the standard as it is published today, or not."),
    "mcp-groundwater-monitoring": Variant(
        "Variant 0 plus the groundwater monitoring MCP server on BRO data (github.com/sjaakd/mcp-groundwater-monitoring).",
        mcp=(host_server("groundwater-monitoring", "http://localhost:18081/mcp", GROUNDWATER_MONITORING_IMAGE, "1.0.10"),),
        tags=("groundwater",),
    ),
    "mcp-bag-ldproxy": Variant(
        "Variant 0 plus the MCP server of the BAG API of ldproxy (github.com/cportele/dsfl-ai, v0.2.0), which holds Amersfoort only "
        "(BAG extract of 8 October 2026), running on the host.",
        mcp=(ldproxy_server("bag", "261120115005"),),
        tags=("bag",),
    ),
    "mcp-bgt-wijkenbuurten-subsurface": Variant(
        "Variant 0 plus the MCP servers of the BGT and the CBS wijken en buurten of ldproxy (github.com/cportele/dsfl-ai, v0.2.0, Amersfoort) and the "
        "subsurface models MCP server (github.com/sjaakd/mcp-subsurface-models) with the Amersfoort extract of GeoTOP and REGIS in its image, all on the host.",
        mcp=(
            ldproxy_server("bgt", "261120115005"),
            ldproxy_server("wijkenbuurten", "261120104208"),
            host_server("subsurface-models", "http://localhost:18082/mcp", SUBSURFACE_MODELS_IMAGE, "1.0.13"),
        ),
        tags=("bgt",),
    ),
    # No question is made for it yet: its tag is on no sample, so a run of it needs ids or tags.
    "mcp-dsfl-context": Variant(
        "Variant 0 plus the semantic context MCP server on catalog.modeldesk.io, which answers what a published information standard "
        "says about its own elements (describe_standard, search_concepts, get_concepts, check_value).",
        mcp=(McpServer("dsfl-context", url="https://catalog.modeldesk.io/mcp/modeldesk/context"),),
        tags=("dsfl-context",),
    ),
    # Made for no sample in particular, like variant 0: on its own it takes every sample, joined to an MCP variant that variant's samples.
    "skill-metadata": Variant(
        "Variant 0 plus the metadata skill (github.com/Bakkej/skills-metadata), which leads an agent from glossaries, model repositories "
        "and data catalogs to a dataset and its access route, such as an MCP server or an OGC API.",
        skills=(METADATA_SKILL,),
    ),
    "skill-mim": Variant(
        "Variant 0 plus the MIM interpret skill (github.com/Geonovum-labs/skills-mim) with its shared mim-core, which reads a MIM-conformant "
        "information model to interpret the data it describes: objecttypen, attribuutsoorten, waardelijsten, kardinaliteit.",
        skills=(MIM_SKILL,),
    ),
}
JOIN = "+"
AgentName = Literal["model", "inspect", "claude-code"]
MAX_TOOL_OUTPUT = 48 * 1024
SANDBOX_COMPOSE = Path(__file__).parent / "sandbox" / "compose.yaml"


def compose(variant: str) -> Variant:
    """The variant by name, or the variants joined with a plus as one: their servers, skills and the samples any of them is made for."""
    parts = variant.split(JOIN)
    unknown = [part for part in parts if part not in VARIANTS]
    if unknown or len(set(parts)) < len(parts) or (len(parts) > 1 and "0" in parts):
        raise ValueError(f"unknown variant {variant!r}; choose from {', '.join(VARIANTS)}, or join variants other than 0 with {JOIN}")
    forms = [VARIANTS[part] for part in parts]
    if len(forms) == 1:
        return forms[0]
    return Variant(
        about=" Joined with: ".join(form.about for form in forms),
        mcp=tuple(server for form in forms for server in form.mcp),
        skills=tuple(s for form in forms for s in form.skills),
        tags=tuple(dict.fromkeys(tag for form in forms for tag in form.tags)),
    )


def takes(variant: str, agent: AgentName) -> bool:
    """Whether the agent can be given the variant's MCP servers and skills.

    The agent model has no tools. Claude Code reaches an HTTP server from its sandbox, but the sandbox cannot run a stdio server's container.
    """
    form = compose(variant)
    if agent == "model":
        return not form.mcp and not form.skills
    return agent == "inspect" or all(server.url for server in form.mcp)


def samples(testset: str, variant: str, ids: list[str] | None = None, tags: list[str] | None = None) -> MemoryDataset:
    """The samples a run of the variant takes: the ids or tags asked for, else those the variant is made for."""
    if ids is None and tags is None and compose(variant).tags:
        tags = list(compose(variant).tags)
    return dataset.load(testset, ids=ids, tags=tags)


def variant_form(variant: str) -> Variant:
    """The variant with a host server moved to the URL in its variable, read after .env is loaded."""
    form = compose(variant)
    moved = {s.name: os.environ.get(url_variable(s), "").strip() for s in form.mcp if s.image}
    servers = tuple(replace(s, url=moved[s.name]) if moved.get(s.name) else s for s in form.mcp)
    return replace(form, mcp=servers)


def _agent(agent: AgentName, map_tool: bool, series_tool: bool, variant: Variant) -> Agent:
    if agent == "model":
        # No system prompt, no tools, no submit tool: the agent is done when the model stops calling tools, and its last message is the answer.
        return react(prompt=None, tools=[], submit=False)
    if agent == "inspect":
        # Inspect's defaults: its own system prompt and submit tool. web_search() uses the search of the model's own provider.
        tools = [web_search(), fetch(), *([show_on_map()] if map_tool else []), *([plot_series()] if series_tool else [])]
        if variant.skills:
            # Inspect's own skill tool, unchanged: it writes the skills to the local sandbox and hands the model a skill's SKILL.md.
            tools.append(skill([s.for_inspect() for s in variant.skills]))
        if not variant.mcp:
            return react(tools=tools, submit=AgentSubmit(answer_only=True))
        # The MCP server comes on top of the tools of variant 0, so that the server is the one difference.
        return _with_mcp(tools, variant.mcp)
    from .claude_code import claude_code_agent

    if not variant.mcp:
        return claude_code_agent(map_tool, series_tool)
    return _claude_code_with_mcp(map_tool, series_tool, variant.mcp)


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


def _recorder(servers: tuple[McpServer, ...], bind: str = "127.0.0.1") -> McpRecorder:
    """The proxy that records what the agent sends to its HTTP servers and what they answer; keep() puts it in the sample store."""
    return McpRecorder({server.name: server.url for server in servers if server.url}, bind)


def _keep(recorder: McpRecorder) -> None:
    """Every MCP message as mcp_calls, and per server its summary as mcp_traffic, which the report reads without the messages."""
    store().set("mcp_calls", recorder.records)
    store().set("mcp_traffic", mcpwire.traffic(recorder.records))


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
        recorder = _recorder(mcp)
        try:
            async with recorder, AsyncExitStack() as stack:
                proxied = [replace(server, url=recorder.url(server.name)) if server.url else server for server in mcp]
                connected = [await stack.enter_async_context(_connect(server)) for server in proxied]
                # Inspect keeps the initialize result in the session only; a server may explain its data there and nowhere else.
                sessions = [c._session for c in connected]
                record_mcp_servers(mcp, [s.server_info for s in sessions])
                prompt = AgentPrompt(instructions=server_instructions([(s.server_info.name, s.instructions) for s in sessions]))
                sources = [ProviderNamedTools(c) for c in connected]
                return await react(prompt=prompt, tools=[*tools, *sources], submit=AgentSubmit(answer_only=True))(state)
        finally:
            _keep(recorder)

    return execute


@agent(name="claude_code_with_mcp")
def _claude_code_with_mcp(map_tool: bool, series_tool: bool, mcp: tuple[McpServer, ...]) -> Agent:
    """Claude Code with its HTTP servers behind the recording proxy, which it reaches from its sandbox at host.docker.internal.
    Its own MCP client logs nothing of the protocol, and the calls of its subagents are not in the conversation."""
    from .claude_code import claude_code_agent

    async def execute(state: AgentState) -> AgentState:
        recorder = _recorder(mcp, bind="0.0.0.0")
        try:
            async with recorder:
                servers = [(server.name, recorder.url(server.name, "host.docker.internal")) for server in mcp if server.url]
                return await claude_code_agent(map_tool, series_tool, servers)(state)
        finally:
            _keep(recorder)

    return execute


def _setup(agent: AgentName, form: Variant):
    if agent != "claude-code":
        return None
    from .claude_code import claude_code_setup

    setup = claude_code_setup([entry for s in form.skills for entry in s.installed()])
    if form.mcp:
        return chain(setup, probe_mcp_servers(form.mcp))
    return setup


def _sandbox(agent: AgentName, form: Variant):
    if agent == "claude-code":
        # A path relative to the working directory, so that the log names no home directory.
        return ("docker", os.path.relpath(SANDBOX_COMPOSE))
    # Inspect's skill tool writes the skills to a sandbox; a temporary directory on the host serves, as the agent runs nothing in it.
    return "local" if form.skills else None


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
      variant: Variant: 0, the question alone; mcp-groundwater-monitoring, mcp-bag-ldproxy, mcp-bgt-wijkenbuurten-subsurface or mcp-dsfl-context, variant 0 plus MCP servers; skill-metadata or skill-mim, variant 0 plus a skill. Join variants with +, as in mcp-dsfl-context+skill-metadata. All but 0 for the agents inspect and claude-code.
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
    compose(variant)
    if agent not in get_args(AgentName):
        raise ValueError(f"unknown agent {agent!r}; choose from {', '.join(get_args(AgentName))}")
    if not takes(variant, agent):
        raise ValueError(f"the agent {agent} does not take the MCP servers or skills of variant {variant}")
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
        sandbox=_sandbox(agent, form),
        model=model,
        message_limit=message_limit,
        token_limit=token_limit,
        time_limit=time_limit,
        cost_limit=cost_limit,
        version="0.1",
        metadata=_metadata(testset, variant, agent, form),
    )
