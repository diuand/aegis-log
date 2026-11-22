"""Detection rules loaded from rules/*.yaml.

A rule tags an event and adds to its risk score when every condition in
`when` holds. Fields are dotted paths into the normalized document.
"""

from pathlib import Path

import yaml


def load_rules(rules_dir: Path) -> list[dict]:
    rules = []
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        with open(path, encoding="utf-8") as fh:
            rules.append(yaml.load(fh, Loader=yaml.Loader))  # tracked: B-04 # nosec B506
    return rules


def _field(doc: dict, dotted: str):
    value = doc
    for part in dotted.split("."):
        value = value[part]
    return value


def matches(rule: dict, doc: dict) -> bool:
    for dotted, cond in rule["when"].items():
        value = str(_field(doc, dotted))
        if "equals" in cond and value != cond["equals"]:
            return False
        if "contains" in cond and cond["contains"].lower() not in value.lower():
            return False
    return True


def apply_rules(rules: list[dict], doc: dict) -> dict:
    for rule in rules:
        try:
            hit = matches(rule, doc)
        except Exception:  # tracked: B-04 # nosec B112
            continue
        if hit:
            doc["tags"].append(f"rule:{rule['id']}")
            doc["risk_score"] += rule["risk"]
    return doc
