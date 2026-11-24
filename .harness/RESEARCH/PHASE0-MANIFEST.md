# Phase 0 Research Manifest

Last updated: 2026-11-24
Status: Round 1 complete; all eight outputs accepted and ready for Skeptic

This manifest lets Skeptic locate all eight independent outputs without exceeding the seven-file handoff limit.

| Question | Task | Researcher angle | Required research output | Required handoff | Status |
|---|---|---|---|---|---|
| RQ-01 | P0-R01A | GPUI/Zed internals and clean-room boundaries | `2026-11-24-rq-01-gpui-internals.md` | `researcher-prior-art-to-skeptic-P0-R01A-1.md` | Done |
| RQ-01 | P0-R01B | Cross-framework architecture | `2026-11-24-rq-01-cross-framework.md` | `researcher-prior-art-to-skeptic-P0-R01B-1.md` | Done |
| RQ-02 | P0-R02A | Core Rust dependency stack | `2026-11-24-rq-02-core-rust-stack.md` | `researcher-libs-to-skeptic-P0-R02A-1.md` | Done |
| RQ-02 | P0-R02B | PyO3/maturin/abi3/typing | `2026-11-24-rq-02-python-abi3-typing.md` | `researcher-libs-to-skeptic-P0-R02B-1.md` | Done |
| RQ-03 | P0-R03A | FFI/GIL/render cost model | `2026-11-24-rq-03-ffi-render-cost-model.md` | `researcher-perf-to-skeptic-P0-R03A-1.md` | Done |
| RQ-03 | P0-R03B | Reproducible benchmark protocol | `2026-11-24-rq-03-benchmark-protocol.md` | `researcher-perf-to-skeptic-P0-R03B-1.md` | Done |
| RQ-04 | P0-R04A | Desktop runtime and rendering | `2026-11-24-rq-04-desktop-runtime.md` | `researcher-platform-to-skeptic-P0-R04A-1.md` | Done |
| RQ-04 | P0-R04B | IME/accessibility/distribution | `2026-11-24-rq-04-ime-a11y-distribution.md` | `researcher-platform-to-skeptic-P0-R04B-1.md` | Done |

Research files live in `.harness/RESEARCH/`; handoffs live in `.harness/HANDOFFS/`.

## Pre-Skeptic reconciliation watchlist

These are cross-stream differences to resolve, not accepted conclusions:

- RQ-03A cites PyO3 0.27.0 for attach/detach mechanics, while RQ-02B proposes PyO3 0.30.1. Verify that the decision-driving semantics remain valid for 0.30.1.
- RQ-03A cites winit 0.30.12 and wgpu 30 documentation. Reconcile those APIs with the exact winit/wgpu versions selected by RQ-02A and RQ-04A/RQ-04B.
- RQ-02B proposes a candidate `macosx_11_0_universal2` build tag, while RQ-04B proposes macOS 26 as the supported/tested floor. Distinguish deployment target from support promise and require an explicit Architect decision.
- RQ-04B uses AccessKit 0.25.2 / accesskit_winit 0.34.2 and winit 0.30.13; reconcile those exact versions with the core dependency graph before accepting an ADR.
- RQ-01A recommends a full-window rebuild fallback with selective caching; RQ-01B recommends event-driven Python patches into a retained Rust tree. Determine whether these are complementary phases or competing first-slice contracts.

## Skeptic disposition summary

In progress at committed Round 1 baseline `cc378c2`. Skeptic must produce `.harness/REVIEWS/phase-0-research-skeptic.md` and list any targeted Round 2 tasks. Orchestrator owns status updates to this manifest and `TASKS.json`.

Skeptic completed at attempt 1 with no Round 2 requests. Its report is accepted as the binding disposition for ADR drafting; all corrections and conservative defaults in that report remain mandatory.
