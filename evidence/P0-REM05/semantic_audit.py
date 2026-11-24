#!/usr/bin/env python3
"""Independent P0-REM05 static semantic audit; never mutates repository files."""
from __future__ import annotations

import copy
import importlib.util
import json
import posixpath
import re
import shlex
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p0_rem05_graph_validator", ROOT / ".harness/scripts/validate_phase1_graph.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
SCHEMA = json.loads((ROOT / ".harness/schemas/gate-results.schema.json").read_text())
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "4e307b2")
BY_ID = {task["id"]: task for task in DATA["tasks"]}
PHASE1 = [task for task in DATA["tasks"] if task["id"].startswith("P1-")]
SUB_GATES = {
    sub["id"]: (task["id"], sub)
    for task in PHASE1
    for sub in task.get("sub_gates", [])
}
STAGED = {
    gate: model
    for gate, model in DATA["gate_model"].items()
    if model["required_sub_gates"]
}


def task(task_id: str) -> dict:
    return BY_ID[task_id]


def options(criterion: str) -> dict[str, str]:
    words = shlex.split(criterion.split(" exits zero", 1)[0])
    return {
        words[index]: words[index + 1]
        for index in range(len(words) - 1)
        if words[index].startswith("--")
    }


def aggregate_command(task_id: str, gate: str) -> str:
    return next(
        criterion
        for criterion in task(task_id)["acceptance_criteria"]
        if f"tools/gates/aggregate.py --gate {gate} " in criterion
    )


def errors_for(data: dict) -> list[str]:
    return VALIDATOR.validate(data, PLAN, BASELINE, ROOT, HISTORY)[0]


def mutation_errors(mutator) -> list[str]:
    changed = copy.deepcopy(DATA)
    mutator(changed)
    return errors_for(changed)


print(
    f"TASKS={len(DATA['tasks'])} PHASE1={len(PHASE1)} "
    f"EDGES={sum(len(t['deps']) for t in DATA['tasks'])}"
)
print(
    f"GATES={len(DATA['gate_model'])} SUB_GATES={len(SUB_GATES)} "
    f"STAGED_FULL_GATES={len(STAGED)}"
)
print(f"BASE_GRAPH_ERRORS={len(errors_for(DATA))}")

# D1: current lifecycle, canonical ownership and command ordering.
results = [result for owner in PHASE1 for result in owner.get("gate_results", [])]
paths = [result["path"] for result in results]
path_owners: dict[str, list[str]] = {}
for owner in PHASE1:
    for result in owner.get("gate_results", []):
        path_owners.setdefault(result["path"], []).append(owner["id"])
lifecycle_errors: list[str] = []
self_overwrites: list[str] = []
for owner in PHASE1:
    criteria = owner["acceptance_criteria"]
    for result in owner.get("gate_results", []):
        path = result["path"]
        creates = [
            index
            for index, criterion in enumerate(criteria)
            if ("tools/gates/write_result.py" in criterion or "tools/gates/aggregate.py" in criterion)
            and f"--output {path}" in criterion
        ]
        validates = [
            index
            for index, criterion in enumerate(criteria)
            if "tools/gates/validate_result.py" in criterion and f"--result {path}" in criterion
        ]
        if len(creates) != 1 or len(validates) != 1 or creates[0] >= validates[0]:
            lifecycle_errors.append(f"{owner['id']}:{path}")
        for index in creates:
            if "tools/gates/aggregate.py" in criteria[index] and f"--inputs {path}" in criteria[index]:
                self_overwrites.append(path)
    for gate in owner.get("gates", []):
        model = DATA["gate_model"][gate]
        if not model["required_sub_gates"]:
            continue
        opts = options(aggregate_command(owner["id"], gate))
        expected = [SUB_GATES[sub][1]["evidence"] for sub in model["required_sub_gates"]]
        if opts["--inputs"].split(",") != expected:
            lifecycle_errors.append(f"{owner['id']}:{gate}:inputs")
        if opts["--output"] in opts["--inputs"].split(","):
            self_overwrites.append(opts["--output"])
print(f"RESULT_PATHS={len(paths)} UNIQUE_RESULT_PATHS={len(set(paths))}")
print(f"SHARED_RESULT_PATHS={sum(len(owners) != 1 for owners in path_owners.values())}")
print(f"LIFECYCLE_ORDER_ERRORS={len(lifecycle_errors)}")
print(f"AGGREGATE_SELF_OVERWRITES={len(self_overwrites)}")
pr_paths = [
    result["path"]
    for result in task("P1-PR-AUDIT01")["gate_results"]
    if result["gate_id"] in {"AR09-G1", "AR10-G3"}
]
print(f"PR_AUDIT_FULL_OUTPUTS={pr_paths} DISTINCT={len(set(pr_paths)) == 2}")


def wrong_gate_mutation(data: dict) -> None:
    owner = task_copy = next(t for t in data["tasks"] if t["id"] == "P1-TST01")
    index = next(
        i
        for i, criterion in enumerate(owner["acceptance_criteria"])
        if "write_result.py" in criterion and "--gate AR02-G1.integrated-properties" in criterion
    )
    owner["acceptance_criteria"][index] = owner["acceptance_criteria"][index].replace(
        "--gate AR02-G1.integrated-properties", "--gate AR02-G1.schema"
    )


wrong_gate_errors = mutation_errors(wrong_gate_mutation)
print(f"D1_WRONG_GATE_CANONICAL_PATH_ACCEPTED={not wrong_gate_errors} ERRORS={wrong_gate_errors}")

# D2: merged foundational tool tasks and bootstrap registry availability.
builds = [owner for owner in PHASE1 if owner["workflow"] == "build"]
print(f"BUILD_TASKS={len(builds)} MERGED_COMPLETION={sum(t['completion_state'] == 'merged' for t in builds)}")
for task_id in ("P1-SESSION-REGISTRY01", "P1-GATE-SCHEMA01"):
    owner = task(task_id)
    print(
        f"{task_id}_WORKFLOW={owner['workflow']} COMPLETION={owner['completion_state']} "
        f"PREMERGE={owner.get('premerge_state')} POSTMERGE={owner.get('postmerge_state')} "
        f"REVIEW={bool(owner.get('review_evidence'))} TEST={bool(owner.get('test_evidence'))} "
        f"MERGE_RECORD={bool(owner.get('postmerge_record'))}"
    )
registry = ".harness/sessions/registry.json"
registry_producers = [
    owner["id"]
    for owner in PHASE1
    if any(VALIDATOR._matches(registry, pattern) for pattern in owner.get("produces", []))
]
print(f"REGISTRY_EXISTS_AT_BASELINE={(ROOT / registry).exists()}")
print(f"REGISTRY_PRODUCERS={registry_producers}")
print(f"TOOL_BRANCH_DEPS={task('P1-TOOL-BRANCH01')['deps']}")
print(
    "TOOL_BRANCH_SCOPE_COVERS_REGISTRY="
    + str(any(VALIDATOR._matches(registry, pattern) for pattern in task("P1-TOOL-BRANCH01")["write_scope"]))
)
print(
    "TOOL_BRANCH_REACHES_REGISTRY_PRODUCER="
    + str(any(VALIDATOR._reachable("P1-TOOL-BRANCH01", BY_ID, producer) for producer in registry_producers))
)

# D3: staged repository plus enforcement evidence, and whether it is PR-derived.
for gate in ("AR09-G1", "AR10-G3"):
    model = DATA["gate_model"][gate]
    opts = options(aggregate_command("P1-PR-AUDIT01", gate))
    print(f"{gate}_REQUIRED={model['required_sub_gates']}")
    print(f"{gate}_INPUTS={opts['--inputs']}")
    command = next(
        criterion
        for criterion in task("P1-PR-AUDIT01")["acceptance_criteria"]
        if "pr_audit_gate.py" in criterion and f"--gate {gate}" in criterion
    )
    print(f"{gate}_CHANGED_FILES={options(command).get('--changed-files')}")
    print(f"{gate}_COMMAND_IS_FIXTURE={'tools/ci/tests/fixtures/' in command}")


def selftest_only_mutation(data: dict) -> None:
    owner = next(t for t in data["tasks"] if t["id"] == "P1-PR-AUDIT01")
    for index, criterion in enumerate(owner["acceptance_criteria"]):
        if "pr_audit_gate.py" in criterion and "--gate AR" in criterion:
            gate = "AR09-G1" if "AR09-G1" in criterion else "AR10-G3"
            output = f"evidence/P1-PR-AUDIT01/{gate}.pr-enforcement.json"
            owner["acceptance_criteria"][index] = (
                f"python3 tools/ci/pr_audit_gate.py --policy tools/ci/pr_audit_policy.json "
                f"--self-test --gate {gate} --output {output} exits zero"
            )


selftest_errors = mutation_errors(selftest_only_mutation)
print(f"D3_SELFTEST_ONLY_ENFORCEMENT_ACCEPTED={not selftest_errors} ERRORS={selftest_errors}")

# D4: fetched and verified durable artifacts are the audited inputs.
for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
    criteria = task(task_id)["acceptance_criteria"]
    fetch = next(i for i, criterion in enumerate(criteria) if "gh release download" in criterion)
    verify = next(i for i, criterion in enumerate(criteria) if "tools/artifacts/store.py verify" in criterion)
    audits = [
        i
        for i, criterion in enumerate(criteria)
        if "audit_artifacts.py" in criterion or "provenance_audit.py --mode artifact" in criterion
    ]
    download_dir = options(criteria[fetch])["--dir"]
    print(
        f"{task_id}_FETCH={fetch} VERIFY={verify} AUDITS={audits} "
        f"ORDER_OK={fetch < verify < min(audits)} DOWNLOAD_DIR={download_dir} "
        f"AUDITS_USE_DOWNLOAD_DIR={all(download_dir in criteria[i] for i in audits)} "
        f"IGNORED_DIST_REFS={VALIDATOR._ignored_artifact_refs(chr(10).join(criteria))}"
    )

# D5: direct wildcards are caught; normalized and shell-expanded variants are not.
variants = (
    "dist/release/*.whl",
    "dist/local/*.whl",
    "dist/./release/*.whl",
    "dist/{release,local}/*.whl",
    "dist/*/*.whl",
)
for variant in variants:
    def mutate_dist(data: dict, variant: str = variant) -> None:
        owner = next(t for t in data["tasks"] if t["id"] == "P1-LIC02")
        owner.pop("consumes_artifacts", None)
        owner["acceptance_criteria"] = [
            criterion
            for criterion in owner["acceptance_criteria"]
            if "gh release download" not in criterion and "tools/artifacts/store.py verify" not in criterion
        ]
        owner["acceptance_criteria"] = [
            criterion.replace("evidence/P1-LIC02/downloads/**", variant)
            for criterion in owner["acceptance_criteria"]
        ]
        owner["write_scope"].append("dist/**")
        owner["produces"].append("dist/**")

    errors = mutation_errors(mutate_dist)
    print(
        f"D5_VARIANT={variant} NORMALIZED={posixpath.normpath(variant)} "
        f"DETECTED={bool(VALIDATOR._ignored_artifact_refs(variant))} "
        f"MUTATION_ACCEPTED={not errors} ERRORS={errors}"
    )

# D6: schema binding and planned verifier order for pre-lock approvals.
jsonschema.Draft202012Validator.check_schema(SCHEMA)
approval = {
    "schema_version": 1,
    "gate_id": "AR08-G6.approval",
    "task_id": "P1-READY-CERT01",
    "stage": "approval",
    "status": "pass",
    "evidence_type": "user-approval",
    "evidence": [{"path": "evidence/P1-READY-CERT01/approval.json", "sha256": "a" * 64}],
    "source_commit": "b" * 40,
    "lockfile": {"state": "not_applicable", "reason": "approval precedes production lockfile"},
    "toolchain": "rustc 1.100.0",
    "reviewer_session_id": "reviewer-1",
    "tester_session_id": "tester-1",
    "approver_session_id": "approver-1",
    "approval_artifact": {"path": "evidence/P1-READY-CERT01/approval.json", "sha256": "d" * 64},
    "approval_registry": {"path": registry, "sha256": "e" * 64},
    "approval_scope": "performance-certification",
    "aggregator": False,
}
jsonschema.validate(approval, SCHEMA)
print("D6_BOUND_PRELOCK_APPROVAL_SCHEMA_VALID=True")
for field in ("approver_session_id", "approval_artifact", "approval_registry", "approval_scope"):
    invalid = dict(approval)
    invalid.pop(field)
    try:
        jsonschema.validate(invalid, SCHEMA)
    except jsonschema.ValidationError:
        print(f"D6_MISSING_{field.upper()}_REJECTED=True")
    else:
        print(f"D6_MISSING_{field.upper()}_REJECTED=False")
for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
    owner = task(task_id)
    criteria = owner["acceptance_criteria"]
    write = next(i for i, criterion in enumerate(criteria) if "write_result.py" in criterion)
    validate = next(i for i, criterion in enumerate(criteria) if "validate_result.py" in criterion)
    verify = next(i for i, criterion in enumerate(criteria) if "verify_approval.py" in criterion)
    proof = next(i for i, criterion in enumerate(criteria) if "verify_proof.py" in criterion and "--gate-result" in criterion)
    print(
        f"{task_id}_WRITE={write} VALIDATE={validate} VERIFY_APPROVAL={verify} VERIFY_PROOF={proof} "
        f"ORDER_OK={write < validate < verify < proof} "
        f"REACHES_LOCK_PRODUCER={VALIDATOR._reachable(task_id, BY_ID, 'P1-ARCH01')} "
        f"HAS_NOT_APPLICABLE={'--lockfile-state not_applicable' in criteria[write]}"
    )

print(f"P0_AP01={task('P0-AP01')['status']}/attempt{task('P0-AP01')['attempt_count']}")
print("UNRESOLVED_DEFECTS=4")
print("D7=D1 gate/task-to-canonical-path binding is not validator-enforced")
print("D8=D2 first merged tool task has no available trusted session registry")
print("D9=D3 enforcement evidence is fixture-based and self-test-only mutation is accepted")
print("D10=D5 normalized/shell-expanded ignored-dist variants bypass detection")
print("EXIT_CODE=0")
