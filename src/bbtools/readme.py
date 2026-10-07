"""Write build/README.md: one section per sheet (purpose, inputs, sources, convention, status, audit) plus the
list of printed course values that disagree with an independent computation.

Everything is taken from the sheet modules' HeaderBlock and SheetDoc, so the README cannot drift from the sheets.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bbtools.constant_definitions import differences
from bbtools.constants import ROOT, TABLE_SOURCES, load_all
from bbtools.xlsx_style import HeaderBlock

README = ROOT / "build" / "README.md"


@dataclass(frozen=True)
class SheetDoc:
    """What the README says about one sheet, beyond its header block."""

    sheet: str
    purpose: str
    inputs: str
    audit: str                        # stats-auditor result, or why none was needed
    disagreements: tuple[str, ...]    # printed course values that disagree with the computation


def _sheet_section(header: HeaderBlock, doc: SheetDoc) -> list[str]:
    """Markdown for one sheet."""
    lines = [
        f"## {doc.sheet}: {header.tool}", "",
        f"- **Doel:** {doc.purpose}",
        f"- **Invoer:** {doc.inputs}",
        f"- **Bron in de cursus:** {header.source}",
        f"- **Conventie:** {header.convention}",
        f"- **Status:** {header.status.label}: {header.status_detail}",
        f"- **Audit:** {doc.audit}",
    ]
    if doc.disagreements:
        lines += ["- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; "
                  "getest als strikte verwachte mislukkingen, strict xfail):"]
        lines += [f"  - {item}" for item in doc.disagreements]
    return lines + [""]


def _constants_section() -> list[str]:
    """Markdown table of printed constants more than one unit of their last digit from their definition."""
    names = {s.key: f"{s.key} ({s.origin})" for s in TABLE_SOURCES}
    larger = [d for d in differences(load_all()) if not d.rounding_only]
    lines = [
        "## Constanten die afwijken van hun wiskundige definitie", "",
        "Elke gedrukte constante is vergeleken met haar definitie (tests/test_constant_definitions.py). "
        "Verschillen van hoogstens één eenheid in het laatste gedrukte cijfer (afronding van afgeronde invoer) staan "
        "hier niet. De rekenbladen gebruiken nog steeds de gedrukte waarden (conventiebeslissing 4); niets is "
        "overschreven.", "",
        "| Tabel | Constante | n | Gedrukt | Definitie | Verschil (eenheden van het laatste cijfer) |",
        "|---|---|---|---|---|---|",
    ]
    lines += [f"| {d.table} | {d.symbol} | {d.n} | {d.printed} | {d.definition:.5f} | {d.units:g} |" for d in larger]
    lines += ["", "Tabellen: " + "; ".join(names.values()) + ".", ""]
    return lines


def write_readme(sheets: list[tuple[HeaderBlock, SheetDoc]], path: Path = README) -> Path:
    """Write the README for the given sheets, in workbook order."""
    lines = [
        "# bb_toolkit.xlsx", "",
        "Offline rekenbladen (calculators) voor het Black Belt-examen. Gemaakt door `src/bbtools/` "
        "(`PYTHONPATH=src python3 -m bbtools.build_workbook`); nooit met de hand aanpassen.", "",
        "**Gebruik:** typ alleen in de gele cellen; groene cellen zijn resultaten. Een resultaatrij blijft leeg tot de "
        "invoer die ze nodig heeft is ingevuld. Elk blad begint met de bron in de cursus, de gebruikte conventie en de "
        "verificatiestatus. Excel herberekent het hele bestand bij het openen.", "",
        "**Extra (boeken):** het blad *Extra (boeken)* bevat de rekenblokken die alleen uit Six Sigma For Dummies en "
        "Harry & Schroeder komen. Die boeken zijn niet te kennen voor het examen.", "",
        "**Cursusindex:** `index.html` naast dit bestand linkt elk onderwerp, elke formule en elke vraag van het "
        "voorbeeldexamen naar de pagina in de cursus (`PYTHONPATH=src python3 -m bbtools.build_index`). Houd `source/` "
        "naast `build/`.", "",
    ]
    for header, doc in sheets:
        lines += _sheet_section(header, doc)
    lines += _constants_section()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path
