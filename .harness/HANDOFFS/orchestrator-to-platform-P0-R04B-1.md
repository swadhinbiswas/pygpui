FROM: Orchestrator
TO: Researcher-Platform instance B
TASK-ID: P0-R04B
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Research IME, focus, accessibility and delivery edge cases for RQ-04. Cover AccessKit integration, accessibility-tree ownership, IME lifecycle, keyboard behavior, abi3 wheel differences, CI/signing/notarization constraints and which steps need unavailable credentials.

WHAT I DID: Defined RQ-04 and marked credential-dependent release operations as blockers rather than assuming them.

EVIDENCE: `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`; `.harness/TASKS.json` task P0-R04B.

WHAT I DID NOT DO / SKIPPED, AND WHY: No signing/notarization or store operation has been attempted. No credentials or remote release infrastructure were provided.

OPEN RISKS & SURPRISES: Accessibility and IME require real OS integration tests; a headless render test cannot prove them.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-04-platform-input-accessibility-distribution.md`; research current primary AccessKit/winit/OS packaging sources, write `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md` with claim-level evidence labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-platform-to-skeptic-P0-R04B-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-platform-P0-R04B-1.md`
3. `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`
4. `.harness/PROCESS.md`
5. `.harness/OPEN_QUESTIONS.md`

CONTEXT I WISH I HAD HAD: Accessibility conformance target and who owns Apple/Windows signing credentials.
