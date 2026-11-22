#!/usr/bin/env python3
"""Definition-of-done checks on the risk register (run by tests/test_register.py).

- every seeded bug B-01..B-10 maps to a row
- no Implemented/Verified row has empty evidence
- every evidence path that looks like a repo path exists
- residual never exceeds inherent; scores are 1-5
- the workbook's formulas are present (scores are never typed numbers)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_register import OUT, ROWS  # noqa: E402

PATHISH = re.compile(r"[\w./-]+\.(?:py|txt|yml|yaml|json|md|xlsx)|\.github/[\w./-]+|[\w-]+/[\w./-]+/")


def problems() -> list[str]:
    out = []
    bugs = {b.strip() for r in ROWS for b in r["bugs"].split(",")}
    out += [f"{b} has no register row" for b in (f"B-{i:02d}" for i in range(1, 11)) if b not in bugs]
    for r in ROWS:
        if r["status"] in ("Implemented", "Verified") and not r["evidence"].strip():
            out.append(f"{r['id']}: {r['status']} with empty evidence")
        if r["RL"] * r["RI"] > r["L"] * r["I"]:
            out.append(f"{r['id']}: residual above inherent")
        if not all(1 <= r[k] <= 5 for k in ("L", "I", "RL", "RI")):
            out.append(f"{r['id']}: score outside 1-5")
        for ref in r["evidence"].split(";"):
            path = ref.strip().split("::")[0].split(" ")[0].split("#")[0]
            if PATHISH.fullmatch(path) and not (ROOT / path).exists():
                out.append(f"{r['id']}: evidence path {path} does not exist")
    if OUT.exists():
        from openpyxl import load_workbook

        ws = load_workbook(OUT)["Register"]
        for row in range(2, len(ROWS) + 2):
            for col in ("I", "J", "N", "O"):
                value = ws[f"{col}{row}"].value
                if not (isinstance(value, str) and value.startswith("=")):
                    out.append(f"Register!{col}{row} is not a formula")
    else:
        out.append(f"{OUT.name} missing (run make register)")
    return out


def main() -> int:
    found = problems()
    for p in found:
        print("FAIL", p)
    print("register OK" if not found else f"{len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
