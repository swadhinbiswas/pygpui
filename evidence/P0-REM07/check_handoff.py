#!/usr/bin/env python3
"""Check the P0-REM07 Test-Engineer handoff Part 3 contract."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(".harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md")
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

text = PATH.read_text(encoding="utf-8")
missing = [field for field in FIELDS if field not in text]
files_match = re.search(
    r"FILES THE RECEIVER MUST READ \(ordered, max 7\):(.*?)(?=CONTEXT I WISH I HAD HAD:|$)",
    text,
    re.S,
)
files = re.findall(r"^\d+\. ", files_match.group(1), re.M) if files_match else []
next_match = re.search(r"EXACT NEXT STEP:(.*?)(?=FILES THE RECEIVER|$)", text, re.S)
next_step = next_match.group(1).strip() if next_match else ""
headers = {
    "from": "FROM: Test-Engineer" in text,
    "to": "TO: Red-Team-Planner" in text,
    "task": "TASK-ID: P0-REM07" in text,
    "attempt": "ATTEMPT #: 1" in text,
    "status_partial": "STATUS: partial" in text,
    "next_step": next_step.startswith("Red-Team-Planner:"),
}
ok = not missing and len(files) == 7 and all(headers.values())
print(f"HANDOFF_PART3={'PASS' if ok else 'FAIL'}")
print(f"fields={len(FIELDS) - len(missing)}/13 files={len(files)} status=partial")
print(f"MISSING={missing!r}")
print(f"HEADERS={headers!r}")
raise SystemExit(0 if ok else 1)
