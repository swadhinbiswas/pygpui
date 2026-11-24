FROM: Orchestrator
TO: Release-CI-Engineer
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Implement the foundational branch-evidence, isolated red-main, tag, rollback, merge-record and session-role verification tools. Work on a short-lived feature branch, run tests first where possible, open a PR, and hand off for independent verification. Do not merge your own work.

WHAT I DID: Approved Phase 0 with zero blockers, completed governance and the hash-bound session seed, committed/pushed baseline `1da73bb`, and authorized this first Wave 1 build task.

EVIDENCE: `.harness/STATE.md`; `.harness/PHASE1-EVIDENCE.md`; `.harness/TASKS.json` task `P1-TOOL-BRANCH01`; `.harness/DECISIONS/0008-benchmark-certification-and-regression-gates.md`; `.harness/PROCESS.md`; `.harness/sessions/registry.json`; baseline `1da73bb`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No implementation exists yet. Reviewer/tester/Integrator sessions will be registered as those independent agents are spawned; do not fabricate roles or self-certify.

OPEN RISKS & SURPRISES: The first real PR will exercise the PR-audit path. Production `origin/main` must never be reddened or force-pushed. `branch_gate.py verify` may remain blocked until independent role evidence exists; that is expected at implementation handoff.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PHASE1-EVIDENCE.md`, `.harness/TASKS.json` task `P1-TOOL-BRANCH01`, `.harness/PROCESS.md` and `.harness/sessions/registry.json`; create worktree `/tmp/opencode/pygpui-P1-TOOL-BRANCH01` on branch `feat/P1-TOOL-BRANCH01-tooling` from current `main`, implement only the assigned `tools/ci/**` and `tools/session/verify_roles.py` scope with tests, run all self-tests and fixture drills, commit and push the branch, open a PR against `main`, write `evidence/P1-TOOL-BRANCH01/README.md`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-release-ci-P1-TOOL-BRANCH01-1.md`
3. `.harness/PHASE1-EVIDENCE.md`
4. `.harness/TASKS.json` task `P1-TOOL-BRANCH01`
5. `.harness/PROCESS.md`
6. `.harness/sessions/registry.json`
7. `.harness/PLANS/phase-1-vertical-slice.md`

CONTEXT I WISH I HAD HAD: Independent reviewer/tester session IDs and a real PR. Implement and self-test first; leave independent verification and merge to later sessions.

## Implementation requirements

- `tools/ci/branch_gate.py`: reject missing reviewer/tester, session reuse, commit mismatch and missing Integrator merge record.
- `tools/ci/run_local_gate.py`: run fmt/lint/tests/graph validation with clear exit codes.
- `tools/ci/red_main_drill.py`: use only a disposable fixture remote under `/tmp/opencode`; never mutate production `origin/main`.
- `tools/ci/rollback_drill.py` and `tag_point.py`: create/verify tags and rehearse revert → gate → revert-of-revert/restore with archived hashes.
- `tools/ci/record_merge.py`: require pre-merge evidence and Integrator role; bind task/output/record identity and merge SHA.
- `tools/session/verify_roles.py`: validate roles against the append-only registry; reject forged or mismatched sessions.
- Tests must include wrong-task/wrong-output/wrong-record and missing-role negative cases.
- Do not edit `.harness/TASKS.json`, `STATE.md`, accepted ADRs, research, reviews or UI feature code. Do not push directly to `main` or merge your own PR.
