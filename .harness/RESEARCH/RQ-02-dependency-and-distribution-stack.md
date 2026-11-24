# RQ-02 — Dependency, version, license and distribution stack

Status: Round 1 active
Decision unblocked: Initial crate/dependency baseline, PyO3/maturin integration, supported Python ABI strategy and strict public typing approach.
Budget: Maximum 3 research rounds.

## Required angles

1. Core Rust stack: winit, wgpu, taffy, cosmic-text, accesskit, rustc-hash and slotmap. Record exact candidate versions, licenses, repository/release activity, known issues, maintenance health, platform gaps and API stability risks.
2. Python boundary and delivery: PyO3, maturin, abi3, GIL/free-threading behavior, type stub generation, mypy --strict compatibility, async runtime integration if needed, and wheel CI/signing constraints for macOS/Windows/Linux.

## Decision-driving questions

- Which exact dependency versions are mutually compatible on all three desktop OS families?
- Which dependencies are required for the first vertical slice versus deferred?
- Can an abi3 extension expose a strict-typed public API without leaking implementation types?
- What license/NOTICE obligations follow from direct and transitive dependencies?
- Which choices materially threaten the no-Python-per-frame requirement?

## Required output per researcher

Record source URL, exact version/tag/commit where relevant, publication or release date, access date, license, and claim confidence. Identify stale sources and contradictions. Recommend a narrow baseline plus rejected alternatives; do not merely list popular crates.
