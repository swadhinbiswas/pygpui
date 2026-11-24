from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.common import GateError, load_json, python_executable, write_json
from tools.ci.evidence import verify_branch
from tools.ci.record_merge import create_merge_record
from tools.ci.tests.helpers import (
    BRANCH_EVIDENCE,
    MERGE_EVIDENCE,
    REVIEW_EVIDENCE,
    ROLES_EVIDENCE,
    TASK_ID,
    TEST_EVIDENCE,
    git,
    make_repository,
    merge_metadata,
    refresh_reference,
    write_bundle,
)

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/ci/branch_gate.py"


def test_branch_gate_accepts_bound_independent_evidence(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)

    result = verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert result.source_commit == source


def test_branch_gate_rejects_missing_named_branch_ref(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    git(tmp_path, "branch", "-m", "feat/P1-TOOL-BRANCH01-renamed")

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "commit"


def test_branch_gate_rejects_source_not_contained_by_named_branch(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    git(tmp_path, "switch", "main")
    git(tmp_path, "branch", "-f", f"feat/{TASK_ID}-tooling", base)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "commit"


@pytest.mark.parametrize(
    ("key", "path"),
    [
        ("review", REVIEW_EVIDENCE),
        ("test", TEST_EVIDENCE),
        ("session_roles", ROLES_EVIDENCE),
    ],
)
@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("source_tree", "0" * 40, "artifact"),
        ("source_tree", None, "artifact"),
        ("branch", "feat/P1-TOOL-BRANCH01-other", "identity"),
        ("branch", None, "identity"),
    ],
)
def test_branch_gate_requires_exact_tree_and_branch_on_every_bound_record(
    tmp_path: Path,
    key: str,
    path: str,
    field: str,
    value: str | None,
    expected_code: str,
) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    record = load_json(tmp_path / path)
    if value is None:
        record.pop(field, None)
    else:
        record[field] = value
    write_json(tmp_path / path, record)
    refresh_reference(tmp_path, evidence, key)
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == expected_code


def test_branch_gate_rejects_commit_mismatch_between_review_and_test(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    review = load_json(tmp_path / REVIEW_EVIDENCE)
    review["source_commit"] = base
    write_json(tmp_path / REVIEW_EVIDENCE, review)
    refresh_reference(tmp_path, evidence, "review")
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "commit"


def test_branch_gate_rejects_noncanonical_branch_name(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["branch"] = "feat/unrelated-task"
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "identity"


def test_branch_gate_rejects_artifact_hash_mismatch(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["artifact_sha256"] = "0" * 64
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "artifact"


def test_branch_gate_rejects_wrong_task_identity(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["task_id"] = "P1-INT01"
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "identity"


def test_branch_gate_rejects_evidence_reference_hash_mismatch(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["review"]["sha256"] = "0" * 64
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

    assert caught.value.code == "evidence"


def test_branch_gate_merged_state_requires_integrator_record(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "merged")

    assert caught.value.code == "merge"


def test_branch_gate_merged_state_accepts_bound_integrator_record(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    git(tmp_path, "switch", "main")
    git(
        tmp_path,
        "merge",
        "--no-ff",
        f"feat/{TASK_ID}-tooling",
        "-m",
        "test: fixture merge",
    )
    merge_sha = git(tmp_path, "rev-parse", "HEAD")
    metadata = merge_metadata(tmp_path, source, merge_sha)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )

    result = verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "merged")

    assert result.merge_record["merge_sha"] == merge_sha


def test_branch_gate_rejects_unsupported_state(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)

    with pytest.raises(GateError) as caught:
        verify_branch(tmp_path, TASK_ID, BRANCH_EVIDENCE, "implemented")

    assert caught.value.code == "state"


def test_branch_gate_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "BRANCH_GATE_SELF_TEST=PASS" in result.stdout


def test_branch_gate_cli_rejects_missing_evidence(tmp_path: Path) -> None:
    make_repository(tmp_path)
    result = subprocess.run(
        [
            python_executable(),
            str(SCRIPT),
            "verify",
            "--repository",
            str(tmp_path),
            "--task",
            TASK_ID,
            "--state",
            "independently_verified",
            "--evidence",
            BRANCH_EVIDENCE,
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "BRANCH_GATE_REJECT" in result.stderr
