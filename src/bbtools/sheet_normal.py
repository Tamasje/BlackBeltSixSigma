"""Normal sheet: probabilities, values for a probability, μ ± kσ, and σ or μ from a tail fraction.

Course: Z = (X − μ)/σ and the 68-95-99.7 rule (deck p. 18); the Excel functions NORM.VERD (NORM.DIST),
NORM.INV and NORMALISEREN (___1.2 statistische functionaliteit in excel.pdf p. 1-3; __NormVerdeling Excel
functies.xlsx); Z table (___1.1 Ztable.pdf). Probabilities are fractions (0.05 = 5 %), displayed as %.
Upper tails use NORM.S.DIST(−z) rather than 1 − NORM.S.DIST(z): same value, no lost digits far out.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    constant_row,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "Normal"

HEADER = HeaderBlock(
    tool="Normal distribution: probabilities, values, μ ± kσ, σ or mean from a tail fraction",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 16-19, 26; ___1.1 Ztable.pdf; "
           "___1.2 statistische functionaliteit in excel.pdf p. 1-3; __NormVerdeling Excel functies.xlsx",
    convention="Excel's normal functions as the course uses them (NORM.DIST = NORM.VERD, NORM.INV); "
               "probabilities are fractions shown as %.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S06-WE09 (NORM.INV / NORM.VERD workbook) and S06-WE10 "
                  "(deck p. 19 notes), the 68-95-99.7 rule (deck p. 18) and the course Z table",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="P(X < x), P(X > x), P(a < X < b); the value x for a probability; μ ± kσ and its coverage; "
            "σ (and variance) or the mean from a known tail fraction, e.g. '2 in 40 below 720 with mean 820'.",
    inputs="mean μ and σ, then per block: x; a and b; a probability p; k; a limit L with the fraction f beyond it.",
    audit="not needed (course worked examples exist)",
    disagreements=(),
)

MU, SIGMA = "B9", "B10"
INPUTS = {"mu": MU, "sigma": SIGMA, "x": "B13", "a": "B19", "b": "B20", "p": "B25", "k": "B32",
          "limit": "B44", "fraction": "B45"}
RESULTS = {
    "z": "B14", "below_x": "B15", "above_x": "B16", "between": "B21", "outside": "B22",
    "x_lower_tail": "B26", "x_upper_tail": "B27", "central_low": "B28", "central_high": "B29",
    "mu_minus_k": "B33", "mu_plus_k": "B34", "inside_k": "B35", "outside_k": "B36",
    "rule_1": "C39", "rule_2": "C40", "rule_3": "C41",
    "sigma_if_below": "B46", "sigma_if_above": "B47", "var_if_below": "B48", "var_if_above": "B49",
    "mu_if_below": "B52", "mu_if_above": "B53",
}
PERCENT = "0.0000%"
NUMBER = "0.0000"
HAVE_DIST = f"ISNUMBER({MU}),ISNUMBER({SIGMA})"


def _probabilities(ws: Worksheet) -> None:
    """Sections 1-3: the distribution and probabilities for values."""
    section_title(ws, 8, "1. The distribution")
    input_row(ws, 9, "Mean μ", "standard normal Z (as in the Z table): μ = 0")
    input_row(ws, 10, "Standard deviation σ", "standard normal Z: σ = 1")

    section_title(ws, 12, "2. Probability below and above a value x")
    input_row(ws, 13, "Value x")
    result_row(ws, 14, "z = (x − μ) / σ", f'=IF(AND({HAVE_DIST},ISNUMBER(B13)),(B13-{MU})/{SIGMA},"")', NUMBER,
               "deck p. 18; Excel NORMALISEREN (STANDARDIZE)")
    result_row(ws, 15, "P(X < x)", '=IF(ISNUMBER(B14),_xlfn.NORM.S.DIST(B14,TRUE),"")', PERCENT,
               "Excel NORM.VERD(x; μ; σ; WAAR) = NORM.DIST(..., TRUE); Z table ___1.1 Ztable.pdf")
    result_row(ws, 16, "P(X > x)", '=IF(ISNUMBER(B14),_xlfn.NORM.S.DIST(-B14,TRUE),"")', PERCENT, "1 − P(X < x)")

    section_title(ws, 18, "3. Probability between two values a < b")
    input_row(ws, 19, "Lower value a")
    input_row(ws, 20, "Upper value b", "must be above a")
    ok = f"AND({HAVE_DIST},ISNUMBER(B19),ISNUMBER(B20),B20>B19)"
    between = f"_xlfn.NORM.DIST(B20,{MU},{SIGMA},TRUE)-_xlfn.NORM.DIST(B19,{MU},{SIGMA},TRUE)"
    result_row(ws, 21, "P(a < X < b)", f'=IF({ok},{between},"")', PERCENT)
    result_row(ws, 22, "P(X < a or X > b)", f'=IF({ok},_xlfn.NORM.DIST(B19,{MU},{SIGMA},TRUE)'
                                             f'+_xlfn.NORM.S.DIST(-(B20-{MU})/{SIGMA},TRUE),"")', PERCENT)


def _inverse(ws: Worksheet) -> None:
    """Section 4: the value belonging to a probability."""
    section_title(ws, 24, "4. Value x for a probability p")
    input_row(ws, 25, "Probability p (as a fraction: 0.01 = 1 %)", "between 0 and 1", "0.0000")
    ok = f"AND({HAVE_DIST},ISNUMBER(B25),B25>0,B25<1)"
    result_row(ws, 26, "x with P(X < x) = p  (lower limit for p below it)", f'=IF({ok},_xlfn.NORM.INV(B25,{MU},{SIGMA}),"")',
               NUMBER, "Excel NORM.INV(p; μ; σ)")
    result_row(ws, 27, "x with P(X > x) = p  (upper limit for p above it)", f'=IF({ok},_xlfn.NORM.INV(1-B25,{MU},{SIGMA}),"")',
               NUMBER, "e.g. 1 % afkeur bovengrens: NORM.INV(0,99; 20; 0,5) (__NormVerdeling Excel functies.xlsx)")
    result_row(ws, 28, "Central interval with p split over both tails: lower end",
               f'=IF({ok},_xlfn.NORM.INV(B25/2,{MU},{SIGMA}),"")', NUMBER, "holds 1 − p of the values")
    result_row(ws, 29, "Central interval with p split over both tails: upper end",
               f'=IF({ok},_xlfn.NORM.INV(1-B25/2,{MU},{SIGMA}),"")', NUMBER)
    validation = DataValidation(type="decimal", operator="between", formula1="0.0000000001", formula2="0.9999999999",
                                allow_blank=True, showErrorMessage=True, errorTitle="Probability",
                                error="Type a fraction between 0 and 1, e.g. 0.01 for 1 %.")
    ws.add_data_validation(validation)
    validation.add("B25")
    validation.add("B45")


def _k_sigma(ws: Worksheet) -> None:
    """Sections 5-6: μ ± kσ and the 68-95-99.7 rule."""
    section_title(ws, 31, "5. μ ± kσ")
    input_row(ws, 32, "k (number of standard deviations)", "e.g. 3")
    ok = f"AND({HAVE_DIST},ISNUMBER(B32))"
    result_row(ws, 33, "μ − kσ", f'=IF({ok},{MU}-B32*{SIGMA},"")', NUMBER,
               "deck p. 19 notes: shoe sizes 42,5 − 3·2,5 = 35")
    result_row(ws, 34, "μ + kσ", f'=IF({ok},{MU}+B32*{SIGMA},"")', NUMBER, "42,5 + 3·2,5 = 50")
    result_row(ws, 35, "Fraction inside μ ± kσ", '=IF(ISNUMBER(B32),1-2*_xlfn.NORM.S.DIST(-ABS(B32),TRUE),"")', PERCENT)
    result_row(ws, 36, "Fraction outside μ ± kσ", '=IF(ISNUMBER(B32),2*_xlfn.NORM.S.DIST(-ABS(B32),TRUE),"")', PERCENT)

    section_title(ws, 38, "6. The 68 - 95 - 99.7 rule (deck p. 18)")
    for row, k, course in ((39, 1, "≈ 68 %"), (40, 2, "≈ 95 %"), (41, 3, "≈ 99.7 %")):
        constant_row(ws, row, f"within μ ± {k}σ", k, "")
        output_cell(ws, f"C{row}", f"=1-2*_xlfn.NORM.S.DIST(-B{row},TRUE)", PERCENT)
        label(ws, row, 4, f"deck p. 18: {course}", italic=True)


def _from_tail(ws: Worksheet) -> None:
    """Sections 7-8: σ (and variance) or μ from a limit and the fraction beyond it."""
    section_title(ws, 43, "7. σ from a tail fraction, mean known (e.g. '2 in 40 below 720, mean 820')")
    input_row(ws, 44, "Limit L", "uses the mean μ from section 1")
    input_row(ws, 45, "Fraction f beyond L (as a fraction: 2/40 = 0.05)", "", "0.0000")
    have = f"AND(ISNUMBER({MU}),ISNUMBER(B44),ISNUMBER(B45),B45>0,B45<1,B45<>0.5)"
    below = f"(B44-{MU})/_xlfn.NORM.S.INV(B45)"
    above = f"(B44-{MU})/_xlfn.NORM.S.INV(1-B45)"
    result_row(ws, 46, "σ if f lies BELOW L", f'=IF({have},IF({below}>0,{below},"not possible: L is on the other side"),"")',
               NUMBER, "(L − μ) / NORM.S.INV(f)")
    result_row(ws, 47, "σ if f lies ABOVE L", f'=IF({have},IF({above}>0,{above},"not possible: L is on the other side"),"")',
               NUMBER, "(L − μ) / NORM.S.INV(1 − f)")
    result_row(ws, 48, "Variance σ² (f below L)", '=IF(ISNUMBER(B46),B46^2,"")', NUMBER)
    result_row(ws, 49, "Variance σ² (f above L)", '=IF(ISNUMBER(B47),B47^2,"")', NUMBER)

    section_title(ws, 51, "8. Mean from a tail fraction, σ known (uses σ from section 1, L and f from section 7)")
    have = f"AND(ISNUMBER({SIGMA}),ISNUMBER(B44),ISNUMBER(B45),B45>0,B45<1)"
    result_row(ws, 52, "μ if f lies BELOW L", f'=IF({have},B44-{SIGMA}*_xlfn.NORM.S.INV(B45),"")', NUMBER,
               "L − σ · NORM.S.INV(f)")
    result_row(ws, 53, "μ if f lies ABOVE L", f'=IF({have},B44-{SIGMA}*_xlfn.NORM.S.INV(1-B45),"")', NUMBER,
               "L − σ · NORM.S.INV(1 − f)")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the normal-distribution calculator."""
    write_header(ws, HEADER)
    _probabilities(ws)
    _inverse(ws)
    _k_sigma(ws)
    _from_tail(ws)
    positive = DataValidation(type="decimal", operator="greaterThan", formula1="0", allow_blank=True,
                              showErrorMessage=True, errorTitle="σ", error="σ must be greater than 0.")
    ws.add_data_validation(positive)
    positive.add(SIGMA)
    ws.column_dimensions["A"].width = 58
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 20
