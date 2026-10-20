"""Build a static site with every committed measurement, for GitHub Pages.

    uv run airco-pages                  # writes site/
    python3 -m http.server -d site      # look at it on http://localhost:8000

For each reports/<name>/logs/logs with .eval files, the site gets the Inspect
viewer (inspect view bundle) under <name>/viewer/ and report.md as
<name>/report.html, plus an index of all measurements, newest first. The site
is built from what is in git and is not committed itself;
.github/workflows/pages.yml builds and deploys it on every push to main.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import markdown
import pandas as pd

from .matrix import strip_absolute_log_dir

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = "airco-harness"
TAGLINE = "Measurements of the test harness of the AI Ready Standaarden project"
STYLE = """
:root { --bg: #ffffff; --fg: #1f2328; --muted: #59636e; --line: #d0d7de; --head: #f6f8fa; --accent: #0b5fa5; --chip: #eef3f8; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #0f1419; --fg: #e6edf3; --muted: #9da7b1; --line: #30363d; --head: #161b22; --accent: #79b8ff; --chip: #1c2530; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
header { border-bottom: 1px solid var(--line); background: var(--head); }
.inner { max-width: 68rem; margin: 0 auto; padding: 0.9rem 1.25rem; }
header .inner { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; align-items: baseline; }
header a.site { font-weight: 650; font-size: 1.1rem; color: var(--fg); text-decoration: none; }
header .tagline { color: var(--muted); font-size: 0.95rem; }
main { max-width: 68rem; margin: 0 auto; padding: 0.5rem 1.25rem 2rem; }
h1 { font-size: 1.75rem; line-height: 1.25; margin: 1.5rem 0 0.5rem; }
h2 { font-size: 1.2rem; margin: 2.25rem 0 0.6rem; }
p { max-width: 50rem; }
p.lead { color: var(--muted); font-size: 1.05rem; }
a { color: var(--accent); }
nav.crumbs { font-size: 0.9rem; color: var(--muted); margin-top: 1.25rem; }
.tablewrap { overflow-x: auto; margin: 1rem 0 1.5rem; border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; font-size: 0.95rem; }
th, td { padding: 0.55rem 0.8rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }
th { background: var(--head); color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.when { white-space: nowrap; font-weight: 600; }
td.when small { display: block; font-weight: 400; color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.78rem; }
.chip { display: inline-block; font: 0.78rem/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; background: var(--chip); border: 1px solid var(--line); border-radius: 4px; padding: 0 0.4rem; margin: 0.1rem 0.25rem 0.1rem 0; white-space: nowrap; }
a.btn { display: inline-block; border: 1px solid var(--line); border-radius: 6px; padding: 0.15rem 0.6rem; margin: 0.1rem 0.25rem 0.1rem 0; text-decoration: none; background: var(--bg); white-space: nowrap; }
a.btn:hover { border-color: var(--accent); }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; background: var(--chip); padding: 0 0.25rem; border-radius: 3px; }
footer { max-width: 68rem; margin: 0 auto; padding: 1rem 1.25rem 2rem; color: var(--muted); font-size: 0.85rem; border-top: 1px solid var(--line); }
"""


def measurements(reports: Path) -> list[Path]:
    """The report folders that hold logs, newest first; the folder name is the start time of the matrix."""
    found = [d for d in reports.iterdir() if d.is_dir() and any((d / "logs" / "logs").glob("*.eval"))] if reports.is_dir() else []
    return sorted(found, key=lambda d: d.name, reverse=True)


def bundle(log_dir: Path, out: Path, shown_log_dir: Path) -> None:
    """The Inspect viewer with the logs copied in; the same command airco-matrix runs after a matrix."""
    inspect = Path(sys.executable).parent / "inspect"
    subprocess.run(
        [str(inspect), "view", "bundle", "--log-dir", str(log_dir), "--output-dir", str(out), "--overwrite"], check=True, capture_output=True, text=True
    )
    strip_absolute_log_dir(out, shown_log_dir)


def summary(measurement: Path) -> dict:
    runs = pd.read_csv(measurement / "runs.csv")
    return {
        "name": measurement.name,
        "samples": runs["sample"].nunique(),
        "variants": sorted(runs["variant"].astype(str).unique()),
        "agents": sorted(runs["agent"].astype(str).unique()) if "agent" in runs else ["model"],
        "models": sorted(runs["model"].unique()),
        "runs": len(runs),
        "cost": float(runs["cost"].sum()),
    }


def page(title: str, body: str, home: str = "./") -> str:
    """One page in the site's layout: header with the site name, the body in main, a footer with the source."""
    commit = os.environ.get("GITHUB_SHA", "")[:7]
    built = f"Built from commit <code>{commit}</code> of " if commit else "Built from "
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<header><div class="inner"><a class="site" href="{home}">{SITE}</a><span class="tagline">{TAGLINE}</span></div></header>\n'
        f"<main>\n{body}\n</main>\n"
        f'<footer>{built}the repository <a href="https://github.com/Geonovum-labs/airco-harness">airco-harness</a>. '
        "The logs in the repository are the source; this site is generated from them.</footer>\n"
        "</body>\n</html>\n"
    )


def when(name: str) -> str:
    """The start time in the folder name as a date for people, or the name itself."""
    try:
        return datetime.strptime(name, "%Y-%m-%dT%H-%M-%S").strftime("%-d %B %Y, %H:%M")
    except ValueError:
        return name


def tables_scrollable(fragment: str) -> str:
    return fragment.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")


def index(rows: list[dict]) -> str:
    body = [
        "<h1>Measurements</h1>",
        '<p class="lead">Each measurement is one matrix of the test harness of the <a href="https://geonovum-labs.github.io/airco/">AI Ready Standaarden project</a>: '
        "a test set on one or more variants of the publication form, against one or more models. "
        "The report gives the metrics per model and variant; the viewer shows every run with its tool calls and scores.</p>",
    ]
    if not rows:
        body.append("<p>No measurements yet.</p>")
        return page(f"{SITE}: measurements", "\n".join(body))
    body += [
        '<div class="tablewrap"><table>',
        '<thead><tr><th>Start</th><th class="num">Samples</th><th>Variants</th><th>Agents</th><th>Models</th><th class="num">Runs</th><th class="num">Cost ($)</th><th></th></tr></thead>',
        "<tbody>",
    ]
    for r in rows:
        name = html.escape(r["name"])
        chips = "".join(f'<span class="chip">{html.escape(m)}</span>' for m in r["models"])
        body.append(
            f'<tr><td class="when">{html.escape(when(r["name"]))}<small>{name}</small></td><td class="num">{r["samples"]}</td>'
            f'<td>{html.escape(", ".join(r["variants"]))}</td><td>{html.escape(", ".join(r["agents"]))}</td><td>{chips}</td><td class="num">{r["runs"]}</td><td class="num">{r["cost"]:.2f}</td>'
            f'<td><a class="btn" href="{name}/report.html">Report</a><a class="btn" href="{name}/viewer/">Viewer</a></td></tr>'
        )
    body += ["</tbody></table></div>"]
    return page(f"{SITE}: measurements", "\n".join(body))


def build(reports: Path, out: Path) -> list[dict]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rows = []
    for m in measurements(reports):
        target = out / m.name
        bundle(m / "logs" / "logs", target / "viewer", Path("reports") / m.name / "logs" / "logs")
        report = tables_scrollable(markdown.markdown((m / "report.md").read_text(encoding="utf-8"), extensions=["tables"]))
        crumbs = (
            f'<nav class="crumbs"><a href="../">All measurements</a> &rsaquo; {html.escape(when(m.name))} &middot; <a href="viewer/">Open the viewer</a></nav>'
        )
        (target / "report.html").write_text(page(f"{SITE}: report {m.name}", f"{crumbs}\n{report}", home="../"), encoding="utf-8")
        rows.append(summary(m))
    (out / "index.html").write_text(index(rows), encoding="utf-8")
    (out / ".nojekyll").touch()
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-pages", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reports", default=str(ROOT / "reports"), help="folder with one bundle per measurement")
    parser.add_argument("--out", default=str(ROOT / "site"), help="output folder; it is emptied first")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = build(Path(args.reports), Path(args.out))
    print(f"{len(rows)} measurement{'' if len(rows) == 1 else 's'}; {args.out}/index.html")
