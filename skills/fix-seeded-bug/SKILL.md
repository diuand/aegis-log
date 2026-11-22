---
name: fix-seeded-bug
description: Fix one seeded bug (B-01..B-10) end to end in its own branch and PR, with red-then-green proof, bug report entry and register update.
---

# Fix a seeded bug

Use this for exactly one bug ID per run. Never fix a second bug "while you
are there"; open another run instead.

1. **Branch.** `git switch -c fix/b-0x-short-name` from an up-to-date `main`.
2. **Reproduce.** Run the bug's tests with the ledger ignored and confirm
   they fail for the right reason:
   `AEGIS_SHOW_RED=1 .venv/bin/python -m pytest -q -k b0x`
3. **Test first.** If the existing regression tests do not cover the exploit
   path you found, add one (harmless marker, localhost only). It must be red.
4. **Fix.** Make the smallest change that removes the root cause. Follow the
   banned-patterns table in `CLAUDE.md`. No new runtime dependency without
   asking the owner.
5. **Close the ID.** Delete the bug's line from `tests/bug_ledger.py` and
   remove any scanner exception tagged `tracked: B-0x` (`# nosec`,
   `.pip-audit-ignore`). The tests are now ordinary must-pass tests.
6. **Check.** `make check` must pass. Keep the output for the PR.
7. **Document.** Add the bug's section to `docs/BUG-REPORT.md` using the
   template there (where, how introduced, exploit, impact, blast radius,
   before/after score, fix, proof, residual). Mark it fixed in the index.
8. **Register.** Update the row in `scripts/build_register.py`: control,
   residual RL/RI with the reason for each drop, evidence paths that exist,
   status `Implemented`. Run `make register`.
9. **Review.** Run `skills/review-pr` and fix every finding before opening
   the PR.
10. **PR.** Title `fix(<area>): <summary> (B-0x)`, body from the template,
    `make check` output and the agent review pasted. Merge only when CI is
    green, with a merge commit.
