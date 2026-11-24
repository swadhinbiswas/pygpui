# pygpui Harness State

Last updated: 2026-11-24
Owner: Orchestrator
Phase: 0 — Discovery & Decisions
Active loop: Loop A — Research
Repository status: Empty workspace bootstrapped on Git `main`; no feature code exists. Local toolchain observed: Python 3.14.10, rustc 1.100.0, cargo 1.100.0.

## Current objective

Resolve the architecture-driving unknowns for a Python-first, Rust-rendered UI framework using evidence, not assertions. Produce verified research, adversarial review, accepted ADRs, and a machine-checkable Phase 1 task graph before implementation starts.

## Completed

- Inspected `/home/swadhin/pygpui`: no files and no existing Git repository.
- Loaded planning/specification guidance.
- Created the file-backed harness contract and Phase 0 task graph.
- Defined four independent research questions and assigned two researchers per question.

## Active work

- RQ-01: prior-art architecture and clean-room boundaries.
- RQ-02: Rust/Python dependency, version, license, and maintenance selection.
- RQ-03: FFI/render-loop performance model and reproducible benchmark design.
- RQ-04: platform windowing/input/IME/accessibility/HiDPI and abi3 distribution constraints.

All eight researchers are Round 1 and may run concurrently. Their permitted writes are their assigned `RESEARCH/` file, an append-only action line in `LOG.md`, and their own handoff.

## Blocked

- Skeptic review waits for all eight Round 1 research files.
- Architecture and planning wait for Skeptic disposition.
- No Git remote is configured, so remote PR creation is unavailable. Research is confined to harness files; later build tasks will use local branches/worktrees until a remote is supplied.

## Next 3 actions

1. Collect and validate all eight Round 1 research handoffs; dispatch targeted Round 2 only for decision-driving claims marked plausible or unverified.
2. Dispatch Skeptic to falsify the combined findings, check source freshness, and issue a claim-by-claim disposition.
3. Dispatch Architect to draft ADRs from verified findings, then Planner and Red-Team-Planner to produce and challenge the Phase 1 task graph.

## Phase 0 exit gate

- Every decision-driving claim is verified, or the three-round cap is reached and uncertainty is recorded in `OPEN_QUESTIONS.md` with a conservative choice.
- Skeptic report contains no unresolved blocking issue.
- Architect-owned ADRs are accepted and immutable.
- Phase 1 `TASKS.json` has explicit dependencies and machine-checkable acceptance criteria.
- Red-Team-Planner reports no blocking issue, or Orchestrator records an explicit bounded exception.
- No implementation task has started before this gate.

## Performance truth policy

The requested numbers are targets, not facts: 120 fps with 1,000 elements; 120 fps for a 10,000-row virtualized list; input-to-frame p95 below 8 ms; idle CPU near zero; no Python callbacks per frame. Each must later be measured by a reproducible benchmark on a disclosed hardware/software stack. Until then, all are unverified.
