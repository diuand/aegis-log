# Bug report: the ten seeded bugs

The baseline (tag `baseline-vulnerable`) plants ten bugs on purpose. Each
has regression tests in `tests/test_seeded_bugs.py` that fail on the
baseline (`docs/evidence/baseline-red.txt`). Each fix PR adds its full
section below and closes the ID in `tests/bug_ledger.py`.

| ID | Bug | Risk | Status |
|---|---|---|---|
| B-01 | Hardcoded intel API key | R-01 | fixed (PR #6) |
| B-02 | SQL injection in `/events/search` | R-02 | fixed (PR #7) |
| B-03 | Path traversal in `/reports/<name>` | R-02 | fixed (PR #8) |
| B-04 | Unsafe YAML rule loading | R-03 | fixed (PR #9) |
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

## B-02, SQL injection in `/events/search`

- **Risk IDs / CWE / ATT&CK:** R-02 / CWE-89 (SQL injection) / T1190 (exploit public-facing application)
- **Where (on tag `baseline-vulnerable`):** `aegis/store.py:39` (f-string query), reached from `aegis/routes.py:37-39` (`user` query parameter).
- **How it was introduced:** an f-string is the most natural way to write "find this user" in Python, and it works for every normal name, so tests with ordinary data pass.
- **How it can be exploited (safe reproduction):** `GET /events/search?user=x' OR '1'='1` returns every stored event (all users, all source IPs); `user=' UNION SELECT ... --` reads values from outside the events table; a name with an apostrophe (`o'neil`) crashes the request with a 500. Reproduction: `tests/test_seeded_bugs.py::test_b02_*` fail on the baseline (`assert 2 == 0`, `assert 500 == 200`).
- **Impact on this app (C/I/A):** C high (any caller dumps the whole event store), I medium (SQLite allows stacked writes through other APIs; here the read path is the main risk), A medium (crafted input crashes the endpoint).
- **Blast radius beyond this app:** the event store holds usernames, internal IPs and threat-intel matches, which maps the network for an attacker and shows which of their IPs are already detected. Chains with B-06 (no authentication: anyone on the host can query) and B-05 (attacker-controlled usernames are stored unvalidated, ready for second-order injection).
- **Likelihood x Impact before / after (R-02):** 4 x 4 = 16 (High) -> 3 x 4 = 12 after this PR; B-03 closes the rest of R-02.
- **The fix (PR #7):** `search_by_user` passes the value as a bound parameter (`WHERE user = ?`), so SQLite treats it as data. The tracked bandit exception (`nosec B608`) is removed with the bug.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b02_tautology_does_not_dump_every_event`, `::test_b02_quote_in_a_name_is_treated_as_data`, `::test_b02_union_cannot_read_outside_the_events_table` pass; bandit is clean on `aegis/` with no exception.
- **Residual risk:** other queries could be added later with string building; the `CLAUDE.md` banned-patterns table, `review.py` and bandit (B608) all flag that. Exact-match search still lets an authenticated caller enumerate users one guess at a time.

## B-03, Path traversal in `/reports/<name>`

- **Risk IDs / CWE / ATT&CK:** R-02 / CWE-22 (path traversal) / T1190 (exploit public-facing application), T1005 (data from local system)
- **Where (on tag `baseline-vulnerable`):** `aegis/routes.py:43` (`<path:name>` converter accepts slashes) and `aegis/routes.py:45` (`os.path.join(reports_dir, name)`).
- **How it was introduced:** `os.path.join` reads like safe path handling, and `<path:...>` lets reports live in sub-folders. Two less-known facts make it dangerous: `..` segments walk out of the folder, and joining an absolute path discards the base entirely.
- **How it can be exploited (safe reproduction):** `GET /reports/..%2Fsecret.txt` returns a file next to the reports folder; `GET /reports/<url-encoded absolute path>` returns any file the service can read (source, `.env`, SSH keys). The tests plant a harmless marker file outside `reports/` and fetch it. Reproduction: `tests/test_seeded_bugs.py::test_b03_*` fail on the baseline (`assert 200 == 404`).
- **Impact on this app (C/I/A):** C high (arbitrary file read as the service user), I none directly, A low.
- **Blast radius beyond this app:** the readable files include `.env` (B-01's key after its fix, plus `AEGIS_API_KEY`), the SQLite store and the user's home directory, so one request can undo the secret hygiene from B-01 and the auth from B-06. On a shared analyst workstation it exposes other projects too.
- **Likelihood x Impact before / after (R-02):** 3 x 4 = 12 after B-02 -> 1 x 4 = 4 (Low) with both fixed.
- **The fix (PR #8):** the route uses the plain `<name>` converter (no slashes reach the handler); `aegis.reports.resolve_report()` accepts only names matching `[a-z0-9][a-z0-9-]{0,63}\.txt`, resolves the path (following symlinks) and refuses anything that is not inside `reports/` and an existing file. Every refusal is a plain 404, so the response does not reveal which check failed.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b03_dotdot_cannot_leave_reports_dir`, `::test_b03_absolute_path_cannot_be_requested`, `::test_b03_only_allowlisted_report_names_are_served` pass; `tests/test_reports_hardening.py` tests the resolver directly with traversal, Windows paths, hidden files and an outward symlink.
- **Residual risk:** anyone who can write into `reports/` decides what is served (keep it owned by the service). The allowlist is a pattern, not a fixed list, so any new `.txt` report is served automatically; that is intended.

## B-04, Unsafe YAML rule loading

- **Risk IDs / CWE / ATT&CK:** R-03 / CWE-502 (deserialization of untrusted data), CWE-754 (improper check for exceptional conditions, the silent skip) / T1059.006 (command and scripting interpreter: Python)
- **Where (on tag `baseline-vulnerable`):** `aegis/rules.py:16` (`yaml.load(fh, Loader=yaml.Loader)`), `aegis/rules.py:39-42` (`except Exception: continue` around matching), `aegis/routes.py:61-65` (reload accepts whatever loads).
- **How it was introduced:** `yaml.load` with an explicit `Loader` silences PyYAML's old warning, so it looks deliberate and safe. The `try/except/continue` looks like robustness: one bad rule should not break ingest.
- **How it can be exploited (safe reproduction):** a rule file containing a `!!python/object/apply:` tag makes the loader call any importable Python function at start-up or on `POST /admin/rules/reload`, i.e. code execution as the service user. The test uses a harmless canary function that only records it was called. Separately, a rule missing `when` is accepted and then silently skipped on every event: detection is off and nothing says so. Reproduction: `tests/test_seeded_bugs.py::test_b04_*` fail on the baseline (canary tripped, reload returns 200, duplicate ids accepted).
- **Impact on this app (C/I/A):** C, I, A all high: code execution owns the process; a silently broken rule blinds the detection the service exists for.
- **Blast radius beyond this app:** whoever can write a rule (a PR, a shared rules folder, a compromised CI step via B-09) gets code execution on every analyst machine that reloads rules. Silent rule failure means attacks pass as "clean" events, so downstream reports and humans trust a blind sensor. Chains with B-06: the unauthenticated reload endpoint let anyone trigger the load.
- **Likelihood x Impact before / after:** 3 x 5 = 15 (High) -> 1 x 5 = 5 (Low).
- **The fix (PR #9):** `yaml.safe_load` (plain data only) and a strict pydantic `Rule` schema: id `AG-nnn`, severity enum, risk 1-50, only known fields, exactly one operator per condition, no unknown keys, unique ids. Any bad file raises `RuleError` and the whole set is rejected; the reload endpoint answers 400 and keeps the previous rules. The silent `except/continue` is gone. The tracked bandit exceptions (`nosec B506`, `nosec B112`) are removed.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b04_python_tags_in_rules_do_not_execute`, `::test_b04_reload_rejects_a_broken_rule_and_keeps_the_old_set`, `::test_b04_duplicate_rule_ids_are_rejected` pass; `tests/test_rules_schema.py` covers each schema rule; bandit is clean.
- **Residual risk:** a schema-valid but wrong rule (bad logic, too broad, too narrow) still passes; that is what the positive/negative samples and code-owner review on `rules/` are for. Reload errors name the file and fields, not contents.
