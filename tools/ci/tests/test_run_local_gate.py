from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tools.ci.common import GateError, python_executable
from tools.ci.run_local_gate import run_local_gate

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/ci/run_local_gate.py"


def test_run_local_gate_runs_fmt_lint_tests_and_graph_in_order(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "ok\n", "")

    code, steps = run_local_gate(tmp_path, ruff="/fixture/ruff", command_runner=runner)

    assert code == 0
    assert [step["name"] for step in steps] == ["fmt", "lint", "tests", "graph"]
    assert commands[0][1:3] == ["format", "--check"]
    assert commands[1][1:2] == ["check"]
    assert "tools/ci/tests" in commands[2]
    assert commands[3][1] == ".harness/scripts/validate_phase1_graph.py"


def test_run_local_gate_default_runner_passes_cwd_by_keyword(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        calls.append(kwargs["cwd"])
        assert kwargs["check"] is False
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("tools.ci.run_local_gate.subprocess.run", fake_run)
    code, steps = run_local_gate(tmp_path, ruff="/fixture/ruff")

    assert code == 0
    assert len(steps) == 4
    assert calls == [tmp_path.resolve()] * 4


def test_run_local_gate_fails_fast_with_distinct_exit_code(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
        commands.append(command)
        return subprocess.CompletedProcess(command, 1, "", "formatter failed\n")

    code, steps = run_local_gate(tmp_path, ruff="/fixture/ruff", command_runner=runner)

    assert code == 10
    assert len(steps) == 1
    assert steps[0]["name"] == "fmt"


@pytest.mark.parametrize(
    ("failed_step", "expected_code"),
    [(1, 11), (2, 12), (3, 13)],
)
def test_run_local_gate_uses_distinct_failure_codes(
    tmp_path: Path, failed_step: int, expected_code: int
) -> None:
    calls = 0

    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
        nonlocal calls
        calls += 1
        exit_code = 1 if calls == failed_step + 1 else 0
        return subprocess.CompletedProcess(command, exit_code, "", "")

    code, steps = run_local_gate(tmp_path, ruff="/fixture/ruff", command_runner=runner)

    assert code == expected_code
    assert len(steps) == failed_step + 1


def test_run_local_gate_missing_ruff_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYGPUI_RUFF", "")
    monkeypatch.setattr("tools.ci.run_local_gate.shutil.which", lambda _: None)
    with pytest.raises(GateError) as caught:
        run_local_gate(tmp_path, ruff=None, command_runner=lambda command, cwd: None)
    assert caught.value.code == "dependency"


def test_configured_missing_ruff_returns_dependency_exit_69(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYGPUI_RUFF"] = "/tmp/opencode/definitely-missing-ruff-attempt-2"

    result = subprocess.run(
        [
            python_executable(),
            str(SCRIPT),
            "--repository",
            str(tmp_path),
            "--mode",
            "full",
        ],
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 69
    assert "LOCAL_GATE_REJECT code=dependency" in result.stderr
    assert "Traceback" not in result.stderr


def test_run_local_gate_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "LOCAL_GATE_SELF_TEST=PASS" in result.stdout
