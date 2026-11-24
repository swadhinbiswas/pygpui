FROM: Orchestrator
TO: Release-CI-Engineer
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 3
STATUS: partial

WHAT I WAS ASKED: Fix independent Reviewer blockers R-01 through R-04 and address R-05 through R-08 where practical. Preserve prior failed review and passed test evidence as attempt archives, reset branch evidence for a new artifact, and return for fresh independent test and review.

WHAT I DID: Validated the review fail decision, reopened build attempt 3, and kept Integrator merge blocked.

EVIDENCE: `.harness/HANDOFFS/reviewer-to-integrator-P1-TOOL-BRANCH01-1.md`; `/tmp/opencode/pygpui-P1-TOOL-BRANCH01/evidence/P1-TOOL-BRANCH01/review.json`; `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer_adversarial.py`; PR https://github.com/swadhinbiswas/pygpui/pull/1 at head `a4c0ae7b0539bc3a78a267049336af95c6c0c00e`.

WHAT I DID NOT DO / SKIPPED, AND WHY: No fix has been made yet. Attempt-2 review fail and test pass remain historical evidence and must not be relabeled.

OPEN RISKS & SURPRISES: This is the last routine fix round. Remaining blockers after attempt 3 require explicit Orchestrator escalation.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/HANDOFFS/reviewer-to-integrator-P1-TOOL-BRANCH01-1.md`, `evidence/P1-TOOL-BRANCH01/review.json`, `evidence/P1-TOOL-BRANCH01/independent-test.json`, `evidence/P1-TOOL-BRANCH01/branch-evidence.json`, `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer_adversarial.py`, `tools/ci/evidence.py`, `tools/ci/record_merge.py`, `tools/ci/common.py`, `tools/ci/red_main_drill.py`, `tools/ci/fixture_git.py` and `tools/ci/run_local_gate.py` in `/tmp/opencode/pygpui-P1-TOOL-BRANCH01`; fix R-01 through R-04 with negative tests, address R-05 through R-08, archive attempt-2 evidence, reset branch evidence, rerun the reviewer probes and full matrix, commit/push the same feature branch, update PR #1, and write `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-3.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-release-ci-P1-TOOL-BRANCH01-3.md`
3. `.harness/HANDOFFS/reviewer-to-integrator-P1-TOOL-BRANCH01-1.md`
4. `evidence/P1-TOOL-BRANCH01/review.json`
5. `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer_adversarial.py`
6. `tools/ci/evidence.py`
7. `tools/ci/record_merge.py`

CONTEXT I WISH I HAD HAD: A canonical evidence-only delta protocol and live GitHub merge fixture. Implement both explicitly; do not rely on source ancestry alone.

## Required fixes

- **R-01:** Require `independent_evidence is True` for pre-merge pass; reject false/missing/non-boolean.
- **R-02:** Record reviewer-attested `reviewed_head_commit`/tree; allow only canonical task-evidence changes after that head; reject any post-review implementation change before pre-merge or merged pass.
- **R-03:** Merged-state CLI verification must use live canonical GitHub metadata by default; require PR head ancestor of merge SHA, merge SHA reachable from `main`/`origin/main`, and expected SHA binding. Offline records cannot return merged PASS.
- **R-04:** Bind PR URL owner/repo to canonical `origin`; reject wrong-repository and option-like selectors before invoking `gh`.
- **R-05:** Validate review/test record roles against assigned reviewer/tester roles.
- **R-06:** Push simulated red main to the fixture remote and verify remote red/green restoration.
- **R-07:** Handle existing empty fixture directories without traceback.
- **R-08:** Refresh canonical README from actual records/logs.
- Preserve attempt-2 review fail and test pass under archival paths; reset canonical review/test references for the new artifact.
