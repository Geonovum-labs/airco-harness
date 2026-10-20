"""Model prices for total_cost and cost_limit.

Inspect 0.3.281 has no prices for the models in the matrix, and its own
--model-cost-config only accepts models in its database, so custom endpoints
(vLLM at Kadaster, a local OpenAI-compatible server) must be registered with
set_model_info. The prices come from model-costs.yaml in the repo root, which
names its sources and the date the prices were read.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import dotenv_values, find_dotenv
from inspect_ai.model import ModelCost, ModelInfo, get_model_info, set_model_cost, set_model_info

COSTS_ENV = "AIRCO_MODEL_COSTS"
DEFAULT_COSTS_FILE = "model-costs.yaml"
FREE = ModelCost(input=0, output=0, input_cache_write=0, input_cache_read=0)


def costs_file() -> Path:
    """The price file that AIRCO_MODEL_COSTS names, in the environment or in .env; a relative path is taken from the folder of .env."""
    env_file = find_dotenv(usecwd=True)
    name = os.environ.get(COSTS_ENV) or (env_file and dotenv_values(env_file).get(COSTS_ENV)) or DEFAULT_COSTS_FILE
    path = Path(name)
    return path if path.is_absolute() or not env_file else Path(env_file).parent / path


def load_prices(file: Path | None = None) -> dict[str, ModelCost]:
    """Dollars per million tokens per model, as the price file names them; the mock model is free."""
    file = file or costs_file()
    prices = {"mockllm/model": FREE}
    if file.exists():
        prices |= {name: ModelCost(**entry) for name, entry in (yaml.safe_load(file.read_text(encoding="utf-8")) or {}).items()}
    return prices


def register_costs(file: Path | None = None) -> dict[str, ModelCost]:
    prices = load_prices(file)
    for name, cost in prices.items():
        if get_model_info(name) is None:
            set_model_info(name, ModelInfo(model=name, cost=cost))
        else:
            set_model_cost(name, cost)
    return prices
