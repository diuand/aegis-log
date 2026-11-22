"""Defence in depth for B-03: the resolver itself, not only the route."""

import os

import pytest

from aegis.reports import resolve_report


@pytest.mark.parametrize("name", [
    "../secret.txt", "..\\secret.txt", "/etc/passwd", "C:\\Windows\\win.ini",
    "daily-summary.txt/../../secret.txt", ".hidden.txt", "notes.md", "DAILY.TXT", "",
])
def test_resolver_rejects_names_outside_the_allowlist(workdir, name):
    assert resolve_report(workdir / "reports", name) is None


def test_resolver_accepts_a_real_report(workdir):
    path = resolve_report(workdir / "reports", "daily-summary.txt")
    assert path is not None and path.name == "daily-summary.txt"


def test_resolver_refuses_a_symlink_that_points_outside(workdir):
    (workdir / "secret.txt").write_text("outside", encoding="utf-8")
    link = workdir / "reports" / "linked.txt"
    try:
        os.symlink(workdir / "secret.txt", link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this machine")
    assert resolve_report(workdir / "reports", "linked.txt") is None
