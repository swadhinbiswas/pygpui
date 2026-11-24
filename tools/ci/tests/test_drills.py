from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from tools.ci.common import GateError, python_executable
from tools.ci.red_main_drill import run_red_main_drill
from tools.ci.rollback_drill import run_rollback_drill
from tools.ci.tests.helpers import add_fake_origin, git, make_repository

ROOT = Path(__file__).resolve().parents[3]
RED_SCRIPT = ROOT / "tools/ci/red_main_drill.py"
ROLLBACK_SCRIPT = ROOT / "tools/ci/rollback_drill.py"


def fixture_directory() -> Path:
    return Path(tempfile.mkdtemp(prefix="branch-tools-test-", dir="/tmp/opencode"))


def test_red_main_drill_restores_fixture_green_and_archives_hashes() -> None:
    fixture = fixture_directory() / "red-main"
    production = fixture_directory() / "production"
    make_repository(production)
    origin_main = add_fake_origin(
        production, fixture_directory() / "production-origin.git"
    )
    before = git(production, "rev-parse", "HEAD")

    result = run_red_main_drill(fixture, production_root=production)

    assert result["fixture"] is True
    assert result["red_main_sha"] != result["restored_green_sha"]
    assert result["gate_after_fix"]["status"] == "pass"
    assert result["fixture_red_origin_main"] == result["red_main_sha"]
    assert result["gate_on_remote_red"]["status"] == "fail"
    assert result["gate_on_remote_green"]["status"] == "pass"
    commands = (fixture / "commands.txt").read_text(encoding="utf-8")
    pushes = [
        line
        for line in commands.splitlines()
        if line.startswith("$ ") and "git push" in line
    ]
    assert len(pushes) == 3
    assert result["production_before"]["main_refs"] == [
        f"refs/remotes/origin/main {origin_main}"
    ]
    assert git(production, "rev-parse", "HEAD") == before
    assert git(production, "rev-parse", "origin/main") == origin_main
    archive = json.loads((fixture / "archive.json").read_text(encoding="utf-8"))
    assert archive["restored_green_sha"] == result["restored_green_sha"]


def test_red_main_drill_rejects_fixture_outside_approved_root(tmp_path: Path) -> None:
    with pytest.raises(GateError) as caught:
        run_red_main_drill(tmp_path / "unsafe", production_root=tmp_path)
    assert caught.value.code == "fixture"


def test_red_main_drill_rejects_nonempty_fixture() -> None:
    fixture = fixture_directory() / "red-main"
    fixture.mkdir()
    (fixture / "unrelated.txt").write_text("do not overwrite\n", encoding="utf-8")
    with pytest.raises(GateError) as caught:
        run_red_main_drill(fixture, production_root=fixture.parent)
    assert caught.value.code == "fixture"
    assert (fixture / "unrelated.txt").read_text(
        encoding="utf-8"
    ) == "do not overwrite\n"


def test_red_main_drill_accepts_existing_empty_fixture() -> None:
    fixture = fixture_directory() / "red-main"
    fixture.mkdir()
    production = fixture_directory() / "production"
    make_repository(production)

    result = run_red_main_drill(fixture, production_root=production)

    assert result["gate_on_remote_red"]["status"] == "fail"
    assert result["gate_on_remote_green"]["status"] == "pass"


def test_rollback_drill_archives_exact_sequence_and_restores_green() -> None:
    fixture = fixture_directory() / "rollback"
    production = fixture_directory() / "production"
    make_repository(production)
    origin_main = add_fake_origin(
        production, fixture_directory() / "production-origin.git"
    )
    before = git(production, "rev-parse", "HEAD")

    result = run_rollback_drill(
        fixture, "phase1/contracts-premerge", production_root=production
    )

    assert result["tag"] == "phase1/contracts-premerge"
    assert result["gate_after_revert"]["status"] == "pass"
    assert result["gate_after_revert_of_revert"]["status"] == "fail"
    assert result["gate_after_remerge"]["status"] == "pass"
    assert result["revert_sha"] != result["revert_of_revert_sha"]
    assert result["restored_green_sha"] != result["injected_failure_sha"]
    assert len(result["pull_requests"]) == 3
    assert result["production_before"]["main_refs"] == [
        f"refs/remotes/origin/main {origin_main}"
    ]
    assert git(production, "rev-parse", "HEAD") == before
    assert git(production, "rev-parse", "origin/main") == origin_main
    archive = json.loads((fixture / "archive.json").read_text(encoding="utf-8"))
    assert archive["tag_record"]["commit"] == result["tag_commit"]


def test_rollback_drill_rejects_fixture_outside_approved_root(tmp_path: Path) -> None:
    with pytest.raises(GateError) as caught:
        run_rollback_drill(
            tmp_path / "unsafe", "phase1/contracts-premerge", production_root=tmp_path
        )
    assert caught.value.code == "fixture"


def test_red_main_drill_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(RED_SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "RED_MAIN_DRILL_SELF_TEST=PASS" in result.stdout


def test_rollback_drill_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(ROLLBACK_SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "ROLLBACK_DRILL_SELF_TEST=PASS" in result.stdout
