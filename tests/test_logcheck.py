import json
import sys
from pathlib import Path

import pytest
from inspect_ai import Task, eval
from inspect_ai.dataset import Sample
from inspect_ai.log import read_eval_log
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


def test_google_key_in_a_map_url_from_a_web_search_is_not_a_finding(tmp_path):
    """A provider's web search returns the thumbnail of a page that embeds a Google map, with the site's public browser key."""
    site_key, leaked_key = "AIza" + "B" * 35, "AIza" + "C" * 35
    thumbnail = f"https://maps.google.com/maps/api/staticmap?center=51.95%2C5.87&amp;zoom=10&amp;sensor=false&amp;key={site_key}"
    (tmp_path / "log.json").write_text(json.dumps({"thumbnail": thumbnail, "leak": f"GOOGLE_KEY={leaked_key}"}), encoding="utf-8")
    assert hits(tmp_path) == [f"api key {leaked_key}"]


def test_image_name_with_a_pixel_density_is_not_an_email(tmp_path):
    (tmp_path / "page.md").write_text("![](/img/stamkaart_1@2x.webp) mail huren@example.nl", encoding="utf-8")
    assert hits(tmp_path) == ["email huren@example.nl"]


def test_mask_emails_replaces_addresses_in_a_log_and_keeps_the_rest(tmp_path):
    page = "Contact: info@sportbedrijfarnhem.nl, or imgeo@geonovum.nl for the standard. Tel 026 123."
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", f"I read: {page}")])
    [log] = eval(Task(dataset=[Sample(input=page)], solver=generate()), model=model, log_dir=str(tmp_path), display="none")
    path = Path(log.location)
    assert hits(path) == ["email info@sportbedrijfarnhem.nl"]

    assert logcheck.mask_emails(path) > 2  # in the input, the answer, the events, the journal and the summaries
    assert hits(path) == []
    [sample] = read_eval_log(str(path)).samples
    assert sample.output.completion == "I read: Contact: [email removed], or imgeo@geonovum.nl for the standard. Tel 026 123."
    assert logcheck.mask_emails(path) == 0


def test_mask_emails_in_a_json_file(tmp_path):
    listing = tmp_path / "listing.json"
    listing.write_text(json.dumps({"a": ["x@example.nl", "huren@geldersepoort.nl"]}), encoding="utf-8")
    assert logcheck.mask_emails(listing) == 1
    assert json.loads(listing.read_text(encoding="utf-8")) == {"a": ["[email removed]", "huren@geldersepoort.nl"]}
