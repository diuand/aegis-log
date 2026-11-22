"""Make untrusted text safe to log: one event per line, no secrets.

`clean()` is used on every untrusted value before it is logged;
`SanitizingFilter` runs on the aegis logger as a safety net for any call
that forgets.
"""

import logging
import re

MAX_LEN = 512

_SECRETS = [
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=\-]{6,}"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"aegk_[A-Za-z0-9]{8,}"), "[REDACTED-KEY]"),
]
_CONTROL = re.compile(r"[\x00-\x1f\x7f  ]")


def clean(value: object) -> str:
    text = str(value)
    for pattern, repl in _SECRETS:
        text = pattern.sub(repl, text)
    # Escape CR, LF and other control characters so a value can never start a new log line.
    text = _CONTROL.sub(lambda m: m.group(0).encode("unicode_escape").decode("ascii"), text)
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN] + "...[truncated]"
    return text


class SanitizingFilter(logging.Filter):
    """Clean the fully formatted message of every record on the aegis logger."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = clean(record.getMessage())
        record.args = None
        return True
