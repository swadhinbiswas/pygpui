"""Independent P0-REM02 adversarial semantic tests.

These tests intentionally live outside the committed root testpaths.  A passing
DefectReproductionTests case means the unsafe condition is still reproducible;
it is not a claim that the condition is safe.  ValidatorBlindSpotTests mutate an
in-memory graph only and demonstrate accepted invalid graphs.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import shlex
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / ".harness/scripts/validate_phase1_graph.py"
SPEC = importlib.util.spec_from_file_location("p0_rem02_graph_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

DATA = json.loads((ROOT / ".harness/TASKS.json").read_text())
PLAN = (ROOT / ".harness/PLANS/phase-1-vertical-slice.md").read_text()
SCHEMA = json.loads((ROOT / ".harness/schemas/gate-results.schema.json").read_text())
BASELINE = VALIDATOR._load_baseline(ROOT, "5ce026d")
HISTORY = VALIDATOR._load_baseline(ROOT, "b9a8504")
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


def aggregate_command(task_id: str, gate: str) -> str:
    return next(
        criterion
        for criterion in task(task_id)["acceptance_criteria"]
        if f"tools/gates/aggregate.py --gate {gate} " in criterion
    )


def command_options(criterion: str) -> dict[str, str]:
    words = shlex.split(criterion.split(" exits zero", 1)[0])
    return {
        words[index]: words[index + 1]
        for index in range(len(words) - 1)
        if words[index].startswith("--")
    }


def validate_mutation(mutator) -> list[str]:
    changed = copy.deepcopy(DATA)
    mutator(changed)
    errors, _ = VALIDATOR.validate(changed, PLAN, BASELINE, ROOT, HISTORY)
    return errors


def approval_record(task_id: str, gate_id: str, stage: str) -> dict:
    return {
        "schema_version": 1,
        "gate_id": gate_id,
        "task_id": task_id,
        "stage": stage,
        "status": "pass",
        "evidence_type": "user-approval",
        "evidence": [
            {
                "path": f"evidence/{task_id}/gate-results.json",
                "sha256": "a" * 64,
            }
        ],
        "source_commit": "b" * 40,
        "lockfile_sha256": "c" * 64,
        "toolchain": "rustc 1.100.0",
        "reviewer_session_id": "reviewer-1",
        "tester_session_id": "tester-1",
        "approver_session_id": "approver-1",
        "aggregator": False,
    }


class TestRemediatedInvariantTests:
    def test_all_thirteen_staged_aggregators_have_schema_and_exact_model_inputs(self) -> None:
        assert len(STAGED) == 13
        for gate, model in STAGED.items():
            owner = task(model["aggregator"])
            criteria = owner["acceptance_criteria"]
            schema_commands = [
                criterion
                for criterion in criteria
                if "tools/gates/validate_result.py" in criterion
                and ".harness/schemas/gate-results.schema.json" in criterion
                and f"--result {owner['gate_evidence']}" in criterion
            ]
            assert schema_commands, gate
            options = command_options(aggregate_command(owner["id"], gate))
            assert options["--gate"] == gate
            assert options["--schema"] == ".harness/schemas/gate-results.schema.json"
            assert options["--output"] == owner["gate_evidence"]
            expected = {SUB_GATES[sub][1]["evidence"] for sub in model["required_sub_gates"]}
            assert set(options["--inputs"].split(",")) == expected, gate

    def test_user_approval_fixtures_are_schema_valid_and_required_fields_fail(self) -> None:
        jsonschema.Draft202012Validator.check_schema(SCHEMA)
        fixtures = [
            approval_record("P1-READY-CERT01", "AR08-G6.approval", "approval"),
            approval_record("P1-READY-CLAIM01", "AR09-G4.wayland-disposition", "wayland-disposition"),
        ]
        for fixture in fixtures:
            jsonschema.validate(fixture, SCHEMA)
            for field in ("evidence_type", "reviewer_session_id", "tester_session_id", "approver_session_id"):
                invalid = dict(fixture)
                invalid.pop(field)
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(invalid, SCHEMA)

    def test_approval_subgates_are_independent_verification_tasks(self) -> None:
        for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
            owner = task(task_id)
            assert owner["workflow"] == "verification"
            assert owner["completion_state"] == "independently_verified"
            assert owner["review_evidence"] and owner["test_evidence"]
            assert "tools/review/verify_proof.py" in owner["verification_command"]
            assert owner["sub_gates"][0]["evidence_type"] == "user-approval"

    def test_all_build_tasks_complete_merged_after_premerge_checks(self) -> None:
        builds = [owner for owner in PHASE1 if owner["workflow"] == "build"]
        assert len(builds) == 36
        for owner in builds:
            criteria = "\n".join(owner["acceptance_criteria"])
            assert owner["completion_state"] == "merged", owner["id"]
            assert owner["premerge_state"] == "independently_verified", owner["id"]
            assert owner["postmerge_state"] == "merged", owner["id"]
            assert owner["merge_owner_role"] == "Integrator", owner["id"]
            assert "tools/ci/branch_gate.py verify" in criteria, owner["id"]
            assert "--state independently_verified" in criteria, owner["id"]
            assert "tools/session/verify_roles.py" in criteria, owner["id"]
            assert "--state merged" not in criteria, owner["id"]

    def test_no_build_branches_directly_from_an_implementation_state(self) -> None:
        for owner in PHASE1:
            if owner["workflow"] != "build":
                continue
            assert not [
                dep for dep in owner["deps"]
                if task(dep)["workflow"] == "implementation"
            ], owner["id"]

    def test_rustcontract_and_conrev_have_branch_and_session_checks(self) -> None:
        for task_id in ("P1-RUSTCONTRACT01", "P1-CONREV01"):
            criteria = "\n".join(task(task_id)["acceptance_criteria"])
            assert f"branch_gate.py verify --task {task_id} --state independently_verified" in criteria
            assert f"verify_roles.py --task {task_id}" in criteria

    def test_int01_has_record_and_verify_commands(self) -> None:
        criteria = "\n".join(task("P1-INT01")["acceptance_criteria"])
        assert "branch_gate.py verify --task P1-SLICE01 --state independently_verified" in criteria
        assert "record_merge.py --task P1-SLICE01" in criteria
        assert "record_merge.py verify --task P1-SLICE01" in criteria

    def test_ar09_g1_and_ar10_g3_include_lic01_repository_subgates(self) -> None:
        for gate in ("AR09-G1", "AR10-G3"):
            model = DATA["gate_model"][gate]
            assert model["required_sub_gates"] == [f"{gate}.repository-evidence"]
            producer, sub = SUB_GATES[model["required_sub_gates"][0]]
            assert producer == "P1-LIC01"
            assert sub["evidence_type"] == "repository"
            assert "P1-LIC01" in task(model["aggregator"])["deps"]

    def test_ar04_g6_has_executable_msrv_audit(self) -> None:
        assert DATA["gate_model"]["AR04-G6"]["aggregator"] == "P1-REL02"
        criteria = "\n".join(task("P1-REL02")["acceptance_criteria"])
        assert "tools/release/audit_msrv_claim.py --metadata ." in criteria
        assert "only when no untested MSRV claim is present" in criteria

    def test_license_consumers_declare_store_and_fetch_verify(self) -> None:
        for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
            owner = task(task_id)
            consumed = owner["consumes_artifacts"][0]
            assert consumed["producer"] == "P1-REL01"
            assert consumed["store_task"] == "P1-ARTIFACT-STORE01"
            assert consumed["producer"] in owner["deps"]
            assert consumed["store_task"] in owner["deps"]
            criteria = "\n".join(owner["acceptance_criteria"])
            assert "gh release download" in criteria
            assert "tools/artifacts/store.py verify" in criteria

    def test_rel02_does_not_reach_wayland_or_claim_readiness(self) -> None:
        for forbidden in ("P1-WAYLAND-GATE01", "P1-READY-CLAIM01"):
            assert not VALIDATOR._reachable("P1-REL02", BY_ID, forbidden)
        criteria = "\n".join(task("P1-REL02")["acceptance_criteria"])
        assert "No upload, Developer ID/notarization, Authenticode, store or publishing command is run" in criteria

    def test_readiness_names_and_owner_notice_producer_match_scope(self) -> None:
        assert "P1-READY-BENCH01" not in BY_ID
        assert "P1-READY-RELEASE01" not in BY_ID
        assert task("P1-READY-BENCH-PROOF01")["title"] == "Record local benchmark proof prerequisites"
        assert task("P1-READY-RELEASE-BUILD01")["title"] == "Record wheel/sdist build prerequisites"
        notice = task("P1-OWNER-NOTICE01")
        assert any(
            VALIDATOR._matches("evidence/P1-OWNER-NOTICE01/validated-notice.json", path)
            for path in notice["produces"]
        )
        assert "P1-OWNER-NOTICE01" in task("P1-LICENSE-CLOSE01")["deps"]
        assert "evidence/P1-OWNER-NOTICE01/validated-notice.json" in "\n".join(
            task("P1-LICENSE-CLOSE01")["acceptance_criteria"]
        )

    def test_root_pytest_entrypoint_and_phase0_gate_are_preserved(self) -> None:
        assert "testpaths = .harness/scripts/tests" in (ROOT / "pytest.ini").read_text()
        assert task("P0-AP01")["status"] == "blocked"
        assert task("P0-AP01")["attempt_count"] == 0
        assert all(owner["status"] == "blocked" and owner["attempt_count"] == 0 for owner in PHASE1)


class TestDefectReproductionTests:
    def test_reproduces_eight_staged_aggregators_reading_and_writing_the_same_file(self) -> None:
        collisions = []
        for gate, model in STAGED.items():
            owner = task(model["aggregator"])
            options = command_options(aggregate_command(owner["id"], gate))
            if options["--output"] in options["--inputs"].split(","):
                collisions.append(gate)
        assert collisions == [
            "AR01-G1", "AR02-G1", "AR02-G2", "AR03-G1",
            "AR05-G2", "AR07-G3", "AR08-G1", "AR10-G1",
        ]

    def test_reproduces_multiple_gate_results_sharing_one_schema_object_file(self) -> None:
        affected = [
            owner["id"] for owner in PHASE1
            if len(owner.get("gates", [])) + len(owner.get("sub_gates", [])) > 1
        ]
        assert len(affected) == 16
        assert SCHEMA["type"] == "object"
        one = approval_record("P1-READY-CERT01", "AR08-G6.approval", "approval")
        two = approval_record("P1-READY-CLAIM01", "AR09-G4.wayland-disposition", "wayland-disposition")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate([one, two], SCHEMA)

    def test_reproduces_pr_audit_two_aggregates_writing_one_output(self) -> None:
        first = command_options(aggregate_command("P1-PR-AUDIT01", "AR09-G1"))
        second = command_options(aggregate_command("P1-PR-AUDIT01", "AR10-G3"))
        assert first["--output"] == second["--output"] == "evidence/P1-PR-AUDIT01/gate-results.json"

    def test_reproduces_schema_validation_before_aggregate_output_exists(self) -> None:
        for gate, model in STAGED.items():
            owner = task(model["aggregator"])
            criteria = owner["acceptance_criteria"]
            validate_index = next(
                index for index, criterion in enumerate(criteria)
                if "tools/gates/validate_result.py" in criterion
            )
            aggregate_index = criteria.index(aggregate_command(owner["id"], gate))
            assert validate_index < aggregate_index, gate
        for task_id in ("P1-CERT-GATE01", "P1-WAYLAND-GATE01"):
            criteria = task(task_id)["acceptance_criteria"]
            assert not any(
                f"--output {task(task_id)['gate_evidence']}" in criterion
                for criterion in criteria
                if "aggregate.py" not in criterion
            ), task_id

    def test_reproduces_unmerged_control_tasks_producing_code(self) -> None:
        for task_id in ("P1-SESSION-REGISTRY01", "P1-GATE-SCHEMA01"):
            owner = task(task_id)
            assert owner["workflow"] == "control"
            assert owner["completion_state"] == "recorded"
            assert any(path.startswith("tools/") for path in owner["produces"])
            assert not owner.get("merge_task")
            assert not owner.get("postmerge_command")

    def test_reproduces_int01_premerge_evidence_produced_only_by_implemented_slice(self) -> None:
        evidence = "evidence/P1-SLICE01/branch-evidence.json"
        producers = [
            owner["id"] for owner in PHASE1
            if any(VALIDATOR._matches(evidence, path) for path in owner.get("produces", []))
        ]
        assert producers == ["P1-SLICE01"]
        assert task("P1-SLICE01")["workflow"] == "implementation"
        assert task("P1-SLICE01")["completion_state"] == "implemented"
        for task_id in ("P1-TST01", "P1-REV01"):
            assert not any(evidence in criterion for criterion in task(task_id)["acceptance_criteria"]), task_id
        assert any(evidence in criterion for criterion in task("P1-INT01")["acceptance_criteria"])

    def test_reproduces_int01_verify_not_bound_to_observed_main_sha(self) -> None:
        criteria = "\n".join(task("P1-INT01")["acceptance_criteria"])
        assert "record_merge.py verify --task P1-SLICE01" in criteria
        assert "--expected-sha <merge-sha>" in criteria
        assert "git rev-parse" not in criteria
        assert "gh pr view" not in criteria

    def test_reproduces_repository_gates_without_enforcement_evidence(self) -> None:
        for gate in ("AR09-G1", "AR10-G3"):
            model = DATA["gate_model"][gate]
            assert all("enforcement" not in sub for sub in model["required_sub_gates"])
            options = command_options(aggregate_command("P1-PR-AUDIT01", gate))
            assert options["--inputs"] == "evidence/P1-LIC01/gate-results.json"
        criteria = task("P1-PR-AUDIT01")["acceptance_criteria"]
        enforcement = [criterion for criterion in criteria if "pr_audit_gate.py" in criterion]
        assert enforcement and all("--self-test" in criterion for criterion in enforcement)

    def test_reproduces_license_audits_before_fetch_and_against_unpopulated_dist(self) -> None:
        for task_id in ("P1-LIC02", "P1-LICENSE-CLOSE01"):
            criteria = task(task_id)["acceptance_criteria"]
            audit_index = next(
                index for index, criterion in enumerate(criteria)
                if "dist/release/**" in criterion
            )
            fetch_index = next(
                index for index, criterion in enumerate(criteria)
                if "gh release download" in criterion
            )
            fetch_options = command_options(criteria[fetch_index])
            assert audit_index < fetch_index, task_id
            assert fetch_options["--dir"] == f"evidence/{task_id}/downloads", task_id
            assert not any(
                "dist/release" in criterion and index > fetch_index
                for index, criterion in enumerate(criteria)
            ), task_id

    def test_reproduces_approver_session_not_bound_to_approval_artifact_or_registry(self) -> None:
        record = approval_record("P1-READY-CERT01", "AR08-G6.approval", "approval")
        record["approver_session_id"] = "forged-approver"
        jsonschema.validate(record, SCHEMA)
        for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
            criteria = task(task_id)["acceptance_criteria"]
            gate_commands = [criterion for criterion in criteria if "gate-results.json" in criterion]
            assert gate_commands and all("validate_result.py" in criterion for criterion in gate_commands)
            assert not any("approver_session_id" in criterion for criterion in criteria)
            assert not any(
                "gate-results.json" in criterion and "verify_proof.py" in criterion
                for criterion in criteria
            )

    def test_reproduces_approval_tasks_without_a_real_lockfile_producer(self) -> None:
        assert not (ROOT / "Cargo.lock").exists()
        for task_id in ("P1-READY-CERT01", "P1-READY-CLAIM01"):
            owner = task(task_id)
            assert not VALIDATOR._reachable(task_id, BY_ID, "P1-ARCH01")
            assert not any("Cargo.lock" in criterion for criterion in owner["acceptance_criteria"])
            assert "lockfile_sha256" in SCHEMA["required"]


class TestValidatorBlindSpotTests:
    def test_validator_accepts_aggregate_self_overwrite(self) -> None:
        def mutate(data):
            owner = next(item for item in data["tasks"] if item["id"] == "P1-CERT-GATE01")
            original = aggregate_command("P1-CERT-GATE01", "AR08-G6")
            changed = original.replace(
                "--inputs evidence/P1-READY-CERT01/gate-results.json,evidence/P1-PERF02/gate-results.json",
                "--inputs evidence/P1-CERT-GATE01/gate-results.json,evidence/P1-PERF02/gate-results.json",
            )
            owner["acceptance_criteria"][owner["acceptance_criteria"].index(original)] = changed

        assert validate_mutation(mutate) == []

    def test_validator_accepts_ignored_dist_consumer_with_wildcard_spelling(self) -> None:
        def mutate(data):
            owner = next(item for item in data["tasks"] if item["id"] == "P1-LIC02")
            owner.pop("consumes_artifacts")
            owner["acceptance_criteria"] = [
                criterion
                for criterion in owner["acceptance_criteria"]
                if "gh release download" not in criterion
                and "tools/artifacts/store.py verify" not in criterion
            ]
            owner["acceptance_criteria"] = [
                criterion.replace("dist/release/**", "dist/release/*.whl")
                for criterion in owner["acceptance_criteria"]
            ]

        assert validate_mutation(mutate) == []

    def test_validator_accepts_repository_gate_without_any_enforcement_command(self) -> None:
        def mutate(data):
            owner = next(item for item in data["tasks"] if item["id"] == "P1-PR-AUDIT01")
            owner["acceptance_criteria"] = [
                criterion
                for criterion in owner["acceptance_criteria"]
                if "test_pr_policy.py" not in criterion
                and "pr_audit_gate.py" not in criterion
            ]

        assert validate_mutation(mutate) == []

    def test_validator_accepts_control_code_producer_without_merge(self) -> None:
        def mutate(data):
            owner = next(item for item in data["tasks"] if item["id"] == "P1-GATE-SCHEMA01")
            owner["workflow"] = "control"
            owner["completion_state"] = "recorded"
            owner.pop("premerge_state", None)
            owner.pop("postmerge_command", None)

        assert validate_mutation(mutate) == []
