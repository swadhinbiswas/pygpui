FROM: Orchestrator
TO: Researcher-Platform instance A
TASK-ID: P0-R04A
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Research desktop windowing/rendering constraints for RQ-04: Wayland vs X11, Windows DX12 vs Vulkan, macOS Metal, HiDPI scaling, winit event semantics and wgpu surface/adapter limitations. Recommend a narrow initial platform baseline with evidence.

WHAT I DID: Defined RQ-04 and separated runtime platform issues from IME/accessibility/distribution issues.

EVIDENCE: `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`; `.harness/TASKS.json` task P0-R04A.

WHAT I DID NOT DO / SKIPPED, AND WHY: No platform support claim has been made. This environment is Linux and cannot by itself verify macOS or Windows behavior.

OPEN RISKS & SURPRISES: Backend availability, driver behavior and OS window-system semantics differ. Documentation support does not equal integration correctness.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-04-platform-input-accessibility-distribution.md`; research current primary winit/wgpu/OS documentation and known issues, write `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md` with claim-level evidence labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-platform-to-skeptic-P0-R04A-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-platform-P0-R04A-1.md`
3. `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`
4. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Required minimum OS releases and whether X11-only Linux support is acceptable initially.
