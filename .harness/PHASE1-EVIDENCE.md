# Phase 1 execution evidence

Status: Wave 0 authorized
Owner: Orchestrator
Approval baseline: `a433d68`
Approval evidence: `.harness/REVIEWS/phase-0-remediation-red-team-attempt-2.md`

## Authorized scope

Only Wave 0/1 foundational tooling is authorized:

1. `P1-GOV01` governance record.
2. `P1-SESSION-SEED01` trusted registry seed.
3. `P1-TOOL-BRANCH01` branch/merge/rollback tooling.
4. After branch tooling is independently verified and merged, the remaining independent gate/session/artifact/audit/platform/docs/release/benchmark tool tasks.

UI feature crates, Python API, renderer, window and wheel work remain blocked until their dependent foundational tools and contract gates are independently verified and merged.

## Remote and branch policy

- Remote: `https://github.com/swadhinbiswas/pygpui.git`
- Default branch: `main`, tracking `origin/main`
- GitHub CLI authenticated as `swadhinbiswas` with repository scope.
- Build agents use short-lived branches/worktrees and open PRs against `main`.
- No direct push or force-push to `main`; Integrator-only merges.
- Reviewer and Test-Engineer must be different sessions from the author.

## Readiness blockers

- Native Windows/macOS build hosts are unavailable.
- Physical Ubuntu/Windows/macOS GPU, IME and assistive-technology runners are unavailable.
- Benchmark collectors and certification hardware are not approved.
- CPython 3.11–3.15 clean environments are not all available.
- Project copyright holder notice, Wayland disposition and release credentials are unavailable.
- No real PR exists yet; PR-audit authenticity will be exercised when the first PR opens.

These blockers affect only their corresponding readiness/claim tasks. They do not block local foundational tool implementation.

## Escalation policy

- Maximum four attempts per task.
- Attempts 1–3 may address review feedback.
- At attempt 4, pass all gates or stop and escalate with evidence and a bounded decision request.
- No fifth attempt is authorized.
- Red main: pause unrelated merges, reproduce, fix or revert through reviewed PRs, rerun full gates and record the restored green hash.

## Current wave

Wave 0 (`P1-GOV01`) is being recorded. Wave 1 begins with `P1-SESSION-SEED01`, then `P1-TOOL-BRANCH01`.
