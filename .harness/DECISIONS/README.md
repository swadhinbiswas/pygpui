# Architecture decisions

Accepted evidence baseline: `796a4e0` (the Skeptic report records the underlying Round 1 research baseline as `cc378c2`).  
Decision date: 2026-11-24. Owner: Architect, task `P0-AR01`, attempt 1.

`Status: Accepted` means the conservative design is adopted for planning. It does **not** mean any performance target, platform, IME path, accessibility workflow, MSRV, wheel, license closure or signing pipeline has been achieved or certified.

| ADR | Decision | Status | Primary validation gates |
|---|---|---|---|
| [0001](0001-rust-owned-runtime-and-python-semantic-boundary.md) | Rust owns the main-thread runtime and every frame; Python owns semantics | Accepted | AR01-G1–G4 |
| [0002](0002-snapshot-first-full-window-rebuild.md) | Complete Rust snapshot replacement and full-window rebuild in slice 1 | Accepted | AR02-G1–G5 |
| [0003](0003-public-python-api-and-module-boundaries.md) | Small typed Python API, opaque generation-safe handles and crate boundaries | Accepted | AR03-G1–G5 |
| [0004](0004-exact-dependency-feature-and-toolchain-baseline.md) | Exact pins, constrained features, Rust 1.100.0 build toolchain and no MSRV promise | Accepted | AR04-G1–G6 |
| [0005](0005-platform-window-and-render-backend-baseline.md) | Vulkan-only Linux, DX12 Windows, macOS 26 arm64 Metal candidate matrix | Accepted | AR05-G1–G6 |
| [0006](0006-input-ime-focus-and-accessibility-ownership.md) | Rust-owned input/IME/focus/accessibility with physical release gates | Accepted | AR06-G1–G6 |
| [0007](0007-abi3-strict-typing-wheel-and-release-evidence.md) | GIL-enabled `abi3-py311`, reviewed strict stubs and evidence-gated wheels | Accepted | AR07-G1–G5 |
| [0008](0008-benchmark-certification-and-regression-gates.md) | Qualified certification, native callback proof and five-block/ten-pair ABBA regressions | Accepted | AR08-G1–G6 |
| [0009](0009-clean-room-license-and-provenance-policy.md) | Concept-only clean room and artifact-level license/NOTICE closure | Accepted | AR09-G1–G5 |
| [0010](0010-license-pygpui-under-apache-2-0.md) | License pygpui-authored project artifacts under Apache-2.0 | Accepted | AR10-G1–G4 |

## Planning entry point

The first demoable slice is the ADR 0002 Counter window: Python creates an entity and view, Rust presents shaped text plus a button, a semantic action updates Python state, one complete snapshot crosses the boundary, Rust rebuilds and presents, and no Python runs on the frame path. Broader widgets, typed patches, damage tracking, the accessibility adapter, IME completeness and virtualized-list authoring follow only after their gates.

Each `ARxx-Gn` is a validation obligation, not an existing test. Phase 1 planning must turn these into owned, dependency-ordered tasks whose acceptance criteria name commands/tests that exit zero or exact measured thresholds. The detailed Skeptic dispositions remain binding, especially §§5–8 of [the review](../REVIEWS/phase-0-research-skeptic.md).

## Open approvals that remain outside ADR acceptance

- OQ-02: certification hardware/display and exact performance gates.
- OQ-03/OQ-11: public OS/architecture and CPython support floors.
- OQ-04: any future free-threaded Python support.
- OQ-07/OQ-09: accessibility target and assistive-technology matrix.
- OQ-08/OQ-13: any source-derived exception and permissive-only Wayland distribution.
- OQ-10: release channel, publishing and signing credential ownership.
- OQ-14: any future MSRV promise.

Until these close, use the conservative defaults in the ADRs and make no corresponding support or certification claim.

## Immutability

Accepted ADRs are records. Do not edit their decisions in place; write a new monotonically numbered ADR that supersedes the old one and update this index. Typo/link repairs are permitted. Numbers are never reused or renumbered.
