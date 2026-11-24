from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = ROOT / ".harness" / "scripts" / "validate_phase1_graph.py"
SPEC = importlib.util.spec_from_file_location("phase1_graph_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class GraphValidatorNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads((ROOT / ".harness" / "TASKS.json").read_text())
        cls.plan = (ROOT / ".harness" / "PLANS" / "phase-1-vertical-slice.md").read_text()
        cls.baseline = VALIDATOR._load_baseline(ROOT, "5ce026d")
        cls.history_baseline = VALIDATOR._load_baseline(ROOT, "c5ed5f3")

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
        self.assert_invalid(
            lambda d: d["tasks"].append(copy.deepcopy(next(t for t in d["tasks"] if t["id"] == "P1-GOV01")))
        )

    def test_missing_dependency_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01")["deps"].append("P1-NOEXIST")
        )

    def test_cycle_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AP01")["deps"].append("P1-GOV01")
        )

    def test_active_phase1_task_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01").update(status="done")
        )

    def test_missing_gate_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].remove("AR01-G3")
        )

    def test_unowned_command_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-GOV01")["acceptance_criteria"].append(
                "python3 tools/missing/proof.py exits zero"
            )
        )

    def test_scope_mismatch_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-TOOL-GRAPH01").update(
                write_scope=["unrelated/**"]
            )
        )

    def test_missing_review_evidence_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-ARCH01").pop("review_evidence", None)
        )

    def test_stale_remote_claim_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: d.update(
                git_workflow={
                    **d["git_workflow"],
                    "merge_policy": "No remote PR is required " + d["git_workflow"]["merge_policy"],
                }
            )
        )

    def test_plan_json_mismatch_is_rejected(self) -> None:
        self.assert_invalid(mutate_plan=lambda p: p.replace("`P1-GOV01`", "`P1-GOV99`"))

    def test_title_mismatch_is_rejected(self) -> None:
        self.assert_invalid(
            mutate_plan=lambda p: p.replace(
                "Authorize Phase 1 and record execution readiness", "Wrong title", 1
            )
        )

    def test_gate_mapping_mismatch_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P1-PERF01")["gates"].append(
                "AR01-G4"
            )
        )

    def test_baseline_done_task_mutation_is_rejected(self) -> None:
        self.assert_invalid(
            lambda d: next(t for t in d["tasks"] if t["id"] == "P0-AR01").update(
                title="Mutated accepted architecture task"
            )
        )


if __name__ == "__main__":
    unittest.main()
