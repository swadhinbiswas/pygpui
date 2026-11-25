#!/usr/bin/env python3
"""Append task-bound Phase 1 session roles under an approved Orchestrator trust root."""

from __future__ import annotations

import argparse
import copy
import fcntl
import os
import re
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import (
    CANONICAL_APPROVAL,
    CANONICAL_REGISTRY,
    GateError,
    atomic_write,
    load_json,
    load_task,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    validate_registry,
)

ROLE_ALIASES = {
    "implementer": {"implementer", "release-ci-engineer"},
    "reviewer": {"reviewer", "independent-reviewer"},
    "tester": {"tester", "test-engineer"},
    "integrator": {"integrator"},
}
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@contextmanager
def _registry_lock(root: Path) -> Iterator[None]:
    directory = root / ".harness/sessions"
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError as error:
        raise GateError(
            "registry", f"cannot open session registry directory: {error}"
        ) from error
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise GateError("registry", f"cannot read {path}: {error}") from error


def _validate_task(root: Path, task_id: str) -> None:
    task = load_task(root, task_id)
    expected = f"evidence/{task_id}/session-roles.json"
    if task.get("session_registry_evidence") != expected:
        raise GateError(
            "identity",
            f"task {task_id} does not declare canonical session-role evidence",
        )


def _validate_assignments(assignments: list[tuple[str, str]]) -> dict[str, str]:
    if not assignments:
        raise GateError("usage", "at least one --assign ROLE=SESSION is required")
    roles: dict[str, str] = {}
    sessions: dict[str, str] = {}
    for role, session_id in assignments:
        if role not in ROLE_ALIASES:
            raise GateError("role", f"unknown session role: {role}")
        if not isinstance(session_id, str) or not SESSION_RE.fullmatch(session_id):
            raise GateError("role", f"invalid session id for {role}: {session_id!r}")
        if role in roles:
            raise GateError("role", f"duplicate role in one request: {role}")
        if session_id in sessions:
            raise GateError(
                "role",
                f"session {session_id} is assigned to both {sessions[session_id]} and {role}",
            )
        roles[role] = session_id
        sessions[session_id] = role
    return roles


def _assert_only_additions(
    before: dict[str, Any], after: dict[str, Any], new_sessions: set[str]
) -> None:
    if set(before) != set(after):
        raise GateError("append_only", "registry top-level fields changed")
    for key, value in before.items():
        if key != "sessions" and value != after[key]:
            raise GateError("append_only", f"registry field changed: {key}")
    before_sessions = before.get("sessions")
    after_sessions = after.get("sessions")
    if not isinstance(before_sessions, dict) or not isinstance(after_sessions, dict):
        raise GateError("append_only", "registry sessions are not objects")
    for session_id, record in before_sessions.items():
        if after_sessions.get(session_id) != record:
            raise GateError(
                "append_only",
                f"existing session record changed or disappeared: {session_id}",
            )
    if set(after_sessions) - set(before_sessions) != new_sessions:
        raise GateError(
            "append_only", "registry mutation was not exactly the requested additions"
        )


def register_roles(
    root: Path,
    task_id: str,
    approver_session: str,
    assignments: list[tuple[str, str]],
) -> dict[str, Any]:
    root = root.resolve()
    _validate_task(root, task_id)
    roles = _validate_assignments(assignments)
    registry_path = root / CANONICAL_REGISTRY
    approval_path = root / CANONICAL_APPROVAL

    with _registry_lock(root):
        registry, current_digest = validate_registry(root)
        approval = load_json(approval_path)
        registry_bytes = _read_bytes(registry_path)
        approval_bytes = _read_bytes(approval_path)
        if sha256_bytes(registry_bytes) != current_digest:
            raise GateError(
                "registry", "registry changed while validation was in progress"
            )
        if approval.get("registry_sha256") != current_digest:
            raise GateError(
                "registry", "approval hash does not match the locked registry bytes"
            )
        if not isinstance(approver_session, str) or approver_session != approval.get(
            "approver_session_id"
        ):
            raise GateError(
                "role", "approver does not match the approved seed Orchestrator"
            )
        sessions = registry.get("sessions")
        if not isinstance(sessions, dict) or not isinstance(
            registry.get("seed_history"), list
        ):
            raise GateError("registry", "registry sessions or seed history are invalid")
        approver_record = sessions.get(approver_session)
        if (
            not isinstance(approver_record, dict)
            or approver_record.get("role") != "orchestrator"
            or approver_record.get("trusted") is not True
            or approver_record.get("seed") is not True
        ):
            raise GateError("role", "approver is not a trusted seed Orchestrator")

        for role, session_id in roles.items():
            if session_id in sessions:
                raise GateError(
                    "role",
                    f"session already exists and cannot be replaced or rebound: {session_id}",
                )
            for existing_id, existing in sessions.items():
                if not isinstance(existing, dict) or existing.get("task_id") != task_id:
                    continue
                existing_role = existing.get("role")
                if (
                    isinstance(existing_role, str)
                    and existing_role in ROLE_ALIASES[role]
                ):
                    raise GateError(
                        "role",
                        f"task {task_id} already has {role} session {existing_id}",
                    )

        proposed = copy.deepcopy(registry)
        proposed_sessions = proposed["sessions"]
        for role, session_id in roles.items():
            proposed_sessions[session_id] = {
                "role": role,
                "task_id": task_id,
                "trusted": True,
            }
        _assert_only_additions(registry, proposed, set(roles.values()))
        proposed_bytes = pretty_json_bytes(proposed)
        proposed_digest = sha256_bytes(proposed_bytes)
        proposed_approval = copy.deepcopy(approval)
        proposed_approval["registry_sha256"] = proposed_digest
        proposed_approval_bytes = pretty_json_bytes(proposed_approval)

        if (
            _read_bytes(registry_path) != registry_bytes
            or _read_bytes(approval_path) != approval_bytes
        ):
            raise GateError("registry", "registry or approval changed before append")
        registry_written = False
        try:
            atomic_write(registry_path, proposed_bytes)
            registry_written = True
            atomic_write(approval_path, proposed_approval_bytes)
        except GateError as error:
            try:
                if registry_written:
                    atomic_write(registry_path, registry_bytes)
                atomic_write(approval_path, approval_bytes)
            except GateError as rollback_error:
                raise GateError(
                    "append_only",
                    f"registry append failed and rollback failed: {rollback_error.message}",
                ) from error
            raise GateError(
                "append_only",
                f"registry append failed; original bytes restored: {error.message}",
            ) from error

        if _read_bytes(registry_path) != proposed_bytes:
            raise GateError(
                "registry", "written registry bytes do not match the approved append"
            )
        if _read_bytes(approval_path) != proposed_approval_bytes:
            raise GateError(
                "registry", "written approval bytes do not match the approved append"
            )
        validate_registry(root)
        return {
            "approver_session_id": approver_session,
            "registry_sha256": proposed_digest,
            "roles": roles,
            "task_id": task_id,
        }


def _parse_assignment(value: str) -> tuple[str, str]:
    if value.count("=") != 1:
        raise GateError("usage", "--assign must be exactly ROLE=SESSION")
    role, session_id = value.split("=", 1)
    return role, session_id


def self_test() -> None:
    from tools.ci.common import write_json
    from tools.ci.tests.helpers import (
        APPROVAL_PATH,
        MERGE_TASK_ID,
        REGISTRY_PATH,
        TASK_ID,
        make_repository,
        write_seed_registry,
    )

    def expect(function, *args, code: str, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except GateError as error:
            if error.code != code:
                raise AssertionError(
                    f"expected {code}, got {error.code}: {error.message}"
                ) from error
            return
        raise AssertionError(f"expected {code} rejection")

    with tempfile.TemporaryDirectory(
        prefix="register-roles-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        make_repository(root)
        write_seed_registry(root, "orchestrator-1")
        before = load_json(root / REGISTRY_PATH)
        result = register_roles(
            root,
            TASK_ID,
            "orchestrator-1",
            [
                ("implementer", "implementer-1"),
                ("reviewer", "reviewer-1"),
                ("tester", "tester-1"),
                ("integrator", "integrator-1"),
            ],
        )
        after = load_json(root / REGISTRY_PATH)
        if after["seed_history"] != before["seed_history"]:
            raise AssertionError("seed history changed")
        if (
            load_json(root / APPROVAL_PATH)["registry_sha256"]
            != result["registry_sha256"]
        ):
            raise AssertionError("approval hash was not refreshed")
        if sha256_file(root / REGISTRY_PATH) != result["registry_sha256"]:
            raise AssertionError("registry hash mismatch after append")
        expect(
            register_roles,
            root,
            TASK_ID,
            "orchestrator-1",
            [("reviewer", "reviewer-2")],
            code="role",
        )
        expect(
            register_roles,
            root,
            TASK_ID,
            "untrusted",
            [("tester", "tester-2")],
            code="role",
        )
        expect(
            register_roles,
            root,
            MERGE_TASK_ID,
            "orchestrator-1",
            [("tester", "tester-2")],
            code="identity",
        )

        non_append = root / "non-append"
        make_repository(non_append)
        write_seed_registry(non_append, "orchestrator-1")
        registry = load_json(non_append / REGISTRY_PATH)
        registry["append_only"] = False
        write_json(non_append / REGISTRY_PATH, registry)
        approval = load_json(non_append / APPROVAL_PATH)
        approval["registry_sha256"] = sha256_file(non_append / REGISTRY_PATH)
        write_json(non_append / APPROVAL_PATH, approval)
        expect(
            register_roles,
            non_append,
            TASK_ID,
            "orchestrator-1",
            [("reviewer", "reviewer-1")],
            code="registry",
        )

        mismatch = root / "mismatch"
        make_repository(mismatch)
        write_seed_registry(mismatch, "orchestrator-1")
        (mismatch / REGISTRY_PATH).write_bytes(
            (mismatch / REGISTRY_PATH).read_bytes() + b"\n"
        )
        expect(
            register_roles,
            mismatch,
            TASK_ID,
            "orchestrator-1",
            [("reviewer", "reviewer-1")],
            code="registry",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--task")
    parser.add_argument("--approver")
    parser.add_argument(
        "--assign",
        action="append",
        default=[],
        metavar="ROLE=SESSION",
        help="repeatable: implementer, reviewer, tester, or integrator",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("REGISTER_ROLES_SELF_TEST=PASS")
        return 0
    try:
        if not args.task or not args.approver or not args.assign:
            raise GateError(
                "usage",
                "--task, --approver and at least one --assign ROLE=SESSION are required",
            )
        assignments = [_parse_assignment(value) for value in args.assign]
        result = register_roles(
            Path(args.repository).resolve(),
            args.task,
            args.approver,
            assignments,
        )
        print(
            "ROLE_REGISTER=PASS "
            f"task={args.task} approver={args.approver} "
            f"roles={','.join(result['roles'])} registry_sha256={result['registry_sha256']}"
        )
        return 0
    except GateError as error:
        print(
            f"ROLE_REGISTER_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
