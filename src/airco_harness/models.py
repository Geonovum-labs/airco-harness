"""Model prices: the ceiling Inspect gets for total_cost and cost_limit, and the exact price of one call for the report.

Inspect 0.3.281 has no prices for the models in the matrix, and its own
--model-cost-config only accepts models in its database, so custom endpoints
(vLLM at Kadaster, a local OpenAI-compatible server) must be registered with
set_model_info. The prices come from model-costs.yaml in the repo root, which
names its sources and the date the prices were read.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values, find_dotenv
from inspect_ai.model import ModelCost, ModelInfo, ModelUsage, compute_model_cost, get_model_info, set_model_cost, set_model_info
from pydantic import BaseModel, ConfigDict, ValidationError

COSTS_ENV = "AIRCO_MODEL_COSTS"
DEFAULT_COSTS_FILE = "model-costs.yaml"


class Rates(BaseModel):
    """Dollars per million tokens."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    input: float
    output: float
    input_cache_write: float
    input_cache_read: float

    def cost(self) -> ModelCost:
        return ModelCost(input=self.input, output=self.output, input_cache_write=self.input_cache_write, input_cache_read=self.input_cache_read)


class LongPrompt(Rates):
    above: int  # a call whose prompt has more tokens than this pays these rates


class Price(Rates):
    web_search: float = 0.0  # dollars per successful server-side web search
    long_prompt: LongPrompt | None = None

    def ceiling(self) -> ModelCost:
        """The highest rates, for Inspect: its total_cost and cost_limit never stop a run too late."""
        return (self.long_prompt or self).cost()

    def call(self, usage: ModelUsage, cache_ttl: str | None = None) -> float:
        """Dollars for one model call, without web searches; cache reads and writes count toward the prompt length."""
        prompt = usage.input_tokens + (usage.input_tokens_cache_write or 0) + (usage.input_tokens_cache_read or 0)
        rates = self.long_prompt if self.long_prompt and prompt > self.long_prompt.above else self
        return compute_model_cost(rates.cost(), usage, cache_ttl)

    def cache_ttl(self, usage: ModelUsage) -> str | None:
        """The cache TTL Inspect billed the call's cache writes at, recovered from its logged total_cost.

        Inspect bills 1h cache writes higher but keeps the TTL out of the usage it logs. It priced the call
        at the base rates (logs before the long_prompt tier was registered) or at the ceiling (since)."""
        if usage.total_cost is None or not usage.input_tokens_cache_write:
            return None
        for ttl in ("5m", "1h"):
            for rates in (self, self.long_prompt):
                if rates and math.isclose(compute_model_cost(rates.cost(), usage, ttl), usage.total_cost, rel_tol=1e-6):
                    return ttl
        return None


FREE = Price(input=0, output=0, input_cache_write=0, input_cache_read=0)


def costs_file() -> Path:
    """The price file that AIRCO_MODEL_COSTS names, in the environment or in .env; a relative path is taken from the folder of .env."""
    env_file = find_dotenv(usecwd=True)
    name = os.environ.get(COSTS_ENV) or (env_file and dotenv_values(env_file).get(COSTS_ENV)) or DEFAULT_COSTS_FILE
    path = Path(name)
    return path if path.is_absolute() or not env_file else Path(env_file).parent / path


def load_prices(file: Path | None = None) -> dict[str, Price]:
    """Dollars per million tokens per model, as the price file names them; the mock model is free."""
    file = file or costs_file()
    prices = {"mockllm/model": FREE}
    if file.exists():
        for name, entry in (yaml.safe_load(file.read_text(encoding="utf-8")) or {}).items():
            try:
                prices[name] = Price(**entry)
            except ValidationError as error:
                raise ValueError(f"{file}: price of {name}: {error}") from error
    return prices


def register_costs(file: Path | None = None) -> dict[str, Price]:
    prices = load_prices(file)
    for name, price in prices.items():
        cost = price.ceiling()
        if get_model_info(name) is None:
            set_model_info(name, ModelInfo(model=name, cost=cost))
        else:
            set_model_cost(name, cost)
    return prices
