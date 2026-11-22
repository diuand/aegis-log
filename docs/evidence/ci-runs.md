# CI and governance runs

GitHub Actions runs for each pull request and the governance check on
`main` (GitHub route 4: the governance run is the server-side evidence that
every commit on `main` came from a merged PR). All runs below concluded
**success**. Every PR was merged with a merge commit only after its checks
were green.

## Pull request CI (`ci.yml`: ruff + pytest + import check, bandit, pip-audit, gitleaks, zizmor)

| PR | Branch | CI run on the PR | Notes |
|---|---|---|---|
| #1 | `phase-1-risk-register` | none | no workflows existed yet (register before code) |
| #2 | `phase-2-baseline` | none | `ci.yml` arrives in #3; the planted `ci-baseline.yml` only runs from `main` |
| #3 | `phase-3-governance-ci` | [run](https://github.com/diuand/aegis-log/actions/runs/45057646190) | also triggered the planted B-09 workflow: [ci-baseline, `pull_request_target`](https://github.com/diuand/aegis-log/actions/runs/45057646583) |
| #4 | `fix/b-09-insecure-ci` | [run](https://github.com/diuand/aegis-log/actions/runs/45057805996) | last run of the insecure workflow: [ci-baseline](https://github.com/diuand/aegis-log/actions/runs/45057805989); zizmor job added here |
| #5 | `phase-4-ai-config` | [run](https://github.com/diuand/aegis-log/actions/runs/45057967863) | no `ci-baseline` run any more: B-09 is closed |
| #6 | `fix/b-01-hardcoded-key` | [run](https://github.com/diuand/aegis-log/actions/runs/45058128567) | |
| #7 | `fix/b-02-sql-injection` | [run](https://github.com/diuand/aegis-log/actions/runs/45058313021) | |
| #8 | `fix/b-03-path-traversal` | [run](https://github.com/diuand/aegis-log/actions/runs/45058482178) | symlink test runs on Linux (skipped on Windows) |
| #9 | `fix/b-04-unsafe-yaml` | [run](https://github.com/diuand/aegis-log/actions/runs/45058673498) | |
| #10 | `fix/b-05-input-validation` | [run](https://github.com/diuand/aegis-log/actions/runs/45058867893) | |
| #11 | `fix/b-06-auth-debug` | [run](https://github.com/diuand/aegis-log/actions/runs/45059076147) | |
| #12 | `fix/b-07-log-injection` | [run](https://github.com/diuand/aegis-log/actions/runs/45059264611) | |
| #13 | `fix/b-08-dependencies` | [run](https://github.com/diuand/aegis-log/actions/runs/45059455018) | pip-audit now gates with no ignores |
| #14 | `docs/phase-6-docs-verification` | see the PR's checks | this file is part of #14 |

## Governance (`governance.yml`) on `main`

One run after every merge from #3 on; all green. Latest run before #14,
[45059520535](https://github.com/diuand/aegis-log/actions/runs/45059520535), output:

```
OK      ab8efad488  PR #13: fix(deps): pin runtime dependencies and upgrade requests past known CVEs (B-08)
OK      af19c0a593  PR #12: fix(logging): one event per log line, no headers, secrets redacted (B-07)
OK      151d63cdb8  PR #11: fix(auth): require an API key on every endpoint except /health; debug off (B-06)
OK      62f6bdd555  PR #10: fix(ingest): validate events, cap body size, never crash (B-05)
OK      8f8a234e9a  PR #9: fix(rules): safe_load plus schema validation for detection rules (B-04)
OK      29ecd28b7f  PR #8: fix(reports): confine report downloads to the reports folder (B-03)
OK      7e636cc022  PR #7: fix(db): parameterize the event search query (B-02)
OK      b161293095  PR #6: fix(config): read the intel API key from the environment (B-01)
OK      9d02dc29cd  PR #5: fix(review): do not scan the files that define the agent controls
OK      c567c08c9b  PR #4: fix(ci): remove the insecure baseline workflow and lint workflows with zizmor (B-09)
OK      86c89c2560  PR #3: ci: add governance controls and lightweight CI
OK      ef107f6ba7  PR #2: feat: deliberately vulnerable baseline with seeded bugs B-01..B-10
OK      51cebdb000  PR #1: docs(register): risk register first, before any code
EXEMPT  fc33a92da5  root commit: chore: initialize repository

All 14 commits on main are accounted for.
```

PR #5 showed its last commit's subject as its title at the time of this run;
it was renamed afterwards to the phase 4 title
("feat(agent): AI configuration, memory, skills and enforced guardrails; fix B-10").

## What the server does not enforce

On a private repository on GitHub Free there is no branch protection: a
direct push to `main` would be accepted by GitHub and only turn the
governance run red afterwards. The local refusals are in
`push-refused-local.txt`; see `docs/PROJECT.md` section 5.
