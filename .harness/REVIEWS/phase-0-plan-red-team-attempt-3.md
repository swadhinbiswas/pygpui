# Phase 0 plan — Red-Team attempt 3 (final planned review)

- Task: `P0-RT01`, attempt 3
- Reviewer: Red-Team-Planner
- Date: 2026-11-24 UTC
- Reviewed baseline: `6e9637cb155f35b2475d9c4221bedca410540678` (`main` and `origin/main`)
- Accepted ADR baseline: `5ce026d`
- Verdict: **changes requested — not approvable**
- **Blocking findings: 5**
- Review-cap status: **three planned Red-Team rounds exhausted; explicit Orchestrator escalation or bounded exceptions are now required**

## 1. Scope and method

I read the assigned State and handoffs, Planner attempt-3 handoff, both prior Red-Team reviews, the revised plan and 64-task graph, gate schema, graph validator and pytest suite, validation evidence, `.harness/PROCESS.md`, `.gitignore`, and all ten accepted ADRs.

I independently:

1. Ran the graph validator with self-tests and the handoff validator.
2. Ran the explicit full pytest suite under `.harness/scripts/tests`; I also tested bare `python3 -m pytest -q` discovery.
3. Recomputed graph structure, transitive `P0-AP01` gating, gate/sub-gate ownership, aggregator dependencies, workflow evidence, artifact flows, readiness dependencies, and scope overlaps.
4. Audited all 52 final aggregators and 26 staged sub-gates for static closure and runtime enforcement.
5. Traced draft-release artifact accessibility from fresh worktrees, pre/post-merge evidence, session-role records, neutral contract-test legality, tag timing, native-lane readiness, and claim-readiness separation.
6. Checked the real GitHub remote, authentication, permissions, branch protection, rulesets, PR list, and credential helper.

No feature code, wheel, native runtime, benchmark, physical test, or future gate tool exists yet. This is a plan-level executability review, not a runtime certification.

## 2. Independent command output

### 2.1 Graph validator

Command:

```text
python3 .harness/scripts/validate_phase1_graph.py --baseline 5ce026d --history-baseline 8ffe8de --self-test
```

Result:

```text
JSON_PARSE=PASS
UNIQUE_IDS=PASS total=78 unique=78
DEPS_RESOLVE=PASS checked=308
CYCLES=PASS count=0
TOPOLOGICAL_ORDER=PASS pass
PHASE1_FIELDS=PASS tasks=64
PHASE1_INITIAL_STATE=PASS blocked/attempt0/max4
PHASE1_AP01_GATE=PASS checked=64
PLAN_TASK_ORDER=PASS plan=64 json=64
PLAN_JSON_METADATA=PASS checked=64
ADR_GATE_COVERAGE=PASS adr=52 plan=52 aggregators=52
ADR_GATE_MAPPINGS=PASS total=52
STAGED_GATE_CLOSURE=PASS sub_gates=26
PHASE0_HISTORY=PASS compared=11
COMMAND_PRODUCERS=PASS criteria=270
REVIEW_MERGE_STATES=PASS premerge/postmerge/session
ARTIFACT_HANDOFF=PASS draft-release/fetch/verify
CRATE_TAG_READINESS=PASS semantic
SCOPE_NORMALIZATION=PASS normalized
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
SELF_TEST_PASS duplicate-producer
SELF_TEST_PASS producer-outside-scope
SELF_TEST_PASS deadlock-ar03-g5-ambiguity
SELF_TEST_PASS deadlock-ar02-g1-proto-scene
SELF_TEST_PASS deadlock-ar02-g1-proto-tst
SELF_TEST_PASS deadlock-ar03-g1-api-tst
SELF_TEST_PASS deadlock-ar07-g3-api-tst
SELF_TEST_PASS deadlock-ar08-g1-bench00
SELF_TEST_PASS deadlock-ar05-g2-render-plat01
SELF_TEST_PASS deadlock-ar05-g2-render-plat02
SELF_TEST_PASS deadlock-ar01-g1-platform-plat02
SELF_TEST_PASS deadlock-ar02-g2-slice-plat02
SELF_TEST_PASS deadlock-ar05-g2-plat01-plat02
SELF_TEST_PASS deadlock-ar10-g1-rel-license
SELF_TEST_PASS deadlock-ar07-g4-plat-wheel
SELF_TEST_PASS deadlock-ar07-g4-plat-rel02
SELF_TEST_PASS deadlock-ar07-g4-wheel-rel02
SELF_TEST_PASS ar03-g5-forbidden-internal-contract
SELF_TEST_PASS ignored-artifact-handoff
SELF_TEST_PASS premerge-merged-state
SELF_TEST_PASS proof-self-certification
SELF_TEST_PASS illegal-core-test-dependency
SELF_TEST_PASS post-contract-tag-timing
SELF_TEST_PASS missing-native-lane-readiness
SELF_TEST_PASS conflated-claim-readiness
VALIDATION=PASS
```

### 2.2 Handoff validator

```text
python3 .harness/scripts/validate_handoff.py .harness/HANDOFFS/planner-to-red-team-P0-RT01-3.md
HANDOFF_FIELDS=PASS fields=13/13 files=7
```

### 2.3 Pytest

Explicit full suite:

```text
python3 -m pytest -q .harness/scripts/tests
25 passed, 15 subtests passed in 1.17s
```

Bare root discovery:

```text
python3 -m pytest -q
no tests ran in 0.00s
Exit code 5
```

The explicit suite is the real suite. Bare pytest does not descend into the hidden `.harness/` directory; see RT3-N02.

### 2.4 Independent semantic audit

```text
TASKS=78 P1=64 EDGES=308
UNIQUE_IDS=PASS
MISSING_DEPS=[]
CYCLES=[]
AP01_NOT_GATED=[]
INITIAL_STATE_BAD=[]
GATE_MODEL=52 SUB_GATES=26
BUILD_TASKS_MISSING_BRANCH_GATE=P1-RUSTCONTRACT01,P1-CONREV01
BUILD_TASKS_MISSING_SESSION_VERIFY=P1-RUSTCONTRACT01,P1-CONREV01
PROOF_TASKS_MISSING_VERIFY_PROOF=[]
READINESS_TASKS_WITH_SUBGATES_BUT_NO_REVIEW_TEST_EVIDENCE=P1-READY-CERT01,P1-READY-CLAIM01
DIST_RELEASE_USERS_WITHOUT_FETCH=P1-LIC02,P1-LICENSE-CLOSE01
REL02_REACHES_READY_CLAIM=True
REL02_REACHES_READY_CERT=False
SCOPE_OVERLAPS=18 UNORDERED=0
```

Static deadlock elimination is real: every sub-gate has one producer, every aggregator depends on its producers, and the 15 known deadlock patterns are absent. Runtime evidence enforcement is not yet complete; see RT3-B01–B03.

## 3. Complete closure matrix

### 3.1 Attempt-1 findings

| Finding | Status | Attempt-3 evidence / residual |
|---|---|---|
| B-01 gate tooling | **Closed** | Owned tool tasks, committed validator/schema, passing tests. |
| B-02 internal contracts | **Closed** | `P1-RUSTCONTRACT01` and frozen internal hand-offs exist. |
| B-03 packaging/local wheel | **Partial** | Durable store added, but two release-artifact consumers still use ignored `dist/`; RT3-B04. |
| B-04 review/merge model | **Partial** | Pre/post states exist, but merged dependency semantics and two build verifications remain incomplete; RT3-B02. |
| B-05 red-main/rollback | **Closed** | Fixture-only drills, tag tasks and restore sequence are owned. |
| B-06 instrumentation/CLI | **Closed** | Production instrumentation and benchmark subcommands have owners/scopes. |
| B-07 manifest/lifecycle ownership | **Closed** | AccessKit manifest and platform wiring tasks are explicit. |
| B-08 acceptance falsifiability | **Partial** | Commands are much stronger, but gate-result enforcement and several atomic gates remain self-certifiable; RT3-B01/B03. |
| B-09 ADR gate semantics | **Partial** | Staged model fixes the old deadlocks, but runtime aggregation and some evidence links remain incomplete; RT3-B01/B03/B05. |
| B-10 IME before AT/list split | **Closed** | `P1-A11Y-AT01` depends on IME; list implementation is separate. |
| B-11 final docs/artifact invalidation | **Partial** | Final docs and artifact gate exist; artifact fetch gap remains; RT3-B04. |
| N-01 external waits | **Partial** | Readiness classes exist, but titles/criteria conflict and notice readiness is unclear; RT3-N01. |
| N-02 control-plane conflicts | **Closed** | Feature-owned LOG/handoffs and Orchestrator-serialized State/TASKS. |
| N-03 sequential overlaps | **Closed** | All 18 detected overlaps are dependency-ordered. |
| N-04 AR09-G1 wording | **Closed** | Plan says unapproved expression prevents merge. |

### 3.2 Attempt-2 blockers

| Finding | Status | Attempt-3 evidence / residual |
|---|---|---|
| RT2-B01 atomic gate deadlocks | **Closed statically, partial operationally** | 52 aggregators/26 sub-gates and dependency closure pass; runtime aggregation/schema enforcement is missing; RT3-B01. |
| RT2-B02 durable artifacts | **Partial** | Draft-release store and most consumers are correct; LIC02 and LICENSE-CLOSE01 lack fetch/verify; RT3-B04. |
| RT2-B03 review/merge evidence | **Partial** | Most tasks have pre-merge/session evidence; RUSTCONTRACT01, CONREV01 and INT01 remain inconsistent; RT3-B02. |
| RT2-B04 neutral contract-test crate | **Closed** | `crates/pygpui-contract-tests` is test-only; core has no foreign-crate test dependency. |
| RT2-B05 pre-contract tag timing | **Closed** | Tag task precedes PROTO01 and verifies the contract path absent. |
| RT2-B06 native-lane readiness | **Closed** | `P1-NATIVE-READY01` gates REL01. |
| RT2-B07 claim-readiness separation | **Partial** | Proof/build readiness is separated, but REL02 still waits on Wayland/claim readiness; RT3-B05. |

### 3.3 Attempt-2 nonblockers

| Finding | Status | Attempt-3 evidence / residual |
|---|---|---|
| RT2-N01 validator blind spots | **Partial** | Many semantic checks added; runtime gate aggregation, readiness sub-gate evidence and some artifact consumers remain unchecked; RT3-B01/B04. |
| RT2-N02 scope normalization | **Closed** | Duplicate scopes/producers and out-of-scope production fail validation. Broad scopes remain a residual risk; RT3-N03. |
| RT2-N03 aggregate estimates | **Closed** | Plan states 70–110 and 120–190 ideal engineer-days plus unbounded waits. |
| RT2-N04 trust-based session identity | **Partial** | Append-only registry and verification tools are planned; one identity/no protection still makes this procedural; RT3-N04. |

## 4. Staged-gate audit

### 4.1 Static closure

All 26 sub-gates have exactly one producer. Every final aggregator transitively depends on each required producer. The 15 known deadlock patterns are rejected by the validator and absent from the graph. AR03-G5 correctly excludes internal-contract stages.

### 4.2 Runtime closure

There are 12 staged full gates:

| Full gate | Aggregator | Required sub-gates | Static deps | Runtime aggregation enforced? |
|---|---|---|---|---|
| AR01-G1 | `P1-PLAT02` | unit lifecycle, installed lifecycle | Pass | **No** aggregate/schema command |
| AR02-G1 | `P1-TST01` | schema, reconciliation, integrated properties | Pass | **No** |
| AR02-G2 | `P1-PLAT02` | headless, presented | Pass | **No** |
| AR03-G1 | `P1-TST01` | typing contract, stubtest | Pass | **No** |
| AR03-G5 | `P1-ARCH01` | metadata, crate graph | Pass | **No** |
| AR05-G2 | `P1-PLAT02` | unit surface, Linux installed, candidate installed | Pass | **No** |
| AR07-G3 | `P1-TST01` | typing contract, stubtest | Pass | **No** |
| AR07-G4 | `P1-REL02` | platform runtime, same-wheel callbacks | Pass | **No** |
| AR08-G1 | `P1-BENCH01` | interface, scenes/collectors | Pass | **No** |
| AR08-G6 | `P1-CERT-GATE01` | approval, measurements | Pass | Aggregate command exists, but approval producer lacks required session evidence |
| AR09-G4 | `P1-WAYLAND-GATE01` | Wayland disposition, artifact audit | Pass | Aggregate command exists, but disposition producer lacks required session evidence |
| AR10-G1 | `P1-LICENSE-CLOSE01` | artifact metadata, owner notice | Pass | **No** |

The schema requires `reviewer_session_id` and `tester_session_id` for every result (`.harness/schemas/gate-results.schema.json:17-18`, `:45-46`). The two readiness producers have neither review/test evidence nor `verify_proof.py` commands. Their sub-gate records therefore have no planned way to satisfy the schema.

## 5. New severity-tagged findings

### [BLOCKING] RT3-B01 — Gate schema and staged aggregation are not enforced by acceptance commands

**References:** `.harness/schemas/gate-results.schema.json:7-19`, `:45-53`; `.harness/PLANS/phase-1-vertical-slice.md:55-62`, `:219`; `.harness/TASKS.json:1187-1192`, `:1233-1238`, `:2714-2721`, `:3437-3443`, `:4174-4182`.

Ten staged aggregators never invoke `tools/gates/aggregate.py` or validate their `gate-results.json` against the schema. Examples include `P1-TST01`, `P1-PLAT02`, `P1-BENCH01`, `P1-ARCH01`, `P1-LICENSE-CLOSE01`, and `P1-REL02`. They can write a full-gate `pass` record without machine-checking required sub-gates, current hashes, or schema conformance.

The two readiness sub-gate producers (`P1-READY-CERT01`, `P1-READY-CLAIM01`) are `recorded` control tasks with no reviewer/tester evidence, yet the schema requires both session IDs. The aggregate commands in `P1-CERT-GATE01` and `P1-WAYLAND-GATE01` would reject the records those producers are planned to create.

**Impact:** The staged model removes static dependency cycles but does not guarantee that a full gate can actually be aggregated from schema-valid, independently verified evidence.

**Required revision:** Make every gated task validate its result against the schema, and make every staged aggregator invoke `tools/gates/aggregate.py` with the exact sub-gate evidence. Either give readiness sub-gates proper independent verification or extend the schema with a distinct, explicitly approved user-approval evidence type. Add negative tests for missing session IDs and missing aggregate invocation.

---

### [BLOCKING] RT3-B02 — Build dependencies stop before merge, and several review/merge checks remain inconsistent

**References:** `.harness/PLANS/phase-1-vertical-slice.md:66-73`; `.harness/TASKS.json:1043`, `:1776`, `:1840`, `:1797-1800`, `:1857-1860`, `:2821-2852`, `:4216-4220`, `:4233-4235`.

The narrative says dependent branches wait for the Integrator's post-merge record, but build tasks declare `completion_state: independently_verified`. The machine-readable dependency model therefore allows consumers to start before producer code is on `main`. No per-build merge-record task or dependency encodes the narrative rule.

Two build tasks, `P1-RUSTCONTRACT01` and `P1-CONREV01`, have review/test fields but no `branch_gate.py verify` or `verify_roles.py` acceptance command. They can self-certify.

`P1-INT01` verifies `P1-SLICE01` at state `independently_verified` using `evidence/P1-INT01/merge.json`, a post-merge file, and never runs `record_merge.py` to create the actual Counter merge record.

**Impact:** A dispatcher following the graph can branch from stale `main`; contract/freeze branches can bypass independent verification; the Counter merge record is not reproducibly created or checked.

**Required revision:** Encode merged-code dependencies explicitly—either build tasks complete at `merged` with separate pre-merge acceptance, or every build producer gets a merge-record task that consumers depend on. Add pre-merge/session commands to RUSTCONTRACT01 and CONREV01. Make INT01 verify SLICE01's pre-merge evidence, invoke `record_merge.py`, then verify the recorded merge SHA.

---

### [BLOCKING] RT3-B03 — Some atomic gates can pass without their ADR-required evidence

**References:** `.harness/TASKS.json:1374-1444`, `:1446-1508`, `:3503-3507`, `:4544-4548`, `:4177`; `.harness/PLANS/phase-1-vertical-slice.md:269`, `:293`, `:300`; ADR 0009 `.harness/DECISIONS/0009-clean-room-license-and-provenance-policy.md:47`; ADR 0010 `.harness/DECISIONS/0010-license-pygpui-under-apache-2-0.md:47`.

`P1-PR-AUDIT01` is the sole aggregator for AR09-G1 and AR10-G3, but it does not depend on `P1-LIC01`, which produces the actual provenance ledger, authored-scope audit, and contribution terms. Its acceptance proves only policy self-tests. The full gates can therefore pass without the repository evidence the ADRs require.

AR04-G6 is mapped to `P1-REL02`, but its only MSRV criterion is the narrative sentence “Release metadata states only pinned Rust 1.100.0 unless …”. No command audits release/docs metadata for an untested MSRV claim.

**Impact:** Gate identifiers remain intact, but these obligations can be marked passed without the claimed evidence.

**Required revision:** Stage AR09-G1 and AR10-G3 from LIC01's real repository ledger/authored-scope/contribution evidence plus PR-AUDIT01's enforcement evidence. Add an executable MSRV-claim audit to REL02 or final docs and make failure block the gate.

---

### [BLOCKING] RT3-B04 — Two release-artifact consumers still rely on ignored `dist/`

**References:** `.gitignore:9`; `.harness/TASKS.json:3490-3528`, `:3675-3709`; compare correct consumers at `:3441-3443`, `:3647-3649`, `:3818-3820`, `:3980-3981`.

`P1-LIC02` and `P1-LICENSE-CLOSE01` audit `dist/release/**` but have no `P1-ARTIFACT-STORE01` dependency, no `consumes_artifacts` entry, and no `gh release download` plus `store.py verify` commands. In a fresh task worktree, the release wheels produced by `P1-REL01` will not exist.

**Impact:** Artifact license and owner-notice closure cannot run under the declared branch/worktree model.

**Required revision:** Add store dependencies, artifact-consumer metadata, download commands, and hash verification to both tasks. Extend the validator to detect every `dist/release/**` consumer, not only consumers that declare `consumes_artifacts`.

---

### [BLOCKING] RT3-B05 — Final draft-release bundle waits on unrelated Wayland/signing/channel approvals

**References:** `.harness/TASKS.json:1203-1241`, `:3733-3780`, `:4130-4149`; `.harness/PLANS/phase-1-vertical-slice.md:34`, `:169`, `:224`; ADR 0007 `.harness/DECISIONS/0007-abi3-strict-typing-wheel-and-release-evidence.md:20`, `:52`.

`P1-REL02` depends on `P1-WAYLAND-GATE01`, which depends on `P1-READY-CLAIM01`. That readiness task requires Wayland disposition, release channel, and credential owners. Yet REL02 is a draft evidence bundle, performs no publication/signing operation, and AR07-G5 explicitly keeps public signing/publishing blocked.

This recreates the attempt-2 false dependency: bundle assembly cannot complete until unrelated claim approvals exist.

**Required revision:** Remove `P1-WAYLAND-GATE01`/`P1-READY-CLAIM01` from REL02's prerequisites. Keep Wayland distribution and signing/publication as separate claim gates that block only the corresponding claim or actual publication.

## 6. Readiness, artifact and workflow assessment

### Readiness

- Native-lane readiness is correctly separated and gates REL01.
- Proof benchmark readiness correctly excludes OQ-02.
- Build release readiness correctly excludes Wayland/signing/publication.
- However, the titles of `P1-READY-BENCH01` and `P1-READY-RELEASE01` still describe the old broad readiness classes, and the owner-notice input expected by LICENSE-CLOSE01 has no explicit producer; see RT3-N01.

### Durable artifacts

- GitHub draft releases are authenticated, non-public, hash-verified, and source/lockfile/toolchain bound.
- Most consumers fetch and verify correctly.
- LIC02 and LICENSE-CLOSE01 do not; see RT3-B04.
- Immutability is policy-only: GitHub draft releases can be altered or deleted by an admin. Hash verification detects content mismatch, and the committed manifest preserves expected hashes, but it does not prevent loss. A retention owner/backup check would strengthen the control; see RT3-N05.

### Review/merge and GitHub

Verified at `6e9637c`:

```text
origin fetch/push = https://github.com/swadhinbiswas/pygpui.git
main = origin/main = 6e9637cb155f35b2475d9c4221bedca410540678
gh account = swadhinbiswas; active; token scopes include repo
viewer permission = ADMIN
branch protection = none (HTTP 404)
rulesets = []
PRs = none
Git HTTPS credential helper = !/usr/bin/gh auth git-credential
```

The mechanical workflow is viable. Role separation remains procedural under one identity; the registry must be operationally trusted and the RT3-B02 gaps closed before it can gate every branch.

## 7. Unsafe parallelization and shared-file assessment

- No unordered literal/prefix write-scope collision was found; all 18 overlaps are dependency-ordered.
- Root manifests, crate contracts, instrumentation hooks, typing tests, benchmark package, release tools, and docs overlaps are sequential.
- Broad scopes such as `crates/*`, `crates/pygpui-platform/**`, and `tools/ci/**` still make accidental edits easy, but the current graph does not dispatch their owners concurrently.
- The larger residual parallelism risk is semantic: build consumers can be released before producer merge records because the graph's completion state is only `independently_verified` (RT3-B02).

## 8. Acceptance-criteria falsification tests

| Falsification attempt | Current result |
|---|---|
| Run graph validator and explicit pytest suite. | **Pass.** |
| Write a full staged-gate `pass` without invoking aggregate/schema validation. | **Can pass:** 10 staged aggregators have no such command. |
| Produce READY-CERT/READY-CLAIM sub-gate JSON without reviewer/tester IDs. | **Planned output cannot satisfy schema;** no verifier task requires the IDs. |
| Start a consumer immediately after its build dependency reaches `independently_verified`. | **Graph allows it,** although producer code may not be on `main`. |
| Mark RUSTCONTRACT01/CONREV01 independently verified without second sessions. | **Can pass:** no branch/session verification command. |
| Run INT01's pre-merge check using its post-merge `merge.json`. | **Inconsistent;** no actual `record_merge.py` invocation. |
| Pass AR09-G1/AR10-G3 using only PR-policy self-tests. | **Can pass;** LIC01 repository evidence is not a dependency. |
| Include an untested MSRV claim in the release bundle. | **Can pass;** no executable MSRV audit. |
| Run LIC02/LICENSE-CLOSE01 in a fresh worktree. | **Fails:** release wheels remain in ignored `dist/`. |
| Assemble REL02 without Wayland counsel/signing credentials. | **Blocked unnecessarily** by READY-CLAIM01. |
| Restore the pre-contract tag and inspect protocol absence. | **Correctly planned:** tag precedes PROTO01 and verifies absence. |
| Build candidate wheels without native Windows/macOS hosts. | **Correctly blocked** by NATIVE-READY01. |
| Run bare root pytest. | **No tests discovered;** explicit hidden-path suite passes. |

## 9. Nonblocking findings

### [HIGH, NONBLOCKING] RT3-N01 — Readiness titles contradict criteria; owner-notice readiness is not explicit

`P1-READY-BENCH01` is titled “hardware, collector and OQ-02 readiness” (`TASKS.json:954`) but its criterion explicitly excludes OQ-02 (`:980`). `P1-READY-RELEASE01` is titled for copyright/Wayland/release-channel readiness (`:991`) but its build criterion only requires CPython/packaging (`:1017`). The plan repeats the stale titles at lines 118–119. LICENSE-CLOSE01 expects an owner notice in READY-RELEASE's manifest (`:3707`), but no criterion requires that field. Rename the tasks and add an explicit notice/claim input owner.

### [MEDIUM, NONBLOCKING] RT3-N02 — Bare pytest does not discover the committed suite

The tests live under hidden `.harness/scripts/tests`; bare `python3 -m pytest -q` exits 5 with no tests. Add a root pytest configuration/testpaths or make the exact explicit suite command the documented CI entry point.

### [MEDIUM, NONBLOCKING] RT3-N03 — Broad scopes remain collision-prone

Scope normalization passes, but broad crate/tool scopes overlap later tasks. All are sequential today. Narrowing scopes or adding ownership assertions would reduce accidental concurrent edits.

### [HIGH, NONBLOCKING] RT3-N04 — Single-identity session trust remains procedural

One GitHub account, no branch protection, and no rulesets mean the append-only registry is the only role-separation control. It is a reasonable harness control, but not a cryptographic trust boundary. Preserve an Orchestrator-controlled ledger and consider signed records or branch protection after CI stabilizes.

### [MEDIUM, NONBLOCKING] RT3-N05 — Draft-release immutability is policy-only

GitHub draft releases can be deleted or changed by an admin. Hash verification detects modification, but not loss. Assign a retention owner and periodic availability check or backup the exact artifacts outside the release object.

## 10. Required Orchestrator action

The three planned review rounds are exhausted. Do **not** silently start a fourth Planner loop.

`P0-AP01` must remain blocked until the Orchestrator either:

1. keeps the gate blocked and commissions a separately authorized remediation plan for RT3-B01–B05; or
2. records explicit, bounded exceptions for each blocker in the harness, with owner, scope, expiry, conservative restrictions, and acceptance of the residual risk.

The recommended decision is **do not approve as-is**. The static graph is now strong, but runtime gate enforcement, merged-dependency semantics, artifact consumer access, atomic gate evidence, and release-bundle claim separation still prevent execution-ready approval.

## 11. Final decision

**Blocking findings: 5. Nonblocking findings: 5.**

The Phase 1 plan is **not approvable**. `P0-AP01` remains blocked pending explicit Orchestrator escalation or bounded exceptions.
