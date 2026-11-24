# pygpui Harness State

Last updated: 2026-11-24
Owner: Orchestrator
Phase: 0 — Discovery & Decisions
Active loop: Loop B — ADRs and Plan
Repository status: Git `main` tracks `origin` at `https://github.com/swadhinbiswas/pygpui.git`; architecture baseline `5ce026d` is pushed. No feature code exists. Local toolchain observed: Python 3.14.10, rustc 1.100.0, cargo 1.100.0.

## Current objective

Resolve the architecture-driving unknowns for a Python-first, Rust-rendered UI framework using evidence, not assertions. Produce verified research, adversarial review, accepted ADRs, and a machine-checkable Phase 1 task graph before implementation starts.

## Completed

- Inspected `/home/swadhin/pygpui`: no files and no existing Git repository.
- Loaded planning/specification guidance.
- Created the file-backed harness contract and Phase 0 task graph.
- Committed the initial harness baseline as `6589bd0`.
- Validated all 14 task IDs, dependency edges and acceptance-criteria lists.
- Defined four independent research questions and assigned two researchers per question.
- Validated and accepted P0-R01A after the author corrected its handoff status; evidence is pinned to Zed commit `168964ea32451900149b5c15ccb2d515e4ecb936`.
- Validated and accepted P0-R04B: IME/focus/accessibility ownership, wheel/CI constraints and credential-blocked release operations are documented with claim-level evidence.
- Validated and accepted P0-R02B: exact PyO3/maturin candidates, abi3/GIL boundaries, reviewed strict stubs and no-default-async policy are documented with claim-level evidence.
- Validated and accepted P0-R01B: pinned cross-framework evidence supports a retained Rust runtime, bounded phase pipeline and generation-safe handles; performance remains unverified.
- Validated and accepted P0-R03A: callback-free architecture conditions, falsifiers, fourteen experiments and seven proposed gates are documented; no target is claimed achieved.
- Validated and accepted P0-R03B: deterministic scenes, strict headless/presented/input/idle gates, native callback counters, immutable baselines and ABBA regression rules are documented; all targets remain unverified.
- Validated and accepted P0-R04A after handoff normalization: explicit OS/backend masks, winit/wgpu constraints, known stable-release defects and platform test gates are documented; no platform is claimed verified.
- Validated and accepted P0-R02A: exact dependency pins, three-target resolver evidence, Linux compile evidence, reproduced Taffy failures and licensing/soundness/MSRV risks are documented.
- Accepted P0-SK01: Skeptic reproduced key evidence, reconciled all cross-stream conflicts, recorded binding corrections and conservative defaults, and requested no Round 2.
- Accepted P0-AR01: ten immutable ADRs define the runtime, snapshot-first Counter slice, API/crate boundaries, exact pins, platform gates, input/a11y ownership, abi3/typing/release policy, benchmark gates, clean-room policy and Apache-2.0 project license.
- Accepted P0-PL01 after independent validation: 32 blocked Phase 1 tasks, 89 resolving dependency edges, all 52 ADR gates mapped, required PR workflow and a thin Counter-first critical path.
- Red-Team attempt 1 completed with changes requested: 11 blocking findings (B-01–B-11) and 4 nonblocking findings. The graph is structurally valid but not execution-ready.

## Active work

Planner attempt 2 is revising the Phase 1 plan and task graph to resolve B-01 through B-11. Red-Team attempt 2 is blocked behind that revision. `P0-AP01` remains blocked; no feature implementation has started.

- RQ-01: prior-art architecture and clean-room boundaries.
- RQ-02: Rust/Python dependency, version, license, and maintenance selection.
- RQ-03: FFI/render-loop performance model and reproducible benchmark design.
- RQ-04: platform windowing/input/IME/accessibility/HiDPI and abi3 distribution constraints.

All eight researchers are Round 1 and may run concurrently. Their permitted writes are their assigned `RESEARCH/` file, an append-only action line in `LOG.md`, and their own handoff.

## Blocked

- Red-Team-Planner waits for Planner's Phase 1 task graph and vertical-slice plan.
- Feature implementation waits for Phase 0 approval after Red-Team review.
- Remote workflow is available: `origin` is configured and `main` tracks `origin/main`. Do not force-push or rewrite published history.

## Next 3 actions

1. Planner attempt 2 resolves B-01 through B-11 and regenerates reproducible validation evidence.
2. Red-Team attempt 2 rechecks the revised committed graph and gate semantics.
3. Orchestrator approves `P0-AP01` only at zero blocking findings, then authorizes the first Counter-slice build wave.

## Phase 0 exit gate

- Every decision-driving claim is verified, or the three-round cap is reached and uncertainty is recorded in `OPEN_QUESTIONS.md` with a conservative choice.
- Skeptic report contains no unresolved blocking issue.
- Architect-owned ADRs are accepted and immutable.
- Phase 1 `TASKS.json` has explicit dependencies and machine-checkable acceptance criteria.
- Red-Team-Planner reports no blocking issue, or Orchestrator records an explicit bounded exception.
- No implementation task has started before this gate.

## Performance truth policy

The requested numbers are targets, not facts: 120 fps with 1,000 elements; 120 fps for a 10,000-row virtualized list; input-to-frame p95 below 8 ms; idle CPU near zero; no Python callbacks per frame. Each must later be measured by a reproducible benchmark on a disclosed hardware/software stack. Until then, all are unverified.
