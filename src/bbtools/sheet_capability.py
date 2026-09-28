"""Capability sheet: Cp, Cpk (Pp, Ppk) and % out of specification, one result row per σ estimate.

Convention decision 1 (inventory/conventions.md): the course estimates σ in several ways, so the sheet does
not choose. Each σ the user fills in gets its own result row, labelled with the course page that uses it.
Decision 2: the "6 sigma criterion" is shown in both readings the course uses.

Formulas (course): Cp = (UL − LL)/6σ (deck p. 33); Cpk = min{(UL − x̄)/3σ, (x̄ − LL)/3σ} (deck p. 34);
% out of spec from the normal distribution (deck p. 18-19, 46; Excel check NORM.VERD on deck p. 46).
All quantities are in the user's measurement unit; percentages are stored as fractions.
"""
from __future__ import annotations

from dataclasses import dataclass

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.sheet_tables import lookup_formula
from bbtools.xlsx_style import (
    BOX,
    HeaderBlock,
    Status,
    column_titles,
    font,
    input_cell,
    label,
    output_cell,
    section_title,
    write_header,
)

SHEET = "Capability"

HEADER = HeaderBlock(
    tool="Process capability: Cp, Cpk (Pp, Ppk) and % out of specification",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 18-20, 32-46, 64; "
           "Six Sigma For Dummies.pdf p. 114-116, 159-165; ___4.1 tabellen SPC.pdf p. 1-2",
    convention="Decisions 1-2: one result row per σ estimate the course uses (none chosen for you); "
               "'6 sigma criterion' shown in both course readings.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S06-WE01, S06-WE02, S06-WE04, S06-WE07, S06-WE08, "
                  "S06-WE12, S06-WE13; a few printed values on deck p. 46 and 49 disagree with the computation "
                  "(listed in build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Cp, Cpk (or Pp, Ppk), Z distances and % / ppm out of specification from LSL, USL, mean and a spread; "
            "the two course readings of the '6 sigma' criterion; the Cp levels of deck p. 39.",
    inputs="LSL and/or USL, mean; then any of: σ given, R̄ (+ n), s̄ (+ n), MR̄, overall s. Each spread gets "
           "its own result row, labelled with the course page that uses it.",
    audit="not needed (course worked examples exist)",
    disagreements=(
        "deck p. 46 (S06-WE01): Cp printed '1,166' (1,4/1,2 = 1.1667 rounds to 1,167); centred Cpk likewise.",
        "deck p. 46 notes (S06-WE01): '5 % totaal' and '2,5 % per zijde' for mean 71,8, σ 0,2, specs 71,4-72,8; "
        "the normal distribution gives 2.275 % below LSL and 0.00003 % above USL (2.275 % total).",
        "deck p. 46 notes (S06-WE01, centred): '0,04 % / 400 ppm' two-sided doubles the rounded 0,02 % / 200 ppm; "
        "computed 0.0465 % / 465 ppm.",
        "deck p. 49 (S06-WE12, Minitab): '% out of spec' 8,74 and 9,33 vs 8.731 and 9.315 computed from the "
        "printed mean 0,14852; Minitab used unrounded data. Pp, Ppk, Cp and Cpk agree.",
    ),
)

# Input cells (tests write here).
INPUTS: dict[str, str] = {
    "lsl": "B9", "usl": "B10", "mean": "B11",
    "sigma_given": "B14", "rbar": "B15", "sbar": "B16", "n": "B17", "mrbar": "B18", "s_overall": "B19",
}

# One result row per σ estimate: key, row, label, σ formula, constant formula, constant text, course source.
@dataclass(frozen=True)
class SigmaRow:
    """One line of the results table."""

    key: str
    row: int
    label: str
    sigma: str        # formula for the σ used (column B)
    constant: str     # formula for the table constant used (column Q), '' if none
    constant_note: str
    source: str


SIGMA_ROWS: tuple[SigmaRow, ...] = (
    SigmaRow("given", 23, "σ given in the question", "=IF(ISNUMBER(B14),B14,\"\")", "", "",
             "the question"),
    SigmaRow("rbar_d2", 24, "R-bar / d2  (short term: Cp, Cpk)", "=IF(AND(ISNUMBER(B15),ISNUMBER(Q24)),B15/Q24,\"\")",
             f"=IF(AND(ISNUMBER(B15),ISNUMBER(B17)),IFERROR({lookup_formula('d2', 'B17')},\"n not in Table 18\"),\"\")",
             "d2 for n, Table 18 (___4.1 tabellen SPC.pdf p. 2)",
             "deck p. 64 (speaker notes); exercise workbooks oefening 2, 3, 5"),
    SigmaRow("sbar", 25, "s-bar used directly  (as deck p. 46 does)", "=IF(ISNUMBER(B16),B16,\"\")", "", "",
             "deck p. 46 (Cp = (72,8 − 71,4)/(6 · 0,2))"),
    SigmaRow("sbar_c4", 26, "s-bar / c4  (unbiased, Table A)", "=IF(AND(ISNUMBER(B16),ISNUMBER(Q26)),B16/Q26,\"\")",
             f"=IF(AND(ISNUMBER(B16),ISNUMBER(B17)),IFERROR({lookup_formula('c4', 'B17')},\"n not in Table A\"),\"\")",
             "c4 for n, Table A (___4.1 tabellen SPC.pdf p. 1)",
             "___4.1 tabellen SPC.pdf p. 1 ('An unbiased est. of SD(X) = s̄/c4')"),
    SigmaRow("mrbar", 27, "MR-bar / 1.128  (individual values)", "=IF(AND(ISNUMBER(B18),ISNUMBER(Q27)),B18/Q27,\"\")",
             f"=IF(ISNUMBER(B18),{lookup_formula('d2', '2')},\"\")",
             "d2 for n = 2 (= 1.128), Table 18",
             "Six Sigma For Dummies.pdf p. 114-116 (σ_ST = R̄/1.128)"),
    SigmaRow("overall", 28, "overall s  (long term: these are Pp, Ppk)", "=IF(ISNUMBER(B19),B19,\"\")", "", "",
             "deck p. 32; Six Sigma For Dummies.pdf p. 164-165"),
)
RESULT_ROWS: dict[str, int] = {r.key: r.row for r in SIGMA_ROWS}

# Result columns (tests read here).
RESULT_COLUMNS: dict[str, str] = {
    "sigma": "B", "cp": "C", "cp_level": "D", "cpu": "E", "cpl": "F", "cpk": "G", "cpk_capable": "H",
    "z_lsl": "I", "z_usl": "J", "below_lsl": "K", "above_usl": "L", "out_total": "M", "ppm_total": "N",
}

# Constants of the course, in their own labelled cells so no formula hides a number.
CP_LEVELS = {"net": "B40", "acceptabel": "B41", "goed": "B42", "six": "B43", "cpk_capable": "B45"}
SIX_SIGMA = {"shift": "B35", "z": "B36"}
CRITERION_ROWS = {"long_term_shift": 32, "short_term_centred": 33}


def _inputs(ws: Worksheet) -> None:
    """Sections 1 and 2: the yellow input cells with their labels and validation."""
    section_title(ws, 8, "1. Specification and process")
    rows = [
        (9, "Lower specification limit LSL", "leave empty for a one-sided specification"),
        (10, "Upper specification limit USL", "leave empty for a one-sided specification"),
        (11, "Process mean x-bar (x̄), or the mean of the subgroup means (X̿)", ""),
    ]
    for row, text, note in rows:
        label(ws, row, 1, text)
        input_cell(ws, f"B{row}")
        label(ws, row, 3, note, italic=True)
    # A warning line of its own, so it never hides the notes in column C; red text, shown only when wrong.
    ws["A12"] = '=IF(AND(ISNUMBER(B9),ISNUMBER(B10),B10<=B9),"Check: USL must be above LSL","")'
    ws["A12"].font = font(bold=True, color="C00000")

    section_title(ws, 13, "2. Spread: fill in only what the question gives. Each filled line gets its own "
                          "result row in section 3.")
    rows = [
        (14, "σ given in the question", "e.g. 'standaardafwijking van 10 mm'"),
        (15, "R-bar (R̄) = average range of the subgroups", "needs n below"),
        (16, "s-bar (s̄) = average standard deviation of the subgroups", "needs n below for s-bar / c4"),
        (17, "n = subgroup size (for R-bar and s-bar)", "2 to 25 (Table 18); Table A also 30-100"),
        (18, "MR-bar (MR̄) = average moving range of individual values", "individuals chart"),
        (19, "s = overall standard deviation of all values (STDEV.S)", "long term"),
    ]
    for row, text, note in rows:
        label(ws, row, 1, text)
        input_cell(ws, f"B{row}")
        label(ws, row, 3, note, italic=True)

    positive = DataValidation(type="decimal", operator="greaterThan", formula1="0", allow_blank=True,
                              showErrorMessage=True, errorTitle="Spread must be positive",
                              error="sigma, R-bar, s-bar, MR-bar and s must be greater than 0.")
    subgroup = DataValidation(type="whole", operator="between", formula1="2", formula2="100", allow_blank=True,
                              showErrorMessage=True, errorTitle="Subgroup size", error="n is a whole number, 2 to 100.")
    ws.add_data_validation(positive)
    ws.add_data_validation(subgroup)
    for coordinate in ("B14", "B15", "B16", "B18", "B19"):
        positive.add(coordinate)
    subgroup.add("B17")


def _result_row(ws: Worksheet, spec: SigmaRow) -> None:
    """One row of section 3: σ, indices, level texts, Z distances and fractions out of spec."""
    r = spec.row
    label(ws, r, 1, spec.label)
    number = "0.0000"
    # Reversed limits would give nonsense such as 197 % out of spec: blank σ, and with it the whole row.
    guarded = f'=IF(AND(ISNUMBER($B$9),ISNUMBER($B$10),$B$10<=$B$9),"",{spec.sigma[1:]})'
    output_cell(ws, f"B{r}", guarded, number)
    output_cell(ws, f"C{r}", f"=IF(AND(ISNUMBER(B{r}),ISNUMBER($B$9),ISNUMBER($B$10)),($B$10-$B$9)/(6*B{r}),\"\")", "0.000")
    output_cell(ws, f"D{r}", f"=IF(ISNUMBER(C{r}),IF(C{r}>=$B$43,\"6 Sigma kwaliteitsniveau\",IF(C{r}>=$B$42,\"goed\","
                             f"IF(C{r}>=$B$41,\"acceptabel\",IF(C{r}>=$B$40,\"net capabel\",\"niet capabel\")))),\"\")")
    output_cell(ws, f"E{r}", f"=IF(AND(ISNUMBER(B{r}),ISNUMBER($B$10),ISNUMBER($B$11)),($B$10-$B$11)/(3*B{r}),\"\")", "0.000")
    output_cell(ws, f"F{r}", f"=IF(AND(ISNUMBER(B{r}),ISNUMBER($B$9),ISNUMBER($B$11)),($B$11-$B$9)/(3*B{r}),\"\")", "0.000")
    output_cell(ws, f"G{r}", f"=IF(AND(ISNUMBER(E{r}),ISNUMBER(F{r})),MIN(E{r},F{r}),IF(ISNUMBER(E{r}),E{r},"
                             f"IF(ISNUMBER(F{r}),F{r},\"\")))", "0.000")
    output_cell(ws, f"H{r}", f"=IF(ISNUMBER(G{r}),IF(G{r}>$B$45,\"yes\",\"no\"),\"\")")
    output_cell(ws, f"I{r}", f"=IF(AND(ISNUMBER(B{r}),ISNUMBER($B$9),ISNUMBER($B$11)),($B$11-$B$9)/B{r},\"\")", "0.000")
    output_cell(ws, f"J{r}", f"=IF(AND(ISNUMBER(B{r}),ISNUMBER($B$10),ISNUMBER($B$11)),($B$10-$B$11)/B{r},\"\")", "0.000")
    # NORM.S.DIST(-z) rather than 1 - NORM.S.DIST(z): same value, no loss of digits in the far tail.
    output_cell(ws, f"K{r}", f"=IF(ISNUMBER(I{r}),_xlfn.NORM.S.DIST(-I{r},TRUE),\"\")", "0.0000%")
    output_cell(ws, f"L{r}", f"=IF(ISNUMBER(J{r}),_xlfn.NORM.S.DIST(-J{r},TRUE),\"\")", "0.0000%")
    output_cell(ws, f"M{r}", f"=IF(OR(ISNUMBER(K{r}),ISNUMBER(L{r})),SUM(K{r},L{r}),\"\")", "0.0000%")
    output_cell(ws, f"N{r}", f"=IF(ISNUMBER(M{r}),M{r}*1000000,\"\")", "#,##0.0")
    if spec.constant:
        output_cell(ws, f"Q{r}", spec.constant, "0.0000")
    label(ws, r, 18, spec.constant_note, italic=True)
    label(ws, r, 19, spec.source, italic=True)


def _results(ws: Worksheet) -> None:
    """Section 3: the results table."""
    section_title(ws, 21, "3. Results: one row per spread estimate (a row stays empty until its input is filled)")
    column_titles(ws, 22, [
        "Spread estimate", "σ used", "Cp  (last row: Pp)", "Cp level (deck p. 39)", "Cpu = (USL − mean) / 3σ",
        "Cpl = (mean − LSL) / 3σ", "Cpk = min(Cpu, Cpl)  (last row: Ppk)", "Cpk > 1.33? (Dummies p. 164)",
        "Z: LSL lies … σ below the mean", "Z: USL lies … σ above the mean", "% below LSL", "% above USL",
        "% out of spec, total", "ppm out of spec, total", "", "", "Constant used", "Which constant", "Course source",
    ])
    for spec in SIGMA_ROWS:
        _result_row(ws, spec)


def _criterion(ws: Worksheet) -> None:
    """Section 4: the '6 sigma' criterion in both course readings (decision 2)."""
    section_title(ws, 30, "4. The '6 sigma' criterion: the most you may have out of spec. The course uses two readings.")
    column_titles(ws, 31, ["Reading", "Z used", "Max % out of spec", "Max ppm", "Course source"])
    label(ws, 32, 1, "Long term, with the 1.5σ shift: one tail beyond Z = 6 − 1.5")
    output_cell(ws, "B32", f"={SIX_SIGMA['z']}-{SIX_SIGMA['shift']}", "0.0")
    output_cell(ws, "C32", "=_xlfn.NORM.S.DIST(-B32,TRUE)", "0.00000%")
    output_cell(ws, "D32", "=C32*1000000", "0.0")
    label(ws, 32, 5, "deck p. 20 (table: 6 -> 3.4 DPMO), 36-37 (notes); Dummies p. 27, 159-160; Harry & Schroeder summary p. 2 (3.4 dpm)",
          italic=True)
    label(ws, 33, 1, "Short term, centred process with Cp = 2: both tails beyond ±6σ")
    output_cell(ws, "B33", f"={SIX_SIGMA['z']}", "0.0")
    output_cell(ws, "C33", "=2*_xlfn.NORM.S.DIST(-B33,TRUE)", "0.0000000%")
    output_cell(ws, "D33", "=C33*1000000", "0.000")
    label(ws, 33, 5, "deck p. 39: 'Cp = 2: 6 Sigma kwaliteitsniveau - 2 defect per miljard' (short term)", italic=True)
    _constant(ws, 35, "Shift assumed by the course (σ)", 1.5, "deck p. 36; Dummies p. 159 ('Zlt = Zst - 1.5')")
    _constant(ws, 36, "Six sigma: distance from mean to spec (σ)", 6, "deck p. 39 (Cp = 2: 6 Sigma kwaliteitsniveau)")


def _levels(ws: Worksheet) -> None:
    """Section 5: the course's interpretation thresholds, referenced by columns D and H."""
    section_title(ws, 38, "5. Interpretation thresholds used in columns D and H")
    label(ws, 39, 1, "Cp < 1: niet capabel", italic=True)
    _constant(ws, 40, "Cp ≥ this: net capabel", 1, "deck p. 39 ('Cp=1: net capabel')")
    _constant(ws, 41, "Cp ≥ this: acceptabel", 1.33, "deck p. 39 ('Cp>=1,33: acceptabel')")
    _constant(ws, 42, "Cp ≥ this: goed", 1.67, "deck p. 39 ('Cp>=1,67: goed')")
    _constant(ws, 43, "Cp ≥ this: 6 Sigma kwaliteitsniveau", 2, "deck p. 39 ('Cp=2: 6 Sigma kwaliteitsniveau')")
    _constant(ws, 45, "Cpk greater than this: capable in the short term", 1.33,
              "Dummies p. 164 ('a CPK greater than 1.33 indicates ... capable in the short-term')")
    section_title(ws, 47, "6. How to improve capability (course)")
    label(ws, 48, 1, "Centre the process (mean to the middle of LSL and USL): Cpk rises to Cp. Deck p. 35, 41-44, 46.")
    label(ws, 49, 1, "Reduce the variation (σ): Cp and Cpk both rise. Deck p. 21-22, 35; Dummies p. 165-166.")


def _constant(ws: Worksheet, row: int, text: str, value: float, source: str) -> None:
    """A course constant in its own boxed cell (not an input, not a result), with its source."""
    label(ws, row, 1, text)
    cell = ws.cell(row=row, column=2, value=value)
    cell.font = font(bold=True)
    cell.border = BOX
    label(ws, row, 3, source, italic=True)


def build_capability_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the capability calculator."""
    write_header(ws, HEADER)
    _inputs(ws)
    _results(ws)
    _criterion(ws)
    _levels(ws)
    ws.column_dimensions["A"].width = 52
    for letter in "BCDEFGHIJKLMN":
        ws.column_dimensions[letter].width = 13
    ws.column_dimensions["D"].width = 22
    for letter in "OP":
        ws.column_dimensions[letter].width = 2
    ws.column_dimensions["Q"].width = 10
    ws.column_dimensions["R"].width = 44
    ws.column_dimensions["S"].width = 60
    ws.row_dimensions[22].height = 42
