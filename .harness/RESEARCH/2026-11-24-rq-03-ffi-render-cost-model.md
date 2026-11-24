# RQ-03 — FFI/render cost model

Date: 2026-11-24
Researcher: Researcher-Perf instance A
Task: P0-R03A, Round 1
Status: research complete; no implementation or benchmark exists

## BLUF

**A callback-free steady-state frame is a testable native-runtime property, not an implication of writing the frame loop in Rust. Guarantee it by accepting complete Rust-side snapshots, scheduling all recurring motion in native code, keeping Python references out of the frame path, and waking Python only for explicit external inputs.** A Python per-frame render callback, `on_next_frame` callback, Python measure function, Python animation tick, signal/pending-call drain, Python-controlled virtual-list provider, or Python object destruction during a frame falsifies the claim.

**None of the requested performance targets is verified here.** The targets are **120 fps**, **1,000 elements**, **10,000 virtualized rows**, **input-to-frame p95 below 8 ms**, **idle CPU near zero**, and **zero Python callbacks per steady-state frame** [RQ03]. All are **[unverified]**. This report supplies a cost model and falsification experiments; it contains no invented pygpui measurements.

### Evidence and number labels

- **[sourced]** — a dated primary source or reproducible local observation supports the statement. A source's own benchmark is not a pygpui result.
- **[estimated]** — a capacity-planning assumption or arithmetic model, not a measurement of pygpui.
- **[unverified]** — a target, proposed gate, hypothesis, or unsupported claim requiring measurement.
- Every quantitative claim below carries one of these labels. Claim IDs (C01, etc.) are stable review handles.

## 1. Decision-driving claims

| ID | Claim | Status | Evidence / limit | Falsifier |
|---|---|---|---|---|
| C01 | If the native runtime owns scheduling, presentation, scene evaluation, and recurring animation, a stable frame can execute without Python bytecode or a Python C-API call. | **verified** as an architectural statement | CPython permits long native code without an attached thread state; PyO3's native closure can use `detach` [S01, S03]. This does not prove a particular binding has no hidden Python dependency. | Any `Python::attach`, `Bound`/`Py` access, Python callable invocation, Python finalizer/refcount update, signal check, pending-call drain, or Python-derived callback discovered on a stable frame. |
| C02 | An unconditional callback-free guarantee requires more than event-only invocation: steady native animation must not call Python each tick, and event notification must not re-enter Python. | **verified** | PyO3 calls into Python require attachment [S01, S03]. Existing Rust UI code distinguishes next-frame callbacks from retained-scene animation [S08, S09]. | A timer, animation, accessibility update, missing-glyph handler, or worker completion attaches to Python during the measured interval. |
| C03 | The binding boundary should execute Python callbacks once per input batch and return a complete, detached snapshot; moving Python calls to a worker thread without removing them does not satisfy C01. | **plausible** | Reproducible isolation design derived from S01/S03; no pygpui implementation exists to audit. | `Python::attach` or Python-object access in the render thread's steady-state call graph. |
| C04 | `120 fps` on a fixed-refresh physical display requires a **120 Hz** presentation path; otherwise the correct headless claim is throughput, not displayed frame rate. | **verified** | wgpu `Fifo` presents one queued frame per vertical blank and re-presents old frames; display refresh controls cadence [S05]. | A measured physical 120 Hz display/presentation trace showing 120 distinct presented frames per second. |
| C05 | A virtualized list's native cost should be bounded by visible rows plus bounded overscan, not by total rows, **if** row geometry is uniform or indexed and no Python row provider runs per frame. | **verified** for the cited uniform-list implementation; **plausible** for pygpui | GPUI computes a visible range and lays out only those items, but its `render_items` callback is invoked during prepaint [S10]. That is evidence for the algorithm, not for pygpui's callback freedom. | Measured work scaling with total row count, or Python execution in range/materialize/layout. |
| C06 | Retained-tree reuse, layout caching, batching, and atlases can remove large repeated costs; none can be assumed effective from the algorithm's presence alone. | **verified** | Primary implementations expose dirty paths, cache keys, batch boundaries, and atlas upload queues [S07–S15]. Their existence does not establish hit rate or timing. | Correctness tests plus counters show cache misses, unnecessary full-tree walks, atlas thrash, or one state transition per primitive. |
| C07 | Input-to-frame latency cannot be inferred from CPU frame duration. It includes native/OS dispatch, possible Python work, queueing, render submission, GPU completion, and present. | **verified** | wgpu documents blocking/backpressure in surface acquisition and presents after submit [S05]; platform APIs add compositor/vblank stages [S16, S17]. | A timestamped end-to-end trace that attributes all stages and still misses the target. |
| C08 | The three PyO3 API variants that can invalidate a no-callback claim are native-created-thread attach, `detach`/reattach, and Python finalizers/reference counting. | **verified** | PyO3 attach creates/destroys thread state when needed and can block; detach reacquires on exit; CPython object access is attachment-bound [S01, S03]. | Attach/detach counters and Python refcount/finalizer counters remain nonzero on stable frames. |

## 2. Scope, assumptions, and exclusions

### Assumptions (all **[estimated]** planning inputs, not measured facts)

1. **A1 — workloads.** The 1,000-element scene is a deterministic tree with rectangles, text, clipping, and overlap; the 10,000-row case uses uniform-height virtual rows with bounded overscan. Real row-height variability, wrapping text, images, shadows, and arbitrary Python layout are separate stress cases.
2. **A2 — native snapshot.** Python produces an immutable, Rust-owned snapshot outside the render loop. The frame path uses native IDs, numeric values, strings already decoded to Rust, and callbacks only in explicitly event-driven native cells.
3. **A3 — stable frame.** “Steady-state frame” excludes startup, window resize, theme/font/device changes, input batches, user code execution, asset misses, and surface reconfiguration. Animation-only frames may be included **only if their animation definitions are native and terminate without Python**.
4. **A4 — platform.** Linux is used for initial CPU/headless work; physical-presentation certification is required on each supported desktop platform. No benchmark hardware, GPU, display refresh, or display-capture instrumentation has been certified.
5. **A5 — frame deadline.** A 120 Hz display gives **8.333 ms** between refreshes **[sourced arithmetic from 1 / 120]**. An internal CPU budget is **6.667 ms** **[estimated]**, leaving **1.667 ms** **[estimated]** for submission/present margin. This is a budget policy, not a measured requirement.
6. **A6 — latency boundary.** The requested **p95 < 8 ms** [RQ03] is initially interpreted as hardware-input timestamp to first submitted frame that visibly responds. “Input-to-photon” needs a calibrated external display timestamp and is a separate, stricter claim.
7. **A7 — idle.** “Near zero” is undefined. Proposed gates in §12 are **[unverified]** until the Orchestrator accepts an operational definition and measurement noise floor.

### Explicitly excluded from this model

Browser/WebAssembly scheduling; mobile lifecycle; accessibility and IME correctness (cost is included only as a falsifier); OS-specific window-decoration work; multi-window contention; arbitrary Python `measure()` callbacks; Python-backed asset providers during a frame. These are not declared free—they are outside the initial bounded claim.

## 3. FFI, GIL, and the callback-free frame

### 3.1 Cost components

PyO3 0.27 distinguishes a zero-cost token already carried by an extension call from `Python::attach`, which performs runtime checks, can create/destroy a thread state on a native-created thread, and can block acquiring the GIL [S01]. In a GIL-enabled build, CPython attachment blocks until the GIL is available; even free-threaded attachment can block during GC or if the GIL is re-enabled [S02]. `Python::detach` releases the attachment for Rust-only work and reacquires it when the closure exits, including panic unwinding [S01, S03].

| Operation | Cost-model term | Evidence status | Notes |
|---|---|---|---|
| Python → Rust event entry | `B_py_entry` | **[unverified]** | Includes Python-to-FFI call, argument conversion, and snapshot extraction. Batch this work; do not repeat per element. |
| Native frame → Python callback | `C_attach + C_wait_gil + C_python + C_exception/return` | **[unverified]** | `C_wait_gil` is unbounded under contention; it cannot be given a safe fixed latency estimate. |
| Rust work while already attached | `R_native` plus GIL-hold opportunity cost | **[verified]** mechanism; cost **[unverified]** | Long layout/paint work should normally run detached if Python threads must progress. |
| Rust frame from persistent native thread | `0` Python calls by construction, **if** no attach/object access/finalizer occurs | **verified** architectural condition | A native thread does not need a Python thread state for pure Rust work [S01, S02]. |
| Drop of `Py<T>` / Python-backed object during frame | Potential refcount/finalizer work under attachment | **verified** mechanism [S01, S03] | Defer dropping Python-backed handles to an event-drain boundary; keep only native handles in the frame arena. |
| Python signal/pending call handling | Potential arbitrary Python execution | **verified** [S01, S02] | Do not call `check_signals`, `Py_AddPendingCall`, or drain Python work in the steady frame path. |

There is **no universal nanosecond cost for a GIL transition** in the primary sources. Any such number would be fabricated for this project. Measure attach, detach, callback, and contention distributions on the target Python builds.

### 3.2 Architecture that can guarantee C01/C02

The guarantee is scoped to an audited native call graph:

1. **Boundary actor.** Python calls one native event/submit function with the GIL held. The function validates and converts input, constructs an owned snapshot, and schedules native work.
2. **Detached native runtime.** After the Python call returns (or inside a carefully bounded `detach` region), a persistent Rust thread owns event queues, clocks, retained state, layout, paint, GPU submission, and frame scheduling. It stores no borrowed `Bound<'py, _>` values. `Py<T>` handles, if unavoidable, are confined to the event actor and dropped there. Releasing the GIL is not a universal frame deadline guarantee: reacquisition can wait, and other Python work can contend for CPU and allocator resources [S01, S02].
3. **Closed scheduling vocabulary.** Frame demand comes from native input, native timers, native animation state, compositor callbacks, and asset-completion messages. The vocabulary contains no “call Python every frame,” no Python animation tick, and no per-frame notification bridge.
4. **Retained native scene.** A dirty tree/layout/display-list cache can be rebuilt in Rust. An animation can transform retained primitives without reconstructing the element tree. GPUI provides primary evidence that this split is implementable: `Scene::advance_animations` mutates retained sprites, while `request_animation_frame` instead installs a next-frame callback [S08, S09]. In pygpui, no native code, callback, destructor, or resource may be reachable from a Python object unless its frame-time behavior is explicitly excluded from the guarantee.
5. **Bounded virtual list.** Visible-range computation, uniform/indexed geometry, clipping, row materialization, and painting are native. Python may supply row data at event time, but cannot be the per-frame row factory unless the callback-free claim is narrowed.
6. **Stable dependency closure.** Native text shaping/rasterization, font fallback, hit testing, accessibility updates, and asset decode do not call Python in the steady path. Any missing glyph, font change, or asset callback goes to the event queue for a later Python notification.
7. **Observable invariant.** Production counters record Python entries, attach/detach pairs, Python-object accesses, Python finalizers, and native frame count. CI asserts zero Python entries during a marked stable-frame window; counters are sampled/aggregated, not logged per frame.

### 3.3 What falsifies the claim

| Falsifier | Why it breaks C01/C02 | Required response |
|---|---|---|
| Python `Render::render` or `paint` equivalent each frame | Direct Python bytecode in every draw | Redesign as retained native state or weaken the claim. |
| `on_next_frame`/`request_animation_frame` used for steady animation | Callback executes before draw [S08, S09] | Use retained-scene/native timeline animation. |
| Python `measure()` or row provider during layout | Called while producing layout/prepaint [S07, S10] | Precompute/cache outside frames or route through native owned data. |
| Python timer wheel / `asyncio` drives frame cadence | Requires Python wakeup each tick | Move clock/timeline to native scheduler. |
| Python signal handlers, pending calls, GC finalizers, or `Py<T>` drops | Python can run or attach during the frame | Keep the frame path detached and purge Python refs at event boundaries. |
| Worker calls Python then posts a per-frame completion | Callback occurred even if render thread is Rust | Remove the Python work or redefine “steady state.” |
| Accessibility, IME, missing glyph, asset, logging, or error handler enters Python | Hidden callback in a nominally native phase | Audit the complete dependency graph; narrow scope if intentionally callback-driven. |
| Native→Python notification is coalesced but still called each frame | Coalescing reduces count, not to zero | Batch and deliver asynchronously at event boundaries, never in render loop. |

A test with a callback deliberately sleeping proves **dependency**, not its normal cost. A separate uninstrumented test measures latency.

## 4. End-to-end cost model

### 4.1 Definitions

For frame `f`:

```text
T_cpu(f) = T_queue + T_diff + T_layout + T_hit + T_paint
          + T_text + T_animate + T_gpu_encode + T_submit + T_present_call

T_gpu(f) = GPU execution time for the submitted command buffer

T_present(f) = submit/present-call completion → display latch (platform-specific)

T_input_to_frame = T_os_input_dispatch + T_event_drain/Python (if any)
                 + T_wait_for_frame_slot + T_cpu(f)

T_input_to_photon = T_input_to_frame + T_gpu(f) + T_present(f)
```

CPU and GPU may overlap across frames; therefore summing one frame's CPU and GPU durations is not generally its latency. Measure timestamps and queue depth. wgpu `Fifo` can block in `get_current_texture` when its approximately three-frame queue is full [S05].

**[estimated]** At 120 Hz, `T_frame = 8.333 ms`; at 60 Hz, `T_frame = 16.667 ms`. Missing the deadline creates cadence/phase errors; an uncapped immediate loop can also cause queue stuffing rather than useful extra displayed frames [S05, S16].

### 4.2 Native frame budget allocation

These are **planning allocations, not benchmark results**. They are intended to expose which component owns a miss.

| Component | Initial 120 Hz budget | Label | Scaling driver |
|---|---:|---|---|
| Event drain / queue | 0.20 ms | **[estimated]** | events per batch, allocations, coalescing |
| Retained-tree dirty/diff | 0.35 ms | **[estimated]** | changed nodes + ancestor paths + retained replay volume |
| Layout invalidation/compute | 0.80 ms | **[estimated]** | dirty subtrees, cache misses, text measurement |
| Hit testing | 0.20 ms | **[estimated]** | candidate hitboxes/clip masks; cache hit rate |
| Paint/display-list build | 0.80 ms | **[estimated]** | visible primitives, layers, clips, replays |
| Text lookup/shape/glyph cache | 0.70 ms | **[estimated]** | visible glyphs, cache misses, shaping/fallback |
| Animation + scrolling | 0.25 ms | **[estimated]** | active native timelines, visible-range churn |
| GPU encode/bind/upload/submit | 1.50 ms | **[estimated]** | batches, state changes, instance bytes, atlas uploads |
| Present-call reserve | 0.40 ms | **[estimated]** | swapchain/backpressure/platform |
| **Planned stage total** | **5.20 ms** | **[estimated]** | diagnosis budget, not a measured CPU ceiling |
| Safety / scheduling reserve | 3.13 ms | **[estimated]** | CPU/GPU variance and OS scheduling |
| **Total refresh interval** | **8.333 ms** | **[sourced arithmetic]** | fixed 120 Hz display |

The earlier **6.667 ms / 1.667 ms** split in A5 is an alternative coarse policy **[estimated]**, not an additional measured cost. Use the component table for diagnosis, and let profiling decide whether the reserve belongs to CPU or GPU.

### 4.3 Event queues

**Model [estimated]:**

```text
T_queue ≈ Q_length × C_dequeue + C_coalesce + C_wake + C_batch_alloc
T_queue_wait ≈ max(0, arrival_work_rate × service_time / (1 - utilization))
```

The second expression explains tail growth near saturation; it is not a queueing guarantee. Use an MPSC or native event-loop queue with bounded capacity, sequence numbers, timestamps, and coalescing only where semantics permit (latest scroll offset, latest pointer position). Preserve ordered events for input/IME correctness. Never let an unbounded Python producer queue grow silently.

Measure queue depth at frame start, drain time, dropped/coalesced count, and wake-to-drain latency. Winit's primary contract provides `Wait`, `WaitUntil`, and `Poll`; duplicate redraw requests are aggregated [S06]. `Poll` is not an idle strategy.

## 5. Retained-tree diffing and layout invalidation

### 5.1 Cost model

**[estimated]** Let `N` be retained nodes, `K` changed nodes, `A` their ancestors, `V` visited nodes, and `R` replayed paint records:

```text
Naive rebuild:       O(N)
Dirty-path rebuild:  O(V + R), where V ≲ N and R depends on subtree size
Clean redraw:        O(R_reused + GPU work), ideally no O(N) Python work
```

A full native scan of 1,000 or 10,000 nodes can still fit a frame; the model does not declare it fatal. The dangerous cases are Python per-node traversal, unstable identity causing total rebuilds, ancestor invalidation fan-out, and replaying/cloning a large subtree for a tiny change.

### 5.2 Primary evidence

- GPUI keeps an invalidator with dirty views and marks ancestor views dirty; it stops ancestor traversal when an already-dirty view is found [S07].
- GPUI reuses prepaint/paint ranges by replaying scene, input, listener, layout, and accessibility-related state; this is retained-record replay, not a generic O(changed-node) diff [S07].
- Taffy 0.16 marks a node dirty by clearing its cache and recursively clearing ancestors only when a cache was actually cleared [S11]. Its cache keys include available space, known dimensions, sizing mode, and axis; a clean input still incurs lookup/rounding work [S11, S12].
- Taffy's current relayout benchmark explicitly distinguishes incremental cache lookup from fresh-tree layout [S13].

### 5.3 Invalidation strategy

Use stable IDs and typed dirty flags: `structure`, `style`, `text`, `paint`, `hit`, `accessibility`, `asset`. Invalidate the minimum correct ancestor path. Keep transform/opacity animation in paint-only state so it does not dirty layout or hit-test shape. Scroll changes should update native transforms, visible ranges, clipping, and hit indexes without rebuilding all row state.

Counters must separate: nodes visited, nodes changed, ancestors dirtied, cache hits/misses, records replayed, and bytes copied. A cache hit rate alone can hide a full-tree scan.

## 6. Hit testing

**Model [estimated]:**

```text
T_hit_naive = O(H × C_bounds_intersection)
T_hit_spatial = O(log H + C_candidates), plus rebuild cost on geometry changes
```

GPUI's current hit test walks hitboxes in reverse paint order, intersects bounds with content masks, and stops at `BlockMouse`; the mouse hit test is recomputed for mouse dispatch and during draw [S14]. This is simple and correct but not a spatial index.

Recommendation: preserve paint-order semantics with a native broad phase (uniform grid, BVH, or interval tree), then exact bounds/clip tests on candidates. Rebuild or update the index only for geometry/hit-tree changes. Pointer movement with no layout change should be event-time work, not full-tree layout.

Test overlapping clips, `BlockMouseExceptScroll`, transforms, captured pointers, offscreen content, and virtualized rows. Measure candidates tested, exact tests, index rebuilds, and hit-test p50/p95/p99 separately from frame time.

## 7. Painter batching, instancing, and GPU submission

### 7.1 Cost model

**[estimated]** For `P` visible primitives, `B` batches, `S` state changes, `U` upload bytes, and `I` instance bytes:

```text
T_paint ≈ P × C_primitive_emit + alloc/copy cost
T_encode ≈ B × (C_pipeline + C_bind + C_draw) + S × C_state + I/C_write_bandwidth
T_gpu   ≈ rasterized_pixels × shading_cost + vertex/fragment work + bandwidth
```

Instancing reduces draw/state overhead; it does not make overdraw, blending, clipping, or texture bandwidth free.

### 7.2 Primary evidence

- wgpu render passes encode draw commands; `draw` takes vertex and instance ranges; `execute_bundles` replays pre-recorded commands [S04].
- GPUI's scene sorts primitives sharing a draw order by kind and atlas texture to improve batching, while preserving required overlap order [S15].
- GPUI's wgpu renderer writes typed instance arrays, creates bind groups, iterates scene batches, issues instanced draws, and submits one command buffer [S17]. Sprite batches also bind an atlas texture; path tiles add curve/paint data.
- The cited renderer still allocates a `Vec` for path data and per-frame bind groups, and its atlas upload queue is drained before frame rendering [S17, S18]. These are optimization targets, not measured bottlenecks.

### 7.3 Recommended strategy

1. Flatten visible elements into native display-list primitives with stable keys.
2. Sort only within legally shared draw-order groups by pipeline, blend, clip, and texture.
3. Use one quad mesh and instance buffers for rectangles/text/sprites where supported.
4. Cache static bind groups by pipeline/layout/texture generation; pool dynamic instance buffers.
5. Prefer retained geometry for static subtrees; replay it rather than re-running Python/Rust element callbacks.
6. Treat each opacity layer, clip change, texture switch, or incompatible blend as a batch boundary. Measure the boundary reasons.
7. Keep a fallback path for devices without optional instancing/multi-draw features; feature detection is not performance portability.

Do not adopt indirect/multi-draw before measuring. Indirect execution has feature requirements, and the renderer may add complexity without reducing the dominant fill cost [S04].

## 8. Glyph atlases and text

### 8.1 Separate the text stages

```text
Text layout: Unicode → shaping → glyph IDs/advances → line boxes
Raster cache: (font, glyph, size, weight, subpixel bin, flags, scale) → bitmap
Atlas: bitmap → packed GPU tile; draw: tile + transform + color
```

These have different invalidation keys and costs. A shaping cache is not a glyph atlas; an atlas hit is not a shaping hit.

### 8.2 Cost model

**[estimated]** For visible glyphs `G`, glyph-cache hit rate `h_g`, atlas hit rate `h_a`, shaped-run hit rate `h_s`, and upload bytes `U`:

```text
T_text ≈ G×(1-h_s)×C_shape_lookup + G×(1-h_g)×C_raster
        + G×(1-h_a)×C_atlas_alloc + U/C_upload_bandwidth + G×C_draw_emit
```

Cold/mixed text can dominate despite a small element count. Subpixel variants, font weight, size, scale, dilation, emoji mode, and hinting flags multiply cache keys.

### 8.3 Primary evidence

- cosmic-text provides shaping, layout, rasterization, fallback, and optional shape-run caching; `ShapeRunCache` is keyed by text and attributes and trimmed by age [S19, S20].
- cosmic-text's glyph cache keys include font ID, glyph ID, font size bits, X/Y subpixel bins, weight, and flags; it uses four X subpixel bins and four Y bins [S21]. Those are implementation choices, not required pygpui constants.
- GPUI's current glyph key includes font/glyph/size/subpixel/scale/emoji/subpixel-rendering/dilation, with four X variants and one Y variant [S22].
- GPUI's wgpu atlas queues per-tile uploads, flushes them before frame rendering, and creates a minimum **1024×1024** atlas texture [S18]. The **1024×1024** value is **[sourced]** for this implementation, not a universal optimum.
- cosmic-text documents that system-font initialization can take up to **one second** in release and longer in debug; this is a source statement, not a pygpui measurement [S19]. It is startup cost and must not be placed in a steady frame.

### 8.4 Recommended strategy

Use native shaping and rasterization with bounded caches and a single glyph-atlas packing policy per texture kind. Prewarm visible text before interaction when possible. Treat font installation, DPI change, theme/dilation change, and device recovery as explicit invalidation events. Report shaping misses, raster misses, atlas allocations, eviction, upload count/bytes, and texture count.

Validate with ASCII, CJK fallback, Arabic/bidirectional shaping, emoji, mixed weights/sizes, fractional scroll, subpixel and grayscale modes, and a long scrolling document with a working set larger than the atlas.

## 9. Animation and scrolling

### 9.1 Animation classes

| Class | Native steady-frame behavior | Python callback? | Status |
|---|---|---|---|
| Transform/opacity/color of retained primitive | Update native timeline and repaint/submit retained scene | No | **verified** mechanism in GPUI [S08] |
| Element-tree animation (`with_animation`) | Rebuild/notify through next-frame callback | Yes in cited implementation | **verified** [S09] |
| Native scrolling with fixed/indexed row heights | Update offset, visible range, transforms, clip, and hit index | No, if rows are native | **verified** algorithm; pygpui **[unverified]** |
| Variable-height/lazy row materialization | Recompute affected ranges/geometry | No only if native and cached | **plausible** |
| GIF/video/canvas simulation | Native decode/update/present | No if native pipeline | **plausible** |
| Python tween/timer/canvas callback | Python each tick | Yes | **verified** disqualifier |

**Model [estimated]:** `A` active native animations cost `O(A)` transform/color updates plus repaint cost. Scrolling costs `O(V_visible + C_range_change + C_clip_update + C_hit_update)`, not `O(N_total)`, only when the list provides uniform/indexed geometry and bounded overscan.

Use absolute monotonic time and deterministic easing; do not accumulate frame deltas for long-running animation. Cap work per frame and stop scheduling when no animation, scroll momentum, input, or invalidation remains. A native timeline can run at 120 Hz without Python, but GPU/compositor cadence may still cap presentation.

### 9.2 Scroll stress cases

- fixed 10,000-row uniform list, fast fling, direction reversal, end clamps;
- one-million-row indexed list to expose accidental total-row scans;
- variable-height rows, wrapping text, sticky headers, images, and selection;
- fractional offsets/DPI changes to expose glyph-cache and hit-test churn;
- overscan values chosen by measurement, not guessed as “safe.”

GPUI's uniform-list source computes a visible range and materializes only it, but calls `render_items` twice in some paths (measurement and prepaint) [S10]. A pygpui implementation must not mistake “virtualized” for “Python-free.”

## 10. Architecture conditions and proof obligations

| Condition | Proof obligation | Failure signal |
|---|---|---|
| Complete native snapshot | Serialization schema + ownership audit | Python objects reachable from frame state |
| Native scheduler | Call graph + timer source audit | Python wakeup per frame |
| Retained native scene | Replay/dirty counters | Full rebuild on animation/scroll |
| Native layout/text/hit | Dependency audit | Python measure/provider/finalizer in frame |
| Native animation | Timeline tests with Python callback trap armed | Any callback during animation-only window |
| Bounded virtualization | Work counters vs total rows | Cost grows with offscreen row count |
| Detached object lifetime | Refcount/finalizer counters | Python decref/`__del__` during frame |
| No hidden runtime callback | Python profile + native attach counters | Attach, signal, pending-call, a11y, or asset callback |
| Stable presentation path | Platform frame timestamps | Repeated/stale frames, queue stuffing, vsync miss |

The strongest practical proof is the conjunction of **static call-graph/type audit** and **runtime zero-counter assertions**. Neither alone is sufficient: an indirect callback can evade a narrow static audit, and a quiet run cannot cover untriggered device/font/asset paths.

## 11. Recommended validation experiments

All experiments below are **[unverified]** proposals. None has been run; no result table is implied.

| ID | Experiment | Independent variables | Measurements | Pass/fail use |
|---|---|---|---|---|
| V01 | **Python callback trap.** Mark a stable window interval; install callback/attach/finalizer counters; render static, native animation, scroll, and idle cases. | workload class; Python GIL build | Python entries, attach/detach, refcounts/finalizers, frames | Zero Python entries/attach/finalizers for each claimed stable class. Any nonzero falsifies C01. |
| V02 | **FFI ablation.** Compare native loop, Python event-only loop, Python callback each frame, and a thread-offloaded Python callback. Keep scene identical. | boundary design | CPU p50/p95/p99, attach wait, callback time, contention | Quantifies the actual FFI cost; offloading must not be credited as zero-callback. |
| V03 | **GIL contention.** Hold GIL in a controlled Python worker for bounded bursts while timing native event attach. | hold duration, thread count, GIL/free-threaded build | attach wait distribution, dropped/late events | Establishes tail risk; no fixed GIL-cost assumption accepted. |
| V04 | **Diff/layout matrix.** Generate deterministic trees with 100, 1,000, and 10,000 nodes; mutate one leaf, one subtree, and all nodes. | mutation shape, depth/fanout, layout mode | visited/changed/dirty counts, cache hits, replay bytes, CPU | Identifies full-scan and invalidation fan-out; checks scaling. |
| V05 | **Hit-test matrix.** Random and adversarial overlapping boxes/clips/transforms. | hitbox count, overlap depth, index type | candidates, exact tests, rebuild cost, hit p99 | Correctness oracle plus budget; no hit-test regression > accepted gate. |
| V06 | **Paint/batch matrix.** Vary primitive count, overlap, texture switches, clip/layer changes, and shadow/path complexity. | scene composition | primitives, batches, draws, state changes, instance/upload bytes, GPU time | Finds whether CPU encoding or GPU fill dominates. |
| V07 | **Glyph working set.** Scroll a document larger than cache/atlas capacity; repeat cold and warm. | alphabet, font/size/DPI, subpixel mode, cache size | shape/raster/atlas hit rates, evictions, uploads, text CPU/GPU | Sets cache sizes from measured hit-rate/cost curve; catches thrash. |
| V08 | **Animation isolation.** Compare retained transform animation with element-tree animation under callback trap. | animation type/count/rate | Python entries, layout/paint work, frame distribution | Retained native path must satisfy V01; callback path must be reported as event-driven. |
| V09 | **Virtual-list scaling.** 10,000 and 1,000,000 rows; fixed, indexed variable, and wrapping text. | total rows, visible rows, overscan, row type | row materializations, layout nodes, hit candidates, scroll frame p99 | Native fixed/indexed cost independent of total rows; callback trap stays zero. |
| V10 | **Input-to-frame trace.** Instrument OS/native input timestamp, event drain, frame slot, CPU phases, submit, GPU fence/timestamps, and present. | input type, load, display/backend | p50/p95/p99 per stage, queue depth | Computes the **8 ms** target [unverified] from end-to-end timestamps, not CPU alone. |
| V11 | **Physical presentation.** Run fixed-refresh 60/120 Hz displays and headless no-vsync. | refresh, present mode, frames-in-flight | unique presented frames, present intervals, dropped/repeated frames | Certifies displayed 120 fps only on a verified 120 Hz path. |
| V12 | **Idle soak.** No input/animation/invalidation for a sustained window; repeat with compositor visible/occluded. | visibility, backend, OS power state | process/thread CPU time, wakeups, GPU utilization, frame count | Applies accepted “near zero” gate; any polling loop is a defect. |
| V13 | **Event-burst/backpressure.** Inject deterministic pointer/scroll/IME bursts with bounded source rates. | burst size/rate, queue policy | depth, wait, coalescing, p95/p99, correctness | No unbounded growth; ordering/correctness maintained. |
| V14 | **Device/font/asset recovery.** Trigger device loss, font install, DPI/theme change, missing glyph, and async asset completion. | recovery type | Python callbacks, invalidation, frame gaps | These are explicitly outside “steady”; confirm no accidental stable-frame callback. |

### Concrete proposed commands (not yet executable; paths are placeholders)

```sh
# Pure Rust component/cache microbenchmarks, release build
cargo bench --manifest-path crates/pygpui-bench/Cargo.toml -- \
  diff layout hit paint text atlas --warm-up-time 2 --measurement-time 10

# Deterministic headless end-to-end scenes; JSON trace per run
cargo run --release --manifest-path crates/pygpui-bench/Cargo.toml -- \
  headless --seed 20261124 --elements 1000 --rows 10000 --frames 12000 \
  --trace-out /tmp/opencode/pygpui-headless.json

# Callback/GIL build matrix; same native workload
PYTHON_GIL=1 python -m pytest tests/bench/test_ffi_matrix.py -q
PYTHON_GIL=0 python -m pytest tests/bench/test_ffi_matrix.py -q

# Physical presentation and idle CPU must run on certified hardware/display
# Commands/platform capture tools to be selected after RQ-04 and hardware certification.
```

The **12,000-frame** sample above is **[estimated]** as enough samples for tail analysis at 120 Hz (**100 seconds** **[sourced arithmetic]**), not a statistically justified universal sample count. Report run-to-run distributions and effective sample size.

## 12. Acceptance criteria and falsification thresholds

All thresholds here are **[unverified]** proposed gates:

- **G01 — callback freedom:** zero Python entries, attach/detach operations, Python refcount/finalizer callbacks, and Python signal/pending-call executions during marked static/native-animation/native-scroll steady windows.
- **G02 — frame throughput:** on a verified 120 Hz physical display, at least **120 unique presented frames/s** **[unverified target]** for the 1,000-element scene and 10,000-row virtualized list; report p50/p95/p99 frame interval, dropped/repeated frames, and workload fidelity.
- **G03 — input latency:** **p95 < 8 ms** **[unverified target]** from captured input timestamp to first submitted visible response; separately report input-to-photon if calibrated.
- **G04 — idle:** proposed **< 1% of one CPU core averaged over 60 seconds**, no native polling loop, and no more than **2 wakeups/s** in an undemanded window **[unverified]**. Replace these with measured OS/compositor noise bounds before certification.
- **G05 — regression:** a greater-than-**10%** regression follows `.harness/PROCESS.md` [P01] **[sourced policy threshold]**. Compare matched hardware/software, same seed/scene/build mode; require profiling and written diagnosis. Do not average away p95/p99 changes.
- **G06 — virtualization:** visible-row work remains bounded as total rows increase from **10,000 to 1,000,000** **[unverified test sizes]**; no offscreen Python calls or full-row scan.
- **G07 — cache correctness:** all diff/layout/atlas/hit optimizations pass deterministic correctness oracles before timing comparison.

## 13. What remains unverified / decision risks

1. Actual pygpui FFI attach/callback costs on GIL-enabled and free-threaded Python.
2. Whether layout, text, hit testing, painting, GPU encoding, or compositor dominates on certified hardware.
3. Whether 1,000 elements and 10,000 rows fit the budgets with realistic content.
4. Whether physical 120 Hz presentation and the 8 ms input target can coexist under load.
5. Operational definition and noise floor for idle CPU.
6. Correctness of incremental invalidation, replay, clipping, text, and accessibility under edge cases.
7. Hidden Python dependencies in native text, asset, accessibility, and error paths.

These risks justify a narrow first ADR: **native event-batch boundary plus retained native runtime**. Performance numbers must wait for V01–V14.

## 14. Dated primary sources

Accessed 2026-11-24. Source dates are publication/release dates where available; repository snapshots are pinned by commit.

- **S01** — PyO3 v0.27.0, `src/marker.rs`, released 2025-10-19 (crate metadata). `Python::attach`, `Python::detach`, zero-cost token, thread-state creation, blocking, panic-safe reacquire. <https://raw.githubusercontent.com/PyO3/pyo3/v0.27.0/src/marker.rs>; release metadata: <https://crates.io/api/v1/crates/pyo3/0.27.0>.
- **S02** — CPython 3.14.10 documentation, “Thread states and the global interpreter lock,” updated 2026-11-24. Attach/detach, free-threaded caveats, signals/pending calls. <https://docs.python.org/3.14/c-api/threads.html>.
- **S03** — PyO3 v0.27.0 user guide, “Calling Python in Rust code” and “Parallelism,” 2025 release line. Attachment token and detaching native work. <https://pyo3.rs/v0.27.0/python-from-rust.html>; <https://pyo3.rs/v0.27.0/parallelism.html>.
- **S04** — wgpu 30.0.0 API documentation, `RenderPass`, current at access. Draws, instance ranges, render bundles, indirect feature requirements. <https://wgpu.rs/doc/wgpu/struct.RenderPass.html>.
- **S05** — wgpu 30.0.0 API documentation, `PresentMode` and `SurfaceConfiguration`, current at access. FIFO queue, blocking, frame latency hints. <https://wgpu.rs/doc/wgpu_types/surface/enum.PresentMode.html>; <https://wgpu.rs/doc/wgpu_types/surface/struct.SurfaceConfiguration.html>.
- **S06** — winit 0.30.12, released 2025-07-27, `ControlFlow` and `WindowEvent`. Wait/poll behavior and redraw coalescing. <https://docs.rs/winit/0.30.12/winit/event_loop/enum.ControlFlow.html>; <https://docs.rs/winit/0.30.12/winit/event/enum.WindowEvent.html>.
- **S07** — Zed/GPUI commit `168964ea32451900149b5c15ccb2d515e4ecb936`, 2026-11-24, `crates/gpui/src/window.rs`. Dirty-view ancestors, frame demand, prepaint/paint range reuse. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/window.rs>.
- **S08** — Zed/GPUI same commit, `crates/gpui/src/scene.rs` and `window.rs`. Retained sprite animation, next-frame callbacks, animation frame interval. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/scene.rs>.
- **S09** — Zed/GPUI same commit, `crates/gpui/src/elements/animation.rs`. Element-tree animation calls `request_animation_frame`. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/elements/animation.rs>.
- **S10** — Zed/GPUI same commit, `crates/gpui/src/elements/uniform_list.rs`. Visible-range virtualization and item provider callbacks. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/elements/uniform_list.rs>.
- **S11** — Taffy 0.16.0, released 2026-11-23, `src/tree/taffy_tree.rs` and `src/tree/cache.rs`. Dirty ancestors and cache keys. <https://github.com/DioxusLabs/taffy/blob/497de49c200daee81a18ce627bec98d5340ae57a/src/tree/taffy_tree.rs>; release metadata: <https://crates.io/api/v1/crates/taffy/0.16.0>.
- **S12** — Taffy 0.16.0, `src/compute/mod.rs`. Cached computation and hidden-layout paths. <https://github.com/DioxusLabs/taffy/blob/497de49c200daee81a18ce627bec98d5340ae57a/src/compute/mod.rs>.
- **S13** — Taffy 0.16.0, `benches/benches/relayout.rs`. Incremental relayout benchmark design. <https://github.com/DioxusLabs/taffy/blob/497de49c200daee81a18ce627bec98d5340ae57a/benches/benches/relayout.rs>.
- **S14** — Zed/GPUI commit above, `window.rs`, `Frame::hit_test` and mouse dispatch. Reverse-order hit testing and clip intersection. Same URL as S07.
- **S15** — Zed/GPUI commit above, `crates/gpui/src/scene.rs`, `PrimitiveKind`. Batching order constraints. Same URL as S08.
- **S16** — Android Developers, “Frame Pacing library,” current at access. Queue stuffing, vblank repetition, presentation timestamps/fences. <https://developer.android.com/games/sdk/frame-pacing>.
- **S17** — Zed/GPUI commit above, `crates/gpui_wgpu/src/wgpu_renderer.rs`. Instance writes, bind groups, batch draws, submission. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui_wgpu/src/wgpu_renderer.rs>.
- **S18** — Zed/GPUI commit above, `crates/gpui_wgpu/src/wgpu_atlas.rs`; `crates/gpui_platform/benches/atlas_upload.rs`. Atlas packing/upload queue and existing benchmark scope. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui_wgpu/src/wgpu_atlas.rs>.
- **S19** — cosmic-text commit `b07cb90a872cb9fec7fea1c72d734f81907fe3ad`, 2026-10-27, `src/font/system.rs`; crate 0.19.0 released 2026-04-22. Font initialization/cache and shape-run cache. <https://github.com/pop-os/cosmic-text/blob/b07cb90a872cb9fec7fea1c72d734f81907fe3ad/src/font/system.rs>; <https://crates.io/api/v1/crates/cosmic-text/0.19.0>.
- **S20** — cosmic-text same commit, `src/shape_run_cache.rs`. Text/attribute cache key and age trimming. <https://github.com/pop-os/cosmic-text/blob/b07cb90a872cb9fec7fea1c72d734f81907fe3ad/src/shape_run_cache.rs>.
- **S21** — cosmic-text same commit, `src/glyph_cache.rs`. Glyph key and subpixel bins. <https://github.com/pop-os/cosmic-text/blob/b07cb90a872cb9fec7fea1c72d734f81907fe3ad/src/glyph_cache.rs>.
- **S22** — Zed/GPUI commit above, `crates/gpui/src/text_system.rs`. Glyph cache key and subpixel variants. <https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/text_system.rs>.
- **P01** — pygpui `.harness/PROCESS.md`, 2026-11-24. Evidence policy, performance loop, >10% regression rule. <../PROCESS.md>.
- **RQ03** — pygpui `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`, 2026-11-24. Targets and required questions. <RQ-03-performance-and-benchmark-model.md>.

## 15. Reproducible local observations (not performance benchmarks)

On 2026-11-24 the workspace reported Python **3.14.10**, rustc **1.100.0**, and cargo **1.100.0** **[sourced local observation]**. No pygpui implementation, renderer, benchmark crate, GPU configuration, or certified display exists; therefore no FFI/frame/latency/idle result was measured. Repository source snapshots were inspected read-only in `/tmp/opencode`; no feature code or harness state was modified by this research.
