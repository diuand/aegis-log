"""Seeded bugs that are still open.

While an ID is listed here, its regression tests (marked
`@pytest.mark.seeded_bug("B-xx")`) run as strict xfail: they must fail. If one
starts passing before its fix PR removes the ID, strict xfail turns the suite
red, so a bug can never be closed silently.

Each fix PR deletes exactly one line below.
"""

# All ten seeded bugs are closed (B-08 was the last).
OPEN_BUGS: set[str] = set()
