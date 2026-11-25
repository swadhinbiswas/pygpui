#!/usr/bin/env python3
"""Run the foundational fmt, lint, test and task-graph gates with distinct fail-closed exit codes."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ci.common import GateError, python_executable

CommandRunner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]
STEP_EXIT_CODES = {"fmt": 10, "lint": 11, "tests": 12, "graph": 13}


def _default_runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GateError(
            "dependency", f"cannot execute {command[0]}: {error}"
        ) from error


def _resolve_ruff(explicit: str | None) -> str:
    configured = explicit or os.environ.get("PYGPUI_RUFF")
    if configured:
        return configured
    found = shutil.which("ruff")
    if found:
        return found
    raise GateError(
        "dependency", "ruff is required; set PYGPUI_RUFF to its executable path"
    )


def run_local_gate(
    root: Path,
    *,
    mode: str = "full",
    ruff: str | None = None,
    command_runner: CommandRunner | None = None,
) -> tuple[int, list[dict[str, object]]]:
    if mode != "full":
        raise GateError("usage", f"unsupported local gate mode: {mode}")
    root = root.resolve()
    ruff_path = _resolve_ruff(ruff)
    runner = command_runner or _default_runner
    commands = [
        ("fmt", [ruff_path, "format", "--check", "tools"]),
        ("lint", [ruff_path, "check", "tools"]),
        (
            "tests",
            [
                python_executable(),
                "-m",
                "pytest",
                "-q",
                "tools/ci/tests",
                ".harness/scripts/tests",
            ],
        ),
        ("graph", [python_executable(), ".harness/scripts/validate_phase1_graph.py"]),
    ]
    steps: list[dict[str, object]] = []
    for name, command in commands:
        result = runner(command, root)
        steps.append(
            {
                "name": name,
                "command": command,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(
                result.stderr,
                end="" if result.stderr.endswith("\n") else "\n",
                file=sys.stderr,
            )
        if result.returncode != 0:
            print(
                f"LOCAL_GATE=FAIL step={name} exit={result.returncode} gate_exit={STEP_EXIT_CODES[name]}"
            )
            return STEP_EXIT_CODES[name], steps
        print(f"LOCAL_GATE_STEP=PASS step={name} exit=0")
    print("LOCAL_GATE=PASS steps=fmt,lint,tests,graph")
    return 0, steps


def self_test() -> None:
    def successful(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, "", "")

    code, steps = run_local_gate(
        Path.cwd(), ruff="/fixture/ruff", command_runner=successful
    )
    if code != 0 or [step["name"] for step in steps] != [
        "fmt",
        "lint",
        "tests",
        "graph",
    ]:
        raise AssertionError("local gate self-test did not run the full ordered suite")

    def failing(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, "", "")

    code, steps = run_local_gate(
        Path.cwd(), ruff="/fixture/ruff", command_runner=failing
    )
    if code != 10 or len(steps) != 1:
        raise AssertionError(
            "local gate self-test did not fail fast with the fmt exit code"
        )

    try:
        run_local_gate(
            Path.cwd(),
            ruff="/tmp/opencode/definitely-missing-ruff-self-test",
        )
    except GateError as error:
        if error.code != "dependency":
            raise AssertionError(
                f"expected dependency rejection, got {error.code}: {error.message}"
            ) from error
    else:
        raise AssertionError("configured missing Ruff unexpectedly executed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--repository", default=".")
    parser.add_argument("--mode", choices=["full"], default="full")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        print("LOCAL_GATE_SELF_TEST=PASS")
        return 0
    try:
        code, _ = run_local_gate(Path(args.repository), mode=args.mode)
        return code
    except GateError as error:
        print(
            f"LOCAL_GATE_REJECT code={error.code} message={error.message}",
            file=sys.stderr,
        )
        return 69 if error.code == "dependency" else 3


if __name__ == "__main__":
    raise SystemExit(main())
