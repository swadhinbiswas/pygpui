# RQ-03 — FFI/render-loop performance model and reproducible benchmarks

Status: Round 1 active
Decision unblocked: Event-only FFI architecture, rendering/diffing strategy and the benchmark harness that can prove or disprove all requested targets.
Budget: Maximum 3 research rounds.

## Targets to operationalize, not assume

- 120 fps with 1,000 elements.
- 10,000-row virtualized list at 120 fps.
- Input-to-frame latency below 8 ms.
- Idle CPU near zero.
- Python is never called per frame; FFI occurs only on events, timers and post-notify rendering.

## Required angles

1. Cost model: PyO3/GIL transitions, event queues, retained-tree diffing, layout invalidation, hit testing, painter batching/instancing, glyph atlas behavior, animation and scrolling. Identify what must be measured rather than estimated.
2. Benchmark protocol: workloads, deterministic scene generation, warmup, sample counts, p50/p95/p99, frame-time budget, display-presented vs headless rendering, input-to-photon/input-to-frame definition, idle CPU measurement, hardware/software disclosure, baseline storage and regression gates.

## Decision-driving questions

- What exact architecture can guarantee no Python callback on a steady-state frame?
- What workload and statistic determines pass/fail for each target?
- How can the benchmark distinguish render cost, Python overhead, compositor/vsync delay and input pipeline latency?
- What is the smallest repeatable baseline and how is a greater-than-10-percent regression detected?

## Required output per researcher

Use dated primary sources or reproducible reasoning with assumptions exposed. Mark all numeric claims as source-backed, estimated or unverified unless actually measured in this environment. Provide concrete proposed commands/thresholds, not assertions that the architecture will be fast.
