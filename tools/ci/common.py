"""Shared fail-closed primitives for Phase 1 branch and merge tooling."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

CANONICAL_REGISTRY = ".harness/sessions/registry.json"
CANONICAL_APPROVAL = ".harness/sessions/seed-approval.json"
CANONICAL_TASKS = ".harness/TASKS.json"
COMMIT_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TASK_RE = re.compile(r"^(?:P[0-9]+|H)-[A-Z0-9-]+$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class GateError(Exception):
    """A stable, machine-readable rejection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def python_executable() -> str:
    """Return a real Python interpreter even inside the packaged OpenCode host."""
    executable = Path(sys.executable)
    if "opencode" in executable.name.lower() and Path("/usr/bin/python3").exists():
        return "/usr/bin/python3"
    return sys.executable


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def pretty_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as error:
        raise GateError("evidence", f"cannot read {path}: {error}") from error


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise GateError("json", f"cannot load JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise GateError("json", f"JSON root must be an object: {path}")
    return value


def atomic_write(path: Path, content: bytes, *, overwrite: bool = True) -> None:
    if not overwrite and path.exists():
        raise GateError("record", f"refusing to overwrite existing record: {path}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, path)
    except OSError as error:
        raise GateError("io", f"cannot write {path}: {error}") from error


def write_json(path: Path, value: object, *, overwrite: bool = True) -> None:
    atomic_write(path, pretty_json_bytes(value), overwrite=overwrite)


def canonical_repo_path(root: Path, value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise GateError("identity", "repository path must be a non-empty POSIX path")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise GateError("identity", f"non-canonical repository path: {value}")
    normalized = pure.as_posix()
    if normalized != value:
        raise GateError("identity", f"non-canonical repository path: {value}")
    resolved_root = root.resolve()
    resolved = (root / normalized).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise GateError("identity", f"repository path escapes root: {value}")
    return normalized


def repo_file(root: Path, value: str) -> Path:
    return root / canonical_repo_path(root, value)


def load_tasks(
    root: Path, tasks_path: str = CANONICAL_TASKS
) -> dict[str, dict[str, Any]]:
    data = load_json(repo_file(root, tasks_path))
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        raise GateError("identity", "task graph must contain a tasks array")
    indexed: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise GateError("identity", "task graph entries must be objects")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not TASK_RE.fullmatch(task_id):
            raise GateError("identity", "task graph contains an invalid task id")
        if task_id in indexed:
            raise GateError("identity", f"duplicate task id: {task_id}")
        indexed[task_id] = task
    return indexed


def load_task(
    root: Path, task_id: str, tasks_path: str = CANONICAL_TASKS
) -> dict[str, Any]:
    if not isinstance(task_id, str) or not TASK_RE.fullmatch(task_id):
        raise GateError("identity", f"invalid task id: {task_id}")
    task = load_tasks(root, tasks_path).get(task_id)
    if task is None:
        raise GateError("identity", f"unknown task: {task_id}")
    return task


def task_path(task: dict[str, Any], field: str) -> str:
    value = task.get(field)
    if not isinstance(value, str) or not value:
        raise GateError("identity", f"task {task.get('id')} lacks canonical {field}")
    return value


def canonical_branch_evidence(task_id: str) -> str:
    if not TASK_RE.fullmatch(task_id):
        raise GateError("identity", f"invalid task id: {task_id}")
    return f"evidence/{task_id}/branch-evidence.json"


def require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise GateError("identity", f"{label} must be a lowercase SHA-256")
    return value


def require_commit(root: Path, value: object, label: str = "commit") -> str:
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        raise GateError("commit", f"{label} must be a full lowercase commit SHA")
    result = run_git(root, "rev-parse", "--verify", f"{value}^{{commit}}", check=False)
    if result.returncode != 0 or result.stdout.strip() != value:
        raise GateError("commit", f"{label} is not an exact local commit: {value}")
    return value


def run_git(
    root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GateError("dependency", f"cannot execute git: {error}") from error
    if check and result.returncode != 0:
        raise GateError("git", f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def git_output(root: Path, *args: str) -> str:
    return run_git(root, *args).stdout.strip()


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return (
        run_git(
            root, "merge-base", "--is-ancestor", ancestor, descendant, check=False
        ).returncode
        == 0
    )


def source_tree(root: Path, source_commit: str) -> str:
    require_commit(root, source_commit, "source_commit")
    return git_output(root, "rev-parse", f"{source_commit}^{{tree}}")


def branch_artifact(
    root: Path, task_id: str, source_commit: str, branch: str
) -> dict[str, str]:
    tree = source_tree(root, source_commit)
    artifact_id = f"{task_id}-branch"
    payload = {
        "artifact_id": artifact_id,
        "branch": branch,
        "output": canonical_branch_evidence(task_id),
        "source_commit": source_commit,
        "source_tree": tree,
        "task_id": task_id,
    }
    return {
        "artifact_id": artifact_id,
        "artifact_sha256": sha256_bytes(canonical_json_bytes(payload)),
        "source_tree": tree,
    }


def validate_registry(root: Path) -> tuple[dict[str, Any], str]:
    registry_path = root / CANONICAL_REGISTRY
    approval_path = root / CANONICAL_APPROVAL
    registry = load_json(registry_path)
    approval = load_json(approval_path)
    digest = sha256_file(registry_path)
    if (
        registry.get("schema_version") != 1
        or registry.get("trust_root") != "orchestrator"
    ):
        raise GateError("registry", "registry schema or trust root is invalid")
    if registry.get("append_only") is not True:
        raise GateError("registry", "registry is not append-only")
    if (
        approval.get("schema_version") != 1
        or approval.get("scope") != "phase1-session-registry-bootstrap"
    ):
        raise GateError("registry", "registry approval scope or schema is invalid")
    if approval.get("registry_sha256") != digest:
        raise GateError(
            "registry", "registry approval hash does not match exact registry bytes"
        )
    sessions = registry.get("sessions")
    if not isinstance(sessions, dict):
        raise GateError("registry", "registry sessions must be an object")
    approver = approval.get("approver_session_id")
    approver_record = sessions.get(approver) if isinstance(approver, str) else None
    if (
        not isinstance(approver_record, dict)
        or approver_record.get("role") != "orchestrator"
        or approver_record.get("trusted") is not True
        or approver_record.get("seed") is not True
    ):
        raise GateError(
            "registry", "registry approval is not bound to a trusted seed Orchestrator"
        )
    return registry, digest


def normalized_role(role: object) -> str:
    if not isinstance(role, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")


def verify_session_role(
    registry: dict[str, Any],
    session_id: object,
    accepted_roles: set[str],
    task_id: str,
    label: str,
) -> str:
    if not isinstance(session_id, str) or not session_id.strip():
        raise GateError("role", f"missing {label} session")
    sessions = registry.get("sessions")
    record = sessions.get(session_id) if isinstance(sessions, dict) else None
    if not isinstance(record, dict):
        raise GateError(
            "role", f"{label} session is absent from registry: {session_id}"
        )
    if record.get("trusted") is not True:
        raise GateError("role", f"{label} session is not trusted: {session_id}")
    if normalized_role(record.get("role")) not in accepted_roles:
        raise GateError("role", f"{label} session has the wrong role: {session_id}")
    bound_task = record.get("task_id")
    if bound_task is not None and bound_task != task_id:
        raise GateError(
            "role", f"{label} session is bound to a different task: {session_id}"
        )
    return session_id
