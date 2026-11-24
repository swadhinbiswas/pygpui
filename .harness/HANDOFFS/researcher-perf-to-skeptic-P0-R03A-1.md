FROM: Researcher-Perf instance A
TO: Skeptic
TASK-ID: P0-R03A
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Build an evidence-aware PyO3/GIL and rendering cost model for RQ-03; identify conditions that can guarantee no Python callback on steady-state frames, falsifiers, assumptions, claim labels, and validation experiments. Research only; no feature code, state/task edits, or commits.

WHAT I DID: Wrote `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md`. It models FFI/GIL attachment and detach, event queues, retained-tree diff/replay, layout invalidation/cache keys, hit testing, painter batching/instancing, glyph shaping/raster/atlas behavior, native animation, virtualized scrolling, GPU submission, and presentation. It defines a callback-free native-runtime architecture and a concrete falsification matrix. It supplies eight decision-driving claims (C01–C08), fourteen proposed experiments (V01–V14), and seven proposed acceptance gates (G01–G07). All performance targets remain explicitly unverified; no benchmark result is claimed.

EVIDENCE: Dated primary sources include PyO3 0.27.0 source/docs (2025-10-19), CPython 3.14.10 thread-state/GIL documentation (updated 2026-11-24), wgpu 30 docs, winit 0.30.12 (2025-07-27), Taffy 0.16.0 (2026-11-23), cosmic-text 0.19.0 / pinned source (2026-04-22 / 2026-10-27), and pinned Zed/GPUI source (2026-11-24). `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md` §§1–14 contains the claim table, cost model, sources, and limitations. No pygpui benchmark exists.

WHAT I DID NOT DO / SKIPPED, AND WHY: No implementation, benchmark execution, hardware certification, or physical-display test was possible because Phase 0 has no feature code or certified benchmark hardware. Numeric frame-budget allocations and proposed idle/latency gates are labelled estimated/unverified. Browser/mobile behavior and arbitrary Python layout/asset callbacks are excluded from the initial guarantee rather than assumed free.

OPEN RISKS & SURPRISES: A Rust frame loop does not prove callback freedom: Python timers, `on_next_frame`, element-tree animation, measure/row providers, finalizers, refcounts, accessibility, missing glyphs, assets, signals, and pending calls can all falsify it. Virtualization is not Python-free if a Python row provider runs per frame. Headless 120 fps throughput is not physical 120 Hz presentation. Input-to-frame p95 below 8 ms cannot be inferred from CPU time. C03 remains plausible rather than verified; the event-batch/native-snapshot design needs implementation audit and V01 runtime proof.

EXACT NEXT STEP: Read `.harness/STATE.md`, `.harness/HANDOFFS/orchestrator-to-skeptic-P0-SK01-1.md`, `.harness/RESEARCH/PHASE0-MANIFEST.md`, all eight Round 1 research files and handoffs, and this report; attempt to falsify C01–C08, especially the callback-free guarantee and the distinction between retained-scene animation and callback-driven animation; issue decision-changing Round 2 requests only where the architecture choice could change.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-skeptic-P0-SK01-1.md`
3. `.harness/RESEARCH/PHASE0-MANIFEST.md`
4. `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md`
5. `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`
6. `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md` (Researcher-Perf B, when present)
7. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Certified CPU/GPU/display hardware, accepted idle-CPU definition, and the intended scope of “steady state” (static only, or native animation/scrolling too). The report conservatively treats static, retained-native animation, and native scrolling as separately testable classes.
