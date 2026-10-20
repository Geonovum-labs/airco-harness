"""The full matrix as one eval_set: test set x variants x agent-model pairs x epochs.

    uv run airco-matrix --models anthropic/claude-haiku-5-5,openai-api/kadaster/qwen3.5-27b --epochs 3
    uv run airco-matrix --models anthropic/claude-haiku-5-5 --agents model,inspect,claude-code --epochs 3
    uv run airco-matrix --models mockllm/model --name dry-run   # dry run without keys

Paid models need --yes after the planned number of runs is shown. The logs and
the bundle are named after the start time unless --name says otherwise.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import get_args

from dotenv import find_dotenv, load_dotenv
from inspect_ai import eval_set

from . import dataset
from .tasks import VARIANTS, AgentName, airco

FREE_PREFIXES = ("mockllm/", "openai-api/local/", "ollama/")
# Claude Code is built for Claude: behind the bridge another model does not use its tools, so such a run measures nothing.
CLAUDE_CODE_PROVIDERS = ("anthropic/", "mockllm/")


def strip_absolute_log_dir(bundle_dir: Path, log_dir: Path) -> None:
    """inspect view bundle writes the absolute log folder into index.html; keep the builder's home directory out."""
    index = bundle_dir / "index.html"
    html = index.read_text(encoding="utf-8")
    index.write_text(re.sub(r'"abs_log_dir": "[^"]*"', f'"abs_log_dir": "{log_dir.as_posix()}"', html), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-matrix", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--testset", default=dataset.DEFAULT_TESTSET, help="test set under testsets/")
    parser.add_argument("--models", default=None, help="comma-separated models; default AIRCO_MATRIX_MODELS")
    parser.add_argument("--variants", default=",".join(VARIANTS), help="comma-separated variants")
    parser.add_argument("--ids", default=None, help="comma-separated sample ids; default all samples")
    parser.add_argument("--epochs", type=int, default=3, help="runs per sample, variant and model")
    parser.add_argument(
        "--agents",
        default="model",
        help="comma-separated agents: model (the model alone), inspect (Inspect's react agent with web search and fetch), claude-code (Claude Code in a Docker sandbox)",
    )
    parser.add_argument(
        "--name",
        default=datetime.now().strftime("%Y-%m-%dT%H-%M-%S"),
        help="log folder logs/<name> and bundle reports/<name>/logs; default the start time, so that bundles sort by time",
    )
    parser.add_argument("--max-samples", type=int, default=8, help="samples that run at the same time")
    parser.add_argument("--cost-limit", type=float, default=0.5, help="cost limit per run in dollars")
    parser.add_argument("--yes", action="store_true", help="confirm a run against paid models")
    return parser


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    args = build_parser().parse_args()
    args.models = args.models or os.environ.get("AIRCO_MATRIX_MODELS")
    if not args.models:
        build_parser().error("no models: pass --models or set AIRCO_MATRIX_MODELS")
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    variants = [v.strip() for v in args.variants.split(",")]
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    unknown = [a for a in agents if a not in get_args(AgentName)]
    if unknown:
        build_parser().error(f"unknown agents {', '.join(unknown)}; choose from {', '.join(get_args(AgentName))}")
    ids = args.ids.split(",") if args.ids else None

    n_samples = len(dataset.load(args.testset, ids=ids))
    combos = [(v, a, m) for v in variants for a in agents for m in models if a != "claude-code" or m.startswith(CLAUDE_CODE_PROVIDERS)]
    skipped = sorted({m for a in agents for m in models if a == "claude-code" and not m.startswith(CLAUDE_CODE_PROVIDERS)})
    runs = n_samples * len(combos) * args.epochs
    paid = [m for m in models if not m.startswith(FREE_PREFIXES)]
    print(
        f"{n_samples} samples x {len(combos)} agent-model pairs x {args.epochs} epochs = {runs} runs ({len(variants)} variants, {len(agents)} agents, {len(models)} models)"
    )
    if skipped:
        print(f"claude-code runs on Anthropic models only; skipped for {', '.join(skipped)}")
    print(f"at most {runs} x {args.cost_limit:.2f} = {runs * args.cost_limit:.2f} dollars for paid models")
    if paid and not args.yes:
        print(f"paid models {', '.join(paid)}: rerun with --yes to start", file=sys.stderr)
        sys.exit(2)

    tasks = [airco(testset=args.testset, variant=v, agent=a, model=m, ids=ids, cost_limit=args.cost_limit) for v, a, m in combos]
    log_dir = Path("logs") / args.name
    bundle_dir = Path("reports") / args.name / "logs"
    success, _ = eval_set(
        tasks,
        log_dir=str(log_dir),
        epochs=args.epochs,
        max_samples=args.max_samples,
        bundle_dir=str(bundle_dir),
        bundle_overwrite=True,
    )
    strip_absolute_log_dir(bundle_dir, log_dir)
    print(f"logs in {log_dir}; report next to the bundle with: uv run airco-report {log_dir} --out {bundle_dir.parent}")
    sys.exit(0 if success else 1)
