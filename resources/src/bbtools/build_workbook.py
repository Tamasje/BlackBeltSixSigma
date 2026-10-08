"""Build bb_toolkit.xlsx (next to studiegids.html, above resources/): one sheet per approved tool, then Tables.

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

from bbtools import (
    sheet_acceptance,
    sheet_anova,
    sheet_capability,
    sheet_charts,
    sheet_conditional,
    sheet_confusion,
    sheet_distributions,
    sheet_doe,
    sheet_extra,
    sheet_grr,
    sheet_means,
    sheet_normal,
    sheet_regression,
    sheet_sigma,
    sheet_tables,
    sheet_variance,
)
from bbtools.constants import ROOT, load_all
from bbtools.readme import write_readme
from bbtools.recalc import RecalcReport, recalc

# the deliverable sits at the top of the project folder, beside studiegids.html; everything else is in resources/
OUTPUT = ROOT.parent / "bb_toolkit.xlsx"

# Calculator sheets in approved order (inventory/approved_tools.md). Each module exposes SHEET, HEADER, DOC and
# build_sheet(ws). Extra (book-only blocks, not examinable) follows the calculators. The Tables sheet comes last:
# calculators look constants up there, users rarely need it.
TOOL_SHEETS = (
    sheet_capability, sheet_normal, sheet_sigma, sheet_variance, sheet_confusion, sheet_distributions, sheet_means,
    sheet_charts, sheet_grr, sheet_acceptance, sheet_anova, sheet_doe, sheet_regression, sheet_conditional,
    sheet_extra,
)


def build_workbook(only: tuple[str, ...] | None = None) -> Workbook:
    """Assemble the workbook in memory: calculators in approved order, then Tables.

    `only` limits the calculators to those sheet names (Tables is always built: the calculators look constants up
    there and depend on nothing else), so a test of one sheet need not recalculate the others.
    """
    wb = Workbook()
    wb.remove(wb.active)
    modules = [m for m in TOOL_SHEETS if only is None or m.SHEET in only]
    sheets = [(module, wb.create_sheet(module.SHEET)) for module in modules]
    sheet_tables.build_tables_sheet(wb, load_all())  # defines the lookup names the calculators use
    for module, ws in sheets:
        module.build_sheet(ws)
    wb.calculation = CalcProperties(fullCalcOnLoad=True)  # Excel computes every formula on open
    return wb


def save(wb: Workbook, path: Path = OUTPUT) -> Path:
    """Write the workbook to `path`, creating its folder if needed."""
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
    """Build, save and verify the toolkit, write resources/build/README.md; print the recalculation summary."""
    path = save(build_workbook())
    report = verify(path)
    print(f"{path}: {report.total_formulas} formulas, {report.total_errors} errors {report.errors or ''}")
    if report.total_errors:
        raise SystemExit(1)
    readme = write_readme([(m.HEADER, m.DOC) for m in (*TOOL_SHEETS, sheet_tables)])
    print(f"{readme}: written")


if __name__ == "__main__":
    main()
