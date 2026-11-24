# ADR 0003: Expose a small typed Python API over opaque native handles

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; this resolves OQ-05 conservatively, subject to prototype validation.

## Context

No public API exists yet. The evidence supports generation-safe identity, weak subscriptions, non-owning window handles and single-owner update turns, but not a particular Python syntax. The minimum API must prove one interactive window without exposing winit, wgpu, Taffy or PyO3 types and without offering a Python frame callback.

## Decision

The provisional public surface is `App`, `Entity[T]`, `WeakEntity[T]`, `View[T]`, `ViewHandle`, `WindowHandle`, `Element`, `Action`, typed errors and the slice-1 elements `Text`, `Button`, `Row` and `Column`. A minimal program is:

```python
from dataclasses import dataclass
from typing import ClassVar
import pygpui as ui

@dataclass(frozen=True)
class Increment(ui.Action):
    name: ClassVar[str] = "increment"
    version: ClassVar[int] = 1

class Counter:
    def __init__(self) -> None:
        self.value = 0

def increment(state: Counter) -> None:
    state.value += 1

class CounterView(ui.View[Counter]):
    def __init__(self, state: ui.Entity[Counter]) -> None:
        self.state = state

    def build(self) -> ui.Element:
        return ui.Column(children=[
            ui.Text(f"Count: {self.state.get().value}"),
            ui.Button(label="Increment", action=Increment()),
        ])

    def update(self, action: ui.Action) -> None:
        if isinstance(action, Increment):
            self.state.update(increment)
            self.refresh()

app = ui.App()
window: ui.WindowHandle = app.mount(
    CounterView(app.entity(Counter())), title="Counter"
)
app.run()
```

- `View.build()` is a semantic-boundary operation, never a render-frame callback. `refresh()` requests one coalesced rebuild; `update()` handles validated semantic actions. Element values are immutable descriptions with stable `key` identity for dynamic children.
- `Entity[T]` is an opaque strong handle. Rust owns its registry record, liveness, generation and version; the Python domain value lives only in the event actor. `entity.weak()` returns `WeakEntity[T]`, which cannot keep it alive; `upgrade()` returns a live `Entity[T]` or `None`. `get`/`update` are legal during setup and Python event turns, not from background threads or native layout/paint.
- `ViewHandle` and `WindowHandle` are opaque, non-owning and generation-checked. A mounted view receives its `ViewHandle` as `self.handle`; delivered actions carry the origin handle and entity version so stale actions can be rejected. Every operation on a stale/closed/wrong-kind handle raises a typed error; no raw index or pointer is exposed.
- `App.run() -> int` is synchronous, once per process, on the platform main thread. Slice 1 mounts one window before `run()`. Window lifecycle changes during callbacks must be deferred with `app.post(...)`; background threads may only post validated commands.
- `build()` is read-only: entity mutation and window lifecycle changes are rejected. `update()` may mutate its bound entity and request refresh, but cannot recursively dispatch or enter `run()`. Deferred commands revalidate handles when executed.
- Closing a window invalidates its handles and subscriptions before another Python event is delivered. Entity release is deferred to an event boundary after the last strong handle disappears; callbacks use weak references to avoid cross-language cycles.
- Public modules re-export only the documented surface through explicit `__all__`; `_native` is private. Action names and payload schemas are versioned independently of Python class names. Errors derive from `PygpuiError`, with `StaleHandleError`, `InvalidSnapshotError`, `ReentrancyError` and `RuntimeUnavailableError` in slice 1.

### Crate and module boundaries

| Boundary | Owns | May not depend on |
|---|---|---|
| `pygpui/` | typed facade, actions, view registry, manual stubs, `py.typed` | public Rust implementation types |
| `crates/pygpui-python` | PyO3 adapter, ABI conversion, event actor | being imported by any other crate |
| `crates/pygpui-protocol` | native snapshot/command/event/error value types | PyO3, winit, wgpu, Taffy |
| `crates/pygpui-core` | identity, bounded queues, lifecycle, invalidation scheduler | platform, renderer, Python |
| `crates/pygpui-scene` | retained nodes, focus/input/IME/a11y mirror, Taffy/text adapters, primitives | PyO3, winit, wgpu |
| `crates/pygpui-render` | wgpu device/surface rendering and native resource caches | PyO3, winit |
| `crates/pygpui-platform` | one winit main loop, OS events, surface orchestration | PyO3 |

Dependency direction is `python → platform → render/core/scene → protocol`; shared types stay in the lower layers. Only the designated crate may import each external framework.

## Alternatives considered

- **Expose raw native handles or a GPUI-like context API:** rejected because it leaks unstable implementation types and makes safe borrowing a Python concern.
- **Python render/measure/animation callbacks:** rejected because they violate ADR 0001 and make the frame path scheduling-dependent.
- **Direct mutable entity access from any thread:** rejected because it bypasses generations, leases and deterministic teardown.
- **A broad widget/API surface in slice 1:** deferred until the Counter slice proves the boundary and typing contract.

## Consequences

- The API is intentionally small and explicit; users call `refresh()` rather than receiving implicit per-frame builds.
- One complete snapshot copy and one event-actor callback are acceptable first-slice costs; FFI cost remains unverified.
- Stable keys and typed actions add authoring discipline but also validation and migration obligations.
- Multiwindow, rich text editing, virtualized-list authoring and async integration require later ADRs rather than ad-hoc expansion.

## Evidence links

- [Skeptic §6 — ownership, API and lifecycle decisions](../REVIEWS/phase-0-research-skeptic.md#6-verified-decision-set-for-architect).
- [RQ-01A — lifecycle/reentrancy recommendation](../RESEARCH/2026-11-24-rq-01-gpui-internals.md#recommendation).
- [RQ-01B R2–R4 — identity, bounded phases and text synchronization](../RESEARCH/2026-11-24-rq-01-cross-framework.md#recommendation).
- [RQ-02B C17–C22 — strict typed facade](../RESEARCH/2026-11-24-rq-02-python-abi3-typing.md#d-strict-typing-and-public-api-strategy).

## Validation gates

- **AR03-G1 — API contract:** the Counter example type-checks under `mypy --strict --disallow-any-explicit --python-version 3.11`; `stubtest` passes with a reviewed allowlist; negative fixtures reject invalid actions, callbacks and `_native` imports.
- **AR03-G2 — handles:** tests exit zero for strong/weak lifetime, generation reuse, wrong-kind/window handles, close-before-event and stale deferred commands.
- **AR03-G3 — reentrancy:** tests exit zero for mutation during `build`, nested dispatch, `run()` reentry, close during notification and entity release during callback; illegal operations raise typed errors rather than deadlock or panic.
- **AR03-G4 — boundary ownership:** a static audit exits zero proving no Python reference exists in `WindowSnapshot`, scene nodes or frame caches, and that only `pygpui-python` imports PyO3.
- **AR03-G5 — crate graph:** `cargo metadata --locked` plus an architecture test exits zero with only the dependency edges in the table.

## Revisit when

The Counter prototype exposes blocking ergonomics problems; multiwindow or async execution is requested; or measured event-boundary cost requires batching/schema changes. Public renames or semantic changes require a compatibility plan and a superseding ADR; internal crate moves may be made without changing the contract.
