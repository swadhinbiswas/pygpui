# Phase 0 research — Skeptic disposition

- Task: `P0-SK01`, attempt 1
- Reviewer: Skeptic
- Review date: 2026-11-24 UTC
- Reviewed baseline: committed Round 1 research at `cc378c2`
- Status: **done**
- Round 2 research requested: **none**

## 1. Scope and method

I read `.harness/STATE.md`, the assigned Orchestrator handoff, `.harness/RESEARCH/PHASE0-MANIFEST.md`, all eight Round 1 research files, and all eight researcher handoffs. I also read the four canonical RQ briefs, `.harness/PROCESS.md`, `.harness/OPEN_QUESTIONS.md`, `.harness/TASKS.json`, and the Phase 0 plan to distinguish research facts from product-policy choices.

This is a falsification review, not a summary. I:

1. Checked exact release metadata and manifests against crates.io for the selected Rust and Python tooling.
2. Re-ran the existing external resolver probe and both Taffy failure probes; independently checked all three target metadata results and the Linux `cargo check --locked --all-targets`.
3. Spot-checked decision-critical pinned source: GPUI lifecycle/cache/frame code, Slint partial rendering, Iced build/draw paths, the Xilem ZStack fix, PyO3 0.30.1 attachment/GIL code, wgpu 30.0.2 surface/backend code, winit 0.30.13 IME/event code, AccessKit adapter/activation contracts, cosmic-text 0.19.0 cache APIs, and the Wayland protocol-license discrepancy.
4. Checked mutable primary issue pages for the slotmap soundness report, winit Wayland licensing and IME reports, cosmic-text's renderer-borrow report, AccessKit virtualization metadata, and the wgpu Metal first-frame fix/backport discrepancy.
5. Checked benchmark-boundary primary sources, including PresentMon 2.3.1, wgpu presentation semantics, CPython threading APIs, and the protocol's arithmetic/ABBA rules.
6. Reconciled every item on the manifest's Pre-Skeptic watchlist and several additional cross-stream conflicts.

Final disposition meanings:

- **verified** — supported by a dated primary source, pinned source, or reproduced local observation. This verifies the stated mechanism/fact, not pygpui's future behavior.
- **plausible** — a defensible design inference or policy choice, but not established for pygpui. It may drive an ADR only with an explicit risk and validation task.
- **unverified** — a target, assumption, estimate, untested integration, or unsupported wording. It must not silently become an accepted fact.

Unnumbered RQ-02A/RQ-03B/RQ-04B material is accounted for by explicit contiguous line ranges in the matrices below. All numbered architecture-driving claims are covered by ID or contiguous ID ranges.

## 2. Source freshness and primary-source support

### 2.1 Exact selected releases

The following release facts were independently confirmed from crates.io on 2026-11-24:

| Component | Confirmed release | Confirmed metadata relevant to the decision |
|---|---|---|
| `winit` | 0.30.13, 2026-03-02 | Apache-2.0; declared Rust 1.70; `rwh_06`, X11 and Wayland features |
| `wgpu` | 30.0.2, 2026-11-12 | MIT OR Apache-2.0; Rust 1.87; `raw-window-handle` 0.6 family |
| `taffy` | 0.16.0, 2026-11-23 | MIT; Rust 1.85; edition 2024 |
| `cosmic-text` | 0.19.0, 2026-04-22 | MIT OR Apache-2.0; Rust 1.89 |
| `accesskit` | 0.25.2, 2026-10-25 | MIT OR Apache-2.0; Rust 1.87 |
| `accesskit_winit` | 0.34.2, 2026-10-25 | Apache-2.0; Rust 1.87; depends on `winit ^0.30.5`, `accesskit ^0.25.2` |
| `rustc-hash` | 2.1.3, 2026-07-02 | Apache-2.0 OR MIT; Rust 1.77 |
| `slotmap` | 1.1.1, 2025-12-06 | Zlib; Rust 1.58 |
| `pyo3` | 0.30.1, 2026-10-14 | MIT OR Apache-2.0; Rust 1.85 |
| `maturin` | 1.16.0, 2026-10-29 | MIT OR Apache-2.0; Rust 1.89 to build |

The exact dependency-only probe at `/tmp/opencode/rq02a-resolve` resolved:

- `x86_64-pc-windows-msvc`: 126 packages
- `aarch64-apple-darwin`: 138 packages
- `x86_64-unknown-linux-gnu`: 206 packages

All three selected the exact direct versions above plus `ordered-float 5.5.1`, whose published manifest declares Rust 1.90. Therefore the resolved graph has an effective floor of **at least Rust 1.90**, not 1.89. Only rustc/cargo 1.100.0 was tested; no minimum-Rust support promise is established.

The Linux locked check passed again during this review. Both Taffy probes failed exactly as reported:

- flex aspect-ratio child: `500x0`, expected `500x250`;
- popup removal: panic `invalid SlotMap key used`.

### 2.2 Version-skew resolutions

| Skew | Resolution | Decision effect |
|---|---|---|
| RQ-03A cites PyO3 0.27.0; RQ-02B selects 0.30.1 | PyO3 0.30.1's pinned `src/marker.rs` and versioned guide retain the relevant mechanics: `Python::attach` may create/destroy a thread state and block; `detach` releases attachment and reacquires on scope exit, including panic unwind. The 0.30 guide also confirms the 0.28+ `gil_used = false` default. | The callback-free conditions remain valid, but 0.30.1 source must govern implementation. |
| RQ-03A cites winit 0.30.12; selected version is 0.30.13 | The 0.30.13 source still defines `ControlFlow::{Poll, Wait, WaitUntil}` and the same redraw-request model. The patch did not invalidate the cost model. | No architecture change. |
| RQ-03A cites wgpu 30.0.0/living docs; selected version is 30.0.2 | The exact v30.0.2 source confirms `CurrentSurfaceTexture`, `Queue::present`, FIFO semantics, nonzero surface extents, and the Metal drawable-count mapping. | No architecture change; use v30.0.2 API text. |
| RQ-03A's cosmic-text cache sources are commit `b07cb90` (2026-10-27), while RQ-02A selects crate 0.19.0 | The compare spans 28 commits, but the specific `ShapeRunCache`, glyph-cache key/subpixel-bin, and `FontSystem::new` timing statements used by RQ-03A are present in the 0.19.0 tag. | No decision change. Do not cite later-trunk behavior as released behavior. |
| RQ-04B labels winit 0.30.13 docs.rs pages as “published 2026-11-16” | crates.io and the release tag show 2026-03-02; 2026-11-16 is the docs.rs build date. | Metadata correction only. |
| GPUI package version remains 0.2.2 while crates.io 0.2.2 dates from 2025 | Only commit `168964ea32451900149b5c15ccb2d515e4ecb936` identifies the reviewed source. | Never use “GPUI 0.2.2” alone as a source anchor. |

### 2.3 Mutable and living evidence

Open issues verify that a problem was reported and remained open on the access date; they do not prove universal applicability. I independently confirmed the key reports used to constrain claims: slotmap #168, winit #4833/#4839/#4843, cosmic-text #543, AccessKit #871, and wgpu #9430/PR #10302.

Living documentation is used only where a versioned source or exact protocol backs the decision. Cross-framework RQ-01B snapshots are current repository commits, not release-package claims; that is acceptable for concept selection but not for dependency/version assertions.

## 3. Cross-stream reconciliation

| Watchlist / conflict | Skeptic resolution | Status |
|---|---|---|
| PyO3 0.27 versus 0.30.1 | Relevant attach/detach/GIL mechanics survive in 0.30.1. Use 0.30.1 documentation and source. | Resolved |
| winit 0.30.12 / wgpu 30 docs versus selected pins | Use winit 0.30.13 and wgpu 30.0.2. Exact resolver and API source agree. | Resolved |
| `macosx_11_0_universal2` candidate versus macOS 26 support floor | A wheel's deployment target is not a support promise. Reject the 11.0 universal2 candidate for the first release. If macOS ships, use a tested macOS 26 deployment target; conservative first matrix is `macosx_26_0_arm64`. Use `macosx_26_0_universal2` only after both architectures pass. | Resolved as policy default |
| AccessKit 0.25.2 / adapter 0.34.2 / winit 0.30.13 | Exact pair is compatible and resolves with winit 0.30.13. Keep AccessKit's optional `pyo3` feature disabled: it requires `pyo3 ^0.29`, which does not accept the selected 0.30.1. | Resolved |
| RQ-01A full-window rebuild versus RQ-01B event-driven patches | These are complementary phases, not competing first-slice contracts. Slice 1 accepts a complete immutable Rust-owned snapshot on each semantic change and rebuilds the affected window in Rust. Stable IDs preserve interaction state. Incremental typed patches and cached subtrees come later, only if measurements justify them. | Resolved |
| RQ-01A “hybrid immediate/retained” versus RQ-01B “retained Rust entity tree” | “Retained” refers to different layers. Python descriptions may be ephemeral; Rust runtime nodes, element state, geometry and scene data are retained. There is no requirement for a persistent Python VDOM. | Resolved |
| RQ-03A “persistent native thread” versus RQ-02B/RQ-04A platform-main-thread event loop | The native runtime may run on the platform main thread; “native thread” does not require spawning a worker. Slice 1 uses one Rust-owned main-thread winit loop, with no render worker. Any later worker must pass platform lifetime/thread tests and still satisfy the callback counters. | Resolved conservatively |
| RQ-03A input-to-frame wording versus RQ-03B | Reject “first submitted frame that visibly responds” as ambiguous. Adopt RQ-03B: OS input-stack receipt to first **presented** frame containing the response token. Input-to-photon is separate. | Resolved |
| RQ-02A enables Linux GLES; RQ-04A claims Vulkan-only | Compile/select Vulkan only for the first Linux baseline. GLES remains deferred and unclaimed. The successful resolver probe with GLES is compatibility evidence, not a support decision. | Resolved conservatively |
| RQ-04A `desired_maximum_frame_latency = 2` versus RQ-03B macOS `maximumDrawableCount = 2` | wgpu maps desired latency 2 to Metal `maximumDrawableCount = 3`. The benchmark must use the same configuration as the runtime. Default to 3; a 2-drawable latency experiment must set desired latency 1 and be named separately. | Resolved conservatively |
| AccessKit requires an initially invisible window; wgpu 30.0.2 Metal withholds pre-visible drawables | With the accessibility adapter, create invisible → attach adapter → show → present, or use a separately tested workaround. Do not promise a pre-show first frame on stable 30.0.2. macOS support remains gated on this sequence and wgpu #9430's absent backport. | Resolved as release gate |
| RQ-02A defers accessibility integration; RQ-04B assigns Rust ownership from the start | Design stable accessibility identity/semantic snapshot hooks early, but defer the platform adapter dependency until after the first render/text slice. No accessibility claim before adapter and AT tests. | Resolved |

## 4. Disposition matrix

### 4.1 RQ-01A — GPUI internals

Source: `.harness/RESEARCH/2026-11-24-rq-01-gpui-internals.md`.

| Claim IDs | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| C-01–C-07 | **verified** | Pinned local source confirms app-owned entities, typed handles, leases, coalesced effects, deferred release, non-owning window handles, and per-window accessed-entity invalidation. Spot checks: `app.rs:2254-2363`, `entity_map.rs:250-313,440-464`, `view.rs:520-649`. | Supports Rust ownership, generation-safe handles, weak subscriptions and deterministic teardown. |
| C-08–C-11 | **verified** | Ephemeral element pass, keyed element state, opt-in cached view subtrees, and retained paint scene are distinct in source. `element.rs`, `view.rs:535-649`, `scene.rs:50-129`. | Supports immediate descriptions plus selective Rust retention; not a persistent Python VDOM. |
| C-12 | **plausible** | The layers coexist in GPUI; pygpui's minimum slice is an inference. | Adopt only as the conservative first-slice model. |
| C-13–C-16 | **verified** | `window.rs:1925-2139` confirms reentrancy deferral, distinct draw/present/callback demand, adaptive scheduling and follow-up frames. Historical blog is correctly subordinated to current source. | Supports a demand-driven native scheduler. |
| C-17 | **plausible** | Source shows compatibility, not Python-boundary feasibility. | ADR invariant plus benchmark proof required. |
| C-18 | **unverified** | No GPUI or pygpui benchmark was run. | No performance claim. |
| C-19–C-23 | **verified** | Typed actions, rendered focus/context dispatch, unstable dispatch-node IDs, capture/bubble routing, Taffy layout and Rust-owned scene handoff are source-backed. | Supports Rust keymap/focus/layout/render ownership. |
| C-24 | **plausible** | Sound ownership recommendation; no pygpui implementation. | May drive ADR with validation task. |
| C-25–C-29 | **verified** | U.S. idea/expression distinction is correctly qualified; Apache-2.0 conditions, pinned GPUI license, NOTICE absence, mixed Zed licensing, and the resolved `ztracing` path are supported. | Supports concept-only clean-room default and provenance rules. |
| C-30 | **plausible** | Conservative process policy, not a legal guarantee. | Adopt as risk control. |
| C-31 | **verified** | Copying/adapting source triggers Apache-2.0 conditions. | No source-derived exception without provenance. |
| C-31a | **plausible** | Conservative treatment of translated expression. | Use as process guidance, not legal holding. |
| C-32 | **unverified** | Full GPUI transitive graph was not audited. | Blocks distribution if GPUI source/binary is linked; not concept reuse. |

### 4.2 RQ-01B — cross-framework prior art

Source: `.harness/RESEARCH/2026-11-24-rq-01-cross-framework.md`.

| Claim IDs | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| C-SL-01–C-SL-05 | **verified** | Pinned Slint source/docs support retained items, lazy dependency-tracked properties, optional partial rendering, Rust-local text editing, and render-phase IME side effects. `RepaintBufferType::NewBuffer` is the default. | Do not infer pixel damage from a retained tree; keep Python out of paint. |
| C-SL-06 | **plausible** | `ItemWeak` lacks the proposed public generation/type/window envelope; the inference is about pygpui's API. | Supports stronger opaque handles. |
| C-IC-01–C-IC-03 | **verified** | Iced source confirms tag/state reconciliation, root layout on build, root draw on draw, and Rust-owned editing/text caches. | Retained state does not imply skipped traversals. |
| C-IC-04 | **plausible** | Controlled-input transaction pattern transfers reasonably; no FFI proof. | Validate with Rust-local editor/Python document synchronization. |
| C-XM-01–C-XM-06 | **verified** | Xilem/Masonry source and commit `9a78df8` confirm lifecycle split, generations, bounded rewrite passes, Rust focus/IME/text ownership, no damage regions, and the ZStack splice-order defect. | Supports phase pipeline and property tests for reorder/teardown. |
| C-FL-01–C-FL-03 | **verified** | Pinned Flutter source supports configuration/runtime separation, dirty queues and retained text/input routing. | Supports declarative-over-retained architecture. |
| C-FL-04 | **plausible** | Mutation guards are a useful model, not a pygpui requirement. | Make legal mutation phases explicit. |
| C-DI-01–C-DI-03 | **verified** | Dear ImGui retains substantial state and has experimental skip-refresh despite an immediate API. | Immediate API and incremental implementation are orthogonal. |
| C-XC-01–C-XC-02 | **verified** | Counterexamples establish the distinctions; reviewed runtimes keep layout/text/input in the UI runtime. | Supports Rust-owned frame pipeline. |
| C-XC-03–C-XC-04 | **plausible** | Exact Python/Rust boundary is not demonstrated by another framework. | Adopt as hypothesis with callback counters and API prototype. |
| C-XC-05 | **unverified** | No comparable pygpui workload or benchmark. | No target claim. |
| R1–R6 | **plausible** | Architecture recommendations synthesized from verified mechanisms. | May drive ADRs only with risks and validation tasks. |
| R7 | **verified process / plausible risk guidance** | No source was copied; file-level licenses differ. | Maintain provenance; no legal sign-off implied. |

### 4.3 RQ-02A — core Rust stack

Source: `.harness/RESEARCH/2026-11-24-rq-02-core-rust-stack.md`.

| Line range / section | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| 17–57, executive decision and inventory | **verified facts / plausible selection** | Exact versions, dates, licenses and declared MSRVs confirmed; maintenance health remains a judgment. | Pins are usable; adoption is not a runtime support claim. |
| 59–94, resolver and constraints | **verified** | Independently reproduced 126/138/206-package target results, exact pins, `rwh_06` family, dual rustc-hash majors, and effective Rust ≥1.90. Linux check passed. | Resolver compatibility established for tested feature set only. |
| 98–117, winit | **verified reports / plausible recommendation / unresolved legal effect** | Release fixes and issue pages confirmed; #4839 and #4843 remain open. Wayland XML carries LGPL text despite MIT crate metadata; #4833 is unresolved. | Use 0.30.13; no complete IME or permissive-only Wayland claim. |
| 119–136, wgpu | **verified reports / plausible recommendation** | v30.0.2 fixes and API confirmed. #9937 applicability to 30.0.2 and target backends remains untested. | Use 30.0.2 with explicit masks and present-path gate. |
| 138–153, Taffy | **verified defects / plausible recommendation** | Both reported failures reproduced locally on 0.16.0. README benchmark is stale and layout-only. | Constrain slice 1 to tested in-flow flex/block; no CSS/full-layout claim. |
| 155–171, cosmic-text | **verified mechanism/reports / plausible recommendation** | 0.19.0 APIs exist; #543 confirmed open; #518/#499 applicability untested here. | Prototype atlas adapter; explicit font family for performance-sensitive monospace. |
| 173–185, AccessKit | **verified contracts/reports / unverified integration** | Adapter/activation contracts confirmed; #871 confirmed open. | Defer adapter; no virtualized-list accessibility claim. |
| 187–195, rustc-hash | **verified docs/report / unverified performance** | #45 is a real reported pattern hazard; no project benchmark. | Internal trusted keys only; avoid map-to-map insertion-order rebuild. |
| 197–207, slotmap | **verified soundness report / plausible mitigation** | #168 independently confirmed: safe-API UB near `u32::MAX`, acknowledged by owner. | Hard-cap node count far below limit; avoid detach/reattach; stale-key tests mandatory. |
| 209–230, slice definition | **plausible** | Dependency roles are verified; the vertical-slice boundary is a recommendation. | Use as planning default, not evidence of feasibility. |
| 232–240, licenses/NOTICE | **verified direct scope / unverified transitive closure** | No NOTICE files in the eight direct crate sources; Wayland mixed-license content independently confirmed. | Full artifact audit before distribution remains mandatory. |
| 253–295, baseline and alternatives | **verified compatibility / plausible selection** | Exact graph resolves; preference among candidates is engineering judgment. | Architect may adopt with constraints. |
| 297–307, validation tasks | **unverified results** | No cross-platform runtime, wheel, benchmark or complete audit exists. | Convert to Phase 1/release gates. |

### 4.4 RQ-02B — Python ABI, typing and delivery

Source: `.harness/RESEARCH/2026-11-24-rq-02-python-abi3-typing.md`.

| Claim IDs | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| C01 | **verified** | PyO3 0.30.1 and maturin 1.16.0 metadata confirmed. | Exact pins usable. |
| C02 | **plausible** | CPython ≥3.11 is a product choice. | Provisional policy only. |
| C03–C09 | **verified** | Stable ABI, 3.13t drop, 3.14t/3.15 `abi3t` distinction, one ABI family per build, OS-specific artifacts, and `gil_used` default are primary-source backed. | GIL-enabled `abi3-py311` is technically coherent. |
| C10 | **plausible** | Conservative safety policy; no pygpui audit. | Use `gil_used = true`; no free-threaded support claim. |
| C11 | **verified** | Confirmed in PyO3 0.30.1 source/guide. | Native-only work can run detached. |
| C12–C15 | **plausible** | Deadlock and event-boundary design inferences; no implementation. | ADR invariants plus tests required. |
| C16 | **unverified** | No benchmark or callback proof. | No performance guarantee. |
| C17–C21 | **verified** | Generator existence/limitations, `py.typed`, mypy strict flags and `stubtest` scope are documented. | Manual reviewed stubs remain source of truth. |
| C22 | **plausible** | Small opaque facade is a design choice. | Validate against OQ-05 API. |
| C23–C25 | **verified** | Async constraints and candidate version confirmed. | No default async runtime. |
| C26 | **plausible** | Main-thread co-driving risk is real but unmeasured. | Defer UI async integration. |
| C27 | **verified** | `call_soon_threadsafe` semantics confirmed; it does not solve co-driving. | Optional later adapter only. |
| C28–C31 | **verified** | Maturin platform/repair/ad-hoc signing scope confirmed. | Wheels are buildable in principle; signing is separate. |
| C32 | **unverified** | No production OS signing pipeline was established. | Treat as unsupported. |
| C33–C36 | **verified** | Apple/Microsoft/PyPI/PEP 639 primary sources support the distinctions. | Do not conflate attestations with executable trust. |

### 4.5 RQ-03A — FFI/render cost model

Source: `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md`.

| Claim IDs / range | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| C01–C02 | **verified as conditional architectural statements** | A pure native call graph can execute without Python; hidden callbacks/finalizers falsify it. PyO3 0.30.1 confirms attachment mechanics. | Define and audit the native frame closure. |
| C03 | **plausible** | Event-batch/complete-snapshot design is not implemented. | First-slice hypothesis. |
| C04 | **verified** | 120 distinct presented frames/s requires a 120 Hz path; headless result is throughput. | Separate capacity and presentation claims. |
| C05 | **plausible for pygpui; algorithm verified** | GPUI materializes a visible range but invokes `render_items` during prepaint/measurement. | Native row materialization required. |
| C06–C08 | **verified** | Cache presence is not cache effectiveness; latency has OS/GPU/present stages; attach/detach/finalizers are the dangerous boundaries. | Measure stages and instrument boundaries. |
| 36–48, A1–A7 and exclusions | **unverified assumptions/policy** | Workloads, steady-state scope, budgets and idle definition are proposals. | Must be approved, not treated as facts. |
| 50–289, cost components and strategy | **verified mechanisms / unverified quantities** | Source-backed API/cache mechanisms; all nanosecond costs, complexity outcomes and budget allocations are estimates. | Use for diagnosis, not certification. |
| 307–348, V01–V14 | **unverified experiments** | None run; commands are placeholders. | Convert to harness tasks. |
| 350–360, G01–G07 | **unverified gates** | Targets and idle threshold are proposals. | OQ-02 approval required. |

### 4.6 RQ-03B — benchmark protocol

Source: `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md`.

| Line range / section | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| 22–30, non-substitution rules | **verified distinctions / unverified policy choices** | Headless, submitted, displayed and photon are distinct; exact gate policy remains proposed. | Adopt distinctions; OQ-02 owns thresholds. |
| 32–54, S1–S17 | **verified source facts** | PresentMon, DXGI/DWM, Wayland, Metal, Vulkan, Python and benchmark-tool claims check out. Android/W3C material is cautionary, not a desktop target. | Supports boundary discipline. |
| 56–123, timeline/input boundary | **verified vocabulary / unverified certification policy** | OS-input-to-presented-response is the stronger, coherent boundary. Clock uncertainty threshold is policy. | Use this boundary; physical input-to-photon remains separate. |
| 125–176, scenes | **unverified proposals** | Deterministic workloads are plausible, but `l10000`'s ≤50-row assertion is off by one at fractional offsets. | Correct to ≤51 or redefine range before use. |
| 178–195, warmups/repetitions | **unverified policy** | Ten processes are reasonable but not empirically qualified. | Qualification run required. |
| 197–295, statistics/gates | **unverified policy with verified arithmetic** | Formulas are explicit; strict literal-120, bootstrap and <1% idle choices are not approved. | No target certification yet. |
| 300–328, disclosure/noise controls | **verified need / unverified policy details** | Environment fingerprint and raw artifacts are necessary; exact controls are proposed. | Keep mandatory. |
| 330–374, platform capture | **verified API semantics / unverified exact-stack capability** | PresentMon 2.3.1 CLI supports the stated default tracking and `MsAllInputToPhotonLatency`; other collectors still require stack qualification. macOS drawable count conflicts with RQ-04A. | Qualify each collector; align renderer config. |
| 376–465, commands | **unverified interface** | `pygpui_bench` does not exist. | Future harness contract only. |
| 467–552, baselines/regression | **verified formula / internally inconsistent block counts** | Five ABBA blocks yield ten pairs from 20 process runs; “ten paired blocks” yields 20 pairs from 40 runs. | Choose five blocks/ten pairs as conservative default. |
| 554–608, output/claim register | **verified format policy / unverified targets** | Claim wording correctly prevents overgeneralization. | Use after a valid run. |

### 4.7 RQ-04A — desktop runtime

Source: `.harness/RESEARCH/2026-11-24-rq-04-desktop-runtime.md`.

| Claim IDs / range | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| C01–C05 | **verified** | Exact winit/wgpu source confirms backends, support table, initialization priority and env-aware selection. | Explicit backend masks mandatory; DX12 is not the implicit all-backend default. |
| C06 | **plausible** | DX12-first Windows is a conservative policy, not a universal correctness/performance result. | Use for narrow baseline. |
| C07–C08 | **verified** | Microsoft/wgpu requirements and Vulkan WSI paths are source-backed. | Capability checks required. |
| C09–C10 | **plausible** | Dual Linux protocols and native Metal are recommendations. | Release-gate both protocols; no fallback claim. |
| C11 | **verified** | Metal/wgpu minimum targets are not support promises. | Keep deployment/support separate. |
| C12 | **plausible** | Logging adapter metadata is a sound audit policy. | Required diagnostics. |
| C13–C23 | **verified** | Winit threading, control flow, redraw, Wayland notify, units/scaling, occlusion, keyboard/IME and teardown facts are source-backed. | Main-thread loop, logical/physical policy, no indefinite `Poll`, explicit IME reset. |
| C24–C33 | **verified** | Exact wgpu 30.0.2 source confirms surface handles, capabilities, status enum, present API, resize/thread constraints and DXC choice. | Implement a bounded surface state machine. |
| C34 | **plausible** | Preferred sRGB format policy is conservative. | Validate color output. |
| I1–I14 | **verified issue existence; applicability mostly plausible/unverified** | I3's `Poll` spin, I8's stable Metal defect and I12's scaling distinction are directly supported; other reports do not prove pygpui failure. | Turn into platform tests, not blanket rejection. |
| 23–41, matrix/profile | **plausible** | Narrowest credible candidate matrix, not tested support. | Candidate test matrix only. |
| 43–58, local Linux observation | **verified local fact** | Host Vulkan/session observation only. | No Ubuntu/GNOME or runtime certification. |
| 136–187, T/L/W/M gates | **unverified tests** | None executed. | Mandatory before support claims. |
| 189–207, support distinction and contradictions | **verified** | Correctly separates upstream support, integration correctness and stable/trunk fixes. | Use as policy. |
| 209–219, U01–U07 | **unverified** | Hardware, policy and packaging choices remain open. | Conservative defaults in §8 below. |

### 4.8 RQ-04B — IME, accessibility and distribution

Source: `.harness/RESEARCH/2026-11-24-rq-04-ime-a11y-distribution.md`.

| Claim IDs / range | Final disposition | Evidence / falsification result | Decision impact |
|---|---|---|---|
| IME-01–IME-05 | **verified source facts; integration remains plausible** | Winit docs confirm lifecycle/UTF-8 offsets; #4508/#4807/#4626 and #4220 support the stated gaps/workarounds. | Explicit composition/focus state machine; no complete IME claim. |
| KBD-01–KBD-02 | **verified** | Focus, physical/logical key and synthetic-event semantics are documented. | Clear pressed state on every focus loss. |
| A11Y-01–A11Y-03 | **verified** | AccessKit tree/update/adapter contracts confirmed in 0.25.2/0.34.2 docs. | Rust tree owner; event-loop proxy first. |
| A11Y-04 | **plausible** | Safe Python/Rust split is an inference. | Prototype before ADR hardens it. |
| A11Y-05 | **verified** | Adapters are best-effort; #840 is a concrete Windows gap. | No WCAG/conformance claim. |
| A11Y-06 | **unverified** | January 2025 discussion does not establish 0.24.1 behavior in 2026. | Test Orca and inspector separately. |
| DIST-01 | **verified** | `abi3` collapses Python minors only. | Per-OS/architecture wheels. |
| DIST-02 | **verified mechanism / unverified absolute wording** | Free-threaded builds are unsupported by the GIL `abi3` path, but “cannot load” is too absolute: CPython can re-enable the GIL for an extension that does not declare free-thread safety. | Say “unsupported and not shipped,” not “unloadable.” |
| DIST-03–DIST-04 | **verified** | Extension suffixes, universal2, manylinux and external-driver limits are documented. | OS-specific build/repair/test lanes. |
| CI-01–CI-02 | **verified** | Native-host requirements and runner labels are documented. | Pin labels; hosted CI is not interactive certification. |
| CI-03 | **plausible** | Hosted runners cannot prove IME/AT/multi-display behavior. | Physical/self-hosted gates required. |
| SIGN-01–SIGN-04 | **verified** | Apple/Microsoft/PyPI primary sources support the signing/attestation distinctions. | Public signing remains separate and blocked. |
| BLOCK-01 | **verified** | No credentials, remote or release project supplied. | Do not attempt release operations. |
| REL-01 | **plausible** | Support matrix is policy, not tested compatibility. | Architect/user approval required. |
| LINUX-01 | **verified** | Wheel and desktop-entry/bundle responsibilities differ. | Wheel/sdist first. |
| REL-02 | **plausible** | Final app bundler owns nested signing/notarization. | Separate release lane if apps are required. |
| 64–78, technical requirements | **plausible/unverified implementation** | Requirements are sound; none implemented. | Phase 1/release tasks. |
| 94–120, IME/a11y contracts | **verified requirements / plausible integration** | UTF-8, focus reset and adapter ordering are source-backed; sequencing needs tests. | Adopt with validation. |
| 123–135, accessibility gate | **unverified outcome** | No AT workflow has run. | No accessibility claim. |
| 137–148, wheel defaults | **unverified proposed artifacts** | Exact filenames not observed; macOS tag conflicts with RQ-02B. | Regenerate after support decision. |
| 150–159, CI design | **plausible** | Reproducible design; no workflow executed. | Release-CI task. |
| 161–200, platform tests | **unverified tests** | No physical IME/AT evidence. | Mandatory before claims. |
| 202–219, conservative defaults | **plausible policy / verified limitations** | Useful defaults; not compatibility evidence. | Use with explicit gates. |

## 5. Severity-tagged findings

There are **no unresolved blocking Skeptic findings for Phase 0 architecture**. The items below are nonblocking to ADR drafting because each has a verified correction or a conservative default. Several are high severity because using the uncorrected text would invalidate a benchmark or a release claim.

### Nonblocking findings

- **[NONBLOCKING-HIGH] F-01 — RQ-03B ABBA counts contradict each other.** Section 5 says ten processes permit five ABBA blocks; §10.2 then says ten paired blocks and ten pairs from five blocks. One `A B B A` block has four process runs and two pairs. **Correction:** use five blocks = 20 process runs = ten pairs, or ten blocks = 40 runs = twenty pairs. Conservative default: five blocks/ten pairs. Do not silently mix the two.
- **[NONBLOCKING-HIGH] F-02 — `l10000`'s ≤50 mounted-row assertion is arithmetically wrong.** A 1,080 px viewport over 32 px rows intersects 34 or 35 rows depending on fractional offset; eight rows of overscan on each side can produce 51 mounted rows away from content edges. **Correction:** assert ≤51, or redefine the visible/overscan accounting and regenerate the scene verifier.
- **[NONBLOCKING-HIGH] F-03 — macOS benchmark and runtime queue depths differ.** RQ-04A's `desired_maximum_frame_latency = 2` maps to `CAMetalLayer.maximumDrawableCount = 3`; RQ-03B specifies 2. **Correction:** benchmark the shipped configuration (3), or name a separate desired-latency-1/two-drawable experiment.
- **[NONBLOCKING-HIGH] F-04 — AccessKit's invisible-window requirement collides with stable wgpu Metal first-frame behavior.** AccessKit must be constructed before first show; wgpu 30.0.2 still contains the pre-visible occlusion check fixed only on trunk by PR #10302. **Default:** create invisible → attach adapter → show → present, and block macOS support until that exact sequence passes. Do not depend on trunk or claim a pre-show first frame on 30.0.2.
- **[NONBLOCKING-HIGH] F-05 — RQ-03A's input endpoint is ambiguous.** “First submitted frame that visibly responds” conflates submission and presentation. **Correction:** use RQ-03B's OS-input-to-first-presented-response definition; report input-to-photon only with calibrated optical/hardware evidence.
- **[NONBLOCKING-HIGH] F-06 — slotmap 1.1.1 has a confirmed safe-API soundness hole.** The trigger is extreme capacity, but “unlikely” is not a mitigation. **Default:** hard-cap framework node slots far below `u32::MAX`, forbid `detach`/`reattach` in slice 1, add stale-key/reinsertion tests, and track the next release.
- **[NONBLOCKING-HIGH] F-07 — Taffy 0.16.0 has reproduced correctness failures.** Flex aspect-ratio transfer and stale hoisted-child removal both fail locally. **Default:** constrain public layout to tested in-flow flex/block; retain a full-refresh/correctness fallback; no CSS-compatibility claim.
- **[NONBLOCKING-MEDIUM] F-08 — Python 3.11 lacks `threading.setprofile_all_threads`.** It was added in 3.12. **Correction:** use it only on 3.12+, or fall back to `sys.setprofile` plus native counters. Native counters remain authoritative.
- **[NONBLOCKING-MEDIUM] F-09 — `PYTHON_GIL=1/0` does not select a Python build.** It toggles the GIL at runtime in a free-threaded-capable interpreter. **Correction:** the benchmark matrix must launch separately installed GIL-enabled and free-threaded interpreters; the first release remains GIL-only.
- **[NONBLOCKING-MEDIUM] F-10 — “free-threaded CPython cannot load GIL abi3 wheels” is overstrong.** The supported/distributed claim is correct; the loader can re-enable the GIL for an extension that does not declare free-thread safety. **Correction:** say “unsupported and not shipped.”
- **[NONBLOCKING-MEDIUM] F-11 — macOS wheel tag, architecture and support floor are conflated across streams.** **Default:** macOS 26 arm64 candidate only; no Intel/universal2 claim until tested; deployment tag follows the tested target, not the candidate 11.0 tag.
- **[NONBLOCKING-MEDIUM] F-12 — Linux GLES is compiled in RQ-02A but excluded by RQ-04A.** **Default:** Vulkan-only compile/selection for slice 1; GLES deferred.
- **[NONBLOCKING-MEDIUM] F-13 — the native-thread description obscures the platform-main-thread requirement and PyO3 `detach`'s `Send` bound.** **Default:** one main-thread winit loop; create non-`Send` UI state inside the detached native scope; no render worker in slice 1; return only `Send` results.
- **[NONBLOCKING-MEDIUM] F-14 — AccessKit's optional `pyo3` feature is incompatible with the selected PyO3 line if enabled.** `accesskit 0.25.2` depends on `pyo3 ^0.29`; selected PyO3 is 0.30.1. **Default:** keep that feature disabled and maintain the Rust-owned accessibility mirror.
- **[NONBLOCKING-LOW] F-15 — RQ-04B mislabels the winit docs.rs build date as the crate publication date.** Use 2026-03-02 for release freshness.
- **[NONBLOCKING-LOW] F-16 — RQ-03A's cosmic-text citations mix a later commit with crate 0.19.0.** The used cache/timing APIs exist in 0.19.0, so the decision survives; future claims must cite the tag.
- **[NONBLOCKING-GATE] F-17 — performance, platform, IME, accessibility, full transitive-license closure and public signing are all unverified.** These are release/certification gates, not reasons to reopen architecture research. Conservative defaults in §8 prevent unsupported claims.

## 6. Verified decision set for Architect

The Architect may use the following inputs. “Verified” below refers to the underlying fact/mechanism; adopting it as pygpui's design remains an Architect decision with the stated constraints.

| Decision | Status | Inputs the Architect may rely on | Required constraint |
|---|---|---|---|
| Rust owns window/event loop, retained UI state, layout, hit testing, focus/key dispatch, text, scene and presentation; Python owns domain state and semantic intent | **plausible adoption, verified prior-art basis** | RQ-01A C-01–C-24; RQ-01B C-XC-01–C-XC-03/R1–R3 | No performance claim; validate with prototype and counters. |
| Slice 1 uses complete Rust-owned snapshot replacement on semantic change, stable IDs, and full-window rebuild; incremental patches/caches are later | **conservative design default** | RQ-01A C-12; RQ-01B R1/R5; manifest watchlist | No generic Python VDOM/differ in slice 1. |
| One Rust-owned platform-main-thread event loop; bounded command queue; reattach only at semantic event boundaries; no Python frame callback | **plausible adoption, verified PyO3/winit mechanics** | RQ-02B C11–C15; RQ-03A C01–C08; RQ-04A C13–C16 | Native counters, sentinels and static reachability audit required. |
| Exact first-slice pins: winit 0.30.13, wgpu 30.0.2, Taffy 0.16.0, cosmic-text 0.19.0, rustc-hash 2.1.3, slotmap 1.1.1, PyO3 0.30.1, maturin 1.16.0 | **verified compatibility; plausible selection** | RQ-02A 17–94; RQ-02B C01; independent resolver/check | Production lockfile still required; constrain known defects. |
| AccessKit 0.25.2 + accesskit_winit 0.34.2 are the selected later-slice pair | **verified compatibility** | RQ-02A 173–185; RQ-04B A11Y-01–A11Y-03 | Adapter deferred; optional `pyo3` feature disabled. |
| Effective Rust floor is at least 1.90; observed toolchain is 1.100.0 | **verified** | Resolved `ordered-float 5.5.1`; local checks | Pin build toolchain; make no MSRV promise until tested. |
| Target backend policy: Vulkan on Linux, DX12 on Windows, Metal on macOS; explicit masks; no GLES fallback claim | **verified constraints; plausible policy** | RQ-04A C01–C12/C24–C33 | Runtime smoke tests required per OS/GPU. |
| CPython ≥3.11 GIL-enabled `abi3-py311`; manual reviewed stubs; no default async runtime | **verified mechanism; plausible product policy** | RQ-02B C02–C28 | OQ-11 approval; clean-wheel tests on every supported minor. |
| Benchmark capacity, presentation and input latency are separate claims; input target ends at first presented response | **verified boundary distinction** | RQ-03B §§1–3; RQ-03A C04/C07 | Thresholds and environment remain OQ-02. |
| Zero-Python-frame claim requires native counters plus sentinels and static audit, not sampling | **verified proof requirement** | RQ-03A §10; RQ-03B §6.5 | Scope to no callback/entry/attachment/finalizer; do not claim zero CPython refcount instructions. |
| IME uses UTF-8 byte offsets, one text source, explicit focus/composition reset and pre-close disable on macOS | **verified requirements; plausible implementation** | RQ-04B IME-01–IME-05/KBD-01–KBD-02 | Physical IME tests before support claim. |
| Accessibility tree identity/diffing stays in Rust; adapter events return to the main loop before Python | **verified contracts; plausible ownership split** | RQ-04B A11Y-01–A11Y-05 | No WCAG claim; virtualized-list metadata is unresolved. |
| Concept-only clean-room implementation is the default; copied/adapted source requires exact provenance and Apache-2.0 compliance | **verified obligations; plausible policy** | RQ-01A C-25–C-32; RQ-01B R7 | Full transitive/artifact audit before distribution. |
| Wheel/sdist first; PyPI attestations are not OS signing; public signing/publishing remain blocked | **verified constraints** | RQ-02B C28–C36; RQ-04B SIGN/BLOCK/REL claims | No release operation without channel, credentials and tested pipeline. |

## 7. Plausible claims requiring validation

These are implementation, certification or policy validations, not new desk-research questions.

| Claim | Validation needed | Appropriate owner / phase |
|---|---|---|
| Event-batch snapshot boundary can preserve reusable Python views without per-frame Python | Small Python API prototype plus V01 callback trap and FFI ablation | Architect + Test/Perf, Phase 1 |
| Main-thread detached native loop handles callbacks, shutdown and `Py<T>` lifetime safely | Close/input/async-completion/finalizer tests on all three OS families | Build + Test, Phase 1 |
| Retained state, dirty flags and caches are sufficient before damage tracking | V04/V06/V09 scaling and cache counters | Perf, Phase 1 |
| cosmic-text 0.19.0 can feed a wgpu atlas without the #543 borrow pattern or unacceptable #518 cost | Text-atlas spike with ASCII/CJK/RTL/emoji and font fallback | Build + Perf, Phase 1 |
| Taffy constrained subset is correct for the first widget set | Regression suite for #804/#1354/#1357 and supported flex/block cases | Build + Test, Phase 1 |
| slotmap mitigation is adequate | Hard-cap invariant, stale-key/reinsertion tests, no detach/reattach review | Build + Reviewer, Phase 1 |
| winit/wgpu pair presents correctly on the candidate matrix | T01–T12 and installed-wheel tests | Platform + Test, before support claim |
| IME state machine avoids duplicate text/stuck keys/candidate-window errors | Physical Japanese/Chinese/Korean/dead-key/focus-transfer tests | Platform + Test, before IME claim |
| Accessibility ownership and virtualized-list representation are usable | VoiceOver/Narrator/Orca workflows; #871 limitation/fix | Platform + Test, before a11y claim |
| abi3 wheels install and run on CPython 3.11–3.15 GIL builds | Native builds, repair, clean installs, `abi3audit`, tag inspection | Release-CI, before publication |
| Wayland binary is acceptable under the project's license policy | Upstream clarification or qualified counsel plus artifact audit | User/Architect/Counsel, before Wayland distribution |
| Public macOS/Windows artifacts are trusted | Developer ID/notarization or Authenticode pipeline and clean-machine verification | Release-CI, before public release |

## 8. Residual uncertainties and conservative defaults

| Uncertainty | Conservative default until resolved | What may change it |
|---|---|---|
| OQ-02 certification hardware and exact gates | No target certification. Keep literal 120.0, OS-input-to-presented-response and <1%-one-core idle as proposals; disclose every environment. | User-approved hardware/display and protocol qualification. |
| OQ-03 OS/architecture floor | Candidate tests: Ubuntu 24.04 x86_64 GNOME Wayland+X11; Windows 11 25H2+ x64 DX12; macOS 26 arm64 Metal. No public support claim. | User requirements plus passing platform gates. |
| OQ-04 free-threaded Python | GIL-enabled only; `gil_used = true`; no 3.13t/3.14t/`abi3t` artifact. | Separate safety audit and wheel/test matrix. |
| OQ-05 minimum API | Architect proposes minimal app/entity/view/element/action surface and one interactive window; snapshot-first boundary. | Accepted ADR and prototype. |
| OQ-07/OQ-09 accessibility scope | No conformance claim; real AT workflows are release gates. | Approved WCAG/AT matrix and passing tests. |
| OQ-08 GPUI source reuse | No copied/adapted source; documented concepts only. | Explicit provenance/license exception. |
| OQ-10 release channel | Wheel/sdist first; no app bundle/store/signing assumption. | User names channel and credential owner. |
| OQ-11 Python range | CPython 3.11–3.15 GIL with `abi3-py311` remains provisional. | User approval and clean-wheel tests. |
| OQ-12 macOS first frame | No macOS support claim on wgpu 30.0.2 until invisible-window/AccessKit/show/present and occlusion tests pass, or a stable backport is adopted. | Physical macOS evidence. |
| OQ-13 Wayland licensing | No permissive-only Wayland distribution claim. X11-only preview is a scope reduction, not Linux support. | Upstream clarification/counsel and artifact audit. |
| OQ-14 MSRV | Pin Rust 1.100.0 for reproducibility; no minimum-support promise. | Production lockfile tested on proposed floor ≥1.90. |
| Full transitive license/NOTICE closure | No binary distribution until exact target/feature artifact audit. | Committed lockfile, SBOM/notices and legal review where needed. |
| Physical IME/AT runners | No IME/accessibility completeness claim. | User-provided hardware and executed evidence. |
| wgpu/winit/cosmic-text/Taffy/slotmap open defects | Use exact pins with documented constraints, tests and fallbacks; never trunk dependencies. | Stable fixes plus regression evidence. |

## 9. Round 2 requests

**None.**

Round 1 plus the targeted primary-source checks above are sufficient to draft ADRs with explicit conservative defaults. Remaining uncertainties are product-policy decisions (OQ-02/03/05/07/09/10/11/13/14), implementation proofs, physical-platform certification, or qualified legal review. Another desk-research round would not change the architecture choice and would consume the three-round cap without reducing the real risk.

The Orchestrator should proceed to Architect using §6, while preserving every gate in §§7–8. No plausible or unverified claim in this review is approved as an achieved fact.
