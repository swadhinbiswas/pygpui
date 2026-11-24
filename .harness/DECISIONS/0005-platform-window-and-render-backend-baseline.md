# ADR 0005: Gate a narrow desktop platform and backend baseline

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User approval of OQ-03 is still required for a public support claim.

## Context

Upstream desktop support and pygpui integration correctness are different claims. No pygpui window, wheel, GPU path or physical input test exists. The local Linux Vulkan observation is host capability only. Stable wgpu 30.0.2 still contains the Metal pre-visible occlusion check, while AccessKit requires an invisible window before its adapter is attached.

## Decision

The **candidate certification matrix**, not a current support promise, is:

| Candidate | Windowing | Render backend | Explicit exclusions |
|---|---|---|---|
| Ubuntu 24.04 LTS x86_64, GNOME | native Wayland and native Xorg; Wayland preferred when available | Vulkan only | other distros/compositors, GLES/OpenGL fallback, Linux ARM64, HDR, transparency, exclusive fullscreen |
| Windows 11 25H2+ x64 | Win32 | DX12 only, D3D12 feature level 11_0+ and WDDM 2.0+ | Windows 10/24H2, Windows ARM, Vulkan fallback, HDR, transparency, exclusive fullscreen |
| macOS 26 arm64 | AppKit | Metal only | Intel, universal2, macOS 11/15/27 deployment/support claims, MoltenVK, HDR, transparency, eGPU switching |

- Use one platform-main-thread winit loop and one wgpu renderer with **no render worker**. Construct an explicit `InstanceDescriptor` backend mask; never rely on `Backends::all()` or implicit initialization order.
- Slice 1 renders one opaque SDR sRGB window with `PresentMode::Fifo` and `desired_maximum_frame_latency = 2`. On Metal this means **three drawables**. A two-drawable experiment must set desired latency 1 and be named separately.
- Use `owned_display_handle`, matching display/window handles, `compatible_surface` and `is_surface_supported`; check nonempty format/present-mode lists and request only required features/limits. Log adapter backend, name, vendor/device and driver information.
- Implement a bounded surface state machine for `Success`, `Suboptimal`, `Outdated`, `Lost`, `Timeout`, `Occluded` and `Validation`. Drop old surface textures before configure, skip zero extents, coalesce resizes to the latest nonzero **physical** size and never depend on driver stretching.
- Layout and hit testing use logical coordinates; framebuffer, cursor and IME areas convert explicitly through the current scale factor. Test fractional scaling and monitor changes.
- Idle uses `Wait`/bounded `WaitUntil`; never leave `Poll` enabled while waiting for a withheld Wayland callback. `WindowEvent::Occluded` is not available on Wayland or Windows in winit 0.30.13.
- macOS stays blocked until physical Apple-silicon tests pass the exact sequence **create invisible → attach AccessKit → show → present**, including cold/occluded launch and quick Cmd-Tab. No pre-show first-frame claim is made for stable wgpu 30.0.2.
- Windows release support stays blocked until the FXC/static-DXC/dynamic-DXC strategy is selected, packaged and audited; no external `dxcompiler.dll` is assumed to exist.
- Wayland-enabled artifacts remain subject to the ADR 0009 license gate. An X11-only preview is a scope reduction, not general Linux support.

## Alternatives considered

- **All backends with runtime fallback:** rejected because it obscures selection and creates unverified GLES/Vulkan/Metal compatibility promises.
- **Vulkan-first on Windows:** deferred; DX12 is the narrow native baseline, not a claim of universal superiority.
- **macOS 11 universal2:** rejected for the first matrix; deployment tag, architecture and support floor are distinct and none is verified.
- **Render worker:** rejected for slice 1 by ADR 0001.
- **Rely on upstream CI or cross-compilation:** rejected as a substitute for installed-artifact runtime tests on real displays and GPUs.

## Consequences

- The matrix narrows variation but still requires native builds, real GPU drivers and interactive runners.
- Unsupported platforms may install or run without being supported; release wording must say so.
- Stable dependency defects become explicit tests or platform blockers, not reasons to adopt trunk.
- HiDPI, resize, occlusion, device loss and first-frame behavior are integration-owned work with no current pass claim.

## Evidence links

- [Skeptic §8 — candidate platform defaults](../REVIEWS/phase-0-research-skeptic.md#8-residual-uncertainties-and-conservative-defaults).
- [RQ-04A §2 — narrow baseline](../RESEARCH/2026-11-24-rq-04-desktop-runtime.md#2-executive-recommendation) and [§8 — T/L/W/M gates](../RESEARCH/2026-11-24-rq-04-desktop-runtime.md#8-required-tests-before-a-platform-support-claim).
- [RQ-04A C24–C34 — wgpu surface constraints](../RESEARCH/2026-11-24-rq-04-desktop-runtime.md#6-claim-ledger--wgpu-surface-and-adapter-limitations).
- [Skeptic F-04 — AccessKit/Metal first-frame collision](../REVIEWS/phase-0-research-skeptic.md#nonblocking-findings).

## Validation gates

- **AR05-G1 — pinned native builds:** T01 passes from `Cargo.lock` on all three candidates; artifact hashes, target, features and toolchain are recorded. Cross-compilation alone does not pass.
- **AR05-G2 — common runtime:** T02–T12 pass on installed wheels: explicit backend, first presented frame, actionable failures, every surface status, exact physical resize, DPI/hit tests, lifecycle, input continuity, idle/responsiveness, SDR color and device-loss handling.
- **AR05-G3 — Linux:** L01–L08 pass on Ubuntu 24.04/GNOME Wayland and native Xorg, including Mesa AMD/Intel and proprietary NVIDIA Vulkan, fractional scale, withheld callbacks, present pairing and a 30-minute resize/idle soak.
- **AR05-G4 — Windows:** W01–W07 pass on Windows 11 25H2+ x64 with current Intel/AMD/NVIDIA DX12 drivers, PMv2 mixed DPI, sustained input/redraw, IME, lifecycle/TDR and a recorded shader-compiler strategy.
- **AR05-G5 — macOS:** M01–M08 pass on physical macOS 26 Apple silicon with Metal validation, the invisible/adapter/show/present sequence, cold/occluded first frame, quick app switching, Retina/mixed displays, live resize, IME teardown and SDR output.
- **AR05-G6 — support claim:** a release manifest links passing AR05-G1–G5 evidence for the exact OS/GPU/display/artifact; any missing gate removes that platform from the support claim.

## Revisit when

User requirements expand the OS/architecture floor; a stable wgpu backport changes the macOS first-frame constraint; the Windows compiler strategy is chosen; or a candidate fails a blocking gate. Expansion requires new wheel targets, physical evidence and a superseding ADR rather than inferring support from upstream documentation.
