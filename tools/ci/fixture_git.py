"""Safety and Git helpers shared by disposable red-main and rollback drills."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

from tools.ci.common import GateError, write_json

APPROVED_FIXTURE_ROOT = Path("/tmp/opencode")


def validate_fixture(path: Path) -> Path:
    if not path.is_absolute():
        raise GateError(
            "fixture", "fixture path must be absolute and under /tmp/opencode"
        )
    approved = APPROVED_FIXTURE_ROOT.resolve()
    resolved = path.resolve()
    if resolved == approved or not resolved.is_relative_to(approved):
        raise GateError("fixture", f"fixture escapes approved disposable root: {path}")
    if path.is_symlink():
        raise GateError("fixture", "fixture path must not be a symlink")
    if resolved.exists() and any(resolved.iterdir()):
        raise GateError("fixture", f"fixture must be absent or empty: {path}")
    return resolved


def run_command(
    command: list[str],
    cwd: Path,
    log: list[dict[str, Any]],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, check=False
    )
    log.append(
        {
            "command": shlex.join(command),
            "cwd": str(cwd),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    if check and result.returncode != 0:
        raise GateError(
            "fixture",
            f"fixture command failed: {shlex.join(command)}: {result.stderr.strip()}",
        )
    return result


def git(root: Path, *args: str, log: list[dict[str, Any]], check: bool = True) -> str:
    result = run_command(["git", *args], root, log, check=check)
    return result.stdout.strip()


def initialize_fixture(
    fixture: Path, tool: str, log: list[dict[str, Any]]
) -> tuple[Path, Path, str]:
    fixture.mkdir(parents=True, exist_ok=True)
    write_json(
        fixture / ".pygpui-fixture.json",
        {
            "approved_root": str(APPROVED_FIXTURE_ROOT.resolve()),
            "created_by": tool,
            "fixture": True,
            "production": False,
            "schema_version": 1,
        },
    )
    remote = fixture / "origin.git"
    work = fixture / "work"
    run_command(
        ["git", "init", "--bare", "--initial-branch=main", str(remote)], fixture, log
    )
    run_command(["git", "init", "-b", "main", str(work)], fixture, log)
    git(work, "config", "user.name", "Disposable Fixture", log=log)
    git(work, "config", "user.email", "fixture@example.invalid", log=log)
    git(work, "remote", "add", "origin", str(remote), log=log)
    (work / "state.txt").write_text("green\n", encoding="utf-8")
    (work / "baseline.txt").write_text("fixture baseline\n", encoding="utf-8")
    gate = work / "full-gate.sh"
    gate.write_text(
        "#!/bin/sh\nset -eu\n"
        'test "$(cat state.txt)" = "green"\n'
        "test -f baseline.txt\n"
        "git diff --check\n"
        "git fsck --no-dangling\n",
        encoding="utf-8",
    )
    gate.chmod(0o755)
    git(work, "add", ".", log=log)
    git(work, "commit", "-m", "test: disposable green baseline", log=log)
    baseline = git(work, "rev-parse", "HEAD", log=log)
    git(work, "push", "-u", "origin", "main", log=log)
    return work, remote, baseline


def snapshot_production(root: Path, log: list[dict[str, Any]]) -> dict[str, Any]:
    result = run_command(
        ["git", "rev-parse", "--show-toplevel"], root, log, check=False
    )
    if result.returncode != 0:
        raise GateError(
            "production", f"production root is not a Git repository: {root}"
        )
    remotes = (
        run_command(["git", "remote", "-v"], root, log).stdout.strip().splitlines()
    )
    refs = run_command(
        ["git", "for-each-ref", "--format=%(refname) %(objectname)", "refs/remotes/"],
        root,
        log,
    ).stdout.splitlines()
    main_refs = sorted(
        line
        for line in refs
        if line.startswith("refs/remotes/") and line.split(" ", 1)[0].endswith("/main")
    )
    head = run_command(["git", "rev-parse", "HEAD"], root, log).stdout.strip()
    return {
        "head": head,
        "main_refs": main_refs,
        "remotes": remotes,
        "root": str(root.resolve()),
    }


def assert_production_unchanged(before: dict[str, Any], after: dict[str, Any]) -> None:
    if before != after:
        raise GateError(
            "production",
            "production repository refs or remotes changed during the fixture drill",
        )


def fixture_origin_main(work: Path, log: list[dict[str, Any]]) -> str:
    result = run_command(
        ["git", "ls-remote", "--exit-code", "origin", "refs/heads/main"],
        work,
        log,
    )
    fields = result.stdout.split()
    if len(fields) != 2 or fields[1] != "refs/heads/main":
        raise GateError("fixture", "fixture origin/main remote ref is invalid")
    return fields[0]


def clone_fixture_gate(
    remote: Path, destination: Path, log: list[dict[str, Any]]
) -> dict[str, Any]:
    run_command(
        ["git", "clone", str(remote), str(destination)], destination.parent, log
    )
    return fixture_gate(destination, log)


def fixture_gate(work: Path, log: list[dict[str, Any]]) -> dict[str, Any]:
    result = run_command(["./full-gate.sh"], work, log, check=False)
    status = "pass" if result.returncode == 0 else "fail"
    return {
        "exit_code": result.returncode,
        "status": status,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def archive(fixture: Path, value: dict[str, Any], log: list[dict[str, Any]]) -> None:
    write_json(fixture / "archive.json", value)
    lines = [
        line
        for entry in log
        for line in (
            f"$ (cwd={entry['cwd']}) {entry['command']}",
            f"exit={entry['exit_code']}",
            entry["stdout"],
            entry["stderr"],
        )
    ]
    (fixture / "commands.txt").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )
