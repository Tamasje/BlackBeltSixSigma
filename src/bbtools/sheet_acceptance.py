"""Acceptance sampling sheet: OC curve of a single-stage attribute plan (n, c), producer's and consumer's risk,
AOQ, AOQL and ATI (rectifying inspection), and the single-stage variables plan (k, n) from AQL and LQL.

Course (Ottoy, Les 2, Acceptance Sampling - Further Reading.pdf): OC(p) = P(X ≤ c | p) = H(c; N, M_p, n) with
M_p = [Np] (p. 4); binomial when N is large compared to n (p. 4; Testing of Hypotheses.pdf p. 5-8); AQL: OC = 1 − α,
LQL: OC = β, normally α = 5 %, β = 10 % (p. 4, decision 12); AOQ(p) = p·OC(p)·(1 − (n/N)·Rs*) with
Rs* = H(c − 1; N − 1, [Np] − 1, n − 1) / H(c; N, [Np], n), AOQL = max AOQ, ATI(p) = n·OC(p) + N·(1 − OC(p)) (p. 10);
variables plan k = (z_pt z_α + z_p0 z_β)/(z_{1−α} + z_{1−β}), n = (z_{1−α} + z_{1−β})² (1 + k²/2)/(z_pt − z_p0)² and
OC(p) ≈ 1 − Φ((z_p + k)√n / √(1 + k²/2)) (p. 9), z_q = the q-quantile of N(0, 1).
The Peach table for designing (n, c) ("tabellen AS.pdf", p. 4) is not in the course files, so plans are checked,
not designed. Row plan: inputs 8-16; risks 18-24; one p 26-32; variables plan 34-45; OC table 47-89.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    column_titles,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "Acceptance sampling"

HEADER = HeaderBlock(
    tool="Acceptance sampling: OC curve of a plan (n, c), producer's / consumer's risk, AOQ, AOQL, ATI, variables plan",
    source="source/course/Les 2/20260529_ottoy_Acceptance Sampling - Further Reading.pdf p. 2-10; "
           "Acceptance Sampling.pdf p. 23-27; Testing of Hypotheses.pdf p. 5-11; Testing of Hypotheses.xlsx",
    convention="Decision 12: α and β inputs prefilled 5 % and 10 % (p. 4; its worked examples use β = 5 %); "
               "hypergeometric OC with M = [Np] when N is given, binomial always shown.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S03-WE06, S03-WE07, S03-WE20, S03-WE21, S04-WE12, "
                  "S04-WE16, S04-WE18",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Acceptance probability OC(p) of a single-stage plan (n, c), α at AQL and β at LQL, AOQ, AOQL and ATI for "
            "rectifying inspection, an OC/AOQ/ATI table, and the variables plan (k, n) from AQL and LQL.",
    inputs="n, c, lot size N (optional: exact hypergeometric OC, AOQ, ATI), AQL, LQL, α, β, a fraction p, the table step.",
    audit="not needed (course worked examples exist)",
    disagreements=(
        "Further Reading p. 4 designs (n, c) with the table of Peach ('tabellen AS.pdf'), which is not in the course "
        "files; the sheet checks a plan instead. Its example plan (164, 2) for (0.5 %, 95 %) and (3.5 %, 5 %) has "
        "OC(0.5 %) = 95 % but OC(3.5 %) = 7.1 % (binomial): Peach's method is approximate, as the page says.",
        "Further Reading p. 10: 'AOQL approximately 1.3 %, at about 1.8 %' for (250, 5), N = 1000 matches the "
        "approximation p·OC(p) (1.30 % at 1.7 %), not the exact formula on the same slide (1.03 % at 1.7 %), although "
        "n/N = 0.25 is not small.",
    ),
)

INPUTS = {"n": "B9", "c": "B10", "N": "B11", "aql": "B12", "lql": "B13", "alpha": "B14", "beta": "B15", "p": "B27",
          "step": "B48"}
RESULTS = {
    "oc_binom_aql": "B20", "oc_hyp_aql": "C20", "alpha_binom": "B21", "alpha_hyp": "C21",
    "beta_binom": "B22", "beta_hyp": "C22",
    "meets_binom": "B24", "meets_hyp": "C24",
    "oc_binom_p": "B28", "oc_hyp_p": "B29", "aoq_p": "B30", "aoq_approx_p": "B31", "ati_p": "B32",
    "k": "B38", "n_formula": "B39", "n_up": "B40", "oc_var_aql": "B41", "oc_var_lql": "B42",
    "aoql": "B45", "p_at_aoql": "C45", "aoql_approx": "B46", "p_at_aoql_approx": "C46",
}
TABLE_FIRST, TABLE_ROWS = 50, 40
PERCENT = "0.0000%"
HAVE_PLAN = "AND(ISNUMBER($B$9),ISNUMBER($B$10),$B$9>0,$B$10>=0)"
HAVE_LOT = "AND(ISNUMBER($B$11),$B$11>=$B$9)"


def _oc_binomial(p: str) -> str:
    """Binomial OC(p) = P(X ≤ c) for the plan in B9 (n) and B10 (c)."""
    return f"_xlfn.BINOM.DIST($B$10,$B$9,{p},TRUE)"


def _oc_hypergeometric(p: str) -> str:
    """Hypergeometric OC(p) = H(c; N, [Np], n) (Further Reading p. 4)."""
    return f"_xlfn.HYPGEOM.DIST($B$10,$B$9,INT({p}*$B$11),$B$11,TRUE)"


def _aoq(p: str, oc: str) -> str:
    """AOQ(p) = p·OC(p)·(1 − (n/N)·Rs*) with Rs* as on Further Reading p. 10 (0 when no defective can be found)."""
    rs = (f"IF(OR($B$10=0,INT({p}*$B$11)=0),0,_xlfn.HYPGEOM.DIST($B$10-1,$B$9-1,INT({p}*$B$11)-1,$B$11-1,TRUE)"
          f"/{oc})")
    return f"IF({oc}=0,0,{p}*{oc}*(1-($B$9/$B$11)*{rs}))"


def _inputs(ws: Worksheet) -> None:
    """Section 1: the plan and the quality levels."""
    section_title(ws, 8, "1. The plan (n, c) and the quality levels (fractions: 0.02 = 2 %)")
    input_row(ws, 9, "n = sample size")
    input_row(ws, 10, "c = acceptance number (accept if defectives ≤ c)")
    input_row(ws, 11, "N = lot size (optional: exact hypergeometric OC, AOQ, ATI)")
    input_row(ws, 12, "AQL (acceptable quality level)", "should normally pass", "0.0000")
    input_row(ws, 13, "LQL = LTPD (limiting quality level)", "should normally be rejected", "0.0000")
    input_row(ws, 14, "α = producer's risk target", "p. 4: normally 5 %", "0.00")
    input_row(ws, 15, "β = consumer's risk target", "p. 4: normally 10 %; its examples use 5 %", "0.00")
    ws["B14"], ws["B15"] = 0.05, 0.10
    label(ws, 16, 1, "Producer's risk: rejecting a good lot (type I). Consumer's risk: accepting a bad lot (type II). "
                     "Further Reading p. 2.", italic=True)


def _risks(ws: Worksheet) -> None:
    """Section 2: OC at AQL and LQL, and the risks."""
    section_title(ws, 18, "2. Risks of the plan")
    column_titles(ws, 19, ["", "binomial", "hypergeometric (needs N)", "Course source"])
    rows = (
        (20, "OC(AQL) = P(accept a lot at AQL)", "$B$12", False),
        (21, "Producer's risk α = 1 − OC(AQL)", "$B$12", True),
        (22, "Consumer's risk β = OC(LQL) = P(accept a lot at LQL)", "$B$13", False),
    )
    for row, text, level, complement in rows:
        label(ws, row, 1, text)
        for column, oc, extra in (("B", _oc_binomial(level), ""), ("C", _oc_hypergeometric(level), f",{HAVE_LOT}")):
            value = f"1-{oc}" if complement else oc
            output_cell(ws, f"{column}{row}", f'=IF(AND({HAVE_PLAN},ISNUMBER({level}){extra}),{value},"")', PERCENT)
    label(ws, 20, 4, "Further Reading p. 4; Testing of Hypotheses.pdf p. 5", italic=True)
    label(ws, 24, 1, "Meets both targets (α ≤ target and β ≤ target)?")
    for column in "BC":
        output_cell(ws, f"{column}24", f'=IF(AND(ISNUMBER({column}21),ISNUMBER({column}22)),IF(AND({column}21<=$B$14,'
                                       f'{column}22<=$B$15),"yes","no"),"")')


def _one_p(ws: Worksheet) -> None:
    """Section 3: OC, AOQ and ATI at one fraction defective."""
    section_title(ws, 26, "3. One lot quality p: acceptance, outgoing quality, inspection effort")
    input_row(ws, 27, "p = fraction defective of the lot", "", "0.0000")
    have = f"AND({HAVE_PLAN},ISNUMBER($B$27))"
    lot = f"AND({have},{HAVE_LOT})"
    result_row(ws, 28, "OC(p), binomial", f'=IF({have},{_oc_binomial("$B$27")},"")', PERCENT)
    result_row(ws, 29, "OC(p), hypergeometric", f'=IF({lot},{_oc_hypergeometric("$B$27")},"")', PERCENT, "p. 4")
    result_row(ws, 30, "AOQ(p) = p·OC(p)·(1 − (n/N)·Rs*)", f'=IF({lot},{_aoq("$B$27", "B29")},"")', PERCENT, "p. 10")
    result_row(ws, 31, "AOQ(p) ≈ p·OC(p) (n << N; hypergeometric OC if N is given)",
               f'=IF({have},$B$27*IF(ISNUMBER(B29),B29,B28),"")', PERCENT, "p. 10")
    result_row(ws, 32, "ATI(p) = n·OC(p) + N·(1 − OC(p))", f'=IF({lot},$B$9*B29+$B$11*(1-B29),"")', "0.0", "p. 10")


def _variables(ws: Worksheet) -> None:
    """Section 4: single-stage variables plan from AQL (p0) and LQL (pt), with α and β of section 1."""
    section_title(ws, 34, "4. Variables plan (normal measurements): accept if (x̄ − limit) / s ≥ k   (p. 9)")
    label(ws, 35, 1, "Uses AQL = p0, LQL = pt, α and β from section 1.", italic=True)
    z = "_xlfn.NORM.S.INV"
    have = "AND(ISNUMBER($B$12),ISNUMBER($B$13),ISNUMBER($B$14),ISNUMBER($B$15),$B$13>$B$12)"
    k = (f"({z}($B$13)*{z}($B$14)+{z}($B$12)*{z}($B$15))/({z}(1-$B$14)+{z}(1-$B$15))")
    result_row(ws, 38, "k = (z_pt z_α + z_p0 z_β) / (z_(1−α) + z_(1−β))", f'=IF({have},{k},"")', "0.0000",
               "Further Reading p. 9 (z_q = q-quantile of N(0,1))")
    result_row(ws, 39, "n = (z_(1−α) + z_(1−β))² (1 + k²/2) / (z_pt − z_p0)²",
               f'=IF(ISNUMBER(B38),({z}(1-$B$14)+{z}(1-$B$15))^2*(1+B38^2/2)/({z}($B$13)-{z}($B$12))^2,"")', "0.00")
    result_row(ws, 40, "n rounded up", '=IF(ISNUMBER(B39),ROUNDUP(B39,0),"")', "0", "p. 9 example: 63.2 -> 64")
    oc = "1-_xlfn.NORM.S.DIST(({z}({p})+B38)*SQRT(B40)/SQRT(1+B38^2/2),TRUE)"
    result_row(ws, 41, "OC(AQL) of this plan", f'=IF(ISNUMBER(B40),{oc.format(z=z, p="$B$12")},"")', PERCENT, "p. 9")
    result_row(ws, 42, "OC(LQL) of this plan", f'=IF(ISNUMBER(B40),{oc.format(z=z, p="$B$13")},"")', PERCENT)


def _table(ws: Worksheet) -> None:
    """Section 5: OC, AOQ and ATI over a grid of p, and the AOQL."""
    section_title(ws, 44, "5. OC curve, AOQ and ATI over a range of p (AOQL = the largest AOQ in the table)")
    first, last = TABLE_FIRST, TABLE_FIRST + TABLE_ROWS
    for row, text, column in ((45, "AOQL with the exact formula (column E) and the p where it occurs", "E"),
                              (46, "AOQL with the approximation p·OC(p) (column D) and its p", "D")):
        label(ws, row, 1, text)
        output_cell(ws, f"B{row}", f'=IF(COUNT({column}{first}:{column}{last})>0,MAX({column}{first}:{column}{last}),"")',
                    PERCENT)
        output_cell(ws, f"C{row}", f'=IF(ISNUMBER(B{row}),INDEX(A{first}:A{last},MATCH(B{row},{column}{first}:'
                                   f'{column}{last},0)),"")', PERCENT)
    label(ws, 45, 4, "exact only to the table step", italic=True)
    label(ws, 46, 4, "p. 10 example (250, 5), N = 1000: 'AOQL ≈ 1.3 % at p ≈ 1.8 %' is this approximation", italic=True)
    input_row(ws, 48, "Table step of p", "Testing of Hypotheses.xlsx uses 0.005 (p from 0 to 0.2)", "0.0000")
    ws["B48"] = 0.005
    column_titles(ws, first - 1, ["p", "OC binomial", "OC hypergeometric", "AOQ ≈ p·OC(p)", "AOQ (exact, p. 10)",
                                  "ATI"])
    for i in range(TABLE_ROWS + 1):
        r = first + i
        output_cell(ws, f"A{r}", f'=IF(ISNUMBER($B$48),{i}*$B$48,"")', PERCENT)
        have = f"AND({HAVE_PLAN},ISNUMBER(A{r}),A{r}<=1)"
        lot = f"AND({have},{HAVE_LOT})"
        output_cell(ws, f"B{r}", f'=IF({have},{_oc_binomial(f"A{r}")},"")', PERCENT)
        output_cell(ws, f"C{r}", f'=IF({lot},{_oc_hypergeometric(f"A{r}")},"")', PERCENT)
        output_cell(ws, f"D{r}", f'=IF(ISNUMBER(C{r}),A{r}*C{r},IF(ISNUMBER(B{r}),A{r}*B{r},""))', PERCENT)
        output_cell(ws, f"E{r}", f'=IF(ISNUMBER(C{r}),{_aoq(f"A{r}", f"C{r}")},"")', PERCENT)
        output_cell(ws, f"F{r}", f'=IF(ISNUMBER(C{r}),$B$9*C{r}+$B$11*(1-C{r}),"")', "0.0")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the acceptance-sampling calculator."""
    write_header(ws, HEADER)
    _inputs(ws)
    _risks(ws)
    _one_p(ws)
    _variables(ws)
    _table(ws)
    label(ws, 92, 1, "Not calculated here: double, sequential (SPRT) and skip-lot plans (Further Reading p. 5-11), "
                     "ISO 2859 / 3951 look-up (p. 12). Designing (n, c) needs the Peach table 'tabellen AS.pdf' (p. 4), "
                     "which is not in the course files.", italic=True)
    whole = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                           showErrorMessage=True, errorTitle="Whole number", error="Type a whole number.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Fraction", error="Type a fraction between 0 and 1.")
    ws.add_data_validation(whole)
    ws.add_data_validation(fraction)
    for coordinate in ("B9", "B10", "B11"):
        whole.add(coordinate)
    for coordinate in ("B12", "B13", "B14", "B15", "B27", "B48"):
        fraction.add(coordinate)
    ws.column_dimensions["A"].width = 58
    for letter in "BCDEF":
        ws.column_dimensions[letter].width = 18
