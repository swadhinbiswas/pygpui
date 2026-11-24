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

## Git and integration

- The initial repository has no remote. Record this rather than fabricating PR URLs.
- Integrator merges only reviewed, green work in dependency order.
- Red main is top priority: pause unrelated work until fixed or reverted.

## Current process risks

- Concurrent agents may share `LOG.md`; appends must be one line and must not rewrite the file.
- Harness JSON is edited by the Orchestrator unless ownership is explicitly handed off.
- No benchmark hardware has been certified; all requested performance numbers are targets only.
