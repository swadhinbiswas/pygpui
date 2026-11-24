# Phase 0 Plan — Discovery and Decisions

Status: Active
Owner: Orchestrator
Created: 2026-11-24
Baseline commit: `6589bd0`

## Goal

Produce an evidence-backed architecture baseline and a reviewable Phase 1 task graph for pygpui without writing feature code or treating requested performance targets as achieved.

## Approach

1. Run four independent research questions with two researchers per question.
2. Require dated primary sources and claim-level `verified` / `plausible` / `unverified` labels.
3. Run one Skeptic over the combined batch. Dispatch targeted Round 2 only where a decision-driving claim remains plausible or unverified.
4. Stop research at three rounds per question. Record residual uncertainty and choose the conservative option.
5. Architect drafts immutable ADRs from verified findings; Planner converts accepted ADRs into machine-checkable tasks; Red-Team-Planner challenges the graph.
6. Orchestrator approves Phase 0 only after blocking findings are resolved or explicitly bounded.

## Alternatives rejected

- **Start a Rust/Python skeleton immediately.** Rejected because dependency, ownership and platform choices are still unknown; a skeleton would conceal assumptions and create rework.
- **Use one researcher per question.** Rejected because independent angles are required to expose contradictions rather than reinforce the first answer.
- **Accept secondary summaries as verification.** Rejected because versions, platform behavior and licensing claims require dated primary evidence.
- **Define later phases from inference.** Rejected because the supplied mission ends at the Phase 0 heading; later gates must be approved explicitly.
- **Assert feasibility from GPUI's existence.** Rejected because pygpui's Python boundary and requested workloads require their own reproducible measurements.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Research sources are stale or vendor documentation overstates support | Wrong dependency/platform ADR | Exact version/date evidence; Skeptic freshness review; conservative baseline |
| Eight agents append concurrently to `LOG.md` | Lost or interleaved log lines | One-line appends only; no rewrites; Orchestrator reconciles state from files |
| Free-threaded Python or platform signing scope expands the first slice | Schedule and ABI risk | Record as separate compatibility/release gates; no unsupported claims |
| Benchmark hardware is unspecified | Targets cannot be certified | Disclose environment and require user-approved certification hardware |
| No Git remote exists | Remote PR workflow unavailable | Local branches/worktrees and recorded diffs until destination is supplied |

## Task breakdown

| Task group | Tasks | Dependency | Done when |
|---|---|---|---|
| Harness bootstrap | H-001 | None | Files parse, graph validates, baseline committed |
| Prior art | P0-R01A, P0-R01B | H-001 | Two research files and handoffs exist |
| Dependencies/distribution | P0-R02A, P0-R02B | H-001 | Two research files and handoffs exist |
| Performance | P0-R03A, P0-R03B | H-001 | Cost model and benchmark protocol exist |
| Platform | P0-R04A, P0-R04B | H-001 | Runtime and IME/a11y/distribution research exist |
| Skeptic | P0-SK01 | All eight research tasks | Claim dispositions and Round 2 scope recorded |
| Architecture | P0-AR01 | P0-SK01 | Accepted ADR set with evidence and alternatives |
| Planning | P0-PL01, P0-RT01 | P0-AR01 | Task graph survives adversarial review |
| Approval | P0-AP01 | P0-RT01 | Gate evidence recorded; Phase 1 authorized |

## Rollback

Phase 0 writes only harness documentation and Git metadata. If the process or scope is rejected, retain the research as historical evidence, mark affected ADRs `Rejected` or supersede them, and revert only unaccepted plan/state changes. Do not delete research or accepted ADR history. No user data or runtime system is modified.

## Exit criteria

- All four questions have completed the research/skeptic loop or reached the explicit three-round cap.
- Every architecture-driving claim is verified or handled as a documented conservative uncertainty.
- ADRs and Phase 1 tasks pass Red-Team review.
- Orchestrator records approval in `STATE.md` before any implementation task starts.
