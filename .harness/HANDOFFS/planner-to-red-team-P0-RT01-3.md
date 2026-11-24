FROM: Planner
TO: Red-Team-Planner
TASK-ID: P0-PL01
ATTEMPT #: 3
STATUS: done

WHAT I WAS ASKED: Perform the final planned Phase 1 revision, resolve RT2-B01 through RT2-B07 and address RT2-N01 through RT2-N04 where practical, preserve prior closures and all 52 ADR obligations, encode staged gate closure and durable artifacts, split pre/post-merge evidence, legalize contract-test boundaries, correct tag timing, add native-lane readiness and separate claim approvals; then regenerate reproducible validation evidence and write this handoff without editing ADRs, research, reviews, `STATE.md`, `PROCESS.md` or feature code and without committing.

WHAT I DID: Read the assigned State, Orchestrator handoff and Red-Team attempt-2 review at blocker baseline `8ffe8de`. Replaced the graph with 64 dependency-ordered Phase 1 tasks and 308 resolving dependency edges. Added a staged gate model with 52 single-owner final aggregators and 26 named sub-gates, plus `.harness/schemas/gate-results.schema.json` and `P1-GATE-SCHEMA01`. Added immutable authenticated GitHub draft-release artifact storage/fetch/verify with source-commit, lockfile, toolchain and SHA-256 binding; ignored `dist/` is no longer shared state. Split build acceptance into pre-merge `independently_verified` and post-merge Integrator records, and required trusted reviewer/tester/session-registry evidence for every proof/verification task. Moved cross-crate contract compile tests to `crates/pygpui-contract-tests`. Moved `P1-TAG-CONTRACT01` before `P1-PROTO01` and required proof that the tagged tree lacks the contract. Added native Linux/Windows/macOS build-lane readiness and separated proof/build readiness from OQ-02 certification and Wayland/signing/publication claim readiness. Rewrote the plan with staged gates, artifact commands/retention/access, review states, dispatch waves, aggregate estimates, risks and complete gate traceability. Expanded the validator and pytest suite with semantic checks and negative tests for all 14 deadlocks, AR03-G5, ignored artifact handoff, pre-merge merged-state acceptance, proof self-certification, illegal core test dependency, post-contract tag timing, missing native-lane readiness and conflated claim readiness. Graph validation and 25 pytest tests plus 15 subtests passed before this handoff was marked done.

EVIDENCE: `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; `.harness/scripts/validate_phase1_graph.py`; `.harness/scripts/validate_handoff.py`; `.harness/scripts/tests/test_validate_phase1_graph.py`; `evidence/P0-PL01/validation-attempt-3.txt`; `.harness/REVIEWS/phase-0-plan-red-team-attempt-2.md`; `.harness/HANDOFFS/orchestrator-to-planner-P0-PL01-3.md`; `.harness/DECISIONS/README.md`; all ten accepted ADRs at `5ce026d`; Red-Team blocker baseline `8ffe8de`.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not edit accepted ADRs, research, reviews, `STATE.md`, `PROCESS.md` or feature code, and I did not commit, push or open a PR. I did not implement future runtime, wheel, benchmark, physical test or gate scripts; those remain blocked Phase 1 work. I did not claim performance, platform, IME, accessibility, license closure, MSRV or signing success.

OPEN RISKS & SURPRISES: Physical platform/IME/AT runners, native Windows/macOS build hosts, benchmark collectors, CPython environments, the owner copyright notice, Wayland disposition and release credentials remain unconfirmed and are explicit readiness blockers. Draft-release immutability is enforced by policy and hash verification, not by GitHub object lock. One GitHub identity and unprotected `main` still require the append-only trusted session registry and Integrator enforcement. The Counter boundary, first real presentation and all performance targets remain unverified. This is the final planned revision round; any residual blocker requires explicit Orchestrator escalation or bounded exception.

EXACT NEXT STEP: Red-Team-Planner: read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/schemas/gate-results.schema.json`, `.harness/scripts/validate_phase1_graph.py`, `.harness/scripts/tests/test_validate_phase1_graph.py`, `evidence/P0-PL01/validation-attempt-3.txt`, `.harness/REVIEWS/phase-0-plan-red-team-attempt-2.md`, `.harness/DECISIONS/README.md`, all ten accepted ADRs and `.harness/PROCESS.md`; independently rerun the graph validator, handoff validator and pytest suite, recheck RT2-B01 through RT2-B07 and RT2-N01 through RT2-N04, and write `.harness/REVIEWS/phase-0-plan-red-team-attempt-3.md` plus `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-RT01-3.md` without editing the plan or task graph.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/planner-to-red-team-P0-RT01-3.md`
3. `.harness/PLANS/phase-1-vertical-slice.md`
4. `.harness/TASKS.json`
5. `.harness/schemas/gate-results.schema.json`
6. `.harness/scripts/validate_phase1_graph.py`
7. `evidence/P0-PL01/validation-attempt-3.txt`

CONTEXT I WISH I HAD HAD: Native Windows/macOS build hosts, physical platform/IME/AT runners, certified benchmark hardware/collectors, CPython 3.11–3.15 environments, distinct reviewer/tester identities or branch protection, the project copyright holder notice, Wayland counsel/upstream disposition and release credential owners. The graph keeps each missing input as an explicit blocked precondition rather than an optimistic estimate.
