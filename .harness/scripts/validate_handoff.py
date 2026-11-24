#!/usr/bin/env python3
"""Validate the Planner -> Red-Team Part 3 handoff for attempt 2."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIELDS = [
    "FROM:",
    "TO:",
    "TASK-ID:",
    "ATTEMPT #:",
    "STATUS:",
    "WHAT I WAS ASKED:",
    "WHAT I DID:",
    "EVIDENCE:",
    "WHAT I DID NOT DO / SKIPPED, AND WHY:",
    "OPEN RISKS & SURPRISES:",
    "EXACT NEXT STEP:",
    "FILES THE RECEIVER MUST READ (ordered, max 7):",
    "CONTEXT I WISH I HAD HAD:",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        default=".harness/HANDOFFS/planner-to-red-team-P0-RT01-3.md",
    )
    parser.add_argument("--attempt", type=int, default=3)
    parser.add_argument("--task-id", default="P0-PL01")
    parser.add_argument("--to", default="Red-Team-Planner")
    args = parser.parse_args()
    text = Path(args.path).read_text(encoding="utf-8")
    missing = [field for field in FIELDS if field not in text]
    errors: list[str] = []
    if missing:
        errors.append(f"missing fields: {missing}")
    for expected in (
        "FROM: Planner",
        f"TO: {args.to}",
        f"TASK-ID: {args.task_id}",
        f"ATTEMPT #: {args.attempt}",
        "STATUS: done",
    ):
        if expected not in text:
            errors.append(f"missing header: {expected}")
    next_step_match = re.search(r"EXACT NEXT STEP:(.*?)(?=FILES THE RECEIVER|$)", text, re.S)
    next_step = next_step_match.group(1).strip() if next_step_match else ""
    if not next_step.startswith(f"{args.to}:"):
        errors.append(f"EXACT NEXT STEP does not direct {args.to}")
    files_match = re.search(
        r"FILES THE RECEIVER MUST READ \(ordered, max 7\):(.*?)(?=CONTEXT I WISH I HAD HAD:|$)",
        text,
        re.S,
    )
    files = re.findall(r"^\d+\. ", files_match.group(1), re.M) if files_match else []
    if not files or len(files) > 7:
        errors.append(f"receiver file list must contain 1-7 entries, found {len(files)}")
    if errors:
        print("HANDOFF_FIELDS=FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"HANDOFF_FIELDS=PASS fields={len(FIELDS)}/{len(FIELDS)} files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
