"""Schema checks for detection rules (B-04 defence in depth)."""

import pytest

from aegis.rules import RuleError, load_rules
from tests.conftest import ROOT

GOOD = "id: AG-010\ntitle: t\nseverity: low\nrisk: 5\nwhen:\n  message:\n    contains: x\n"


def write(tmp_path, text):
    (tmp_path / "r.yaml").write_text(text, encoding="utf-8")
    return tmp_path


def test_shipped_rules_are_valid():
    assert [r.id for r in load_rules(ROOT / "rules")] == ["AG-001", "AG-002"]


def test_good_rule_loads(tmp_path):
    assert load_rules(write(tmp_path, GOOD))[0].risk == 5


@pytest.mark.parametrize("bad", [
    GOOD.replace("AG-010", "rm -rf"),                    # id format
    GOOD.replace("severity: low", "severity: urgent"),   # severity enum
    GOOD.replace("risk: 5", "risk: 500"),                # risk range
    GOOD.replace("message:", "source.port:"),            # unknown field
    GOOD.replace("contains: x", "contains: x\n    equals: y"),  # two operators
    GOOD.replace("contains: x", "regex: x"),             # unknown operator
    GOOD + "extra: 1\n",                                 # unknown key
    "just a string\n",                                   # not a mapping
])
def test_invalid_rules_are_rejected(tmp_path, bad):
    with pytest.raises(RuleError):
        load_rules(write(tmp_path, bad))


def test_error_names_the_file_not_the_contents(tmp_path):
    with pytest.raises(RuleError, match=r"^r\.yaml: invalid rule"):
        load_rules(write(tmp_path, GOOD.replace("risk: 5", "risk: 0")))
