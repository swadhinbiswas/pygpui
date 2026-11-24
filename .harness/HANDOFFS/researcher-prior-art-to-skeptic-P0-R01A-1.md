FROM: Researcher-Prior-Art instance A
TO: Skeptic
TASK-ID: P0-R01A
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Research current primary GPUI/Zed sources for RQ-01, concentrating on entity/view/window lifecycle, retained state, frame scheduling, actions/keymaps, Rust ownership of rendering, and clean-room/Apache-2.0 boundaries. Distinguish documented facts from inference and produce claim-level verified/plausible/unverified labels. Research only; no feature code or orchestration-state edits.

WHAT I DID: Pinned upstream `main` to `168964ea32451900149b5c15ccb2d515e4ecb936` (2026-11-24T07:24:54Z), inspected official docs and source in a sparse local checkout, and wrote the assigned report. Established the current immediate-tree/selective-retention model, app-owned entity and deferred-release lifecycle, non-owning window handles, dirty/draw/present separation, action/key-context dispatch, and Rust-owned scene pipeline. Reconciled older design posts with current source and investigated component licensing, NOTICE absence at the pinned snapshot, GPL `ui`/`workspace` boundaries, and the resolved historical `ztracing` GPL issue.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md`; `.harness/LOG.md`; pinned source URLs and claim IDs C-01 through C-32 in the report; local evidence checkout `/tmp/opencode/zed-gpui-168964e` with HEAD `168964ea32451900149b5c15ccb2d515e4ecb936`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No GPUI build, runtime experiment, or performance benchmark was run, so numerical targets and untested edge behavior remain unverified. No complete transitive dependency-license audit or jurisdiction-wide legal opinion was attempted; those exceed this task and remain explicit gaps. Cross-framework comparison was left to P0-R01B. No source code was copied, and no feature code, TASKS.json, STATE.md, or another agent's file was changed.

OPEN RISKS & SURPRISES: Current `main` still declares GPUI 0.2.2 although crates.io 0.2.2 was published 2025-10-22, so version alone is not a source anchor. Current source is more retained/adaptive than the 2023 “stateless DOM” and 2024 fixed pacing descriptions. The Python/Rust ownership split and minimum hybrid are plausible recommendations, not measured results. No NOTICE file exists at the pinned GPUI snapshot, but any actual distributed artifact and third-party dependency still needs rechecking. The old GPL `ztracing` allegation is stale for this commit, while the full dependency graph remains unaudited.

EXACT NEXT STEP: Read `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md` and the pinned sources; falsify or confirm claims C-01 through C-32, especially C-07/C-10 dependency tracking, C-12/C-17/C-24 architecture inferences, and C-25 through C-32 licensing boundaries; issue targeted Round 2 requests only where a decision could change.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md`
2. `.harness/RESEARCH/RQ-01-prior-art-architecture.md`
3. `.harness/HANDOFFS/orchestrator-to-prior-art-P0-R01A-1.md`
4. `.harness/PROCESS.md`
5. `.harness/OPEN_QUESTIONS.md`
6. `.harness/STATE.md`
7. `/tmp/opencode/zed-gpui-168964e/crates/gpui/src/view.rs`

CONTEXT I WISH I HAD HAD: The exact upstream commit is now fixed at `168964ea32451900149b5c15ccb2d515e4ecb936`. Source-level derivation remains unapproved under OQ-08; the conservative default is concept-only clean-room implementation. RQ-02 owns dependency/FFI selection and RQ-03 owns performance validation, so this report deliberately does not close those questions.
