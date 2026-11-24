# Phase 0 remediation round 4 — direct D11–D17 closure

Status: Authorized
Owner: Orchestrator
Date: 2026-11-24
Baseline: `b96625b`
Inputs: `evidence/P0-REM07/independent-verification.txt`; `.harness/REVIEWS/phase-0-remediation-red-team.md`
Decision: Authorize `P0-REM08` to fix D11–D17 directly and encode their attacks as authoritative Phase 1 acceptance gates. No UI feature code is authorized.

## Required closure

- **D11:** seed self-test runs without extra required args; approval hash matches written registry bytes; rerun preserves append-only sessions; canonical registry output is validator-bound.
- **D12:** validator parses CLI arguments and rejects duplicate `--gate`, `--task`, `--result`, `--inputs`, `--output`.
- **D13:** validator binds approval artifact/registry/scope command values to the reviewed sub-gate declaration.
- **D14:** validator rejects discarded `gh` output and fabricated PR artifacts; real identity/diff outputs must feed enforcement.
- **D15:** validator binds post-merge command task/output and record path to the owning task.
- **D16:** validator binds artifact verify manifest and download directory; supports `--dir=` and rejects audit-path mismatch.
- **D17:** validator shell-unescapes and normalizes ignored `dist/` paths.

Encode corresponding adversarial acceptance tests in `P1-SESSION-SEED01`, `P1-GATE-SCHEMA01`, `P1-READY-CERT01`, `P1-READY-CLAIM01`, `P1-PR-AUDIT01`, `P1-TOOL-BRANCH01`, `P1-ARTIFACT-STORE01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` and `P1-TOOL-RELEASE01` so future implementations cannot regress.

## Acceptance

- All D11–D17 attack cases are rejected or closed.
- Root pytest, graph validator and handoff validator pass with new regression tests.
- `P0-AP01` and every Phase 1 task remain blocked at attempt zero.
- No ADR, research, review, `STATE.md`, `PROCESS.md` or feature code is edited.

## Rollback

Revert the round-4 commit as a unit if prior closures regress. This authorization expires after narrow Red-Team re-review.
