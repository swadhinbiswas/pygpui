#!/usr/bin/env python3
"""Independent P0-REM07 static semantic audit; never mutates repository files."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p0_rem07_audit_validator", ROOT / ".harness/scripts/validate_phase1_graph.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

ATTACK_SPEC = importlib.util.spec_from_file_location(
    "p0_rem07_audit_attacks", Path(__file__).with_name("attack_probe.py")
)
ATTACKS = importlib.util.module_from_spec(ATTACK_SPEC)
assert ATTACK_SPEC.loader is not None
ATTACK_SPEC.loader.exec_module(ATTACKS)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "63beab0")
BY_ID = {task["id"]: task for task in DATA["tasks"]}
PHASE1 = [task for task in DATA["tasks"] if task["id"].startswith("P1-")]
SUB_GATES = {
    sub["id"]: (task["id"], sub)
    for task in PHASE1
    for sub in task.get("sub_gates", [])
}


def options(text: str) -> dict[str, str]:
    words = text.split(" exits zero", 1)[0].split()
    return {words[i]: words[i + 1] for i in range(len(words) - 1) if words[i].startswith("--")}


def aggregate(task_id: str, gate: str) -> str:
    return next(
        text for text in BY_ID[task_id]["acceptance_criteria"]
        if "tools/gates/aggregate.py" in text and f"--gate {gate}" in text
    )


errors, _ = VALIDATOR.validate(DATA, PLAN, BASELINE, ROOT, HISTORY)
print(
    f"TASKS={len(DATA['tasks'])} PHASE1={len(PHASE1)} "
    f"EDGES={sum(len(task['deps']) for task in DATA['tasks'])}"
)
print(
    f"GATES={len(DATA['gate_model'])} SUB_GATES={len(SUB_GATES)} "
    f"STAGED_FULL_GATES={sum(bool(model['required_sub_gates']) for model in DATA['gate_model'].values())}"
)
print(f"BASE_GRAPH_ERRORS={len(errors)}")

results = [result for task in PHASE1 for result in task.get("gate_results", [])]
paths = [result["path"] for result in results]
lifecycle_errors: list[str] = []
self_overwrites: list[str] = []
for owner in PHASE1:
    criteria = owner["acceptance_criteria"]
    for result in owner.get("gate_results", []):
        path = result["path"]
        creates = [
            i for i, text in enumerate(criteria)
            if ("write_result.py" in text or "aggregate.py" in text) and f"--output {path}" in text
        ]
        validates = [
            i for i, text in enumerate(criteria)
            if "validate_result.py" in text and f"--result {path}" in text
        ]
        if len(creates) != 1 or len(validates) != 1 or creates[0] >= validates[0]:
            lifecycle_errors.append(path)
        if any("aggregate.py" in criteria[i] and f"--inputs {path}" in criteria[i] for i in creates):
            self_overwrites.append(path)
    for gate in owner.get("gates", []):
        model = DATA["gate_model"][gate]
        if not model["required_sub_gates"]:
            continue
        opts = options(aggregate(owner["id"], gate))
        expected = [SUB_GATES[sub][1]["evidence"] for sub in model["required_sub_gates"]]
        if opts["--inputs"].split(",") != expected:
            lifecycle_errors.append(f"{owner['id']}:{gate}:inputs")
        if opts["--output"] in opts["--inputs"].split(","):
            self_overwrites.append(opts["--output"])
print(f"RESULT_PATHS={len(paths)} UNIQUE_RESULT_PATHS={len(set(paths))}")
print(f"LIFECYCLE_ORDER_ERRORS={len(lifecycle_errors)}")
print(f"AGGREGATE_SELF_OVERWRITES={len(self_overwrites)}")

builds = [task for task in PHASE1 if task["workflow"] == "build"]
print(f"BUILD_TASKS={len(builds)} MERGED_COMPLETION={sum(task['completion_state'] == 'merged' for task in builds)}")
for task_id in ("P1-SESSION-REGISTRY01", "P1-GATE-SCHEMA01"):
    owner = BY_ID[task_id]
    print(
        f"{task_id}_WORKFLOW={owner['workflow']} COMPLETION={owner['completion_state']} "
        f"PREMERGE={owner['premerge_state']} POSTMERGE={owner['postmerge_state']} "
        f"REVIEW={bool(owner['review_evidence'])} TEST={bool(owner['test_evidence'])} "
        f"MERGE_RECORD={bool(owner['postmerge_record'])}"
    )

seed = BY_ID["P1-SESSION-SEED01"]
print(f"REGISTRY_EXISTS_AT_BASELINE={(ROOT / '.harness/sessions/registry.json').exists()}")
print(
    "SEED_PRECEDES_FIRST_BUILD="
    + str("P1-SESSION-SEED01" in BY_ID["P1-TOOL-BRANCH01"]["deps"]
          and not VALIDATOR._reachable("P1-SESSION-SEED01", BY_ID, "P1-TOOL-BRANCH01"))
)
print(f"SEED_REGISTRY_PRODUCER={'.harness/sessions/registry.json' in seed['produces']}")

for gate in ("AR09-G1", "AR10-G3"):
    opts = options(aggregate("P1-PR-AUDIT01", gate))
    print(f"{gate}_REQUIRED={DATA['gate_model'][gate]['required_sub_gates']}")
    print(f"{gate}_INPUTS={opts['--inputs']}")
pr_criteria = BY_ID["P1-PR-AUDIT01"]["acceptance_criteria"]
print(
    "PR_IDENTITY_CAPTURE="
    + str(any("gh pr view" in text and "--json number,headRefOid,baseRefOid,author,state" in text for text in pr_criteria))
)
print(
    "PR_CHANGED_FILES_CAPTURE="
    + str(any("gh pr diff" in text and "--name-only" in text for text in pr_criteria))
)

for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
    criteria = BY_ID[task_id]["acceptance_criteria"]
    fetch = next(i for i, text in enumerate(criteria) if "gh release download" in text)
    verify = next(i for i, text in enumerate(criteria) if "store.py verify" in text)
    audits = [i for i, text in enumerate(criteria) if "audit_artifacts.py" in text or "provenance_audit.py --mode artifact" in text]
    download_dir = options(criteria[fetch])["--dir"]
    print(
        f"{task_id}_FETCH={fetch} VERIFY={verify} AUDITS={audits} "
        f"ORDER_OK={fetch < verify < min(audits)} DOWNLOAD_DIR={download_dir} "
        f"AUDITS_USE_DOWNLOAD_DIR={all(download_dir in criteria[i] for i in audits)} "
        f"IGNORED_DIST_REFS={VALIDATOR._ignored_artifact_refs(chr(10).join(criteria))}"
    )

for variant in ("dist/release/*.whl", "dist/local/*.whl", "dist/./release/*.whl", "dist/{release,local}/*.whl", "dist/*/*.whl", "dist"):
    print(f"DIST_VARIANT={variant} DETECTED={bool(VALIDATOR._ignored_artifact_refs(variant))}")

for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
    criteria = BY_ID[task_id]["acceptance_criteria"]
    write = next(i for i, text in enumerate(criteria) if "write_result.py" in text)
    validate = next(i for i, text in enumerate(criteria) if "validate_result.py" in text)
    approval = next(i for i, text in enumerate(criteria) if "verify_approval.py" in text)
    proof = next(i for i, text in enumerate(criteria) if "verify_proof.py" in text and "--gate-result" in text)
    print(
        f"{task_id}_WRITE={write} VALIDATE={validate} VERIFY_APPROVAL={approval} VERIFY_PROOF={proof} "
        f"ORDER_OK={write < validate < approval < proof} "
        f"REACHES_LOCK_PRODUCER={VALIDATOR._reachable(task_id, BY_ID, 'P1-ARCH01')} "
        f"HAS_NOT_APPLICABLE={'--lockfile-state not_applicable' in criteria[write]}"
    )

print(f"P0_AP01={BY_ID['P0-AP01']['status']}/attempt{BY_ID['P0-AP01']['attempt_count']}")
print(
    "ALL_PHASE1_BLOCKED_ATTEMPT0="
    + str(all(task["status"] == "blocked" and task["attempt_count"] == 0 for task in PHASE1))
)

accepted = 0
for name, mutate in ATTACKS.ATTACKS:
    changed = copy.deepcopy(DATA)
    mutate(changed)
    attack_errors, _ = VALIDATOR.validate(changed, PLAN, BASELINE, ROOT, HISTORY)
    accepted += not attack_errors
    print(f"NEW_ATTACK={name} ACCEPTED={not attack_errors} ERRORS={attack_errors}")
print(f"NEW_ATTACKS_TOTAL={len(ATTACKS.ATTACKS)} NEW_ATTACKS_ACCEPTED={accepted}")

self_test = subprocess.run(
    ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"), "--self-test"],
    cwd=ROOT, text=True, capture_output=True,
)
print(f"SEED_DOCUMENTED_SELF_TEST_EXIT={self_test.returncode}")

with tempfile.TemporaryDirectory(dir="/tmp/opencode") as directory:
    registry = Path(directory) / "registry.json"
    approval_path = Path(directory) / "seed-approval.json"
    command = [
        "python3", str(ROOT / ".harness/scripts/seed_session_registry.py"),
        "--output", str(registry), "--approval", str(approval_path),
    ]
    first = subprocess.run(command + ["--orchestrator-session", "orch-1"], cwd=ROOT, text=True, capture_output=True)
    approval_data = json.loads(approval_path.read_text())
    actual_hash = hashlib.sha256(registry.read_bytes()).hexdigest()
    before = set(json.loads(registry.read_text())["sessions"])
    second = subprocess.run(command + ["--orchestrator-session", "orch-2"], cwd=ROOT, text=True, capture_output=True)
    after = set(json.loads(registry.read_text())["sessions"])
    print(f"SEED_FIRST_EXIT={first.returncode} SEED_SECOND_EXIT={second.returncode}")
    print(f"SEED_APPROVAL_REGISTRY_SHA256={approval_data['registry_sha256']}")
    print(f"SEED_ACTUAL_REGISTRY_SHA256={actual_hash}")
    print(f"SEED_APPROVAL_HASH_MATCHES_FILE={approval_data['registry_sha256'] == actual_hash}")
    print(f"SEED_RESEED_APPEND_ONLY_PRESERVED={before.issubset(after)}")

print("UNRESOLVED_DEFECTS=7")
print("D11=registry seed command/hash/append-only/output binding is incomplete")
print("D12=duplicate CLI flags bypass canonical result identity and lifecycle checks")
print("D13=approval command artifact/registry/scope bindings are not enforced")
print("D14=gh PR capture can discard real output and substitute fabricated artifacts")
print("D15=post-merge command/record task and path identity are not enforced")
print("D16=artifact fetch/verify/audit manifest and path binding is incomplete")
print("D17=ignored-dist normalization misses shell-escaped spellings")
print("EXIT_CODE=0")
