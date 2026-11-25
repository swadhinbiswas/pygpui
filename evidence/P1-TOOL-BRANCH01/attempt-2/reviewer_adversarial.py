from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/tmp/opencode/pygpui-P1-TOOL-BRANCH01")
sys.path.insert(0, str(REPO))

from tools.ci.common import canonical_json_bytes, load_json, sha256_bytes, write_json
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


def record(name: str, accepted: bool, detail: str) -> None:
    results.append({"name": name, "accepted": accepted, "detail": detail})
    print(f"{'ACCEPTED' if accepted else 'REJECTED'} {name}: {detail}")


def commit_evidence(root: Path, message: str) -> str:
    git(root, "add", ".")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


with tempfile.TemporaryDirectory(
    prefix="reviewer-adversarial-", dir="/tmp/opencode"
) as directory:
    base_dir = Path(directory)

    root = base_dir / "independent-flag"
    base, source = make_repository(root)
    evidence = write_bundle(root, base, source)
    evidence["independent_evidence"] = False
    write_json(root / BRANCH_EVIDENCE, evidence)
    try:
        verify_branch(root, TASK_ID, BRANCH_EVIDENCE, "independently_verified")
    except Exception as error:  # evidence capture only
        record("independent_evidence_false", False, repr(error))
    else:
        record(
            "independent_evidence_false",
            True,
            "verify_branch accepted state=independently_verified with independent_evidence=false",
        )

    root = base_dir / "record-role"
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
    try:
        verify_premerge(root, TASK_ID, BRANCH_EVIDENCE)
    except Exception as error:
        record("contradictory_record_roles", False, repr(error))
    else:
        record(
            "contradictory_record_roles",
            True,
            "review role=implementer and test role=reviewer were accepted",
        )

    root = base_dir / "unreviewed-descendant"
    base, source = make_repository(root)
    write_bundle(root, base, source)
    commit_evidence(root, "test: commit evidence after reviewed source")
    (root / "fixture.txt").write_text("unreviewed code change\n", encoding="utf-8")
    git(root, "add", "fixture.txt")
    git(root, "commit", "-m", "feat: unreviewed post-source change")
    unreviewed_head = git(root, "rev-parse", "HEAD")
    verify_premerge(root, TASK_ID, BRANCH_EVIDENCE)
    changed = git(root, "diff", "--name-only", source, unreviewed_head)
    git(root, "switch", "main")
    git(
        root,
        "merge",
        "--no-ff",
        f"feat/{TASK_ID}-tooling",
        "-m",
        "test: merge unreviewed descendant",
    )
    merge_sha = git(root, "rev-parse", "HEAD")
    metadata = merge_metadata(root, unreviewed_head, merge_sha)
    create_merge_record(
        root,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    verify_branch(root, TASK_ID, BRANCH_EVIDENCE, "merged")
    record(
        "unreviewed_descendant_head",
        True,
        f"source={source} merged_head={unreviewed_head} changed={changed!r}",
    )

    root = base_dir / "external-pr"
    base, source = make_repository(root)
    write_bundle(root, base, source)
    git(root, "remote", "add", "origin", "https://github.com/swadhinbiswas/pygpui.git")
    evidence_head = commit_evidence(root, "test: commit evidence")
    git(root, "switch", "main")
    git(
        root,
        "merge",
        "--no-ff",
        f"feat/{TASK_ID}-tooling",
        "-m",
        "test: external PR fixture merge",
    )
    merge_sha = git(root, "rev-parse", "HEAD")
    metadata = merge_metadata(root, evidence_head, merge_sha)
    metadata["url"] = "https://github.com/attacker/pygpui/pull/1"
    create_merge_record(
        root,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    record(
        "external_repository_pr",
        True,
        "origin=swadhinbiswas/pygpui but attacker/pygpui PR metadata was accepted",
    )

    root = base_dir / "offline-forged-merge"
    base, source = make_repository(root)
    write_bundle(root, base, source)
    evidence_head = commit_evidence(root, "test: commit evidence")
    git(root, "switch", "-c", "fixture/side")
    (root / "side.txt").write_text("side branch only\n", encoding="utf-8")
    git(root, "add", "side.txt")
    git(root, "commit", "-m", "test: side branch not merged")
    side_head = git(root, "rev-parse", "HEAD")
    git(root, "switch", f"feat/{TASK_ID}-tooling")
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
    metadata = merge_metadata(root, evidence_head, merge_sha)
    create_merge_record(
        root,
        TASK_ID,
        str(metadata["url"]),
        merge_sha,
        MERGE_EVIDENCE,
        metadata,
    )
    forged = load_json(root / MERGE_EVIDENCE)
    forged["pr_url"] = "https://github.com/attacker/pygpui/pull/42"
    forged["number"] = 42
    forged["merged_at"] = "2099-01-01T00:00:00Z"
    forged["head_oid"] = side_head
    payload = dict(forged)
    payload.pop("record_id", None)
    forged["record_id"] = sha256_bytes(canonical_json_bytes(payload))
    write_json(root / MERGE_EVIDENCE, forged)
    verify_merge_record(root, TASK_ID, MERGE_EVIDENCE, merge_sha)
    verify_branch(root, TASK_ID, BRANCH_EVIDENCE, "merged")
    ancestry = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", side_head, merge_sha],
        check=False,
        capture_output=True,
        text=True,
    )
    record(
        "offline_forged_merge_record",
        True,
        f"forged PR URL/head accepted; side_head={side_head} merge_sha={merge_sha} side_is_ancestor={ancestry.returncode == 0}",
    )

    production = base_dir / "production"
    make_repository(production)
    fixture = base_dir / "red-main"
    drill = run_red_main_drill(fixture, production_root=production)
    commands = (fixture / "commands.txt").read_text(encoding="utf-8")
    pushes = [line for line in commands.splitlines() if line.startswith("$ ") and "git push" in line]
    record(
        "red_main_fixture_remote_never_red",
        True,
        f"push_count={len(pushes)} red_main={drill['red_main_sha']} final_origin_main={drill['fixture_origin_main']} pushes={pushes}",
    )

    production = base_dir / "empty-production"
    make_repository(production)
    empty = base_dir / "empty-fixture"
    empty.mkdir()
    try:
        run_red_main_drill(empty, production_root=production)
    except Exception as error:
        record("existing_empty_fixture", False, f"{type(error).__name__}: {error}")
    else:
        record("existing_empty_fixture", True, "existing empty fixture was accepted")

summary = {
    "probes": results,
    "accepted_control_bypasses": [
        item["name"]
        for item in results
        if item["accepted"]
        and item["name"]
        in {
            "independent_evidence_false",
            "contradictory_record_roles",
            "unreviewed_descendant_head",
            "external_repository_pr",
            "offline_forged_merge_record",
        }
    ],
}
print("REVIEWER_ADVERSARIAL_SUMMARY=" + json.dumps(summary, sort_keys=True))
