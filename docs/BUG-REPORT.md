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
| B-09 | Insecure CI workflow | R-08 | open |
| B-10 | Poisoned agent memory; no agent permission rules | R-09 | open |
