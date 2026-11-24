# RQ-02B — Python ABI, typing, runtime and wheel delivery boundary

Status: Round 1 complete  
Task: P0-R02B  
Researcher: Researcher-Libs instance B  
Research/access date: 2026-11-24  
Decision unblocked: Python delivery boundary for RQ-02; OQ-04 free-threaded launch policy; strict public API strategy; cross-platform wheel plan.

## Question

How should pygpui bind Rust to Python, target the CPython ABI, expose a strict-typed public API, integrate optional async runtimes, and build/sign wheels for macOS, Windows and Linux while keeping Python out of the per-frame path?

## Method and limits

- Reviewed versioned PyO3 0.30.1 documentation and tagged source, maturin 1.16.0 documentation/tagged source/release workflow, current PyPI/crates.io metadata, CPython/PEP specifications, mypy 2.4.1 documentation, and OS-vendor signing documentation.
- Reproduced local tool versions only: Python 3.14.10, rustc 1.100.0, cargo 1.100.0 on Linux. No pygpui code exists, so no extension, wheel, window, typing or performance result has been measured.
- All sources below were accessed on 2026-11-24. “Latest” means latest stable release found on that date, not a promise about later releases.
- Evidence labels follow `.harness/PROCESS.md`: **verified**, **plausible**, **unverified**.

## Executive recommendation

1. **verified mechanism / plausible adoption:** Pin the first vertical slice to **PyO3 0.30.1** and **maturin 1.16.0**. Target CPython **>=3.11** with `abi3-py311`; publish one GIL-enabled `cp311-abi3` wheel per OS/architecture, not one wheel per Python minor. Python 3.10 reached EOL on 2026-10-01. [S01, S02, S08, S34]
2. **verified:** Current PyO3 **does not support Python 3.13t**; 0.29.0 explicitly dropped it. Do not claim 3.13t. Python 3.14t is officially supported by CPython, but needs a separate version-specific wheel and is not an initial target. `abi3t` starts at Python 3.15 and is also deferred. [S03, S05, S16, S17]
3. **plausible:** Keep `#[pymodule(gil_used = true)]` until the extension's `unsafe`, `Send`/`Sync`, callback and shutdown behavior are audited. PyO3 0.28+ defaults to claiming free-threaded safety, which is inappropriate before that audit. [S04]
4. **plausible:** Rust owns the native event loop, retained scene, layout, animation and rendering. `App.run()` detaches from Python for the native loop and only reattaches for discrete semantic callbacks. Raw OS events, redraw requests and frames never call Python. This is an architectural invariant to implement and test, not a measured performance result. [S04, S27]
5. **verified mechanism / plausible adoption:** Ship an in-package `py.typed` and hand-reviewed `.pyi` files. Use PyO3 0.30.1 `experimental-inspect` plus `maturin generate-stubs` only as a reviewed draft/diff initially; the generator is still active development and has documented completeness limitations. [S06, S07, S20–S23]
6. **verified:** `mypy --strict` is useful but does not forbid every explicit `Any`. Add `disallow_any_explicit = true` for the public surface, run clean-installed-wheel consumer tests, and run `stubtest` for runtime signature drift. `stubtest` does not prove semantic return-type correctness. [S19–S22]
7. **plausible:** Do not put Tokio, `experimental-async`, or `pyo3-async-runtimes` in the first slice's default path. If awaitable non-UI operations are later required, evaluate `pyo3-async-runtimes 0.30.0`; co-driving it with a native desktop UI loop remains unverified, especially on macOS. [S09, S24, S25]
8. **verified:** `abi3` reduces Python-minor builds only. It does not remove OS/architecture builds, native-library repair, platform testing, accessibility work or OS signing policy. [S02, S10–S13]
9. **verified scope / unverified production support:** maturin 1.16.0 supports PyPI trusted publishing/attestations and performs limited **ad-hoc** Mach-O re-signing during macOS wheel repair. No documented Developer ID/notarization or Authenticode pipeline was established; treat production OS signing as unsupported until separately implemented and tested. [S11–S15, S29–S33]
10. **plausible:** Provisional first-release matrix: macOS universal2, Windows x64, Linux x86_64 manylinux_2_28. Defer Windows ARM64, Linux ARM64, musllinux, 32-bit and all free-threaded wheels until OQ-03 and demand justify them. [S26, S27]

## Exact candidate versions and disposition

| Component | Exact version | Release/publication date | License | MSRV / Python requirement | Role and disposition | Evidence |
|---|---:|---|---|---|---|---|
| PyO3 | 0.30.1 | 2026-10-14 | MIT OR Apache-2.0 | Rust 1.85; CPython 3.9–3.15 supported by this release line | **Adopt**, exact pin for first slice | S01, S02 |
| maturin | 1.16.0 | 2026-10-29 | MIT OR Apache-2.0 | Rust 1.89 to build maturin; published tool wheel requires Python >=3.7 | **Adopt**, exact pin for first slice | S08, S10, S11 |
| CPython ABI floor | 3.11 (`abi3-py311`) | Product choice; 3.10 EOL 2026-10-01 | N/A | N/A | **Provisional adopt**; avoids an EOL floor and reduces typing backports | S02, S34 |
| mypy | 2.4.1 | 2026-10-28 | MIT | Python >=3.10 | **Adopt as development gate**, not runtime dependency | S19 |
| PyO3 stub generator | `experimental-inspect` in PyO3 0.30.1; `pyo3-introspection` 0.30 line | 2026-10-14 / maturin dependency current at access | MIT OR Apache-2.0 | Same as PyO3 | **Evaluate in CI**, not sole source of public stubs | S01, S06, S11 |
| pyo3-async-runtimes | 0.30.0 | 2026-10-15 | Apache-2.0 | Rust 1.85; Python >=3.9 | **Defer**, optional non-UI async adapter candidate | S24 |
| Tokio | 1.54.1 | 2026-10-21 | MIT | Rust 1.85 | **Defer**, only if the optional adapter selects Tokio | S25 |
| cibuildwheel | 4.3.5 | 2026-10-27 | BSD-2-Clause | Python >=3.11 | **Evaluated alternative** to maturin-generated CI; useful for multi-interpreter tests and automatic `abi3audit` | S26, S27 |
| arwen-codesign | 0.0.1-alpha.1 | 2026-03-05 | MIT | Edition 2021 | Transitive maturin build-tool dependency on non-macOS; **not** a pygpui runtime dependency or production signing solution | S11, S14 |
| pyo3-asyncio | 0.20.0 | 2023-11-11 | Apache-2.0 | Older PyO3 line | **Reject for new baseline**; stale relative to PyO3 0.30.1 | S35 |

The project MSRV cannot be finalized until RQ-02A's core Rust stack is known. PyO3 requires at least Rust 1.85; maturin itself requires 1.89 if built from source. The observed local rustc 1.100.0 satisfies both, but this is not a minimum-support claim. [S01, S08, S36]

## Findings and claim ledger

### A. ABI and Python-version policy

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C01 | PyO3 0.30.1 and maturin 1.16.0 are the current stable baseline found on 2026-11-24. | **verified** | Tagged releases and registry metadata agree. Pin them for the first slice. [S01, S08] |
| C02 | A CPython >=3.11 floor is a conservative initial product choice. | **plausible** | `abi3-py311` exists; Python 3.10 is EOL. Actual dependency and user requirements still need approval. [S02, S34] |
| C03 | `abi3-py311` produces a wheel usable by GIL-enabled CPython 3.11 and later, subject to testing every supported minor. | **verified** | PEP 384/PyO3 define forward ABI compatibility; CPython warns Stable ABI is not a complete behavioral guarantee. [S02, S03, S37] |
| C04 | Current PyO3 cannot be claimed to support Python 3.13t. | **verified** | PyO3 0.29.0 dropped 3.13t; the proposed 0.30.1 baseline inherits that decision. [S05] |
| C05 | CPython 3.14 made free-threaded mode officially supported, but 3.14t has no `abi3`/`abi3t` stable-ABI wheel path. | **verified** | Python 3.14 release/PEP 779 and PEP 803. A 3.14t wheel would be version-specific (`cp314-cp314t`) and is deferred. [S16, S17] |
| C06 | `abi3t` exists for Python 3.15+ and can target both GIL-enabled and free-threaded 3.15+ interpreters. | **verified** | PEP 803, PyO3 0.30.1 and maturin >=1.14. It is not a 3.13t or 3.14t solution. [S02, S10, S18] |
| C07 | Enabling both `abi3` and `abi3t` Cargo features does not make one maturin invocation produce both wheel families. | **verified** | Maturin selects at most one stable ABI family per build; separate interpreter-specific builds are required. [S10] |
| C08 | `abi3` does not eliminate OS/architecture-specific artifacts or release policy. | **verified** | Wheels remain platform-tagged; native dependency repair, OS testing and signing are separate. [S02, S10–S13] |

### B. GIL and free-threaded behavior

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C09 | Since PyO3 0.28, modules default to declaring that they do not need the GIL. | **verified** | `gil_used = false` is the default; the declaration is an author attestation, not proof of safety. [S04] |
| C10 | pygpui should initially declare `gil_used = true` and treat free-threaded Python as unsupported. | **plausible** | Conservative until Rust `unsafe`, exposed `pyclass` mutation, callback threading and shutdown are audited. Importing on a free-threaded interpreter may re-enable the GIL and warn. [S04] |
| C11 | `Python::detach` releases the GIL/attachment for Rust-only work; `Python::attach` is required before touching Python objects again. | **verified** | PyO3 0.30.1 API and free-threading guide. Detaching also remains important on free-threaded builds to avoid global-synchronization deadlocks. [S04] |
| C12 | A long-running native loop must not hold a Python attachment or a Rust mutex that a reattaching callback may need. | **plausible** | PyO3 documents deadlocks when holding locks across attach/detach boundaries. Require short lock scopes and callback tests. [S04] |

### C. Event-driven Python boundary with no per-frame callbacks

The proposed boundary is semantic, not frame-based:

```text
Python setup / actions
        |
        v
thread-safe command queue -----> Rust UI thread
                                      |-- OS window/input/IME/accessibility events
                                      |-- retained scene + layout + animation
                                      |-- render/present loop (no Python)
                                      |
                                      +-- optional discrete semantic event/callback
                                               |
                                               v
                                      Python/asyncio adapter
```

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C13 | Rust can own the event loop and render loop while Python supplies setup, actions and optional semantic event handlers. | **plausible** | Supported by PyO3 attach/detach and native-loop ownership, but no pygpui implementation exists. Make this an ADR-level design invariant. [S04] |
| C14 | Redraw requests, animation ticks, layout, text shaping, accessibility-tree updates and GPU submission should not cross into Python. | **plausible** | This is the concrete mechanism for the no-Python-per-frame requirement. Raw events stay in Rust; only meaningful application events may cross. |
| C15 | Python remains event-driven even though it does not receive every frame. | **plausible** | Python dispatches commands and receives discrete semantic events. “Event-driven” describes the application boundary, not a Python callback on each OS redraw. |
| C16 | The proposed boundary guarantees the 120 fps, 8 ms input-to-frame and near-zero idle CPU targets. | **unverified** | No implementation or benchmark exists. Structural callback counting can prove “zero Python calls per frame”; performance still requires RQ-03 benchmarks. |

Implementation consequences for the first slice:

- Expose synchronous `App.run()` on the platform UI thread. Inside the PyO3 method, detach around the native loop; reattach only to deliver a discrete callback or lifecycle result. [S04]
- Drain a bounded/backpressured action queue at safe native-loop boundaries. Do not expose arbitrary Python render callbacks; that would invalidate C14.
- Use `Py<T>` handles rather than borrowed `Bound<'py, T>` across detach, and test reference-drop behavior. Do not enable `pyo3_disable_reference_pool` without a detached-drop audit. [S02, S04]
- Instrument a counter for every Python attachment/callback. A frame test must observe zero increments during steady-state redraw/animation with no semantic events. This is a proposed acceptance test, not an existing result.

### D. Strict typing and public API strategy

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C17 | PyO3 0.30.1 can generate `.pyi` files through `experimental-inspect`, `pyo3-introspection`, `maturin generate-stubs`, and `maturin build --generate-stubs`. | **verified** | Versioned PyO3 guide and maturin 1.15+ changelog. [S06, S07, S11] |
| C18 | Generated stubs are not yet a safe sole source of truth for a strict public API. | **verified** | The feature is active development; unsupported module forms, missing type metadata, `Incomplete` modules and Python-version-dependent output are documented. [S06] |
| C19 | In-package `.pyi` files plus `py.typed` are a supported way to type a PyO3/maturin package. | **verified** | PyO3 typing guide, current typing specification and mypy installed-package docs. [S07, S20, S21] |
| C20 | `mypy --strict` checks important unsoundness flags but does not forbid all explicit `Any`. | **verified** | mypy 2.4.1 lists the exact strict flag set; `disallow-any-explicit` is separate. [S19] |
| C21 | `stubtest` can catch runtime/stub signature drift and works with extension modules, but cannot prove semantic annotation accuracy. | **verified** | mypy's `stubtest` documentation states both capabilities and limits. [S22] |
| C22 | A small, opaque, manually reviewed public surface can avoid leaking wgpu/winit/PyO3 implementation types. | **plausible** | Use a typed Python facade over a private `_native` extension, explicit `__all__`, protocols/literals/type variables, and no public `Any`. Must be validated against the eventual OQ-05 API. |

Recommended typing layout:

```text
pygpui/
  __init__.py          # small typed facade / re-exports
  __init__.pyi         # public contract (or inline annotations if preferred)
  _native.*            # private PyO3 extension
  _native.pyi          # private boundary contract
  py.typed             # PEP 561 marker
```

Recommended gates:

1. Run `mypy --strict --disallow-any-explicit --python-version 3.11` over the public facade and typing fixtures. Keep `--no-implicit-reexport` (included by strict) and explicit `__all__`.
2. Test a **clean installed wheel**, not the source checkout, so missing `py.typed`/`.pyi` files fail CI.
3. Run `python -m mypy.stubtest pygpui` with a tiny, reviewed allowlist; do not use broad `ignore_missing_imports` or package-wide `ignore_errors`.
4. Add negative consumer fixtures: wrong action type, invalid callback signature, missing required event field and accidental import of `_native` should fail type checking where intended.
5. If generated stubs are enabled, generate with the oldest supported ABI/target (`abi3-py311`) and review the diff. Do not publish `Any`, `Incomplete`, typeshed implementation helpers or unstable generated syntax without review. [S06]

### E. Optional async runtime integration

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C23 | PyO3 `experimental-async` supports `async fn` in `#[pyfunction]`/`#[pymethods]`, but awaitables are currently asyncio-specific. | **verified** | PyO3 0.30.1 async guide. [S09] |
| C24 | PyO3 async functions require `Send + 'static` futures/parameters and remain attached across `.await` unless a workaround detaches. | **verified** | The guide documents the constraint and current `AllowThreads` workaround. This is unsuitable as an unreviewed default UI-loop mechanism. [S09] |
| C25 | `pyo3-async-runtimes 0.30.0` is the current PyO3-org bridge candidate for Tokio/async-std and asyncio. | **verified** | Tagged release, registry metadata and PyO3 ecosystem guide. [S24] |
| C26 | It should not own the first slice's desktop UI loop. | **plausible** | Its documented model surrenders the main thread to Python and runs Rust runtimes in the background; native desktop UI main-thread requirements make co-driving a separate spike. [S24] |
| C27 | `loop.call_soon_threadsafe` can deliver discrete Rust-originated events to an already-running asyncio loop. | **verified** | Python 3.15.2 asyncio docs. It does not solve same-thread co-driving of blocking `App.run()` and `run_forever()`. [S28] |

Recommendation: no async runtime dependency in the first slice. Later, add an optional adapter for non-UI awaitables only. An `await app.run()` API, background asyncio loop thread, or native-loop/asyncio co-driver requires a dedicated macOS/Windows/Linux spike covering main-thread rules, cancellation, shutdown and wakeups. Never schedule Python per frame.

### F. Wheel build, repair and signing constraints

| ID | Claim | Label | Evidence and consequence |
|---|---|---|---|
| C28 | maturin 1.16.0 builds PyO3 wheels for Windows, Linux and macOS and detects `abi3`/`abi3t`. | **verified** | Maturin bindings/platform/distribution docs. [S10, S12] |
| C29 | Linux wheels intended for PyPI need manylinux/musllinux-compatible tags and native-library auditing; a plain `linux` tag is rejected unless separately validated. | **verified** | Maturin distribution docs. [S12] |
| C30 | maturin 1.15+ reimplemented macOS delocate and Windows delvewheel repair; 1.16.0 uses ad-hoc Mach-O signing after repair. | **verified** | Changelog and tagged `macos.rs`/`macos_sign.rs`. [S11, S13, S14] |
| C31 | maturin's Mach-O signing is ad-hoc (`codesign -s -` or `arwen-codesign`), not Developer ID signing or notarization. | **verified** | Tagged source and arwen-codesign metadata. [S13, S14] |
| C32 | No production macOS notarization or Windows Authenticode support is established for maturin 1.16.0. | **unverified** | `BuildOptions` exposes no signing flags and the release workflow uses attestations, not OS signing. Treat as unsupported pending a separate tested pipeline. [S11, S15, S29, S30] |
| C33 | Apple notarization requires valid Developer ID signing, hardened runtime and a secure timestamp for the documented deliverable types. | **verified** | Apple developer documentation. Whether a pygpui wheel itself is a notarization deliverable is not established; an `.app`/`.pkg` release would be a separate task. [S29] |
| C34 | Windows Authenticode signing is a separate operation on PE artifacts such as `.pyd`/DLL files, with certificate and RFC 3161 timestamp. | **verified** | Microsoft SignTool docs, updated 2026-11-20. Sign after repair and before repacking if policy requires it; verify on clean Windows. [S30] |
| C35 | PyPI Trusted Publishing and PEP 740 attestations provide package provenance, not macOS/Windows executable trust. | **verified** | PyPI docs, PEP 740 and maturin trusted-publishing support. [S12, S31, S32] |
| C36 | License expressions/files should be packaged using PEP 639/Core Metadata 2.4; dependency notices remain a release gate. | **verified** | PEP 639; maturin 1.16.0 release notes include a `License-File` sdist-root fix. [S11, S33] |

Provisional wheel matrix (subject to OQ-03 and RQ-02A dependency floors):

| Platform | Initial artifact | Build/repair constraint | Required validation | Signing stance |
|---|---|---|---|---|
| macOS | `cp311-abi3-macosx_11_0_universal2` **candidate tag** | Build on macOS; explicitly set deployment target after dependency audit; universal2 external dylibs must contain both arches | Import on CPython 3.11–3.15 GIL; real window/input/close on Intel and Apple Silicon; inspect bundled dylibs | Internal ad-hoc re-sign only. Developer ID/notarization **not claimed** |
| Windows | `cp311-abi3-win_amd64` | MSVC x64; repair DLL dependencies; avoid mixing CRTs | Import on CPython 3.11–3.15 GIL; real window/input/IME/close on approved minimum Windows | Authenticode **not provided by maturin evidence**; separate SignTool pipeline if required |
| Linux | `cp311-abi3-manylinux_2_28_x86_64` | manylinux_2_28 container; auditwheel/maturin repair; no unsupported host-glibc tag | Import on CPython 3.11–3.15 GIL; headless CI plus real Wayland/X11 window/input smoke | PyPI attestations; distro/package signing out of scope |

Deferred unless demand is approved: Windows ARM64, Linux aarch64, musllinux, 32-bit, PyPy/GraalPy, CPython 3.14t, 3.15t/`abi3t`, and separate installer/app bundles. Cibuildwheel 4.3.5 lists Windows ARM64 as experimental and no longer lists 3.13t; this supports deferral rather than a broader launch matrix. [S26, S27]

## Contradictions and stale-source resolutions

| Contradiction / stale source | Resolution |
|---|---|
| PyO3 0.30.1's free-threading chapter still says there is no limited API for free-threaded builds, while the same version's features/building docs describe `abi3t`. | The “no limited API” text is stale for Python 3.15+. PEP 803 and versioned features docs establish `abi3t` only for 3.15+; 3.14t still needs version-specific wheels. [S02–S06, S18] |
| Maturin's living bindings page examples still use PyO3 0.29.0; platform support text says CPython 3.8–3.14, while current PyO3 0.30.1 drops 3.8 and supports 3.15. | Use exact release/tag metadata and cibuildwheel 4.3.5's current identifier table; treat the overview as lagging. [S01, S08, S10, S27] |
| PyO3's older typing page says manual `.pyi` files are currently best; the newer type-stub page provides a generator. | Both are true: manual stubs remain the conservative public contract; generation exists but is explicitly active development. [S06, S07] |
| Maturin shows both `abi3` and `abi3t` features in one Cargo declaration, which can be misread as one build producing both wheel families. | The same page explicitly says one maturin build selects at most one stable ABI family. Use separate builds when both are needed. [S10] |
| PyO3's generic `abi3` description says a host interpreter is required, while its distribution chapter allows version-specific `abi3-pyXY` cross-builds/no interpreter. | Scope the requirement to generic host-targeted `abi3`; `abi3-pyXY` carries an explicit minimum and is the cross-build path. [S02, S03] |
| `arwen-codesign` existence can be mistaken for full macOS signing support. | It is alpha ad-hoc Mach-O signing used during repair. It supplies neither Developer ID identity nor notarization. [S13, S14] |
| Cibuildwheel historical pages mention experimental 3.13t builds. | Current 4.3.5 docs/changelog removed 3.13t; current PyO3 also dropped it. No 3.13t claim. [S05, S27] |

## Rejected alternatives

- **Python callbacks per frame or arbitrary Python render functions:** directly violates the mission's no-Python-per-frame constraint and makes frame latency depend on Python scheduling. **Rejected.**
- **Version-specific wheels for every CPython minor as the initial default:** multiplies OS × Python artifacts without a demonstrated need. Keep as a fallback only if an API/perf requirement defeats `abi3`. **Rejected for first slice.**
- **Claiming 3.13t support:** contradicted by current PyO3. **Rejected.**
- **Making 3.14t or `abi3t` a launch gate:** adds separate ABI/thread-safety evidence with no stated user requirement; OQ-04 says it is not required for the initial vertical slice. **Deferred.**
- **Publishing unreviewed generated stubs:** generator completeness and target-version limitations can leak `Any`/`Incomplete` or invalid syntax. **Rejected as source of truth.**
- **`pyo3-asyncio 0.20.0`:** last published 2023-11-11 and not aligned with PyO3 0.30.1. **Rejected.**
- **Tokio/asyncio owning the desktop UI loop in the first slice:** main-thread and cancellation behavior is not established across platforms. **Deferred pending spike.**
- **Claiming maturin provides production code signing/notarization:** evidence establishes attestations and limited ad-hoc Mach-O repair signing only. **Rejected.**

## Conservative recommendation for Architect/Planner

Adopt a narrow, testable baseline:

- `pyo3 = 0.30.1` exactly, with `abi3-py311`; enable `experimental-inspect` only for reviewed stub-diff tooling.
- `maturin = 1.16.0` exactly for build/release tooling.
- `requires-python = ">=3.11"`; GIL-enabled CPython only for launch.
- Explicit `gil_used = true` until a free-threaded safety audit and tests pass.
- Rust-owned synchronous native `App.run()`; no Python frame callbacks; optional discrete semantic callbacks only.
- Typed public package with `py.typed`, hand-reviewed public `.pyi`, private `_native` extension, `mypy --strict` plus `disallow_any_explicit`, installed-wheel consumer tests and `stubtest`.
- No default async runtime. Revisit `pyo3-async-runtimes 0.30.0` only for a demonstrated awaitable non-UI use case.
- Provisional OS/arch matrix: macOS universal2, Windows x64, Linux x86_64 manylinux_2_28. Final OS-version floors wait for OQ-03 and the core dependency audit.
- PyPI Trusted Publishing + PEP 740 attestations. Do not claim Developer ID/notarization/Authenticode support; create separate release tasks only if the distribution policy requires them.

## Validation tasks required before ADR acceptance / release

1. Build a minimal PyO3 0.30.1 `abi3-py311` extension with maturin 1.16.0 on all three OS families; inspect wheel tags and import the **same wheel** on CPython 3.11, 3.12, 3.13, 3.14 and 3.15 GIL builds.
2. Test `gil_used = true` behavior and detach/attach callback handling; separately audit `unsafe`, `Send`/`Sync`, `pyclass` borrows and shutdown before considering `gil_used = false`.
3. Create a real window on each approved OS/arch; verify close, input, IME, accessibility and HiDPI behavior. Headless import tests are insufficient.
4. Add an instrumentation test proving zero Python attachments/callbacks during steady-state frames; then run RQ-03 performance benchmarks.
5. Verify wheel contents include `py.typed`, public `.pyi`, private native stubs and license files; run strict consumer mypy tests and `stubtest` from a clean install.
6. If stub generation is enabled, compare generated output against manual stubs on the oldest target and reject `Any`/`Incomplete`/unreviewed helper imports.
7. Decide OQ-03 OS/version/architecture floors and whether delivery is PyPI-only or includes `.app`/`.pkg`/installer artifacts. Only then define signing/notarization requirements and credentials.
8. If async UI integration is requested, run a dedicated co-driving spike covering main-thread rules, loop wakeup, cancellation and shutdown on all three platforms.

## Source register

All URLs accessed 2026-11-24. Documentation licenses are noted where meaningful; “N/A” means vendor documentation rather than a redistributed software component.

| ID | Primary source | Exact version/tag/commit | Publication/release date | License | Supports |
|---|---|---|---|---|---|
| S01 | https://crates.io/api/v1/crates/pyo3/0.30.1 ; https://raw.githubusercontent.com/PyO3/pyo3/v0.30.1/Cargo.toml | PyO3 0.30.1; `f168538672f2c32e32f7c1b702a502ee92de1edf` | 2026-10-14 | MIT OR Apache-2.0 | C01; features; MSRV; license |
| S02 | https://pyo3.rs/v0.30.1/features.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | `abi3`, `abi3t`, `experimental-async`, `experimental-inspect`, reference-pool flag |
| S03 | https://pyo3.rs/v0.30.1/building-and-distribution.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | Stable ABI build steps; platform tags; missing features |
| S04 | https://pyo3.rs/v0.30.1/free-threading.html ; https://pyo3.rs/v0.30.1/parallelism.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | GIL default, attach/detach, deadlocks, thread safety |
| S05 | https://pyo3.rs/v0.30.1/changelog.html | PyO3 0.30.1 | 0.29.0 entry 2026-06-11; 0.30.1 entry 2026-10-14 | MIT OR Apache-2.0 | Dropped 3.13t; Python 3.8 drop; 3.15 support |
| S06 | https://pyo3.rs/v0.30.1/type-stub.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | Generator commands and limitations |
| S07 | https://pyo3.rs/v0.30.1/python-typing-hints.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | Manual stubs, `py.typed`, maturin packaging |
| S08 | https://crates.io/api/v1/crates/maturin/1.16.0 ; https://github.com/PyO3/maturin/releases/tag/v1.16.0 | maturin 1.16.0; peeled commit `3bec0a32ae2b67ad4fac0194f762f44141e51473` | 2026-10-29 | MIT OR Apache-2.0 | C01; release changes; MSRV; license |
| S09 | https://pyo3.rs/v0.30.1/async-await.html | PyO3 0.30.1 | Living versioned docs; release 2026-10-14 | MIT OR Apache-2.0 | Async constraints and asyncio-only behavior |
| S10 | https://www.maturin.rs/bindings.html ; https://www.maturin.rs/platform_support.html | Living docs cross-checked against maturin 1.16.0 | Accessed 2026-11-24 | MIT OR Apache-2.0 | ABI-family selection; platform support; stale overview evidence |
| S11 | https://raw.githubusercontent.com/PyO3/maturin/v1.16.0/Cargo.toml ; https://raw.githubusercontent.com/PyO3/maturin/v1.16.0/src/build_options.rs | maturin 1.16.0; `3bec0a32...` | 2026-10-29 | MIT OR Apache-2.0 | Dependencies, features, no public signing option, `generate-stubs` |
| S12 | https://www.maturin.rs/distribution.html ; https://www.maturin.rs/config.html | Living docs cross-checked against maturin 1.16.0 | Accessed 2026-11-24 | MIT OR Apache-2.0 | manylinux, repair, generate-ci, trusted publishing, attestations |
| S13 | https://raw.githubusercontent.com/PyO3/maturin/v1.16.0/src/auditwheel/macos_sign.rs ; https://raw.githubusercontent.com/PyO3/maturin/v1.16.0/src/auditwheel/macos.rs | maturin 1.16.0; `3bec0a32...` | 2026-10-29 | MIT OR Apache-2.0 | Ad-hoc codesign scope; universal2 repair checks |
| S14 | https://crates.io/api/v1/crates/arwen-codesign/0.0.1-alpha.1 | arwen-codesign 0.0.1-alpha.1 | 2026-03-05 | MIT | Ad-hoc signing dependency and maturity |
| S15 | https://raw.githubusercontent.com/PyO3/maturin/v1.16.0/.github/workflows/release.yml | maturin 1.16.0; `3bec0a32...` | 2026-10-29 | MIT OR Apache-2.0 | Release workflow uses attestations; no OS signing steps |
| S16 | https://www.python.org/downloads/release/python-3140/ | CPython 3.14.0 | 2025-10-07 | PSF-2.0 | Official free-threaded support (PEP 779) |
| S17 | https://peps.python.org/pep-0703/ | PEP 703; resolution 2023-10-24 | Created 2023-01-09 | Public domain / CC0 | Free-threaded ABI and thread-state model |
| S18 | https://peps.python.org/pep-0803/ ; https://www.python.org/downloads/release/python-3150/ | PEP 803; CPython 3.15.0 | PEP created 2025-08-19, resolved 2026-03-30; Python 2026-10-09 | Public domain / CC0; PSF-2.0 | `abi3t` starts at 3.15 |
| S19 | https://pypi.org/pypi/mypy/json ; https://mypy.readthedocs.io/en/stable/command_line.html | mypy 2.4.1 | 2026-10-28 | MIT | Exact strict flags; release metadata |
| S20 | https://typing.python.org/en/latest/spec/distributing.html | Living typing specification | Accessed 2026-11-24 | PSF-2.0 | Current replacement for historical PEP 561 packaging rules |
| S21 | https://mypy.readthedocs.io/en/stable/installed_packages.html ; https://mypy.readthedocs.io/en/stable/stubs.html | mypy 2.4.1 docs | Accessed 2026-11-24 | MIT | In-package stubs, `py.typed`, installed-package checking |
| S22 | https://mypy.readthedocs.io/en/stable/stubtest.html | mypy 2.4.1 docs | Accessed 2026-11-24 | MIT | Runtime/stub consistency and limitations |
| S23 | https://peps.python.org/pep-0561/ | PEP 561; historical | Created 2017-09-09; last modified 2025-02-01 | Public domain | Historical origin; superseded by S20 |
| S24 | https://crates.io/api/v1/crates/pyo3-async-runtimes/0.30.0 ; https://github.com/PyO3/pyo3-async-runtimes/releases/tag/v0.30.0 ; https://raw.githubusercontent.com/PyO3/pyo3-async-runtimes/v0.30.0/Cargo.toml ; https://github.com/PyO3/pyo3-async-runtimes#readme | 0.30.0; `ae43efd860cf0f7a9697b99449fa747536e1415d` | 2026-10-15 | Apache-2.0 | Async bridge candidate, runtime features and main-thread model |
| S25 | https://crates.io/api/v1/crates/tokio/1.54.1 ; https://github.com/tokio-rs/tokio/releases/tag/tokio-1.54.1 | Tokio 1.54.1; `b53b2001ed2ccfd9b87e32a0c6da1a1eebdc80b8` | 2026-10-21 | MIT | Optional runtime version only |
| S26 | https://pypi.org/pypi/cibuildwheel/json | cibuildwheel 4.3.5 | 2026-10-27 | BSD-2-Clause | CI alternative version/license |
| S27 | https://cibuildwheel.pypa.io/en/stable/options/ ; https://cibuildwheel.pypa.io/en/stable/faq/ | cibuildwheel 4.3.5 docs | Accessed 2026-11-24 | BSD-2-Clause | Build identifiers, no 3.13t, ARM64 experimental, manylinux defaults, abi3audit |
| S28 | https://docs.python.org/3.15.2/library/asyncio-eventloop.html | CPython 3.15.2 docs | Python 3.15.2 released 2026-10-25 | PSF-2.0 | `call_soon_threadsafe` semantics |
| S29 | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution ; https://developer.apple.com/documentation/security/resolving-common-notarization-issues | Living Apple docs | Accessed 2026-11-24 | N/A | Developer ID, hardened runtime, timestamp, notarization scope |
| S30 | https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool ; https://learn.microsoft.com/en-us/windows/win32/seccrypto/using-signtool-to-sign-a-file | Updated docs; Windows 11 24H2 SDK build 10.0.26100.0 referenced for current metadata workflow | Updated 2026-11-20 | N/A | Authenticode, SHA-256, RFC 3161, verification |
| S31 | https://peps.python.org/pep-0740/ | PEP 740; resolution 2024-07-17 | Created 2024-01-08 | Public domain / CC0 | Index attestations; wheel-signature limitations |
| S32 | https://docs.pypi.org/attestations ; https://blog.pypi.org/posts/2024-11-14-pypi-now-supports-digital-attestations | PyPI attestation docs/blog | Blog 2024-11-14; living docs accessed 2026-11-24 | N/A | Provenance vs OS signing |
| S33 | https://peps.python.org/pep-0639/ | PEP 639 / Core Metadata 2.4 | Created 2019-08-15; living spec accessed 2026-11-24 | Public domain / CC0 | SPDX license expression and license files |
| S34 | https://peps.python.org/pep-0619/ | PEP 619 | 3.10 EOL 2026-10-01; page modified 2026-10-01 | Public domain | Python floor rationale |
| S35 | https://crates.io/api/v1/crates/pyo3-asyncio/0.20.0 | pyo3-asyncio 0.20.0 | 2023-11-11 | Apache-2.0 | Rejected stale async alternative |
| S36 | Local reproducible commands: `python3 --version`, `rustc --version`, `cargo --version` | Python 3.14.10; rustc/cargo 1.100.0 | Observed 2026-11-24 | N/A | Local environment only; not a support matrix |
| S37 | https://peps.python.org/pep-0384/ ; https://docs.python.org/3/c-api/stable.html | PEP 384; current CPython stable-ABI docs (3.15.2 at access) | PEP created 2009-05-17; CPython docs release 2026-10-25 | Public domain; PSF-2.0 | Stable ABI promise, Limited API and testing caveats |
