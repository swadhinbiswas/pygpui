FROM: Test-Engineer
TO: Reviewer
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 1
STATUS: done

WHAT I WAS ASKED: Independently verify PR #1 at bound source commit `841fb384d08f7d598c2e0ab8242cfe0643bb5d14`, source tree `a59b49f159b46204a5ffaf6c111b3b44f6fff9d8`, artifact `5c8926a78f52b9f6b8df679ac66c62eee238ebb4dc03602abdd9b3fbe333e5cf`, and registry `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498`; rerun the full matrix and fresh fixture drills, inspect fail-closed behavior, write canonical independent evidence, update only its test hash, and hand off without merging.

WHAT I DID: Ran seed verify/self-test, `python3 -m pytest tools/ci/tests`, the full local gate, all tool self-tests, and fresh independent red-main/rollback drills. The required matrix passed: 76 focused tests; 164 combined tests plus 18 subtests; graph `VALIDATION=PASS`; every self-test passed; both drills restored green and reported `production_unchanged=true`. I then ran five independent adversarial fail-closed probes. All five failed, revealing blocking defects T-01 through T-05. I wrote `decision=fail` evidence, updated only `branch-evidence.json`'s test SHA-256, committed/pushed the two evidence files, and left `state=implemented` and `independent_evidence=false`.

EVIDENCE: `evidence/P1-TOOL-BRANCH01/independent-test.json` SHA-256 `cd60953cac91f9b667d6e58704241b457dc05226f72cb31b5e531fdbec03a3a4`; `evidence/P1-TOOL-BRANCH01/branch-evidence.json` SHA-256 `9a32635f33f7f1e3de2dc74ccded0eb5ba6d664c85379fcacb93058b4ddf98e3`; adversarial script `/tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial_checks.py` SHA-256 `eb7f189a43b35b1e0bb7c0b2b27f646b001f95dd1ea39120a64d22187e4c9ab7`; adversarial log SHA-256 `d44594d47e89a4d3f2e33c3ec904096b3940a58ce1ad50f5db6913ee4676b52c`; red-main archive SHA-256 `a8f16de20bebc5d51bc6965349ad9e672da767f6ffd0b5116c1ac2048f4bf86b`; rollback archive SHA-256 `68f3a22162b1a449e5308b4d33d24f8acd0efa00f46578de9e3630ca3e105d38`. Evidence commit and new PR head: `51a17f78dc939ffc58757b54357a4c47de4d606c`. Production `origin/main` remained `4e69db8e6683a025f3adc672e3a4cb54d1ffb26d` before and after all checks.

WHAT I DID NOT DO / SKIPPED, AND WHY: I did not fix implementation defects, create `review.json` or `merge.json`, change the bound source commit, edit `TASKS.json`, `STATE.md`, ADRs or UI code, modify/force-push `main`, or merge PR #1. Independent verification must remain failed until the implementation is corrected and independently retested; role registration and green author tests are not certification.

OPEN RISKS & SURPRISES: T-01: `verify_premerge` accepts evidence after the named branch is renamed, so it never proves the branch ref exists or contains the source. T-02: a trusted reviewer record with no `task_id` is accepted. T-03: a review record with a contradictory `source_tree` is accepted after its hash is refreshed. T-04: a review record naming another valid-prefix branch is accepted. T-05: a configured nonexistent Ruff executable raises `FileNotFoundError` and exits 1 with a traceback instead of dependency exit 69. The required matrix is green, but these fail-closed gaps block a pass decision. Detailed reproductions, exact commands, outputs, log paths and hashes are in `independent-test.json`.

EXACT NEXT STEP: Reviewer: read the seven files below and PR #1 at `51a17f78dc939ffc58757b54357a4c47de4d606c`; independently reproduce or adjudicate T-01 through T-05 against the stated fail-closed contract; do not approve or advance the branch while the independent test decision is `fail`; return the defects to Release-CI-Engineer through Orchestrator for correction and a fresh independent test attempt.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `evidence/P1-TOOL-BRANCH01/independent-test.json`
2. `evidence/P1-TOOL-BRANCH01/branch-evidence.json`
3. `/tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial_checks.py`
4. `/tmp/opencode/P1-TOOL-BRANCH01-independent-ses_df27261c9ffdiy0RA5Ko2oSdxl/adversarial-checks.txt`
5. `tools/ci/evidence.py`
6. `tools/ci/common.py`
7. `tools/ci/run_local_gate.py`

CONTEXT I WISH I HAD HAD: A canonical bound-record schema that explicitly requires and validates branch/source-tree identity, plus negative tests for absent branch refs, absent role task binding, contradictory record identity, and configured-but-unexecutable Ruff. The existing 76 tests and self-tests do not cover those cases.
