"""The risk register meets the definition of done (scripts/check_register.py)."""

import sys

from tests.conftest import ROOT

sys.path.insert(0, str(ROOT / "scripts"))

import check_register  # noqa: E402


def test_register_has_no_problems():
    assert check_register.problems() == []


def test_register_xlsx_is_up_to_date_with_the_script():
    from build_register import OUT, ROWS
    from openpyxl import load_workbook

    ws = load_workbook(OUT)["Register"]
    for i, row in enumerate(ROWS, start=2):
        assert ws[f"A{i}"].value == row["id"]
        assert ws[f"Q{i}"].value == row["status"], f"{row['id']}: run make register"
        assert ws[f"P{i}"].value == (row["evidence"] or None)
