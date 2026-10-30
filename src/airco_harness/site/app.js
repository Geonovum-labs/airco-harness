// The pages of the site: overview, measurement and comparison, rendered from data.json.
// All aggregation goes through stats.js, which tests/test_site_stats.py holds to airco-report's numbers.
// Names and values from the logs are data: they go into the page as text nodes, never as HTML.

import {aggregate, commonSamples, costPerCorrect, groupBy} from "./stats.js";
import {createMap, KINDS, panden, PLACE_STYLE} from "./map.js";

const root = document.body.dataset.root;
const app = document.getElementById("app");
const data = await fetch(root + "data.json").then(r => r.json());
const MEASUREMENTS = new Map(data.measurements.map(m => [m.name, m]));
const dark = window.matchMedia("(prefers-color-scheme: dark)");

const METRICS = {
  complete: {label: "complete", share: true, about: "share of the expected content in the answer"},
  correct: {label: "correct", share: true, about: "share of runs that are fully right and invent nothing"},
  source: {label: "source", share: true, about: "share of runs that retrieved an authoritative source"},
  parseable: {label: "parseable", share: true, about: "share of runs whose answer could be read"},
  invented: {label: "invented", share: false, about: "names, values or places per run that do not exist"},
};
const HEAT_METRICS = ["complete", "correct", "source", "parseable"];

// ---------- small helpers ----------

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) if (c !== null && c !== undefined && c !== false) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}
const fmt = (v, digits = 2) => (v === null || v === undefined || Number.isNaN(v) ? "n/a" : Number(v).toFixed(digits));
const money = v => (v === null || v === undefined ? "n/a" : `$${Number(v).toFixed(2)}`);
const compact = v => (v === null || v === undefined ? "n/a" : v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${Math.round(v / 1e3)}K` : String(Math.round(v)));
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const series = () => Array.from({length: 8}, (_, i) => css(`--series-${i + 1}`));

function when(name, short = false) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})/.exec(name);
  if (!m) return name;
  const date = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  const day = date.toLocaleDateString("en-GB", short ? {day: "numeric", month: "short"} : {day: "numeric", month: "long", year: "numeric"});
  return `${day}, ${m[4]}:${m[5]}`;
}

function params() {
  return new URLSearchParams(location.hash.slice(1));
}
function setParams(values) {
  const p = params();
  for (const [k, v] of Object.entries(values)) (v === null || v === undefined || v === "" ? p.delete(k) : p.set(k, v));
  history.replaceState(null, "", `#${p}`);
}

function select(label, options, value, onchange) {
  const s = h("select", {onchange: e => onchange(e.target.value)}, options.map(([v, text]) => h("option", {value: v, text, selected: v === value})));
  return h("label", {}, label, s);
}

function kpi(label, value, note) {
  return h("div", {class: "kpi"}, h("div", {class: "label", text: label}), h("div", {class: "value", text: value}), note ? h("div", {class: "note", text: note}) : null);
}

function table(head, rows, numeric = []) {
  return h("div", {class: "tablewrap"}, h("table", {},
    h("thead", {}, h("tr", {}, head.map((t, i) => h("th", {class: numeric.includes(i) ? "num" : null, text: t})))),
    h("tbody", {}, rows)));
}

const tooltip = h("div", {class: "tooltip", role: "status", hidden: true});
document.body.append(tooltip);
function tip(target, lines) {
  const show = e => {
    tooltip.replaceChildren(...lines().map((line, i) => (i === 0 ? h("strong", {text: line}) : h("div", {text: line}))));
    tooltip.hidden = false;
    const r = target.getBoundingClientRect();
    const x = e && e.clientX ? e.clientX + 14 : r.right + 8, y = e && e.clientY ? e.clientY + 14 : r.top;
    tooltip.style.left = `${Math.min(x, innerWidth - tooltip.offsetWidth - 8)}px`;
    tooltip.style.top = `${Math.min(y, innerHeight - tooltip.offsetHeight - 8)}px`;
  };
  const hide = () => (tooltip.hidden = true);
  target.addEventListener("pointermove", show);
  target.addEventListener("focus", () => show());
  target.addEventListener("pointerleave", hide);
  target.addEventListener("blur", hide);
}

// ---------- heatmap: model x agent ----------

function ramp() {
  // Sequential blue, light to dark; in dark mode its own steps, low values receding to the dark surface.
  const steps = dark.matches ? ["#0d366b", "#184f95", "#2a78d6", "#5598e7", "#9ec5f4"] : ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"];
  const scale = d3.scaleLinear().domain([0, 0.25, 0.5, 0.75, 1]).range(steps).interpolate(d3.interpolateRgb).clamp(true);
  const ink = v => (dark.matches ? (v >= 0.6 ? "#0b0b0b" : "#f0efec") : v >= 0.45 ? "#ffffff" : "#0b0b0b");
  return {scale, ink, steps};
}

/** A grid of models by agents; value(model, agent) gives {mean, se, n} or null; onSelect(model, agent) on click. */
function heatmap({models, agents, value, metric, selected, onSelect, detail}) {
  const {scale, ink} = ramp();
  const grid = h("div", {class: "heatmap", role: "grid", style: `grid-template-columns: max-content repeat(${agents.length}, minmax(6.5rem, 1fr))`});
  grid.append(h("div"), ...agents.map(a => h("div", {class: "colhead", text: a})));
  for (const model of models) {
    grid.append(h("div", {class: "rowhead", text: model}));
    for (const agent of agents) {
      const v = value(model, agent);
      if (!v || v.mean === null) {
        grid.append(h("div", {class: "cell none", text: "not run"}));
        continue;
      }
      const pressed = selected && selected[0] === model && selected[1] === agent;
      const cell = h("button", {class: "cell", "aria-pressed": onSelect ? String(!!pressed) : null, style: `background:${scale(v.mean)};color:${ink(v.mean)}`,
        "aria-label": `${model}, ${agent}: ${metric} ${fmt(v.mean)}`, onclick: onSelect ? () => onSelect(model, agent) : null},
        h("span", {class: "v", text: fmt(v.mean)}), h("span", {class: "s", text: v.se === null ? (v.runs ? `${v.runs} run${v.runs === 1 ? "" : "s"}` : `${v.n} sample`) : `± ${fmt(v.se)}`}));
      if (!onSelect) cell.style.cursor = "default";
      tip(cell, () => [`${metric} ${fmt(v.mean)}${v.se === null ? "" : ` ± ${fmt(v.se)}`}`, `${model} · ${agent}`, `${v.n} sample${v.n === 1 ? "" : "s"}${v.runs ? ` · ${v.runs} runs` : ""}`, ...(detail ? detail(model, agent) : [])]);
      grid.append(cell);
    }
  }
  return grid;
}

function scaleLegend(metric) {
  const {steps} = ramp();
  return h("div", {class: "scale"}, h("span", {text: `${metric}: 0`}), h("span", {class: "bar", style: `background: linear-gradient(to right, ${steps.join(",")})`}), h("span", {text: "1"}));
}

// ---------- shared shapes ----------

/** The summary of a metric over a group of runs, with the number of runs for the heatmap's second line. */
function cellValue(group, metric) {
  return group ? {...aggregate(group, metric), runs: group.length} : null;
}

function runsOf(filter) {
  return data.runs.filter(filter);
}
// Within a provider, models from small to capable, so a row or a colour reads as a step up. A name without a known tier
// goes after the known ones, alphabetically.
const TIERS = [["nano", 0], ["mini", 1], ["small", 1], ["haiku", 1], ["flash", 1], ["medium", 2], ["sonnet", 2], ["large", 3], ["opus", 3], ["pro", 3], ["fable", 4]];
function tier(model) {
  const name = model.split("/").pop().toLowerCase();
  const found = TIERS.find(([word]) => new RegExp(`(^|[-_.])${word}([-_.]|$)`).test(name));
  return found ? found[1] : 9;
}
/** Compare two model names: by provider, then by tier, then by name. */
function byModel(a, b) {
  const provider = m => (m.includes("/") ? m.split("/")[0] : "");
  return provider(a).localeCompare(provider(b)) || tier(a) - tier(b) || a.localeCompare(b);
}
function sortedModels(runs) {
  return [...new Set(runs.map(r => r.model))].sort(byModel);
}
function sortedAgents(runs) {
  const order = ["model", "inspect", "claude-code"];
  return [...new Set(runs.map(r => r.agent))].sort((a, b) => (order.indexOf(a) + 99 * (order.indexOf(a) < 0)) - (order.indexOf(b) + 99 * (order.indexOf(b) < 0)) || a.localeCompare(b));
}
/** The question the agent got, as the reader should see it first: large for one sample, a list to choose from for several. */
function questionBlock(m, sample, onChoose) {
  const asked = Object.entries(m.questions || {}).filter(([s]) => !sample || s === sample);
  if (!asked.length) return null;
  if (asked.length === 1) {
    const [s, text] = asked[0];
    return h("figure", {class: "question"}, h("figcaption", {}, "Question to the agent · ", h("span", {class: "chip", text: s})), h("blockquote", {text}));
  }
  return h("section", {class: "questions"}, h("h2", {text: "Questions to the agent"}),
    h("ol", {}, asked.map(([s, text]) => h("li", {}, onChoose ? h("button", {class: "chip linklike", text: s, onclick: () => onChoose(s)}) : h("span", {class: "chip", text: s}), " ", h("span", {text})))));
}

function testsetLabel(m) {
  return m.testset_versions.length ? m.testset_versions.join(", ") : m.testsets.join(", ");
}

// ---------- overview ----------

function overview() {
  if (!data.measurements.length) return [h("h1", {text: "Measurements"}), h("p", {class: "empty", text: "No measurements yet."})];
  const p = params();
  const testsets = [...new Set(data.measurements.flatMap(m => m.testsets))].sort();
  const testset = testsets.includes(p.get("testset")) ? p.get("testset") : "";
  const ms = data.measurements.filter(m => !testset || m.testsets.includes(testset));
  const names = new Set(ms.map(m => m.name));
  const runs = runsOf(r => names.has(r.m));

  const body = [
    h("h1", {text: "Measurements"}),
    h("p", {class: "lead"}, "Each measurement runs a test set against agents and models. The cells show ", h("b", {text: "complete"}),
      ": the share of the expected content in the answer, averaged per sample over its epochs and then over the samples. Open a measurement for its runs, or ",
      h("a", {href: "compare.html", text: "compare"}), " measurements, variants, models and agents."),
    h("div", {class: "filters"}, select("Test set", [["", "All test sets"], ...testsets.map(t => [t, t])], testset, v => { setParams({testset: v}); render(); })),
    h("div", {class: "kpis"}, kpi("Measurements", String(ms.length)), kpi("Runs", String(runs.length)),
      kpi("Samples", String(new Set(runs.map(r => r.sample)).size)), kpi("Cost", money(runs.reduce((a, r) => a + (r.cost || 0), 0)), "as Inspect logged it")),
  ];

  // The current state of a test set: for each of its samples, the runs of the newest measurement that has it.
  const cards = (testset ? [testset] : testsets).map(t => {
    const own = ms.filter(m => m.testsets.includes(t));
    const newest = new Map();
    for (const m of own) for (const sample of m.samples) if (!newest.has(sample)) newest.set(sample, m.name);
    const current = runsOf(r => newest.get(r.sample) === r.m);
    const used = [...new Set(newest.values())].map(n => MEASUREMENTS.get(n));
    const groups = groupBy(current, r => `${r.model}|${r.agent}`);
    const link = used.length === 1 ? `${used[0].name}/report.html` : null;
    return h("section", {class: "card"},
      h("header", {}, h("h2", {text: t}), h("p", {text: `${newest.size} sample${newest.size === 1 ? "" : "s"} · ${current.length} runs`})),
      h("p", {class: "muted", style: "margin:0 0 0.6rem;font-size:0.88rem"}, "Newest run of each sample: ", ...used.flatMap((m, i) => [i ? ", " : "",
        h("a", {href: `${m.name}/report.html`, text: when(m.name, true)}), ` (${m.samples.filter(x => newest.get(x) === m.name).join(", ")})`])),
      heatmap({models: sortedModels(current), agents: sortedAgents(current), metric: "complete",
        value: (model, agent) => cellValue(groups.get(`${model}|${agent}`), "complete"),
        onSelect: link ? (model, agent) => (location.href = `${link}#model=${encodeURIComponent(model)}&agent=${encodeURIComponent(agent)}`) : null,
        detail: (model, agent) => [`correct ${fmt(aggregate(groups.get(`${model}|${agent}`), "correct").mean)}`, link ? "Click for the runs" : "Open a measurement for the runs"]}),
      scaleLegend("complete"));
  });
  body.push(h("h2", {text: "Current results per test set", style: "margin-top:1.5rem"}), h("div", {class: "grid-2"}, cards));

  body.push(h("h2", {text: "All measurements", style: "margin-top:1.75rem"}), table(
    ["Start", "Test set and samples", "Agents", "Models", "Runs", "Cost", ""],
    ms.map(m => h("tr", {},
      h("td", {class: "nowrap"}, h("a", {href: `${m.name}/report.html`, text: when(m.name)}), h("div", {class: "muted", style: "font-size:0.78rem", text: m.name})),
      h("td", {}, h("div", {class: "nowrap", text: testsetLabel(m)}), h("div", {class: "muted", style: "font-size:0.85rem", text: m.samples.join(", ")})),
      h("td", {class: "nowrap"}, m.agents.map(a => h("div", {text: a}))),
      h("td", {}, m.models.map(x => h("span", {class: "chip", text: x}))),
      h("td", {class: "num", text: String(m.runs)}),
      h("td", {class: "num", text: money(m.cost)}),
      h("td", {class: "nowrap"}, h("a", {class: "btn", href: `${m.name}/report.html`, text: "Dashboard"}), h("a", {class: "btn", href: `${m.name}/viewer/`, text: "Viewer"})))),
    [4, 5]));
  return body;
}

// ---------- measurement ----------

function measurementPage() {
  const name = document.body.dataset.measurement;
  const m = MEASUREMENTS.get(name);
  const p = params();
  const sample = m.samples.includes(p.get("sample")) ? p.get("sample") : "";
  const metric = HEAT_METRICS.includes(p.get("metric")) ? p.get("metric") : "complete";
  const all = runsOf(r => r.m === name);
  const runs = all.filter(r => !sample || r.sample === sample);
  const models = sortedModels(all), agents = sortedAgents(all);
  const groups = groupBy(runs, r => `${r.model}|${r.agent}`);
  const pair = [p.get("model"), p.get("agent")];
  const chosen = groups.has(`${pair[0]}|${pair[1]}`) ? pair : (() => {
    // Open on the pair that did best on the metric, so the page starts on something worth reading.
    let best = null;
    for (const [key, g] of groups) { const v = aggregate(g, metric).mean; if (v !== null && (!best || v > best[1])) best = [key.split("|"), v]; }
    return best ? best[0] : null;
  })();
  const limits = m.limits;
  const facts = [
    ["Test set", testsetLabel(m)], ["Commit", m.commits.join(", ") || "n/a"],
    ["Cost limit", limits.cost.length ? limits.cost.map(v => `$${v}`).join(", ") : "none"],
    ["Token limit", limits.token.map(compact).join(", ") || "none"], ["Message limit", limits.message.join(", ") || "none"],
  ];

  const body = [
    h("nav", {class: "crumbs"}, h("a", {href: "../", text: "All measurements"}), " › ", when(name), " · ", h("a", {href: "viewer/", text: "Viewer"}), " · ",
      h("a", {href: `https://github.com/Geonovum-labs/airco-harness/blob/main/reports/${name}/report.md`, text: "report.md"}), " · ",
      h("a", {href: `../compare.html#by=model&measurement=${encodeURIComponent(name)}`, text: "Compare"})),
    h("h1", {text: `Measurement of ${when(name)}`}),
    h("p", {class: "facts"}, facts.map(([k, v]) => h("span", {}, `${k} `, h("b", {text: v})))),
    questionBlock(m, sample, s => { setParams({sample: s}); render(); }),
    h("div", {class: "kpis"}, kpi("Runs", String(m.runs), `${m.models.length} models · ${m.agents.length} agents`), kpi("Samples", String(m.samples.length), m.samples.slice(0, 3).join(", ")),
      kpi("Cost", money(m.cost), "all runs"), kpi("Errors / at a limit", `${m.failed} / ${m.at_limit}`, "a run at a limit counts as answered")),
    h("div", {class: "filters"},
      select("Sample", [["", `All samples (${m.samples.length})`], ...m.samples.map(s => [s, s])], sample, v => { setParams({sample: v}); render(); }),
      select("Metric", HEAT_METRICS.map(k => [k, k]), metric, v => { setParams({metric: v}); render(); })),
  ];

  body.push(h("section", {class: "card"},
    h("header", {}, h("h2", {text: `${metric} per model and agent`}), h("p", {text: `${METRICS[metric].about}; mean over samples, each sample first averaged over its epochs. Choose a cell for its runs.`})),
    heatmap({models, agents, metric, selected: chosen, value: (model, agent) => cellValue(groups.get(`${model}|${agent}`), metric),
      onSelect: (model, agent) => { setParams({model, agent}); render(); document.getElementById("detail").scrollIntoView({behavior: "smooth", block: "start"}); },
      detail: (model, agent) => { const g = groups.get(`${model}|${agent}`); return [`${g.length} runs · ${money(g.reduce((a, r) => a + (r.cost || 0), 0))}`]; }}),
    scaleLegend(metric)));

  body.push(chosen ? pairDetail(name, chosen, groups.get(`${chosen[0]}|${chosen[1]}`)) : h("p", {class: "empty", id: "detail", text: "No runs for this selection."}));

  const rows = [...groups].map(([key, g]) => {
    const [model, agent] = key.split("|");
    return h("tr", {}, h("td", {class: "nowrap", text: model}), h("td", {text: agent}),
      ...Object.keys(METRICS).map(k => { const v = aggregate(g, k); return h("td", {class: "num", text: v.se === null ? fmt(v.mean) : `${fmt(v.mean)} ± ${fmt(v.se)}`}); }));
  });
  body.push(h("details", {}, h("summary", {text: "Table: quality metrics per model and agent"}),
    table(["Model", "Agent", ...Object.keys(METRICS)], rows, [2, 3, 4, 5, 6])));
  const trajectory = [...groups].map(([key, g]) => {
    const [model, agent] = key.split("|");
    return h("tr", {}, h("td", {class: "nowrap", text: model}), h("td", {text: agent}),
      h("td", {class: "num", text: fmt(aggregate(g, "tool_calls").mean, 1)}), h("td", {class: "num", text: compact(aggregate(g, "tokens").mean)}),
      h("td", {class: "num", text: fmt(aggregate(g, "total_time_s").mean, 0)}), h("td", {class: "num", text: money(g.reduce((a, r) => a + (r.cost || 0), 0))}),
      h("td", {class: "num", text: money(costPerCorrect(g))}));
  });
  body.push(h("details", {}, h("summary", {text: "Trajectory and cost per model and agent"}),
    table(["Model", "Agent", "Tool calls", "Tokens", "Time (s)", "Cost", "Cost per correct"], trajectory, [2, 3, 4, 5, 6])));
  return body;
}

// ---------- retrieved URLs: per host a button, its exact URLs in a popover ----------

const urlPopover = h("div", {id: "urls", popover: "auto", role: "dialog", "aria-label": "Retrieved URLs"});
document.body.append(urlPopover);

const safeHref = url => { try { return ["http:", "https:"].includes(new URL(url).protocol) ? url : null; } catch { return null; } };
const hostOf = url => { try { return new URL(url).host; } catch { return url; } };

const CLASSES = {
  authoritative: {label: "authoritative", note: "counts for source"},
  non_authoritative: {label: "non-authoritative", note: "makes source 0"},
  other: {label: "other", note: "does not count for source"},
};
const badge = cls => h("span", {class: `badge ${cls}`, text: (CLASSES[cls] || CLASSES.other).label});

/** Readable text for an encoded URL part (a SPARQL query, a filter); the link keeps the exact URL. */
const readable = text => { try { return decodeURIComponent(text.replace(/\+/g, " ")); } catch { return text; } };

/** A URL with its origin muted, so the path and query that differ between URLs of one host stand out. */
function urlText(url) {
  try {
    const u = new URL(url);
    return [h("span", {class: "origin", text: u.origin}), h("span", {class: "path", text: readable(`${u.pathname}${u.search}${u.hash}`)})];
  } catch {
    return [h("span", {class: "path", text: url})];
  }
}

/** Open the URL popover next to its button: below it, else above it, else in the larger of the two spaces with
its height cut to fit, so the header with the host and the close button always stays in view. */
function placePopover(button) {
  urlPopover.style.maxHeight = "";
  urlPopover.showPopover();
  const r = button.getBoundingClientRect(), margin = 8, gap = 6;
  const below = innerHeight - r.bottom - gap - margin, above = r.top - gap - margin;
  const natural = urlPopover.offsetHeight;
  let top;
  if (natural <= below) top = r.bottom + gap;
  else if (natural <= above) top = r.top - gap - natural;
  else if (below >= above) { urlPopover.style.maxHeight = `${below}px`; top = r.bottom + gap; }
  else { urlPopover.style.maxHeight = `${above}px`; top = margin; }
  urlPopover.style.top = `${top}px`;
  urlPopover.style.left = `${Math.max(margin, Math.min(r.left, innerWidth - urlPopover.offsetWidth - margin))}px`;
}

/** A short name for why a retrieval failed: its HTTP status, or the kind of error. */
const WHY = {
  "no connection": "No HTTP status: the connection failed before a server answered.",
  timeout: "No HTTP status: no answer came within the time limit.",
  "command failed": "No HTTP status: the shell command failed and its output names no status for this URL.",
  failed: "No HTTP status: the retrieval failed without an answer.",
};

/** The badge of a failed retrieval: red with the HTTP status the server sent, or grey and dashed when no server answered. */
function failureBadge(x) {
  const kind = failure(x);
  return h("span", {class: `badge failed${x.status ? "" : " nostatus"}`, text: kind, title: x.status ? `HTTP ${x.status}: the server answered with this status.` : WHY[kind]});
}

function failure(x) {
  if (x.status) return String(x.status);
  if (/connect/i.test(x.error)) return "no connection";
  if (/timeout/i.test(x.error)) return "timeout";
  if (/^exit code/i.test(x.error)) return "command failed";
  return "failed";
}

function urlItem(x) {
  return safeHref(x.url)
    ? h("a", {href: x.url, target: "_blank", rel: "noopener noreferrer", title: "Open in a new tab"}, ...urlText(x.url), h("span", {class: "ext", "aria-hidden": "true", text: "↗"}))
    : h("span", {}, ...urlText(x.url));
}

/** The hosts a run retrieved from or failed to, each a button that lists the exact URLs; links only for http(s), as the URLs come from the logs. */
function retrievedFrom(run) {
  const ok = run.retrieved || [], failed = run.errors || [];
  if (!ok.length && !failed.length) return h("span", {class: "muted", text: "nothing retrieved"});
  const hosts = new Map();
  for (const x of ok) { const k = hostOf(x.url); if (!hosts.has(k)) hosts.set(k, {ok: [], failed: []}); hosts.get(k).ok.push(x); }
  for (const x of failed) { const k = hostOf(x.url); if (!hosts.has(k)) hosts.set(k, {ok: [], failed: []}); hosts.get(k).failed.push(x); }
  return [...hosts].map(([host, {ok: good, failed: bad}]) => {
    const cls = good.length ? good[0].class : null;
    const kinds = [...new Set(bad.map(failure))];
    const answered = bad.some(x => x.status);
    const failPill = bad.length ? h("span", {class: `badge failed${answered ? "" : " nostatus"}`, title: answered ? "Failed; a server answered with an error status" : WHY[kinds[0]] || WHY.failed,
      text: kinds.length === 1 ? (bad.length > 1 ? `${kinds[0]} ×${bad.length}` : kinds[0]) : `${bad.length} failed`}) : null;
    // The usual class, other, goes without a badge in the table; the popover always names it.
    const button = h("button", {class: "hostbtn", type: "button", "aria-haspopup": "dialog",
      title: [good.length ? `${good.length} URL${good.length === 1 ? "" : "s"} retrieved` : null, bad.length ? `${bad.length} failed` : null].filter(Boolean).join(", ") + ` from ${host}`},
      h("span", {class: "host", text: host}), cls && cls !== "other" ? badge(cls) : null, good.length > 1 ? h("span", {class: "count", text: `×${good.length}`}) : null, failPill);
    button.addEventListener("click", () => {
      const close = h("button", {class: "close", type: "button", "aria-label": "Close", text: "×", onclick: () => urlPopover.hidePopover()});
      const parts = [h("div", {class: "pophead"}, h("div", {}, h("b", {class: "host", text: host}), cls ? badge(cls) : null), close)];
      if (good.length) parts.push(h("p", {class: "popnote", text: `${good.length} URL${good.length === 1 ? "" : "s"} retrieved with success · ${(CLASSES[cls] || CLASSES.other).note}`}),
        h("ol", {class: "urls"}, good.map(x => h("li", {}, urlItem(x)))));
      if (bad.length) parts.push(h("p", {class: "popnote failed", text: `${bad.length} URL${bad.length === 1 ? "" : "s"} failed · does not count for source`}),
        h("ol", {class: "urls"}, bad.map(x => h("li", {class: "fail"},
          failureBadge(x),
          h("div", {class: "failurl"}, urlItem(x), x.error && ![`HTTP ${x.status}`, String(x.status)].includes(x.error) ? h("div", {class: "errmsg", text: x.error}) : null,
            x.times > 1 ? h("div", {class: "errmsg", text: `${x.times} times`}) : null,
            ["Bash", "code_execution"].includes(x.tool) ? h("div", {class: "errmsg", text: x.status ? "status from the output of a shell command" : "a shell command that failed; its output names no status for this URL"}) : null,
            x.output ? h("details", {class: "output"}, h("summary", {text: "Output"}), h("pre", {text: x.output})) : null)))));
      urlPopover.replaceChildren(...parts);
      placePopover(button);
      close.focus();
    });
    return h("div", {class: "hostline"}, button);
  });
}

function pairDetail(name, [model, agent], runs) {
  const ordered = [...runs].sort((a, b) => a.sample.localeCompare(b.sample) || a.epoch - b.epoch);
  const viewer = r => `viewer/#/logs/${encodeURIComponent(r.log)}/samples/sample/${encodeURIComponent(r.sample)}/${r.epoch}/`;
  const onMap = ordered.filter(r => data.maps[r.sample]);
  const section = h("section", {class: "card", id: "detail"},
    h("header", {}, h("h2", {text: `${model} · ${agent}`}),
      h("p", {text: ["complete", "correct", "source"].map(k => `${k} ${fmt(aggregate(runs, k).mean)}`).join(" · ")})));
  let showOnMap = null;
  if (onMap.length) {
    const result = h("p", {class: "result"});
    const counts = h("ul", {class: "legend"});
    const element = h("div", {id: "map", role: "img", "aria-label": "Map of the chosen run"});
    // How the rule reads the map, per sample: which panden count, and why, from the note in its expected.json.
    const scoring = [...new Set(onMap.map(r => r.sample))].map(s => {
      const entry = data.maps[s];
      return h("div", {class: "scoring"},
        h("p", {}, h("b", {text: "Required: "}), `the ${entry.must.length} panden the map has to show; each one missing lowers complete. `,
          h("b", {text: "Optional: "}), `the other ${entry.optional} panden of the BAG extract; the map may show them or leave them out, without effect on the score. `,
          h("b", {text: "Invented: "}), "a place on none of these panden."),
        entry.note ? h("details", {}, h("summary", {text: `Why these panden${onMap.some(r => r.sample !== s) ? ` (${s})` : ""}`}), h("p", {text: entry.note})) : null);
    });
    section.append(h("p", {class: "muted", style: "margin:0.25rem 0"}, "What the agent showed with ", h("code", {text: "show_on_map"}),
      ", on the BRT achtergrondkaart in RD; each pand has a marker in its colour."),
      ...scoring, result, element, counts);
    const draw = createMap(element);
    showOnMap = async run => {
      const sample = data.maps[run.sample];
      const c = draw(run, sample.must, await panden(root, sample.panden));
      result.textContent = `${run.sample} · epoch ${run.epoch}: ${run.explanation}`;
      counts.replaceChildren(...Object.entries(KINDS).map(([k, kind]) => h("li", {}, h("span", {class: "key sq", style: `border-color:${kind.style.color};background:${kind.style.fillOpacity ? kind.style.fillColor : "transparent"}`}), `${kind.label}: `, h("b", {text: String(c[k])}))),
        h("li", {}, h("span", {class: "key", style: `background:${PLACE_STYLE.fillColor};border:2px solid ${PLACE_STYLE.color}`}), "invented, on no pand: ", h("b", {text: String(c.unmatched)})));
      section.querySelectorAll("tr.selected").forEach(tr => tr.classList.remove("selected"));
      document.getElementById(`run-${run.sample}-${run.epoch}`)?.classList.add("selected");
    };
  }
  const rows = ordered.map(r => h("tr", {id: `run-${r.sample}-${r.epoch}`},
    h("td", {class: "nowrap"}, data.maps[r.sample] ? h("button", {class: "btn", text: "Show", onclick: () => { showOnMap(r); document.getElementById("map").scrollIntoView({behavior: "smooth", block: "center"}); }}) : null,
      h("a", {class: "btn", href: viewer(r), text: "Log"})),
    h("td", {class: "nowrap", text: r.sample}), h("td", {class: "num", text: String(r.epoch)}),
    ...["correct", "complete", "invented", "source"].map(k => h("td", {class: "num", text: r.failed ? "error" : fmt(r[k], k === "invented" ? 0 : 2)})),
    h("td", {style: "min-width:14rem", text: r.limit ? `${r.explanation} (stopped at the ${r.limit} limit)` : r.explanation || ""}),
    h("td", {class: "small"}, retrievedFrom(r)),
    h("td", {class: "num", text: money(r.cost)})));
  section.append(table(["", "Sample", "Epoch", "correct", "complete", "invented", "source", "Outcome", "Retrieved from", "Cost"], rows, [2, 3, 4, 5, 6, 9]));
  if (showOnMap) {
    // Open on the first run that put anything on the map.
    const first = onMap.find(r => r.map && (r.map.shown.length || r.map.unmatched.length)) || onMap[0];
    requestAnimationFrame(() => showOnMap(first));
  }
  return section;
}

// ---------- compare ----------

const DIMENSIONS = {measurement: "Measurement", variant: "Variant", model: "Model", agent: "Agent"};
const value = (r, d) => (d === "measurement" ? r.m : r[d]);

function comparePage() {
  const p = params();
  const by = DIMENSIONS[p.get("by")] ? p.get("by") : "agent";
  const metric = METRICS[p.get("metric")] ? p.get("metric") : "complete";
  const testsets = [...new Set(data.measurements.flatMap(m => m.testsets))].sort();
  const inTestset = t => new Set(data.measurements.filter(m => !t || m.testsets.includes(t)).map(m => m.name));
  const testset = testsets.includes(p.get("testset")) ? p.get("testset") : "";
  let runs = runsOf(r => inTestset(testset).has(r.m));
  const samples = [...new Set(runs.map(r => r.sample))].sort();
  const sample = samples.includes(p.get("sample")) ? p.get("sample") : "";
  if (sample) runs = runs.filter(r => r.sample === sample);
  // What is not compared is held fixed: by default the newest measurement, and every variant pooled only when asked.
  const measurementsHere = data.measurements.filter(m => runs.some(r => r.m === m.name)).map(m => m.name);
  const fixedMeasurement = by === "measurement" ? "" : measurementsHere.includes(p.get("measurement")) ? p.get("measurement") : p.get("measurement") === "all" ? "all" : measurementsHere[0] || "";
  if (fixedMeasurement && fixedMeasurement !== "all") runs = runs.filter(r => r.m === fixedMeasurement);
  const variants = [...new Set(runs.map(r => r.variant))].sort();
  const fixedVariant = by === "variant" ? "" : variants.includes(p.get("variant")) ? p.get("variant") : "";
  if (fixedVariant) runs = runs.filter(r => r.variant === fixedVariant);

  // Groups in a fixed order, so a value keeps its colour when others are switched off.
  let values = [...new Set(runs.map(r => value(r, by)))];
  values = by === "measurement" ? values.sort() : by === "agent" ? sortedAgents(runs).filter(a => values.includes(a)) : by === "model" ? values.sort(byModel) : values.sort();
  const capped = values.slice(-8);
  const chosen = p.get("groups") ? p.get("groups").split(",").filter(v => capped.includes(v)) : by === "measurement" ? capped.slice(-3) : capped;
  const label = v => (by === "measurement" ? when(v, true) : v);
  const colours = series();
  const colour = v => colours[capped.indexOf(v)];

  const update = values => { setParams(values); render(); };
  const body = [
    h("h1", {text: "Compare"}),
    h("p", {class: "lead", text: "Compare measurements over time, variants of the publication form, models or agents, with the rest held fixed. " +
      "Each group is scored on the samples every group in the row has, so a difference is never a difference in questions. Dots are means over samples; the bars are one standard error."}),
    h("div", {class: "filters"},
      h("label", {}, "Compare by", h("div", {class: "segmented"}, Object.entries(DIMENSIONS).map(([k, text]) =>
        h("button", {text, "aria-pressed": String(k === by), onclick: () => update({by: k, groups: null})})))),
      select("Metric", Object.keys(METRICS).map(k => [k, k]), metric, v => update({metric: v})),
      select("Test set", [["", "All test sets"], ...testsets.map(t => [t, t])], testset, v => update({testset: v, sample: null, groups: null})),
      select("Sample", [["", `All samples (${samples.length})`], ...samples.map(s => [s, s])], sample, v => update({sample: v, groups: null})),
      by !== "measurement" ? select("Measurement", [["all", "All, pooled"], ...measurementsHere.map(n => [n, when(n)])], fixedMeasurement, v => update({measurement: v, groups: null})) : null,
      by !== "variant" ? select("Variant", [["", variants.length > 1 ? "All, pooled" : `${variants[0] ?? "none"}`], ...(variants.length > 1 ? variants.map(v => [v, v]) : [])], fixedVariant, v => update({variant: v, groups: null})) : null),
  ];
  if (sample) {
    const asked = data.measurements.find(m => m.questions && m.questions[sample]);
    if (asked) body.push(questionBlock(asked, sample));
  }
  if (!capped.length) return [...body, h("p", {class: "empty", text: "No runs for this selection."})];
  body.push(h("div", {class: "groups", role: "group", "aria-label": "Groups"}, h("span", {class: "muted", text: `${DIMENSIONS[by]}s:`}), capped.map(v =>
    h("label", {}, h("input", {type: "checkbox", checked: chosen.includes(v), onchange: e => {
      const next = e.target.checked ? [...chosen, v] : chosen.filter(x => x !== v);
      update({groups: capped.filter(x => next.includes(x)).join(",") || "none"});
    }}), h("span", {class: "key", style: `display:inline-block;width:0.7rem;height:0.7rem;border-radius:50%;background:${colour(v)}`}), label(v)))));
  if (values.length > capped.length) body.push(h("p", {class: "muted", text: `Only the newest ${capped.length} of ${values.length} are offered; narrow the selection to compare others.`}));

  body.push(...comparisonWarnings(by, chosen, runs, fixedMeasurement));
  if (!chosen.length) return [...body, h("p", {class: "empty", text: "Choose at least one group."})];

  const rowDims = ["model", "agent"].filter(d => d !== by);
  const rowKey = r => rowDims.map(d => r[d]).join(" · ");
  const points = [], tableRows = [];
  const rowOrder = [...new Set(runs.filter(r => chosen.includes(value(r, by))).sort((a, b) => byModel(a.model, b.model) || sortedAgents([a, b]).indexOf(a.agent) - sortedAgents([a, b]).indexOf(b.agent)).map(rowKey))];
  let disjoint = 0;
  for (const row of rowOrder) {
    const present = chosen.map(g => [g, runs.filter(r => rowKey(r) === row && value(r, by) === g)]).filter(([, rs]) => rs.some(r => !r.failed));
    const common = commonSamples(present.map(([, rs]) => rs));
    if (present.length > 1 && !common.size) disjoint++;
    const stats = new Map(present.map(([g, rs]) => [g, aggregate(rs, metric, common)]));
    for (const [g, s] of stats) if (s.mean !== null) points.push({row, group: g, groupLabel: label(g), ...s, lo: s.mean - (s.se ?? 0), hi: s.mean + (s.se ?? 0)});
    const first = stats.get(chosen[0]), last = stats.get(chosen[chosen.length - 1]);
    const delta = chosen.length > 1 && first && last && first.mean !== null && last.mean !== null ? last.mean - first.mean : null;
    tableRows.push(h("tr", {}, h("td", {class: "nowrap", text: row}), h("td", {class: "num", text: String(common.size)}),
      ...chosen.map(g => { const s = stats.get(g); return h("td", {class: "num", text: !s ? "not run" : s.mean === null ? "no sample in common" : s.se === null ? fmt(s.mean) : `${fmt(s.mean)} ± ${fmt(s.se)}`}); }),
      chosen.length > 1 ? h("td", {class: "num", style: delta ? `color:var(${(delta > 0) === (metric !== "invented") ? "--good" : "--bad"})` : null, text: delta === null ? "n/a" : `${delta > 0 ? "+" : ""}${fmt(delta)}`}) : null));
  }

  if (disjoint === rowOrder.length) {
    const sampleList = chosen.map(g => `${label(g)}: ${[...new Set(runs.filter(r => value(r, by) === g).map(r => r.sample))].join(", ")}`).join("; ");
    body.push(h("div", {class: "warning", role: "note"}, h("b", {text: "Nothing to compare. "}),
      `The chosen ${DIMENSIONS[by].toLowerCase()}s have no sample in common (${sampleList}). A comparison over time needs the same sample in more than one measurement: run it again, or compare by model or agent.`));
    return body;
  }
  const chart = h("div", {class: "chart"});
  body.push(h("section", {class: "card"},
    h("header", {}, h("h2", {text: `${metric} by ${DIMENSIONS[by].toLowerCase()}`}), h("p", {text: METRICS[metric].about})),
    h("ul", {class: "legend"}, chosen.map(g => h("li", {}, h("span", {class: "key", style: `background:${colour(g)}`}), label(g)))), chart));
  body.push(h("h3", {text: "Table"}), table([rowDims.map(d => DIMENSIONS[d]).join(" · "), "Samples", ...chosen.map(label), ...(chosen.length > 1 ? [`Δ ${label(chosen[chosen.length - 1])} vs ${label(chosen[0])}`] : [])], tableRows,
    [1, ...chosen.map((_, i) => i + 2), chosen.length + 2]));

  requestAnimationFrame(() => {
    const longest = Math.max(...rowOrder.map(r => r.length), 10);
    // Past three groups colour alone no longer tells them apart: each dot gets its group's name on the y axis, and the rows move to the right.
    const many = chosen.length > 3;
    const longestGroup = Math.max(...chosen.map(g => label(g).length), 4);
    const xmax = METRICS[metric].share ? 1 : Math.max(1, ...points.map(d => d.hi));
    chart.replaceChildren(Plot.plot({
      width: Math.max(chart.clientWidth, 520),
      height: rowOrder.length * (chosen.length * 18 + 22) + 40,
      marginLeft: Math.min(320, (many ? longestGroup : longest) * 7 + 16), marginRight: many ? Math.min(320, longest * 7 + 16) : 16, marginTop: 28,
      style: {background: "transparent", color: css("--fg"), fontSize: "12px"},
      x: {domain: [0, xmax], grid: true, label: metric, labelAnchor: "left", tickFormat: METRICS[metric].share ? ".1f" : "d", axis: "top"},
      y: {domain: chosen, axis: many ? "left" : null, tickFormat: label, tickSize: 0, label: null, padding: 0.25},
      fy: {domain: rowOrder, label: null, axis: many ? "right" : "left", padding: 0.15},
      color: {domain: capped, range: colours},
      marks: [
        Plot.ruleY(points, {fy: "row", y: "group", x1: "lo", x2: "hi", stroke: "group", strokeWidth: 2}),
        Plot.dot(points, {fy: "row", y: "group", x: "mean", fill: "group", r: 6, stroke: css("--card"), strokeWidth: 2,
          channels: {Group: "groupLabel", Samples: "n"}, tip: {format: {fy: true, y: false, fill: false, x: d => fmt(d), Group: true, Samples: true}}}),
      ],
    }));
  });
  return body;
}

function comparisonWarnings(by, chosen, runs, fixedMeasurement) {
  const notes = [];
  const factsOf = names => [...names].map(n => MEASUREMENTS.get(n));
  if (by === "measurement" || by === "variant") {
    const per = chosen.map(g => factsOf(new Set(runs.filter(r => value(r, by) === g).map(r => r.m))));
    for (const [key, text] of [["testset_versions", "test set versions"], ["commits", "commits of the harness"]]) {
      const sets = per.map(ms => ms.flatMap(m => m[key]).sort().join(", "));
      if (new Set(sets).size > 1) notes.push(`The groups differ in ${text}: ${chosen.map((g, i) => `${by === "measurement" ? when(g, true) : g}: ${sets[i] || "n/a"}`).join("; ")}.`);
    }
    for (const [key, text] of [["cost", "cost limit"], ["token", "token limit"], ["message", "message limit"]]) {
      const sets = per.map(ms => ms.flatMap(m => m.limits[key]).sort().join(", "));
      if (new Set(sets).size > 1) notes.push(`The groups differ in ${text}: ${chosen.map((g, i) => `${by === "measurement" ? when(g, true) : g}: ${sets[i] || "none"}`).join("; ")}. A run that hits a limit counts as answered with what it had.`);
    }
  }
  if (by !== "measurement" && fixedMeasurement === "all" && new Set(runs.map(r => r.m)).size > 1) notes.push("Runs of several measurements are pooled per sample; choose one measurement to hold it fixed.");
  return notes.length ? [h("div", {class: "warning", role: "note"}, h("b", {text: "Read with care. "}), notes.length === 1 ? notes[0] : h("ul", {}, notes.map(n => h("li", {text: n}))))] : [];
}

// ---------- render ----------

function render() {
  const page = document.body.dataset.page;
  const body = page === "overview" ? overview() : page === "measurement" ? measurementPage() : comparePage();
  app.replaceChildren(...body);
}
render();
dark.addEventListener("change", render);
