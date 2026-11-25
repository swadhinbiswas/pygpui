from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.common import (
    GateError,
    load_json,
    python_executable,
    verify_session_role,
    write_json,
)
from tools.ci.evidence import verify_premerge
from tools.ci.tests.helpers import (
    APPROVAL_PATH,
    BRANCH_EVIDENCE,
    REGISTRY_PATH,
    ROLES_EVIDENCE,
    TASK_ID,
    make_repository,
    refresh_reference,
    sha256_file,
    write_bundle,
)

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/session/verify_roles.py"


def test_verify_roles_accepts_distinct_trusted_sessions(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)

    result = verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert result.evidence["reviewer_session_id"] == "reviewer-1"
    assert result.evidence["tester_session_id"] == "tester-1"


@pytest.mark.parametrize(
    ("role", "accepted_roles"),
    [
        ("implementer", {"implementer"}),
        ("reviewer", {"reviewer"}),
        ("tester", {"tester"}),
        ("integrator", {"integrator"}),
    ],
)
def test_verify_roles_requires_explicit_matching_task_on_every_nonseed_role(
    role: str, accepted_roles: set[str]
) -> None:
    registry = {
        "sessions": {
            "unbound-session": {
                "role": role,
                "trusted": True,
            }
        }
    }

    with pytest.raises(GateError) as caught:
        verify_session_role(
            registry,
            "unbound-session",
            accepted_roles,
            TASK_ID,
            role,
        )

    assert caught.value.code == "role"


def test_verify_roles_rejects_missing_reviewer(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence.pop("reviewer_session_id")
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "role"


def test_verify_roles_rejects_missing_tester(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence.pop("tester_session_id")
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "role"


def test_verify_roles_rejects_session_reuse(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["tester_session_id"] = evidence["reviewer_session_id"]
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "role"


def test_verify_roles_rejects_author_as_reviewer_or_tester(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    evidence["reviewer_session_id"] = evidence["implementer_session_id"]
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "role"


def test_verify_roles_rejects_untrusted_registry_session(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    registry_path = tmp_path / REGISTRY_PATH
    registry = load_json(registry_path)
    registry["sessions"]["reviewer-1"]["trusted"] = False
    write_json(registry_path, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(registry_path)
    write_json(tmp_path / APPROVAL_PATH, approval)
    evidence = load_json(tmp_path / BRANCH_EVIDENCE)
    evidence["registry_sha256"] = approval["registry_sha256"]
    evidence["registry"]["sha256"] = approval["registry_sha256"]
    roles = load_json(tmp_path / ROLES_EVIDENCE)
    roles["registry_sha256"] = approval["registry_sha256"]
    write_json(tmp_path / ROLES_EVIDENCE, roles)
    for key, path in (
        ("review", "evidence/P1-TOOL-BRANCH01/review.json"),
        ("test", "evidence/P1-TOOL-BRANCH01/independent-test.json"),
    ):
        record = load_json(tmp_path / path)
        record["registry_sha256"] = approval["registry_sha256"]
        write_json(tmp_path / path, record)
        refresh_reference(tmp_path, evidence, key)
    refresh_reference(tmp_path, evidence, "session_roles")
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "role"


def test_verify_roles_rejects_registry_approval_hash_mismatch(tmp_path: Path) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    registry_path = tmp_path / REGISTRY_PATH
    registry_path.write_bytes(registry_path.read_bytes() + b"\n")

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "registry"


def test_verify_roles_rejects_wrong_role_even_when_session_is_trusted(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    write_bundle(tmp_path, base, source)
    registry = load_json(tmp_path / REGISTRY_PATH)
    registry["sessions"]["reviewer-1"]["role"] = "orchestrator"
    write_json(tmp_path / REGISTRY_PATH, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(tmp_path / REGISTRY_PATH)
    write_json(tmp_path / APPROVAL_PATH, approval)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code in {"registry", "role"}


def test_verify_roles_rejects_non_pass_independent_test(
    tmp_path: Path,
) -> None:
    base, source = make_repository(tmp_path)
    evidence = write_bundle(tmp_path, base, source)
    test = load_json(tmp_path / "evidence/P1-TOOL-BRANCH01/independent-test.json")
    test["decision"] = "fail"
    write_json(tmp_path / "evidence/P1-TOOL-BRANCH01/independent-test.json", test)
    refresh_reference(tmp_path, evidence, "test")
    write_json(tmp_path / BRANCH_EVIDENCE, evidence)

    with pytest.raises(GateError) as caught:
        verify_premerge(tmp_path, TASK_ID, BRANCH_EVIDENCE)

    assert caught.value.code == "evidence"


def test_verify_roles_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "SESSION_ROLES_SELF_TEST=PASS" in result.stdout
