"""Scanner exceptions must belong to an open seeded bug.

The scanners went live in phase 3 while bugs were still open on purpose, so
their existing findings were recorded as exceptions tied to a bug ID. These
tests make sure no exception outlives its bug and no untracked one appears.
"""

import re

from tests.bug_ledger import OPEN_BUGS
from tests.conftest import ROOT

TRACKED = re.compile(r"tracked: (B-\d\d)")


def test_every_nosec_in_the_service_names_an_open_bug():
    problems = []
    for path in (ROOT / "aegis").rglob("*.py"):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "nosec" not in line:
                continue
            m = TRACKED.search(line)
            if not m or m.group(1) not in OPEN_BUGS:
                problems.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()}")
    assert problems == []


def test_every_pip_audit_exception_names_an_open_bug():
    path = ROOT / ".pip-audit-ignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    problems = []
    for line in lines:
        if not line.split("#")[0].strip():
            continue
        m = TRACKED.search(line)
        if not m or m.group(1) not in OPEN_BUGS:
            problems.append(line)
    assert problems == []
