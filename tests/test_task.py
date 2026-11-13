"""The airco task end to end with a scripted mock model: logging, metadata and scores, without keys or network."""

import json
import re
import sys
from pathlib import Path

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelCost, ModelOutput, get_model, get_model_info

from airco_harness import models, tasks
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
    with pytest.raises(ValueError, match="unknown variant '0a'; choose from 0, mcp-groundwater-monitoring, mcp-bag-ldproxy"):
        airco(variant="0a")
    with pytest.raises(ValueError, match="unknown agent 'react'"):
        airco(agent="react")
    assert [s.id for s in airco(ids=" imgeo-G04-03 ,").dataset] == ["imgeo-G04-03"]
    with pytest.raises(ValueError, match="unknown sample ids: imgeo-G99-01"):
        airco(ids="imgeo-G04-03,imgeo-G99-01")
    assert [s.id for s in airco(testset="dsfl").dataset] == [f"dsfl-{n:02}" for n in range(1, 16)]
    with pytest.raises(ValueError, match="unknown test set 'nl-sbb'; choose from dsfl, imgeo"):
        airco(testset="nl-sbb")


def test_tags_select_the_samples_with_one_of_them():
    assert [s.id for s in airco(testset="dsfl", tags="bro").dataset] == [f"dsfl-{n:02}" for n in range(6, 16)]
    assert [s.id for s in airco(testset="dsfl", tags="bro,bag").dataset] == [f"dsfl-{n:02}" for n in range(1, 16)]
    assert [s.id for s in airco(testset="dsfl", tags="bro", ids="dsfl-01,dsfl-06").dataset] == ["dsfl-06"]
    assert airco(testset="dsfl", tags="bro").dataset[0].metadata["tags"] == ["bro", "groundwater"]
    assert [s.id for s in airco(testset="dsfl", tags="subsurface").dataset] == [f"dsfl-{n:02}" for n in range(9, 16)]
    assert [s.id for s in airco(testset="dsfl", tags="groundwater").dataset] == ["dsfl-06", "dsfl-07", "dsfl-08"]
    assert [s.id for s in airco(testset="dsfl", tags="bag,groundwater").dataset] == [f"dsfl-{n:02}" for n in range(1, 9)]


GROUNDWATER = "mcp-groundwater-monitoring"


def test_a_variant_runs_the_samples_it_is_made_for_unless_ids_or_tags_choose_others():
    assert [s.id for s in airco(testset="dsfl", variant=GROUNDWATER, agent="inspect").dataset] == ["dsfl-06", "dsfl-07", "dsfl-08"]
    assert [s.id for s in airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-01").dataset] == ["dsfl-01"]
    assert len(airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", tags="bag").dataset) == 5
    with pytest.raises(ValueError, match="no samples of test set imgeo for variant mcp-groundwater-monitoring"):
        airco(variant=GROUNDWATER, agent="inspect")


@pytest.mark.parametrize(("variant", "agent"), [(GROUNDWATER, "model"), (GROUNDWATER, "claude-code"), ("mcp-bag-ldproxy", "model")])
def test_an_mcp_variant_refuses_an_agent_that_cannot_reach_its_server(variant, agent):
    with pytest.raises(ValueError, match=f"the agent {agent} does not take the MCP server of variant {variant}"):
        airco(testset="dsfl", variant=variant, agent=agent)


def test_claude_code_reaches_an_http_server_under_the_name_a_user_would_give_it():
    from airco_harness import claude_code

    assert tasks.takes("mcp-bag-ldproxy", "claude-code") and not tasks.takes(GROUNDWATER, "claude-code")
    assert claude_code.server_name("https://bag.ldproxy.net/bag/mcp") == "bag"
    assert len(airco(testset="dsfl", variant="mcp-bag-ldproxy", agent="claude-code").dataset) == 5


def test_an_mcp_variant_gives_the_server_tools_under_names_the_model_apis_accept(tmp_path, monkeypatch):
    """The stub server names its tool groundwater-monitoring.series.get, as the real one does; Anthropic refuses a dot in a tool name."""
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(sys.executable, str(stub)), tags=("bro",)))
    outputs = [
        ModelOutput.for_tool_call(
            "mockllm/model", "groundwater-monitoring_series_get", {"gldBroId": "GLD000000025798", "from": "2026-09-21", "to": "2026-09-21"}
        ),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": json.dumps({"value": 2.13, "unit": "m", "reference_plane": "NAP"})}),
    ]
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=outputs), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    [result] = [m for m in sample.messages if m.role == "tool"]
    assert result.function == "groundwater-monitoring_series_get"
    payload = json.loads(result.text)
    assert payload["segments"][0]["gldBroId"] == "GLD000000025798"
    assert payload["window"] == {"from": "2026-09-21", "to": "2026-09-21", "total": 1, "returned": 1, "truncated": False}
    assert sample.scores["quality"].value["correct"] == 1
    assert log.eval.metadata["variant_form"] == {"about": "stub", "mcp": [sys.executable, str(stub)], "tags": ["bro"]}
    [system] = [m for m in sample.messages if m.role == "system"]
    assert "## stub-groundwater-monitoring\nCall groundwater-monitoring.series.get for a level." in system.text
    assert "You are a helpful assistant attempting to submit the best possible answer" in system.text


def test_an_mcp_run_records_the_server_that_answered_initialize(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(sys.executable, str(stub)), tags=("bro",)))
    submit = ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "{}"})
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=[submit]), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    recorded = sample.store["mcp_server"]
    assert recorded["name"] == "stub-groundwater-monitoring"
    assert recorded["version"] == "1.2.3"


def test_variant_0_records_no_server(tmp_path):
    [sample] = run(tmp_path, text_model(json.dumps(ANSWER))).samples
    assert "mcp_server" not in sample.store


def test_a_server_without_instructions_leaves_the_prompt_of_variant_0():
    assert tasks.server_instructions("bag", None) is None and tasks.server_instructions("bag", "") is None


def test_plot_tool_is_available_alongside_the_mcp_server(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(sys.executable, str(stub)), tags=("bro",)))
    expected = json.loads((tasks.dataset.TESTSETS_DIR / "dsfl/samples/dsfl-08/expected.json").read_text(encoding="utf-8"))
    data = {
        "points": [{"date": date, "value": value} for date, value in expected["points"].items()],
        "unit": "m",
        "reference_plane": "NAP",
        "connect_gaps": False,
    }
    outputs = [
        ModelOutput.for_tool_call(
            "mockllm/model", "groundwater-monitoring_series_get", {"gldBroId": "GLD000000025798", "from": "2026-09-21", "to": "2026-09-21"}
        ),
        ModelOutput.for_tool_call("mockllm/model", "plot_series", {"data": data}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "Zie de grafiek."}),
    ]
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-08")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=outputs), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    assert [m.function for m in sample.messages if m.role == "tool"] == ["groundwater-monitoring_series_get", "plot_series"]
    assert sample.scores["quality"].value["correct"] == 1


def test_samples_that_run_at_the_same_time_each_get_their_own_server(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(sys.executable, str(stub)), tags=("bro",)))
    call = ModelOutput.for_tool_call(
        "mockllm/model", "groundwater-monitoring_series_get", {"gldBroId": "GLD000000025798", "from": "2026-09-21", "to": "2026-09-21"}
    )
    submit = ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "{}"})

    def script(messages, *_):
        # Each sample follows its own conversation; a shared list would depend on how the samples interleave.
        return submit if any(m.role == "tool" for m in messages) else call

    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06,dsfl-07")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=script), log_dir=str(tmp_path), display="none", max_samples=2)
    assert log.status == "success"
    results = [[json.loads(m.text) for m in s.messages if m.role == "tool"] for s in log.samples]
    assert [len(r) for r in results] == [1, 1]
    assert all(r[0]["window"]["truncated"] is False for r in results)


def test_local_groundwater_server_uses_utf8_and_records_resolved_command(tmp_path, monkeypatch):
    jar = tmp_path / "server.jar"
    jar.touch()
    monkeypatch.setenv("AIRCO_GROUNDWATER_MCP_JAR", str(jar))
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    assert task.metadata["variant_form"]["mcp"] == ("java", "-Dstdout.encoding=UTF-8", "-jar", str(jar))
    monkeypatch.setenv("AIRCO_GROUNDWATER_MCP_JAR", str(tmp_path / "missing.jar"))
    with pytest.raises(ValueError, match="AIRCO_GROUNDWATER_MCP_JAR is not a file"):
        airco(testset="dsfl", variant=GROUNDWATER, agent="inspect")


def test_the_groundwater_variant_runs_a_pinned_image():
    command = tasks.VARIANTS[GROUNDWATER].mcp
    assert command[:-1] == ("docker", "run", "-i", "--rm", "--platform", "linux/amd64", "-e", "QUARKUS_PROFILE=prod")
    assert re.fullmatch(r"ghcr\.io/sjaakd/mcp-groundwater-monitoring@sha256:[0-9a-f]{64}", command[-1])
    assert command[-1].endswith("sha256:ebbce9d90a7bdefca2e19178ccb108dae54c9894d2ae38cace38270187434344")


def test_the_bag_variant_reaches_its_server_over_http_and_runs_the_bag_samples():
    assert tasks.VARIANTS["mcp-bag-ldproxy"].mcp == "https://bag.ldproxy.net/bag/mcp"
    assert [s.id for s in airco(testset="dsfl", variant="mcp-bag-ldproxy", agent="inspect").dataset] == [f"dsfl-0{n}" for n in range(1, 6)]


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
