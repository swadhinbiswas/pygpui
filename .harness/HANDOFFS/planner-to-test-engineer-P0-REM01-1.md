FROM: Planner
TO: Test-Engineer
TASK-ID: P0-REM01
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Perform the explicitly authorized targeted remediation after the three-round cap: close only RT3-B01 through RT3-B05 and address RT3-N01/N02 where practical, without expanding scope or weakening ADRs; update the Phase 1 plan, task graph, gate schema, graph validator and tests; keep `P0-AP01` and every Phase 1 task blocked at attempt zero; regenerate exact validation evidence; and hand off for independent remediation testing.

WHAT I DID: Read the assigned State, Orchestrator handoff, targeted remediation plan and Red-Team attempt-3 review at escalation baseline `b9a8504`. Updated the graph to 65 Phase 1 tasks and 316 resolving dependencies while preserving 52 final aggregators and 26 staged sub-gates. Every gated task now validates its result against `.harness/schemas/gate-results.schema.json`; every staged aggregator invokes `tools/gates/aggregate.py`. The schema now requires `evidence_type`, and user approvals require an approver session; READY-CERT01/READY-CLAIM01 are independent verification tasks with reviewer/tester/session evidence. Build tasks now satisfy dependencies only at `merged`; RUSTCONTRACT01/CONREV01 have pre-merge branch/session checks; INT01 verifies SLICE01 pre-merge evidence, invokes `record_merge.py`, and verifies the actual merge SHA. AR09-G1/AR10-G3 include LIC01 repository-evidence sub-gates; AR04-G6 has an executable MSRV-claim audit. LIC02/LICENSE-CLOSE01 fetch and verify durable release artifacts, and the validator detects every ignored `dist/` consumer. REL02 no longer depends on Wayland/signing/channel claim approvals. Renamed stale readiness tasks, added explicit `P1-OWNER-NOTICE01`, and added root `pytest.ini` so bare root pytest discovers the hidden suite. Added negative tests for every remediation failure mode and schema tests for missing sessions, missing evidence type and missing approver. Graph validation, root pytest and handoff validation passed before this task was marked done.

EVIDENCE: `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `.harness/schemas/gate-results.schema.json`; `.harness/scripts/validate_phase1_graph.py`; `.harness/scripts/validate_handoff.py`; `.harness/scripts/tests/test_validate_phase1_graph.py`; `pytest.ini`; `evidence/P0-REM01/validation.txt`; `.harness/PLANS/phase-0-targeted-remediation.md`; `.harness/REVIEWS/phase-0-plan-red-team-attempt-3.md`; escalation baseline `b9a8504`.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not edit accepted ADRs, research, reviews, `STATE.md`, `PROCESS.md` or feature code, and I did not commit, push or open a PR. I did not implement future gate/session/artifact/runtime tools; they remain blocked Phase 1 work. I did not claim performance, platform, IME, accessibility, license closure, MSRV or signing success.

OPEN RISKS & SURPRISES: Native Windows/macOS hosts, physical platform/IME/AT runners, benchmark collectors, CPython environments, the owner copyright notice, Wayland disposition and release credentials remain unconfirmed. Draft-release immutability is policy/hash-enforced rather than GitHub object-locked. One GitHub identity and unprotected `main` still require the append-only trusted session registry and Integrator enforcement. Broad write scopes remain collision-prone but dependency-ordered. The Counter boundary, first real presentation and all performance targets remain unverified.

EXACT NEXT STEP: Test-Engineer: read `.harness/STATE.md`, this handoff, `.harness/PLANS/phase-0-targeted-remediation.md`, `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `.harness/schemas/gate-results.schema.json`, `.harness/scripts/validate_phase1_graph.py`, `.harness/scripts/tests/test_validate_phase1_graph.py`, `pytest.ini` and `evidence/P0-REM01/validation.txt`; independently rerun the graph validator, handoff validator and bare root pytest, add/execute falsification tests for RT3-B01 through RT3-B05 and RT3-N01/N02, and write `.harness/HANDOFFS/test-engineer-to-red-team-P0-REM02-1.md` without editing the plan, graph, schema or validators.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/planner-to-test-engineer-P0-REM01-1.md`
3. `.harness/PLANS/phase-0-targeted-remediation.md`
4. `.harness/PLANS/phase-1-vertical-slice.md`
5. `.harness/TASKS.json`
6. `.harness/schemas/gate-results.schema.json`
7. `evidence/P0-REM01/validation.txt`

CONTEXT I WISH I HAD HAD: Concrete implementations of the future gate/session/artifact tools, native Windows/macOS build hosts, physical platform/IME/AT runners, benchmark collectors, CPython environments, distinct reviewer/tester identities or branch protection, the project copyright holder notice, Wayland disposition and release credential owners. The graph keeps each missing input as an explicit blocked precondition.
