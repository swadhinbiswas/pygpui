"""Independent P0-REM05 adversarial tests.

Closure tests assert the revised graph's current invariants. Defect-attack tests
assert the stronger machine-checkable contract required by the remediation plan;
their failures are findings, not tests to weaken or skip.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "p0_rem05_validator", ROOT / ".harness/scripts/validate_phase1_graph.py"
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


def validate_mutation(mutator) -> list[str]:
    changed = copy.deepcopy(DATA)
    mutator(changed)
    return VALIDATOR.validate(changed, PLAN, BASELINE, ROOT, HISTORY)[0]


def approval_record() -> dict:
    return {
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
        "approval_registry": {"path": ".harness/sessions/registry.json", "sha256": "e" * 64},
        "approval_scope": "performance-certification",
        "aggregator": False,
    }


class TestRemediationClosure:
    def test_base_graph_validates(self) -> None:
        assert VALIDATOR.validate(DATA, PLAN, BASELINE, ROOT, HISTORY)[0] == []

    def test_all_78_result_paths_are_unique_canonical_and_created_before_validation(self) -> None:
        results = [result for owner in PHASE1 for result in owner.get("gate_results", [])]
        assert len(results) == 78
        assert len({result["path"] for result in results}) == 78
        for owner in PHASE1:
            for result in owner.get("gate_results", []):
                assert result["path"] == f"evidence/{owner['id']}/{result['gate_id']}.json"
                criteria = owner["acceptance_criteria"]
                create = next(
                    i
                    for i, criterion in enumerate(criteria)
                    if ("write_result.py" in criterion or "aggregate.py" in criterion)
                    and f"--output {result['path']}" in criterion
                )
                validate = next(
                    i
                    for i, criterion in enumerate(criteria)
                    if "validate_result.py" in criterion and f"--result {result['path']}" in criterion
                )
                assert create < validate

    def test_no_aggregate_reads_its_output_and_pr_audit_outputs_are_distinct(self) -> None:
        for owner in PHASE1:
            for criterion in owner["acceptance_criteria"]:
                if "aggregate.py" not in criterion or "--gate " not in criterion:
                    continue
                words = criterion.split(" exits zero", 1)[0].split()
                output = words[words.index("--output") + 1]
                inputs = words[words.index("--inputs") + 1].split(",")
                assert output not in inputs
        pr_outputs = [
            result["path"]
            for result in BY_ID["P1-PR-AUDIT01"]["gate_results"]
            if result["gate_id"] in {"AR09-G1", "AR10-G3"}
        ]
        assert pr_outputs == [
            "evidence/P1-PR-AUDIT01/AR09-G1.json",
            "evidence/P1-PR-AUDIT01/AR10-G3.json",
        ]

    def test_foundational_session_and_schema_tasks_are_merged_builds(self) -> None:
        for task_id in ("P1-SESSION-REGISTRY01", "P1-GATE-SCHEMA01"):
            owner = BY_ID[task_id]
            assert owner["workflow"] == "build"
            assert owner["completion_state"] == "merged"
            assert owner["premerge_state"] == "independently_verified"
            assert owner["postmerge_state"] == "merged"
            assert owner["review_evidence"] and owner["test_evidence"]
            assert owner["postmerge_record"] and owner["postmerge_command"]

    def test_repository_gates_stage_repository_and_enforcement_inputs(self) -> None:
        for gate in ("AR09-G1", "AR10-G3"):
            assert DATA["gate_model"][gate]["required_sub_gates"] == [
                f"{gate}.repository-evidence",
                f"{gate}.pr-enforcement",
            ]
            aggregate = next(
                criterion
                for criterion in BY_ID["P1-PR-AUDIT01"]["acceptance_criteria"]
                if "aggregate.py" in criterion and f"--gate {gate}" in criterion
            )
            assert f"evidence/P1-LIC01/{gate}.repository-evidence.json" in aggregate
            assert f"evidence/P1-PR-AUDIT01/{gate}.pr-enforcement.json" in aggregate

    def test_license_audits_run_after_fetch_verify_on_downloaded_files(self) -> None:
        for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
            criteria = BY_ID[task_id]["acceptance_criteria"]
            fetch = next(i for i, criterion in enumerate(criteria) if "gh release download" in criterion)
            verify = next(i for i, criterion in enumerate(criteria) if "store.py verify" in criterion)
            audits = [
                i
                for i, criterion in enumerate(criteria)
                if "audit_artifacts.py" in criterion or "provenance_audit.py --mode artifact" in criterion
            ]
            download_dir = f"evidence/{task_id}/downloads"
            assert fetch < verify < min(audits)
            assert all(download_dir in criteria[index] for index in audits)
            assert not any("dist/release" in criterion or "dist/local" in criterion for criterion in criteria)

    def test_bound_prelock_approvals_validate_and_verification_is_ordered(self) -> None:
        jsonschema.validate(approval_record(), SCHEMA)
        for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
            criteria = BY_ID[task_id]["acceptance_criteria"]
            write = next(i for i, criterion in enumerate(criteria) if "write_result.py" in criterion)
            validate = next(i for i, criterion in enumerate(criteria) if "validate_result.py" in criterion)
            verify = next(i for i, criterion in enumerate(criteria) if "verify_approval.py" in criterion)
            proof = next(i for i, criterion in enumerate(criteria) if "verify_proof.py" in criterion and "--gate-result" in criterion)
            assert write < validate < verify < proof
            assert "--lockfile-state not_applicable" in criteria[write]
            assert not VALIDATOR._reachable(task_id, BY_ID, "P1-ARCH01")

    def test_phase0_authorization_remains_blocked(self) -> None:
        assert BY_ID["P0-AP01"]["status"] == "blocked"
        assert BY_ID["P0-AP01"]["attempt_count"] == 0
        assert all(owner["status"] == "blocked" and owner["attempt_count"] == 0 for owner in PHASE1)


class TestUnresolvedDefectAttacks:
    def test_result_gate_and_task_ids_must_match_the_canonical_path(self) -> None:
        for owner in PHASE1:
            for result in owner.get("gate_results", []):
                command = next(
                    criterion
                    for criterion in owner["acceptance_criteria"]
                    if ("write_result.py" in criterion or "aggregate.py" in criterion)
                    and f"--output {result['path']}" in criterion
                )
                words = command.split(" exits zero", 1)[0].split()
                if "write_result.py" in command:
                    assert words[words.index("--gate") + 1] == result["gate_id"]
                    assert words[words.index("--task") + 1] == owner["id"]

    def test_validator_rejects_a_wrong_gate_id_at_a_canonical_result_path(self) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-TST01")
            index = next(
                i
                for i, criterion in enumerate(owner["acceptance_criteria"])
                if "write_result.py" in criterion and "--gate AR02-G1.integrated-properties" in criterion
            )
            owner["acceptance_criteria"][index] = owner["acceptance_criteria"][index].replace(
                "--gate AR02-G1.integrated-properties", "--gate AR02-G1.schema"
            )

        assert validate_mutation(mutate)

    def test_enforcement_evidence_is_derived_from_a_pr_not_a_committed_fixture(self) -> None:
        commands = [
            criterion
            for criterion in BY_ID["P1-PR-AUDIT01"]["acceptance_criteria"]
            if "pr_audit_gate.py" in criterion and "--gate AR" in criterion
        ]
        assert len(commands) == 2
        assert all("tools/ci/tests/fixtures/" not in command for command in commands)
        assert all(
            "--pr " in command or "gh pr diff" in command or "--changed-files evidence/P1-PR-AUDIT01/" in command
            for command in commands
        )

    def test_validator_rejects_self_test_only_per_pr_enforcement(self) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-PR-AUDIT01")
            for index, criterion in enumerate(owner["acceptance_criteria"]):
                if "pr_audit_gate.py" in criterion and "--gate AR" in criterion:
                    gate = "AR09-G1" if "AR09-G1" in criterion else "AR10-G3"
                    owner["acceptance_criteria"][index] = (
                        "python3 tools/ci/pr_audit_gate.py --policy tools/ci/pr_audit_policy.json "
                        f"--self-test --gate {gate} --output evidence/P1-PR-AUDIT01/{gate}.pr-enforcement.json exits zero"
                    )

        assert validate_mutation(mutate)

    @pytest.mark.parametrize(
        "variant",
        ["dist/./release/*.whl", "dist/{release,local}/*.whl", "dist/*/*.whl"],
    )
    def test_validator_rejects_normalized_or_shell_expanded_ignored_dist_variants(self, variant: str) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-LIC02")
            owner.pop("consumes_artifacts", None)
            owner["acceptance_criteria"] = [
                criterion
                for criterion in owner["acceptance_criteria"]
                if "gh release download" not in criterion and "store.py verify" not in criterion
            ]
            owner["acceptance_criteria"] = [
                criterion.replace("evidence/P1-LIC02/downloads/**", variant)
                for criterion in owner["acceptance_criteria"]
            ]
            owner["write_scope"].append("dist/**")
            owner["produces"].append("dist/**")

        assert validate_mutation(mutate)

    def test_first_merged_tool_task_has_an_available_trusted_registry_producer(self) -> None:
        registry = ".harness/sessions/registry.json"
        producers = [
            owner["id"]
            for owner in PHASE1
            if any(VALIDATOR._matches(registry, pattern) for pattern in owner.get("produces", []))
        ]
        assert producers == ["P1-SESSION-REGISTRY01"]
        assert not VALIDATOR._reachable("P1-TOOL-BRANCH01", BY_ID, "P1-SESSION-REGISTRY01")
        assert any(
            VALIDATOR._matches(registry, pattern)
            for pattern in BY_ID["P1-TOOL-BRANCH01"]["write_scope"]
        ) or any(
            VALIDATOR._reachable("P1-TOOL-BRANCH01", BY_ID, producer)
            for producer in producers
        )
