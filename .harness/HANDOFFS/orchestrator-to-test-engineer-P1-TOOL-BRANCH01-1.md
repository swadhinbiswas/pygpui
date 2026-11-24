FROM: Orchestrator
TO: Test-Engineer
TASK-ID: P1-TOOL-BRANCH01
ATTEMPT #: 1
STATUS: partial

WHAT I WAS ASKED: Independently verify PR #1 at bound source commit `841fb384d08f7d598c2e0ab8242cfe0643bb5d14`, artifact `5c8926a78f52b9f6b8df679ac66c62eee238ebb4dc03602abdd9b3fbe333e5cf`, registry `bff3da2e946852d3cfc1a52e237e2ee106d42222bf231992197f0aa114d65498`. Run the full test/local-gate/drill/self-test matrix and write canonical independent test evidence. Do not review your own implementation, fabricate roles, or merge.

WHAT I DID: Registered distinct implementer/reviewer/tester/Integrator sessions, refreshed the hash-bound registry approval, and had the build agent bind the new registry/artifact identity into PR #1 head `f106b5e8de7385a53dfc8a3c138147139a36e767`.

EVIDENCE: `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-1.md`; `/tmp/opencode/pygpui-P1-TOOL-BRANCH01/evidence/P1-TOOL-BRANCH01/README.md`; `/tmp/opencode/pygpui-P1-TOOL-BRANCH01/evidence/P1-TOOL-BRANCH01/branch-evidence.json`; `/tmp/opencode/pygpui-P1-TOOL-BRANCH01/evidence/P1-TOOL-BRANCH01/session-roles.json`; PR https://github.com/swadhinbiswas/pygpui/pull/1.

WHAT I DID NOT DO / SKIPPED, AND WHY: No independent test evidence exists yet. Reviewer evidence and Integrator merge remain separate later steps.

OPEN RISKS & SURPRISES: The implementation and role registry are ready, but independent evidence must bind the exact source commit/tree/artifact and registry bytes. A test failure is a valid result and must block verification.

EXACT NEXT STEP: Read `.harness/STATE.md`, this handoff, `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-1.md`, `evidence/P1-TOOL-BRANCH01/README.md`, `evidence/P1-TOOL-BRANCH01/branch-evidence.json`, `evidence/P1-TOOL-BRANCH01/session-roles.json`, `.harness/TASKS.json` task `P1-TOOL-BRANCH01`, `.harness/PROCESS.md` and `.harness/sessions/registry.json` in worktree `/tmp/opencode/pygpui-P1-TOOL-BRANCH01`; rerun the full independent matrix on PR head, write only `evidence/P1-TOOL-BRANCH01/independent-test.json` and the corresponding test hash in `branch-evidence.json`, commit/push the evidence without changing the bound source commit, and write `.harness/HANDOFFS/test-engineer-to-reviewer-P1-TOOL-BRANCH01-1.md`.

FILES THE RECEIVER MUST READ (ordered, max 7):
1. `.harness/STATE.md`
2. `.harness/HANDOFFS/orchestrator-to-test-engineer-P1-TOOL-BRANCH01-1.md`
3. `.harness/HANDOFFS/release-ci-to-test-engineer-P1-TOOL-BRANCH01-1.md`
4. `evidence/P1-TOOL-BRANCH01/README.md`
5. `evidence/P1-TOOL-BRANCH01/branch-evidence.json`
6. `evidence/P1-TOOL-BRANCH01/session-roles.json`
7. `.harness/TASKS.json` task `P1-TOOL-BRANCH01`

CONTEXT I WISH I HAD HAD: A clean Ruff installation on the independent runner. The author used `/tmp/opencode/uv-tools/ruff/bin/ruff`; use the same executable or install Ruff outside the repo and record it.
