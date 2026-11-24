from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = ROOT / ".harness" / "scripts" / "validate_phase1_graph.py"
SPEC = importlib.util.spec_from_file_location("phase1_graph_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class GraphValidatorSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((ROOT / ".harness" / "TASKS.json").read_text())
        cls.plan = (ROOT / ".harness" / "PLANS" / "phase-1-vertical-slice.md").read_text()
        cls.baseline = VALIDATOR._load_baseline(ROOT, "5ce026d")
        cls.history_baseline = VALIDATOR._load_baseline(ROOT, "b9a8504")

    def assert_invalid(self, mutate_data=None, mutate_plan=None) -> None:
        data = copy.deepcopy(self.data)
        plan = self.plan
        if mutate_data:
            mutate_data(data)
        if mutate_plan:
            plan = mutate_plan(plan)
        errors, _ = VALIDATOR.validate(data, plan, self.baseline, ROOT, self.history_baseline)
        self.assertTrue(errors, "mutated graph unexpectedly validated")

    def test_base_graph_is_valid(self) -> None:
        errors, _ = VALIDATOR.validate(self.data, self.plan, self.baseline, ROOT, self.history_baseline)
        self.assertEqual([], errors)

    def test_duplicate_id_is_rejected(self) -> None:
        self.assert_invalid(lambda d: d["tasks"].append(copy.deepcopy(next(t for t in d["tasks"] if t["id"] == "P1-GOV01"))))

    def test_missing_dependency_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["deps"].append("P1-NOEXIST"))

    def test_cycle_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AP01")["deps"].append("P1-GOV01"))

    def test_active_phase1_task_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01").update(status="done"))

    def test_missing_gate_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].remove("AR01-G3"))

    def test_unowned_command_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01")["acceptance_criteria"].append("python3 tools/missing/proof.py exits zero"))

    def test_scope_mismatch_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-GRAPH01").update(write_scope=["unrelated/**"]))

    def test_missing_review_evidence_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").pop("review_evidence", None))

    def test_stale_remote_claim_is_rejected(self) -> None:
        self.assert_invalid(lambda d: d.update(git_workflow={**d["git_workflow"], "merge_policy": "No remote PR is required " + d["git_workflow"]["merge_policy"]}))

    def test_plan_json_mismatch_is_rejected(self) -> None:
        self.assert_invalid(mutate_plan=lambda p: p.replace("`P1-GOV01`", "`P1-GOV99`"))

    def test_title_mismatch_is_rejected(self) -> None:
        self.assert_invalid(mutate_plan=lambda p: p.replace("Authorize Phase 1 and record execution readiness", "Wrong title", 1))

    def test_gate_mapping_mismatch_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].append("AR01-G4"))

    def test_baseline_done_task_mutation_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AR01").update(title="Mutated"))

    def test_duplicate_producer_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["produces"].append("Cargo.toml"))

    def test_producer_outside_scope_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["produces"].append("unowned/file.txt"))

    def test_all_known_deadlocks_are_rejected(self) -> None:
        for pattern in self.data["known_deadlock_patterns"]:
            with self.subTest(pattern=pattern["name"]):
                self.assert_invalid(
                    lambda d, p=pattern: next(t for t in d["tasks"] if t["id"] == p["upstream_task"])["gates"].append(p["gate"])
                )

    def test_ar03_g5_forbidden_internal_contract_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["sub_gates"].append({"id": "AR03-G5.internal-contracts", "stage": "internal-contracts", "evidence": "evidence/P1-ARCH01/gate-results.json"}))

    def test_ignored_artifact_handoff_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"] if "gh release download" not in c]))

    def test_premerge_merged_state_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["acceptance_criteria"].append("python3 tools/ci/branch_gate.py verify --task P1-ARCH01 --state merged exits zero"))

    def test_proof_self_certification_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01").pop("review_evidence", None))

    def test_illegal_core_test_dependency_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"].append("cargo test -p pygpui-core --test internal_contracts exits zero"))

    def test_post_contract_tag_timing_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TAG-CONTRACT01")["deps"].append("P1-PROTO01"))

    def test_missing_native_lane_readiness_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL01")["deps"].remove("P1-NATIVE-READY01"))

    def test_conflated_claim_readiness_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["deps"].append("P1-READY-CERT01"))

    def test_missing_schema_validation_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"] if "tools/gates/validate_result.py" not in c]))

    def test_missing_aggregate_invocation_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PLAT02")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-PLAT02")["acceptance_criteria"] if "tools/gates/aggregate.py" not in c]))

    def test_readiness_approval_self_certification_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01").update(workflow="readiness", completion_state="recorded"))

    def test_build_premerge_completion_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").update(completion_state="independently_verified"))

    def test_rustcontract_missing_session_check_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-RUSTCONTRACT01")["acceptance_criteria"] if "verify_roles.py" not in c]))

    def test_conrev_missing_branch_check_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-CONREV01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-CONREV01")["acceptance_criteria"] if "branch_gate.py" not in c]))

    def test_int01_missing_merge_record_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-INT01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-INT01")["acceptance_criteria"] if "record_merge.py" not in c]))

    def test_repository_gate_missing_lic01_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["deps"].remove("P1-LIC01"))

    def test_msrv_audit_missing_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL02")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-REL02")["acceptance_criteria"] if "audit_msrv_claim.py" not in c]))

    def test_lic02_ignored_artifact_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"] if "gh release download" not in c]))

    def test_rel02_wayland_dependency_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-REL02")["deps"].append("P1-WAYLAND-GATE01"))

    def test_owner_notice_missing_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LICENSE-CLOSE01")["deps"].remove("P1-OWNER-NOTICE01"))


class GateResultSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((ROOT / ".harness/schemas/gate-results.schema.json").read_text())
        cls.valid = {
            "schema_version": 1,
            "gate_id": "AR08-G6.approval",
            "task_id": "P1-READY-CERT01",
            "stage": "approval",
            "status": "pass",
            "evidence_type": "user-approval",
            "evidence": [{"path": "evidence/P1-READY-CERT01/approval.json", "sha256": "a" * 64}],
            "source_commit": "b" * 40,
            "lockfile_sha256": "c" * 64,
            "toolchain": "rustc 1.100.0",
            "reviewer_session_id": "reviewer-1",
            "tester_session_id": "tester-1",
            "approver_session_id": "approver-1",
            "aggregator": False,
        }

    def test_valid_approval_record_passes(self) -> None:
        jsonschema.validate(self.valid, self.schema)

    def test_missing_session_ids_fail(self) -> None:
        record = dict(self.valid)
        record.pop("reviewer_session_id")
        record.pop("tester_session_id")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(record, self.schema)

    def test_user_approval_without_approver_fails(self) -> None:
        record = dict(self.valid)
        record.pop("approver_session_id")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(record, self.schema)

    def test_missing_evidence_type_fails(self) -> None:
        record = dict(self.valid)
        record.pop("evidence_type")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(record, self.schema)


if __name__ == "__main__":
    unittest.main()
