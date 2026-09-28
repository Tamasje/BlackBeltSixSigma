"""Recalculate a workbook with LibreOffice headless and report formula errors.

openpyxl writes formulas without cached values, so nothing can be read back until a spreadsheet engine
has computed them. This follows the approach of the Anthropic xlsx skill's `recalc.py`: a throwaway
LibreOffice profile holding a one-line Basic macro (calculateAll, store), so the user's own LibreOffice
profile is never touched. LibreOffice is the test-time engine (CLAUDE.md); Excel for Mac is checked by hand.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook

MACRO_MODULE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub
</script:module>"""
MACRO_URL = "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application"
ERROR_VALUES = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A")


class RecalcError(RuntimeError):
    """LibreOffice could not recalculate the file; nothing was computed."""


@dataclass(frozen=True)
class RecalcReport:
    """Outcome of one recalculation: formula count and every cell holding an error value."""

    path: Path
    total_formulas: int
    errors: dict[str, list[str]] = field(default_factory=dict)  # error value -> ['Sheet!A1', ...]

    @property
    def total_errors(self) -> int:
        """Number of cells holding any spreadsheet error value."""
        return sum(len(cells) for cells in self.errors.values())


def soffice_path() -> str:
    """Absolute path of the soffice executable; raises RecalcError if LibreOffice is not installed."""
    found = shutil.which("soffice")
    if found is None:
        raise RecalcError("soffice not found on PATH; install LibreOffice (brew install --cask libreoffice)")
    return found


def _make_profile(profile_dir: Path, soffice: str, timeout_s: int) -> str:
    """Initialise a fresh LibreOffice profile in `profile_dir`, install the macro, return its file URL."""
    url = profile_dir.as_uri()
    subprocess.run([soffice, "--headless", "--terminate_after_init", f"-env:UserInstallation={url}"],
                   capture_output=True, timeout=timeout_s, check=False)
    macro_dir = profile_dir / "user" / "basic" / "Standard"
    if not macro_dir.is_dir():
        raise RecalcError(f"LibreOffice did not create a profile in {profile_dir}")
    (macro_dir / "Module1.xba").write_text(MACRO_MODULE, encoding="utf-8")
    return url


def _run_macro(path: Path, profile_url: str, soffice: str, timeout_s: int) -> None:
    """Open `path` in LibreOffice, recalculate every formula and save it in place."""
    before = path.stat().st_mtime_ns
    result = subprocess.run(
        [soffice, "--headless", "--norestore", f"-env:UserInstallation={profile_url}", MACRO_URL, str(path)],
        capture_output=True, text=True, timeout=timeout_s, check=False,
    )
    if result.returncode != 0:
        raise RecalcError(f"LibreOffice failed on {path}: {result.stderr.strip() or result.returncode}")
    if path.stat().st_mtime_ns == before:
        # A second LibreOffice instance swallows the request and exits 0 without saving.
        raise RecalcError(f"LibreOffice exited without rewriting {path}; close other LibreOffice windows and retry")


def scan(path: Path) -> RecalcReport:
    """Count formulas and collect cells whose cached value is a spreadsheet error."""
    formulas = load_workbook(path, data_only=False)
    values = load_workbook(path, data_only=True)
    total = 0
    errors: dict[str, list[str]] = {}
    for ws in formulas.worksheets:
        cached = values[ws.title]
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    total += 1
                value = cached[cell.coordinate].value
                if isinstance(value, str) and value in ERROR_VALUES:
                    errors.setdefault(value, []).append(f"{ws.title}!{cell.coordinate}")
    return RecalcReport(path=path, total_formulas=total, errors=errors)


def recalc(path: Path, timeout_s: int = 120) -> RecalcReport:
    """Recalculate `path` in place with LibreOffice headless and return what it computed."""
    soffice = soffice_path()
    with tempfile.TemporaryDirectory(prefix="bbtools-lo-profile-", ignore_cleanup_errors=True) as tmp:
        profile_url = _make_profile(Path(tmp), soffice, timeout_s)
        _run_macro(path.resolve(), profile_url, soffice, timeout_s)
    return scan(path)
