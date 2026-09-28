"""The Tables sheet: every transcribed control-chart constant table in full, disagreements highlighted.

Calculators never hard-code a constant; they look it up here through workbook names such as `T18_d2`
(values) and `T18_n` (subgroup sizes). `lookup_formula` builds that lookup.
"""
from __future__ import annotations

from collections import defaultdict

from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.constants import USED_TABLE, AverageRangeTable, ConstantTable, load_average_range_table
from bbtools.printed import decimals_printed, parse_printed, rounding_consistent
from bbtools.readme import SheetDoc
from bbtools.xlsx_style import BOX, FLAG_FILL, HeaderBlock, Status, column_titles, font, label, write_header

SHEET = "Tables"

HEADER = HeaderBlock(
    tool="Tables: control-chart, capability and MSA constants",
    source="source/course/Les 4/___4.1 tabellen SPC.pdf p. 1-2; Control charts - constants.pdf p. 1-2; "
           "Six Sigma For Dummies.pdf p. 250; Les 5/20260619_ottoy_tabel MSA.pdf p. 1",
    convention="Decision 4: calculators use Table 18; c4 and d3 from Table A; A3, E2, B5, B6 from Six Sigma "
               "Demystified. Every source is shown in full, as printed.",
    status=Status.VERIFIED,
    status_detail="transcriptions of both scanned tables double-checked cell by cell; values compared with "
                  "their mathematical definitions in tests/test_constants.py",
)


DOC = SheetDoc(
    sheet=SHEET,
    purpose="Every control-chart constant table of the course, exactly as printed, with the lookup ranges the "
            "calculators use. Orange cells differ beyond rounding from another printed source (hover for the values).",
    inputs="none (reference sheet)",
    audit="not needed (transcriptions double-checked; values compared with their definitions)",
    disagreements=(),
)


def excel_name(key: str, symbol: str) -> str:
    """Workbook name for one constant column, e.g. ('T18', '1/d2') -> 'T18_inv_d2'."""
    return f"{key}_{symbol.replace('1/', 'inv_').replace('*', 'star')}"


def lookup_formula(symbol: str, n_ref: str) -> str:
    """Excel expression (no leading '=') returning `symbol` for subgroup size `n_ref`, from the used table."""
    key = USED_TABLE[symbol]
    return f"INDEX({excel_name(key, symbol)},MATCH({n_ref},{key}_n,0))"


def d2_star_formula(g_ref: str, m_ref: str) -> str:
    """Excel expression for d2* of g subgroups of size m (tabel MSA.pdf)."""
    return f"INDEX(MSA_d2star,MATCH({g_ref},MSA_g,0),MATCH({m_ref},MSA_m,0))"


def msa_d2_formula(m_ref: str) -> str:
    """Excel expression for d2 (g → ∞) of subgroup size m, from the last row of tabel MSA.pdf."""
    return f"INDEX(MSA_d2,1,MATCH({m_ref},MSA_m,0))"


def disagreeing_cells(tables: tuple[ConstantTable, ...]) -> dict[tuple[str, str, str], list[str]]:
    """(table key, symbol, n) -> other sources' printed values, for every value that disagrees beyond rounding."""
    seen: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    for table in tables:
        for symbol, column in table.symbol_columns().items():
            for row in table.rows:
                value = row[column].strip()
                if value and _is_number(value):
                    seen[(symbol, row[0].strip())].append((table.source.key, value))
    flagged: dict[tuple[str, str, str], list[str]] = {}
    for (symbol, n), entries in seen.items():
        if len(entries) > 1 and not rounding_consistent([v for _, v in entries]):
            for key, value in entries:
                flagged[(key, symbol, n)] = [f"{other_key}: {other}" for other_key, other in entries if other_key != key]
    return flagged


def _is_number(text: str) -> bool:
    """True if the printed text is a single number."""
    try:
        parse_printed(text)
    except ValueError:
        return False
    return True


def _write_cell(ws: Worksheet, row: int, column: int, printed: str) -> None:
    """Write a printed value: numbers as numbers displayed with the printed decimals, the rest as text."""
    cell = ws.cell(row=row, column=column)
    if printed.strip() and _is_number(printed):
        cell.value = float(parse_printed(printed))
        decimals = decimals_printed(printed)
        cell.number_format = "0" if decimals == 0 else "0." + "0" * decimals
    else:
        cell.value = printed
    cell.font = font()
    cell.border = BOX


def _write_table(ws: Worksheet, wb: Workbook, top: int, table: ConstantTable,
                 flagged: dict[tuple[str, str, str], list[str]]) -> int:
    """Write one table starting at row `top`, define its workbook names, return the next free row."""
    label(ws, top, 1, table.title, bold=True)
    label(ws, top + 1, 1, f"Source: {table.source_file} p. {table.source_page}. Printed there as from: "
                          f"{table.source.origin}.", italic=True)
    label(ws, top + 2, 1, table.source.role, bold=True)
    column_titles(ws, top + 3, list(table.columns))
    first = top + 4
    for offset, row in enumerate(table.rows):
        for column, printed in enumerate(row, start=1):
            _write_cell(ws, first + offset, column, printed)
    last = first + len(table.rows) - 1
    symbols = {i: s for s, i in table.symbol_columns().items()}
    for offset, row in enumerate(table.rows):
        n = row[0].strip()
        if n == "0":  # Six Sigma Demystified p. 1 prints a stray row '0 | 2.606' (review_items.md)
            ws.cell(row=first + offset, column=1).comment = Comment(
                "Printed like this in the source (a stray row after n = 2). Not a subgroup size; never used.", "bbtools")
        for column, symbol in symbols.items():
            others = flagged.get((table.source.key, symbol, n))
            if others:
                cell = ws.cell(row=first + offset, column=column + 1)
                cell.fill = FLAG_FILL
                cell.comment = Comment("Other printed sources: " + "; ".join(others), "bbtools")
    _define(wb, f"{table.source.key}_n", 1, first, last)
    for column, symbol in symbols.items():
        _define(wb, excel_name(table.source.key, symbol), column + 1, first, last)
    return last + 2


def _define(wb: Workbook, name: str, column: int, first: int, last: int) -> None:
    """Workbook-level name for one column range on the Tables sheet."""
    letter = get_column_letter(column)
    wb.defined_names[name] = DefinedName(name, attr_text=f"{SHEET}!${letter}${first}:${letter}${last}")


def _define_area(wb: Workbook, name: str, top_left: tuple[int, int], bottom_right: tuple[int, int]) -> None:
    """Workbook-level name for a rectangular range (row, column) on the Tables sheet."""
    (r1, c1), (r2, c2) = top_left, bottom_right
    area = f"${get_column_letter(c1)}${r1}:${get_column_letter(c2)}${r2}"
    wb.defined_names[name] = DefinedName(name, attr_text=f"{SHEET}!{area}")


def _write_average_range(ws: Worksheet, wb: Workbook, top: int, table: AverageRangeTable) -> int:
    """The MSA d2* table as two grids (d2* and ν, rows g, columns m) plus the d2 and cd rows; returns the next row."""
    label(ws, top, 1, table.title, bold=True)
    label(ws, top + 1, 1, f"Source: {table.source_file} p. {table.source_page}. Printed there as from: Measurement "
                          f"Systems Analysis Reference Manual (DaimlerChrysler, Ford, GM), 2002.", italic=True)
    label(ws, top + 2, 1, "USED by the Gage R&R sheet (K1 = 1/d2 with g → ∞; K2, K3 = 1/d2* with g = 1). Each printed "
                          "cell 'ν / d2*' is split into the two grids below.", bold=True)
    row = top + 3
    for grid_name, values, fmt_source in (("d2*", table.d2_star, "d2_star"), ("ν (degrees of freedom)", table.nu, "nu")):
        column_titles(ws, row, [f"{grid_name}: g \\ m"] + [str(m) for m in table.m])
        for column, m in enumerate(table.m, start=2):
            ws.cell(row=row, column=column).value = m  # numeric, so MATCH finds it
        for offset, (g, printed) in enumerate(zip(table.g, values, strict=True), start=1):
            ws.cell(row=row + offset, column=1, value=g).border = BOX
            for column, text in enumerate(printed, start=2):
                _write_cell(ws, row + offset, column, text)
        name = "MSA_d2star" if fmt_source == "d2_star" else "MSA_nu"
        _define_area(wb, name, (row + 1, 2), (row + len(table.g), 1 + len(table.m)))
        if fmt_source == "d2_star":
            _define_area(wb, "MSA_m", (row, 2), (row, 1 + len(table.m)))
            _define(wb, "MSA_g", 1, row + 1, row + len(table.g))
        row += len(table.g) + 2
    for text, values, name in (("d2 (g → ∞)", table.d2, "MSA_d2"), ("cd", table.cd, "MSA_cd")):
        label(ws, row, 1, text, bold=True)
        for column, printed in enumerate(values, start=2):
            _write_cell(ws, row, column, printed)
        _define_area(wb, name, (row, 2), (row, 1 + len(table.m)))
        row += 1
    return row + 1


def build_tables_sheet(wb: Workbook, tables: tuple[ConstantTable, ...]) -> Worksheet:
    """Add the Tables sheet to `wb` and define the lookup names the calculators use."""
    ws = wb.create_sheet(SHEET)
    write_header(ws, HEADER)
    label(ws, 8, 1, "How to read: each table below is exactly as printed in the course. Calculators take d2, "
                    "A2, D3, D4 ... from Table 18; c4 and d3 from Table A; A3, E2, B5, B6 from Six Sigma "
                    "Demystified. Orange = that value differs (beyond rounding) from another source for the same n; "
                    "hover the cell to see the other values.")
    flagged = disagreeing_cells(tables)
    row = 10
    for table in tables:
        row = _write_table(ws, wb, row, table, flagged)
    _write_average_range(ws, wb, row, load_average_range_table())
    ws.column_dimensions["A"].width = 16
    for column in range(2, 20):
        ws.column_dimensions[get_column_letter(column)].width = 9
    return ws
