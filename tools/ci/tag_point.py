#!/usr/bin/env python3
"""Create and verify annotated immutable Git tag points for rollback drills."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import (
    TAG_RE,
    GateError,
    canonical_repo_path,
    git_output,
    load_json,
    require_commit,
    run_git,
    write_json,
)


def _tag_ref(tag: str) -> str:
    if (
        not isinstance(tag, str)
        or not TAG_RE.fullmatch(tag)
        or ".." in tag
        or "@{" in tag
    ):
        raise GateError("tag", f"invalid tag name: {tag}")
    return f"refs/tags/{tag}"


def create_tag(root: Path, tag: str, commit: str, output: str) -> dict[str, Any]:
    root = root.resolve()
    ref = _tag_ref(tag)
    if run_git(root, "check-ref-format", ref, check=False).returncode != 0:
        raise GateError("tag", f"invalid tag ref: {tag}")
    commit = require_commit(root, commit, "tag commit")
    canonical_repo_path(root, output)
    if run_git(root, "show-ref", "--verify", ref, check=False).returncode == 0:
        raise GateError("tag", f"tag already exists: {tag}")
    run_git(
        root,
        "tag",
        "-a",
        tag,
        commit,
        "-m",
        f"pygpui immutable tag point {tag} at {commit}",
    )
    tag_object = git_output(root, "rev-parse", ref)
    if git_output(root, "cat-file", "-t", ref) != "tag":
        raise GateError("tag", "created tag is not annotated")
    record = {
        "schema_version": 1,
        "tag": tag,
        "ref": ref,
        "commit": commit,
        "tag_object_sha": tag_object,
        "record_path": output,
        "annotated": True,
    }
    write_json(root / output, record, overwrite=False)
    return record


def verify_tag(
    root: Path, tag: str, output: str, expected_commit: str | None = None
) -> dict[str, Any]:
    root = root.resolve()
    ref = _tag_ref(tag)
    canonical_repo_path(root, output)
    record = load_json(root / output)
    if (
        record.get("schema_version") != 1
        or record.get("tag") != tag
        or record.get("ref") != ref
        or record.get("record_path") != output
        or record.get("annotated") is not True
    ):
        raise GateError("tag", "tag record identity is invalid")
    if run_git(root, "show-ref", "--verify", ref, check=False).returncode != 0:
        raise GateError("tag", f"tag is absent: {tag}")
    if git_output(root, "cat-file", "-t", ref) != "tag":
        raise GateError("tag", "tag is not annotated")
    tag_object = git_output(root, "rev-parse", ref)
    commit = git_output(root, "rev-parse", f"{ref}^{{commit}}")
    if record.get("tag_object_sha") != tag_object:
        raise GateError("tag", "tag object moved after its record was created")
    if record.get("commit") != commit:
        raise GateError("tag", "tag commit moved after its record was created")
    if expected_commit is not None and commit != require_commit(
        root, expected_commit, "expected tag commit"
    ):
        raise GateError("tag", "tag does not point at the expected commit")
    return record


def self_test() -> None:
    from tools.ci.tests.helpers import git, make_repository

    with tempfile.TemporaryDirectory(
        prefix="tag-point-self-test-", dir="/tmp/opencode"
    ) as directory:
        root = Path(directory)
        base, source = make_repository(root)
        output = "evidence/P1-TOOL-BRANCH01/fixture-tag.json"
        create_tag(root, "phase1/contracts-premerge", source, output)
        verify_tag(root, "phase1/contracts-premerge", output, source)
        git(root, "tag", "-f", "-a", "phase1/contracts-premerge", base, "-m", "moved")
        try:
            verify_tag(root, "phase1/contracts-premerge", output, source)
        except GateError as error:
            if error.code != "tag":
                raise
        else:
            raise AssertionError("moved tag unexpectedly verified")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", nargs="?", choices=["create", "verify"], default="create"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--tag")
    parser.add_argument("--commit")
    parser.add_argument("--expected-commit")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("TAG_POINT_SELF_TEST=PASS")
        return 0
    try:
        if not args.tag or not args.output:
            raise GateError("usage", "--tag and --output are required")
        root = Path(args.repository).resolve()
        if args.command == "create":
            commit = args.commit or git_output(root, "rev-parse", "HEAD")
            record = create_tag(root, args.tag, commit, args.output)
            print(
                f"TAG_POINT_CREATE=PASS tag={args.tag} commit={record['commit']} output={args.output}"
            )
        else:
            record = verify_tag(root, args.tag, args.output, args.expected_commit)
            print(
                f"TAG_POINT_VERIFY=PASS tag={args.tag} commit={record['commit']} output={args.output}"
            )
        return 0
    except GateError as error:
        print(
            f"TAG_POINT_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
