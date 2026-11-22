#!/usr/bin/env python3
"""PreToolUse guard for the coding agent (B-10 fix).

Claude Code sends the pending tool call as JSON on stdin. Exit code 2 blocks
the call and shows the reason to the agent; exit 0 lets it run. The guard
fails closed: input it cannot parse is blocked.

Blocked:
  - git push to main (explicit refspec, or a bare push while on main)
  - force pushes (--force, -f, --force-with-lease, +refspec) and deleting main
  - bypassing hooks (--no-verify, core.hooksPath overrides)
  - reading secret files (.env, secrets/, private keys) by any tool
  - editing the guardrails themselves (.claude/settings.json, .claude/hooks/)
"""

import json
import re
import shlex
import subprocess
import sys

SECRET_PATH = re.compile(r"(^|[\\/])(\.env(\.(?!example\b)[\w.-]+)?|secrets[\\/].*|id_(rsa|ed25519)\S*|\S+\.pem)$")
GUARDRAILS = re.compile(r"(^|[\\/])\.claude[\\/](settings(\.local)?\.json|hooks[\\/].*)$")


def block(reason: str) -> None:
    print(f"aegis guard: blocked: {reason}", file=sys.stderr)
    sys.exit(2)


def current_branch() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],  # nosec B603 B607
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def split(command: str) -> list[list[str]]:
    """Split a shell line into simple commands (on ; && || |)."""
    parts = re.split(r"\s*(?:;|&&|\|\||\|)\s*", command)
    words = []
    for part in parts:
        try:
            words.append(shlex.split(part, posix=True))
        except ValueError:
            block("unparseable shell command")
    return [w for w in words if w]


def check_git(words: list[str]) -> None:
    if "--no-verify" in words or any("core.hookspath" in w.lower() for w in words):
        block("bypassing git hooks is not allowed")
    if "push" not in words:
        return
    args = words[words.index("push") + 1:]
    if any(a in ("--force", "-f", "--force-with-lease") or a.startswith("--force-with-lease=")
           for a in args):
        block("force push")
    refspecs = [a for a in args if not a.startswith("-")][1:]  # drop the remote name
    for ref in refspecs:
        if ref.startswith("+"):
            block("force push (+refspec)")
        dest = ref.split(":")[-1]
        if dest in ("main", "refs/heads/main"):
            block("push to main; open a pull request instead")
    if not refspecs and current_branch() == "main":
        block("push while on main; open a pull request instead")


def check_bash(command: str) -> None:
    for words in split(command):
        if words[0] == "git" or (len(words) > 1 and words[0] == "command" and words[1] == "git"):
            check_git(words)
        for w in words[1:]:
            if SECRET_PATH.search(w):
                block(f"access to a secret file ({w})")


def main() -> None:
    try:
        event = json.load(sys.stdin)
        tool = event["tool_name"]
        params = event.get("tool_input") or {}
    except (ValueError, KeyError, TypeError):
        block("could not parse the hook input (failing closed)")

    if tool == "Bash":
        check_bash(str(params.get("command", "")))
    path = str(params.get("file_path") or params.get("path") or params.get("notebook_path") or "")
    if path and SECRET_PATH.search(path):
        block(f"access to a secret file ({path})")
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit") and GUARDRAILS.search(path):
        block("editing the agent guardrails needs a human-reviewed PR")
    sys.exit(0)


if __name__ == "__main__":
    main()
