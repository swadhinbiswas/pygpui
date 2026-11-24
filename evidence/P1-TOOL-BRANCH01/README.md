# P1-TOOL-BRANCH01 — branch, merge and rollback tooling

Status: **partial** — implementation and author-run verification are complete; independent review/test and Integrator merge are intentionally pending.

## Identity

| Field | Value |
|---|---|
| Task | `P1-TOOL-BRANCH01` |
| Branch | `feat/P1-TOOL-BRANCH01-tooling` |
| Worktree | `/tmp/opencode/pygpui-P1-TOOL-BRANCH01` |
| Dispatch baseline | `15d29b32a066eeab7f4fdcc9b8a02456c4c0434f` |
| Initial implementation commit | `cebbb44c29336e0b74aa0acc75686c136bb8e10d` |
| Bound source commit | `031524fd65d14d5a5818e277ac1bfc28d6e0db5b` |
| PR opened from commit | `bdf0e39d2d2f474ae273f0efb6728a150a188442` |
| Bound source tree | `b6d70180cacfcaa8aa76a0e6d2a5aeae94cd7b6e` |
| Branch artifact | `P1-TOOL-BRANCH01-branch` |
| Artifact SHA-256 | `76d214d68d773084a3fa4e09422c2a19324beff9604d010b830d608aed514503` |
| Attempt-1 fail artifact | `attempt-1/independent-test.json` SHA-256 `cd60953cac91f9b667d6e58704241b457dc05226f72cb31b5e531fdbec03a3a4` |
| Approved registry SHA-256 | `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498` |
| PR URL | https://github.com/swadhinbiswas/pygpui/pull/1 |

Changes are limited to `tools/ci/**`, `tools/session/verify_roles.py`, `tools/session/register_roles.py`, `evidence/P1-TOOL-BRANCH01/**`, and the Orchestrator-approved `.harness/sessions/registry.json` / `.harness/sessions/seed-approval.json` updates. No production `main` push, force-push, self-merge, harness-state edit, ADR edit, or UI feature edit was performed.

## Attempt-2 T-01–T-05 remediation

Attempt-1 independent evidence remains unchanged at `attempt-1/independent-test.json` with `decision=fail` and SHA-256 `cd60953cac91f9b667d6e58704241b457dc05226f72cb31b5e531fdbec03a3a4`. Its adversarial script/log are archived byte-for-byte beside it. The canonical attempt-2 `independent-test.json` is absent.

The new negative tests failed before the fix (`19 failed, 29 passed`; `tests-first-attempt-2.txt`). After the fix, the same independent adversarial script passed all five probes:

```text
PASS named_branch_ref_must_exist_and_contain_source
PASS reviewer_role_must_have_explicit_task_binding
PASS review_record_tree_must_match_branch_artifact
PASS review_record_branch_must_match_branch_artifact
PASS configured_missing_ruff_must_return_dependency_exit_69: expected exit=69 actual exit=69
ADVERSARIAL_SUMMARY={"checks": [...], "failed": [], "passed": true}
```

Full output: `adversarial-checks-attempt-2.txt`.

- **T-01:** `refs/heads/<branch>` must exist and contain the reviewed source commit.
- **T-02:** every non-seed role must carry an explicit matching `task_id`.
- **T-03/T-04:** review, independent-test, and session-role records must carry the exact artifact `source_tree` and `branch`; fixture record producers now emit both.
- **T-05:** command execution `OSError`/`FileNotFoundError` becomes `GateError(dependency)` and CLI exit `69` with `LOCAL_GATE_REJECT`, not a traceback.

Registered roles and registry hash `bff3da2e...` were preserved without mutation.

## Implemented controls

- `branch_gate.py` rejects absent reviewer/tester roles, role reuse, author self-review, wrong roles/tasks, missing or non-containing named branch refs, commit/tree/artifact mismatch, missing/contradictory branch/tree fields on bound records, stale evidence hashes, non-pass review/test decisions, and missing Integrator records for merged state.
- `verify_roles.py` validates the exact approved registry bytes, trusted seed approval, explicit matching `task_id` on every non-seed role, distinct implementer/reviewer/tester sessions, and a distinct Integrator when assigned.
- `register_roles.py` appends task-bound implementer/reviewer/tester/Integrator records in one locked, all-or-nothing update; preserves every existing record and seed-history entry; refreshes the approval to the exact new registry bytes; and rejects duplicate/conflicting roles, session reuse, wrong task binding, untrusted approvers, non-append-only registries, and hash mismatches.
- `record_merge.py` creates append-only canonical records only after trusted pre-merge evidence and live `gh pr view` metadata agree on PR, branch, head commit, merge commit and merge into `main`. It supports both a build task's canonical `merge.json` and the authoritative `P1-INT01` Integrator-owned output. `verify` rechecks local bindings and, by default, GitHub metadata.
- `tag_point.py` creates annotated tags and rejects existing/moved tags or mismatched record identity.
- `red_main_drill.py` and `rollback_drill.py` accept only absent/empty absolute fixture paths under `/tmp/opencode`, use a fixture-local bare remote, snapshot production refs/remotes read-only, and fail if production state changes.
- `run_local_gate.py` runs Ruff format, Ruff lint, both test suites, and graph validation with exit codes `0`, `10`, `11`, `12`, `13`, or `69` for a missing/unexecutable Ruff dependency.

Canonical identity is enforced as task ID + canonical output path + record path. Commit/artifact binding uses the full source commit, Git tree, branch, task and canonical branch-evidence output. Review, test, session-role and merge records must repeat the same identity and exact file hashes. The post-change binding recheck passed; see `branch-evidence-binding.txt`.

## Exact author-run commands and output

Full output is preserved in the linked files.

### Tests-first

```text
$ python3 -m pytest tools/ci/tests
collected 0 items / 7 errors
ModuleNotFoundError: No module named 'tools.ci.common'
```

This intentional pre-implementation failure is preserved in `tests-first.txt`.

The targeted role-registration follow-up also began with a failing test:

```text
$ python3 -m pytest tools/ci/tests/test_register_roles.py
collected 0 items / 1 error
ModuleNotFoundError: No module named 'tools.session.register_roles'
```

Evidence: `tests-first-register-roles.txt`.

### Formatting and lint

Ruff `0.17.6` was installed outside the repository at `/tmp/opencode/uv-tools/ruff/bin/ruff`.

```text
$ /tmp/opencode/uv-tools/ruff/bin/ruff format --check tools
20 files already formatted

$ /tmp/opencode/uv-tools/ruff/bin/ruff check tools
All checks passed!
```

Evidence: `fmt.txt`, `lint.txt`.

### Task test suite

```text
$ python3 -m pytest tools/ci/tests
collected 76 items
95 passed in 3.65s
```

Evidence: `pytest.txt`.

### Root harness suite

```text
$ python3 -m pytest -q
88 passed, 18 subtests passed in 12.82s
```

Evidence: `root-pytest.txt`.

### Full local gate

```text
$ PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
20 files already formatted
LOCAL_GATE_STEP=PASS step=fmt exit=0
All checks passed!
LOCAL_GATE_STEP=PASS step=lint exit=0
183 passed, 18 subtests passed in 21.88s
LOCAL_GATE_STEP=PASS step=tests exit=0
JSON_PARSE=PASS
...
POSTMERGE_IDENTITY=PASS task+output+record
...
VALIDATION=PASS
LOCAL_GATE_STEP=PASS step=graph exit=0
LOCAL_GATE=PASS steps=fmt,lint,tests,graph
```

Evidence: `local-gate.txt`. Graph-only output is in `graph-validation.txt`.

### Tool self-tests

Every command exited zero.

```text
$ python3 tools/ci/branch_gate.py --self-test
BRANCH_GATE_SELF_TEST=PASS

$ python3 tools/ci/record_merge.py --self-test
RECORD_MERGE_SELF_TEST=PASS

$ python3 tools/ci/red_main_drill.py --self-test
RED_MAIN_DRILL_SELF_TEST=PASS

$ python3 tools/ci/rollback_drill.py --self-test
ROLLBACK_DRILL_SELF_TEST=PASS

$ python3 tools/ci/tag_point.py --self-test
TAG_POINT_SELF_TEST=PASS

$ python3 tools/ci/run_local_gate.py --self-test
LOCAL_GATE_SELF_TEST=PASS

$ python3 tools/session/verify_roles.py --self-test
SESSION_ROLES_SELF_TEST=PASS

$ python3 tools/session/register_roles.py --self-test
REGISTER_ROLES_SELF_TEST=PASS

$ python3 .harness/scripts/seed_session_registry.py --self-test
SESSION_SEED_SELF_TEST=PASS

$ python3 .harness/scripts/seed_session_registry.py --verify
SESSION_SEED_VERIFY=PASS
```

The local-gate self-test deliberately prints one expected `LOCAL_GATE=FAIL step=fmt exit=1 gate_exit=10` before its final PASS to prove fail-fast behavior. Individual outputs are in `*-self-test.txt` and `seed-verify.txt`.

## Disposable fixture drills

### Red main

```text
$ python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-attempt-2
RED_MAIN_DRILL=PASS fixture=/tmp/opencode/red-main-attempt-2 red_main=16e398557009d1bdbbba4b18fe279ea67d45ab3d restored_green=b2b23bfd30734a1d9fdec0e14d81c65842cb2c59 production_unchanged=true
```

The fixture gate failed on red main (exit `1`) and passed after restoration (exit `0`). Fixture PRs are explicitly marked simulated. Durable copies: `attempt-2/red-main/archive.json` and `attempt-2/red-main/commands.txt`.

### Rollback

```text
$ python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-attempt-2 --tag phase1/contracts-premerge
ROLLBACK_DRILL=PASS fixture=/tmp/opencode/rollback-attempt-2 tag=phase1/contracts-premerge revert=6725cac26edcaaccae42daf1d1c155584aab5f40 revert_of_revert=949cc035fd3dca36872f00b432e22f7ab830c202 restored_green=3db9beb3f26e5599a120a48b0b257d9c0729d75b production_unchanged=true
```

Archived sequence:

1. Annotated tag at `5f44faf8575fb6d8d75ab872c2904754bd8a85ed`.
2. Simulated reviewed fixture merge `969da8492b339e25fa0818b8a6d2175b357c7f17`; full fixture gate passed.
3. Injected failure `985d1b1e36073e1fc1837f7be1fe79305ef52848`; gate failed.
4. Revert `6725cac26edcaaccae42daf1d1c155584aab5f40`; gate passed.
5. Revert-of-revert `949cc035fd3dca36872f00b432e22f7ab830c202`; gate failed as expected.
6. Simulated reviewed re-merge restored green at `3db9beb3f26e5599a120a48b0b257d9c0729d75b`; full fixture gate passed.

The fixture full gate checks green state, baseline presence, `git diff --check`, and `git fsck --no-dangling`. Fixture PR/review records are simulations, not independent evidence. Durable copies: `attempt-2/rollback/archive.json`, `attempt-2/rollback/commands.txt`, and `attempt-2/rollback/tag-record.json`.

### Production main integrity

Before and after both drills:

```text
$ git ls-remote origin refs/heads/main
75fb21736be9d32055522ee2f0c403f32858b1ba	refs/heads/main

$ git rev-parse origin/main
75fb21736be9d32055522ee2f0c403f32858b1ba
```

Both fixture archives also contain identical production before/after snapshots, including `refs/remotes/origin/main`. Evidence: `production-main-after.txt`, `production-origin-main-after.txt`.

## Independent gates intentionally skipped

Orchestrator used `register_roles.py` to append the real task-bound roles. The registry approval now verifies at SHA-256 `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498`.

| Role | Session |
|---|---|
| Implementer | `ses_df2be4996ffek8O5wu7RwOeubn` |
| Reviewer | `ses_df27261c9ffcukQUulA8P0LN89` |
| Tester | `ses_df27261c9ffdiy0RA5Ko2oSdxl` |
| Integrator | `ses_df27261c8ffeJbVXcZMsund3Hf` |

`session-roles.json` says `status: assigned` and carries the exact branch, source commit/tree, artifact, registry, and role IDs. `branch-evidence.json` references its exact hash but remains `state: implemented` with `independent_evidence: false` and null review/test hashes for the new source. Attempt-1 fail evidence is archived unchanged; no independent pass was inferred from role registration or the author rerun.

```text
$ python3 .harness/scripts/seed_session_registry.py --verify
SESSION_SEED_VERIFY=PASS

$ python3 tools/ci/branch_gate.py verify --task P1-TOOL-BRANCH01 --state independently_verified --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
BRANCH_GATE_REJECT code=state message=branch evidence is not independently_verified
(exit 3)

$ python3 tools/session/verify_roles.py --task P1-TOOL-BRANCH01 --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
SESSION_ROLES_REJECT code=state message=branch evidence is not independently_verified
(exit 3)
```

Evidence: `seed-verify.txt`, `branch-gate-verify-attempt-2.txt`, `verify-roles-attempt-2.txt`, `branch-evidence-binding.txt`. `review.json`, `independent-test.json`, and `merge.json` remain deliberately absent.

### Exact independent-session verification commands

Independent sessions should first verify the approved registry and rerun the author controls against bound source `031524fd65d14d5a5818e277ac1bfc28d6e0db5b` on the final PR head recorded in the attempt-2 handoff:

```bash
python3 .harness/scripts/seed_session_registry.py --verify
python3 -m pytest tools/ci/tests
PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
python3 tools/ci/branch_gate.py --self-test
python3 tools/ci/record_merge.py --self-test
python3 tools/session/register_roles.py --self-test
python3 tools/session/verify_roles.py --self-test
python3 /tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial_checks.py
python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-attempt-2-independent
python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-attempt-2-independent --tag phase1/contracts-premerge
```

After the reviewer and tester have written canonical `review.json` and `independent-test.json`, and the branch evidence has been assembled with `state: independently_verified` plus their exact hashes, run:

```bash
python3 tools/ci/branch_gate.py verify --task P1-TOOL-BRANCH01 --state independently_verified --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
python3 tools/session/verify_roles.py --task P1-TOOL-BRANCH01 --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
```

Both commands must exit zero before Integrator merge. The author must not create the independent review/test records.

## D11–D17 relevant closure

- **D11:** the existing seed self-test/verify was rerun; the registered role append preserves seed history and its approval matches exact registry bytes (`bff3da2e...`). `register_roles.py` has duplicate/conflict/untrusted/non-append-only/hash-mismatch negatives.
- **D12:** CLI tools use single-valued argparse options; canonical task/output/record flags are validated again in code.
- **D13:** session roles are checked against the exact approved registry and task, not asserted by evidence alone.
- **D14:** merge recording requires live canonical `gh pr view` metadata; fixture PRs are never accepted as production PR evidence.
- **D15:** merge task/output/record identity is canonical, including the special Integrator-owned `P1-INT01` record path.
- **D16:** no release-artifact path is introduced by this task.
- **D17:** no ignored-`dist` path is introduced by this task.

## Residual risks and receiver actions

1. Distinct task-bound roles are registered and the approval hash verifies. Independent sessions must still run the exact commands above, write their own canonical evidence, and pass both independent gates before merge.
2. Reviewer and tester must bind source `031524fd65d14d5a5818e277ac1bfc28d6e0db5b`, tree `b6d70180cacfcaa8aa76a0e6d2a5aeae94cd7b6e`, artifact `76d214d68d773084a3fa4e09422c2a19324beff9604d010b830d608aed514503`, the named branch, and registry `bff3da2e...` in canonical `review.json` and `independent-test.json`; the author must not self-certify.
3. Integrator must merge the PR and run the canonical `record_merge.py` command. Merge-commit ancestry is required; squash merges are intentionally unsupported until a separate policy/evidence design exists.
4. Ruff is an external local dependency. The exact tested executable was outside the repository; a clean runner must install Ruff or set `PYGPUI_RUFF`.
5. The session trust root is the approved local registry/approval file pair, not a cryptographic signature. The later registry task owns stronger append-only infrastructure.
6. Fixture drills prove control flow and production-ref isolation, not independent human review or production CI readiness.
