#!/usr/bin/env python3
"""Fail if a commit on main's first-parent line did not come from a merged PR.

Used by .github/workflows/governance.yml (GITHUB_ROUTE 4). Stdlib only.
The root commit is exempt: it existed before main could receive a PR.
"""

import json
import os
import subprocess
import sys
import urllib.request

API = "https://api.github.com"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def pr_that_merged(repo: str, sha: str, token: str) -> dict | None:
    req = urllib.request.Request(
        f"{API}/repos/{repo}/commits/{sha}/pulls",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # nosec B310 - fixed https API host
        for pr in json.load(resp):
            if pr.get("merged_at") and pr.get("merge_commit_sha") == sha and pr["base"]["ref"] == "main":
                return pr
    return None


def main() -> int:
    repo, token = os.environ["REPO"], os.environ["GITHUB_TOKEN"]
    failures = 0
    shas = git("rev-list", "--first-parent", "HEAD").split()
    for sha in shas:
        parents = git("rev-list", "--parents", "-n", "1", sha).split()[1:]
        subject = git("log", "-1", "--format=%s", sha)
        if not parents:
            print(f"EXEMPT  {sha[:10]}  root commit: {subject}")
            continue
        pr = pr_that_merged(repo, sha, token)
        if pr:
            print(f"OK      {sha[:10]}  PR #{pr['number']}: {pr['title']}")
        else:
            print(f"FAIL    {sha[:10]}  no merged PR: {subject}")
            failures += 1
    if failures:
        print(f"\n{failures} commit(s) reached main without a merged PR.", file=sys.stderr)
        return 1
    print(f"\nAll {len(shas)} commits on main are accounted for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
