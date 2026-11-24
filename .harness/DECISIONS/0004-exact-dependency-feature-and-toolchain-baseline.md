# ADR 0004: Pin the exact dependency, feature and toolchain baseline

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation.

## Context

The selected releases resolve together in the research probe, and Linux `cargo check --locked --all-targets` passed on rustc/cargo 1.100.0. That probe included a broader Taffy feature set and Linux GLES; it is compatibility evidence, not proof of the narrower production baseline or of runtime support. The resolved graph requires Rust at least 1.90 through `ordered-float 5.5.1`. Known Taffy, cosmic-text, slotmap and rustc-hash issues require explicit constraints.

## Decision

Slice 1 uses these **exact direct pins** and no Git/trunk dependencies:

| Role | Pin and feature policy |
|---|---|
| Python binding | `pyo3 = "=0.30.1"`, `default-features = false`, `features = ["macros", "extension-module", "abi3-py311"]`; optional `stubs = ["pyo3/experimental-inspect"]` is disabled by default and used only for reviewed stub diffs |
| Build tool | `maturin = "=1.16.0"` as pinned release tooling, not a runtime dependency |
| Window/event loop | `winit = "=0.30.13"`, `default-features = false`, `features = ["rwh_06", "x11", "wayland", "wayland-dlopen"]` |
| GPU renderer | `wgpu = "=30.0.2"`, `default-features = false`, `features = ["std", "wgsl"]` plus exactly one target backend: `vulkan` on Linux, `dx12` on Windows, `metal` on macOS |
| Layout | `taffy = "=0.16.0"`, `default-features = false`, `features = ["std", "taffy_tree", "flexbox", "block_layout"]` |
| Text | `cosmic-text = "=0.19.0"`, `default-features = false`, `features = ["std", "swash", "fontconfig"]` |
| Internal maps | `rustc-hash = "=2.1.3"`, `default-features = false`, `features = ["std"]` |
| Native identity | `slotmap = "=1.1.1"`, `default-features = false`, `features = ["std"]` |
| Deferred accessibility | `accesskit = "=0.25.2"` with `default-features = false`; `accesskit_winit = "=0.34.2"` with its published defaults when the later adapter slice starts |

Additional policy:

- **Linux compiles and selects Vulkan only.** GLES/OpenGL/WebGPU/WebGL are not enabled or claimed.
- AccessKit's optional `pyo3` feature remains **disabled**; it requires PyO3 0.29 and conflicts with the selected 0.30.1 line. The adapter is not a slice-1 dependency.
- Taffy's public subset is tested in-flow flex/block only. Grid, float, calc, CSS parsing, aspect-ratio-driven flex sizing and mutable absolute popup containers are deferred. Unsupported constructs fail validation; an invariant failure triggers one clean full-tree rebuild, then fails closed if still incorrect.
- Slotmap allocation is hard-capped at **65,536 live native node slots** across framework and Taffy trees, far below `u32::MAX`. `detach`/`reattach` is forbidden in slice 1; stale-key and reinsertion tests are mandatory.
- rustc-hash is for trusted internal keys only. Do not rebuild a map by inserting another FxHash map's iteration order; attacker-controlled dictionaries use randomized hashing.
- Pin Rust **1.100.0** in `rust-toolchain.toml`, use edition 2024, commit `Cargo.lock`, and build with `--locked`. No nightly, Cargo patches or floating prereleases. The effective floor is at least 1.90, but **no MSRV promise** is made until the production lockfile is tested on the proposed floor.
- Python development typing is gated by mypy **2.4.1**. There is no default runtime Python dependency and no async runtime in slice 1.

## Alternatives considered

- **winit 0.31 beta or wgpu trunk:** rejected because unreleased APIs/fixes are not a reproducible baseline.
- **wgpu default/all backends or Linux GLES fallback:** rejected because it broadens loading, packaging and support claims without evidence.
- **Taffy defaults/full CSS subset:** rejected because reproduced 0.16.0 defects would become public correctness promises.
- **Taffy 0.15.1 or wgpu 29.0.4 as co-baselines:** retained only as named diagnostic comparators, not production alternatives.
- **AccessKit in the first render slice:** deferred because adapter threading, activation and virtualization do not help prove the first frame.
- **Claim Rust 1.89/1.90 MSRV from manifests alone:** rejected; only 1.100.0 was exercised.

## Consequences

- Exact pins improve reproducibility but require deliberate, tested upgrades; wgpu has a short breaking-release cadence.
- The narrower Taffy feature set and node cap reduce risk but reject layouts users may expect.
- cosmic-text still needs an atlas/borrow-pattern spike, an explicit resolved monospace family for performance-sensitive text and font-fallback tests.
- The production lockfile will differ from the research probe and must be regenerated and validated before any build claim.
- Slotmap 1.1.1 remains a tracked soundness risk; the cap and API ban are mitigations, not an upstream fix.

## Evidence links

- [Skeptic §2.1 — exact releases and effective Rust floor](../REVIEWS/phase-0-research-skeptic.md#21-exact-selected-releases) and [§8](../REVIEWS/phase-0-research-skeptic.md#8-residual-uncertainties-and-conservative-defaults).
- [RQ-02A — inventory, resolver and narrow recommendation](../RESEARCH/2026-11-24-rq-02-core-rust-stack.md#narrow-recommendation).
- [RQ-02B — exact PyO3/maturin candidates](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#exact-candidate-versions-and-disposition).
- [Published feature manifests recorded in the RQ-02A source register](../RESEARCH/2026-11-24-rq-02-core-rust-stack.md#source-register) (Taffy, cosmic-text, AccessKit and adapter).

## Validation gates

- **AR04-G1 — production lock:** regenerate `Cargo.lock` for the exact table, then `cargo check --locked --all-targets` and target metadata checks for `x86_64-unknown-linux-gnu`, `x86_64-pc-windows-msvc` and `aarch64-apple-darwin` exit zero; an architecture test asserts exact versions/features, no GLES, no AccessKit in slice 1 and no disabled-feature leakage.
- **AR04-G2 — Taffy constraints:** regression tests for #804, #1354 and #1357 plus supported flex/block cases exit zero; unsupported public layouts return typed validation errors; full-tree fallback equivalence is property-tested.
- **AR04-G3 — slotmap guards:** tests exit zero for the 65,536-slot cap, stale keys, reuse/reinsertion and forbidden `detach`/`reattach`; a source audit finds no forbidden calls.
- **AR04-G4 — text adapter:** a cosmic-text 0.19.0 atlas spike passes ASCII/CJK/RTL/emoji/fallback tests without the #543 borrow pattern and reports #518 behavior for generic versus explicit monospace families.
- **AR04-G5 — map/rebuild safety:** large scene-rebuild tests and a source audit exclude the rustc-hash #45 insertion-order pattern.
- **AR04-G6 — toolchain claim:** any future MSRV statement requires a clean `--locked` build/test on that exact compiler; until then release metadata states only the pinned build toolchain.

## Revisit when

A stable upstream release fixes a constraining defect, the production lockfile fails a target, or benchmarks identify a dependency-level bottleneck. Version/feature changes require a new lockfile, the relevant gates and a superseding ADR when they alter support, safety or public behavior.
