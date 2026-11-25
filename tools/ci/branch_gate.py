#!/usr/bin/env python3
"""Fail closed unless a branch has distinct trusted review/test evidence and, when merged, an Integrator record."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import GateError, load_json, write_json
from tools.ci.evidence import verify_branch


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
    from tools.ci.record_merge import create_merge_record
    from tools.ci.tests.helpers import (
        BRANCH_EVIDENCE,
        MERGE_EVIDENCE,
        REVIEW_EVIDENCE,
        TASK_ID,
        git,
        make_repository,
        merge_metadata,
        refresh_reference,
        write_bundle,
    )

    with tempfile.TemporaryDirectory(
        prefix="branch-gate-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        base, source = make_repository(root, with_origin=True)
        evidence = write_bundle(root, base, source)
        original = (root / BRANCH_EVIDENCE).read_bytes()
        verify_branch(root, TASK_ID, BRANCH_EVIDENCE, "independently_verified")

        missing_reviewer = dict(evidence)
        missing_reviewer.pop("reviewer_session_id")
        write_json(root / BRANCH_EVIDENCE, missing_reviewer)
        _expect_rejection(
            verify_branch,
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "independently_verified",
            code="role",
        )
        missing_tester = dict(evidence)
        missing_tester.pop("tester_session_id")
        write_json(root / BRANCH_EVIDENCE, missing_tester)
        _expect_rejection(
            verify_branch,
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "independently_verified",
            code="role",
        )
        reused = dict(evidence)
        reused["tester_session_id"] = reused["reviewer_session_id"]
        write_json(root / BRANCH_EVIDENCE, reused)
        _expect_rejection(
            verify_branch,
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "independently_verified",
            code="role",
        )
        write_json(root / BRANCH_EVIDENCE, json.loads(original))
        review = load_json(root / REVIEW_EVIDENCE)
        review["source_commit"] = base
        write_json(root / REVIEW_EVIDENCE, review)
        refresh_reference(root, evidence, "review")
        write_json(root / BRANCH_EVIDENCE, evidence)
        _expect_rejection(
            verify_branch,
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "independently_verified",
            code="commit",
        )
        # Rebuild the bundle so referenced hashes are exact before testing merged state.
        evidence = write_bundle(root, base, source)
        _expect_rejection(
            verify_branch,
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "merged",
            code="merge",
        )
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
        create_merge_record(
            root,
            TASK_ID,
            str(metadata["url"]),
            merge_sha,
            MERGE_EVIDENCE,
            metadata,
        )
        verify_branch(
            root,
            TASK_ID,
            BRANCH_EVIDENCE,
            "merged",
            pr_metadata=metadata,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["verify"], default="verify")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--task")
    parser.add_argument("--state", choices=["independently_verified", "merged"])
    parser.add_argument("--evidence")
    parser.add_argument("--record")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("BRANCH_GATE_SELF_TEST=PASS")
        return 0
    try:
        missing = [
            name for name in ("task", "state", "evidence") if not getattr(args, name)
        ]
        if missing:
            raise GateError(
                "usage",
                f"verify requires --task, --state and --evidence; missing {missing}",
            )
        verified = verify_branch(
            Path(args.repository).resolve(),
            args.task,
            args.evidence,
            args.state,
            record_path=args.record,
        )
        print(
            "BRANCH_GATE_VERIFY=PASS "
            f"task={args.task} state={args.state} commit={verified.source_commit} "
            f"artifact={verified.evidence['artifact_id']} reviewer={verified.evidence['reviewer_session_id']} "
            f"tester={verified.evidence['tester_session_id']}"
        )
        return 0
    except GateError as error:
        print(
            f"BRANCH_GATE_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
