#!/usr/bin/env python3
"""Independent P0-REM07 adversarial probes; repository files are never mutated."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p0_rem07_graph_validator", ROOT / ".harness/scripts/validate_phase1_graph.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "63beab0")


def task(data: dict, task_id: str) -> dict:
    return next(item for item in data["tasks"] if item["id"] == task_id)


def criterion(task_data: dict, needle: str) -> tuple[int, str]:
    return next(
        (index, text)
        for index, text in enumerate(task_data["acceptance_criteria"])
        if needle in text
    )


def duplicate_write_gate(data: dict) -> None:
    owner = task(data, "P1-TST01")
    index, text = criterion(owner, "write_result.py --gate AR02-G1.integrated-properties")
    owner["acceptance_criteria"][index] = text.replace(
        "--gate AR02-G1.integrated-properties",
        "--gate AR02-G1.integrated-properties --gate AR02-G1.schema",
    )


def duplicate_write_task(data: dict) -> None:
    owner = task(data, "P1-TST01")
    index, text = criterion(owner, "write_result.py --gate AR02-G1.integrated-properties")
    owner["acceptance_criteria"][index] = text.replace(
        "--task P1-TST01", "--task P1-TST01 --task P1-PROTO01"
    )


def duplicate_validate_result(data: dict) -> None:
    owner = task(data, "P1-TST01")
    index, text = criterion(owner, "validate_result.py --schema")
    text = next(
        text
        for text in owner["acceptance_criteria"]
        if "validate_result.py" in text
        and "--result evidence/P1-TST01/AR02-G1.integrated-properties.json" in text
    )
    index = owner["acceptance_criteria"].index(text)
    owner["acceptance_criteria"][index] = text.replace(
        "--result evidence/P1-TST01/AR02-G1.integrated-properties.json",
        "--result evidence/P1-TST01/AR02-G1.integrated-properties.json "
        "--result evidence/P1-TST01/AR02-G1.schema.json",
    )


def duplicate_aggregate_inputs(data: dict) -> None:
    owner = task(data, "P1-TST01")
    index, text = criterion(owner, "aggregate.py --gate AR02-G1")
    owner["acceptance_criteria"][index] = text.replace(
        "--output evidence/P1-TST01/AR02-G1.json",
        "--output evidence/P1-TST01/AR02-G1.json "
        "--inputs evidence/P1-TST01/./AR02-G1.json",
    )


def duplicate_aggregate_output(data: dict) -> None:
    owner = task(data, "P1-TST01")
    index, text = criterion(owner, "aggregate.py --gate AR02-G1")
    owner["acceptance_criteria"][index] = text.replace(
        "--output evidence/P1-TST01/AR02-G1.json",
        "--output evidence/P1-TST01/AR02-G1.json "
        "--output evidence/P1-PROTO01/AR02-G1.schema.json",
    )


def approval_binding_flags_removed(data: dict) -> None:
    owner = task(data, "P1-READY-CERT01")
    index, text = criterion(owner, "write_result.py --gate AR08-G6.approval")
    for flag in (
        "--approval-artifact evidence/P1-READY-CERT01/approval.json",
        "--approval-registry .harness/sessions/registry.json",
        "--approval-scope performance-certification",
    ):
        text = text.replace(flag + " ", "")
    owner["acceptance_criteria"][index] = text


def approval_binding_values_changed(data: dict) -> None:
    owner = task(data, "P1-READY-CERT01")
    index, text = criterion(owner, "write_result.py --gate AR08-G6.approval")
    owner["acceptance_criteria"][index] = (
        text.replace("evidence/P1-READY-CERT01/approval.json", "evidence/P1-READY-CERT01/forged.json")
        .replace(".harness/sessions/registry.json", ".harness/sessions/untrusted.json")
        .replace("--approval-scope performance-certification", "--approval-scope unrelated-claim")
    )


def fabricated_pr_capture(data: dict) -> None:
    owner = task(data, "P1-PR-AUDIT01")
    criteria = owner["acceptance_criteria"]
    view_index = next(i for i, text in enumerate(criteria) if "gh pr view" in text)
    diff_index = next(i for i, text in enumerate(criteria) if "gh pr diff" in text)
    criteria[view_index] = (
        "gh pr view <pr-number> --json number,headRefOid,baseRefOid,author,state > /dev/null "
        "&& printf '%s\\n' '{\"number\":1,\"headRefOid\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\","
        "\"baseRefOid\":\"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\",\"author\":{\"login\":\"forged\"},"
        "\"state\":\"OPEN\"}' > evidence/P1-PR-AUDIT01/pr.json exits zero"
    )
    criteria[diff_index] = (
        "gh pr diff <pr-number> --name-only > /dev/null "
        "&& printf '%s\\n' 'README.md' > evidence/P1-PR-AUDIT01/changed-files.txt exits zero"
    )


def seed_writes_noncanonical_registry(data: dict) -> None:
    owner = task(data, "P1-SESSION-SEED01")
    criteria = owner["acceptance_criteria"]
    seed_index = next(i for i, text in enumerate(criteria) if "seed_session_registry.py --orchestrator-session" in text)
    hash_index = next(i for i, text in enumerate(criteria) if text.startswith("sha256sum "))
    criteria[seed_index] = criteria[seed_index].replace(
        "--output .harness/sessions/registry.json --approval .harness/sessions/seed-approval.json",
        "--output evidence/P1-SESSION-SEED01/registry.json "
        "--approval evidence/P1-SESSION-SEED01/seed-approval.json",
    )
    criteria[hash_index] = (
        "sha256sum evidence/P1-SESSION-SEED01/registry.json "
        "evidence/P1-SESSION-SEED01/seed-approval.json "
        "> evidence/P1-SESSION-SEED01/seed-sha256.txt exits zero"
    )


def postmerge_command_wrong_identity(data: dict) -> None:
    owner = task(data, "P1-TOOL-BRANCH01")
    owner["postmerge_command"] = owner["postmerge_command"].replace(
        "--task P1-TOOL-BRANCH01", "--task P1-GATE-SCHEMA01"
    ).replace(
        "--output evidence/P1-TOOL-BRANCH01/merge.json",
        "--output evidence/P1-GATE-SCHEMA01/merge.json",
    )


def postmerge_record_wrong_path(data: dict) -> None:
    owner = task(data, "P1-TOOL-BRANCH01")
    owner["postmerge_record"] = "evidence/P1-GATE-SCHEMA01/merge.json"


def artifact_verifies_wrong_manifest(data: dict) -> None:
    owner = task(data, "P1-LIC02")
    index, text = criterion(owner, "store.py verify")
    owner["acceptance_criteria"][index] = text.replace(
        "artifacts/release/<artifact-id>/manifest.json",
        "artifacts/local/<artifact-id>/manifest.json",
    )


def artifact_equals_dir_bypasses_audit_path_check(data: dict) -> None:
    owner = task(data, "P1-LIC02")
    criteria = owner["acceptance_criteria"]
    fetch_index = next(i for i, text in enumerate(criteria) if "gh release download" in text)
    criteria[fetch_index] = criteria[fetch_index].replace(
        "--dir evidence/P1-LIC02/downloads", "--dir=evidence/P1-LIC02/downloads"
    )
    for index, text in enumerate(criteria):
        if "audit_artifacts.py" in text or "provenance_audit.py --mode artifact" in text:
            criteria[index] = text.replace("evidence/P1-LIC02/downloads/**", "somewhere-else/**")


def escaped_dist_path(data: dict) -> None:
    owner = task(data, "P1-LIC02")
    owner["acceptance_criteria"].append(
        "python3 tools/release/clean_install_matrix.py --artifacts d\\ist/release/*.whl exits zero"
    )


ATTACKS: list[tuple[str, Callable[[dict], None]]] = [
    ("D1/D7 duplicate write_result --gate", duplicate_write_gate),
    ("D1/D7 duplicate write_result --task", duplicate_write_task),
    ("D1 duplicate validate_result --result", duplicate_validate_result),
    ("D1 duplicate aggregate --inputs", duplicate_aggregate_inputs),
    ("D1 duplicate aggregate --output", duplicate_aggregate_output),
    ("D6 approval binding flags removed", approval_binding_flags_removed),
    ("D6 approval binding values changed", approval_binding_values_changed),
    ("D9 gh output discarded for fabricated PR artifacts", fabricated_pr_capture),
    ("D8 seed writes noncanonical registry", seed_writes_noncanonical_registry),
    ("D2 postmerge command wrong task/output", postmerge_command_wrong_identity),
    ("D2 postmerge record wrong path", postmerge_record_wrong_path),
    ("D4 verify uses wrong artifact manifest", artifact_verifies_wrong_manifest),
    ("D4 --dir= bypasses downloaded-path audit check", artifact_equals_dir_bypasses_audit_path_check),
    ("D10 backslash-escaped dist path", escaped_dist_path),
]


def main() -> int:
    base_errors, _ = VALIDATOR.validate(DATA, PLAN, BASELINE, ROOT, HISTORY)
    print(f"BASE_GRAPH_ERRORS={len(base_errors)}")
    accepted = 0
    for name, mutate in ATTACKS:
        changed = copy.deepcopy(DATA)
        mutate(changed)
        errors, _ = VALIDATOR.validate(changed, PLAN, BASELINE, ROOT, HISTORY)
        if not errors:
            accepted += 1
        print(f"ATTACK={name} ACCEPTED={not errors} ERRORS={errors}")
    print(f"ATTACKS_TOTAL={len(ATTACKS)} ATTACKS_ACCEPTED={accepted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
