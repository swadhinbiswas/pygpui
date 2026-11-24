FROM: Orchestrator
TO: Planner
TASK-ID: P0-REM06
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Fix residuals D7–D10 without expanding scope or weakening prior closures. Update only the Phase 1 plan, task graph, schema, validators and tests; keep feature implementation blocked.

WHAT I DID: Validated the fresh independent retest, declined remediation acceptance, authorized round 3, and reopened targeted Planner work as `P0-REM06`.

EVIDENCE: `evidence/P0-REM05/independent-verification.txt`; `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM05-1.md`; `.harness/PLANS/phase-0-remediation-round-3.md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; `.harness/scripts/validate_phase1_graph.py`; baseline `df8bfcf`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No residual is accepted as closed and no UI feature code is authorized.

OPEN RISKS & SURPRISES: Bootstrap trust and real-PR evidence must be concrete, not circular or fixture-based.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-remediation-round-3.md` and `evidence/P0-REM05/independent-verification.txt`; fix D7 through D10 in `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/schemas/gate-results.schema.json`, `.harness/scripts/validate_phase1_graph.py` and its tests; regenerate `evidence/P0-REM06/validation.txt`, append one action line to `LOG.md`, and write `.harness/HANDOFFS/planner-to-test-engineer-P0-REM06-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-REM06-1.md`
3. `.harness/PLANS/phase-0-remediation-round-3.md`
4. `evidence/P0-REM05/independent-verification.txt`
5. `.harness/PLANS/phase-1-vertical-slice.md`
6. `.harness/TASKS.json`
7. `.harness/scripts/validate_phase1_graph.py`

CONTEXT I WISH I HAD HAD: An initialized trusted root registry and a real PR changed-file feed. Specify exact bootstrap and PR commands so execution does not depend on inference.

## Required fixes

- **D7:** Parse `write_result.py --task/--gate/--output`; enforce canonical `evidence/<task>/<gate>.json` identity.
- **D8:** Add an Orchestrator-controlled registry seed before the first merged build; make `P1-TOOL-BRANCH01` depend on it.
- **D9:** Derive per-PR changed files/identity from `gh pr diff`/API; reject committed fixtures and `--self-test` as enforcement evidence.
- **D10:** Normalize path segments/braces/globs; non-producers may not reference any `dist/` path; only declared producers may write/consume ignored build output.
