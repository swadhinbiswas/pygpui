FROM: Orchestrator
TO: Planner
TASK-ID: P0-PL01
ATTEMPT #: 3
STATUS: partial

WHAT I WAS ASKED: Perform the final planned Phase 1 revision, resolving RT2-B01 through RT2-B07 without editing accepted ADRs or starting feature implementation. Produce a semantically executable graph with staged/atomic gate closure, durable artifacts, independent pre/post-merge evidence, legal crate-test boundaries, correct rollback timing and separated readiness approvals.

WHAT I DID: Validated Red-Team attempt 2, kept `P0-AP01` blocked, reopened Planner at attempt 3, and prepared this final-round handoff.

EVIDENCE: `.harness/REVIEWS/phase-0-plan-red-team-attempt-2.md`; `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-RT01-2.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/scripts/validate_phase1_graph.py`; `evidence/P0-RT01/gate-level-precheck.txt`; reviewed baseline `c5ca6d1`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No plan revision or implementation has occurred. The three-round planning cap is nearly reached; this round must resolve the semantic issues rather than add scope.

OPEN RISKS & SURPRISES: Structural validation cannot detect semantic deadlocks, ignored artifact handoffs, circular merge evidence, illegal test-only crate dependencies, mistimed rollback tags or conflated readiness approvals.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `.harness/REVIEWS/phase-0-plan-red-team-attempt-2.md`; resolve RT2-B01 through RT2-B07 in `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/scripts/validate_phase1_graph.py` and its tests; regenerate `evidence/P0-PL01/validation-attempt-3.txt`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-red-team-P0-RT01-3.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-PL01-3.md`
3. `.harness/REVIEWS/phase-0-plan-red-team-attempt-2.md`
4. `.harness/PLANS/phase-1-vertical-slice.md`
5. `.harness/TASKS.json`
6. `.harness/scripts/validate_phase1_graph.py`
7. `.harness/scripts/tests/test_validate_phase1_graph.py`

CONTEXT I WISH I HAD HAD: A durable artifact store, trusted session registry, native Windows/macOS build hosts, physical runners, benchmark collectors and user approvals. Encode missing infrastructure as explicit blocked preconditions; do not hide it in estimates.

## Required revision coverage

- **RT2-B01:** Choose staged sub-gates with final aggregators or atomic final mappings. Add a `gate-results.json` schema, task-stage fields and semantic validator tests that reject all 14 deadlocks and the AR03-G5 ambiguity.
- **RT2-B02:** Add immutable durable wheel storage/fetch/verify, source-commit/lockfile/toolchain binding and invalidation on source change. Do not rely on ignored `dist/` as shared state.
- **RT2-B03:** Split pre-merge independent verification from post-merge Integrator recording. Every proof/verification task needs distinct reviewer/tester evidence and a trusted session-role record; no self-certification.
- **RT2-B04:** Move cross-crate contract compile tests to a neutral integration/contract-test target outside `pygpui-core`; update architecture checks for the explicit test-only edge.
- **RT2-B05:** Create and verify the pre-contract tag before PROTO01 merges; prove the tagged tree lacks the contract.
- **RT2-B06:** Add native Windows/macOS/Linux build-lane readiness before candidate wheel builds.
- **RT2-B07:** Split build/proof readiness from OQ-02 certification, Wayland distribution and signing/publication approvals. Candidate builds and callback/baseline work must not wait for unrelated claim credentials.

Also address RT2-N01 through RT2-N04 where practical. Keep `P0-AP01` and all Phase 1 tasks blocked. Do not edit ADRs, research, reviews, `STATE.md` or feature code; do not commit.
