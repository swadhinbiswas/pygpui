FROM: Orchestrator
TO: Red-Team-Planner
TASK-ID: P0-REM03
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Verify only the proposed bounded exceptions for D11–D17. Decide whether each exception has an owning Phase 1 task, a hard expiry, conservative restrictions and an accepted residual risk sufficient to open `P0-AP01`. Do not reopen the entire plan.

WHAT I DID: Validated the final independent retest, classified D11–D17 as future-tool implementation acceptance tests, and proposed explicit bounded exceptions in `.harness/PLANS/phase-1-bounded-authorization.md`.

EVIDENCE: `evidence/P0-REM07/independent-verification.txt`; `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md`; `.harness/PLANS/phase-1-bounded-authorization.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; baseline `a5ec49b`.

WHAT I DID NOT DO / SKIPPED, AND WHY: `P0-AP01` is not approved yet. No Phase 1 task has started and no exception permits an unsupported claim or merge.

OPEN RISKS & SURPRISES: The exceptions are only safe if their owning tasks cannot be marked done/merged until the exact attacks fail. Red-Team should reject any exception that lacks a hard gate or could be silently bypassed.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-1-bounded-authorization.md`, `evidence/P0-REM07/independent-verification.txt`, `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md`, `.harness/PLANS/phase-1-vertical-slice.md` and `.harness/TASKS.json`; adjudicate each D11–D17 exception boundary and write `.harness/REVIEWS/phase-0-remediation-red-team.md` plus `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-REM03-1.md` with a final approve/reject recommendation.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-red-team-P0-REM03-1.md`
3. `.harness/PLANS/phase-1-bounded-authorization.md`
4. `evidence/P0-REM07/independent-verification.txt`
5. `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md`
6. `.harness/PLANS/phase-1-vertical-slice.md`
7. `.harness/TASKS.json`

CONTEXT I WISH I HAD HAD: Concrete future tool implementations and a real PR. The decision is about exception enforceability, not whether unimplemented tools already pass.
