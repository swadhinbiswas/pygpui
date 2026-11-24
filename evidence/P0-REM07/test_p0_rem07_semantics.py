"""Independent P0-REM07 semantic retest and adversarial contract tests.

Closure tests assert the original D1-D10 repairs. New attack tests assert the
stronger stated contracts; failures are unresolved findings, not tests to skip.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / ".harness/scripts/validate_phase1_graph.py"
SPEC = importlib.util.spec_from_file_location("p0_rem07_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

ATTACK_SPEC = importlib.util.spec_from_file_location(
    "p0_rem07_attack_probe", Path(__file__).with_name("attack_probe.py")
)
ATTACKS_MODULE = importlib.util.module_from_spec(ATTACK_SPEC)
assert ATTACK_SPEC.loader is not None
ATTACK_SPEC.loader.exec_module(ATTACKS_MODULE)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
SCHEMA = json.loads((ROOT / ".harness/schemas/gate-results.schema.json").read_text())
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "63beab0")
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


class TestOriginalDefectClosure:
    def test_base_graph_validates(self) -> None:
        assert VALIDATOR.validate(DATA, PLAN, BASELINE, ROOT, HISTORY)[0] == []

    def test_d1_result_paths_are_unique_canonical_and_ordered(self) -> None:
        results = [result for owner in PHASE1 for result in owner.get("gate_results", [])]
        assert len(results) == 78
        assert len({result["path"] for result in results}) == 78
        for owner in PHASE1:
            for result in owner.get("gate_results", []):
                assert result["path"] == f"evidence/{owner['id']}/{result['gate_id']}.json"
                criteria = owner["acceptance_criteria"]
                creates = [
                    i for i, text in enumerate(criteria)
                    if ("write_result.py" in text or "aggregate.py" in text)
                    and f"--output {result['path']}" in text
                ]
                validates = [
                    i for i, text in enumerate(criteria)
                    if "validate_result.py" in text and f"--result {result['path']}" in text
                ]
                assert len(creates) == len(validates) == 1
                assert creates[0] < validates[0]

    def test_d1_duplicate_result_path_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-PR-AUDIT01")
            owner["gate_results"][1]["path"] = owner["gate_results"][0]["path"]
        assert validate_mutation(mutate)

    def test_d1_validation_before_creation_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-TST01")
            create = next(i for i, text in enumerate(owner["acceptance_criteria"]) if "aggregate.py --gate AR02-G1" in text)
            validate = next(i for i, text in enumerate(owner["acceptance_criteria"]) if "validate_result.py" in text and "evidence/P1-TST01/AR02-G1.json" in text)
            owner["acceptance_criteria"][create], owner["acceptance_criteria"][validate] = (
                owner["acceptance_criteria"][validate], owner["acceptance_criteria"][create]
            )
        assert validate_mutation(mutate)

    def test_d2_foundational_tools_are_merged_builds(self) -> None:
        for task_id in ("P1-SESSION-REGISTRY01", "P1-GATE-SCHEMA01"):
            owner = BY_ID[task_id]
            assert owner["workflow"] == "build"
            assert owner["completion_state"] == "merged"
            assert owner["premerge_state"] == "independently_verified"
            assert owner["postmerge_state"] == "merged"
            assert owner["review_evidence"] and owner["test_evidence"]
            assert owner["postmerge_record"] and owner["postmerge_command"]

    def test_d2_control_code_producer_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            next(t for t in data["tasks"] if t["id"] == "P1-SESSION-REGISTRY01").update(
                workflow="control", completion_state="recorded"
            )
        assert validate_mutation(mutate)

    def test_d3_repository_and_enforcement_inputs_are_atomic(self) -> None:
        for gate in ("AR09-G1", "AR10-G3"):
            assert DATA["gate_model"][gate]["required_sub_gates"] == [
                f"{gate}.repository-evidence", f"{gate}.pr-enforcement"
            ]
            aggregate = next(
                text for text in BY_ID["P1-PR-AUDIT01"]["acceptance_criteria"]
                if "aggregate.py" in text and f"--gate {gate}" in text
            )
            assert f"evidence/P1-LIC01/{gate}.repository-evidence.json" in aggregate
            assert f"evidence/P1-PR-AUDIT01/{gate}.pr-enforcement.json" in aggregate

    def test_d3_missing_enforcement_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            data["gate_model"]["AR09-G1"]["required_sub_gates"] = ["AR09-G1.repository-evidence"]
        assert validate_mutation(mutate)

    def test_d4_license_audits_follow_fetch_and_verify_on_downloads(self) -> None:
        for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
            criteria = BY_ID[task_id]["acceptance_criteria"]
            fetch = next(i for i, text in enumerate(criteria) if "gh release download" in text)
            verify = next(i for i, text in enumerate(criteria) if "store.py verify" in text)
            audits = [i for i, text in enumerate(criteria) if "audit_artifacts.py" in text or "provenance_audit.py --mode artifact" in text]
            assert fetch < verify < min(audits)
            assert all(f"evidence/{task_id}/downloads/**" in criteria[i] for i in audits)

    def test_d4_audit_before_fetch_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-LIC02")
            fetch = next(text for text in owner["acceptance_criteria"] if "gh release download" in text)
            owner["acceptance_criteria"].remove(fetch)
            owner["acceptance_criteria"].append(fetch)
        assert validate_mutation(mutate)

    @pytest.mark.parametrize("variant", ["dist/release/*.whl", "dist/local/*.whl", "dist/./release/*.whl", "dist/{release,local}/*.whl", "dist/*/*.whl", "dist"])
    def test_d5_d10_documented_dist_variants_are_rejected(self, variant: str) -> None:
        def mutate(data: dict, variant: str = variant) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-LIC02")
            owner.pop("consumes_artifacts", None)
            owner["acceptance_criteria"] = [
                text for text in owner["acceptance_criteria"]
                if "gh release download" not in text and "store.py verify" not in text
            ]
            owner["acceptance_criteria"] = [
                text.replace("evidence/P1-LIC02/downloads/**", variant)
                for text in owner["acceptance_criteria"]
            ]
            owner["write_scope"].append("dist/**")
            owner["produces"].append("dist/**")
        assert validate_mutation(mutate)

    def test_d6_bound_prelock_approval_schema_and_order(self) -> None:
        jsonschema.validate(approval_record(), SCHEMA)
        for field in ("approver_session_id", "approval_artifact", "approval_registry", "approval_scope"):
            invalid = approval_record()
            invalid.pop(field)
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(invalid, SCHEMA)
        for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
            criteria = BY_ID[task_id]["acceptance_criteria"]
            write = next(i for i, text in enumerate(criteria) if "write_result.py" in text)
            validate = next(i for i, text in enumerate(criteria) if "validate_result.py" in text)
            approval = next(i for i, text in enumerate(criteria) if "verify_approval.py" in text)
            proof = next(i for i, text in enumerate(criteria) if "verify_proof.py" in text and "--gate-result" in text)
            assert write < validate < approval < proof
            assert "--lockfile-state not_applicable" in criteria[write]

    def test_d6_missing_subgate_approval_binding_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            next(t for t in data["tasks"] if t["id"] == "P1-READY-CERT01")["sub_gates"][0].pop("approval_registry")
        assert validate_mutation(mutate)

    def test_d7_wrong_gate_and_task_identities_are_rejected(self) -> None:
        def wrong_gate(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-TST01")
            owner["acceptance_criteria"] = [
                text.replace("--gate AR02-G1.integrated-properties", "--gate AR02-G1.schema")
                if "write_result.py" in text else text
                for text in owner["acceptance_criteria"]
            ]
        def wrong_task(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-TST01")
            owner["acceptance_criteria"] = [
                text.replace("--task P1-TST01", "--task P1-PROTO01")
                if "write_result.py" in text else text
                for text in owner["acceptance_criteria"]
            ]
        assert validate_mutation(wrong_gate)
        assert validate_mutation(wrong_task)

    def test_d8_seed_precedes_first_build_and_registry_extends_it(self) -> None:
        seed = BY_ID["P1-SESSION-SEED01"]
        assert seed["owner_role"] == "Orchestrator"
        assert seed["workflow"] == "control"
        assert ".harness/sessions/registry.json" in seed["produces"]
        assert "P1-SESSION-SEED01" in BY_ID["P1-TOOL-BRANCH01"]["deps"]
        assert "P1-SESSION-SEED01" in BY_ID["P1-SESSION-REGISTRY01"]["deps"]
        assert not VALIDATOR._reachable("P1-SESSION-SEED01", BY_ID, "P1-TOOL-BRANCH01")

    def test_d8_missing_seed_dependency_is_rejected(self) -> None:
        def mutate(data: dict) -> None:
            next(t for t in data["tasks"] if t["id"] == "P1-TOOL-BRANCH01")["deps"].remove("P1-SESSION-SEED01")
        assert validate_mutation(mutate)

    def test_d9_current_capture_and_producers_use_gh_derived_artifacts(self) -> None:
        criteria = BY_ID["P1-PR-AUDIT01"]["acceptance_criteria"]
        assert any("gh pr view" in text and "--json number,headRefOid,baseRefOid,author,state" in text for text in criteria)
        assert any("gh pr diff" in text and "--name-only" in text for text in criteria)
        producers = [text for text in criteria if "pr_audit_gate.py" in text and "--output evidence/P1-PR-AUDIT01/" in text]
        assert len(producers) == 2
        assert all("--self-test" not in text and "fixtures/" not in text for text in producers)
        assert all("--pr evidence/P1-PR-AUDIT01/pr.json" in text for text in producers)
        assert all("--changed-files evidence/P1-PR-AUDIT01/changed-files.txt" in text for text in producers)

    def test_d9_fixture_and_self_test_producers_are_rejected(self) -> None:
        def fixture(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-PR-AUDIT01")
            owner["acceptance_criteria"] = [
                text.replace("evidence/P1-PR-AUDIT01/changed-files.txt", "tools/ci/tests/fixtures/changed-files.txt")
                if "pr_audit_gate.py" in text and "--self-test" not in text else text
                for text in owner["acceptance_criteria"]
            ]
        def selftest(data: dict) -> None:
            owner = next(t for t in data["tasks"] if t["id"] == "P1-PR-AUDIT01")
            owner["acceptance_criteria"] = [
                text.replace("python3 tools/ci/pr_audit_gate.py", "python3 tools/ci/pr_audit_gate.py --self-test")
                if "pr_audit_gate.py" in text and "--output evidence/P1-PR-AUDIT01/AR09-G1.pr-enforcement.json" in text else text
                for text in owner["acceptance_criteria"]
            ]
        assert validate_mutation(fixture)
        assert validate_mutation(selftest)

    def test_phase0_authorization_and_all_phase1_tasks_remain_blocked(self) -> None:
        assert BY_ID["P0-AP01"]["status"] == "blocked"
        assert BY_ID["P0-AP01"]["attempt_count"] == 0
        assert all(owner["status"] == "blocked" and owner["attempt_count"] == 0 for owner in PHASE1)


class TestNewAdversarialAttacks:
    @pytest.mark.parametrize("name,mutate", ATTACKS_MODULE.ATTACKS, ids=[name for name, _ in ATTACKS_MODULE.ATTACKS])
    def test_validator_rejects_new_semantic_attack(self, name: str, mutate) -> None:
        assert validate_mutation(mutate), f"validator accepted unsafe attack: {name}"


class TestSeedTrustRootContract:
    def test_documented_seed_self_test_command_exits_zero(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"), "--self-test"],
            cwd=ROOT, text=True, capture_output=True,
        )
        assert result.returncode == 0, result.stderr

    def test_seed_approval_hash_matches_written_registry_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            result = subprocess.run(
                ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"),
                 "--orchestrator-session", "orch-1", "--output", str(registry), "--approval", str(approval)],
                cwd=ROOT, text=True, capture_output=True,
            )
            assert result.returncode == 0, result.stderr
            approval_data = json.loads(approval.read_text())
            actual = hashlib.sha256(registry.read_bytes()).hexdigest()
            assert approval_data["registry_sha256"] == actual

    def test_reseed_preserves_existing_append_only_sessions(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            command = ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"),
                       "--output", str(registry), "--approval", str(approval)]
            first = subprocess.run(command + ["--orchestrator-session", "orch-1"], cwd=ROOT, text=True, capture_output=True)
            assert first.returncode == 0, first.stderr
            before = set(json.loads(registry.read_text())["sessions"])
            second = subprocess.run(command + ["--orchestrator-session", "orch-2"], cwd=ROOT, text=True, capture_output=True)
            assert second.returncode == 0, second.stderr
            after = set(json.loads(registry.read_text())["sessions"])
            assert before.issubset(after)
