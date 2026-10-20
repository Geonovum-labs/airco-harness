"""The airco task end to end with a scripted mock model: logging, metadata and scores, without keys or network."""

import json

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelCost, ModelOutput, get_model, get_model_info

from airco_harness import models
from airco_harness.tasks import airco

ANSWER = {"objecttype": "OverigBouwwerk", "type": "bassin"}


def text_model(*texts):
    return get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", t) for t in texts])


def run(tmp_path, model, **kwargs):
    [log] = eval(airco(ids="imgeo-G04-03", **kwargs), model=model, log_dir=str(tmp_path), display="none")
    return log


def test_variant_0_is_the_question_alone(tmp_path):
    """No system prompt, no tools, no submit: the last assistant message is the answer."""
    log = run(tmp_path, text_model(json.dumps(ANSWER)))
    [sample] = log.samples
    assert [m.role for m in sample.messages] == ["user", "assistant"]
    assert sample.messages[0].text.startswith("Een openluchtzwembad")
    assert (sample.output.completion, sample.scores["quality"].value["correct"], sample.scores["source"].value) == (json.dumps(ANSWER), 1, {"source": 0})


def test_run_metadata_names_test_set_variant_and_agent(tmp_path):
    # Inspect records the git commit too, but not under pytest; test_cli covers that.
    log = run(tmp_path, text_model("{}"))
    m = log.eval.metadata
    assert m["testset"] == {"name": "imgeo", "version": "0.3"}
    assert (m["setup"], m["agent"], m["variant"]) == (1, "model", "0")
    assert (log.eval.task_args["variant"], log.eval.task_args["agent"]) == ("0", "model")


def test_a_wrong_or_unreadable_answer_is_scored_not_failed(tmp_path):
    log = run(tmp_path, text_model("I do not know"))
    [sample] = log.samples
    assert (sample.error, sample.scores["quality"].value) == (None, {"correct": 0, "complete": 0.0, "invented": 0, "parseable": 0})


def test_a_model_that_calls_a_tool_it_does_not_have_hits_the_message_limit(tmp_path):
    outputs = [ModelOutput.for_tool_call("mockllm/model", "WebFetch", {"url": "https://docs.geostandaarden.nl/imgeo/catalogus/bgt/"})] * 10
    log = run(tmp_path, get_model("mockllm/model", custom_outputs=outputs), message_limit=6)
    [sample] = log.samples
    assert (sample.error, sample.limit.type, sample.scores["quality"].value["correct"], sample.scores["source"].value["source"]) == (None, "message", 0, 0)


def test_unknown_variant_agent_sample_or_test_set():
    with pytest.raises(ValueError, match="unknown variant '0a'; choose from 0"):
        airco(variant="0a")
    with pytest.raises(ValueError, match="unknown agent 'react'"):
        airco(agent="react")
    assert [s.id for s in airco(ids=" imgeo-G04-03 ,").dataset] == ["imgeo-G04-03"]
    with pytest.raises(ValueError, match="unknown sample ids: imgeo-G99-01"):
        airco(ids="imgeo-G04-03,imgeo-G99-01")
    with pytest.raises(ValueError, match="unknown test set 'nl-sbb'; choose from imgeo"):
        airco(testset="nl-sbb")


def test_price_file_registers_a_model_inspect_does_not_know(tmp_path):
    prices = tmp_path / "model-costs.yaml"
    prices.write_text("test/custom: {input: 1, output: 2, input_cache_write: 3, input_cache_read: 4}\n", encoding="utf-8")
    models.register_costs(prices)
    assert get_model_info("test/custom").cost == ModelCost(input=1, output=2, input_cache_write=3, input_cache_read=4)


def test_price_file_named_in_env_file_is_used(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("AIRCO_MODEL_COSTS=prices/other.yaml\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AIRCO_MODEL_COSTS", raising=False)
    assert models.costs_file() == tmp_path / "prices" / "other.yaml"


def test_relative_price_file_is_read_next_to_env(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    monkeypatch.chdir(tmp_path / "sub")
    monkeypatch.setenv("AIRCO_MODEL_COSTS", "model-costs.yaml")
    assert models.costs_file() == tmp_path / "model-costs.yaml"


def test_claude_code_sandbox_has_the_network_on_and_the_fetch_preflight_off():
    """Inspect's default sandbox has no network, and behind the bridge Claude Code's WebFetch preflight cannot reach Anthropic."""
    import yaml

    from airco_harness import claude_code
    from airco_harness.tasks import SANDBOX_COMPOSE

    service = yaml.safe_load(SANDBOX_COMPOSE.read_text(encoding="utf-8"))["services"]["default"]
    assert (service["image"], service["network_mode"]) == ("aisiuk/inspect-tool-support", "bridge")
    assert claude_code.SETTINGS == {"skipWebFetchPreflight": True}
    assert claude_code.CLAUDE_CODE_VERSION.count(".") == 2
