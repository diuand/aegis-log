# Bug report: the ten seeded bugs

The baseline (tag `baseline-vulnerable`) plants ten bugs on purpose. Each
has regression tests in `tests/test_seeded_bugs.py` that fail on the
baseline (`docs/evidence/baseline-red.txt`). Each fix PR adds its full
section below and closes the ID in `tests/bug_ledger.py`.

| ID | Bug | Risk | Status |
|---|---|---|---|
| B-01 | Hardcoded intel API key | R-01 | open |
| B-02 | SQL injection in `/events/search` | R-02 | open |
| B-03 | Path traversal in `/reports/<name>` | R-02 | open |
| B-04 | Unsafe YAML rule loading | R-03 | open |
| B-05 | No ingest validation or size cap | R-04 | open |
| B-06 | No authentication; `debug=True` | R-05 | open |
| B-07 | Log injection and secrets in logs | R-06 | open |
| B-08 | Unpinned and vulnerable dependencies | R-07 | open |
| B-09 | Insecure CI workflow | R-08 | fixed (PR #4) |
| B-10 | Poisoned agent memory; no agent permission rules | R-09 | open |

---

## B-09, Insecure CI workflow

- **Risk IDs / CWE / ATT&CK:** R-08 / CWE-829 (inclusion of functionality from an untrusted control sphere) / T1195.002 (compromise software supply chain)
- **Where (on tag `baseline-vulnerable`):** `.github/workflows/ci-baseline.yml:4` (`pull_request_target`), `:7` (`permissions: write-all`), `:13-15` (checkout of `github.event.pull_request.head.sha`), `:13` and `:16` (actions referenced by the moving tags `@v4` and `@v5`).
- **How it was introduced:** it looks like an ordinary test workflow. `pull_request_target` is often copied from examples because it "makes PRs from forks work" (it gives them secrets and a write token), and `@v4` reads like a sensible version pin.
- **How it can be exploited (safe, not performed against GitHub):** `pull_request_target` runs in the context of the base repository with its secrets and a token. Combined with `write-all` and a checkout of the PR's head commit, any PR author's code (for example a modified `tests/conftest.py`) runs with a token that can push to `main`, create releases or rewrite workflows. Separately, whoever controls the `actions/checkout` repository can move the `v4` tag to new code, which then runs with the same token. Reproduction: `zizmor` on the baseline file reports `dangerous-triggers`, two `unpinned-uses` and `artipacked`; `tests/test_seeded_bugs.py::test_b09_*` fail on the baseline.
- **Impact on this app (C/I/A):** C high (repository secrets readable), I high (attacker can push code that later runs on analysts' machines), A medium (workflows and releases can be deleted).
- **Blast radius beyond this app:** the CI token is a supply-chain key: a malicious commit to `main` reaches every clone, and the professor's machine when the repo is graded. It chains with B-01 (a key in the repo becomes readable by the injected step) and with R-10 (on GitHub Free there is no branch protection to stop a pushed commit). The AI agent would also pull the poisoned code as context.
- **Likelihood x Impact before / after:** 3 x 5 = 15 (High) -> 1 x 5 = 5 (Low).
- **The fix:** PR #4 deletes `ci-baseline.yml`. `ci.yml` (added in phase 3) uses `pull_request` only, declares `permissions: contents: read`, pins every action to a full commit SHA with the tag in a comment, sets `persist-credentials: false`, and a new `workflow-lint` job runs `zizmor` on every PR, with online audits that check each pinned SHA belongs to its action.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b09_no_workflow_uses_pull_request_target`, `::test_b09_workflow_tokens_are_least_privilege`, `::test_b09_every_action_is_pinned_to_a_full_sha` are now ordinary must-pass tests; the CI `zizmor` job is green on this PR.
- **Residual risk:** a pinned SHA is only as trustworthy as the code it points to; updates must be reviewed (Dependabot is not enabled). Someone with write access can still edit a workflow; CODEOWNERS requests review on `.github/` but cannot require it on GitHub Free.
