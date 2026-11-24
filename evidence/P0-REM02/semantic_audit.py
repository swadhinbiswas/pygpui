#!/usr/bin/env python3
"""Static independent semantic audit for P0-REM02; does not modify the graph."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import shlex
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p0_rem02_audit_validator", ROOT / ".harness/scripts/validate_phase1_graph.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
SCHEMA = json.loads((ROOT / ".harness/schemas/gate-results.schema.json").read_text())
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "b9a8504")
BY_ID = {task["id"]: task for task in DATA["tasks"]}
PHASE1 = [task for task in DATA["tasks"] if task["id"].startswith("P1-")]
SUB_GATES = {
    sub["id"]: (task["id"], sub)
    for task in PHASE1
    for sub in task.get("sub_gates", [])
}
STAGED = {gate: model for gate, model in DATA["gate_model"].items() if model["required_sub_gates"]}


def options(criterion: str) -> dict[str, str]:
    words = shlex.split(criterion.split(" exits zero", 1)[0])
    return {words[i]: words[i + 1] for i in range(len(words) - 1) if words[i].startswith("--")}


def aggregate(task_id: str, gate: str) -> str:
    return next(
        criterion for criterion in BY_ID[task_id]["acceptance_criteria"]
        if f"tools/gates/aggregate.py --gate {gate} " in criterion
    )


def errors_for(data: dict) -> list[str]:
    return VALIDATOR.validate(data, PLAN, BASELINE, ROOT, HISTORY)[0]


print(f"TASKS={len(DATA['tasks'])} PHASE1={len(PHASE1)} EDGES={sum(len(t['deps']) for t in DATA['tasks'])}")
print(f"GATES={len(DATA['gate_model'])} SUB_GATES={sum(len(t.get('sub_gates', [])) for t in PHASE1)} STAGED_FULL_GATES={len(STAGED)}")
print("STAGED_AGGREGATOR_AUDIT")
collisions = []
for gate, model in STAGED.items():
    owner = BY_ID[model["aggregator"]]
    opts = options(aggregate(owner["id"], gate))
    expected = {SUB_GATES[sub][1]["evidence"] for sub in model["required_sub_gates"]}
    exact_inputs = set(opts["--inputs"].split(",")) == expected
    schema_ok = any(
        "tools/gates/validate_result.py" in criterion
        and ".harness/schemas/gate-results.schema.json" in criterion
        for criterion in owner["acceptance_criteria"]
    )
    self_overwrite = opts["--output"] in opts["--inputs"].split(",")
    if self_overwrite:
        collisions.append(gate)
    print(
        f"{gate} owner={owner['id']} schema={schema_ok} exact_inputs={exact_inputs} "
        f"self_overwrite={self_overwrite} output={opts['--output']}"
    )
print(f"SELF_OVERWRITE_GATES={len(collisions)} {','.join(collisions)}")

multi = [
    task["id"] for task in PHASE1
    if len(task.get("gates", [])) + len(task.get("sub_gates", [])) > 1
]
print(f"MULTI_RESULT_SINGLE_FILE_TASKS={len(multi)} {','.join(multi)}")
print(f"SCHEMA_RESULT_TYPE={SCHEMA['type']}")

builds = [task for task in PHASE1 if task["workflow"] == "build"]
print(f"BUILD_TASKS={len(builds)} MERGED_COMPLETION={sum(t['completion_state'] == 'merged' for t in builds)}")
print(
    "BUILD_DIRECT_IMPLEMENTATION_DEPS="
    + str(sum(
        any(BY_ID[dep]["workflow"] == "implementation" for dep in task["deps"])
        for task in builds
    ))
)
for task_id in ("P1-RUSTCONTRACT01", "P1-CONREV01"):
    text = "\n".join(BY_ID[task_id]["acceptance_criteria"])
    print(
        f"{task_id}_BRANCH_CHECK={'branch_gate.py verify' in text} "
        f"SESSION_CHECK={'verify_roles.py' in text} MERGED={BY_ID[task_id]['completion_state'] == 'merged'}"
    )
int_text = "\n".join(BY_ID["P1-INT01"]["acceptance_criteria"])
print(
    "INT01_PREMERGE=" + str("--task P1-SLICE01 --state independently_verified" in int_text)
    + " RECORD=" + str("record_merge.py --task P1-SLICE01" in int_text)
    + " VERIFY=" + str("record_merge.py verify --task P1-SLICE01" in int_text)
)

for gate in ("AR09-G1", "AR10-G3"):
    opts = options(aggregate("P1-PR-AUDIT01", gate))
    print(f"{gate}_INPUTS={opts['--inputs']} REQUIRED={','.join(DATA['gate_model'][gate]['required_sub_gates'])}")
print("AR04_G6_MSRV_AUDIT=" + str(any("audit_msrv_claim.py" in c for c in BY_ID["P1-REL02"]["acceptance_criteria"])))

for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
    criteria = BY_ID[task_id]["acceptance_criteria"]
    audit = next(i for i, c in enumerate(criteria) if "dist/release/**" in c)
    fetch = next(i for i, c in enumerate(criteria) if "gh release download" in c)
    print(
        f"{task_id}_DIST_AUDIT_INDEX={audit} FETCH_INDEX={fetch} "
        f"FETCH_DIR={options(criteria[fetch])['--dir']}"
    )

print(
    "REL02_REACHES_WAYLAND=" + str(VALIDATOR._reachable("P1-REL02", BY_ID, "P1-WAYLAND-GATE01"))
    + " REL02_REACHES_CLAIM_READY=" + str(VALIDATOR._reachable("P1-REL02", BY_ID, "P1-READY-CLAIM01"))
)
print(
    "READINESS_RENAMED=" + str("P1-READY-BENCH01" not in BY_ID and "P1-READY-RELEASE01" not in BY_ID)
    + " OWNER_NOTICE_DEP=" + str("P1-OWNER-NOTICE01" in BY_ID["P1-LICENSE-CLOSE01"]["deps"])
)
print("PYTEST_TESTPATHS=" + str("testpaths = .harness/scripts/tests" in (ROOT / "pytest.ini").read_text()))
print(f"P0_AP01={BY_ID['P0-AP01']['status']}/attempt{BY_ID['P0-AP01']['attempt_count']}")

approval = {
    "schema_version": 1,
    "gate_id": "AR08-G6.approval",
    "task_id": "P1-READY-CERT01",
    "stage": "approval",
    "status": "pass",
    "evidence_type": "user-approval",
    "evidence": [{"path": "evidence/P1-READY-CERT01/gate-results.json", "sha256": "a" * 64}],
    "source_commit": "b" * 40,
    "lockfile_sha256": "c" * 64,
    "toolchain": "rustc 1.100.0",
    "reviewer_session_id": "reviewer-1",
    "tester_session_id": "tester-1",
    "approver_session_id": "forged-approver",
    "aggregator": False,
}
jsonschema.validate(approval, SCHEMA)
print("FORGED_APPROVER_SCHEMA_VALID=True")
for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
    print(
        f"{task_id}_REACHES_LOCK_PRODUCER={VALIDATOR._reachable(task_id, BY_ID, 'P1-ARCH01')} "
        f"HAS_LOCK_COMMAND={any('Cargo.lock' in c for c in BY_ID[task_id]['acceptance_criteria'])}"
    )

mutated = copy.deepcopy(DATA)
owner = next(t for t in mutated["tasks"] if t["id"] == "P1-LIC02")
owner.pop("consumes_artifacts")
owner["acceptance_criteria"] = [
    c for c in owner["acceptance_criteria"]
    if "gh release download" not in c and "tools/artifacts/store.py verify" not in c
]
owner["acceptance_criteria"] = [c.replace("dist/release/**", "dist/release/*.whl") for c in owner["acceptance_criteria"]]
print(f"VALIDATOR_ACCEPTS_DIST_WILDCARD_BYPASS={not errors_for(mutated)}")

mutated = copy.deepcopy(DATA)
owner = next(t for t in mutated["tasks"] if t["id"] == "P1-PR-AUDIT01")
owner["acceptance_criteria"] = [
    c for c in owner["acceptance_criteria"]
    if "test_pr_policy.py" not in c and "pr_audit_gate.py" not in c
]
print(f"VALIDATOR_ACCEPTS_NO_ENFORCEMENT_COMMAND={not errors_for(mutated)}")

print("DEFECT D1: single-object gate-results paths are reused by multiple results; eight aggregators overwrite an input and PR-AUDIT01 overwrites its first full-gate output with its second.")
print("DEFECT D2: P1-SESSION-REGISTRY01 and P1-GATE-SCHEMA01 produce code but complete recorded with no independent review or merge record.")
print("DEFECT D3: AR09-G1/AR10-G3 aggregate only LIC01 repository evidence; per-PR enforcement is not staged evidence and can be removed without validator rejection.")
print("DEFECT D4: LIC02/LICENSE-CLOSE01 audit dist/release before fetching, and fetch into evidence downloads rather than the audited dist/release path.")
print("DEFECT D5: ignored-artifact detection matches only literal dist/release/** and dist/local/**; dist/release/*.whl bypasses it.")
print("DEFECT D6: approval records accept an unbound approver ID and require a lockfile hash although neither approval task reaches the Cargo.lock producer or hashes it.")
print("UNRESOLVED_REMEDIATION_DEFECTS=6")
