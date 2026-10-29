// The statistics of the site, the same as airco-report's: the sample is the unit of analysis.
// A metric is first averaged over the epochs of each sample, then the mean and the standard error are taken over
// the samples. A run with an error is left out; a run at a limit counts with the scores it got (0 where it got none).
// tests/test_site_stats.py checks these functions against airco_harness.report.summary.

export const QUALITY = ["correct", "complete", "invented", "parseable", "source"];
export const TRAJECTORY = ["tool_calls", "tokens", "total_time_s"];

const mean = values => values.reduce((a, b) => a + b, 0) / values.length;

/** Mean, standard error (null below two samples) and number of samples of a list of per-sample values. */
export function summary(values) {
  const v = values.filter(x => x !== null && x !== undefined && !Number.isNaN(x));
  if (!v.length) return {mean: null, se: null, n: 0};
  const m = mean(v);
  if (v.length < 2) return {mean: m, se: null, n: 1};
  const sd = Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / (v.length - 1));
  return {mean: m, se: sd / Math.sqrt(v.length), n: v.length};
}

/** Per sample, the mean of a metric over the epochs of the runs that did not fail: Map(sample -> mean). */
export function perSample(runs, metric) {
  const bySample = new Map();
  for (const r of runs) {
    if (r.failed) continue;
    const value = r[metric];
    if (value === null || value === undefined) continue;
    if (!bySample.has(r.sample)) bySample.set(r.sample, []);
    bySample.get(r.sample).push(value);
  }
  return new Map([...bySample].map(([sample, values]) => [sample, mean(values)]));
}

/** The summary of a metric over runs, optionally only over the given samples. */
export function aggregate(runs, metric, samples = null) {
  const values = [...perSample(runs, metric)].filter(([sample]) => !samples || samples.has(sample)).map(([, v]) => v);
  return summary(values);
}

/** Runs grouped by a key function, in first-seen order: Map(key -> runs). */
export function groupBy(runs, key) {
  const groups = new Map();
  for (const r of runs) {
    const k = key(r);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(r);
  }
  return groups;
}

/** The samples every group has a completed run of: the fair base for comparing the groups. */
export function commonSamples(groups) {
  const sets = groups.map(runs => new Set(runs.filter(r => !r.failed).map(r => r.sample)));
  if (!sets.length) return new Set();
  return new Set([...sets[0]].filter(s => sets.every(set => set.has(s))));
}

/** Dollars per correct run, over all runs including failed ones; null without a correct run or with an unpriced run. */
export function costPerCorrect(runs) {
  const correct = runs.filter(r => !r.failed && r.correct === 1).length;
  if (!correct || runs.some(r => r.cost === null)) return null;
  return runs.reduce((a, r) => a + r.cost, 0) / correct;
}
