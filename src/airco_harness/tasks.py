"""The airco task: a test set on one variant with one agent, as an Inspect Task.

The harness measures the baseline: the question as a user asks it, to the agent
as the user has it. Variant 0 is the question alone. Three agents answer it:
"model" is the model without a system prompt and without tools, the floor;
"inspect" is Inspect's own react() agent with its prompt, web search and a
fetch tool, the same for every model; "claude-code" is Claude Code with its
own prompt and tools, what a user has. In a test set with a map question, the
agents inspect and claude-code also get show_on_map, the map a user sees.
"""

import os
from importlib.metadata import version
from pathlib import Path
from typing import Literal, get_args

from dotenv import find_dotenv, load_dotenv
from inspect_ai import Task, task
from inspect_ai.agent import Agent, AgentSubmit, as_solver, react
from inspect_ai.model import GenerateConfig
from inspect_ai.tool import web_search

from . import dataset
from .models import register_costs
from .scorers import quality, source
from .tools import fetch, show_on_map

VARIANTS = ("0",)
AgentName = Literal["model", "inspect", "claude-code"]
MAX_TOOL_OUTPUT = 48 * 1024
SANDBOX_COMPOSE = Path(__file__).parent / "sandbox" / "compose.yaml"


def _agent(agent: AgentName, map_tool: bool) -> Agent:
    if agent == "model":
        # No system prompt, no tools, no submit tool: the agent is done when the model stops calling tools, and its last message is the answer.
        return react(prompt=None, tools=[], submit=False)
    if agent == "inspect":
        # Inspect's defaults: its own system prompt and submit tool. web_search() uses the search of the model's own provider.
        return react(tools=[web_search(), fetch(), *([show_on_map()] if map_tool else [])], submit=AgentSubmit(answer_only=True))
    from .claude_code import claude_code_agent

    return claude_code_agent(map_tool)


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
    }


@task
def airco(
    testset: str = dataset.DEFAULT_TESTSET,
    variant: str = "0",
    agent: AgentName = "model",
    ids: str | list[str] | None = None,
    model: str | None = None,
    message_limit: int = 60,
    token_limit: int = 600_000,
    time_limit: int = 900,
    cost_limit: float | None = 2.0,
) -> Task:
    """The test set on one variant of the publication form, with one agent.

    Args:
      testset: Test set under testsets/.
      variant: Variant: 0, the question alone.
      agent: model for the model without prompt or tools; inspect for Inspect's react() with web search and fetch; claude-code for Claude Code in a Docker sandbox.
      ids: Comma-separated sample ids; default all samples.
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
    load_dotenv(find_dotenv(usecwd=True))
    register_costs()
    selected = ids.split(",") if isinstance(ids, str) else ids
    return Task(
        dataset=dataset.load(testset, ids=selected),
        setup=_setup(agent),
        solver=as_solver(_agent(agent, dataset.asks_for_map(testset))),
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
