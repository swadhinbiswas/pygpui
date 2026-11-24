FROM: Researcher-Prior-Art instance B
TO: Skeptic
TASK-ID: P0-R01B
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Research cross-framework UI architecture for RQ-01, comparing Slint, Iced, Xilem/Masonry, Flutter and Dear ImGui where relevant, with focus on retained versus immediate rendering, incremental updates, layout/text/input ownership, Python-first API transfer, Rust-owned frames, documentation intention versus implementation evidence, and clean-room boundaries.

WHAT I DID: Read `.harness/STATE.md`, the orchestrator handoff, `.harness/RESEARCH/RQ-01-prior-art-architecture.md`, and `.harness/PROCESS.md`; appended the required start line quoting the handoff's exact next step; reviewed pinned primary documentation/source snapshots for Slint, Iced, Xilem/Masonry, Flutter, and Dear ImGui; compared their retained state, reconciliation, invalidation, text/input ownership, and render-loop boundaries; recorded claim-level `verified` / `plausible` / `unverified` labels, contradictions, recommendations, and exact evidence gaps. Qt was intentionally omitted because it did not change the architecture decision; Dear ImGui was included as the immediate-mode contrast.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-01-cross-framework.md`. Primary snapshots: Slint `70067e98eac2870d2ed11510134d518b51e5ea13` (2026-11-24), Iced `98bd48fe011efc0ec5819fee0fa7673a7169ff11` (2026-11-19), Xilem/Masonry `9a78df878a9269a88325ebd71f3f68c757f0a396` (2026-11-22), Flutter `c0b4744c302be253e6cececa7b553baa32e44543` (2026-11-24), and Dear ImGui `bd4e3b0abccd653490d68beeb72f0750cde6d5f6` (2026-11-23), with exact line-linked citations and license texts in the research file.

WHAT I DID NOT DO / SKIPPED, AND WHY: No feature code, dependency selection, renderer/text-engine selection, FFI design, benchmark, commit, or edits to `TASKS.json`, `STATE.md`, or another researcher's file. GPUI-specific clean-room analysis belongs to the GPUI-internals stream. Qt was not researched because the retained scene-graph category was already evidenced by Slint, Iced, Xilem/Masonry, and Flutter; reopen it only if Qt integration or licensing becomes decision-relevant. Current repository heads were used as dated evidence snapshots, not as verified release-package contents.

OPEN RISKS & SURPRISES: Documentation shorthand often overstates implementation behavior: Slint's partial renderer does not imply partial pixels under its default `NewBuffer`; Iced retains state but still calls root layout/draw on its build/draw paths; Masonry caches scenes and uses dirty passes but explicitly lacks damage regions; Dear ImGui now has an experimental window skip-refresh path despite its immediate API. The 2026-11-22 Xilem ZStack fix is concrete evidence that dynamic splice ordering and stale identity remain correctness-critical. All pygpui performance targets remain unverified. Slint's triple license must not be treated as Apache-2.0. No source code was copied.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/RESEARCH/2026-11-24-rq-01-cross-framework.md`, `.harness/RESEARCH/RQ-01-prior-art-architecture.md`, the GPUI-internals research file, and `.harness/PROCESS.md`, then review all eight Round 1 research files; falsify claims C-XC-03/C-XC-04, C-SL-06/C-XM-02/R2, R4, R5 and R6, check cited commit dates and line anchors, write `.harness/REVIEWS/phase-0-research-skeptic.md` with a claim-by-claim verified/plausible/unverified disposition and only decision-changing Round 2 requests, then append one action line to `LOG.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/researcher-prior-art-to-skeptic-P0-R01B-1.md`
3. `.harness/RESEARCH/2026-11-24-rq-01-cross-framework.md`
4. `.harness/RESEARCH/RQ-01-prior-art-architecture.md`
5. `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md`
6. `.harness/PROCESS.md`
7. `.harness/TASKS.json` task P0-SK01

CONTEXT I WISH I HAD HAD: The prioritized first-release widget set and interaction complexity, target platforms, candidate renderer/text-stack shortlist, FFI constraints, project licensing posture, and a certified benchmark hardware/software stack.
