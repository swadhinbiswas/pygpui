# Phase 1 plan — execution-ready Counter slice

- Planner task: `P0-PL01`, attempt 3
- Prepared: 2026-11-24
- Accepted ADR baseline: `5ce026d`
- Red-Team blocker baseline: `8ffe8de`
- Execution state: **final planned revision; `P0-AP01` and every Phase 1 task remain `blocked` at attempt zero**
- Authoritative graph: `.harness/TASKS.json`
- Reproducible validators: `.harness/scripts/validate_phase1_graph.py`, `.harness/scripts/validate_handoff.py`
- Gate schema: `.harness/schemas/gate-results.schema.json`
- Delivery model: branch/worktree → PR → trusted independent pre-merge verification → Integrator-only merge → post-merge record. No force-push or direct push to `main`.

## 1. Goal

Deliver the ADR 0002 Counter window first: Python creates an entity/view; Rust presents shaped text and a button; click or keyboard activation updates Python state exactly once; one complete Rust-owned snapshot crosses the boundary; Rust rebuilds and presents the response; close is clean; no Python runs on the frame path. Preserve all 52 ADR gates with staged, fail-closed evidence rather than expanding into a broad widget framework.

## 2. Scope and non-goals

### In scope

- Exact crate graph, pins, toolchain, production lockfile, root Python packaging and a neutral test-only contract crate.
- Frozen external and internal contracts before parallel implementation.
- Counter only, using `App`, `Entity[T]`, `WeakEntity[T]`, `View[T]`, opaque handles, `Action`, typed errors and `Text`/`Button`/`Row`/`Column`.
- One main-thread winit loop, one wgpu renderer, complete snapshot replacement and full-window rebuild.
- Owned gate tooling, staged sub-gates, trusted session evidence, durable artifacts, isolated rollback drills and per-PR provenance audits.
- Independent tests, unsafe/GIL/lifetime review, native instrumentation, callback sentinels, headless and physical platform smoke tests.
- Benchmark, platform, IME, accessibility, wheel, typing, license/SBOM, artifact-invalidation and release-evidence gates.

### Non-goals

- A broad widget framework, CSS compatibility, multiwindow, async integration, rich-text public authoring, app bundles or stores.
- Incremental patches, subtree caches, damage tracking or a persistent Python VDOM before the ADR 0002 scaling decision and a superseding ADR.
- Public free-threaded Python, `abi3t`, macOS Intel/universal2, Linux ARM64, GLES/OpenGL fallback, HDR, transparency or exclusive fullscreen.
- An MSRV promise, final performance certification, WCAG claim, complete-IME claim, virtualized-list accessibility claim, permissive-only Wayland distribution claim, public signing, notarization or publishing.
- Editing accepted ADRs, research, reviews, `STATE.md`, `PROCESS.md` or feature code in this planning task.

## 3. Attempt-2 blocker resolution

| Finding | Revision |
|---|---|
| RT2-B01 | Added `gate_model`, 26 staged sub-gates, 52 single-owner final aggregators, `.harness/schemas/gate-results.schema.json`, `P1-GATE-SCHEMA01` and semantic validator checks for all 14 deadlocks plus AR03-G5. |
| RT2-B02 | Added `P1-ARTIFACT-STORE01`; wheels use unique append-only GitHub draft-release tags, authenticated fetch/verify, source-commit/lockfile/toolchain binding and immutable artifact IDs. Ignored `dist/` is never shared state. |
| RT2-B03 | Build tasks now complete pre-merge at `independently_verified`; Integrator merge records are post-merge. Every proof/verification task requires distinct reviewer/tester evidence checked by the trusted session registry. |
| RT2-B04 | Cross-crate contract compile tests moved to `crates/pygpui-contract-tests`; production crates never depend on it and `pygpui-core` has no foreign-crate test dependency. |
| RT2-B05 | `P1-TAG-CONTRACT01` now runs before `P1-PROTO01` and verifies the tagged tree lacks the protocol contract. |
| RT2-B06 | Added `P1-NATIVE-READY01`; candidate wheel builds require native Linux/Windows/macOS lanes. |
| RT2-B07 | Split proof/build readiness from OQ-02 certification and Wayland/signing/publication claim readiness; local wheels, callback proof and baselines no longer wait for unrelated approvals. |
| RT2-N01 | Validator now checks staged closure, artifact handoff, review/merge ordering, crate legality, tag timing, native readiness, claim separation and scope normalization. |
| RT2-N02 | Scopes/producers are normalized; duplicate entries and `produces` outside `write_scope` fail validation. |
| RT2-N03 | Aggregate estimates and unbounded external waits are stated in §9. |
| RT2-N04 | Session roles live in an append-only Orchestrator-controlled registry; records are checked rather than merely asserted. Branch protection remains deferred. |

## 4. Staged gate model

Each full `ARxx-Gn` has exactly one final aggregator in `gate_model`. Producer tasks emit named sub-gates such as `AR02-G1.schema`, `AR05-G2.linux-installed` or `AR07-G4.same-wheel-callbacks`. An aggregator passes only when every required sub-gate passes with current source/artifact hashes.

- `gate-results.json` conforms to `.harness/schemas/gate-results.schema.json`.
- Status is one of `pass`, `fail`, `inconclusive`, `blocked` or `not_measured`.
- Every result binds source commit, lockfile SHA-256, toolchain and SHA-256 evidence.
- Reviewer and tester session IDs must differ and exist in `.harness/sessions/registry.json`.
- Missing, disabled, stale or inconclusive evidence fails closed.
- AR03-G5 contains only metadata and crate-graph stages; internal-contract tests are deliberately not part of that ADR gate.

## 5. Dependency and branch-state semantics

A dependency is satisfied only when the producer reaches its declared state:

- `implemented`: code and author-run tests exist on the branch; branch artifacts may be consumed but the branch may not be merged.
- `independently_verified`: trusted reviewer and tester sessions accepted the same commit/artifact; pre-merge acceptance is complete.
- `merged`: the Integrator accepted pre-merge evidence, merged the PR and recorded the merge SHA; consumers branch from this `main`.
- `recorded`: a control/readiness task archived a structured result without a code-merge claim.

Build tasks complete at `independently_verified`. Their acceptance cannot require `--state merged`. After merge, the Integrator runs `tools/ci/record_merge.py` and writes `evidence/<task-id>/merge.json`; dependent branches wait for that record. `P1-SLICE01` is the sole implementation-stage exception, followed by `P1-TST01`, `P1-REV01` and `P1-INT01`.

### Trusted single-identity review model

One GitHub identity is available. Role separation is procedural but machine-checked:

1. Orchestrator appends implementer/reviewer/tester/Integrator session roles to `.harness/sessions/registry.json`.
2. Implementer records branch, commit, scope and author-run logs.
3. Reviewer and tester sessions must be distinct and record the same commit/artifact.
4. `tools/session/verify_roles.py` and `tools/review/verify_proof.py` reject self-certification, missing roles and commit mismatch.
5. Integrator alone merges and records the post-merge SHA.

## 6. Durable artifact store

**Mechanism:** authenticated GitHub draft-release assets. Draft releases are not public and need no publishing credentials.

- Unique tag: `artifacts/<artifact-id>`.
- Upload: `gh release create artifacts/<artifact-id> --draft --title <artifact-id> --notes <manifest-summary>` then `gh release upload artifacts/<artifact-id> <files>`.
- Fetch: `gh release download artifacts/<artifact-id> --dir <destination>`.
- Verify: `python3 tools/artifacts/store.py verify --manifest <manifest.json> --dir <destination>`.
- Retention: no automatic expiry; retain through Phase 1 closure and required audit/review periods.
- Access: authenticated `swadhinbiswas` account with `repo` scope.
- Immutability: never reuse a tag, overwrite/delete an asset or rewrite a manifest. Repair creates a new artifact ID.
- Binding: manifest records source commit, `Cargo.lock` SHA-256, Rust toolchain, target/features and artifact SHA-256.

`P1-LOCALWHEEL01` binds its wheel to the reviewed `P1-SLICE01` commit. Every installed-wheel consumer fetches and verifies the durable asset. `P1-ARTIFACT-GATE01` rejects stale downstream hashes.

## 7. Dependency-ordered task graph

All tasks start at attempt 0, status `blocked` and branch state `not_started`. Ranges are ideal engineer-days including tests/review, excluding hardware, counsel and user wait time.

| ID | Deliverable | Owner | Dependencies | Size / range |
|---|---|---|---|---|
| `P1-GOV01` | Authorize Phase 1 and record execution readiness | Orchestrator | `P0-AP01` | S / 1–2 |
| `P1-SESSION-REGISTRY01` | Own the trusted append-only session-role registry | Orchestrator | `P1-GOV01` | M / 3–5 |
| `P1-GATE-SCHEMA01` | Own the staged gate-results schema and aggregator | Release-CI-Engineer | `P1-GOV01` | M / 3–5 |
| `P1-TOOL-BRANCH01` | Own branch evidence, isolated red-main, tag and rollback tooling | Release-CI-Engineer | `P1-GOV01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-TOOL-GRAPH01` | Own and negatively test graph and contract-freeze validators | Release-CI-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | M / 3–5 |
| `P1-TOOL-AUDIT01` | Own fail-closed provenance, source, safety and per-PR audit tools | License-Compliance-Reviewer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-PLATFORM01` | Own readiness, platform, IME, AT and support-manifest gate tools | Platform-Test-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-DOC01` | Own documentation build and claim-evidence audit tooling | Technical-Writer | `P1-GOV01`, `P1-TOOL-BRANCH01` | S / 2–3 |
| `P1-TOOL-RELEASE01` | Own artifact audit, clean-install, reproducibility and invalidation tools | Release-CI-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | L / 6–8 |
| `P1-TOOL-BENCH01` | Own benchmark readiness, collector and interpreter diagnostic tools | Perf-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01` | M / 3–5 |
| `P1-ARTIFACT-STORE01` | Own immutable draft-release artifact storage, fetch and verification | Release-CI-Engineer | `P1-GOV01`, `P1-TOOL-BRANCH01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-READY-PLATFORM01` | Record physical platform, IME and AT runner readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-PLATFORM01` | S / 1–2 |
| `P1-READY-BENCH01` | Record benchmark hardware, collector and OQ-02 readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-BENCH01` | S / 1–2 |
| `P1-READY-RELEASE01` | Record CPython, copyright, Wayland and release-channel readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-RELEASE01` | S / 1–2 |
| `P1-ARCH01` | Create exact workspace, crate graph, pins and production lock | Integrator | `P1-GOV01`, `P1-TOOL-GRAPH01`, `P1-TOOL-BRANCH01`, `P1-TOOL-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-NATIVE-READY01` | Record native Linux, Windows and macOS wheel-build lane readiness | Orchestrator | `P1-GOV01`, `P1-TOOL-RELEASE01` | S / 1–2 |
| `P1-READY-CERT01` | Record OQ-02 performance certification approval | Orchestrator | `P1-GOV01`, `P1-TOOL-BENCH01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-READY-CLAIM01` | Record Wayland, signing and publication claim approvals | Orchestrator | `P1-GOV01`, `P1-TOOL-RELEASE01`, `P1-TOOL-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-PACK01` | Create root Python packaging and locked development environment | Python-API-Engineer | `P1-ARCH01` | M / 3–5 |
| `P1-CI01` | Configure local CI, per-PR audits and isolated red-main policy | Release-CI-Engineer | `P1-ARCH01`, `P1-TOOL-BRANCH01`, `P1-TOOL-AUDIT01` | M / 3–5 |
| `P1-LIC01` | Establish clean-room provenance and Apache-2.0 repository baseline | License-Compliance-Reviewer | `P1-ARCH01`, `P1-PACK01`, `P1-TOOL-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-PR-AUDIT01` | Enforce provenance and authored-scope audits on every PR | License-Compliance-Reviewer | `P1-CI01`, `P1-TOOL-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 2–3 |
| `P1-TAG-CONTRACT01` | Create the immutable pre-contract rollback tag | Integrator | `P1-ARCH01`, `P1-PR-AUDIT01`, `P1-TOOL-BRANCH01` | XS / 0.5–1 |
| `P1-PROTO01` | Define snapshot, command, event, error and identity contracts | Protocol-Engineer | `P1-ARCH01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-API01` | Freeze typed Python API, handle semantics and public stubs | Python-API-Engineer | `P1-PROTO01`, `P1-PACK01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-BENCH00` | Freeze benchmark CLI, scene, counter and artifact interface | Perf-Engineer | `P1-PROTO01`, `P1-PACK01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 2–3 |
| `P1-RUSTCONTRACT01` | Define and compile-test internal Rust hand-offs and instrumentation contract | Integrator | `P1-PROTO01`, `P1-PR-AUDIT01`, `P1-TAG-CONTRACT01` | L / 6–8 |
| `P1-CONREV01` | Independently review and freeze external and internal contracts | Independent-Reviewer | `P1-API01`, `P1-BENCH00`, `P1-RUSTCONTRACT01`, `P1-LIC01`, `P1-CI01`, `P1-TOOL-GRAPH01` | S / 1–2 |
| `P1-CORE01` | Implement bounded command queue and demand/idle scheduler | Rust-Core-Engineer | `P1-CONREV01`, `P1-PR-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-TEXT01` | Implement cosmic-text shaping, glyph atlas and fallback | Rust-Text-Engineer | `P1-CONREV01`, `P1-PR-AUDIT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-CORE02` | Implement generation-safe handles, slot cap and teardown | Rust-Core-Engineer | `P1-CORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-SCENE01` | Implement snapshot reconciliation, full rebuild and constrained layout | Rust-Scene-Engineer | `P1-TEXT01`, `P1-CONREV01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-INPUT01` | Implement Rust-owned pointer, key, focus and IME state machines | Rust-Input-Engineer | `P1-SCENE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-RENDER01` | Implement wgpu renderer, text draws and surface state machine | Rust-Render-Engineer | `P1-SCENE01`, `P1-TEXT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-PLATFORM01` | Implement the single winit main-thread loop and event orchestration | Rust-Platform-Engineer | `P1-CORE01`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-PY01` | Implement the PyO3 event actor and Python facade binding | Python-Binding-Engineer | `P1-PLATFORM01`, `P1-SCENE01`, `P1-CORE02`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-INSTRUMENT01` | Add production native counters and deliberate sentinels across the frame closure | Rust-Core-Engineer | `P1-CORE02`, `P1-SCENE01`, `P1-RENDER01`, `P1-PLATFORM01`, `P1-PY01` | M / 3–5 |
| `P1-BENCHCLI01` | Implement and negatively test every benchmark subcommand | Perf-Engineer | `P1-BENCH00`, `P1-PACK01`, `P1-INSTRUMENT01`, `P1-PR-AUDIT01` | L / 6–8 |
| `P1-SLICE01` | Implement the Counter vertical slice on an unmerged feature branch | Integrator | `P1-CORE02`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01`, `P1-PLATFORM01`, `P1-PY01`, `P1-INSTRUMENT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-LOCALWHEEL01` | Build and hash a local Linux wheel from the Counter branch | Release-CI-Engineer | `P1-SLICE01`, `P1-PACK01`, `P1-LIC01`, `P1-TOOL-RELEASE01`, `P1-ARTIFACT-STORE01` | M / 3–5 |
| `P1-TST01` | Independently verify Counter behavior, typing and snapshot properties | Test-Engineer | `P1-SLICE01`, `P1-LOCALWHEEL01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-REV01` | Independently review Counter correctness and unsafe/GIL/lifetime safety | Independent-Reviewer | `P1-SLICE01`, `P1-TST01`, `P1-LOCALWHEEL01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-INT01` | Integrator-only merge of the verified Counter PR | Integrator | `P1-REV01`, `P1-TST01`, `P1-TOOL-BRANCH01`, `P1-LIC01` | S / 1–2 |
| `P1-PERF01` | Prove callback-free windows and separate-interpreter diagnostics | Perf-Engineer | `P1-INT01`, `P1-BENCHCLI01`, `P1-READY-BENCH01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-PLAT01` | Run Linux headless and native common-runtime smoke gates | Platform-Test-Engineer | `P1-INT01`, `P1-LOCALWHEEL01`, `P1-TOOL-PLATFORM01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-A11Y-MANIFEST01` | Add exact AccessKit dependencies and refresh lock under Integrator ownership | Integrator | `P1-INT01`, `P1-PR-AUDIT01` | S / 1–2 |
| `P1-DOC01` | Write initial Counter documentation and claim-evidence policy | Technical-Writer | `P1-API01`, `P1-INT01`, `P1-TOOL-DOC01` | S / 2–3 |
| `P1-BENCH01` | Implement deterministic scenes, qualify collectors and capture immutable baseline | Perf-Engineer | `P1-INT01`, `P1-PERF01`, `P1-BENCHCLI01`, `P1-PLAT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-A11Y01` | Implement Rust semantic mirror, AccessKit adapter and window lifecycle wiring | Rust-Accessibility-Engineer | `P1-A11Y-MANIFEST01`, `P1-PLATFORM01`, `P1-INPUT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-REL01` | Build and audit native candidate wheels and sdist | Release-CI-Engineer | `P1-INT01`, `P1-A11Y01`, `P1-LIC01`, `P1-READY-RELEASE01`, `P1-TOOL-RELEASE01`, `P1-NATIVE-READY01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-A11Y-LIST01` | Implement and unit-test the accessible 10,000-row representation | Rust-Accessibility-Engineer | `P1-A11Y01`, `P1-BENCH01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-PLAT02` | Close candidate platform certification and support-manifest gates | Platform-Test-Engineer | `P1-REL01`, `P1-PLAT01`, `P1-A11Y01`, `P1-READY-PLATFORM01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-LIC02` | Close artifact license, SBOM, notice and Wayland distribution gates | License-Compliance-Reviewer | `P1-REL01`, `P1-LIC01`, `P1-READY-RELEASE01`, `P1-TOOL-RELEASE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-PERF02` | Qualify presented/input metrics, execute ABBA compare gate and decide scaling | Perf-Engineer | `P1-BENCH01`, `P1-PLAT02`, `P1-READY-BENCH01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |
| `P1-IME01` | Run physical IME matrix and cited platform defect exercises | Platform-Test-Engineer | `P1-PLAT02`, `P1-READY-PLATFORM01`, `P1-REL01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-LICENSE-CLOSE01` | Close AR10-G1 with the owner notice and exact artifact metadata | License-Compliance-Reviewer | `P1-LIC02`, `P1-REL01`, `P1-READY-RELEASE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-WAYLAND-GATE01` | Aggregate AR09-G4 only after artifact audit and claim disposition | License-Compliance-Reviewer | `P1-LIC02`, `P1-READY-CLAIM01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-A11Y-AT01` | Certify physical AT workflows after IME evidence | Accessibility-Test-Engineer | `P1-IME01`, `P1-A11Y-LIST01`, `P1-PLAT02`, `P1-READY-PLATFORM01`, `P1-REL01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-A11Y-BENCH01` | Prove AT-on frame, idle and callback gates after benchmark qualification | Perf-Engineer | `P1-A11Y01`, `P1-BENCH01`, `P1-PERF02`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-CERT-GATE01` | Aggregate AR08-G6 only after measurements and OQ-02 approval | Perf-Engineer | `P1-PERF02`, `P1-READY-CERT01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-WHEEL-CALLBACK01` | Rerun callback and AT-on proof on the exact release wheel hashes | Perf-Engineer | `P1-REL01`, `P1-PERF01`, `P1-BENCHCLI01`, `P1-A11Y-BENCH01`, `P1-ARTIFACT-STORE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | M / 3–5 |
| `P1-ARTIFACT-GATE01` | Verify current artifact hashes and invalidate stale downstream evidence | Release-CI-Engineer | `P1-REL01`, `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-WHEEL-CALLBACK01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` | S / 1–2 |
| `P1-DOC-FINAL01` | Close final documentation and claim register against current evidence hashes | Technical-Writer | `P1-DOC01`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-LICENSE-CLOSE01`, `P1-ARTIFACT-GATE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | S / 1–2 |
| `P1-REL02` | Verify same-wheel clean installs and assemble the final reproducible release bundle | Release-CI-Engineer | `P1-REL01`, `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y-AT01`, `P1-A11Y-BENCH01`, `P1-WHEEL-CALLBACK01`, `P1-LIC02`, `P1-LICENSE-CLOSE01`, `P1-ARTIFACT-GATE01`, `P1-DOC-FINAL01`, `P1-READY-RELEASE01`, `P1-ARTIFACT-STORE01`, `P1-WAYLAND-GATE01`, `P1-GATE-SCHEMA01`, `P1-SESSION-REGISTRY01` | L / 6–8 |

Later rows are evidence gates, not authorization for broader features. Missing readiness or evidence keeps the affected task and claim blocked.

## 8. First dispatch waves

| Wave | Dispatch | Join condition |
|---|---|---|
| 0 | `P1-GOV01` | `P0-AP01` done; graph/remote/auth policy recorded |
| 1-control | `P1-SESSION-REGISTRY01`, `P1-GATE-SCHEMA01` | Trusted roles and staged gate schema validate |
| 1-tools | `P1-TOOL-BRANCH01`, then other tool tasks including `P1-ARTIFACT-STORE01` | Every gate script has negative tests and pre-merge evidence |
| 1-readiness | Platform, proof/build, native-lane, certification and claim readiness | Each readiness class gates only its own work/claim |
| 2-scaffold | `P1-ARCH01` → `P1-PACK01` → `P1-LIC01`; CI and per-PR audits follow producers | Legal crate graph, packaging and per-PR controls active |
| 3-contracts | `P1-TAG-CONTRACT01` → `P1-PROTO01` → API/benchmark/internal contracts | Tag verified before protocol merge; contracts independently verified |
| 4-freeze | `P1-CONREV01` | External/internal contract hashes frozen |
| 5-modules | Core/text/scene/input/render/platform/Python/instrumentation/benchmark CLI | Real producer dependencies; neutral contract tests pass |
| 6-counter | `P1-SLICE01` | Counter works headlessly on an unmerged branch |
| 7-counter-verify | Local wheel → independent tests/review → Integrator merge record | Same durable wheel hash tested; no circular merge acceptance |
| 8-evidence | Platform, benchmark, IME, AT, callback and license bundles | Physical readiness and exact artifact hashes enforced |
| 9-closure | Certification/Wayland aggregators → artifact gate → final docs → release bundle | No stale hash or unsupported claim enters final evidence |

## 9. Critical path, estimates and external waits

**Counter:** approval → governance/session/gate tools → scaffold/packaging → pre-contract tag/protocol/contracts/freeze → core/text/scene/input/render/platform/Python/instrumentation → Counter branch → durable local wheel → independent tests/review → Integrator merge.

**Evidence completion:** Counter merge → adapter/release artifacts → physical platform matrix → benchmark/input/ABBA measurements → IME → accessible-list implementation → AT → AT-on/exact-wheel callbacks → license/artifact closure → certification/Wayland aggregators → final docs/release bundle.

Per-task ranges imply roughly **70–110 ideal engineer-days** on the Counter critical path and **120–190 ideal engineer-days** to final evidence closure for one experienced engineer, before review staffing and merge queues. Physical runners, native hosts, collectors, counsel, user approvals and credentials are **unbounded external waits**, not included in those ranges.

## 10. Interface ownership and safe parallel boundaries

| Path/interface | Owner | Rule |
|---|---|---|
| Root Cargo manifests/lock/toolchain | Integrator | Only scaffold and AccessKit manifest tasks; no parallel edits |
| `pyproject.toml`, dev lock, package skeleton | Python-API-Engineer | Before typing/wheel/release consumers |
| `crates/pygpui-protocol/**` | Protocol-Engineer | Sole external schema owner |
| `crates/pygpui-contract-tests/**` | Integrator | Test-only; no production crate depends on it |
| Internal Rust contracts | Integrator | Frozen by `P1-CONREV01` |
| Core | Rust-Core-Engineer | No scene/render/platform dev-dependency |
| Scene layout/text/input/a11y | Respective Rust owners | Producer dependencies encode hand-offs |
| Render | Rust-Render-Engineer | No PyO3/winit |
| Platform | Rust-Platform-Engineer | Sole winit owner; depends on core/scene/input/render |
| Python binding | Python-Binding-Engineer | Sole PyO3 owner |
| Benchmark package | Perf-Engineer | Contract then all subcommands |
| Gate/session/artifact tools | Release-CI/Orchestrator owners | Trusted registries and append-only artifacts |
| License/audit tools | License-Compliance-Reviewer | Per-PR and per-artifact closure |
| Docs | Technical-Writer | Initial docs then hash-closed final claim register |

## 11. Fail-closed evidence and invalidation

- A full gate passes only through its aggregator after all required sub-gates pass.
- Proof commands exit nonzero on inconclusive/disabled/missing evidence.
- Native callback counters are authoritative; any nonzero boundary counter is an absolute failure.
- Headless hashes prove capacity only; presentation needs qualified physical collectors.
- Artifact repair creates a new immutable ID and invalidates downstream platform/callback/benchmark/IME/AT/license/docs evidence until re-audited.
- OQ-02, Wayland distribution and signing/publication approvals gate only their corresponding claims, not local builds or callback/baseline proof.

## 12. Rollback and red-main safety

- `P1-TAG-CONTRACT01` creates `phase1/contracts-premerge` before protocol merge and proves the contract is absent.
- `P1-SLICE01` creates `phase1/counter-premerge` before Counter merge.
- Drills use disposable fixture remotes under `/tmp/opencode`; production `origin/main` is never reddened.
- Exact sequence: tag → reviewed merge in fixture → inject failure → revert → full gate → revert-of-revert or re-merge → full gate → archive fixture PRs/tags/green hashes.
- Production rollback uses a reviewed revert PR merged only by the Integrator. No force-push or history rewrite.

## 13. Risks and residual uncertainty

| Risk | Control |
|---|---|
| Single identity/no branch protection | Append-only trusted session registry and Integrator checklist |
| Physical/native/collector infrastructure absent | Scoped readiness tasks; affected claims stay blocked |
| GIL/unsafe/lifetime defects | Internal contracts, instrumentation and independent safety review |
| Dependency defects | Constrained Taffy/slotmap/cosmic-text tests |
| Metal/IME/AT gaps | Physical platform, IME-before-AT and AT-on gates |
| Invalid benchmark semantics | Staged schema, actual compare command and qualified collectors |
| Artifact loss/staleness | Draft-release storage, hash verification and invalidation gate |
| Wayland/copyright/signing uncertainty | Claim-only readiness and aggregator gates |
| Control-plane conflicts | Orchestrator-serialized State/TASKS; branch-owned LOG/handoffs |

## 14. ADR gate traceability

| AR01-G1 | `P1-PLAT02` | `AR01-G1.unit-lifecycle`, `AR01-G1.installed-lifecycle` | Main-thread unit and candidate installed-wheel lifecycle evidence pass |
| AR01-G2 | `P1-REV01` | atomic | Static call-graph audit exits zero; no Python frame path |
| AR01-G3 | `P1-PERF01` | atomic | Native counters zero and sentinels exactly one |
| AR01-G4 | `P1-CORE01` | atomic | Bounded queue and 60-second idle tests exit zero |
| AR02-G1 | `P1-TST01` | `AR02-G1.schema`, `AR02-G1.reconciliation`, `AR02-G1.integrated-properties` | Schema, reconciliation and integrated property sub-gates pass |
| AR02-G2 | `P1-PLAT02` | `AR02-G2.headless`, `AR02-G2.presented` | Headless and candidate presented-response sub-gates pass |
| AR02-G3 | `P1-SCENE01` | atomic | One rebuild per semantic change; zero no-change rebuilds |
| AR02-G4 | `P1-PERF01` | atomic | Submission-to-presentation counters stay zero |
| AR02-G5 | `P1-PERF02` | atomic | Scaling pass or profile names full rebuild blocker |
| AR03-G1 | `P1-TST01` | `AR03-G1.typing-contract`, `AR03-G1.stubtest` | Typing-contract and stubtest sub-gates pass |
| AR03-G2 | `P1-CORE02` | atomic | Handle lifetime/generation tests pass |
| AR03-G3 | `P1-PY01` | atomic | Reentrancy and release tests pass |
| AR03-G4 | `P1-REV01` | atomic | No Python reference in snapshot/scene/cache |
| AR03-G5 | `P1-ARCH01` | `AR03-G5.metadata`, `AR03-G5.crate-graph` | Metadata and crate-graph sub-gates pass; no internal-contract stage |
| AR04-G1 | `P1-ARCH01` | atomic | Locked check and target metadata pass |
| AR04-G2 | `P1-SCENE01` | atomic | Taffy constrained subset and fallback pass |
| AR04-G3 | `P1-CORE02` | atomic | Slot cap and no-detach audit pass |
| AR04-G4 | `P1-TEXT01` | atomic | Text atlas/fallback tests pass |
| AR04-G5 | `P1-SCENE01` | atomic | Map rebuild safety audit passes |
| AR04-G6 | `P1-REL02` | atomic | No untested MSRV claim |
| AR05-G1 | `P1-REL01` | atomic | Native candidate builds and hashes pass |
| AR05-G2 | `P1-PLAT02` | `AR05-G2.unit-surface`, `AR05-G2.linux-installed`, `AR05-G2.candidate-installed` | Unit, Linux-installed and candidate-installed sub-gates pass |
| AR05-G3 | `P1-PLAT02` | atomic | Linux Wayland/Xorg matrix passes |
| AR05-G4 | `P1-PLAT02` | atomic | Windows DX12 matrix passes |
| AR05-G5 | `P1-PLAT02` | atomic | macOS Apple-silicon matrix passes |
| AR05-G6 | `P1-PLAT02` | atomic | Support manifest includes only passed platforms |
| AR06-G1 | `P1-INPUT01` | atomic | IME/focus property tests pass |
| AR06-G2 | `P1-IME01` | atomic | Physical IME matrix passes |
| AR06-G3 | `P1-A11Y01` | atomic | AccessKit consumer tests pass |
| AR06-G4 | `P1-A11Y-AT01` | atomic | Physical AT workflows pass after IME |
| AR06-G5 | `P1-A11Y-BENCH01` | atomic | AT-on callback/frame/idle proof passes |
| AR06-G6 | `P1-A11Y-LIST01` | atomic | Accessible 10,000-row representation tested |
| AR07-G1 | `P1-REL01` | atomic | Wheel/sdist build and content audit pass |
| AR07-G2 | `P1-REL02` | atomic | Same-wheel CPython matrix passes |
| AR07-G3 | `P1-TST01` | `AR07-G3.typing-contract`, `AR07-G3.stubtest` | Typing-contract and stubtest sub-gates pass |
| AR07-G4 | `P1-REL02` | `AR07-G4.platform-runtime`, `AR07-G4.same-wheel-callbacks` | Platform-runtime and same-wheel callback sub-gates pass |
| AR07-G5 | `P1-REL02` | atomic | Reproducible bundle passes; signing remains blocked |
| AR08-G1 | `P1-BENCH01` | `AR08-G1.interface`, `AR08-G1.scenes-collectors` | Interface and scene/collector sub-gates pass |
| AR08-G2 | `P1-BENCH01` | atomic | Immutable ten-process baseline passes |
| AR08-G3 | `P1-PERF01` | atomic | Zero counters and separate-interpreter diagnostics pass |
| AR08-G4 | `P1-PERF02` | atomic | Presented/input qualification passes or is inconclusive |
| AR08-G5 | `P1-PERF02` | atomic | Actual compare command enforces >10% diagnosis rule |
| AR08-G6 | `P1-CERT-GATE01` | `AR08-G6.approval`, `AR08-G6.measurements` | Measurement and OQ-02 approval sub-gates pass |
| AR09-G1 | `P1-PR-AUDIT01` | atomic | Per-PR provenance audit prevents unapproved merge |
| AR09-G2 | `P1-LIC02` | atomic | Artifact license/advisory closure passes |
| AR09-G3 | `P1-LIC02` | atomic | Notice/content audit matches SBOM |
| AR09-G4 | `P1-WAYLAND-GATE01` | `AR09-G4.wayland-disposition`, `AR09-G4.artifact-audit` | Artifact-audit and Wayland-disposition sub-gates pass |
| AR09-G5 | `P1-LIC01` | atomic | Source-exception workflow rejects incomplete records |
| AR10-G1 | `P1-LICENSE-CLOSE01` | `AR10-G1.artifact-metadata`, `AR10-G1.owner-notice` | Artifact-metadata and owner-notice sub-gates pass |
| AR10-G2 | `P1-LIC02` | atomic | Artifact contents/SBOM agree |
| AR10-G3 | `P1-PR-AUDIT01` | atomic | Per-PR authored-scope audit passes |
| AR10-G4 | `P1-DOC-FINAL01` | atomic | Final docs link only current evidence or blocked claims |

## 15. Plan completion

This revision is complete only when graph/handoff validators and negative tests pass, exact output is written to `evidence/P0-PL01/validation-attempt-3.txt`, `P0-PL01` is done at attempt 3 and the Red-Team attempt-3 handoff contains every Part 3 field. No Phase 1 task or `P0-AP01` is authorized by this plan.
