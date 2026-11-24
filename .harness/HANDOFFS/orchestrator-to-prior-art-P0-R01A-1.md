FROM: Orchestrator
TO: Researcher-Prior-Art instance A
TASK-ID: P0-R01A
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Research GPUI/Zed internals and clean-room boundaries for RQ-01, concentrating on primary GPUI architecture: entity/view/window lifecycle, retained state, frame scheduling, actions/keymaps and Rust ownership of per-frame work. This is read-only research apart from the explicitly assigned harness outputs.

WHAT I DID: Defined RQ-01 and the Phase 0 evidence rules; verified the workspace began empty.

EVIDENCE: `.harness/RESEARCH/RQ-01-prior-art-architecture.md`; `.harness/PROCESS.md`; `.harness/TASKS.json` task P0-R01A.

WHAT I DID NOT DO / SKIPPED, AND WHY: No architecture decision has been made and no source has been copied. Research must precede design.

OPEN RISKS & SURPRISES: The mission text ends at the Phase 0 heading. GPUI is Apache-2.0, but concept reuse and source derivation must be distinguished carefully.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-01-prior-art-architecture.md`; research primary GPUI/Zed sources, write `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md` with claim-level evidence labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-prior-art-to-skeptic-P0-R01A-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-prior-art-P0-R01A-1.md`
3. `.harness/RESEARCH/RQ-01-prior-art-architecture.md`
4. `.harness/PROCESS.md`
5. `.harness/OPEN_QUESTIONS.md`

CONTEXT I WISH I HAD HAD: Exact upstream commit/tag to anchor comparisons, and whether the user expects source-level derivation or concept-only inspiration.
