# Open Questions and Conservative Defaults

Last updated: 2026-11-24

| ID | Question | Why it matters | Conservative default until decided | Decider | Blocks |
|---|---|---|---|---|---|
| OQ-01 | The supplied mission ends at the heading `PHASE 0 - DISCOVERY & DECISIONS`; later phase definitions and gates were not provided. | Prevents inventing an approved roadmap. | Treat Phase 0 as research, skeptical verification, ADRs, task graph and red-team approval. Do not infer later phase gates. | User / Orchestrator | Yes, for implementation |
| OQ-02 | What exact hardware/OS/driver/display configuration will certify the performance targets? | 120 fps and 8 ms are hardware- and pipeline-dependent. | Require disclosed hardware/software, warmup, repeated samples and separate headless vs presented-frame metrics. Never certify an unspecified machine. | User | Yes, for final target certification |
| OQ-03 | Which OS releases and CPU architectures are required at first release? | Affects dependency support, CI cost, wheel matrix and platform APIs. | Research currently supported stable desktop versions; propose the narrowest credible macOS/Windows/Linux matrix in an ADR. | Architect with user approval | Yes, for release plan |
| OQ-04 | Is free-threaded Python 3.13t a launch requirement or an optional compatibility target? | Changes ABI, GIL assumptions, extension safety and test matrix. | Keep the event-loop boundary GIL-aware and avoid claiming 3.13t support until separately tested. | Architect / User | No for initial vertical slice |
| OQ-05 | What is the minimum public API and first user-visible demo? | Prevents building a broad framework without an end-to-end spine. | Architect proposes a minimal app/entity/view/element/action surface and one interactive window demo. | Architect | Yes, for Phase 1 scope |
| OQ-06 | No Git remote or PR destination is configured. | The operating model asks build agents to open PRs. | Use local branches/worktrees and recorded diffs; do not invent a remote or push anywhere. | User | No for research; yes for remote PR workflow |
| OQ-07 | What does production-grade mean for accessibility, crash handling, packaging and support policy? | These can dominate schedule and platform-specific risk. | Treat accessibility, input correctness, error handling, licenses and reproducible builds as release gates rather than optional polish. | Architect / User | Yes, for release definition |
| OQ-08 | Are derived GPUI source snippets permitted? | Apache-2.0 notice/header obligations differ from clean-room concept reuse. | Prefer documented concepts and clean-room implementation; do not copy source unless provenance and license obligations are explicitly recorded. | Architect / User | Yes, if source is copied |
