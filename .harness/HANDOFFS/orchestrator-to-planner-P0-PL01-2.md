FROM: Orchestrator
TO: Planner
TASK-ID: P0-PL01
ATTEMPT #: 2
STATUS: partial

WHAT I WAS ASKED: Revise the Phase 1 plan and task graph to resolve every blocking Red-Team finding B-01 through B-11, without editing accepted ADRs or starting feature implementation. Produce an execution-ready graph with owned tooling, internal contracts, packaging, review/merge semantics, fail-closed evidence and artifact invalidation rules.

WHAT I DID: Validated and accepted Red-Team attempt 1 as changes requested. Kept `P0-AP01` blocked, reopened `P0-PL01` at attempt 2, and prepared this revision handoff.

EVIDENCE: `.harness/REVIEWS/phase-0-plan-red-team.md`; `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-RT01-1.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; reviewed baseline `81f794d`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No plan revision has been made yet. Accepted ADRs are immutable and no feature task may start before the gate passes.

OPEN RISKS & SURPRISES: The graph is acyclic and maps all 52 ADR gate IDs, but identifier coverage hid missing producers, false parallelism, a wheel-ordering cycle, a done/merge deadlock and acceptance criteria that could pass without evidence.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `.harness/REVIEWS/phase-0-plan-red-team.md`; resolve B-01 through B-11 in `.harness/PLANS/phase-1-vertical-slice.md` and `.harness/TASKS.json`, add missing owned tooling/internal-contract/packaging/review/evidence tasks and dependencies, regenerate reproducible validation evidence, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-red-team-P0-RT01-2.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-PL01-2.md`
3. `.harness/REVIEWS/phase-0-plan-red-team.md`
4. `.harness/PLANS/phase-1-vertical-slice.md`
5. `.harness/TASKS.json`
6. `.harness/DECISIONS/README.md`
7. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Distinct reviewer/Test-Engineer identities, physical platform/IME/AT runners, benchmark collectors, CPython 3.11–3.15 environments, copyright notice, Wayland disposition and release credentials. Represent missing inputs as explicit blocked preconditions, not hidden estimates.

## Required revision coverage

- **B-01:** Own and negatively test every gate script; commit the actual graph validator and regenerate reproducible evidence.
- **B-02:** Add an internal Rust contract/freeze task for text, paint, hit/focus, platform and instrumentation hand-offs; repair producer dependencies.
- **B-03:** Add root Python packaging, locked dev environment and a local wheel task before installed-wheel tests.
- **B-04:** Define implemented/verified/merged states and per-branch independent review/test/Integrator evidence; resolve the Counter PR deadlock.
- **B-05:** Move red-main/rollback drills to an isolated remote/fixture; assign tooling, tag creation and exact revert/restore steps.
- **B-06:** Assign production instrumentation hooks and every benchmark subcommand with negative tests.
- **B-07:** Repair wave-1 ordering and AccessKit manifest/lifecycle ownership.
- **B-08:** Replace narrative audits with exact commands, inputs, artifacts and nonzero fail-closed outcomes.
- **B-09:** Restore executable AR06-G5, AR07-G4, AR08-G3/G5, AR09-G1, AR10-G1 and AR10-G3 semantics.
- **B-10:** Add IME→AT ordering and split accessible-list implementation from physical AT certification.
- **B-11:** Add final documentation/claim closure and artifact-hash invalidation/re-audit edges.

Also address N-01 through N-04 where practical. Keep `P0-AP01` and all Phase 1 tasks blocked until Orchestrator approval. Do not edit ADRs, research, reviews, `STATE.md` or feature code; do not commit.
