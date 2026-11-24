# Phase 1 plan — execution-ready Counter slice

- Planner task: `P0-PL01`, attempt 2
- Prepared: 2026-11-24
- Accepted ADR baseline: `5ce026d`
- Red-Team blocker baseline: `c5ed5f3`
- Execution state: **planning revision; `P0-AP01` and every Phase 1 task remain `blocked` at attempt zero**
- Authoritative graph: `.harness/TASKS.json`
- Reproducible validator: `.harness/scripts/validate_phase1_graph.py`
- Delivery model: short-lived branch/worktree → push → PR → independent review/tests → Integrator-only merge. `origin` is `https://github.com/swadhinbiswas/pygpui.git`, `main` tracks `origin/main`, and `gh` is authenticated. No force-push or direct push to `main` is allowed.

## 1. Goal

Deliver the ADR 0002 Counter window first: Python creates an entity/view; Rust presents shaped text and a button; click or keyboard activation updates Python state exactly once; one complete Rust-owned snapshot crosses the boundary; Rust rebuilds and presents the response; close is clean; no Python runs on the frame path. Preserve all 52 ADR gates with executable, fail-closed evidence rather than expanding into a broad widget framework.

## 2. Scope and non-goals

### In scope

- Exact crate graph, pins, toolchain, production lockfile and root Python packaging.
- Frozen external and internal contracts before parallel implementation.
- Counter only, using `App`, `Entity[T]`, `WeakEntity[T]`, `View[T]`, opaque handles, `Action`, typed errors and `Text`/`Button`/`Row`/`Column`.
- One main-thread winit loop, one wgpu renderer, complete snapshot replacement and full-window rebuild.
- Owned gate tooling, negative tests, branch evidence, isolated rollback drills and per-PR provenance audits.
- Independent tests, unsafe/GIL/lifetime review, native instrumentation, callback sentinels, headless and physical platform smoke tests.
- Benchmark, platform, IME, accessibility, wheel, typing, license/SBOM, artifact-invalidation and release-evidence gates.

### Non-goals

- A broad widget framework, CSS compatibility, multiwindow, async integration, rich-text public authoring, app bundles or stores.
- Incremental patches, subtree caches, damage tracking or a persistent Python VDOM before the ADR 0002 scaling decision and a superseding ADR.
- Public free-threaded Python, `abi3t`, macOS Intel/universal2, Linux ARM64, GLES/OpenGL fallback, HDR, transparency or exclusive fullscreen.
- An MSRV promise, final performance certification, WCAG claim, complete-IME claim, virtualized-list accessibility claim, permissive-only Wayland distribution claim, public signing, notarization or publishing.
- Editing accepted ADRs, research, reviews, `STATE.md` or feature code in this planning task.

## 3. Blocker resolution map

| Finding | Revision |
|---|---|
| B-01 | Added `P1-TOOL-GRAPH01`, `P1-TOOL-BRANCH01`, `P1-TOOL-AUDIT01`, `P1-TOOL-PLATFORM01`, `P1-TOOL-DOC01`, `P1-TOOL-RELEASE01`, `P1-TOOL-BENCH01`; created the actual graph validator and 13 negative tests; every local command path is checked against a producer and write scope. |
| B-02 | Added `P1-RUSTCONTRACT01` for text, paint, hit/focus, platform and instrumentation hand-offs; `P1-CONREV01` freezes their hashes; module dependencies now encode real producers. |
| B-03 | Added `P1-PACK01` and `P1-LOCALWHEEL01`; installed-wheel tests depend on the hashed local wheel, not the later release wheel. |
| B-04 | Defined `implemented`, `independently_verified`, `merged` and `recorded`; every build branch requires distinct session-role evidence; only `P1-SLICE01` completes at `implemented`, then `P1-TST01`/`P1-REV01` verify and `P1-INT01` merges. |
| B-05 | Red-main and rollback drills run only against disposable fixture remotes; tags, revert → gate → revert-of-revert/restore and green hashes are owned by `P1-TOOL-BRANCH01`, `P1-TAG-CONTRACT01`, `P1-SLICE01` and `P1-INT01`. |
| B-06 | Added `P1-INSTRUMENT01` and `P1-BENCHCLI01`; production counter/sentinel hooks and `boundary`, `compare`, `input`, `report`, collector and interpreter subcommands have owners and negative tests. |
| B-07 | `P1-LIC01` now depends on manifests/packaging; `P1-A11Y-MANIFEST01` owns AccessKit manifest/lock edits; `P1-A11Y01` owns platform window-lifecycle wiring. |
| B-08 | Acceptance criteria name commands, inputs, outputs and exit semantics; proof gates exit nonzero on missing, disabled, stale or inconclusive evidence; tool self-tests exit zero only after verifying negative rejection. |
| B-09 | Added AT-on benchmarks, exact-wheel callback reruns, separate-interpreter diagnostics, real compare-gate integration, per-PR provenance/authored-scope audits and a separate AR10-G1 closure task. |
| B-10 | `P1-A11Y-AT01` depends on `P1-IME01`; accessible-list implementation is split into `P1-A11Y-LIST01` from physical AT certification. |
| B-11 | Added `P1-DOC-FINAL01` and `P1-ARTIFACT-GATE01`; immutable artifact hashes invalidate downstream evidence and force re-audit before final docs/release closure. |
| N-01 | Added explicit `P1-READY-PLATFORM01`, `P1-READY-BENCH01` and `P1-READY-RELEASE01` fail-closed readiness tasks. |
| N-02 | Feature branches own their LOG/handoff files; the Orchestrator serializes `STATE.md`/`TASKS.json`; the Integrator resolves control-plane conflicts before merge. |
| N-03 | A consumer branches only after its producer reaches the declared completion state; merged producers must be present on current `main`. |
| N-04 | AR09-G1 wording is explicit: unapproved copied/translated expression **prevents merge**. |

## 4. Dependency and branch-state semantics

A dependency is satisfied only when the producer reaches its declared `completion_state`:

- `implemented`: code and author-run tests exist on the branch. Branch artifacts may be consumed; the branch may not be merged.
- `independently_verified`: a different reviewer session and tester session accepted the same commit with command logs. Evidence may be consumed.
- `merged`: the Integrator accepted the branch evidence, merged the PR into green `main`, and recorded the merge SHA. Consumers branch from this merged `main`.
- `recorded`: a control/readiness task archived a structured result without claiming a code merge.

Every `build` task completes at `merged` and carries `review_evidence`, `test_evidence` and `merge_evidence`. `P1-SLICE01` is the sole `implementation` exception: it completes at `implemented`, produces the local wheel, then `P1-TST01` and `P1-REV01` independently verify it and `P1-INT01` performs the Integrator-only merge. Verification/proof tasks complete at `independently_verified`; readiness/control tasks complete at `recorded`.

### Single-identity review model

Only one GitHub identity is available. Role separation is therefore proved by distinct agent session IDs and harness records, not GitHub approval metadata:

1. Implementer records branch, commit, scope and author-run command logs.
2. Independent Reviewer session records findings and disposition on the same commit.
3. Independent Test-Engineer session reruns the named tests on the same commit/artifact.
4. Integrator session checks all records with `tools/ci/branch_gate.py`, merges only reviewed/green PRs and records the merge SHA.

`tools/ci/branch_gate.py` exits nonzero for missing roles, session reuse, commit mismatch, missing logs or missing merge evidence. GitHub branch protection is not assumed.

### Control plane

Feature branches append their own one-line LOG action and write their own handoff/evidence files. Only Orchestrator-owned control tasks edit `STATE.md` or `TASKS.json`. The Integrator resolves control-plane conflicts before merge and never accepts a feature branch that silently changes task state.

## 5. Dependency-ordered task graph

All tasks start at attempt 0 and status `blocked`. Ranges are ideal engineer-days including tests/review, excluding hardware, counsel and user wait time.

| ID | Deliverable | Owner | Dependencies | Size / range |
|---|---|---|---|---|
| `P1-GOV01` | Authorize Phase 1 and record execution readiness | Orchestrator | `P0-AP01` | S / 1–2 |
| `P1-TOOL-BRANCH01` | Own branch evidence, isolated red-main, tag and rollback tooling | Release-CI-Engineer | `P1-GOV01` | L / 6–8 |
| `P1-TOOL-GRAPH01` | Own and negatively test graph and contract-freeze validators | Release-CI-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | M / 3–5 |
| `P1-TOOL-AUDIT01` | Own fail-closed provenance, source, safety and per-PR audit tools | License-Compliance-Reviewer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-PLATFORM01` | Own readiness, platform, IME, AT and support-manifest gate tools | Platform-Test-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-DOC01` | Own documentation build and claim-evidence audit tooling | Technical-Writer | `P1-GOV01`, `P1-TOOL-BRANCH01` | S / 2–3 |
| `P1-TOOL-RELEASE01` | Own artifact audit, clean-install, reproducibility and invalidation tools | Release-CI-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-BENCH01` | Own benchmark readiness, collector and interpreter diagnostic tools | Perf-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | M / 3–5 |
| `P1-READY-PLATFORM01` | Record physical platform, IME and AT runner readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-PLATFORM01` | S / 1–2 |
| `P1-READY-BENCH01` | Record benchmark hardware, collector and OQ-02 readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-BENCH01` | S / 1–2 |
| `P1-READY-RELEASE01` | Record CPython, copyright, Wayland and release-channel readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-RELEASE01` | S / 1–2 |
| `P1-ARCH01` | Create exact workspace, crate graph, pins and production lock | Integrator | `P1-GOV01`, `P1-TOOL-GRAPH01`, `P1-TOOL-BRANCH01`, `P1-TOOL-AUDIT01` | M / 3–5 |
| `P1-PACK01` | Create root Python packaging and locked development environment | Python-API-Engineer | `P1-ARCH01` | M / 3–5 |
| `P1-CI01` | Configure local CI, per-PR audits and isolated red-main policy | Release-CI-Engineer | `P1-ARCH01`, `P1-TOOL-BRANCH01`, `P1-TOOL-AUDIT01` | M / 3–5 |
| `P1-LIC01` | Establish clean-room provenance and Apache-2.0 repository baseline | License-Compliance-Reviewer | `P1-ARCH01`, `P1-PACK01`, `P1-TOOL-AUDIT01` | M / 3–5 |
| `P1-PR-AUDIT01` | Enforce provenance and authored-scope audits on every PR | License-Compliance-Reviewer | `P1-CI01`, `P1-TOOL-AUDIT01` | S / 2–3 |
| `P1-PROTO01` | Define snapshot, command, event, error and identity contracts | Protocol-Engineer | `P1-ARCH01`, `P1-PR-AUDIT01` | M / 3–5 |
| `P1-TAG-CONTRACT01` | Create the immutable pre-contract rollback tag | Integrator | `P1-PROTO01`, `P1-TOOL-BRANCH01` | XS / 0.5–1 |
| `P1-API01` | Freeze typed Python API, handle semantics and public stubs | Python-API-Engineer | `P1-PROTO01`, `P1-PACK01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01` | M / 3–5 |
| `P1-BENCH00` | Freeze benchmark CLI, scene, counter and artifact interface | Perf-Engineer | `P1-PROTO01`, `P1-PACK01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01` | S / 2–3 |
| `P1-RUSTCONTRACT01` | Define and compile-test internal Rust hand-offs and instrumentation contract | Integrator | `P1-PROTO01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01` | L / 6–8 |
| `P1-CONREV01` | Independently review and freeze external and internal contracts | Independent-Reviewer | `P1-API01`, `P1-BENCH00`, `P1-RUSTCONTRACT01`, `P1-LIC01`, `P1-CI01`, `P1-TOOL-GRAPH01` | S / 1–2 |
| `P1-CORE01` | Implement bounded command queue and demand/idle scheduler | Rust-Core-Engineer | `P1-CONREV01`, `P1-PR-AUDIT01` | M / 3–5 |
| `P1-TEXT01` | Implement cosmic-text shaping, glyph atlas and fallback | Rust-Text-Engineer | `P1-CONREV01`, `P1-PR-AUDIT01` | M / 3–5 |
| `P1-CORE02` | Implement generation-safe handles, slot cap and teardown | Rust-Core-Engineer | `P1-CORE01` | M / 3–5 |
| `P1-SCENE01` | Implement snapshot reconciliation, full rebuild and constrained layout | Rust-Scene-Engineer | `P1-TEXT01`, `P1-CONREV01` | L / 6–8 |
| `P1-INPUT01` | Implement Rust-owned pointer, key, focus and IME state machines | Rust-Input-Engineer | `P1-SCENE01` | M / 3–5 |
| `P1-RENDER01` | Implement wgpu renderer, text draws and surface state machine | Rust-Render-Engineer | `P1-SCENE01`, `P1-TEXT01` | L / 6–8 |
| `P1-PLATFORM01` | Implement the single winit main-thread loop and event orchestration | Rust-Platform-Engineer | `P1-CORE01`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01` | L / 6–8 |
| `P1-PY01` | Implement the PyO3 event actor and Python facade binding | Python-Binding-Engineer | `P1-PLATFORM01`, `P1-SCENE01`, `P1-CORE02` | L / 6–8 |
| `P1-INSTRUMENT01` | Add production native counters and deliberate sentinels across the frame closure | Rust-Core-Engineer | `P1-CORE02`, `P1-SCENE01`, `P1-RENDER01`, `P1-PLATFORM01`, `P1-PY01` | M / 3–5 |
| `P1-BENCHCLI01` | Implement and negatively test every benchmark subcommand | Perf-Engineer | `P1-BENCH00`, `P1-PACK01`, `P1-INSTRUMENT01`, `P1-PR-AUDIT01` | L / 6–8 |
| `P1-SLICE01` | Implement the Counter vertical slice on an unmerged feature branch | Integrator | `P1-CORE02`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01`, `P1-PLATFORM01`, `P1-PY01`, `P1-INSTRUMENT01` | M / 3–5 |
| `P1-LOCALWHEEL01` | Build and hash a local Linux wheel from the Counter branch | Release-CI-Engineer | `P1-SLICE01`, `P1-PACK01`, `P1-LIC01`, `P1-TOOL-RELEASE01` | M / 3–5 |
| `P1-TST01` | Independently verify Counter behavior, typing and snapshot properties | Test-Engineer | `P1-SLICE01`, `P1-LOCALWHEEL01` | M / 3–5 |
| `P1-REV01` | Independently review Counter correctness and unsafe/GIL/lifetime safety | Independent-Reviewer | `P1-SLICE01`, `P1-TST01`, `P1-LOCALWHEEL01` | M / 3–5 |
| `P1-INT01` | Integrator-only merge of the verified Counter PR | Integrator | `P1-REV01`, `P1-TST01`, `P1-TOOL-BRANCH01`, `P1-LIC01` | S / 1–2 |
| `P1-PERF01` | Prove callback-free windows and separate-interpreter diagnostics | Perf-Engineer | `P1-INT01`, `P1-BENCHCLI01`, `P1-READY-BENCH01` | M / 3–5 |
| `P1-PLAT01` | Run Linux headless and native common-runtime smoke gates | Platform-Test-Engineer | `P1-INT01`, `P1-LOCALWHEEL01`, `P1-TOOL-PLATFORM01` | M / 3–5 |
| `P1-A11Y-MANIFEST01` | Add exact AccessKit dependencies and refresh lock under Integrator ownership | Integrator | `P1-INT01`, `P1-PR-AUDIT01` | S / 1–2 |
| `P1-DOC01` | Write initial Counter documentation and claim-evidence policy | Technical-Writer | `P1-API01`, `P1-INT01`, `P1-TOOL-DOC01` | S / 2–3 |
| `P1-BENCH01` | Implement deterministic scenes, qualify collectors and capture immutable baseline | Perf-Engineer | `P1-INT01`, `P1-PERF01`, `P1-BENCHCLI01`, `P1-PLAT01` | L / 6–8 |
| `P1-A11Y01` | Implement Rust semantic mirror, AccessKit adapter and window lifecycle wiring | Rust-Accessibility-Engineer | `P1-A11Y-MANIFEST01`, `P1-PLATFORM01`, `P1-INPUT01` | L / 6–8 |
| `P1-REL01` | Build and audit native candidate wheels and sdist | Release-CI-Engineer | `P1-INT01`, `P1-A11Y01`, `P1-LIC01`, `P1-READY-RELEASE01`, `P1-TOOL-RELEASE01` | L / 6–8 |
| `P1-A11Y-LIST01` | Implement and unit-test the accessible 10,000-row representation | Rust-Accessibility-Engineer | `P1-A11Y01`, `P1-BENCH01` | M / 3–5 |
| `P1-PLAT02` | Close candidate platform certification and support-manifest gates | Platform-Test-Engineer | `P1-REL01`, `P1-PLAT01`, `P1-A11Y01`, `P1-READY-PLATFORM01` | L / 6–8 |
| `P1-LIC02` | Close artifact license, SBOM, notice and Wayland distribution gates | License-Compliance-Reviewer | `P1-REL01`, `P1-LIC01`, `P1-READY-RELEASE01`, `P1-TOOL-RELEASE01` | M / 3–5 |
| `P1-PERF02` | Qualify presented/input metrics, execute ABBA compare gate and decide scaling | Perf-Engineer | `P1-BENCH01`, `P1-PLAT02`, `P1-READY-BENCH01` | L / 6–8 |
| `P1-IME01` | Run physical IME matrix and cited platform defect exercises | Platform-Test-Engineer | `P1-PLAT02`, `P1-READY-PLATFORM01` | M / 3–5 |
| `P1-LICENSE-CLOSE01` | Close AR10-G1 with the owner notice and exact artifact metadata | License-Compliance-Reviewer | `P1-LIC02`, `P1-REL01`, `P1-READY-RELEASE01` | S / 1–2 |
| `P1-A11Y-AT01` | Certify physical AT workflows after IME evidence | Accessibility-Test-Engineer | `P1-IME01`, `P1-A11Y-LIST01`, `P1-PLAT02`, `P1-READY-PLATFORM01` | M / 3–5 |
| `P1-A11Y-BENCH01` | Prove AT-on frame, idle and callback gates after benchmark qualification | Perf-Engineer | `P1-A11Y01`, `P1-BENCH01`, `P1-PERF02` | M / 3–5 |
| `P1-WHEEL-CALLBACK01` | Rerun callback and AT-on proof on the exact release wheel hashes | Perf-Engineer | `P1-REL01`, `P1-PERF01`, `P1-BENCHCLI01`, `P1-A11Y-BENCH01` | M / 3–5 |
| `P1-ARTIFACT-GATE01` | Verify current artifact hashes and invalidate stale downstream evidence | Release-CI-Engineer | `P1-REL01`, `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-WHEEL-CALLBACK01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` | S / 1–2 |
| `P1-DOC-FINAL01` | Close final documentation and claim register against current evidence hashes | Technical-Writer | `P1-DOC01`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-LICENSE-CLOSE01`, `P1-ARTIFACT-GATE01` | S / 1–2 |
| `P1-REL02` | Verify same-wheel clean installs and assemble the final reproducible release bundle | Release-CI-Engineer | `P1-REL01`, `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-WHEEL-CALLBACK01`, `P1-LIC02`, `P1-LICENSE-CLOSE01`, `P1-ARTIFACT-GATE01`, `P1-DOC-FINAL01`, `P1-READY-RELEASE01` | L / 6–8 |

Later rows are evidence gates, not authorization for broader features. Missing readiness or evidence keeps the affected task and claim blocked.

## 6. First dispatch waves

| Wave | Dispatch | Boundary / join condition |
|---|---|---|
| 0 | `P1-GOV01` | `P0-AP01` done; graph, remote/auth, readiness and branch policy recorded |
| 1-tools | `P1-TOOL-BRANCH01`, then the other six tool tasks in parallel | Branch evidence tool exists first; every gate script has negative tests and a merged owner branch |
| 1-readiness | `P1-READY-PLATFORM01`, `P1-READY-BENCH01`, `P1-READY-RELEASE01` | Fail closed if hardware, collectors, interpreters, notice, Wayland or credentials are missing |
| 2-scaffold | `P1-ARCH01` → `P1-PACK01` → `P1-LIC01`; `P1-CI01` and `P1-PR-AUDIT01` follow their tool/manifest producers | No parallel manifest edits; per-PR provenance/authored-scope checks are active before source branches |
| 3-contracts | `P1-PROTO01` → `P1-TAG-CONTRACT01` → `P1-API01`, `P1-BENCH00`, `P1-RUSTCONTRACT01` | External and internal contracts are implemented and independently reviewed |
| 4-freeze | `P1-CONREV01` | Contract hashes frozen; missing/changed hash exits nonzero |
| 5-modules | `P1-CORE01` → `P1-CORE02`; `P1-TEXT01` → `P1-SCENE01` → `P1-INPUT01`/`P1-RENDER01` → `P1-PLATFORM01` → `P1-PY01` → `P1-INSTRUMENT01`; `P1-BENCHCLI01` after instrumentation | Dependencies encode real text/paint/hit/focus/platform/instrumentation producers; no unfrozen interface parallelism |
| 6-counter | `P1-SLICE01` | Counter works headlessly on an unmerged feature branch; premerge tag created |
| 7-counter-verify | `P1-LOCALWHEEL01` → `P1-TST01` and `P1-REV01` → `P1-INT01` | Same hashed local wheel is tested; independent review passes; Integrator alone merges |
| 8-evidence | Platform, benchmark, IME, AT, wheel-callback and license proof bundles | Physical readiness and exact artifact hashes are mandatory; proof gates fail nonzero when inconclusive |
| 9-closure | `P1-ARTIFACT-GATE01` → `P1-DOC-FINAL01` → `P1-REL02` | No stale artifact hash or unsupported claim enters the final bundle |

## 7. Interface ownership and safe parallel boundaries

| Path/interface | Owner | Rule |
|---|---|---|
| Root Cargo manifests, lock, toolchain | Integrator | Only `P1-ARCH01` and `P1-A11Y-MANIFEST01`; no parallel edits |
| `pyproject.toml`, dev lock, package skeleton | Python-API-Engineer | `P1-PACK01` before typing, wheel or release consumers |
| `crates/pygpui-protocol/**` | Protocol-Engineer | Sole external value-schema owner |
| Internal Rust contracts | Integrator | `P1-RUSTCONTRACT01`; hashes frozen by `P1-CONREV01` |
| `crates/pygpui-core/**` | Rust-Core-Engineer | Queue/handles/scheduler/instrumentation; serial core tasks |
| Scene layout/reconcile | Rust-Scene-Engineer | Depends on text measurement producer |
| Scene text | Rust-Text-Engineer | Frozen text trait; disjoint from layout |
| Scene input | Rust-Input-Engineer | Depends on scene hit/focus tree |
| Scene a11y/list | Rust-Accessibility-Engineer | Adapter after Counter merge; list implementation separate from AT certification |
| `crates/pygpui-render/**` | Rust-Render-Engineer | Depends on scene/text paint hand-off; no PyO3/winit |
| `crates/pygpui-platform/**` | Rust-Platform-Engineer | Depends on core/scene/text/input/render; sole winit owner |
| `crates/pygpui-python/**` | Python-Binding-Engineer | Depends on platform/scene; sole PyO3 owner |
| `pygpui_bench/**` | Perf-Engineer | Contract first, then all subcommands with negative tests |
| `.harness/scripts/**` | Release-CI-Engineer | Graph/freeze validators and negative tests |
| `tools/ci/**` | Release-CI-Engineer | Branch gate, isolated drills, tags and local runner |
| `tools/license/**`, `tools/audit/**` | License-Compliance-Reviewer | Provenance, authored scope and safety audits |
| `tools/platform/**` | Platform-Test-Engineer | Readiness/platform/IME/AT/support-manifest gates |
| `tools/release/**` | Release-CI-Engineer | Artifact, clean-install, reproducibility and invalidation gates |
| `tools/docs/**` | Technical-Writer | Claim-evidence audit |
| `docs/**` | Technical-Writer | Initial docs and final hash-closed claim register |

Shared files serialize work. A consumer starts only after its producer is `merged`, except the explicit Counter branch-artifact path.

## 8. Critical path and estimates

**Counter:** `P0-AP01` → `P1-GOV01` → `P1-TOOL-BRANCH01`/tool wave → `P1-ARCH01` → `P1-PACK01` → `P1-PROTO01` → contracts/freeze → `P1-CORE01` → `P1-CORE02` and text/scene/input/render/platform/Python/instrumentation chain → `P1-SLICE01` → `P1-LOCALWHEEL01` → `P1-TST01`/`P1-REV01` → `P1-INT01`.

**Evidence-gated completion:** Counter merge → accessibility adapter and release wheels → physical platform gates → benchmark/input/ABBA decision → IME → accessible-list implementation → AT → AT-on and exact-wheel callback proof → license/notice closure → artifact-hash gate → final docs → release bundle.

S = 1–2 ideal engineer-days; M = 3–5; L = 6–8; XS = 0.5–1. No task is XL. Estimates include tests, review churn and PR integration but exclude hardware queues, counsel, user decisions and signing credentials. The critical path is longer than attempt 1 because missing producers and review states are now explicit.

## 9. Fail-closed evidence and artifact invalidation

- A listed gate is not passed because its identifier exists. Each gated task writes `evidence/<task-id>/gate-results.json`; missing, disabled, stale or inconclusive evidence keeps the task out of `done`.
- Proof commands exit nonzero on inconclusive/disabled/missing evidence. Diagnostic commands may emit `inconclusive`, but a pass claim may not consume it.
- Native callback counters are authoritative. Any nonzero callback/frame-entry/GIL/attachment/finalizer counter is an absolute failure.
- Headless hashes and submit counts are capacity evidence only. Presentation and OS-input-to-presented-response require qualified physical collectors.
- Artifacts are immutable by SHA-256. Repair creates a new artifact ID; `P1-ARTIFACT-GATE01` rejects stale downstream platform, callback, benchmark, IME, AT, license and docs evidence and reopens the affected tasks.
- AR10-G1 is separate from repository baseline work: `P1-LICENSE-CLOSE01` cannot pass without the owner-supplied copyright notice and exact artifact metadata.

## 10. Rollback and red-main safety

- `P1-TAG-CONTRACT01` creates and pushes `phase1/contracts-premerge` without force.
- `P1-SLICE01` creates and pushes `phase1/counter-premerge` without force.
- `P1-TOOL-BRANCH01` owns `tools/ci/red_main_drill.py` and `tools/ci/rollback_drill.py`.
- Drills use disposable bare remotes or fixture repositories under `/tmp/opencode`; production `origin/main` is never reddened.
- Exact rollback sequence: create tag → merge reviewed change in fixture → inject observed failure → `git revert <merge>` → rerun full gate → `git revert <revert>` or re-merge the reviewed commit → rerun full gate → archive fixture PRs, tags and green hashes.
- Production rollback uses a reviewed revert PR merged only by the Integrator. No force-push or history rewrite is permitted.

## 11. Risks and residual uncertainty

| Risk | Control |
|---|---|
| One GitHub identity cannot prove role separation | Distinct session-role evidence checked by `branch_gate.py`; Integrator checklist |
| Physical runners/collectors unavailable | Explicit readiness tasks; affected claims stay blocked |
| Python/Rust main-thread/GIL lifetime defects | Internal contract, instrumentation, independent unsafe/GIL/lifetime review and close/finalizer tests |
| Taffy/slotmap/cosmic-text defects | Constrained layout, 65,536 cap, no detach/reattach, atlas/fallback tests |
| Metal first-frame/AccessKit ordering | Invisible → attach → show → present; physical macOS gate |
| IME/AT platform gaps | State-machine properties, IME-before-AT dependency and physical workflows |
| Invalid benchmark endpoint/counts | Frozen protocol, ≤51 rows, five blocks/ten pairs, actual compare command |
| Wayland/copyright/signing uncertainty | Readiness and artifact gates; no unsupported distribution/trust claim |
| Artifact repair stales evidence | Immutable hashes and `P1-ARTIFACT-GATE01` rerun edge |
| Control-plane conflicts | Orchestrator-serialized `STATE.md`/`TASKS.json`; feature-owned LOG/handoffs |

## 12. ADR gate traceability

| AR01-G1 | `P1-PLATFORM01`, `P1-PLAT02` | Main-thread lifecycle and installed-wheel close/no-worker tests exit zero |
| AR01-G2 | `P1-REV01` | Static dependency/call-graph audit exits zero; no Python frame path |
| AR01-G3 | `P1-PERF01` | Native counters are zero and each deliberate sentinel is exactly one |
| AR01-G4 | `P1-CORE01` | Bounded queue/backpressure and 60-second idle tests exit zero |
| AR02-G1 | `P1-PROTO01`, `P1-SCENE01`, `P1-TST01` | Atomic replacement, rollback, identity/reorder/teardown properties exit zero |
| AR02-G2 | `P1-SLICE01`, `P1-PLAT02` | Counter headless and candidate presented-response tests exit zero; click/key update once |
| AR02-G3 | `P1-SCENE01` | One full rebuild per semantic change and zero no-change rebuilds |
| AR02-G4 | `P1-PERF01` | Submission-to-presentation counters and sentinels stay zero |
| AR02-G5 | `P1-PERF02` | e1000/l10000 pass or profile names full rebuild as blocker before incremental work |
| AR03-G1 | `P1-API01`, `P1-TST01` | Strict mypy, stubtest and negative API fixtures pass |
| AR03-G2 | `P1-CORE02`, `P1-TST01` | Strong/weak/generation/wrong-kind/stale-handle tests exit zero |
| AR03-G3 | `P1-PY01`, `P1-TST01` | Reentrancy, build mutation, run reentry and release tests exit zero |
| AR03-G4 | `P1-REV01` | No Python reference in snapshot/scene/cache; ownership audit exits zero |
| AR03-G5 | `P1-ARCH01`, `P1-CONREV01` | cargo metadata --locked and crate-graph/internal-contract tests exit zero |
| AR04-G1 | `P1-ARCH01` | Locked check and three-target metadata exit zero; no GLES/AccessKit leakage |
| AR04-G2 | `P1-SCENE01` | Taffy #804/#1354/#1357, supported subset and fallback tests exit zero |
| AR04-G3 | `P1-CORE02` | 65,536 cap, stale/reuse tests and no-detach source audit exit zero |
| AR04-G4 | `P1-TEXT01` | ASCII/CJK/RTL/emoji/fallback atlas tests exit zero; #518 behavior recorded |
| AR04-G5 | `P1-SCENE01` | Large rebuild test and rustc-hash pattern audit exit zero |
| AR04-G6 | `P1-REL02` | Release states only pinned Rust 1.100.0 unless exact-compiler MSRV evidence passes |
| AR05-G1 | `P1-REL01` | Native candidate builds exit zero with artifact/target/feature/toolchain hashes |
| AR05-G2 | `P1-RENDER01`, `P1-PLAT01`, `P1-PLAT02` | Installed-wheel T02-T12 exit zero with physical evidence |
| AR05-G3 | `P1-PLAT02` | Linux L01-L08 on Wayland/Xorg pass including 30-minute soak |
| AR05-G4 | `P1-PLAT02` | Windows W01-W07 pass with recorded shader-compiler strategy |
| AR05-G5 | `P1-PLAT02` | macOS M01-M08 pass with invisible/adapter/show/present sequence |
| AR05-G6 | `P1-PLAT02`, `P1-REL02` | Support manifest includes only platforms with complete passing evidence |
| AR06-G1 | `P1-INPUT01` | IME/focus/UTF-8/version/close property tests exit zero |
| AR06-G2 | `P1-IME01` | Physical Japanese/Chinese/Korean/dead-key matrix passes cited defect exercises |
| AR06-G3 | `P1-A11Y01` | AccessKit identity/diff/focus/action consumer tests exit zero |
| AR06-G4 | `P1-A11Y-AT01` | VoiceOver/Narrator/Orca workflows pass after IME evidence; inspector-only fails |
| AR06-G5 | `P1-A11Y-BENCH01` | AT-on benchmark has zero Python-boundary counters and no frame/idle regression |
| AR06-G6 | `P1-A11Y-LIST01` | 10,000-row accessible representation and #871 disposition are tested before claim |
| AR07-G1 | `P1-REL01` | Three wheels plus sdist pass tag/abi3audit/repair/content checks |
| AR07-G2 | `P1-REL02` | Same wheels pass clean CPython 3.11-3.15 GIL matrix on candidate OSs |
| AR07-G3 | `P1-API01`, `P1-TST01` | mypy 2.4.1 strict/explicit-Any and stubtest exit zero |
| AR07-G4 | `P1-PLAT02`, `P1-WHEEL-CALLBACK01`, `P1-REL02` | Exact release-wheel hashes pass callback reruns; pre-wheel evidence is rejected |
| AR07-G5 | `P1-REL02` | Reproducibility and evidence archive exit zero; public signing/publishing stays blocked |
| AR08-G1 | `P1-BENCH00`, `P1-BENCH01` | Scene/harness/collector qualification exits zero including ≤51 rows and raw hashes |
| AR08-G2 | `P1-BENCH01` | Ten valid fresh-process runs per scenario form an immutable baseline |
| AR08-G3 | `P1-PERF01` | Static audit, zero counters, Python 3.11 fallback and separate interpreters pass |
| AR08-G4 | `P1-PERF02` | Presented/input collector and clock checks pass or status is inconclusive |
| AR08-G5 | `P1-PERF02` | Actual compare command rejects >10% until diagnosis; exactly 10.0% and ten pairs verified |
| AR08-G6 | `P1-PERF02` | pass requires OQ-02, correctness/counters, environment and raw artifacts |
| AR09-G1 | `P1-LIC01`, `P1-PR-AUDIT01` | Complete per-PR provenance ledger; unapproved copied/translated expression prevents merge |
| AR09-G2 | `P1-LIC02` | Lockfile-fed scanner/SBOM exits zero with no unreviewed exception per artifact |
| AR09-G3 | `P1-LIC02` | Wheel/sdist license/copyright/NOTICE/font/asset audit matches SBOM |
| AR09-G4 | `P1-LIC02` | Wayland clarification/counsel plus audit is archived or publication stays blocked |
| AR09-G5 | `P1-LIC01` | Source-exception workflow rejects incomplete records and accepts all required fields |
| AR10-G1 | `P1-REL01`, `P1-LICENSE-CLOSE01` | Cargo/wheel metadata, official LICENSE and owner notice checks exit zero |
| AR10-G2 | `P1-LIC02` | Artifact contents and SBOM agree; no third-party file is relicensed |
| AR10-G3 | `P1-LIC01`, `P1-PR-AUDIT01` | Per-PR authored-file audit and Apache-2.0 inbound contribution terms pass |
| AR10-G4 | `P1-DOC-FINAL01`, `P1-REL02` | Artifact gates pass and final docs make no unsupported patent/trademark/Wayland claim |

## 13. Plan completion

This revision is complete only when the repository validator, handoff validator and negative tests pass, exact output is written to `evidence/P0-PL01/validation-attempt-2.txt`, `P0-PL01` is marked done at attempt 2, and the Red-Team attempt-2 handoff contains every Part 3 field. No Phase 1 task or `P0-AP01` is authorized by this plan.
