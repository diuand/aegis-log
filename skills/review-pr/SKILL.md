---
name: review-pr
description: Review the current branch against main before opening a PR. Mechanical banned-pattern pass plus a judgement pass; output goes under "Agent review" in the PR.
---

# Review a branch before opening its PR

This is an agent-assisted review, not an enforced gate (no model API key is
available and Copilot code review is not part of Copilot Free). It is run
locally, by the agent or the owner, before every PR.

## 1. Mechanical pass

```bash
.venv/bin/python skills/review-pr/review.py          # compares HEAD with main
.venv/bin/python skills/review-pr/review.py --base origin/main
```

`review.py` diffs the branch against the base and reports:
- added lines that match a banned pattern from `CLAUDE.md` (keys, f-string
  SQL, `yaml.load`, `debug=True`, `0.0.0.0`, tag-pinned actions,
  `pull_request_target`, `write-all`, hook bypasses);
- sensitive paths touched (`.github/`, `.claude/`, `memory/`, `skills/`,
  `rules/`, `CLAUDE.md`), which need the owner's attention;
- commits that cite no `R-xx` / `B-xx` ID;
- service code changed without a test change.

## 2. Judgement pass (answer each in one line)

1. Does the change do what the PR title says, and nothing else?
2. Is a seeded bug fixed outside its own PR?
3. Is any test weakened, skipped or deleted to make the suite green?
4. Do the new tests exercise the real exploit path, not a mock of it?
5. Could the change open a new path to a risk in the register?
6. Are error messages free of stack traces, paths and secrets?
7. Does the register row's residual score match what the control really does?
8. Is the evidence real, small and masked?
9. Would the owner be able to explain this change in an oral exam?

## 3. Output

Paste the `review.py` output and the nine answers under "Agent review" in
the PR. Fix every finding before the PR is opened; if a finding is accepted
instead, say why in the PR.
