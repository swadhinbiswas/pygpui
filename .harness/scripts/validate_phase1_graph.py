#!/usr/bin/env python3
"""Reproducible structural and semantic validation for the Phase 1 task graph."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_PHASE1_FIELDS = {
    "id", "title", "owner_role", "deps", "status", "attempt_count", "max_attempts",
    "acceptance_criteria", "evidence_links", "size", "estimate_range_days", "workflow",
    "completion_state", "branch_state", "produces", "write_scope", "sub_gates",
}

STALE_REMOTE_PHRASES = (
    "No remote PR is required", "requires no remote", "no remote PR requirement",
    "local feature branch", "local main integration", "No remote exists",
)

LOCAL_PATH_RE = re.compile(
    r"(?<![\w])((?:\.harness|tools|tests|crates|pygpui|pygpui_bench|examples|docs|BENCH|packaging|provenance|evidence|dist|artifacts)/[A-Za-z0-9_.*<>/${}-]+)"
)
CARGO_TEST_RE = re.compile(r"cargo test\s+-p\s+([A-Za-z0-9_-]+)(.*?)(?= exits|;|$)")
PLAN_ROW_RE = re.compile(r"\| `(P1-[A-Z0-9-]+)` \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$")
GATE_RE = re.compile(r"\*\*(AR\d{2}-G\d+)\b")
PLAN_GATE_RE = re.compile(r"^\| (AR\d{2}-G\d+) \|", re.MULTILINE)


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if fnmatch.fnmatchcase(path, pattern):
        return True
    return pattern.endswith("/") and path.startswith(pattern)


def _scope_covers_pattern(produce: str, scope: str) -> bool:
    if produce == scope:
        return True
    if scope.endswith("/**"):
        prefix = scope[:-3].rstrip("/")
        return produce == prefix or produce.startswith(prefix + "/")
    if produce.endswith("/**") and scope == produce:
        return True
    return fnmatch.fnmatchcase(produce, scope)


def _covered_by_scope(path: str, scopes: list[str]) -> bool:
    return any(_matches(path, scope) for scope in scopes)


def _plan_rows(plan_text: str) -> list[tuple[str, str, str, str, str]]:
    marker = "## 7. Dependency-ordered task graph"
    section = plan_text.split(marker, 1)[1]
    section = section.split("\n## ", 1)[0]
    rows: list[tuple[str, str, str, str, str]] = []
    for line in section.splitlines():
        match = PLAN_ROW_RE.match(line)
        if match:
            rows.append(match.groups())
    return rows


def _adr_gates(repo_root: Path) -> set[str]:
    gates: set[str] = set()
    for path in sorted((repo_root / ".harness" / "DECISIONS").glob("00*.md")):
        gates.update(GATE_RE.findall(path.read_text(encoding="utf-8")))
    return gates


def _reachable(task_id: str, by_id: dict[str, dict[str, Any]], target: str) -> bool:
    seen: set[str] = set()

    def visit(current: str) -> bool:
        if current == target:
            return True
        if current in seen or current not in by_id:
            return False
        seen.add(current)
        return any(visit(dep) for dep in by_id[current].get("deps", []))

    return visit(task_id)


def _command_paths(criterion: str, task: dict[str, Any]) -> set[str]:
    paths = {match.rstrip(".,;:") for match in LOCAL_PATH_RE.findall(criterion)}
    for package, tail in CARGO_TEST_RE.findall(criterion):
        test_match = re.search(r"--test\s+([A-Za-z0-9_-]+)", tail)
        paths.add(
            f"crates/{package}/tests/{test_match.group(1)}.rs"
            if test_match else f"crates/{package}/**"
        )
    if "cargo test --workspace" in criterion or "cargo metadata" in criterion:
        paths.add("Cargo.toml")
    if re.search(r"python3?\s+-m\s+pygpui_bench\b", criterion):
        paths.add("pygpui_bench/**")
    if "stubtest pygpui" in criterion:
        paths.add("pygpui/__init__.py")
    if "compileall" in criterion and "pygpui" in criterion:
        paths.add("pygpui/__init__.py")
    if "maturin" in criterion:
        paths.add("pyproject.toml")
    if "make -C docs" in criterion:
        paths.add("docs/Makefile")
    return paths


def validate(
    data: dict[str, Any],
    plan_text: str,
    baseline_data: dict[str, Any],
    repo_root: Path,
    history_baseline_data: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    tasks = data.get("tasks", [])
    ids = [task.get("id") for task in tasks]
    metrics["tasks_total"] = len(tasks)
    metrics["unique_ids"] = len(set(ids))
    if len(ids) != len(set(ids)):
        errors.append("duplicate task IDs")

    id_set = set(ids)
    by_id = {task["id"]: task for task in tasks if "id" in task}
    missing_deps = [(t["id"], d) for t in tasks for d in t.get("deps", []) if d not in id_set]
    metrics["dependency_count"] = sum(len(t.get("deps", [])) for t in tasks)
    if missing_deps:
        errors.append(f"unresolved dependencies: {missing_deps}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            errors.append(f"dependency cycle includes {task_id}")
            return
        if task_id in visited or task_id not in by_id:
            return
        visiting.add(task_id)
        for dep in by_id[task_id].get("deps", []):
            visit(dep)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in by_id:
        visit(task_id)

    positions = {task_id: index for index, task_id in enumerate(ids)}
    order_errors = [
        (t["id"], dep) for t in tasks for dep in t.get("deps", [])
        if dep in positions and positions[dep] >= positions[t["id"]]
    ]
    if order_errors:
        errors.append(f"task array is not topological: {order_errors}")

    phase1 = [t for t in tasks if t.get("id", "").startswith("P1-")]
    metrics["phase1_total"] = len(phase1)
    field_errors: list[str] = []
    for task in phase1:
        absent = sorted(REQUIRED_PHASE1_FIELDS - set(task))
        if absent:
            field_errors.append(f"{task['id']} missing fields {absent}")
        if task.get("status") != "blocked" or task.get("attempt_count") != 0:
            field_errors.append(f"{task['id']} is not blocked at attempt zero")
        if task.get("max_attempts") != 4:
            field_errors.append(f"{task['id']} does not preserve max_attempts=4")
        if task.get("branch_state") != "not_started":
            field_errors.append(f"{task['id']} branch_state is not not_started")
        if not task.get("acceptance_criteria") or not task.get("evidence_links"):
            field_errors.append(f"{task['id']} has empty criteria/evidence")
        if not task.get("produces") or not task.get("write_scope"):
            field_errors.append(f"{task['id']} has no producer/write-scope contract")
        if len(task.get("produces", [])) != len(set(task.get("produces", []))):
            field_errors.append(f"{task['id']} has duplicate produces entries")
        if len(task.get("write_scope", [])) != len(set(task.get("write_scope", []))):
            field_errors.append(f"{task['id']} has duplicate write_scope entries")
        for produced in task.get("produces", []):
            if not any(_scope_covers_pattern(produced, scope) for scope in task.get("write_scope", [])):
                field_errors.append(f"{task['id']} produces outside write_scope: {produced}")
        workflow = task.get("workflow")
        completion = task.get("completion_state")
        if workflow == "build":
            for field in (
                "branch_prefix", "review_evidence", "test_evidence", "session_registry_evidence",
                "premerge_state", "postmerge_state", "merge_owner_role", "postmerge_record", "postmerge_command",
            ):
                if not task.get(field):
                    field_errors.append(f"{task['id']} missing branch evidence field {field}")
            if completion != "independently_verified" or task.get("premerge_state") != "independently_verified":
                field_errors.append(f"{task['id']} build task must complete independently_verified")
            if task.get("postmerge_state") != "merged" or task.get("merge_owner_role") != "Integrator":
                field_errors.append(f"{task['id']} post-merge record must be Integrator-owned")
            if any("--state merged" in c for c in task.get("acceptance_criteria", [])):
                field_errors.append(f"{task['id']} has circular pre-merge merged-state acceptance")
        elif workflow == "implementation":
            for field in ("review_task", "test_task", "merge_task"):
                if not task.get(field):
                    field_errors.append(f"{task['id']} missing {field}")
            if completion != "implemented":
                field_errors.append(f"{task['id']} implementation task must complete implemented")
        elif workflow in {"verification", "proof"}:
            for field in ("review_evidence", "test_evidence", "session_registry_evidence", "verification_command"):
                if not task.get(field):
                    field_errors.append(f"{task['id']} missing independent proof field {field}")
            if completion != "independently_verified":
                field_errors.append(f"{task['id']} must complete independently_verified")
            if not _reachable(task["id"], by_id, "P1-SESSION-REGISTRY01"):
                field_errors.append(f"{task['id']} proof task is not gated by the session registry")
        elif workflow == "merge":
            if completion != "merged" or not task.get("merge_evidence"):
                field_errors.append(f"{task['id']} merge task must complete merged with merge evidence")
        elif workflow in {"readiness", "control"}:
            if completion != "recorded":
                field_errors.append(f"{task['id']} must complete recorded")
        else:
            field_errors.append(f"{task['id']} has unknown workflow {workflow!r}")
        if task.get("gates"):
            gate_evidence = task.get("gate_evidence")
            if not gate_evidence or gate_evidence not in task.get("evidence_links", []):
                field_errors.append(f"{task['id']} has gates without linked gate_evidence")
    if field_errors:
        errors.extend(field_errors)

    if "P0-AP01" in by_id:
        if by_id["P0-AP01"].get("status") != "blocked" or by_id["P0-AP01"].get("attempt_count") != 0:
            errors.append("P0-AP01 must remain blocked at attempt zero")
    else:
        errors.append("P0-AP01 is missing")
    not_gated = [t["id"] for t in phase1 if not _reachable(t["id"], by_id, "P0-AP01")]
    if not_gated:
        errors.append(f"Phase 1 tasks not transitively gated by P0-AP01: {not_gated}")
    planner = by_id.get("P0-PL01")
    if not planner or planner.get("attempt_count") != 3 or planner.get("status") not in {"in_progress", "done"}:
        errors.append("P0-PL01 must be attempt 3 and in_progress or done")

    rows = _plan_rows(plan_text)
    plan_ids = [r[0] for r in rows]
    json_ids = [t["id"] for t in phase1]
    metrics["plan_tasks"] = len(rows)
    if plan_ids != json_ids:
        errors.append("plan/JSON Phase 1 task order mismatch")
    metadata_errors: list[str] = []
    for task_id, deliverable, owner, deps_text, size_text in rows:
        if task_id not in by_id:
            continue
        task = by_id[task_id]
        plan_deps = re.findall(r"`([^`]+)`", deps_text)
        plan_size = size_text.split("/")[0].strip().replace("–", "-")
        numbers = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", size_text)]
        if plan_deps != task.get("deps"):
            metadata_errors.append(f"{task_id} dependency mismatch")
        if owner.strip() != task.get("owner_role"):
            metadata_errors.append(f"{task_id} owner mismatch")
        if deliverable.strip() != task.get("title"):
            metadata_errors.append(f"{task_id} title mismatch")
        if plan_size != task.get("size"):
            metadata_errors.append(f"{task_id} size mismatch")
        if len(numbers) >= 2 and [numbers[0], numbers[1]] != task.get("estimate_range_days"):
            metadata_errors.append(f"{task_id} estimate range mismatch")
    if metadata_errors:
        errors.extend(metadata_errors)

    source_gates = _adr_gates(repo_root)
    plan_gates = set(PLAN_GATE_RE.findall(plan_text))
    task_gates = {g for t in phase1 for g in t.get("gates", [])}
    gate_model = data.get("gate_model", {})
    metrics["adr_gates"] = len(source_gates)
    metrics["plan_gates"] = len(plan_gates)
    metrics["task_gate_mappings"] = len(task_gates)
    metrics["task_gate_mapping_total"] = sum(len(t.get("gates", [])) for t in phase1)
    if source_gates != plan_gates or source_gates != task_gates or source_gates != set(gate_model):
        errors.append("full gate coverage mismatch across ADRs, plan, tasks and gate_model")

    plan_gate_map: dict[str, list[str]] = {}
    for line in plan_text.splitlines():
        match = re.match(r"^\| (AR\d{2}-G\d+) \| (.*?) \| (.*?) \|$", line)
        if match:
            plan_gate_map[match.group(1)] = re.findall(r"`([^`]+)`", match.group(2))
    task_gate_map: dict[str, list[str]] = {}
    for task in phase1:
        for gate in task.get("gates", []):
            task_gate_map.setdefault(gate, []).append(task["id"])
    if plan_gate_map != task_gate_map:
        errors.append("plan/JSON ADR gate aggregator mappings mismatch")

    subgate_producers: dict[str, list[str]] = {}
    for task in phase1:
        for sg in task.get("sub_gates", []):
            sg_id = sg.get("id", "")
            if not re.match(r"^AR\d{2}-G\d+\.[a-z0-9-]+$", sg_id):
                errors.append(f"{task['id']} has invalid sub-gate id {sg_id}")
                continue
            subgate_producers.setdefault(sg_id, []).append(task["id"])
            evidence = sg.get("evidence")
            if not evidence or not any(_matches(evidence, p) for p in task.get("produces", [])):
                errors.append(f"{task['id']} sub-gate {sg_id} lacks produced evidence")
    metrics["sub_gates"] = sum(len(t.get("sub_gates", [])) for t in phase1)
    for gate, model in gate_model.items():
        aggregator = model.get("aggregator")
        if aggregator not in by_id or gate not in by_id[aggregator].get("gates", []):
            errors.append(f"{gate} aggregator is missing or does not own the full gate")
            continue
        required = model.get("required_sub_gates", [])
        for sg_id in required:
            producers = subgate_producers.get(sg_id, [])
            if len(producers) != 1:
                errors.append(f"{gate} required sub-gate {sg_id} has {len(producers)} producers")
                continue
            producer = producers[0]
            if producer != aggregator and not _reachable(aggregator, by_id, producer):
                errors.append(f"{gate} aggregator does not depend on sub-gate producer {producer}")
        for sg_id in model.get("forbidden_sub_gates", []):
            if sg_id in subgate_producers:
                errors.append(f"{gate} contains forbidden sub-gate {sg_id}")
    for sg_id, producers in subgate_producers.items():
        if len(producers) != 1:
            errors.append(f"sub-gate {sg_id} has duplicate producers {producers}")
    for pattern in data.get("known_deadlock_patterns", []):
        upstream = by_id.get(pattern.get("upstream_task"))
        gate = pattern.get("gate")
        if upstream and gate in upstream.get("gates", []) and gate_model.get(gate, {}).get("aggregator") != upstream["id"]:
            errors.append(f"known deadlock {pattern.get('name')} is present")

    history_data = history_baseline_data or baseline_data
    baseline_done = {
        t["id"]: t for t in history_data.get("tasks", [])
        if not t["id"].startswith("P1-") and t.get("status") == "done"
    }
    missing_done = sorted(set(baseline_done) - id_set)
    if missing_done:
        errors.append(f"baseline-done tasks missing: {missing_done}")
    changed_history = [t["id"] for t in tasks if t["id"] in baseline_done and baseline_done[t["id"]] != t]
    metrics["phase0_history_compared"] = len(baseline_done)
    if changed_history:
        errors.append(f"Phase 0 history changed: {changed_history}")

    # Durable artifact handoff semantics.
    store = data.get("artifact_store", {})
    if store.get("mechanism") != "GitHub draft release assets" or store.get("immutability", "").find("Never reuse") < 0:
        errors.append("durable artifact store policy is missing")
    artifact_errors: list[str] = []
    for task in phase1:
        binding = task.get("artifact_binding")
        if binding:
            if binding.get("store_task") not in task.get("deps", []):
                artifact_errors.append(f"{task['id']} artifact producer lacks store dependency")
            if not any(_matches(binding.get("manifest", ""), p) for p in task.get("produces", [])):
                artifact_errors.append(f"{task['id']} artifact manifest is not produced")
            criteria = "\n".join(task.get("acceptance_criteria", []))
            if "tools/artifacts/store.py upload" not in criteria or "tools/artifacts/store.py verify" not in criteria:
                artifact_errors.append(f"{task['id']} artifact producer lacks upload/verify commands")
        for consumed in task.get("consumes_artifacts", []):
            if consumed.get("producer") not in task.get("deps", []) or consumed.get("store_task") not in task.get("deps", []):
                artifact_errors.append(f"{task['id']} artifact consumer lacks producer/store dependency")
            criteria = "\n".join(task.get("acceptance_criteria", []))
            if "gh release download" not in criteria or "tools/artifacts/store.py verify" not in criteria:
                artifact_errors.append(f"{task['id']} artifact consumer lacks fetch/verify commands")
    if artifact_errors:
        errors.extend(artifact_errors)

    # Crate, tag, readiness and claim-separation semantics.
    rust = by_id.get("P1-RUSTCONTRACT01", {})
    if "crates/pygpui-contract-tests/**" not in rust.get("produces", []):
        errors.append("cross-crate contracts lack a neutral test crate")
    if any("pygpui-core --test internal_contracts" in c for c in rust.get("acceptance_criteria", [])):
        errors.append("cross-crate contracts illegally test through pygpui-core")
    tag = by_id.get("P1-TAG-CONTRACT01", {})
    proto = by_id.get("P1-PROTO01", {})
    if "P1-PROTO01" in tag.get("deps", []) or "P1-TAG-CONTRACT01" not in proto.get("deps", []):
        errors.append("pre-contract tag timing is invalid")
    if not any("--verify-absent crates/pygpui-protocol/src/lib.rs" in c for c in tag.get("acceptance_criteria", [])):
        errors.append("pre-contract tag does not prove the contract is absent")
    if "P1-NATIVE-READY01" not in by_id.get("P1-REL01", {}).get("deps", []):
        errors.append("candidate wheel build lacks native-lane readiness")
    if _reachable("P1-PERF01", by_id, "P1-READY-CERT01"):
        errors.append("callback proof is conflated with OQ-02 certification")
    if _reachable("P1-REL01", by_id, "P1-READY-CERT01") or _reachable("P1-REL01", by_id, "P1-READY-CLAIM01"):
        errors.append("candidate artifact build is conflated with claim approvals")

    # Command producer/write-scope closure.
    baseline_producers = data.get("baseline_producers", {})
    producer_errors: list[str] = []
    command_count = 0
    for task in phase1:
        for criterion in task.get("acceptance_criteria", []):
            command_count += 1
            for path in _command_paths(criterion, task):
                candidates: list[str] = []
                for pattern, producer in baseline_producers.items():
                    if _matches(path, pattern):
                        candidates.append(producer)
                for producer_task in phase1:
                    if any(_matches(path, p) for p in producer_task.get("produces", [])):
                        candidates.append(producer_task["id"])
                if not candidates:
                    producer_errors.append(f"{task['id']} command path has no producer: {path}")
                    continue
                valid = False
                for producer_id in set(candidates):
                    if producer_id in {task["id"], "P0-PL01"}:
                        valid = True
                        break
                    if producer_id in by_id and _reachable(task["id"], by_id, producer_id):
                        if _covered_by_scope(path, by_id[producer_id].get("write_scope", [])):
                            valid = True
                            break
                if not valid:
                    producer_errors.append(f"{task['id']} command path lacks dependency/scope producer: {path}")
    metrics["acceptance_criteria_checked"] = command_count
    if producer_errors:
        errors.extend(producer_errors)

    combined = plan_text + "\n" + json.dumps(data)
    stale = [p for p in STALE_REMOTE_PHRASES if p in combined]
    if stale:
        errors.append(f"stale remote/workflow statements: {stale}")
    if data.get("git_workflow", {}).get("remote") != "https://github.com/swadhinbiswas/pygpui.git":
        errors.append("git_workflow.remote is not the configured origin")
    if "Integrator-only" not in data.get("git_workflow", {}).get("merge_policy", ""):
        errors.append("git_workflow.merge_policy lacks Integrator-only merges")
    return errors, metrics


def _load_baseline(repo_root: Path, baseline: str) -> dict[str, Any]:
    return json.loads(subprocess.check_output(["git", "show", f"{baseline}:.harness/TASKS.json"], cwd=repo_root, text=True))


def run_self_tests(repo_root: Path, baseline: str, history_baseline: str) -> list[str]:
    data = json.loads((repo_root / ".harness/TASKS.json").read_text())
    plan = (repo_root / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
    baseline_data = _load_baseline(repo_root, baseline)
    history_data = _load_baseline(repo_root, history_baseline)
    base_errors, _ = validate(data, plan, baseline_data, repo_root, history_data)
    if base_errors:
        return [f"base graph invalid before negative tests: {error}" for error in base_errors]
    results: list[str] = []

    def expect_failure(name: str, mutate_data=None, mutate_plan=None) -> None:
        changed = copy.deepcopy(data)
        changed_plan = plan
        if mutate_data:
            mutate_data(changed)
        if mutate_plan:
            changed_plan = mutate_plan(changed_plan)
        errors, _ = validate(changed, changed_plan, baseline_data, repo_root, history_data)
        results.append(f"SELF_TEST_{'FAIL' if not errors else 'PASS'} {name}")

    expect_failure("duplicate-id", lambda d: d["tasks"].append(copy.deepcopy(next(t for t in d["tasks"] if t["id"] == "P1-GOV01"))))
    expect_failure("missing-dependency", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["deps"].append("P1-NOEXIST"))
    expect_failure("cycle", lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AP01")["deps"].append("P1-GOV01"))
    expect_failure("phase1-active", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01").update(status="done"))
    expect_failure("missing-gate", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].remove("AR01-G3"))
    expect_failure("unowned-command", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01")["acceptance_criteria"].append("python3 tools/missing/proof.py exits zero"))
    expect_failure("scope-mismatch", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-GRAPH01").update(write_scope=["unrelated/**"]))
    expect_failure("missing-review-evidence", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").pop("review_evidence", None))
    expect_failure("stale-remote", lambda d: d.update(git_workflow={**d["git_workflow"], "merge_policy": "No remote PR is required " + d["git_workflow"]["merge_policy"]}))
    expect_failure("plan-json-mismatch", mutate_plan=lambda p: p.replace("`P1-GOV01`", "`P1-GOV99`"))
    expect_failure("title-mismatch", mutate_plan=lambda p: p.replace("Authorize Phase 1 and record execution readiness", "Wrong title", 1))
    expect_failure("gate-mapping-mismatch", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].append("AR01-G4"))
    expect_failure("baseline-done-mutation", lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AR01").update(title="Mutated"))
    expect_failure("duplicate-producer", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["produces"].append("Cargo.toml"))
    expect_failure("producer-outside-scope", lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["produces"].append("unowned/file.txt"))

    for pattern in data.get("known_deadlock_patterns", []):
        name = pattern["name"]
        gate = pattern["gate"]
        upstream = pattern["upstream_task"]
        expect_failure(
            f"deadlock-{name}",
            lambda d, gate=gate, upstream=upstream: next(t for t in d["tasks"] if t["id"] == upstream)["gates"].append(gate),
        )
    expect_failure(
        "ar03-g5-forbidden-internal-contract",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["sub_gates"].append(
            {"id": "AR03-G5.internal-contracts", "stage": "internal-contracts", "evidence": "evidence/P1-ARCH01/gate-results.json"}
        ),
    )
    expect_failure(
        "ignored-artifact-handoff",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"] if "gh release download" not in c]
        ),
    )
    expect_failure(
        "premerge-merged-state",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["acceptance_criteria"].append(
            "python3 tools/ci/branch_gate.py verify --task P1-ARCH01 --state merged exits zero"
        ),
    )
    expect_failure(
        "proof-self-certification",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01").pop("review_evidence", None),
    )
    expect_failure(
        "illegal-core-test-dependency",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"].append(
            "cargo test -p pygpui-core --test internal_contracts exits zero"
        ),
    )
    expect_failure(
        "post-contract-tag-timing",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TAG-CONTRACT01")["deps"].append("P1-PROTO01"),
    )
    expect_failure(
        "missing-native-lane-readiness",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL01")["deps"].remove("P1-NATIVE-READY01"),
    )
    expect_failure(
        "conflated-claim-readiness",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["deps"].append("P1-READY-CERT01"),
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="5ce026d")
    parser.add_argument("--history-baseline", default="8ffe8de")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        data = json.loads((root / ".harness/TASKS.json").read_text())
        plan = (root / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
        baseline_data = _load_baseline(root, args.baseline)
        history_data = _load_baseline(root, args.history_baseline)
    except Exception as exc:
        print("JSON_PARSE=FAIL")
        print(f"ERROR: {exc}")
        return 1
    print("JSON_PARSE=PASS")
    errors, metrics = validate(data, plan, baseline_data, root, history_data)
    checks = [
        ("UNIQUE_IDS", metrics["tasks_total"] == metrics["unique_ids"], f"total={metrics['tasks_total']} unique={metrics['unique_ids']}"),
        ("DEPS_RESOLVE", not any(e.startswith("unresolved dependencies") for e in errors), f"checked={metrics['dependency_count']}"),
        ("CYCLES", not any("dependency cycle" in e for e in errors), "count=0"),
        ("TOPOLOGICAL_ORDER", not any("not topological" in e for e in errors), "pass"),
        ("PHASE1_FIELDS", not any("missing fields" in e or "branch evidence" in e or "must complete" in e or "unknown workflow" in e or "gates without" in e or "branch_state" in e for e in errors), f"tasks={metrics['phase1_total']}"),
        ("PHASE1_INITIAL_STATE", not any("blocked at attempt zero" in e or "max_attempts" in e or "P0-AP01 must" in e for e in errors), "blocked/attempt0/max4"),
        ("PHASE1_AP01_GATE", not any("not transitively gated" in e for e in errors), f"checked={metrics['phase1_total']}"),
        ("PLAN_TASK_ORDER", not any("plan/JSON Phase 1 task order" in e for e in errors), f"plan={metrics['plan_tasks']} json={metrics['phase1_total']}"),
        ("PLAN_JSON_METADATA", not any("mismatch" in e and any(w in e for w in ("dependency", "owner", "title", "size", "estimate")) for e in errors), f"checked={metrics['plan_tasks']}"),
        ("ADR_GATE_COVERAGE", metrics["adr_gates"] == metrics["plan_gates"] == metrics["task_gate_mappings"] and not any("full gate coverage" in e for e in errors), f"adr={metrics['adr_gates']} plan={metrics['plan_gates']} aggregators={metrics['task_gate_mappings']}"),
        ("ADR_GATE_MAPPINGS", not any("aggregator mappings" in e for e in errors), f"total={metrics['task_gate_mapping_total']}"),
        ("STAGED_GATE_CLOSURE", not any("sub-gate" in e or "aggregator" in e or "known deadlock" in e for e in errors), f"sub_gates={metrics['sub_gates']}"),
        ("PHASE0_HISTORY", not any("Phase 0 history" in e or "baseline-done tasks missing" in e for e in errors), f"compared={metrics['phase0_history_compared']}"),
        ("COMMAND_PRODUCERS", not any("command path" in e for e in errors), f"criteria={metrics['acceptance_criteria_checked']}"),
        ("REVIEW_MERGE_STATES", not any("circular pre-merge" in e or "post-merge record" in e or "independent proof field" in e or "proof task is not gated" in e for e in errors), "premerge/postmerge/session"),
        ("ARTIFACT_HANDOFF", not any("artifact" in e for e in errors), "draft-release/fetch/verify"),
        ("CRATE_TAG_READINESS", not any("neutral test crate" in e or "illegally test" in e or "tag timing" in e or "tag does not prove" in e or "native-lane readiness" in e or "conflated" in e for e in errors), "semantic"),
        ("SCOPE_NORMALIZATION", not any("duplicate produces" in e or "duplicate write_scope" in e or "outside write_scope" in e for e in errors), "normalized"),
        ("REMOTE_WORKFLOW", not any("stale remote" in e or "git_workflow" in e for e in errors), "stale=0"),
    ]
    for name, ok, detail in checks:
        print(f"{name}={'PASS' if ok else 'FAIL'} {detail}")
    if args.self_test:
        results = run_self_tests(root, args.baseline, args.history_baseline)
        for line in results:
            print(line)
        if any(line.startswith("SELF_TEST_FAIL") for line in results):
            errors.append("negative self-test failed")
    if errors:
        print("VALIDATION=FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
