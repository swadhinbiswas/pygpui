# Phase 0 plan — Red-Team attempt 2

- Task: `P0-RT01`, attempt 2
- Reviewer: Red-Team-Planner
- Date: 2026-11-24 UTC
- Reviewed baseline: `c5ca6d1970149f438f3cc124c7d6dcfaf9a7f8b1` (`main` and `origin/main`)
- Accepted ADR baseline: `5ce026d`
- Verdict: **changes requested — not approvable**
- **Blocking findings: 7**

## 1. Scope and method

I read the assigned State and handoffs, Planner attempt-2 handoff, the attempt-1 Red-Team review, the Orchestrator's 20-relationship precheck, the revised plan and 56-task graph, the committed graph validator and its pytest suite, validation evidence, `.harness/PROCESS.md`, `.gitignore`, and all ten accepted ADRs.

I independently:

1. Ran `python3 .harness/scripts/validate_phase1_graph.py --baseline 5ce026d --self-test`.
2. Ran `python3 -m pytest -q .harness/scripts/tests/test_validate_phase1_graph.py`.
3. Recomputed graph structure, transitive `P0-AP01` gating, gate coverage, downstream shared-gate relationships, workflow evidence fields, producer/write-scope overlaps, and branch-prefix uniqueness with a separate audit script.
4. Inspected the real remote, tracking branch, authenticated `gh` identity/scopes, repository permission, branch protection, rulesets, PR list, and Git credential helper.
5. Traced artifact availability through ignored paths, review/merge state transitions, rollback tag timing, crate dependency boundaries, and readiness dependencies.
6. Adjudicated each of the 20 upstream/downstream gate relationships against the ADR text, upstream acceptance commands, and the atomic `gate_policy`.

No feature code, wheel, native runtime, gate script, benchmark, or physical evidence exists yet. This review assesses whether the plan can execute without deadlock or self-certification; it does not claim implementation success or failure.

## 2. Independent validation output

### 2.1 Graph validator

```text
JSON_PARSE=PASS
UNIQUE_IDS=PASS total=70 unique=70
DEPS_RESOLVE=PASS checked=202
CYCLES=PASS count=0
TOPOLOGICAL_ORDER=PASS pass
PHASE1_FIELDS=PASS tasks=56
PHASE1_INITIAL_STATE=PASS blocked/attempt0/max4
PHASE1_AP01_GATE=PASS checked=56
PLAN_TASK_ORDER=PASS plan=56 json=56
PLAN_JSON_METADATA=PASS checked=56
ADR_GATE_COVERAGE=PASS adr=52 plan=52 task_mappings=52
ADR_GATE_MAPPINGS=PASS total=71
PHASE0_HISTORY=PASS compared=11
COMMAND_PRODUCERS=PASS criteria=190
REMOTE_WORKFLOW=PASS stale=0
SELF_TEST_PASS duplicate-id
SELF_TEST_PASS missing-dependency
SELF_TEST_PASS cycle
SELF_TEST_PASS phase1-active
SELF_TEST_PASS missing-gate
SELF_TEST_PASS unowned-command
SELF_TEST_PASS scope-mismatch
SELF_TEST_PASS missing-review-evidence
SELF_TEST_PASS stale-remote
SELF_TEST_PASS plan-json-mismatch
SELF_TEST_PASS title-mismatch
SELF_TEST_PASS gate-mapping-mismatch
SELF_TEST_PASS baseline-done-mutation
VALIDATION=PASS
```

### 2.2 Pytest negative suite

```text
14 passed in 0.25s
```

The suite contains one positive base-graph test and 13 negative tests, matching the validator's 13 self-test mutations.

### 2.3 Independent semantic checks

```text
TASKS=70 P1=56 EDGES=202
UNIQUE_IDS=PASS
MISSING_DEPS=[]
CYCLES=[]
AP01_NOT_GATED=[]
INITIAL_STATE_BAD=[]
ADR_GATES source=52 plan=52 tasks=52
DOWNSTREAM_GATE_RELATIONSHIPS=20
SUB_GATE_FIELDS=[]
GATE_RESULT_SCHEMA_PRODUCERS=[]
PROOF_VERIFY_TASKS_WITHOUT_REVIEW_TEST_FIELDS=14
BUILD_TASKS_WITHOUT_REVIEW_TEST_MERGE_FIELDS=0
LITERAL_OR_PREFIX_SCOPE_OVERLAPS=17 (all dependency-ordered)
EXACT_PRODUCER_OVERLAPS=Cargo.toml, Cargo.lock, examples/counter.py
```

`git check-ignore -v` confirms both `dist/local/*.whl` and `dist/release/*.whl` are ignored by `.gitignore:9`.

Structural validation is genuinely improved. It does not test gate semantics, artifact handoff, pre-merge versus post-merge acceptance, proof-task independence, crate dependency legality, or tag timing; the remaining blockers are in those areas.

## 3. Finding-by-finding closure matrix

| Prior finding | Status | Evidence / residual issue |
|---|---|---|
| **B-01 — gate tooling/producer** | **Closed** | Seven tool-owning tasks now exist (`.harness/PLANS/phase-1-vertical-slice.md:40`, `:89-95`; `.harness/TASKS.json:339-689`). The graph validator and tests are committed and pass. Future scripts are appropriately blocked, not falsely claimed complete. |
| **B-02 — internal Rust contracts** | **Partial** | `P1-RUSTCONTRACT01`, hashes, and real module dependencies were added (`TASKS.json:1285-1393`, `:1451-1829`). However its compile test lives in `pygpui-core`, which cannot legally depend on scene/render/platform; see RT2-B04. |
| **B-03 — packaging/local wheel** | **Partial** | `P1-PACK01` and `P1-LOCALWHEEL01` exist (`TASKS.json:868-920`, `:1993-2033`). Wheels are produced under ignored `dist/`, with no durable handoff or source-commit binding; see RT2-B02. |
| **B-04 — review/merge model** | **Partial** | Completion states and a single-identity session model are defined (`plan:56-80`). Build-task acceptance still requires a merged-state check before merge, and proof/verification tasks have no independent-evidence fields; see RT2-B03. |
| **B-05 — red-main/rollback** | **Partial** | Fixture-only drills and tag tasks exist (`plan:207-214`; `TASKS.json:339-388`, `:1136-1170`, `:1933-1991`). The “pre-contract” tag is created only after `P1-PROTO01` is merged; see RT2-B05. |
| **B-06 — instrumentation/CLI** | **Closed** | `P1-INSTRUMENT01` has explicit cross-crate production scopes and `P1-BENCHCLI01` owns all subcommands with negative tests (`TASKS.json:1821-1931`). |
| **B-07 — manifest/lifecycle ownership** | **Closed** | `P1-LIC01` now depends on manifests/packaging, and `P1-A11Y-MANIFEST01` plus expanded platform window scope own AccessKit integration (`TASKS.json:973-1033`, `:2258-2472`). |
| **B-08 — acceptance falsifiability** | **Closed for command naming** | Criteria now name commands, inputs, outputs, and fail-closed behavior. Remaining narrative assertions are attached to named test commands. The missing structured gate-result schema is part of RT2-B01. |
| **B-09 — ADR gate semantics** | **Partial** | AT-on, exact-wheel, interpreter, compare, provenance, and notice-closure tasks were added. Atomic gate mappings still deadlock; see RT2-B01 and RT2-B07. |
| **B-10 — IME before AT / hidden list work** | **Closed** | `P1-A11Y-AT01` depends on `P1-IME01`; accessible-list implementation is split into `P1-A11Y-LIST01` (`TASKS.json:2533-2581`, `:2810-2850`). |
| **B-11 — final docs/artifact invalidation** | **Partial** | `P1-ARTIFACT-GATE01` and `P1-DOC-FINAL01` exist (`TASKS.json:2935-3032`). Durable artifact availability and source-commit binding remain missing; see RT2-B02. |
| **N-01 — external waits** | **Partial** | Three readiness tasks exist (`TASKS.json:691-797`), but native wheel-build readiness is missing and certification/publication approvals are conflated with non-certification work; see RT2-B06/B07. |
| **N-02 — control-plane conflicts** | **Closed** | Feature-owned LOG/handoffs, Orchestrator-serialized State/TASKS, and Integrator conflict resolution are explicit (`plan:78-80`). |
| **N-03 — sequential overlaps** | **Closed** | Consumer-after-merged-producer semantics are explicit (`plan:188`; `TASKS.json:3101-3105`). All 17 detected scope overlaps are dependency-ordered. |
| **N-04 — AR09-G1 wording** | **Closed** | Plan line 276 now says unapproved copied/translated expression **prevents merge**. |

## 4. Gate-semantics adjudication: all 20 relationships

The controlling rule is atomic: `.harness/TASKS.json:3107` says a task may be done only when **every listed `ARxx-Gn` has a passing structured gate result**. There are no sub-gate fields, no staged gate-result schema, and no producer for such a schema. Therefore an upstream task cannot complete by producing only its stage of a multi-stage gate unless its acceptance criteria independently satisfy the entire ADR gate.

**Result: 14 deadlocks, 1 ambiguous relationship, 5 safe relationships.**

| # | Upstream → downstream | Gate | Upstream evidence available | Adjudication |
|---:|---|---|---|---|
| 1 | `P1-ARCH01` → `P1-CONREV01` | AR03-G5 | Crate-graph test and metadata (`TASKS.json:843-850`) | **Ambiguous.** ADR 0003 requires metadata plus crate-graph test, which ARCH01 can satisfy. But plan line 246 also makes internal-contract tests part of AR03-G5, and only CONREV01 runs them (`:1377`). Under the plan's own atomic wording this deadlocks; under the ADR it is safe. Remove internal-contract tests from AR03-G5 or define staged sub-gates. |
| 2 | `P1-PROTO01` → `P1-SCENE01` | AR02-G1 | Schema/property contract tests (`:1116-1119`) | **Deadlock.** Full-refresh equivalence and runtime reconciliation cannot be proven before SCENE01 exists. |
| 3 | `P1-PROTO01` → `P1-TST01` | AR02-G1 | Same schema/property evidence | **Deadlock.** TST01's integrated properties are downstream-only. |
| 4 | `P1-API01` → `P1-TST01` | AR03-G1 | mypy plus API contract pytest (`:1208-1212`) | **Deadlock.** API01 never runs the ADR-required `stubtest`; TST01 does (`:2071`). |
| 5 | `P1-API01` → `P1-TST01` | AR07-G3 | Same API evidence | **Deadlock.** Full typing gate includes `stubtest`, which is downstream. |
| 6 | `P1-BENCH00` → `P1-BENCH01` | AR08-G1 | Contract-only fixture (`:1264-1268`) | **Deadlock.** Both deterministic scenes and collector qualification are only in BENCH01 (`:2395-2397`). |
| 7 | `P1-CORE02` → `P1-TST01` | AR03-G2 | Handle/slotmap tests and source audit (`:1535-1538`) | **Safe.** Upstream acceptance can satisfy the ADR gate without integrated Counter tests. |
| 8 | `P1-SCENE01` → `P1-TST01` | AR02-G1 | Reconcile/Taffy/rebuild tests (`:1595-1599`) | **Safe.** Scene implementation can prove replacement/rollback/reorder properties. |
| 9 | `P1-RENDER01` → `P1-PLAT01` | AR05-G2 | Renderer unit tests only (`:1697-1700`) | **Deadlock.** AR05-G2 requires installed-wheel T02–T12 physical evidence. |
| 10 | `P1-RENDER01` → `P1-PLAT02` | AR05-G2 | Renderer unit tests only | **Deadlock.** Same downstream-only installed-wheel proof. |
| 11 | `P1-PLATFORM01` → `P1-PLAT02` | AR01-G1 | Platform lifecycle unit tests (`:1749-1753`) | **Deadlock.** AR01-G1 also requires installed-wheel tests on each candidate OS. |
| 12 | `P1-PY01` → `P1-TST01` | AR03-G3 | PyO3 unit/reentrancy tests (`:1800-1804`) | **Safe.** Upstream tests can satisfy the reentrancy gate. |
| 13 | `P1-SLICE01` → `P1-PLAT02` | AR02-G2 | Headless Counter tests (`:1976-1980`) | **Deadlock.** AR02-G2 requires a clean installed wheel and presented response on each candidate OS. |
| 14 | `P1-PLAT01` → `P1-PLAT02` | AR05-G2 | Linux-local installed-wheel suite (`:2247-2249`) | **Deadlock.** PLAT01 covers only Linux-local; the gate is the common candidate runtime matrix. |
| 15 | `P1-REL01` → `P1-LICENSE-CLOSE01` | AR10-G1 | Native builds and artifact audit (`:2510-2516`) | **Deadlock.** Owner-notice and exact packaged metadata closure is only in LICENSE-CLOSE01 (`:2798-2800`). |
| 16 | `P1-PLAT02` → `P1-REL02` | AR05-G6 | Support-manifest generation (`:2622-2624`) | **Safe.** PLAT02 can independently produce a valid support manifest. |
| 17 | `P1-PLAT02` → `P1-WHEEL-CALLBACK01` | AR07-G4 | Platform evidence only | **Deadlock.** AR07-G4 also requires callback proof on the same wheel. |
| 18 | `P1-PLAT02` → `P1-REL02` | AR07-G4 | Platform evidence only | **Deadlock.** Full runtime gate includes downstream callback reruns. |
| 19 | `P1-WHEEL-CALLBACK01` → `P1-REL02` | AR07-G4 | Exact-wheel callback evidence (`:2924-2926`) | **Deadlock.** This task has no platform-gate dependency/input, so it cannot independently satisfy the full runtime gate. |
| 20 | `P1-DOC-FINAL01` → `P1-REL02` | AR10-G4 | Artifact-gated final docs (`:3014-3017`) | **Safe.** Its dependencies include the license/artifact evidence needed for the wording gate. |

The plan's statement that proof commands fail closed is sound, but it does not solve these completion cycles. A staged model must state exactly which sub-evidence each producer owns and which later task aggregates the full ADR gate.

## 5. New severity-tagged findings

### [BLOCKING] RT2-B01 — Atomic multi-stage gate policy creates 14 deadlocks and one ambiguity

**References:** `.harness/TASKS.json:3107`; `.harness/PLANS/phase-1-vertical-slice.md:200-205`, `:233-284`; `evidence/P0-RT01/gate-level-precheck.txt:6-26`; task criteria cited in §4.

The graph validator passes because it checks gate identifiers and mappings, not whether an upstream task can satisfy the whole gate before its downstream consumer. No `sub_gates`, `gate_stage`, or equivalent fields exist, and no task produces a `gate-results` schema.

**Impact:** Under the declared atomic policy, tasks such as API01, BENCH00, RENDER01, PLATFORM01, SLICE01, PLAT01, REL01, and PLAT02 cannot reach `done`, yet downstream tasks depend on them. The graph is structurally acyclic but semantically deadlocked.

**Required revision:** Choose and encode one model:

- **Staged:** define named sub-gates (for example schema/reconciliation/E2E for AR02-G1, unit/installed-runtime for AR05-G2, platform/callback for AR07-G4), the exact evidence required from each task, and a final aggregator that alone marks the full ADR gate passed; or
- **Atomic:** map each full gate only to the task that can satisfy it and remove downstream-only gate IDs from upstream tasks.

Add a schema/validator for `gate-results.json` and negative tests that reject the 14 deadlock patterns and the AR03-G5 ambiguity.

---

### [BLOCKING] RT2-B02 — Wheel artifacts are ignored and have no durable handoff or source-commit binding

**References:** `.gitignore:9`; `.harness/TASKS.json:1993-2033`, `:2035-2128`, `:2217-2256`, `:2474-2531`, `:2583-2632`, `:3034-3098`; `.harness/PLANS/phase-1-vertical-slice.md:204`.

`P1-LOCALWHEEL01` writes `dist/local/**`; `P1-REL01` writes `dist/release/**`. Both paths are gitignored. Their completion evidence records hashes, but no task stores the actual wheels in a durable artifact store, registry, or other location available to later worktrees. TST01, PLAT01, PLAT02, IME01, AT01, WHEEL-CALLBACK01, and REL02 all consume those artifacts.

The local wheel is also not explicitly bound to the `P1-SLICE01` commit that REV01 reviews. A branch fix can therefore leave a stale wheel hash in use unless an undocumented manual process rebuilds and invalidates it.

**Impact:** Installed-wheel acceptance commands cannot run from the declared branch/worktree model, and “same wheel” evidence is not reproducible.

**Required revision:** Add an immutable artifact store keyed by SHA-256, with explicit upload/fetch/verify commands and a task-owned handoff manifest containing source commit, lockfile hash, toolchain, target/features, and artifact hashes. Bind the local wheel to SLICE01's reviewed commit and invalidate/rebuild it on any slice change. Do not rely on ignored `dist/` as shared state.

---

### [BLOCKING] RT2-B03 — Review/merge acceptance is circular, and proof tasks can self-certify

**References:** `.harness/PLANS/phase-1-vertical-slice.md:58-76`; `.harness/TASKS.json:375`, `:423`, `:476`, `:851`, `:2006-2007`, `:2046-2047`, `:2094-2095`, `:2184-2185`, `:2230`, `:2597`, `:3103-3118`; `.harness/PROCESS.md:54-56`; `.harness/scripts/validate_phase1_graph.py:216-224`.

Every build task includes a pre-handoff acceptance command of the form `branch_gate.py verify --state merged ...` (for example `TASKS.json:375`, `:851`). Merge evidence cannot exist until the Integrator merges the PR, but PROCESS requires clean acceptance before review/merge. The command is therefore either impossible before merge or a post-merge tautology that cannot gate the merge.

Separately, all 14 `proof`/`verification` tasks declare `completion_state: independently_verified` but have no `review_evidence`, `test_evidence`, reviewer/tester task, or branch-gate command. The validator checks only the completion-state string for these workflows. A proof task can mark itself independently verified without a second session.

**Impact:** The single-identity session-role model is not operationally closed for either build merges or proof acceptance.

**Required revision:** Split build acceptance into a pre-merge `independently_verified` gate and a post-merge Integrator record. Add required reviewer/tester evidence fields and verification tasks/commands for every proof/verification task. Define a trusted session registry or signed records so distinct session IDs cannot simply be asserted by one session.

---

### [BLOCKING] RT2-B04 — The internal-contract compile test violates the core crate boundary

**References:** `.harness/TASKS.json:1285-1325`, especially `:1300-1304` and `:1322`; ADR 0003 `.harness/DECISIONS/0003-public-python-api-and-module-boundaries.md:69-74`.

`P1-RUSTCONTRACT01` places scene, render, and platform hand-off contracts in those crates, but the only compile test is `cargo test -p pygpui-core --test internal_contracts`. Testing those foreign types from the core crate requires core dev-dependencies on scene/render/platform, contrary to ADR 0003's rule that core may not depend on platform or renderer and creating potential dependency cycles.

**Impact:** The task cannot both compile-test all hand-offs and preserve the accepted crate graph.

**Required revision:** Put cross-crate contract compile tests in a neutral integration/contract-test crate or workspace test target that is not `pygpui-core` and is not imported by production crates. Update the architecture test to allow only that explicit test-only boundary.

---

### [BLOCKING] RT2-B05 — The “pre-contract” rollback tag is created after the contract is merged

**References:** `.harness/PLANS/phase-1-vertical-slice.md:105`, `:209`; `.harness/TASKS.json:1136-1164`.

`P1-TAG-CONTRACT01` depends on `P1-PROTO01`, which completes at `merged`, then creates `phase1/contracts-premerge` from `origin/main`. The tag therefore points to main **after** the protocol contract has landed, not to the rollback base before it.

**Impact:** Reverting to the advertised pre-contract tag does not remove the contract change.

**Required revision:** Create the tag from the recorded base commit before PROTO01 is merged, or retarget it to PROTO01's parent/base and prove that the tagged tree lacks the contract. Record and validate the expected tree/hash.

---

### [BLOCKING] RT2-B06 — Native candidate wheel builds lack native-lane readiness

**References:** `.harness/TASKS.json:691-719`, `:2474-2516`; ADR 0005 `.harness/DECISIONS/0005-platform-window-and-render-backend-baseline.md:55`.

`P1-REL01` must build in native Linux, Windows, and macOS lanes, and cross-compilation alone is rejected (`TASKS.json:2511-2515`). It depends on `P1-READY-RELEASE01`, but that readiness task covers CPython, notice, Wayland, and channel/credentials—not native Windows/macOS build hosts. The task that records physical platform runners, `P1-READY-PLATFORM01`, is not a REL01 dependency.

**Impact:** REL01 can be dispatched without the infrastructure its acceptance criteria require.

**Required revision:** Add a native-build-readiness dependency/task for REL01, or make it depend on an appropriately scoped readiness manifest that confirms all three native lanes and toolchains.

---

### [BLOCKING] RT2-B07 — Readiness tasks conflate non-certification work with publication/certification approvals

**References:** `.harness/PLANS/phase-1-vertical-slice.md:33`; `.harness/TASKS.json:727-760`, `:763-796`, `:2172-2207`, `:2477-2483`, `:3037-3049`; ADR 0007 `.harness/DECISIONS/0007-abi3-strict-typing-wheel-and-release-evidence.md:20`, `:52`; ADR 0008 `0008-benchmark-certification-and-regression-gates.md:14`.

Two false dependencies remain:

- `P1-PERF01` requires `P1-READY-BENCH01`, which requires OQ-02 certification approval (`TASKS.json:755`). Callback isolation and interpreter diagnostics are proof work that ADR 0008 permits before target certification.
- `P1-REL01` requires `P1-READY-RELEASE01`, which requires a channel/credential owner (`:791`). Candidate wheel/sdist build evidence does not require public signing or publishing credentials; ADR 0007 explicitly keeps those operations unauthorized and separate.

The same release readiness also gates artifact builds on Wayland counsel, although building an artifact and making a distribution claim are different decisions.

**Impact:** Work that should be possible under the plan's non-goals is blocked on unrelated user/counsel approvals, and the graph contradicts its own separation of build evidence from trust/certification claims.

**Required revision:** Split readiness into build/proof prerequisites and claim/publication prerequisites. Let local wheel, candidate artifact, callback, and baseline work proceed without OQ-02 or signing credentials. Keep OQ-02, Wayland distribution, and public signing/publishing as blockers only on the corresponding certification or publication claim.

## 6. Unsafe parallelization and shared-file assessment

- No unordered literal/prefix write-scope collision was found. All 17 overlaps are dependency-ordered.
- Exact producer overlaps for `Cargo.toml`, `Cargo.lock`, and `examples/counter.py` are sequential and intentional.
- Several proof/readiness tasks duplicate the same evidence scope twice in their arrays (for example `TASKS.json:704-706`, `:2008-2011`). This is harmless but indicates weak scope normalization.
- Broad owners such as `crates/pygpui-platform/**` overlap later instrumentation, Counter test, manifest, and a11y tasks. They are sequential today, but the scope makes accidental concurrent edits easier to miss.
- The validator does not check semantic collisions inside broad scopes, duplicate `produces` entries, or whether `produces` is always a subset of `write_scope`.
- The control-plane model is improved: feature LOG/handoff files are branch-owned, and State/TASKS changes are Orchestrator-serialized.

## 7. Acceptance-criteria falsification tests

| Falsification attempt | Current result |
|---|---|
| Run the committed validator and negative suite. | **Pass:** validator and 14 pytest tests pass. |
| Ask the validator whether API01 can complete AR03-G1/AR07-G3 without `stubtest`. | **Accepted:** base graph passes despite missing upstream `stubtest`. |
| Ask whether BENCH00 can complete AR08-G1 without real scenes/collector qualification. | **Accepted:** base graph passes. |
| Ask whether RENDER01/PLATFORM01/SLICE01 can complete installed-wheel gates from unit/headless evidence. | **Accepted:** base graph passes. |
| Ask whether PLAT02 can complete AR07-G4 without callback proof. | **Accepted:** base graph passes. |
| Look for staged sub-gate fields or a gate-result schema. | **None exist.** |
| Build a local/release wheel, commit the task branch, then check out a fresh consumer worktree. | **Artifact absent:** `dist/` is gitignored and no store/fetch step exists. |
| Run a build task's merged-state acceptance before its PR is merged. | **Impossible:** merge evidence does not exist yet. |
| Mark a proof task independently verified without a second session. | **Possible:** no required review/test fields or verifier task. |
| Compile scene/render/platform contracts through `pygpui-core`'s test target without forbidden dev-dependencies. | **Not demonstrated;** likely violates ADR 0003. |
| Restore `phase1/contracts-premerge` and inspect whether PROTO01 is absent. | **No:** tag is created from post-PROTO01 `origin/main`. |
| Dispatch REL01 without Windows/macOS native build hosts. | **Possible:** no native-build readiness dependency. |
| Run callback proof before OQ-02 approval, or build candidate wheels without signing credentials. | **Blocked unnecessarily** by readiness dependencies. |

## 8. GitHub workflow and single-identity assessment

Verified at `c5ca6d1`:

```text
origin fetch/push = https://github.com/swadhinbiswas/pygpui.git
main = origin/main = c5ca6d1970149f438f3cc124c7d6dcfaf9a7f8b1
gh account = swadhinbiswas; active; token scopes include repo
viewer permission = ADMIN
branch protection = none (HTTP 404)
rulesets = []
PRs = none
Git HTTPS credential helper = !/usr/bin/gh auth git-credential
```

The mechanical push/PR path is viable. Role separation remains procedural: one identity, no protection, no rulesets. The plan's distinct-session model is directionally correct, but RT2-B03 must close the evidence and pre/post-merge gaps before it can be relied upon.

## 9. Nonblocking findings

### [HIGH, NONBLOCKING] RT2-N01 — Validator blind spots

`.harness/scripts/validate_phase1_graph.py` validates structure and literal command producers, but not gate-stage semantics, durable artifact availability, proof-task independence, review/merge ordering, crate dependency legality, tag timing, or actual remote/auth state. Add semantic checks as the graph evolves.

### [MEDIUM, NONBLOCKING] RT2-N02 — Scope normalization and broad overlaps

Duplicate evidence-scope entries and broad crate scopes reduce the value of collision checks. Normalize scopes and add tests for duplicate producers and `produces` outside `write_scope`.

### [MEDIUM, NONBLOCKING] RT2-N03 — Aggregate estimates remain undocumented

The plan still gives per-task ideal engineer-days but no aggregate range or calendar treatment for hardware, counsel, user approval, native lanes, or review staffing. Readiness tasks improve this, but the end-to-end range should be stated as a range plus unbounded external waits.

### [LOW, NONBLOCKING] RT2-N04 — Session identity remains trust-based

Even after RT2-B03, distinct session IDs under one GitHub account are only as trustworthy as the harness registry. Signed records or an append-only Orchestrator-controlled session ledger would strengthen the model; branch protection remains deferred under OQ-15.

## 10. Required Planner attempt-3 revisions

1. **RT2-B01:** Encode staged sub-gates or atomic final mappings; resolve all 14 deadlocks and the AR03-G5 ambiguity; add a gate-result schema and semantic validator tests.
2. **RT2-B02:** Add durable immutable artifact storage/fetch/verify and bind local/release wheels to source commits and invalidation rules.
3. **RT2-B03:** Split pre-merge verification from post-merge recording; require independent evidence for every proof/verification task; define trusted session-role records.
4. **RT2-B04:** Move cross-crate contract compile tests out of `pygpui-core` into a neutral test boundary.
5. **RT2-B05:** Create and verify the pre-contract tag before PROTO01 merges.
6. **RT2-B06:** Add native Windows/macOS build-lane readiness before REL01.
7. **RT2-B07:** Split build/proof readiness from OQ-02, Wayland distribution, and signing/publication approvals.

Then regenerate validator evidence, add negative tests for these semantic failures, and submit a Planner attempt-3 handoff for Red-Team attempt 3. Do not edit accepted ADRs to make the graph pass.

## 11. Final decision

**Blocking findings: 7. Nonblocking findings: 4.**

The revised plan is substantially better but **not approvable**. `P0-AP01` must remain blocked. The Orchestrator should dispatch Planner attempt 3, followed by Red-Team attempt 3 against the revised committed baseline.
