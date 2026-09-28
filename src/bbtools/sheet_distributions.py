"""Distributions sheet: E[X], Var[X] and probabilities for Bernoulli, binomial, hypergeometric, Poisson,
exponential and uniform distributions (the families of exam Q6).

Course: binomial defectives in a lot P[i] = C(N,i) π^i (1−π)^(N−i) with E[i] = Nπ (Acceptance Sampling.pdf
p. 12); hypergeometric sampling distribution of defectives in a sample (p. 16; Testing of Hypotheses.xlsx
'OC-curve (hypergeometric)'); Poisson for counts, exponential for waiting times (Naert Les 1 p. 7-9);
uniform and exponential densities (Acceptance Sampling.xlsm 'distributions'). Excel functions as the course's
workbooks use them: BINOM.DIST, HYPGEOM.DIST, POISSON.DIST, EXPON.DIST.
Only the binomial and hypergeometric blocks have course worked examples; the others are marked as such.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import HeaderBlock, Status, font, input_row, result_row, section_title, write_header

SHEET = "Distributions"
NO_EXAMPLE = "no course worked example for this block (checked by the stats-auditor, build/README.md)"

HEADER = HeaderBlock(
    tool="Distributions: E[X], Var[X] and probabilities (Bernoulli, binomial, hypergeometric, Poisson, exponential, uniform)",
    source="source/course/Les 2/20260529_ottoy_Acceptance Sampling.pdf p. 12, 16, 20; Acceptance Sampling.xlsm; "
           "Testing of Hypotheses.xlsx; Les 1/20260522_naert_big data.pdf p. 5-10",
    convention="Excel's distribution functions as used in the course workbooks; k counts are whole numbers; "
               "P(X ≥ k) = 1 − P(X ≤ k − 1).",
    status=Status.VERIFIED,
    status_detail="binomial and hypergeometric blocks tested against course worked examples S04-WE02, S03-WE19, "
                  "S03-WE21; Bernoulli, Poisson, exponential and uniform blocks have no course example (audited)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Mean, variance and point / cumulative probabilities of the distribution families of the course and of "
            "exam Q6 (Bernoulli, binomial, hypergeometric, Poisson, exponential, uniform).",
    inputs="per block: p; n, p, k; N, D, n, k; λ, k; rate, t; a, b, x.",
    audit="stats-auditor PASS (2026-09-28) for the Bernoulli, Poisson, exponential and uniform blocks: all 14 values "
          "for one input agree with an independent computation. But the cited pages print no general formula for "
          "these four families (Naert Les 1 p. 7-9 only names Poisson for counts and exponential for waiting "
          "times; Acceptance Sampling.xlsm 'distributions' evaluates EXPON.DIST with a rate and a uniform density "
          "on [1, 2]); the sheet uses the standard definitions. Open question for the user.",
    disagreements=(),
)

INPUTS = {
    "bern_p": "B9",
    "bin_n": "B14", "bin_p": "B15", "bin_k": "B16",
    "hyp_N": "B25", "hyp_D": "B26", "hyp_n": "B27", "hyp_k": "B28",
    "poi_lambda": "B36", "poi_k": "B37",
    "exp_rate": "B45", "exp_t": "B46",
    "uni_a": "B53", "uni_b": "B54", "uni_x": "B55",
}
RESULTS = {
    "bern_mean": "B10", "bern_var": "B11",
    "bin_mean": "B17", "bin_var": "B18", "bin_sd": "B19", "bin_pk": "B20", "bin_le": "B21", "bin_ge": "B22",
    "hyp_mean": "B29", "hyp_var": "B30", "hyp_pk": "B31", "hyp_le": "B32", "hyp_ge": "B33",
    "poi_mean": "B38", "poi_var": "B39", "poi_pk": "B40", "poi_le": "B41", "poi_ge": "B42",
    "exp_mean": "B47", "exp_var": "B48", "exp_le": "B49", "exp_gt": "B50",
    "uni_mean": "B56", "uni_var": "B57", "uni_le": "B58",
}
NUMBER = "0.000000"
PROBABILITY = "0.000000%"


def _note(ws: Worksheet, row: int) -> None:
    """Red note next to a section title: this block has no course worked example."""
    ws.cell(row=row, column=4, value=NO_EXAMPLE).font = font(italic=True, color="C00000")


def _bernoulli_binomial(ws: Worksheet) -> None:
    """Sections 1-2."""
    section_title(ws, 8, "1. Bernoulli: one item, X = 1 (e.g. non-conform) with probability p")
    _note(ws, 8)
    input_row(ws, 9, "p = P(X = 1) (fraction)", "e.g. 2 in 40 -> 0.05", "0.0000")
    ok = "AND(ISNUMBER(B9),B9>=0,B9<=1)"
    result_row(ws, 10, "E[X] = p", f'=IF({ok},B9,"")', NUMBER)
    result_row(ws, 11, "Var[X] = p (1 − p)", f'=IF({ok},B9*(1-B9),"")', NUMBER)

    section_title(ws, 13, "2. Binomial: number of successes (e.g. defectives) in n independent trials")
    input_row(ws, 14, "n = number of trials (items)")
    input_row(ws, 15, "p = probability per trial (fraction)", "", "0.000000")
    input_row(ws, 16, "k (for the probabilities)")
    ok = "AND(ISNUMBER(B14),ISNUMBER(B15),B15>=0,B15<=1)"
    okk = f"AND({ok},ISNUMBER(B16))"
    result_row(ws, 17, "E[X] = n p", f'=IF({ok},B14*B15,"")', NUMBER, "Acceptance Sampling.pdf p. 12 (E[i] = Nπ)")
    result_row(ws, 18, "Var[X] = n p (1 − p)", f'=IF({ok},B14*B15*(1-B15),"")', NUMBER)
    result_row(ws, 19, "σ = √Var[X]", '=IF(ISNUMBER(B18),SQRT(B18),"")', NUMBER)
    result_row(ws, 20, "P(X = k)", f'=IF({okk},_xlfn.BINOM.DIST(B16,B14,B15,FALSE),"")', PROBABILITY,
               "P[i] = C(n,i) p^i (1 − p)^(n − i) (p. 12); Excel BINOM.DIST(k; n; p; ONWAAR)")
    result_row(ws, 21, "P(X ≤ k)", f'=IF({okk},_xlfn.BINOM.DIST(B16,B14,B15,TRUE),"")', PROBABILITY,
               "OC-curve P[d ≤ c] (Confidence Intervals.xlsx, Testing of Hypotheses.xlsx)")
    result_row(ws, 22, "P(X ≥ k)", f'=IF({okk},IF(B16<=0,1,1-_xlfn.BINOM.DIST(B16-1,B14,B15,TRUE)),"")', PROBABILITY)


def _hypergeometric(ws: Worksheet) -> None:
    """Section 3."""
    section_title(ws, 24, "3. Hypergeometric: defectives in a sample of n drawn without replacement from a lot")
    input_row(ws, 25, "N = lot size")
    input_row(ws, 26, "D = defectives in the lot", "D = π · N")
    input_row(ws, 27, "n = sample size")
    input_row(ws, 28, "k (for the probabilities)")
    ok = "AND(ISNUMBER(B25),ISNUMBER(B26),ISNUMBER(B27),B25>1,B26<=B25,B27<=B25)"
    okk = f"AND({ok},ISNUMBER(B28))"
    result_row(ws, 29, "E[X] = n D / N", f'=IF({ok},B27*B26/B25,"")', NUMBER)
    result_row(ws, 30, "Var[X] = n (D/N)(1 − D/N)(N − n)/(N − 1)",
               f'=IF({ok},B27*(B26/B25)*(1-B26/B25)*(B25-B27)/(B25-1),"")', NUMBER)
    result_row(ws, 31, "P(X = k)", f'=IF({okk},_xlfn.HYPGEOM.DIST(B28,B27,B26,B25,FALSE),"")', PROBABILITY,
               "Acceptance Sampling.pdf p. 16: P[d = i] = C(D,i) C(N−D,n−i) / C(N,n)")
    result_row(ws, 32, "P(X ≤ k)", f'=IF({okk},_xlfn.HYPGEOM.DIST(B28,B27,B26,B25,TRUE),"")', PROBABILITY,
               "Testing of Hypotheses.xlsx 'OC-curve (hypergeometric)'")
    result_row(ws, 33, "P(X ≥ k)", f'=IF({okk},IF(B28<=0,1,1-_xlfn.HYPGEOM.DIST(B28-1,B27,B26,B25,TRUE)),"")',
               PROBABILITY)


def _poisson_exponential_uniform(ws: Worksheet) -> None:
    """Sections 4-7."""
    section_title(ws, 35, "4. Poisson: number of events in a fixed interval (e.g. orders per week)")
    _note(ws, 35)
    input_row(ws, 36, "λ = mean number of events per interval", "Naert Les 1 p. 9: λ = 2.959 customers / minute")
    input_row(ws, 37, "k (for the probabilities)")
    ok = "AND(ISNUMBER(B36),B36>0)"
    okk = f"AND({ok},ISNUMBER(B37))"
    result_row(ws, 38, "E[X] = λ", f'=IF({ok},B36,"")', NUMBER, "Naert Les 1 p. 7-9 (Poisson for counts)")
    result_row(ws, 39, "Var[X] = λ", f'=IF({ok},B36,"")', NUMBER)
    result_row(ws, 40, "P(X = k)", f'=IF({okk},_xlfn.POISSON.DIST(B37,B36,FALSE),"")', PROBABILITY,
               "Excel POISSON.DIST(k; λ; ONWAAR)")
    result_row(ws, 41, "P(X ≤ k)", f'=IF({okk},_xlfn.POISSON.DIST(B37,B36,TRUE),"")', PROBABILITY)
    result_row(ws, 42, "P(X ≥ k)", f'=IF({okk},IF(B37<=0,1,1-_xlfn.POISSON.DIST(B37-1,B36,TRUE)),"")', PROBABILITY)

    section_title(ws, 44, "5. Exponential: waiting time between events (rate λ per unit time)")
    _note(ws, 44)
    input_row(ws, 45, "rate λ = events per unit time", "e.g. 175.3 orders per week")
    input_row(ws, 46, "t (for the probabilities)")
    ok = "AND(ISNUMBER(B45),B45>0)"
    okt = f"AND({ok},ISNUMBER(B46))"
    result_row(ws, 47, "E[T] = 1 / λ", f'=IF({ok},1/B45,"")', NUMBER, "Naert Les 1 p. 7 (exponential for waiting times)")
    result_row(ws, 48, "Var[T] = 1 / λ²", f'=IF({ok},1/B45^2,"")', "0.0000000000")
    result_row(ws, 49, "P(T ≤ t) = 1 − e^(−λt)", f'=IF({okt},_xlfn.EXPON.DIST(B46,B45,TRUE),"")', PROBABILITY,
               "Excel EXPON.DIST(t; λ; WAAR) (Acceptance Sampling.xlsm 'distributions')")
    result_row(ws, 50, "P(T > t) = e^(−λt)", f'=IF({okt},EXP(-B45*B46),"")', PROBABILITY)

    section_title(ws, 52, "6. Uniform on [a, b]")
    _note(ws, 52)
    input_row(ws, 53, "a (lower end)")
    input_row(ws, 54, "b (upper end)")
    input_row(ws, 55, "x (for the probability)")
    ok = "AND(ISNUMBER(B53),ISNUMBER(B54),B54>B53)"
    result_row(ws, 56, "E[X] = (a + b) / 2", f'=IF({ok},(B53+B54)/2,"")', NUMBER, "Acceptance Sampling.xlsm 'distributions'")
    result_row(ws, 57, "Var[X] = (b − a)² / 12", f'=IF({ok},(B54-B53)^2/12,"")', NUMBER)
    result_row(ws, 58, "P(X ≤ x)", f'=IF(AND({ok},ISNUMBER(B55)),MIN(1,MAX(0,(B55-B53)/(B54-B53))),"")', PROBABILITY)

    section_title(ws, 60, "7. Normal: E[X] = μ, Var[X] = σ²; probabilities and σ from a tail fraction on the Normal sheet")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the distributions calculator."""
    write_header(ws, HEADER)
    _bernoulli_binomial(ws)
    _hypergeometric(ws)
    _poisson_exponential_uniform(ws)
    whole = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                           showErrorMessage=True, errorTitle="Whole number", error="Type a whole number, 0 or more.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Probability", error="Type a fraction between 0 and 1.")
    ws.add_data_validation(whole)
    ws.add_data_validation(fraction)
    for coordinate in ("B14", "B16", "B25", "B26", "B27", "B28", "B37"):
        whole.add(coordinate)
    for coordinate in ("B9", "B15"):
        fraction.add(coordinate)
    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
