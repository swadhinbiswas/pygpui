from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.common import GateError, python_executable
from tools.ci.tag_point import create_tag, verify_tag
from tools.ci.tests.helpers import git, make_repository

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/ci/tag_point.py"


def test_tag_point_creates_and_verifies_annotated_immutable_tag(tmp_path: Path) -> None:
    _, source = make_repository(tmp_path)
    output = "evidence/P1-TOOL-BRANCH01/fixture-tag.json"

    created = create_tag(tmp_path, "phase1/contracts-premerge", source, output)
    verified = verify_tag(tmp_path, "phase1/contracts-premerge", output, source)

    assert created["commit"] == source
    assert verified["tag_object_sha"] == created["tag_object_sha"]
    assert (
        git(tmp_path, "cat-file", "-t", "refs/tags/phase1/contracts-premerge") == "tag"
    )


def test_tag_point_rejects_existing_tag(tmp_path: Path) -> None:
    _, source = make_repository(tmp_path)
    output = "evidence/P1-TOOL-BRANCH01/fixture-tag.json"
    create_tag(tmp_path, "phase1/contracts-premerge", source, output)

    with pytest.raises(GateError) as caught:
        create_tag(tmp_path, "phase1/contracts-premerge", source, output)

    assert caught.value.code == "tag"


def test_tag_point_rejects_moved_tag(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    output = "evidence/P1-TOOL-BRANCH01/fixture-tag.json"
    create_tag(tmp_path, "phase1/contracts-premerge", source, output)
    git(tmp_path, "tag", "-f", "-a", "phase1/contracts-premerge", base, "-m", "moved")

    with pytest.raises(GateError) as caught:
        verify_tag(tmp_path, "phase1/contracts-premerge", output, source)

    assert caught.value.code == "tag"


def test_tag_point_rejects_invalid_tag_name(tmp_path: Path) -> None:
    _, source = make_repository(tmp_path)
    with pytest.raises(GateError) as caught:
        create_tag(
            tmp_path, "bad tag", source, "evidence/P1-TOOL-BRANCH01/fixture-tag.json"
        )
    assert caught.value.code == "tag"


def test_tag_point_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "TAG_POINT_SELF_TEST=PASS" in result.stdout
