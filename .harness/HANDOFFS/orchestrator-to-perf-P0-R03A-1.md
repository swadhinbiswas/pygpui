FROM: Orchestrator
TO: Researcher-Perf instance A
TASK-ID: P0-R03A
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Build an evidence-aware performance cost model for RQ-03. Explain FFI/GIL boundaries and the architectural conditions required for event-only Python calls, then identify costs and invalidation strategies for tree diffing, layout, hit testing, painting/batching, text atlases, animation and scrolling.

WHAT I DID: Converted the requested performance targets into research questions and prohibited unmeasured assertions.

EVIDENCE: `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`; `.harness/PROCESS.md` performance truth policy.

WHAT I DID NOT DO / SKIPPED, AND WHY: No benchmark has been run because no implementation exists. Numeric estimates must be labelled and must not be presented as results.

OPEN RISKS & SURPRISES: A Rust frame loop alone does not prove 120 fps; layout, text, GPU submission, compositor and Python wakeups can each dominate.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-03-performance-and-benchmark-model.md`; research primary FFI/GIL and rendering-pipeline evidence, write `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md` with assumptions and claim-level labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-perf-to-skeptic-P0-R03A-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-perf-P0-R03A-1.md`
3. `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`
4. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Target benchmark hardware and whether certification requires physical display presentation or accepts headless frame-time evidence.
