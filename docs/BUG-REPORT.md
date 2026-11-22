# Bug report: the ten seeded bugs

The baseline (tag `baseline-vulnerable`) plants ten bugs on purpose. Each
has regression tests in `tests/test_seeded_bugs.py` that fail on the
baseline (`docs/evidence/baseline-red.txt`). Each fix PR adds its full
section below and closes the ID in `tests/bug_ledger.py`.

| ID | Bug | Risk | Status |
|---|---|---|---|
| B-01 | Hardcoded intel API key | R-01 | fixed (PR #6) |
| B-02 | SQL injection in `/events/search` | R-02 | open |
| B-03 | Path traversal in `/reports/<name>` | R-02 | open |
| B-04 | Unsafe YAML rule loading | R-03 | open |
| B-05 | No ingest validation or size cap | R-04 | open |
| B-06 | No authentication; `debug=True` | R-05 | open |
| B-07 | Log injection and secrets in logs | R-06 | open |
| B-08 | Unpinned and vulnerable dependencies | R-07 | open |
| B-09 | Insecure CI workflow | R-08 | fixed (PR #4) |
| B-10 | Poisoned agent memory; no agent permission rules | R-09 | fixed (PR #5) |

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

## B-10, Poisoned agent memory and no agent permission rules

- **Risk IDs / CWE / ATT&CK:** R-09 / MITRE ATLAS AML.T0051 (LLM prompt injection, here through persistent context: memory poisoning) / no CWE fits exactly; closest is CWE-1427 (improper neutralization of input used for LLM prompting).
- **Where (on tag `baseline-vulnerable`):** `.claude/memory/workflow-shortcuts.md:3-5` (the note), `CLAUDE.md:5` (imports it into every session); `.claude/settings.json` absent (no deny rules, no hooks).
- **How it was introduced:** the note reads like a harmless team preference ("the owner prefers speed"). Memory files were never reviewed, so nothing questioned it, and it sat in the one place the agent always reads.
- **How it can be exploited (safe reproduction):** the note itself is inert text and runs nothing. The exploit is behavioural: an agent that trusts its memory would push small changes straight to `main`, skip tests and commit with hook bypasses, defeating R-10's controls from inside. Reproduction: `tests/test_seeded_bugs.py::test_b10_*` fail on the baseline (the note matches the poison pattern; `.claude/settings.json` and the guard do not exist).
- **Impact on this app (C/I/A):** I high (unreviewed code lands on `main`), C medium (nothing stopped the agent from reading `.env`), A low.
- **Blast radius beyond this app:** a poisoned instruction persists across every session and every developer who uses the agent on this repo. It chains with B-09 (a CI change pushed without review) and B-01 (an agent allowed to read `.env` can paste a real key into a commit or a chat). If the repository is used as context elsewhere, the note travels with it.
- **Likelihood x Impact before / after:** 3 x 4 = 12 (Medium) -> 2 x 4 = 8 (Medium).
- **The fix (PR #5):** the note is deleted and `CLAUDE.md` now imports only `memory/MEMORY.md`. Memory and skills live in `memory/` and `skills/`, owned by CODEOWNERS, so changes need a PR. `.claude/settings.json` adds deny rules (push to main, force push, hook bypass, `.env` and `secrets/` reads, guardrail edits) and a `PreToolUse` hook (`.claude/hooks/guard.sh` -> `guard.py`) that checks every Bash, Read, Edit, Write, Grep call and fails closed. The original note is kept quarantined in `memory/quarantined-workflow-shortcuts.md` as a record, marked so it is never imported.
- **Why prose alone is not a control:** `CLAUDE.md` saying "never push to main" is advice the model may weigh against other context, including a poisoned note. The deny rules and the hook run outside the model: the tool call is refused before it executes, whatever the context says.
- **Proof the fix works:** `docs/evidence/hook-blocked.txt` (real PreToolUse payloads: pushes to main, force pushes, hook bypass, `.env` reads and guardrail edits blocked; ordinary work allowed; malformed input blocked); `tests/test_seeded_bugs.py::test_b10_*` now pass; `tests/test_agent_guard.py`.
- **Residual risk:** a human can still edit `.claude/settings.json` or run git without the agent; review of memory PRs depends on the owner's attention (not required on GitHub Free). The guard parses commands with simple rules; an obfuscated command (for example built through variables) could slip past it, which is why the git-level pre-push hook and the governance workflow stay in place as further layers.

## B-01, Hardcoded intel API key

- **Risk IDs / CWE / ATT&CK:** R-01 / CWE-798 (use of hard-coded credentials) / T1552.001 (unsecured credentials: credentials in files)
- **Where (on tag `baseline-vulnerable`):** `aegis/config.py:10` (`INTEL_API_KEY = "aegk_..."`), used at `aegis/config.py:32`.
- **How it was introduced:** a module-level constant next to the other settings looks like configuration, and it "just works" on every machine. bandit does not flag it, because its hardcoded-password check only looks at names containing `password`, `secret` or `token`, not `KEY`.
- **How it can be exploited (safe reproduction):** anyone with read access to a clone, fork, CI log or backup reads the key from `aegis/config.py` or from history (`git log -p -S aegk_`). With a real MISP key that means reading or poisoning the team's threat intel. Reproduction: `tests/test_seeded_bugs.py::test_b01_*` fail on the baseline; `gitleaks git --config .gitleaks.toml` reports `aegis-intel-key` at commit `d2981ef`.
- **Impact on this app (C/I/A):** C high (the provider credential is public to every reader), I medium (a stolen key can add false indicators that change `risk_score`), A low.
- **Blast radius beyond this app:** the key belongs to the intel platform, not to aegis-log, so the damage lands on every system that trusts that platform's indicators. It chains with B-09 (any injected CI step can read it), B-07 (keys travelled into logs) and B-10 (an unrestricted agent could paste it into a prompt or commit). Rotating it needs the platform owner, and history keeps the old value forever.
- **Likelihood x Impact before / after:** 4 x 4 = 16 (High) -> 2 x 4 = 8 (Medium).
- **The fix (PR #6):** `aegis/config.py` reads `AEGIS_INTEL_API_KEY` from the environment or the git-ignored `.env` (a small KEY=VALUE parser, no extra dependency); the default is empty. `.env.example` documents the variable with an empty placeholder, and `make setup` creates `.env` from it. gitleaks (default rules plus the `aegk_` rule) runs in pre-commit and in CI since phase 3; `.gitleaksignore` exempts only the seeded commit's exact fingerprint, so any new occurrence is still reported.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b01_no_credential_literal_in_source`, `::test_b01_intel_key_comes_from_environment`, `::test_b01_intel_key_is_empty_when_not_configured` pass; `docs/evidence/gitleaks-refused.txt` shows a freshly generated key being refused; the CI `gitleaks` job scans full history on every PR.
- **Residual risk:** the fake key stays in git history by design (the bug must stay reproducible); with a real key the only fix would be rotation. A developer can still skip the local hook; CI catches the push afterwards, but by then the key is on GitHub and must be rotated. `.env` on a laptop is plaintext; SOPS/age was not added (optional in the spec).
