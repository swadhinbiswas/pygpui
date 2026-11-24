FROM: Orchestrator
TO: Planner
TASK-ID: P0-PL01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Convert the accepted Phase 0 ADRs into a Phase 1 task graph in `.harness/TASKS.json`. Every task must have an owner role, explicit dependencies, status, attempt count, evidence links and machine-checkable acceptance criteria. Put a thin end-to-end user-visible vertical slice before broader framework expansion.

WHAT I DID: Completed research and Skeptic review, prepared Architect handoff, and defined the planning gate. No Phase 1 implementation task is authorized yet.

EVIDENCE: `.harness/DECISIONS/README.md`; `.harness/DECISIONS/0001-…0010-…md`; `.harness/HANDOFFS/architect-to-planner-P0-AR01-1.md`; `.harness/REVIEWS/phase-0-research-skeptic.md`; `.harness/TASKS.json` task P0-PL01.

WHAT I DID NOT DO / SKIPPED, AND WHY: No Phase 1 task graph exists before accepted ADRs. Guessing interfaces now would serialize or invalidate parallel build work.

OPEN RISKS & SURPRISES: The first slice must prove the Python/Rust boundary and a real presented frame without prematurely building every widget, accessibility adapter or packaging lane. No Git remote exists, so build tasks must plan local branches/worktrees and recorded diffs until a remote is supplied.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/DECISIONS/README.md`, all ten accepted ADRs, `.harness/HANDOFFS/architect-to-planner-P0-AR01-1.md` and `.harness/REVIEWS/phase-0-research-skeptic.md`; update `.harness/TASKS.json` with a dependency-ordered Phase 1 graph and write `.harness/PLANS/phase-1-vertical-slice.md`, then append one action line to `LOG.md` and write `.harness/HANDOFFS/planner-to-red-team-P0-PL01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-planner-P0-PL01-1.md`
3. `.harness/DECISIONS/README.md`
4. `.harness/HANDOFFS/architect-to-planner-P0-AR01-1.md`
5. `.harness/REVIEWS/phase-0-research-skeptic.md`
6. `.harness/PROCESS.md`
7. `.harness/TASKS.json`

CONTEXT I WISH I HAD HAD: Approved OS/Python/Rust support floors, release channel, benchmark certification hardware and accessibility target. Where unresolved, plan the narrow conservative gate rather than assuming approval.

## Planning requirements

- Start with one demoable slice: a Python-created app opens a native window, renders text and a simple interactive control, handles a semantic event, updates state, and redraws without Python on the frame path.
- Sequence shared contracts before parallel work: crate/module boundaries, snapshot schema, handle semantics, error shape and benchmark interface.
- Split independent Rust modules only after their interfaces are fixed; avoid multiple agents editing the same manifest or public API.
- Acceptance criteria must name a test, benchmark threshold or command that exits zero. Examples: `cargo test -p pygpui-core`; `cargo clippy --workspace --all-targets -- -D warnings`; `mypy --strict --disallow-any-explicit`; a headless scene assertion; a zero-Python-callback sentinel test.
- Include Test-Engineer, independent Reviewer, Integrator, Perf-Engineer and Release/CI work in the graph, not as afterthoughts.
- Include rollback/revert boundaries and the four-attempt escalation rule.
- Keep performance targets unverified until the benchmark harness and approved environment exist.
- Do not authorize feature implementation in Phase 0; Phase 1 begins only after Red-Team review and Orchestrator approval.
