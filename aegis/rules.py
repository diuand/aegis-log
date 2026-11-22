"""Detection rules loaded from rules/*.yaml.

A rule tags an event and adds to its risk score when every condition in
`when` holds. Files are parsed with yaml.safe_load (plain data only) and
validated against a strict schema; a set with any bad file is rejected as a
whole, so a broken rule can never silently switch detection off.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

FIELDS = {"message", "user.name", "source.ip", "destination.ip"}


class RuleError(ValueError):
    """A rule file is unsafe or invalid; the whole set is rejected."""


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equals: str | None = None
    contains: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def exactly_one_operator(self):
        if (self.equals is None) == (self.contains is None):
            raise ValueError("each condition needs exactly one of: equals, contains")
        return self


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^AG-\d{3}$")
    title: str = Field(min_length=1, max_length=120)
    severity: Literal["low", "medium", "high", "critical"]
    risk: int = Field(ge=1, le=50)
    when: dict[str, Condition] = Field(min_length=1)

    @field_validator("when")
    @classmethod
    def known_fields(cls, value: dict[str, Condition]):
        unknown = sorted(set(value) - FIELDS)
        if unknown:
            raise ValueError(f"unknown field(s) {unknown}; allowed: {sorted(FIELDS)}")
        return value


def load_rules(rules_dir: Path) -> list[Rule]:
    rules: list[Rule] = []
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            rules.append(Rule.model_validate(data))
        except yaml.YAMLError as exc:
            raise RuleError(f"{path.name}: not plain YAML data ({exc.__class__.__name__})") from exc
        except ValidationError as exc:
            fields = ", ".join(".".join(map(str, e["loc"])) or "<root>" for e in exc.errors())
            raise RuleError(f"{path.name}: invalid rule ({fields})") from exc
    ids = [r.id for r in rules]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise RuleError(f"duplicate rule id(s): {dupes}")
    return rules


def _field(doc: dict, dotted: str) -> str:
    value = doc
    for part in dotted.split("."):
        value = value.get(part, "") if isinstance(value, dict) else ""
    return str(value)


def matches(rule: Rule, doc: dict) -> bool:
    for dotted, cond in rule.when.items():
        value = _field(doc, dotted)
        if cond.equals is not None and value != cond.equals:
            return False
        if cond.contains is not None and cond.contains.lower() not in value.lower():
            return False
    return True


def apply_rules(rules: list[Rule], doc: dict) -> dict:
    for rule in rules:
        if matches(rule, doc):
            doc["tags"].append(f"rule:{rule.id}")
            doc["risk_score"] += rule.risk
    return doc
