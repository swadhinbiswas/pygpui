FROM: Orchestrator
TO: Planner
TASK-ID: P0-REM08
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Directly close D11–D17 in current harness tooling and encode each attack as an authoritative acceptance gate on the owning Phase 1 tasks. Do not rely on an unencoded exception document.

WHAT I DID: Validated Red-Team's rejection, declined the bounded authorization as written, and authorized a final direct closure pass.

EVIDENCE: `.harness/REVIEWS/phase-0-remediation-red-team.md`; `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-REM03-1.md`; `evidence/P0-REM07/independent-verification.txt`; `.harness/PLANS/phase-0-remediation-round-4.md`; `.harness/TASKS.json`; `.harness/scripts/seed_session_registry.py`; `.harness/scripts/validate_phase1_graph.py`; baseline `b96625b`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No exception is accepted and no Phase 1 task has started.

OPEN RISKS & SURPRISES: This pass must fix actual current tooling where it exists and encode future-tool tests where it does not. A document-only change will be rejected again.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-remediation-round-4.md`, `.harness/REVIEWS/phase-0-remediation-red-team.md` and `evidence/P0-REM07/independent-verification.txt`; directly fix D11 through D17 in `.harness/scripts/seed_session_registry.py`, `.harness/scripts/validate_phase1_graph.py`, `.harness/TASKS.json`, `.harness/PLANS/phase-1-vertical-slice.md` and committed tests; regenerate `evidence/P0-REM08/validation.txt`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-red-team-P0-REM08-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-REM08-1.md`
3. `.harness/PLANS/phase-0-remediation-round-4.md`
4. `.harness/REVIEWS/phase-0-remediation-red-team.md`
5. `evidence/P0-REM07/independent-verification.txt`
6. `.harness/TASKS.json`
7. `.harness/scripts/validate_phase1_graph.py`

CONTEXT I WISH I HAD HAD: Concrete future tools and a real PR. Fix current validator/seed behavior now; encode exact adversarial tests for future tools so they cannot merge without closure.
