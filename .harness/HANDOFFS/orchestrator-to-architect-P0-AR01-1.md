FROM: Orchestrator
TO: Architect
TASK-ID: P0-AR01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Turn the Skeptic-approved Phase 0 evidence into concise architecture decision records for pygpui. Own public API, module boundaries, runtime ownership, dependency baseline, platform baseline, performance gates and licensing posture. List rejected alternatives and negative consequences. Do not write feature code.

WHAT I DID: Completed and committed eight independent Round 1 research streams, dispatched Skeptic, and defined the required ADR coverage and machine-checkable Phase 0 gate.

EVIDENCE: `.harness/REVIEWS/phase-0-research-skeptic.md`; `.harness/HANDOFFS/skeptic-to-orchestrator-P0-SK01-1.md`; `.harness/RESEARCH/PHASE0-MANIFEST.md`; `.harness/TASKS.json` task P0-AR01; committed Round 1 baseline `cc378c2`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No ADR is drafted or accepted before Skeptic disposition. Architecture must not launder plausible or unverified research into factual claims.

OPEN RISKS & SURPRISES: Cross-stream differences include PyO3 source version versus proposed pin, macOS deployment target versus support floor, Apple-silicon-only versus universal2, full-window rebuild versus event-driven patches, Wayland mixed-license content, stable wgpu/winit defects, Taffy layout failures and slotmap's acknowledged soundness report.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/REVIEWS/phase-0-research-skeptic.md`, `.harness/RESEARCH/PHASE0-MANIFEST.md`, `.harness/OPEN_QUESTIONS.md` and `.harness/PROCESS.md`; draft the required ADRs in `.harness/DECISIONS/` with evidence links, rejected alternatives, negative consequences and revisit triggers, then append one action line to `LOG.md` and write `.harness/HANDOFFS/architect-to-planner-P0-AR01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-architect-P0-AR01-1.md`
3. `.harness/REVIEWS/phase-0-research-skeptic.md`
4. `.harness/RESEARCH/PHASE0-MANIFEST.md`
5. `.harness/OPEN_QUESTIONS.md`
6. `.harness/PROCESS.md`
7. `.harness/TASKS.json` tasks P0-AR01 and P0-PL01

CONTEXT I WISH I HAD HAD: User-approved OS/CPU/Python support floors, accessibility target, release channel and benchmark certification environment. Where these remain open, choose the narrowest conservative scope and record the unresolved approval rather than inventing it.

## Required ADR coverage

1. Rust-owned event-driven runtime and Python semantic boundary.
2. Retained/immediate model, first-slice update contract and cache/invalidation policy.
3. Public Python API, entity/view/handle semantics and lifecycle/reentrancy rules.
4. Exact Rust/Python dependency and feature baseline, MSRV/toolchain policy and deferred components.
5. Platform/window/render backend baseline and support-claim gates.
6. Input, IME, focus and accessibility ownership/integration policy.
7. abi3, strict typing, wheel matrix and release evidence policy.
8. Benchmark protocol, target certification and regression gates.
9. Clean-room, dependency provenance, license/NOTICE and third-party audit policy.

Accepted ADRs are immutable. Plausible recommendations may be accepted only as conservative product choices with explicit validation tasks; unverified claims may not be presented as facts.

## Binding Skeptic corrections

- Slice 1 uses complete Rust-owned snapshot replacement on semantic change, stable IDs and a full-window Rust rebuild. Typed incremental patches and cached subtrees are later optimizations.
- Use one platform-main-thread winit loop in slice 1; no render worker. Reattach Python only at semantic event boundaries.
- Use the exact selected pins. Linux compiles/selects Vulkan only; GLES is deferred. AccessKit's optional `pyo3` feature stays disabled.
- Candidate macOS policy is macOS 26 arm64 only; no Intel/universal2 or 11.0 deployment-target claim until tested.
- Benchmark input latency ends at the first presented response, not submission. Use five ABBA blocks = twenty process runs = ten pairs; allow at most 51 mounted list rows; benchmark Metal with three drawables for desired latency 2.
- Python-boundary proof uses native counters and sentinels. `threading.setprofile_all_threads` is 3.12+ only; benchmark GIL builds by launching separate interpreters, not `PYTHON_GIL`.
- Hard-cap slotmap node slots far below `u32::MAX`, forbid `detach`/`reattach` in slice 1, and constrain Taffy to tested in-flow flex/block with correctness fallbacks.
- No performance, platform, IME, accessibility, permissive-only Wayland, MSRV or public-signing claim without its stated evidence gate.
