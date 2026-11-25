#!/usr/bin/env python3
"""Create and verify canonical Integrator-only merge records."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import (
    GateError,
    canonical_branch_evidence,
    canonical_json_bytes,
    canonical_repo_path,
    git_output,
    is_ancestor,
    load_json,
    load_task,
    load_tasks,
    require_commit,
    sha256_bytes,
    sha256_file,
    source_tree,
    validate_registry,
    verify_session_role,
    write_json,
)
from tools.ci.evidence import (
    VerifiedBranch,
    verify_premerge,
    verify_reviewed_head_delta,
)

PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/[1-9][0-9]*$"
)
ORIGIN_RE = re.compile(
    r"^(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"
)


def _origin_repo(root: Path) -> tuple[str, str]:
    try:
        url = git_output(root, "remote", "get-url", "origin")
    except GateError as error:
        raise GateError(
            "pr", f"canonical GitHub origin is required: {error.message}"
        ) from error
    match = ORIGIN_RE.fullmatch(url)
    if not match:
        raise GateError("pr", f"origin is not a canonical GitHub repository: {url}")
    return match.group("owner"), match.group("repo")


def _validate_pr_selector(root: Path, pr: str) -> str:
    if not isinstance(pr, str) or not pr or pr.startswith("-"):
        raise GateError("pr", "PR selector must be a canonical GitHub URL")
    match = PR_URL_RE.fullmatch(pr)
    if not match:
        raise GateError("pr", "PR selector must be a canonical GitHub URL")
    owner, repo = _origin_repo(root)
    if (match.group("owner").lower(), match.group("repo").lower()) != (
        owner.lower(),
        repo.lower(),
    ):
        raise GateError("pr", "PR repository does not match canonical origin")
    return pr


def _record_owner(
    root: Path, source_task: dict[str, Any], output: str
) -> dict[str, Any]:
    canonical_repo_path(root, output)
    source_id = str(source_task["id"])
    if (
        source_task.get("workflow") == "build"
        and source_task.get("postmerge_record") == output
    ):
        if source_task.get("merge_owner_role") != "Integrator":
            raise GateError(
                "role", "source task does not designate an Integrator merge owner"
            )
        return source_task
    candidates = []
    for task in load_tasks(root).values():
        if task.get("workflow") != "merge" or task.get("owner_role") != "Integrator":
            continue
        if output not in {task.get("merge_evidence"), task.get("postmerge_record")}:
            continue
        if source_id not in task.get("deps", []):
            continue
        candidates.append(task)
    if len(candidates) != 1:
        raise GateError(
            "identity",
            f"merge output is not a unique canonical Integrator record: {output}",
        )
    return candidates[0]


def _validate_pr_metadata(
    root: Path,
    verified: VerifiedBranch,
    pr: str,
    merge_sha: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise GateError("pr", "gh pr view did not return an object")
    url = metadata.get("url")
    if not isinstance(url, str):
        raise GateError("pr", "gh pr view returned a non-canonical GitHub PR URL")
    _validate_pr_selector(root, url)
    if pr != url:
        raise GateError("pr", "requested PR URL does not match gh pr view")
    if metadata.get("state") != "MERGED" or metadata.get("baseRefName") != "main":
        raise GateError("pr", "PR must be merged into main")
    if not isinstance(metadata.get("mergedAt"), str) or not metadata["mergedAt"]:
        raise GateError("pr", "PR lacks a merge timestamp")
    merge_commit = metadata.get("mergeCommit")
    if not isinstance(merge_commit, dict) or merge_commit.get("oid") != merge_sha:
        raise GateError("merge", "merge SHA does not match gh pr view mergeCommit.oid")
    head_oid = require_commit(root, metadata.get("headRefOid"), "PR head commit")
    if not is_ancestor(root, head_oid, merge_sha):
        raise GateError(
            "merge", "PR head commit is not an ancestor of the merge commit"
        )
    verify_reviewed_head_delta(root, verified, head_oid)
    if metadata.get("headRefName") != verified.evidence.get("branch"):
        raise GateError("pr", "PR head branch does not match the reviewed branch")
    number = metadata.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise GateError("pr", "PR number is invalid")
    if not url.endswith(f"/pull/{number}"):
        raise GateError("pr", "PR URL and number do not match")
    return {
        "author_login": (metadata.get("author") or {}).get("login")
        if isinstance(metadata.get("author"), dict)
        else None,
        "base_ref": "main",
        "head_oid": head_oid,
        "head_ref": metadata["headRefName"],
        "merge_commit_oid": merge_sha,
        "merged_at": metadata["mergedAt"],
        "number": number,
        "pr_state": "MERGED",
        "pr_url": url,
    }


def fetch_pr_metadata(root: Path, pr: str) -> dict[str, Any]:
    pr = _validate_pr_selector(root, pr)
    fields = "author,baseRefName,headRefName,headRefOid,mergeCommit,mergedAt,number,state,url"
    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr, "--json", fields],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GateError("dependency", f"cannot execute gh: {error}") from error
    if result.returncode != 0:
        raise GateError("pr", f"gh pr view failed: {result.stderr.strip()}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise GateError("pr", f"gh pr view returned invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise GateError("pr", "gh pr view did not return an object")
    return value


def _record_id(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_id", None)
    return sha256_bytes(canonical_json_bytes(payload))


def create_merge_record(
    root: Path,
    task_id: str,
    pr: str,
    merge_sha: str,
    output: str,
    pr_metadata: dict[str, Any],
    *,
    premerge_evidence: str | None = None,
    integrator_session: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    task = load_task(root, task_id)
    if task.get("workflow") != "build":
        raise GateError("identity", "merge records must bind a source build task")
    evidence_path = premerge_evidence or canonical_branch_evidence(task_id)
    canonical_repo_path(root, evidence_path)
    if evidence_path != canonical_branch_evidence(task_id):
        raise GateError("identity", "pre-merge evidence path is not canonical")
    verified = verify_premerge(root, task_id, evidence_path)
    owner = _record_owner(root, task, output)
    merge_sha = require_commit(root, merge_sha, "merge_sha")
    if not is_ancestor(root, verified.source_commit, merge_sha):
        raise GateError(
            "merge", "merge commit does not contain the reviewed source commit"
        )
    pr_fields = _validate_pr_metadata(root, verified, pr, merge_sha, pr_metadata)
    registry, _ = validate_registry(root)
    integrator = integrator_session or verified.evidence.get("integrator_session_id")
    integrator = verify_session_role(
        registry, integrator, {"integrator"}, task_id, "Integrator"
    )
    if verified.session_roles.get("integrator_session_id") != integrator:
        raise GateError(
            "role", "Integrator is not bound in the canonical session-role record"
        )
    if verified.evidence.get("integrator_session_id") != integrator:
        raise GateError("role", "Integrator does not match the pre-merge evidence")
    for other in (
        verified.evidence.get("implementer_session_id"),
        verified.evidence.get("reviewer_session_id"),
        verified.evidence.get("tester_session_id"),
    ):
        if integrator == other:
            raise GateError(
                "role", "Integrator must be distinct from author, reviewer and tester"
            )

    record: dict[str, Any] = {
        "schema_version": 1,
        "task_id": task_id,
        "record_owner_task_id": owner["id"],
        "record_path": output,
        "premerge_evidence_path": evidence_path,
        "premerge_evidence_sha256": sha256_file(root / evidence_path),
        "source_commit": verified.source_commit,
        "source_tree": verified.evidence["source_tree"],
        "merge_sha": merge_sha,
        "merge_tree": source_tree(root, merge_sha),
        "branch": verified.evidence["branch"],
        "artifact_id": verified.evidence["artifact_id"],
        "artifact_sha256": verified.evidence["artifact_sha256"],
        "registry_sha256": verified.registry_digest,
        "implementer_session_id": verified.evidence["implementer_session_id"],
        "reviewer_session_id": verified.evidence["reviewer_session_id"],
        "tester_session_id": verified.evidence["tester_session_id"],
        "integrator_session_id": integrator,
        "integrator_role": "integrator",
        "review_sha256": verified.evidence["review"]["sha256"],
        "test_sha256": verified.evidence["test"]["sha256"],
        "session_roles_sha256": verified.evidence["session_roles"]["sha256"],
        **pr_fields,
    }
    record["record_id"] = _record_id(record)
    write_json(root / output, record, overwrite=False)
    return record


def verify_merge_record(
    root: Path,
    task_id: str,
    record_path: str,
    expected_sha: str | None = None,
    *,
    premerge: VerifiedBranch | None = None,
    pr_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    task = load_task(root, task_id)
    if task.get("workflow") != "build":
        raise GateError(
            "identity", "merge record verification requires a source build task"
        )
    owner = _record_owner(root, task, record_path)
    if not (root / record_path).is_file():
        raise GateError("merge", f"Integrator merge record is missing: {record_path}")
    record = load_json(root / record_path)
    if record.get("schema_version") != 1:
        raise GateError("identity", "merge record schema version is invalid")
    if (
        record.get("task_id") != task_id
        or record.get("record_owner_task_id") != owner["id"]
        or record.get("record_path") != record_path
    ):
        raise GateError(
            "identity", "merge record task/output/record identity is not canonical"
        )
    record_id = record.get("record_id")
    if not isinstance(record_id, str) or record_id != _record_id(record):
        raise GateError("identity", "merge record identity hash is invalid")
    evidence_path = record.get("premerge_evidence_path")
    if evidence_path != canonical_branch_evidence(task_id):
        raise GateError(
            "identity", "merge record pre-merge evidence path is not canonical"
        )
    verified = premerge or verify_premerge(root, task_id, str(evidence_path))
    if record.get("premerge_evidence_sha256") != sha256_file(root / str(evidence_path)):
        raise GateError("evidence", "merge record pre-merge evidence hash is stale")
    for key in (
        "source_commit",
        "source_tree",
        "branch",
        "artifact_id",
        "artifact_sha256",
        "registry_sha256",
        "implementer_session_id",
        "reviewer_session_id",
        "tester_session_id",
        "integrator_session_id",
    ):
        if record.get(key) != verified.evidence.get(key):
            raise GateError(
                "binding", f"merge record {key} does not match pre-merge evidence"
            )
    if record.get("review_sha256") != verified.evidence["review"]["sha256"]:
        raise GateError("binding", "merge record review hash is stale")
    if record.get("test_sha256") != verified.evidence["test"]["sha256"]:
        raise GateError("binding", "merge record independent-test hash is stale")
    if (
        record.get("session_roles_sha256")
        != verified.evidence["session_roles"]["sha256"]
    ):
        raise GateError("binding", "merge record session-role hash is stale")
    registry, _ = validate_registry(root)
    verify_session_role(
        registry,
        record.get("integrator_session_id"),
        {"integrator"},
        task_id,
        "Integrator",
    )
    if record.get("integrator_role") != "integrator":
        raise GateError("role", "merge record does not identify the Integrator role")
    merge_sha = require_commit(root, record.get("merge_sha"), "merge_sha")
    if not isinstance(expected_sha, str) or not expected_sha:
        raise GateError(
            "merge", "an expected merge SHA is required for merged verification"
        )
    if merge_sha != expected_sha:
        raise GateError("merge", "merge SHA does not match --expected-sha")
    if not (
        is_ancestor(root, merge_sha, "main")
        or is_ancestor(root, merge_sha, "origin/main")
    ):
        raise GateError(
            "merge", "merge commit is not reachable from main or origin/main"
        )
    if not is_ancestor(root, verified.source_commit, merge_sha):
        raise GateError(
            "merge", "merge commit does not contain the reviewed source commit"
        )
    if record.get("merge_tree") != source_tree(root, merge_sha):
        raise GateError("merge", "merge record tree hash is stale")
    pr_url = record.get("pr_url")
    if not isinstance(pr_url, str):
        raise GateError("pr", "merge record PR URL is not canonical")
    _validate_pr_selector(root, pr_url)
    number = record.get("number")
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number < 1
        or not pr_url.endswith(f"/pull/{number}")
    ):
        raise GateError("pr", "merge record PR number is invalid")
    if record.get("pr_state") != "MERGED" or record.get("base_ref") != "main":
        raise GateError("pr", "merge record does not describe a merge into main")
    if record.get("merge_commit_oid") != merge_sha or record.get(
        "head_ref"
    ) != verified.evidence.get("branch"):
        raise GateError("pr", "merge record PR commit or branch binding is invalid")
    if not isinstance(record.get("merged_at"), str) or not record["merged_at"]:
        raise GateError("pr", "merge record lacks a merge timestamp")
    head_oid = require_commit(root, record.get("head_oid"), "recorded PR head commit")
    if not is_ancestor(root, head_oid, merge_sha):
        raise GateError(
            "merge", "recorded PR head is not an ancestor of the merge commit"
        )
    verify_reviewed_head_delta(root, verified, head_oid)
    metadata = (
        pr_metadata if pr_metadata is not None else fetch_pr_metadata(root, pr_url)
    )
    expected_fields = _validate_pr_metadata(root, verified, pr_url, merge_sha, metadata)
    for key, value in expected_fields.items():
        if record.get(key) != value:
            raise GateError("pr", f"merge record PR field is stale: {key}")
    return record


def _expect_rejection(function, *args, code: str, **kwargs) -> None:
    try:
        function(*args, **kwargs)
    except GateError as error:
        if error.code != code:
            raise AssertionError(
                f"expected {code}, got {error.code}: {error.message}"
            ) from error
        return
    raise AssertionError(f"expected {code} rejection")


def self_test() -> None:
    from tools.ci.tests.helpers import (
        BRANCH_EVIDENCE,
        MERGE_EVIDENCE,
        TASK_ID,
        git,
        make_repository,
        merge_metadata,
        write_bundle,
    )

    with tempfile.TemporaryDirectory(
        prefix="record-merge-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        base, source = make_repository(root, with_origin=True)
        evidence = write_bundle(root, base, source)
        git(root, "switch", "main")
        git(
            root,
            "merge",
            "--no-ff",
            f"feat/{TASK_ID}-tooling",
            "-m",
            "test: fixture merge",
        )
        merge_sha = git(root, "rev-parse", "HEAD")
        metadata = merge_metadata(root, source, merge_sha)
        evidence["merge_sha"] = merge_sha
        write_json(root / BRANCH_EVIDENCE, evidence)
        evidence_bytes = (root / BRANCH_EVIDENCE).read_bytes()
        (root / BRANCH_EVIDENCE).unlink()
        _expect_rejection(
            create_merge_record,
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
            code="evidence",
        )
        (root / BRANCH_EVIDENCE).write_bytes(evidence_bytes)
        evidence["integrator_session_id"] = "reviewer-1"
        write_json(root / BRANCH_EVIDENCE, evidence)
        _expect_rejection(
            create_merge_record,
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
            code="role",
        )
        write_json(root / BRANCH_EVIDENCE, json.loads(evidence_bytes))
        _expect_rejection(
            create_merge_record,
            root,
            "P1-INT01",
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
            code="identity",
        )
        _expect_rejection(
            create_merge_record,
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            f"evidence/{TASK_ID}/wrong.json",
            metadata,
            code="identity",
        )
        wrong_metadata = dict(metadata)
        wrong_metadata["mergeCommit"] = {"oid": source}
        _expect_rejection(
            create_merge_record,
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            wrong_metadata,
            code="merge",
        )
        record = create_merge_record(
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )
        verify_merge_record(
            root, TASK_ID, MERGE_EVIDENCE, merge_sha, pr_metadata=metadata
        )
        record["record_path"] = f"evidence/{TASK_ID}/wrong.json"
        write_json(root / MERGE_EVIDENCE, record)
        _expect_rejection(
            verify_merge_record,
            root,
            TASK_ID,
            MERGE_EVIDENCE,
            merge_sha,
            code="identity",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["verify"], default="record")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--task")
    parser.add_argument("--pr")
    parser.add_argument("--merge-sha")
    parser.add_argument("--output")
    parser.add_argument("--record")
    parser.add_argument("--expected-sha")
    parser.add_argument("--premerge-evidence")
    parser.add_argument("--integrator-session")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="deprecated; offline merged verification is prohibited",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("RECORD_MERGE_SELF_TEST=PASS")
        return 0
    root = Path(args.repository).resolve()
    try:
        if args.command == "verify":
            missing = [
                name
                for name in ("task", "record", "expected_sha")
                if not getattr(args, name)
            ]
            if missing:
                raise GateError(
                    "usage",
                    f"verify requires --task, --record and --expected-sha; missing {missing}",
                )
            if args.offline:
                raise GateError("pr", "offline merged verification is prohibited")
            record = verify_merge_record(
                root, args.task, args.record, args.expected_sha
            )
            print(
                "RECORD_MERGE_VERIFY=PASS "
                f"task={args.task} record={args.record} merge_sha={record['merge_sha']} mode=github"
            )
            return 0
        missing = [
            name
            for name in ("task", "pr", "merge-sha", "output")
            if not getattr(args, name.replace("-", "_"))
        ]
        if missing:
            raise GateError(
                "usage",
                f"record requires --task, --pr, --merge-sha and --output; missing {missing}",
            )
        metadata = fetch_pr_metadata(root, args.pr)
        record = create_merge_record(
            root,
            args.task,
            args.pr,
            args.merge_sha,
            args.output,
            metadata,
            premerge_evidence=args.premerge_evidence,
            integrator_session=args.integrator_session,
        )
        print(
            "RECORD_MERGE=PASS "
            f"task={args.task} owner={record['record_owner_task_id']} "
            f"record={record['record_path']} merge_sha={record['merge_sha']}"
        )
        return 0
    except GateError as error:
        print(
            f"RECORD_MERGE_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
