# P1-GOV01 evidence

Status: complete
Owner: Orchestrator
Approval baseline: `a433d68`

## Commands

- `python3 .harness/scripts/validate_phase1_graph.py --baseline 5ce026d --self-test` — exit 0; full output in `graph-validation.txt`.
- `git remote get-url origin` — `https://github.com/swadhinbiswas/pygpui.git`; output in `remote.txt`.
- `git branch -vv` — `main` tracks `origin/main` at `a433d68`; output in `branches.txt`.
- `gh auth status` — authenticated as `swadhinbiswas` with `repo` scope; output in `github-auth.txt`.

## Governance record

`.harness/PHASE1-EVIDENCE.md` records authorized waves, readiness blockers, branch/PR policy and the four-attempt escalation rule.

## Result

Wave 0 is complete. Wave 1 may begin with `P1-SESSION-SEED01`, followed by `P1-TOOL-BRANCH01`. UI feature work remains blocked.
