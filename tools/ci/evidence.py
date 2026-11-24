"""Canonical, commit-bound pre-merge evidence and trusted session validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.ci.common import (
    GateError,
    branch_artifact,
    canonical_branch_evidence,
    canonical_repo_path,
    is_ancestor,
    load_json,
    load_task,
    normalized_role,
    require_commit,
    require_sha256,
    sha256_file,
    task_path,
    validate_registry,
    verify_session_role,
)

REGISTRY_PATH = ".harness/sessions/registry.json"
ROLE_KEYS = (
    "implementer_session_id",
    "reviewer_session_id",
    "tester_session_id",
    "integrator_session_id",
)


@dataclass
class VerifiedBranch:
    task: dict[str, Any]
    evidence: dict[str, Any]
    review: dict[str, Any]
    test: dict[str, Any]
    session_roles: dict[str, Any]
    registry_digest: str
    source_commit: str
    merge_record: dict[str, Any] | None = None


def _canonical_file(
    root: Path,
    task: dict[str, Any],
    field: str,
    filename: str,
) -> tuple[str, Path]:
    task_id = str(task["id"])
    expected = f"evidence/{task_id}/{filename}"
    value = task_path(task, field)
    canonical_repo_path(root, value)
    if value != expected:
        raise GateError("identity", f"task {task_id} {field} is not canonical: {value}")
    return value, root / value


def _reference(
    root: Path, evidence: dict[str, Any], key: str, expected: str
) -> tuple[dict[str, Any], Path]:
    reference = evidence.get(key)
    if not isinstance(reference, dict) or reference.get("path") != expected:
        raise GateError("identity", f"{key} reference has the wrong canonical path")
    require_sha256(reference.get("sha256"), f"{key} reference hash")
    path = root / expected
    if sha256_file(path) != reference["sha256"]:
        raise GateError(
            "evidence", f"{key} evidence hash does not match exact file bytes"
        )
    return load_json(path), path


def _validate_bound_record(
    record: dict[str, Any],
    *,
    label: str,
    expected_path: str,
    task_id: str,
    source_commit: str,
    artifact_id: str,
    artifact_sha256: str,
    registry_digest: str,
) -> None:
    if record.get("schema_version") != 1:
        raise GateError("identity", f"{label} schema version is invalid")
    if record.get("task_id") != task_id or record.get("record_path") != expected_path:
        raise GateError(
            "identity", f"{label} task/output/record identity is not canonical"
        )
    if record.get("source_commit") != source_commit:
        raise GateError("commit", f"{label} commit does not match the branch artifact")
    if (
        record.get("artifact_id") != artifact_id
        or record.get("artifact_sha256") != artifact_sha256
    ):
        raise GateError(
            "artifact", f"{label} artifact does not match the branch artifact"
        )
    if record.get("registry_sha256") != registry_digest:
        raise GateError(
            "registry", f"{label} registry hash does not match the trust root"
        )


def verify_premerge(
    root: Path,
    task_id: str,
    evidence_path: str,
) -> VerifiedBranch:
    root = root.resolve()
    task = load_task(root, task_id)
    canonical_evidence = canonical_branch_evidence(task_id)
    canonical_repo_path(root, evidence_path)
    if evidence_path != canonical_evidence:
        raise GateError(
            "identity", f"branch evidence path is not canonical: {evidence_path}"
        )
    if not (root / evidence_path).is_file():
        raise GateError("evidence", f"branch evidence is missing: {evidence_path}")
    evidence = load_json(root / evidence_path)
    if evidence.get("schema_version") != 1:
        raise GateError("identity", "branch evidence schema version is invalid")
    if (
        evidence.get("task_id") != task_id
        or evidence.get("record_path") != canonical_evidence
    ):
        raise GateError(
            "identity", "branch evidence task/output/record identity is not canonical"
        )
    if evidence.get("state") != "independently_verified":
        raise GateError("state", "branch evidence is not independently_verified")
    branch = evidence.get("branch")
    if (
        not isinstance(branch, str)
        or not branch
        or any(character.isspace() for character in branch)
    ):
        raise GateError("identity", "branch evidence lacks a valid branch name")
    branch_prefix = task.get("branch_prefix")
    if (
        isinstance(branch_prefix, str)
        and branch_prefix
        and not branch.startswith(branch_prefix.split(",", 1)[0])
    ):
        raise GateError(
            "identity", "branch name does not match the task's canonical branch prefix"
        )
    source_commit = require_commit(root, evidence.get("source_commit"), "source_commit")
    base_commit = require_commit(root, evidence.get("base_commit"), "base_commit")
    if not is_ancestor(root, base_commit, source_commit):
        raise GateError(
            "commit", "base commit is not an ancestor of the reviewed source commit"
        )
    artifact = branch_artifact(root, task_id, source_commit, branch)
    if (
        evidence.get("artifact_id") != artifact["artifact_id"]
        or evidence.get("artifact_sha256") != artifact["artifact_sha256"]
        or evidence.get("source_tree") != artifact["source_tree"]
    ):
        raise GateError(
            "artifact",
            "branch artifact is not bound to the exact source commit and tree",
        )

    registry, registry_digest = validate_registry(root)
    registry_reference = evidence.get("registry")
    if (
        not isinstance(registry_reference, dict)
        or registry_reference.get("path") != REGISTRY_PATH
        or registry_reference.get("sha256") != registry_digest
        or evidence.get("registry_sha256") != registry_digest
    ):
        raise GateError(
            "registry",
            "branch evidence is not bound to the exact approved registry bytes",
        )

    review_path, _ = _canonical_file(root, task, "review_evidence", "review.json")
    test_path, _ = _canonical_file(root, task, "test_evidence", "independent-test.json")
    roles_path, _ = _canonical_file(
        root, task, "session_registry_evidence", "session-roles.json"
    )
    review, _ = _reference(root, evidence, "review", review_path)
    test, _ = _reference(root, evidence, "test", test_path)
    session_roles, _ = _reference(root, evidence, "session_roles", roles_path)
    for label, record, path in (
        ("review", review, review_path),
        ("independent test", test, test_path),
        ("session roles", session_roles, roles_path),
    ):
        _validate_bound_record(
            record,
            label=label,
            expected_path=path,
            task_id=task_id,
            source_commit=source_commit,
            artifact_id=artifact["artifact_id"],
            artifact_sha256=artifact["artifact_sha256"],
            registry_digest=registry_digest,
        )
    if review.get("decision") != "pass" or test.get("decision") != "pass":
        raise GateError(
            "evidence", "review and independent test decisions must both be pass"
        )
    if (
        session_roles.get("status") != "assigned"
        or session_roles.get("registry_path") != REGISTRY_PATH
    ):
        raise GateError(
            "role", "session role record is not an assigned canonical registry snapshot"
        )

    owner_role = normalized_role(task.get("owner_role"))
    implementer_roles = {"implementer", "release-ci-engineer", owner_role} - {""}
    reviewer_roles = {"reviewer", "independent-reviewer"}
    tester_roles = {"tester", "test-engineer"}
    role_values: dict[str, str] = {}
    for key, accepted in (
        ("implementer_session_id", implementer_roles),
        ("reviewer_session_id", reviewer_roles),
        ("tester_session_id", tester_roles),
    ):
        session_id = verify_session_role(
            registry, evidence.get(key), accepted, task_id, key
        )
        if session_roles.get(key) != session_id:
            raise GateError("role", f"session role record mismatches {key}")
        role_values[key] = session_id
    if review.get("session_id") != role_values["reviewer_session_id"]:
        raise GateError("role", "review session does not match the assigned reviewer")
    if test.get("session_id") != role_values["tester_session_id"]:
        raise GateError(
            "role", "independent test session does not match the assigned tester"
        )
    if len(set(role_values.values())) != 3:
        raise GateError(
            "role", "implementer, reviewer and tester sessions must be distinct"
        )

    integrator = evidence.get("integrator_session_id")
    if integrator is not None:
        integrator = verify_session_role(
            registry, integrator, {"integrator"}, task_id, "Integrator"
        )
        if session_roles.get("integrator_session_id") != integrator:
            raise GateError("role", "session role record mismatches Integrator")
        if integrator in set(role_values.values()):
            raise GateError(
                "role",
                "Integrator must be distinct from implementer, reviewer and tester",
            )
        role_values["integrator_session_id"] = integrator
    elif "integrator_session_id" in session_roles:
        raise GateError("role", "session role record contains an unbound Integrator")

    return VerifiedBranch(
        task=task,
        evidence=evidence,
        review=review,
        test=test,
        session_roles=session_roles,
        registry_digest=registry_digest,
        source_commit=source_commit,
    )


def verify_branch(
    root: Path,
    task_id: str,
    evidence_path: str,
    state: str,
    *,
    record_path: str | None = None,
) -> VerifiedBranch:
    if state not in {"independently_verified", "merged"}:
        raise GateError("state", f"unsupported branch state: {state}")
    verified = verify_premerge(root, task_id, evidence_path)
    if state == "independently_verified":
        return verified
    if (
        verified.task.get("workflow") != "build"
        or verified.task.get("completion_state") != "merged"
    ):
        raise GateError(
            "state", "merged branch state is only valid for merged build tasks"
        )
    expected = (
        record_path
        if record_path is not None
        else task_path(verified.task, "postmerge_record")
    )
    from tools.ci.record_merge import verify_merge_record

    verified.merge_record = verify_merge_record(
        root.resolve(),
        task_id,
        expected,
        verified.evidence.get("merge_sha")
        if isinstance(verified.evidence.get("merge_sha"), str)
        else None,
        premerge=verified,
    )
    return verified
