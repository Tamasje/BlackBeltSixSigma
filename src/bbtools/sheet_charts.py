"""Control charts sheet: X̄-R and X̄-s from subgroups, individuals and moving range (I-MR), p chart and u chart.

Course: X̄/R and X̄/s limits CL = X̿, X̿ ± A2·R̄, D3·R̄ … D4·R̄, X̿ ± A3·s̄, B3·s̄ … B4·s̄ (deck p. 74); σ = R̄/d2 and
σ(x̄) = σ/√n (deck p. 64 notes); I-MR X̄ ± E2·MR̄, D4·MR̄ (Dummies p. 249); p chart p̄ ± 3√(p̄(1 − p̄)/n_i) and u chart
ū ± 3√(ū/n_i) (Dummies p. 254); Western Electric rules (deck p. 68-69). Constants from the Tables sheet
(decision 4: Table 18; c4 from Table A; A3 and E2 from Six Sigma Demystified). A negative lower limit is set to 0.

Row plan: X̄-R / X̄-s summary 8-27, subgroup table 30-79 (50 subgroups); I-MR 82-192 (100 values);
p chart 195-250 (50 subgroups); u chart 253-308 (50 subgroups); rules 311-316.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.sheet_tables import lookup_formula
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    column_titles,
    input_cell,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "Control charts"

HEADER = HeaderBlock(
    tool="Control charts: X̄-R and X̄-s (subgroups), I-MR (individuals), p chart and u chart, with out-of-limit flags",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 54-58, 62-74; ___4.1 tabellen SPC.pdf "
           "p. 1-2; Six Sigma For Dummies.pdf p. 239-256; Les 5/20260619_ottoy_Rheostat Knob Data.xls",
    convention="Decision 4: constants from Table 18 (A2, D3, D4, B3, B4, d2), Table A (c4), Six Sigma Demystified "
               "(A3, E2); 3σ limits; a negative lower limit is shown as 0.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S06-WE03, S06-WE05, S06-WE06, S08-WE18, S08-WE21, S10-WE04a, "
                  "S10-WE04b; a few printed values disagree (build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Control limits and centre lines for X̄-R, X̄-s, I-MR, p and u charts, the σ estimates R̄/d2 and s̄/c4, and a "
            "flag for every subgroup or point outside its limits.",
    inputs="subgroups as raw values (up to 10 per row) or as typed x̄ and R (and s) with n; individual values; subgroup "
           "sizes with defectives (p) or defects (u).",
    audit="not needed (course worked examples exist)",
    disagreements=(
        "Rheostat Knob Data.xls (Les 5, S10-WE04a/b) computes UCL_R with D4 = 2.114 (Six Sigma Demystified); the Les 4 "
        "exercise workbooks use 2.115 (Table 18), which the sheet uses (decision 4). The X̄ limits agree.",
        "Dummies p. 256 (S08-WE21): u-chart upper limit printed '2379' without a decimal point; computed 2.379 for the "
        "last subgroup (n = 65). Centre line and lower limit agree.",
        "Dummies p. 251 and 255 (S08-WE19, S08-WE20): chart readouts without the data or subgroup size behind them; "
        "not used as test targets.",
    ),
)

SUBGROUPS, FIRST_SUBGROUP = 50, 30
INDIVIDUALS, FIRST_INDIVIDUAL = 100, 93
ATTRIBUTE_ROWS, FIRST_P, FIRST_U = 50, 201, 259
NUMBER = "0.000000"
X_COLUMNS = "BCDEFGHIJK"  # x1 .. x10 of a subgroup

INPUTS = {"n_typed": "B9"}
SUMMARY = {"k": "B12", "n": "B13", "equal": "B14", "xbarbar": "B15", "rbar": "B16", "sbar": "B17",
           "sigma_r": "B18", "d2": "C18", "sigma_s": "B19", "c4": "C19", "sigma_xbar": "B20"}
LIMITS = {"xbar_r": 23, "r": 24, "xbar_s": 25, "s": 26}  # columns B = LCL, C = CL, D = UCL, F/G = constants
IMR = {"k": "B83", "xbar": "B84", "mrbar": "B85", "sigma": "B86", "x_row": 89, "mr_row": 90}
P_CHART = {"n_total": "B196", "d_total": "B197", "pbar": "B198"}
U_CHART = {"n_total": "B254", "c_total": "B255", "ubar": "B256"}


def subgroup_row(index: int) -> int:
    """Row of subgroup `index` (0-based) in the X̄-R / X̄-s table."""
    return FIRST_SUBGROUP + index


def _constant(symbol: str, n_ref: str) -> str:
    """Formula for a table constant at subgroup size `n_ref`, or a message when n is outside the table."""
    return f'=IF(ISNUMBER({n_ref}),IFERROR({lookup_formula(symbol, n_ref)},"n not in table"),"")'


def _flag(value: str, low: str, high: str) -> str:
    """Formula: 'above UCL' / 'below LCL' / '' for a plotted value against its limits."""
    return (f'=IF(AND(ISNUMBER({value}),ISNUMBER({low}),ISNUMBER({high})),IF({value}>{high},"above UCL",'
            f'IF({value}<{low},"below LCL","")),"")')


def _subgroups(ws: Worksheet) -> None:
    """Section 1: X̄-R and X̄-s summary, limits and the subgroup table."""
    section_title(ws, 8, "1. X̄-R and X̄-s charts from subgroups (fill the table from row 30: raw values, or x̄ and R)")
    input_row(ws, 9, "n = subgroup size, when subgroups are typed as x̄ and R", "raw values: n is counted per row")
    section_title(ws, 11, "Summary of the subgroups")
    first, last = subgroup_row(0), subgroup_row(SUBGROUPS - 1)
    col = {name: f"{letter}{first}:{letter}{last}" for name, letter in (("n", "O"), ("x", "P"), ("r", "Q"), ("s", "R"))}
    result_row(ws, 12, "k = number of subgroups", f'=IF(COUNT({col["x"]})>0,COUNT({col["x"]}),"")', "0")
    result_row(ws, 13, "n used (largest subgroup size)", f'=IF(COUNT({col["n"]})>0,MAX({col["n"]}),"")', "0")
    result_row(ws, 14, "Equal subgroup sizes?", f'=IF(COUNT({col["n"]})>0,IF(MIN({col["n"]})=MAX({col["n"]}),"yes",'
               f'"NO: limits use the largest n (deck p. 74: variable sample size)"),"")')
    result_row(ws, 15, "X̿ = mean of the subgroup means", f'=IF(COUNT({col["x"]})>0,AVERAGE({col["x"]}),"")', NUMBER)
    result_row(ws, 16, "R̄ = mean range", f'=IF(COUNT({col["r"]})>0,AVERAGE({col["r"]}),"")', NUMBER)
    result_row(ws, 17, "s̄ = mean standard deviation", f'=IF(COUNT({col["s"]})>0,AVERAGE({col["s"]}),"")', NUMBER)
    label(ws, 18, 1, "σ̂ = R̄ / d2  (d2 in column C)")
    output_cell(ws, "C18", _constant("d2", "B13"), "0.000")
    output_cell(ws, "B18", '=IF(AND(ISNUMBER(B16),ISNUMBER(C18)),B16/C18,"")', NUMBER)
    label(ws, 18, 4, "deck p. 64 (speaker notes)", italic=True)
    label(ws, 19, 1, "σ̂ = s̄ / c4  (c4 in column C)")
    output_cell(ws, "C19", _constant("c4", "B13"), "0.0000")
    output_cell(ws, "B19", '=IF(AND(ISNUMBER(B17),ISNUMBER(C19)),B17/C19,"")', NUMBER)
    label(ws, 19, 4, "___4.1 tabellen SPC.pdf p. 1", italic=True)
    result_row(ws, 20, "σ(x̄) = σ̂ / √n  (with R̄/d2)", '=IF(AND(ISNUMBER(B18),ISNUMBER(B13)),B18/SQRT(B13),"")', NUMBER,
               "deck p. 64 notes")

    column_titles(ws, 22, ["Chart", "LCL", "CL", "UCL", "Constants", "value", "value", "Course source"])
    specs = {
        "xbar_r": ("X̄ chart with R̄: X̿ ± A2·R̄", "A2", None, "B15", "B16", "deck p. 74; Dummies p. 249"),
        "r": ("R chart: D3·R̄ … D4·R̄", "D3", "D4", "B16", "B16", "deck p. 74"),
        "xbar_s": ("X̄ chart with s̄: X̿ ± A3·s̄", "A3", None, "B15", "B17", "deck p. 74; notes p. 73: s preferred for n > 10"),
        "s": ("s chart: B3·s̄ … B4·s̄", "B3", "B4", "B17", "B17", "deck p. 74"),
    }
    for key, (text, c1, c2, centre, spread, source) in specs.items():
        r = LIMITS[key]
        label(ws, r, 1, text)
        label(ws, r, 5, f"{c1}, {c2}" if c2 else c1)
        output_cell(ws, f"F{r}", _constant(c1, "$B$13"), "0.000")
        if c2:
            output_cell(ws, f"G{r}", _constant(c2, "$B$13"), "0.000")
        needed = [centre, f"F{r}"] + ([f"G{r}"] if c2 else [])
        ok = "AND(" + ",".join(f"ISNUMBER({cell})" for cell in needed) + ")"
        if c2:  # R and s charts: limits are constant × centre line
            output_cell(ws, f"B{r}", f'=IF({ok},F{r}*{centre},"")', NUMBER)
            output_cell(ws, f"D{r}", f'=IF({ok},G{r}*{centre},"")', NUMBER)
        else:   # X̄ charts: X̿ ± constant × spread
            output_cell(ws, f"B{r}", f'=IF(AND({ok},ISNUMBER({spread})),{centre}-F{r}*{spread},"")', NUMBER)
            output_cell(ws, f"D{r}", f'=IF(AND({ok},ISNUMBER({spread})),{centre}+F{r}*{spread},"")', NUMBER)
        output_cell(ws, f"C{r}", f'=IF(ISNUMBER({centre}),{centre},"")', NUMBER)
        label(ws, r, 8, source, italic=True)

    column_titles(ws, FIRST_SUBGROUP - 1, ["Subgroup", *[f"x{i}" for i in range(1, 11)], "or: x̄ typed", "R typed",
                                            "s typed", "n", "x̄", "R", "s", "x̄ vs X̄-R", "R vs R", "x̄ vs X̄-s", "s vs s"])
    lim = {key: (f"$B${r}", f"$D${r}") for key, r in LIMITS.items()}
    for index in range(SUBGROUPS):
        r = subgroup_row(index)
        raw = f"B{r}:K{r}"
        ws[f"A{r}"] = index + 1
        for letter in X_COLUMNS + "LMN":
            input_cell(ws, f"{letter}{r}")
        output_cell(ws, f"O{r}", f'=IF(COUNT({raw})>0,COUNT({raw}),IF(OR(ISNUMBER(L{r}),ISNUMBER(M{r})),$B$9,""))', "0")
        output_cell(ws, f"P{r}", f'=IF(COUNT({raw})>0,AVERAGE({raw}),IF(ISNUMBER(L{r}),L{r},""))', NUMBER)
        output_cell(ws, f"Q{r}", f'=IF(COUNT({raw})>1,MAX({raw})-MIN({raw}),IF(ISNUMBER(M{r}),M{r},""))', NUMBER)
        output_cell(ws, f"R{r}", f'=IF(COUNT({raw})>1,_xlfn.STDEV.S({raw}),IF(ISNUMBER(N{r}),N{r},""))', NUMBER)
        output_cell(ws, f"S{r}", _flag(f"P{r}", *lim["xbar_r"]))
        output_cell(ws, f"T{r}", _flag(f"Q{r}", *lim["r"]))
        output_cell(ws, f"U{r}", _flag(f"P{r}", *lim["xbar_s"]))
        output_cell(ws, f"V{r}", _flag(f"R{r}", *lim["s"]))


def _individuals(ws: Worksheet) -> None:
    """Section 2: individuals and moving range."""
    first, last = FIRST_INDIVIDUAL, FIRST_INDIVIDUAL + INDIVIDUALS - 1
    section_title(ws, 82, "2. Individuals and moving range (I-MR): one value per time point (table from row 93)")
    result_row(ws, 83, "k = number of values", f'=IF(COUNT(B{first}:B{last})>0,COUNT(B{first}:B{last}),"")', "0")
    result_row(ws, 84, "X̄ = mean of the values", f'=IF(COUNT(B{first}:B{last})>0,AVERAGE(B{first}:B{last}),"")', NUMBER)
    result_row(ws, 85, "MR̄ = mean moving range", f'=IF(COUNT(C{first}:C{last})>0,AVERAGE(C{first}:C{last}),"")', NUMBER,
               "Dummies p. 249 (MR_i = |X_(i+1) − X_i|)")
    label(ws, 86, 1, "σ̂ = MR̄ / d2(n = 2)  (d2 in column C)")
    output_cell(ws, "C86", f"={lookup_formula('d2', '2')}", "0.000")
    output_cell(ws, "B86", '=IF(ISNUMBER(B85),B85/C86,"")', NUMBER)
    label(ws, 86, 4, "Dummies p. 116 (σ_ST = R̄/1.128)", italic=True)
    column_titles(ws, 88, ["Chart", "LCL", "CL", "UCL", "Constants", "value", "value", "Course source"])
    label(ws, 89, 1, "X chart: X̄ ± E2·MR̄")
    label(ws, 89, 5, "E2 (n = 2)")
    output_cell(ws, "F89", f"={lookup_formula('E2', '2')}", "0.000")
    output_cell(ws, "B89", '=IF(AND(ISNUMBER(B84),ISNUMBER(B85)),B84-F89*B85,"")', NUMBER)
    output_cell(ws, "C89", '=IF(ISNUMBER(B84),B84,"")', NUMBER)
    output_cell(ws, "D89", '=IF(AND(ISNUMBER(B84),ISNUMBER(B85)),B84+F89*B85,"")', NUMBER)
    label(ws, 90, 1, "MR chart: D3·MR̄ … D4·MR̄")
    label(ws, 90, 5, "D3, D4 (n = 2)")
    output_cell(ws, "F90", f"={lookup_formula('D3', '2')}", "0.000")
    output_cell(ws, "G90", f"={lookup_formula('D4', '2')}", "0.000")
    output_cell(ws, "B90", '=IF(ISNUMBER(B85),F90*B85,"")', NUMBER)
    output_cell(ws, "C90", '=IF(ISNUMBER(B85),B85,"")', NUMBER)
    output_cell(ws, "D90", '=IF(ISNUMBER(B85),G90*B85,"")', NUMBER)
    label(ws, 89, 8, "Dummies p. 249", italic=True)
    column_titles(ws, first - 1, ["#", "value x_i", "MR_i = |x_i − x_(i−1)|", "x vs X chart", "MR vs MR chart"])
    for index in range(INDIVIDUALS):
        r = first + index
        ws[f"A{r}"] = index + 1
        input_cell(ws, f"B{r}")
        mr = f'=IF(AND(ISNUMBER(B{r}),ISNUMBER(B{r - 1})),ABS(B{r}-B{r - 1}),"")' if index else '=""'
        output_cell(ws, f"C{r}", mr, NUMBER)
        output_cell(ws, f"D{r}", _flag(f"B{r}", "$B$89", "$D$89"))
        output_cell(ws, f"E{r}", _flag(f"C{r}", "$B$90", "$D$90"))


def _attribute_chart(ws: Worksheet, top: int, first: int, kind: str) -> None:
    """Sections 3-4: p chart (defectives) or u chart (defects), limits per subgroup."""
    last = first + ATTRIBUTE_ROWS - 1
    if kind == "p":
        section_title(ws, top, "3. p chart: fraction defective per subgroup (defectives: pass / fail data)")
        what, total_label, centre_label = "defectives d_i", "total defectives", "p̄ = total defectives / total inspected"
        spread = "SQRT({c}*(1-{c})/B{r})"
        source = "Dummies p. 254 (binomial)"
    else:
        section_title(ws, top, "4. u chart: defects per unit per subgroup (defects: count data)")
        what, total_label, centre_label = "defects c_i", "total defects", "ū = total defects / total units"
        spread = "SQRT({c}/B{r})"
        source = "Dummies p. 254 (Poisson)"
    have = f"COUNT(B{first}:B{last})>0"
    result_row(ws, top + 1, "total inspected (units)", f'=IF({have},SUM(B{first}:B{last}),"")', "0")
    result_row(ws, top + 2, total_label, f'=IF({have},SUM(C{first}:C{last}),"")', "0")
    result_row(ws, top + 3, centre_label, f'=IF(AND({have},B{top + 1}>0),B{top + 2}/B{top + 1},"")', NUMBER, source)
    label(ws, top + 4, 1, "Limits per subgroup: centre ± 3 · " + ("√(p̄(1 − p̄)/n_i)" if kind == "p" else "√(ū/n_i)")
          + "; a negative lower limit is 0.", italic=True)
    column_titles(ws, first - 1, ["#", "subgroup size n_i", what, "p_i" if kind == "p" else "u_i", "LCL_i", "UCL_i",
                                  "flag"])
    centre = f"$B${top + 3}"
    for index in range(ATTRIBUTE_ROWS):
        r = first + index
        ws[f"A{r}"] = index + 1
        input_cell(ws, f"B{r}")
        input_cell(ws, f"C{r}")
        ok = f"AND(ISNUMBER(B{r}),ISNUMBER(C{r}),B{r}>0,ISNUMBER({centre}))"
        half = "3*" + spread.format(c=centre, r=r)
        output_cell(ws, f"D{r}", f'=IF({ok},C{r}/B{r},"")', NUMBER)
        output_cell(ws, f"E{r}", f'=IF({ok},MAX(0,{centre}-{half}),"")', NUMBER)
        output_cell(ws, f"F{r}", f'=IF({ok},{centre}+{half},"")', NUMBER)
        output_cell(ws, f"G{r}", _flag(f"D{r}", f"E{r}", f"F{r}"))


def _rules(ws: Worksheet) -> None:
    """Section 5: how the course reads a control chart."""
    section_title(ws, 311, "5. Reading the chart: Western Electric rules (deck p. 68-69)")
    rules = (
        "1. One or more points outside the control limits (flagged in the tables above).",
        "2. Two of three consecutive points outside the two-sigma warning limits but still inside the control limits.",
        "3. Four of five consecutive points beyond the one-sigma limits.",
        "4. A run of eight consecutive points on one side of the centre line.",
        "More sensitizing rules, zones A/B/C and tampering vs. under-reacting: deck p. 65-70; Dummies p. 245-247.",
    )
    for offset, text in enumerate(rules):
        label(ws, 312 + offset, 1, text, italic=offset == 4)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the control-chart calculator."""
    write_header(ws, HEADER)
    _subgroups(ws)
    _individuals(ws)
    _attribute_chart(ws, 195, FIRST_P, "p")
    _attribute_chart(ws, 253, FIRST_U, "u")
    _rules(ws)
    size = DataValidation(type="whole", operator="between", formula1="2", formula2="25", allow_blank=True,
                          showErrorMessage=True, errorTitle="Subgroup size", error="n is a whole number, 2 to 25.")
    ws.add_data_validation(size)
    size.add(INPUTS["n_typed"])
    ws.column_dimensions["A"].width = 44
    for letter in "BCDEFGHIJKLMNOPQRSTUV":
        ws.column_dimensions[letter].width = 11
