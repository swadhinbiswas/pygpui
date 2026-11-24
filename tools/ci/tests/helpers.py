from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

TASK_ID = "P1-TOOL-BRANCH01"
MERGE_TASK_ID = "P1-INT01"
REGISTRY_PATH = ".harness/sessions/registry.json"
APPROVAL_PATH = ".harness/sessions/seed-approval.json"
BRANCH_EVIDENCE = f"evidence/{TASK_ID}/branch-evidence.json"
REVIEW_EVIDENCE = f"evidence/{TASK_ID}/review.json"
TEST_EVIDENCE = f"evidence/{TASK_ID}/independent-test.json"
ROLES_EVIDENCE = f"evidence/{TASK_ID}/session-roles.json"
MERGE_EVIDENCE = f"evidence/{TASK_ID}/merge.json"
INTEGRATOR_EVIDENCE = f"evidence/{MERGE_TASK_ID}/merge.json"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def make_repository(root: Path, *, with_origin: bool = False) -> tuple[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Fixture Author")
    git(root, "config", "user.email", "fixture@example.invalid")
    if with_origin:
        git(root, "remote", "add", "origin", "https://github.com/example/pygpui.git")
    task = {
        "id": TASK_ID,
        "title": "Fixture branch tooling",
        "owner_role": "Release-CI-Engineer",
        "workflow": "build",
        "completion_state": "merged",
        "deps": [],
        "review_evidence": REVIEW_EVIDENCE,
        "test_evidence": TEST_EVIDENCE,
        "merge_evidence": MERGE_EVIDENCE,
        "postmerge_record": MERGE_EVIDENCE,
        "session_registry_evidence": ROLES_EVIDENCE,
        "merge_owner_role": "Integrator",
        "premerge_state": "independently_verified",
        "postmerge_state": "merged",
        "branch_prefix": f"feat/{TASK_ID}-",
        "postmerge_command": (
            f"python3 tools/ci/record_merge.py --task {TASK_ID} --pr <pr-url> "
            f"--merge-sha <merge-sha> --output {MERGE_EVIDENCE}"
        ),
    }
    merge_task = {
        "id": MERGE_TASK_ID,
        "title": "Fixture Integrator merge",
        "owner_role": "Integrator",
        "workflow": "merge",
        "deps": [TASK_ID],
        "merge_evidence": INTEGRATOR_EVIDENCE,
    }
    write_json(root / ".harness/TASKS.json", {"tasks": [task, merge_task]})
    (root / "fixture.txt").write_text("baseline\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "test: fixture baseline")
    base = git(root, "rev-parse", "HEAD")
    git(root, "switch", "-c", f"feat/{TASK_ID}-tooling")
    (root / "fixture.txt").write_text("implemented\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "feat: fixture implementation")
    source = git(root, "rev-parse", "HEAD")
    return base, source


def add_fake_origin(root: Path, remote: Path) -> str:
    git(root, "init", "--bare", "--initial-branch=main", str(remote))
    git(root, "remote", "add", "origin", str(remote))
    git(root, "switch", "main")
    git(root, "push", "-u", "origin", "main")
    main_sha = git(root, "rev-parse", "HEAD")
    git(root, "switch", f"feat/{TASK_ID}-tooling")
    return main_sha


def write_seed_registry(root: Path, orchestrator_id: str = "orchestrator-1") -> str:
    registry = {
        "append_only": True,
        "schema_version": 1,
        "seed_history": [
            {
                "approver_session_id": orchestrator_id,
                "registry_sha256": "0" * 64,
            }
        ],
        "sessions": {
            orchestrator_id: {
                "role": "orchestrator",
                "trusted": True,
                "seed": True,
            }
        },
        "trust_root": "orchestrator",
    }
    registry_bytes = (json.dumps(registry, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    digest = sha256_bytes(registry_bytes)
    write_json(
        root / APPROVAL_PATH,
        {
            "approver_session_id": orchestrator_id,
            "registry_sha256": digest,
            "schema_version": 1,
            "scope": "phase1-session-registry-bootstrap",
        },
    )
    (root / REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REGISTRY_PATH).write_bytes(registry_bytes)
    return digest


def write_registry(root: Path, role_sessions: dict[str, str] | None = None) -> str:
    roles = role_sessions or {
        "implementer_session_id": "implementer-1",
        "reviewer_session_id": "reviewer-1",
        "tester_session_id": "tester-1",
        "integrator_session_id": "integrator-1",
    }
    role_names = {
        "implementer_session_id": "release-ci-engineer",
        "reviewer_session_id": "independent-reviewer",
        "tester_session_id": "test-engineer",
        "integrator_session_id": "integrator",
    }
    sessions = {
        "orchestrator-1": {"role": "orchestrator", "trusted": True, "seed": True},
    }
    for key, session_id in roles.items():
        sessions[session_id] = {
            "role": role_names[key],
            "trusted": True,
            "task_id": TASK_ID,
        }
    registry = {
        "append_only": True,
        "schema_version": 1,
        "seed_history": [],
        "sessions": sessions,
        "trust_root": "orchestrator",
    }
    registry_bytes = (json.dumps(registry, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    digest = sha256_bytes(registry_bytes)
    write_json(
        root / APPROVAL_PATH,
        {
            "approver_session_id": "orchestrator-1",
            "registry_sha256": digest,
            "schema_version": 1,
            "scope": "phase1-session-registry-bootstrap",
        },
    )
    (root / REGISTRY_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / REGISTRY_PATH).write_bytes(registry_bytes)
    return digest


def artifact_identity(root: Path, source_commit: str, branch: str) -> dict[str, str]:
    tree = git(root, "rev-parse", f"{source_commit}^{{tree}}")
    artifact_id = f"{TASK_ID}-branch"
    payload = {
        "artifact_id": artifact_id,
        "branch": branch,
        "output": BRANCH_EVIDENCE,
        "source_commit": source_commit,
        "source_tree": tree,
        "task_id": TASK_ID,
    }
    return {
        "artifact_id": artifact_id,
        "artifact_sha256": sha256_bytes(canonical_bytes(payload)),
        "source_tree": tree,
    }


def write_bundle(
    root: Path,
    base_commit: str,
    source_commit: str,
    branch: str = f"feat/{TASK_ID}-tooling",
    role_sessions: dict[str, str] | None = None,
) -> dict[str, object]:
    roles = role_sessions or {
        "implementer_session_id": "implementer-1",
        "reviewer_session_id": "reviewer-1",
        "tester_session_id": "tester-1",
        "integrator_session_id": "integrator-1",
    }
    registry_digest = write_registry(root, roles)
    artifact = artifact_identity(root, source_commit, branch)
    common = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "branch": branch,
        "source_commit": source_commit,
        "source_tree": artifact["source_tree"],
        "artifact_id": artifact["artifact_id"],
        "artifact_sha256": artifact["artifact_sha256"],
        "registry_sha256": registry_digest,
    }
    review = {
        **common,
        "decision": "pass",
        "record_path": REVIEW_EVIDENCE,
        "reviewed_head_commit": source_commit,
        "reviewed_head_tree": artifact["source_tree"],
        "role": "independent-reviewer",
        "session_id": roles["reviewer_session_id"],
    }
    test = {
        **common,
        "decision": "pass",
        "record_path": TEST_EVIDENCE,
        "role": "test-engineer",
        "session_id": roles["tester_session_id"],
    }
    write_json(root / REVIEW_EVIDENCE, review)
    write_json(root / TEST_EVIDENCE, test)
    session_roles = {
        **common,
        "record_path": ROLES_EVIDENCE,
        "registry_path": REGISTRY_PATH,
        "status": "assigned",
        **roles,
    }
    write_json(root / ROLES_EVIDENCE, session_roles)
    evidence = {
        **common,
        **artifact,
        **roles,
        "base_commit": base_commit,
        "branch": branch,
        "independent_evidence": True,
        "record_path": BRANCH_EVIDENCE,
        "reviewed_head_commit": source_commit,
        "reviewed_head_tree": artifact["source_tree"],
        "registry": {"path": REGISTRY_PATH, "sha256": registry_digest},
        "review": {
            "path": REVIEW_EVIDENCE,
            "sha256": sha256_file(root / REVIEW_EVIDENCE),
        },
        "test": {"path": TEST_EVIDENCE, "sha256": sha256_file(root / TEST_EVIDENCE)},
        "session_roles": {
            "path": ROLES_EVIDENCE,
            "sha256": sha256_file(root / ROLES_EVIDENCE),
        },
        "state": "independently_verified",
    }
    write_json(root / BRANCH_EVIDENCE, evidence)
    return evidence


def refresh_reference(root: Path, evidence: dict[str, object], key: str) -> None:
    reference = evidence[key]
    assert isinstance(reference, dict)
    reference["sha256"] = sha256_file(root / str(reference["path"]))


def merge_metadata(root: Path, source_commit: str, merge_sha: str) -> dict[str, object]:
    return {
        "author": {"login": "fixture-integrator"},
        "baseRefName": "main",
        "headRefName": f"feat/{TASK_ID}-tooling",
        "headRefOid": source_commit,
        "mergeCommit": {"oid": merge_sha},
        "mergedAt": "2026-11-24T00:00:00Z",
        "number": 1,
        "state": "MERGED",
        "url": "https://github.com/example/pygpui/pull/1",
    }
