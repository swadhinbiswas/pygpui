# Phase 0 remediation round 3 — residual closure

Status: Authorized
Owner: Orchestrator
Date: 2026-11-24
Baseline: `df8bfcf`
Input: `evidence/P0-REM05/independent-verification.txt`
Decision: Authorize `P0-REM06` to fix D7–D10, then `P0-REM07` independent retest and `P0-REM03` final Red-Team verification. No UI feature code is authorized.

## Defects to close

- **D7 — canonical identity binding:** validator must parse each `write_result.py` command and require `--task` and `--gate` to match the canonical `evidence/<task>/<gate>.json` output path.
- **D8 — trusted-registry bootstrap:** add an Orchestrator-controlled registry seed task before the first merged build; `P1-TOOL-BRANCH01` must depend on it. The later session-registry build extends the seeded registry.
- **D9 — real PR enforcement:** per-PR evidence must derive changed files and PR identity from an actual PR (`gh pr diff`/API), not a committed fixture or `--self-test`. Validator rejects fixture/self-test evidence producers.
- **D10 — ignored-dist normalization:** non-producer tasks may not reference any normalized or shell-expanded `dist/` path. Normalize `.` segments, braces and glob variants; producer tasks remain the only allowed `dist/` writers/consumers.

## Acceptance

- All D7–D10 attack cases fail against the revised graph/schema/validator.
- D1–D6 closures remain intact.
- Root pytest and graph/handoff validators pass with new committed regression tests.
- `P0-AP01` and every Phase 1 task remain blocked at attempt zero.
- No accepted ADR, research, review, `STATE.md`, `PROCESS.md` or feature code is edited.

## Rollback

Revert the round-3 commit as a unit if prior closures regress. Preserve independent evidence. This authorization expires after retest and final Red-Team verification.
