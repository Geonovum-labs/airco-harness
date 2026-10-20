import json
import sys

import pytest
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.solver import generate

from airco_harness import logcheck

KEY = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV"


def hits(path):
    return sorted(h.split(": ", 1)[1] for h in logcheck.scan(str(path)))


def test_flags_keys_mail_and_home_paths_but_not_known_placeholders(tmp_path, monkeypatch):
    monkeypatch.setenv("EXAMPLE_API_KEY", "secret-123456789")
    (tmp_path / "a.json").write_text(
        json.dumps(
            {
                "env": "secret-123456789",
                "key": f"line one\n{KEY}",
                "mail": "someone@example.org",
                "contact": "see\nimgeo@geonovum.nl",
                "path": "/Users/someone",
                "windows": "C:\\Users\\someone\\airco",
            }
        )
    )
    assert hits(tmp_path) == [
        f"api key {KEY}",
        "email someone@example.org",
        "home path /Users/someone",
        "home path C:\\Users\\someone",
        "value of EXAMPLE_API_KEY",
    ]


def test_finds_a_key_on_its_own_line_inside_an_eval_log(tmp_path):
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", f"output of cat:\n{KEY}\n")])
    eval(Task(dataset=[Sample(input="x")], solver=generate()), model=model, log_dir=str(tmp_path), display="none")
    assert f"api key {KEY}" in hits(tmp_path)


def test_unreadable_log_is_reported_and_the_rest_is_still_scanned(tmp_path):
    (tmp_path / "broken.eval").write_bytes(b"PK\x03\x04 truncated")
    (tmp_path / "b.md").write_text(f"leak: {KEY}", encoding="utf-8")
    found = hits(tmp_path)
    assert found[0] == f"api key {KEY}"
    assert found[1].startswith("unreadable, not checked")


def test_missing_path_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["airco-logcheck", str(tmp_path / "does-not-exist")])
    with pytest.raises(SystemExit) as stop:
        logcheck.main()
    assert stop.value.code == 2


def test_home_path_in_a_traceback_of_the_virtualenv_is_not_a_finding(tmp_path):
    """Inspect writes the traceback of a retried provider error into the log; the frames name the installation, nothing else."""
    traceback = 'Traceback (most recent call last):\n  File "/Users/someone/work/airco-harness/.venv/lib/python3.15/site-packages/inspect_ai/x.py", line 1'
    (tmp_path / "log.json").write_text(json.dumps({"traceback": traceback, "note": "see /Users/someone/notes.txt"}), encoding="utf-8")
    assert hits(tmp_path) == ["home path /Users/someone"]
