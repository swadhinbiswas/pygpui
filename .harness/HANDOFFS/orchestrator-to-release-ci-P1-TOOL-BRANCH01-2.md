FROM: Orchestrator
TO: Release-CI-Engineer
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 2
STATUS: partial

WHAT I WAS ASKED: Fix independent Test-Engineer blockers T-01 through T-05 on the existing PR branch, add regression tests, recompute the branch artifact, and hand back for independent retest. Do not merge or weaken the failed evidence.

WHAT I DID: Validated the independent fail decision, reopened build attempt 2, and preserved the attempt-1 evidence.

EVIDENCE: `.harness/HANDOFFS/test-engineer-to-reviewer-P1-TOOL-BRANCH01-1.md`; `/tmp/opencode/pygpui-P1-TOOL-BRANCH01/evidence/P1-TOOL-BRANCH01/independent-test.json`; `/tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial_checks.py`; PR https://github.com/swadhinbiswas/pygpui/pull/1 at head `51a17f78dc939ffc58757b54357a4c47de4d606c`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No fix has been made yet. The failed independent evidence remains valid for attempt 1 and must not be relabeled as passing.

OPEN RISKS & SURPRISES: The green suite missed real fail-closed gaps. Fixes must be proven by the same independent adversarial probes, not only new author tests.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/HANDOFFS/test-engineer-to-reviewer-P1-TOOL-BRANCH01-1.md`, `evidence/P1-TOOL-BRANCH01/independent-test.json` and `tools/ci/evidence.py`, `tools/ci/common.py`, `tools/ci/run_local_gate.py` in `/tmp/opencode/pygpui-P1-TOOL-BRANCH01`; fix T-01 through T-05 with negative tests, archive the attempt-1 failed evidence, reset branch evidence for the new artifact, rerun the full matrix and adversarial probes, commit/push the same feature branch, update PR #1, and write `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-2.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-release-ci-P1-TOOL-BRANCH01-2.md`
3. `.harness/HANDOFFS/test-engineer-to-reviewer-P1-TOOL-BRANCH01-1.md`
4. `evidence/P1-TOOL-BRANCH01/independent-test.json`
5. `/tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial_checks.py`
6. `tools/ci/evidence.py`
7. `tools/ci/run_local_gate.py`

CONTEXT I WISH I HAD HAD: A canonical bound-record schema requiring branch/source_tree on every independent record. Add it now rather than accepting contradictory optional fields.

## Required fixes

- **T-01:** Require `refs/heads/<branch>` to exist and the reviewed source commit to be an ancestor of that branch tip.
- **T-02:** Require explicit matching `task_id` for every non-seed implementer/reviewer/tester/Integrator role.
- **T-03:** Require exact `source_tree` equality on bound review/test/session-role records; update records to carry it.
- **T-04:** Require exact `branch` equality on bound review/test/session-role records; update records to carry it.
- **T-05:** Catch configured Ruff `OSError`/`FileNotFoundError`, return dependency exit `69`, and add a negative test.
- Preserve attempt-1 fail evidence under an archival filename; do not overwrite or relabel it.
- Keep registry roles/hash unchanged unless a real role change is required; any registry change must refresh approval and rebind evidence.
