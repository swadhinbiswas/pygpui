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
| Bound source commit | `4b120d7460627ee18873cd1bc8882038eb22677c` |
| Bound source tree | `15dad9dd5bf8442c98251e8238c4b91bb959b550` |
| Branch artifact | `P1-TOOL-BRANCH01-branch` |
| Artifact SHA-256 | `505ca6e3add4f31e0fb90ba52eeaafa99850e93ef0e651269b5c67562b920657` |
| PR URL | Pending `gh pr create`; this line is updated before final handoff. |

Only `tools/ci/**`, `tools/session/verify_roles.py`, and `evidence/P1-TOOL-BRANCH01/**` were changed. No production `main` push, force-push, self-merge, harness-state edit, ADR edit, or UI feature edit was performed.

## Implemented controls

- `branch_gate.py` rejects absent reviewer/tester roles, role reuse, author self-review, wrong roles/tasks, commit/tree/artifact mismatch, stale evidence hashes, non-pass review/test decisions, and missing Integrator records for merged state.
- `verify_roles.py` validates the exact approved registry bytes, trusted seed approval, task-bound roles, distinct implementer/reviewer/tester sessions, and a distinct Integrator when assigned.
- `record_merge.py` creates append-only canonical records only after trusted pre-merge evidence and live `gh pr view` metadata agree on PR, branch, head commit, merge commit and merge into `main`. It supports both a build task's canonical `merge.json` and the authoritative `P1-INT01` Integrator-owned output. `verify` rechecks local bindings and, by default, GitHub metadata.
- `tag_point.py` creates annotated tags and rejects existing/moved tags or mismatched record identity.
- `red_main_drill.py` and `rollback_drill.py` accept only absent/empty absolute fixture paths under `/tmp/opencode`, use a fixture-local bare remote, snapshot production refs/remotes read-only, and fail if production state changes.
- `run_local_gate.py` runs Ruff format, Ruff lint, both test suites, and graph validation with exit codes `0`, `10`, `11`, `12`, `13`, or `69` for a missing Ruff dependency.

Canonical identity is enforced as task ID + canonical output path + record path. Commit/artifact binding uses the full source commit, Git tree, branch, task and canonical branch-evidence output. Review, test, session-role and merge records must repeat the same identity and exact file hashes.

## Exact author-run commands and output

Full output is preserved in the linked files.

### Tests-first

```text
$ python3 -m pytest tools/ci/tests
collected 0 items / 7 errors
ModuleNotFoundError: No module named 'tools.ci.common'
```

This intentional pre-implementation failure is preserved in `tests-first.txt`.

### Formatting and lint

Ruff `0.17.6` was installed outside the repository at `/tmp/opencode/uv-tools/ruff/bin/ruff`.

```text
$ /tmp/opencode/uv-tools/ruff/bin/ruff format --check tools
18 files already formatted

$ /tmp/opencode/uv-tools/ruff/bin/ruff check tools
All checks passed!
```

Evidence: `fmt.txt`, `lint.txt`.

### Task test suite

```text
$ python3 -m pytest tools/ci/tests
collected 60 items
60 passed in 2.54s
```

Evidence: `pytest.txt`.

### Root harness suite

```text
$ python3 -m pytest -q
88 passed, 18 subtests passed in 12.68s
```

Evidence: `root-pytest.txt`.

### Full local gate

```text
$ PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
18 files already formatted
LOCAL_GATE_STEP=PASS step=fmt exit=0
All checks passed!
LOCAL_GATE_STEP=PASS step=lint exit=0
148 passed, 18 subtests passed in 15.17s
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
RED_MAIN_DRILL=PASS fixture=/tmp/opencode/red-main-fixture red_main=cf4669c26aa48f2fe704e504194de2ffc5549ca9 restored_green=a4bcc15133a833f4b34bbcaf69a70d51fda7aa50 production_unchanged=true
```

The fixture gate failed on red main (exit `1`) and passed after restoration (exit `0`). Fixture PRs are explicitly marked simulated. Durable copies: `fixtures/red-main/archive.json` and `fixtures/red-main/commands.txt`.

### Rollback

```text
$ python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-fixture --tag phase1/contracts-premerge
ROLLBACK_DRILL=PASS fixture=/tmp/opencode/rollback-fixture tag=phase1/contracts-premerge revert=8405be01ef2d2b2f561fd61253876f32f95a445e revert_of_revert=194b9c18646678563853215618684918aa5c4c19 restored_green=42c88e5d637c16f230d0b78f46285c66fbbefe05 production_unchanged=true
```

Archived sequence:

1. Annotated tag at `6ebc96c9f5075c5fb2177ec0f1bf5a108f6a8b8c`.
2. Simulated reviewed fixture merge `b59b937269789b6b604989dc72a3cc7bc4ca4c01`; full fixture gate passed.
3. Injected failure `25eecc6d4d361ec12b2a373e3e11ecfabd6924ab`; gate failed.
4. Revert `8405be01ef2d2b2f561fd61253876f32f95a445e`; gate passed.
5. Revert-of-revert `194b9c18646678563853215618684918aa5c4c19`; gate failed as expected.
6. Simulated reviewed re-merge restored green at `42c88e5d637c16f230d0b78f46285c66fbbefe05`; full fixture gate passed.

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

The authoritative registry currently contains only the seed Orchestrator. No implementer, reviewer, tester, or Integrator session was invented. `branch-evidence.json` therefore says `state: implemented`, and `session-roles.json` says `status: pending` with null role IDs.

```text
$ python3 tools/ci/branch_gate.py verify --task P1-TOOL-BRANCH01 --state independently_verified --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
BRANCH_GATE_REJECT code=state message=branch evidence is not independently_verified
(exit 3)

$ python3 tools/session/verify_roles.py --task P1-TOOL-BRANCH01 --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
SESSION_ROLES_REJECT code=state message=branch evidence is not independently_verified
(exit 3)
```

Evidence: `branch-gate-verify.txt`, `verify-roles.txt`. `review.json`, `independent-test.json`, and `merge.json` are deliberately absent until independent sessions act.

## D11–D17 relevant closure

- **D11:** the existing seed self-test/verify was rerun; registry approval matches exact bytes (`186313d1...`).
- **D12:** CLI tools use single-valued argparse options; canonical task/output/record flags are validated again in code.
- **D13:** session roles are checked against the exact approved registry and task, not asserted by evidence alone.
- **D14:** merge recording requires live canonical `gh pr view` metadata; fixture PRs are never accepted as production PR evidence.
- **D15:** merge task/output/record identity is canonical, including the special Integrator-owned `P1-INT01` record path.
- **D16:** no release-artifact path is introduced by this task.
- **D17:** no ignored-`dist` path is introduced by this task.

## Residual risks and receiver actions

1. Orchestrator must append distinct task-bound implementer/reviewer/tester/Integrator sessions and refresh the seed approval hash. Until then independent gates remain blocked by design.
2. Reviewer and tester must bind the same source commit/tree/artifact and write canonical `review.json` and `independent-test.json`; the author must not self-certify.
3. Integrator must merge the PR and run the canonical `record_merge.py` command. Merge-commit ancestry is required; squash merges are intentionally unsupported until a separate policy/evidence design exists.
4. Ruff is an external local dependency. The exact tested executable was outside the repository; a clean runner must install Ruff or set `PYGPUI_RUFF`.
5. The session trust root is the approved local registry/approval file pair, not a cryptographic signature. The later registry task owns stronger append-only infrastructure.
6. Fixture drills prove control flow and production-ref isolation, not independent human review or production CI readiness.
