"""Build a static site with every committed measurement, for GitHub Pages.

    uv run airco-pages                  # writes site/
    python3 -m http.server -d site      # look at it on http://localhost:8000

The site is a dashboard over all measurements under reports/<name>/logs/logs:

- index.html, the overview: every measurement, and the latest per test set as a
  model x agent heatmap;
- <name>/report.html, a measurement: the heatmap of a chosen metric, the runs of
  a chosen model and agent with links into the log, and for a map question the
  map of each run on the BRT achtergrondkaart of PDOK in RD (EPSG:28992);
- compare.html: measurements over time, variants, models or agents side by side,
  each group scored on the samples all groups have;
- <name>/viewer/, the Inspect viewer (inspect view bundle) with the logs.

The pages are thin HTML shells; site/app.js renders them from data.json, which
sitedata.py reads from the logs. The statistics are in site/stats.js and agree
with airco-report (tests/test_site_stats.py). The site is built from what is in
git and is not committed itself; .github/workflows/pages.yml builds and deploys
it on every push to main.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import sitedata
from .matrix import strip_absolute_log_dir

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = Path(__file__).resolve().parent / "site"
SITE = "airco-harness"
TAGLINE = "Measurements of the test harness of the AI Ready Standaarden project"
# Pinned versions from cdnjs and jsDelivr; Leaflet and Proj4Leaflet only on a page that can draw a map.
SCRIPTS = [
    "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js",
    "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.17/dist/plot.umd.min.js",
]
MAP_SCRIPTS = [
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js",
    "https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.11.0/proj4.js",
    "https://cdnjs.cloudflare.com/ajax/libs/proj4leaflet/1.0.2/proj4leaflet.min.js",
]
MAP_STYLE = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"


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


def page(title: str, kind: str, root: str, current: str, extra: dict[str, str] | None = None, maps: bool = False) -> str:
    """A shell in the site's layout; app.js fills <main> for the page `kind` (overview, measurement or compare)."""
    commit = os.environ.get("GITHUB_SHA", "")[:7]
    built = f"Built from commit <code>{commit}</code> of " if commit else "Built from "
    attributes = "".join(f' data-{k}="{html.escape(v)}"' for k, v in (extra or {}).items())
    links = [("Measurements", f"{root}index.html", "overview"), ("Compare", f"{root}compare.html", "compare")]
    nav = "".join(f'<a href="{href}"{" aria-current=page" if key == current else ""}>{text}</a>' for text, href, key in links)
    styles = [f'<link rel="stylesheet" href="{root}assets/style.css">'] + ([f'<link rel="stylesheet" href="{MAP_STYLE}">'] if maps else [])
    scripts = [f'<script src="{src}"></script>' for src in SCRIPTS + (MAP_SCRIPTS if maps else [])]
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n" + "\n".join(styles + scripts) + "\n</head>\n"
        f'<body data-page="{kind}" data-root="{root}"{attributes}>\n'
        f'<header><div class="inner"><a class="site" href="{root}index.html">{SITE}</a><nav>{nav}</nav><span class="tagline">{TAGLINE}</span></div></header>\n'
        '<main id="app"><p class="empty">Loading the measurements…</p><noscript><p>This page needs JavaScript; the reports are also in the repository as report.md.</p></noscript></main>\n'
        f'<footer>{built}the repository <a href="https://github.com/Geonovum-labs/airco-harness">airco-harness</a>. '
        "The logs in the repository are the source; this site is generated from them.</footer>\n"
        f'<script type="module" src="{root}assets/app.js"></script>\n'
        "</body>\n</html>\n"
    )


def build(reports: Path, out: Path) -> list[dict]:
    """The whole site in `out`; the facts of each measurement, newest first."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    found = measurements(reports)
    for m in found:
        bundle(m / "logs" / "logs", out / m.name / "viewer", Path("reports") / m.name / "logs" / "logs")
    data = sitedata.dataset(found)
    sitedata.write(data, out)
    shutil.copytree(ASSETS, out / "assets")
    (out / "index.html").write_text(page(f"{SITE}: measurements", "overview", "./", "overview"), encoding="utf-8")
    (out / "compare.html").write_text(page(f"{SITE}: compare", "compare", "./", "compare"), encoding="utf-8")
    for facts in data["measurements"]:
        has_map = any(r.get("map") for r in data["runs"] if r["m"] == facts["name"])
        shell = page(f"{SITE}: measurement {facts['name']}", "measurement", "../", "", {"measurement": facts["name"]}, maps=has_map)
        (out / facts["name"] / "report.html").write_text(shell, encoding="utf-8")
    (out / ".nojekyll").touch()
    return data["measurements"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airco-pages", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reports", default=str(ROOT / "reports"), help="folder with one bundle per measurement")
    parser.add_argument("--out", default=str(ROOT / "site"), help="output folder; it is emptied first")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = build(Path(args.reports), Path(args.out))
    print(f"{len(rows)} measurement{'' if len(rows) == 1 else 's'}; {args.out}/index.html")
