# Phase 0 remediation — bounded-exception Red-Team review

- Task: `P0-REM03`, attempt 1
- Reviewer: Red-Team-Planner
- Date: 2026-11-24 UTC
- Reviewed baseline: `b96625b6063092d146235b9ddb753725b792cfd1`
- Scope: D11–D17 exception boundaries only
- Verdict: **reject the proposed bounded authorization**
- **Rejected exception boundaries: 7 of 7**
- `P0-AP01`: **must remain blocked**

## 1. Scope and method

I read the assigned State and handoff, the proposed bounded authorization, the independent D11–D17 evidence and Test-Engineer handoff, the Phase 1 plan, and the authoritative task graph.

I checked each exception for:

1. an owning Phase 1 task;
2. an expiry/hard gate that prevents `done` or `merged` before the exact attack fails;
3. blocked dependent claims;
4. concrete restrictions;
5. explicit residual-risk acceptance; and
6. actual encoding in the owning task's acceptance criteria or validator.

I also compared the pre-proposal baseline `a5ec49b` with `b96625b` to determine whether the proposal changed any Phase 1 completion gate.

This was not a new full-plan audit. I did not reopen unrelated architecture, ADR, runtime, performance, platform, or release questions.

## 2. Controlling evidence

The proposed authorization says:

> Each exception is recorded in the owning task's acceptance criteria and evidence; missing closure keeps that task `blocked`/`partial`, not `done`.

— `.harness/PLANS/phase-1-bounded-authorization.md:31`

That statement is not true in the authoritative graph. The diff from `a5ec49b` to `b96625b` changes only Phase 0 remediation task state/evidence and adds the proposal/evidence. It makes **no change to any `P1-*` task acceptance criterion, dependency, gate result, or validator requirement**.

The independent retest establishes that all seven attacks are currently accepted:

- D11: documented seed self-test exits 2; approval hash differs from written registry; reseed replaces sessions; noncanonical seed output validates.
- D12: duplicate CLI flags are accepted.
- D13: approval artifact/registry/scope flags can be removed or forged.
- D14: real `gh` output can be discarded and fabricated artifacts substituted.
- D15: wrong-task/wrong-output merge commands and records validate.
- D16: wrong manifest and `--dir=` path bypasses validate.
- D17: shell-escaped `d\ist` bypasses ignored-path detection.

— `evidence/P0-REM07/independent-verification.txt:368-396`, `:459-646`

Because `TASKS.json` is authoritative under `.harness/PROCESS.md:7`, restrictions that exist only in the proposed authorization document do not create hard task-completion or merge gates.

## 3. Exception-by-exception adjudication

| Defect | Owning task exists? | Hard expiry encoded? | Exact attack encoded in acceptance? | Dependent claims protected? | Concrete restriction? | Residual risk accepted? | Verdict |
|---|---|---|---|---|---|---|---|
| **D11 — seed executability/hash/append-only/canonical output** | Yes: `P1-SESSION-SEED01`, `P1-SESSION-REGISTRY01` | Only “before seed is done”; not enforceable beyond three generic commands | **No.** Seed acceptance runs the script, a self-test, and `sha256sum`; it never checks approval-hash equality, reseed preservation, or canonical output (`.harness/TASKS.json:541-544`) | No. A falsely completed seed unblocks `P1-TOOL-BRANCH01` and `P1-SESSION-REGISTRY01` | Yes, in proposal line 18 only | Yes: procedural seed trust | **REJECT** |
| **D12 — duplicate CLI flags** | Yes: `P1-GATE-SCHEMA01` | “Before merged,” but not encoded | **No.** Self-test covers duplicate result paths/self-overwrite/order, not duplicate `--gate`, `--task`, `--result`, `--inputs`, or `--output` (`TASKS.json:1092-1097`) | No. Later gate writers/aggregators can consume ambiguous identities | Yes, proposal line 19 only | Yes: permissive initial CLI cannot ship | **REJECT** |
| **D13 — approval command binding** | Yes: `P1-GATE-SCHEMA01`, `P1-READY-CERT01`, `P1-READY-CLAIM01` | “Before approval sub-gates pass,” but equality attacks are not tested | **No.** Commands contain the right flags, but no acceptance test rejects removed/changed artifact/registry/scope values (`TASKS.json:1514-1516`, `:1584-1586`) | No. Forged approval records can satisfy the declaration | Yes, proposal line 20 only | Yes: human/procedural approval trust | **REJECT** |
| **D14 — fabricated PR artifacts** | Yes: `P1-PR-AUDIT01` | “Before AR09-G1/AR10-G3,” but authenticity attack is not tested | **No.** Real `gh` capture commands exist, but nothing rejects redirection to `/dev/null` plus fabricated files (`TASKS.json:1884-1900`) | No. Both provenance/authored-scope gates can consume fabricated inputs | Yes, proposal line 21 only | Yes: no real PR yet | **REJECT** |
| **D15 — post-merge identity** | Yes: `P1-TOOL-BRANCH01`; merge records on build tasks | “Before treated as merged,” but wrong task/path is not tested | **No.** `record_merge.py --self-test` omits wrong-task and wrong-output cases (`TASKS.json:590-597`) | No. Another task's merge record can satisfy merged-state semantics | Yes, proposal line 22 only | Yes: single identity/Integrator enforcement | **REJECT** |
| **D16 — artifact manifest/path binding** | Yes: `P1-ARTIFACT-STORE01`, `P1-LIC02`, `P1-LICENSE-CLOSE01` | “Before license/notice gates,” but bypasses are not tested | **No.** Current commands use the declared manifest/directory, but no test rejects a different manifest or `--dir=` bypass (`TASKS.json:4386-4464`, `:4662-4724`) | No. Audits can run on unverified or arbitrary files | Yes, proposal line 23 only | Yes: policy/hash immutability | **REJECT** |
| **D17 — shell-escaped ignored paths** | Yes: `P1-TOOL-RELEASE01`, graph validator | “Before TOOL-RELEASE01 merged,” but normalization attack is not tested | **No.** No owning acceptance criterion requires shell unescaping or the `d\ist` regression (`TASKS.json:969-975`) | No. Ignored `dist/` can re-enter non-producer tasks | Yes, proposal line 24 only | Yes: validator may evolve | **REJECT** |

## 4. Systemic blocking finding

### [BLOCKING] REM-B01 — The proposed exceptions are not authoritative completion gates

**References:** `.harness/PLANS/phase-1-bounded-authorization.md:8`, `:18-24`, `:31-32`; `.harness/PROCESS.md:7`; `.harness/TASKS.json:510-551`, `:554-619`, `:1060-1116`, `:1472-1600`, `:1850-1945`, `:4386-4724`; `git diff a5ec49b..b96625b -- .harness/TASKS.json`.

The proposal correctly identifies owners, intended expiries, restrictions, and residual risks. However, none of the exact D11–D17 attacks is encoded in the owning `P1-*` acceptance criteria. The baseline diff confirms that the proposal did not amend those criteria.

Consequently:

- `P1-SESSION-SEED01` can be marked `recorded` once its three generic commands exit, even if hash binding, reseed preservation, or canonical output remains broken.
- `P1-GATE-SCHEMA01`, `P1-PR-AUDIT01`, `P1-TOOL-BRANCH01`, `P1-ARTIFACT-STORE01`, `P1-LIC02`, `P1-LICENSE-CLOSE01`, `P1-TOOL-RELEASE01`, and the graph validator can be independently verified/merged without the listed adversarial tests.
- Dependent tasks and claims are protected only by the current behavior of future, unimplemented tools—not by an enforceable acceptance gate.

**Required correction:** Add the exact D11–D17 attack commands and expected nonzero/positive outcomes to the owning tasks' `acceptance_criteria`, and add validator regression tests where the graph itself must reject the mutation. Alternatively, replace the proposal with an implementation-only authorization that explicitly prohibits any affected task from reaching `done`/`merged` until a separately recorded closure gate passes. The current document alone is insufficient.

## 5. Wave 0/1 safety assessment

- **Wave 0 (`P1-GOV01`):** Safe only after `P0-AP01` is validly approved. It creates governance/evidence records and no UI feature code.
- **Wave 1 seed (`P1-SESSION-SEED01`):** **Not safe to authorize as written.** D11 is the trust-root boundary. If the seed can be marked recorded without hash/append-only/canonical guarantees, `P1-TOOL-BRANCH01` and the entire session-role chain inherit an unproven trust root.
- **Wave 1 tools:** `P1-TOOL-BRANCH01` directly or transitively precedes the other foundational tools and `P1-ARCH01`. Because D12–D17 are not encoded in those tools' acceptance, Wave 1 could merge permissive or bypassable controls and then present them as closed.
- **UI feature work:** It is structurally downstream of the foundational tools, but that gating is only as strong as the tool completion gates. With REM-B01 unresolved, the UI gate is not reliably closed.

Therefore Wave 0/1 may not be treated as safely authorized by the proposed exceptions.

## 6. Residual-risk assessment

The proposal explicitly accepts procedural seed trust, human approval trust, absence of a real PR, single-identity Integrator enforcement, policy-based draft-release immutability, and evolving validator hardening. Those residual risks are acceptable **only after** the corresponding attacks are hard acceptance gates.

No exception authorizes an unsupported claim, ADR change, direct `main` push, force-push, self-merge, or feature implementation before its owning tool closes. That intent is sound; the enforcement encoding is missing.

## 7. Final recommendation

**Reject all seven proposed exception boundaries as currently written.**

`P0-AP01` must remain blocked. The Orchestrator should either:

1. add the exact D11–D17 adversarial acceptance tests to the owning Phase 1 tasks/validator and request a narrow re-review; or
2. issue a revised implementation-only authorization that prevents every affected task from being marked `done` or `merged` until an explicit, independently verified closure record exists.

Do not approve the current bounded authorization and do not dispatch Wave 1 on the basis of this document alone.
