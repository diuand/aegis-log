# Contributing

## Ground rules

1. **Never commit to `main`.** Work on a branch: `phase-n-topic`, `fix/b-0x-short-name`, `docs/...`.
2. **Every change reaches `main` through a pull request**, merged with a merge commit, that cites the risk IDs (`R-xx`) and bug IDs (`B-xx`) it touches.
3. **`make check` must pass** before the PR is opened; paste its output into the PR. Merge only when CI is green.
4. **No force pushes. Never skip hooks.** Do not disable a check or weaken a test to make it pass.
5. **One seeded bug per fix PR.** A seeded bug is never fixed quietly inside another change.

## Setup

```bash
make setup    # .venv + runtime and dev dependencies
make hooks    # installs the pre-commit AND pre-push hooks (needs gitleaks on PATH)
```

| Hook | Stage | What it stops |
|---|---|---|
| `no-commit-to-branch` | commit | commits made directly on `main` |
| `gitleaks` | commit | secrets in staged changes (default rules plus the `aegk_` key format) |
| `detect-private-key`, `check-added-large-files`, `check-yaml` | commit | keys, large binaries, broken YAML |
| `protect-main-push` | push | pushes to `main`, deleting `main`, force pushes |

## Commit messages: Conventional Commits

```
<type>(<optional scope>): <summary in the imperative>

<why, in plain language>

Refs: R-02 B-03
```

Types used here: `feat`, `fix`, `docs`, `test`, `ci`, `chore`, `refactor`.

## Pull requests

Fill in every line of the PR template's self-review checklist ("n/a" is
fine where it applies). From phase 4 on, run `skills/review-pr` locally and
paste its output under "Agent review".
