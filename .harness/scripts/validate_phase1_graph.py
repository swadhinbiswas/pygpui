#!/usr/bin/env python3
"""Reproducible structural and producer validation for the Phase 1 task graph."""

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
    "id",
    "title",
    "owner_role",
    "deps",
    "status",
    "attempt_count",
    "max_attempts",
    "acceptance_criteria",
    "evidence_links",
    "size",
    "estimate_range_days",
    "workflow",
    "completion_state",
    "produces",
    "write_scope",
}

STALE_REMOTE_PHRASES = (
    "No remote PR is required",
    "requires no remote",
    "no remote PR requirement",
    "local feature branch",
    "local main integration",
    "No remote exists",
)

LOCAL_PATH_RE = re.compile(
    r"(?<![\w])((?:\.harness|tools|tests|crates|pygpui|pygpui_bench|examples|docs|BENCH|packaging|provenance|evidence|dist)/[A-Za-z0-9_.*<>/${}-]+)"
)
CARGO_TEST_RE = re.compile(r"cargo test\s+-p\s+([A-Za-z0-9_-]+)(.*?)(?= exits|;|$)")
PLAN_ROW_RE = re.compile(
    r"\| `(P1-[A-Z0-9-]+)` \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|$"
)
GATE_RE = re.compile(r"\*\*(AR\d{2}-G\d+)\b")
PLAN_GATE_RE = re.compile(r"^\| (AR\d{2}-G\d+) \|", re.MULTILINE)


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if pattern.endswith("/") and path.startswith(pattern):
        return True
    return False


def _covered_by_scope(path: str, scopes: list[str]) -> bool:
    return any(_matches(path, scope) for scope in scopes)


def _plan_rows(plan_text: str) -> list[tuple[str, str, str, str, str]]:
    section = plan_text.split("## 5. Dependency-ordered task graph", 1)[1].split(
        "## 6.", 1
    )[0]
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
        return any(visit(dep) for dep in by_id[current]["deps"])

    return visit(task_id)


def _command_paths(criterion: str, task: dict[str, Any]) -> set[str]:
    paths = {match.rstrip(".,;:") for match in LOCAL_PATH_RE.findall(criterion)}
    for package, tail in CARGO_TEST_RE.findall(criterion):
        test_match = re.search(r"--test\s+([A-Za-z0-9_-]+)", tail)
        if test_match:
            paths.add(f"crates/{package}/tests/{test_match.group(1)}.rs")
        else:
            paths.add(f"crates/{package}/**")
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
    for path in list(paths):
        if path.startswith(f"evidence/{task['id']}/"):
            continue
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
    missing_deps = [
        (task["id"], dep)
        for task in tasks
        for dep in task.get("deps", [])
        if dep not in id_set
    ]
    metrics["dependency_count"] = sum(len(task.get("deps", [])) for task in tasks)
    if missing_deps:
        errors.append(f"unresolved dependencies: {missing_deps}")

    # DFS cycle check.
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

    # Array order must be topological.
    positions = {task_id: index for index, task_id in enumerate(ids)}
    order_errors = [
        (task["id"], dep)
        for task in tasks
        for dep in task.get("deps", [])
        if dep in positions and positions[dep] >= positions[task["id"]]
    ]
    if order_errors:
        errors.append(f"task array is not topological: {order_errors}")

    phase1 = [task for task in tasks if task.get("id", "").startswith("P1-")]
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
        if not task.get("acceptance_criteria") or not task.get("evidence_links"):
            field_errors.append(f"{task['id']} has empty criteria/evidence")
        if not task.get("produces") or not task.get("write_scope"):
            field_errors.append(f"{task['id']} has no producer/write-scope contract")
        workflow = task.get("workflow")
        completion = task.get("completion_state")
        if workflow == "build":
            for field in ("branch_prefix", "review_evidence", "test_evidence", "merge_evidence"):
                if not task.get(field):
                    field_errors.append(f"{task['id']} missing branch evidence field {field}")
            if completion != "merged":
                field_errors.append(f"{task['id']} build task must complete merged")
        elif workflow == "implementation":
            for field in ("review_task", "test_task", "merge_task"):
                if not task.get(field):
                    field_errors.append(f"{task['id']} missing {field}")
            if completion != "implemented":
                field_errors.append(f"{task['id']} implementation task must complete implemented")
        elif workflow in {"verification", "proof"}:
            if completion != "independently_verified":
                field_errors.append(f"{task['id']} must complete independently_verified")
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
        ap01 = by_id["P0-AP01"]
        if ap01.get("status") != "blocked" or ap01.get("attempt_count") != 0:
            errors.append("P0-AP01 must remain blocked at attempt zero")
    else:
        errors.append("P0-AP01 is missing")

    not_gated = [
        task["id"] for task in phase1 if not _reachable(task["id"], by_id, "P0-AP01")
    ]
    if not_gated:
        errors.append(f"Phase 1 tasks not transitively gated by P0-AP01: {not_gated}")

    planner = by_id.get("P0-PL01")
    if not planner or planner.get("attempt_count") != 2 or planner.get("status") not in {
        "in_progress",
        "done",
    }:
        errors.append("P0-PL01 must be attempt 2 and in_progress or done")

    rows = _plan_rows(plan_text)
    plan_ids = [row[0] for row in rows]
    json_ids = [task["id"] for task in phase1]
    metrics["plan_tasks"] = len(rows)
    if plan_ids != json_ids:
        errors.append("plan/JSON Phase 1 task order mismatch")
    metadata_errors: list[str] = []
    for task_id, _deliverable, owner, deps_text, size_text in rows:
        if task_id not in by_id:
            continue
        task = by_id[task_id]
        plan_deps = re.findall(r"`([^`]+)`", deps_text)
        plan_size = size_text.split("/")[0].strip().replace("–", "-")
        numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", size_text)]
        if plan_deps != task.get("deps"):
            metadata_errors.append(f"{task_id} dependency mismatch")
        if owner.strip() != task.get("owner_role"):
            metadata_errors.append(f"{task_id} owner mismatch")
        if _deliverable.strip() != task.get("title"):
            metadata_errors.append(f"{task_id} title mismatch")
        if plan_size != task.get("size"):
            metadata_errors.append(f"{task_id} size mismatch")
        if len(numbers) >= 2 and [numbers[0], numbers[1]] != task.get(
            "estimate_range_days"
        ):
            metadata_errors.append(f"{task_id} estimate range mismatch")
    if metadata_errors:
        errors.extend(metadata_errors)

    source_gates = _adr_gates(repo_root)
    plan_gates = set(PLAN_GATE_RE.findall(plan_text))
    task_gates = {gate for task in phase1 for gate in task.get("gates", [])}
    metrics["adr_gates"] = len(source_gates)
    metrics["plan_gates"] = len(plan_gates)
    metrics["task_gate_mappings"] = len(task_gates)
    metrics["task_gate_mapping_total"] = sum(len(task.get("gates", [])) for task in phase1)
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
        errors.append("plan/JSON ADR gate task mappings mismatch")
    if source_gates != plan_gates:
        errors.append(
            f"plan gate mismatch missing={sorted(source_gates-plan_gates)} extra={sorted(plan_gates-source_gates)}"
        )
    if source_gates != task_gates:
        errors.append(
            f"task gate mismatch missing={sorted(source_gates-task_gates)} extra={sorted(task_gates-source_gates)}"
        )

    history_data = history_baseline_data or baseline_data
    baseline_done = {
        task["id"]: task
        for task in history_data.get("tasks", [])
        if not task["id"].startswith("P1-") and task.get("status") == "done"
    }
    missing_done = sorted(set(baseline_done) - id_set)
    if missing_done:
        errors.append(f"baseline-done tasks missing: {missing_done}")
    changed_history = [
        task["id"]
        for task in tasks
        if task["id"] in baseline_done and baseline_done[task["id"]] != task
    ]
    metrics["phase0_history_compared"] = len(baseline_done)
    if changed_history:
        errors.append(f"Phase 0 history changed: {changed_history}")

    # Every local command input/output must have a producer and a covering write scope.
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
                    if any(_matches(path, pattern) for pattern in producer_task.get("produces", [])):
                        candidates.append(producer_task["id"])
                if not candidates:
                    producer_errors.append(f"{task['id']} command path has no producer: {path}")
                    continue
                valid = False
                for producer_id in set(candidates):
                    if producer_id == task["id"]:
                        valid = True
                        break
                    if producer_id == "P0-PL01":
                        valid = True
                        break
                    if producer_id in by_id and _reachable(task["id"], by_id, producer_id):
                        producer = by_id[producer_id]
                        if _covered_by_scope(path, producer.get("write_scope", [])):
                            valid = True
                            break
                if not valid:
                    producer_errors.append(
                        f"{task['id']} command path lacks dependency/scope producer: {path}"
                    )
    metrics["acceptance_criteria_checked"] = command_count
    if producer_errors:
        errors.extend(producer_errors)

    combined = plan_text + "\n" + json.dumps(data)
    stale = [phrase for phrase in STALE_REMOTE_PHRASES if phrase in combined]
    if stale:
        errors.append(f"stale remote/workflow statements: {stale}")

    if data.get("git_workflow", {}).get("remote") != "https://github.com/swadhinbiswas/pygpui.git":
        errors.append("git_workflow.remote is not the configured origin")
    if "Integrator-only" not in data.get("git_workflow", {}).get("merge_policy", ""):
        errors.append("git_workflow.merge_policy lacks Integrator-only merges")

    return errors, metrics


def _load_baseline(repo_root: Path, baseline: str) -> dict[str, Any]:
    raw = subprocess.check_output(
        ["git", "show", f"{baseline}:.harness/TASKS.json"], cwd=repo_root, text=True
    )
    return json.loads(raw)


def run_self_tests(repo_root: Path, baseline: str, history_baseline: str) -> list[str]:
    tasks_path = repo_root / ".harness" / "TASKS.json"
    plan_path = repo_root / ".harness" / "PLANS" / "phase-1-vertical-slice.md"
    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    plan = plan_path.read_text(encoding="utf-8")
    baseline_data = _load_baseline(repo_root, baseline)
    history_baseline_data = _load_baseline(repo_root, history_baseline)
    base_errors, _ = validate(data, plan, baseline_data, repo_root, history_baseline_data)
    if base_errors:
        return [f"base graph invalid before negative tests: {error}" for error in base_errors]

    results: list[str] = []

    def expect_failure(name: str, mutate_data=None, mutate_plan=None) -> None:
        changed = copy.deepcopy(data)
        changed_plan = plan
        if mutate_data is not None:
            mutate_data(changed)
        if mutate_plan is not None:
            changed_plan = mutate_plan(changed_plan)
        errors, _ = validate(changed, changed_plan, baseline_data, repo_root, history_baseline_data)
        if not errors:
            results.append(f"SELF_TEST_FAIL {name}: mutation was accepted")
        else:
            results.append(f"SELF_TEST_PASS {name}")

    expect_failure(
        "duplicate-id",
        lambda d: d["tasks"].append(copy.deepcopy(next(t for t in d["tasks"] if t["id"] == "P1-GOV01"))),
    )
    expect_failure(
        "missing-dependency",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["deps"].append("P1-NOEXIST"),
    )
    expect_failure(
        "cycle",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AP01")["deps"].append("P1-GOV01"),
    )
    expect_failure(
        "phase1-active",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01").update(status="done"),
    )
    expect_failure(
        "missing-gate",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].remove("AR01-G3"),
    )
    expect_failure(
        "unowned-command",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01")["acceptance_criteria"].append(
            "python3 tools/missing/proof.py exits zero"
        ),
    )
    expect_failure(
        "scope-mismatch",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-GRAPH01").update(write_scope=["unrelated/**"]),
    )
    expect_failure(
        "missing-review-evidence",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").pop("review_evidence", None),
    )
    expect_failure(
        "stale-remote",
        lambda d: d.update(git_workflow={**d["git_workflow"], "merge_policy": "No remote PR is required" + d["git_workflow"]["merge_policy"]}),
    )
    expect_failure(
        "plan-json-mismatch",
        mutate_plan=lambda p: p.replace('`P1-GOV01`', '`P1-GOV99`'),
    )
    expect_failure(
        "title-mismatch",
        mutate_plan=lambda p: p.replace('Authorize Phase 1 and record execution readiness', 'Wrong title', 1),
    )
    expect_failure(
        "gate-mapping-mismatch",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].append("AR01-G4"),
    )
    expect_failure(
        "baseline-done-mutation",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AR01").update(
            title="Mutated accepted architecture task"
        ),
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="5ce026d")
    parser.add_argument("--history-baseline", default="c5ed5f3")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    tasks_path = repo_root / ".harness" / "TASKS.json"
    plan_path = repo_root / ".harness" / "PLANS" / "phase-1-vertical-slice.md"

    try:
        data = json.loads(tasks_path.read_text(encoding="utf-8"))
        plan = plan_path.read_text(encoding="utf-8")
        baseline_data = _load_baseline(repo_root, args.baseline)
        history_baseline_data = _load_baseline(repo_root, args.history_baseline)
    except Exception as exc:
        print("JSON_PARSE=FAIL")
        print(f"ERROR: {exc}")
        return 1

    print("JSON_PARSE=PASS")
    errors, metrics = validate(data, plan, baseline_data, repo_root, history_baseline_data)
    checks = [
        ("UNIQUE_IDS", metrics["tasks_total"] == metrics["unique_ids"], f"total={metrics['tasks_total']} unique={metrics['unique_ids']}"),
        ("DEPS_RESOLVE", not any(error.startswith("unresolved dependencies") for error in errors), f"checked={metrics['dependency_count']}"),
        ("CYCLES", not any("dependency cycle" in error for error in errors), "count=0" if not any("dependency cycle" in error for error in errors) else "count>0"),
        ("TOPOLOGICAL_ORDER", not any("not topological" in error for error in errors), "pass" if not any("not topological" in error for error in errors) else "fail"),
        ("PHASE1_FIELDS", not any("missing fields" in error or "branch evidence" in error or "must complete" in error or "unknown workflow" in error or "gates without" in error for error in errors), f"tasks={metrics['phase1_total']}"),
        ("PHASE1_INITIAL_STATE", not any("blocked at attempt zero" in error or "max_attempts" in error or "P0-AP01 must" in error for error in errors), "blocked/attempt0/max4"),
        ("PHASE1_AP01_GATE", not any("not transitively gated" in error for error in errors), f"checked={metrics['phase1_total']}"),
        ("PLAN_TASK_ORDER", not any("plan/JSON Phase 1 task order" in error for error in errors), f"plan={metrics['plan_tasks']} json={metrics['phase1_total']}"),
        ("PLAN_JSON_METADATA", not any("mismatch" in error and any(word in error for word in ("dependency", "owner", "title", "size", "estimate")) for error in errors), f"checked={metrics['plan_tasks']}"),
        ("ADR_GATE_COVERAGE", metrics["adr_gates"] == metrics["plan_gates"] == metrics["task_gate_mappings"] and not any("gate mismatch" in error for error in errors), f"adr={metrics['adr_gates']} plan={metrics['plan_gates']} task_mappings={metrics['task_gate_mappings']}"),
        ("ADR_GATE_MAPPINGS", "plan/JSON ADR gate task mappings mismatch" not in errors, f"total={metrics['task_gate_mapping_total']}"),
        ("PHASE0_HISTORY", not any("Phase 0 history changed" in error for error in errors), f"compared={metrics['phase0_history_compared']}"),
        ("COMMAND_PRODUCERS", not any("command path" in error for error in errors), f"criteria={metrics['acceptance_criteria_checked']}"),
        ("REMOTE_WORKFLOW", not any("stale remote" in error or "git_workflow" in error for error in errors), "stale=0" if not any("stale remote" in error or "git_workflow" in error for error in errors) else "stale>0"),
    ]
    for name, ok, detail in checks:
        print(f"{name}={'PASS' if ok else 'FAIL'} {detail}")

    if args.self_test:
        self_test_results = run_self_tests(repo_root, args.baseline, args.history_baseline)
        for line in self_test_results:
            print(line)
        if any(line.startswith("SELF_TEST_FAIL") for line in self_test_results):
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
