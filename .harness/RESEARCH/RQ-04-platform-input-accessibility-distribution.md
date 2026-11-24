# RQ-04 — Platform, input, accessibility and distribution constraints

Status: Round 1 active
Decision unblocked: Initial platform support matrix, window/render backend choices, IME/focus/a11y integration and cross-platform release feasibility.
Budget: Maximum 3 research rounds.

## Required angles

1. Desktop runtime: Wayland vs X11, Windows DX12 vs Vulkan selection, macOS Metal specifics, HiDPI scaling, winit event semantics and wgpu adapter/surface limitations.
2. Input and delivery: IME lifecycle, AccessKit integration, keyboard/focus behavior, accessibility tree ownership, abi3 wheel differences across operating systems, CI runners, code signing/notarization constraints and Linux packaging expectations.

## Decision-driving questions

- Which backend/API choices minimize platform-specific branches without hiding correctness bugs?
- How must Rust own IME, focus and accessibility state while Python describes application state?
- What platform-specific test coverage is required before claiming support?
- Which distribution steps require user-owned credentials or infrastructure and must therefore remain blocked?
- What is the narrowest credible first-release macOS/Windows/Linux matrix?

## Required output per researcher

Cite dated primary documentation and issue/release evidence. Separate upstream guarantees from integration assumptions. Record contradictions, conservative defaults and explicit unknowns. Do not claim signing, notarization or store distribution is complete without credentials and executed evidence.
