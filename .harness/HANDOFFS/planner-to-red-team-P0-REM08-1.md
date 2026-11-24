FROM: Planner
TO: Red-Team-Planner
TASK-ID: P0-REM08
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Directly fix D11 through D17 in current harness tooling, encode each attack as an authoritative acceptance gate on the owning Phase 1 tasks, preserve all prior closures and accepted ADRs, keep `P0-AP01` and every Phase 1 task blocked at attempt zero, regenerate exact validation evidence, and hand off for narrow Red-Team re-review without UI feature code or commits.

WHAT I DID: Read the assigned State, Orchestrator handoff, round-4 plan, Red-Team rejection and independent D11-D17 evidence at baseline `e54ecaf`. Fixed the registry seed so `--self-test` needs no extra argument, approval hashes match exact written registry bytes, reseed preserves append-only sessions/history, `--verify` detects tampering, and canonical outputs are validator-bound. Added parsed CLI argument handling with duplicate singleton-flag rejection. Bound approval artifact/registry/scope command values to sub-gate declarations. Required canonical real `gh pr view`/`gh pr diff` capture files and rejected `/dev/null`, fabricated writers and enforcement-before-capture. Bound post-merge command task/output and record path to each owning task. Bound artifact verify manifests/directories to `consumes_artifacts`, added `--dir=` support and exact verified-directory audit checks. Shell-unescaped and normalized ignored `dist/` paths. Added explicit adversarial acceptance criteria to SESSION-SEED01, GATE-SCHEMA01, READY-CERT01, READY-CLAIM01, PR-AUDIT01, TOOL-BRANCH01, ARTIFACT-STORE01, LIC02, LICENSE-CLOSE01 and TOOL-RELEASE01. Added committed seed tests and D11-D17 graph regression tests. The independent P0-REM07 attack suite now passes all 41 tests; root pytest passes 86 tests plus 18 subtests.

EVIDENCE: `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; `.harness/scripts/seed_session_registry.py`; `.harness/scripts/validate_phase1_graph.py`; `.harness/scripts/validate_handoff.py`; `.harness/scripts/tests/test_validate_phase1_graph.py`; `.harness/scripts/tests/test_seed_session_registry.py`; `pytest.ini`; `evidence/P0-REM08/validation.txt`; `evidence/P0-REM07/independent-verification.txt`; `.harness/REVIEWS/phase-0-remediation-red-team.md`; `.harness/PLANS/phase-0-remediation-round-4.md`; baseline `e54ecaf`.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not edit accepted ADRs, research, reviews, `STATE.md`, `PROCESS.md` or UI feature code, and I did not commit, push or open a PR. I did not implement future gate/session/artifact/runtime tools beyond the current registry seed; their adversarial requirements are now hard acceptance gates. I did not claim performance, platform, IME, accessibility, license closure, MSRV or signing success.

OPEN RISKS & SURPRISES: The registry seed establishes procedural, not cryptographic trust. Future tools must implement the exact parsed CLI, approval, PR, merge and artifact semantics now required by their owning tasks. Native Windows/macOS hosts, physical platform/IME/AT runners, benchmark collectors, CPython environments, the owner copyright notice, Wayland disposition and release credentials remain unconfirmed. Draft-release immutability remains policy/hash-enforced. The Counter boundary, first real presentation and all performance targets remain unverified.

EXACT NEXT STEP: Red-Team-Planner: read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-remediation-round-4.md`, `.harness/REVIEWS/phase-0-remediation-red-team.md`, `evidence/P0-REM07/independent-verification.txt`, `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/scripts/seed_session_registry.py`, `.harness/scripts/validate_phase1_graph.py`, `.harness/scripts/tests/test_validate_phase1_graph.py`, `.harness/scripts/tests/test_seed_session_registry.py`, `pytest.ini` and `evidence/P0-REM08/validation.txt`; independently rerun the graph validator, handoff validator, root pytest and P0-REM07 attack suite, verify D11 through D17 are encoded in every owning task, and write `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-REM03-2.md` without editing the plan, graph, schema or validators.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/planner-to-red-team-P0-REM08-1.md`
3. `.harness/PLANS/phase-0-remediation-round-4.md`
4. `.harness/REVIEWS/phase-0-remediation-red-team.md`
5. `evidence/P0-REM07/independent-verification.txt`
6. `.harness/TASKS.json`
7. `evidence/P0-REM08/validation.txt`

CONTEXT I WISH I HAD HAD: Concrete future gate/session/artifact tool implementations, a real PR, native Windows/macOS build hosts, physical platform/IME/AT runners, benchmark collectors, CPython environments, distinct reviewer/tester identities or branch protection, the project copyright holder notice, Wayland disposition and release credential owners. The graph keeps each missing input as an explicit blocked precondition.
