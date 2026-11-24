from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
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
        cls.history_baseline = VALIDATOR._load_baseline(ROOT, "e54ecaf")

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

    def test_d1_duplicate_result_path_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["gate_results"][1].update(path=next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["gate_results"][0]["path"]))

    def test_d1_aggregate_self_overwrite_is_rejected(self) -> None:
        def mutate(d):
            task = next(t for t in d["tasks"] if t["id"] == "P1-TST01")
            for index, criterion in enumerate(task["acceptance_criteria"]):
                if "tools/gates/aggregate.py --gate AR02-G1" in criterion:
                    task["acceptance_criteria"][index] = criterion.replace(
                        "--output evidence/P1-TST01/AR02-G1.json",
                        "--output evidence/P1-PROTO01/AR02-G1.schema.json",
                    )
                    break
        self.assert_invalid(mutate)

    def test_d1_validation_before_creation_is_rejected(self) -> None:
        def mutate(d):
            task = next(t for t in d["tasks"] if t["id"] == "P1-TST01")
            validate_index = next(i for i, c in enumerate(task["acceptance_criteria"]) if "validate_result.py" in c and "AR02-G1.json" in c)
            create_index = next(i for i, c in enumerate(task["acceptance_criteria"]) if "aggregate.py --gate AR02-G1" in c)
            task["acceptance_criteria"][validate_index], task["acceptance_criteria"][create_index] = task["acceptance_criteria"][create_index], task["acceptance_criteria"][validate_index]
        self.assert_invalid(mutate)

    def test_d1_pr_audit_outputs_are_distinct(self) -> None:
        task = next(t for t in self.data["tasks"] if t["id"] == "P1-PR-AUDIT01")
        paths = [r["path"] for r in task["gate_results"] if r["gate_id"] in {"AR09-G1", "AR10-G3"}]
        self.assertEqual(2, len(set(paths)))

    def test_d2_control_code_producer_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-SESSION-REGISTRY01").update(workflow="control", completion_state="recorded"))

    def test_d2_gate_schema_control_producer_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GATE-SCHEMA01").update(workflow="control", completion_state="recorded"))

    def test_d3_missing_enforcement_subgate_is_rejected(self) -> None:
        self.assert_invalid(lambda d: d["gate_model"]["AR09-G1"].update(required_sub_gates=["AR09-G1.repository-evidence"]))

    def test_d3_missing_enforcement_command_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(slice(None), [c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"] if "pr_audit_gate.py" not in c]))

    def test_d4_audit_before_fetch_is_rejected(self) -> None:
        def mutate(d):
            task = next(t for t in d["tasks"] if t["id"] == "P1-LIC02")
            fetch = next(c for c in task["acceptance_criteria"] if "gh release download" in c)
            task["acceptance_criteria"].remove(fetch)
            task["acceptance_criteria"].append(fetch)
        self.assert_invalid(mutate)

    def test_d4_audit_against_non_downloaded_path_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LICENSE-CLOSE01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("evidence/P1-LICENSE-CLOSE01/downloads/**", "somewhere-else/**") if "audit_artifacts.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-LICENSE-CLOSE01")["acceptance_criteria"]]))

    def test_d5_dist_wildcard_bypass_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append("python3 tools/release/audit_artifacts.py --artifacts dist/release/*.whl exits zero"))

    def test_d5_dist_local_wildcard_bypass_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append("python3 tools/release/audit_artifacts.py --artifacts dist/local/*.whl exits zero"))

    def test_d6_unbound_approval_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["sub_gates"][0].pop("approval_registry"))

    def test_d7_wrong_gate_identity_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--gate AR02-G1.integrated-properties", "--gate AR02-G1.schema") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d7_wrong_task_identity_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--task P1-TST01", "--task P1-PROTO01") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d8_missing_registry_seed_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01")["deps"].remove("P1-SESSION-SEED01"))

    def test_d8_non_orchestrator_seed_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-SESSION-SEED01").update(owner_role="Release-CI-Engineer"))

    def test_d9_fixture_enforcement_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("evidence/P1-PR-AUDIT01/changed-files.txt", "tools/ci/tests/fixtures/changed-files.txt") if "pr_audit_gate.py" in c and "--self-test" not in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]))

    def test_d9_self_test_enforcement_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("python3 tools/ci/pr_audit_gate.py", "python3 tools/ci/pr_audit_gate.py --self-test") if "pr_audit_gate.py" in c and "--output evidence/P1-PR-AUDIT01/AR09-G1.pr-enforcement.json" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]))

    def test_d10_normalized_dist_variants_are_rejected(self) -> None:
        for variant in ("dist/./release/*.whl", "dist/{release,local}/*.whl", "dist/*/*.whl"):
            with self.subTest(variant=variant):
                self.assert_invalid(lambda d, variant=variant: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append(f"python3 tools/release/audit_artifacts.py --artifacts {variant} exits zero"))

    def test_d10_nonproducer_bare_dist_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append("python3 tools/release/audit_artifacts.py --artifacts dist exits zero"))

    def test_d11_ncanonical_seed_output_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-SESSION-SEED01")["acceptance_criteria"].__setitem__(0, next(t for t in d["tasks"] if t["id"] == "P1-SESSION-SEED01")["acceptance_criteria"][0].replace("--output .harness/sessions/registry.json", "--output evidence/P1-SESSION-SEED01/registry.json")))

    def test_d12_duplicate_write_gate_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--gate AR02-G1.integrated-properties", "--gate AR02-G1.integrated-properties --gate AR02-G1.schema") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d12_duplicate_write_task_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("--task P1-TST01", "--task P1-TST01 --task P1-PROTO01") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d12_duplicate_validate_result_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --result evidence/P1-TST01/wrong.json exits zero", 1) if "validate_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d12_duplicate_aggregate_inputs_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --inputs evidence/P1-TST01/./AR02-G1.json exits zero", 1) if "aggregate.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d12_duplicate_aggregate_output_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" exits zero", " --output evidence/P1-TST01/wrong.json exits zero", 1) if "aggregate.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-TST01")["acceptance_criteria"]]))

    def test_d13_removed_approval_bindings_are_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace(" --approval-artifact evidence/P1-READY-CERT01/approval.json --approval-registry .harness/sessions/registry.json --approval-scope performance-certification", "") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"]]))

    def test_d13_forged_approval_bindings_are_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("evidence/P1-READY-CERT01/approval.json", "forged.json").replace(".harness/sessions/registry.json", "untrusted.json").replace("performance-certification", "unrelated-claim") if "write_result.py" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-READY-CERT01")["acceptance_criteria"]]))

    def test_d14_discarded_gh_output_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].__setitem__(slice(None), [c.replace("> evidence/P1-PR-AUDIT01/pr.json", "> /dev/null").replace("> evidence/P1-PR-AUDIT01/changed-files.txt", "> /dev/null") if "gh pr " in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"]]))

    def test_d14_fabricated_pr_artifacts_are_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PR-AUDIT01")["acceptance_criteria"].extend(["printf '{}' > evidence/P1-PR-AUDIT01/pr.json exits zero", "printf 'fake' > evidence/P1-PR-AUDIT01/changed-files.txt exits zero"]))

    def test_d15_wrong_postmerge_command_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01").update(postmerge_command="python3 tools/ci/record_merge.py --task P1-GATE-SCHEMA01 --output evidence/P1-GATE-SCHEMA01/merge.json"))

    def test_d15_wrong_postmerge_record_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-BRANCH01").update(postmerge_record="evidence/P1-GATE-SCHEMA01/merge.json"))

    def test_d16_wrong_verify_manifest_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].__setitem__(slice(None), [c.replace("artifacts/release/<artifact-id>/manifest.json", "artifacts/local/<artifact-id>/manifest.json") if "store.py verify" in c else c for c in next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"]]))

    def test_d16_dir_equals_audit_bypass_is_rejected(self) -> None:
        def mutate(d):
            task = next(t for t in d["tasks"] if t["id"] == "P1-LIC02")
            task["acceptance_criteria"] = [
                c.replace("--dir evidence/P1-LIC02/downloads", "--dir=evidence/P1-LIC02/downloads").replace("evidence/P1-LIC02/downloads/**", "somewhere-else/**")
                for c in task["acceptance_criteria"]
            ]
        self.assert_invalid(mutate)

    def test_d17_shell_escaped_dist_is_rejected(self) -> None:
        self.assert_invalid(lambda d: next(t for t in d["tasks"] if t["id"] == "P1-LIC02")["acceptance_criteria"].append(r"python3 tools/release/audit_artifacts.py --artifacts d\ist/release/*.whl exits zero"))


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

    def test_approval_without_artifact_or_registry_fails(self) -> None:
        record = dict(self.valid)
        record.pop("approval_artifact")
        record.pop("approval_registry")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(record, self.schema)

    def test_prelock_not_applicable_without_hash_is_valid(self) -> None:
        record = dict(self.valid)
        record["lockfile"] = {"state": "not_applicable", "reason": "approval precedes production lockfile"}
        jsonschema.validate(record, self.schema)

    def test_sha256_lockfile_without_hash_fails(self) -> None:
        record = dict(self.valid)
        record["lockfile"] = {"state": "sha256"}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(record, self.schema)


class SessionSeedScriptTests(unittest.TestCase):
    def test_seed_self_test_passes(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"), "--orchestrator-session", "orch-1", "--self-test"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SESSION_SEED_SELF_TEST=PASS", result.stdout)

    def test_seed_creates_bound_registry_and_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            result = subprocess.run(
                ["python3", str(ROOT / ".harness/scripts/seed_session_registry.py"), "--orchestrator-session", "orch-1", "--output", str(registry), "--approval", str(approval)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            registry_data = json.loads(registry.read_text())
            approval_data = json.loads(approval.read_text())
            self.assertEqual("orchestrator", registry_data["trust_root"])
            self.assertEqual("orchestrator", registry_data["sessions"]["orch-1"]["role"])
            self.assertEqual("orch-1", approval_data["approver_session_id"])
            self.assertEqual(64, len(approval_data["registry_sha256"]))


if __name__ == "__main__":
    unittest.main()
