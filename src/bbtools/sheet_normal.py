"""Normaal sheet (Normal): probabilities, values for a probability, μ ± kσ, and σ or μ from a tail fraction.

Course: Z = (X − μ)/σ and the 68-95-99.7 rule (deck p. 19); the Excel functions NORM.VERD (NORM.DIST),
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

SHEET = "Normaal"

HEADER = HeaderBlock(
    tool="Normale verdeling (normal distribution): kansen, waarden, μ ± kσ, σ of gemiddelde uit een staartfractie",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 16-19, 27; ___1.1 Ztable.pdf; "
           "___1.2 statistische functionaliteit in excel.pdf p. 1-3; __NormVerdeling Excel functies.xlsx",
    convention="De normale functies van Excel zoals de cursus ze gebruikt (NORM.DIST = NORM.VERD, NORM.INV); "
               "kansen zijn fracties, weergegeven als %.",
    status=Status.VERIFIED,
    status_detail="getest tegen de uitgewerkte cursusvoorbeelden (worked examples) S06-WE09 (werkmap NORM.INV / "
                  "NORM.VERD) en S06-WE10 (notities bij deck p. 19), de 68-95-99,7-regel (deck p. 19) en de Z-tabel "
                  "van de cursus",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="P(X < x), P(X > x), P(a < X < b); de waarde x bij een kans; μ ± kσ en het aandeel daarbinnen; "
            "σ (en variantie) of het gemiddelde uit een bekende staartfractie (tail fraction), bv. '2 op 40 onder 720 "
            "bij gemiddelde 820'.",
    inputs="gemiddelde μ en σ, dan per blok: x; a en b; een kans p; k; een grens L met de fractie f voorbij L.",
    audit="niet nodig (er zijn uitgewerkte cursusvoorbeelden)",
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
    section_title(ws, 8, "1. De verdeling")
    input_row(ws, 9, "Gemiddelde (mean) μ", "standaardnormale Z (zoals in de Z-tabel): μ = 0")
    input_row(ws, 10, "Standaardafwijking (standard deviation) σ", "standaardnormale Z: σ = 1")

    section_title(ws, 12, "2. Kans onder en boven een waarde x")
    input_row(ws, 13, "Waarde x")
    result_row(ws, 14, "z = (x − μ) / σ", f'=IF(AND({HAVE_DIST},ISNUMBER(B13)),(B13-{MU})/{SIGMA},"")', NUMBER,
               "deck p. 19; Excel NORMALISEREN (STANDARDIZE)")
    result_row(ws, 15, "P(X < x)", '=IF(ISNUMBER(B14),_xlfn.NORM.S.DIST(B14,TRUE),"")', PERCENT,
               "Excel NORM.VERD(x; μ; σ; WAAR) = NORM.DIST(..., TRUE); Z-tabel ___1.1 Ztable.pdf")
    result_row(ws, 16, "P(X > x)", '=IF(ISNUMBER(B14),_xlfn.NORM.S.DIST(-B14,TRUE),"")', PERCENT, "1 − P(X < x)")

    section_title(ws, 18, "3. Kans tussen twee waarden a < b")
    input_row(ws, 19, "Kleinste waarde a")
    input_row(ws, 20, "Grootste waarde b", "moet groter zijn dan a")
    ok = f"AND({HAVE_DIST},ISNUMBER(B19),ISNUMBER(B20),B20>B19)"
    between = f"_xlfn.NORM.DIST(B20,{MU},{SIGMA},TRUE)-_xlfn.NORM.DIST(B19,{MU},{SIGMA},TRUE)"
    result_row(ws, 21, "P(a < X < b)", f'=IF({ok},{between},"")', PERCENT)
    result_row(ws, 22, "P(X < a of X > b)", f'=IF({ok},_xlfn.NORM.DIST(B19,{MU},{SIGMA},TRUE)'
                                             f'+_xlfn.NORM.S.DIST(-(B20-{MU})/{SIGMA},TRUE),"")', PERCENT)


def _inverse(ws: Worksheet) -> None:
    """Section 4: the value belonging to a probability."""
    section_title(ws, 24, "4. Waarde x bij een kans p")
    input_row(ws, 25, "Kans p (als fractie: 0,01 = 1 %)", "tussen 0 en 1", "0.0000")
    ok = f"AND({HAVE_DIST},ISNUMBER(B25),B25>0,B25<1)"
    result_row(ws, 26, "x met P(X < x) = p  (ondergrens met p eronder)",
               f'=IF({ok},_xlfn.NORM.INV(B25,{MU},{SIGMA}),"")',
               NUMBER, "Excel NORM.INV(p; μ; σ)")
    result_row(ws, 27, "x met P(X > x) = p  (bovengrens met p erboven)",
               f'=IF({ok},_xlfn.NORM.INV(1-B25,{MU},{SIGMA}),"")',
               NUMBER, "bv. 1 % afkeur bovengrens: NORM.INV(0,99; 20; 0,5) (__NormVerdeling Excel functies.xlsx)")
    result_row(ws, 28, "Centraal interval (p over beide staarten): ondergrens",
               f'=IF({ok},_xlfn.NORM.INV(B25/2,{MU},{SIGMA}),"")', NUMBER, "bevat 1 − p van de waarden")
    result_row(ws, 29, "Centraal interval (p over beide staarten): bovengrens",
               f'=IF({ok},_xlfn.NORM.INV(1-B25/2,{MU},{SIGMA}),"")', NUMBER)
    validation = DataValidation(type="decimal", operator="between", formula1="0.0000000001", formula2="0.9999999999",
                                allow_blank=True, showErrorMessage=True, errorTitle="Kans",
                                error="Typ een fractie tussen 0 en 1, bv. 0,01 voor 1 %.")
    ws.add_data_validation(validation)
    validation.add("B25")
    validation.add("B45")


def _k_sigma(ws: Worksheet) -> None:
    """Sections 5-6: μ ± kσ and the 68-95-99.7 rule."""
    section_title(ws, 31, "5. μ ± kσ")
    input_row(ws, 32, "k (aantal standaardafwijkingen)", "bv. 3")
    ok = f"AND({HAVE_DIST},ISNUMBER(B32))"
    result_row(ws, 33, "μ − kσ", f'=IF({ok},{MU}-B32*{SIGMA},"")', NUMBER,
               "deck p. 19, notities: schoenmaten 42,5 − 3·2,5 = 35")
    result_row(ws, 34, "μ + kσ", f'=IF({ok},{MU}+B32*{SIGMA},"")', NUMBER, "42,5 + 3·2,5 = 50")
    result_row(ws, 35, "Fractie binnen μ ± kσ", '=IF(ISNUMBER(B32),1-2*_xlfn.NORM.S.DIST(-ABS(B32),TRUE),"")', PERCENT)
    result_row(ws, 36, "Fractie buiten μ ± kσ", '=IF(ISNUMBER(B32),2*_xlfn.NORM.S.DIST(-ABS(B32),TRUE),"")', PERCENT)

    section_title(ws, 38, "6. De 68 - 95 - 99,7-regel (deck p. 19)")
    for row, k, course in ((39, 1, "≈ 68 %"), (40, 2, "≈ 95 %"), (41, 3, "≈ 99,7 %")):
        constant_row(ws, row, f"binnen μ ± {k}σ", k, "")
        output_cell(ws, f"C{row}", f"=1-2*_xlfn.NORM.S.DIST(-B{row},TRUE)", PERCENT)
        label(ws, row, 4, f"deck p. 19: {course}", italic=True)


def _from_tail(ws: Worksheet) -> None:
    """Sections 7-8: σ (and variance) or μ from a limit and the fraction beyond it."""
    section_title(ws, 43, "7. σ uit een staartfractie (tail fraction), gemiddelde bekend (bv. '2 op 40 onder 720, "
                          "gemiddelde 820')")
    input_row(ws, 44, "Grens L", "gebruikt het gemiddelde μ uit blok 1")
    input_row(ws, 45, "Fractie f voorbij L (als fractie: 2/40 = 0,05)", "", "0.0000")
    have = f"AND(ISNUMBER({MU}),ISNUMBER(B44),ISNUMBER(B45),B45>0,B45<1,B45<>0.5)"
    below = f"(B44-{MU})/_xlfn.NORM.S.INV(B45)"
    above = f"(B44-{MU})/_xlfn.NORM.S.INV(1-B45)"
    result_row(ws, 46, "σ als f ONDER L ligt", f'=IF({have},IF({below}>0,{below},"niet mogelijk: L ligt aan de andere kant"),"")',
               NUMBER, "(L − μ) / NORM.S.INV(f)")
    result_row(ws, 47, "σ als f BOVEN L ligt", f'=IF({have},IF({above}>0,{above},"niet mogelijk: L ligt aan de andere kant"),"")',
               NUMBER, "(L − μ) / NORM.S.INV(1 − f)")
    result_row(ws, 48, "Variantie σ² (f onder L)", '=IF(ISNUMBER(B46),B46^2,"")', NUMBER)
    result_row(ws, 49, "Variantie σ² (f boven L)", '=IF(ISNUMBER(B47),B47^2,"")', NUMBER)

    section_title(ws, 51, "8. Gemiddelde uit een staartfractie, σ bekend (gebruikt σ uit blok 1, L en f uit blok 7)")
    have = f"AND(ISNUMBER({SIGMA}),ISNUMBER(B44),ISNUMBER(B45),B45>0,B45<1)"
    result_row(ws, 52, "μ als f ONDER L ligt", f'=IF({have},B44-{SIGMA}*_xlfn.NORM.S.INV(B45),"")', NUMBER,
               "L − σ · NORM.S.INV(f)")
    result_row(ws, 53, "μ als f BOVEN L ligt", f'=IF({have},B44-{SIGMA}*_xlfn.NORM.S.INV(1-B45),"")', NUMBER,
               "L − σ · NORM.S.INV(1 − f)")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the normal-distribution calculator."""
    write_header(ws, HEADER)
    _probabilities(ws)
    _inverse(ws)
    _k_sigma(ws)
    _from_tail(ws)
    positive = DataValidation(type="decimal", operator="greaterThan", formula1="0", allow_blank=True,
                              showErrorMessage=True, errorTitle="σ", error="σ moet groter zijn dan 0.")
    ws.add_data_validation(positive)
    positive.add(SIGMA)
    ws.column_dimensions["A"].width = 58
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 20
