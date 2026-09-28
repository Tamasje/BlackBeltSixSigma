"""Transcribed constant tables (inventory/constants/*.csv) as typed values, plus which table each calculator uses.

Values stay the strings the course prints; converting to numbers happens only where a cell is written or a
comparison is made, so the printed precision is never lost.

Which table a calculator uses is convention decision 4 (inventory/conventions.md): Table 18 first (the
lecturer's exercise workbooks use its values), then Table A for c4 and d3, then Six Sigma Demystified for
A3, E2, B5 and B6. Dummies Table 10-2 is shown for reference only.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS_DIR = ROOT / "inventory" / "constants"
PROVENANCE_COLUMNS = ("source_file", "source_page", "table_name")

# Symbols of control-chart / MSA constants. Case matters: d3 (range spread) is not D3 (limit factor).
CONSTANT_SYMBOLS = {
    "A", "A0", "A1", "A2", "A3", "c2", "1/c2", "c4", "1/c4", "B1", "B2", "B3", "B4", "B5", "B6",
    "d2", "1/d2", "d3", "D1", "D2", "D3", "D4", "E2", "d2*",
}


@dataclass(frozen=True)
class TableSource:
    """One constant table shown on the Tables sheet."""

    key: str       # short prefix for workbook names, e.g. 'T18' -> T18_d2
    csv_stem: str  # file name in inventory/constants/ without .csv
    role: str      # what the calculators use it for, shown next to the table
    origin: str    # the book the course copied it from, as printed on the page


TABLE_SOURCES: tuple[TableSource, ...] = (
    TableSource("T18", "S06_table_18_factors_for_computing_control_chart_lines",
                "USED by the calculators (the lecturer's exercise workbooks use these values).",
                "E.L. Crow, F.A. Davis, M.W. Maxfield, Statistics Manual, 1960 (adapted from ASTM, 1951)"),
    TableSource("TA", "S06_table_a_bias_correction_factors_for_estimating_standard_devi",
                "USED for c4 and d3 (Table 18 does not give them). Reference for d2 and c2.",
                "D.J. Wheeler, Understanding Industrial Experimentation, 1987"),
    TableSource("SSD1", "S06_control_chart_constants_chart_for_average_chart_for_standard",
                "USED for A3, B5 and B6 (Table 18 and Table A do not give them). Reference otherwise.",
                "Six Sigma Demystified, 2nd edition"),
    TableSource("SSD2", "S06_control_chart_constants_chart_for_ranges_x_charts_six_sigma",
                "USED for E2 (Table 18 and Table A do not give it). Reference otherwise.",
                "Six Sigma Demystified, 2nd edition"),
    TableSource("DUM", "S08_table_10_2_continuous_data_control_chart_constants_a2_a3_b3",
                "Reference only.",
                "Six Sigma For Dummies, Table 10-2"),
)

# Decision 4: the table a calculator takes each constant from.
USED_TABLE: dict[str, str] = {
    "A": "T18", "A0": "T18", "A1": "T18", "A2": "T18", "c2": "T18", "1/c2": "T18",
    "B1": "T18", "B2": "T18", "B3": "T18", "B4": "T18", "d2": "T18", "1/d2": "T18",
    "D1": "T18", "D2": "T18", "D3": "T18", "D4": "T18",
    "c4": "TA", "d3": "TA",
    "A3": "SSD1", "1/c4": "SSD1", "B5": "SSD1", "B6": "SSD1", "E2": "SSD2",
}


@dataclass(frozen=True)
class ConstantTable:
    """A transcribed table: printed column labels and printed cell strings, with its provenance."""

    source: TableSource
    title: str
    source_file: str
    source_page: int
    columns: tuple[str, ...]            # first column is the subgroup size n
    rows: tuple[tuple[str, ...], ...]   # printed strings, same width as columns

    def symbol_columns(self) -> dict[str, int]:
        """Constant symbol -> column index, for every column that is a known constant."""
        return {normalise_symbol(c): i for i, c in enumerate(self.columns) if normalise_symbol(c) in CONSTANT_SYMBOLS}

    def value(self, symbol: str, n: int) -> str | None:
        """Printed value of `symbol` for subgroup size `n`, or None if the table does not give it."""
        column = self.symbol_columns().get(symbol)
        if column is None:
            return None
        for row in self.rows:
            if row[0].strip() == str(n) and row[column].strip():
                return row[column].strip()
        return None


def normalise_symbol(label: str) -> str:
    """Map a column label such as 'd₂', 'D_4' or 'A 2' onto a CONSTANT_SYMBOLS spelling."""
    text = unicodedata.normalize("NFKC", label)  # turns subscript digits into plain digits
    return re.sub(r"[\s_{}$]", "", text)


def load_table(source: TableSource, constants_dir: Path = CONSTANTS_DIR) -> ConstantTable:
    """Read one table CSV written by merge_inventory.py; provenance columns move into the dataclass."""
    path = constants_dir / f"{source.csv_stem}.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        body = [row for row in reader if row]
    width = len(header) - len(PROVENANCE_COLUMNS)
    if tuple(header[width:]) != PROVENANCE_COLUMNS:
        raise ValueError(f"{path}: expected provenance columns {PROVENANCE_COLUMNS}, found {header[width:]}")
    files = {row[width] for row in body}
    pages = {row[width + 1] for row in body}
    titles = {row[width + 2] for row in body}
    if len(files) != 1 or len(pages) != 1 or len(titles) != 1:
        raise ValueError(f"{path}: rows disagree on provenance ({files}, {pages}, {titles})")
    return ConstantTable(
        source=source,
        title=titles.pop(),
        source_file=files.pop(),
        source_page=int(pages.pop()),
        columns=tuple(header[:width]),
        rows=tuple(tuple(row[:width]) for row in body),
    )


def load_all(constants_dir: Path = CONSTANTS_DIR) -> tuple[ConstantTable, ...]:
    """Every table listed in TABLE_SOURCES, in display order."""
    return tuple(load_table(source, constants_dir) for source in TABLE_SOURCES)


AVERAGE_RANGE_STEM = "S10_values_associated_with_the_distribution_of_the_average_range"


@dataclass(frozen=True)
class AverageRangeTable:
    """'Values associated with the Distribution of the Average Range' (tabel MSA.pdf p. 1, from the AIAG MSA manual).

    Each printed cell holds two numbers, 'ν/d2*', for g subgroups (rows) of size m (columns); the last printed row
    holds d2 (g → ∞) and the constant difference cd. All values stay the printed strings.
    """

    title: str
    source_file: str
    source_page: int
    m: tuple[int, ...]                       # subgroup sizes (columns), 2 .. 20
    g: tuple[int, ...]                       # numbers of subgroups (rows), 1 .. 20
    nu: tuple[tuple[str, ...], ...]          # [g][m] degrees of freedom
    d2_star: tuple[tuple[str, ...], ...]     # [g][m] d2*
    d2: tuple[str, ...]                      # [m] d2 for g → ∞
    cd: tuple[str, ...]                      # [m] constant difference of ν


def load_average_range_table(constants_dir: Path = CONSTANTS_DIR) -> AverageRangeTable:
    """Read the MSA d2* table CSV and split every 'ν/d2*' cell into its two printed numbers."""
    path = constants_dir / f"{AVERAGE_RANGE_STEM}.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    header, body = rows[0], [row for row in rows[1:] if row]
    width = len(header) - len(PROVENANCE_COLUMNS)
    m = tuple(int(label) for label in header[1:width])
    grid = [row for row in body if row[0].strip().isdigit()]
    last = next(row for row in body if row[0].startswith("d2"))

    def split(cell: str) -> tuple[str, str]:
        first, second = cell.split("/")
        return first.strip(), second.strip()

    pairs = [[split(cell) for cell in row[1:width]] for row in grid]
    d2_cd = [split(cell) for cell in last[1:width]]
    return AverageRangeTable(
        title=body[0][width + 2], source_file=body[0][width], source_page=int(body[0][width + 1]),
        m=m, g=tuple(int(row[0]) for row in grid),
        nu=tuple(tuple(p[0] for p in row) for row in pairs),
        d2_star=tuple(tuple(p[1] for p in row) for row in pairs),
        d2=tuple(p[0] for p in d2_cd), cd=tuple(p[1] for p in d2_cd),
    )
