"""The airco task end to end with a scripted mock model: logging, metadata and scores, without keys or network."""

import json
import re
import sys
from pathlib import Path

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelCost, ModelOutput, ModelUsage, get_model, get_model_info

from airco_harness import mcpwire, models, report, tasks
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
    assert [s.id for s in airco(testset="dsfl").dataset] == [f"dsfl-{n:02}" for n in range(1, 17)]
    with pytest.raises(ValueError, match="unknown test set 'nl-sbb'; choose from dsfl, imgeo"):
        airco(testset="nl-sbb")


def test_tags_select_the_samples_with_one_of_them():
    assert [s.id for s in airco(testset="dsfl", tags="bro").dataset] == [f"dsfl-{n:02}" for n in range(6, 17)]
    assert [s.id for s in airco(testset="dsfl", tags="bro,bag").dataset] == [f"dsfl-{n:02}" for n in range(1, 17)]
    assert [s.id for s in airco(testset="dsfl", tags="bro", ids="dsfl-01,dsfl-06").dataset] == ["dsfl-06"]
    assert airco(testset="dsfl", tags="bro").dataset[0].metadata["tags"] == ["bro", "groundwater"]
    assert [s.id for s in airco(testset="dsfl", tags="subsurface").dataset] == [f"dsfl-{n:02}" for n in range(9, 17)]
    assert [s.id for s in airco(testset="dsfl", tags="groundwater").dataset] == ["dsfl-06", "dsfl-07", "dsfl-08"]
    assert [s.id for s in airco(testset="dsfl", tags="bag,groundwater").dataset] == [f"dsfl-{n:02}" for n in range(1, 9)]


GROUNDWATER = "mcp-groundwater-monitoring"


def test_a_variant_runs_the_samples_it_is_made_for_unless_ids_or_tags_choose_others():
    assert [s.id for s in airco(testset="dsfl", variant=GROUNDWATER, agent="inspect").dataset] == ["dsfl-06", "dsfl-07", "dsfl-08"]
    assert [s.id for s in airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-01").dataset] == ["dsfl-01"]
    assert len(airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", tags="bag").dataset) == 5
    with pytest.raises(ValueError, match="no samples of test set imgeo for variant mcp-groundwater-monitoring"):
        airco(variant=GROUNDWATER, agent="inspect")


@pytest.mark.parametrize(("variant", "agent"), [(GROUNDWATER, "model"), ("mcp-bag-ldproxy", "model"), ("mcp-bgt-wijkenbuurten-subsurface", "model")])
def test_an_mcp_variant_refuses_an_agent_that_cannot_reach_its_server(variant, agent):
    with pytest.raises(ValueError, match=f"the agent {agent} does not take the MCP servers or skills of variant {variant}"):
        airco(testset="dsfl", variant=variant, agent=agent)


def test_claude_code_reaches_an_http_server_under_the_name_a_user_would_give_it():
    assert tasks.takes("mcp-bag-ldproxy", "claude-code") and tasks.takes(GROUNDWATER, "claude-code")
    assert [s.name for s in tasks.VARIANTS["mcp-bag-ldproxy"].mcp] == ["bag"]
    assert len(airco(testset="dsfl", variant="mcp-bag-ldproxy", agent="claude-code").dataset) == 5


def test_an_mcp_variant_gives_the_server_tools_under_names_the_model_apis_accept(tmp_path, monkeypatch):
    """The stub server names its tool groundwater-monitoring.series.get, as the real one does; Anthropic refuses a dot in a tool name."""
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(
        tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(tasks.McpServer("groundwater-monitoring", command=(sys.executable, str(stub))),), tags=("bro",))
    )
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
    assert log.eval.metadata["variant_form"] == {
        "about": "stub",
        "mcp": [{"name": "groundwater-monitoring", "url": "", "command": [sys.executable, str(stub)], "image": "", "version": ""}],
        "skills": [],
        "tags": ["bro"],
    }
    [system] = [m for m in sample.messages if m.role == "system"]
    assert "## stub-groundwater-monitoring\nCall groundwater-monitoring.series.get for a level." in system.text
    assert "You are a helpful assistant attempting to submit the best possible answer" in system.text


def test_an_mcp_run_records_the_server_that_answered_initialize(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(
        tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(tasks.McpServer("groundwater-monitoring", command=(sys.executable, str(stub))),), tags=("bro",))
    )
    submit = ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "{}"})
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=[submit]), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    [recorded] = sample.store["mcp_server"]
    assert recorded["name"] == "stub-groundwater-monitoring"
    assert recorded["version"] == "1.2.3"


def test_variant_0_records_no_server(tmp_path):
    [sample] = run(tmp_path, text_model(json.dumps(ANSWER))).samples
    assert "mcp_server" not in sample.store


def test_a_server_without_instructions_leaves_the_prompt_of_variant_0():
    assert tasks.server_instructions([("bag", None)]) is None and tasks.server_instructions([("bag", ""), ("bgt", None)]) is None
    both = tasks.server_instructions([("bgt", "Use the BGT."), ("wijkenbuurten", None), ("subsurface-models", "Use GeoTOP.")])
    assert both.endswith("## bgt\nUse the BGT.\n\n## subsurface-models\nUse GeoTOP.")


def test_plot_tool_is_available_alongside_the_mcp_server(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(
        tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(tasks.McpServer("groundwater-monitoring", command=(sys.executable, str(stub))),), tags=("bro",))
    )
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
    monkeypatch.setitem(
        tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(tasks.McpServer("groundwater-monitoring", command=(sys.executable, str(stub))),), tags=("bro",))
    )
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


@pytest.fixture
def http_stub():
    """The stub server over HTTP on a free port, as a host server runs."""
    import socket
    import subprocess
    import time

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    process = subprocess.Popen([sys.executable, str(Path(__file__).parent / "fixtures" / "stub_mcp_server.py"), str(port)], stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        process.wait()


def test_the_proxy_records_every_mcp_message_of_an_http_server_with_its_protocol_version(tmp_path, monkeypatch, http_stub):
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(tasks.McpServer("groundwater-monitoring", url=http_stub),), tags=("bro",)))
    outputs = [
        ModelOutput.for_tool_call(
            "mockllm/model", "groundwater-monitoring_series_get", {"gldBroId": "GLD000000025798", "from": "2026-09-21", "to": "2026-09-21"}
        ),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": json.dumps({"value": 2.13, "unit": "m", "reference_plane": "NAP"})}),
    ]
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=outputs), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    assert sample.error is None and sample.scores["quality"].value["correct"] == 1
    records = sample.store["mcp_calls"]
    handshake = next(r for r in records if r["method"] == "initialize")
    [call] = [r for r in records if r["method"] == "tools/call"]
    assert (handshake["server"], handshake["agreed"], handshake["server_info"]["version"]) == ("groundwater-monitoring", "2025-11-25", "1.2.3")
    assert (call["tool"], call["protocol"], call["status"]) == ("groundwater-monitoring.series.get", "2025-11-25", 200) and "error" not in call
    [server] = mcpwire.traffic(records)
    assert (server["protocols"], server["tool_calls"], server["errors"], server["handshake"]["method"]) == (["2025-11-25"], 1, 0, "initialize")


def test_a_stdio_server_reaches_the_agent_inspect_only(monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    monkeypatch.setitem(tasks.VARIANTS, "stub", tasks.Variant("stub", mcp=(tasks.McpServer("stub", command=(sys.executable, str(stub))),)))
    assert tasks.takes("stub", "inspect") and not tasks.takes("stub", "claude-code")


def test_the_groundwater_variant_reaches_a_pinned_image_on_the_host_and_its_variable_moves_it(monkeypatch):
    [server] = tasks.VARIANTS[GROUNDWATER].mcp
    assert server.url == "http://localhost:18081/mcp"
    assert re.fullmatch(r"ghcr\.io/sjaakd/mcp-groundwater-monitoring@sha256:[0-9a-f]{64}", server.image)
    assert server.image.endswith("sha256:0f4bd731e90fc2fcf29f0a221f93aa74d5b6c0d40d08a54adff07735a38577ee") and server.version == "1.0.10"
    monkeypatch.setenv("AIRCO_GROUNDWATER_MONITORING_URL", "http://localhost:9001/mcp")
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [moved] = task.metadata["variant_form"]["mcp"]
    assert (moved["url"], moved["version"]) == ("http://localhost:9001/mcp", "1.0.10")


def test_a_server_that_reports_another_version_than_its_pin_fails_the_run(tmp_path, monkeypatch):
    stub = Path(__file__).parent / "fixtures" / "stub_mcp_server.py"
    pinned = tasks.McpServer("groundwater-monitoring", command=(sys.executable, str(stub)), image="stub", version="9.9.9")
    monkeypatch.setitem(tasks.VARIANTS, GROUNDWATER, tasks.Variant("stub", mcp=(pinned,), tags=("bro",)))
    submit = ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "{}"})
    task = airco(testset="dsfl", variant=GROUNDWATER, agent="inspect", ids="dsfl-06")
    [log] = eval(task, model=get_model("mockllm/model", custom_outputs=[submit]), log_dir=str(tmp_path), display="none")
    [sample] = log.samples
    assert "reports version 1.2.3, not 9.9.9 of stub" in sample.error.message


def test_the_bag_variant_reaches_its_server_over_http_and_runs_the_bag_samples():
    assert tasks.VARIANTS["mcp-bag-ldproxy"].mcp == (tasks.McpServer("bag", url="https://bag.ldproxy.net/bag/mcp"),)
    assert [s.id for s in airco(testset="dsfl", variant="mcp-bag-ldproxy", agent="inspect").dataset] == [f"dsfl-0{n}" for n in range(1, 6)]


def test_the_bgt_variant_gives_three_named_servers_one_of_them_on_the_host(monkeypatch):
    variant = "mcp-bgt-wijkenbuurten-subsurface"
    servers = tasks.VARIANTS[variant].mcp
    assert [(s.name, s.url) for s in servers] == [
        ("bgt", "https://bag.ldproxy.net/bgt/mcp"),
        ("wijkenbuurten", "https://bag.ldproxy.net/wijkenbuurten/mcp"),
        ("subsurface-models", "http://localhost:18082/mcp"),
    ]
    assert servers[2].image.endswith("sha256:806d7ff5d58dab50c445dd7f1a4a1208e6b785eadcb759b589f7f66c48b36a2c") and servers[2].version == "1.0.13"
    assert not servers[0].version and not servers[1].version
    assert tasks.takes(variant, "claude-code") and tasks.takes(variant, "inspect") and not tasks.takes(variant, "model")
    assert [s.id for s in airco(testset="dsfl", variant=variant, agent="inspect").dataset] == ["dsfl-16"]
    monkeypatch.setenv("AIRCO_SUBSURFACE_MODELS_URL", "http://localhost:9000/mcp")
    moved = tasks.variant_form(variant).mcp[2]
    assert moved.url == "http://localhost:9000/mcp"


def test_the_dsfl_context_variant_reaches_its_server_over_http_and_has_no_samples_of_its_own_yet():
    variant = "mcp-dsfl-context"
    assert tasks.VARIANTS[variant].mcp == (tasks.McpServer("dsfl-context", url="https://catalog.modeldesk.io/mcp/modeldesk/context"),)
    assert tasks.takes(variant, "inspect") and tasks.takes(variant, "claude-code") and not tasks.takes(variant, "model")
    with pytest.raises(ValueError, match="no samples of test set dsfl for variant mcp-dsfl-context"):
        airco(testset="dsfl", variant=variant, agent="inspect")
    assert [s.id for s in airco(testset="dsfl", variant=variant, agent="claude-code", ids="dsfl-01").dataset] == ["dsfl-01"]


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
    assert service["extra_hosts"] == ["host.docker.internal:host-gateway"]
    assert claude_code.SETTINGS == {"skipWebFetchPreflight": True}
    assert claude_code.CLAUDE_CODE_VERSION.count(".") == 2


HAIKU = models.Price(
    input=0.10,
    output=0.50,
    input_cache_write=0.125,
    input_cache_read=0.01,
    long_prompt=models.LongPrompt(above=100000, input=0.50, output=2.50, input_cache_write=0.625, input_cache_read=0.05),
)


def usage(input, cache_write, cache_read, output, total_cost=None):
    return ModelUsage(
        input_tokens=input,
        input_tokens_cache_write=cache_write,
        input_tokens_cache_read=cache_read,
        output_tokens=output,
        total_tokens=input + output,
        total_cost=total_cost,
    )


def test_a_short_prompt_pays_the_base_rates_as_logged_by_inspect():
    assert HAIKU.call(usage(4, 97484, 0, 396)) == pytest.approx(0.0123839, rel=1e-9)


def test_a_prompt_over_the_threshold_pays_the_long_rates_for_every_token_of_the_call():
    assert HAIKU.call(usage(10, 1000, 120000, 2000)) == pytest.approx(0.01163, rel=1e-9)


def test_the_threshold_is_exclusive_and_counts_cache_tokens():
    assert HAIKU.call(usage(0, 40000, 60000, 0)) == pytest.approx(0.0056)
    assert HAIKU.call(usage(1, 40000, 60000, 0)) == pytest.approx((0.5 + 25000 + 3000) / 1e6)


def test_inspect_gets_the_highest_rates_of_a_model():
    assert HAIKU.ceiling() == ModelCost(input=0.50, output=2.50, input_cache_write=0.625, input_cache_read=0.05)


def test_an_unknown_key_in_a_price_names_the_model_and_the_key(tmp_path):
    prices = tmp_path / "model-costs.yaml"
    prices.write_text("a/x: {input: 1, output: 1, input_cache_write: 1, input_cache_read: 1, long_promt: {above: 1}}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"a/x[\s\S]*long_promt"):
        models.load_prices(prices)


def test_the_shipped_price_file_prices_haiku_in_tiers_and_counts_web_searches():
    prices = models.load_prices(Path(__file__).parent.parent / "model-costs.yaml")
    assert prices["anthropic/claude-haiku-5-5"].ceiling().input == 0.50
    assert [prices[f"anthropic/claude-{m}"].web_search for m in ("haiku-5-5", "sonnet-5-5", "opus-5-5", "fable-5-1")] == [0.01] * 4


def test_a_one_hour_cache_write_is_recovered_from_the_cost_inspect_logged():
    sonnet = models.Price(input=2.00, output=10.00, input_cache_write=2.50, input_cache_read=0.10)
    claude_code_call = usage(2, 26654, 0, 212, total_cost=0.10874)
    assert sonnet.cache_ttl(claude_code_call) == "1h"
    assert sonnet.call(claude_code_call, "1h") == pytest.approx(0.10874, rel=1e-9)
    assert sonnet.cache_ttl(usage(2, 26654, 0, 212, total_cost=0.068759)) == "5m"
    assert sonnet.cache_ttl(usage(2, 26654, 0, 212)) is None


def test_the_ttl_of_a_haiku_call_logged_at_the_ceiling_is_recovered_too():
    logged_at_ceiling = usage(10, 1000, 20000, 100, total_cost=(10 * 0.50 + 1000 * 0.625 * 1.6 + 20000 * 0.05 + 100 * 2.50) / 1e6)
    assert HAIKU.cache_ttl(logged_at_ceiling) == "1h"
    assert HAIKU.call(logged_at_ceiling, "1h") == pytest.approx((10 * 0.10 + 1000 * 0.125 * 1.6 + 20000 * 0.01 + 100 * 0.50) / 1e6)


def test_joined_variants_give_the_servers_and_skills_of_both_on_the_samples_the_mcp_variant_is_made_for():
    form = tasks.compose("mcp-dsfl-context+skill-metadata")
    assert ([s.name for s in form.mcp], [s.name for s in form.skills], form.tags) == (["dsfl-context"], ["metadata"], ("dsfl-context",))
    assert tasks.compose("skill-metadata").tags == ()


@pytest.mark.parametrize("variant", ["skill-metadata+nope", "skill-metadata+skill-metadata", "0+skill-metadata"])
def test_a_join_of_an_unknown_a_repeated_or_the_baseline_variant_is_refused(variant):
    with pytest.raises(ValueError, match=f"unknown variant '{re.escape(variant)}'"):
        airco(variant=variant)


def test_a_skill_variant_refuses_the_agent_without_tools():
    with pytest.raises(ValueError, match="the agent model does not take the MCP servers or skills of variant skill-metadata"):
        airco(variant="skill-metadata", agent="model")


def test_the_inspect_agent_loads_a_skill_with_inspects_skill_tool_and_the_report_counts_it(tmp_path):
    outputs = [
        ModelOutput.for_tool_call("mockllm/model", "skill", {"command": "metadata"}),
        ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": json.dumps(ANSWER)}),
    ]
    log = run(tmp_path, get_model("mockllm/model", custom_outputs=outputs), variant="skill-metadata", agent="inspect")
    [sample] = log.samples
    [loaded] = [m for m in sample.messages if m.role == "tool" and m.function == "skill"]
    assert "<command-name>metadata</command-name>" in loaded.text
    assert "Find the metadata that leads to the right source for the question" in loaded.text
    assert (sample.scores["source"].metadata["skills"], sample.scores["quality"].value["correct"]) == (["metadata"], 1)
    assert log.eval.metadata["variant_form"]["skills"] == [
        {"name": "metadata", "origin": "https://github.com/Bakkej/skills-metadata", "revision": tasks.METADATA_SKILL.revision}
    ]
    [row] = report.runs(str(tmp_path)).to_dict("records")
    assert (row["skills"], row["skill_used"]) == ("metadata", 1.0)


def test_a_run_that_offers_a_skill_and_does_not_load_it_counts_as_not_used(tmp_path):
    outputs = [ModelOutput.for_tool_call("mockllm/model", "submit", {"answer": "{}"})]
    run(tmp_path, get_model("mockllm/model", custom_outputs=outputs), variant="skill-metadata", agent="inspect")
    [row] = report.runs(str(tmp_path)).to_dict("records")
    assert (row["skills"], row["skill_used"]) == ("", 0.0)
