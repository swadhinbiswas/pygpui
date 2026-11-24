FROM: Researcher-Perf instance B
TO: Skeptic
TASK-ID: P0-R03B
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Design a reproducible RQ-03 benchmark protocol for 120 fps with 1,000 elements, a 10,000-row virtualized list at 120 fps, input-to-frame below 8 ms, near-zero idle CPU, and no Python call per frame. Define deterministic scenes, warmup, sample counts, p50/p95/p99, exact pass/fail statistics, hardware/software disclosure, headless versus presented metrics, the input boundary, idle CPU measurement, baseline format, >10% regression detection, concrete proposed commands/thresholds, and claim-level labels. Research only; no feature code, TASKS.json/STATE.md edits, or commits.

WHAT I DID: Wrote `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md`. It defines `e1000`, `l10000`, input, idle, and Python-boundary workloads; 10 fresh-process repetitions per scenario; explicit warmups and sample counts; nearest-rank percentiles; seeded 100,000-resample bootstrap intervals; separate headless-capacity and display-presented gates; OS-input-to-first-presented-response as the input-to-frame boundary; a proposed <1% of one-core idle gate; native Python-boundary counters with sentinels; full environment/raw-artifact disclosure; Windows/macOS/Wayland/X11/headless capture plans and limitations; immutable baseline layout; ABBA paired >10% regression semantics; and proposed `pygpui_bench`, Criterion, and pytest-benchmark commands. It includes 17 primary sources and a claim-level label register. Every requested performance number remains explicitly unverified.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md` §§0–13; `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`; `.harness/OPEN_QUESTIONS.md` OQ-02; `.harness/PROCESS.md`; `.harness/LOG.md`. Primary sources include Google Benchmark guidance, PresentMon 2.3.1, Microsoft DXGI/DWM/GetMessageTime documentation, Android frame-pacing documentation, Wayland presentation-time protocol, Apple Metal presentation APIs, Khronos Vulkan present APIs, W3C timing drafts, Python 3.14 profiling docs, Mesa release notes, Criterion.rs, and pytest-benchmark. No pygpui benchmark, baseline, or certified hardware exists.

WHAT I DID NOT DO / SKIPPED, AND WHY: No feature code, benchmark harness, benchmark execution, baseline capture, hardware certification, or physical-display test was performed because Phase 0 has no implementation or approved certification environment. The proposed 120 fps, input, idle, warmup, sample-count, confidence, and regression thresholds are policy proposals, not measured facts. Android material is used only as primary frame-pacing guidance, not as a proposed desktop support target. Physical input-to-photon remains unavailable without calibrated optical/hardware capture.

OPEN RISKS & SURPRISES: Strict literal 120 gating can fail a panel marketed as 120 Hz but measured at 119.88 Hz; the protocol refuses silent rounding and leaves any nominal-120 alternative to OQ-02/user approval. Wayland core input timestamps have millisecond granularity and an undefined clock base, Vulkan present fences/waits are not precise photon timestamps, Windows GetMessageTime is not a guaranteed sub-millisecond source, and PresentMon documents GPU/CPU instrumentation limitations. Headless throughput cannot certify displayed pacing or input-to-display. “Near zero” is proposed as <1% of one core, not zero. Ten-process confidence intervals are policy-informed by Google Benchmark's >=9-repetition warning but remain statistically coarse. Zero Python calls requires native counters and working sentinels; profiling or sparse sampling alone is insufficient. The list workload certifies only fixed-height virtualization with at most 50 retained row nodes.

EXACT NEXT STEP: Read `.harness/STATE.md`, `.harness/HANDOFFS/orchestrator-to-skeptic-P0-SK01-1.md`, `.harness/RESEARCH/PHASE0-MANIFEST.md`, this report, `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md`, and `.harness/OPEN_QUESTIONS.md`; attempt to falsify the benchmark boundaries, scene validity, sample/CI rules, strict 120 and idle thresholds, Python-counter proof, platform collectors, and ABBA regression semantics; issue targeted Round 2 requests only where a decision could change, while keeping OQ-02 blocking final certification.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-skeptic-P0-SK01-1.md`
3. `.harness/RESEARCH/PHASE0-MANIFEST.md`
4. `.harness/RESEARCH/2026-11-24-rq-03-benchmark-protocol.md`
5. `.harness/RESEARCH/RQ-03-performance-and-benchmark-model.md`
6. `.harness/RESEARCH/2026-11-24-rq-03-ffi-render-cost-model.md`
7. `.harness/OPEN_QUESTIONS.md`

CONTEXT I WISH I HAD HAD: A user-approved CPU/GPU/OS/driver/display certification profile, a decision between literal 120.0 fps and nominal-120 utilization, an accepted definition of near-zero idle CPU, a calibrated physical-input/photodiode setup, and empirical variance data to qualify the proposed ten-process sample count. Until those exist, the protocol is a reproducible plan and all target-attainment claims remain unverified.
