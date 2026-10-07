"""Verdelingen sheet (Distributions): E[X], Var[X] and probabilities for Bernoulli, binomial, hypergeometric,
Poisson, exponential and uniform distributions (the families of exam Q6).

Course: binomial defectives in a lot P[i] = C(N,i) π^i (1−π)^(N−i) with E[i] = Nπ (Acceptance Sampling.pdf
p. 12); hypergeometric sampling distribution of defectives in a sample (p. 16; Testing of Hypotheses.xlsx
'OC-curve (hypergeometric)'); Poisson for counts, exponential for waiting times (Naert Les 1 p. 7-9);
uniform and exponential densities (Acceptance Sampling.xlsm 'distributions'). Excel functions as the course's
workbooks use them: BINOM.DIST, HYPGEOM.DIST, POISSON.DIST, EXPON.DIST.
The course prints no general formula for the Bernoulli, Poisson, exponential and uniform blocks (it only names
these distributions); they use the standard definitions, labelled as such (decision 20). Worked examples: binomial,
hypergeometric and Poisson (Naert Les 1 p. 10).
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import HeaderBlock, Status, font, input_row, result_row, section_title, write_header

SHEET = "Verdelingen"
STANDARD = ("standaarddefinitie, niet gedrukt in de cursus (beslissing 20); geen uitgewerkt cursusvoorbeeld; "
            "gecontroleerd door de stats-auditor (build/README.md)")
STANDARD_POISSON = ("standaarddefinitie, niet gedrukt in de cursus (beslissing 20); cursusvoorbeeld "
                    "Naert Les 1 p. 9-10 (λ = 2,959) getest")

HEADER = HeaderBlock(
    tool="Verdelingen (distributions): E[X], Var[X] en kansen (Bernoulli, binomiaal, hypergeometrisch, Poisson, "
         "exponentieel, uniform)",
    source="source/course/Les 2/20260529_ottoy_Acceptance Sampling.pdf p. 12, 16, 20; Acceptance Sampling.xlsm; "
           "Testing of Hypotheses.xlsx; Les 1/20260522_naert_big data.pdf p. 5-10",
    convention="De verdelingsfuncties van Excel zoals de werkmappen van de cursus ze gebruiken; aantallen k zijn "
               "gehele getallen; P(X ≥ k) = 1 − P(X ≤ k − 1).",
    status=Status.VERIFIED,
    status_detail="binomiaal en hypergeometrisch blok getest tegen de uitgewerkte cursusvoorbeelden (worked "
                  "examples) S04-WE02, S03-WE19, S03-WE21, het Poisson-blok tegen S02-WE09; Bernoulli, Poisson, "
                  "exponentieel en uniform gebruiken standaarddefinities die niet in de cursus gedrukt staan "
                  "(beslissing 20; geaudit)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Gemiddelde, variantie en punt- en cumulatieve kansen van de verdelingsfamilies uit de cursus en uit "
            "examenvraag Q6 (Bernoulli, binomiaal, hypergeometrisch, Poisson, exponentieel, uniform).",
    inputs="per blok: p; n, p, k; N, D, n, k; λ, k; intensiteit (rate) λ, t; a, b, x.",
    audit="stats-auditor PASS (2026-09-28) voor de blokken Bernoulli, Poisson, exponentieel en uniform: alle 14 "
          "waarden voor één invoer kloppen met een onafhankelijke berekening. De geciteerde pagina's drukken echter "
          "geen algemene formule voor deze vier families (Naert Les 1 p. 7-9 noemt alleen Poisson voor tellingen en "
          "exponentieel voor wachttijden; Acceptance Sampling.xlsm 'distributions' berekent EXPON.DIST met een "
          "intensiteit (rate) en een uniforme dichtheid op [1, 2]); het blad gebruikt de standaarddefinities, als "
          "zodanig aangeduid (beslissing 20).",
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


def _note(ws: Worksheet, row: int, text: str = STANDARD) -> None:
    """Red note next to a section title: this block's formulas are standard definitions, not course formulas."""
    ws.cell(row=row, column=4, value=text).font = font(italic=True, color="C00000")


def _bernoulli_binomial(ws: Worksheet) -> None:
    """Sections 1-2."""
    section_title(ws, 8, "1. Bernoulli: één stuk, X = 1 (bv. niet-conform) met kans p")
    _note(ws, 8)
    input_row(ws, 9, "p = P(X = 1) (fractie)", "bv. 2 op 40 -> 0,05", "0.0000")
    ok = "AND(ISNUMBER(B9),B9>=0,B9<=1)"
    result_row(ws, 10, "E[X] = p", f'=IF({ok},B9,"")', NUMBER)
    result_row(ws, 11, "Var[X] = p (1 − p)", f'=IF({ok},B9*(1-B9),"")', NUMBER)

    section_title(ws, 13, "2. Binomiaal (binomial): aantal successen (bv. defecte stuks) in n onafhankelijke "
                          "herhalingen (trials)")
    input_row(ws, 14, "n = aantal herhalingen (stuks)")
    input_row(ws, 15, "p = kans per herhaling (fractie)", "", "0.000000")
    input_row(ws, 16, "k (voor de kansen)")
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
    section_title(ws, 24, "3. Hypergeometrisch (hypergeometric): defecte stuks in een steekproef van n, zonder "
                          "teruglegging uit een lot")
    input_row(ws, 25, "N = lotgrootte (lot size)")
    input_row(ws, 26, "D = defecte stuks in het lot", "D = π · N")
    input_row(ws, 27, "n = steekproefgrootte (sample size)")
    input_row(ws, 28, "k (voor de kansen)")
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
    section_title(ws, 35, "4. Poisson: aantal gebeurtenissen in een vast interval (bv. bestellingen per week)")
    _note(ws, 35, STANDARD_POISSON)
    input_row(ws, 36, "λ = gemiddeld aantal gebeurtenissen per interval",
              "Naert Les 1 p. 9-10: λ = 2,959 klanten / minuut")
    input_row(ws, 37, "k (voor de kansen)")
    ok = "AND(ISNUMBER(B36),B36>0)"
    okk = f"AND({ok},ISNUMBER(B37))"
    result_row(ws, 38, "E[X] = λ", f'=IF({ok},B36,"")', NUMBER,
               "Naert Les 1 p. 7-9 noemt Poisson voor tellingen (counts)")
    result_row(ws, 39, "Var[X] = λ", f'=IF({ok},B36,"")', NUMBER)
    result_row(ws, 40, "P(X = k)", f'=IF({okk},_xlfn.POISSON.DIST(B37,B36,FALSE),"")', PROBABILITY,
               "Excel POISSON.DIST(k; λ; ONWAAR)")
    result_row(ws, 41, "P(X ≤ k)", f'=IF({okk},_xlfn.POISSON.DIST(B37,B36,TRUE),"")', PROBABILITY)
    result_row(ws, 42, "P(X ≥ k)", f'=IF({okk},IF(B37<=0,1,1-_xlfn.POISSON.DIST(B37-1,B36,TRUE)),"")', PROBABILITY)

    section_title(ws, 44, "5. Exponentieel (exponential): wachttijd tussen gebeurtenissen (intensiteit λ per "
                          "tijdseenheid)")
    _note(ws, 44)
    input_row(ws, 45, "intensiteit (rate) λ = gebeurtenissen per tijdseenheid", "bv. 175,3 bestellingen per week")
    input_row(ws, 46, "t (voor de kansen)")
    ok = "AND(ISNUMBER(B45),B45>0)"
    okt = f"AND({ok},ISNUMBER(B46))"
    result_row(ws, 47, "E[T] = 1 / λ", f'=IF({ok},1/B45,"")', NUMBER,
               "Naert Les 1 p. 7 noemt exponentieel voor wachttijden")
    result_row(ws, 48, "Var[T] = 1 / λ²", f'=IF({ok},1/B45^2,"")', "0.0000000000")
    result_row(ws, 49, "P(T ≤ t) = 1 − e^(−λt)", f'=IF({okt},_xlfn.EXPON.DIST(B46,B45,TRUE),"")', PROBABILITY,
               "Excel EXPON.DIST(t; λ; WAAR); de werkmap van de cursus gebruikt EXPON.DIST met een intensiteit (rate) "
               "(Acceptance Sampling.xlsm)")
    result_row(ws, 50, "P(T > t) = e^(−λt)", f'=IF({okt},EXP(-B45*B46),"")', PROBABILITY)

    section_title(ws, 52, "6. Uniforme verdeling (uniform) op [a, b]")
    _note(ws, 52)
    input_row(ws, 53, "a (ondergrens)")
    input_row(ws, 54, "b (bovengrens)")
    input_row(ws, 55, "x (voor de kans)")
    ok = "AND(ISNUMBER(B53),ISNUMBER(B54),B54>B53)"
    result_row(ws, 56, "E[X] = (a + b) / 2", f'=IF({ok},(B53+B54)/2,"")', NUMBER,
               "Acceptance Sampling.xlsm 'distributions' (uniforme dichtheid op [1, 2])")
    result_row(ws, 57, "Var[X] = (b − a)² / 12", f'=IF({ok},(B54-B53)^2/12,"")', NUMBER)
    result_row(ws, 58, "P(X ≤ x)", f'=IF(AND({ok},ISNUMBER(B55)),MIN(1,MAX(0,(B55-B53)/(B54-B53))),"")', PROBABILITY)

    section_title(ws, 60, "7. Normaal (normal): E[X] = μ, Var[X] = σ²; kansen en σ uit een staartfractie op het "
                          "blad Normaal")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the distributions calculator."""
    write_header(ws, HEADER)
    _bernoulli_binomial(ws)
    _hypergeometric(ws)
    _poisson_exponential_uniform(ws)
    whole = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                           showErrorMessage=True, errorTitle="Geheel getal", error="Typ een geheel getal, 0 of meer.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Kans", error="Typ een fractie tussen 0 en 1.")
    ws.add_data_validation(whole)
    ws.add_data_validation(fraction)
    for coordinate in ("B14", "B16", "B25", "B26", "B27", "B28", "B37"):
        whole.add(coordinate)
    for coordinate in ("B9", "B15"):
        fraction.add(coordinate)
    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
