FROM: Researcher-Libs instance B
TO: Skeptic
TASK-ID: P0-R02B
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Research the Python delivery boundary for RQ-02: current PyO3, maturin, abi3/abi3t, GIL/free-threaded behavior, type stub generation, mypy --strict public API strategy, optional async runtime integration, and macOS/Windows/Linux wheel build/signing constraints. Explain an event-driven design with no Python callbacks per frame and produce claim-level evidence, contradictions and a conservative recommendation.

WHAT I DID: Read the required harness files; verified local Python 3.14.10 and rustc/cargo 1.100.0; researched versioned primary sources and registry metadata current on 2026-11-24; wrote the assigned research file with 36 labelled claims, 37 primary sources, a provisional wheel matrix, rejected alternatives and validation tasks. Recommended PyO3 0.30.1 + maturin 1.16.0, CPython >=3.11 `abi3-py311`, GIL-enabled launch only, manual reviewed public stubs plus `py.typed`, strict installed-wheel typing tests, and no default async runtime.

EVIDENCE: `.harness/RESEARCH/2026-11-24-rq-02-python-abi3-typing.md`; `.harness/RESEARCH/RQ-02-dependency-and-distribution-stack.md`; `.harness/OPEN_QUESTIONS.md` OQ-04; source register S01–S37 in the research file.

WHAT I DID NOT DO / SKIPPED, AND WHY: No feature code, wheel build, native window test, benchmark, macOS/Windows run, signing operation or credential setup was performed; none exists yet and this was research-only. No 3.13t support or production OS signing support is claimed. No TASKS.json, STATE.md, ADR or implementation file was edited, and no commit was made.

OPEN RISKS & SURPRISES: Current PyO3 0.29+ dropped 3.13t; PyO3 0.28+ defaults modules to claiming free-threaded safety, so the research recommends explicit `gil_used = true` until audited. PyO3/maturin living docs contain stale 3.13t/abi3t and version-overview text. Stub generation exists but remains active development. Async bridge documentation surrenders the main thread to Python, so native UI-loop co-driving is unverified. Maturin evidence establishes PyPI attestations and limited ad-hoc Mach-O repair signing, not Developer ID/notarization or Authenticode. OQ-03 OS/arch floors, OQ-05 public API and the distribution/signing policy remain unresolved; actual ABI compatibility and performance are untested.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/RESEARCH/2026-11-24-rq-02-python-abi3-typing.md`, `.harness/RESEARCH/RQ-02-dependency-and-distribution-stack.md`, and `.harness/OPEN_QUESTIONS.md`; falsify claims C01–C36 against the cited primary sources and record a claim-by-claim disposition in `.harness/REVIEWS/phase-0-research-skeptic.md` when the full eight-file batch is available, requesting Round 2 only where a decision could change.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/researcher-libs-to-skeptic-P0-R02B-1.md`
3. `.harness/RESEARCH/2026-11-24-rq-02-python-abi3-typing.md`
4. `.harness/RESEARCH/RQ-02-dependency-and-distribution-stack.md`
5. `.harness/OPEN_QUESTIONS.md`
6. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Approved minimum Python and OS versions; required CPU architectures; whether free-threaded Python is a launch requirement; whether delivery is PyPI-only or includes signed app/installer bundles; the minimum public API; available CI runners and release credentials.
