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
| Bound source commit | `841fb384d08f7d598c2e0ab8242cfe0643bb5d14` |
| PR opened from commit | `bdf0e39d2d2f474ae273f0efb6728a150a188442` |
| Bound source tree | `a59b49f159b46204a5ffaf6c111b3b44f6fff9d8` |
| Branch artifact | `P1-TOOL-BRANCH01-branch` |
| Artifact SHA-256 | `5c8926a78f52b9f6b8df679ac66c62eee238ebb4dc03602abdd9b3fbe333e5cf` |
| Approved registry SHA-256 | `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498` |
| PR URL | https://github.com/swadhinbiswas/pygpui/pull/1 |

Changes are limited to `tools/ci/**`, `tools/session/verify_roles.py`, `tools/session/register_roles.py`, `evidence/P1-TOOL-BRANCH01/**`, and the Orchestrator-approved `.harness/sessions/registry.json` / `.harness/sessions/seed-approval.json` updates. No production `main` push, force-push, self-merge, harness-state edit, ADR edit, or UI feature edit was performed.

## Implemented controls

- `branch_gate.py` rejects absent reviewer/tester roles, role reuse, author self-review, wrong roles/tasks, commit/tree/artifact mismatch, stale evidence hashes, non-pass review/test decisions, and missing Integrator records for merged state.
- `verify_roles.py` validates the exact approved registry bytes, trusted seed approval, task-bound roles, distinct implementer/reviewer/tester sessions, and a distinct Integrator when assigned.
- `register_roles.py` appends task-bound implementer/reviewer/tester/Integrator records in one locked, all-or-nothing update; preserves every existing record and seed-history entry; refreshes the approval to the exact new registry bytes; and rejects duplicate/conflicting roles, session reuse, wrong task binding, untrusted approvers, non-append-only registries, and hash mismatches.
- `record_merge.py` creates append-only canonical records only after trusted pre-merge evidence and live `gh pr view` metadata agree on PR, branch, head commit, merge commit and merge into `main`. It supports both a build task's canonical `merge.json` and the authoritative `P1-INT01` Integrator-owned output. `verify` rechecks local bindings and, by default, GitHub metadata.
- `tag_point.py` creates annotated tags and rejects existing/moved tags or mismatched record identity.
- `red_main_drill.py` and `rollback_drill.py` accept only absent/empty absolute fixture paths under `/tmp/opencode`, use a fixture-local bare remote, snapshot production refs/remotes read-only, and fail if production state changes.
- `run_local_gate.py` runs Ruff format, Ruff lint, both test suites, and graph validation with exit codes `0`, `10`, `11`, `12`, `13`, or `69` for a missing Ruff dependency.

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
76 passed in 2.96s
```

Evidence: `pytest.txt`.

### Root harness suite

```text
$ python3 -m pytest -q
88 passed, 18 subtests passed in 12.66s
```

Evidence: `root-pytest.txt`.

### Full local gate

```text
$ PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
20 files already formatted
LOCAL_GATE_STEP=PASS step=fmt exit=0
All checks passed!
LOCAL_GATE_STEP=PASS step=lint exit=0
164 passed, 18 subtests passed in 20.02s
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
$ python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-fixture
RED_MAIN_DRILL=PASS fixture=/tmp/opencode/red-main-fixture red_main=af756be3e9fe6829bb0f096c8e499bea85cbbee3 restored_green=23714a509dfbfb4eb23c75e57092b52bdb08c518 production_unchanged=true
```

The fixture gate failed on red main (exit `1`) and passed after restoration (exit `0`). Fixture PRs are explicitly marked simulated. Durable copies: `fixtures/red-main/archive.json` and `fixtures/red-main/commands.txt`.

### Rollback

```text
$ python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-fixture --tag phase1/contracts-premerge
ROLLBACK_DRILL=PASS fixture=/tmp/opencode/rollback-fixture tag=phase1/contracts-premerge revert=6e3b368400efe5dc5619feb409503bb6e8af1f53 revert_of_revert=0c118437c9951539d809aa29558b0e7c8ef0828f restored_green=f1ba85f20fcbdc89fe4de29036ff6f86ca5148cc production_unchanged=true
```

Archived sequence:

1. Annotated tag at `010cea56b6c472470df4485fe4a980107b85e567`.
2. Simulated reviewed fixture merge `8c44013545f70d1b47c5345c8634279c1d1d3fad`; full fixture gate passed.
3. Injected failure `7fd55b3aaa81c59a425bb45cafa7532f0bcaf0b1`; gate failed.
4. Revert `6e3b368400efe5dc5619feb409503bb6e8af1f53`; gate passed.
5. Revert-of-revert `0c118437c9951539d809aa29558b0e7c8ef0828f`; gate failed as expected.
6. Simulated reviewed re-merge restored green at `f1ba85f20fcbdc89fe4de29036ff6f86ca5148cc`; full fixture gate passed.

The fixture full gate checks green state, baseline presence, `git diff --check`, and `git fsck --no-dangling`. Fixture PR/review records are simulations, not independent evidence. Durable copies: `fixtures/rollback/archive.json`, `fixtures/rollback/commands.txt`, and `fixtures/rollback/tag-record.json`.

### Production main integrity

Before and after both drills:

```text
$ git ls-remote origin refs/heads/main
15d29b32a066eeab7f4fdcc9b8a02456c4c0434f	refs/heads/main

$ git rev-parse origin/main
15d29b32a066eeab7f4fdcc9b8a02456c4c0434f
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

`session-roles.json` now says `status: assigned`. `branch-evidence.json` references the exact registry and role-assignment hashes but remains `state: implemented` with `independent_evidence: false`. No independent result was inferred from role registration.

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

Evidence: `seed-verify.txt`, `branch-gate-verify.txt`, `verify-roles.txt`, `branch-evidence-binding.txt`. `review.json`, `independent-test.json`, and `merge.json` remain deliberately absent.

### Exact independent-session verification commands

Independent sessions should first verify the approved registry and rerun the author controls on PR head `e2033cfd888c2f4cf3c92544a4d999c3245ef7da`:

```bash
python3 .harness/scripts/seed_session_registry.py --verify
python3 -m pytest tools/ci/tests
PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
python3 tools/ci/branch_gate.py --self-test
python3 tools/ci/record_merge.py --self-test
python3 tools/session/register_roles.py --self-test
python3 tools/session/verify_roles.py --self-test
python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-independent
python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-independent --tag phase1/contracts-premerge
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
2. Reviewer and tester must bind the same source commit/tree/artifact and write canonical `review.json` and `independent-test.json`; the author must not self-certify.
3. Integrator must merge the PR and run the canonical `record_merge.py` command. Merge-commit ancestry is required; squash merges are intentionally unsupported until a separate policy/evidence design exists.
4. Ruff is an external local dependency. The exact tested executable was outside the repository; a clean runner must install Ruff or set `PYGPUI_RUFF`.
5. The session trust root is the approved local registry/approval file pair, not a cryptographic signature. The later registry task owns stronger append-only infrastructure.
6. Fixture drills prove control flow and production-ref isolation, not independent human review or production CI readiness.
