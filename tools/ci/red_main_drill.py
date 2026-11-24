#!/usr/bin/env python3
"""Rehearse red-main detection and restoration using only a disposable /tmp/opencode fixture remote."""

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
    clone_fixture_gate,
    fixture_gate,
    fixture_origin_main,
    git,
    initialize_fixture,
    snapshot_production,
    validate_fixture,
)


def run_red_main_drill(
    fixture: Path, production_root: Path | None = None
) -> dict[str, Any]:
    fixture = validate_fixture(fixture)
    production_root = (production_root or Path.cwd()).resolve()
    log: list[dict[str, Any]] = []
    before = snapshot_production(production_root, log)
    work, remote, baseline = initialize_fixture(fixture, "red_main_drill.py", log)

    git(work, "switch", "-c", "fixture/red-main", log=log)
    (work / "state.txt").write_text("red\n", encoding="utf-8")
    git(work, "commit", "-am", "test: inject fixture red main", log=log)
    red_commit = git(work, "rev-parse", "HEAD", log=log)
    git(work, "switch", "main", log=log)
    git(
        work,
        "merge",
        "--no-ff",
        "fixture/red-main",
        "-m",
        "test: simulated reviewed red merge",
        log=log,
    )
    red_main_sha = git(work, "rev-parse", "HEAD", log=log)
    gate_on_red = fixture_gate(work, log)
    if gate_on_red["status"] != "fail":
        raise GateError("fixture", "red-main fixture gate unexpectedly passed")
    git(work, "push", "origin", "main", log=log)
    fixture_red_origin_main = fixture_origin_main(work, log)
    if fixture_red_origin_main != red_main_sha:
        raise GateError("fixture", "fixture origin/main was not pushed to red")
    gate_on_remote_red = clone_fixture_gate(remote, fixture / "remote-red-check", log)
    if gate_on_remote_red["status"] != "fail":
        raise GateError("fixture", "fixture remote red clone gate unexpectedly passed")

    git(work, "switch", "-c", "fixture/restore-main", log=log)
    (work / "state.txt").write_text("green\n", encoding="utf-8")
    git(work, "commit", "-am", "test: restore fixture green main", log=log)
    restore_commit = git(work, "rev-parse", "HEAD", log=log)
    git(work, "switch", "main", log=log)
    git(
        work,
        "merge",
        "--no-ff",
        "fixture/restore-main",
        "-m",
        "test: simulated reviewed restoration",
        log=log,
    )
    restored_green_sha = git(work, "rev-parse", "HEAD", log=log)
    gate_after_fix = fixture_gate(work, log)
    if gate_after_fix["status"] != "pass":
        raise GateError("fixture", "restored fixture gate did not pass")
    git(work, "push", "origin", "main", log=log)
    restored_fixture_origin_main = fixture_origin_main(work, log)
    if restored_fixture_origin_main != restored_green_sha:
        raise GateError(
            "fixture", "fixture origin/main does not point at restored green"
        )
    gate_on_remote_green = clone_fixture_gate(
        remote, fixture / "remote-green-check", log
    )
    if gate_on_remote_green["status"] != "pass":
        raise GateError("fixture", "fixture remote green clone gate did not pass")

    after = snapshot_production(production_root, log)
    assert_production_unchanged(before, after)
    result: dict[str, Any] = {
        "schema_version": 1,
        "fixture": True,
        "independent_evidence": False,
        "fixture_remote": str(remote),
        "baseline_sha": baseline,
        "red_commit": red_commit,
        "red_main_sha": red_main_sha,
        "restore_commit": restore_commit,
        "restored_green_sha": restored_green_sha,
        "fixture_red_origin_main": fixture_red_origin_main,
        "fixture_origin_main": restored_fixture_origin_main,
        "gate_on_red": gate_on_red,
        "gate_on_remote_red": gate_on_remote_red,
        "gate_after_fix": gate_after_fix,
        "gate_on_remote_green": gate_on_remote_green,
        "pause_unrelated_merges": True,
        "production_before": before,
        "production_after": after,
        "production_unchanged": True,
        "pull_requests": [
            {
                "fixture": True,
                "kind": "red-main-injection",
                "merge_sha": red_main_sha,
                "review": "simulated-two-parent-fixture-merge",
            },
            {
                "fixture": True,
                "kind": "restoration",
                "merge_sha": restored_green_sha,
                "review": "simulated-two-parent-fixture-merge",
            },
        ],
    }
    archive(fixture, result, log)
    return result


def self_test() -> None:
    from tools.ci.tests.helpers import make_repository

    with tempfile.TemporaryDirectory(
        prefix="red-main-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        production = root / "production"
        make_repository(production)
        result = run_red_main_drill(root / "red-main", production_root=production)
        if (
            result["gate_after_fix"]["status"] != "pass"
            or result["gate_on_remote_red"]["status"] != "fail"
            or result["gate_on_remote_green"]["status"] != "pass"
            or not result["production_unchanged"]
        ):
            raise AssertionError("red-main self-test did not restore green safely")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--fixture")
    parser.add_argument(
        "--repository", default=".", help="production repository observed read-only"
    )
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("RED_MAIN_DRILL_SELF_TEST=PASS")
        return 0
    try:
        if not args.fixture:
            raise GateError("usage", "--fixture is required")
        result = run_red_main_drill(Path(args.fixture), Path(args.repository))
        print(
            "RED_MAIN_DRILL=PASS "
            f"fixture={Path(args.fixture).resolve()} red_main={result['red_main_sha']} "
            f"restored_green={result['restored_green_sha']} production_unchanged=true"
        )
        return 0
    except GateError as error:
        print(
            f"RED_MAIN_DRILL_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
