FROM: Researcher-Libs instance A
TO: Skeptic
TASK-ID: P0-R02A
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Investigate current exact candidate versions, licenses, compatibility, maintenance/release activity, known bugs/issues and platform gaps for winit, wgpu, taffy, cosmic-text, accesskit, rustc-hash and slotmap; separate first vertical-slice requirements from deferred components; produce claim-labelled primary-source research without implementation.

WHAT I DID: Queried crates.io metadata, published manifests, repository/release pages, documentation and primary issue trackers on 2026-11-24. Built an external scratch resolver probe with exact pins and target-specific wgpu features; resolved Windows x64, macOS arm64 and Linux x64 metadata; ran a locked Linux cargo check; reproduced two Taffy 0.16.0 failures locally; documented licenses, stale/contradictory evidence, a narrow baseline, rejected alternatives and validation gates.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-02-core-rust-stack.md`; scratch probe `/tmp/opencode/rq02a-resolve/Cargo.toml`; local Taffy probe `/tmp/opencode/rq02a-resolve/src/bin/taffy_issue_probe.rs`; `LOG.md` start and completion entries for P0-R02A.

WHAT I DID NOT DO / SKIPPED, AND WHY: No feature code, workspace dependency manifest, TASKS.json/STATE.md edit, commit, wheel build, Windows/macOS compile or runtime test, rendering benchmark, complete transitive NOTICE audit, or legal opinion was produced. This was research-only; cross-platform runtime and distribution questions remain explicit gates rather than inferred facts.

OPEN RISKS & SURPRISES: Taffy 0.16.0 was one day old and locally reproduced flex aspect-ratio and stale-hoisted-child failures. wgpu 30 has an open presentation regression report, an NVIDIA Linux GLES issue and a DX12 unaligned-copy allocator leak. winit has open X11/Windows IME gaps and unresolved Wayland/LGPL protocol metadata. cosmic-text 0.19.0 has open monospace-performance and custom-renderer borrow issues. AccessKit has open virtualized-list metadata, scroll-diff performance and empty-text-run hang reports. slotmap 1.1.1 has an acknowledged extreme-capacity safe-API soundness issue. The direct MSRV maximum is 1.89, but the resolved graph requires at least 1.90 through ordered-float; only rustc/cargo 1.100.0 was tested.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `.harness/RESEARCH/2026-11-24-rq-02-core-rust-stack.md`; falsify the exact-version, compatibility, issue-status, license and slice claims, record claim-by-claim dispositions, and append one action line to `LOG.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/researcher-libs-to-skeptic-P0-R02A-1.md`
3. `.harness/RESEARCH/2026-11-24-rq-02-core-rust-stack.md`
4. `.harness/PROCESS.md`
5. `.harness/RESEARCH/RQ-02-dependency-and-distribution-stack.md`
6. `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md`
7. `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md`

CONTEXT I WISH I HAD HAD: The project's minimum supported Rust version; whether distribution must exclude all copyleft/mixed-license content; the formal acceptance scope of the first vertical slice; whether Web/mobile are confirmed non-goals; and the certified OS/GPU/driver/present-mode benchmark matrix.
