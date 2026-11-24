FROM: Researcher-Platform instance B
TO: Skeptic
TASK-ID: P0-R04B
ATTEMPT #: 1
STATUS: done

## Part 3

**WHAT I WAS ASKED:** Research current primary evidence for IME lifecycle, focus/keyboard behavior, AccessKit integration and accessibility-tree ownership, abi3 wheel differences across macOS/Windows/Linux, CI runners, code signing/notarization and Linux packaging. Separate technical requirements from credential-dependent blocked operations, recommend platform-specific integration tests and conservative release defaults, and label every decision-driving claim verified/plausible/unverified.

**WHAT I DID:** Wrote `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md` with 28 labelled claims, 39 dated/versioned primary sources, explicit technical-versus-blocked tables, an IME/focus contract, an AccessKit ownership recommendation, proposed wheel tags, a CI runner matrix, platform-specific test gates and a conservative first-release support policy. Highlighted current open winit issues #4508, #4807 and #4626; AccessKit issue #840; stable-winit focus-transfer sequencing; UTF-8 preedit offsets; abi3/free-threaded limits; Apple/Windows signing requirements; PyPI Trusted Publishing; and the distinction between a manylinux wheel and a standalone Linux desktop package.

**EVIDENCE:** `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md`; `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`; `.harness/HANDOFFS/orchestrator-to-platform-P0-R04B-1.md`; `.harness/STATE.md`; `.harness/PROCESS.md`.

**WHAT I DID NOT DO / SKIPPED, AND WHY:** No feature code, `TASKS.json`/`STATE.md` edits, commits, wheel builds, CI execution, signing, notarization, store submission or publishing. This was research-only and Phase 0 forbids implementation. No Apple/Windows/PyPI/store credentials, Git remote or interactive certification runners were provided, so those operations remain explicitly blocked rather than assumed.

**OPEN RISKS & SURPRISES:** Real IME and assistive-technology behavior cannot be proven by headless tests. Current winit documentation and Windows behavior conflict; macOS has open commit-loss and teardown-abort reports; AccessKit adapters remain best-effort with platform-specific gaps; historical Unix lazy-activation behavior needs re-testing on the pinned version. The proposed support floor and Python range are plausible policy choices, not tested compatibility. Final OS/Python/dependency choices require reconciliation with P0-R04A and P0-R02A/B. Credential ownership, accessibility conformance target, physical test hardware and the standalone-app bundling decision remain unknown.

**EXACT NEXT STEP:** Read `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md` and the other RQ-04 output; falsify each decision-driving claim, check issue/source freshness, distinguish documented guarantees from integration inferences, and issue a claim-by-claim verified/plausible/unverified disposition with targeted Round 2 tasks only where the architecture or release decision would change.

**FILES THE RECEIVER MUST READ (ordered, max 7):**
1. `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md`
2. `.harness/RESEARCH/RQ-04-platform-input-accessibility-distribution.md`
3. `.harness/HANDOFFS/orchestrator-to-platform-P0-R04B-1.md`
4. `.harness/PROCESS.md`
5. `.harness/STATE.md`
6. `.harness/RESEARCH/PHASE0-MANIFEST.md`

**CONTEXT I WISH I HAD HAD:** The user-approved accessibility conformance target and supported assistive technologies; the owner of Apple Developer ID/notary and Windows Authenticode credentials; physical Mac/Windows/Linux machines with configured IMEs and screen readers; the final OS/Python support floor; and whether the first user-facing release is a Python library or a separately bundled desktop application.
