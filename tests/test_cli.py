"""The documented commands through the real command line, so registry names and -T parsing are covered."""

import os
import subprocess

from inspect_ai.log import read_eval_log


def run(*args, cwd=None):
    # Without the pytest marker in the environment, Inspect records the git commit as it does for a real run.
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
    return subprocess.run(["uv", "run", "--no-sync", *args], capture_output=True, text=True, cwd=cwd, timeout=300, env=env)


def test_airco_task_from_the_command_line_with_a_numeric_variant(tmp_path):
    result = run(
        "inspect",
        "eval",
        "airco_harness/airco",
        "-T",
        "variant=0",
        "-T",
        "ids=imgeo-G04-03",
        "-T",
        "message_limit=4",
        "--model",
        "mockllm/model",
        "--log-dir",
        str(tmp_path),
        "--display",
        "none",
    )
    assert result.returncode == 0, result.stderr[-2000:]
    [log] = tmp_path.glob("*.eval")
    assert read_eval_log(str(log), header_only=True).eval.revision.type == "git"


def test_report_on_an_empty_folder_is_a_clear_error(tmp_path):
    result = run("airco-report", str(tmp_path))
    assert result.returncode == 2
    assert "no samples in .eval logs" in result.stderr
