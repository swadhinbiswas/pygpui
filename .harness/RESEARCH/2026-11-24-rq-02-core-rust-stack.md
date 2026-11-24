# RQ-02A — Core Rust rendering, layout, text and accessibility stack

- Task: `P0-R02A`, Round 1, Researcher-Libs instance A
- Research date and source access date: **2026-11-24 (UTC)**
- Scope: `winit`, `wgpu`, `taffy`, `cosmic-text`, `accesskit`, `rustc-hash`, and `slotmap`
- Out of scope: PyO3/maturin/abi3/typing (RQ-02B), benchmark protocol (RQ-03B), and the final platform support policy (RQ-04)
- Workspace changes: research documentation only; no feature code, dependency manifest, `TASKS.json`, `STATE.md`, or commit

## Evidence convention

- **verified** — dated primary source or reproducible local observation.
- **plausible** — inference from primary evidence, but not directly established.
- **unverified** — assumption, report whose applicability is not established, or work not executed here.

An open issue verifies that a problem was reported and remains open on the access date; it does **not** by itself verify that every configuration is affected. Local probes are explicitly identified below.

## Executive decision

**verified** — The exact stable candidates below resolve together for `x86_64-pc-windows-msvc`, `aarch64-apple-darwin`, and `x86_64-unknown-linux-gnu` with the tested feature set. A Linux `cargo check --locked --all-targets` also passed on rustc/cargo 1.100.0. This establishes resolver compatibility and one host compile, not three-platform runtime support.

**plausible** — Adopt the pinned baseline below for the first retained-mode vertical slice, with target-specific wgpu backends and explicit regression tests for the known Taffy, wgpu, cosmic-text, winit, and slotmap issues. There is no existing implementation, so Taffy 0.16's breaking changes carry no migration cost.

**unverified** — The 120 fps, 10,000-row, sub-8 ms input-to-frame, and near-zero idle CPU targets are not established by this research. No rendering benchmark or Windows/macOS runtime test was run.

| Role | Exact candidate | Slice decision |
|---|---|---|
| Native window/event loop | `winit =0.30.13` | Required |
| GPU rendering | `wgpu =30.0.2` | Required |
| Layout | `taffy =0.16.0` | Required, initially constrained to tested in-flow flex/block cases |
| Text shaping/layout/raster source | `cosmic-text =0.19.0` | Required for the first real text element |
| Accessibility schema | `accesskit =0.25.2` | Version selected; integration deferred |
| winit accessibility adapter | `accesskit_winit =0.34.2` | Version selected as a pair with AccessKit; integration deferred |
| Fast internal maps | `rustc-hash =2.1.3` | Required when the retained scene/node store is introduced |
| Generation-checked node IDs | `slotmap =1.1.1` | Required when the retained scene/node store is introduced |

**verified** — `winit` has a newer prerelease, `0.31.0-beta.4` (2026-10-24), but `0.30.13` is the current maximum stable version. The prerelease is not the recommended production baseline. [W-CRATE] [W-BETA]

## Exact candidate inventory

All version, license, and declared-MSRV facts in this table are **verified** from crates.io metadata and the published crate manifests. Repository activity is the GitHub API `pushed_at` value observed on 2026-11-24; it is activity evidence, not a release date.

| Crate | Exact stable version | Publication/release date (UTC) | Tag / published commit | License | Declared MSRV | Latest repository push |
|---|---:|---|---|---|---:|---:|
| winit | 0.30.13 | 2026-03-02 | `v0.30.13` / `e9809ef54b18499bb4f2cac945719ecc2a61061b` | Apache-2.0 | 1.70.0 | 2026-11-22 |
| wgpu | 30.0.2 | 2026-11-12 | `v30.0.2` / `2b38d994b38dd001157d31fd3321111103a8dd80` | MIT OR Apache-2.0 | 1.87.0 | 2026-11-24 |
| taffy | 0.16.0 | 2026-11-23 | `v0.16.0` / `497de49c200daee81a18ce627bec98d5340ae57a` | MIT | 1.85 | 2026-11-23 |
| cosmic-text | 0.19.0 | 2026-04-22 | `0.19.0` / `c24886c2471e5606587c46090cd25dbbf209186b` | MIT OR Apache-2.0 | 1.89 | 2026-10-27 |
| accesskit | 0.25.2 | 2026-10-25 | published commit `f3026222559c7f5f46d8f25cb7404de68eb149f0` | MIT OR Apache-2.0 | 1.87 | 2026-11-23 |
| accesskit_winit | 0.34.2 | 2026-10-25 | `accesskit_winit-v0.34.2` / `f3026222559c7f5f46d8f25cb7404de68eb149f0` | Apache-2.0 | 1.87 | 2026-11-23 |
| rustc-hash | 2.1.3 | 2026-07-02 | published commit `c13e7ccca705e6255387a2ebc6dca142d6881621` | Apache-2.0 OR MIT | 1.77 | 2026-10-15 |
| slotmap | 1.1.1 | 2025-12-06 | published commit `2d56154b9b628f7d7a506f24ebc4f55a13ec8fed` | Zlib | 1.58.0 | 2026-09-04 |

Sources: [W-CRATE] [W-REL] [G-CRATE] [G-REL] [T-CRATE] [T-REL] [C-CRATE] [C-REL] [A-CRATE] [AW-CRATE] [AW-REL] [R-CRATE] [S-CRATE]; repository API URLs are in the source register.

**verified** — Recent release activity is strong for winit, wgpu, Taffy, cosmic-text, and AccessKit. rustc-hash and slotmap have slower release cadences, but both repositories show 2026 pushes. [REPO-APIS]

**plausible** — Maintenance health is acceptable for a pinned prototype baseline, with two qualifications: Taffy 0.16.0 was only one day old on the access date, and slotmap has an acknowledged open soundness report awaiting a next version. Open-issue counts alone were not used as a health score because GitHub's repository count includes pull requests.

## Compatibility and reproducible local observations

### Resolver probe

**verified** — A scratch dependency-only probe outside the workspace used cargo 1.100.0 and rustc 1.100.0 on `x86_64-unknown-linux-gnu`. It pinned all selected versions with `=` and used:

- winit: `default-features = false`, `rwh_06`, `x11`, `wayland`, `wayland-dlopen`
- wgpu: `default-features = false`; Windows `std + wgsl + dx12`, macOS `std + wgsl + metal`, Linux `std + wgsl + vulkan + gles`
- taffy 0.16.0: `std`, `taffy_tree`, flexbox, block, float, grid, calc, content-size and detailed-layout features
- cosmic-text: `default-features = false`, `std`, `swash`, `fontconfig`
- AccessKit 0.25.2 without optional Python/serde features; `accesskit_winit` 0.34.2 with defaults
- rustc-hash 2.1.3 and slotmap 1.1.1 with `std`

`cargo generate-lockfile` reported **324 packages**. `cargo metadata --format-version 1 --filter-platform <target>` then succeeded for all three targets:

| Target | Resolved packages in metadata | Key result |
|---|---:|---|
| `x86_64-pc-windows-msvc` | 126 | winit 0.30.13, wgpu 30.0.2, Taffy 0.16.0, cosmic-text 0.19.0, AccessKit 0.25.2, adapter 0.34.2, raw-window-handle 0.6.2 |
| `aarch64-apple-darwin` | 138 | Same direct versions and raw-window-handle 0.6.2 |
| `x86_64-unknown-linux-gnu` | 206 | Same direct versions and raw-window-handle 0.6.2 |

**verified** — `cargo check --locked --all-targets` passed on Linux in 15.19 seconds. The only warnings were unused direct dependencies in the intentionally empty probe. No Windows or macOS cross-compilation or runtime test was performed.

### Version-constraint findings

**verified** — wgpu 30.0.2 requires `raw-window-handle ^0.6.2`; winit's `rwh_06` feature and accesskit_winit's default `rwh_06` feature select the same 0.6 handle family. Enabling winit's older `rwh_05`/`rwh_04` features is unnecessary for this baseline. [W-MANIFEST] [G-MANIFEST] [AW-MANIFEST]

**verified** — `accesskit_winit 0.34.2` depends on `winit ^0.30.5` and `accesskit ^0.25.2`; the selected winit 0.30.13 and AccessKit 0.25.2 satisfy those constraints. Its default features also enable winit X11/Wayland support. [AW-MANIFEST]

**verified** — Taffy 0.16.0 depends on `rustc-hash ^2` and `slotmap ^1.0.6`; cosmic-text 0.19.0 depends on `rustc-hash ^2.1.1`. The selected 2.1.3 and 1.1.1 satisfy both. [T-MANIFEST] [C-MANIFEST]

**verified** — The resolved graph contains both rustc-hash 1.1.0 and 2.1.3. `cargo tree -i rustc-hash@1.1.0` attributes 1.1.0 to wgpu 30.0.2's Naga/wgpu-core graph, while Taffy and cosmic-text use 2.1.3. This is normal coexistence of incompatible semver majors, not a resolution failure; project code must not pass a v2 `FxHashMap` type into a dependency that exposes a v1 type.

**verified** — The highest direct-crate MSRV is cosmic-text's 1.89, but the current resolved graph has an effective MSRV of at least **1.90** because `ordered-float 5.5.1` declares Rust 1.90 on all three target metadata results. The observed local 1.100.0 toolchain is sufficient; an MSRV-1.89 support claim would not be established by the direct manifests alone.

**unverified** — Actual adapter availability, surface configuration, text rendering, IME, accessibility, HiDPI behavior, and frame pacing on Windows and macOS remain untested. Linux runtime rendering was also not exercised.

## Per-crate findings

### winit 0.30.13

**verified** — role and platform scope.** Winit supplies window creation and input, not drawing or native menus. Its published feature document lists Windows, macOS, X11, Wayland, iOS, Android, Web, and Redox; the desktop slice only needs the first four. [W-FEATURES]

**verified** — compatibility.** The `rwh_06` feature exposes raw-window-handle 0.6 for wgpu and AccessKit. The recommended Linux features include both X11 and Wayland with dynamic Wayland loading. [W-MANIFEST]

**verified** — API stability risk.** Winit is pre-1.0, documents pending API reworks, and has an active 0.31 beta line. Pinning 0.30.13 and committing the lockfile is therefore preferable to a floating `0.30` requirement. [W-FEATURES] [W-BETA]

**verified** — recent fixes.** The 0.30.13 release fixes macOS non-file drag crashes, an out-of-bounds Pinyin IME selection-range crash, a Windows IME flag-masking bug, and X11 hit-test/timestamp issues. These are reasons to prefer 0.30.13 over 0.30.12. [W-REL]

**verified** — open platform issues relevant to later slices:**

- X11 IME commit loss with ibus/libpinyin is reported against 0.30.13; CJK composition can render but never deliver `Ime::Commit`. This blocks a claim of complete X11 text-input support. [W-4839]
- Windows IME remains IMM32-based; moving a candidate window during scrolling without changing composition text is reported unsupported, with TSF requested. [W-4843]
- An intermittent macOS AppKit crash when re-showing a hidden app is reported against 0.30.13 on one Intel Mac. Applicability to Apple Silicon is not established. [W-4820]
- The published feature matrix marks popup windows missing on all desktop platforms and has other platform-specific gaps. Custom in-window popovers are feasible; native popup-window semantics are a separate deferred problem. [W-FEATURES]

**verified** — license caveat.** Winit's `wayland` feature unconditionally includes `wayland-protocols-plasma`. Issue #4833 reports LGPL-2.1-or-later KDE protocol XML compiled into Wayland-enabled binaries and asks for an opt-out; a contributor replies that the generated declarations may not create an LGPL problem. The legal question is unresolved. [W-4833] [WP-MANIFEST] [WP-XML]

**plausible** — recommendation.** Use 0.30.13 for the first native window/event-loop slice. Defer IME completeness, native popups, advanced fullscreen/cursor behavior, and mobile/Web until platform-specific acceptance tests exist. If distribution must be permissive-only, resolve #4833 before claiming the Wayland binary is license-cleared.

### wgpu 30.0.2

**verified** — role and support tiers.** Wgpu runs natively on Vulkan, Metal, DX12 and OpenGL. Its current support table calls Vulkan on Windows/Linux, Metal on macOS/iOS, and DX12 on Windows first-class; OpenGL is best-effort/downlevel, with ANGLE required for macOS OpenGL. [G-README]

**verified** — why 30.0.2.** The 30.0.2 release fixes a mapped-buffer use-after-free on device loss/destruction, a surface-acquire texture-ID leak, Metal wide-gamut surface crashes/color issues, and a Naga feature-combination compile error. [G-REL]

**verified** — open backend issues:**

- A 29→30 presentation regression is reported with a standalone reproducer: Windows/Vulkan/NVIDIA showed higher present wall time, and a 2026-11-23 Linux/radv report also reproduced it. The issue remains open; 30.0.2 impact is **unverified** until the same benchmark is run. [G-9937]
- OpenGL/GLES on NVIDIA Linux has a long-running open issue. A 2026-11-24 report still fails on a recent driver even with a candidate fix commit; Vulkan is reported working in older comments. Do not treat GLES as a reliable universal Linux fallback. [G-4751]
- DX12 unaligned buffer/texture copies are reported to leak allocator resources on wgpu 30.0.2 and trunk. A UI atlas uploader should align copy layouts and add allocator-growth tests. [G-11068]
- Metal `stencil8` shader reads are reported to return zero on Intel Macs; Apple Silicon was not reproducible in the maintainer's test. Avoid sampled stencil8 in the first renderer and test Intel Macs if that feature is later used. [G-10309]

**verified** — Windows packaging gap.** The README says the `dxc` compiler selection requires `dxcompiler.dll` (minimum v1.8.2502) in the working directory; `static-dxc` must be enabled for static DXC, otherwise wgpu falls back to FXC. A Python wheel must choose and test one strategy rather than assuming the DLL exists. [G-README]

**verified** — API/spec churn.** Wgpu's README states a three-month breaking-release cadence and that WebGPU/WGSL are still drafts. Version 30 also changed surface presentation and vertex-buffer APIs. Isolate renderer code behind an internal module and pin the version. [G-README] [G-30]

**plausible** — recommendation.** Use 30.0.2, not 29.0.4, but make the 29/30 present-path comparison a release gate. Compile only target-relevant backends. Prefer Vulkan on Linux; retain GLES only as tested best-effort fallback. Resolve the Windows DXC packaging strategy before publishing Windows wheels.

### taffy 0.16.0

**verified** — role and dependencies.** Taffy implements CSS Block, Flexbox and Grid, plus float/calc/content-size features in 0.16. It is platform-independent Rust. The 0.16 default tree uses slotmap and rustc-hash. [T-README] [T-MANIFEST]

**verified** — breaking changes.** The 0.16.0 release raises MSRV to 1.85, moves to Rust 2024, changes calc handles, changes scrollable-overflow representation, changes custom float-placement APIs, and changes cache serialization/mutability. It also adds FxHash node-context lookups and several block/flex/grid fixes. [T-REL]

**verified** — current bugs reproduced locally on 0.16.0:**

1. **Flex aspect-ratio transfer.** A scratch probe with a 500×100 flex row and one `flex-grow: 1; aspect-ratio: 2` child produced `500x0`, not the expected `500x250`. This reproduces the still-open issue #804 on the exact candidate. [T-804] [LOCAL-TAFFY]
2. **Stale hoisted-child list after popup removal.** A scratch probe laid out an absolute popup in a relative container, removed the popup so the container became a leaf, and recomputed. Taffy 0.16.0 panicked with `invalid SlotMap key used`, matching issue #1354. The issue also reports a stack-overflow variant after reparenting. [T-1354] [LOCAL-TAFFY]

**verified** — additional open issue.** `round_layout` can leave out-of-flow nodes inside `display: none` subtrees with stale final layout; issue #1357 is open and linked to a workaround/PR. [T-1357]

**plausible** — recommendation.** Select 0.16.0 because there is no migration cost and it contains relevant fixes, but constrain slice 1 to tested in-flow flex/block layouts. Do not advertise aspect-ratio-driven flex sizing, mutable absolute popup containers, or full CSS compatibility until regression tests pass or upstream fixes are adopted. Grid/float/custom formatting contexts can remain deferred even if compiled.

**unverified** — The README benchmark table is not evidence for the project's 120 fps target: it uses an older commit (`e747f6e`), measures layout only, and excludes tree creation and text layout. [T-README]

### cosmic-text 0.19.0

**verified** — role and platform scope.** Cosmic-text provides shaping through HarfRust, rasterization through Swash, bidirectional layout, and font fallback. Its README explicitly claims full-feature support on Linux, macOS and Windows; other platforms may need custom fallback. [C-README]

**verified** — dependencies.** The selected version requires fontdb 0.23, harfrust 0.5, skrifa 0.40, rustc-hash 2.1.1+, and optional Swash 0.2.6+. The recommended `std + swash + fontconfig` feature set resolves successfully. [C-MANIFEST]

**verified** — release changes.** Version 0.19.0 includes lazy buffer setters, text decoration, `layout_runs`, cursor/RTL helpers, variable-font matching fixes, scroll-shaping optimizations, and several rendering corrections. [C-REL]

**verified** — open issues relevant to a renderer:**

- Generic `Family::Monospace` shaping is reported 10–20× slower than an explicit family on stock macOS, with per-shape fallback scans. The report is against 0.19.0 and remains open; fix commits are referenced but not released. [C-518]
- A custom `Renderer` implementation using `Buffer::render` plus `LegacyRenderer` cannot borrow `FontSystem` twice; the issue is open against 0.19 and a PR is proposed. This affects the exact custom-renderer integration pattern a wgpu text atlas may use. [C-543]
- Fontconfig aliases are reported not respected. System-font fallback fidelity therefore needs a Linux acceptance test. [C-499]

**plausible** — recommendation.** Use one long-lived `FontSystem`, shape on text/style changes rather than every frame, cache runs/glyphs, and use an explicit resolved font family for performance-sensitive monospace UI until #518 is fixed. Prototype the text-atlas path against `layout_runs`/the released API and keep the #543 borrow workaround behind a small adapter. Defer rich editing, syntax highlighting, Vi mode, and comprehensive color-font/fallback claims.

**unverified** — Cosmic-text does not by itself establish texture-atlas upload cost, GPU memory use, or frame-time behavior in this project. Those require the RQ-03 benchmark.

### accesskit 0.25.2 + accesskit_winit 0.34.2

**verified** — role and adapter coverage.** AccessKit defines the accessibility tree/action schema; platform adapters are required. The published adapter list covers Windows UIA, macOS NSAccessibility, Unix AT-SPI, Android, and the winit adapter. No Web adapter is listed; accesskit_winit says unsupported platforms compile but do nothing. [A-README] [AW-README]

**verified** — runtime integration cost.** On Linux/Unix, accesskit_winit's API is blocking but internally spawns async tasks. Its default uses `async-io`; a Tokio user should enable `tokio`. Android support currently requires GameActivity. [AW-README] [AW-MANIFEST]

**verified** — open issues relevant to the target framework:**

- Virtualized lists/tables cannot announce provided `row_count`/`row_index` through current platform adapters, according to open issue #871. This directly affects the 10,000-row accessibility goal. [A-871]
- Accessibility tree child-diffing during scrolling is reported slow; a downstream patch is offered but not merged. [A-856]
- `TextPosition::to_line_index` can loop forever on an empty text run, reproduced with published 0.25.1/consumer 0.39.1 on macOS. The issue remains open; 0.25.2 applicability is **unverified** until retested. [A-864]

**plausible** — recommendation.** Keep the exact pair as the selected accessibility baseline, but defer integration beyond the first render/layout/text slice. Accessibility must be integrated and tested before any public accessibility claim, and virtualized-list semantics need an explicit upstream fix or documented limitation.

### rustc-hash 2.1.3

**verified** — intended use.** The crate documents FxHash as a fast, non-cryptographic hash for rustc-like trusted workloads and explicitly contrasts it with default SipHash. It is suitable for internal ID/style maps, not as a security boundary for attacker-controlled keys. [R-DOCS]

**verified** — known performance issue.** Issue #45 reports accidental quadratic behavior when inserting one FxHashMap's iteration order into another under 2.x; different seeds do not avoid it. The issue is still open. This matters if scene snapshots are rebuilt by iterating another FxHashMap. [R-45]

**verified** — platform gap.** The only current open test failure listed is on SPARC64, outside the three desktop targets; no desktop-specific blocker was found in the primary issue list. [R-ISSUES]

**plausible** — recommendation.** Pin 2.1.3 for internal maps. Do not downgrade project code to 1.1 merely because Naga uses it transitively. Avoid the #45 insertion-order pattern, pre-size maps, and benchmark large scene rebuilds. Use randomized hashing for any attacker-controlled dictionary.

### slotmap 1.1.1

**verified** — intended use.** Slotmap provides persistent, versioned keys with O(1) insertion/access/removal and secondary maps. Its documentation recommends it for graph nodes/entities where stable safe references are needed. [S-DOCS]

**verified** — acknowledged soundness issue.** Issue #168 reports a safe-API path at `u32::MAX` slots where `reattach` can collide with the free-list sentinel and eventually reach undefined behavior. It requires roughly 2^32 slots/tens of GB, was found by source audit rather than execution, and the owner said on 2026-11-03 that it would be fixed in the next version. It remains open with no milestone. [S-168]

**verified** — other open contract issue.** Issue #159 reports `shrink_to(min_capacity)` may return capacity below the requested minimum, found with Kani; it has no maintainer response on the accessed page. [S-159]

**plausible** — recommendation.** Pin 1.1.1 for generation-checked IDs, cap application node counts far below the documented limit, avoid `detach`/`reattach` in the first implementation, and add stale-key/reinsertion tests. Track the next slotmap release as a security/soundness update rather than treating 1.1.1 as final.

**unverified** — A project-specific benchmark comparing SlotMap, HopSlotMap, DenseSlotMap, or plain `Vec` storage has not been run. The first slice should use one simple key type and measure before optimizing iteration layout.

## First vertical-slice requirements versus deferred components

**plausible** — working definition of slice 1.** One native desktop window owned by a Rust event loop; a wgpu clear/rectangle pass; a small retained tree with stable IDs; simple in-flow flex/block layout; one shaped/rasterized text element; and a Python-to-Rust event/update round trip with no Python callback per rendered frame. Cross-target resolution is required for Windows/macOS/Linux, while runtime smoke tests may be staged Linux first and must pass on all three before support is claimed.

### Required in slice 1

- **verified** — winit 0.30.13 with `rwh_06`; X11 and Wayland on Linux.
- **verified** — wgpu 30.0.2 with `std + wgsl` and target-native backend features.
- **verified** — Taffy 0.16.0 for the tested in-flow layout subset.
- **verified** — cosmic-text 0.19.0 with `std + swash + fontconfig` for text.
- **verified** — rustc-hash 2.1.3 and slotmap 1.1.1 once retained node storage is present; both are already transitive through Taffy/cosmic-text, but direct use must be a deliberate internal API choice.
- **unverified** — The Python boundary, abi3 wheel, event proxy, and typing design are RQ-02B/RQ-03A work and are not validated here.

### Deferred, with explicit gates

- **Accessibility integration:** accesskit 0.25.2 + accesskit_winit 0.34.2 after the first render/text slice, but before accessibility claims. Gate on UIA, NSAccessibility and AT-SPI smoke tests plus #871/#864 disposition.
- **IME completeness and rich text editing:** gate on winit #4839/#4843 and cosmic-text editing/fallback tests.
- **Native popup windows, multiwindow, advanced fullscreen/cursor/monitor behavior:** gate on platform tests; do not infer support from window creation alone.
- **Taffy aspect-ratio flex sizing and mutable absolute popup containers:** gate on #804/#1354 regression tests or an upstream fix.
- **Virtualized 10,000-row list:** defer until layout, rendering, text, accessibility row metadata, and benchmark criteria all pass independently.
- **WebAssembly/browser, Android/iOS, Redox, 32-bit Windows, DRM, ANGLE and MoltenVK:** non-goals for this desktop baseline unless separately approved.
- **Optional crate features:** no AccessKit `pyo3`, no slotmap `serde`/`unstable`, no rustc-hash `nightly`, no cosmic-text `vi`, and no wgpu WebGPU/WebGL in the first desktop build.

## License and NOTICE implications

**verified** — direct licenses.** The direct stack is permissive: Apache-2.0, MIT, dual MIT/Apache-2.0, or Zlib. No direct crate archive inspected contained a `NOTICE` file. [DIRECT-LICENSES]

**verified** — baseline obligations.** For a binary distribution, retain and reproduce the applicable license/copyright texts in the project's third-party notices. Apache-2.0 requires preserving license and applicable notices and marking modified files; MIT requires the copyright and permission notice; Zlib requires preserving the notice in source distributions, not misrepresenting origin, and marking altered source. This is an engineering summary, not a legal opinion. [APACHE] [MIT] [ZLIB]

**verified** — transitive license uncertainty.** The direct-crate list is not a complete distribution audit. In particular, `wayland-protocols-plasma 0.3.12` declares MIT in Cargo metadata, while bundled KDE XML files declare LGPL-2.1-or-later and the crate ships LGPL texts. Winit issue #4833 and the contributor reply disagree about the consequence for generated bindings. Conservatively record this as unresolved mixed-license content until counsel or an upstream licensing clarification accepts it. [WP-MANIFEST] [WP-XML] [W-4833]

**unverified** — complete NOTICE inventory.** A final lockfile does not yet exist in the project workspace, and no wheel has been built. Generate the definitive transitive inventory and notices from the committed lockfile and actual target/feature matrix before distribution. If `static-dxc` is selected, audit its additional dependencies and notices as part of that Windows packaging decision.

## Contradictions and stale evidence

| Contradiction / stale source | Disposition |
|---|---|
| Winit 0.30.13 release adds Wayland `set_resize_increments`, but the same tag's `FEATURES.md` matrix still marks Wayland resize increments missing. | **verified** stale feature matrix; use release notes plus runtime tests, not that cell alone. [W-REL] [W-FEATURES] |
| Winit crates.io `newest_version` is 0.31.0-beta.4 while `max_stable_version` is 0.30.13. | **verified** distinction; beta is not the stable candidate. [W-CRATE] |
| GitHub's repository license heuristic reports Apache-2.0 for wgpu/cosmic-text and BSD-3-Clause for AccessKit, while published crate manifests say MIT OR Apache-2.0. | **verified** metadata conflict; crate manifest and shipped license files govern this research's direct-license record. [G-MANIFEST] [C-MANIFEST] [A-MANIFEST] [A-LICENSES] |
| `wayland-protocols-plasma` Cargo metadata says MIT, but bundled protocol XML says LGPL-2.1-or-later. | **verified** mixed metadata; legal effect unresolved. [WP-MANIFEST] [WP-XML] [W-4833] |
| Taffy README performance table references old commit `e747f6e`, not 0.16.0. | **verified** stale for candidate performance; do not use it as target evidence. [T-README] |
| AccessKit's latest GitHub release at the repository level is the winit adapter, not necessarily the latest `accesskit` schema crate. | **verified** packaging distinction; core and adapter versions were checked separately. [A-CRATE] [AW-REL] |

## Narrow recommendation

**plausible** — recommended baseline, subject to the validation gates below:**

```toml
winit = { version = "=0.30.13", default-features = false, features = ["rwh_06", "x11", "wayland", "wayland-dlopen"] }
taffy = "=0.16.0"
cosmic-text = { version = "=0.19.0", default-features = false, features = ["std", "swash", "fontconfig"] }
rustc-hash = { version = "=2.1.3", default-features = false, features = ["std"] }
slotmap = { version = "=1.1.1", default-features = false, features = ["std"] }

[target.'cfg(target_os = "windows")'.dependencies]
wgpu = { version = "=30.0.2", default-features = false, features = ["std", "wgsl", "dx12"] }

[target.'cfg(target_os = "macos")'.dependencies]
wgpu = { version = "=30.0.2", default-features = false, features = ["std", "wgsl", "metal"] }

[target.'cfg(target_os = "linux")'.dependencies]
wgpu = { version = "=30.0.2", default-features = false, features = ["std", "wgsl", "vulkan", "gles"] }
```

Deferred accessibility pair, when its integration slice starts:

```toml
accesskit = "=0.25.2"
accesskit_winit = "=0.34.2"
```

**verified** — The first block is the same direct version/feature baseline used for the successful resolver probe, except that the probe included AccessKit and a broader Taffy feature set. Removing/deferring those cannot introduce a direct-version conflict, but the production lockfile still must be regenerated and checked.

### Rejected alternatives

| Alternative | Disposition |
|---|---|
| winit 0.31.0-beta.4 | **Rejected for baseline:** prerelease with active API rework; revisit only after a stable 0.31 release and migration tests. [W-BETA] |
| wgpu 29.0.4 | **Rejected as default:** lacks 30.0.2's mapped-buffer UAF and other fixes. Keep only as a benchmark comparator for #9937, not a co-baseline. [G-REL] [G-9937] |
| wgpu default features on native desktop | **Rejected:** enables every backend plus WebGPU; target-specific features reduce unnecessary surface and packaging assumptions. [G-MANIFEST] |
| Taffy 0.15.1 | **Rejected as primary:** lower MSRV is irrelevant to the observed 1.100 toolchain, and it misses 0.16 fixes/FxHash. Retain only as a fallback if 0.16 regression tests fail. [T-REL] |
| AccessKit integrated into the first render-only slice | **Rejected sequencing:** it adds platform adapters, Linux executor integration, tree/action plumbing and known virtualization/text bugs without helping prove the first rendered frame. The exact versions remain selected for the next slice. |
| rustc-hash 1.1.0 for project code | **Rejected:** Taffy/cosmic-text require 2.x; Naga's transitive 1.1.0 is not a reason to fragment project APIs. [T-MANIFEST] [C-MANIFEST] |
| Default SipHash for every internal scene map | **Rejected as a blanket default:** use FxHash for trusted internal keys, but retain randomized hashing where keys are attacker-controlled. Actual performance benefit remains a benchmark question. [R-DOCS] |
| Plain `Vec` indices as the long-term retained-node identity | **Rejected as framework foundation:** stale indices/ABA hazards undermine retained trees. A trivial static prototype can use indices, but the baseline should use versioned keys. [S-DOCS] |
| Git `main`/trunk dependencies | **Rejected:** unreproducible and outside the exact-release evidence used here. |

## Required validation before architecture lock

1. **verified need / unverified result** — Generate the production lockfile and run Windows/macOS cross-builds plus native runtime smoke tests on all three desktop OS families.
2. **verified need / unverified result** — Benchmark wgpu 30.0.2 presentation against 29.0.4 using the #9937 reproducer and the project's disclosed hardware/present-mode matrix.
3. **verified need / unverified result** — Test Linux Vulkan on NVIDIA/AMD/Intel and GLES only as an explicitly supported fallback; resolve the Windows DXC DLL/static-DXC strategy.
4. **verified need / unverified result** — Add Taffy regressions for #804, #1354 and #1357; constrain public layout features until they pass.
5. **verified need / unverified result** — Prototype cosmic-text glyph layout/atlas integration, including #543's borrow pattern and #518's monospace path.
6. **verified need / unverified result** — Retest AccessKit #864 on 0.25.2 and define a virtualized-list accessibility limitation/fix for #871.
7. **verified need / unverified result** — Run a slotmap stale-key/reinsertion suite and track #168; add a rustc-hash large-rebuild benchmark for #45.
8. **verified need / unverified result** — Audit the final transitive license/NOTICE inventory, especially Wayland protocol XML and any static-DXC dependencies.
9. **verified need / unverified result** — If an MSRV policy is adopted, test the actual lockfile on that compiler; the current resolved graph requires at least Rust 1.90.

## Source register

All sources were accessed **2026-11-24**. Dates in the text are publication/release/issue dates from the source, not access dates.

### Registry metadata and published manifests

- [W-CRATE] <https://crates.io/api/v1/crates/winit>
- [W-MANIFEST] <https://github.com/rust-windowing/winit/blob/e9809ef54b18499bb4f2cac945719ecc2a61061b/Cargo.toml>
- [G-CRATE] <https://crates.io/api/v1/crates/wgpu>
- [G-MANIFEST] <https://github.com/gfx-rs/wgpu/blob/2b38d994b38dd001157d31fd3321111103a8dd80/wgpu/Cargo.toml>
- [T-CRATE] <https://crates.io/api/v1/crates/taffy>
- [T-MANIFEST] <https://github.com/DioxusLabs/taffy/blob/497de49c200daee81a18ce627bec98d5340ae57a/Cargo.toml>
- [C-CRATE] <https://crates.io/api/v1/crates/cosmic-text>
- [C-MANIFEST] <https://github.com/pop-os/cosmic-text/blob/c24886c2471e5606587c46090cd25dbbf209186b/Cargo.toml>
- [A-CRATE] <https://crates.io/api/v1/crates/accesskit>
- [A-MANIFEST] <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/accesskit/Cargo.toml>
- [AW-CRATE] <https://crates.io/api/v1/crates/accesskit_winit>
- [AW-MANIFEST] <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/adapters/winit/Cargo.toml>
- [R-CRATE] <https://crates.io/api/v1/crates/rustc-hash>
- [S-CRATE] <https://crates.io/api/v1/crates/slotmap>
- [WP-MANIFEST] <https://github.com/Smithay/wayland-rs/blob/a3d7927d87799b2955bf491b51c7c2a3a82da661/wayland-protocols-plasma/Cargo.toml>
- [WP-XML] <https://docs.rs/crate/wayland-protocols-plasma/0.3.12/source/plasma-wayland-protocols/src/protocols/blur.xml>

### Releases, docs and repository activity

- [W-REL] <https://github.com/rust-windowing/winit/releases/tag/v0.30.13> — 2026-03-02
- [W-BETA] <https://github.com/rust-windowing/winit/releases/tag/v0.31.0-beta.4> — 2026-10-24
- [W-FEATURES] <https://github.com/rust-windowing/winit/blob/v0.30.13/FEATURES.md>
- [G-REL] <https://github.com/gfx-rs/wgpu/releases/tag/v30.0.2> — 2026-11-12
- [G-30] <https://github.com/gfx-rs/wgpu/releases/tag/v30.0.0> — 2026-07-01
- [G-README] <https://github.com/gfx-rs/wgpu/blob/v30.0.2/wgpu/README.md>
- [T-REL] <https://github.com/DioxusLabs/taffy/releases/tag/v0.16.0> — 2026-11-23
- [T-README] <https://github.com/DioxusLabs/taffy/blob/v0.16.0/README.md>
- [C-REL] <https://github.com/pop-os/cosmic-text/releases/tag/0.19.0> — 2026-04-22
- [C-README] <https://github.com/pop-os/cosmic-text/blob/0.19.0/README.md>
- [AW-REL] <https://github.com/AccessKit/accesskit/releases/tag/accesskit_winit-v0.34.2> — 2026-10-25
- [A-README] <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/README.md>
- [AW-README] <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/adapters/winit/README.md>
- [R-DOCS] <https://github.com/rust-lang/rustc-hash/blob/c13e7ccca705e6255387a2ebc6dca142d6881621/src/lib.rs>
- [S-DOCS] <https://github.com/orlp/slotmap/blob/2d56154b9b628f7d7a506f24ebc4f55a13ec8fed/src/lib.rs>
- [REPO-APIS] GitHub repository metadata: <https://api.github.com/repos/rust-windowing/winit>, <https://api.github.com/repos/gfx-rs/wgpu>, <https://api.github.com/repos/DioxusLabs/taffy>, <https://api.github.com/repos/pop-os/cosmic-text>, <https://api.github.com/repos/AccessKit/accesskit>, <https://api.github.com/repos/rust-lang/rustc-hash>, <https://api.github.com/repos/orlp/slotmap>

### Primary issue trackers

- [W-4833] <https://github.com/rust-windowing/winit/issues/4833> — opened 2026-11-11
- [W-4839] <https://github.com/rust-windowing/winit/issues/4839> — opened 2026-11-16
- [W-4843] <https://github.com/rust-windowing/winit/issues/4843> — opened 2026-11-17
- [W-4820] <https://github.com/rust-windowing/winit/issues/4820> — opened 2026-11-06
- [G-9937] <https://github.com/gfx-rs/wgpu/issues/9937> — opened 2026-07-23; updated 2026-11-23
- [G-4751] <https://github.com/gfx-rs/wgpu/issues/4751> — opened 2023-11-22; updated 2026-11-24
- [G-11068] <https://github.com/gfx-rs/wgpu/issues/11068> — opened 2026-11-21
- [G-10309] <https://github.com/gfx-rs/wgpu/issues/10309> — opened 2026-09-11
- [T-804] <https://github.com/DioxusLabs/taffy/issues/804> — opened 2025-02-18; 0.15.1/main confirmation 2026-11-04
- [T-1354] <https://github.com/DioxusLabs/taffy/issues/1354> — opened 2026-10-24
- [T-1357] <https://github.com/DioxusLabs/taffy/issues/1357> — opened 2026-10-25
- [C-518] <https://github.com/pop-os/cosmic-text/issues/518> — opened 2026-07-05
- [C-543] <https://github.com/pop-os/cosmic-text/issues/543> — opened 2026-10-27
- [C-499] <https://github.com/pop-os/cosmic-text/issues/499> — opened 2026-04-04
- [A-871] <https://github.com/AccessKit/accesskit/issues/871> — opened 2026-11-22
- [A-856] <https://github.com/AccessKit/accesskit/issues/856> — opened 2026-11-07
- [A-864] <https://github.com/AccessKit/accesskit/issues/864> — opened 2026-11-17
- [R-45] <https://github.com/rust-lang/rustc-hash/issues/45> — opened 2024-06-19
- [R-ISSUES] <https://github.com/rust-lang/rustc-hash/issues>
- [S-168] <https://github.com/orlp/slotmap/issues/168> — opened 2026-10-30; owner response 2026-11-03
- [S-159] <https://github.com/orlp/slotmap/issues/159> — opened 2026-06-22

### License texts

- [DIRECT-LICENSES] Published crate manifests and archives listed above; winit <https://github.com/rust-windowing/winit/blob/v0.30.13/LICENSE>, wgpu <https://github.com/gfx-rs/wgpu/blob/v30.0.2/LICENSE.APACHE> and <https://github.com/gfx-rs/wgpu/blob/v30.0.2/LICENSE.MIT>, cosmic-text <https://github.com/pop-os/cosmic-text/blob/0.19.0/LICENSE-APACHE> and <https://github.com/pop-os/cosmic-text/blob/0.19.0/LICENSE-MIT>, rustc-hash <https://github.com/rust-lang/rustc-hash/blob/c13e7ccca705e6255387a2ebc6dca142d6881621/LICENSE-APACHE> and <https://github.com/rust-lang/rustc-hash/blob/c13e7ccca705e6255387a2ebc6dca142d6881621/LICENSE-MIT>, slotmap <https://github.com/orlp/slotmap/blob/2d56154b9b628f7d7a506f24ebc4f55a13ec8fed/LICENSE>, AccessKit <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/LICENSE-APACHE> and <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/LICENSE-MIT>
- [A-LICENSES] <https://github.com/AccessKit/accesskit/blob/f3026222559c7f5f46d8f25cb7404de68eb149f0/Cargo.toml>
- [APACHE] <https://www.apache.org/licenses/LICENSE-2.0>
- [MIT] <https://opensource.org/license/mit/>
- [ZLIB] <https://github.com/orlp/slotmap/blob/2d56154b9b628f7d7a506f24ebc4f55a13ec8fed/LICENSE>

### Local research probe

- [LOCAL-TAFFY] Scratch probe at `/tmp/opencode/rq02a-resolve/src/bin/taffy_issue_probe.rs`, run 2026-11-24 with the exact locked Taffy 0.16.0 graph. `aspect` printed `aspect-ratio child: 500x0` and failed the expected `500x250` assertion; `stale` panicked with `invalid SlotMap key used`. These are reproducible observations, not project feature code.
