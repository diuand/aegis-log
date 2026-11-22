#!/usr/bin/env python3
"""Build RISK-REGISTER.xlsx from the rows below.

The course template was not available, so the workbook is generated here with
the same structure (Read me, Register, Scales, Heat map). Keeping the data in
this script makes every register change reviewable as a normal diff; the
workbook is rebuilt with `make register` and committed next to it.

Scores, levels and the heat map are Excel formulas, never typed numbers.
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parent.parent / "RISK-REGISTER.xlsx"
REVIEWED = "2026-11-22"

# One dict per risk. L/I = inherent likelihood/impact, RL/RI = residual.
ROWS = [
    {
        "id": "R-01", "register": "External",
        "asset": "Threat-intel provider API key",
        "threat": "Key committed to source or history and harvested from a clone, fork or log",
        "ref": "T1552.001 / CWE-798", "bugs": "B-01", "L": 4, "I": 4,
        "control": "Key read from AEGIS_INTEL_API_KEY (environment or git-ignored .env; .env.example holds placeholders only). gitleaks with a custom aegk_ rule in pre-commit and CI; the seeded value is ignored by exact fingerprint only. Likelihood 4->2: a new key is refused before commit and caught again in CI, but a human can still bypass the local hook and the old fake key stays in history by design. Impact stays 4.",
        "RL": 2, "RI": 4,
        "evidence": "tests/test_seeded_bugs.py::test_b01_*; docs/evidence/gitleaks-refused.txt; .gitleaks.toml; CI job gitleaks",
        "status": "Implemented",
    },
    {
        "id": "R-02", "register": "Internal",
        "asset": "Stored events and the host filesystem",
        "threat": "Analyst query parameters reach SQL and file paths unchecked (injection, traversal)",
        "ref": "T1190 / CWE-89, CWE-22", "bugs": "B-02, B-03", "L": 4, "I": 4,
        "control": "B-02 closed: the search query uses a bound parameter, so input is data, never SQL. B-03 still open (reports). Likelihood 4->3 for now: one of the two injection paths is gone.",
        "RL": 3, "RI": 4,
        "evidence": "tests/test_seeded_bugs.py::test_b02_*; aegis/store.py",
        "status": "Open",
    },
    {
        "id": "R-03", "register": "Internal",
        "asset": "Detection rules (rules/*.yaml)",
        "threat": "A rule file runs code when loaded, or a broken rule silently switches detection off",
        "ref": "CWE-502", "bugs": "B-04", "L": 3, "I": 5,
        "control": "Planned: yaml.safe_load, schema validation, all-or-nothing reload, CODEOWNERS on rules/",
        "RL": 3, "RI": 5, "evidence": "", "status": "Open",
    },
    {
        "id": "R-04", "register": "External",
        "asset": "Ingest pipeline",
        "threat": "Malformed or oversized telemetry from hostile sources crashes ingest; known-bad sources pass unflagged",
        "ref": "T1499 / CWE-20, CWE-400", "bugs": "B-05", "L": 4, "I": 3,
        "control": "Planned: schema validation, body size cap, clean 400/413 errors; intel enrichment raises risk_score",
        "RL": 4, "RI": 3, "evidence": "", "status": "Open",
    },
    {
        "id": "R-05", "register": "Internal",
        "asset": "Ingest and admin endpoints",
        "threat": "Anyone who reaches the port can write events or reload rules; the Werkzeug debugger runs code",
        "ref": "CWE-306, CWE-489", "bugs": "B-06", "L": 4, "I": 5,
        "control": "Planned: deny-by-default API key (constant-time compare), debug off, loopback bind",
        "RL": 4, "RI": 5, "evidence": "", "status": "Open",
    },
    {
        "id": "R-06", "register": "Internal",
        "asset": "Service logs",
        "threat": "Forged log lines mislead the analyst; credentials and tokens are written to logs",
        "ref": "T1070 / CWE-117, CWE-532", "bugs": "B-07", "L": 3, "I": 3,
        "control": "Planned: escape control characters, redact secrets, never log request headers",
        "RL": 3, "RI": 3, "evidence": "", "status": "Open",
    },
    {
        "id": "R-07", "register": "External",
        "asset": "Python dependency tree",
        "threat": "Old or unpinned package with a known CVE is installed",
        "ref": "T1195.001 / OWASP A06", "bugs": "B-08", "L": 3, "I": 4,
        "control": "Planned: exact pins, upgrade the vulnerable package, pip-audit in make check and CI",
        "RL": 3, "RI": 4, "evidence": "", "status": "Open",
    },
    {
        "id": "R-08", "register": "Operational",
        "asset": "CI pipeline and repository token",
        "threat": "pull_request_target with a write-all token runs PR code; a retagged action runs with that token",
        "ref": "T1195.002 / CWE-829", "bugs": "B-09", "L": 3, "I": 5,
        "control": "ci-baseline.yml deleted. ci.yml: pull_request trigger only, top-level permissions contents: read, every action pinned to a full SHA, persist-credentials: false, zizmor lints every workflow on every PR. Likelihood 3->1: the trigger and token that made the attack possible are gone and a linter blocks their return. Impact stays 5.",
        "RL": 1, "RI": 5,
        "evidence": "tests/test_seeded_bugs.py::test_b09_*; .github/workflows/ci.yml (workflow-lint job); docs/BUG-REPORT.md#b-09",
        "status": "Implemented",
    },
    {
        "id": "R-09", "register": "Operational",
        "asset": "AI coding agent",
        "threat": "A poisoned memory note steers the agent; no permission rules stop pushes to main or secret reads",
        "ref": "ATLAS AML.T0051 / context poisoning", "bugs": "B-10", "L": 3, "I": 4,
        "control": "Poisoned note deleted and no longer imported; memory lives in memory/ and changes only by PR (CODEOWNERS). .claude/settings.json deny rules plus a PreToolUse guard that blocks pushes to main, force pushes, hook bypasses, secret reads and guardrail edits, and fails closed. Likelihood 3->2: a new poisoned note could still be merged by a careless review, but the actions it asks for are blocked. Impact stays 4.",
        "RL": 2, "RI": 4,
        "evidence": "docs/evidence/hook-blocked.txt; tests/test_seeded_bugs.py::test_b10_*; tests/test_agent_guard.py; .claude/settings.json",
        "status": "Implemented",
    },
    {
        "id": "R-10", "register": "Operational",
        "asset": "main branch",
        "threat": "Unreviewed or weakly reviewed change reaches main (no branch protection on a private Free repo, no automated reviewer)",
        "ref": "-", "bugs": "none", "L": 4, "I": 4,
        "control": "Planned: PR-only workflow, local hooks, governance workflow, PR checklist, agent-assisted review",
        "RL": 4, "RI": 4, "evidence": "", "status": "Open",
    },
]

HEADERS = [
    "ID", "Register", "Asset", "Threat / technique", "ATT&CK / CWE", "Bugs",
    "L", "I", "Inherent", "Inherent level", "Control", "RL", "RI", "Residual",
    "Residual level", "Evidence", "Status", "Owner", "Last reviewed",
]
WIDTHS = [7, 12, 26, 48, 22, 10, 5, 5, 9, 11, 52, 5, 5, 9, 11, 46, 12, 14, 13]

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
FILLS = {
    "Low": PatternFill("solid", fgColor="C6EFCE"),
    "Medium": PatternFill("solid", fgColor="FFEB9C"),
    "High": PatternFill("solid", fgColor="FFC7CE"),
}


def level(cell: str) -> str:
    return f'=IF({cell}="","",IF({cell}>=15,"High",IF({cell}>=8,"Medium","Low")))'


def read_me(ws) -> None:
    ws.title = "Read me"
    lines = [
        ("aegis-log risk register", True),
        ("", False),
        ("Written before any code. Every control in the repository answers a row here,", False),
        ("and every pull request cites the risk IDs it touches.", False),
        ("", False),
        ("The course template was not available when this was built, so the workbook", False),
        ("is generated by scripts/build_register.py with the same structure:", False),
        ("Register (the rows), Scales (how to score), Heat map (counts per cell).", False),
        ("", False),
        ("Registers: Operational = risk the AI agent and the pipeline introduce;", False),
        ("Internal = risk in the security function this service supports;", False),
        ("External = risk from the threat landscape.", False),
        ("", False),
        ("Inherent = L x I before controls. Residual = RL x RI after the control.", False),
        ("Bands: 1-7 Low, 8-14 Medium, 15-25 High. Scores and levels are formulas.", False),
        ("A row marked Implemented or Verified must name evidence a reviewer can open.", False),
        ("Status: Open, Implemented, Verified, Accepted.", False),
    ]
    for i, (text, bold) in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=text).font = Font(bold=bold, size=14 if bold else 11)
    ws.column_dimensions["A"].width = 90


def register(ws) -> None:
    ws.title = "Register"
    for col, (name, width) in enumerate(zip(HEADERS, WIDTHS, strict=True), start=1):
        c = ws.cell(row=1, column=col, value=name)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD_FILL
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BORDER
        ws.column_dimensions[c.column_letter].width = width
    for r, row in enumerate(ROWS, start=2):
        values = [
            row["id"], row["register"], row["asset"], row["threat"], row["ref"], row["bugs"],
            row["L"], row["I"], f"=G{r}*H{r}", level(f"I{r}"), row["control"],
            row["RL"], row["RI"], f"=L{r}*M{r}", level(f"N{r}"), row["evidence"],
            row["status"], "Project owner", REVIEWED,
        ]
        for col, value in enumerate(values, start=1):
            c = ws.cell(row=r, column=col, value=value)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BORDER
    last = len(ROWS) + 1
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:S{last}"

    dv_reg = DataValidation(type="list", formula1='"Operational,Internal,External"', allow_blank=False)
    dv_score = DataValidation(type="whole", operator="between", formula1="1", formula2="5")
    dv_status = DataValidation(type="list", formula1='"Open,Implemented,Verified,Accepted"')
    for dv in (dv_reg, dv_score, dv_status):
        ws.add_data_validation(dv)
    dv_reg.add(f"B2:B{last}")
    for col in "GHLM":
        dv_score.add(f"{col}2:{col}{last}")
    dv_status.add(f"Q2:Q{last}")

    for col in "JO":
        rng = f"{col}2:{col}{last}"
        for name, fill in FILLS.items():
            ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{name}"'], fill=fill))
    # Flag a row claimed as done without evidence.
    ws.conditional_formatting.add(
        f"P2:P{last}",
        FormulaRule(formula=['AND(OR($Q2="Implemented",$Q2="Verified"),LEN($P2)=0)'],
                    fill=PatternFill("solid", fgColor="FF0000")),
    )


def scales(ws) -> None:
    ws.title = "Scales"
    rows = [
        ("Score", "Likelihood", "Impact"),
        (1, "Rare: no realistic path with current controls", "Negligible: no effect on C, I or A"),
        (2, "Unlikely: needs unusual conditions or insider error", "Minor: contained, fixed in hours, no data exposure"),
        (3, "Possible: plausible within the project lifetime", "Moderate: one component degraded, limited exposure"),
        (4, "Likely: expected without the control", "Major: detection blind or secrets exposed"),
        (5, "Almost certain: already observed or trivial to trigger", "Severe: full compromise of the service or its credentials"),
        ("", "", ""),
        ("Band", "Score range", ""),
        ("Low", "1-7", ""),
        ("Medium", "8-14", ""),
        ("High", "15-25", ""),
    ]
    for r, values in enumerate(rows, start=1):
        for c, v in enumerate(values, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = Font(bold=r in (1, 8))
    for name, r in (("Low", 9), ("Medium", 10), ("High", 11)):
        ws.cell(row=r, column=1).fill = FILLS[name]
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 60


def heat_map(ws) -> None:
    ws.title = "Heat map"
    last = len(ROWS) + 1
    for title, lcol, icol, top in (
        ("Inherent (count of risks)", "G", "H", 1), ("Residual (count of risks)", "L", "M", 10)
    ):
        ws.cell(row=top, column=1, value=title).font = Font(bold=True)
        ws.cell(row=top + 1, column=1, value="L \\ I").font = Font(bold=True)
        for i in range(1, 6):
            ws.cell(row=top + 1, column=1 + i, value=i).font = Font(bold=True)
        for li, lik in enumerate(range(5, 0, -1)):
            r = top + 2 + li
            ws.cell(row=r, column=1, value=lik).font = Font(bold=True)
            for imp in range(1, 6):
                formula = (f"=COUNTIFS(Register!${lcol}$2:${lcol}${last},{lik},"
                           f"Register!${icol}$2:${icol}${last},{imp})")
                cell = ws.cell(row=r, column=1 + imp, value=formula)
                score = lik * imp
                band = "High" if score >= 15 else "Medium" if score >= 8 else "Low"
                cell.fill = FILLS[band]
                cell.alignment = Alignment(horizontal="center")
                cell.border = BORDER


def main() -> None:
    wb = Workbook()
    read_me(wb.active)
    register(wb.create_sheet())
    scales(wb.create_sheet())
    heat_map(wb.create_sheet())
    wb.save(OUT)
    print(f"wrote {OUT.name}: {len(ROWS)} risks")


if __name__ == "__main__":
    main()
