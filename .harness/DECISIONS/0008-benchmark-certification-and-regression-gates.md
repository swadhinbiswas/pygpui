# ADR 0008: Certify performance only with qualified evidence and ABBA regression gates

Status: Accepted
Date: 2026-11-24
Deciders: Architect (P0-AR01), under Orchestrator delegation; User approval of OQ-02 is required before target certification.

## Context

No benchmark implementation, baseline, certified hardware or performance result exists. Headless completion, submitted frames, compositor presentation and photons are different boundaries. The research protocol contained conflicting ABBA counts, an off-by-one mounted-row limit and a Metal queue-depth mismatch; the Skeptic corrections are binding. The 120 fps, p95 <8 ms and near-zero-idle numbers remain unverified targets.

## Decision

- Keep separate claim families for headless capacity, presented pacing, input response, idle CPU and Python-boundary isolation. No result may be generalized beyond its disclosed environment, build, scene hash and collector.
- Final target certification is blocked until User approves the hardware/OS/driver/display stack and exact gates under OQ-02. Until then results are local observations or `ci_smoke`, never certification.
- Use deterministic `e1000` and `l10000` scenes. `l10000` has 10,000 model rows and asserts **at most 51 mounted row nodes** per frame, unique contiguous visible IDs and no offscreen Python row provider. Rendering all rows invalidates the workload.
- Qualification/target runs use **ten fresh processes per variant**. Baseline/candidate regression uses **five `A B B A` blocks = 20 process runs = ten pairs** (ten A runs and ten B runs), never the contradictory “ten paired blocks” wording.
- Input latency is measured from **OS input-stack receipt to the first presented frame containing the unique response token**. Submission, GPU completion and injector timestamps are not substitutes. Input-to-photon is separate and requires calibrated optical/hardware evidence. Click and key are reported separately; a 50 ms response timeout is a failed trial.
- The benchmark uses the shipped renderer configuration: `Fifo`, desired maximum frame latency 2 and, on Metal, **three drawables**. A two-drawable experiment must set desired latency 1 and have a separate name.
- Native counters are authoritative for `rust_to_python_callbacks`, `python_to_rust_frame_entries`, `render_thread_gil_acquires`, attachments and Python finalizers. Every measured window must be zero. Deliberate callback and frame-entry sentinels must each increment exactly once before warmup; failed/disabled counters make the run inconclusive.
- Corroborate with Python profiling outside timing certification: use `threading.setprofile_all_threads` on Python 3.12+, and on **Python 3.11 fall back to `sys.setprofile` plus native counters**. Compare GIL-enabled and free-threaded builds only by launching separately installed interpreters; `PYTHON_GIL` does not select a build. The release remains GIL-only.
- Provisional target gates, pending OQ-02, are literal **≥120.0 presented fps** on a qualified 120 Hz path with no dropped application frames; **p95 <8.000000 ms** OS-input-to-presented-response; and **<1% of one CPU core** application process-tree idle over 60 seconds with zero application submissions/presentations. Do not round into a pass.
- Store immutable baselines under `BENCH/baselines/<environment_id>/<baseline_id>/` with manifest, scene hashes, raw runs/captures, per-process values, analysis settings and SHA-256 indexes. Never overwrite a baseline.
- For lower-is-better metrics use `100*(candidate-baseline)/baseline`; for FPS use `100*(baseline-candidate)/baseline`. The headline regression is the median of the ten paired deltas. A value **>10.0%** is a potential regression and immediately requires profiling plus a written diagnosis; exactly 10.0% is not greater. A paired-bootstrap 95% lower bound >10.0% confirms it. An interval crossing 10.0% is inconclusive and may add predeclared 10-pair blocks up to 30 pairs; it is never a pass.
- Any nonzero Python-boundary counter is an absolute failure. Other zero-baseline metrics require a predeclared absolute tolerance. Diagnostics and component benchmarks use the same >10% diagnosis rule but cannot replace end-to-end evidence.

## Alternatives considered

- **Certify from headless FPS or submit-call counts:** rejected because neither proves presentation or input-to-display latency.
- **Use app-callback-to-submit as the 8 ms endpoint:** rejected as ambiguous and weaker than the adopted boundary.
- **Sampling-only callback proof:** rejected because it can miss FFI/finalizer paths; native counters plus sentinels and a static audit are required.
- **Ten ABBA blocks/20 pairs:** rejected in favor of the Skeptic's five blocks/ten pairs.
- **Mount ≤50 rows:** rejected because fractional viewport/overscan arithmetic can produce 51.
- **Metal two drawables with desired latency 2:** rejected because wgpu maps that setting to three drawables.
- **Nominal-120 rounding or unspecified-machine certification:** rejected; measured refresh and exact values are reported.

## Consequences

- Certification needs physical displays, qualified collectors and clock calibration; hosted/headless CI can only smoke-test.
- Strict gates may fail on nominal 119.88 Hz panels or noisy hardware; that result is reported, not rounded away.
- The protocol and harness are new implementation work, and all numbers remain unverified until valid runs exist.
- Regression triage can block a hot-path merge even when a target has not yet been certified.

## Evidence links

- [Skeptic F-01–F-03/F-05/F-08/F-09 — binding benchmark corrections](../REVIEWS/phase-0-research-skeptic.md#nonblocking-findings).
- [RQ-03B — boundaries, scenes and exact gate semantics](../RESEARCH/2026-11-24-rq-03-benchmark-protocol.md#6-statistics-and-exact-gate-semantics).
- [RQ-03B — baseline and >10% regression protocol](../RESEARCH/2026-11-24-rq-03-benchmark-protocol.md#10-baseline-format-and-10-regression-detection).
- [RQ-03A V01–V14 — experiments](../RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md#11-recommended-validation-experiments).
- [`.harness/PROCESS.md` performance loop](../PROCESS.md#performance-loop).

## Validation gates

- **AR08-G1 — harness qualification:** `python -m pygpui_bench scene verify ...` and collector qualification exit zero for both scenes, the ≤51-row assertion, sentinel counters, clock-domain checks and raw-artifact hashing before any performance claim.
- **AR08-G2 — immutable baseline:** ten valid fresh-process runs per scenario create a complete immutable baseline; missing raw data, environment fields or sentinels fails validation.
- **AR08-G3 — boundary proof:** static audit plus V01 native counters pass zero in every measured static/native-animation/native-scroll/input frame window; the Python 3.11 fallback and separate-interpreter matrix are exercised.
- **AR08-G4 — presented/input qualification:** platform collectors prove the exact presentation endpoint and, for the 8 ms gate, OS input receipt with the predeclared clock-uncertainty rule; otherwise status is `inconclusive`, not pass.
- **AR08-G5 — regression gate:** `python -m pygpui_bench compare ... --threshold-percent 10` exits nonzero for a potential/confirmed regression until profiling and a written diagnosis are linked; exactly 10.0%, zero-baseline handling and all ten pairs are verified by unit tests.
- **AR08-G6 — target report:** a report may say `pass` only with OQ-02 approval, all correctness/counter gates, valid environment fingerprint and raw artifacts; otherwise it is `not_certified`, `not_measured`, `fail` or `inconclusive`.

## Revisit when

User approves OQ-02 hardware/gates; collector or clock semantics change; a baseline shows >10% movement; or the runtime configuration changes queue depth, backend, scene or build profile. Protocol changes require a new protocol ID and cannot rewrite an accepted baseline.
