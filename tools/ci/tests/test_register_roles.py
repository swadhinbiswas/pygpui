from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.common import (
    GateError,
    load_json,
    python_executable,
    sha256_file,
    write_json,
)
from tools.ci.tests.helpers import (
    APPROVAL_PATH,
    MERGE_TASK_ID,
    REGISTRY_PATH,
    TASK_ID,
    make_repository,
    write_seed_registry,
)
from tools.session.register_roles import register_roles

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/session/register_roles.py"
APPROVER = "orchestrator-1"


def test_register_roles_appends_all_task_bound_roles_and_preserves_seed_history(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry_before = load_json(tmp_path / REGISTRY_PATH)
    approval_before = load_json(tmp_path / APPROVAL_PATH)

    result = register_roles(
        tmp_path,
        TASK_ID,
        APPROVER,
        [
            ("implementer", "implementer-1"),
            ("reviewer", "reviewer-1"),
            ("tester", "tester-1"),
            ("integrator", "integrator-1"),
        ],
    )

    registry_after = load_json(tmp_path / REGISTRY_PATH)
    approval_after = load_json(tmp_path / APPROVAL_PATH)
    assert registry_after["seed_history"] == registry_before["seed_history"]
    assert registry_after["sessions"][APPROVER] == registry_before["sessions"][APPROVER]
    assert set(registry_after["sessions"]) == {
        APPROVER,
        "implementer-1",
        "reviewer-1",
        "tester-1",
        "integrator-1",
    }
    for role, session_id in result["roles"].items():
        assert registry_after["sessions"][session_id] == {
            "role": role,
            "task_id": TASK_ID,
            "trusted": True,
        }
    assert (
        approval_after["approver_session_id"] == approval_before["approver_session_id"]
    )
    assert approval_after["scope"] == approval_before["scope"]
    assert approval_after["registry_sha256"] == sha256_file(tmp_path / REGISTRY_PATH)
    assert result["registry_sha256"] == approval_after["registry_sha256"]


def test_register_roles_rejects_duplicate_role_in_one_request_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "reviewer-1"), ("reviewer", "reviewer-2")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_existing_duplicate_role_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    register_roles(tmp_path, TASK_ID, APPROVER, [("reviewer", "reviewer-1")])
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(tmp_path, TASK_ID, APPROVER, [("reviewer", "reviewer-2")])

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


@pytest.mark.parametrize(
    ("role", "existing_role"),
    [
        ("implementer", "release-ci-engineer"),
        ("reviewer", "independent-reviewer"),
        ("tester", "test-engineer"),
    ],
)
def test_register_roles_rejects_existing_role_alias_for_same_task(
    tmp_path: Path, role: str, existing_role: str
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry = load_json(tmp_path / REGISTRY_PATH)
    registry["sessions"]["existing-session"] = {
        "role": existing_role,
        "task_id": TASK_ID,
        "trusted": True,
    }
    write_json(tmp_path / REGISTRY_PATH, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(tmp_path / REGISTRY_PATH)
    write_json(tmp_path / APPROVAL_PATH, approval)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [(role, "new-session")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_session_reused_for_conflicting_role(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    register_roles(tmp_path, TASK_ID, APPROVER, [("reviewer", "reviewer-1")])
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(tmp_path, TASK_ID, APPROVER, [("tester", "reviewer-1")])

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_same_session_for_two_roles_in_one_request(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "shared-session"), ("tester", "shared-session")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_wrong_task_without_session_registry_binding(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            MERGE_TASK_ID,
            APPROVER,
            [("reviewer", "reviewer-1")],
        )

    assert caught.value.code == "identity"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_session_bound_to_another_task(tmp_path: Path) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry = load_json(tmp_path / REGISTRY_PATH)
    registry["sessions"]["foreign-session"] = {
        "role": "reviewer",
        "task_id": MERGE_TASK_ID,
        "trusted": True,
    }
    write_json(tmp_path / REGISTRY_PATH, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(tmp_path / REGISTRY_PATH)
    write_json(tmp_path / APPROVAL_PATH, approval)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "foreign-session")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_untrusted_approver_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            "untrusted-orchestrator",
            [("reviewer", "reviewer-1")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_untrusted_seed_record_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry = load_json(tmp_path / REGISTRY_PATH)
    registry["sessions"][APPROVER]["trusted"] = False
    write_json(tmp_path / REGISTRY_PATH, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(tmp_path / REGISTRY_PATH)
    write_json(tmp_path / APPROVAL_PATH, approval)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "reviewer-1")],
        )

    assert caught.value.code == "registry"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_non_append_only_registry_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry = load_json(tmp_path / REGISTRY_PATH)
    registry["append_only"] = False
    write_json(tmp_path / REGISTRY_PATH, registry)
    approval = load_json(tmp_path / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(tmp_path / REGISTRY_PATH)
    write_json(tmp_path / APPROVAL_PATH, approval)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "reviewer-1")],
        )

    assert caught.value.code == "registry"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_rejects_approval_hash_mismatch_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    registry_path = tmp_path / REGISTRY_PATH
    registry_path.write_bytes(registry_path.read_bytes() + b"\n")
    before = registry_path.read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "reviewer-1")],
        )

    assert caught.value.code == "registry"
    assert registry_path.read_bytes() == before


def test_register_roles_rejects_invalid_session_id_without_mutation(
    tmp_path: Path,
) -> None:
    make_repository(tmp_path)
    write_seed_registry(tmp_path, APPROVER)
    before = (tmp_path / REGISTRY_PATH).read_bytes()

    with pytest.raises(GateError) as caught:
        register_roles(
            tmp_path,
            TASK_ID,
            APPROVER,
            [("reviewer", "bad session")],
        )

    assert caught.value.code == "role"
    assert (tmp_path / REGISTRY_PATH).read_bytes() == before


def test_register_roles_cli_self_test_exits_zero() -> None:
    result = subprocess.run(
        [python_executable(), str(SCRIPT), "--self-test"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "REGISTER_ROLES_SELF_TEST=PASS" in result.stdout
