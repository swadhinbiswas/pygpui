# Phase 1 bounded authorization — implementation-level exceptions

Status: Proposed for Red-Team verification
Owner: Orchestrator
Date: 2026-11-24
Baseline: `a5ec49b`
Input: `evidence/P0-REM07/independent-verification.txt`
Decision proposed: Approve `P0-AP01` with bounded exceptions for D11–D17. No exception permits a claim, merge or dependent task to pass before the owning tool satisfies the listed attacks.

## Why bound instead of replan

The graph, ADR gates, staged evidence model, merge semantics and artifact flow are structurally complete and independently tested. D11–D17 concern runtime behavior of future tools (`seed_session_registry.py`, gate/approval tools, PR audit, merge records, artifact store and validator hardening). They are concrete implementation acceptance tests, not architecture decisions. Further planning cannot prove unimplemented code; the owning Phase 1 tasks must implement and independently test them.

## Exceptions

| Defect | Owning Phase 1 task(s) | Expiry / hard gate | Conservative restriction | Residual risk accepted |
|---|---|---|---|---|
| D11 — seed executability, hash, append-only, canonical output | `P1-SESSION-SEED01`, `P1-SESSION-REGISTRY01` | Before `P1-SESSION-SEED01` is done; before any build uses the registry | Exact documented self-test must exit zero; approval hash must match written bytes; reseed must preserve sessions; output must be canonical | Seed trust is procedural, not cryptographic |
| D12 — duplicate CLI flags bypass lifecycle | `P1-GATE-SCHEMA01` | Before `P1-GATE-SCHEMA01` is merged | Reject duplicate `--gate`, `--task`, `--result`, `--inputs`, `--output`; add adversarial tests | Future CLI implementations may initially be permissive; they cannot ship/merge |
| D13 — approval command binding | `P1-GATE-SCHEMA01`, `P1-READY-CERT01`, `P1-READY-CLAIM01` | Before approval sub-gates can pass | Command artifact/registry/scope must equal reviewed sub-gate declaration; forged/missing values fail | User approval remains a human/procedural trust boundary |
| D14 — fabricated PR artifacts | `P1-PR-AUDIT01` | Before AR09-G1/AR10-G3 can pass | Capture real `gh pr view`/`gh pr diff` output without discarding it; bind identity/diff hashes; test on a real PR | No PR exists yet; enforcement remains unverified until one does |
| D15 — post-merge identity | `P1-TOOL-BRANCH01` and every build merge record | Before any build task is treated as merged | `record_merge.py` task/output must match the canonical task record; wrong-task/path mutations fail | Single GitHub identity still requires Integrator enforcement |
| D16 — artifact manifest/path binding | `P1-ARTIFACT-STORE01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` | Before license/notice gates can pass | Verify the declared release manifest; audits must use the exact verified download directory; support `--dir=` and reject mismatches | Draft-release immutability remains policy/hash-enforced |
| D17 — shell-escaped ignored paths | `P1-TOOL-RELEASE01`, graph validator | Before `P1-TOOL-RELEASE01` is merged | Shell-unescape and normalize paths; non-producers may not reference any `dist/` spelling | Validator hardening may evolve; attacks must remain regression tests |

## Authorization restrictions

- Phase 1 may start only with Wave 0/1 governance, registry seed, gate/session/artifact/branch tooling.
- No UI feature crate, Python API, renderer, window or wheel implementation may merge until the foundational tool exceptions it depends on are closed.
- No performance, platform, IME, accessibility, license, MSRV, signing or publication claim may pass while its evidence gate is unresolved.
- Each exception is recorded in the owning task's acceptance criteria and evidence; missing closure keeps that task `blocked`/`partial`, not `done`.
- Exceptions expire when their owning task is independently verified and merged. They do not authorize weakening ADRs or deleting attack tests.

## Rollback

If Red-Team rejects these boundaries, `P0-AP01` stays blocked and no Phase 1 task starts. If an owning tool fails an exception attack, stop dependent work, fix or revert that tool, and rerun the full relevant gate. Accepted ADRs and independent evidence remain immutable.
