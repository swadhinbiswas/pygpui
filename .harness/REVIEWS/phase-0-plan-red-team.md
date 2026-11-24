# Phase 0 plan — adversarial Red-Team review

- Task: `P0-RT01`, attempt 1
- Reviewer: Red-Team-Planner
- Date: 2026-11-24 UTC
- Reviewed baseline: `81f794d1f23b4f7741db8dbc03775b5ecf20ae0b` (`main` and `origin/main`)
- Accepted ADR baseline: `5ce026d`
- Verdict: **changes requested — not approvable**
- **Blocking findings: 11**

## 1. Scope and method

I read `.harness/STATE.md`, the assigned Orchestrator handoff, `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `evidence/P0-PL01/validation.txt`, the Planner handoff, `.harness/DECISIONS/README.md`, all ten ADRs, `.harness/REVIEWS/phase-0-research-skeptic.md`, `.harness/PROCESS.md`, and `.harness/OPEN_QUESTIONS.md`.

I did not rely on the Planner's validation summary. I independently:

1. Parsed `TASKS.json`; checked unique IDs, dependency resolution, DFS cycles, topological order, required Phase 1 fields, initial status/attempts, and transitive `P0-AP01` gating.
2. Extracted task order, owners, dependencies, sizes, and ranges from the plan and compared them with JSON.
3. Extracted all `ARxx-Gn` identifiers from the ten ADRs and compared them with plan and task mappings.
4. Inspected the committed tree and working tree for every named script, test target, manifest, wheel, and evidence producer; compared those artifacts with task write scopes and dependencies.
5. Traced the proposed wave-5 interfaces and the Counter/review/merge path for hidden serialization, missing producers, and deadlocks.
6. Checked the real remote, tracking branch, authenticated `gh` identity/scopes, repository permission, branch protection, rulesets, PR list, and Git credential helper.
7. Performed static falsification of acceptance criteria: could a task be marked done without the evidence its wording claims?

No feature code, wheel, native window, benchmark harness, or gate script exists at this baseline, so runtime/platform/performance execution was not possible. The findings below are plan-level defects, not claims that future implementation will fail.

## 2. Machine-checkable graph checks

Independent Python audit of `.harness/TASKS.json` and the plan:

```text
JSON_PARSE=PASS
TASKS total=46 unique=46 phase1=32
UNIQUE_IDS=PASS duplicates=[]
DEPS_RESOLVE=PASS checked=89 missing=[]
CYCLES=PASS count=0
TOPOLOGICAL_ORDER=PASS levels=24
PHASE1_FIELDS=PASS
PHASE1_INITIAL_STATE=PASS
PHASE1_AP01_GATE=PASS checked=32
PLAN_TASK_ORDER=PASS plan=32 json=32
PLAN_JSON_METADATA=PASS checked=32
ADR_GATES source=52 unique=52 plan=52 unique=52
ADR_GATE_COVERAGE=PASS
ADR_GATE_MISSING_SOURCE_TO_PLAN=[]
ADR_GATE_MISSING_SOURCE_TO_TASKS=[]
TASK_GATE_MAPPINGS=71 unique=52
```

Interpretation:

- The graph is structurally well-formed and acyclic. All 32 Phase 1 tasks are transitively gated by `P0-AP01`.
- All 52 ADR gate identifiers remain present. Identifier coverage does **not** establish that the obligations are executable or intact; see B-09.
- The Planner's counts are reproducible. Its validation artifact is not itself reproducible because the validator it names is absent; see B-01.
- Plan/JSON owner, dependency, size, and range metadata agree. Plan deliverable labels are intentionally shorter than JSON titles and are not treated as mismatches.

## 3. Task/wave findings table

| Wave / tasks | Independent assessment | Findings |
|---|---|---|
| 0 — `P1-GOV01` | Gate and initial state are correct, but its first acceptance command names a nonexistent validator. Hardware/OQ readiness is recorded but not represented as dispatch prerequisites. | B-01; N-01 |
| 1 — `P1-ARCH01`, `P1-LIC01` | Workspace ownership is clear. The claimed parallel wave is not executable: `P1-LIC01` requires `cargo metadata --no-deps` from manifests only `P1-ARCH01` produces. The architecture test is asserted but never invoked by a named command. | B-07; B-08 |
| 2 — `P1-PROTO01`, `P1-CI01` | Protocol tests have an owner. Protocol's source audit is unnamed. The red-main drill cannot create a red `origin/main` without violating the stated merge policy. | B-01; B-05; B-08 |
| 3 — `P1-API01`, `P1-BENCH00` | Public API/stub ownership is good. No locked Python development environment or `pyproject.toml` producer exists. `P1-BENCH00` freezes only a contract; later `boundary`, `compare`, `input`, and `report` implementations are not explicitly owned. | B-03; B-06 |
| 4 — `P1-CONREV01` | External contract review is explicit, but its checker is unowned and the freeze omits internal Rust traits/hand-offs. The review branch itself has no independent review/test gate. | B-01; B-02; B-04 |
| 5a — `P1-CORE01`, `P1-SCENE01`, `P1-TEXT01`, `P1-INPUT01`, `P1-RENDER01` | Core queue work is independently testable. Scene/text/input/render are dispatched in parallel without frozen text-measurement, paint/scene, hit/focus, or instrumentation contracts and without producer dependencies. | B-02; B-06; B-08 |
| 5b — `P1-CORE02`, `P1-PLATFORM01`, `P1-PY01` | Handle work is serialized correctly. Platform lacks core/scene/text/input dependencies; Python binding lacks platform/scene dependencies. Their acceptance criteria require integrations those branches cannot contain. | B-02 |
| 6 — `P1-SLICE01` | The integration join is correctly placed after all modules, but `counter_headless` has no explicit producer, no local wheel exists for the next wave, and "done after merge" conflicts with the later final-merge task. | B-03; B-04; B-08 |
| 7a — `P1-TST01`, `P1-PLAT01` | Both require a clean installed wheel. No predecessor builds one; `P1-REL01` is later and depends on the merge these tests are meant to gate. | B-03 |
| 7b/7c — `P1-REV01`, `P1-INT01` | Safety review is substantive, but the Counter PR may already have been merged under the general done rule. Rollback tooling is unowned and the premerge tag has no creation step. | B-04; B-05 |
| Later — `P1-PERF01`, `P1-A11Y01` | Callback instrumentation requires production edits outside `P1-PERF01` scope. `P1-A11Y01` needs Cargo/lock and platform window-lifecycle edits outside its scope, and claims an ADR 0008 regression gate before the benchmark tasks exist. | B-06; B-07; B-09 |
| Later — `P1-REL01`, `P1-PLAT02` | Release scripts have an owner, but root Python packaging metadata does not. Platform scripts/support-manifest generator are unowned, and physical runner readiness is not a dependency. | B-01; B-03; B-07; N-01 |
| Later — `P1-BENCH01`, `P1-PERF02` | Scene/baseline work is owned. Collector qualification is unnamed; `P1-PERF02` cannot wire CLI commands outside its `analysis/**` scope and does not execute the actual regression gate required by AR08-G5. | B-01; B-06; B-08; B-09 |
| Later — `P1-IME01`, `P1-A11Y02` | IME tooling is unowned. AT testing requires text input with IME but has no `P1-IME01` dependency. The 10,000-row accessible representation hides production design/implementation inside a 3–5 day test bundle. | B-01; B-10; N-01 |
| Later — `P1-LIC02`, `P1-DOC01`, `P1-REL02` | Artifact audit tooling is owned. Documentation is scheduled before the final performance/IME/AT/license evidence it must describe, and no final documentation update exists. Same-wheel callback proof is not tied to artifact hashes. | B-09; B-11 |

## 4. Severity-tagged findings

### [BLOCKING] B-01 — Required gate tooling has no producer; the Planner validation cannot be rerun

**References:** `.harness/TASKS.json:273`, `:450`, `:500`, `:526`, `:720`, `:769`, `:864`, `:938`, `:961`, `:1010`; task write scopes at `:268`, `:370`, `:445`, `:469`, `:493`, `:517`, `:543`, `:567`, `:590`, `:615`, `:640`, `:715`, `:738`, `:762`, `:786`, `:810`, `:834`, `:859`, `:884`, `:908`, `:933`, `:956`, `:979`, `:1004`, `:1028`.

The committed tree at `81f794d` contains no `.harness/scripts/` or `tools/` directory. In particular:

- `.harness/scripts/validate_phase1_graph.py` — invoked by `P1-GOV01`; no task may create it.
- `.harness/scripts/check_contract_freeze.py` — invoked by `P1-CONREV01`; its scope contains only the review and freeze JSON.
- `.harness/scripts/platform_gate.py` — invoked by `P1-PLAT01` and `P1-PLAT02`; neither scope contains it.
- `.harness/scripts/ime_gate.py`, `.harness/scripts/at_gate.py` — invoked by `P1-IME01` and `P1-A11Y02`; neither scope contains them.
- `tools/audit/slotmap_policy.py`, `tools/audit/map_rebuild_safety.py` — invoked by `P1-CORE02` and `P1-SCENE01`; no owner.
- `tools/ci/rollback_drill.py` — invoked by `P1-INT01`; `P1-CI01` owns `tools/ci/**` but has no deliverable for it, and `P1-INT01` cannot create it.
- `tools/docs/audit_claims.py` — invoked by `P1-DOC01`; its scope is only `README.md` and `docs/**`.

Consequently `P1-GOV01` cannot satisfy its first criterion, and `evidence/P0-PL01/validation.txt:1-12` records results from an uncommitted, unreproducible validation path.

**Required revision:** Add an owned gate-tool foundation task before all consumers, or explicitly extend the appropriate write scopes and acceptance criteria so each script is created and negatively tested by its owner. Commit or otherwise archive the exact validator used to produce `evidence/P0-PL01/validation.txt`, and make `P1-GOV01` invoke that committed validator.

---

### [BLOCKING] B-02 — Internal Rust contracts are not frozen; wave 5 has missing producer dependencies

**References:** `.harness/PLANS/phase-1-vertical-slice.md:19`, `:63`, `:67`, `:129`; `.harness/TASKS.json:512`, `:538`, `:562`, `:589`, `:610`, `:635`; ADR 0003 `.harness/DECISIONS/0003-public-python-api-and-module-boundaries.md:62-74`.

The plan says shared contracts are frozen before parallel implementation, but the freeze covers snapshot/command/event/error types, public Python/stubs, and benchmark interfaces. It does not produce or hash internal Rust contracts for:

- text measurement/shaping and glyph-atlas hand-off;
- scene-to-render paint input;
- hit/focus trees consumed by input routing;
- platform event/surface orchestration consumed by core/scene/input;
- native instrumentation counters and sentinels.

The ownership table asserts a “Frozen text trait” at plan line 129, but no task creates that trait or includes it in `P1-CONREV01`'s freeze at `.harness/TASKS.json:450`.

The dependency consequences are concrete:

- `P1-RENDER01` depends only on `P1-CONREV01`, yet claims text draws and a deterministic scene hash (`TASKS.json:595-597`) without `P1-TEXT01` or a frozen paint/text hand-off.
- `P1-INPUT01` depends only on `P1-CONREV01`, yet must prove click/Enter/Space routing (`TASKS.json:574`) without the scene hit/focus tree.
- `P1-PLATFORM01` depends only on `P1-CONREV01` and `P1-RENDER01` (`TASKS.json:610`), yet its native turn must route input, accept snapshots, and rebuild (`:622`), requiring core/scene/text/input implementations or frozen test adapters.
- `P1-PY01` depends only on `P1-CONREV01` and `P1-CORE02` (`TASKS.json:635`), yet must test `App.run()` on the platform main thread (`:646`) without `P1-PLATFORM01` or scene integration.

**Required revision:** Add a `P1-RUSTCONTRACT01`-style task before wave 5 that defines and tests these internal traits/value hand-offs, gives each one an owner, and includes their hashes in `P1-CONREV01`. Then add real dependencies (for example scene↔text measurement, render←scene/text hand-off, input←scene hit/focus, platform←core/scene/input/render, Python←platform/scene) or provide compile-tested adapters that make the claimed parallel work genuinely independent.

---

### [BLOCKING] B-03 — Installed-wheel tests have no wheel producer; Python packaging and dev environments are unowned

**References:** `.harness/TASKS.json:695`, `:720`, `:829`, `:1023`; `P1-ARCH01` scope at `:293`; `P1-REL01` scope at `:834`.

`P1-TST01` and `P1-PLAT01` both require a clean local installed wheel, but no predecessor produces a wheel. `P1-REL01` is the first explicit wheel-build task and depends on `P1-INT01`; `P1-INT01` depends on `P1-REV01`, which depends on `P1-TST01`. Simply adding `P1-REL01` as a predecessor would create a cycle.

There is also no producer for root `pyproject.toml`, Python package metadata, a locked development environment, mypy 2.4.1, pytest/Hypothesis pins, or a local wheel-build recipe. `P1-ARCH01` writes only Cargo manifests/lock/toolchain. On the review host, `maturin 1.16.0` and pytest exist, but `mypy` and `stubtest` do not; ambient tools are not a reproducible plan.

**Required revision:** Add a `P1-PACK01`/`P1-LOCALWHEEL01` task after the integrated Counter branch and before `P1-TST01`/`P1-PLAT01`. It must own `pyproject.toml`, package metadata, the locked dev environment, and a local Linux wheel plus SHA-256 manifest. Make both test tasks depend on it. Keep native candidate wheels in `P1-REL01` as a separate later gate.

---

### [BLOCKING] B-04 — The done/merge model deadlocks wave 7 and does not schedule independent review for every branch

**References:** `.harness/PLANS/phase-1-vertical-slice.md:37`, `:49-50`, `:54`, `:64-65`; `.harness/TASKS.json:660`, `:685`, `:710`, `:733`, `:757`; `.harness/PROCESS.md:35-37`, `:56-57`.

Plan line 37 says a task is done only after the Integrator records its reviewed PR merge. Plan line 54 says a wave starts only after every predecessor is done. Under those rules, `P1-SLICE01` must already be merged before `P1-TST01`, `P1-PLAT01`, and `P1-REV01` start. But wave 7 and `P1-INT01` say the Integrator later merges the reviewed Counter PR (`TASKS.json:767`). Either:

- `P1-SLICE01` is done/merged first, leaving no Counter PR for `P1-INT01`; or
- `P1-SLICE01` remains incomplete, so wave 7 cannot legally start.

Separately, the process requires a different Reviewer and Test-Engineer for every build branch, but the graph contains explicit independent review/test tasks only for the contract and final Counter slice. There are no scheduled review/test artifacts, owners, dependencies, or estimates for the other task branches, including `P1-CONREV01`, `P1-REV01`, `P1-TST01`, `P1-PLAT01`, release tasks, and Integrator-authored tasks.

The real remote check confirms `origin=https://github.com/swadhinbiswas/pygpui.git`, `main=origin/main=81f794d`, authenticated account `swadhinbiswas` with `repo` scope and admin permission. However, `main` is unprotected and the repository has no rulesets. The only authenticated identity available in this workspace is `swadhinbiswas`; unless separate credentials are supplied, agent sessions share that identity, so GitHub approval/merge metadata cannot by itself prove role separation.

**Required revision:** Define explicit branch states such as `implemented`, `independently verified`, and `merged`, and state which state satisfies a task dependency. Resolve whether wave 7 reviews one still-open Counter PR or separate post-merge test/review PRs. Add a generic per-branch review/test/Integrator gate with named evidence, distinct reviewer identity, and merge record, or add explicit review tasks for every branch. If GitHub approvals are required, provide distinct identities or branch protection; otherwise define signed/harness review evidence and an Integrator checklist that is checked before merge.

---

### [BLOCKING] B-05 — The red-main and rollback drills are not executable under the merge policy

**References:** `.harness/TASKS.json:376-377`, `:769`; `.harness/PLANS/phase-1-vertical-slice.md:167-173`; `.harness/PROCESS.md:56-57`, `:63-65`.

`P1-CI01` must inject a failing commit, open a PR, and restore green `origin/main`. Under the stated policy, the only ways to make the real `origin/main` red are a direct push to `main` or merging a knowingly red PR. Both are forbidden. A drill that never reddens `main` does not test red-main recovery; a drill that does redden it violates the policy it is meant to rehearse.

Rollback is also incomplete:

- `tools/ci/rollback_drill.py` has no producer (B-01).
- No task creates the pre-freeze or `phase1/counter-premerge` tag before the relevant merge.
- `P1-INT01` cannot create the rollback script under its write scope.
- “Restoring the reviewed merge” is not an exact revert/revert-of-revert or re-merge procedure with commands and expected hashes.

**Required revision:** Run fault injection against a disposable bare remote, temporary fork, or isolated fixture repository, with an explicit statement that production `origin/main` is untouched. If a bounded break-glass rehearsal on the real remote is desired, obtain and record an Orchestrator exception with exact safety controls. Add tag-creation acceptance criteria, assign the rollback script to an owner before `P1-INT01`, and specify the full revert → gate → restore sequence with archived PRs, tags, and green hashes.

---

### [BLOCKING] B-06 — Native instrumentation and benchmark subcommands lack producers and write scopes

**References:** `.harness/TASKS.json:425-428`, `:786-794`, `:817`, `:884-892`, `:908-916`; ADR 0008 `.harness/DECISIONS/0008-benchmark-certification-and-regression-gates.md:19-24`, `:53-58`.

`P1-PERF01` must prove native callback/frame-entry/GIL/attachment/finalizer counters and deliberate sentinels, but its write scope contains only benchmarks, tests, and evidence. Adding authoritative counters to the frame closure requires edits in core, scene, render, platform, and Python binding crates. No module task requires those hooks, and no instrumentation contract is frozen.

Likewise:

- `python -m pygpui_bench boundary verify` is required by `P1-PERF01`, but `P1-BENCH00` only requires `--help` and contract-only scene verification.
- `compare`, `input qualify`, and `report` are required by `P1-PERF02`, but its write scope is only `pygpui_bench/analysis/**`; CLI wiring outside `analysis/**` is not owned.
- Collector qualification is required by `P1-BENCH01` but has no named command or producer.

**Required revision:** Include counter/sentinel interfaces in the internal contract freeze and add production instrumentation work with explicit crate scopes before `P1-PERF01`. Assign and test each benchmark subcommand in an owned task, including negative fixtures for disabled counters, invalid collectors, missing raw artifacts, and wrong endpoints. Add an independently reviewed instrumentation audit.

---

### [BLOCKING] B-07 — Manifest and integration edits fall outside owner scopes; wave 1 is not actually parallel

**References:** `.harness/PLANS/phase-1-vertical-slice.md:59`, `:124`, `:131`; `.harness/TASKS.json:314`, `:326`, `:810`, `:816-818`; ADR 0006 `.harness/DECISIONS/0006-input-ime-focus-and-accessibility-ownership.md:20-21`.

`P1-LIC01` is dispatched in parallel with `P1-ARCH01`, but its criterion at `TASKS.json:326` runs `cargo metadata --no-deps` and audits workspace/PEP 639 metadata. The manifests it audits are produced only by `P1-ARCH01`, and `P1-LIC01` has no dependency on it.

`P1-A11Y01` must add exact AccessKit dependencies and enforce create-invisible → attach-adapter → show, but its scope contains only scene/platform `a11y/**` directories and tests. It cannot edit crate manifests, `Cargo.lock`, or the platform window-creation/orchestration code outside `a11y/**`. The root manifest/lock owner is the Integrator, with no dependency or handoff task for those edits.

**Required revision:** Either make `P1-LIC01` depend on `P1-ARCH01` (and abandon the claimed wave-1 parallelism), or split repository license baseline from workspace metadata validation. Add an Integrator-owned manifest/lock update task for AccessKit and rerun architecture, lock, and license gates. Expand or split the platform lifecycle wiring scope so the invisible/attach/show sequence can actually be implemented and reviewed.

---

### [BLOCKING] B-08 — Several acceptance criteria can pass without the claimed evidence

**References:** `.harness/TASKS.json:298-301`, `:352`, `:550`, `:598`, `:623`, `:791-794`, `:816`, `:868`, `:1009`, `:1035`.

Examples of falsifiable acceptance gaps:

- `P1-ARCH01` says `cargo metadata` exits zero “and an architecture test asserts,” but never runs the architecture test. The task can pass with no test target or a non-executed test.
- Multiple criteria say “a source audit exits zero” without naming a command, script, input set, or output artifact.
- `P1-PLAT02` names no support-manifest generator command or schema.
- `P1-DOC01` refers to a command “recorded in docs/Makefile” instead of naming a target; a placeholder quickstart can satisfy it.
- `P1-REL02` says “a reproducibility check exits zero” without a command or defined equality criteria.
- `P1-PERF01` requires `boundary verify` to exit zero while also saying failed/disabled counters make a run inconclusive. Unless inconclusive is a nonzero outcome for this proof task, the callback-free gate can be marked done without zero counters.

**Required revision:** Replace narrative audits with exact commands, input paths, output artifacts, and expected exit codes. Add negative fixtures proving each gate fails on missing/disabled evidence. Require proof tasks such as `P1-PERF01` to exit nonzero on inconclusive/disabled counters, and record structured per-gate results rather than a single task-level “done.”

---

### [BLOCKING] B-09 — All 52 gate IDs are present, but several ADR obligations are not intact

**References:** ADR 0006 `.harness/DECISIONS/0006-input-ime-focus-and-accessibility-ownership.md:52`; ADR 0007 `0007-abi3-strict-typing-wheel-and-release-evidence.md:51`; ADR 0008 `0008-benchmark-certification-and-regression-gates.md:55-58`; ADR 0009 `0009-clean-room-license-and-provenance-policy.md:47`; ADR 0010 `0010-license-pygpui-under-apache-2-0.md:45-47`; `.harness/TASKS.json:781`, `:805`, `:817`, `:913`, `:1034`.

Identifier coverage is 52/52, but these obligations are weakened or unexecutable:

1. **AR06-G5:** `P1-A11Y01` claims enabling AT does not regress ADR 0008 frame/idle gates, but it runs before `P1-BENCH01`/`P1-PERF02`; `P1-PERF01` runs before the adapter exists. No task observes both AT enabled and the qualified benchmark gates.
2. **AR07-G4:** `P1-REL02` says it verifies callback gates, but no criterion reruns the callback suite on the exact `P1-REL01` wheel or checks artifact-hash equality with the evidence. Pre-wheel `P1-PERF01` evidence is not same-artifact evidence.
3. **AR08-G3:** the ADR requires the Python 3.11 fallback and a separate-interpreter matrix. `P1-PERF01:794` covers 3.11 versus 3.12+ profiling but does not exercise separately installed GIL-enabled/free-threaded interpreters.
4. **AR08-G5:** the ADR requires the actual compare command to reject >10% until profiling/diagnosis is linked. `P1-PERF02:913` runs only `compare --help` and unit tests; there is no end-to-end fixture proving the command's gate behavior.
5. **AR09-G1 / AR10-G3:** repository provenance/authored-file audits occur in `P1-LIC01`, before most source exists. `P1-CI01`'s local gate does not run those audits, so later PRs can merge unaudited copied/adapted or authored files.
6. **AR10-G1:** `P1-LIC01:327` explicitly permits a missing owner notice while keeping distribution blocked, yet the task lists AR10-G1 as a gate. A task can be “done” without that gate passing unless gate status is separate from task status.

**Required revision:** Keep the ADRs immutable and repair the plan/tasks: add a post-benchmark AT-on regression gate; add a same-wheel callback rerun with hash equality; add the separate-interpreter diagnostic matrix; add an actual compare-gate integration fixture; run provenance/authored-file audits on every PR; and represent gate outcomes explicitly so a task cannot be done while a listed gate is unmet.

---

### [BLOCKING] B-10 — `P1-A11Y02` tests IME text input without depending on physical IME evidence

**References:** `.harness/TASKS.json:928`, `:951`, `:961`; `.harness/PLANS/phase-1-vertical-slice.md:102-103`.

`P1-A11Y02` requires VoiceOver/Narrator/Orca workflows including “text input with IME,” but its dependencies omit `P1-IME01`. Both tasks are downstream of `P1-PLAT02`, so they can run concurrently and the AT bundle can finish without the cited physical IME matrix.

The same 3–5 day task also designs/implements the 10,000-row accessible representation in production code and runs physical AT workflows on three platforms. That is hidden implementation plus certification work, not a small test bundle.

**Required revision:** Add `P1-A11Y02 → P1-IME01`, or split IME-dependent AT cases into a later task that requires archived IME evidence. Split accessible-list design/implementation from physical AT certification and estimate them separately.

---

### [BLOCKING] B-11 — Final documentation/evidence ordering and artifact invalidation are not represented

**References:** `.harness/TASKS.json:999`, `:1009-1011`, `:1023`; `.harness/PLANS/phase-1-vertical-slice.md:104-106`, `:116`, `:171`.

`P1-DOC01` depends only on `P1-API01` and `P1-INT01`, but must maintain the claim register for performance, platform, IME, accessibility, license, and signing evidence. Most of that evidence is produced later by `P1-PLAT02`, `P1-PERF02`, `P1-IME01`, `P1-A11Y02`, and `P1-LIC02`. `P1-REL02` then depends on both `P1-DOC01` and those later tasks, but no task updates the docs/claim register after the evidence arrives.

The plan also says repaired artifacts must be regenerated and re-audited, but the graph has no invalidation/re-run edges. If `P1-REL01` is repaired after `P1-LIC02` or platform/performance evidence, downstream evidence can refer to stale hashes while remaining marked done.

**Required revision:** Split initial Counter documentation from final evidence/claim closure. Add a final docs task after performance/IME/AT/license evidence and before `P1-REL02`. Define immutable artifact IDs/hashes and require all dependent platform, callback, benchmark, and license gates to rerun when an artifact changes.

## 5. Missing dependency / tool / artifact list

### 5.1 Missing or incorrect dependencies

| Consumer | Missing producer / prerequisite | Required correction |
|---|---|---|
| `P1-LIC01` | `P1-ARCH01` manifests for metadata audit | Add dependency or split the metadata gate. |
| Wave 5 consumers | Internal Rust contract task | Add and freeze text, paint, hit/focus, platform, and instrumentation hand-offs. |
| `P1-SCENE01` / `P1-RENDER01` | Text measurement/atlas hand-off | Depend on an owned contract/implementation or compile-tested adapter. |
| `P1-INPUT01` | Scene hit/focus tree | Add dependency or frozen adapter plus final integration dependency. |
| `P1-PLATFORM01` | Core/scene/text/input implementations | Add dependencies; current branch cannot satisfy its native-turn criterion. |
| `P1-PY01` | Platform/scene integration | Add dependencies; current branch cannot test main-thread `App.run()`. |
| `P1-TST01`, `P1-PLAT01` | Local installed wheel | Add `P1-PACK01`/`P1-LOCALWHEEL01` before both. |
| `P1-PERF01` | Production counter/sentinel hooks | Add instrumentation tasks/scopes before proof. |
| `P1-PERF01`, `P1-PERF02` | Benchmark `boundary`/`compare`/`input`/`report` implementations | Assign CLI implementation and integration tests. |
| `P1-A11Y01` | Cargo/lock and platform lifecycle edits | Add Integrator manifest task and wiring scope/dependency. |
| AR06-G5 final proof | AT enabled plus qualified benchmark | Add a later AT-on benchmark gate. |
| AR07-G4 | Callback evidence on exact release wheel | Add same-artifact rerun/hash check. |
| `P1-A11Y02` | `P1-IME01` physical evidence | Add dependency or split IME-dependent AT cases. |
| Final claim register | Final performance/IME/AT/license evidence | Add final docs closure before `P1-REL02`. |
| Every task branch | Independent review/test and Integrator merge evidence | Add a per-branch verification/merge gate. |

### 5.2 Unowned tools and artifacts

| Artifact | Invoked by | Current status |
|---|---|---|
| `.harness/scripts/validate_phase1_graph.py` | `P1-GOV01` | Missing; no write scope. |
| `.harness/scripts/check_contract_freeze.py` | `P1-CONREV01` | Missing; no write scope. |
| `.harness/scripts/platform_gate.py` | `P1-PLAT01`, `P1-PLAT02` | Missing; no write scope. |
| `.harness/scripts/ime_gate.py` | `P1-IME01` | Missing; no write scope. |
| `.harness/scripts/at_gate.py` | `P1-A11Y02` | Missing; no write scope. |
| `tools/audit/slotmap_policy.py` | `P1-CORE02` | Missing; no owner. |
| `tools/audit/map_rebuild_safety.py` | `P1-SCENE01` | Missing; no owner. |
| `tools/ci/rollback_drill.py` | `P1-INT01` | Missing; no producer in `P1-CI01`. |
| `tools/docs/audit_claims.py` | `P1-DOC01` | Missing; outside scope. |
| `crates/pygpui-platform/tests/counter_headless.rs` | `P1-SLICE01` | No explicit producer or scope. |
| `pyproject.toml` / Python metadata | API, typing, maturin, packaging | No task or write scope. |
| Locked Python dev environment | mypy/pytest/Hypothesis/stubtest | No task or artifact. |
| Local Linux wheel before wave 7 | `P1-TST01`, `P1-PLAT01` | No producer. |
| Native counter/sentinel hooks | `P1-PERF01`, `P1-A11Y01` | No production scope or interface owner. |
| `pygpui_bench boundary` implementation | `P1-PERF01` | Not required from `P1-BENCH00`. |
| `pygpui_bench compare/input/report` wiring | `P1-PERF02` | Outside `analysis/**` scope. |
| Support-manifest generator | `P1-PLAT02` | Unnamed and unowned. |
| Pre-freeze and Counter premerge tags | Contract/Counter rollback | No creation task/criterion. |
| Per-branch review/test records | Every build PR | No general producer. |

## 6. Unsafe parallelization and shared-file analysis

### Safe or conditionally safe boundaries

- Protocol, Python facade, benchmark contract, CI scripts, and separate Rust crate directories have mostly disjoint literal scopes.
- Evidence directories are task-specific.
- The four literal scope overlaps found by the audit are sequential in the dependency graph: `P1-LIC01`/`P1-LIC02`, `P1-API01`/`P1-TST01`, `P1-BENCH00`/`P1-BENCH01`, and `P1-REL01`/`P1-REL02`. They are safe only if the earlier task is merged before the later branch starts.

### Unsafe boundaries

- **Wave 1:** `P1-LIC01` and `P1-ARCH01` are called parallel, but license metadata validation needs the workspace manifests.
- **Wave 5:** text/scene/input/render/platform/Python work shares unfrozen internal contracts and missing producer dependencies.
- **Manifests:** the plan forbids parallel manifest edits, but `P1-A11Y01` requires manifest/lock changes it cannot make. Root `pyproject.toml` has no owner at all.
- **Instrumentation:** `P1-PERF01` and `P1-A11Y01` require cross-crate production hooks outside their scopes.
- **Control plane:** every branch must append `.harness/LOG.md` and write a handoff, while the Orchestrator updates `.harness/STATE.md` and `.harness/TASKS.json`. One-line appends reduce but do not eliminate Git conflicts; no serialization/control-plane merge procedure is defined.
- **Post-freeze changes:** returning to `P1-CONREV01` is stated, but there is no dependency invalidation rule for already merged consumers or artifact evidence.

## 7. Acceptance-criteria falsification tests

| Test | Expected if the plan is sound | Current result |
|---|---|---|
| Run `python3 .harness/scripts/validate_phase1_graph.py --baseline 5ce026d` | Exit zero from a committed, owned validator. | **Fails:** file does not exist. |
| Dispatch wave 1 exactly as written and run `P1-LIC01`'s metadata criterion. | Both branches have required inputs. | **Fails:** `P1-LIC01` has no `Cargo.toml` producer in its branch. |
| Start wave 5 from the freeze and compile render/input/platform/Python consumers. | Frozen internal traits and producer code exist. | **Fails:** no internal trait task/hash or required dependencies exist. |
| Complete `P1-SLICE01`, then start `P1-TST01` and install the local wheel. | A predecessor-produced wheel is installable. | **Fails:** no `pyproject.toml` or local wheel task exists. |
| Execute `P1-CI01`'s red-main drill on real `origin/main` without policy exceptions. | Main becomes red and is recovered without forbidden operations. | **Impossible:** requires direct push or red PR merge. |
| Mark `P1-SLICE01` done under plan line 37, then execute wave 7 and `P1-INT01`. | The final merge has a PR to merge. | **Deadlock:** Counter PR is already merged, or wave 7 started from an undone predecessor. |
| Run only `P1-ARCH01`'s named `cargo metadata` command and omit the architecture test. | Gate fails because AR03-G5 requires the test. | **Can pass:** no command executes the test. |
| Return disabled counters/inconclusive from `boundary verify` with exit zero. | `P1-PERF01` cannot be done. | **Can pass under current wording.** |
| Try to evidence AR06-G5 after `P1-PERF01` and `P1-A11Y01`. | One task observes AT enabled under qualified frame/idle gates. | **Fails:** the two features never coexist with the benchmark gates. |
| Feed pre-wheel `P1-PERF01` evidence to `P1-REL02` without rerunning callbacks. | AR07-G4 rejects it unless artifact hashes match. | **Can pass:** no same-wheel rerun/hash criterion exists. |
| Run AR08-G3's separate-interpreter matrix. | GIL-enabled and free-threaded interpreters are launched separately. | **Missing:** no task criterion requires it. |
| Run only `compare --help` plus ABBA unit tests. | AR08-G5 requires an actual >10% rejection/diagnosis integration check. | **Can satisfy the task without the gate behavior.** |
| Copy/adapt source in a later PR after `P1-LIC01` is done. | A pre-merge provenance audit blocks it. | **Can merge:** no per-PR audit is scheduled. |
| Run `P1-A11Y02` without `P1-IME01`. | AT text-input-with-IME evidence requires physical IME evidence. | **Can pass:** dependency is absent. |
| Finish `P1-DOC01`, then produce final performance/IME/AT/license evidence. | Final claim register links the passing evidence. | **No task performs the final update.** |
| Execute rollback using only listed task commands. | Tags, revert PR, gate rerun, restore, and green hash are produced. | **Fails:** script/tag creation and exact restore procedure are absent. |

## 8. Estimate, rollback, and PR-workflow assessment

### Estimates

- S/M/L ranges are honest about being ideal engineer-days and explicitly exclude hardware, counsel, user decisions, and signing credentials (`plan:71`, `:143-145`).
- Summing the stated dependency path gives approximately **33–54 ideal engineer-days to `P1-INT01`** and **60–91 to `P1-REL02`**, before review staffing, merge queues, hardware access, counsel, or user waits. These aggregates are not shown in the plan.
- `P1-A11Y02`'s 3–5 days hides accessible-list production implementation plus three-platform physical AT testing. `P1-REL02`'s 6–8 days hides 15 OS×CPython clean-install lanes, reproducibility work, and evidence reconciliation.
- `P1-GOV01` records availability but no task owns procurement, user approval, counsel response, or a maximum wait/escalation path.

### Rollback

- Contract, Counter, benchmark, platform, and artifact rollback intents are documented.
- Execution is not yet planned: missing script producer, missing tag creation, ambiguous restore sequence, and the red-main policy contradiction are blocking (B-05).
- Artifact repair can invalidate downstream evidence without graph re-run edges (B-11).

### Real GitHub workflow

Verified observations:

```text
origin fetch/push = https://github.com/swadhinbiswas/pygpui.git
main = origin/main = 81f794d1f23b4f7741db8dbc03775b5ecf20ae0b
gh account = swadhinbiswas; active; token scopes include repo
viewer permission = ADMIN
branch protection = none (HTTP 404)
rulesets = []
open/historical PRs = none
Git HTTPS credential helper = gh auth git-credential
```

The mechanical branch/push/PR path is viable. Role separation is not technically enforced: one account, no protection, and no rulesets. The plan's harness-only enforcement is acceptable only after B-04 defines per-branch review evidence and Integrator checks. OQ-15's deferral of branch protection does not remove the need for that procedural evidence.

## 9. Nonblocking findings

### [HIGH, NONBLOCKING] N-01 — External waits are acknowledged but not scheduled

`plan:99-104`, `:118`, `:144` correctly disclose hardware/collector/counsel/user waits, but there are no readiness dependencies, owners, target dates, or escalation deadlines. Add them before dispatching affected bundles; this does not by itself invalidate the narrow Counter build.

### [HIGH, NONBLOCKING] N-02 — Shared control-plane conflict procedure is incomplete

`.harness/PROCESS.md:69-70` recognizes concurrent `LOG.md` appends and Orchestrator-only harness JSON, but feature branches still need handoffs/log actions while `STATE.md`/`TASKS.json` change on `main`. Define whether these records are committed on feature branches, collected as PR evidence, or appended by the Orchestrator after merge.

### [MEDIUM, NONBLOCKING] N-03 — Sequential scope overlaps need explicit merge ordering

The four literal overlaps listed in §6 are dependency-ordered, but the plan should state that the earlier branch must be merged before the later branch is created. Otherwise “from current green main” can silently branch from a stale base.

### [LOW, NONBLOCKING] N-04 — AR09-G1 wording is ambiguous

`plan:224` says “unapproved copied/translated expression blocks merge,” which can be read as allowing the merge. Clarify to “unapproved copied/translated expression blocks prevent merge,” without editing the accepted ADR.

## 10. Required revisions before re-review

1. **B-01:** Assign and test every gate tool; archive the actual graph validator and regenerate reproducible validation evidence.
2. **B-02:** Add an internal Rust contract/freeze task and repair wave-5 producer dependencies.
3. **B-03:** Add root Python packaging, locked dev environment, and a local wheel task before installed-wheel tests.
4. **B-04:** Resolve done-versus-merged semantics and schedule independent review/test/Integrator evidence for every branch.
5. **B-05:** Make red-main/rollback drills policy-safe and executable in an isolated target, with tag creation and exact restore steps.
6. **B-06:** Assign production instrumentation and all benchmark subcommand implementations with negative tests.
7. **B-07:** Repair wave-1 ordering and A11Y manifest/lifecycle ownership.
8. **B-08:** Replace narrative criteria with exact commands/artifacts/exit codes and fail-closed proof semantics.
9. **B-09:** Restore executable semantics for AR06-G5, AR07-G4, AR08-G3/G5, AR09-G1, AR10-G1, and AR10-G3.
10. **B-10:** Add IME dependency and split accessible-list implementation from physical AT certification.
11. **B-11:** Add final documentation/claim closure and artifact-hash invalidation/re-audit rules.

Re-run the independent graph, producer, write-scope, gate-semantics, and workflow checks after revision. Do not edit accepted ADRs to make the task graph pass.

## 11. Final decision

**Blocking findings: 11. Nonblocking findings: 4.**

The Phase 1 plan is **not approvable**. `P0-AP01` must remain blocked. The Orchestrator should dispatch a Planner revision loop and then a second Red-Team attempt against the revised committed baseline.
