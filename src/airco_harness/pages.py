"""Build a static site with every committed measurement, for GitHub Pages.

    uv run airco-pages                  # writes site/
    python3 -m http.server -d site      # look at it on http://localhost:8000

The site is a dashboard over all measurements under reports/<name>/logs/logs:

- index.html, the overview: every measurement, and the latest per test set as a
  model x agent heatmap;
- <name>/report.html, a measurement: its main finding, correct or complete per
  model and agent with the gain of each variant over variant 0, the questions that fail,
  the cost per correct answer, and per question every run as a mark that opens
  the run with a link into the log and, for a map question, its map on the BRT
  achtergrondkaart of PDOK in RD (EPSG:28992);
- compare.html: measurements over time, variants, models or agents side by side,
  each group scored on the samples all groups have;
- <name>/viewer/, the Inspect viewer (inspect view bundle) with the logs.

The pages are thin HTML shells; site/app.js renders them from data.json, which
sitedata.py reads from the logs. The statistics are in site/stats.js and agree
with airco-report (tests/test_site_stats.py). The site is built from what is in
git and is not committed itself; .github/workflows/pages.yml builds and deploys
it on every push to main.

Reading a measurement's logs and bundling its viewer take most of the build.
With --cache, each measurement's part is kept under a key of its logs and of
everything else it is read with (CODE), and a later build reuses it while
neither changed. A change to the pages' scripts alone rebuilds nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
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
REPO = "https://github.com/Geonovum-labs/airco-harness"
# The GitHub mark from GitHub's Octicons (mark-github, 16 px), in the colour of the text around it.
GITHUB_MARK = (
    '<svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true" fill="currentColor"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 '
    "8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15"
    ".08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12"
    "-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38"
    '.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path></svg>'
)
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
# What a measurement's part of the site is read with besides its logs: the harness and its rules, the test sets, the
# reference sources and models, the prices and the locked dependencies. The pages' own scripts (ASSETS) are left out.
CODE = ["src", "validators", "testsets", "sources", "reference-models", "model-costs.yaml", "pyproject.toml", "uv.lock"]


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


def digest(base: Path, paths: list[Path]) -> str:
    """The SHA-256 of the files under `paths`, their paths relative to `base` included, without Python's caches."""
    h = hashlib.sha256()
    for path in paths:
        files = [path] if path.is_file() else sorted(path.rglob("*"))
        for file in files:
            if file.is_file() and "__pycache__" not in file.parts and not file.is_relative_to(ASSETS):
                h.update(f"{file.relative_to(base).as_posix()}\0{file.stat().st_size}\0".encode())
                h.update(file.read_bytes())
    return h.hexdigest()


def part(m: Path, out: Path, entry: Path | None) -> tuple[dict, list[dict], dict]:
    """A measurement's facts, runs and maps, with its viewer written to out; from the cache entry when it is there."""
    log_dir = m / "logs" / "logs"
    viewer = out / m.name / "viewer"
    if entry and (entry / "part.json").exists():
        shutil.copytree(entry / "viewer", viewer)
        return tuple(json.loads((entry / "part.json").read_text(encoding="utf-8")))
    bundle(log_dir, viewer, Path("reports") / m.name / "logs" / "logs")
    found = sitedata.measurement(m.name, log_dir)
    if entry:
        # part.json is written last, so an entry that a crash left half written is read again rather than used.
        shutil.rmtree(entry, ignore_errors=True)
        shutil.copytree(viewer, entry / "viewer")
        (entry / "part.json").write_text(json.dumps(found, ensure_ascii=False), encoding="utf-8")
    return found


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
        f'<header><div class="inner"><a class="site" href="{root}index.html">{SITE}</a><nav>{nav}</nav><span class="tagline">{TAGLINE}</span>'
        f'<a class="repo" href="{REPO}" title="airco-harness on GitHub" aria-label="airco-harness on GitHub">{GITHUB_MARK}</a></div></header>\n'
        '<main id="app"><p class="empty">Loading the measurements…</p><noscript><p>This page needs JavaScript; the reports are also in the repository as report.md.</p></noscript></main>\n'
        f'<footer>{built}the repository <a href="{REPO}">airco-harness</a>. '
        "The logs in the repository are the source; this site is generated from them.</footer>\n"
        f'<script type="module" src="{root}assets/app.js"></script>\n'
        "</body>\n</html>\n"
    )


def build(reports: Path, out: Path, cache: Path | None = None) -> list[dict]:
    """The whole site in `out`; the facts of each measurement, newest first. A cache keeps only what this build used."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    found = measurements(reports)
    code = digest(ROOT, [ROOT / p for p in CODE]) if cache else ""
    entries = {m: cache / f"{m.name}-{hashlib.sha256((code + digest(m, [m / 'logs' / 'logs'])).encode()).hexdigest()[:20]}" if cache else None for m in found}
    data = sitedata.dataset([part(m, out, entries[m]) for m in found])
    if cache and cache.is_dir():
        for stale in set(cache.iterdir()) - set(entries.values()):
            shutil.rmtree(stale)
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
    parser.add_argument("--cache", help="folder that keeps each measurement's part between builds; none by default")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = build(Path(args.reports), Path(args.out), Path(args.cache) if args.cache else None)
    print(f"{len(rows)} measurement{'' if len(rows) == 1 else 's'}; {args.out}/index.html")
