"""Seeded bugs that are still open.

While an ID is listed here, its regression tests (marked
`@pytest.mark.seeded_bug("B-xx")`) run as strict xfail: they must fail. If one
starts passing before its fix PR removes the ID, strict xfail turns the suite
red, so a bug can never be closed silently.

Each fix PR deletes exactly one line below.
"""

OPEN_BUGS = {
    "B-01",  # hardcoded intel API key
    "B-02",  # SQL injection in /events/search
    "B-03",  # path traversal in /reports/<name>
    "B-04",  # unsafe YAML rule loading
    "B-05",  # no ingest validation or size cap
    "B-06",  # no authentication, debug=True
    "B-07",  # log injection and secrets in logs
    "B-08",  # unpinned and vulnerable dependencies
    "B-09",  # insecure CI workflow
    "B-10",  # poisoned agent memory, no agent permission rules
}
