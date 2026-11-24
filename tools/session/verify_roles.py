#!/usr/bin/env python3
"""Verify task-bound implementer, reviewer, tester and Integrator roles against the approved append-only registry."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import GateError, load_json, write_json
from tools.ci.evidence import verify_premerge


def _expect_rejection(function, *args, code: str) -> None:
    try:
        function(*args)
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
        TASK_ID,
        make_repository,
        write_bundle,
    )

    with tempfile.TemporaryDirectory(
        prefix="verify-roles-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        base, source = make_repository(root)
        evidence = write_bundle(root, base, source)
        verify_premerge(root, TASK_ID, BRANCH_EVIDENCE)
        forged = dict(evidence)
        forged["reviewer_session_id"] = "forged-reviewer"
        write_json(root / BRANCH_EVIDENCE, forged)
        _expect_rejection(verify_premerge, root, TASK_ID, BRANCH_EVIDENCE, code="role")
        mismatched = dict(evidence)
        mismatched["tester_session_id"] = mismatched["reviewer_session_id"]
        write_json(root / BRANCH_EVIDENCE, mismatched)
        _expect_rejection(verify_premerge, root, TASK_ID, BRANCH_EVIDENCE, code="role")
        registry = load_json(root / ".harness/sessions/registry.json")
        registry["sessions"]["reviewer-1"]["task_id"] = "P1-INT01"
        write_json(root / ".harness/sessions/registry.json", registry)
        _expect_rejection(
            verify_premerge, root, TASK_ID, BRANCH_EVIDENCE, code="registry"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--task")
    parser.add_argument("--evidence")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("SESSION_ROLES_SELF_TEST=PASS")
        return 0
    try:
        if not args.task or not args.evidence:
            raise GateError("usage", "--task and --evidence are required")
        verified = verify_premerge(
            Path(args.repository).resolve(), args.task, args.evidence
        )
        print(
            "SESSION_ROLES_VERIFY=PASS "
            f"task={args.task} implementer={verified.evidence['implementer_session_id']} "
            f"reviewer={verified.evidence['reviewer_session_id']} tester={verified.evidence['tester_session_id']} "
            f"integrator={verified.evidence.get('integrator_session_id', 'unassigned')} "
            f"registry_sha256={verified.registry_digest}"
        )
        return 0
    except GateError as error:
        print(
            f"SESSION_ROLES_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
