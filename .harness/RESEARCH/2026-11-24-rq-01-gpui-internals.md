# RQ-01A — GPUI internals and clean-room boundaries

Research date and access date: **2026-11-24 UTC**  
Researcher: Researcher-Prior-Art instance A  
Task: P0-R01A, Round 1

## Question

What can the current GPUI/Zed primary sources establish about entity/view/window lifecycle, retained state, frame scheduling, actions/keymaps, and rendering ownership; and which architectural concepts may pygpui independently reimplement without copying protected expression or losing Apache-2.0 provenance?

## Decision unblocked

The runtime ownership model, the smallest coherent hybrid immediate/retained model, the Python/Rust update boundary, lifecycle and reentrancy rules, and the default clean-room/licensing policy for Phase 0 ADRs.

This report does **not** certify the requested 120 fps, 10,000-row, sub-8 ms input-to-frame, or near-zero idle CPU targets. Those remain benchmark questions for RQ-03.

## Evidence anchor and method

- Upstream repository: `zed-industries/zed`.
- Pinned `main` commit: **`168964ea32451900149b5c15ccb2d515e4ecb936`**.
- Commit timestamp: **2026-11-24T07:24:54Z**.
- Commit subject: `agent: Add thread-only picks for the model, profile and thinking effort (#66869)`.
- `crates/gpui/Cargo.toml` at that commit declares package version **0.2.2** and license **Apache-2.0**.
- crates.io reports `gpui` **0.2.2** published **2025-10-22T03:56:29Z**. Therefore the version string alone does not identify the current source snapshot.
- Reproducible local evidence checkout: `/tmp/opencode/zed-gpui-168964e`; `git rev-parse HEAD` returned the pinned commit above. It was a sparse, blob-filtered checkout of GPUI and license files.
- Method: read official GPUI documentation, pinned source and manifests, Zed design posts, the Apache-2.0 text, and a U.S. Copyright Office primary source. No GPUI program was built or run. No source code is reproduced here.

Confidence meanings follow `.harness/PROCESS.md`: **verified** = dated primary source or reproducible local observation; **plausible** = indirect support requiring validation; **unverified** = assumption, estimate, stale evidence, or unsupported assertion.

## Dated primary sources

| ID | Source title and URL | Version/date | What it supports |
|---|---|---|---|
| S01 | [GPUI home](https://gpui.rs/) and [pinned GPUI README](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/README.md) | Accessed 2026-11-24; README at pinned commit, package 0.2.2 | Official “hybrid immediate and retained” description; entities/views/elements; root view and frame overview |
| S02 | [GPUI `Cargo.toml`](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/Cargo.toml) | Pinned commit 2026-11-24; version 0.2.2 | Direct package license, version, platform features, dependencies |
| S03 | [Contexts](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/docs/contexts.md) | Pinned commit 2026-11-24; accessed same date | `App`, `Context<T>`, async contexts, `Window`, `Entity<T>` ownership and fallibility |
| S04 | [Ownership and data flow](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/_ownership_and_data_flow.rs) | Pinned commit 2026-11-24; accessed same date | App-owned entity state, handles, `observe`/`notify`, `subscribe`/`emit`, subscriptions |
| S05 | [Element module](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/element.rs) | Pinned commit 2026-11-24; accessed same date | Ephemeral element tree, `Render`, `RenderOnce`, `Element`, stable IDs, prepaint state |
| S06 | [View module](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/view.rs) | Pinned commit 2026-11-24; accessed same date | Entity-backed views, opt-in cached subtrees, cache key, dependency recording, prepaint/paint replay |
| S07 | [Window module](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/window.rs) | Pinned commit 2026-11-24; accessed same date | Dirty views, frame callbacks, draw/present split, retained element state, key dispatch, non-owning window handles |
| S08 | [App module](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/app.rs) and [entity map](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/app/entity_map.rs) | Pinned commit 2026-11-24; accessed same date | Update/effect cycle, coalescing, leases, release cleanup, window removal, tracked entity dependencies |
| S09 | [Key Dispatch guide](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/docs/key_dispatch.md), [action module](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/action.rs), [keymap](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/keymap.rs), [dispatch tree](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/key_dispatch.rs) | Pinned commit 2026-11-24; accessed same date | Typed actions, JSON payloads, key contexts, precedence, multi-key sequences, capture/bubble routing |
| S10 | [Scene](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/scene.rs) and [platform abstraction](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/gpui/src/platform.rs) | Pinned commit 2026-11-24; accessed same date | Platform-neutral paint primitives, scene replay/animation, `PlatformWindow::draw`, frame callbacks and wakers |
| S11 | [Leveraging Rust and the GPU to render user interfaces at 120 FPS](https://zed.dev/blog/videogame) | Published 2023-03-07; accessed 2026-11-24 | Historical rendering rationale, layout/paint/scene separation, batching and text atlas design |
| S12 | [Optimizing the Metal pipeline to maintain 120 FPS in GPUI](https://zed.dev/blog/120fps) | Published 2024-02-07; accessed 2026-11-24 | Presentation/cadence interaction, triple buffering, historical post-input presentation policy; not a general benchmark |
| S13 | [Zed Weekly #23](https://zed.dev/blog/zed-weekly-23) | Published 2023-10-13; accessed 2026-11-24 | Historical GPUI 2 design: stateless DOM goal, stateful element IDs, full-window rerender capability |
| S14 | [Zed README licensing section](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/README.md) and [Zed software overview](https://zed.dev/software-overview) | Pinned commit/current page, accessed 2026-11-24 | Repository-wide mixed licensing; GPUI is an Apache-licensed reusable component, most Zed code is GPL |
| S15 | [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) | License dated 2004-01; accessed 2026-11-24 | Copyright/patent grant, redistribution conditions, modification notices, retained notices, conditional NOTICE propagation, trademark limitation |
| S16 | [U.S. Copyright Office Circular 33, Works Not Protected by Copyright](https://www.copyright.gov/circs/circ33.pdf) | Published 2021-03-26; accessed 2026-11-24 | U.S. distinction between unprotectable ideas/methods/systems and protectable expression; jurisdiction-specific |
| S17 | [crates.io `gpui` 0.2.2 API record](https://crates.io/api/v1/crates/gpui/0.2.2) | Published 2025-10-22; accessed 2026-11-24 | Published package metadata and release date |
| S18 | [Zed issue #55470](https://github.com/zed-industries/zed/issues/55470), [relicense commit `ac5af8b9e1ea3f7922fbabefe409c05b8766135c`](https://github.com/zed-industries/zed/commit/ac5af8b9e1ea3f7922fbabefe409c05b8766135c), and current [ztracing](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/ztracing/Cargo.toml)/[zlog](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/zlog/Cargo.toml) manifests | Issue 2026-05-02; relicense 2026-09-01; current commit/access 2026-11-24 | Historical GPL dependency concern and its current resolution for these crates |
| S19 | [Zed `ui` manifest](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/ui/Cargo.toml) and [`workspace` manifest](https://github.com/zed-industries/zed/blob/168964ea32451900149b5c15ccb2d515e4ecb936/crates/workspace/Cargo.toml) | Pinned commit 2026-11-24; accessed same date | Concrete examples of GPL-3.0-or-later crates outside GPUI |

## Findings and claim-level evidence

### 1. Entity, view, and context lifecycle

**C-01 — verified.** GPUI’s `App` owns entity state. `Entity<T>` is a typed handle; state is accessed through an `App`/`Context<T>`. A view is an entity that implements `Render`. The official docs explicitly describe this model. Evidence: S03, S04, S05.

**C-02 — verified.** An entity handle is not a borrow of the underlying state. The implementation combines a slotmap identity, type information, and a reference-count table. Strong handle cloning/dropping adjusts liveness; weak handles do not retain the entity and fail to upgrade after release. The entity map has a separate owned-storage map. Evidence: S08, `EntityMap`, `AnyEntity`, `WeakEntity`.

**C-03 — verified.** Entity mutation is mediated by an application update and a lease. Reading/updating is recorded as an entity access. Updating an entity that is already leased has an explicit failure path; the `AppCell` also detects conflicting application borrows. Evidence: S08, `AppCell`, `update_entity_erased`, `EntityMap::lease_inner`, `double_lease_panic`.

**C-04 — verified.** `notify` and typed events are effects, not unrestricted recursive callbacks. Effects are coalesced and drained after the outermost update; effects can enqueue more effects. Observer/subscriber closures retain weak handles and return whether they should remain subscribed. Evidence: S04, S08, `push_effect`, `flush_effects`, `observe_internal`, `subscribe_internal`.

**C-05 — verified.** Entity destruction is deferred until the effect cycle after the last strong handle disappears. GPUI removes observers/listeners/window dependency links, invokes release callbacks, then drops the owned state. This gives a deterministic cleanup point but also means “last handle dropped” and “state destroyed” are not the same instant. Evidence: S08, `AnyEntity::drop`, `take_dropped`, `release_dropped_entities`.

**C-06 — verified.** `WindowHandle<V>` is copyable and explicitly non-owning. Reads/updates return errors when the window is closed or the root type differs. Window removal is marked during a window update and completed when that update unwinds; tracked entity-to-window links are removed and close observers run. Evidence: S07 `WindowHandle`; S08 `update_window_erased`/`trail`.

**C-07 — verified.** The current source records which entities a window actually accessed during a draw. On `notify`, only windows currently displaying that entity are invalidated. Cached views restore their prior dependency sets when their prepaint output is reused. Evidence: S06 `accessed_entities`; S07 `record_entities_accessed`; S08 `tracked_entities`, `window_invalidators_by_entity`, `App::notify`.

**Architectural implication — plausible.** A pygpui runtime should use opaque, generation-aware handles rather than exposing Rust pointers or Python object IDs. Rust should be the sole owner of UI entities and windows; Python should interact through checked operations. Weak callbacks and deterministic teardown are necessary to avoid cross-language reference cycles. This is a design inference from C-01 through C-07, not a GPUI Python-binding fact.

### 2. Retained versus immediate rendering

**C-08 — verified.** The ordinary element tree is immediate: a view’s `Render` builds elements, GPUI performs layout/prepaint/paint, and the element values and their callbacks are dropped before the next tree is built. `RequestLayoutState` and `PrepaintState` are per-pass values, not a persistent virtual DOM. Evidence: S05 module documentation and `Element` trait.

**C-09 — verified.** GPUI separately retains identity-keyed element state. `GlobalElementId` plus state `TypeId` identifies state; accessed keys are carried forward and unaccessed keys are dropped at frame finish. `use_state`/`use_keyed_state` expose longer-lived entity state for elements. This is the retained home for interaction state such as pending mouse-down/click/hover and for selected layout caches. Evidence: S07 `Frame::finish`, `with_element_state`, `use_state`, `use_keyed_state`; S05 `GlobalElementId`.

**C-10 — verified.** Entity-backed view subtrees can be explicitly cached with `Entity::cached`/`AnyView::cached`. Reuse requires matching bounds, content mask, text style, opacity, no dirty mark for the entity, and no forced refresh. Reuse replays prepaint/paint ranges into the new frame instead of rerendering the subtree. Caching is not enabled merely because a type is a view. Evidence: S06 `ViewElementState`, `request_layout_view`, `prepaint_view`, `paint_view`; S07 `reuse_paint`.

**C-11 — verified.** The retained `Scene` is a paint-operation/primitive buffer, not a retained widget tree. It remains available for presentation and for cached-subtree replay. Current `Scene` supports primitives, layers, native views, and animation poses that can advance without rebuilding the scene. Evidence: S10 `Scene`; S07 `Frame`, `present`, `advance_scene_animations`, `reuse_paint`.

**C-12 — plausible.** The smallest coherent hybrid for pygpui is: an ephemeral declarative tree produced on semantic changes; durable Rust-owned entities for long-lived view/model state; identity-keyed Rust element state for gestures and local UI memory; optional cached subtrees for expensive stable regions; and a whole-window rebuild fallback. GPUI establishes that these layers can coexist, but it does not establish that pygpui needs GPUI’s full automatic dependency graph in its first vertical slice. Evidence: C-08 through C-11.

### 3. Frame scheduling and presentation

**C-13 — verified.** GPUI separates invalidation, drawing, and presentation. The window invalidator coalesces dirty state and wakes/schedules the platform frame source. A platform frame request runs pending next-frame callbacks, draws only when dirty or forced, and otherwise may present an existing scene when presentation/animation/high-rate-input demand exists. Remaining dirty/callback/animation demand schedules another frame. Evidence: S07 `WindowInvalidator`, `on_request_frame`, `draw`, `present`; S10 `PlatformWindow`.

**C-14 — verified.** `on_next_frame` creates frame demand without dirtying the window. `request_animation_frame` schedules a next-frame notification for the current view. Thus “callback scheduled,” “redraw required,” and “present required” are distinct states. Evidence: S07 `on_next_frame`, `request_animation_frame`, `has_frame_demand`, `should_draw`, `needs_present`.

**C-15 — verified.** Reentrant platform frame requests during a draw are detected and deferred rather than nesting another draw or reborrowing `App`. After drawing, GPUI also checks whether the window became dirty again and rearms the frame source. Evidence: S07 `draw_in_progress` branch and post-frame rescheduling in `on_request_frame`.

**C-16 — verified.** Current scheduling includes inactive-window, low-power, thermal, animation-rate, and high-rate-input considerations. The 2024 Metal post describes a historical fixed one-second post-input presentation policy; that post is not a complete description of the 2026 scheduler. Evidence: S07 `minimum_frame_interval`, `InputRateTracker`, `FramePacer`; S12.

**C-17 — plausible.** An event-only Python/Rust boundary is compatible with this model: Python handles semantic input/state changes, while Rust coalesces invalidations and owns repeated layout/paint/present work. Animation and cached repainting can then run without Python callbacks. Whether the bridge can meet the numerical targets is unverified and belongs to RQ-03.

**C-18 — unverified.** “Idle CPU near zero,” stable 120 fps, 10,000-row throughput, and p95 input-to-frame below 8 ms are not established by this source review. The Metal post reports a specific historical macOS investigation, not a reproducible cross-platform certification. Evidence: S12 is anecdotal/design evidence only; no local benchmark was run.

### 4. Actions and keymaps

**C-19 — verified.** GPUI actions are typed, cloneable, type-erased commands. Complex actions can carry JSON-deserialized data and schemas. Actions are independent of raw key events and can be invoked by menus or programmatic dispatch as well as keybindings. Evidence: S09 `Action`, action guide.

**C-20 — verified.** Key contexts are attached to nodes in the dispatch tree built during rendering. Resolution prefers the deepest matching context, then later-added bindings; multi-key sequences have pending-input and replay behavior. Dispatch node IDs are explicitly unstable between frames. Evidence: S09 `Keymap::bindings_for_input`, `DispatchTree`, `dispatch_key`, `flush_dispatch`; S07 `dispatch_key_event`.

**C-21 — verified.** Low-level key events use capture then bubble phases along the focused dispatch path. Matched actions have global/window capture and bubble handling, and propagation can be stopped. Key matching therefore depends on the current rendered focus/context tree, not merely a global shortcut table. Evidence: S07 `dispatch_key_down_up_event`, `dispatch_action_on_node_inner`; S09.

**Architectural implication — plausible.** pygpui should resolve shortcuts and focus in Rust, expose named/payload-validated actions to Python, and call Python only when an action or semantic input event is delivered. Python should not perform per-frame keymap matching. This preserves a single precedence model and creates a clean event boundary. Evidence: C-19 through C-21.

### 5. Rendering ownership

**C-22 — verified.** Elements own layout/prepaint/paint behavior. Layout uses Taffy; prepaint records hit/focus/dispatch/accessibility state; paint emits platform-neutral primitives into `Scene`. `Window::present` passes the scene to `PlatformWindow::draw`. Evidence: S05, S07, S10.

**C-23 — verified.** Rendering work is Rust-owned in GPUI: application state access, tree construction, layout, hit testing, dispatch, scene construction/replay, text-system interaction, and the platform draw handoff. The 2023 design post explains the deliberate primitive/batching/atlas approach, but current source is the authority for current structure. Evidence: S05, S07, S10, S11.

**C-24 — plausible.** For pygpui, Rust should own the window, retained UI state, layout, hit testing, dispatch tree, scene/cache, and presentation loop. Python may own application-domain state and produce declarative intent on change. Keeping Python objects or callbacks in per-frame render caches would undermine the no-Python-per-frame constraint and complicate ownership. This is an architecture recommendation, not a measured result.

### 6. Clean-room and Apache-2.0 boundaries

**C-25 — verified, U.S.-specific.** The U.S. Copyright Office states that copyright does not protect ideas, procedures, processes, systems, methods of operation, concepts, principles, or discoveries, although their particular expression may be protected. Therefore architectural concepts can be studied and independently expressed; this is not a worldwide legal conclusion. Evidence: S16.

**C-26 — verified.** Apache-2.0 permits reproduction and derivative works subject to conditions. Redistribution requires giving recipients the license; modified files must carry prominent change notices; source-form derivatives must retain pertinent copyright, patent, trademark, and attribution notices; and NOTICE attribution must be propagated only if the upstream Work includes a NOTICE text file. The license also limits trademark permission and contains a patent grant/termination provision. Evidence: S15 sections 2, 3, 4, and 6.

**C-27 — verified.** At the pinned commit, `crates/gpui/Cargo.toml` declares Apache-2.0, and `crates/gpui/LICENSE-APACHE` symlinks to the repository license containing the Zed copyright notice. A local `git ls-tree` inspection found no `NOTICE` file at the repository root or under `crates/gpui`. Thus this snapshot has no upstream GPUI NOTICE file to propagate, but the license and pertinent notices still apply. Evidence: S02, S15, pinned tree observation.

**C-28 — verified.** The Zed repository is not uniformly Apache-licensed. The repository README says most Zed source is GPL-3.0-or-later with Apache components; `crates/ui` and `crates/workspace` explicitly declare GPL-3.0-or-later. “Found in the Zed repository” is not a sufficient license provenance record. Evidence: S14, S19.

**C-29 — verified.** The 2026 issue alleging a GPL path through `sum_tree -> ztracing` was historical. Commit `ac5af8b…` relicensed `zlog`, `ztracing`, and `ztracing_macro` to Apache-2.0 on 2026-09-01; the pinned current manifests declare Apache-2.0. The issue was closed on 2026-10-07. This falsifies the stale claim for this snapshot, but does not substitute for a complete dependency-license audit. Evidence: S18.

**C-30 — plausible.** A clean-room policy should restrict implementation inputs to documented behavior and independently written design notes; prohibit copying or transliterating source, comments, shaders, tests, fixtures, and assets; use pygpui-specific public names where practical; and maintain a provenance ledger for any later exception. “Clean-room” is a risk-control process, not a guarantee against all copyright, patent, trademark, or contract claims. Evidence: C-25, C-26; process recommendation.

**C-31 — verified.** If pygpui later copies or adapts GPUI source, it is not merely concept reuse: the Apache-2.0 redistribution conditions in C-26 apply. Evidence: S15.

**C-31a — plausible.** A provenance record for any source-derived exception should include the exact commit, path, original copyright/license, modifications, and retained notices. Translated or ported expression should be treated as source-derived unless qualified counsel determines otherwise. This is conservative process guidance, not a legal holding. Evidence: C-25, C-26, C-30.

**C-32 — unverified.** The entire current GPUI transitive dependency graph has not been proven permissively licensed by this research. Only the direct GPUI declaration and the specifically investigated `ztracing`/`zlog` path were checked. A selected dependency snapshot requires a complete license inventory before distribution. Evidence: scope limitation; S02, S18.

## Contradictions, stale evidence, and reconciliations

1. **“Hybrid immediate/retained” versus “stateless DOM.”** The 2023 Weekly #23 post describes GPUI 2’s design goal as a stateless DOM capable of full-window rerender. Current source retains keyed element state and supports cached view subtrees. These are compatible when separated by time: the immediate tree remains the default, while retention is explicit and selective. Current source wins for current behavior. Evidence: S13 versus S05–S07.

2. **“Root render at the start of each frame” versus idle/cached behavior.** The README describes root rendering at frame start, but current code does not draw on every platform tick when there is no demand, and cached nested views can skip render/layout/prepaint/paint. The accurate current statement is “root render on a dirty/forced draw, with selective subtree reuse.” Evidence: S01 versus S06, S07.

3. **Historical frame pacing versus current scheduler.** The 2024 Metal post’s one-second post-input presentation policy and blocking/synchronization discussion should not be copied into a 2026 design unchanged. Current source has demand flags, reentrancy protection, adaptive throttling, animation intervals, and high-rate-input tracking. Evidence: S12 versus S07.

4. **Version ambiguity.** `gpui` 0.2.2 on crates.io dates from 2025-10-22, while `main` still says 0.2.2 at the 2026-11-24 commit. Treating “0.2.2” as an immutable source anchor would be wrong. Evidence: S02, S17.

5. **Historical GPL dependency allegation.** Issue #55470 accurately described a past concern but is stale for the pinned snapshot. The current manifests and relicense commit supersede it. A skeptic should reject any present-tense claim that this specific path is still GPL at `168964e…`, while still requiring a full graph audit. Evidence: S18.

6. **Repository license versus component license.** GitHub’s repository-level GPL label and the GPUI package’s Apache-2.0 declaration can both be true because licenses are per component/crate. Copying from `crates/ui` or `crates/workspace` crosses a materially different boundary from studying `crates/gpui`. Evidence: S02, S14, S19.

## Recommendation

### Runtime ownership model — plausible recommendation

- **Rust owns:** windows, entity registry, retained element/view state, layout trees, hitboxes, focus/dispatch tree, scene, caches, animation clock, frame invalidation, platform event loop, and presentation.
- **Python owns:** application-domain models and policy, plus the author-facing declarative component vocabulary and semantic event handlers.
- **Bridge:** typed commands/events with opaque handles and validated payloads. Python is called on semantic changes/input, not on every animation or present tick.
- **Do not infer performance:** the ownership split removes an avoidable per-frame boundary, but the actual FFI/GIL cost must be measured under RQ-03.

### Smallest coherent hybrid — plausible recommendation

1. Begin with a full window rebuild on dirty semantic updates.
2. Add stable IDs for stateful views and interaction state; retain that state in Rust by identity.
3. Add opt-in cached subtrees for expensive stable regions; do not begin with a general virtual-DOM differ.
4. Keep a forced full-refresh path for correctness, theme/layout changes, debugging, and cache invalidation.
5. Advance simple animations in Rust when possible; request a redraw only when the scene cannot be updated independently.
6. Add GPUI-style automatic read-dependency tracking only if coarse invalidation benchmarks show a decision-driving problem.

### Lifecycle and reentrancy contract — plausible recommendation

- Handles contain kind, runtime ID, and generation; all operations fail safely on stale handles.
- Window handles are non-owning. Closing a window invalidates its handles and subscriptions before Python can receive another event for it.
- Entity callbacks/subscriptions use weak references. Ownership is explicit and acyclic; teardown has one owner.
- Rust mutations run under a single UI-thread borrow. Nested Python-to-Rust calls during a Rust update are rejected or deferred, never allowed to form a second mutable lease.
- Queue Python-originated mutations into the UI turn. Do not synchronously reenter Python while holding an application borrow, dependency-table lock, or platform/GPU resource.
- Notifications are coalesced and flushed at a defined update boundary. Release callbacks run before final destruction.
- Test window close during dispatch, entity release during notification, cross-window moves, repeated teardown, stale async completion, and callback-triggered callback chains.

### Actions/keymaps — plausible recommendation

- Define a stable action name and versioned payload schema independent of Python implementation names.
- Build focus/key contexts in Rust from the current rendered tree.
- Resolve precedence and multi-key sequences in Rust.
- Deliver only matched actions/semantic input to Python, with capture/bubble or stop-propagation semantics preserved.
- Never persist raw dispatch-node IDs across frames.

### Clean-room/licensing default — verified obligations, plausible policy

- Default to **documented concepts plus independent implementation**. Do not copy GPUI source into pygpui.
- Restrict implementation study to Apache-licensed components unless a separate GPL/AGPL decision is explicitly approved.
- Maintain `THIRD_PARTY_NOTICES`/provenance records for dependencies and any future source-derived exception.
- If source is ever copied or adapted: record upstream URL, exact commit, file path, original copyright/license, modification notice, and retained attribution; distribute the Apache-2.0 text; recheck the actual source archive for NOTICE.
- No NOTICE file was found in this pinned GPUI snapshot, so do not invent a Zed NOTICE obligation from this evidence. Do recheck the exact artifact and every third-party dependency before release.
- Obtain qualified legal review before making worldwide “clean-room,” trademark, patent, or combined-work claims.

## Evidence gaps and required follow-up

| Gap | Current status | Decision impact | Evidence needed |
|---|---|---|---|
| G-01 Runtime behavior | **unverified**: source review only; GPUI was not built or exercised | Does not block concept selection; blocks claims about exact runtime edge behavior | Focused tests/prototypes for teardown, reentrancy, stale handles, cached-view invalidation, and cross-window entities |
| G-02 Performance targets | **unverified**: no benchmark | Blocks performance certification and any promise of no-Python-per-frame feasibility | RQ-03 reproducible benchmark on disclosed hardware/software, including headless and presented-frame metrics |
| G-03 Published crate versus `main` | **verified difference in dates; unverified behavioral delta** | Claims anchored to `168964e…` may not apply to crates.io 0.2.2 | Diff the exact published 0.2.2 archive against the chosen commit if that artifact is used |
| G-04 Python/GIL integration | **unverified** here | Blocks final FFI design, not Rust ownership recommendation | RQ-02/RQ-03 PyO3 threading, GIL, callback, and free-threaded-build evidence |
| G-05 Complete dependency license closure | **unverified** | Blocks distribution if GPUI or a snapshot is linked as a dependency; not blocking for concept-only clean-room work | Full `cargo metadata`/license inventory for the selected commit and features, including third-party notices |
| G-06 Jurisdiction and non-copyright rights | **unverified** | Blocks absolute legal safety claims | Qualified counsel for distribution jurisdictions, patents, trademarks, and any source-derived exception |
| G-07 Cache correctness under all dynamic inputs | **plausible** from source; not exhaustively tested | Blocks removing full-refresh fallback | Tests for inherited style, opacity, content mask, focus, theme, font, DPI, and dependency changes |
| G-08 Current cross-thread handle semantics | **unverified** in this report | Blocks any claim that Python background threads may directly mutate UI entities | Inspect/test current `Send`/`Sync` contracts and async context behavior; conservative default is UI-thread mutation only |

## Bottom line

Current GPUI source supports a **Rust-owned, event-driven UI runtime with an immediate element tree plus selective retained state and cached subtrees**. Its lifecycle is built around app-owned entities, weak observers, deferred effect/release processing, non-owning window handles, and guarded single-owner updates. Actions/keymaps and rendering are integrated through the rendered dispatch tree and a platform-neutral scene.

For pygpui, the conservative Phase 0 choice is to adopt those **architectural concepts**, not their implementation expression: Python domain state and semantic events at the boundary; Rust window/entity/layout/scene/frame ownership; identity-keyed retained UI state; opt-in caching; and clean-room implementation with Apache-2.0 provenance required for any future copied source.
