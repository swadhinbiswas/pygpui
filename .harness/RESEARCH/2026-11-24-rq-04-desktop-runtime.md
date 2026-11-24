# RQ-04A — Desktop windowing and rendering runtime

- **Date:** 2026-11-24
- **Task:** P0-R04A, Round 1
- **Researcher:** Researcher-Platform instance A
- **Status:** Research complete; Skeptic disposition and platform execution tests pending
- **Question:** Which Wayland/X11, Windows DX12/Vulkan, macOS Metal, HiDPI, winit event-loop and wgpu surface/adapter constraints determine a narrow, credible first-release desktop baseline?

## 1. Evidence policy and scope

Labels follow `.harness/PROCESS.md`:

- **verified** — supported by a dated primary source or a reproducible local observation.
- **plausible** — indirect or secondary support, or an engineering recommendation whose application to pygpui has not been executed.
- **unverified** — an assumption, unsupported extrapolation, or behavior not tested in this environment.

**verified:** Source and issue state below is as observed on 2026-11-24. Versions are pinned to winit `0.30.13` and wgpu `30.0.2`, the latest stable versions reported by crates.io on that date [S1, S7]. The winit `0.31.0-beta.4` line is not treated as stable [S1].

**verified:** This host is Linux, not macOS or Windows. No macOS/Windows build, launch, screenshot, input, signing, notarization or driver test was performed. No feature code was created. A local `vulkaninfo --summary` observation is recorded in §3; it proves host Vulkan capability only, not winit/wgpu integration correctness.

**verified:** GitHub's unauthenticated API rate-limited partway through issue enumeration. Issue state was then checked on the linked primary GitHub issue pages; mutable issue state must be rechecked by Skeptic [I1–I12].

## 2. Executive recommendation

**plausible:** Use one Rust-owned winit event loop and one wgpu renderer, with an explicit single native backend per OS: **Vulkan on Linux, DX12 on Windows, Metal on macOS**. Do not write three rendering frontends and do not silently use `Backends::all()`.

**plausible:** Pin the initial integration to winit `0.30.13` + wgpu `30.0.2`, enable winit's `rwh_06` handle support, and retain `Cargo.lock`. Their published metadata is compatible at the raw-window-handle major version: winit optionally depends on `rwh_06 = ^0.6`, while wgpu 30.0.2 requires `raw-window-handle = ^0.6.2` [S1, S7]. **unverified:** The pair has not been compiled or run in this workspace.

**plausible:** Initial public support matrix, subject to the gates in §8:

| Platform | Narrow baseline | Windowing | Renderer | Explicit exclusions |
|---|---|---|---|---|
| Linux | Ubuntu 24.04 LTS x86-64, GNOME desktop | Native Wayland and native Xorg; one winit build, Wayland preferred when available | Vulkan only | Other distros/compositors are best-effort; GLES/OpenGL fallback, ARM64, exclusive fullscreen, HDR and transparency are not claimed |
| Windows | Windows 11 25H2 or newer, x86-64 | Win32 | DX12 only, D3D12 feature level 11_0+ and WDDM 2.0+ | Windows 10, Windows on ARM, Vulkan fallback, HDR, transparency and exclusive fullscreen are not claimed |
| macOS | macOS 26 Tahoe, Apple silicon (arm64) | AppKit | Metal only | macOS 15/27, Intel/universal2, Vulkan/MoltenVK, HDR, transparency and eGPU switching are not claimed |

**plausible:** The macOS row intentionally matches the current wgpu CI OS (`macos-26`) and excludes both older systems and the newly released macOS 27 until tested [S14, S23]. Windows 24H2 Home/Pro reached its listed end date on 2026-10-14, before this research date, so it is not a sensible new consumer baseline; 25H2 is listed through 2027-10-13 [S17]. Ubuntu 24.04 LTS has five years of standard maintenance and is also wgpu's Linux CI image [S14, S18].

**plausible:** First-release renderer profile: one opaque SDR sRGB window, `PresentMode::Fifo`, `desired_maximum_frame_latency = 2`, `TextureUsages::RENDER_ATTACHMENT`, no optional wgpu features, and only the device limits the renderer actually needs. `Fifo` is the only presentation mode guaranteed by wgpu, and the default configuration uses frame latency 2 [S11]. Metal's HAL accepts only `Fifo` and `Immediate` [S13].

**unverified:** All integration-correctness and performance claims for pygpui remain unverified until the tests in §8 execute on the named operating systems and real display/GPU paths. Upstream CI and documentation do not substitute for those tests.

## 3. Local Linux observation

**verified:** Reproducible observations on 2026-11-24:

| Item | Observed value |
|---|---|
| OS/kernel/architecture | CachyOS Linux, kernel `6.18.60-3-cachyos-lts`, x86-64 |
| Session | `XDG_SESSION_TYPE=wayland`, `WAYLAND_DISPLAY=wayland-1`, `DISPLAY=:0`, `XDG_CURRENT_DESKTOP=Hyprland` |
| Vulkan tool | `/sbin/vulkaninfo`; instance version `1.4.363` |
| Relevant instance extensions | `VK_KHR_wayland_surface` revision 6, `VK_KHR_xcb_surface` revision 6, `VK_KHR_xlib_surface` revision 6, `VK_KHR_surface` revision 25 |
| GPU0 | NVIDIA GeForce RTX 3060 Ti, proprietary driver `620.73.04`, Vulkan `1.4.357` |
| GPU1 | Intel RPL-S integrated GPU, Mesa `26.3.1-arch3.5`, Vulkan `1.4.363` |
| Headless compositor | `/sbin/weston` exists |
| Not found | `wayland-info`, `Xvfb`, `xvfb-run` |

**unverified:** No winit window, wgpu surface, presentation loop, input path or Wayland frame callback was exercised. These observations cannot certify Ubuntu/GNOME behavior, either GPU's wgpu correctness, or any macOS/Windows behavior.

## 4. Claim ledger — platform and backend selection

| ID | Claim | Label | Evidence and boundary |
|---|---|---|---|
| C01 | winit 0.30.13 exposes Windows, macOS, Unix/X11 and Unix/Wayland desktop backends; Wayland and X11 are default features and `wayland-dlopen` avoids a hard link to the Wayland client library. | **verified** | winit 0.30.13 feature metadata and `FEATURES.md` [S1, S3]. Compile-time availability is not runtime validation. |
| C02 | winit's support matrix marks window creation, resizing, HiDPI and keyboard input as working on Windows/macOS/Linux X11/Wayland, but marks several adjacent features missing or partly broken. | **verified** | Pinned `FEATURES.md` [S3]. The matrix is an upstream support statement, not a pygpui integration result. |
| C03 | wgpu 30.0.2 calls Vulkan, Metal and DX12 first-class backends; OpenGL is downlevel/best-effort. | **verified** | wgpu 30.0.2 README support table [S8]. |
| C04 | wgpu 30.0.2 initializes native HALs in Vulkan → Metal → DX12 → GL order, and the per-backend list order implies adapter priority. | **verified** | `wgpu-core/src/instance.rs` lines 38–41 and 83–90 [S10]. Therefore “DX12 is the Windows default” is false for this version when Vulkan is available. |
| C05 | `Backends::all()` is the default, `PRIMARY` includes Vulkan/Metal/DX12, and `WGPU_BACKEND` only changes selection when an environment-aware constructor/`with_env` path is used. | **verified** | `wgpu-types/src/backend.rs`, `instance.rs`, and wgpu API instance docs [S10, S11]. Explicit `InstanceDescriptor { backends, .. }` without `with_env` is deterministic. |
| C06 | Windows DX12 is the narrow primary baseline; Vulkan is deferred to diagnostic/compatibility testing. | **plausible** | Both are first-class [S8], but DX12 is native to the chosen Windows OS, avoids requiring a separate Vulkan loader/driver, and open Windows Vulkan reports show resize-scaling and presentation variability [I7, I12]. No claim that DX12 is universally more correct or faster. |
| C07 | Microsoft documents D3D12 as requiring a D3D12-compatible GPU and WDDM 2.0 driver; wgpu describes DX12 as Windows 10+. | **verified** | Microsoft Learn updated 2025-03-11 and wgpu backend docs [S15, S10]. The recommended Windows 11 floor is a conservative support-policy choice, not a wgpu minimum. |
| C08 | wgpu's Vulkan backend has distinct Wayland, Xlib and XCB surface paths; its instance requests the corresponding WSI extensions and rejects a handle lacking its required extension. | **verified** | wgpu Vulkan HAL source [S12]. Choosing Vulkan for both Linux protocols is the plausible recommendation in §2; actual driver exposure remains a runtime capability check. |
| C09 | Native Wayland and native Xorg should both be release-gated; an explicitly labelled X11-only preview is acceptable only as a scope reduction, not as a general “Linux desktop supported” claim. | **plausible** | winit supports both [S3], but their scale, redraw, position and occlusion semantics differ [S4–S6, S19, S20]. Ubuntu desktops and current sessions commonly require Wayland; no survey is claimed here. |
| C10 | macOS should use native Metal, not Vulkan/MoltenVK, in the first release. | **plausible** | Metal is first-class on macOS; Vulkan there requires MoltenVK [S8]. Metal introduces AppKit/main-thread and drawable/occlusion constraints that require dedicated tests [S11, S13]. |
| C11 | Apple Metal itself dates to macOS 10.11 and wgpu's Metal HAL says its minimum target is 10.13; neither fact establishes pygpui support on those systems. | **verified** | Apple Metal documentation and pinned wgpu Metal source [S16, S13]. wgpu 30 CI uses macOS 26 [S14]. |
| C12 | Explicit backend masks plus logging `AdapterInfo.backend`, name, vendor/device, driver and driver_info are required for a support claim. | **plausible** | Adapter metadata and backend selection are exposed [S10, S11]. Logging makes the otherwise opaque selection auditable; it does not prove correctness. |

## 5. Claim ledger — winit event, HiDPI and input semantics

| ID | Claim | Label | Evidence and boundary |
|---|---|---|---|
| C13 | winit requires cross-platform `EventLoop` creation on the main thread and only once per application; the type is neither `Send` nor `Sync`. `Window` is `Send + Sync`, but macOS UI interactions may be scheduled to and block on the main thread. | **verified** | winit 0.30.13 `event_loop.rs` and `window.rs` [S4, S5]. |
| C14 | `ControlFlow::Wait` is the idle default; `WaitUntil` supports bounded timers; `Poll` immediately starts another iteration. winit explicitly recommends vsync rather than `Poll` for native-refresh rendering. | **verified** | winit `ControlFlow` documentation [S4]. Leaving `Poll` enabled while Wayland withholds a callback is an integration hazard [I3]. |
| C15 | `RedrawRequested` follows OS invalidation or `request_redraw`; duplicate requests are aggregated. It is not a fixed-rate frame clock and has no strong ordering guarantee relative to other events. | **verified** | winit `Window::request_redraw` and `WindowEvent::RedrawRequested` docs [S5, S6]. |
| C16 | On Wayland, `pre_present_notify` schedules a frame callback used to throttle redraws; it is unsupported on Windows, macOS and X11. winit instructs callers to invoke it after drawing and before submitting the buffer. | **verified** | winit window docs [S5]. pygpui should pair it with an actual present rather than notify and then skip/block indefinitely; that is an integration policy. |
| C17 | `Resized` and `inner_size()` are physical pixels. `ScaleFactorChanged` carries the new per-window scale and an `InnerSizeWriter`; cursor position is physical; `PixelDelta` scrolling is physical while `LineDelta` is lines. | **verified** | winit event/window docs [S5, S6]. Layout and hit testing therefore require an explicit logical/physical conversion policy. |
| C18 | Wayland scale is compositor-suggested per window, using fractional scale when available and integer scale otherwise; X11 uses `WINIT_X11_SCALE_FACTOR`, then `Xft.dpi`, then XRandR dimensions. | **verified** | winit `Window::scale_factor` docs [S5]. Fractional protocol source defines scale numerator/120 and buffer sizing [S19]. |
| C19 | Windows PMv2 supplies raw pixels and `WM_DPICHANGED`; the application must relayout and resize rather than rely on bitmap stretching. | **verified** | Microsoft high-DPI guidance updated 2026-09-10 and winit Win32 `WM_DPICHANGED` handling [S21, S5]. |
| C20 | macOS Retina scaling is reflected in the layer/view backing scale; wgpu's Metal surface computes pixel dimensions from layer bounds × `contentsScale`. | **verified** | winit scale-factor docs and wgpu Metal surface source [S5, S13]. pygpui's own atlas/layout/hit-test response remains untested. |
| C21 | `WindowEvent::Occluded` is unsupported on Wayland and Windows in winit 0.30.13, so a cross-platform render-sleep policy cannot depend on that event everywhere. | **verified** | winit event documentation [S6]. |
| C22 | Keyboard events distinguish `physical_key`, `logical_key`, `text`, `repeat` and `is_synthetic`; X11/Windows synthesize focus-transition key events. IME is off by default and must be enabled for text input; preedit suppresses ordinary key events by contract. | **verified** | winit event/window docs [S5, S6]. Open platform issues mean the contract is not sufficient proof of correct integration [I5, I6, I10]. |
| C23 | On macOS, dead-key composition requires IME to be enabled; disabling IME before window destruction is a required workaround for an open 0.30.13 teardown abort. | **verified** | winit docs and issue #4626 [S5, I10]. The workaround prevents the reported path; it is not an upstream fix. |

## 6. Claim ledger — wgpu surface and adapter limitations

| ID | Claim | Label | Evidence and boundary |
|---|---|---|---|
| C24 | For winit integration, wgpu documents `EventLoop::owned_display_handle()` with `InstanceDescriptor::new_with_display_handle(...)`; a surface's display/window handles must match and outlive it. | **verified** | wgpu 29+ migration notes and v30 surface/instance source [S9, S11]. |
| C25 | `Instance::create_surface` creates surfaces for all backends enabled in the instance. `request_adapter` with `compatible_surface` filters adapters that cannot present to that surface. | **verified** | wgpu API source [S11]. A narrow instance mask avoids irrelevant driver loaders and makes startup diagnostics deterministic. |
| C26 | An incompatible surface/adapter pair is not a usable configuration: `SurfaceCapabilities.formats` and `present_modes` can be empty, and `Adapter::is_surface_supported` exists. | **verified** | wgpu surface capability docs and adapter API [S11]. Never index `formats[0]` without checking. |
| C27 | Adapters expose their supported features and best limits; wgpu device limits/features vary by adapter, and requesting unsupported values panics or fails. | **verified** | wgpu adapter/device docs [S11]. Requesting only what the renderer needs is the plausible policy in §2; a common renderer does not imply identical device limits. |
| C28 | wgpu 30 replaced `SurfaceTexture::present()` with `Queue::present(surface_texture)` and `get_current_texture` returns `CurrentSurfaceTexture`, not `Result<SurfaceTexture, SurfaceError>`. | **verified** | wgpu changelog and API [S9, S11]. Old tutorials are not valid integration evidence. |
| C29 | Surface configuration width/height must be nonzero; configuring while an old `SurfaceTexture` is alive panics. Resize/status handling must drop the old frame before reconfiguration. | **verified** | wgpu surface API and type docs [S11]. Minimized/zero-size windows must skip configuration. |
| C30 | `Success`, `Suboptimal`, `Outdated`, `Lost`, `Timeout`, `Occluded` and `Validation` require different handling: retry `Occluded` when visible, use bounded retry/reconfiguration for `Timeout`, reconfigure or recover for `Outdated`/`Lost`, and route `Validation` to the error handler. | **verified** | wgpu surface status docs and changelog example [S9, S11]. A retry loop must not busy-poll or hide device loss. |
| C31 | The swapchain extent should be kept equal to the physical surface size. When extents differ, behavior is platform-specific; macOS currently scales, and Vulkan drivers can stretch or letterbox. | **verified** | wgpu `SurfaceConfiguration` docs and issue #10196 [S11, I12]. Correctness must not depend on compositor stretch. |
| C32 | Metal surface creation must happen on the main thread; HDR queries on Metal also require the main thread. Metal config sets `CAMetalLayer` drawable size, maximum drawable count and pixel format. | **verified** | wgpu surface API and Metal HAL [S11, S13]. Other rendering-thread choices still need lifetime/thread tests. |
| C33 | DX12 can use FXC, dynamic DXC or static DXC; dynamic DXC needs a compatible `dxcompiler.dll`, otherwise wgpu falls back to FXC. | **verified** | wgpu README and DX12 HAL [S8, S12]. Choice affects packaging and must be recorded; no compiler performance claim is made. |
| C34 | Use a preferred supported sRGB surface format and test color output; format, alpha and present-mode capability lists are adapter/surface-specific. | **plausible** | Capability APIs are verified [S11]; the preferred-format policy is a conservative integration choice. |

## 7. Known issues and contradictions

Issue status is **verified** as observed on 2026-11-24; whether pygpui reproduces it is **unverified** unless stated otherwise.

| ID | Issue/status | Verified evidence | Consequence for pygpui |
|---|---|---|---|
| I1 | winit #4656 — open, Windows redraw starvation under continuous input; reported on 0.31.0-beta.2 | Primary issue page, opened 2026-08-03 [I1] | **plausible:** Test sustained input + redraw on Windows; do not claim the report proves a 0.30.13 defect. |
| I2 | winit #4708 — open, Windows modal title-bar drag is choppy when redrawing every frame; measured on 0.30.13 | Primary issue/search record, opened 2026-09-23 [I2] | **plausible:** Window move/resize responsiveness is a release gate, especially with a render worker. |
| I3 | winit #4668 — open/disputed, Wayland 0.30.13 zero-timeout spin when redraw waits on a withheld frame callback; maintainer removed the bug label | Primary issue page, opened 2026-08-19; `Poll` semantics and eframe-level mitigation discussed [I3] | **verified:** `Poll` can spin by contract. **plausible:** pygpui must not leave indefinite `Poll` while waiting for Wayland callbacks and must test withheld callbacks/occlusion. |
| I4 | winit #4440 — open, macOS cross-monitor `set_outer_position`/`request_inner_size` uses the wrong monitor scale | Primary issue record, opened 2025-12-14 on macOS 26.1 [I4] | **plausible:** Saved geometry and mixed-DPI monitor movement need explicit tests; do not infer all scaling is broken. |
| I5 | winit #4508 — open, Windows IME still emits `KeyboardInput`; `NamedKey::Process` filtering proposed | Primary issue page, opened 2026-03-11 on Windows 11 25H2 / winit 0.30.13 [I5] | **verified:** The documented preedit suppression contract has a platform counterexample. Text insertion and shortcuts need real IME tests. |
| I6 | winit #4526 — open, macOS leaks key-release events after IME composition | Primary issue record, opened 2026-03-17 on macOS 15.7.3 / 0.30.13 [I6] | **plausible:** Focus/shortcut state needs reconciliation tests with Japanese/Chinese IMEs. |
| I7 | wgpu #9937 — open, wgpu 29→30 presentation-time regression reports on Windows Vulkan and Linux RADV | Primary issue page, opened 2026-07-23, updated 2026-11-23 [I7] | **plausible:** Benchmark 30.0.2 on the exact release backends. DX12/Metal were not tested in the original report; do not generalize it to them. |
| I8 | wgpu #9430 — first frame occluded on macOS; fix #10302 merged to trunk 2026-10-20 but is absent from v30.0.2 source/changelog | Issue, merged PR, and v30.0.2 `metal/surface.rs`/changelog comparison [I8, S9, S13] | **verified:** Current stable 30.0.2 still has the pre-fix occlusion check. macOS startup/first-present is a blocking integration test. |
| I9 | wgpu #11001 — open, Metal quick Cmd-Tab away/back can freeze about one second | Primary issue page, opened 2026-11-19; seen on trunk and 29.0.4, macOS 15.7.4/M2 [I9] | **plausible:** Test quick occlusion/restore. Applicability to 30.0.2 is likely from shared logic but not independently established. |
| I10 | winit #4626 — open, macOS active IME composition can abort during 0.30.13 window teardown | Primary issue page, opened 2026-07-13; disabling IME before exit reported as workaround [I10] | **verified:** Teardown ordering must clear IME before dropping the window. |
| I11 | wgpu #8224 — open, Vulkan repeated surface reconfiguration reported to leak memory and slow submit; maintainer asked on 2026-11-09 whether it still occurs | Primary issue page, opened 2025-09-14 [I11] | **plausible:** Linux/Vulkan resize soak and memory measurements are release gates. Avoid reconfiguring on every duplicate resize event. |
| I12 | wgpu #10196 — open, Vulkan swapchain scaling differs by driver while DX12 stretches; no released unified scaling control | Primary issue page, opened 2026-08-29, updated 2026-11-23 [I12] | **verified:** Relying on stretch is unsafe. **plausible:** This supports DX12-first Windows, but Linux still needs exact extent synchronization. |

Additional limitations:

- **verified:** wgpu #7670 remains an open macOS resize-performance report; it does not prove all resizing is broken, but it makes live-resize profiling mandatory [I13].
- **verified:** wgpu #8526 tracks missing pipeline-cache support on DX12/Metal; startup shader/pipeline compilation should be measured and, if needed, warmed before the first visible frame [I14].
- **verified:** winit 0.30.13's `FEATURES.md` still marks Wayland resize increments unsupported, while the same tag's release note says `Window::set_resize_increments` was added on Wayland [S2, S3]. Treat the matrix as stale on that cell and test behavior rather than choosing from either statement alone.
- **verified:** winit 0.31 beta changes IME preedit-before-commit behavior, so code or tests copied from 0.31 documentation are not automatically valid for 0.30.13 [S1, S6].
- **verified:** Upstream CI is evidence of upstream testing, not application integration: wgpu 30.0.2 CI uses `windows-2022`, `macos-26` and `ubuntu-24.04`; it does not certify pygpui, Python wheels, every GPU vendor, or interactive display behavior [S14].

## 8. Required tests before a platform-support claim

These are **plausible release gates**, derived from the verified constraints above. A headless test may supplement but cannot replace real presentation/input tests.

### 8.1 Common runtime gates

| Gate | Required assertion/evidence |
|---|---|
| T01 — pinned build | Build winit 0.30.13 + wgpu 30.0.2 + `rwh_06` from `Cargo.lock` on each target. Record toolchain, target, features and artifact hashes. Cross-compilation alone does not pass runtime gates. |
| T02 — startup/backend | Main-thread event loop and window creation; explicit backend mask; `owned_display_handle`; main-thread surface creation; `compatible_surface`; `is_surface_supported`; first frame presented. Log adapter backend/name/driver and surface capabilities. |
| T03 — failure diagnostics | No adapter, incompatible surface, missing WSI extension, unsupported format/limits and device-loss paths produce a bounded, actionable error rather than panic, busy loop or silent blank window. |
| T04 — surface state machine | Exercise every `CurrentSurfaceTexture` variant with test hooks where natural triggering is impractical. Drop old textures before configure; never configure zero dimensions; recover from Outdated/Lost; skip Timeout/Occluded without spinning; surface Validation reaches the error scope/device-loss handler. |
| T05 — exact resize | During continuous resize, configure to the latest nonzero **physical** `inner_size`; verify rendered content fills the client area and does not depend on stretch. Coalesce duplicate resize notifications. |
| T06 — DPI/hit testing | At 1.0 and at least two fractional scales, compare logical layout, physical framebuffer, text/icon raster scale and click target. Move the same window across displays and change scale while running. |
| T07 — lifecycle | Minimize/restore, maximize/restore, focus/blur, close, surface/window/event-loop drop order, repeated create/destroy, and no use-after-drop of display/window handles. Disable IME before macOS window drop. |
| T08 — input continuity | Key down/up/repeat, synthetic focus events, modifiers, mouse capture/release, wheel and touchpad deltas, text insertion, dead keys, IME preedit/commit/cancel, focus loss during composition, and close during composition. No duplicated commits or stuck modifiers. |
| T09 — idle/responsiveness | With no animation/dirty state, use `Wait`/bounded `WaitUntil`; measure 60 s process and main-thread CPU. During continuous input and rendering, close/move/resize remains responsive. No indefinite `Poll` or `request_redraw` chain. |
| T10 — presentation/color | Golden/checker/gradient screenshots at SDR sRGB on each backend; no banding introduced by the chosen format, no stale stretched frame after resize, `Fifo`, latency 2. HDR is out of scope and must not be enabled accidentally. |
| T11 — device loss | Exercise safe `Device::destroy`/error callbacks and, where vendor tooling permits, a real GPU reset/TDR. The application reports loss and either recreates the device/surface or exits cleanly. |
| T12 — release artifact | Run the installed wheel/app, not only `cargo run`, through T02–T11. Record OS build, GPU, driver, displays, session type and logs. |

### 8.2 Linux — Ubuntu 24.04 LTS x86-64

- **L01 — native Wayland:** GNOME/Mutter session with `WAYLAND_DISPLAY` set. Capture `WAYLAND_DEBUG=1`; verify initial configure/ack before buffer attach, correct `wp_viewport` destination/buffer size, and `VK_KHR_wayland_surface` adapter support [S19, S20].
- **L02 — fractional and fallback scaling:** Test 1.0, 1.25/1.5/1.75 where the compositor supports fractional-scale-v1, and an integer-only fallback. Verify `ScaleFactorChanged`, physical framebuffer and pointer hit-testing.
- **L03 — callback starvation:** Minimize/occlude or use a controlled compositor that withholds `wl_surface.frame`. Verify no zero-timeout spin, no indefinite redraw starvation, bounded CPU, and prompt recovery when callbacks/input resume. Do not wait for unsupported Wayland `WindowEvent::Occluded` [I3].
- **L04 — present pairing:** Instrument that each Wayland `pre_present_notify` is followed by `Queue::present`; skipped/lost acquisitions do not leave a false throttle state.
- **L05 — native Xorg:** Unset `WAYLAND_DISPLAY`; verify Xlib or XCB selection, `VK_KHR_xlib_surface`/`VK_KHR_xcb_surface`, Xft/RandR scaling and focus events. Test XWayland separately and do not label it native Xorg.
- **L06 — Vulkan drivers:** Run the common gates on Mesa (AMD or Intel) and proprietary NVIDIA. The local RTX 3060 Ti + Mesa Intel host is useful smoke evidence only after an application exists; it does not cover Ubuntu/GNOME.
- **L07 — resize/soak:** Repeated rapid resize, monitor hotplug and 30-minute animation/idle cycle with RSS/GPU-memory/submit-time observations, specifically covering wgpu #8224 and #9937 [I7, I11].
- **L08 — headless supplement:** Nested Weston may automate basic lifecycle/scale smoke tests, but visible-window input, focus and real compositor behavior require a logged-in session. The available `/sbin/weston` is not itself a passed test.

### 8.3 Windows — Windows 11 25H2+ x86-64

- **W01 — DX12 only:** Assert `AdapterInfo.backend == Dx12`; D3D12 feature level 11_0+; DXGI surface support; selected shader compiler recorded. Enable the D3D12 debug layer/Graphics Tools in the test configuration.
- **W02 — PMv2 mixed DPI:** Test 100/125/150/175/200%, launch on each scale, move between monitors, dock/undock and change scale live. Verify physical `Resized`, logical layout, cursor/IME position and no bitmap-blurred fallback [S21].
- **W03 — sustained input/redraw:** Continuously move pointer/type while requesting redraws; verify no starvation equivalent to winit #4656. Test title-bar modal drag and live resize for #4708 [I1, I2].
- **W04 — IME:** Windows 11 Japanese and Chinese IMEs: filter `NamedKey::Process` as needed, verify preedit/commit does not double-insert text or trigger shortcuts, and verify release/focus reconciliation [I5].
- **W05 — driver matrix:** At least one current Intel, AMD and NVIDIA DX12 driver. A Windows Server CI runner or software adapter is not sufficient evidence for a consumer GPU claim.
- **W06 — lifecycle/recovery:** Minimize/restore, monitor unplug/replug, close during present, safe device destruction and real TDR where practical. Record driver-version-specific failures rather than hiding them behind a generic “unsupported GPU” message.
- **W07 — performance comparison:** Measure acquire/encode/submit/present separately and compare against wgpu 29.0.4 if investigating #9937. Do not assume a Vulkan result transfers to DX12 [I7].

### 8.4 macOS — macOS 26 Apple silicon

- **M01 — Metal only:** Assert `AdapterInfo.backend == Metal`; surface creation on main thread; Metal API Validation enabled in the test harness; record Mac model, GPU, macOS build and display scale.
- **M02 — first frame:** Test cold visible launch, hidden-then-show, launch while occluded, and show immediately after window creation. A first frame must appear without an resize workaround or permanent blank window. Explicitly covers the logic still present in wgpu 30.0.2 [I8].
- **M03 — quick app switching:** Repeated Cmd-Tab away/back in under one second, plus longer occlusion and partial occlusion. Measure restore latency and event-loop responsiveness; covers #11001 [I9].
- **M04 — Retina/mixed displays:** Built-in Retina plus external 1x display; move window, change arrangement, sleep/wake and reconnect display. Verify layer bounds × `contentsScale`, framebuffer extent, logical layout, pointer and IME cursor area [S5, S13].
- **M05 — live resize:** Drag all edges/corners, maximize/restore and borderless fullscreen. Check stale-frame stretch and profile surface recreation; covers #7670 and the general extent rule [I12, I13].
- **M06 — IME/dead keys/teardown:** Enable IME for text fields, test dead keys plus Japanese/Chinese composition, focus loss/cancel, release-after-commit, and disable IME before close. Repeated close-during-composition must not abort [I6, I10].
- **M07 — SDR only:** Force/test SDR sRGB output even on wide-gamut/HDR-capable displays; no accidental EDR opt-in. wgpu 30.0.2's HDR color-space fixes do not establish an HDR feature claim [S9].
- **M08 — real hardware:** Physical Apple silicon is mandatory for the support claim. A cross-compile or headless Metal test cannot pass M02–M07.

## 9. Upstream support versus integration correctness

**verified:** Upstream support means a crate/API/backend exists, has documentation and is exercised by upstream CI. It does not establish that pygpui selected the correct raw display/window handles, physical extent, scale conversion, device limits, surface mode, status transition, thread affinity, input state or teardown order.

**verified:** The following are integration-owned and currently **unverified** for pygpui: actual adapter selection on hybrid GPUs; Wayland configure/callback behavior; Windows PMv2 and modal-loop responsiveness; Metal first frame/occlusion behavior; resize/color correctness; IME/focus behavior; idle CPU; frame pacing; and installed-artifact behavior.

**plausible:** The narrow baseline reduces variation but does not remove these obligations. A platform may be removed from the release claim if its blocking gates fail; passing upstream's examples is not an exception.

## 10. Contradictions and conservative resolutions

| Contradiction | Resolution |
|---|---|
| “wgpu defaults to DX12 on Windows” versus source order Vulkan → Metal → DX12 | **verified:** Source wins. Set an explicit DX12 mask on Windows [S10]. |
| Wayland resize increments shown unsupported versus 0.30.13 release note adding them | **verified:** Same-tag documentation is inconsistent. Test the behavior; do not claim matrix completeness [S2, S3]. |
| Metal first-frame fix merged before wgpu 30.0.2 release versus released tag still containing old check | **verified:** Merge to trunk is not backport to the v30 release branch. Treat 30.0.2 as unfixed and gate macOS startup [I8, S9, S13]. |
| Metal framework/wgpu minimum macOS is much older than current CI | **verified:** Minimum build target is not a support promise. Use macOS 26 for the first claim [S13, S14]. |
| `RedrawRequested` is encouraged for drawing versus not being a high-rate clock | **verified:** Use it for invalidation-driven rendering; use vsync and a separate scheduling policy for animation. Do not equate it with 120 Hz [S4, S5]. |
| `Occluded` exists in winit versus usable on every desktop | **verified:** It is unsupported on Wayland and Windows in 0.30.13. Use surface status plus conservative wait/dirty-state logic [S6]. |
| Stable crate versions versus current trunk fixes | **verified:** Production baseline stays on stable pins; known stable defects get tests/workarounds or block the affected platform, not an unreleased trunk dependency. |

## 11. Unknowns and Round 2 candidates

| ID | Unknown | Label | Validation that would close it |
|---|---|---|---|
| U01 | Does the pinned winit/wgpu pair build and present on all three baseline targets? | **unverified** | T01/T02 and installed-artifact tests. |
| U02 | Can macOS 26 pass first-frame and quick Cmd-Tab gates on 30.0.2 without a fragile workaround? | **unverified** | M02/M03; otherwise block macOS or wait for a stable backport. |
| U03 | Does wgpu 30.0.2 meet pygpui's presentation/CPU targets on baseline GPUs? | **unverified** | RQ-03 benchmark protocol plus T09/T10; investigate #9937 rather than asserting a regression. |
| U04 | Is Ubuntu 24.04/GNOME Wayland stable under withheld callbacks, long idle and resize soak? | **unverified** | L03/L07 on real GNOME; the local Hyprland/CachyOS environment is not a substitute. |
| U05 | Are macOS 15, Intel Macs, Windows 10/ARM, other Linux compositors and other distros required by users? | **unverified** | User/Architect decision (OQ-03). Each expansion needs its own tests and wheel/CI implications. |
| U06 | Which DX12 compiler should be packaged: FXC, static DXC or dynamic DXC? | **unverified** | W01 plus package-size/license/startup comparison. No external DLL should be assumed present. |
| U07 | Are HDR, transparency, multi-window, multi-GPU switching or exclusive fullscreen first-release requirements? | **unverified** | User scope decision; all are excluded from this recommendation until separately designed/tested. |

## 12. Source registry

All URLs accessed 2026-11-24. Tagged source is preferred over mutable documentation where available.

### Crates, releases and upstream documentation

- **S1:** crates.io API, winit 0.30.13 metadata/features (published 2026-03-02), plus crate version listing showing 0.30.13 latest stable and 0.31.0-beta.4 newest: <https://crates.io/api/v1/crates/winit> and <https://crates.io/api/v1/crates/winit/0.30.13>.
- **S2:** rust-windowing/winit release v0.30.13 (2026-03-02): <https://github.com/rust-windowing/winit/releases/tag/v0.30.13>.
- **S3:** winit v0.30.13 `FEATURES.md`: <https://raw.githubusercontent.com/rust-windowing/winit/v0.30.13/FEATURES.md>.
- **S4:** winit v0.30.13 `src/event_loop.rs`: <https://raw.githubusercontent.com/rust-windowing/winit/v0.30.13/src/event_loop.rs>.
- **S5:** winit v0.30.13 `src/window.rs`: <https://raw.githubusercontent.com/rust-windowing/winit/v0.30.13/src/window.rs>.
- **S6:** winit v0.30.13 `src/event.rs`: <https://raw.githubusercontent.com/rust-windowing/winit/v0.30.13/src/event.rs>.
- **S7:** crates.io API, wgpu 30.0.2 metadata/dependencies (published 2026-11-12): <https://crates.io/api/v1/crates/wgpu> and <https://crates.io/api/v1/crates/wgpu/30.0.2/dependencies>.
- **S8:** wgpu v30.0.2 README/support table and environment variables: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/README.md>.
- **S9:** wgpu v30.0.2 changelog (release date 2026-11-12): <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/CHANGELOG.md>.
- **S10:** wgpu v30.0.2 backend/instance selection: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-types/src/backend.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-types/src/instance.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-core/src/instance.rs>.
- **S11:** wgpu v30.0.2 surface/adapter/instance APIs and capability types: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu/src/api/surface.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu/src/api/adapter.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu/src/api/instance.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-types/src/surface.rs>.
- **S12:** wgpu v30.0.2 DX12/Vulkan HAL instance and WSI code: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-hal/src/dx12/instance.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-hal/src/vulkan/instance.rs>.
- **S13:** wgpu v30.0.2 Metal HAL and surface: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-hal/src/metal/mod.rs>, <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/wgpu-hal/src/metal/surface.rs>.
- **S14:** wgpu v30.0.2 CI matrix: <https://raw.githubusercontent.com/gfx-rs/wgpu/v30.0.2/.github/workflows/ci.yml>.

### OS and protocol primary sources

- **S15:** Microsoft Learn, “Understanding Direct3D 12,” updated 2025-03-11: <https://learn.microsoft.com/en-us/windows/win32/direct3d12/directx-12-getting-started>.
- **S16:** Apple Developer Documentation, “Metal” (framework availability macOS 10.11+) and “Detecting GPU features and Metal software versions”: <https://developer.apple.com/documentation/metal>, <https://developer.apple.com/documentation/metal/detecting-gpu-features-and-metal-software-versions>.
- **S17:** Microsoft Learn, Windows 11 Home/Pro lifecycle, updated 2026-09-29: <https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro>.
- **S18:** Canonical, Ubuntu 24.04 LTS release and five-year standard maintenance (2024-04-25): <https://canonical.com/blog/canonical-releases-ubuntu-24-04-noble-numbat>.
- **S19:** wayland-protocols fractional-scale-v1 XML (copyright 2022; protocol version 1), canonical <https://gitlab.freedesktop.org/wayland/wayland-protocols/-/blob/main/staging/fractional-scale/fractional-scale-v1.xml>, accessed through mirror <https://raw.githubusercontent.com/wayland-mirror/wayland-protocols/main/staging/fractional-scale/fractional-scale-v1.xml>.
- **S20:** wayland-protocols stable xdg-shell XML (version 7), canonical <https://gitlab.freedesktop.org/wayland/wayland-protocols/-/blob/main/stable/xdg-shell/xdg-shell.xml>, accessed through mirror <https://raw.githubusercontent.com/wayland-mirror/wayland-protocols/main/stable/xdg-shell/xdg-shell.xml>.
- **S21:** Microsoft Learn, “High DPI Desktop Application Development on Windows,” updated 2026-09-10: <https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows>.
- **S22:** Apple Support, macOS Tahoe 26 compatibility, published 2026-09-14: <https://support.apple.com/en-us/122867>.
- **S23:** Apple Support, current macOS release/update listing, published 2026-11-09 (includes macOS 27 and Tahoe 26): <https://support.apple.com/en-us/109033>.

### Primary issue/release evidence

- **I1:** winit #4656: <https://github.com/rust-windowing/winit/issues/4656>.
- **I2:** winit #4708: <https://github.com/rust-windowing/winit/issues/4708>.
- **I3:** winit #4668: <https://github.com/rust-windowing/winit/issues/4668>.
- **I4:** winit #4440: <https://github.com/rust-windowing/winit/issues/4440>.
- **I5:** winit #4508: <https://github.com/rust-windowing/winit/issues/4508>.
- **I6:** winit #4526: <https://github.com/rust-windowing/winit/issues/4526>.
- **I7:** wgpu #9937: <https://github.com/gfx-rs/wgpu/issues/9937>.
- **I8:** wgpu #9430 and merged PR #10302: <https://github.com/gfx-rs/wgpu/issues/9430>, <https://github.com/gfx-rs/wgpu/pull/10302>.
- **I9:** wgpu #11001: <https://github.com/gfx-rs/wgpu/issues/11001>.
- **I10:** winit #4626: <https://github.com/rust-windowing/winit/issues/4626>.
- **I11:** wgpu #8224: <https://github.com/gfx-rs/wgpu/issues/8224>.
- **I12:** wgpu #10196: <https://github.com/gfx-rs/wgpu/issues/10196>.
- **I13:** wgpu #7670: <https://github.com/gfx-rs/wgpu/issues/7670>.
- **I14:** wgpu #8526: <https://github.com/gfx-rs/wgpu/issues/8526>.

## 13. Confidence and recommendation

**verified:** The backend and API facts in C01–C05, C07–C08, C11, C13–C23 and C24–C33 are grounded in pinned primary sources or direct local observation.

**plausible:** The narrow matrix and renderer profile in §2 are the lowest-variation credible starting point found in this research. The most important decision is not “which API has the longest support list,” but “which exact OS/backend/display combination has passed the integration gates.”

**unverified:** No pygpui platform is yet verified. The immediate next work is Skeptic falsification, then a minimal cross-platform runtime spike and the tests in §8—not feature implementation.
