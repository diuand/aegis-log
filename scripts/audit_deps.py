#!/usr/bin/env python3
"""Run pip-audit on requirements.txt, honouring tracked exceptions.

Each non-comment line of .pip-audit-ignore is `<vuln-id>  # tracked: B-xx ...`.
tests/test_tracked_exceptions.py fails if an entry names a bug that is
already closed, so an exception cannot outlive its bug.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ignored_ids() -> list[str]:
    path = ROOT / ".pip-audit-ignore"
    if not path.exists():
        return []
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#")[0].strip()
        if entry:
            ids.append(entry)
    return ids


def main() -> int:
    cmd = [sys.executable, "-m", "pip_audit", "-r", str(ROOT / "requirements.txt"),
           "--progress-spinner", "off", "--desc", "on"]
    for vuln in ignored_ids():
        cmd += ["--ignore-vuln", vuln]
    return subprocess.call(cmd)  # nosec B603 - fixed argument list, no shell


if __name__ == "__main__":
    sys.exit(main())
