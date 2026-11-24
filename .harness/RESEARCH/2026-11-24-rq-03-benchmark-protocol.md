# RQ-03-B — Reproducible performance benchmark protocol

- Task: `P0-R03B`, Round 1, Researcher-Perf instance B
- Date: 2026-11-24
- Status: **protocol proposal; no benchmark implementation, baseline, certified hardware, or performance result exists yet**
- Scope: operationalize the requested 1,000-element, 10,000-row virtualized-list, input-latency, idle-CPU, and no-Python-per-frame targets without asserting that they are attainable.

## 0. Evidence and claim discipline

This document uses the harness labels:

- **verified** — a dated primary source or reproducible reasoning establishes the statement. Source-backed API semantics are verified only as descriptions of those APIs, not as measurements of pygpui.
- **plausible** — indirect evidence supports the statement, but the target environment has not established it.
- **unverified** — an assumption, policy proposal, estimate, or performance target that has not been measured.

**All requested performance numbers remain `unverified`.** The frame budget `1000 / 120 = 8.333333333… ms` is verified arithmetic; sustaining it is unverified. The sample counts, idle threshold, confidence rules, and regression rules below are **proposed policy (`unverified`)**, not claims from a benchmark standard.

OQ-02 remains open: no hardware/OS/driver/display configuration has been approved to certify the targets. Until that decision is made, a run may produce a disclosed local observation, but it cannot certify pygpui generally.

The `python -m pygpui_bench …` commands below are a **proposed harness CLI contract**. That module does not exist in Phase 0. No command in this document has been run as a pygpui benchmark.

## 1. Non-substitution rules

1. **Headless capacity and display-presented pacing are separate claims.** Offscreen render completion cannot prove displayed FPS, compositor behavior, vsync pacing, or input-to-display latency. [verified: S3, S5, S9, S10, S11]
2. **“Input-to-frame” has one named end boundary.** For target certification it means OS input-stack receipt to the first presented frame containing the input's visible response. App-callback-to-render-complete is a component metric, not a substitute. Physical input-to-photon requires an optical measurement or an explicitly calibrated hardware timestamp. [verified boundary distinction: S9, S12; proposed certification policy: unverified]
3. **“Near-zero idle CPU” is not zero and not whole-machine percent.** It is total application process-tree CPU core-seconds divided by wall seconds. Compositor/GPU-service CPU is reported separately. [proposed policy: unverified]
4. **Zero Python calls is an instrumented count, not a sampling impression.** Every steady-state frame window must have zero Rust-to-Python callbacks, zero Python-to-Rust frame entries, and zero render-thread GIL acquisitions; a deliberate sentinel must prove the counters work. [proposed policy: unverified]
5. **No rounding into a pass.** Results retain at least nine significant decimal digits. A displayed `119.9` is not reported as `120` for gate purposes.
6. **No outlier deletion after looking at results.** Warmup is excluded by predeclared markers. A corrupt trace invalidates the whole run. Dropped/late application frames and input timeouts are failures, not exclusions.
7. **No unspecified-machine certification.** A claim must name its environment fingerprint, build, scene hash, raw artifacts, and analysis version. [verified requirement: S1; OQ-02 policy: unverified]

## 2. Primary guidance and what it establishes

All sources were accessed 2026-11-24. Pinned versions/commits are used where practical.

| ID | Primary source | Established fact used here | Label |
|---|---|---|---|
| S1 | Google Benchmark, [User Guide](https://google.github.io/benchmark/user_guide.html) | Warmup results can be discarded explicitly; repetitions report mean and standard deviation; JSON context includes machine information. This supports separate setup/warmup/measurement and environment disclosure. | verified |
| S2 | Google Benchmark, [Benchmark Tools](https://google.github.io/benchmark/tools.html) | `compare.py` warns that its Mann–Whitney comparison needs no fewer than 9 repetitions; performance comparisons are noisy and statistical significance does not prove practical equivalence. | verified |
| S3 | PresentMon [v2.3.1 console documentation](https://raw.githubusercontent.com/GameTechDev/PresentMon/v2.3.1/README-ConsoleApplication.md) | Windows ETW capture exposes CPU/GPU/display metrics, input-to-photon metrics, presentation mode, `MsBetweenDisplayChange`, and dropped-frame handling. `--exclude_dropped` would remove failed presentations and must not be used here. | verified |
| S4 | PresentMon [v2.3.1 README](https://raw.githubusercontent.com/GameTechDev/PresentMon/v2.3.1/README.md) | PresentMon 2.x is Windows-focused; OpenGL/Vulkan instrumentation can make CPU-derived fields less accurate; Hardware-Accelerated GPU Scheduling can distort GPU timing. | verified |
| S5 | Microsoft, [`DXGI_FRAME_STATISTICS`](https://learn.microsoft.com/en-us/windows/win32/api/dxgi/ns-dxgi-dxgi_frame_statistics) | `PresentCount` is not necessarily the number of `Present` calls. Swap-chain frame statistics are limited to flip-model or full-screen swap chains. A call-count FPS is not display FPS. | verified |
| S6 | Microsoft, [DWM frame timing](https://learn.microsoft.com/en-us/windows/win32/dwm/frametiming-ovw) | DWM has separate composition timing and scheduling APIs; application rendering and desktop composition are asynchronous. | verified |
| S7 | Android, [`Choreographer.FrameTimeline`](https://developer.android.com/reference/android/view/Choreographer.FrameTimeline) | Expected presentation time and vsync ID are explicit and correlatable; “expected” is not a measured photon. Android is not a proposed pygpui desktop certification platform, but this is primary frame-pacing guidance. | verified |
| S8 | Android, [Frame Pacing library](https://developer.android.com/games/sdk/frame-pacing) | Submitting as fast as possible can buffer-stuff, add latency, and produce irregular frame times; presentation timestamps and sync fences address pacing; histograms distinguish queue delay and present delay. | verified |
| S9 | Wayland, [presentation-time protocol, commit 819004adb3ab7e46f3fa3caef05b96e20434b244](https://raw.githubusercontent.com/wayland-mirror/wayland-protocols/819004adb3ab7e46f3fa3caef05b96e20434b244/stable/presentation-time/presentation-time.xml) and [protocol model](https://wayland.freedesktop.org/docs/book/Protocol.html) | Presentation feedback has its own clock; `presented` may be approximated; flags distinguish hardware clock/completion. Core Wayland input timestamps have millisecond granularity and an undefined base, so they cannot simply be subtracted from presentation timestamps. | verified |
| S10 | Apple, [`MTLDrawable.presentedTime`](https://developer.apple.com/tutorials/data/documentation/metal/mtldrawable/presentedtime.json), [`addPresentedHandler`](https://developer.apple.com/tutorials/data/documentation/metal/mtldrawable/addpresentedhandler(_:).json), and [`CAMetalLayer.maximumDrawableCount`](https://developer.apple.com/tutorials/data/documentation/quartzcore/cametallayer/maximumdrawablecount.json) | `presentedTime` is the host time when displayed; query it in the presented handler; it is `0` when not presented or dropped. The drawable pool accepts 2 or 3 drawables. | verified |
| S11 | Khronos, [`VK_KHR_present_wait`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_present_wait.html) and [`VkSwapchainPresentFenceInfoKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/VkSwapchainPresentFenceInfoKHR.html) | Present wait finishes when visible but has no precise first-pixel timing guarantee. A swapchain present fence may not wait for the present operation to complete. Neither is an unqualified photon timestamp. | verified |
| S12 | W3C, [Event Timing API editor's draft, 2026-11-13](https://w3c.github.io/event-timing/) and [High Resolution Time editor's draft, 2026-11-06](https://w3c.github.io/hr-time/) | Event Timing distinguishes hardware event time, handler processing, and next rendering update, but reports duration at 8 ms granularity. High-resolution clocks can be coarsened. These are work-in-progress web specifications, used here only as primary cautions about boundary/resolution confusion. | verified |
| S13 | Microsoft, [`GetMessageTime`](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmessagetime) | It is message-queue creation time in milliseconds, not a guaranteed sub-millisecond hardware-input timestamp. It cannot silently certify an 8 ms boundary. | verified |
| S14 | Python 3.14, [`threading.setprofile_all_threads`](https://docs.python.org/3.14/library/threading.html#threading.setprofile_all_threads) and [`sys.setprofile`](https://docs.python.org/3.14/library/sys.html#sys.setprofile) | A profile hook can be installed for current and future Python threads. This is useful corroboration, but native render threads and all FFI boundaries still require native counters. | verified |
| S15 | Mesa, [18.2.3 release notes](https://docs.mesa3d.org/relnotes/18.2.3.html) | That release made EGL swap interval/buffers no-ops for non-window surfaces. This is old, version-specific evidence; current drivers must be probed rather than assumed. It reinforces why surfaceless swapping is not presentation. | verified |
| S16 | Criterion.rs, [Command-Line Options](https://bheisler.github.io/criterion.rs/book/user_guide/command_line_options.html) | `--save-baseline` writes/overwrites a named baseline; `--baseline` compares without overwriting. Unique immutable IDs and archiving are therefore required by this protocol. | verified |
| S17 | pytest-benchmark [5.2.0 usage](https://pytest-benchmark.readthedocs.io/en/v5.2.0/usage.html) | Supports warmup, rounds/iterations control, saved runs, JSON timing data, comparison, and `--benchmark-compare-fail` expressions such as `mean:10%`. | verified |

## 3. Measurement boundaries

### 3.1 Frame timeline vocabulary

For every rendered frame, record the applicable timestamps in one disclosed clock domain:

```text
t_frame_begin       Rust starts the steady-state frame
t_layout_end        layout/invalidation completes, if applicable
t_record_end        render recording/command construction completes
t_submit_begin       present/queue submission begins
t_submit_end         present/queue submission returns
t_gpu_complete       GPU reports relevant work complete
t_displayed          platform/compositor reports first display of this frame
t_photon             calibrated optical/hardware observation of emitted light, if available
```

Derived metrics:

- `cpu_render_ms = t_submit_begin - t_frame_begin`
- `submit_api_ms = t_submit_end - t_submit_begin`
- `gpu_ms = t_gpu_complete - t_gpu_begin` where a GPU-begin timestamp exists
- `submit_to_display_ms = t_displayed - t_submit_end`
- `headless_completion_interval_ms = t_gpu_complete[i] - t_gpu_complete[i-1]`
- `presented_interval_ms = t_displayed[i] - t_displayed[i-1]`
- `presented_fps = 1000 / mean(presented_interval_ms)`
- `dropped_count` from the presentation capture, including frames never displayed

Never substitute `t_submit_end` for `t_gpu_complete`, `t_gpu_complete` for `t_displayed`, or `t_displayed` for `t_photon`. Vulkan present fences and present waits have the limitations in S11. On Windows use `MsBetweenDisplayChange` for display cadence; `DisplayedTime` is dwell duration, not an absolute display timestamp. [verified: S3, S11]

### 3.2 Input-to-frame definition

The certification metric is:

```text
input_to_frame_ms = t_displayed(response_frame) - t_input_os(response_input)
```

- `t_input_os`: timestamp at the OS input stack's receipt of the physical or controller-generated input report, before application dispatch. The exact source and clock must be declared.
- `response_frame`: the first frame whose unique visual response token is presented. A frame rendered before the input, or a frame not containing the token, cannot end the trial.
- If only OS/compositor presentation feedback exists, name the claim **input-to-display**, not input-to-photon.
- If an optical detector/high-speed camera observes the marker with a calibrated shared clock, additionally report **input-to-photon**.
- Headless runs report `input_to_gpu_complete`; they cannot pass the presented input target.

Required component fields per trial:

```text
input_to_dispatch_ms = t_dispatch - t_input_os
dispatch_to_frame_begin_ms = t_frame_begin - t_dispatch
cpu_render_ms
submit_api_ms
gpu_ms
gpu_complete_to_display_ms = t_displayed - t_gpu_complete
input_to_frame_ms
input_to_photon_ms  # nullable; only if calibrated optical capture exists
input_id, response_frame_id, present_id/vsync_id, clock_id, timestamp_source
```

Use one outstanding trial at a time. Each input toggles a fixed 32×32 black/white marker (or selects a row with a unique token), the controller waits for the corresponding presentation acknowledgement, then waits a seeded uniform 0–16 ms before the next input. This avoids input queueing while sampling different phases within a refresh interval. A verified 50 ms response timeout is a failed trial, not an exclusion. [proposed policy: unverified]

Clock validity requirements:

- Both endpoints must be comparable in the same clock domain, or transformed by a measured offset and drift.
- Record clock IDs, resolution, offset, drift, and calibration artifacts.
- Proposed certification requirement: total endpoint uncertainty **<0.25 ms**; unknown or coarser timing makes the run `inconclusive`. This threshold is policy, not source-backed. [unverified]
- Wayland core input timestamps cannot be used directly against `wp_presentation` time (S9). Use a monotonic kernel/libevdev timestamp, instrumented compositor timestamp on a compatible clock, or calibrated external capture.
- Windows `GetMessageTime` alone is insufficient (S13). Prefer PresentMon's ETW-derived `MsAllInputToPhotonLatency` after validation on the exact stack, plus app frame correlation.
- A timestamp taken immediately before `SendInput`, `uinput`, or a controller write measures the injector boundary, not OS receipt. Label it `synthetic_injector_to_display`; it is useful for CI but not physical-input certification.

## 4. Deterministic scenes

Scene construction happens once, before warmup and outside timed regions. It may use Python. No Python call is allowed in a measured frame window. Scene JSON and font/assets are content-hashed.

Common proposed configuration:

- Logical viewport: 1920×1080; device scale factor 1.0.
- Fixed-rate 120 Hz display for presented certification; actual measured refresh also recorded.
- Single fixed window, focused, visible, unobscured, no remote desktop, no recording overlay, AC power.
- Tearing disabled; VRR disabled; HDR disabled unless a separately named scenario requires them.
- A fixed, disclosed headless queue depth of 2; never an unbounded submission queue. Any other depth creates a separately named scenario.
- Packaged font files and SHA-256 hashes; ASCII-only benchmark strings to make glyph coverage deterministic.
- Seed: `0x52513033`; animation phase and input jitter derive from it.
- Scene construction asserts counts and emits a scene hash. Every 1,200th frame, outside the timed hot path where possible, records a structural/state digest for offline correctness verification; no per-frame readback to Python.

### 4.1 `e1000` — 1,000 visible elements

- Exactly 1,000 leaf elements in a 25-column × 40-row grid; no hidden wrapper elements counted as leaves.
- Cell width 76.8, height 27; leaf origin `(4 + 76.8*c, 4 + 27*r)`, size 68.8×22.
- Composition by `i % 10`: 8 filled rounded rectangles, 1 text element (`Item 0000`-style ASCII), 1 vector path. This yields 800 rectangles, 100 text elements, 100 paths.
- All 1,000 are visible at the start of every frame. Full damage every frame.
- Deterministic 1 Hz animation: ±2 logical px translation and opacity variation from a per-element phase. Animation state advances in Rust from elapsed simulation time.
- Geometry is precomputed; layout is not rerun solely because an element translates. This isolates the render/paint path. A separate layout-heavy scenario is required before making layout-cost claims.
- Assertions: `model_element_count == 1000`, `visible_leaf_count == 1000`, scene hash matches, no Python frame entries.

### 4.2 `l10000` — 10,000-row virtualized list

- Model: exactly 10,000 fixed-height rows, row height 32 logical px, content height 320,000 px.
- Viewport height 1,080 gives 34 visible rows including the partial row.
- Overscan: 8 rows before and after, so at most 50 row nodes are retained/mounted.
- Each row has exactly three leaf elements: text (`Row 00000 pygpui`), a 12×12 checkbox rectangle, and a trailing progress rectangle. Root/container nodes are reported separately.
- Continuous scroll at 1,920 logical px/s. A 180 s measured window traverses 345,600 px, covering the entire 10,000-row model once and wrapping.
- Recycling is required. Rendering all 10,000 rows, or retaining more than 50 row nodes, invalidates the virtualization workload.
- Assertions each frame: model row count 10,000; retained row nodes ≤50; visible row IDs are unique, contiguous in the expected range, and nonblank; no row outside the viewport-plus-overscan window remains mounted.
- Report p50/p95/p99 of retained row count, mount/unmount count per frame, and mount/unmount time. Correctness limits are pass/fail assertions, not averages.
- This certifies only fixed-height virtualization. Variable row height, nested lists, images, and complex accessibility trees need separate scenarios. [proposed policy: unverified]

### 4.3 `input` — interactive response

- Use `e1000` as the background scene, with the marker response described in §3.2.
- Test click and key paths separately; do not pool them into one headline percentile.
- 100 warmup trials per process, then 1,000 valid sequential trials per process, 10 processes per input kind.
- No input coalescing: wait for each response presentation before the next trial.
- Every trial has an input ID, response-frame ID, timestamps, and timeout status.

### 4.4 `idle` — quiescent application

- Construct `e1000`, present one final valid frame, then stop animation, scrolling, and application timers.
- The event loop blocks waiting for external events. It must not sleep-poll or render unchanged frames.
- Warmup 30 s; measure 60 s per process, 10 processes.
- App process-tree CPU is sampled at 1 Hz. Also capture context switches, voluntary switches, and wakeups where the OS permits.
- Required: zero application frame submissions and zero application presentations during the measured idle window. Compositor work is separate and disclosed.

## 5. Warmup, repetitions, and sample counts

Each repetition is a **fresh process**. Setup and warmup are excluded by markers, not by deleting slow samples.

| Scenario/surface | Warmup per process | Measured sample per process | Processes | Total measured sample |
|---|---:|---:|---:|---:|
| `e1000` headless | 7,200 completed frames and ≥60 s | 14,400 completed frames | 10 | 144,000 completions |
| `e1000` presented | 30 s and ≥3,600 frames | 120 s / 14,400 target frames | 10 | 1,200 s / 144,000 target frames |
| `l10000` headless | 3,600 completed frames and ≥30 s | 21,600 completed frames | 10 | 216,000 completions |
| `l10000` presented | 30 s and ≥3,600 frames | 180 s / 21,600 target frames | 10 | 1,800 s / 216,000 target frames |
| click input-to-display | 100 trials | 1,000 valid trials | 10 | 10,000 trials |
| key input-to-display | 100 trials | 1,000 valid trials | 10 | 10,000 trials |
| idle CPU | 30 s | 60 s, 1 Hz samples | 10 | 600 s / 600 samples |
| Python-boundary proof | Same as corresponding frame scenario | Same measured frame windows | 10 | Every measured frame window |

Warmup also requires: shaders/pipeline variants and glyph atlas initialized; scene assertions passing; no first-time shader/font/resource initialization or new mount of a resource class during the measured window; and stable thermal/power state. Expected row recycling in `l10000` is not a first-time resource initialization. Proposed thermal-stability check: CPU/GPU temperature changes by no more than 2 °C across the final 60 s of warmup. If stability is not reached after 180 s, mark the run `inconclusive` rather than shortening warmup. [unverified policy]

Ten processes are chosen to permit five ABBA baseline/candidate blocks and exceed S2's minimum warning of nine repetitions. A hot-path CI smoke profile may use one process and fewer samples, but its output is explicitly `ci_smoke`, never target certification.

## 6. Statistics and exact gate semantics

### 6.1 Percentiles and confidence intervals

For a sample of `n` values sorted ascending, percentile `p` is nearest-rank:

```text
index = ceil(p * n) - 1       # zero-based; p50=0.50, p95=0.95, p99=0.99
```

Report count, min, max, mean, standard deviation, p50, p95, and p99 for every latency/duration family. Report p50/p95/p99 both per process and pooled, but never treat correlated frames as independent observations.

For each process compute the run statistic `s_i`. Use exactly **100,000** percentile-bootstrap resamples of the 10 run statistics with NumPy `default_rng(0x52513033)`:

- One-sided 95% lower bound: 5th percentile of resampled statistics.
- One-sided 95% upper bound: 95th percentile.
- Two-sided 95% interval: 2.5th and 97.5th percentiles.
- Resample aggregation: mean for FPS, mean frame interval, and idle CPU; median for per-process p95/p99 latency summaries.
- Quantile method: linear interpolation.
- Store seed, generator/version, resample count, method, and every per-process statistic.

The bootstrap estimates run-to-run uncertainty. With only 10 processes it is coarse; a boundary-straddling interval is `inconclusive`, not a pass. [unverified policy]

### 6.2 Frame target `T120`

```text
T120_ms = 1000 / 120 = 8.333333333333333…
```

**Headless capacity, for each scene:**

- Fixed 14,400 (`e1000`) or 21,600 (`l10000`) completed frames.
- `fps_i = completed_frames_i / (measurement_end - measurement_start)` in seconds; measurement starts immediately before the first steady frame and ends after the last GPU completion.
- Pass requires every process to complete its fixed count, scene correctness to pass, the one-sided 95% lower bound on mean per-process FPS to be **≥120.0**, and each process's headless completion-interval p95 to be **≤T120_ms**.
- p50/p99 remain mandatory diagnostics. This is a capacity result, not displayed FPS.

**Presented pacing, for each scene:**

- Use display-change intervals, including gaps caused by dropped frames. Do not use `Present()` call intervals.
- Pass requires: zero application-dropped frames; every process's mean presented interval **≤T120_ms**; every process's presented-interval p95 **≤T120_ms**; and the one-sided 95% upper bound on mean per-process interval **≤T120_ms**.
- p50/p99 and dropped count are published. Any dropped frame already fails the strict gate.
- **Literal 120 mode is the default.** A panel whose measured refresh is 119.88 Hz can fail the literal `≥120.0` / `≤8.333333…` gate even if marketed as 120 Hz. Report that fact rather than rounding.
- An optional **nominal-120 utilization** diagnostic may report `presented_fps / measured_refresh_hz`, but it cannot replace the literal target unless the Orchestrator/user preapproves a different gate under OQ-02. No such alternative is approved now.

These strict rules are conservative policy proposals. They do not assert that a real renderer will pass. [unverified]

### 6.3 Input target

For click and key separately:

- 10,000 valid trials, 1,000 from each of 10 processes.
- Compute pooled p50/p95/p99 of `input_to_frame_ms` and per-process p95.
- Pass requires pooled p95 **<8.000000 ms**, the one-sided 95% upper confidence bound on median per-process p95 **<8.000000 ms**, zero verified response timeouts, zero unmatched input/frame IDs, and valid clock calibration.
- Any timeout fails. A trace with missing/ambiguous correlation is `inconclusive` and must be rerun after the instrumentation fault is fixed.
- p99 and maximum are mandatory diagnostics. The RQ-03 wording makes p95 the gate; therefore a p95 pass permits only the claim “measured p95 below 8 ms on this stack,” never “all inputs below 8 ms.”
- Headless `input_to_gpu_complete` is not eligible for this gate.

### 6.4 Idle CPU target

For each process:

```text
idle_cpu_core_fraction = (process_tree_user_cpu_seconds + process_tree_system_cpu_seconds)
                         / measured_wall_seconds
```

- Sum all application threads and child processes. Record compositor and GPU-service CPU separately.
- Pass requires every process's idle fraction **<0.01** (less than 1% of one CPU core), the one-sided 95% upper confidence bound on mean idle fraction **<0.01**, zero application frame submissions/presentations, and valid process accounting.
- Report p50/p95/p99 of the 1 Hz core-fraction samples, wakeups, and context switches.
- “Near zero” is thus an explicit proposed threshold, not a synonym for exactly 0%. [unverified]

### 6.5 Python never called per frame

Native boundary counters increment only on boundary crossings; any instrumentation overhead must be measured and disclosed, and the profiling corroboration run is kept out of timing certification. Record for every measured frame window:

```text
rust_to_python_callbacks
python_to_rust_frame_entries
render_thread_gil_acquires
frame_window_id
frame_id
```

Pass requires all three counts to be **0 in every measured window**, across both animated scenes and input-triggered frames. Python is allowed to run during setup and event dispatch outside the frame window.

Required anti-false-zero checks:

1. Before warmup, invoke one deliberate Rust-to-Python sentinel outside a measured frame; its counter must increment exactly once.
2. Before warmup, invoke one deliberate Python-to-Rust frame-entry sentinel; its counter must increment exactly once.
3. Run a separate corroboration pass with `sys.setprofile` and `threading.setprofile_all_threads` (S14), recording all Python-thread profile events inside frame windows. Profiling overhead disqualifies that pass from timing certification.
4. Native counters remain authoritative because Python profiling does not cover every native thread or every possible FFI path.
5. A sampling-only trace, a disabled counter, or a failed sentinel makes the claim `inconclusive`.

### 6.6 Overall statuses

- `pass`: all required gates, correctness assertions, instrumentation checks, and environment approvals pass.
- `fail`: at least one measured gate or absolute correctness/counter rule is violated.
- `inconclusive`: missing capture, clock uncertainty, boundary-straddling CI, failed instrumentation validation, or incomplete samples.
- `not_measured`: default before any valid run.
- `not_certified`: measurements exist, but OQ-02 has not approved the environment for certification.

No average across scenes can hide a failed scene, surface, input kind, or process repetition.

## 7. Hardware/software disclosure and run validity

### 7.1 Required environment fields

| Group | Required fields |
|---|---|
| Identity | UTC start/end, run ID, task/protocol version, operator, host ID, repository commit, dirty-tree state, binary SHA-256, source/benchmark digest |
| CPU | vendor/model/architecture, physical/logical cores, cache sizes, base/measured clocks, governor, EPP/P-state policy, affinity, cgroup CPU quota, SMT state |
| GPU | vendor/model/device IDs, VRAM, driver name/version/date, Vulkan/OpenGL/Metal version and extensions actually used, hardware vs software adapter, GPU scheduling mode |
| Memory/system | RAM size/speed, motherboard/firmware where available, VM/container/bare-metal, power source, thermal/power limits |
| OS/desktop | OS edition/build/kernel, compositor/window manager, session type, graphics session, update channel |
| Display | make/model, connection, native/active resolution, nominal and measured refresh, scaling, HDR/VRR/tearing state, fullscreen/windowed, output ID |
| Software | Python implementation/version/build/GIL/free-threaded state, Rust compiler, Cargo, Cargo profile/flags, lockfile hash, PyO3 version, graphics backend, font/asset hashes |
| Renderer | viewport/DPR, MSAA, color format/space, vsync/present mode, swapchain/drawable count, queue depth, shader cache state, render-thread count/affinity |
| Measurement | capture tool/version/hash, clock IDs/resolution/offset/drift, timestamp source, presented-time semantics, uncertainty, raw file hashes, analysis version/seed |
| Scene | scene ID/hash/seed, element/row counts, visible/mounted counts, animation/scroll law, correctness assertions, draw calls/vertices/texture and glyph-atlas counters |
| Validity | warmup markers, measured markers, dropped/late/missing counts, exclusions (predeclared only), background load, thermal observations, sentinel results, per-gate status |

A changed CPU governor, driver, display mode, DPR, swapchain depth, font set, or build profile invalidates comparison with an otherwise identical baseline unless a compatibility exception was approved **before** the run. [unverified policy]

### 7.2 Preflight and noise controls

- Close unrelated applications; record load average and top CPU consumers before and after every process.
- Use AC power and a fixed performance/power profile; disable sleep, notifications, updates, and automatic display mode changes during a block.
- Keep CPU/GPU temperatures and clocks observable. Record throttling events; a throttled run is not silently deleted.
- Disable overlays, screen recording, remote desktop, and accessibility tooling that injects input unless it is the declared input path.
- Do not run baseline and candidate concurrently.
- Rebuild each binary once before its block; no build occurs during a measurement block.
- Store commands, environment diff, and complete stdout/stderr.

## 8. Platform capture plans and limitations

### 8.1 Windows

- Presented capture: PresentMon 2.3.1 or a later explicitly pinned version, targeting the exact process ID.
- Use v2 metrics, QPC time, GPU tracking, and input tracking. Request display metadata only when the pinned PresentMon CLI supports it, and record the exact option/version. Do not pass `--exclude_dropped`, `--no_track_display`, `--no_track_gpu`, or `--no_track_input`.
- Parse `MsBetweenDisplayChange` for cadence, `MsAllInputToPhotonLatency` for the input metric, and CPU/GPU/display fields for decomposition.
- DWM timing and DXGI statistics are secondary checks. DXGI `PresentCount` is not a call counter and is restricted to supported swap-chain modes (S5).
- Record HWS on/off. S4 warns that HWS and OpenGL/Vulkan can reduce the accuracy of some PresentMon-derived CPU/GPU fields; disclose the limitation and corroborate with native app timing.
- If the required input source/resolution is not available, report synthetic input-to-display only; do not certify physical input latency.

### 8.2 macOS

- Use `CAMetalLayer` with `maximumDrawableCount=2` for the low-latency reference configuration; record any use of 3.
- Register `addPresentedHandler`, read `presentedTime`, and preserve frame/drawable IDs. A zero value is a dropped/not-presented result (S10).
- Use Metal GPU timestamps/events for GPU-complete and `presentedTime` for presentation. Do not infer photons without calibration.
- Optional trace command on a supported Xcode installation, after setting `APP_PID` to the harness-reported pygpui process ID:

```sh
xcrun xctrace record --template 'Metal System Trace' --attach "$APP_PID" --time-limit 150s --output trace.xctrace
```

- Record macOS build, Xcode/trace-tool version, Metal GPU/OS, display ProMotion/VRR state, and whether `presentedTime` was validated against the display. PresentMon 2.x is not the macOS collector.

### 8.3 Linux / Wayland

- Probe compositor, output, and presentation support with `wayland-info`; record `wp_presentation` version, clock ID, refresh, sequence, and flags.
- Capture one `presentation_feedback` per `wl_surface.commit`; record `presented` and `discarded`. Preserve `hw_clock` and `hw_completion` flags. A compositor approximation without calibration is not a photon claim (S9).
- Use `wl_surface.frame` for frame callbacks, but do not treat its callback delivery time as display time.
- For Vulkan, probe `VK_KHR_present_id`/`VK_KHR_present_wait`; use IDs for correlation, but respect S11's timing limitations.
- Input-to-display requires kernel/libevdev or instrumented compositor timestamps in a compatible monotonic clock, or external capture. Core Wayland input timestamps alone are insufficient (S9).
- If the compositor does not expose sufficiently reliable presentation feedback, the presented target is `inconclusive` on that stack.

### 8.4 Linux / X11

- Record X server, driver, Mesa version, GLX/Vulkan extensions, active mode, and VRR state with `xrandr --verbose`, `glxinfo -B`, and `vulkaninfo --summary`.
- Use the X11 Present extension's MSC/notification events only after verifying their semantics and clock mapping on the exact server/driver. An extension's presence alone is not proof of photon timing.
- If only swap completion or estimated vblank is available, report that boundary and leave presented certification `inconclusive`.

### 8.5 Headless/offscreen

- Declare EGL surfaceless/pbuffer, Vulkan offscreen, or other surface type; backend, adapter, and whether a hardware GPU is actually used.
- Use GPU timestamp queries/fences to identify GPU completion. Do not use `glFinish` as the normal per-frame measurement mechanism; it serializes work and changes the workload.
- Software rasterizers such as llvmpipe/SwiftShader are valid smoke tests only, not hardware target certification.
- There is no display-presented FPS, vsync, compositor latency, input-to-display, or photon metric in a truly headless run. S15 is version-specific evidence that EGL swap behavior cannot be assumed to imply presentation.

## 9. Proposed commands

These commands define the future harness interface. Paths and executable names are proposals, not existing tooling.

### 9.1 Manifest and scene verification

```sh
python -m pygpui_bench manifest --output BENCH/results/env.json
python -m pygpui_bench scene verify --scene e1000 --seed 0x52513033 --width 1920 --height 1080 --dpi-scale 1 --output BENCH/results/e1000-scene.json
python -m pygpui_bench scene verify --scene l10000 --seed 0x52513033 --rows 10000 --row-height 32 --overscan 8 --scroll-px-per-second 1920 --output BENCH/results/l10000-scene.json
```

Supporting inventory commands, captured rather than interpreted by hand:

```sh
python -VV
rustc --version --verbose
cargo --version
lscpu
lspci -nnk
glxinfo -B
vulkaninfo --summary
wayland-info
xrandr --verbose
```

Use `system_profiler SPHardwareDataType SPDisplaysDataType` on macOS and `Get-CimInstance`/`dxdiag /t` equivalents on Windows. Store raw output and tool exit codes.

### 9.2 Headless capacity

```sh
python -m pygpui_bench run --scene e1000 --surface offscreen --frames 14400 --warmup-frames 7200 --warmup-min-seconds 60 --repetitions 10 --queue-depth 2 --output-dir BENCH/results/e1000-headless
python -m pygpui_bench run --scene l10000 --surface offscreen --frames 21600 --warmup-frames 3600 --warmup-min-seconds 30 --repetitions 10 --queue-depth 2 --output-dir BENCH/results/l10000-headless
```

### 9.3 Presented pacing

The harness must emit `measure_start`, `measure_end`, frame IDs, and process ID so the collector can be trimmed exactly.

```sh
python -m pygpui_bench run --scene e1000 --surface window --target-hz 120 --warmup-seconds 30 --measure-seconds 120 --repetitions 10 --present-mode fifo --output-dir BENCH/results/e1000-presented
python -m pygpui_bench run --scene l10000 --surface window --target-hz 120 --warmup-seconds 30 --measure-seconds 180 --repetitions 10 --present-mode fifo --scroll-px-per-second 1920 --output-dir BENCH/results/l10000-presented
```

Windows manual equivalent for one 150 s `e1000` capture (30 s warmup + 120 s measured), after setting `$AppPID` to the harness-reported pygpui process ID:

```powershell
PresentMon.exe --process_id $AppPID --timed 150 --terminate_after_timed --output_file BENCH/results/e1000-presented/rep01.csv --v2_metrics --qpc_time_ms --session_name pygpui-e1000-r01
```

Do not add dropped-frame exclusion. The 2.3.1 CLI has no positive `--track_input` switch; input/GPU/display tracking are omitted from disable flags and therefore left enabled. Verify exact options against the pinned binary before use.

### 9.4 Input, idle, and Python proof

```sh
python -m pygpui_bench run --scene input --input-kind click --surface window --target-hz 120 --warmup-trials 100 --trials 1000 --repetitions 10 --timestamp-source os-input-stack --endpoint presented --response-timeout-ms 50 --output-dir BENCH/results/input-click
python -m pygpui_bench run --scene input --input-kind key --surface window --target-hz 120 --warmup-trials 100 --trials 1000 --repetitions 10 --timestamp-source os-input-stack --endpoint presented --response-timeout-ms 50 --output-dir BENCH/results/input-key
python -m pygpui_bench idle --scene e1000 --surface window --warmup-seconds 30 --seconds 60 --sample-hz 1 --repetitions 10 --include-children --output-dir BENCH/results/idle
python -m pygpui_bench prove-python-boundary --scene e1000 --surface offscreen --frames 14400 --repetitions 10 --sentinel --profile-all-python-threads --output-dir BENCH/results/python-proof-e1000
python -m pygpui_bench prove-python-boundary --scene l10000 --surface offscreen --frames 21600 --warmup-frames 3600 --repetitions 10 --sentinel --profile-all-python-threads --output-dir BENCH/results/python-proof-l10000
python -m pygpui_bench prove-python-boundary --scene input --input-kind click --surface window --trials 1000 --repetitions 10 --sentinel --profile-all-python-threads --output-dir BENCH/results/python-proof-input
```

### 9.5 Analysis and target report

```sh
python -m pygpui_bench analyze --input BENCH/results --protocol 2026-11-24-rq-03-benchmark-protocol --bootstrap-resamples 100000 --seed 0x52513033 --output BENCH/results/target-report.json
python -m pygpui_bench compare --baseline BENCH/baselines/<env>/<baseline-id> --candidate BENCH/results/<candidate-id> --threshold-percent 10 --bootstrap-resamples 100000 --seed 0x52513033 --output BENCH/results/regression-report.json
```

### 9.6 Component microbenchmarks required by the performance loop

Hot-path merges must also run the declared Criterion and pytest-benchmark suites. These localize regressions but cannot replace end-to-end frame, input, idle, or presentation evidence. Benchmark target/file names below are proposed and do not exist yet.

```sh
ENV_ID=approved-environment-id
BASELINE_ID=new-immutable-id
BENCH_ROOT="$PWD/BENCH/baselines/$ENV_ID/$BASELINE_ID"
cargo bench --bench pygpui_hot_path -- --save-baseline "$BASELINE_ID"
pytest benches/test_hot_path.py --benchmark-only --benchmark-warmup=on --benchmark-min-rounds=10 --benchmark-save="$BASELINE_ID" --benchmark-save-data --benchmark-storage="file://$BENCH_ROOT/microbench/pytest" --benchmark-json="$BENCH_ROOT/microbench/pytest/results.json"
```

Candidate comparison uses a new run ID and never overwrites the baseline:

```sh
cargo bench --bench pygpui_hot_path -- --baseline "$BASELINE_ID"
pytest benches/test_hot_path.py --benchmark-only --benchmark-compare="$BASELINE_ID" --benchmark-compare-fail=mean:10% --benchmark-storage="file://$BENCH_ROOT/microbench/pytest"
```

Archive Criterion's generated baseline data under the immutable baseline directory; its `--save-baseline` operation can overwrite a reused name (S16). Record exact Criterion/pytest-benchmark versions, benchmark IDs, input hashes, units, aggregation, and raw data hashes. Apply the same >10% formula and diagnosis rule to each predeclared component metric as a separate family; do not average component timings into frame FPS. [verified command semantics: S16/S17; proposed integration policy: unverified]

## 10. Baseline format and >10% regression detection

### 10.1 Minimum repeatable baseline

A baseline is an immutable set containing:

```text
BENCH/baselines/<environment_id>/<baseline_id>/
  manifest.json             # complete environment/build/protocol disclosure
  scenes/<scene-hash>.json  # deterministic scene definitions
  runs/rep01.jsonl … rep10.jsonl
  capture/rep01.csv …       # native presentation/input captures, when applicable
  microbench/criterion/    # archived Criterion output for declared hot-path benches
  microbench/pytest/       # saved pytest-benchmark JSON, when applicable
  raw.sha256
  summary.json              # per-process and pooled statistics
  analysis.json             # code version, seed, bootstrap settings, gate results
  analysis.sha256
```

`manifest.json` and `summary.json` must include at least:

```json
{
  "schema_version": 1,
  "protocol_id": "2026-11-24-rq-03-benchmark-protocol",
  "baseline_id": "<immutable-id>",
  "environment_fingerprint": "<canonical-json-sha256>",
  "source_commit": "<commit>",
  "binary_sha256": "<sha256>",
  "scene_id": "e1000",
  "scene_sha256": "<sha256>",
  "surface": "offscreen|window",
  "metric": "fps|frame_interval_p95|input_to_frame_p95|idle_cpu_core_fraction",
  "unit": "fps|ms|core_fraction",
  "direction": "higher_is_better|lower_is_better",
  "aggregation": "mean_per_process|median_per_process",
  "expected_processes": 10,
  "per_process_values": [],
  "pooled": {"n": "<count>", "p50": "<value>", "p95": "<value>", "p99": "<value>"},
  "bootstrap": {"resamples": 100000, "seed": "0x52513033", "method": "percentile"},
  "gate": {"threshold": "<value>", "status": "pass|fail|inconclusive|not_measured"},
  "evidence_label": "unverified",
  "raw_sha256": ["<hashes>"]
}
```

The placeholders are schema examples, not results. A valid baseline must replace the empty `per_process_values` with exactly ten numbers. A baseline missing any raw run, environment field, or analysis setting is invalid. Baselines are never overwritten; an accepted intentional update creates a new ID linked to its predecessor.

### 10.2 Primary regression family

Automatic regression checks cover these **eight primary metric IDs**:

1. `e1000_headless_fps` — higher is better.
2. `e1000_presented_fps` — higher is better.
3. `l10000_headless_fps` — higher is better.
4. `l10000_presented_fps` — higher is better.
5. `input_click_to_frame_p95_ms` — lower is better.
6. `input_key_to_frame_p95_ms` — lower is better.
7. `idle_cpu_core_fraction` — lower is better.
8. `python_frame_boundary_calls` — absolute zero gate; any nonzero value fails, with no relative-delta calculation.

p50/p99, CPU/GPU components, mount churn, and wakeups are mandatory diagnostics. A >10% deterioration in a diagnostic opens a profiling ticket but does not silently change the primary status. Declared Criterion/pytest-benchmark component metrics form a separate regression family under §9.6 and the same >10% rule.

For lower-is-better metrics:

```text
delta_percent_i = 100 * (candidate_i - baseline_i) / baseline_i
```

For FPS:

```text
delta_percent_i = 100 * (baseline_i - candidate_i) / baseline_i
```

Use the metric's declared run aggregation. In each `A B B A` block, pair `A1` with `B1` and `B2` with `A2`; this yields ten baseline/candidate pairs from five blocks. The headline delta is the median of the ten paired deltas. For a paired-bootstrap interval, resample the ten pairs with replacement, recompute each paired delta, and take the median; use the same 100,000-resample/seed rule as §6.1. Intervals are per metric at 95%; no family-wise significance claim is made across the eight metrics.

- `potential_regression`: headline delta **>10.0%**. Exactly 10.0% is not greater than 10%. This triggers profiling and a written diagnosis immediately, per the performance loop.
- `confirmed_regression`: potential regression and the paired-bootstrap two-sided 95% lower bound for median delta is **>10.0%**.
- `inconclusive`: potential regression but the interval includes or falls below 10.0%. Add one 10-pair block, then another if needed, up to 30 pairs total. If still inconclusive, status remains `inconclusive`; do not call it a pass.
- `no_detected_regression`: headline delta ≤10.0%. This does not prove equality.
- `improvement`: two-sided 95% upper bound for delta <0.
- Baseline value zero: relative change is undefined. Any nonzero Python-call/frame counter is an absolute failure; other zero-baseline metrics use an explicitly predeclared absolute tolerance, never division by zero.

Run ten paired blocks in `A B B A` order, where A is the frozen baseline and B is the candidate. Reject comparisons with different environment fingerprints unless a prior compatibility rule covers the exact difference. Report all paired values, raw hashes, delta, interval, and status. [unverified policy; methodology motivated by S1/S2]

## 11. Required output/claim format

Every result must contain one record per claim:

```json
{
  "claim_id": "e1000-presented-120",
  "claim_text": "On environment <fingerprint>, e1000 sustained at least 120 displayed fps under protocol <id>.",
  "evidence_label": "unverified",
  "claim_status": "not_measured",
  "measured_value": null,
  "unit": "fps",
  "statistic": "mean_per_process",
  "n_processes": 10,
  "n_frames": 0,
  "ci95": null,
  "environment_fingerprint": null,
  "raw_artifacts": [],
  "limitations": ["OQ-02 unresolved"]
}
```

Allowed claim wording after a valid run:

- “Measured headless render capacity of X fps for scene hash H on environment E.”
- “Measured presented p95 interval of X ms and dropped count D on display E.”
- “Measured click input-to-display p95 of X ms using timestamp source S.”
- “Measured idle application CPU of X% of one core; compositor CPU was Y%.”
- “Observed zero instrumented Python calls across N frame windows; sentinels passed.”

Disallowed without the corresponding evidence:

- “The framework supports 120 fps” from one headless run.
- “Input latency is below 8 ms” from app-callback-to-submit timing.
- “Idle CPU is zero” from a task-manager rounded display.
- “Python is never called” from sparse stack sampling.
- “Input-to-photon” without calibrated optical/hardware evidence.
- Any cross-machine generalization from a single environment.

## 12. Claim-level label register

| Claim | Label now | Reason / validation needed |
|---|---|---|
| Frame submit, GPU completion, compositor presentation, and photon are different boundaries. | verified | S3, S5, S9, S10, S11. |
| Headless FPS cannot certify presented FPS or input-to-display. | verified | Platform APIs have separate boundaries; no physical display exists headlessly. |
| 120 Hz corresponds to an 8.333333… ms interval. | verified | Arithmetic only. |
| pygpui sustains 120 fps with 1,000 elements. | unverified | No implementation or measurement. |
| pygpui sustains 120 fps with the defined 10,000-row virtualized list. | unverified | No implementation or measurement. |
| The proposed scenes are representative of all future applications. | unverified | They cover only the declared mixed, fixed-height workloads. |
| pygpui can meet input-to-display p95 <8 ms. | unverified | Hardware, input path, clock calibration, and implementation are unresolved. |
| “Near-zero idle” can be operationalized as <1% of one core. | unverified | Proposed policy; user/Orchestrator approval required. |
| Python can be kept out of every frame window. | unverified | Architecture must implement and pass native counters plus sentinels. |
| Ten processes and the proposed warmups are sufficient for certification. | unverified | Policy informed by S1/S2; validate variance during harness qualification. |
| The >10% regression rule is reproducible. | verified | Formula, pairing, seed, and statuses are fully defined here; its effectiveness at detecting real regressions remains unverified until used. |
| A particular hardware/OS/driver/display stack certifies the targets. | unverified | OQ-02 is open; no stack is selected or measured. |

## 13. Skeptic review priorities

1. Challenge whether strict literal 120 gating is intended, especially on 119.88 Hz panels; do not allow silent nominal-120 substitution.
2. Challenge the <1% one-core idle definition and the <0.25 ms endpoint-uncertainty policy; both are proposals, not measured facts.
3. Verify that each platform collector really supplies the claimed boundary and resolution. Wayland input timestamps and Vulkan present fences are known traps.
4. Require native Python-boundary counters and sentinels; reject sampling-only “zero callbacks” evidence.
5. Check that list virtualization assertions prevent a fake pass that mounts all 10,000 rows.
6. Check ABBA pairing, zero-baseline handling, and the distinction between a >10% potential regression and a statistically confirmed one.
7. Keep OQ-02 blocking final certification until a concrete environment is approved.
