// A run's scorer explanation as one short line a reader can follow. validators/rules.py writes the explanations;
// a shape this file does not know is shown as it is.

const items = text => (text.match(/'[^']*'|"[^"]*"/g) || []).map(x => x.slice(1, -1));
const count = (n, one, many = `${one}s`) => `${Number(n).toLocaleString("en-US")} ${Number(n) === 1 ? one : many}`;

const RULES = [
  [/^not parseable: no map shown/, () => "No map shown"],
  [/^not parseable: no plot shown/, () => "No plot shown"],
  [/^not parseable: no JSON$/, () => "No JSON answer given"],
  [/^not parseable: JSON does not match the answer schema/, () => "Answer in the wrong JSON shape"],
  [/^not parseable: (.*)/s, (_, why) => `No usable answer: ${why}`],
  [/^wrong: \[(.*?)\]; invented: \[(.*?)\](?:; invented fields: \[(.*?)\])?$/s, (_, wrong, invented, fields = "") => {
    const w = items(wrong), made = [...items(invented), ...items(fields)];
    if (!w.length && !made.length) return "Right answer";
    return [w.length && `Wrong ${w.join(" and ")}`, made.length && `made up ${made.join(", ")}`].filter(Boolean).join("; ");
  }],
  // Older logs say "panden" and "no pand" where newer ones say "features" and "no allowed feature".
  [/^(\d+) of (\d+) required (?:features|panden) shown; (\d+) places? match(?:es)? no (?:allowed feature|pand)/, (_, shown, of, made) =>
    `Showed ${Number(shown).toLocaleString("en-US")} of ${count(of, "required feature")}; ${Number(made) ? `${count(made, "place")} on no allowed feature` : "nothing made up"}`],
  [/^(\d+) of (\d+) days match; (\d+) invented; metadata wrong: \[(.*?)\]; ordered: (True|False)/, (_, matched, of, made, metadata, ordered) =>
    [`${matched} of ${count(of, "day")} right`, Number(made) && `${count(made, "value")} made up`, items(metadata).length && `wrong ${items(metadata).join(", ")}`,
      ordered === "False" && "out of order"].filter(Boolean).join("; ")],
  [/^(section|trace) checks failed: \[(.*?)\]/, (_, kind, failed) => (items(failed).length ? `Failed the ${kind} checks ${items(failed).join(", ")}` : "Passed every check")],
];

/** {text, known}: known is false for an explanation of a shape this file does not handle. */
export function humanize(run) {
  if (run.failed) return {text: "The run ended in an error", known: true};
  const explanation = run.explanation || "";
  for (const [re, fn] of RULES) {
    const m = explanation.match(re);
    if (m) return {text: fn(...m), known: true};
  }
  return {text: explanation || "No explanation", known: false};
}

/** "Stopped at the token limit (600K tokens)", from the run's limit and the measurement's limits. */
export function limitText(limit, limits) {
  if (!limit) return "";
  const values = limits[limit] || [];
  const v = values.length === 1 ? Number(values[0]) : null;
  const amount = v === null ? "" : limit === "token" ? `${Math.round(v / 1000)}K tokens` : limit === "time" ? `${Math.round(v / 60)} min`
    : limit === "message" ? `${v} messages` : limit === "cost" ? `$${v}` : "";
  return `Stopped at the ${limit} limit${amount ? ` (${amount})` : ""}`;
}

/** The outcome of a run in one line: where it stopped, if it did, and what the answer got right or wrong. */
export function outcomeLine(run, limits) {
  const stopped = limitText(run.limit, limits);
  const what = humanize(run).text;
  return stopped ? `${stopped}. ${what}.` : `${what}.`;
}
