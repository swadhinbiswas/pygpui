# ADR 0001: Keep the UI runtime and every frame in Rust

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User retains the open approvals listed in `.harness/OPEN_QUESTIONS.md`.

## Context

The accepted Skeptic baseline is `796a4e0`; its report records the reviewed research baseline as `cc378c2`. Pinned prior art verifies that native UI runtimes can separate event dispatch, retained state, layout, paint and presentation. It does **not** prove that pygpui will meet any frame-rate, latency or idle-CPU target. PyO3 0.30.1 and winit 0.30.13 mechanics support a detached native loop, but hidden callbacks, finalizers or Python-backed frame state would invalidate the no-Python-per-frame invariant.

## Decision

- Rust owns the platform-main-thread event loop, windows, entity registry, retained UI nodes and element state, layout, text, hit testing, focus/key dispatch, IME state, accessibility mirror, scene, caches, animation clock and presentation.
- Python owns application-domain values, reusable view definitions, semantic intent and event handlers. It does not own layout, paint resources or frame scheduling.
- Slice 1 runs **one winit loop on the platform main thread with no render worker**. `App.run()` detaches from Python for native work and reattaches only at coalesced semantic-event or lifecycle boundaries.
- The steady-frame closure contains native data only. There is **no Python callback per frame**. Python callables, `Py<T>` values, borrowed Python objects, signal/pending-call drains and Python finalizers are confined to the event actor and are not reachable from a frame.
- Commands cross a bounded queue. Non-`Send` UI state is created and used inside the detached main-thread scope; only `Send` results cross back to Python.

## Alternatives considered

- **Python-owned loop or Python render callback per frame:** rejected because it makes frame cadence and latency depend on Python scheduling and directly violates the mission.
- **Rust render worker behind a Python main loop:** rejected for slice 1 because platform main-thread rules, surface lifetime and shutdown become harder; a worker also does not remove Python callbacks by itself.
- **Persistent Python VDOM as the retained tree:** rejected because it introduces Python objects into reconciliation and risks per-frame execution.
- **Two native loops or an asyncio co-driver:** deferred; main-thread ownership, cancellation and wakeup behavior are unverified across the candidate platforms.

## Consequences

- Native animation, scrolling and unchanged redraws can be callback-free by construction, but this remains a hypothesis until counters and sentinels pass.
- UI mutation is main-thread/event-turn oriented. Background Python threads may only post validated commands.
- The first slice accepts platform-thread and shutdown complexity instead of deferring it to a worker abstraction.
- Free-threaded Python remains unsupported; `gil_used = true` is mandatory until a separate safety audit.

## Evidence links

- [Skeptic §6 — verified decision set](../REVIEWS/phase-0-research-skeptic.md#6-verified-decision-set-for-architect) and [§8 — conservative defaults](../REVIEWS/phase-0-research-skeptic.md#8-residual-uncertainties-and-conservative-defaults).
- [RQ-02B C11–C16 — attach/detach and event boundary](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#c-event-driven-python-boundary-with-no-per-frame-callbacks).
- [RQ-03A §10 — proof obligations](../RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md#10-architecture-conditions-and-proof-obligations).
- [RQ-04A C13–C16 — main-thread loop and redraw semantics](../RESEARCH/2026-11-24-rq-04-desktop-runtime.md#5-claim-ledger--winit-event-hidpi-and-input-semantics).

## Validation gates

- **AR01-G1 — main-thread lifecycle:** `cargo test -p pygpui-platform --test main_thread_lifecycle` exits zero and installed-wheel tests on each candidate OS prove one loop, main-thread creation, clean close, no render worker and no use-after-drop of window/display handles.
- **AR01-G2 — native frame closure:** a committed static dependency/call-graph audit exits zero; only `pygpui-python` may depend on PyO3, and the frame closure has no Python entry, attach, object-access or finalizer path.
- **AR01-G3 — callback proof:** V01-style tests pass native counters and deliberate sentinels, with zero Python callbacks, frame entries, attachments and finalizers in every marked static/native-animation/native-scroll window.
- **AR01-G4 — queue and idle:** bounded-queue/backpressure tests exit zero; a 60-second idle test proves `Wait`/bounded `WaitUntil`, no indefinite `Poll`, no unchanged-frame submissions and bounded wakeups.

## Revisit when

A measured steady-frame counter is nonzero; main-thread lifecycle tests fail; or profiling shows a main-thread bottleneck that a worker could address. Any worker proposal requires a superseding ADR, platform lifetime tests and the same callback-proof gates. Revisit the GIL policy only after a free-threaded safety audit and separate interpreter/wheel evidence.
