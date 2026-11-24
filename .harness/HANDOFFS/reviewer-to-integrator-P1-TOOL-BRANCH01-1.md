FROM: Independent-Reviewer
TO: Integrator
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Independently review PR #1 attempt 2 at dispatched head `995c710afc6f57922670eecb3b2bab5e2248cf55`, bound source `031524fd65d14d5a5818e277ac1bfc28d6e0db5b`, tree `b6d70180cacfcaa8aa76a0e6d2a5aeae94cd7b6e`, artifact `76d214d68d773084a3fa4e09422c2a19324beff9604d010b830d608aed514503`, registry `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498`, and independent test SHA `7d48be25ea27b6724e954ef042ad50e2a01f25c42d82894162ad0887449b17c5`; review correctness, fail-closed behavior, security/path handling, command execution, role trust, identity/ancestry binding, merge integrity, fixture isolation, rollback semantics, errors, maintainability and tests; do not merge.

WHAT I DID: Read the required state, handoffs, canonical evidence, task/process contract and full PR diff. Independently reran 95 focused tests, the full local gate (183 tests plus 18 subtests), all ten seed/tool self-tests, the exact T-01–T-05 adversarial script, fresh red-main and rollback drills, missing-Ruff handling, and new reviewer adversarial probes. The dispatched matrix passed, but the new probes found four blocking control bypasses. Wrote canonical `review.json` with `decision=fail`, committed/pushed only that review record, and left branch evidence unchanged at `state=implemented` and `independent_evidence=false`.

EVIDENCE: Canonical review `evidence/P1-TOOL-BRANCH01/review.json` SHA-256 `1e20e25db6550c6088526c06e1be85bf5365aaf9ddd28d1be493e4a410d2dc08`; review commit and new PR head `a4c0ae7b0539bc3a78a267049336af95c6c0c00e`; unchanged branch evidence SHA-256 `88be62d31a829780e946bdb9423bad3e689d2242e1d7b05b13faef9968ab76c6`; unchanged independent test SHA-256 `7d48be25ea27b6724e954ef042ad50e2a01f25c42d82894162ad0887449b17c5`; reviewer adversarial script SHA-256 `88792de51c9b35fc6bc8b0db4a3c48ecf7225b160163e2748b753d2f893adb05`; reviewer adversarial log SHA-256 `a44e671530d7934c39f8352ede6014c2d3e9970b53018f6d85b5b1c21355a5d5`; full PR diff SHA-256 `0290107c0114a9e4cb1c1087147c53d2b2d5935e9d364c8b60ee43c846b9b38d`; evidence index `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/evidence-sha256.txt` SHA-256 `8a740460200b7da3739d5c06fb43c69d01699ccd09001133fc0fe48926747800`.

BLOCKING FINDINGS:
- **R-01 / high / blocking:** `tools/ci/evidence.py:145-146` accepts `state=independently_verified` while `independent_evidence=false`; the flag is never checked. Require boolean true and add false/missing/non-boolean negatives.
- **R-02 / critical / blocking:** `tools/ci/evidence.py:169-173` and `tools/ci/record_merge.py:92-96,170-173` require only source ancestry. A post-review implementation commit on a descendant head passed pre-merge, merge-record creation and merged-state verification. Bind the final reviewed head/tree or enforce a reviewer-attested canonical evidence-only post-source delta.
- **R-03 / critical / blocking:** `tools/ci/record_merge.py:226-341` accepts self-hashed offline PR fields, does not require PR head ancestry to the merge commit or merge reachability from main, and `tools/ci/evidence.py:314-324` calls it without live metadata. A forged record with an unrelated side-branch head passed merged-state verification. Require authoritative live metadata, head→merge ancestry, main/origin-main reachability and expected merge-SHA binding for merged PASS.
- **R-04 / high / blocking:** `tools/ci/record_merge.py:37,71-116` accepts any GitHub owner/repo and never compares the PR with origin. Metadata for `attacker/pygpui` was accepted while origin was `swadhinbiswas/pygpui`. Bind canonical PR URL/repository to origin and reject arbitrary/option-like selectors.

NONBLOCKING FINDINGS:
- **R-05 / medium:** contradictory review/test `role` fields are accepted; validate record roles against assigned sessions.
- **R-06 / medium:** the red-main drill never pushes red main to its fixture remote; strengthen it to exercise remote red detection/restoration.
- **R-07 / low:** an existing empty fixture passes validation but then raises unhandled `FileExistsError`; make directory creation/error handling match the documented contract.
- **R-08 / low:** `evidence/P1-TOOL-BRANCH01/README.md` contains stale absence claims, an impossible test count and stale production-main hashes; refresh from canonical records.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not update `branch-evidence.json`, run a passing branch/role gate, create or edit `merge.json`, edit `independent-test.json`, change the bound source commit, edit `TASKS.json`, `STATE.md`, ADRs or UI code, push to main, force-push, self-merge, or merge PR #1. The review failed, so independent certification and merge remain prohibited. No second clean runner or independent static-analysis service was available; the wrong-repository path was tested with deterministic local metadata rather than an external GitHub repository.

OPEN RISKS & SURPRISES: All existing tests and T-01–T-05 probes pass, but they do not cover the four blocking bypasses. The current `031524f..a4c0ae7` delta is evidence-only; R-02 is a reusable gate defect that would accept future post-review code changes. Production `origin/main` remained `c2c6c5fecd3f8f8b55e5d0aa36fab9024f20acc1` before and after review. PR #1 remains OPEN. GitHub mergeability was UNKNOWN at dispatch and no merge was attempted.

EXACT NEXT STEP: Integrator: do not merge PR #1. Return R-01 through R-04 to the Release-CI-Engineer for implementation attempt 3, require regression negatives plus a fresh independent Test-Engineer pass and Reviewer pass, keep `branch-evidence.json` at `state=implemented` and `independent_evidence=false` until those gates pass, and only then perform the separately authorized Integrator merge and canonical merge-record workflow.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `evidence/P1-TOOL-BRANCH01/review.json`
2. `evidence/P1-TOOL-BRANCH01/branch-evidence.json`
3. `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer-adversarial.txt`
4. `/tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer_adversarial.py`
5. `evidence/P1-TOOL-BRANCH01/independent-test.json`
6. `.harness/HANDOFFS/test-engineer-to-reviewer-P1-TOOL-BRANCH01-2.md`
7. `.harness/TASKS.json` task `P1-TOOL-BRANCH01`

CONTEXT I WISH I HAD HAD: Tests that mutate the final PR head, independent-evidence flag, PR repository and offline merge record would have exposed these defects before independent testing. Future review fixtures should model evidence-only commits separately from implementation commits and should require live/authoritative merge verification for any merged-state PASS.
