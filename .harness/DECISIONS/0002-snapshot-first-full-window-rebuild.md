# ADR 0002: Replace complete Rust snapshots and rebuild the window in slice 1

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation.

## Context

Retained state, an immediate authoring API, incremental updates and damage tracking are separate choices. The accepted evidence supports stable native identity and a bounded phase pipeline, but no pygpui implementation exists. Taffy 0.16.0 has reproduced correctness defects, so the first slice must optimize for a small, falsifiable correctness boundary rather than generic incrementality.

## Decision

- On each semantic change, the Python facade invokes `View.build()` once, validates the result and submits **one complete immutable `WindowSnapshot` owned by Rust**. No Python object is retained in the snapshot or frame path.
- Rust atomically replaces the previous snapshot. Stable user keys plus node kind reconcile retained identity state, but slice 1 performs a **full-window rebuild**: root layout, hit tree, focus/dispatch tree, accessibility mirror and paint scene are rebuilt for the affected window. Validation failure leaves the previous snapshot intact.
- The native turn is: drain events/timers → route input with current focus/capture/hit state → deliver coalesced semantic events to Python → accept a complete snapshot → validate/replace → full rebuild → encode/submit/present → coalesce follow-up demand.
- Invalidation, draw and present demand are distinct. Idle uses `Wait`; native timers use bounded `WaitUntil`. No Python callable exists for redraw, layout, paint, animation ticks or unchanged frames.
- Slice 1 has no typed incremental patches, subtree layout/paint caches or damage regions. Long-lived native resource caches such as a font system, shaped-text cache and glyph atlas are allowed only when keyed by native snapshot data and excluded from Python ownership. A forced full refresh is always available.
- The first vertical slice is a **Counter window**: Python creates an `Entity[Counter]`; Rust presents a shaped text label and button; click/key activation emits an `Increment` action; Python updates the entity and builds one replacement snapshot; Rust rebuilds and presents the response; close tears down cleanly. It must complete without Python on the frame path.

## Alternatives considered

- **Typed incremental patches first:** deferred because schema, ordering and stale-target correctness would expand the first slice without evidence that full native rebuilds are too slow.
- **Persistent Python VDOM/differ:** rejected because it retains Python state in the update path and invites per-frame execution.
- **Damage-region rendering first:** deferred; retained trees do not imply pixel damage, and a full redraw is the conservative fallback.
- **Whole-application Python immediate mode:** rejected unless Python output is cached and replayed natively, at which point it is event-driven submission rather than a Python frame loop.

## Consequences

- The update contract is easy to test and reason about; stable IDs preserve focus, text-edit and gesture state across replacement.
- Every semantic change can cost a full native layout/scene rebuild. The 1,000-element and 10,000-row targets are therefore unverified.
- Users must provide stable keys for dynamic sequences; ordering, removal and teardown need property tests.
- Later patches or caches must be opt-in, correctness-gated and benchmark-justified; they cannot silently change snapshot semantics.

## Evidence links

- [Skeptic §3 — snapshot/full-window reconciliation](../REVIEWS/phase-0-research-skeptic.md#3-cross-stream-reconciliation) and [§6](../REVIEWS/phase-0-research-skeptic.md#6-verified-decision-set-for-architect).
- [RQ-01A C-08–C-17 — immediate tree, retained state and scheduling](../RESEARCH/2026-11-24-rq-01-gpui-internals.md#2-retained-versus-immediate-rendering).
- [RQ-01B R3/R5 — bounded phases and layered incrementality](../RESEARCH/2026-11-24-rq-01-cross-framework.md#recommendation).
- [RQ-02A — reproduced Taffy failures](../RESEARCH/2026-11-24-rq-02-core-rust-stack.md#taffy-0160).

## Validation gates

- **AR02-G1 — snapshot contract:** schema/property tests exit zero for atomic replacement, rejected-snapshot rollback, stable-key reorder/insert/remove, duplicate keys, stale handles and full-refresh equivalence.
- **AR02-G2 — thin end-to-end slice:** a clean installed wheel runs the Counter demo, reports a presented response frame and exits zero on each candidate OS; click and keyboard paths each update the label exactly once.
- **AR02-G3 — rebuild proof:** native counters prove a semantic change visits the root and rebuilds layout/hit/focus/scene once, while a no-change interval performs no rebuild and no Python entry.
- **AR02-G4 — frame isolation:** V01 counters/sentinels remain zero between snapshot submission and presentation, including native resource-cache hits and misses.
- **AR02-G5 — scaling decision:** `e1000` and `l10000` benchmarks under ADR 0008 either pass their provisional gates or produce a profile identifying whether full rebuild is the blocker before any incremental design is proposed.

## Revisit when

ADR 0008 measurements show a decision-driving full-rebuild cost, or a stable Taffy fix plus property tests makes a narrower layout subset safe. Incremental patches, subtree caching or damage tracking require a superseding ADR with correctness oracles and before/after evidence; full refresh remains the fallback.
