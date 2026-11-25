#!/usr/bin/env python3
"""Rehearse tag → merge → failure → revert → gate → revert-of-revert → re-merge → gate in a disposable fixture."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import GateError
from tools.ci.fixture_git import (
    archive,
    assert_production_unchanged,
    fixture_gate,
    git,
    initialize_fixture,
    snapshot_production,
    validate_fixture,
)
from tools.ci.tag_point import create_tag, verify_tag


def _expect_gate(result: dict[str, Any], expected: str, label: str) -> None:
    if result["status"] != expected:
        raise GateError(
            "fixture", f"{label} expected {expected}, got {result['status']}"
        )


def run_rollback_drill(
    fixture: Path,
    tag: str,
    production_root: Path | None = None,
) -> dict[str, Any]:
    fixture = validate_fixture(fixture)
    production_root = (production_root or Path.cwd()).resolve()
    log: list[dict[str, Any]] = []
    before = snapshot_production(production_root, log)
    work, remote, baseline = initialize_fixture(fixture, "rollback_drill.py", log)

    tag_output = "evidence/tag-record.json"
    tag_record = create_tag(work, tag, baseline, tag_output)
    verify_tag(work, tag, tag_output, baseline)

    git(work, "switch", "-c", "fixture/contracts", log=log)
    (work / "contract.txt").write_text("fixture contract\n", encoding="utf-8")
    git(work, "add", "contract.txt", log=log)
    git(work, "commit", "-m", "test: add fixture contract", log=log)
    git(work, "switch", "main", log=log)
    git(
        work,
        "merge",
        "--no-ff",
        "fixture/contracts",
        "-m",
        "test: simulated reviewed contract merge",
        log=log,
    )
    reviewed_merge_sha = git(work, "rev-parse", "HEAD", log=log)
    _expect_gate(fixture_gate(work, log), "pass", "gate after reviewed fixture merge")

    (work / "state.txt").write_text("red\n", encoding="utf-8")
    git(work, "commit", "-am", "test: inject fixture failure", log=log)
    injected_failure_sha = git(work, "rev-parse", "HEAD", log=log)
    _expect_gate(fixture_gate(work, log), "fail", "gate after injected failure")

    git(work, "revert", "--no-edit", injected_failure_sha, log=log)
    revert_sha = git(work, "rev-parse", "HEAD", log=log)
    gate_after_revert = fixture_gate(work, log)
    _expect_gate(gate_after_revert, "pass", "gate after revert")

    git(work, "revert", "--no-edit", revert_sha, log=log)
    revert_of_revert_sha = git(work, "rev-parse", "HEAD", log=log)
    gate_after_revert_of_revert = fixture_gate(work, log)
    _expect_gate(gate_after_revert_of_revert, "fail", "gate after revert-of-revert")

    git(work, "switch", "-c", "fixture/remerge-green", log=log)
    (work / "state.txt").write_text("green\n", encoding="utf-8")
    git(work, "commit", "-am", "test: re-merge fixture restoration", log=log)
    remerge_commit = git(work, "rev-parse", "HEAD", log=log)
    git(work, "switch", "main", log=log)
    git(
        work,
        "merge",
        "--no-ff",
        "fixture/remerge-green",
        "-m",
        "test: simulated reviewed re-merge",
        log=log,
    )
    remerge_sha = git(work, "rev-parse", "HEAD", log=log)
    gate_after_remerge = fixture_gate(work, log)
    _expect_gate(gate_after_remerge, "pass", "gate after re-merge")
    restored_green_sha = git(work, "rev-parse", "HEAD", log=log)
    git(work, "push", "origin", "main", log=log)
    fixture_origin_main = git(work, "rev-parse", "origin/main", log=log)
    if fixture_origin_main != restored_green_sha:
        raise GateError(
            "fixture", "fixture origin/main does not point at restored green"
        )
    tags = git(work, "tag", "--list", log=log).splitlines()
    if tag not in tags:
        raise GateError("fixture", "rollback tag is absent from the restored fixture")

    after = snapshot_production(production_root, log)
    assert_production_unchanged(before, after)
    result: dict[str, Any] = {
        "schema_version": 1,
        "fixture": True,
        "independent_evidence": False,
        "fixture_remote": str(remote),
        "tag": tag,
        "tag_commit": baseline,
        "tag_record": tag_record,
        "reviewed_merge_sha": reviewed_merge_sha,
        "injected_failure_sha": injected_failure_sha,
        "revert_sha": revert_sha,
        "gate_after_revert": gate_after_revert,
        "revert_of_revert_sha": revert_of_revert_sha,
        "gate_after_revert_of_revert": gate_after_revert_of_revert,
        "remerge_commit": remerge_commit,
        "remerge_sha": remerge_sha,
        "gate_after_remerge": gate_after_remerge,
        "restored_green_sha": restored_green_sha,
        "fixture_origin_main": fixture_origin_main,
        "tags": tags,
        "review_mode": "simulated-two-parent-fixture-merges",
        "production_before": before,
        "production_after": after,
        "production_unchanged": True,
        "pull_requests": [
            {
                "fixture": True,
                "kind": "reviewed-contract-merge",
                "merge_sha": reviewed_merge_sha,
                "review": "simulated-two-parent-fixture-merge",
            },
            {
                "fixture": True,
                "kind": "revert",
                "merge_sha": revert_sha,
                "review": "simulated-fixture-revert",
            },
            {
                "fixture": True,
                "kind": "remerge-restoration",
                "merge_sha": remerge_sha,
                "review": "simulated-two-parent-fixture-merge",
            },
        ],
    }
    archive(fixture, result, log)
    return result


def self_test() -> None:
    from tools.ci.tests.helpers import make_repository

    with tempfile.TemporaryDirectory(
        prefix="rollback-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        production = root / "production"
        make_repository(production)
        result = run_rollback_drill(
            root / "rollback", "phase1/contracts-premerge", production_root=production
        )
        if (
            result["gate_after_remerge"]["status"] != "pass"
            or not result["production_unchanged"]
        ):
            raise AssertionError("rollback self-test did not restore green safely")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument("--tag")
    parser.add_argument(
        "--repository", default=".", help="production repository observed read-only"
    )
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("ROLLBACK_DRILL_SELF_TEST=PASS")
        return 0
    try:
        if not args.fixture or not args.tag:
            raise GateError("usage", "--fixture and --tag are required")
        result = run_rollback_drill(Path(args.fixture), args.tag, Path(args.repository))
        print(
            "ROLLBACK_DRILL=PASS "
            f"fixture={Path(args.fixture).resolve()} tag={args.tag} "
            f"revert={result['revert_sha']} revert_of_revert={result['revert_of_revert_sha']} "
            f"restored_green={result['restored_green_sha']} production_unchanged=true"
        )
        return 0
    except GateError as error:
        print(
            f"ROLLBACK_DRILL_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
