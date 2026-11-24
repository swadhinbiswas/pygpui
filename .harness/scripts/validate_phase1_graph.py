#!/usr/bin/env python3
"""Reproducible structural and semantic validation for the Phase 1 task graph."""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import shlex
import subprocess
import sys
import posixpath
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


def _expand_braces(value: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", value)
    if not match:
        return [value]
    expanded: list[str] = []
    for option in match.group(1).split(","):
        expanded.extend(_expand_braces(value[:match.start()] + option + value[match.end():]))
    return expanded


def _parse_cli(command: str) -> dict[str, list[str]]:
    command = command.split(" exits", 1)[0]
    try:
        tokens = shlex.split(command)
    except ValueError:
        return {}
    parsed: dict[str, list[str]] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--"):
            if "=" in token:
                flag, value = token.split("=", 1)
                parsed.setdefault(flag, []).append(value)
            elif index + 1 < len(tokens) and not tokens[index + 1].startswith("--"):
                parsed.setdefault(token, []).append(tokens[index + 1])
                index += 1
            else:
                parsed.setdefault(token, []).append("")
        index += 1
    return parsed


SINGLETON_FLAGS = {
    "--gate", "--task", "--result", "--inputs", "--output", "--manifest", "--dir",
    "--pr", "--changed-files", "--approval-artifact", "--approval-registry",
    "--approval-scope", "--approver-session", "--merge-sha", "--record",
    "--expected-sha", "--registry", "--gate-result", "--schema", "--evidence",
}


def _duplicate_flags(command: str) -> list[str]:
    parsed = _parse_cli(command)
    return [flag for flag in SINGLETON_FLAGS if len(parsed.get(flag, [])) > 1]


def _ignored_artifact_refs(text: str) -> list[str]:
    text = text.split(" exits", 1)[0]
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    normalized: list[str] = []
    for token in tokens:
        token = token.strip("'\".,;|&<>")
        for candidate in _expand_braces(token):
            path = posixpath.normpath(candidate)
            if path == "dist" or path.startswith("dist/"):
                normalized.append(path)
    return normalized


def _parse_write_result(command: str) -> dict[str, str] | None:
    if "tools/gates/write_result.py" not in command or "--self-test" in command:
        return None
    parsed = _parse_cli(command)
    return {
        flag: values[0]
        for flag, values in parsed.items()
        if flag in {"--task", "--gate", "--output"} and values
    }


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
        for criterion in task.get("acceptance_criteria", []):
            duplicates = _duplicate_flags(criterion)
            if duplicates:
                field_errors.append(f"{task['id']} has duplicate CLI flags {duplicates}")
        if task.get("postmerge_command") and _duplicate_flags(task["postmerge_command"]):
            field_errors.append(f"{task['id']} postmerge command has duplicate CLI flags")
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
            if completion != "merged" or task.get("premerge_state") != "independently_verified":
                field_errors.append(f"{task['id']} build task must complete merged after pre-merge verification")
            if task.get("postmerge_state") != "merged" or task.get("merge_owner_role") != "Integrator":
                field_errors.append(f"{task['id']} post-merge record must be Integrator-owned")
            expected_record = f"evidence/{task['id']}/merge.json"
            if task.get("postmerge_record") != expected_record:
                field_errors.append(f"{task['id']} postmerge record is not canonical")
            postmerge_args = _parse_cli(task.get("postmerge_command", ""))
            if postmerge_args.get("--task") != [task["id"]] or postmerge_args.get("--output") != [expected_record]:
                field_errors.append(f"{task['id']} postmerge command identity/path is not canonical")
            criteria_text = "\n".join(task.get("acceptance_criteria", []))
            if "tools/ci/branch_gate.py verify" not in criteria_text or "--state independently_verified" not in criteria_text:
                field_errors.append(f"{task['id']} lacks pre-merge branch verification")
            if "tools/session/verify_roles.py" not in criteria_text:
                field_errors.append(f"{task['id']} lacks trusted session verification")
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
        if task.get("gates") or task.get("sub_gates"):
            expected_ids = list(task.get("sub_gates", [])) + list(task.get("gates", []))
            expected_gate_ids = [sg["id"] for sg in task.get("sub_gates", [])] + list(task.get("gates", []))
            results = task.get("gate_results", [])
            result_ids = [result.get("gate_id") for result in results]
            if sorted(result_ids) != sorted(expected_gate_ids) or len(results) != len(set(result_ids)):
                field_errors.append(f"{task['id']} gate_results do not uniquely cover its gates/sub-gates")
            for result in results:
                path = result.get("path", "")
                expected_path = f"evidence/{task['id']}/{result.get('gate_id')}.json"
                if path != expected_path:
                    field_errors.append(f"{task['id']} has non-canonical or shared result path {path}")
                if path not in task.get("evidence_links", []):
                    field_errors.append(f"{task['id']} result path is not linked evidence")
            if any(path.endswith("/gate-results.json") for path in task.get("evidence_links", [])):
                field_errors.append(f"{task['id']} retains stale generic gate-results evidence")
            criteria_text = "\n".join(task.get("acceptance_criteria", []))
            if "tools/gates/validate_result.py" not in criteria_text or ".harness/schemas/gate-results.schema.json" not in criteria_text:
                field_errors.append(f"{task['id']} gate result lacks schema validation")
            if task.get("gates"):
                for gate in task.get("gates", []):
                    if data.get("gate_model", {}).get(gate, {}).get("required_sub_gates") and f"tools/gates/aggregate.py --gate {gate}" not in criteria_text:
                        field_errors.append(f"{task['id']} staged aggregator {gate} lacks aggregate invocation")
        if task.get("workflow") in {"control", "readiness"}:
            code_producers = [p for p in task.get("produces", []) if p.startswith(("tools/", "crates/", "pygpui/", ".harness/schemas/"))]
            if code_producers:
                field_errors.append(f"{task['id']} code-producing control/readiness task is not a merged build task")
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
    if not planner or planner.get("attempt_count") != 3 or planner.get("status") != "done":
        errors.append("P0-PL01 must remain done at attempt 3")
    remediation = by_id.get("P0-REM01")
    if not remediation or remediation.get("attempt_count") != 1 or remediation.get("status") != "done":
        errors.append("P0-REM01 must remain done at attempt 1")
    remediation2 = by_id.get("P0-REM04")
    if not remediation2 or remediation2.get("attempt_count") != 1 or remediation2.get("status") != "done":
        errors.append("P0-REM04 must remain done at attempt 1")
    remediation3 = by_id.get("P0-REM06")
    if not remediation3 or remediation3.get("attempt_count") != 1 or remediation3.get("status") != "done":
        errors.append("P0-REM06 must remain done at attempt 1")
    remediation4 = by_id.get("P0-REM08")
    if not remediation4 or remediation4.get("attempt_count") != 1 or remediation4.get("status") not in {"in_progress", "done"}:
        errors.append("P0-REM08 must be attempt 1 and in_progress or done")
    seed = by_id.get("P1-SESSION-SEED01")
    if not seed or seed.get("owner_role") != "Orchestrator" or seed.get("workflow") != "control":
        errors.append("trusted session-registry seed is missing or not Orchestrator-controlled")
    if seed and ".harness/sessions/registry.json" not in seed.get("produces", []):
        errors.append("session-registry seed does not produce the trust root")
    if seed:
        seed_commands = [c for c in seed.get("acceptance_criteria", []) if c.startswith("python3 .harness/scripts/seed_session_registry.py")]
        seed_create = [c for c in seed_commands if "--self-test" not in c and "--verify" not in c]
        if len(seed_create) != 1:
            errors.append("session-registry seed lacks exactly one canonical create command")
        else:
            args = _parse_cli(seed_create[0])
            if args.get("--output") != [".harness/sessions/registry.json"] or args.get("--approval") != [".harness/sessions/seed-approval.json"]:
                errors.append("session-registry seed command output is not canonical")
        if not any(c.strip() == "python3 .harness/scripts/seed_session_registry.py --self-test exits zero" for c in seed_commands):
            errors.append("session-registry seed self-test requires extra arguments")
        if not any("seed_session_registry.py --verify" in c and ".harness/sessions/registry.json" in c and ".harness/sessions/seed-approval.json" in c for c in seed_commands):
            errors.append("session-registry seed lacks approval-hash verification")
    if "P1-SESSION-SEED01" not in by_id.get("P1-TOOL-BRANCH01", {}).get("deps", []):
        errors.append("first merged build lacks session-registry seed dependency")
    if seed and any(dep.startswith("P1-") and by_id.get(dep, {}).get("workflow") == "build" for dep in seed.get("deps", [])):
        errors.append("session-registry seed has circular build dependency")
    if "P1-SESSION-SEED01" not in by_id.get("P1-SESSION-REGISTRY01", {}).get("deps", []):
        errors.append("session-registry build does not extend the seeded trust root")

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
    subgate_objects: dict[str, tuple[str, dict[str, Any]]] = {}
    for task in phase1:
        for sg in task.get("sub_gates", []):
            sg_id = sg.get("id", "")
            if not re.match(r"^AR\d{2}-G\d+\.[a-z0-9-]+$", sg_id):
                errors.append(f"{task['id']} has invalid sub-gate id {sg_id}")
                continue
            subgate_producers.setdefault(sg_id, []).append(task["id"])
            subgate_objects[sg_id] = (task["id"], sg)
            evidence = sg.get("evidence")
            if not evidence or not any(_matches(evidence, p) for p in task.get("produces", [])):
                errors.append(f"{task['id']} sub-gate {sg_id} lacks produced evidence")
            if sg.get("evidence_type") == "user-approval":
                if task.get("workflow") != "verification" or not task.get("review_evidence") or not task.get("test_evidence"):
                    errors.append(f"{task['id']} user-approval sub-gate lacks independent verification")
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

    result_path_owners: dict[str, list[str]] = {}
    for task in phase1:
        criteria = task.get("acceptance_criteria", [])
        for result in task.get("gate_results", []):
            path = result.get("path", "")
            result_path_owners.setdefault(path, []).append(task["id"])
            for index, criterion in enumerate(criteria):
                parsed = _parse_write_result(criterion)
                if parsed is None:
                    continue
                if parsed.get("--output") == path:
                    expected_gate = result.get("gate_id")
                    if parsed.get("--task") != task["id"] or parsed.get("--gate") != expected_gate:
                        errors.append(f"{task['id']} write_result identity does not match canonical path {path}")
            creation_indices = []
            validation_indices = []
            for index, criterion in enumerate(criteria):
                parsed = _parse_cli(criterion)
                if ("tools/gates/write_result.py" in criterion or "tools/gates/aggregate.py" in criterion) and parsed.get("--output") == [path]:
                    creation_indices.append(index)
                if "tools/gates/validate_result.py" in criterion and parsed.get("--result") == [path]:
                    validation_indices.append(index)
            if len(creation_indices) != 1 or len(validation_indices) != 1:
                errors.append(f"{task['id']} result {path} lacks exactly one create and one validate command")
            elif creation_indices[0] >= validation_indices[0]:
                errors.append(f"{task['id']} validates result {path} before creation")
            for index in creation_indices:
                if "tools/gates/aggregate.py" in criteria[index] and f"--inputs {path}" in criteria[index]:
                    errors.append(f"{task['id']} aggregate command reads and writes {path}")
        expected_write_outputs = {
            f"evidence/{task['id']}/{sg['id']}.json" for sg in task.get("sub_gates", [])
        } | {
            f"evidence/{task['id']}/{gate}.json" for gate in task.get("gates", [])
            if not gate_model.get(gate, {}).get("required_sub_gates")
        }
        actual_write_outputs = {
            parsed.get("--output") for criterion in criteria
            if (parsed := _parse_write_result(criterion)) is not None
        }
        if actual_write_outputs != expected_write_outputs:
            errors.append(f"{task['id']} write_result outputs do not match canonical result identities")
        for gate in task.get("gates", []):
            model = gate_model.get(gate, {})
            if not model.get("required_sub_gates"):
                continue
            output = f"evidence/{task['id']}/{gate}.json"
            aggregate_indices = [
                i for i, c in enumerate(criteria)
                if "tools/gates/aggregate.py" in c and _parse_cli(c).get("--gate") == [gate]
            ]
            if len(aggregate_indices) != 1:
                errors.append(f"{task['id']} staged gate {gate} lacks exactly one aggregate command")
                continue
            aggregate = criteria[aggregate_indices[0]]
            expected_inputs = [subgate_objects[sg_id][1]["evidence"] for sg_id in model["required_sub_gates"]]
            aggregate_args = _parse_cli(aggregate)
            actual_inputs = aggregate_args.get("--inputs", [""])[0].split(",") if aggregate_args.get("--inputs") else []
            if actual_inputs != expected_inputs:
                errors.append(f"{task['id']} staged gate {gate} has incorrect aggregate inputs")
            if output in actual_inputs:
                errors.append(f"{task['id']} staged gate {gate} self-overwrites its output")
    for path, owners in result_path_owners.items():
        if len(owners) != 1:
            errors.append(f"gate result path is shared: {path} owners={owners}")
    metrics["gate_result_paths"] = len(result_path_owners)

    for sg_id, (task_id, sg) in subgate_objects.items():
        task = by_id[task_id]
        if sg.get("evidence_type") == "user-approval":
            for field in ("approval_artifact", "approval_registry", "approval_scope"):
                if not sg.get(field):
                    errors.append(f"{task_id} user-approval sub-gate lacks {field}")
            write_commands = [
                c for c in task.get("acceptance_criteria", [])
                if "tools/gates/write_result.py" in c and _parse_cli(c).get("--gate") == [sg_id]
            ]
            if not write_commands:
                errors.append(f"{task_id} approval sub-gate lacks write_result command")
            else:
                args = _parse_cli(write_commands[0])
                expected_bindings = {
                    "--approval-artifact": sg.get("approval_artifact"),
                    "--approval-registry": sg.get("approval_registry"),
                    "--approval-scope": sg.get("approval_scope"),
                }
                for flag, expected in expected_bindings.items():
                    if args.get(flag) != [expected]:
                        errors.append(f"{task_id} approval {flag} does not match sub-gate declaration")
                if args.get("--lockfile-state") != ["not_applicable"] or args.get("--approver-session") != ["<approver-session>"]:
                    errors.append(f"{task_id} pre-lock approval lacks explicit not-applicable/approver binding")
            approval_commands = [c for c in task.get("acceptance_criteria", []) if "tools/session/verify_approval.py" in c]
            if not approval_commands:
                errors.append(f"{task_id} user-approval sub-gate lacks registry/artifact verification")
            else:
                args = _parse_cli(approval_commands[0])
                if args.get("--result") != [sg["evidence"]] or args.get("--registry") != [sg.get("approval_registry")] or args.get("--approval-artifact") != [sg.get("approval_artifact")]:
                    errors.append(f"{task_id} verify_approval command does not match sub-gate binding")
            proof_commands = [c for c in task.get("acceptance_criteria", []) if "tools/review/verify_proof.py" in c]
            if not any(_parse_cli(c).get("--gate-result") == [sg["evidence"]] for c in proof_commands):
                errors.append(f"{task_id} user-approval proof verification lacks gate-result binding")
            ordered = task.get("acceptance_criteria", [])
            write_index = next((i for i, c in enumerate(ordered) if "tools/gates/write_result.py" in c and _parse_cli(c).get("--gate") == [sg_id]), -1)
            validate_index = next((i for i, c in enumerate(ordered) if "tools/gates/validate_result.py" in c and _parse_cli(c).get("--result") == [sg["evidence"]]), -1)
            approval_index = next((i for i, c in enumerate(ordered) if "tools/session/verify_approval.py" in c), -1)
            if not (write_index < validate_index < approval_index):
                errors.append(f"{task_id} approval verification is not ordered after result creation and schema validation")

    for gate in ("AR09-G1", "AR10-G3"):
        required = gate_model.get(gate, {}).get("required_sub_gates", [])
        if f"{gate}.repository-evidence" not in required or f"{gate}.pr-enforcement" not in required:
            errors.append(f"{gate} does not aggregate repository and per-PR enforcement evidence")
    pr_task = by_id.get("P1-PR-AUDIT01", {})
    pr_criteria = pr_task.get("acceptance_criteria", [])
    identity_captures = [
        (i, re.search(r"gh pr view\b.*?>\s*([^\s]+)\s+exits zero", c))
        for i, c in enumerate(pr_criteria) if "gh pr view" in c
    ]
    diff_captures = [
        (i, re.search(r"gh pr diff\b.*?>\s*([^\s]+)\s+exits zero", c))
        for i, c in enumerate(pr_criteria) if "gh pr diff" in c
    ]
    if len(identity_captures) != 1 or not identity_captures[0][1] or identity_captures[0][1].group(1) != "evidence/P1-PR-AUDIT01/pr.json":
        errors.append("per-PR identity capture does not write the canonical PR artifact")
    if len(diff_captures) != 1 or not diff_captures[0][1] or diff_captures[0][1].group(1) != "evidence/P1-PR-AUDIT01/changed-files.txt":
        errors.append("per-PR changed-file capture does not write the canonical diff artifact")
    if any("/dev/null" in c for c in pr_criteria if "gh pr view" in c or "gh pr diff" in c):
        errors.append("per-PR gh output is discarded")
    for canonical in ("evidence/P1-PR-AUDIT01/pr.json", "evidence/P1-PR-AUDIT01/changed-files.txt"):
        if any(re.search(r"\b(?:printf|echo|cat|tee)\b", c) and canonical in c for c in pr_criteria):
            errors.append(f"fabricated writer targets canonical PR artifact {canonical}")
    for gate in ("AR09-G1", "AR10-G3"):
        output = f"evidence/P1-PR-AUDIT01/{gate}.pr-enforcement.json"
        producers = [(i, c) for i, c in enumerate(pr_criteria) if "pr_audit_gate.py" in c and _parse_cli(c).get("--output") == [output]]
        if len(producers) != 1:
            errors.append(f"{gate} lacks exactly one real per-PR enforcement producer")
            continue
        index, command = producers[0]
        args = _parse_cli(command)
        if "--self-test" in command or "fixtures/" in command:
            errors.append(f"{gate} enforcement evidence is fixture/self-test based")
        if args.get("--pr") != ["evidence/P1-PR-AUDIT01/pr.json"] or args.get("--changed-files") != ["evidence/P1-PR-AUDIT01/changed-files.txt"]:
            errors.append(f"{gate} enforcement command does not consume canonical real PR evidence")
        if identity_captures and diff_captures and not (identity_captures[0][0] < index and diff_captures[0][0] < index):
            errors.append(f"{gate} enforcement runs before real PR capture")
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
            criteria_list = task.get("acceptance_criteria", [])
            fetch_commands = [(i, c) for i, c in enumerate(criteria_list) if "gh release download" in c]
            verify_commands = [(i, c) for i, c in enumerate(criteria_list) if "tools/artifacts/store.py verify" in c]
            if len(fetch_commands) != 1 or len(verify_commands) != 1:
                artifact_errors.append(f"{task['id']} artifact consumer lacks exactly one fetch/verify pair")
                continue
            fetch_index, fetch_command = fetch_commands[0]
            verify_index, verify_command = verify_commands[0]
            fetch_args = _parse_cli(fetch_command)
            verify_args = _parse_cli(verify_command)
            download_dir = fetch_args.get("--dir", [None])[0]
            if not download_dir:
                artifact_errors.append(f"{task['id']} artifact fetch lacks download directory")
                continue
            if verify_args.get("--manifest") != [consumed.get("manifest")] or verify_args.get("--dir") != [download_dir]:
                artifact_errors.append(f"{task['id']} artifact verify manifest/directory does not match declaration/fetch")
            audit_indices = [i for i, c in enumerate(criteria_list) if "audit_artifacts.py" in c or "provenance_audit.py --mode artifact" in c]
            if not (fetch_index < verify_index):
                artifact_errors.append(f"{task['id']} artifact verify is not ordered after fetch")
            if audit_indices and not (fetch_index < verify_index < min(audit_indices)):
                artifact_errors.append(f"{task['id']} artifact audit is not ordered after fetch/verify")
            for index in audit_indices:
                audit_args = _parse_cli(criteria_list[index])
                audit_path = audit_args.get("--artifacts", [""])[0]
                normalized_audit = posixpath.normpath(audit_path)
                normalized_dir = posixpath.normpath(download_dir)
                if not (normalized_audit == normalized_dir or normalized_audit.startswith(normalized_dir.rstrip("/") + "/")):
                    artifact_errors.append(f"{task['id']} artifact audit does not use the exact verified download directory")
        ignored_refs = [
            ref for criterion in task.get("acceptance_criteria", [])
            for ref in _ignored_artifact_refs(criterion)
        ]
        if task.get("ignored_output_paths") and not task.get("artifact_binding"):
            artifact_errors.append(f"{task['id']} declares ignored output paths without artifact producer binding")
        if task.get("artifact_binding"):
            allowed = task.get("ignored_output_paths", [])
            for ref in ignored_refs:
                if not any(_matches(ref, pattern) for pattern in allowed):
                    artifact_errors.append(f"{task['id']} producer references undeclared ignored dist path {ref}")
        elif ignored_refs:
            artifact_errors.append(f"{task['id']} non-producer references ignored dist paths: {ignored_refs}")
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
    if _reachable("P1-REL02", by_id, "P1-WAYLAND-GATE01") or _reachable("P1-REL02", by_id, "P1-READY-CLAIM01"):
        errors.append("draft release bundle is conflated with Wayland/signing/channel approvals")

    int01 = by_id.get("P1-INT01", {})
    int_criteria = "\n".join(int01.get("acceptance_criteria", []))
    for required in (
        "branch_gate.py verify --task P1-SLICE01 --state independently_verified",
        "record_merge.py --task P1-SLICE01",
        "record_merge.py verify --task P1-SLICE01",
    ):
        if required not in int_criteria:
            errors.append("INT01 lacks reproducible Counter merge recording/verification")
    record_commands = [c for c in int01.get("acceptance_criteria", []) if "record_merge.py" in c and " verify " not in c]
    verify_record_commands = [c for c in int01.get("acceptance_criteria", []) if "record_merge.py verify" in c]
    if len(record_commands) != 1 or _parse_cli(record_commands[0]).get("--task") != ["P1-SLICE01"] or _parse_cli(record_commands[0]).get("--output") != ["evidence/P1-INT01/merge.json"]:
        errors.append("INT01 record_merge command identity/path is not canonical")
    if len(verify_record_commands) != 1 or _parse_cli(verify_record_commands[0]).get("--task") != ["P1-SLICE01"] or _parse_cli(verify_record_commands[0]).get("--record") != ["evidence/P1-INT01/merge.json"]:
        errors.append("INT01 record_merge verification identity/path is not canonical")
    if "P1-LIC01" not in by_id.get("P1-PR-AUDIT01", {}).get("deps", []):
        errors.append("AR09-G1/AR10-G3 aggregator lacks LIC01 repository evidence")
    for gate in ("AR09-G1", "AR10-G3"):
        if not any(sg.startswith(gate + ".repository-evidence") for t in phase1 for sg in [x["id"] for x in t.get("sub_gates", [])]):
            errors.append(f"{gate} lacks LIC01 repository-evidence sub-gate")
    if not any("tools/release/audit_msrv_claim.py" in c for c in by_id.get("P1-REL02", {}).get("acceptance_criteria", [])):
        errors.append("AR04-G6 lacks executable MSRV-claim audit")
    if "P1-OWNER-NOTICE01" not in by_id.get("P1-LICENSE-CLOSE01", {}).get("deps", []):
        errors.append("owner-notice input has no explicit producer dependency")
    if "P1-READY-BENCH01" in by_id or "P1-READY-RELEASE01" in by_id:
        errors.append("stale readiness task IDs remain")
    pytest_ini = repo_root / "pytest.ini"
    if not pytest_ini.exists() or "testpaths = .harness/scripts/tests" not in pytest_ini.read_text():
        errors.append("root pytest entry point is not configured")

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
                    if producer_id in {task["id"], "P0-PL01", "P0-REM06", "P0-REM08"}:
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
    expect_failure(
        "missing-schema-validation",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"] if "tools/gates/validate_result.py" not in c]
        ),
    )
    expect_failure(
        "missing-aggregate-invocation",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PLAT02")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-PLAT02")["acceptance_criteria"] if "tools/gates/aggregate.py" not in c]
        ),
    )
    expect_failure(
        "readiness-approval-self-certification",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01").update(workflow="readiness", completion_state="recorded"),
    )
    expect_failure(
        "build-premerge-completion",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").update(completion_state="independently_verified"),
    )
    expect_failure(
        "rustcontract-missing-session-check",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"] if "verify_roles.py" not in c]
        ),
    )
    expect_failure(
        "conrev-missing-branch-check",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-CONREV01")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-CONREV01")["acceptance_criteria"] if "branch_gate.py" not in c]
        ),
    )
    expect_failure(
        "int01-missing-merge-record",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-INT01")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-INT01")["acceptance_criteria"] if "record_merge.py" not in c]
        ),
    )
    expect_failure(
        "repository-gate-missing-lic01",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["deps"].remove("P1-LIC01"),
    )
    expect_failure(
        "msrv-audit-missing",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL02")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-REL02")["acceptance_criteria"] if "audit_msrv_claim.py" not in c]
        ),
    )
    expect_failure(
        "lic02-ignored-artifact",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].__setitem__(
            slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"] if "gh release download" not in c]
        ),
    )
    expect_failure(
        "rel02-wayland-dependency",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL02")["deps"].append("P1-WAYLAND-GATE01"),
    )
    expect_failure(
        "owner-notice-missing",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LICENSE-CLOSE01")["deps"].remove("P1-OWNER-NOTICE01"),
    )
    expect_failure(
        "d1-duplicate-result-path",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["gate_results"][1].update(
            path=next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["gate_results"][0]["path"]
        ),
    )
    expect_failure(
        "d1-validation-before-creation",
        lambda d: (
            lambda task: (
                task["acceptance_criteria"].__setitem__(
                    slice(None),
                    list(reversed(task["acceptance_criteria"])),
                )
            )
        )(next(t for t in d["tasks"] if t["id"] == "P1-TST01")),
    )
    expect_failure(
        "d2-control-code-producer",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-SESSION-REGISTRY01").update(
            workflow="control", completion_state="recorded"
        ),
    )
    expect_failure(
        "d3-missing-enforcement",
        lambda d: d["gate_model"]["AR09-G1"].update(required_sub_gates=["AR09-G1.repository-evidence"]),
    )
    expect_failure(
        "d4-audit-before-fetch",
        lambda d: (
            lambda task: (
                task["acceptance_criteria"].append(task["acceptance_criteria"].pop(0))
            )
        )(next(t for t in d["tasks"] if t["id"] == "P1-LIC02")),
    )
    expect_failure(
        "d5-dist-wildcard-bypass",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append(
            "python3 tools/release/audit_artifacts.py --artifacts dist/release/*.whl exits zero"
        ),
    )
    expect_failure(
        "d6-unbound-approval",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["sub_gates"][0].pop("approval_registry"),
    )
    expect_failure(
        "d7-wrong-gate-identity",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(
            slice(None), [c.replace("--gate AR02-G1.integrated-properties", "--gate AR02-G1.schema") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]
        ),
    )
    expect_failure(
        "d7-wrong-task-identity",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(
            slice(None), [c.replace("--task P1-TST01", "--task P1-PROTO01") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]
        ),
    )
    expect_failure(
        "d8-missing-registry-seed",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01")["deps"].remove("P1-SESSION-SEED01"),
    )
    expect_failure(
        "d9-fixture-enforcement",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(
            slice(None), [c.replace("evidence/P1-PR-AUDIT01/changed-files.txt", "tools/ci/tests/fixtures/changed-files.txt") if "pr_audit_gate.py" in c and "--self-test" not in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]
        ),
    )
    expect_failure(
        "d9-self-test-enforcement",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(
            slice(None), [c.replace("python3 tools/ci/pr_audit_gate.py", "python3 tools/ci/pr_audit_gate.py --self-test") if "pr_audit_gate.py" in c and "--output evidence/P1-PR-AUDIT01/AR09-G1.pr-enforcement.json" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]
        ),
    )
    for variant in ("dist/./release/*.whl", "dist/{release,local}/*.whl", "dist/*/*.whl"):
        expect_failure(
            f"d10-dist-variant-{variant}",
            lambda d, variant=variant: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append(
                f"python3 tools/release/audit_artifacts.py --artifacts {variant} exits zero"
            ),
        )
    expect_failure(
        "d11-noncanonical-seed-output",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-SESSION-SEED01")["acceptance_criteria"].__setitem__(
            0, next(t for t in d["tasks"] if t["id"] == "P1-SESSION-SEED01")["acceptance_criteria"][0].replace("--output .harness/sessions/registry.json", "--output evidence/P1-SESSION-SEED01/registry.json")
        ),
    )
    expect_failure(
        "d12-duplicate-write-gate",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--gate AR02-G1.integrated-properties", "--gate AR02-G1.integrated-properties --gate AR02-G1.schema") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d12-duplicate-write-task",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--task P1-TST01", "--task P1-TST01 --task P1-PROTO01") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d12-duplicate-validate-result",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --result evidence/P1-TST01/wrong.json exits zero", 1) if "validate_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d12-duplicate-aggregate-inputs",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --inputs evidence/P1-TST01/./AR02-G1.json exits zero", 1) if "aggregate.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d12-duplicate-aggregate-output",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --output evidence/P1-TST01/wrong.json exits zero", 1) if "aggregate.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d13-removed-approval-bindings",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" --approval-artifact evidence/P1-READY-CERT01/approval.json --approval-registry .harness/sessions/registry.json --approval-scope performance-certification", "") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d13-forged-approval-bindings",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("evidence/P1-READY-CERT01/approval.json", "forged.json").replace(".harness/sessions/registry.json", "untrusted.json").replace("performance-certification", "unrelated-claim") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d14-discarded-gh-output",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("> evidence/P1-PR-AUDIT01/pr.json", "> /dev/null").replace("> evidence/P1-PR-AUDIT01/changed-files.txt", "> /dev/null") if "gh pr " in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]),
    )
    expect_failure(
        "d14-fabricated-pr-artifacts",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].extend(["printf '{}' > evidence/P1-PR-AUDIT01/pr.json exits zero", "printf 'fake' > evidence/P1-PR-AUDIT01/changed-files.txt exits zero"]),
    )
    expect_failure(
        "d15-wrong-postmerge-command",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01").update(postmerge_command="python3 tools/ci/record_merge.py --task P1-GATE-SCHEMA01 --output evidence/P1-GATE-SCHEMA01/merge.json"),
    )
    expect_failure(
        "d15-wrong-postmerge-record",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01").update(postmerge_record="evidence/P1-GATE-SCHEMA01/merge.json"),
    )
    expect_failure(
        "d16-wrong-verify-manifest",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].__setitem__(slice(None), [c.replace("artifacts/release/<artifact-id>/manifest.json", "artifacts/local/<artifact-id>/manifest.json") if "store.py verify" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"]]),
    )
    expect_failure(
        "d16-dir-equals-audit-bypass",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--dir evidence/P1-LIC02/downloads", "--dir=evidence/P1-LIC02/downloads").replace("evidence/P1-LIC02/downloads/**", "somewhere-else/**") for c in next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"]]),
    )
    expect_failure(
        "d17-shell-escaped-dist",
        lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append(r"python3 tools/release/audit_artifacts.py --artifacts d\ist/release/*.whl exits zero"),
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default="5ce026d")
    parser.add_argument("--history-baseline", default="e54ecaf")
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
        ("PHASE1_FIELDS", not any("missing fields" in e or "branch evidence" in e or "must complete" in e or "unknown workflow" in e or "gates without" in e or "branch_state" in e or "schema validation" in e or "aggregate invocation" in e or "lacks pre-merge" in e or "lacks trusted session" in e or "code-producing control" in e or "gate_results" in e or "result path" in e or "write_result" in e or "duplicate CLI" in e or "postmerge command identity" in e for e in errors), f"tasks={metrics['phase1_total']}"),
        ("PHASE1_INITIAL_STATE", not any("blocked at attempt zero" in e or "max_attempts" in e or "P0-AP01 must" in e for e in errors), "blocked/attempt0/max4"),
        ("PHASE1_AP01_GATE", not any("not transitively gated" in e for e in errors), f"checked={metrics['phase1_total']}"),
        ("PLAN_TASK_ORDER", not any("plan/JSON Phase 1 task order" in e for e in errors), f"plan={metrics['plan_tasks']} json={metrics['phase1_total']}"),
        ("PLAN_JSON_METADATA", not any("mismatch" in e and any(w in e for w in ("dependency", "owner", "title", "size", "estimate")) for e in errors), f"checked={metrics['plan_tasks']}"),
        ("ADR_GATE_COVERAGE", metrics["adr_gates"] == metrics["plan_gates"] == metrics["task_gate_mappings"] and not any("full gate coverage" in e for e in errors), f"adr={metrics['adr_gates']} plan={metrics['plan_gates']} aggregators={metrics['task_gate_mappings']}"),
        ("ADR_GATE_MAPPINGS", not any("aggregator mappings" in e for e in errors), f"total={metrics['task_gate_mapping_total']}"),
        ("STAGED_GATE_CLOSURE", not any("sub-gate" in e or "aggregator" in e or "known deadlock" in e for e in errors), f"sub_gates={metrics['sub_gates']}"),
        ("GATE_RUNTIME", not any("schema validation" in e or "aggregate invocation" in e or "user-approval sub-gate" in e for e in errors), "schema+aggregate+independent-approval"),
        ("GATE_RESULT_LIFECYCLE", not any("result" in e and any(word in e for word in ("create", "validate", "shared", "self-overwrites", "gate_results", "path")) for e in errors), f"unique_paths={metrics.get('gate_result_paths', 0)}"),
        ("CANONICAL_RESULT_IDENTITY", not any("write_result identity" in e or "write_result outputs" in e for e in errors), "task+gate+path"),
        ("CLI_ARGUMENT_PARSING", not any("duplicate CLI flags" in e for e in errors), "singleton-flags"),
        ("SEED_CONTRACT", not any("session-registry seed" in e or "seed self-test" in e or "approval-hash" in e for e in errors), "self-test+hash+append+canonical"),
        ("REGISTRY_BOOTSTRAP", not any("session-registry seed" in e or "first merged build lacks" in e or "seeded trust root" in e for e in errors), "orchestrator-seed-before-build"),
        ("REAL_PR_EVIDENCE", not any("per-PR enforcement" in e or "enforcement evidence" in e or "enforcement command" in e or "enforcement producer" in e for e in errors), "gh-pr-identity+diff"),
        ("PR_CAPTURE_AUTHENTICITY", not any("identity capture" in e or "changed-file capture" in e or "gh output is discarded" in e or "fabricated writer" in e or "before real PR capture" in e for e in errors), "canonical-capture-no-fabrication"),
        ("APPROVAL_BINDING", not any("approval" in e or "not-applicable" in e or "approver" in e for e in errors), "session+artifact+registry+scope+prelock"),
        ("ATOMIC_GATE_EVIDENCE", not any("AR09-G1" in e or "AR10-G3" in e or "AR04-G6" in e or "owner-notice" in e or "per-PR enforcement" in e for e in errors), "repository+enforcement+MSRV+notice"),
        ("PHASE0_HISTORY", not any("Phase 0 history" in e or "baseline-done tasks missing" in e for e in errors), f"compared={metrics['phase0_history_compared']}"),
        ("COMMAND_PRODUCERS", not any("command path" in e for e in errors), f"criteria={metrics['acceptance_criteria_checked']}"),
        ("REVIEW_MERGE_STATES", not any("circular pre-merge" in e or "post-merge record" in e or "independent proof field" in e or "proof task is not gated" in e or "build task must complete" in e or "lacks pre-merge" in e or "lacks trusted session" in e or "INT01 lacks" in e for e in errors), "merged-deps+premerge+session"),
        ("POSTMERGE_IDENTITY", not any("postmerge command" in e or "postmerge record" in e or "record_merge command" in e or "record_merge verification" in e for e in errors), "task+output+record"),
        ("ARTIFACT_HANDOFF", not any("artifact" in e or "ignored dist" in e for e in errors), "draft-release/fetch/verify/normalized-dist"),
        ("ARTIFACT_COMMAND_BINDING", not any("verify manifest/directory" in e or "exact verified download" in e or "fetch/verify pair" in e for e in errors), "manifest+dir+audit-path"),
        ("DIST_NORMALIZATION", not any("ignored dist" in e or "undeclared ignored" in e for e in errors), "segments+braces+globs+shell-unescape"),
        ("CRATE_TAG_READINESS", not any("neutral test crate" in e or "illegally test" in e or "tag timing" in e or "tag does not prove" in e or "native-lane readiness" in e or "conflated" in e or "draft release bundle" in e for e in errors), "semantic"),
        ("PYTEST_ENTRYPOINT", "root pytest entry point" not in errors, "root pytest.ini"),
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
