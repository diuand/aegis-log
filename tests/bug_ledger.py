"""Seeded bugs that are still open.

While an ID is listed here, its regression tests (marked
`@pytest.mark.seeded_bug("B-xx")`) run as strict xfail: they must fail. If one
starts passing before its fix PR removes the ID, strict xfail turns the suite
red, so a bug can never be closed silently.

Each fix PR deletes exactly one line below.
"""

OPEN_BUGS = {
    "B-06",  # no authentication, debug=True
    "B-07",  # log injection and secrets in logs
    "B-08",  # unpinned and vulnerable dependencies
}
