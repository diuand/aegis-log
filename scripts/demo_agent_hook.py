#!/usr/bin/env python3
"""Evidence: feed real PreToolUse payloads to the guard and show its decision.

These are the exact JSON shapes Claude Code sends to the hook. Exit code 2
means the tool call is blocked before it runs.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / ".claude" / "hooks" / "guard.py"

CASES = [
    ("Bash", {"command": "git push origin main"}),
    ("Bash", {"command": "git push origin HEAD:main"}),
    ("Bash", {"command": "git push --force origin fix/b-02-sql-injection"}),
    ("Bash", {"command": "git push origin +fix/b-02-sql-injection"}),
    ("Bash", {"command": "git push origin :main"}),
    ("Bash", {"command": "git commit -m 'quick fix' --no-verify"}),
    ("Bash", {"command": "make test && git push origin main"}),
    ("Bash", {"command": "cat .env"}),
    ("Read", {"file_path": ".env"}),
    ("Read", {"file_path": "secrets/intel.key"}),
    ("Edit", {"file_path": ".claude/hooks/guard.py", "old_string": "a", "new_string": "b"}),
    ("Bash", {"command": "git status"}),
    ("Bash", {"command": "git push -u origin fix/b-02-sql-injection"}),
    ("Read", {"file_path": ".env.example"}),
    ("Bash", {"command": "make check"}),
]


def main() -> None:
    print("# make evidence-hook: PreToolUse guard decisions (.claude/hooks/guard.py)")
    print("# exit 2 = blocked before the tool runs, exit 0 = allowed\n")
    for tool, params in CASES:
        payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": params})
        proc = subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True,  # nosec B603
                              text=True, timeout=20, cwd=ROOT)
        shown = params.get("command") or params.get("file_path")
        verdict = "BLOCKED" if proc.returncode == 2 else "allowed" if proc.returncode == 0 else "ERROR"
        print(f"{verdict:8} exit {proc.returncode}  {tool}: {shown}")
        if proc.stderr.strip():
            print(f"         {proc.stderr.strip()}")
    bad = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True,  # nosec B603
                         text=True, timeout=20)
    print(f"\n{'BLOCKED' if bad.returncode == 2 else 'ERROR':8} exit {bad.returncode}  malformed input "
          "(fails closed)")


if __name__ == "__main__":
    main()
