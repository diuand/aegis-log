"""Unit tests for aegis.logsafe (B-07)."""

import logging

from aegis.logsafe import MAX_LEN, SanitizingFilter, clean


def test_newlines_and_control_chars_are_escaped():
    out = clean("ok\r\nFAKE line\x1b[31m more")
    assert "\n" not in out and "\r" not in out and "\x1b" not in out and " " not in out
    assert "\\n" in out


def test_credentials_are_redacted():
    out = clean("Authorization: Bearer abc.def-123456 password=hunter2 api_key: k1 aegk_ABCDEFGH12345678")
    for secret in ("abc.def-123456", "hunter2", "k1 ", "aegk_ABCDEFGH12345678"):
        assert secret not in out
    assert out.count("[REDACTED") == 4


def test_long_values_are_truncated():
    assert len(clean("A" * 5000)) <= MAX_LEN + len("...[truncated]")


def test_filter_cleans_records_that_skipped_clean():
    record = logging.LogRecord("aegis", logging.INFO, __file__, 1, "user=%s", ("bob\nINFO forged",), None)
    SanitizingFilter().filter(record)
    assert "\n" not in record.getMessage()
