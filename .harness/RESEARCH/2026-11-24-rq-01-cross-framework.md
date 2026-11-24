# RQ-01 — Cross-framework UI architecture prior art

- **Date:** 2026-11-24
- **Researcher:** Researcher-Prior-Art instance B
- **Task:** P0-R01B, Round 1
- **Status:** Complete for Skeptic review
- **Scope:** Slint, Iced, Xilem/Masonry, Flutter, and Dear ImGui. Qt is deliberately excluded because it adds no new architectural category to the retained scene-graph evidence already covered by Slint, Iced, Xilem/Masonry, and Flutter. Dear ImGui is included because the immediate-mode boundary is decision-relevant.
- **Method:** Dated primary documentation and source snapshots, with implementation checks for decision-driving claims. No source code was copied into this repository. No feature code, `TASKS.json`, `STATE.md`, or another researcher's file was changed.

## Question

How should a Python-first UI framework divide application state, view lifecycle, layout, text, input, and frame ownership between Python and Rust, and which retained/immediate rendering and incremental-update patterns transfer without requiring Python callbacks on every frame?

## Decision unblocked

This research supports decisions on:

1. A retained Rust runtime with Python as the application-model and view-description layer.
2. A bounded, phase-based update pipeline rather than arbitrary reentrant mutation.
3. Stable, generation-checked entity handles and deferred mutation queues.
4. Rust ownership of layout, text editing/shaping, focus/IME/clipboard, render primitives, and every rendered frame.
5. A narrow immediate-mode escape hatch, not a whole-application immediate-mode loop.
6. Clean-room use of behavioral concepts, with source-derived code and assets tracked separately for license provenance.

It does **not** select a renderer, text engine, windowing backend, FFI mechanism, or final Python API.

## Executive finding

**Use a retained Rust entity tree with dirty-flag-driven passes, and let Python produce typed view descriptions or patches only when application state changes.** [plausible]

The strongest transferable pattern is the combination of:

- Slint's dependency-tracked properties and item caches;
- Iced's tag/state reconciliation;
- Xilem's explicit `rebuild(previous)` lifecycle plus generational routing IDs;
- Masonry's bounded rewrite passes, layout/compose/paint invalidation, and cached scenes;
- Flutter's separation of ephemeral widget configuration from retained elements/render objects and dirty build/layout/paint queues; and
- Dear ImGui's immediate API as a bounded escape hatch for ephemeral or tool UI.

No reviewed source proves that any of these architectures meets pygpui's 120 fps, 8 ms input-to-frame, idle-CPU, or zero-Python-callback targets. Those remain [unverified] until a reproducible pygpui benchmark exists.

## Terms used in this report

- **Retained model:** The UI runtime keeps element/widget state, geometry, or render data across frames.
- **Immediate API:** Application code reissues UI commands each frame. This says nothing about whether the library retains internal state.
- **Incremental update:** The runtime avoids some rebuilding, layout, text shaping, painting, or rasterization after a change.
- **Damage tracking:** The runtime computes screen regions that need pixel repainting. This is a stronger and separate property from retaining a widget tree or cached draw commands.

These axes are orthogonal. Dear ImGui has an immediate API but retains windows and interaction state; Masonry has a retained tree but currently lacks damage-region rendering.

## Dated primary sources

All links below were retrieved on **2026-11-24**. Documentation pages without individual publication dates are dated by the exact repository commit that contained them. Current heads are evidence snapshots, not claims about released package contents.

| ID | Framework and snapshot | Primary evidence used |
|---|---|---|
| S1 | **Slint**, commit [`70067e98eac2870d2ed11510134d518b51e5ea13`](https://github.com/slint-ui/slint/commit/70067e98eac2870d2ed11510134d518b51e5ea13), committed **2026-11-24** | [Item tree](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/item-tree.md), [layout](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/layout-system.md), [text layout](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/text-layout.md), [input](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/input-event-system.md), [property bindings](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/property-binding-deep-dive.md), [renderers](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/custom-renderer.md), and implementation files cited below. |
| S2 | **Iced**, commit [`98bd48fe011efc0ec5819fee0fa7673a7169ff11`](https://github.com/iced-rs/iced/commit/98bd48fe011efc0ec5819fee0fa7673a7169ff11), committed **2026-11-19** | [README](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/README.md), [`runtime/src/user_interface.rs`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/runtime/src/user_interface.rs), [`core/src/widget/tree.rs`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/core/src/widget/tree.rs), [`core/src/text/input.rs`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/core/src/text/input.rs), [`widget/src/text_input.rs`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/widget/src/text_input.rs), and graphics text-cache sources. |
| S3 | **Xilem/Masonry**, commit [`9a78df878a9269a88325ebd71f3f68c757f0a396`](https://github.com/linebender/xilem/commit/9a78df878a9269a88325ebd71f3f68c757f0a396), committed **2026-11-22** | [Repository architecture](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/ARCHITECTURE.md), [Masonry architecture](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry/ARCHITECTURE.md), [pass system](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/doc/pass_system.md), Xilem view/sequence sources, Masonry pass sources, and `TextArea` source. |
| S4 | **Flutter**, commit [`c0b4744c302be253e6cececa7b553baa32e44543`](https://github.com/flutter/flutter/commit/c0b4744c302be253e6cececa7b553baa32e44543), committed **2026-11-24** | [`widgets/framework.dart`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart), [`rendering/object.dart`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/object.dart), [`rendering/paragraph.dart`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/paragraph.dart), and [`gestures/binding.dart`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/gestures/binding.dart). |
| S5 | **Dear ImGui**, commit [`bd4e3b0abccd653490d68beeb72f0750cde6d5f6`](https://github.com/ocornut/imgui/commit/bd4e3b0abccd653490d68beeb72f0750cde6d5f6), committed **2026-11-23** | [FAQ](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/docs/FAQ.md), [`imgui.cpp`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp), [`imgui_internal.h`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_internal.h), [`imgui_widgets.cpp`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_widgets.cpp), [`imgui_draw.cpp`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_draw.cpp), and the GLFW/OpenGL example loop. |
| S6 | **License primary texts at the same snapshots** | [Slint `LICENSE.md`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/LICENSE.md), [Iced `LICENSE`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/LICENSE), [Xilem/Masonry `LICENSE`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/LICENSE), [Flutter `LICENSE`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/LICENSE), [Dear ImGui `LICENSE.txt`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/LICENSE.txt). |

**Masonry source-location note.** The standalone `linebender/masonry` repository's latest commit is the 2024-05-29 [move-to-Xilem README update](https://github.com/linebender/masonry/commit/23a53ec67863eef8b3c4b7f449fd447217bcae05). Current Masonry implementation evidence in this report comes from the `masonry/` and `masonry_core/` workspace crates in `linebender/xilem` at S3. [verified]

## Findings

### Cross-framework comparison

| Framework | Application/UI model | Retained data | Incremental behavior | Layout, text, and input ownership | Transferable concept |
|---|---|---|---|---|---|
| **Slint** | Declarative components over a runtime item tree | Item trees, properties, bindings, per-item graphics/text caches, partial-render cache | Lazy property evaluation; dependency-tracked repaint requests; optional dirty-region filtering and reused-buffer repaint | Rust core owns item geometry, input dispatch/focus, text editing state and Parley-based layout; platform adapter owns OS events/surfaces | Property dependency tracking, weak item handles, renderer-independent item traversal, explicit partial-render fallback |
| **Iced** | Elm-inspired state/messages/view/update; widgets reconciled against a persistent state tree | Widget `Tree` with tags, state, size, translation, children; text editor and renderer caches | Tag-based state reconciliation; text-cache reuse; UI runtime still invokes root layout and draw on its build/draw paths | Rust runtime/widgets own event routing, editing and layout; renderer abstractions own drawing and text caches | Tag/state continuity, controlled-input reconciliation, renderer-agnostic widget contract |
| **Xilem/Masonry** | Lightweight Xilem views rebuilt into a retained Masonry widget tree | View state and routing paths; widget arena, properties, geometry, cached scenes, focus/capture state | Xilem sequence diffing; Masonry invalidation passes; measurement and scene caches; bounded rewrite loop | Rust owns widget passes, text focus, pointer capture, IME, Parley editor/layout, Vello scenes and accessibility | Two-level architecture: reactive view diff above a retained, testable pass engine |
| **Flutter** | Declarative widget configuration reconciled into retained elements and render objects | Elements/state, render tree, layers/display lists, dirty queues, text painter and hit-test paths | Dirty-element build queue; type/key child reconciliation; dirty layout/paint queues; repaint boundaries | Flutter framework owns build/layout/paint/input routing; engine owns text and Skia rendering | Separate configuration from runtime nodes; keys/generations; explicit relayout/repaint boundaries |
| **Dear ImGui** | Immediate API; application submits UI each frame by default | Internal windows, ID stacks, per-window storage, active/focus state, text-edit state, draw lists; experimental skip-refresh path | Default re-submission/layout; explicit experimental window refresh avoidance; clipped long-text optimizations | Library owns CPU layout, hit testing, editing and mesh generation; platform/renderer backends own OS input and GPU submission | Immediate leaf commands, stable IDs, renderer-neutral draw data, explicit capture flags |

### Slint

**C-SL-01 — Slint retains a runtime item tree and separates rendering from hit-testing traversal. [verified]**

The primary item-tree documentation describes flat item arrays, dynamic repeater subtrees, `ItemRc`/`ItemWeak`, and separate back-to-front rendering versus front-to-back hit testing. The implementation defines `ItemRc` as a strong item-tree reference plus an index, `ItemWeak::upgrade` as an optional tree upgrade, and `TraversalOrder::{BackToFront, FrontToBack}`. Evidence: [S1 item-tree documentation](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/item-tree.md), [`item_tree.rs#L335-L342`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/item_tree.rs#L335-L342), [`#L1209-L1236`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/item_tree.rs#L1209-L1236).

**C-SL-02 — Slint's reactivity is lazy and dependency-tracked, not an eager rebuild of every view. [verified]**

`PropertyHandle::update` evaluates a dirty binding only when the value is read, and property reads register with the current binding. `PropertyTracker::evaluate_if_dirty` evaluates only when dirty while preserving dependency registration. Evidence: [`properties.rs#L768-L810`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/properties.rs#L768-L810), [`#L1329-L1438`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/properties.rs#L1329-L1438), and the [property-binding deep dive](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/property-binding-deep-dive.md).

**C-SL-03 — Slint supports partial rendering, but partial rendering is a capability rather than the default pixel-redraw behavior. [verified]**

`PartialRenderer` computes dirty regions from changed geometry or dirty rendering-property trackers, and `filter_item` can suppress off-screen or clean items. However, `RepaintBufferType::NewBuffer` is the default and explicitly means the full window is redrawn. Partial pixel reuse requires a reused or swapped buffer. Evidence: [`partial_renderer.rs#L1-L18`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/partial_renderer.rs#L1-L18), [`#L375-L392`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/partial_renderer.rs#L375-L392), [`#L458-L520`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/partial_renderer.rs#L458-L520), [`#L768-L797`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/partial_renderer.rs#L768-L797).

**C-SL-04 — Slint keeps text-edit state in the Rust item and uses renderer text-layout queries for cursor and hit-testing geometry. [verified]**

`TextInput` stores text, cursor/anchor offsets, preedit state, undo/redo data, focus and rendering-cache metadata. Mouse handling asks the renderer for byte offset/affinity, key handling processes IME composition, and rendering delegates to `draw_text_input`. Evidence: [`items/text.rs#L1105-L1155`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/items/text.rs#L1105-L1155), [`#L1241-L1285`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/items/text.rs#L1241-L1285), [`#L1367-L1425`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/items/text.rs#L1367-L1425), [`#L1550-L1570`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/items/text.rs#L1550-L1570), and the [text-layout documentation](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/docs/development/text-layout.md).

**C-SL-05 — Slint's render phase is not strictly side-effect-free. [verified]**

`TextInput::render` can issue an input-method update request to the window adapter. Evidence: [`items/text.rs#L1671-L1688`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/items/text.rs#L1671-L1688).

**C-SL-06 — Slint's weak item handle is a useful lifecycle pattern, but it is not by itself a generation-safe public handle. [plausible]**

`ItemWeak` contains an item-tree weak reference and an index; upgrade validates tree lifetime but the shown type has no explicit generation field. A Python-facing handle should therefore add window identity, entity type, and generation validation rather than expose raw indices. This is an inference from the source, not a claim that Slint's internal handles are unsafe. Evidence: [`item_tree.rs#L1209-L1222`](https://github.com/slint-ui/slint/blob/70067e98eac2870d2ed11510134d518b51e5ea13/internal/core/item_tree.rs#L1209-L1222).

### Iced

**C-IC-01 — Iced retains a persistent widget-state tree and reconciles new widgets against it by tag. [verified]**

`UserInterface::build` accepts a reusable `Cache`, calls `state.diff(&mut root)`, and then lays out the root. `Tree::diff` recreates state when the widget tag differs; otherwise it delegates to widget-specific diffing. Evidence: [`user_interface.rs#L99-L128`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/runtime/src/user_interface.rs#L99-L128), [`widget/tree.rs#L1-L68`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/core/src/widget/tree.rs#L1-L68).

**C-IC-02 — Iced's retained state tree does not imply that its UI layer skips whole layout or draw traversals. [verified]**

On `UserInterface::build`, the runtime calls root layout after diffing. On `UserInterface::draw`, it resets the renderer and calls root draw. Widget-specific layout and renderer implementations may still avoid individual work, but these call sites do not establish damage tracking or whole-subtree paint skipping. Evidence: [`user_interface.rs#L99-L128`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/runtime/src/user_interface.rs#L99-L128), [`#L557-L603`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/runtime/src/user_interface.rs#L557-L603).

**C-IC-03 — Iced owns text editing and input-method behavior in retained widget state, while text shaping/layout is cached in the graphics layer. [verified]**

`TextInput` uses a typed tree state containing `text::Input`, the last externally supplied value, and transaction tracking. Layout synchronizes external text when no pending transaction is active. Text updates request redraw or layout invalidation, and the graphics cache stores shaped cosmic-text buffers keyed by content and text attributes. Evidence: [`widget/src/text_input.rs#L262-L311`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/widget/src/text_input.rs#L262-L311), [`#L454-L458`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/widget/src/text_input.rs#L454-L458), [`core/src/text/input.rs#L132-L205`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/core/src/text/input.rs#L132-L205), [`graphics/src/text/cache.rs#L11-L100`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/graphics/src/text/cache.rs#L11-L100).

**C-IC-04 — Iced's controlled-input transaction pattern is directly relevant to a Python model with a Rust-local editor. [plausible]**

The source avoids overwriting a locally edited value while an external transaction is unresolved. Applying the same rule would prevent a delayed Python state echo from resetting the caret or discarding IME composition. This is a design inference, not a measured FFI result. Evidence: [`widget/src/text_input.rs#L283-L311`](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/widget/src/text_input.rs#L283-L311).

### Xilem and Masonry

**C-XM-01 — Xilem separates lightweight reactive views from Masonry's retained widget tree. [verified]**

Xilem's `View` trait has `build`, `rebuild(previous)`, `teardown`, and `message` lifecycle methods. Masonry's `RenderRoot` owns the widget tree and runs event, rewrite, and render passes. Evidence: [`xilem_core/src/view.rs#L23-L105`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/xilem_core/src/view.rs#L23-L105), [`masonry_core/src/app/render_root.rs#L53-L72`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/app/render_root.rs#L53-L72), and [Masonry architecture](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry/ARCHITECTURE.md).

**C-XM-02 — Xilem uses view paths and generations to reject stale messages to rebuilt sequence children. [verified]**

`Vec<ViewSequence>` packs index and generation into a `ViewId`, increments the generation when a child is removed, and returns `MessageResult::Stale` when a message's generation no longer matches. Evidence: [`impl_vec.rs#L11-L55`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/xilem_core/src/view_sequences/impl_vec.rs#L11-L55), [`#L106-L190`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/xilem_core/src/view_sequences/impl_vec.rs#L106-L190), [`#L213-L229`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/xilem_core/src/view_sequences/impl_vec.rs#L213-L229).

**C-XM-03 — Masonry incrementally invalidates layout/compose/paint work, but it does not currently implement damage-region rendering. [verified]**

The layout pass returns early when layout is clean and the chosen size is unchanged. The paint pass rebuilds scenes only for widgets with paint requests, appends cached scenes, and still recurses through children. Both `RenderRoot::redraw` and the paint pass contain explicit TODOs for invalidation/damage regions. Evidence: [`passes/layout.rs#L350-L380`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/passes/layout.rs#L350-L380), [`passes/paint.rs#L90-L210`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/passes/paint.rs#L90-L210), [`app/render_root.rs#L609-L622`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/app/render_root.rs#L609-L622).

**C-XM-04 — Masonry bounds rewrite-pass reentrancy and defers unresolved invalidations to a later frame. [verified]**

`run_rewrite_passes` runs at most four iterations; if invalidations remain, it warns and requests another redraw. Deferred mutate callbacks whose target was removed are skipped. Evidence: [`app/render_root.rs#L828-L881`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/app/render_root.rs#L828-L881), [`passes/mutate.rs#L64-L82`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/passes/mutate.rs#L64-L82).

**C-XM-05 — Masonry centralizes focus, pointer capture, IME, and text editing in Rust. [verified]**

The pass-system documentation routes pointer events to the hovered/capturing widget and text/accessibility events to the focused widget, then bubbles to parents. `TextArea` owns a Parley `PlainEditor` and handles IME preedit/commit, selection, cursor animation, layout and paint invalidation. Evidence: [pass-system documentation](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry_core/src/doc/pass_system.md), [`widgets/text_area.rs#L47-L81`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry/src/widgets/text_area.rs#L47-L81), [`#L544-L800`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/masonry/src/widgets/text_area.rs#L544-L800).

**C-XM-06 — Reactive reconciliation still has correctness-critical ordering invariants; the 2026-11-22 Xilem fix is direct implementation evidence. [verified]**

Commit `9a78df878a9269a88325ebd71f3f68c757f0a396` fixes `ZStackSplice` inserting rebuilt dynamic children at the end instead of the sequence splice index. The commit message records resulting z-order divergence, downcast mismatches, and possible panics on later rebuilds. The fixed source inserts at `self.idx` and advances it. Evidence: [dated fix commit](https://github.com/linebender/xilem/commit/9a78df878a9269a88325ebd71f3f68c757f0a396), [`xilem_masonry/src/view/zstack.rs`](https://github.com/linebender/xilem/blob/9a78df878a9269a88325ebd71f3f68c757f0a396/xilem_masonry/src/view/zstack.rs).

### Flutter

**C-FL-01 — Flutter's declarative widgets are configuration objects; elements and render objects are retained across builds. [verified]**

`updateChild` reuses an element when runtime type and key match, updates it in place, or removes/replaces it otherwise. Multi-child reconciliation scans matching ends and uses keyed matching for the middle. Evidence: [`framework.dart#L384-L388`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L384-L388), [`#L3987-L4070`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L3987-L4070), [`#L4223-L4295`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L4223-L4295).

**C-FL-02 — Flutter incrementally schedules build, layout, and paint work. [verified]**

`BuildOwner` sorts and rebuilds dirty elements. `PipelineOwner.flushLayout` processes dirty layout nodes and skips clean nodes; `flushPaint` processes dirty paint nodes. `RenderObject.layout` returns early when constraints and layout are unchanged, and repaint boundaries limit dirty propagation. Evidence: [`framework.dart#L2833-L2844`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L2833-L2844), [`rendering/object.dart#L1139-L1177`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/object.dart#L1139-L1177), [`#L1295-L1330`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/object.dart#L1295-L1330), [`#L2810-L2870`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/object.dart#L2810-L2870), [`#L3344-L3368`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/object.dart#L3344-L3368).

**C-FL-03 — Flutter's text layout and input routing are retained runtime responsibilities. [verified]**

`RenderParagraph` owns a `TextPainter`, lays out text and inline placeholders during `performLayout`, and ensures a valid layout before painting. Pointer-down performs a hit test and stores the hit-test path; subsequent move/up events use the down path, with pointer-router dispatch for captured gestures. Evidence: [`rendering/paragraph.dart#L329-L405`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/paragraph.dart#L329-L405), [`#L972-L986`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/paragraph.dart#L972-L986), [`#L1046-L1050`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/rendering/paragraph.dart#L1046-L1050), [`gestures/binding.dart#L385-L430`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/gestures/binding.dart#L385-L430), [`#L467-L485`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/gestures/binding.dart#L467-L485).

**C-FL-04 — Flutter's build-time mutation guards are a useful model for FFI reentrancy rules. [plausible]**

The framework asserts against marking unrelated dirty elements during build and exposes explicit lifecycle/mutation phases. A Python/Rust boundary should make legal mutation phases explicit in the API and reject or defer mutations from paint/layout callbacks. This is an inference from Flutter's guards, not a requirement to reproduce its internals. Evidence: [`framework.dart#L5374-L5405`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L5374-L5405), [`#L5538-L5574`](https://github.com/flutter/flutter/blob/c0b4744c302be253e6cececa7b553baa32e44543/packages/flutter/lib/src/widgets/framework.dart#L5538-L5574).

### Dear ImGui

**C-DI-01 — Dear ImGui's default API is immediate, but its implementation retains substantial UI state. [verified]**

The programmer guide says application code creates the UI every frame. The implementation finds or creates windows by name and retains window information across frames; `ImGuiContext` retains window maps and per-window state storage; `ImGuiInputTextState` retains active text-edit state. Evidence: [`imgui.cpp#L201-L217`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L201-L217), [`#L7635-L7655`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L7635-L7655), [`imgui_internal.h#L1327-L1379`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_internal.h#L1327-L1379), [`#L2360-L2365`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_internal.h#L2360-L2365), [`#L2770-L2772`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_internal.h#L2770-L2772).

**C-DI-02 — Dear ImGui currently has an experimental window skip-refresh path, so full UI re-submission is not universal implementation behavior. [verified]**

`UpdateWindowSkipRefresh` can mark a window to avoid refresh unless it is appearing, hidden, hovered, or focused under the selected policy. The begin path skips initialization and item submission when `SkipRefresh` is set. Evidence: [`imgui.cpp#L7600-L7622`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L7600-L7622), [`#L7804-L7820`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L7804-L7820), [`#L8373-L8390`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L8373-L8390).

**C-DI-03 — Dear ImGui keeps layout, hit testing, text rendering, and mesh generation in the library; the backend receives renderer-neutral draw data and input/capture flags. [verified]**

The programmer guide states that rendering information is stored in command lists and the library does not touch GPU state. The example loop calls platform/renderer new-frame hooks, `NewFrame`, UI submission, `Render`, then `RenderDrawData`. The FAQ defines `WantCaptureMouse`, `WantCaptureKeyboard`, and `WantTextInput` as the input-routing contract. Text measurement and glyph drawing are implemented in the library's draw path. Evidence: [`imgui.cpp#L271-L318`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui.cpp#L271-L318), [`imgui_draw.cpp#L2950-L2985`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_draw.cpp#L2950-L2985), [`#L7343-L7365`](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/imgui_draw.cpp#L7343-L7365), [FAQ input-routing section](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/docs/FAQ.md#q-how-can-i-tell-whether-to-dispatch-mousekeyboard-to-dear-imgui-or-my-application), and the [example main loop](https://github.com/ocornut/imgui/blob/bd4e3b0abccd653490d68beeb72f0750cde6d5f6/examples/example_glfw_opengl3/main.cpp).

### Cross-cutting conclusions

**C-XC-01 — Retained versus immediate is an API choice; incrementality is an implementation choice. [verified]**

Dear ImGui's immediate API retains windows and state and now has an experimental skip-refresh path. Flutter recreates widget configuration while retaining elements/render objects. Masonry retains widgets/scenes but lacks pixel damage tracking. These sources establish that the categories cannot be used as synonyms. Evidence: C-DI-01, C-DI-02, C-FL-01, C-XM-03.

**C-XC-02 — Every reviewed full UI runtime keeps layout, text geometry, focus/capture, and input routing inside the UI runtime rather than delegating them to application business logic. [verified]**

Evidence: C-SL-04, C-IC-03, C-XM-05, C-FL-03, C-DI-03.

**C-XC-03 — A Python-first API can use Python as a patch producer while Rust owns every frame, but the FFI cost and ergonomics are not established by this research. [plausible]**

The architecture follows the division above, but no reviewed framework demonstrates this exact Python/Rust boundary. It requires the RQ-03 benchmark and a Python API prototype.

**C-XC-04 — Whole-application Python immediate mode conflicts with the “no Python callbacks per frame” target unless Python output is cached and replayed by Rust. [plausible]**

If Python executes widget-producing code each frame, the target is violated by construction. Caching a Python-produced command tree changes the execution model into event-driven submission plus Rust replay; at that point the retained/immediate distinction is mostly API syntax. This is an architectural inference, not a measured FFI cost.

**C-XC-05 — None of the reviewed evidence establishes that retained trees, dirty flags, cached scenes, or damage regions meet pygpui's requested performance numbers. [unverified]**

The sources describe mechanisms, not comparable pygpui workloads on certified hardware. `STATE.md` explicitly classifies all requested numbers as targets.

## Claim-level confidence

Every decision-driving `C-*` claim and `R*` recommendation carries an inline label:

- **verified** — directly supported by a dated primary documentation/source snapshot or reproducible observation.
- **plausible** — an architectural inference supported by the reviewed mechanisms but not established for pygpui.
- **unverified** — an assumption, target, or claim without adequate evidence.

The comparison table summarizes the detailed `C-*` claims. No performance target is labeled verified.

## Contradictions and documentation-intention gaps

| Framework | Documentation intention or shorthand | Implementation evidence | Resolution for pygpui |
|---|---|---|---|
| **Slint** | Custom-renderer documentation presents partial rendering as an optional implementation feature. | `PartialRenderer` exists in core, but `RepaintBufferType::NewBuffer` is the default full redraw. | Treat dirty-region filtering and framebuffer reuse as separate, testable choices. Do not infer partial pixels from a retained item tree. [verified] |
| **Slint** | Rendering is naturally discussed as drawing. | `TextInput::render` can request a platform IME update. | Keep paint callbacks free of Python and preferably queue platform side effects outside the pure paint phase. [verified fact; plausible recommendation] |
| **Iced** | README advertises a reactive model and responsive layout. | `UserInterface::build` diffs state and then calls root layout; `draw` resets and calls root draw. | “Reactive” proves state continuity, not damage tracking or bounded layout work. Benchmark actual traversal and renderer costs. [verified] |
| **Masonry** | Architecture says “be dumb,” with no reconciliation logic or clever optimizations. | Masonry has invalidation flags, measurement caches, per-widget scene caches, and a bounded rewrite loop. Xilem supplies reconciliation. | Read the goal as “no high-level reconciliation in Masonry,” not “no caching or algorithms.” Preserve the layer boundary. [verified] |
| **Flutter** | Declarative widget descriptions can be recreated by `build`. | Elements and render objects are retained; `updateChild` reconciles by type/key and dirty queues schedule work. | Declarative configuration does not require recreating runtime nodes or native objects. [verified] |
| **Dear ImGui** | FAQ comparison says UI is fully issued every update and the library stores minimal data. | The FAQ also explicitly says IMGUI describes the API, not the implementation. Current source retains windows/state and has experimental skip-refresh. | Use Dear ImGui as an immediate-API contrast, not as evidence that immediate mode is stateless or always fully laid out. [verified] |
| **Xilem** | Reactive views and generational IDs are intended to preserve identity and reject stale messages. | The 2026-11-22 ZStack fix records real index-order corruption and later downcast/panic failures. | Generation checks are necessary but insufficient; sequence splice order, key identity, and teardown invariants need property tests. [verified] |

## Recommendation

### R1 — Adopt a retained Rust core with event-driven Python patches. [plausible]

- **Python owns:** application/domain state, reusable Python view definitions, command construction, and user callback code.
- **Rust owns:** windows, entity slots, retained view/runtime nodes, geometry, text editor and shaping caches, focus/capture/IME/clipboard state, accessibility state, render resources, frame scheduling, and presentation.
- **Boundary:** Python emits typed descriptions or patches when state changes or an event is delivered. Rust validates and applies them. Python is not called to rebuild, lay out, shape, paint, or present an unchanged frame.

This combines Xilem's view/runtime split, Iced's tag/state continuity, Slint's dependency tracking, and Masonry's pass engine without copying their implementations.

### R2 — Make entity identity explicit and generation-safe. [plausible]

Use a handle containing at least window ID, entity slot, generation, and expected node kind. Validate every handle at the FFI boundary and again when deferred work executes. Parent links should be weak or index-based; callbacks should carry the origin handle and a state version. Reject stale generations instead of silently routing to a reused slot.

Transfer sources: Slint `ItemWeak`, Xilem `ViewId` generations, Flutter keys, and Dear ImGui ID scopes. The Xilem ZStack incident shows why identity alone does not replace ordering and teardown tests.

### R3 — Use a bounded phase pipeline and prohibit arbitrary reentrancy. [plausible]

Recommended Rust-owned phases:

1. Drain platform input and internal timers.
2. Route input using current focus/capture/hit-test state.
3. Queue semantic messages for Python and drain deferred mutations.
4. Diff/apply view patches and run a bounded number of rewrite/update passes.
5. Run layout, compose/transform, text layout, and accessibility invalidation.
6. Queue platform effects such as IME cursor updates and clipboard requests.
7. Paint/cache render data and present.

Rules: no entity deletion during layout or paint; no Python callback while Rust holds a tree borrow; deferred mutations revalidate targets; cap rewrite iterations and defer unresolved work to the next frame. Transfer sources: Masonry's four-pass cap and Flutter's build/layout mutation guards.

### R4 — Keep transient text interaction in Rust and synchronize semantic document changes to Python. [plausible]

Rust should own caret, anchor, selection geometry, preedit/composition, undo/redo, cursor blink, hit-testing, shaping, wrapping, and text caches. Python owns the document's application meaning and receives versioned semantic changes. External Python text updates must not overwrite a newer local edit or active composition.

Use one documented offset convention across the FFI, preferably UTF-8 byte offsets with explicit validation, because the reviewed Rust text stacks expose byte-based editing and cursor APIs. Do not assume Python string indices are interchangeable.

Transfer sources: Slint `TextInput`, Iced `text::Input` and transaction tracking, Masonry `PlainEditor`, Flutter `TextPainter`, and Dear ImGui `ImGuiInputTextState`.

### R5 — Incrementality should be layered and measured independently. [plausible]

Implement, in order:

1. Retained node identity and state.
2. Dirty flags for layout, compose/transform, paint, accessibility, and text shaping.
3. Measurement, shaped-paragraph, scene/display-list, and resource caches.
4. Virtualization that creates only visible rows.
5. Optional damage-region rasterization with a full-redraw fallback.

A retained tree is not proof of incremental rendering. Masonry's cached scenes without damage regions and Slint's default `NewBuffer` full redraw are direct counterexamples to that inference.

### R6 — Allow immediate mode only as a narrow Rust-owned leaf. [plausible]

An ephemeral overlay, inspector, tool palette, or debug HUD may use an immediate command builder. The builder must execute in Rust or replay a cached Rust command buffer. If Python supplies the leaf description, submit it on change rather than invoking Python every frame.

Do not make the primary application API whole-tree immediate mode: that either requires Python each frame or disguises a retained command cache as immediate mode.

### R7 — Keep clean-room boundaries behavioral and provenance explicit. [verified for this report's process; plausible as risk guidance]

This report copied no source code and describes mechanisms rather than translating implementation line by line. The reviewed licenses differ materially:

| Framework | Primary license evidence at S1–S5 | Consequence for future provenance review |
|---|---|---|
| Slint | Triple license: royalty-free desktop/mobile/web license, GPLv3, or commercial license; documentation/examples are MIT. | Do not assume Apache-2.0. Any Slint-derived code or assets need exact file-level license review. |
| Iced | MIT. | MIT notice retention applies to copied substantial portions. |
| Xilem/Masonry | Apache-2.0. | Source-derived ports need license, modified-file notices, retained attributions, and NOTICE treatment where applicable. |
| Flutter | BSD-3-Clause. | Source-derived ports need copyright/conditions retention and binary notice reproduction. |
| Dear ImGui | MIT. | MIT notice retention applies to copied substantial portions. |

Behavioral concepts can be recorded as prior art, but this report does not make a legal determination that any future implementation is non-infringing. Any source-derived port, generated code, asset, or substantial translation should receive provenance review before merge. The GPUI-specific clean-room decision remains with the GPUI-internals research stream.

## Exact evidence gaps

1. **No pygpui benchmark exists.** The 120 fps, 10,000-row, p95 < 8 ms, idle-CPU, and zero-Python-callback targets are [unverified]. Required: RQ-03's reproducible benchmark with disclosed hardware/software and callback counters.
2. **No cross-framework performance comparison on one workload.** Source mechanisms are comparable; frame times are not. Required: identical widget/text/input workload across candidate backends, with and without virtualization and damage tracking.
3. **No evidence for the exact Python/Rust FFI cost.** Required: patch serialization, GIL acquisition, callback, and stale-handle validation measurements on the event path and the unchanged frame path.
4. **No selected text stack.** Parley, cosmic-text, Skia text, or another engine differ in shaping, editing, IME, font fallback, and allocation behavior. Required: RQ-02 dependency selection plus text-specific benchmarks and IME tests.
5. **No selected renderer or damage strategy.** Required: renderer-specific scene/display-list reuse, partial-buffer semantics, GPU timestamp profiling, and occlusion/resize behavior.
6. **No platform matrix.** Required: RQ-04 evidence for Windows/macOS/Linux IME, clipboard, accessibility, HiDPI, pointer capture, and input-method lifecycle.
7. **No dynamic-tree correctness campaign.** Required: property/fuzz tests for keyed reorder, insert/remove at arbitrary indices, teardown during queued events, stale generations, repeated rebuilds, and nested sequences. The Xilem ZStack fix makes this a blocking validation area.
8. **No Python API ergonomics evidence.** Required: a small prototype with reusable Python views, controlled text input, stable handles, event callbacks, and a virtualized list; measure both correctness and developer friction.
9. **No release-package verification.** The evidence is pinned to current repository commits. Required: repeat decision-critical checks against the exact versions selected for pygpui.
10. **Qt was not researched.** This is intentional scope control, not a finding that Qt is unsuitable. Reopen only if Qt/QML integration or licensing becomes a live option.
11. **No legal sign-off.** Required before any source-derived code or assets are accepted; license texts alone do not decide derivative-work or provenance questions.

## Claims the Skeptic should attack first

1. **C-XC-03/C-XC-04:** whether event-driven Python patches can truly avoid Python on unchanged frames while preserving a pleasant reusable-view API.
2. **C-SL-06/C-XM-02/R2:** whether the proposed generation/type/window handle validation is sufficient for deferred events and dynamic sequence mutation.
3. **R4:** whether Rust-local text editing can synchronize with a Python document model without lost updates, cursor resets, or IME corruption.
4. **R5:** which incrementality layer is actually necessary for the performance targets; damage tracking must not become an unmeasured prerequisite.
5. **R6:** whether a Rust-owned immediate leaf adds enough value to justify a second authoring model.
