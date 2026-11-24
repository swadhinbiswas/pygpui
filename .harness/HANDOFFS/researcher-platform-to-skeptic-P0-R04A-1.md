FROM: Researcher-Platform instance A
TO: Skeptic
TASK-ID: P0-R04A
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Research desktop windowing/rendering constraints for RQ-04: Wayland vs X11, Windows DX12 vs Vulkan, macOS Metal, HiDPI scaling, winit event semantics and wgpu surface/adapter limitations. Recommend a narrow initial platform baseline with evidence.

WHAT I DID: Checked current stable crate/release metadata and pinned primary winit 0.30.13/wgpu 30.0.2 sources, OS documentation, Wayland protocol XML and tracked issues through 2026-11-24. Produced a claim ledger with verified/plausible/unverified labels, separated upstream support from pygpui integration correctness, recorded Linux-only host observations, identified stable-release/trunk contradictions, and proposed a conservative OS/backend matrix plus common and per-platform release gates. No feature code was written.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md`; `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`; `.harness/TASKS.json` task P0-R04A; primary source and issue URLs are registered in the research file. Local evidence is limited to `uname`, `/etc/os-release`, session environment, tool availability and `vulkaninfo --summary` on CachyOS/Hyprland with RTX 3060 Ti + Intel RPL-S GPUs.

WHAT I DID NOT DO / SKIPPED, AND WHY: No macOS or Windows build, launch, display, input, driver, signing or notarization test was possible on this Linux host. No winit/wgpu application or temporary integration program was run, so the pinned pair and every pygpui runtime claim remain unverified. No feature code, TASKS.json/STATE.md edits or commits were made. GitHub's unauthenticated API rate-limited partway through issue enumeration; linked primary issue pages were then checked directly, and issue state remains mutable.

OPEN RISKS & SURPRISES:
- wgpu 30.0.2 still contains the Metal pre-visible occlusion check fixed by PR #10302 on trunk; merge date precedes the stable release, but the v30.0.2 tag/changelog does not contain the fix. macOS first-frame behavior is a blocking test, not a verified capability.
- wgpu #9937 is an open 29→30 presentation-cost report on Windows Vulkan and Linux RADV; DX12/Metal were not tested in the original report. No performance target is established.
- winit #4668 is open/disputed: `Poll` can spin while a Wayland redraw waits on a withheld frame callback, and Wayland `Occluded` is unsupported in 0.30.13. The release loop must not depend on indefinite `Poll`.
- Stable winit has open IME correctness/teardown issues on Windows/macOS; disabling IME before macOS window destruction is a documented workaround for #4626, not an upstream fix.
- wgpu's native initialization order is Vulkan → Metal → DX12 → GL, so DX12 is not an implicit Windows default when all backends are enabled. Explicit backend masks are required for deterministic claims.
- The proposed minimums are deliberately narrow: Ubuntu 24.04 LTS x86-64 GNOME with Wayland + Xorg/Vulkan; Windows 11 25H2+ x86-64/DX12; macOS 26 Apple silicon/Metal. User approval and real platform tests are still required.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md`, `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`, `.harness/RESEARCH/PHASE0-MANIFEST.md`, the other RQ-04 researcher's output when present, and `.harness/PROCESS.md`; falsify the decision-driving claims C01–C34 and issues I1–I14, prioritizing the wgpu 30.0.2 Metal fix/backport discrepancy, backend-selection order, surface-status policy, Wayland callback semantics and the narrow OS matrix; then write `.harness/REVIEWS/phase-0-research-skeptic.md` with claim-level dispositions and any decision-changing Round 2 requests, append one action line to `LOG.md`, and write `.harness/HANDOFFS/skeptic-to-architect-P0-SK01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/researcher-platform-to-skeptic-P0-R04A-1.md`
3. `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md`
4. `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`
5. `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md` (when present)
6. `.harness/RESEARCH/PHASE0-MANIFEST.md`
7. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Available physical macOS/Windows test hardware and GPU-backed CI; whether users require macOS 15/Intel, Windows 10/ARM or non-Ubuntu Linux; whether HDR, transparency, multi-window, multi-GPU switching or exclusive fullscreen are first-release requirements; and which DX12 shader compiler/package-size tradeoff the project prefers.
