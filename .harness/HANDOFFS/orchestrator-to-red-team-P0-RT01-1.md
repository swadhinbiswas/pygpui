FROM: Orchestrator
TO: Red-Team-Planner
TASK-ID: P0-RT01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Adversarially review the accepted ADRs and Phase 1 task graph before implementation. Find missing dependencies, hidden coupling, shared-file contention, unrealistic estimates, absent rollback, weak acceptance criteria and verification/release work hidden outside the graph.

WHAT I DID: Defined the planning and red-team gates, prepared Planner handoff, and preserved Skeptic's binding constraints for the plan.

EVIDENCE: `.harness/DECISIONS/README.md`; `.harness/DECISIONS/0001-…0010-…md`; `.harness/PLANS/phase-1-vertical-slice.md`; `.harness/TASKS.json`; `evidence/P0-PL01/validation.txt`; `.harness/HANDOFFS/planner-to-red-team-P0-PL01-1.md`; `.harness/REVIEWS/phase-0-research-skeptic.md`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No plan exists to review until Architect and Planner complete. Red-team cannot approve an unwritten graph.

OPEN RISKS & SURPRISES: Parallel build agents can collide on manifests, snapshot schemas, public stubs and benchmark interfaces. A horizontal “build all crates” plan would delay the first real window and hide integration risk.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/DECISIONS/README.md`, all ten accepted ADRs, `.harness/PLANS/phase-1-vertical-slice.md`, `.harness/TASKS.json`, `evidence/P0-PL01/validation.txt`, `.harness/HANDOFFS/planner-to-red-team-P0-PL01-1.md` and `.harness/REVIEWS/phase-0-research-skeptic.md`; write `.harness/REVIEWS/phase-0-plan-red-team.md` with severity-tagged findings and a final blocking-issue count, then append one action line to `LOG.md` and write `.harness/HANDOFFS/red-team-planner-to-orchestrator-P0-RT01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-red-team-P0-RT01-1.md`
3. `.harness/DECISIONS/README.md`
4. `.harness/PLANS/phase-1-vertical-slice.md`
5. `.harness/TASKS.json`
6. `.harness/REVIEWS/phase-0-research-skeptic.md`
7. `.harness/PROCESS.md`

CONTEXT I WISH I HAD HAD: Team throughput, available physical test hardware, CI budget, remote repository and release credentials. Estimates must remain ranges/buckets rather than fake precision.

## Review checklist

- Every dependency edge exists and points to a task that produces the needed contract.
- Shared interfaces have one owner and land before parallel consumers branch.
- The first slice is user-visible and independently revertable.
- Every task has a test, benchmark threshold or command that exits zero.
- Unit, property, integration, headless, screenshot/fuzz and platform tests are represented where relevant.
- Unsafe code, GIL discipline, handle lifetime, teardown and ref cycles have explicit review gates.
- Performance harness and baseline capture precede any target claim.
- Wheel/typing/license/SBOM/audit work is in the graph, not omitted as release polish.
- Local worktree/branch workflow is viable without a remote; no fabricated PR requirement blocks progress.
- Estimates include review, CI, platform certification and rework; no XL task is left unsplit.
- Rollback exists for every mergeable slice and red-main recovery is explicit.
