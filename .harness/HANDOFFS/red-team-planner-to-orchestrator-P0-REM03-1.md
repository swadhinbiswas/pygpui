FROM: Red-Team-Planner
TO: Orchestrator
TASK-ID: P0-REM03
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Perform a narrow exception-boundary review of D11–D17 only; confirm each exception has an owning Phase 1 task, enforceable expiry/hard gate, blocked dependent claims, concrete restrictions and accepted residual risk; verify Wave 0/1 safety; and recommend whether `P0-AP01` may open.

WHAT I DID: Read the assigned State/handoff, bounded-authorization proposal, independent D11–D17 evidence, Test-Engineer handoff, Phase 1 plan and authoritative task graph. Compared `a5ec49b` with `b96625b` and confirmed the proposal changed no `P1-*` acceptance criterion, dependency, gate result, or validator requirement. Wrote `.harness/REVIEWS/phase-0-remediation-red-team.md` with a seven-row approve/reject matrix, systemic blocking finding REM-B01, Wave 0/1 assessment, and final recommendation.

EVIDENCE: `.harness/REVIEWS/phase-0-remediation-red-team.md`; `.harness/PLANS/phase-1-bounded-authorization.md`; `evidence/P0-REM07/independent-verification.txt`; `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/PROCESS.md`; baseline `b96625b6063092d146235b9ddb753725b792cfd1`.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not reopen unrelated plan areas or rerun the full graph audit. I did not edit the plan, TASKS.json, schema, validators, evidence, ADRs, STATE.md, PROCESS.md, or feature code, and I did not commit. Future tools do not exist, so this review assesses enforceability of their acceptance boundaries, not runtime behavior.

OPEN RISKS & SURPRISES: All seven owning tasks exist and the proposal states concrete restrictions/residual risks, but none of the exact attacks is encoded in the authoritative `P1-*` acceptance criteria. The proposal's line 31 claim that each exception is recorded in the owning task is false. As written, the seed trust root and downstream branch/gate/PR/artifact/release controls can be marked complete or merged without failing the listed attacks. Wave 1 is therefore not safe to authorize from this document alone.

EXACT NEXT STEP: Orchestrator: reject the current bounded authorization and keep `P0-AP01` blocked. Either add the exact D11–D17 adversarial commands and expected rejection/closure outcomes to the owning `P1-*` task acceptance criteria and validator tests, then dispatch a narrow `P0-REM03` attempt-2 re-review; or issue a revised implementation-only authorization that prohibits every affected task from reaching `done`/`merged` until an explicit independently verified closure record exists. Do not dispatch Wave 1 on the current proposal.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/REVIEWS/phase-0-remediation-red-team.md`
2. `.harness/PLANS/phase-1-bounded-authorization.md`
3. `.harness/TASKS.json`
4. `evidence/P0-REM07/independent-verification.txt`
5. `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM07-1.md`
6. `.harness/PLANS/phase-1-vertical-slice.md`
7. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Concrete future tool implementations and a real PR. The decision is about whether the exception boundaries are enforceable before those tools exist. Final result: 7 of 7 exception boundaries rejected; `P0-AP01` remains blocked.
