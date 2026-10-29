"""Build a static site with every committed measurement, for GitHub Pages.

    uv run airco-pages                  # writes site/
    python3 -m http.server -d site      # look at it on http://localhost:8000

For each reports/<name>/logs/logs with .eval files, the site gets the Inspect
viewer (inspect view bundle) under <name>/viewer/ and report.md as
<name>/report.html, plus an index of all measurements, newest first. In the
report of a measurement with a map question, the section of map questions
gets a map: the BRT achtergrondkaart of PDOK in RD (EPSG:28992) with the run
chosen in its table, from the maps.json that airco-report wrote and the BAG
extract under sources/. The site
is built from what is in git and is not committed itself;
.github/workflows/pages.yml builds and deploys it on every push to main.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import markdown
import pandas as pd

from validators import sources

from . import report as report_module
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
td:first-child { white-space: nowrap; }
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


def page(title: str, body: str, home: str = "./", head: str = "") -> str:
    """One page in the site's layout: header with the site name, the body in main, a footer with the source."""
    commit = os.environ.get("GITHUB_SHA", "")[:7]
    built = f"Built from commit <code>{commit}</code> of " if commit else "Built from "
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n<style>{STYLE}</style>\n{head}</head>\n<body>\n"
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


# Leaflet with Proj4Leaflet draws the BRT achtergrondkaart in RD; NL Maps (nlmaps.nl) offers it only in Web Mercator.
MAP_HEAD = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.11.0/proj4.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/proj4leaflet/1.0.2/proj4leaflet.min.js"></script>
<style>
#map { height: clamp(22rem, 65vh, 40rem); border: 1px solid var(--line); border-radius: 8px; margin: 0.75rem 0; scroll-margin-top: 1rem; }
button.show { font: inherit; font-size: 0.85rem; cursor: pointer; color: var(--accent); background: var(--bg); border: 1px solid var(--line); border-radius: 6px; padding: 0.1rem 0.5rem; white-space: nowrap; }
button.show:hover { border-color: var(--accent); }
tr.selected td { background: var(--chip); }
#maps + .tablewrap td:nth-child(-n+6) { white-space: nowrap; }
#maps + .tablewrap td:nth-child(7) { min-width: 13rem; }
#maps + .tablewrap td:nth-child(8) { font-size: 0.85rem; color: var(--muted); overflow-wrap: anywhere; }
#maps + .tablewrap .same { display: none; }
tr.selected button.show { color: var(--fg); font-weight: 600; }
ul.legend { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 0.25rem 1.25rem; font-size: 0.92rem; }
ul.legend span.key { display: inline-block; width: 0.9rem; height: 0.9rem; border-radius: 3px; margin-right: 0.4rem; vertical-align: -0.1rem; border: 2px solid; }
ul.legend span.dot { border-radius: 50%; }
p.result { font-weight: 600; }
</style>
"""

# Pand fill and outline by what the run did with it; the colours read on the grey BRT in light and dark mode.
MAP_SCRIPT = """
const data = JSON.parse(document.getElementById("maps-data").textContent);
const rd = new L.Proj.CRS("EPSG:28992",
  "+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel " +
  "+towgs84=565.417,50.3319,465.552,-0.398957,0.343988,-1.8774,4.0725 +units=m +no_defs",
  {resolutions: [3440.64, 1720.32, 860.16, 430.08, 215.04, 107.52, 53.76, 26.88, 13.44, 6.72, 3.36, 1.68, 0.84, 0.42, 0.21],
   origin: [-285401.92, 903401.92], bounds: L.bounds([-285401.92, 22598.08], [595401.92, 903401.92])});
const map = L.map("map", {crs: rd, center: [52.1, 5.3], zoom: 3, maxZoom: 14});
L.tileLayer("https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:28992/{z}/{x}/{y}.png",
  {minZoom: 0, maxZoom: 14, attribution: 'BRT achtergrondkaart: <a href="https://www.pdok.nl/">PDOK</a>, Kadaster'}).addTo(map);
const STYLES = {
  hit: {color: "#1a7f37", fillColor: "#2da44e", fillOpacity: 0.65, weight: 2},
  missing: {color: "#cf222e", fillColor: "#cf222e", fillOpacity: 0.15, weight: 2, dashArray: "4 3"},
  extra: {color: "#0969da", fillColor: "#218bff", fillOpacity: 0.5, weight: 2},
  rest: {color: "#6e7781", fillOpacity: 0, weight: 1},
};
let layer = null;
function show(i) {
  const run = data.runs[i], sample = data.samples[run.sample];
  const must = new Set(sample.must), shown = new Set(run.shown);
  const kind = id => must.has(id) ? (shown.has(id) ? "hit" : "missing") : (shown.has(id) ? "extra" : "rest");
  const counts = {hit: 0, missing: 0, extra: 0, rest: 0};
  // A pand is a few meters wide, so at city scale a dot in its colour marks it too.
  const dots = [];
  const panden = L.geoJSON(sample.panden, {style: f => { const k = kind(f.properties.identificatie); counts[k]++; return STYLES[k]; },
    onEachFeature: (f, l) => {
      const k = kind(f.properties.identificatie), tip = `pand ${f.properties.identificatie}`;
      l.bindTooltip(tip);
      dots.push(L.circleMarker(l.getBounds().getCenter(), {...STYLES[k], radius: k === "rest" ? 3 : 5, fillOpacity: k === "rest" ? 0 : 0.9}).bindTooltip(tip));
    }});
  const places = run.unmatched.map(([lon, lat]) => L.circleMarker([lat, lon], {radius: 6, color: "#9a6700", fillColor: "#d4a72c", fillOpacity: 0.9, weight: 2})
    .bindTooltip(`on no pand: ${lat.toFixed(5)}, ${lon.toFixed(5)}`));
  if (layer) layer.remove();
  layer = L.layerGroup([panden, ...dots, ...places]).addTo(map);
  map.fitBounds(panden.getBounds(), {padding: [20, 20]});
  for (const k in counts) document.getElementById(`n-${k}`).textContent = counts[k];
  document.getElementById("n-unmatched").textContent = run.unmatched.length;
  document.getElementById("result").textContent = `${run.sample} · ${run.model} · ${run.agent} · variant ${run.variant} · epoch ${run.epoch}: ${run.explanation}`;
}
// Each row of the table of map questions gets a button for its run, matched on model, agent, variant, sample and epoch.
const key = r => [r.model, r.agent, r.variant, r.sample, r.epoch].join("|");
const index = new Map(data.runs.map((r, i) => [key(r), i]));
const table = document.getElementById("maps").nextElementSibling.querySelector("table");
// The button goes first, so it stays in view when the table scrolls sideways on a small screen.
const head = table.querySelector("thead tr");
head.insertBefore(document.createElement("th"), head.firstChild).textContent = "Map";
const choose = (tr, i) => {
  table.querySelectorAll("tr.selected").forEach(r => r.classList.remove("selected"));
  tr.classList.add("selected");
  show(i);
};
let first = null;
for (const tr of table.querySelectorAll("tbody tr")) {
  const [model, agent, variant, sample, epoch] = [...tr.cells].slice(0, 5).map(td => td.textContent.trim());
  const i = index.get(key({model, agent, variant, sample, epoch}));
  const cell = tr.insertCell(0);
  if (i === undefined) continue;
  const button = cell.appendChild(document.createElement("button"));
  button.className = "show";
  button.textContent = "Show";
  button.addEventListener("click", () => { choose(tr, i); document.getElementById("map").scrollIntoView({behavior: "smooth", block: "start"}); });
  const run = data.runs[i];
  if (!first && (run.shown.length || run.unmatched.length)) first = [tr, i];
}
// Variant and sample are the same in every row of most measurements; the line above the map names them, so their columns can go.
for (const column of [3, 4]) {
  const cells = [...table.rows].map(row => row.cells[column]);
  if (new Set(cells.slice(1).map(td => td.textContent.trim())).size === 1) cells.forEach(td => td.classList.add("same"));
}
// Open on the first run that put anything on the map.
if (first) choose(...first); else show(0);
"""


def _rounded(coordinates: object) -> object:
    """Coordinates to 6 decimals, about 10 cm, so the page carries less than the extract."""
    return [_rounded(c) for c in coordinates] if isinstance(coordinates, list) and not isinstance(coordinates[0], float) else [round(c, 6) for c in coordinates]


def _panden(reference: str) -> dict:
    features = json.loads(sources.path(reference).read_text(encoding="utf-8"))["features"]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"identificatie": f["properties"]["identificatie"]},
                "geometry": {"type": f["geometry"]["type"], "coordinates": _rounded(f["geometry"]["coordinates"])},
            }  # fmt: skip
            for f in features
        ],
    }


MAP_HEADING = "<h2>Map questions per run</h2>"


def map_section(shown: dict) -> str:
    """The map of the section of map questions: the panden of the sample's extract on the BRT achtergrondkaart, coloured by
    what the run chosen in the section's table showed."""
    data = {"samples": {s: {"must": e["must"], "panden": _panden(e["reference"])} for s, e in shown["samples"].items()}, "runs": shown["runs"]}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    legend = [
        ("hit", "#1a7f37", "#2da44e", "required and shown"),
        ("missing", "#cf222e", "transparent", "required, not shown"),
        ("extra", "#0969da", "#218bff", "allowed, shown"),
        ("rest", "#6e7781", "transparent", "allowed, not shown"),
    ]
    items = "".join(
        f'<li><span class="key" style="border-color:{line};background:{fill}"></span>{text}: <b id="n-{key}">0</b></li>' for key, line, fill, text in legend
    )
    items += '<li><span class="key dot" style="border-color:#9a6700;background:#d4a72c"></span>place on no pand: <b id="n-unmatched">0</b></li>'
    return (
        "<p>What the agent showed with <code>show_on_map</code>, on the BRT achtergrondkaart in RD. "
        "Each pand of the BAG extract that the rule scores against has a marker in its colour; a place on no pand is a yellow dot, "
        "and one outside the Netherlands, such as with longitude and latitude swapped, is counted but not in view. "
        "Choose a run with <b>Show</b> in the table below the map.</p>\n"
        '<p class="result" id="result"></p>\n'
        '<div id="map" role="img" aria-label="Map of the chosen run"></div>\n'
        f'<ul class="legend">{items}</ul>\n'
        f'<script type="application/json" id="maps-data">{payload}</script>\n'
    )


def with_map(report: str, shown: dict) -> str:
    """The report with the map between the heading of the section of map questions and its table, and the script that ties the two."""
    heading = report.index(MAP_HEADING)
    table = report.index('<div class="tablewrap">', heading)
    # The note in report.md points a reader of the markdown to the site; on the site the map is right here.
    intro = report[heading + len(MAP_HEADING) : table].replace(f"<p>{report_module.MAP_NOTE}</p>", "")
    before = report[:heading] + MAP_HEADING.replace("<h2>", '<h2 id="maps-heading">') + intro
    return f'{before}{map_section(shown)}<div id="maps"></div>{report[table:]}\n<script>{MAP_SCRIPT}</script>'


def build(reports: Path, out: Path) -> list[dict]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rows = []
    for m in measurements(reports):
        target = out / m.name
        bundle(m / "logs" / "logs", target / "viewer", Path("reports") / m.name / "logs" / "logs")
        report = tables_scrollable(markdown.markdown((m / "report.md").read_text(encoding="utf-8"), extensions=["tables"]))
        has_maps = (m / "maps.json").exists()
        if has_maps:
            report = with_map(report, json.loads((m / "maps.json").read_text(encoding="utf-8")))
        to_maps = ' &middot; <a href="#maps-heading">Map questions</a>' if has_maps else ""
        crumbs = f'<nav class="crumbs"><a href="../">All measurements</a> &rsaquo; {html.escape(when(m.name))} &middot; <a href="viewer/">Open the viewer</a>{to_maps}</nav>'
        body = f"{crumbs}\n{report}"
        (target / "report.html").write_text(page(f"{SITE}: report {m.name}", body, home="../", head=MAP_HEAD if has_maps else ""), encoding="utf-8")
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
