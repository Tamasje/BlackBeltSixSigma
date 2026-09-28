"""Build build/bb_toolkit.xlsx: one sheet per approved tool, then the Tables sheet.

The delivered file is exactly what openpyxl writes (formulas, no cached values), flagged so Excel
recalculates everything when it opens. LibreOffice recalculates a *copy* to prove every formula
evaluates; its own re-save is not delivered because LibreOffice rewrites some formulas (e.g. TRUE -> TRUE()).

Run: PYTHONPATH=src python3 -m bbtools.build_workbook
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.workbook.properties import CalcProperties

from bbtools import sheet_capability, sheet_normal, sheet_sigma, sheet_tables
from bbtools.constants import ROOT, load_all
from bbtools.readme import write_readme
from bbtools.recalc import RecalcReport, recalc

OUTPUT = ROOT / "build" / "bb_toolkit.xlsx"

# Calculator sheets in approved order (inventory/approved_tools.md). Each module exposes SHEET, HEADER, DOC and
# build_sheet(ws). The Tables sheet comes last: calculators look constants up there, users rarely need it.
TOOL_SHEETS = (sheet_capability, sheet_normal, sheet_sigma)


def build_workbook() -> Workbook:
    """Assemble the workbook in memory: calculators in approved order, then Tables."""
    wb = Workbook()
    wb.remove(wb.active)
    sheets = [(module, wb.create_sheet(module.SHEET)) for module in TOOL_SHEETS]
    sheet_tables.build_tables_sheet(wb, load_all())  # defines the lookup names the calculators use
    for module, ws in sheets:
        module.build_sheet(ws)
    wb.calculation = CalcProperties(fullCalcOnLoad=True)  # Excel computes every formula on open
    return wb


def save(wb: Workbook, path: Path = OUTPUT) -> Path:
    """Write the workbook to `path`, creating build/ if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def verify(path: Path) -> RecalcReport:
    """Recalculate a temporary copy of `path` with LibreOffice and report formula errors."""
    with tempfile.TemporaryDirectory(prefix="bbtools-verify-") as tmp:
        copy = Path(tmp) / path.name
        shutil.copyfile(path, copy)
        return recalc(copy)


def main() -> None:
    """Build, save and verify the toolkit, write build/README.md; print the recalculation summary."""
    path = save(build_workbook())
    report = verify(path)
    print(f"{path}: {report.total_formulas} formulas, {report.total_errors} errors {report.errors or ''}")
    if report.total_errors:
        raise SystemExit(1)
    readme = write_readme([(m.HEADER, m.DOC) for m in (*TOOL_SHEETS, sheet_tables)])
    print(f"{readme}: written")


if __name__ == "__main__":
    main()
