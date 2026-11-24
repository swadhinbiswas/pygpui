FROM: Orchestrator
TO: Researcher-Perf instance B
TASK-ID: P0-R03B
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Design the reproducible benchmark protocol for RQ-03. Define scene workloads, warmup, sample counts, statistics, hardware disclosure, baseline/regression handling and exact pass/fail semantics for 1,000 elements, a 10,000-row virtualized list, sub-8-ms input-to-frame latency and near-zero idle CPU.

WHAT I DID: Recorded all requested numbers as unverified targets and required separate headless versus presented-frame metrics.

EVIDENCE: `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`; `.harness/TASKS.json` task P0-R03B.

WHAT I DID NOT DO / SKIPPED, AND WHY: No implementation or baseline exists yet. This task designs how evidence will be produced, not what the future results will be.

OPEN RISKS & SURPRISES: Input-to-frame can mean event-loop dispatch, render completion or photon presentation. The protocol must name the measured boundary and report all relevant components.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff and `RQ-03-performance-and-benchmark-model.md`; research benchmark methodology and platform frame-pacing primitives, write `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md` with concrete proposed thresholds/commands and claim-level labels, then append one action line to `LOG.md` and write `HANDOFFS/researcher-perf-to-skeptic-P0-R03B-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-perf-P0-R03B-1.md`
3. `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`
4. `.harness/PROCESS.md`
5. `.harness/OPEN_QUESTIONS.md`

CONTEXT I WISH I HAD HAD: CI hardware variability policy and acceptable confidence intervals for target certification.
