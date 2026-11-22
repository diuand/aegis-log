"""Extra coverage for the PreToolUse guard beyond the B-10 regression tests."""

import json
import subprocess
import sys

import pytest

from tests.conftest import ROOT

GUARD = ROOT / ".claude" / "hooks" / "guard.py"


def decide(tool: str, **params) -> int:
    payload = json.dumps({"tool_name": tool, "tool_input": params})
    return subprocess.run([sys.executable, str(GUARD)], input=payload, capture_output=True,
                          text=True, timeout=20).returncode


@pytest.mark.parametrize("command", [
    "git push origin HEAD:main",
    "git push origin refs/heads/main",
    "git push origin :main",
    "git push --force-with-lease origin fix/x",
    "git push origin +fix/x",
    "git commit --no-verify -m x",
    "git -c core.hooksPath=/dev/null commit -m x",
    "make test && git push origin main",
    "cat .env",
    "type secrets/intel.key",
])
def test_dangerous_bash_is_blocked(command):
    assert decide("Bash", command=command) == 2


@pytest.mark.parametrize("command", [
    "git status", "git push -u origin fix/b-05-input-validation", "make check", "cat .env.example",
])
def test_ordinary_bash_is_allowed(command):
    assert decide("Bash", command=command) == 0


def test_secret_files_cannot_be_read_by_file_tools():
    assert decide("Read", file_path=".env") == 2
    assert decide("Grep", path="secrets/") == 2
    assert decide("Read", file_path="README.md") == 0


def test_guardrails_cannot_be_edited_by_the_agent():
    assert decide("Edit", file_path=".claude/settings.json") == 2
    assert decide("Write", file_path=".claude/hooks/guard.py") == 2
    assert decide("Edit", file_path="aegis/routes.py") == 0


def test_malformed_input_fails_closed():
    proc = subprocess.run([sys.executable, str(GUARD)], input="{not json", capture_output=True,
                          text=True, timeout=20)
    assert proc.returncode == 2
