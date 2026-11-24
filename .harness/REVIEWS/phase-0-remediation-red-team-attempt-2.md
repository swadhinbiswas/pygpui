# Phase 0 remediation — final narrow Red-Team gate review

- Task: `P0-REM03`, attempt 2
- Reviewer: Red-Team-Planner
- Date: 2026-11-24 UTC
- Reviewed baseline: `68907f81d6c91959a5f2e57f47aa9ada71acc220`
- Scope: D11–D17 closure and Wave 0/1 authorization boundary only
- Verdict: **approve**
- **Blocking findings: 0**
- Recommendation: **Orchestrator may approve `P0-AP01` and dispatch Wave 0/1 foundational work**

## 1. Scope and method

I read the assigned State and handoff, Planner remediation handoff, round-4 plan, prior Red-Team rejection, independent D11–D17 report, Planner validation evidence, authoritative task graph, registry seed implementation, graph validator and tests, seed tests, and pytest configuration.

I independently ran:

1. graph validator with self-tests;
2. root pytest;
3. the P0-REM07 independent semantic/attack suite;
4. the P0-REM07 attack probe;
5. seed self-test; and
6. Planner handoff validation with explicit metadata.

I then checked each D11–D17 defect against its owning `P1-*` acceptance criteria, validator regression tests, dependencies, and completion/merge state. I did not reopen unrelated architecture or require runtime proof from tools that are intentionally unimplemented.

## 2. Independent command output

### 2.1 Graph validator

```text
JSON_PARSE=PASS
UNIQUE_IDS=PASS total=88 unique=88
DEPS_RESOLVE=PASS checked=326
CYCLES=PASS count=0
TOPOLOGICAL_ORDER=PASS pass
PHASE1_FIELDS=PASS tasks=66
PHASE1_INITIAL_STATE=PASS blocked/attempt0/max4
PHASE1_AP01_GATE=PASS checked=66
PLAN_TASK_ORDER=PASS plan=66 json=66
PLAN_JSON_METADATA=PASS checked=66
ADR_GATE_COVERAGE=PASS adr=52 plan=52 aggregators=52
ADR_GATE_MAPPINGS=PASS total=52
STAGED_GATE_CLOSURE=PASS sub_gates=26
GATE_RUNTIME=PASS schema+aggregate+independent-approval
GATE_RESULT_LIFECYCLE=PASS unique_paths=78
CANONICAL_RESULT_IDENTITY=PASS task+gate+path
CLI_ARGUMENT_PARSING=PASS singleton-flags
SEED_CONTRACT=PASS self-test+hash+append+canonical
REGISTRY_BOOTSTRAP=PASS orchestrator-seed-before-build
REAL_PR_EVIDENCE=PASS gh-pr-identity+diff
PR_CAPTURE_AUTHENTICITY=PASS canonical-capture-no-fabrication
APPROVAL_BINDING=PASS session+artifact+registry+scope+prelock
ATOMIC_GATE_EVIDENCE=PASS repository+enforcement+MSRV+notice
PHASE0_HISTORY=PASS compared=16
COMMAND_PRODUCERS=PASS criteria=468
REVIEW_MERGE_STATES=PASS merged-deps+premerge+session
POSTMERGE_IDENTITY=PASS task+output+record
ARTIFACT_HANDOFF=PASS draft-release/fetch/verify/normalized-dist
ARTIFACT_COMMAND_BINDING=PASS manifest+dir+audit-path
DIST_NORMALIZATION=PASS segments+braces+globs+shell-unescape
CRATE_TAG_READINESS=PASS semantic
PYTEST_ENTRYPOINT=PASS root pytest.ini
SCOPE_NORMALIZATION=PASS normalized
REMOTE_WORKFLOW=PASS stale=0
... all structural and D11-D17 self-tests PASS ...
VALIDATION=PASS
```

The self-test output includes explicit passes for:

```text
d11-noncanonical-seed-output
d12-duplicate-write-gate
d12-duplicate-write-task
d12-duplicate-validate-result
d12-duplicate-aggregate-inputs
d12-duplicate-aggregate-output
d13-removed-approval-bindings
d13-forged-approval-bindings
d14-discarded-gh-output
d14-fabricated-pr-artifacts
d15-wrong-postmerge-command
d15-wrong-postmerge-record
d16-wrong-verify-manifest
d16-dir-equals-audit-bypass
d17-shell-escaped-dist
```

### 2.2 Root pytest

```text
86 passed, 18 subtests passed in 12.62s
```

### 2.3 Independent P0-REM07 suite and attack probe

```text
python3 -m pytest -q evidence/P0-REM07/test_p0_rem07_semantics.py
41 passed in 4.68s
```

```text
BASE_GRAPH_ERRORS=0
ATTACKS_TOTAL=14
ATTACKS_ACCEPTED=0
```

Every formerly accepted D11–D17 graph mutation now returns a specific validation error.

### 2.4 Seed and handoff

```text
python3 .harness/scripts/seed_session_registry.py --self-test
SESSION_SEED_SELF_TEST=PASS
```

```text
python3 .harness/scripts/validate_handoff.py .harness/HANDOFFS/planner-to-red-team-P0-REM08-1.md --task-id P0-REM08 --to Red-Team-Planner --attempt 1
HANDOFF_FIELDS=PASS fields=13/13 files=7
```

## 3. D11–D17 closure matrix

| Defect | Owning task(s) | Direct implementation closure | Authoritative task/validator gate | Result |
|---|---|---|---|---|
| **D11 — seed executability, exact-byte hash, append-only reseed, canonical output** | `P1-SESSION-SEED01`, `P1-SESSION-REGISTRY01` | `--self-test` needs no extra args; registry and approval use identical canonical bytes; reseed preserves sessions/history; `--verify` rejects tampering (`seed_session_registry.py:17-22`, `:50-77`, `:80-103`, `:107-125`) | Seed acceptance runs create, no-arg self-test, hash verify and dedicated tests (`TASKS.json:575-580`); registry rejects non-append-only edits and hash mismatch (`:696-700`); validator rejects noncanonical seed output (`validate_phase1_graph.py:371-394`; test `:241-242`) | **CLOSED** |
| **D12 — duplicate CLI flags** | `P1-GATE-SCHEMA01` | Parsed `shlex` argument map and singleton duplicate rejection (`validate_phase1_graph.py:57-90`, `:255-260`) | GATE-SCHEMA requires CLI ambiguity tests and self-tests for write/validate/aggregate (`TASKS.json:1130-1138`); five duplicate-flag regressions reject (`test_validate_phase1_graph.py:244-257`) | **CLOSED** |
| **D13 — approval artifact/registry/scope binding** | `P1-GATE-SCHEMA01`, `P1-READY-CERT01`, `P1-READY-CLAIM01` | Validator compares command values to the reviewed sub-gate declaration and verifies ordering (`validate_phase1_graph.py:550-589`) | Both approval tasks require exact bound commands plus removed/forged-value tests (`TASKS.json:1557-1561`, `:1628-1632`); graph regressions reject removed and forged bindings (`test_validate_phase1_graph.py:259-263`) | **CLOSED** |
| **D14 — fabricated PR artifacts** | `P1-PR-AUDIT01` | Validator requires canonical `gh pr view`/`gh pr diff` outputs, rejects `/dev/null` and fabricated writers, and enforces capture-before-enforcement (`validate_phase1_graph.py:595-627`) | PR-AUDIT requires real capture commands and authenticity tests (`TASKS.json:1933-1949`); discarded/fabricated attacks reject (`test_validate_phase1_graph.py:265-269`) | **CLOSED** |
| **D15 — post-merge task/output/record identity** | `P1-TOOL-BRANCH01`; every build merge record | Validator binds `postmerge_record` to `evidence/<task>/merge.json` and parses command `--task`/`--output` (`validate_phase1_graph.py:283-288`) | TOOL-BRANCH requires wrong-task/output/record rejection (`TASKS.json:633-634`); all build tasks inherit canonical validation; regressions reject both mutations (`test_validate_phase1_graph.py:271-275`) | **CLOSED** |
| **D16 — artifact manifest/download/audit binding** | `P1-ARTIFACT-STORE01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` | Validator binds fetch directory, verify manifest/directory and audit path; supports `--dir=` (`validate_phase1_graph.py:662-692`) | Store, LIC02 and LICENSE-CLOSE each require wrong-manifest/`--dir=`/audit-path rejection (`TASKS.json:1201`, `:4484`, `:4751`); regressions reject both attacks (`test_validate_phase1_graph.py:277-287`) | **CLOSED** |
| **D17 — shell-escaped ignored `dist/` paths** | `P1-TOOL-RELEASE01`, graph validator | `_ignored_artifact_refs` shell-unescapes, expands braces and normalizes paths (`validate_phase1_graph.py:93-106`, `:693-705`) | TOOL-RELEASE requires normalization regression tests (`TASKS.json:1013`); `d\ist` attack now normalizes to `dist/` and rejects (`test_validate_phase1_graph.py:289-290`) | **CLOSED** |

All seven defects are directly closed in current harness tooling and encoded as authoritative Phase 1 gates. The prior REM-B01 condition—restrictions existing only in an exception document—is removed.

## 4. Wave 0/1 authorization assessment

### Wave 0

`P1-GOV01` may start only after `P0-AP01` is approved. It records governance, remote/auth, waves and escalation policy; it creates no UI feature code.

### Wave 1

The dependency chain is safe for implementation:

1. `P1-SESSION-SEED01` follows GOV01 and cannot be recorded without D11's self-test, hash, append-only and canonical-output gates.
2. `P1-TOOL-BRANCH01` depends on the seed and cannot merge without D15's canonical merge-record checks.
3. Session registry, gate schema, artifact store, graph/audit/platform/docs/release/benchmark tools follow the branch tool and carry their respective D12–D17 acceptance gates.
4. Approval, PR, artifact-consumer and release tasks that consume those tools explicitly depend on the relevant owners and retain the adversarial tests.
5. `P1-ARCH01` and all UI-facing tasks remain downstream of the foundational tool closures. No UI crate, Python API, renderer, window or wheel task is authorized merely by approving Wave 0/1.

At the reviewed baseline, `P0-AP01` and all 66 Phase 1 tasks are still `blocked` at attempt zero. Approval changes only the authorization gate; it does not mark any Phase 1 task complete.

## 5. Residual risks accepted for implementation start

These remain implementation-time risks, not blockers to beginning Wave 0/1:

- future gate/session/artifact/PR tools must implement the encoded semantics exactly;
- no real PR exists yet, so D14's real-`gh` path will first be exercised during Phase 1;
- the registry and single-identity review model remain procedural rather than cryptographic;
- native hosts, physical platform/IME/AT runners, collectors, CPython environments, owner notice, Wayland disposition and release credentials remain unavailable or unconfirmed;
- no performance, platform, accessibility, license-closure, MSRV or signing claim is approved by this gate review.

Each affected task remains blocked on its own evidence/readiness gate.

## 6. Final recommendation

**Approve `P0-AP01` with no bounded exceptions required for D11–D17.**

The current contracts, validator regressions and authoritative task acceptance criteria are sufficient to begin Wave 0/1 foundational implementation. UI feature work remains gated by dependent tool closure.

**Final blocking-issue count: 0.**
