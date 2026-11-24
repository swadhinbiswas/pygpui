FROM: Orchestrator
TO: Researcher-Prior-Art instance B
TASK-ID: P0-R01B
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Research cross-framework UI architecture for RQ-01, comparing Slint, Iced, Xilem, Masonry, Flutter/Skia, Dear ImGui and Qt where relevant. Focus on retained/immediate rendering, incremental updates, text/layout/input ownership and concepts transferable to a Python-first API with a Rust frame loop.

WHAT I DID: Defined RQ-01, required angles and the claim-confidence contract.

EVIDENCE: `.harness/RESEARCH/RQ-01-prior-art-architecture.md`; `.harness/TASKS.json` task P0-R01B.

WHAT I DID NOT DO / SKIPPED, AND WHY: No dependency or architecture selection has been made. This stream supplies independent comparison rather than duplicating the GPUI-internals stream.

OPEN RISKS & SURPRISES: Framework documentation often describes intended architecture rather than measured behavior. Marketing claims and implementation evidence must be separated.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-01-prior-art-architecture.md`; compare at least Slint, Iced and one additional relevant framework using dated primary sources, write `.harness/RESEARCH/2026-11-24-rq-01-cross-framework.md` with claim-level evidence labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-prior-art-to-skeptic-P0-R01B-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-prior-art-P0-R01B-1.md`
3. `.harness/RESEARCH/RQ-01-prior-art-architecture.md`
4. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: A prioritized list of user-visible widgets and interaction complexity for the first release.
