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
from tools.ci.record_merge import (
    create_merge_record,
    fetch_pr_metadata,
    verify_merge_record,
)
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
    base, source = make_repository(root, with_origin=True)
    evidence = write_bundle(root, base, source)
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
    evidence["merge_sha"] = merge_sha
    write_json(root / BRANCH_EVIDENCE, evidence)
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
    verified = verify_merge_record(
        tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha, pr_metadata=metadata
    )

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
    verified = verify_merge_record(
        tmp_path, TASK_ID, INTEGRATOR_EVIDENCE, merge_sha, pr_metadata=metadata
    )

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
    base, source = make_repository(tmp_path, with_origin=True)
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
    base, source = make_repository(tmp_path, with_origin=True)
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


def test_record_merge_rejects_unreviewed_implementation_descendant(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path, with_origin=True)
    write_bundle(tmp_path, base, source)
    git(tmp_path, "add", f"evidence/{TASK_ID}")
    git(tmp_path, "commit", "-m", "test: evidence after review")
    (tmp_path / "fixture.txt").write_text("unreviewed code\n", encoding="utf-8")
    git(tmp_path, "add", "fixture.txt")
    git(tmp_path, "commit", "-m", "feat: unreviewed code")
    head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "switch", "main")
    git(tmp_path, "merge", "--no-ff", f"feat/{TASK_ID}-tooling", "-m", "test: merge")
    merge_sha = git(tmp_path, "rev-parse", "HEAD")
    metadata = merge_metadata(tmp_path, head, merge_sha)

    with pytest.raises(GateError) as caught:
        create_merge_record(
            tmp_path,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )

    assert caught.value.code == "identity"


def test_record_merge_rejects_pr_head_not_contained_by_merge(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path, with_origin=True)
    write_bundle(tmp_path, base, source)
    git(tmp_path, "switch", "-c", "fixture/side")
    (tmp_path / "side.txt").write_text("side\n", encoding="utf-8")
    git(tmp_path, "add", "side.txt")
    git(tmp_path, "commit", "-m", "test: side branch")
    side_head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "switch", "main")
    git(tmp_path, "merge", "--no-ff", f"feat/{TASK_ID}-tooling", "-m", "test: merge")
    merge_sha = git(tmp_path, "rev-parse", "HEAD")
    metadata = merge_metadata(tmp_path, side_head, merge_sha)

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


def test_record_merge_rejects_wrong_repository_pr_before_writing(
    tmp_path: Path,
) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    metadata["url"] = "https://github.com/attacker/pygpui/pull/1"

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
    assert not (tmp_path / MERGE_EVIDENCE).exists()


@pytest.mark.parametrize("selector", ["--help", "1", "owner/repo#1"])
def test_fetch_pr_metadata_rejects_noncanonical_selector_before_gh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selector: str
) -> None:
    def unexpected(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise AssertionError("gh must not run for an option-like selector")

    monkeypatch.setattr("tools.ci.record_merge.subprocess.run", unexpected)
    with pytest.raises(GateError) as caught:
        fetch_pr_metadata(tmp_path, selector)
    assert caught.value.code == "pr"


def test_verify_merge_record_fetches_live_metadata_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
    calls: list[str] = []

    def fake_fetch(root: Path, pr: str) -> dict[str, object]:
        calls.append(pr)
        return metadata

    monkeypatch.setattr("tools.ci.record_merge.fetch_pr_metadata", fake_fetch)
    record = verify_merge_record(tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha)

    assert record["merge_sha"] == merge_sha
    assert calls == [str(metadata["url"])]


def test_verify_merge_record_requires_expected_merge_sha(tmp_path: Path) -> None:
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
        verify_merge_record(
            tmp_path, TASK_ID, MERGE_EVIDENCE, None, pr_metadata=metadata
        )

    assert caught.value.code == "merge"


def test_verify_merge_record_rejects_merge_not_reachable_from_main(
    tmp_path: Path,
) -> None:
    base, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    git(tmp_path, "switch", f"feat/{TASK_ID}-tooling")
    git(tmp_path, "branch", "-f", "main", base)

    with pytest.raises(GateError) as caught:
        verify_merge_record(
            tmp_path, TASK_ID, MERGE_EVIDENCE, merge_sha, pr_metadata=metadata
        )

    assert caught.value.code == "merge"


def test_record_merge_cli_offline_cannot_return_merged_pass(tmp_path: Path) -> None:
    _, merge_sha, metadata = make_merged_repository(tmp_path)
    create_merge_record(
        tmp_path,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )

    result = subprocess.run(
        [
            python_executable(),
            str(SCRIPT),
            "verify",
            "--repository",
            str(tmp_path),
            "--task",
            TASK_ID,
            "--record",
            MERGE_EVIDENCE,
            "--expected-sha",
            merge_sha,
            "--offline",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "RECORD_MERGE_VERIFY=PASS" not in result.stdout
    assert "offline" in result.stderr.lower()


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
