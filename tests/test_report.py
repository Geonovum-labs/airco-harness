"""Report, rescore and the matrix cost guard on real logs from scripted mock models."""

import json
import math
import sys
from pathlib import Path

import pytest
from inspect_ai import eval
from inspect_ai.log import EvalRevision, read_eval_log, write_eval_log
from inspect_ai.model import ModelOutput, get_model

from airco_harness import matrix, report, rescore
from airco_harness.tasks import airco

GOOD = json.dumps({"objecttype": "OverigBouwwerk", "type": "bassin"})
SAMPLE = "imgeo-G04-03"
PAGE = "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/"


def calls(*steps):
    return get_model("mockllm/model", custom_outputs=[ModelOutput.for_tool_call("mockllm/model", name, args) for name, args in steps])


@pytest.fixture(scope="module")
def log_dir(tmp_path_factory):
    """The one sample with a priced mock model, three ways.

    The agent model answers correctly in two epochs (variant 0, task version 0.1); then it answers
    something unreadable; then it keeps calling a tool it does not have until the message limit.
    The last two run as separate tasks so that every run has its own row.
    """
    target = tmp_path_factory.mktemp("logs")
    prices = target / "prices.yaml"
    prices.write_text("mockllm/model: {input: 1000000, output: 1000000, input_cache_write: 0, input_cache_read: 0}\n", encoding="utf-8")
    mp = pytest.MonkeyPatch()
    mp.setenv("AIRCO_MODEL_COSTS", str(prices))
    good = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", GOOD), ModelOutput.from_content("mockllm/model", GOOD)])
    unreadable = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", "I do not know")])
    looping = calls(*[("WebFetch", {"url": PAGE})] * 10)
    for model, epochs, message_limit in [(good, 2, 60), (unreadable, 1, 60), (looping, 1, 6)]:
        task = airco(ids=SAMPLE, message_limit=message_limit, cost_limit=None)
        eval(task, model=model, log_dir=str(target), epochs=epochs, max_samples=1, display="none")
    yield str(target)
    mp.undo()


def test_runs_table(log_dir):
    table = report.runs(log_dir)
    rows = {(r.sample, r.epoch, r.limit, r.parseable): r for r in table.itertuples()}
    assert sorted(rows) == [(SAMPLE, 1, "", 0.0), (SAMPLE, 1, "", 1.0), (SAMPLE, 1, "message", 0.0), (SAMPLE, 2, "", 1.0)]
    good, unreadable, at_limit = rows[(SAMPLE, 1, "", 1.0)], rows[(SAMPLE, 1, "", 0.0)], rows[(SAMPLE, 1, "message", 0.0)]
    assert [(r.variant, r.agent, r.correct, r.failed, r.tool_calls) for r in (good, unreadable)] == [
        ("0", "model", 1.0, False, 0),
        ("0", "model", 0.0, False, 0),
    ]
    assert (at_limit.failed, at_limit.reason, at_limit.correct, at_limit.tool_calls > 0) == (False, "message", 0.0, True)
    assert all(r.cost > 0 for r in table.itertuples())
    assert good.tokens_input > 0
    assert list(table["retrieved"].unique()) == [""]


def test_retrieved_urls_come_from_the_source_scorer():
    recorded = {PAGE: "authoritative", "https://geonovum.github.io/IMGeo-dev/": "non_authoritative"}
    assert report._retrieved(json.dumps(recorded)) == f"{PAGE} (authoritative); https://geonovum.github.io/IMGeo-dev/ (non_authoritative)"
    assert (report._retrieved(recorded), report._retrieved(None), report._retrieved(float("nan"))) == (report._retrieved(json.dumps(recorded)), "", "")


def test_cost_is_what_inspect_logged_and_unknown_without_a_price():
    assert report._cost(json.dumps({"a/x": {"total_cost": 0.25}, "a/y": {"total_cost": 0.5}})) == 0.75
    assert math.isnan(report._cost(json.dumps({"a/x": {"input_tokens": 10}})))


def test_report_goes_next_to_the_logs_unless_out_says_otherwise(log_dir, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["airco-report", log_dir])
    report.main()
    assert capsys.readouterr().out.strip() == f"4 runs; {Path(log_dir) / 'report' / 'report.md'}"


def as_three_samples_on_one_variant(table):
    """The runs relabeled as three samples, so the summary has more than one sample to average over."""
    labels = table.apply(lambda r: "c" if r["limit"] else "a" if r["parseable"] == 1 else "b", axis=1)
    return table.assign(sample=labels)


def test_summary_averages_epochs_per_sample_and_counts_a_run_at_a_limit_as_wrong(log_dir):
    table = as_three_samples_on_one_variant(report.runs(log_dir))
    [row] = report.summary(table).to_dict("records")
    assert (row["samples"], row["runs"], row["failed"], row["limit"]) == (3, 4, 0, 1)
    assert (row["correct"], row["correct_se"], row["parseable"]) == (pytest.approx(1 / 3), pytest.approx(1 / 3), pytest.approx(1 / 3))
    assert row["cost_per_correct"] == pytest.approx(table["cost"].sum() / 2)


def test_summary_leaves_out_a_run_with_an_error(log_dir):
    table = as_three_samples_on_one_variant(report.runs(log_dir))
    table.loc[table["sample"] == "c", ["failed", "limit"]] = [True, ""]
    [row] = report.summary(table).to_dict("records")
    assert (row["samples"], row["runs"], row["failed"], row["limit"], row["correct"]) == (3, 4, 1, 0, 0.5)


def test_markdown_shows_means_and_failed_runs_without_na(log_dir):
    text = report.markdown(as_three_samples_on_one_variant(report.runs(log_dir)), log_dir)
    assert "| mockllm/model | model | 0 | 3 | 4 | 0 | 1 | 0.33 (0.33) |" in text
    assert "| mockllm/model | model | 0 | c | 1 | message |" in text
    assert f"| mockllm/model | model | 0 | {SAMPLE} | 1 | message |" in report.markdown(report.runs(log_dir), log_dir)
    assert "<NA>" not in text and "nan" not in text


def test_csv_columns_are_in_a_fixed_order(log_dir):
    columns = list(report.runs(log_dir).columns)
    assert columns[-5:] == ["correct", "complete", "invented", "parseable", "source"]


def test_report_on_logs_where_nothing_was_scored(tmp_path):
    eval(airco(ids=SAMPLE), model=calls(), log_dir=str(tmp_path), display="none")
    table = report.runs(str(tmp_path))
    assert (len(table), bool(table["failed"].all()), math.isnan(table["correct"][0])) == (1, True, True)
    assert "no completed runs" in report.markdown(table, str(tmp_path))


def first_log(log_dir):
    """The log whose runs are all correct; file names alone do not fix the order within one second."""
    return next(p for p in sorted(Path(log_dir).glob("*.eval")) if all(s.scores["quality"].value["correct"] == 1 for s in read_eval_log(str(p)).samples))


def test_rescore_reproduces_and_a_changed_score_is_caught(log_dir, tmp_path):
    log = read_eval_log(str(first_log(log_dir)))
    rescored, _ = rescore.rescore(log, str(tmp_path), "rescore.eval")
    assert rescore.compare_scores(rescore.scores_of(log), rescore.scores_of(rescored)) == []
    sample = rescored.samples[0]
    sample.scores["quality"].value = {**sample.scores["quality"].value, "correct": 0}
    expected = f"('{sample.id}', {sample.epoch}, 'quality', 'correct'): 1 -> 0"
    assert rescore.compare_scores(rescore.scores_of(log), rescore.scores_of(rescored)) == [expected]


def test_comparison_treats_nan_extra_keys_text_and_empty_logs_as_problems():
    key = ("s", 1, "quality", "correct")
    assert rescore.compare_scores({key: 1.0}, {key: float("nan")}) == [f"{key}: 1.0 -> nan"]
    assert rescore.compare_scores({key: float("nan")}, {key: float("nan")}) == []
    assert rescore.compare_scores({key: 1}, {key: 1, ("s", 1, "x", "y"): 0}) == ["only in rescore: ('s', 1, 'x', 'y')"]
    assert rescore.compare_scores({key: "C"}, {key: "I"}) == [f"{key}: C -> I"]
    assert rescore.compare_scores({}, {key: 1}) == ["the original log has no scores to compare"]


def test_rescore_cli_warns_when_the_checkout_is_not_the_commit_of_the_run(log_dir, tmp_path, monkeypatch, capsys):
    path = tmp_path / "old.eval"
    log = read_eval_log(str(first_log(log_dir)))
    log.eval.revision = EvalRevision(type="git", origin="", commit="0000000", dirty=True)
    write_eval_log(log, str(path))
    monkeypatch.setattr(sys, "argv", ["airco-rescore", str(path), "--out", str(tmp_path / "out")])
    with pytest.raises(SystemExit) as stop:
        rescore.main()
    out = capsys.readouterr()
    assert stop.value.code == 0
    assert "the run was made with uncommitted changes" in out.err
    assert "the run was made at commit 0000000, this checkout is at" in out.err
    assert "scores equal within 0.0" in out.out


def test_matrix_refuses_paid_models_without_yes(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["airco-matrix", "--models", "anthropic/claude-haiku-5-5", "--ids", SAMPLE, "--epochs", "3"])
    with pytest.raises(SystemExit) as stop:
        matrix.main()
    assert stop.value.code == 2
    out = capsys.readouterr()
    assert "1 samples x 1 agent-model pairs x 3 epochs = 3 runs" in out.out
    assert "at most 3 x 0.50 = 1.50 dollars" in out.out
    assert "rerun with --yes" in out.err


def test_bundle_index_keeps_no_absolute_log_dir(tmp_path):
    (tmp_path / "index.html").write_text('<script>{"log_dir": "logs", "abs_log_dir": "/Users/someone/airco-harness/logs/x"}</script>', encoding="utf-8")
    matrix.strip_absolute_log_dir(tmp_path, Path("logs/x"))
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == '<script>{"log_dir": "logs", "abs_log_dir": "logs/x"}</script>'


def test_a_map_question_gets_correct_and_complete_per_sample_and_a_line_per_run(log_dir):
    table = report.runs(log_dir)
    first = table.index[0]
    table.loc[first, ["rule", "explanation", "complete"]] = ["map", "42 of 61 required panden shown; 0 places match no pand", 0.69]
    text = report.markdown(table, log_dir)
    assert "## `correct` / `complete` per sample (mean over epochs)" in text
    assert "## Map questions per run" in text
    assert f"| mockllm/model | model | 0 | {SAMPLE} | 1 | 42 of 61 required panden shown; 0 places match no pand | nothing |" in text
    assert "## Map questions" not in report.markdown(report.runs(log_dir), log_dir)


def test_hosts_are_listed_once_with_their_class():
    retrieved = {"https://api.pdok.nl/a": "authoritative", "https://nominatim.openstreetmap.org/x": "other", "https://api.pdok.nl/b": "authoritative"}
    assert report._hosts(retrieved) == "api.pdok.nl (authoritative), nominatim.openstreetmap.org (other)"
    assert report._hosts(None) == ""
