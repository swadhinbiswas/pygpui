from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/tmp/opencode/pygpui-P1-TOOL-BRANCH01")
sys.path.insert(0, str(REPO))

from tools.ci.common import GateError, load_json, python_executable, write_json
from tools.ci.evidence import verify_premerge
from tools.ci.tests.helpers import (
    APPROVAL_PATH,
    BRANCH_EVIDENCE,
    REGISTRY_PATH,
    REVIEW_EVIDENCE,
    ROLES_EVIDENCE,
    TASK_ID,
    TEST_EVIDENCE,
    git,
    make_repository,
    refresh_reference,
    sha256_file,
    write_bundle,
)

results: list[dict[str, object]] = []


def record(name: str, passed: bool, detail: str) -> None:
    results.append({"name": name, "passed": passed, "detail": detail})
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")


def expect_rejection(name: str, function) -> None:
    try:
        function()
    except GateError as error:
        record(name, True, f"rejected code={error.code} message={error.message}")
    else:
        record(name, False, "verifier unexpectedly accepted the mutated evidence")


with tempfile.TemporaryDirectory(
    prefix="independent-adversarial-", dir="/tmp/opencode"
) as directory:
    root = Path(directory)

    branch_root = root / "branch-ref"
    base, source = make_repository(branch_root)
    write_bundle(branch_root, base, source)
    git(branch_root, "branch", "-m", "feat/P1-TOOL-BRANCH01-renamed")
    expect_rejection(
        "named_branch_ref_must_exist_and_contain_source",
        lambda: verify_premerge(branch_root, TASK_ID, BRANCH_EVIDENCE),
    )

    role_root = root / "role-task-binding"
    base, source = make_repository(role_root)
    evidence = write_bundle(role_root, base, source)
    registry_path = role_root / REGISTRY_PATH
    registry = load_json(registry_path)
    registry["sessions"]["reviewer-1"].pop("task_id")
    write_json(registry_path, registry)
    approval = load_json(role_root / APPROVAL_PATH)
    approval["registry_sha256"] = sha256_file(registry_path)
    write_json(role_root / APPROVAL_PATH, approval)
    evidence["registry_sha256"] = approval["registry_sha256"]
    evidence["registry"]["sha256"] = approval["registry_sha256"]
    for relative in (REVIEW_EVIDENCE, TEST_EVIDENCE, ROLES_EVIDENCE):
        record_value = load_json(role_root / relative)
        record_value["registry_sha256"] = approval["registry_sha256"]
        write_json(role_root / relative, record_value)
    for key in ("review", "test", "session_roles"):
        refresh_reference(role_root, evidence, key)
    write_json(role_root / BRANCH_EVIDENCE, evidence)
    expect_rejection(
        "reviewer_role_must_have_explicit_task_binding",
        lambda: verify_premerge(role_root, TASK_ID, BRANCH_EVIDENCE),
    )

    tree_root = root / "record-tree"
    base, source = make_repository(tree_root)
    evidence = write_bundle(tree_root, base, source)
    review = load_json(tree_root / REVIEW_EVIDENCE)
    review["source_tree"] = "0" * 40
    write_json(tree_root / REVIEW_EVIDENCE, review)
    refresh_reference(tree_root, evidence, "review")
    write_json(tree_root / BRANCH_EVIDENCE, evidence)
    expect_rejection(
        "review_record_tree_must_match_branch_artifact",
        lambda: verify_premerge(tree_root, TASK_ID, BRANCH_EVIDENCE),
    )

    record_branch_root = root / "record-branch"
    base, source = make_repository(record_branch_root)
    evidence = write_bundle(record_branch_root, base, source)
    review = load_json(record_branch_root / REVIEW_EVIDENCE)
    review["branch"] = "feat/P1-TOOL-BRANCH01-other"
    write_json(record_branch_root / REVIEW_EVIDENCE, review)
    refresh_reference(record_branch_root, evidence, "review")
    write_json(record_branch_root / BRANCH_EVIDENCE, evidence)
    expect_rejection(
        "review_record_branch_must_match_branch_artifact",
        lambda: verify_premerge(record_branch_root, TASK_ID, BRANCH_EVIDENCE),
    )

missing_ruff = "/tmp/opencode/definitely-missing-ruff-independent"
env = dict(os.environ)
env["PYGPUI_RUFF"] = missing_ruff
completed = subprocess.run(
    [
        python_executable(),
        "tools/ci/run_local_gate.py",
        "--repository",
        str(root),
        "--mode",
        "full",
    ],
    cwd=REPO,
    env=env,
    text=True,
    capture_output=True,
    check=False,
)
print("MISSING_RUFF_STDOUT_BEGIN")
print(completed.stdout, end="")
print("MISSING_RUFF_STDOUT_END")
print("MISSING_RUFF_STDERR_BEGIN")
print(completed.stderr, end="")
print("MISSING_RUFF_STDERR_END")
record(
    "configured_missing_ruff_must_return_dependency_exit_69",
    completed.returncode == 69,
    f"expected exit=69 actual exit={completed.returncode}",
)

summary = {
    "checks": results,
    "failed": [result["name"] for result in results if not result["passed"]],
    "passed": all(result["passed"] for result in results),
}
print("ADVERSARIAL_SUMMARY=" + json.dumps(summary, sort_keys=True))
raise SystemExit(0 if summary["passed"] else 1)
