FROM: Orchestrator
TO: Planner
TASK-ID: P0-REM01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Perform an explicitly authorized, narrowly scoped remediation of RT3-B01 through RT3-B05 after the three-round planning cap. Update only the Phase 1 plan, task graph, gate schema and validators/tests. Do not edit accepted ADRs, research, reviews, `STATE.md` or feature code.

WHAT I DID: Validated Red-Team attempt 3, declined approval as-is, recorded a targeted remediation plan, reopened planning work as `P0-REM01`, and kept `P0-AP01` blocked behind independent remediation verification.

EVIDENCE: `.harness/REVIEWS/phase-0-plan-red-team-attempt-3.md`; `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-RT01-3.md`; `.harness/PLANS/phase-0-targeted-remediation.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; reviewed baseline `6e9637c`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No bounded exception was granted and no feature implementation was authorized. The final review found real execution blockers that must be closed rather than waived.

OPEN RISKS & SURPRISES: This is a targeted remediation, not a general fourth planning loop. Changes must stay limited to the five findings and must not expand scope or weaken ADR obligations.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-targeted-remediation.md` and `.harness/REVIEWS/phase-0-plan-red-team-attempt-3.md`; close RT3-B01 through RT3-B05 in `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/schemas/gate-results.schema.json`, `.harness/scripts/validate_phase1_graph.py` and its tests; regenerate `evidence/P0-REM01/validation.txt`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-test-engineer-P0-REM01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-REM01-1.md`
3. `.harness/PLANS/phase-0-targeted-remediation.md`
4. `.harness/REVIEWS/phase-0-plan-red-team-attempt-3.md`
5. `.harness/PLANS/phase-1-vertical-slice.md`
6. `.harness/TASKS.json`
7. `.harness/schemas/gate-results.schema.json`

CONTEXT I WISH I HAD HAD: Concrete implementations of the future gate/session/artifact tools are still blocked Phase 1 work. Remediation must specify exact commands, producers, schemas and negative tests without implementing UI feature code.

## Exact remediation requirements

- **RT3-B01:** Every staged aggregator validates schema and invokes aggregation; readiness approval evidence has a valid schema path and independent verification.
- **RT3-B02:** Encode merged-code dependencies/merge-record tasks; add pre-merge/session checks to RUSTCONTRACT01/CONREV01; make INT01 record and verify the actual merge SHA.
- **RT3-B03:** Stage AR09-G1/AR10-G3 from LIC01 evidence; add executable AR04-G6 MSRV-claim audit.
- **RT3-B04:** LIC02/LICENSE-CLOSE01 fetch/verify durable artifacts; validator detects all ignored-artifact consumers.
- **RT3-B05:** Remove Wayland/signing/channel claim dependencies from REL02; keep them only on corresponding claims/publication.
- Address RT3-N01/N02 where practical: rename readiness tasks, make owner-notice input explicit, and configure/document the hidden test suite entry point.
