# Put the tracking tag before `nosec`

**Correction.** Phase 3 annotated tracked findings as
`# nosec B608 - tracked: B-02`. Bandit parses every word after `nosec` as a
test ID, so `make check` printed warnings like "B is not a test name or id"
and the real signal got buried.

**Rule.** Write `# tracked: B-02 # nosec B608`. The tracking tag comes first;
only test IDs follow `nosec`. `tests/test_tracked_exceptions.py` finds the
tag anywhere on the line and fails if it names a closed bug.
