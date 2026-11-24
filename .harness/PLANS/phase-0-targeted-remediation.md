# Phase 0 escalation — targeted plan remediation

Status: Authorized
Owner: Orchestrator
Date: 2026-11-24
Reviewed baseline: `6e9637c`
Decision: Do not approve `P0-AP01` as-is. Authorize a targeted remediation pass for RT3-B01 through RT3-B05, then independent verification. No UI feature implementation is authorized by this decision.

## Why escalate

Three planned Red-Team rounds are exhausted. The graph is structurally strong, but five execution semantics remain unsafe: runtime gate aggregation/schema enforcement, merged-code dependency semantics, atomic gate evidence, durable artifact consumption, and release-bundle claim separation.

## Scope

- **P0-REM01 — Planner remediation:** update the plan, task graph, gate schema and validator/tests to close RT3-B01–B05 and RT3-N01/N02 where practical.
- **P0-REM02 — Independent verification:** a different Test-Engineer reruns all validators and adds/executes falsification tests against the revised semantics.
- **P0-REM03 — Red-Team verification:** a different Red-Team session verifies closure and issues a final zero/nonzero blocker count.

No ADR, research finding, performance target, platform claim or release claim may be weakened. No feature crate, Python API, renderer, window, wheel or benchmark implementation may start until `P0-AP01` is approved.

## Required closure

1. Every staged aggregator invokes schema validation and `tools/gates/aggregate.py`; readiness approvals use an explicit evidence type that satisfies the schema or gain independent verification.
2. Build consumers depend on merged code or explicit merge-record tasks; RUSTCONTRACT01/CONREV01 gain pre-merge/session checks; INT01 records and verifies the actual merge SHA.
3. AR09-G1/AR10-G3 include LIC01 repository evidence; AR04-G6 has an executable MSRV-claim audit.
4. LIC02 and LICENSE-CLOSE01 fetch and verify durable release artifacts; the validator detects every ignored-artifact consumer.
5. REL02 no longer waits on Wayland/signing/channel claim approvals; those gate only the corresponding claims/publication.

## Acceptance and expiry

- `P0-REM01` is done only when reproducible validation evidence exists and all five findings have exact task/schema/command closure.
- `P0-REM02` is done only when independent tests pass and no self-certification path remains.
- `P0-REM03` is done only with zero blocking findings or a new explicit Orchestrator decision.
- This authorization expires when the remediation pass completes. It does not authorize a general fourth planning loop or feature implementation.

## Rollback

Remediation changes only harness planning/schema/validator files and task metadata. Revert the remediation commit as a unit if it introduces regressions; accepted ADRs and research remain untouched. `P0-AP01` stays blocked throughout.
