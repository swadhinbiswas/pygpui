# Phase 1 plan — minimum build-ready Counter slice

- Planner task: `P0-PL01`, attempt 1
- Prepared: 2026-11-24
- Accepted ADR baseline: `5ce026d`
- Execution state: **planning complete; every Phase 1 task is `blocked` behind `P0-AP01`**
- Authoritative graph: `.harness/TASKS.json`
- Delivery model: short-lived branch/worktree → push → PR against `main` → independent review/tests → Integrator-only merge. `origin` is `https://github.com/swadhinbiswas/pygpui.git`, `main` tracks `origin/main`, and `gh` is authenticated. No force-push or direct push to `main` is allowed.

## 1. Goal

Ship the ADR 0002 Counter window first: Python creates an entity/view; Rust presents shaped text and a button; click or keyboard activation updates Python state exactly once; one complete Rust-owned snapshot crosses the boundary; Rust rebuilds and presents the response; close is clean; no Python runs on the frame path. Preserve every ADR gate, but defer broader framework work and keep later certification work as evidence-gated bundles.

## 2. Scope and non-goals

### In scope

- Exact crate graph, pins, toolchain and production lockfile.
- Frozen shared contracts before parallel implementation: snapshot/command/event/error types, handle semantics, public Python/stub boundary and benchmark interface.
- Counter only, using `App`, `Entity[T]`, `WeakEntity[T]`, `View[T]`, opaque handles, `Action`, typed errors and `Text`/`Button`/`Row`/`Column`.
- One main-thread winit loop, one wgpu renderer, complete snapshot replacement and full-window rebuild.
- Independent tests, unsafe/GIL/lifetime review, callback sentinels, headless and native smoke tests.
- Benchmark, platform, IME, accessibility, wheel, typing, license/SBOM and release-evidence gates required by the accepted ADRs.

### Non-goals

- A broad widget framework, CSS compatibility, multiwindow, async integration, rich-text public authoring, app bundles or stores.
- Incremental patches, subtree caches, damage tracking or a persistent Python VDOM before the ADR 0002 scaling decision and a superseding ADR.
- Public free-threaded Python, `abi3t`, macOS Intel/universal2, Linux ARM64, GLES/OpenGL fallback, HDR, transparency or exclusive fullscreen.
- An MSRV promise, final performance certification, WCAG claim, complete-IME claim, virtualized-list accessibility claim, permissive-only Wayland distribution claim, public signing, notarization or publishing.
- Editing accepted ADRs, research or review files.

## 3. Claim and evidence rules

- Accepted ADRs establish design obligations, not achieved performance or support.
- `evidence_links` on blocked tasks are required output locations, not claims of completion.
- A task is `done` only when its commands exit zero, required physical evidence is archived, assigned independent review/testing passes and the Integrator records the reviewed PR merge/diff.
- Headless hashes and submit counters prove capacity only, never presentation.
- Input latency ends at the first **presented** frame containing the response token. Input-to-photon is separate.
- Performance stays `not_measured`, `not_certified`, `fail` or `inconclusive` until OQ-02 and AR08 gates pass. Provisional targets are literal: at least 120.0 presented fps on a qualified 120 Hz path, p95 below 8.000000 ms, and below 1% of one CPU core over a 60-second idle with zero application submissions/presentations.
- Any nonzero Python callback/frame-entry/attachment/finalizer counter in a measured window is an absolute failure.
- Missing platform, IME, AT, license or signing evidence removes the claim; upstream docs and cross-compilation are not substitutes.

### Required Git/PR workflow

1. Start every build task from current green `main` in a short-lived `feat/<task-id>-<slug>` or `fix/<task-id>-<slug>` branch/worktree.
2. Read `STATE.md` and the assigned handoff, quote the exact next step in the first `LOG.md` action, and keep edits inside the assigned write scope.
3. Run the task's build, lint and test commands; commit with a Conventional Commit message; push the branch; open a PR against `main` with `gh pr create`.
4. Link the task ID, ADR gates, exact test/benchmark output and rollback in the PR. A different Reviewer and Test-Engineer verify the change.
5. Never push directly to `main`, force-push, rewrite published history or merge your own unreviewed work. Only the Integrator merges reviewed, green PRs in dependency order and reruns the full matrix/benchmarks.

## 4. First dispatch waves

These waves are the operational contract for the Orchestrator after Red-Team approval. A wave starts only when every listed predecessor is `done`.

| Wave | Dispatch | Write scopes | Join condition |
|---|---|---|---|
| 0 | `P1-GOV01` alone | `.harness/PHASE1-EVIDENCE.md`, dispatch/attempt register | `P0-AP01` is `done`; remote/auth and branch/worktree/PR rules recorded |
| 1 | `P1-ARCH01` and `P1-LIC01` in parallel | Integrator: root manifests/lockfile/toolchain only. License reviewer: `LICENSE`, notices/provenance ledger only | Exact workspace resolves; provenance baseline exists |
| 2 | `P1-PROTO01` and `P1-CI01` in parallel | Protocol crate only. CI/release scripts only | Protocol contract tests and local CI/red-main drill pass |
| 3 | `P1-API01` and `P1-BENCH00` in parallel | Python facade/stubs/examples only. Benchmark package/contracts only | Strict API contract and benchmark interface validate |
| 4 | `P1-CONREV01` alone | Review report and contract-freeze hash record only | Zero blocking findings; shared interfaces frozen |
| 5 | `P1-CORE01`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01` in parallel; then `P1-CORE02`, `P1-PLATFORM01`, `P1-PY01` as their deps complete | Disjoint crate/subdirectory scopes in §7 | Each module's tests pass without editing another owner's files |
| 6 | `P1-SLICE01` alone | `feat/P1-SLICE01-counter` worktree and Counter example/test wiring only | Counter works headlessly and in local native smoke; PR opened against `main` |
| 7 | `P1-TST01` and `P1-PLAT01` in parallel; then `P1-REV01`; then `P1-INT01` | Tests/platform evidence only; Reviewer writes review only; Integrator merges the reviewed PR | Independent tests and safety review pass; reviewed Counter PR is green and revertible |

No two agents edit the same manifest, protocol schema, public API/stub, lockfile or integration branch. Post-freeze interface changes return to `P1-CONREV01`; they are not patched into consumer branches.

## 5. Dependency-ordered task graph

All tasks start at attempt 0 and status `blocked`. Ranges are ideal engineer-days including tests/review, excluding hardware, counsel and user wait time.

| ID | Deliverable | Owner | Dependencies | Size / range |
|---|---|---|---|---|
| `P1-GOV01` | Authorization, environment/claim register, branch/worktree/PR and four-attempt protocol | Orchestrator | `P0-AP01` | S / 1–2 |
| `P1-ARCH01` | Exact crate graph, pins, toolchain and production lock | Integrator | `P1-GOV01` | M / 3–5 |
| `P1-LIC01` | Clean-room provenance and Apache-2.0 repository baseline | License-Compliance-Reviewer | `P1-GOV01` | M / 3–5 |
| `P1-PROTO01` | Snapshot/command/event/error and identity contracts | Protocol-Engineer | `P1-ARCH01` | M / 3–5 |
| `P1-CI01` | Local-first CI and red-main recovery drill | Release-CI-Engineer | `P1-ARCH01` | M / 3–5 |
| `P1-API01` | Public Python API, handle semantics and strict stubs | Python-API-Engineer | `P1-PROTO01` | M / 3–5 |
| `P1-BENCH00` | Benchmark CLI, scene, counter and artifact interface | Perf-Engineer | `P1-PROTO01` | S–M / 2–3 |
| `P1-CONREV01` | Independent contract review and freeze | Independent-Reviewer | `P1-API01`, `P1-BENCH00`, `P1-PROTO01`, `P1-LIC01`, `P1-CI01` | S / 1–2 |
| `P1-CORE01` | Bounded command queue and demand/idle scheduler | Rust-Core-Engineer | `P1-CONREV01` | M / 3–5 |
| `P1-CORE02` | Generation-safe handles, slot cap and teardown | Rust-Core-Engineer | `P1-CORE01` | M / 3–5 |
| `P1-SCENE01` | Snapshot reconciliation, full rebuild and constrained Taffy | Rust-Scene-Engineer | `P1-CONREV01` | L / 6–8 |
| `P1-TEXT01` | cosmic-text shaping/atlas and fallback | Rust-Text-Engineer | `P1-CONREV01` | M / 3–5 |
| `P1-INPUT01` | Pointer/key/focus plus IME state machine and properties | Rust-Input-Engineer | `P1-CONREV01` | M / 3–5 |
| `P1-RENDER01` | wgpu renderer, text draws and surface state machine | Rust-Render-Engineer | `P1-CONREV01` | L / 6–8 |
| `P1-PLATFORM01` | winit main-thread loop and event orchestration | Rust-Platform-Engineer | `P1-CONREV01`, `P1-RENDER01` | L / 6–8 |
| `P1-PY01` | PyO3 event actor and facade implementation | Python-Binding-Engineer | `P1-CONREV01`, `P1-CORE02` | L / 6–8 |
| `P1-SLICE01` | Integrate Counter end to end on a feature worktree and PR | Integrator | `P1-CORE01`, `P1-CORE02`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01`, `P1-PLATFORM01`, `P1-PY01` | M / 3–5 |
| `P1-TST01` | Independent Counter E2E, typing, reentrancy and property suite | Test-Engineer | `P1-SLICE01` | M / 3–5 |
| `P1-PLAT01` | Linux headless/native common-runtime smoke | Platform-Test-Engineer | `P1-SLICE01` | M / 3–5 |
| `P1-REV01` | Independent correctness and unsafe/GIL/lifetime review | Independent-Reviewer | `P1-SLICE01`, `P1-TST01` | M / 3–5 |
| `P1-INT01` | Integrator-only merge of reviewed Counter PR and rollback rehearsal | Integrator | `P1-REV01`, `P1-CI01`, `P1-LIC01` | S / 1–2 |
| `P1-PERF01` | Native callback counters, sentinels and frame isolation | Perf-Engineer | `P1-SLICE01`, `P1-REV01` | M / 3–5 |
| `P1-A11Y01` | Rust semantic mirror and AccessKit adapter consumer tests | Rust-Accessibility-Engineer | `P1-INT01`, `P1-INPUT01` | L / 6–8 |
| `P1-REL01` | Native candidate wheels/sdist build, repair and audit | Release-CI-Engineer | `P1-INT01`, `P1-LIC01`, `P1-CI01` | L / 6–8 |
| `P1-PLAT02` | Candidate platform certification bundle T/L/W/M and support manifest | Platform-Test-Engineer | `P1-REL01`, `P1-PLAT01`, `P1-A11Y01` | L / 6–8 plus hardware |
| `P1-BENCH01` | Deterministic scenes, qualification and immutable baseline | Perf-Engineer | `P1-INT01`, `P1-BENCH00`, `P1-PLAT01`, `P1-PERF01` | L / 6–8 |
| `P1-PERF02` | Presented/input qualification, ABBA regression and scaling report | Perf-Engineer | `P1-BENCH01`, `P1-PLAT02` | L / 6–8 plus collector wait |
| `P1-IME01` | Physical IME matrix and platform defect exercises | Platform-Test-Engineer | `P1-PLAT02` | M / 3–5 plus hardware |
| `P1-A11Y02` | Physical AT workflows and accessible 10,000-row representation | Accessibility-Test-Engineer | `P1-A11Y01`, `P1-PLAT02`, `P1-BENCH01`, `P1-PERF02` | M / 3–5 plus hardware |
| `P1-LIC02` | Artifact dependency/license/SBOM/NOTICE and Wayland disposition | License-Compliance-Reviewer | `P1-REL01`, `P1-LIC01` | M / 3–5 plus external review |
| `P1-DOC01` | Counter docs, benchmark/release evidence and claim register | Technical-Writer | `P1-API01`, `P1-INT01` | S–M / 2–3 |
| `P1-REL02` | Same-wheel clean installs, reproducibility and release bundle | Release-CI-Engineer | `P1-REL01`, `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y02`, `P1-LIC02`, `P1-DOC01` | L / 6–8 |

Later rows are deliberately gate bundles, not authorization for broader features. If a bundle cannot be completed, its exact claim remains blocked; it does not expand Phase 1 scope.

## 6. Critical path

**Counter:** `P0-AP01` → `P1-GOV01` → `P1-ARCH01` → `P1-PROTO01` → `P1-API01` → `P1-CONREV01` → `P1-CORE01` → `P1-CORE02` → `P1-PY01` → `P1-SLICE01` → `P1-TST01` → `P1-REV01` → `P1-INT01`.

Scene, text, input, render and platform are parallel branches after the freeze; all join at `P1-SLICE01`.

**Evidence-gated completion:** Counter merge → wheels (`P1-REL01`) → platform bundle (`P1-PLAT02`) → benchmark/input decision (`P1-PERF02`) and IME/AT (`P1-IME01`, `P1-A11Y02`) → artifact license closure (`P1-LIC02`) → release bundle (`P1-REL02`).

The likely longest wait is physical hardware/collectors and native runners. Public signing/publishing stays blocked and is not a Phase 1 completion condition.

## 7. Interface ownership and parallel boundaries

| Path/interface | Owner | Boundary |
|---|---|---|
| Root manifests, workspace, toolchain, `Cargo.lock` | Integrator | No parallel edits; post-freeze changes rerun architecture/lock gates |
| `crates/pygpui-protocol/**` | Protocol-Engineer | Sole schema owner; consumers do not edit |
| `pygpui/**`, public stubs, `py.typed`, public examples | Python-API-Engineer; Binding-Engineer only for private `_native` | Public changes require contract re-review |
| `crates/pygpui-core/**` | Rust-Core-Engineer | Queue/handles/scheduler; core tasks are serial |
| `crates/pygpui-scene/src/layout/**` and reconciliation | Rust-Scene-Engineer | No Python/native platform types in protocol |
| `crates/pygpui-scene/src/text/**` | Rust-Text-Engineer | Frozen text trait; disjoint from layout |
| `crates/pygpui-scene/src/input/**` | Rust-Input-Engineer | Rust-only input/IME/focus |
| `crates/pygpui-scene/src/a11y/**` | Rust-Accessibility-Engineer | Hooks in slice 1; adapter after Counter merge |
| `crates/pygpui-render/**` | Rust-Render-Engineer | No PyO3/winit imports |
| `crates/pygpui-platform/**` | Rust-Platform-Engineer | Sole winit owner; no PyO3 imports |
| `crates/pygpui-python/**` | Python-Binding-Engineer | Sole PyO3 owner; never imported by another crate |
| `tests/**` and gate drivers | Test/Platform-Test Engineers | Tests do not mutate production APIs |
| `benches/**`, `pygpui_bench/**`, `BENCH/**` | Perf-Engineer | Baselines immutable; protocol changes get a new ID |
| CI/packaging scripts | Release-CI-Engineer | No lockfile edits |
| License/notices/provenance/SBOM | License-Compliance-Reviewer | Per-artifact audit after repair/repack |
| `docs/**` | Technical-Writer | Claims link to evidence or are marked unverified/blocked |

## 8. Estimates and unknowns

- S = 1–2 ideal engineer-days; M = 3–5; L = 6–8. No task is XL.
- Estimates include tests, review churn and PR integration, but exclude user decisions, hardware queues, counsel and signing credentials.
- The Counter range is wide because the Python/Rust main-thread/GIL boundary and first real presentation are unproven. If `P1-SLICE01` fails twice, stop and escalate with a minimal reproduction rather than expanding the framework.
- Benchmark numbers are targets, not estimates or achieved facts.

## 9. Risks and controls

| Risk | Control | Tasks |
|---|---|---|
| Contract churn after parallel work | Freeze hashes; one owner per interface; re-review changes | `P1-CONREV01`, `P1-ARCH01` |
| GIL/unsafe/lifetime defect | Event actor only; detached frame closure; independent safety review and close/finalizer tests | `P1-PY01`, `P1-REV01`, `P1-TST01` |
| Hidden Python frame callback/finalizer | Native counters, sentinels and static call-graph audit | `P1-PERF01` |
| Taffy/slotmap/cosmic-text defects | Constrained layout, 65,536-slot cap, no detach/reattach, atlas/fallback tests | `P1-CORE02`, `P1-SCENE01`, `P1-TEXT01` |
| Surface/DPI/device-loss differences | Bounded state machine and physical T/L/W/M gates | `P1-RENDER01`, `P1-PLAT01`, `P1-PLAT02` |
| Metal first-frame/AccessKit ordering | Invisible → attach adapter → show → present; no pre-show claim | `P1-A11Y01`, `P1-PLAT02` |
| IME/AT platform gaps | State-machine properties plus physical IME and AT workflows | `P1-INPUT01`, `P1-IME01`, `P1-A11Y02` |
| Invalid benchmark endpoint/counts | Frozen protocol, ≤51 rows, five blocks/ten pairs, presented-response endpoint | `P1-BENCH00`, `P1-BENCH01`, `P1-PERF02` |
| No certified hardware/OQ-02 | Report not certified/inconclusive; keep targets provisional | `P1-GOV01`, `P1-PERF02` |
| Wayland/license/copyright uncertainty | Artifact audit; do not invent copyright notice; block affected distribution | `P1-LIC01`, `P1-LIC02` |
| Signing/publishing credentials absent | Keep public signing/publishing blocked; wheel/sdist evidence does not establish OS trust | `P1-REL02` |
| Red main | Pause, bisect locally, fix/revert, rerun full gate, record recovery | `P1-CI01`, `P1-INT01` |

## 10. Rollback and escalation

- **Contracts:** tag pre-freeze; revert the freeze as one unit through a reviewed PR. Post-freeze schema/API changes require a new reviewed contract commit.
- **Counter:** tag `phase1/counter-premerge`; the Integrator opens/merges a revert PR if correctness/lifecycle/frame-isolation gates fail. Keep schema/lockfile changes with the slice.
- **Benchmarks:** never overwrite baselines. Protocol/config changes create a new protocol/environment/baseline ID.
- **Platform/input/a11y:** revert the change independently and remove the affected claim; never adopt trunk dependencies as a shortcut.
- **Artifacts:** quarantine exact hashes; retain raw evidence; regenerate and re-audit repaired artifacts.

**Red main:** stop unrelated merges; reproduce on `main` synced with `origin/main`; `git bisect run` the smallest failing gate; fix forward on a `fix/` worktree or open a revert PR; the Integrator merges only after review; rerun fmt, clippy, workspace tests, typing and relevant installed-wheel/headless tests; record the restored green `origin/main` hash before resuming. Never force-push.

**Four-attempt rule:** every task has `max_attempts: 4`. Attempts 1–3 may address review feedback. At attempt 4, pass all gates or stop as `partial`/`blocked`/`failed` and escalate to the Orchestrator with evidence and a bounded decision request. No fifth attempt is authorized.

## 11. ADR gate traceability

| Gate | Phase 1 task IDs | Required exit |
|---|---|---|
| AR01-G1 | `P1-PLATFORM01`, `P1-PLAT02` | Main-thread lifecycle and installed-wheel close/no-worker tests exit zero |
| AR01-G2 | `P1-REV01` | Static dependency/call-graph audit exits zero; no Python frame path |
| AR01-G3 | `P1-PERF01` | Native counters zero; each sentinel exactly once |
| AR01-G4 | `P1-CORE01` | Bounded queue/backpressure and 60-second idle tests exit zero |
| AR02-G1 | `P1-PROTO01`, `P1-SCENE01`, `P1-TST01` | Atomic replacement/rollback/identity/reorder/teardown properties exit zero |
| AR02-G2 | `P1-SLICE01`, `P1-PLAT02` | Counter headless test and candidate presented-response smoke exit zero; click/key update once |
| AR02-G3 | `P1-SCENE01` | One rebuild per semantic change; zero no-change rebuilds |
| AR02-G4 | `P1-PERF01` | Submission-to-presentation counters/sentinels stay zero |
| AR02-G5 | `P1-PERF02` | `e1000`/`l10000` pass or profile names full rebuild blocker; no incremental work authorized |
| AR03-G1 | `P1-API01`, `P1-TST01` | Strict mypy, `stubtest` and negative fixtures pass |
| AR03-G2 | `P1-CORE02`, `P1-TST01` | Strong/weak/generation/wrong-kind/stale-handle tests exit zero |
| AR03-G3 | `P1-PY01`, `P1-TST01` | Reentrancy/build mutation/run reentry/release tests exit zero |
| AR03-G4 | `P1-REV01` | No Python references in snapshot/scene/cache; audit exits zero |
| AR03-G5 | `P1-ARCH01`, `P1-CONREV01` | `cargo metadata --locked` and crate-graph test exit zero |
| AR04-G1 | `P1-ARCH01` | Locked check and three-target metadata exit zero; no GLES/AccessKit leakage |
| AR04-G2 | `P1-SCENE01` | Taffy #804/#1354/#1357, supported subset and fallback tests exit zero |
| AR04-G3 | `P1-CORE02` | 65,536 cap, stale/reuse tests and no-detach source audit exit zero |
| AR04-G4 | `P1-TEXT01` | ASCII/CJK/RTL/emoji/fallback tests exit zero; #518 behavior reported |
| AR04-G5 | `P1-SCENE01` | Large rebuild test and rustc-hash pattern audit exit zero |
| AR04-G6 | `P1-REL02` | Release states only pinned Rust 1.100.0 unless an exact-compiler MSRV run passes |
| AR05-G1 | `P1-REL01` | Native candidate builds exit zero with artifact/target/feature/toolchain hashes |
| AR05-G2 | `P1-PLAT01`, `P1-PLAT02` | Installed-wheel T02–T12 exit zero |
| AR05-G3 | `P1-PLAT02` | Linux L01–L08 on Wayland and Xorg pass, including 30-minute soak |
| AR05-G4 | `P1-PLAT02` | Windows W01–W07 pass with recorded compiler strategy |
| AR05-G5 | `P1-PLAT02` | macOS M01–M08 pass with invisible/adapter/show/present sequence |
| AR05-G6 | `P1-PLAT02`, `P1-REL02` | Support manifest includes only platforms with all passing evidence |
| AR06-G1 | `P1-INPUT01` | IME/focus/UTF-8/version/close property tests exit zero |
| AR06-G2 | `P1-IME01` | Physical Japanese/Chinese/Korean/dead-key matrix passes with cited defects exercised |
| AR06-G3 | `P1-A11Y01` | AccessKit identity/diff/focus/action consumer tests exit zero |
| AR06-G4 | `P1-A11Y02` | VoiceOver/Narrator/Orca workflows pass; inspector-only evidence fails |
| AR06-G5 | `P1-A11Y01`, `P1-PERF01` | No Python from adapter threads; no frame/idle regression |
| AR06-G6 | `P1-A11Y02` | Tested 10,000-row accessible representation and #871 disposition exist before claim |
| AR07-G1 | `P1-REL01` | Three wheels plus sdist pass tag/suffix/`abi3audit`/repair/content checks |
| AR07-G2 | `P1-REL02` | Same wheel passes clean CPython 3.11–3.15 GIL matrix on candidate OSs |
| AR07-G3 | `P1-API01`, `P1-TST01` | mypy 2.4.1 strict/explicit-Any and `stubtest` exit zero |
| AR07-G4 | `P1-REL02`, `P1-PLAT02`, `P1-PERF01` | Same artifact passes platform and callback gates; editable run is insufficient |
| AR07-G5 | `P1-REL02` | Reproducibility and evidence archive exit zero; public signing/publishing remains blocked |
| AR08-G1 | `P1-BENCH00`, `P1-BENCH01` | Scene/harness/collector qualification exits zero, including ≤51 rows and raw hashes |
| AR08-G2 | `P1-BENCH01` | Ten valid fresh-process runs per scenario form immutable baseline |
| AR08-G3 | `P1-PERF01` | Static audit and zero counters pass; Python 3.11 fallback and separate interpreters exercised |
| AR08-G4 | `P1-PERF02` | Presented/input collector and clock checks pass or status is `inconclusive` |
| AR08-G5 | `P1-PERF02` | ABBA tests reject >10%, accept exactly 10.0%, and verify all ten pairs/bootstrap rules |
| AR08-G6 | `P1-PERF02` | `pass` only with OQ-02, correctness/counters, environment and raw artifacts |
| AR09-G1 | `P1-LIC01` | Complete provenance ledger; unapproved copied/translated expression blocks merge |
| AR09-G2 | `P1-LIC02` | Lockfile-fed scanner/SBOM exits zero with no unreviewed exception per artifact |
| AR09-G3 | `P1-LIC02` | Wheel/sdist license/copyright/NOTICE/font/asset audit exits zero and matches SBOM |
| AR09-G4 | `P1-LIC02` | Wayland clarification/counsel plus audit is archived, or publication stays blocked |
| AR09-G5 | `P1-LIC01` | Source-exception workflow rejects incomplete records and accepts all required fields |
| AR10-G1 | `P1-LIC01`, `P1-REL01`, `P1-LIC02` | Cargo/wheel metadata and official LICENSE/owner notice checks exit zero |
| AR10-G2 | `P1-LIC02` | Artifact contents and SBOM agree; no third-party file is relicensed |
| AR10-G3 | `P1-LIC01` | Authored-file audit and Apache-2.0 inbound contribution terms pass |
| AR10-G4 | `P1-LIC02`, `P1-DOC01`, `P1-REL02` | Artifact gates pass; no patent/trademark/clean-room/permissive-only Wayland claim |

## 12. Plan completion

This plan is complete when `TASKS.json` preserves completed Phase 0 history, contains this ordered graph with all required task fields, every gate above maps to a task, the final `LOG.md` action is appended and the Red-Team-Planner handoff contains every Part 3 field.
