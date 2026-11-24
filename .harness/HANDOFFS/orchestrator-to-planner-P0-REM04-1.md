FROM: Orchestrator
TO: Planner
TASK-ID: P0-REM04
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Fix the six independent remediation defects D1–D6 without expanding scope or weakening ADRs. Update only the Phase 1 plan, task graph, gate schema, validators and tests; preserve all prior closures and keep feature implementation blocked.

WHAT I DID: Validated the independent Test-Engineer report, declined remediation acceptance, authorized round 2, and reopened targeted Planner work as `P0-REM04`.

EVIDENCE: `evidence/P0-REM02/independent-verification.txt`; `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM02-1.md`; `.harness/PLANS/phase-0-remediation-round-2.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; `.harness/scripts/validate_phase1_graph.py`; baseline `7240d9b`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No defect is accepted as closed and no UI feature code is authorized. Structural validator success is insufficient while independent reproductions confirm unsafe conditions.

OPEN RISKS & SURPRISES: Gate evidence file lifecycle and early approval binding are subtle; fixes must be executable as sequential shell commands, not merely schema-valid in isolation.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-remediation-round-2.md` and `evidence/P0-REM02/independent-verification.txt`; fix D1 through D6 in `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/schemas/gate-results.schema.json`, `.harness/scripts/validate_phase1_graph.py` and its tests; regenerate `evidence/P0-REM04/validation.txt`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-test-engineer-P0-REM04-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-REM04-1.md`
3. `.harness/PLANS/phase-0-remediation-round-2.md`
4. `evidence/P0-REM02/independent-verification.txt`
5. `.harness/PLANS/phase-1-vertical-slice.md`
6. `.harness/TASKS.json`
7. `.harness/schemas/gate-results.schema.json`

CONTEXT I WISH I HAD HAD: Concrete future tool implementations and a real early-approval artifact format. Specify exact file layouts and command ordering so an independent executor can run them without inference.

## Required fixes

- **D1:** Unique result file per gate/sub-gate or a true multi-result schema; no aggregate self-overwrite; distinct PR-AUDIT outputs; output schema validation after aggregate creation.
- **D2:** Session-registry and gate-schema producers become merged build tasks with pre-merge review/test and Integrator merge records.
- **D3:** AR09-G1/AR10-G3 aggregate repository and per-PR enforcement sub-gates with real enforcement commands.
- **D4:** Fetch/verify durable artifacts before audit; audit the downloaded path; remove unpopulated `dist/release` audits.
- **D5:** Validator detects all ignored artifact path/glob variants under `dist/release` and `dist/local`.
- **D6:** Bind approval records to approver session and approval artifact; represent pre-lockfile approval without a fabricated lockfile hash.
