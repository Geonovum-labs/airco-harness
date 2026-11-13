// The pages of the site: overview, measurement and comparison, rendered from data.json.
// All aggregation goes through stats.js, which tests/test_site_stats.py holds to airco-report's numbers.
// Names and values from the logs are data: they go into the page as text nodes, never as HTML.

import {aggregate, commonSamples, costPerCorrect, groupBy, mcpServers, paired} from "./stats.js";
import {outcomeLine} from "./outcome.js";
import {createMap, KINDS, panden, PLACE_STYLE} from "./map.js";

const root = document.body.dataset.root;
const app = document.getElementById("app");
// GitHub Pages lets a browser keep data.json for ten minutes; revalidate, so that a merged measurement shows at once.
const data = await fetch(root + "data.json", {cache: "no-cache"}).then(r => r.json());
const MEASUREMENTS = new Map(data.measurements.map(m => [m.name, m]));
const dark = window.matchMedia("(prefers-color-scheme: dark)");

const METRICS = {
  complete: {label: "complete", share: true, about: "share of the expected content in the answer"},
  correct: {label: "correct", share: true, about: "share of runs that are fully right and invent nothing"},
  source: {label: "source", share: true, about: "share of runs that retrieved an authoritative source"},
  parseable: {label: "parseable", share: true, about: "share of runs whose answer could be read"},
  invented: {label: "invented", share: false, about: "names, values or places per run that do not exist"},
};

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
addEventListener("scroll", () => (tooltip.hidden = true), {passive: true});
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
  const variants = [...new Set(runs.map(r => r.variant))].sort();
  const variant = variants.includes(p.get("variant")) ? p.get("variant") : variants[0];

  const body = [
    h("h1", {text: "Measurements"}),
    h("p", {class: "lead"}, "Each measurement runs a test set against agents and models. The cells show ", h("b", {text: "complete"}),
      ": the share of the expected content in the answer, averaged per sample over its epochs and then over the samples. Open a measurement for its runs, or ",
      h("a", {href: "compare.html", text: "compare"}), " measurements, variants, models and agents."),
    h("div", {class: "filters"}, select("Test set", [["", "All test sets"], ...testsets.map(t => [t, t])], testset, v => { setParams({testset: v}); render(); }),
      variants.length > 1 ? select("Variant", variants.map(v => [v, v]), variant, v => { setParams({variant: v}); render(); }) : null),
    h("div", {class: "kpis"}, kpi("Measurements", String(ms.length)), kpi("Runs", String(runs.length)),
      kpi("Samples", String(new Set(runs.map(r => r.sample)).size)), kpi("Cost", money(runs.reduce((a, r) => a + (r.cost || 0), 0)), "as Inspect logged it")),
  ];

  // The current state of a test set: for each of its samples, the runs of the newest measurement that has it on the variant.
  const ofVariant = new Set(runs.filter(r => r.variant === variant).map(r => `${r.m}|${r.sample}`));
  const cards = (testset ? [testset] : testsets).map(t => {
    const own = ms.filter(m => m.testsets.includes(t));
    const newest = new Map();
    for (const m of own) for (const sample of m.samples) if (!newest.has(sample) && ofVariant.has(`${m.name}|${sample}`)) newest.set(sample, m.name);
    if (!newest.size) return null;
    const current = runsOf(r => newest.get(r.sample) === r.m && r.variant === variant);
    const used = [...new Set(newest.values())].map(n => MEASUREMENTS.get(n));
    const groups = groupBy(current, r => `${r.model}|${r.agent}`);
    const link = used.length === 1 ? `${used[0].name}/report.html#variant=${encodeURIComponent(variant)}` : null;
    return h("section", {class: "card"},
      h("header", {}, h("h2", {text: t}), h("p", {text: `${newest.size} sample${newest.size === 1 ? "" : "s"} · ${current.length} runs${variants.length > 1 ? ` · variant ${variant}` : ""}`})),
      h("p", {class: "muted", style: "margin:0 0 0.6rem;font-size:0.88rem"}, "Newest run of each sample: ", ...used.flatMap((m, i) => [i ? ", " : "",
        h("a", {href: `${m.name}/report.html`, text: when(m.name, true)}), ` (${m.samples.filter(x => newest.get(x) === m.name).join(", ")})`])),
      heatmap({models: sortedModels(current), agents: sortedAgents(current), metric: "complete",
        value: (model, agent) => cellValue(groups.get(`${model}|${agent}`), "complete"),
        onSelect: link ? (model, agent) => (location.href = `${link}&model=${encodeURIComponent(model)}&agent=${encodeURIComponent(agent)}`) : null,
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
  if (/connect/i.test(x.error) || /:000$/.test(x.error)) return "no connection";
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

const INVENTED = "invented, no allowed match";

/** The colour key of a kind of pand, or of a place on no pand, as the map draws it. */
function swatch(kind) {
  if (kind === "invented") return h("span", {class: "key", style: `background:${PLACE_STYLE.fillColor};border:2px solid ${PLACE_STYLE.color}`});
  const {style} = KINDS[kind];
  return h("span", {class: "key sq", style: `border-color:${style.color};background:${style.fillOpacity ? style.fillColor : "transparent"}`});
}

// ---------- measurement ----------

const BASELINE = "0";
const ALONE = "model"; // the agent that is the model alone, without tools
// Variant colors by role: the baseline orange, the other variants blue and aqua in sorted order. Only these three pass
// the dataviz validator for marks that can sit beside each other in any pairing; a further variant is drawn in muted ink.
const HUES = ["--v-base", "--v-1", "--v-2"];
const COMPLETE = "share of the expected content in the answer";
const NOISE = "No run-to-run noise margin has been measured yet, so read small differences with care.";
const SOURCE_NOTE = "source counts web retrievals with a URL only; an MCP call carries no URL, so it does not count.";

const pct = v => (v === null || v === undefined ? "n/a" : `${Math.round(v * 100)}%`);
const pts = v => (v === null || v === undefined ? "n/a" : `${v < 0 ? "−" : "+"}${Math.abs(Math.round(v * 100))} pts`);
const plusMinus = s => (s.se === null ? "" : ` ± ${Math.round(s.se * 100)}`);
const dollars = v => (v === null || v === undefined ? "n/a" : v < 0.1 ? `$${v.toFixed(3)}` : `$${v.toFixed(2)}`);
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
const setupName = s => `${s.model} with ${s.agent === ALONE ? "no tools" : s.agent}`;
const runKey = r => [r.model, r.agent, r.variant, r.sample, r.epoch].join("|");
const viewerLink = r => `viewer/#/logs/${encodeURIComponent(r.log)}/samples/sample/${encodeURIComponent(r.sample)}/${r.epoch}/`;
// A sample id can mean another question in another measurement, so a map question is looked up per measurement.
const mapOf = r => data.maps[`${r.m}/${r.sample}`];

/** A question split into what is asked and how to answer, so the ask can be read first. */
function splitQuestion(text) {
  const cut = text.search(/ (Answer with|Antwoord met)/);
  return cut > 0 ? [text.slice(0, cut), text.slice(cut + 1)] : [text, ""];
}

function limitsText(limits) {
  const shown = {token: v => `${compact(+v)} tokens`, time: v => `${Math.round(v / 60)} min`, message: v => `${v} messages`, cost: v => `$${v}`};
  return Object.entries(shown).filter(([k]) => limits[k]?.length).map(([k, f]) => limits[k].map(f).join(" or ")).join(", ") || "none";
}

/** One model with one agent: its runs per variant, the samples its variants are scored on (those every variant it ran
 * has, so that the distance between two marks is the gain) and per variant other than the baseline its paired gain. */
function setup(model, agent, runs, variants, baseline) {
  const byVariant = new Map(variants.map(v => [v, runs.filter(r => r.variant === v)]).filter(([, rs]) => rs.length));
  const groups = [...byVariant.values()];
  const common = groups.length > 1 ? commonSamples(groups) : null;
  const samples = common && common.size ? common : null;
  const base = baseline ? byVariant.get(baseline) : null;
  return {
    model, agent, byVariant, samples, disjoint: !!common && !common.size,
    marks: new Map([...byVariant].map(([v, rs]) => [v, aggregate(rs, "complete", samples)])),
    gains: new Map(base && samples ? [...byVariant].filter(([v]) => v !== baseline).map(([v, rs]) => [v, paired(base, rs, "complete", samples)]) : []),
    scored: v => (samples ? byVariant.get(v).filter(r => samples.has(r.sample)) : byVariant.get(v) || []),
  };
}

/** What a measurement compares. Variants with the baseline first. Setups are every model with every agent; the chart
 * rows are the agents with tools, and the model alone is a ring on the rows of its model, or a row when it is all the
 * model ran. */
function design(all) {
  const names = [...new Set(all.map(r => r.variant))].sort();
  const baseline = names.includes(BASELINE) ? BASELINE : null;
  const variants = baseline ? [baseline, ...names.filter(v => v !== baseline)] : names;
  const others = variants.filter(v => v !== baseline);
  const style = new Map(variants.map(v => {
    const hue = HUES[v === baseline ? 0 : others.indexOf(v) + 1];
    return [v, {color: `var(${hue || "--muted"})`, label: v === baseline ? "Variant 0, the baseline" : `Variant ${v}`}];
  }));
  const setups = [], rows = [];
  for (const model of sortedModels(all)) {
    const own = all.filter(r => r.model === model);
    const mine = sortedAgents(own).map(agent => setup(model, agent, own.filter(r => r.agent === agent), variants, baseline));
    const tools = mine.filter(s => s.agent !== ALONE), alone = mine.find(s => s.agent === ALONE) || null;
    setups.push(...mine);
    rows.push(...(tools.length ? tools.map(s => ({...s, alone})) : mine.map(s => ({...s, alone: null}))));
  }
  return {variants, baseline, others, comparing: !!baseline && others.length > 0, style, setups, rows};
}

const scoredRuns = (rows, v) => rows.flatMap(r => (r.byVariant.has(v) ? r.scored(v) : []));
const ringOf = r => (r.alone ? aggregate([...r.alone.byVariant.values()].flat(), "complete", r.samples) : null);

/** The answer to the measurement's question in one to three sentences, worded for its shape. */
function headline(d, m) {
  const questions = m.samples.length === 1 ? "one question" : `${m.samples.length} questions`;
  const found = (rows, v) => pct(aggregate(scoredRuns(rows, v), "complete").mean);
  if (!d.comparing) {
    const without = d.baseline ? [] : ["This measurement has no baseline variant 0, so it shows scores without gains."];
    if (d.variants.length > 1) {
      return [...without, ...d.variants.map(v => {
        const rows = d.rows.filter(r => r.byVariant.has(v));
        return `With variant ${v}, the ${plural(rows.length, "setup")} found ${found(rows, v)} of the expected content.`;
      })].slice(0, 3);
    }
    const v = d.variants[0];
    const ranked = d.rows.filter(r => r.marks.get(v)?.mean != null).sort((a, b) => b.marks.get(v).mean - a.marks.get(v).mean);
    const [best, worst] = [ranked[0], ranked[ranked.length - 1]];
    const alone = [...new Set(d.rows.map(r => r.alone).filter(Boolean))].flatMap(a => [...a.byVariant.values()].flat());
    return [
      `${d.baseline ? "The" : `With variant ${v}, the`} ${plural(ranked.length, "setup")} found ${found(ranked, v)} of the expected content over the ${questions}.`,
      ...without,
      ranked.length > 1 ? `${setupName(best)} scored highest at ${pct(best.marks.get(v).mean)}, ${setupName(worst)} lowest at ${pct(worst.marks.get(v).mean)}.` : "",
      alone.length && d.baseline ? `Without tools, the models alone found ${pct(aggregate(alone, "complete").mean)}.` : "",
    ].filter(Boolean).slice(0, 3);
  }
  const lines = d.others.map(v => {
    const both = d.rows.filter(r => r.gains.get(v)?.mean != null);
    if (!both.length) return [`No setup ran both variant 0 and variant ${v} on the same questions, so there is no gain to show.`];
    const ranked = [...both].sort((a, b) => b.gains.get(v).mean - a.gains.get(v).mean);
    const [most, least] = [ranked[0], ranked[ranked.length - 1]];
    return [
      `With variant ${v}, the ${plural(both.length, "setup")} that also ran variant 0 found ${found(both, v)} of the expected content, against ${found(both, d.baseline)} without it.`,
      both.length > 1 ? `${both.filter(r => r.gains.get(v).mean > 0).length} of ${both.length} scored higher; ${setupName(most)} gained most (${pts(most.gains.get(v).mean)}), ${setupName(least)} least (${pts(least.gains.get(v).mean)}).` : "",
    ];
  });
  return (lines.length === 1 ? lines[0] : lines.map(l => l[0])).filter(Boolean).slice(0, 3);
}

// ---------- marks shared by the charts ----------

const x = v => `${Math.max(0, Math.min(1, v)) * 100}%`;
const gridlines = () => [0, 0.25, 0.5, 0.75, 1].map(t => h("span", {class: "grid", style: `left:${x(t)}`, "aria-hidden": "true"}));
const axisRow = cls => h("div", {class: `drow axis ${cls}`, "aria-hidden": "true"}, h("div"),
  h("div", {class: "track"}, h("div", {class: "plot"}, [0, 0.25, 0.5, 0.75, 1].map(t => h("span", {class: "tick", style: `left:${x(t)}`, text: pct(t)})))), h("div"));
const dotKey = (d, v) => h("span", {class: "dot key", style: `--c:${d.style.get(v).color}`, "aria-hidden": "true"});

/** A 0 to 100% track with one dot per variant, a faint band of one standard error around each, and a ring for the model alone. */
function track(d, marks, ring) {
  const values = [...marks.values()].filter(s => s.mean !== null).map(s => s.mean);
  const lo = Math.min(...values), hi = Math.max(...values);
  return h("div", {class: "track"}, h("div", {class: "plot"}, gridlines(),
    [...marks].filter(([, s]) => s.mean !== null && s.se !== null).map(([v, s]) => {
      const a = Math.max(0, s.mean - s.se), b = Math.min(1, s.mean + s.se);
      return h("span", {class: "band", style: `left:${x(a)};width:${(b - a) * 100}%;--c:${d.style.get(v).color}`});
    }),
    values.length > 1 ? h("span", {class: "stem", style: `left:${x(lo)};width:${(hi - lo) * 100}%`}) : null,
    ring && ring.mean !== null ? h("span", {class: "dot ring", style: `left:${x(ring.mean)}`}) : null,
    [...marks].filter(([, s]) => s.mean !== null).map(([v, s]) => h("span", {class: "dot", style: `left:${x(s.mean)};--c:${d.style.get(v).color}`}))));
}

function legend(d, {ring = false, band = false, variants = d.variants} = {}) {
  return h("ul", {class: "legend"}, variants.map(v => h("li", {}, dotKey(d, v), d.style.get(v).label)),
    ring ? h("li", {}, h("span", {class: "dot key ring", "aria-hidden": "true"}), "Same model, no tools") : null,
    band ? h("li", {}, h("span", {class: "bandkey", "aria-hidden": "true"}), "Shaded: one standard error over the questions") : null);
}

/** A card with a chart and its table view behind a toggle. */
function chartCard({title, note, legendList, chart, tableView, after, id}) {
  const wrap = h("div", {hidden: true}, tableView);
  const toggle = h("button", {class: "btn", type: "button", "aria-pressed": "false", text: "Table", onclick: () => {
    const on = wrap.hidden;
    wrap.hidden = !on; chart.hidden = on;
    toggle.setAttribute("aria-pressed", String(on)); toggle.textContent = on ? "Chart" : "Table";
  }});
  return h("section", {class: "card", id}, h("div", {class: "cardhead"}, h("h2", {text: title}), toggle),
    note ? h("p", {class: "cardnote", text: note}) : null, legendList, chart, wrap, after);
}

// ---------- per model and agent ----------

function setupChart(d, m) {
  const groups = [...groupBy(d.rows, r => r.model).values()];
  // Without a baseline to gain over, the column gives the score itself.
  const meanCell = r => h("div", {class: "dgain"}, [...r.marks].map(([v, s]) => h("div", {}, d.variants.length > 1 ? dotKey(d, v) : null, h("b", {text: pct(s.mean)}))));
  const gainCell = r => h("div", {class: "dgain"}, d.others.map(v => {
    const g = r.gains.get(v);
    const why = !r.byVariant.has(v) ? `not run with variant ${v}` : !r.byVariant.has(d.baseline) ? "not run with variant 0" : r.disjoint ? "no question in common" : "";
    return h("div", {class: g && g.mean !== null ? "" : "muted", title: why || null}, d.others.length > 1 ? dotKey(d, v) : null, h("b", {text: g && g.mean !== null ? pts(g.mean) : "n/a"}));
  }));
  const lines = r => {
    const ring = ringOf(r);
    return [setupName(r),
      ...[...r.marks].map(([v, s]) => `${d.style.get(v).label}: ${pct(s.mean)}${plusMinus(s)} (${plural(s.n, "question")})`),
      ...(ring && ring.mean !== null ? [`Same model, no tools: ${pct(ring.mean)}${plusMinus(ring)}`] : []),
      ...[...r.gains].map(([v, g]) => `Gain of variant ${v}: ${pts(g.mean)}${g.se === null ? "" : `, standard error ${Math.round(g.se * 100)} pts`}, paired over ${plural(g.n, "question")}`),
      ...(r.disjoint ? ["The variants of this setup ran no question in common."] : [])];
  };
  const rows = groups.map(rs => h("div", {class: "dgroup"}, h("div", {class: "dmodel", text: rs[0].model}),
    h("div", {}, rs.map(r => {
      const row = h("div", {class: "drow setup", tabindex: "0", "aria-label": lines(r).join(". ")},
        h("div", {class: "dagent", text: r.agent === ALONE ? "no tools" : r.agent}), track(d, r.marks, ringOf(r)), d.comparing ? gainCell(r) : meanCell(r));
      tip(row, () => lines(r));
      return row;
    }))));
  const head = h("div", {class: "drow dhead"}, h("div"), h("div", {class: "plotlabel", text: `complete: ${COMPLETE}`}), h("div", {class: "dgain", text: d.comparing ? "Gain" : "Mean"}));
  const anyRing = d.rows.some(r => ringOf(r)?.mean != null), anyBand = d.rows.some(r => [...r.marks.values()].some(s => s.se !== null));
  const columns = ["Model", "Agent", ...d.variants.map(v => `Variant ${v}`), ...(anyRing ? ["No tools"] : []), ...(d.comparing ? d.others.map(v => `Gain ${v}`) : []), "Questions"];
  const tableView = table(columns,
    d.rows.map(r => h("tr", {}, h("td", {class: "nowrap", text: r.model}), h("td", {text: r.agent}),
      d.variants.map(v => { const s = r.marks.get(v); return h("td", {class: "num", text: s ? `${pct(s.mean)}${plusMinus(s)}` : "not run"}); }),
      anyRing ? h("td", {class: "num", text: ringOf(r) ? pct(ringOf(r).mean) : ""}) : null,
      d.comparing ? d.others.map(v => { const g = r.gains.get(v); return h("td", {class: "num", text: g ? `${pts(g.mean)}${g.se === null ? "" : ` ± ${Math.round(g.se * 100)}`}` : "n/a"}); }) : null,
      h("td", {class: "num", text: String(r.samples ? r.samples.size : Math.max(...[...r.marks.values()].map(s => s.n)))}))),
    columns.map((_, i) => i).slice(2));
  return chartCard({
    title: "Per model and agent",
    note: `Each mark is the mean over the questions, each question first averaged over its epochs. ${d.variants.length > 1 ? "The marks of a row count only the questions every variant of that row ran. " : ""}Hover or focus a row for the exact numbers.`,
    legendList: legend(d, {ring: anyRing, band: anyBand}),
    chart: h("div", {class: "dumbbell setups"}, head, rows, axisRow("")),
    tableView,
    after: d.comparing ? h("p", {class: "noise", text: NOISE}) : null,
    id: "setups",
  });
}

// ---------- which questions fail ----------

/** Per question, each variant pooled over the setups that ran that question with every variant that has it. */
function questionStats(d, m) {
  return m.samples.map((sample, i) => {
    const present = d.variants.filter(v => d.rows.some(r => (r.byVariant.get(v) || []).some(x => x.sample === sample && !x.failed)));
    const rows = d.rows.filter(r => present.every(v => (r.byVariant.get(v) || []).some(x => x.sample === sample && !x.failed)));
    const of = (r, v) => r.byVariant.get(v).filter(x => x.sample === sample);
    const stats = new Map(present.map(v => [v, aggregate(rows.flatMap(r => of(r, v)), "complete")]));
    const solved = new Map(present.map(v => [v, rows.filter(r => aggregate(of(r, v), "complete").mean === 1).length]));
    const alone = [...new Set(d.rows.map(r => r.alone).filter(Boolean))].flatMap(a => [...a.byVariant.values()].flat()).filter(x => x.sample === sample);
    const base = d.baseline && stats.get(d.baseline);
    const gains = new Map(base ? present.filter(v => v !== d.baseline).map(v => [v, stats.get(v).mean - base.mean]) : []);
    return {sample, n: i + 1, text: splitQuestion(m.questions[sample] || sample)[0], present, rows, stats, solved, gains, ring: alone.length ? aggregate(alone, "complete") : null};
  });
}

function questionChart(d, m, qs) {
  const right = q => (d.comparing
    ? h("div", {class: "dgain"}, d.others.map(v => h("div", {class: q.gains.has(v) ? "" : "muted", title: q.gains.has(v) ? null : `variant ${v} or variant 0 did not run this question`},
      d.others.length > 1 ? dotKey(d, v) : null, h("b", {text: q.gains.has(v) ? pts(q.gains.get(v)) : "n/a"}))))
    : h("div", {class: "dgain"}, h("b", {text: `${q.solved.get(d.variants[0]) ?? 0} of ${q.rows.length}`}), h("small", {text: "fully solved"})));
  const lines = q => [`Q${q.n} (${q.sample})`, ...q.present.map(v => `${d.style.get(v).label}: ${pct(q.stats.get(v).mean)}, fully solved by ${q.solved.get(v)} of ${plural(q.rows.length, "setup")}`),
    ...(q.ring ? [`Same model, no tools: ${pct(q.ring.mean)}`] : []), ...[...q.gains].map(([v, g]) => `Gain of variant ${v}: ${pts(g)}`)];
  const rows = qs.map(q => {
    const row = h("div", {class: "drow question", tabindex: "0", "aria-label": lines(q).join(". ")},
      h("a", {class: "qlabel", href: `#q-${q.sample}`, title: q.text, onclick: e => { e.preventDefault(); document.getElementById(`q-${q.sample}`)?.scrollIntoView({behavior: "smooth"}); }},
        h("b", {text: `Q${q.n} `}), h("span", {text: q.text})),
      track(d, q.stats, q.ring), right(q));
    tip(row, () => lines(q));
    return row;
  });
  const head = h("div", {class: "drow question dhead"}, h("div"), h("div", {class: "plotlabel", text: "complete, pooled over the setups"}), h("div", {class: "dgain", text: d.comparing ? "Gain" : "Setups"}));
  const scored = qs.filter(q => q.present.length);
  const v1 = d.comparing ? d.others[0] : d.variants[0];
  const withV = scored.filter(q => q.stats.has(v1));
  let note = "";
  if (withV.length > 1) {
    const hardest = withV.reduce((a, b) => (b.stats.get(v1).mean < a.stats.get(v1).mean ? b : a));
    const lifted = withV.filter(q => q.gains.has(v1));
    const most = lifted.length ? lifted.reduce((a, b) => (b.gains.get(v1) > a.gains.get(v1) ? b : a)) : null;
    note = [most ? `Q${most.n} gains most with variant ${v1} (${pct(most.stats.get(d.baseline).mean)} to ${pct(most.stats.get(v1).mean)}).` : "",
      `Q${hardest.n} is hardest${d.comparing ? ` with variant ${v1}` : ""}: ${pct(hardest.stats.get(v1).mean)}, fully solved by ${hardest.solved.get(v1)} of ${plural(hardest.rows.length, "setup")}.`].filter(Boolean).join(" ");
  }
  const columns = ["Question", ...d.variants.map(v => `Variant ${v}`), ...d.variants.map(v => `Solved, ${v}`), ...(d.comparing ? d.others.map(v => `Gain ${v}`) : []), "Setups"];
  const tableView = table(columns,
    qs.map(q => h("tr", {}, h("td", {text: `Q${q.n} ${q.text}`}),
      d.variants.map(v => h("td", {class: "num", text: q.stats.has(v) ? pct(q.stats.get(v).mean) : "not run"})),
      d.variants.map(v => h("td", {class: "num", text: q.solved.has(v) ? String(q.solved.get(v)) : ""})),
      d.comparing ? d.others.map(v => h("td", {class: "num", text: q.gains.has(v) ? pts(q.gains.get(v)) : "n/a"})) : null,
      h("td", {class: "num", text: String(q.rows.length)}))),
    columns.map((_, i) => i).slice(1));
  return chartCard({
    title: "Which questions fail",
    note: `${note} Each question pools the runs of the setups that ran it with ${d.variants.length > 1 ? "every variant that has it" : "the variant"}; "fully solved" counts setups whose every epoch was complete.`.trim(),
    legendList: legend(d, {ring: qs.some(q => q.ring)}),
    chart: h("div", {class: "dumbbell questions"}, head, rows, axisRow("question")),
    tableView,
    id: "questions",
  });
}

// ---------- cost per correct answer ----------

function costCard(d, m) {
  const change = (base, after) => (after === null ? "" : base === null ? "none correct with variant 0"
    : after < base ? `${(base / after).toFixed(base / after >= 10 ? 0 : 1)}× cheaper than variant 0` : `${(after / base).toFixed(1)}× dearer than variant 0`);
  const rows = d.setups.map(s => {
    const cost = new Map([...s.byVariant.keys()].map(v => [v, costPerCorrect(s.scored(v))]));
    const versus = v => (v !== d.baseline && cost.has(d.baseline) && s.samples ? change(cost.get(d.baseline), cost.get(v)) : "");
    return h("tr", {}, h("td", {class: "who"}, h("span", {text: s.model}), " ", h("span", {class: "muted", text: s.agent === ALONE ? "no tools" : s.agent})),
      d.variants.map(v => h("td", {class: "num"}, !cost.has(v) ? "not run" : cost.get(v) === null ? "none correct" : dollars(cost.get(v)),
        cost.has(v) && versus(v) ? h("small", {class: "change", text: versus(v)}) : null)));
  });
  return h("section", {class: "card", id: "cost"},
    h("div", {class: "cardhead"}, h("h2", {text: "Cost per correct answer"})),
    h("p", {class: "cardnote", text: `All API cost of a setup's runs divided by its fully correct answers${d.variants.length > 1 ? ", over the questions every variant of the setup ran" : ""}. The whole measurement cost ${money(m.cost)}.`}),
    table(["Model and agent", ...d.variants.map(v => `Variant ${v}`)], rows, d.variants.map((_, i) => i + 1)));
}

// ---------- question cards: every run as a mark ----------

const SHAPES = {answered: "Answered", hollow: "No usable answer", limit: "Stopped at a limit", error: "Error"};
const shapeOf = r => (r.failed ? "error" : r.limit ? "limit" : r.parseable === 0 ? "hollow" : "answered");

function markLines(d, m, r) {
  return [r.failed ? "error" : pct(r.complete), setupName(r), `${d.style.get(r.variant).label}, epoch ${r.epoch}`, outcomeLine(r, m.limits)];
}

/** One lane of marks, a run each; runs with the same score sit side by side instead of on top of each other. */
function lane(d, m, runs, selected, onPick) {
  const marks = [];
  for (const [value, same] of groupBy(runs, r => Math.round((r.complete ?? 0) * 100))) {
    same.forEach((r, i) => {
      const step = value <= 3 ? i : value >= 97 ? -i : i - (same.length - 1) / 2;
      const shape = shapeOf(r);
      const mark = h("button", {class: `mark ${shape}${selected === runKey(r) ? " selected" : ""}`, type: "button", "data-run": runKey(r),
        style: `left:calc(${value}% + ${step * 11}px);--c:${d.style.get(r.variant).color}`, "aria-label": markLines(d, m, r).join(". "), "aria-pressed": String(selected === runKey(r)),
        onclick: () => onPick(r)});
      tip(mark, () => markLines(d, m, r));
      marks.push(mark);
    });
  }
  return h("div", {class: "lane"}, marks);
}

function summaryLines(d, m, sample) {
  const isMap = !!data.maps[`${m.name}/${sample}`];
  const line = (rs, label, v) => {
    const limited = rs.filter(r => r.limit);
    const kinds = [...groupBy(limited, r => r.limit)].map(([k, g]) => `${g.length} ${k}`).join(", ");
    const parts = [
      `${rs.filter(r => r.correct === 1).length} fully right`,
      `${rs.filter(r => !r.failed && r.parseable === 0).length} ${isMap ? "showed no map" : "gave no usable answer"}`,
      limited.length ? `${limited.length} stopped at a limit (${kinds})` : "none stopped at a limit",
      isMap ? `${rs.filter(r => r.invented > 0).length} put places on no allowed feature` : `${rs.filter(r => r.parseable === 1 && r.correct !== 1).length} gave a wrong answer`,
      ...(rs.some(r => r.failed) ? [`${rs.filter(r => r.failed).length} ended in an error`] : []),
    ];
    return h("li", {}, v ? dotKey(d, v) : null, h("b", {text: `${label}, ${plural(rs.length, "run")}: `}), `${parts.join(", ")}.`);
  };
  const tools = d.setups.filter(s => s.agent !== ALONE), alone = d.setups.filter(s => s.agent === ALONE);
  const ofSample = (ss, v) => ss.flatMap(s => (s.byVariant.get(v) || []).filter(r => r.sample === sample));
  return [
    ...d.variants.map(v => [v, ofSample(tools, v)]).filter(([, rs]) => rs.length).map(([v, rs]) => line(rs, `Agents with tools${d.variants.length > 1 ? `, variant ${v}` : ""}`, v)),
    ...d.variants.map(v => [v, ofSample(alone, v)]).filter(([, rs]) => rs.length).map(([v, rs]) => line(rs, `Model alone, no tools${d.variants.length > 1 ? `, variant ${v}` : ""}`, null)),
  ];
}

function questionCard(d, m, sample, n, selected, onPick) {
  const [ask, format] = splitQuestion(m.questions[sample] || sample);
  const map = data.maps[`${m.name}/${sample}`];
  const means = s => {
    const values = d.variants.filter(v => (s.byVariant.get(v) || []).some(r => r.sample === sample))
      .map(v => [v, aggregate(s.byVariant.get(v).filter(r => r.sample === sample), "complete").mean]);
    return h("div", {class: "rvals"}, values.flatMap(([v, mean], i) => [i ? h("span", {class: "to", text: values.length === 2 && d.comparing ? " to " : " "}) : null, dotKey(d, v), pct(mean)]));
  };
  const groups = [...groupBy(d.setups, s => s.model).values()].map(ss => {
    const lanes = ss.map(s => [s, d.variants.map(v => (s.byVariant.get(v) || []).filter(r => r.sample === sample).sort((a, b) => a.epoch - b.epoch)).filter(rs => rs.length)]).filter(([, ls]) => ls.length);
    if (!lanes.length) return null;
    return h("div", {class: "qgroup"}, h("div", {class: "mname", text: ss[0].model}),
      h("div", {}, lanes.map(([s, ls]) => h("div", {class: "qrow"}, h("div", {class: "aname", text: s.agent === ALONE ? "no tools" : s.agent}),
        h("div", {class: "strip"}, gridlines(), ls.map(rs => lane(d, m, rs, selected, onPick))), means(s)))));
  });
  const chosen = selected ? data.runs.find(r => r.m === m.name && r.sample === sample && runKey(r) === selected) : null;
  const epochs = rs => rs.map(r => `${r.failed ? "error" : pct(r.complete)}${r.limit ? "*" : ""}`).join(", ") || "not run";
  const tableView = h("details", {class: "tableview"}, h("summary", {text: "Table view"}),
    table(["Model", "Agent", ...d.variants.map(v => `Variant ${v}, per epoch`)],
      d.setups.filter(s => [...s.byVariant.values()].flat().some(r => r.sample === sample)).map(s => h("tr", {}, h("td", {class: "nowrap", text: s.model}), h("td", {text: s.agent}),
        d.variants.map(v => h("td", {class: "num", text: epochs((s.byVariant.get(v) || []).filter(r => r.sample === sample).sort((a, b) => a.epoch - b.epoch))}))))),
    h("p", {class: "muted small", text: "* stopped at a limit"}));
  return h("section", {class: "card question", id: `q-${sample}`, "aria-labelledby": `h-${sample}`},
    h("div", {class: "qnum"}, `Question ${n} `, h("span", {class: "chip", text: sample})),
    h("h3", {id: `h-${sample}`, text: ask}),
    format || map ? h("p", {class: "format"}, format, map ? `${format ? " " : ""}Expected: the ${plural(map.must.length, "required feature")} on the map.` : "") : null,
    h("ul", {class: "why"}, summaryLines(d, m, sample)),
    h("div", {class: "qplot"}, h("div", {class: "qrow axisrow", "aria-hidden": "true"}, h("div", {class: "aname"}),
      h("div", {class: "qaxis"}, [0, 0.5, 1].map(t => h("span", {style: `left:${x(t)}`, text: pct(t)}))), h("div", {class: "rvals muted", text: "Mean"})), groups),
    chosen ? runDetail(d, m, chosen) : null,
    tableView);
}

function cardsLegend(d, m) {
  const shapes = Object.entries(SHAPES).filter(([k]) => k !== "error" || data.runs.some(r => r.m === m.name && r.failed));
  return h("div", {class: "marklegend"},
    h("p", {text: "Each mark is one run: its position is complete, the share of the expected content in the answer. Choose a mark for the run's outcome, its sources and its log."}),
    h("ul", {class: "legend"}, d.variants.map(v => h("li", {}, dotKey(d, v), d.style.get(v).label)),
      shapes.map(([k, label]) => h("li", {}, h("span", {class: `mark key ${k}`, "aria-hidden": "true"}), label))));
}

// ---------- the detail of one run ----------

/** The hosts a run retrieved from, the first two shown and the rest behind a button. */
function hostList(run) {
  const lines = retrievedFrom(run);
  if (!Array.isArray(lines) || lines.length <= 2) return lines;
  const more = h("button", {class: "btn", type: "button", text: `+${lines.length - 2}`, "aria-label": `Show ${lines.length - 2} more hosts`, onclick: () => more.replaceWith(...lines.slice(2))});
  return [...lines.slice(0, 2), more];
}

function runDetail(d, m, run) {
  const yes = (v, ok, no) => (run.failed ? "error" : v === 1 ? ok : no);
  const score = (label, value, good) => h("div", {}, h("dt", {text: label}), h("dd", {class: good === undefined || run.failed ? "" : good ? "ok" : "bad", text: value}));
  const close = h("button", {class: "btn", type: "button", text: "Close", onclick: () => { setParams({run: null}); render(); document.querySelector(`[data-run="${CSS.escape(runKey(run))}"]`)?.focus({preventScroll: true}); }});
  const section = h("div", {class: "detail", id: "detail", role: "region", "aria-label": "Run detail"},
    h("div", {class: "detailhead"}, h("strong", {text: `${setupName(run)} · variant ${run.variant} · epoch ${run.epoch}`}),
      h("span", {}, h("a", {class: "btn", href: viewerLink(run), text: "Log"}), close)),
    h("p", {class: "outcome", text: outcomeLine(run, m.limits)}),
    h("dl", {class: "scores"},
      score("complete", run.failed ? "error" : pct(run.complete)), score("correct", yes(run.correct, "yes", "no"), run.correct === 1),
      score("parseable", yes(run.parseable, "usable", "not usable"), run.parseable === 1), score("source", yes(run.source, "yes", "no"), run.source === 1),
      score("invented", run.failed ? "error" : String(run.invented ?? "n/a"), run.invented === 0)),
    h("p", {class: "muted small", text: `${SOURCE_NOTE[0].toUpperCase()}${SOURCE_NOTE.slice(1)}`}),
    h("p", {class: "effort", text: [dollars(run.cost), `${compact(run.tokens)} tokens`, plural(run.tool_calls ?? 0, "tool call"), `${fmt(run.total_time_s, 0)} s`].join(" · ")}),
    h("div", {class: "sources"}, h("span", {class: "k", text: "Retrieved from"}), h("div", {class: "hosts"}, hostList(run))),
    run.mcp_server ? h("p", {class: "muted small", text: `MCP server available: ${run.mcp_server}.`}) : null);
  const sample = mapOf(run);
  if (sample) {
    const result = h("p", {class: "result"}), counts = h("ul", {class: "legend"});
    const element = h("div", {id: "map", role: "img", "aria-label": "Map of the chosen run"});
    section.append(h("div", {class: "scoring"},
      h("p", {}, h("b", {text: "Required: "}), `the ${sample.must.length} features the map has to show; each one missing lowers complete. `,
        h("b", {text: "Optional: "}), `${sample.optional} other reference features may be shown without effect on the score. `,
        h("b", {text: "Invented: "}), "a place with no allowed match."),
      sample.note ? h("details", {}, h("summary", {text: "Why these features"}), h("p", {text: sample.note})) : null),
      h("p", {class: "muted small"}, "What the agent showed with ", h("code", {text: "show_on_map"}), ", on the BRT achtergrondkaart in RD. Click a feature or a dot for what the agent said about that place."),
      result, element, counts);
    // Leaflet needs the element in the page to size the map, so it draws after the page is in place.
    requestAnimationFrame(async () => {
      const c = createMap(element)(run, sample.must, await panden(root, sample.panden), sample.allowed_optional ?? null);
      result.textContent = run.explanation;
      counts.replaceChildren(...Object.keys(KINDS).map(k => h("li", {}, swatch(k), `${KINDS[k].label}: `, h("b", {text: String(c[k])}))),
        h("li", {}, swatch("invented"), `${INVENTED}: `, h("b", {text: String(c.unmatched)})));
    });
  }
  return section;
}

// ---------- the page ----------

let arriving = true;

function measurementPage() {
  const name = document.body.dataset.measurement;
  const m = MEASUREMENTS.get(name);
  const all = runsOf(r => r.m === name);
  const d = design(all);
  const p = params();
  const selected = all.some(r => runKey(r) === p.get("run")) ? p.get("run") : null;
  const onPick = r => {
    const key = runKey(r);
    setParams({run: selected === key ? null : key});
    render();
    document.querySelector(`[data-run="${CSS.escape(key)}"]`)?.focus({preventScroll: true});
  };
  const facts = [
    ["Test set", testsetLabel(m)], ["Commit", m.commits.join(", ") || "n/a"], ["Limits per run", limitsText(m.limits)],
    ["Runs", String(m.runs)], ["Errors", String(m.failed)], ["At a limit", String(m.at_limit)], ["Cost", money(m.cost)],
  ];
  const [verdict, ...rest] = headline(d, m);
  const qs = questionStats(d, m);
  const split = groupBy(all, r => `${r.model}|${r.agent}|${r.variant}`);
  const cells = d.setups.flatMap(s => d.variants.map(v => `${s.model}|${s.agent}|${v}`)).filter(k => split.has(k)).map(k => [k.split("|"), split.get(k)]);
  const quality = cells.map(([[model, agent, v], g]) =>
    h("tr", {}, h("td", {class: "nowrap", text: model}), h("td", {text: agent}), h("td", {class: "nowrap", text: v}),
      ...Object.keys(METRICS).map(k => { const s = aggregate(g, k); return h("td", {class: "num", text: s.se === null ? fmt(s.mean) : `${fmt(s.mean)} ± ${fmt(s.se)}`}); })));
  const trajectory = cells.map(([[model, agent, v], g]) =>
    h("tr", {}, h("td", {class: "nowrap", text: model}), h("td", {text: agent}), h("td", {class: "nowrap", text: v}),
      h("td", {class: "num", text: fmt(aggregate(g, "tool_calls").mean, 1)}), h("td", {class: "num", text: compact(aggregate(g, "tokens").mean)}),
      h("td", {class: "num", text: fmt(aggregate(g, "total_time_s").mean, 0)}), h("td", {class: "num", text: money(g.reduce((a, r) => a + (r.cost || 0), 0))}),
      h("td", {class: "num", text: money(costPerCorrect(g))})));
  // A link to a run opens the page on it; a run chosen on the page opens where the reader already is.
  if (selected && arriving) requestAnimationFrame(() => document.getElementById("detail")?.scrollIntoView({block: "start"}));
  arriving = false;
  return [
    h("nav", {class: "crumbs"}, h("a", {href: "../", text: "All measurements"}), " › ", when(name), " · ", h("a", {href: "viewer/", text: "Viewer"}), " · ",
      h("a", {href: `https://github.com/Geonovum-labs/airco-harness/blob/main/reports/${name}/report.md`, text: "report.md"}), " · ",
      h("a", {href: `../compare.html#by=${d.variants.length > 1 ? "variant" : "model"}&measurement=${encodeURIComponent(name)}`, text: d.variants.length > 1 ? "Compare variants" : "Compare"})),
    h("h1", {text: `Measurement of ${when(name)}`}),
    h("p", {class: "facts"}, facts.map(([k, v]) => h("span", {}, `${k} `, h("b", {text: v})))),
    h("section", {class: "answer", "aria-label": "Main finding"}, h("p", {class: "verdict", text: verdict}), rest.length ? h("p", {class: "lines", text: rest.join(" ")}) : null),
    setupChart(d, m),
    qs.length > 1 ? questionChart(d, m, qs) : null,
    costCard(d, m),
    h("h2", {class: "section", text: m.samples.length > 1 ? "Question by question" : "The question"}),
    cardsLegend(d, m),
    ...m.samples.map((s, i) => questionCard(d, m, s, i + 1, selected, onPick)),
    h("details", {}, h("summary", {text: "Table: quality metrics per model, agent and variant"}),
      table(["Model", "Agent", "Variant", ...Object.keys(METRICS)], quality, [3, 4, 5, 6, 7]),
      h("p", {class: "muted small", text: `Mean ± standard error over the questions. ${SOURCE_NOTE[0].toUpperCase()}${SOURCE_NOTE.slice(1)}`})),
    h("details", {}, h("summary", {text: "Table: trajectory and cost per model, agent and variant"}),
      table(["Model", "Agent", "Variant", "Tool calls", "Tokens", "Time (s)", "Cost", "Cost per correct"], trajectory, [3, 4, 5, 6, 7])),
  ].filter(Boolean);
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
  // Per run, because one measurement can mix variants with and without a server. Variants differ in their server by design.
  if (by !== "variant") {
    const servers = chosen.map(g => mcpServers(runs.filter(r => value(r, by) === g)));
    if (new Set(servers).size > 1) notes.push(`The groups ran against different MCP server versions: ${chosen.map((g, i) => `${by === "measurement" ? when(g, true) : g}: ${servers[i] || "none recorded"}`).join("; ")}.`);
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
