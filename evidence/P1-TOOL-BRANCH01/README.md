# P1-TOOL-BRANCH01 — attempt 3

Status: **partial**. R-01 through R-08 are addressed and author-run controls pass. Fresh independent test/review and Integrator merge remain pending.

## Identity

| Field | Value |
|---|---|
| Task | `P1-TOOL-BRANCH01` |
| Branch | `feat/P1-TOOL-BRANCH01-tooling` |
| Worktree | `/tmp/opencode/pygpui-P1-TOOL-BRANCH01` |
| Dispatch baseline | `15d29b32a066eeab7f4fdcc9b8a02456c4c0434f` |
| Bound source commit | `64ad0559fad5ffcf2f9a60aa028cb8698aaec141` |
| Bound source tree | `385946388f2d087a709baa871d25f07f76bdae3a` |
| Branch artifact | `P1-TOOL-BRANCH01-branch` |
| Artifact SHA-256 | `b52037513ac6b7e80fc202cfd2aa5c729af442807641fb553d84d64dc35908fc` |
| Approved registry SHA-256 | `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498` |
| PR | https://github.com/swadhinbiswas/pygpui/pull/1 |

Registered roles remain implementer `ses_df2be4996ffek8O5wu7RwOeubn`, reviewer `ses_df27261c9ffcukQUulA8P0LN89`, tester `ses_df27261c9ffdiy0RA5Ko2oSdxl`, and Integrator `ses_df27261c8ffeJbVXcZMsund3Hf`. The registry and approval were not changed in attempt 3.

## Preserved historical evidence

- Attempt-1 test fail: `attempt-1/independent-test.json`, SHA-256 `cd60953cac91f9b667d6e58704241b457dc05226f72cb31b5e531fdbec03a3a4`.
- Attempt-2 test pass: `attempt-2/independent-test.json`, SHA-256 `7d48be25ea27b6724e954ef042ad50e2a01f25c42d82894162ad0887449b17c5`.
- Attempt-2 review fail: `attempt-2/review.json`, SHA-256 `1e20e25db6550c6088526c06e1be85bf5365aaf9ddd28d1be493e4a410d2dc08`.
- Exact reviewer adversarial script/log: `attempt-2/reviewer_adversarial.py` SHA-256 `88792de51c9b35fc6bc8b0db4a3c48ecf7225b160163e2748b753d2f893adb05`; `attempt-2/reviewer-adversarial.txt` SHA-256 `a44e671530d7934c39f8352ede6014c2d3e9970b53018f6d85b5b1c21355a5d5`.

Canonical attempt-3 `review.json`, `independent-test.json`, and `merge.json` are absent. `branch-evidence.json` has null reviewed-head/review/test identities, `state=implemented`, and `independent_evidence=false`.

## R-01–R-08 controls

- **R-01:** pre-merge pass requires `independent_evidence is True`; false, missing, null, string, and integer values reject.
- **R-02:** review and branch evidence must repeat reviewer-attested `reviewed_head_commit`/`reviewed_head_tree`. The reviewed head must contain the source and be ancestral to the final branch/PR head. Every post-reviewed-head path must be under `evidence/P1-TOOL-BRANCH01/`; implementation changes reject before pre-merge or merged pass.
- **R-03:** merged verification requires an expected merge SHA, PR head ancestry to the merge commit, merge reachability from `main` or `origin/main`, and live canonical GitHub metadata by default. `--offline` cannot return merged PASS.
- **R-04:** PR selectors must be canonical GitHub URLs whose owner/repository matches `origin`; option-like, numeric, and wrong-repository selectors reject before `gh`.
- **R-05:** review/test record roles must be independent-reviewer/tester roles and match assigned sessions.
- **R-06:** red main is pushed to the fixture remote, verified by `git ls-remote`, cloned, and gated red; restored green is pushed, cloned, and gated green.
- **R-07:** an existing empty fixture directory is accepted and initialized without traceback.
- **R-08:** this README is rebuilt from the committed attempt-3 records and logs.

## Exact author-run outputs

### Tests-first

```text
$ python3 -m pytest tools/ci/tests/test_branch_gate.py tools/ci/tests/test_record_merge.py tools/ci/tests/test_drills.py
22 failed, 45 passed in 9.01s
```

Evidence: `tests-first-attempt-3.txt`.

### Reviewer probes

The exact archived reviewer script was rerun unchanged. It rejected R-01 and R-05, then failed closed at R-02 with:

```text
REJECTED independent_evidence_false: GateError('branch evidence independent_evidence must be boolean true')
REJECTED contradictory_record_roles: GateError('review record role is not an independent reviewer')
tools.ci.common.GateError: post-review implementation changes are forbidden: ['.harness/sessions/registry.json', '.harness/sessions/seed-approval.json', 'fixture.txt']
```

That script does not catch expected exceptions for its later direct-call probes, so it exits `1` at the first expected R-02 rejection instead of printing a final summary. It reported no accepted bypass. Exact output: `reviewer-adversarial-attempt-3.txt`.

A clearly labeled author-run guarded probe then exercised all seven control areas:

```text
PASS R-01-independent-flag
PASS R-05-record-roles
PASS R-02-unreviewed-descendant
PASS R-03-offline-forged-merge
PASS R-04-wrong-repository
PASS R-06-remote-red-green: pushes=3
PASS R-07-existing-empty: accepted
AUTHOR_REVIEWER_PROBES_SUMMARY={"author_run": true, "failed": [], "independent_evidence": false, "passed": true, ...}
```

Evidence: `attempt-3/reviewer-probes-author.py`, `reviewer-probes-author-attempt-3.txt`. This is remediation evidence, not independent certification.

### Format, lint, tests, graph

```text
$ /tmp/opencode/uv-tools/ruff/bin/ruff format --check tools
20 files already formatted

$ /tmp/opencode/uv-tools/ruff/bin/ruff check tools
All checks passed!

$ python3 -m pytest tools/ci/tests
120 passed in 5.36s

$ python3 -m pytest -q
88 passed, 18 subtests passed in 12.75s

$ PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
208 passed, 18 subtests passed in 26.58s
VALIDATION=PASS
LOCAL_GATE=PASS steps=fmt,lint,tests,graph
```

Evidence: `fmt.txt`, `lint.txt`, `pytest.txt`, `root-pytest.txt`, `local-gate.txt`, `graph-validation.txt`.

### Self-tests

Every command exited zero:

```text
SESSION_SEED_VERIFY=PASS
SESSION_SEED_SELF_TEST=PASS
BRANCH_GATE_SELF_TEST=PASS
RECORD_MERGE_SELF_TEST=PASS
REGISTER_ROLES_SELF_TEST=PASS
SESSION_ROLES_SELF_TEST=PASS
RED_MAIN_DRILL_SELF_TEST=PASS
ROLLBACK_DRILL_SELF_TEST=PASS
TAG_POINT_SELF_TEST=PASS
LOCAL_GATE_SELF_TEST=PASS
```

The local-gate self-test deliberately prints one expected fail-fast fixture line before its PASS.

### Fresh fixture drills

```text
$ python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-attempt-3
RED_MAIN_DRILL=PASS fixture=/tmp/opencode/red-main-attempt-3 red_main=afbab3d6830079036774374443e9c83cfa5c8e6d restored_green=1ebe438876472342d8c2fbeff5dcc9cf529ea7a0 production_unchanged=true

$ python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-attempt-3 --tag phase1/contracts-premerge
ROLLBACK_DRILL=PASS fixture=/tmp/opencode/rollback-attempt-3 tag=phase1/contracts-premerge revert=c00b7b311746f05e5911b25da001220e413c8a1f revert_of_revert=751f3c56c3431764a85bb9fd45ac8b48bfae974d restored_green=b2d5e2aafc2993e7d218810f0dd1cd8b6094e0f1 production_unchanged=true
```

Red-main remote state was `afbab3d...` with a cloned remote gate failure, then `1ebe438...` with a cloned remote gate pass. Three pushes were archived. Rollback archived tag `867cea8501b63a76f53877cb1538aef299ecc02c`, reviewed merge `7363e5f6711fea959c05d61176d87699088e640c`, injected failure `9a5e5177832f43c0471b1a215c78db67d9285c65`, revert, revert-of-revert, re-merge, and restored green. Durable copies are under `attempt-3/red-main/**` and `attempt-3/rollback/**`.

### Production main integrity

```text
$ git ls-remote origin refs/heads/main
88417230087ffaa09f0565ea5d4bbf72f34d1e44	refs/heads/main

$ git rev-parse origin/main
88417230087ffaa09f0565ea5d4bbf72f34d1e44
```

Both values were identical before and after the drills. Evidence: `production-main-after.txt`, `production-origin-main-after.txt`.

## Current independent-gate disposition

```text
$ python3 tools/ci/branch_gate.py verify --task P1-TOOL-BRANCH01 --state independently_verified --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
BRANCH_GATE_REJECT code=state message=branch evidence is not independently_verified
(exit 3)

$ python3 tools/session/verify_roles.py --task P1-TOOL-BRANCH01 --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
SESSION_ROLES_REJECT code=state message=branch evidence is not independently_verified
(exit 3)
```

Evidence: `branch-gate-verify-attempt-3.txt`, `verify-roles-attempt-3.txt`, `branch-evidence-binding.txt`.

## Independent retest commands

Run against the final PR head recorded in the attempt-3 handoff:

```bash
python3 .harness/scripts/seed_session_registry.py --verify
python3 -m pytest tools/ci/tests
PYGPUI_RUFF=/tmp/opencode/uv-tools/ruff/bin/ruff python3 tools/ci/run_local_gate.py --mode full
python3 tools/ci/branch_gate.py --self-test
python3 tools/ci/record_merge.py --self-test
python3 tools/session/register_roles.py --self-test
python3 tools/session/verify_roles.py --self-test
python3 /tmp/opencode/P1-TOOL-BRANCH01-review-ses_df27261c9ffcukQUulA8P0LN89/reviewer_adversarial.py
python3 tools/ci/red_main_drill.py --fixture /tmp/opencode/red-main-attempt-3-independent
python3 tools/ci/rollback_drill.py --fixture /tmp/opencode/rollback-attempt-3-independent --tag phase1/contracts-premerge
```

The archived reviewer script is expected to fail closed by raising at the first fixed bypass; the independent reviewer should capture that as rejection or use the guarded probe pattern rather than treating an expected `GateError` as a harness failure.

Fresh review/test records must bind source `64ad0559fad5ffcf2f9a60aa028cb8698aaec141`, tree `385946388f2d087a709baa871d25f07f76bdae3a`, artifact `b52037513ac6b7e80fc202cfd2aa5c729af442807641fb553d84d64dc35908fc`, registry `bff3da2e...`, named branch, and exact roles. The reviewer must additionally attest `reviewed_head_commit`/`reviewed_head_tree`; only canonical task-evidence commits may follow that head.

After fresh records exist and branch evidence is assembled with `state=independently_verified` and `independent_evidence=true`:

```bash
python3 tools/ci/branch_gate.py verify --task P1-TOOL-BRANCH01 --state independently_verified --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
python3 tools/session/verify_roles.py --task P1-TOOL-BRANCH01 --evidence evidence/P1-TOOL-BRANCH01/branch-evidence.json
```

Merged verification additionally requires the expected merge SHA and live GitHub metadata; offline merged PASS is prohibited.

## Residual risks

1. Attempt 3 is the last routine fix round. Fresh independent test and review are still mandatory; author probes are not certification.
2. The exact reviewer script lacks expected-exception guards for R-02/R-03/R-04 and therefore aborts on the first correct rejection. This limitation is preserved and disclosed rather than worked around in production code.
3. Ruff remains an external dependency at `/tmp/opencode/uv-tools/ruff/bin/ruff`.
4. The trust root remains the approved local registry/approval pair; the later registry task owns stronger infrastructure.
5. No merge, direct/force push to `main`, or independent pass evidence was produced.
