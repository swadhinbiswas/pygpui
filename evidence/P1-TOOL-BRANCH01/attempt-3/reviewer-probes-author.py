from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path("/tmp/opencode/pygpui-P1-TOOL-BRANCH01")
sys.path.insert(0, str(REPO))

from tools.ci.common import (
    GateError,
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    write_json,
)
from tools.ci.evidence import verify_branch, verify_premerge
from tools.ci.record_merge import create_merge_record, verify_merge_record
from tools.ci.red_main_drill import run_red_main_drill
from tools.ci.tests.helpers import (
    BRANCH_EVIDENCE,
    MERGE_EVIDENCE,
    REVIEW_EVIDENCE,
    TASK_ID,
    TEST_EVIDENCE,
    git,
    make_repository,
    merge_metadata,
    refresh_reference,
    write_bundle,
)

results: list[dict[str, object]] = []


def rejected(name: str, function) -> None:
    try:
        function()
    except GateError as error:
        results.append({"name": name, "passed": True, "detail": f"{error.code}: {error.message}"})
        print(f"PASS {name}: {error.code}: {error.message}")
    else:
        results.append({"name": name, "passed": False, "detail": "unexpected acceptance"})
        print(f"FAIL {name}: unexpected acceptance")


with tempfile.TemporaryDirectory(prefix="attempt3-author-probes-", dir="/tmp/opencode") as directory:
    root = Path(directory) / "independent-flag"
    base, source = make_repository(root)
    evidence = write_bundle(root, base, source)
    evidence["independent_evidence"] = False
    write_json(root / BRANCH_EVIDENCE, evidence)
    rejected("R-01-independent-flag", lambda: verify_branch(root, TASK_ID, BRANCH_EVIDENCE, "independently_verified"))

    root = Path(directory) / "record-role"
    base, source = make_repository(root)
    evidence = write_bundle(root, base, source)
    review = load_json(root / REVIEW_EVIDENCE)
    review["role"] = "implementer"
    write_json(root / REVIEW_EVIDENCE, review)
    test = load_json(root / TEST_EVIDENCE)
    test["role"] = "reviewer"
    write_json(root / TEST_EVIDENCE, test)
    refresh_reference(root, evidence, "review")
    refresh_reference(root, evidence, "test")
    write_json(root / BRANCH_EVIDENCE, evidence)
    rejected("R-05-record-roles", lambda: verify_premerge(root, TASK_ID, BRANCH_EVIDENCE))

    root = Path(directory) / "unreviewed-descendant"
    base, source = make_repository(root)
    write_bundle(root, base, source)
    git(root, "add", f"evidence/{TASK_ID}")
    git(root, "commit", "-m", "test: evidence-only post-review commit")
    (root / "fixture.txt").write_text("unreviewed implementation\n", encoding="utf-8")
    git(root, "add", "fixture.txt")
    git(root, "commit", "-m", "feat: unreviewed implementation")
    rejected("R-02-unreviewed-descendant", lambda: verify_premerge(root, TASK_ID, BRANCH_EVIDENCE))

    root = Path(directory) / "offline-forged-merge"
    base, source = make_repository(root, with_origin=True)
    evidence = write_bundle(root, base, source)
    git(root, "add", f"evidence/{TASK_ID}")
    git(root, "commit", "-m", "test: evidence-only post-review commit")
    evidence_head = git(root, "rev-parse", "HEAD")
    git(root, "switch", "-c", "fixture/side")
    (root / "side.txt").write_text("side only\n", encoding="utf-8")
    git(root, "add", "side.txt")
    git(root, "commit", "-m", "test: unmerged side head")
    side_head = git(root, "rev-parse", "HEAD")
    git(root, "switch", f"feat/{TASK_ID}-tooling")
    git(root, "switch", "main")
    git(root, "merge", "--no-ff", f"feat/{TASK_ID}-tooling", "-m", "test: merge reviewed head")
    merge_sha = git(root, "rev-parse", "HEAD")
    evidence["merge_sha"] = merge_sha
    write_json(root / BRANCH_EVIDENCE, evidence)
    metadata = merge_metadata(root, evidence_head, merge_sha)
    create_merge_record(root, TASK_ID, str(metadata["url"]), merge_sha, MERGE_EVIDENCE, metadata)
    forged = load_json(root / MERGE_EVIDENCE)
    forged["head_oid"] = side_head
    payload = dict(forged)
    payload.pop("record_id")
    forged["record_id"] = sha256_bytes(canonical_json_bytes(payload))
    write_json(root / MERGE_EVIDENCE, forged)
    rejected("R-03-offline-forged-merge", lambda: verify_merge_record(root, TASK_ID, MERGE_EVIDENCE, merge_sha))

    root = Path(directory) / "wrong-repository"
    base, source = make_repository(root, with_origin=True)
    write_bundle(root, base, source)
    git(root, "add", f"evidence/{TASK_ID}")
    git(root, "commit", "-m", "test: evidence-only commit")
    head = git(root, "rev-parse", "HEAD")
    git(root, "switch", "main")
    git(root, "merge", "--no-ff", f"feat/{TASK_ID}-tooling", "-m", "test: merge")
    merge_sha = git(root, "rev-parse", "HEAD")
    metadata = merge_metadata(root, head, merge_sha)
    metadata["url"] = "https://github.com/attacker/pygpui/pull/1"
    rejected(
        "R-04-wrong-repository",
        lambda: create_merge_record(root, TASK_ID, str(metadata["url"]), merge_sha, MERGE_EVIDENCE, metadata),
    )

    production = Path(directory) / "production"
    make_repository(production)
    fixture = Path(directory) / "red-main"
    drill = run_red_main_drill(fixture, production_root=production)
    commands = (fixture / "commands.txt").read_text(encoding="utf-8")
    pushes = [line for line in commands.splitlines() if line.startswith("$ ") and "git push" in line]
    remote_ok = (
        drill["fixture_red_origin_main"] == drill["red_main_sha"]
        and drill["gate_on_remote_red"]["status"] == "fail"
        and drill["gate_on_remote_green"]["status"] == "pass"
        and len(pushes) == 3
    )
    results.append({"name": "R-06-remote-red-green", "passed": remote_ok, "detail": f"pushes={len(pushes)}"})
    print(f"{'PASS' if remote_ok else 'FAIL'} R-06-remote-red-green: pushes={len(pushes)}")

    production = Path(directory) / "empty-production"
    make_repository(production)
    empty = Path(directory) / "empty-fixture"
    empty.mkdir()
    try:
        run_red_main_drill(empty, production_root=production)
    except Exception as error:
        results.append({"name": "R-07-existing-empty", "passed": False, "detail": repr(error)})
        print(f"FAIL R-07-existing-empty: {error!r}")
    else:
        results.append({"name": "R-07-existing-empty", "passed": True, "detail": "accepted"})
        print("PASS R-07-existing-empty: accepted")

summary = {
    "author_run": True,
    "independent_evidence": False,
    "failed": [item["name"] for item in results if not item["passed"]],
    "passed": all(item["passed"] for item in results),
    "probes": results,
}
print("AUTHOR_REVIEWER_PROBES_SUMMARY=" + json.dumps(summary, sort_keys=True))
raise SystemExit(0 if summary["passed"] else 1)
