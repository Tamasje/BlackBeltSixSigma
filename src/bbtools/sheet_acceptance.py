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

SHEET = "Aanvaardingssteekproeven"

HEADER = HeaderBlock(
    tool="Aanvaardingssteekproeven (acceptance sampling): OC-curve van een plan (n, c), "
         "producenten-/consumentenrisico, AOQ, AOQL, ATI, plan voor variabelen",
    source="source/course/Les 2/20260529_ottoy_Acceptance Sampling - Further Reading.pdf p. 2-10; "
           "Acceptance Sampling.pdf p. 23-27; Testing of Hypotheses.pdf p. 5-11; Testing of Hypotheses.xlsx",
    convention="Beslissing 12: invoer α en β vooraf ingevuld op 5 % en 10 % (p. 4; de uitgewerkte voorbeelden daar "
               "gebruiken β = 5 %); hypergeometrische OC met M = [Np] als N gegeven is, binomiale OC altijd getoond.",
    status=Status.VERIFIED,
    status_detail="getest tegen uitgewerkte voorbeelden van de cursus S03-WE06, S03-WE07, S03-WE20, S03-WE21, "
                  "S04-WE12, S04-WE16, S04-WE18",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Aanvaardingskans OC(p) van een enkelvoudig steekproefplan (single-stage plan) (n, c), α bij AQL en β bij "
            "LQL, AOQ, AOQL en ATI bij rectificerende inspectie (rectifying inspection), een OC/AOQ/ATI-tabel, en het "
            "plan voor variabelen (variables plan) (k, n) uit AQL en LQL.",
    inputs="n, c, lotgrootte N (optioneel: exacte hypergeometrische OC, AOQ, ATI), AQL, LQL, α, β, een fractie p, de "
           "stapgrootte van de tabel.",
    audit="niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)",
    disagreements=(
        "Further Reading p. 4 ontwerpt (n, c) met de tabel van Peach ('tabellen AS.pdf'), die niet in de "
        "cursusbestanden zit; het blad controleert daarom een plan. Het voorbeeldplan (164, 2) voor (0,5 %, 95 %) en "
        "(3,5 %, 5 %) heeft OC(0,5 %) = 95 % maar OC(3,5 %) = 7,1 % (binomiaal): de methode van Peach is benaderend, "
        "zoals de pagina zegt.",
        "Further Reading p. 10: 'AOQL approximately 1.3 %, at about 1.8 %' voor (250, 5), N = 1000 klopt met de "
        "benadering p·OC(p) (1,30 % bij 1,7 %), niet met de exacte formule op dezelfde slide (1,03 % bij 1,7 %), "
        "hoewel n/N = 0,25 niet klein is.",
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
    section_title(ws, 8, "1. Het plan (n, c) en de kwaliteitsniveaus (fracties: 0,02 = 2 %)")
    input_row(ws, 9, "n = steekproefgrootte (sample size)")
    input_row(ws, 10, "c = aanvaardingsgetal (acceptance number): aanvaard als aantal defecte stuks ≤ c")
    input_row(ws, 11, "N = lotgrootte (lot size) (optioneel: exacte hypergeometrische OC, AOQ, ATI)")
    input_row(ws, 12, "AQL = aanvaardbaar kwaliteitsniveau (acceptable quality level)", "wordt normaal aanvaard",
              "0.0000")
    input_row(ws, 13, "LQL = LTPD = limietkwaliteit (limiting quality level)", "wordt normaal afgekeurd", "0.0000")
    input_row(ws, 14, "α = doel voor het producentenrisico (producer's risk)", "p. 4: normaal 5 %", "0.00")
    input_row(ws, 15, "β = doel voor het consumentenrisico (consumer's risk)",
              "p. 4: normaal 10 %; de voorbeelden daar gebruiken 5 %", "0.00")
    ws["B14"], ws["B15"] = 0.05, 0.10
    label(ws, 16, 1, "Producentenrisico: een goed lot afkeuren (type I). Consumentenrisico: een slecht lot aanvaarden "
                     "(type II). Further Reading p. 2.", italic=True)


def _risks(ws: Worksheet) -> None:
    """Section 2: OC at AQL and LQL, and the risks."""
    section_title(ws, 18, "2. Risico's van het plan")
    column_titles(ws, 19, ["", "binomiaal", "hypergeometrisch (vraagt N)", "Bron in de cursus"])
    rows = (
        (20, "OC(AQL) = P(lot bij AQL aanvaarden)", "$B$12", False),
        (21, "Producentenrisico (producer's risk) α = 1 − OC(AQL)", "$B$12", True),
        (22, "Consumentenrisico (consumer's risk) β = OC(LQL) = P(lot bij LQL aanvaarden)", "$B$13", False),
    )
    for row, text, level, complement in rows:
        label(ws, row, 1, text)
        for column, oc, extra in (("B", _oc_binomial(level), ""), ("C", _oc_hypergeometric(level), f",{HAVE_LOT}")):
            value = f"1-{oc}" if complement else oc
            output_cell(ws, f"{column}{row}", f'=IF(AND({HAVE_PLAN},ISNUMBER({level}){extra}),{value},"")', PERCENT)
    label(ws, 20, 4, "Further Reading p. 4; Testing of Hypotheses.pdf p. 5", italic=True)
    label(ws, 24, 1, "Haalt beide doelen (α ≤ doel en β ≤ doel)?")
    for column in "BC":
        output_cell(ws, f"{column}24", f'=IF(AND(ISNUMBER({column}21),ISNUMBER({column}22)),IF(AND({column}21<=$B$14,'
                                       f'{column}22<=$B$15),"ja","nee"),"")')


def _one_p(ws: Worksheet) -> None:
    """Section 3: OC, AOQ and ATI at one fraction defective."""
    section_title(ws, 26, "3. Eén lotkwaliteit p: aanvaarding, uitgaande kwaliteit, inspectie-inspanning")
    input_row(ws, 27, "p = fractie defect (fraction defective) van het lot", "", "0.0000")
    have = f"AND({HAVE_PLAN},ISNUMBER($B$27))"
    lot = f"AND({have},{HAVE_LOT})"
    result_row(ws, 28, "OC(p), binomiaal", f'=IF({have},{_oc_binomial("$B$27")},"")', PERCENT)
    result_row(ws, 29, "OC(p), hypergeometrisch", f'=IF({lot},{_oc_hypergeometric("$B$27")},"")', PERCENT, "p. 4")
    result_row(ws, 30, "AOQ(p) (average outgoing quality) = p·OC(p)·(1 − (n/N)·Rs*)",
               f'=IF({lot},{_aoq("$B$27", "B29")},"")', PERCENT, "p. 10")
    result_row(ws, 31, "AOQ(p) ≈ p·OC(p) (n << N; hypergeometrische OC als N gegeven is)",
               f'=IF({have},$B$27*IF(ISNUMBER(B29),B29,B28),"")', PERCENT, "p. 10")
    result_row(ws, 32, "ATI(p) (average total inspection) = n·OC(p) + N·(1 − OC(p))",
               f'=IF({lot},$B$9*B29+$B$11*(1-B29),"")', "0.0", "p. 10")


def _variables(ws: Worksheet) -> None:
    """Section 4: single-stage variables plan from AQL (p0) and LQL (pt), with α and β of section 1."""
    section_title(ws, 34, "4. Plan voor variabelen (variables plan, normaal verdeelde metingen): aanvaard als "
                          "(x̄ − grens) / s ≥ k   (p. 9)")
    label(ws, 35, 1, "Gebruikt AQL = p0, LQL = pt, α en β uit sectie 1.", italic=True)
    z = "_xlfn.NORM.S.INV"
    have = "AND(ISNUMBER($B$12),ISNUMBER($B$13),ISNUMBER($B$14),ISNUMBER($B$15),$B$13>$B$12)"
    k = (f"({z}($B$13)*{z}($B$14)+{z}($B$12)*{z}($B$15))/({z}(1-$B$14)+{z}(1-$B$15))")
    result_row(ws, 38, "k = (z_pt z_α + z_p0 z_β) / (z_(1−α) + z_(1−β))", f'=IF({have},{k},"")', "0.0000",
               "Further Reading p. 9 (z_q = q-kwantiel van N(0,1))")
    result_row(ws, 39, "n = (z_(1−α) + z_(1−β))² (1 + k²/2) / (z_pt − z_p0)²",
               f'=IF(ISNUMBER(B38),({z}(1-$B$14)+{z}(1-$B$15))^2*(1+B38^2/2)/({z}($B$13)-{z}($B$12))^2,"")', "0.00")
    result_row(ws, 40, "n naar boven afgerond", '=IF(ISNUMBER(B39),ROUNDUP(B39,0),"")', "0",
               "voorbeeld p. 9: 63,2 → 64")
    oc = "1-_xlfn.NORM.S.DIST(({z}({p})+B38)*SQRT(B40)/SQRT(1+B38^2/2),TRUE)"
    result_row(ws, 41, "OC(AQL) van dit plan", f'=IF(ISNUMBER(B40),{oc.format(z=z, p="$B$12")},"")', PERCENT, "p. 9")
    result_row(ws, 42, "OC(LQL) van dit plan", f'=IF(ISNUMBER(B40),{oc.format(z=z, p="$B$13")},"")', PERCENT)


def _table(ws: Worksheet) -> None:
    """Section 5: OC, AOQ and ATI over a grid of p, and the AOQL."""
    section_title(ws, 44, "5. OC-curve, AOQ en ATI over een reeks p (AOQL = de grootste AOQ in de tabel)")
    first, last = TABLE_FIRST, TABLE_FIRST + TABLE_ROWS
    for row, text, column in ((45, "AOQL met de exacte formule (kolom E) en de p waarbij ze optreedt", "E"),
                              (46, "AOQL met de benadering p·OC(p) (kolom D) en haar p", "D")):
        label(ws, row, 1, text)
        output_cell(ws, f"B{row}", f'=IF(COUNT({column}{first}:{column}{last})>0,MAX({column}{first}:{column}{last}),"")',
                    PERCENT)
        output_cell(ws, f"C{row}", f'=IF(ISNUMBER(B{row}),INDEX(A{first}:A{last},MATCH(B{row},{column}{first}:'
                                   f'{column}{last},0)),"")', PERCENT)
    label(ws, 45, 4, "alleen exact tot op de stapgrootte van de tabel", italic=True)
    label(ws, 46, 4, "voorbeeld p. 10 (250, 5), N = 1000: AOQL ≈ 1,3 % bij p ≈ 1,8 % is deze benadering", italic=True)
    input_row(ws, 48, "Stapgrootte van p in de tabel", "Testing of Hypotheses.xlsx gebruikt 0,005 (p van 0 tot 0,2)",
              "0.0000")
    ws["B48"] = 0.005
    column_titles(ws, first - 1, ["p", "OC binomiaal", "OC hypergeometrisch", "AOQ ≈ p·OC(p)", "AOQ (exact, p. 10)",
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
    label(ws, 92, 1, "Hier niet berekend: dubbele, sequentiële (SPRT) en skip-lot-plannen (double, sequential, "
                     "skip-lot plans; Further Reading p. 5-11), opzoeken in ISO 2859 / 3951 (p. 12). Een plan (n, c) "
                     "ontwerpen vraagt de tabel van Peach 'tabellen AS.pdf' (p. 4), die niet in de cursusbestanden zit.",
          italic=True)
    whole = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                           showErrorMessage=True, errorTitle="Geheel getal", error="Typ een geheel getal.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Fractie", error="Typ een fractie tussen 0 en 1.")
    ws.add_data_validation(whole)
    ws.add_data_validation(fraction)
    for coordinate in ("B9", "B10", "B11"):
        whole.add(coordinate)
    for coordinate in ("B12", "B13", "B14", "B15", "B27", "B48"):
        fraction.add(coordinate)
    ws.column_dimensions["A"].width = 58
    for letter in "BCDEF":
        ws.column_dimensions[letter].width = 18
