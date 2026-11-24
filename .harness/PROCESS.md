# pygpui Working Process

This file is the harness operating contract. It may be updated after retrospectives; accepted ADRs may only be superseded, never edited in place.

## Authority and state

- `STATE.md` is the current orchestration view; `TASKS.json` is the task graph.
- Files, not chat memory, are authoritative. Write results before ending a run.
- Read `STATE.md` and the assigned handoff before acting.
- Never edit another agent's in-flight files. Use `HANDOFFS/` for transfer.
- Orchestrator decomposes, dispatches, verifies and decides; specialist agents perform research, design and implementation.

## Evidence labels

Every decision-driving research claim must be one of:

- **verified** — supported by a dated primary source or reproducible local observation;
- **plausible** — supported indirectly or by secondary evidence, but not established;
- **unverified** — assumption, estimate, stale evidence or unsupported assertion.

Unverified claims cannot silently drive an ADR. Plausible claims require an explicit risk and a validation task.

## Research loop

- Per question, dispatch two or three researchers with different angles.
- Research is capped at three rounds. Stop when the decision would not change.
- Skeptic runs after each combined batch and attempts to falsify findings.
- Record unresolved uncertainty and choose the conservative option at the cap.

## Build and review loop

- Implementation begins only after Phase 0 approval.
- Each build task uses its own local branch/worktree. A remote PR is opened only when a destination is configured.
- Build agent runs build, lint and unit tests before handoff.
- A different Test-Engineer and Reviewer verify the work.
- Blocking review findings return to the build agent with the review attached.
- Maximum four attempts per task, then escalate to Orchestrator.

## Performance loop

- Hot-path merges trigger criterion/pytest-benchmark comparison against `BENCH/baseline`.
- A regression greater than 10% or target miss requires profiling and a written diagnosis.
- Targets remain unverified until a reproducible benchmark passes on a disclosed environment.

## Handoffs and logs

Use `HANDOFFS/<from>-to-<to>-<task-id>-<attempt>.md` and the exact Part 3 fields. The receiver's first `LOG.md` action line must quote the handoff's exact next step. Append one concise line per agent action to `LOG.md`; never rewrite prior entries.

## Build-agent PR workflow

1. Create a short-lived branch/worktree named `feat/<task-id>-<slug>` or `fix/<task-id>-<slug>` from current green `main`.
2. Read `STATE.md` and the assigned handoff before editing; quote the exact next step in the first `LOG.md` line.
3. Write failing tests first where behavior changes. Keep the branch scoped to the assigned files/interfaces.
4. Run the task's build, lint and test commands; record exact outputs in the handoff. A clean result is required before review.
5. Commit with a Conventional Commit message, push the branch, and open a PR against `main` with `gh pr create`. Link the task, ADR gates, tests, benchmark evidence and rollback.
6. Never push directly to `main`, force-push a shared branch, or merge your own unreviewed work. A different Reviewer and Test-Engineer must verify the change.
7. Integrator merges in dependency order, reruns the full matrix and benchmarks, and reverts immediately if `main` becomes red.

## Git and integration

- `origin` is `https://github.com/swadhinbiswas/pygpui.git`; `main` tracks `origin/main`. The initial remote was empty and received the harness/ADR baseline without force.
- Build agents use short-lived branches/worktrees and open PRs against `main`. Never force-push or rewrite published history.
- `main` is currently unprotected on GitHub. Until stable CI check names exist, the Integrator enforces reviewed/green merges through the harness; branch protection is deferred under OQ-15.
- Integrator merges only reviewed, green work in dependency order.
- Red main is top priority: pause unrelated work until fixed or reverted.

## Current process risks

- Concurrent agents may share `LOG.md`; appends must be one line and must not rewrite the file.
- Harness JSON is edited by the Orchestrator unless ownership is explicitly handed off.
- No benchmark hardware has been certified; all requested performance numbers are targets only.
