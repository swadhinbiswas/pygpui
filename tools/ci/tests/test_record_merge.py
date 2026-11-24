from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.common import (
    GateError,
    canonical_json_bytes,
    load_json,
    python_executable,
    sha256_bytes,
    write_json,
)
from tools.ci.record_merge import create_merge_record, verify_merge_record
from tools.ci.tests.helpers import (
    BRANCH_EVIDENCE,
    INTEGRATOR_EVIDENCE,
    MERGE_EVIDENCE,
    MERGE_TASK_ID,
    TASK_ID,
    git,
    make_repository,
    merge_metadata,
    write_bundle,
)

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/ci/record_merge.py"


def make_merged_repository(root: Path) -> tuple[str, str, dict[str, object]]:
    base, source = make_repository(root)
    write_bundle(root, base, source)
    git(root, "switch", "main")
    git(
        root,
        "merge",
        "--no-ff",
        f"feat/{TASK_ID}-tooling",
        "-m",
        "test: reviewed fixture merge",
    )
    merge_sha = git(root, "rev-parse", "HEAD")
    return source, merge_sha, merge_metadata(root, source, merge_sha)


def test_record_merge_creates_canonical_bound_record(tmp_path: Path) -> None:
    source, merge_sha, metadata = make_merged_repository(tmp_path)

    record = create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    verified = verify_merge_record(tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha)

    assert record["task_id"] == TASK_ID
    assert record["record_owner_task_id"] == TASK_ID
    assert record["record_path"] == MERGE_EVIDENCE
    assert record["source_commit"] == source
    assert verified["merge_sha"] == merge_sha


def test_record_merge_supports_integrator_owned_output_for_source_task(
    tmp_path: Path,
) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)

    record = create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        INTEGRATOR_EVIDENCE,
        metadata,
    )
    verified = verify_merge_record(tmp_path, TASK_ID, INTEGRATOR_EVIDENCE, merge_sha)

    assert record["task_id"] == TASK_ID
    assert record["record_owner_task_id"] == MERGE_TASK_ID
    assert verified["record_path"] == INTEGRATOR_EVIDENCE


def test_record_merge_rejects_missing_premerge_evidence(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    (tmp_path / BRANCH_EVIDENCE).unlink()

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "evidence"


def test_record_merge_rejects_non_integrator_session(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["integrator_session_id"] = "reviewer-1"
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)
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

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "role"


def test_record_merge_rejects_merge_sha_mismatch(tmp_path: Path) -> None:
    source, merge_sha, metadata = make_merged_repository(tmp_path)
    metadata["mergeCommit"]["oid"] = source

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "merge"


def test_record_merge_rejects_merge_commit_without_reviewed_source(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    metadata = merge_metadata(tmp_path, source, base)

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            base,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "merge"


def test_record_merge_rejects_pr_metadata_for_wrong_base_or_state(
    tmp_path: Path,
) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    metadata["baseRefName"] = "develop"

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "pr"


def test_record_merge_rejects_wrong_task_identity(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            MERGE_TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "identity"


def test_record_merge_rejects_wrong_output_identity(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            f"evidence/{TASK_ID}/not-merge.json",
            metadata,
        )

    assert caught.value.code == "identity"


def test_record_merge_rejects_tampered_record_identity(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    record = load_json(tmp_path / MERGE_EVIDENCE)
    record["record_path"] = INTEGRATOR_EVIDENCE
    write_json(tmp_path / MERGE_EVIDENCE, record)

    with pytest.raises(GateError) as caught:
        verify_merge_record(tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha)

    assert caught.value.code == "identity"


def test_record_merge_rejects_tampered_record_id(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    record = load_json(tmp_path / MERGE_EVIDENCE)
    record["record_id"] = "0" * 64
    write_json(tmp_path / MERGE_EVIDENCE, record)

    with pytest.raises(GateError) as caught:
        verify_merge_record(tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha)

    assert caught.value.code == "identity"


def test_record_merge_rejects_unmerged_pr_state_even_with_recomputed_id(
    tmp_path: Path,
) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    record = load_json(tmp_path / MERGE_EVIDENCE)
    record["pr_state"] = "OPEN"
    payload = dict(record)
    payload.pop("record_id")
    record["record_id"] = sha256_bytes(canonical_json_bytes(payload))
    write_json(tmp_path / MERGE_EVIDENCE, record)

    with pytest.raises(GateError) as caught:
        verify_merge_record(tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha)

    assert caught.value.code == "pr"


def test_record_merge_does_not_overwrite_existing_record(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "record"


def test_record_merge_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "RECORD_MERGE_SELF_TEST=PASS" in result.stdout
