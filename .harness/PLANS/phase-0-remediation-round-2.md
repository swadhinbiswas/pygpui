# Phase 0 remediation round 2 — independent defect closure

Status: Authorized
Owner: Orchestrator
Date: 2026-11-24
Baseline: `7240d9b`
Input: `evidence/P0-REM02/independent-verification.txt`
Decision: Authorize `P0-REM04` to fix D1–D6, then `P0-REM05` independent retest and `P0-REM03` final Red-Team verification. No UI feature code is authorized.

## Defects to close

- **D1 — gate-result lifecycle:** use unique result files or a multi-result schema; no aggregator may read and write the same file; PR-AUDIT01 must emit distinct AR09-G1/AR10-G3 outputs; validate aggregate outputs after creation.
- **D2 — code-producing control tasks:** `P1-SESSION-REGISTRY01` and `P1-GATE-SCHEMA01` become merged build tasks with independent pre-merge review/test and Integrator merge records.
- **D3 — repository gate enforcement:** AR09-G1/AR10-G3 stage and aggregate both LIC01 repository evidence and real per-PR provenance/authored-scope enforcement evidence.
- **D4 — artifact audit ordering/path:** LIC02/LICENSE-CLOSE01 fetch and verify durable artifacts first, then audit the downloaded files; remove audits against unpopulated ignored `dist/release`.
- **D5 — ignored-artifact detection:** validator normalizes and detects all `dist/release`/`dist/local` path and glob spellings, including `*.whl`.
- **D6 — approval evidence binding:** user-approval records bind approver identity to an approval artifact and trusted registry; pre-lockfile approvals use an explicit not-applicable lockfile state rather than a fabricated hash.

## Acceptance

- All six independent defect reproductions fail against the revised plan/schema/validator.
- Existing 41 tests plus 15 subtests still pass, with new committed regression tests.
- Graph/handoff validators pass and `P0-AP01` remains blocked.
- No accepted ADR, research, review, `STATE.md`, `PROCESS.md` or feature code is edited.

## Rollback

Revert the remediation commit as a unit if it regresses prior closures. Preserve the independent Test-Engineer evidence and accepted ADRs. This authorization expires after remediation retest and final Red-Team verification.
