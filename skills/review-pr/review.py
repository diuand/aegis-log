#!/usr/bin/env python3
"""Mechanical pass of the review-pr skill: diff the branch against a base.

Usage: review.py [--base main]
Prints a Markdown report for the "Agent review" section of the PR and exits
1 if it found a banned pattern.
"""

import argparse
import re
import subprocess
import sys

BANNED = [
    ("literal intel key", re.compile(r"aegk_[A-Za-z0-9]{24,}")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("SQL built from a string", re.compile(r"""(execute\(\s*f["']|f["']\s*(SELECT|INSERT|UPDATE|DELETE)\b)""", re.I)),
    ("unsafe yaml.load", re.compile(r"yaml\.load\(|yaml\.(Unsafe)?Loader\b")),
    ("debug=True", re.compile(r"debug\s*=\s*True")),
    ("bind to all interfaces", re.compile(r"0\.0\.0\.0")),
    ("action pinned by tag", re.compile(r"uses:\s*[\w.-]+/[\w./-]+@(?![0-9a-f]{40}\b)\S+")),
    ("pull_request_target trigger", re.compile(r"pull_request_target")),
    ("write-all token", re.compile(r"write-all")),
    ("hook bypass", re.compile(r"--no-verify|core\.hooksPath", re.I)),
    ("unpinned requirement", re.compile(r"^(?!#)[A-Za-z0-9_.\-\[\]]+\s*$")),
]
# Patterns are code rules; docs, tests and this skill quote them on purpose.
SCANNED = re.compile(r"^(aegis/|scripts/|\.github/workflows/|rules/|requirements[\w-]*\.txt$|\.claude/)")
SENSITIVE = re.compile(r"^(\.github/|\.claude/|memory/|skills/|rules/|CLAUDE\.md$|scripts/hooks/)")
IDS = re.compile(r"\b[RB]-\d\d\b")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607


def added_lines(base: str):
    path = None
    for line in git("diff", "--unified=0", f"{base}...HEAD").splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("+") and not line.startswith("+++") and path:
            yield path, line[1:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="main")
    base = ap.parse_args().base

    files = [f for f in git("diff", "--name-only", f"{base}...HEAD").splitlines() if f]
    commits = [c for c in git("log", "--format=%h%x09%s%x09%b%x1e", f"{base}..HEAD").split("\x1e") if c.strip()]

    findings = []
    for path, text in added_lines(base):
        if not SCANNED.match(path):
            continue
        for name, rx in BANNED:
            if name == "unpinned requirement" and not path.startswith("requirements"):
                continue
            if rx.search(text):
                findings.append(f"- **{name}** in `{path}`: `{text.strip()[:100]}`")

    sensitive = sorted(f for f in files if SENSITIVE.match(f))
    no_ids = [c.split("\t")[0].strip() + " " + c.split("\t")[1] for c in commits if not IDS.search(c)]
    code_changed = any(f.startswith("aegis/") for f in files)
    tests_changed = any(f.startswith("tests/") for f in files)

    print(f"### review.py (base `{base}`, {len(commits)} commit(s), {len(files)} file(s))\n")
    print("**Banned patterns in added lines:**", "none" if not findings else "")
    for f in findings:
        print(f)
    print("\n**Sensitive paths touched (owner review):**", ", ".join(f"`{s}`" for s in sensitive) or "none")
    print("\n**Commits without a risk or bug ID:**", ", ".join(no_ids) or "none")
    if code_changed and not tests_changed:
        print("\n**Warning:** service code changed but no test changed.")
    else:
        print("\n**Tests:**", "changed with the code" if code_changed else "no service code changed")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
