# ADR 0006: Own input, IME, focus and accessibility in Rust

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User retains OQ-07/OQ-09 accessibility approvals.

## Context

Winit exposes raw window, keyboard and IME events; it does not supply pygpui's focus model or guarantee complete IME behavior. Open reports cover Windows key events during composition, macOS commit/teardown issues and X11 commit loss. AccessKit separates a provider tree from platform adapters, but adapters are best-effort and may call handlers on platform-dependent threads. No physical IME or assistive-technology test has run.

## Decision

- Every winit event enters one Rust-owned boundary. Rust owns native focus reconciliation, pressed-key state, pointer capture, hit testing, shortcut resolution, capture/bubble routing, text-editor state and the accessibility mirror. Python supplies domain text, semantic labels/values/actions and focus policy; it never receives raw adapter-thread callbacks.
- Use physical keys for position-based input and logical keys for configurable shortcuts. Identify synthetic/repeat events. Clear pressed keys and composition state on **every** focus loss, even where the OS sends no synthetic release.
- Editable controls own IME. Model `Enabled → Preedit* → empty Preedit → Commit → Disabled`, plus direct `Commit` and external disable. While IME is allowed, insert text only from `Ime::Commit`; raw `KeyboardInput` must not duplicate text. Composition gates candidate navigation, Enter, Space, arrows, Backspace and application shortcuts.
- All editor and IME offsets at the boundary are **UTF-8 byte offsets**. Convert Python code-point indices exactly once in Rust and test CJK, emoji and combining marks.
- On input-target change, use a generation-tagged disable → clear → handle `Disabled` → enable sequence for the new target and update its caret/candidate area after caret, scroll, resize or scale changes. Ignore stale-generation events.
- Rust is the sole text-editing source during composition. External Python document updates carry a version and must not overwrite a newer local edit or active preedit.
- Before dropping a macOS window, call `set_ime_allowed(false)` while it is alive. This is a workaround for winit #4626, not an upstream fix.
- Define stable accessibility identity and semantic snapshot hooks in slice 1, but defer the platform adapter until after the first render/text slice. The selected later pair is AccessKit 0.25.2 + accesskit_winit 0.34.2; AccessKit's optional `pyo3` feature stays disabled.
- When integrated, create the window invisible, attach the adapter, then show. Forward every event through `process_event` before application handling. Start with `with_event_loop_proxy`; queue activation/action/deactivation work to the main loop before any Python call. Rust owns stable `NodeId`s, focus and tree diffing; every update carries current focus.
- No WCAG/conformance, complete-IME or virtualized-list accessibility claim is made. AccessKit #871 leaves 10,000-row metadata unresolved; visible-range plus total-row/scroll semantics require a designed and tested representation.

## Alternatives considered

- **Let Python handle raw key/IME events or focus:** rejected because it introduces per-event Python work, duplicate text paths and platform-thread hazards.
- **Rely on winit's documented preedit suppression everywhere:** rejected because Windows #4508 is a documented counterexample.
- **Call Python directly from accessibility handlers:** rejected because handler threads are platform-dependent and would break the native-frame and lifecycle invariants.
- **Enable AccessKit's `pyo3` feature:** rejected because it requires PyO3 0.29 rather than the selected 0.30.1.
- **Integrate the adapter into the first render-only slice:** deferred because it does not help prove the first frame and adds activation/threading risk.

## Consequences

- Input correctness requires a Rust state machine and physical OS tests, not just event forwarding.
- Python gives up direct native focus/IME control in exchange for deterministic ownership and no cross-thread calls.
- Accessibility semantics are designed early, but adapter cost, AT activation and virtualized-list usability remain unverified.
- Known IME gaps can block a platform/input-method support claim without blocking the basic Counter slice.

## Evidence links

- [Skeptic §6 — IME and accessibility decisions](../REVIEWS/phase-0-research-skeptic.md#6-verified-decision-set-for-architect) and [§7 — physical validation needs](../REVIEWS/phase-0-research-skeptic.md#7-plausible-claims-requiring-validation).
- [RQ-04B IME/KBD/A11Y claim register](../RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md#claim-register).
- [RQ-04B — IME/focus contract](../RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md#ime-and-focus-integration-contract) and [accessibility release gate](../RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md#accessibility-release-gate).
- [RQ-01B R4 — Rust-local text synchronization](../RESEARCH/2026-11-24-rq-01-cross-framework.md#recommendation).

## Validation gates

- **AR06-G1 — state machines:** unit/property tests exit zero for direct commit, empty-preedit clearing, UTF-8 offsets, focus A→B→C races, stale disable events, focus-loss reset, external text version conflicts and close during composition.
- **AR06-G2 — physical IME:** logged tests pass for Japanese, Chinese and Korean IMEs plus dead keys on each candidate OS/protocol; Windows #4508, macOS #4807/#4626 and X11 #4839 are explicitly exercised with no duplicate text, stuck key or shortcut activation.
- **AR06-G3 — accessibility tree:** AccessKit consumer tests exit zero for stable IDs, full/incremental updates, focus removal/restoration, unchanged properties and action routing exactly once on the main loop.
- **AR06-G4 — assistive technology:** VoiceOver, Narrator and Orca workflows pass keyboard-only operation, navigation, action invocation, text input with IME and dynamic updates; inspector-only evidence does not pass.
- **AR06-G5 — callback isolation:** native counters/sentinels prove no Python call from accessibility adapter threads or during a11y-only frame updates; enabling AT does not regress ADR 0008 idle/frame gates.
- **AR06-G6 — virtualized list:** a tested accessible representation for 10,000 rows, including #871 disposition, exists before any list accessibility claim.

## Revisit when

A stable winit release fixes the cited IME defects; AccessKit fixes virtualization or adapter gaps; or User approves a WCAG/AT target. Any direct accessibility handler must first pass a no-Python/thread-affinity audit. Broader IME or conformance wording requires the corresponding physical evidence, not merely adapter integration.
