"""ANOVA, DOE and regression sheet: one-way ANOVA, effects and ANOVA of a 2^k factorial (k = 2 … 5, up to 4
replicates) and simple linear regression with tests, confidence and prediction intervals.

Course (De Vuyst, Les 3, DOE.pdf): one-way ANOVA SS_Total = ΣΣ (Yij − Ȳ..)², SS_Error = ΣΣ (Yij − Ȳi.)²,
SS_Treatment = Σ n (Ȳi. − Ȳ..)² (p. 6), F = MS_Treatment / MS_Error ~ F(a − 1, a(n − 1)) (p. 7-8, Table 4.6);
2^k designs with levels coded −1/+1 (p. 46), in standard order (p. 70, 74); effect = mean response at +1 minus mean at
−1 = contrast / (n 2^(k−1)), SS = contrast² / (n 2^k) (p. 48, 57, 66); s.e.(effect) = √(σ̂² / (n 2^(k−2))) and
effect ± 2 s.e. (p. 67-68); single replicate: pool the higher-order interactions into the error (p. 72, 77);
Dummies p. 233: coefficient = effect / 2, β0 = mean of all runs. Regression.pdf: b1 = S_xy / S_xx (p. 17-19),
SS_T = SS_R + SS_E, R² = SS_R / SS_T (p. 24-27), MS_E = SS_E / (n − 2) (p. 28), Var(b1) = σ²/S_xx,
Var(b0) = σ²(1/n + x̄²/S_xx) (p. 29), t-tests (p. 30-31), F-test (p. 33), CIs (p. 34), CI of the mean response
(p. 35-36) and prediction interval (p. 38). R²_adj: p. 56 prints 1 − (1 − R²)(n − 1)/(n − k − 2); the course's own
outputs (Regression p. 22: 87.1 %; DOE p. 61: 0.8666) and σ̂ = √(SSE/(n − k − 1)) (p. 57) use n − k − 1. Both are shown.

Row plan: α 9; one-way ANOVA 11-57 (data B14:I43); factorial 60-149 (runs 65-96, effects 110-140, model table
143-149; sign columns Q:AU); regression 152-189 (data B191:C390).
"""
from __future__ import annotations

from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    column_titles,
    font,
    input_cell,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "ANOVA DOE regressie"

HEADER = HeaderBlock(
    tool="Eenwegs-ANOVA (one-way ANOVA), effecten en ANOVA van een 2^k-factoriële proefopzet (factorial design, "
         "k = 2 tot 5), enkelvoudige lineaire regressie (simple linear regression)",
    source="source/course/Les 3/20260605_de vuyst_BB_DOE.pdf p. 3-15, 46-92; 20260605_de vuyst_BB_Regression.pdf "
           "p. 16-38, 56-57",
    convention="Invoer α vooraf ingevuld op 0,05 (beslissing 5); BI's en t-toetsen van de regressie eenzijdig en "
               "tweezijdig naast elkaar (beslissing 6); factoren gecodeerd −1/+1 in standaardvolgorde (standard order; "
               "DOE p. 46, 70, 74); één herhaling (single replicate): interacties van een gekozen orde en hoger in de "
               "fout poolen (DOE p. 72, 77); R²_adj op beide manieren getoond.",
    status=Status.VERIFIED,
    status_detail="getest tegen uitgewerkte voorbeelden van de cursus S05-WE01, S05-WE02, S05-WE05 tot S05-WE09, "
                  "S05-WE17, S05-WE18, en tegen S08-WE16 (extra, Dummies; niet te kennen); gedrukte waarden die niet "
                  "kloppen staan in build/README.md",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Eenwegs-ANOVA-tabel; effecten, coëfficiënten (extra, Dummies; niet te kennen), kwadratensommen (SS), "
            "F-toetsen en intervallen ±2 s.e. van een 2^k-factoriële proefopzet met zuivere fout (pure error) uit "
            "herhalingen en/of gepoolde interacties van hogere orde, de ANOVA van het model en R²; enkelvoudige "
            "lineaire regressie met ANOVA, R², t-toetsen, BI's van β0 en β1, en het BI van de gemiddelde respons en "
            "het predictie-interval bij x0.",
    inputs="α; ANOVA: tot 8 groepen van elk tot 30 waarden (één kolom per groep); factorieel: k, optioneel de orde "
           "vanaf waar gepoold wordt, tot 4 herhalingen per run in standaardvolgorde; regressie: tot 200 paren (x, y), "
           "x0 en de H0-waarden van β1 en β0.",
    audit="niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)",
    disagreements=(
        "DOE p. 50 (S05-WE05): '[AB] = 5,78 – 4,92 = 0,857'; het exacte effect is 0,8583 (gemiddelden 5,7767 en "
        "4,9183).",
        "DOE p. 71 (S05-WE08): SS_ABC (en MS) gedrukt als 5,5625; de gegevens op p. 70 geven contrast 9 en SS 81/16 = "
        "5,0625, wat ook de gedrukte F0 2,08, P 0,19 en het totaal 92,9375 impliceren. De gedrukte P van A, "
        "2,54 × 10^-3, is 2,534 × 10^-3 voor F0 18,69 op F(1, 8).",
        "DOE p. 53 (S05-WE06): 'AB = (52 + 20)/2 − (30 + 40)/2 = −1'; die uitdrukking is gelijk aan +1, wat het blad "
        "geeft.",
        "Regression p. 56 drukt R²_adj = 1 − (1 − R²)(n − 1)/(n − k − 2); de eigen outputs van de cursus gebruiken "
        "n − k − 1 (Regression p. 22 Minitab R-Sq(adj) 87,1 %; DOE p. 61 Adj R-Squared 0,8666; σ̂ op Regression "
        "p. 57). Het blad toont beide, met label.",
        "Regression p. 21 (S05-WE17): de gefitte rechte 'ŷ = 74.20 + 14.97x' van Figure 11-4 verschilt van de "
        "kleinste-kwadratenwaarden (least squares) 74,283 en 14,947 van de Minitab-output op p. 22, die het blad "
        "reproduceert.",
    ),
)

ALPHA = "$B$9"
NUMBER = "0.000000"
DECISION = '=IF(ISNUMBER({p}),IF({p}<' + ALPHA + ',"verwerp H0","H0 niet verwerpen"),"")'

GROUP_COLUMNS = "BCDEFGHI"
FIRST_GROUP_ROW, LAST_GROUP_ROW = 14, 43
ANOVA_ROWS = {"treatments": 52, "error": 53, "total": 54}  # B SS, C df, D MS, E F, F p, G F crit, H decision
GROUP_STATS = {"n": 45, "mean": 46, "sd": 47}

FACTORS = "ABCDE"
REPLICATE_COLUMNS = "GHIJ"
RUNS, FIRST_RUN, FIRST_EFFECT = 32, 65, 110
SIGN_FIRST_COLUMN = 17  # column Q: sign column of effect 1 (A); effect m sits in column Q + m − 1
MODEL_ROWS = {"model": 144, "error": 145, "total": 146}  # B SS, C df, D MS, E F, F p, G decision

FIRST_PAIR, PAIRS = 191, 200
X_DATA = f"$B${FIRST_PAIR}:$B${FIRST_PAIR + PAIRS - 1}"
Y_DATA = f"$C${FIRST_PAIR}:$C${FIRST_PAIR + PAIRS - 1}"
T_TESTS = {"b1": 181, "b0": 182}  # B estimate, C H0 value, D t, E-G p (≠, >, <), H-J decisions
INTERVALS = {"b1": 185, "b0": 186, "mean": 187, "prediction": 188}  # B centre, C s.e., D-E two-sided, F lower, G upper

INPUTS = {"alpha": "B9", "k": "B61", "pool_order": "B62", "x0": "B153", "beta1_0": "B154", "beta0_0": "B155"}
RESULTS = {
    "grand_mean": "B55", "pooled_sd": "B56", "groups": "B57",
    "n_rep": "B98", "complete": "B99", "N": "B100", "beta0": "B101", "ss_pe": "B102", "df_pe": "B103",
    "ss_pool": "B104", "df_pool": "B105", "mse": "B106", "se_effect": "B107",
    "r2_doe": "B147", "r2_adj_doe": "B148", "r2_adj_doe_p56": "B149",
    "pairs": "B156", "n": "B157", "xbar": "B158", "ybar": "B159", "sxx": "B160", "b1": "B161", "b0": "B162",
    "sst": "B163", "ssr": "B164", "sse": "B165", "mse_reg": "B166", "s": "B167", "r2": "B168", "r2_adj": "B169",
    "r2_adj_p56": "B170", "F": "B171", "p_F": "B172", "se_b1": "B174", "se_b0": "B175", "fit": "B176",
    "se_fit": "B177", "se_pred": "B178",
}


def effect_name(mask: int) -> str:
    """Effect label of a factor bitmask: 1 -> 'A', 3 -> 'AB', 7 -> 'ABC' (bit j = factor j)."""
    return "".join(FACTORS[j] for j in range(len(FACTORS)) if mask >> j & 1)


def sign(run: int, mask: int) -> int:
    """Coded level (−1/+1) of effect `mask` in standard-order run `run` (0-based): the product of its factors' levels.

    In standard order factor j is +1 in run r exactly when bit j of r is set (A alternates every run, B every 2 runs).
    """
    value = 1
    for j in range(len(FACTORS)):
        if mask >> j & 1:
            value *= 1 if run >> j & 1 else -1
    return value


def run_row(run: int) -> int:
    """Sheet row of standard-order run `run` (0-based)."""
    return FIRST_RUN + run


def effect_row(mask: int) -> int:
    """Sheet row of effect `mask` (1 … 31) in the effects table."""
    return FIRST_EFFECT + mask - 1


def group_cell(group: int, i: int) -> str:
    """Input cell of value i (0-based) of one-way ANOVA group `group` (0-based)."""
    return f"{GROUP_COLUMNS[group]}{FIRST_GROUP_ROW + i}"


def response_cell(run: int, replicate: int) -> str:
    """Input cell of replicate `replicate` (0-based) of standard-order run `run` (0-based)."""
    return f"{REPLICATE_COLUMNS[replicate]}{run_row(run)}"


def pair_cells(i: int) -> tuple[str, str]:
    """Input cells (x, y) of regression pair i (0-based)."""
    return f"B{FIRST_PAIR + i}", f"C{FIRST_PAIR + i}"


def _settings(ws: Worksheet) -> None:
    """Row 9: α (decision 5)."""
    section_title(ws, 8, "Instellingen")
    input_row(ws, 9, "Significantieniveau α (significance level; betrouwbaarheid = 1 − α)",
              "de cursus heeft geen standaardwaarde; de meeste cursusvoorbeelden gebruiken 5 %; gebruik de waarde uit "
              "de vraag", "0.0000")
    ws["B9"] = 0.05


def _group_statistics(ws: Worksheet) -> None:
    """Rows 45-49: per group n, mean, s and the two terms of SS_Treatment and SS_Error."""
    for row, text in ((45, "n_i"), (46, "gemiddelde Ȳ_i"), (47, "standaardafwijking s_i"), (48, "n_i (Ȳ_i − Ȳ)²"),
                      (49, "Σ (Y_ij − Ȳ_i)²")):
        label(ws, row, 1, text)
    for letter in GROUP_COLUMNS:
        column = f"{letter}{FIRST_GROUP_ROW}:{letter}{LAST_GROUP_ROW}"
        output_cell(ws, f"{letter}45", f'=IF(COUNT({column})>0,COUNT({column}),"")', "0")
        output_cell(ws, f"{letter}46", f'=IF(COUNT({column})>0,AVERAGE({column}),"")', NUMBER)
        output_cell(ws, f"{letter}47", f'=IF(COUNT({column})>1,_xlfn.STDEV.S({column}),"")', NUMBER)
        output_cell(ws, f"{letter}48", f'=IF(ISNUMBER({letter}46),{letter}45*({letter}46-$B$55)^2,"")', NUMBER)
        output_cell(ws, f"{letter}49", f'=IF(COUNT({column})>0,DEVSQ({column}),"")', NUMBER)


def _one_way(ws: Worksheet) -> None:
    """Section 1: one-way ANOVA from up to 8 groups of raw values (DOE p. 6-8)."""
    section_title(ws, 11, "1. Eenwegs-ANOVA (one-way ANOVA): één kolom per groep (factorniveau, factor level), de "
                          "waarden eronder (rijen 14-43)")
    label(ws, 12, 1, "Rij 13: desgewenst een naam per groep. Groepen mogen verschillend groot zijn.", italic=True)
    label(ws, 13, 1, "groepsnaam", bold=True)
    for letter in GROUP_COLUMNS:
        input_cell(ws, f"{letter}13")
        for row in range(FIRST_GROUP_ROW, LAST_GROUP_ROW + 1):
            input_cell(ws, f"{letter}{row}")
    _group_statistics(ws)
    everything = f"B{FIRST_GROUP_ROW}:I{LAST_GROUP_ROW}"
    ok = "AND(ISNUMBER($B$57),$B$57>=2,SUM(B45:I45)>$B$57)"  # at least 2 groups and error df > 0
    column_titles(ws, 51, ["Bron (source)", "SS", "df", "MS", "F0", "p-waarde", "kritieke F bij α", "Besluit bij α"])
    rows = {
        52: ("Behandelingen (treatments, tussen de groepen)", "SUM(B48:I48)", "$B$57-1"),
        53: ("Fout (error, binnen de groepen)", "SUM(B49:I49)", "SUM(B45:I45)-$B$57"),
        54: ("Totaal", f"DEVSQ({everything})", "SUM(B45:I45)-1"),
    }
    for row, (text, ss, df) in rows.items():
        label(ws, row, 1, text)
        output_cell(ws, f"B{row}", f'=IF({ok},{ss},"")', "0.0000")
        output_cell(ws, f"C{row}", f'=IF({ok},{df},"")', "0")
    output_cell(ws, "D52", '=IF(ISNUMBER(B52),B52/C52,"")', "0.0000")
    output_cell(ws, "D53", '=IF(ISNUMBER(B53),B53/C53,"")', "0.0000")
    output_cell(ws, "E52", '=IF(AND(ISNUMBER(D53),N(D53)>0),D52/D53,"")', "0.0000")
    output_cell(ws, "F52", '=IF(ISNUMBER(E52),_xlfn.F.DIST.RT(E52,C52,C53),"")', "0.000000")
    output_cell(ws, "G52", f'=IF(ISNUMBER(E52),_xlfn.F.INV.RT({ALPHA},C52,C53),"")', "0.0000")
    output_cell(ws, "H52", DECISION.format(p="F52"))
    label(ws, 53, 5, "H0: alle groepsgemiddelden gelijk (DOE p. 7-8, Table 4.6)", italic=True)
    result_row(ws, 55, "totaal gemiddelde Ȳ (grand mean)", f'=IF(COUNT({everything})>0,AVERAGE({everything}),"")',
               NUMBER)
    result_row(ws, 56, "gepoolde standaardafwijking √MS_E", '=IF(ISNUMBER(D53),SQRT(D53),"")', NUMBER)
    result_row(ws, 57, "a = aantal groepen", '=IF(COUNT(B45:I45)>0,COUNT(B45:I45),"")', "0")


def _runs(ws: Worksheet) -> None:
    """Rows 64-96: the 32 standard-order runs, their replicate inputs and per-run summaries."""
    column_titles(ws, 64, ["Run", *FACTORS, "y herhaling 1", "y herhaling 2", "y herhaling 3", "y herhaling 4", "n",
                           "gemiddelde van de run", "som van de run", "Σ (y − gemiddelde van de run)²",
                           "in de proefopzet (1/0)"])
    for run in range(RUNS):
        r = run_row(run)
        ws[f"A{r}"] = run + 1
        ws[f"A{r}"].font = font()
        output_cell(ws, f"O{r}", f"=IF(AND(ISNUMBER($B$61),$B$61>=2,$B$61<=5,A{r}<=2^$B$61),1,0)", "0")
        for j, letter in enumerate("BCDEF"):
            output_cell(ws, f"{letter}{r}", f'=IF(AND(O{r}=1,{j + 1}<=$B$61),{1 if run >> j & 1 else -1},"")', "0")
        for letter in REPLICATE_COLUMNS:
            input_cell(ws, f"{letter}{r}")
        ys = f"G{r}:J{r}"
        output_cell(ws, f"K{r}", f'=IF(AND(O{r}=1,COUNT({ys})>0),COUNT({ys}),"")', "0")
        output_cell(ws, f"L{r}", f'=IF(ISNUMBER(K{r}),AVERAGE({ys}),"")', NUMBER)
        output_cell(ws, f"M{r}", f"=IF(ISNUMBER(K{r}),SUM({ys}),0)", NUMBER)
        output_cell(ws, f"N{r}", f"=IF(ISNUMBER(K{r}),DEVSQ({ys}),0)", NUMBER)
    label(ws, 63, SIGN_FIRST_COLUMN, "Teken (−1/+1) van elk effect in elke run: gebruikt door de contrastformules",
          italic=True)
    for mask in range(1, RUNS):
        column = SIGN_FIRST_COLUMN + mask - 1
        ws.cell(row=64, column=column, value=effect_name(mask)).font = font(bold=True)
        for run in range(RUNS):
            ws.cell(row=run_row(run), column=column, value=sign(run, mask)).font = font(color="808080")


def _error_estimate(ws: Worksheet) -> None:
    """Rows 98-107: n, completeness, β0, pure error, pooled interactions, MS_E and s.e.(effect)."""
    first, last = run_row(0), run_row(RUNS - 1)
    n_col, in_design = f"K{first}:K{last}", f"O{first}:O{last}"
    result_row(ws, 98, "n = herhalingen (replicates) per run", f'=IF(COUNT({n_col})>0,MAX({n_col}),"")', "0")
    result_row(ws, 99, "Volledige proefopzet (runs 1 … 2^k hebben elk n responsen)?",
               f'=IF(COUNT({n_col})=0,"",IF(AND(COUNT({n_col})=SUM({in_design}),MIN({n_col})=MAX({n_col})),"ja",'
               f'"NEE: vul runs 1 … 2^k in, elk met hetzelfde aantal herhalingen"))')
    ok = '$B$99="ja"'
    pooling = "AND(ISNUMBER($B$62),$B$62>=2)"
    ss, order = f"F{FIRST_EFFECT}:F{effect_row(RUNS - 1)}", f"B{FIRST_EFFECT}:B{effect_row(RUNS - 1)}"
    result_row(ws, 100, "N = 2^k · n waarnemingen", f'=IF({ok},2^$B$61*$B$98,"")', "0")
    result_row(ws, 101, "totaal gemiddelde (grand mean) = β0", f'=IF({ok},SUM(M{first}:M{last})/$B$100,"")', NUMBER,
               "β0: Dummies p. 233 (extra, Dummies; niet te kennen)")
    result_row(ws, 102, "SS zuivere fout (pure error, tussen de herhalingen)", f'=IF({ok},SUM(N{first}:N{last}),"")',
               "0.0000")
    result_row(ws, 103, "df zuivere fout = 2^k (n − 1)", f'=IF({ok},2^$B$61*($B$98-1),"")', "0")
    result_row(ws, 104, "SS gepoolde interacties (orde ≥ B62)",
               f'=IF({ok},IF({pooling},SUMIFS({ss},{order},">="&$B$62),0),"")', "0.0000", "DOE p. 72, 77")
    result_row(ws, 105, "df gepoolde interacties",
               f'=IF({ok},IF({pooling},COUNTIFS({order},">="&$B$62,{ss},">=0"),0),"")', "0")
    result_row(ws, 106, "σ̂² = MS_E = (SS zuivere fout + SS gepoold) / (df + df)",
               f'=IF(AND({ok},N($B$103)+N($B$105)>0),($B$102+$B$104)/($B$103+$B$105),"")', NUMBER)
    result_row(ws, 107, "standaardfout (standard error) s.e.(effect) = √(σ̂² / (n 2^(k−2)))",
               '=IF(ISNUMBER($B$106),SQRT($B$106/($B$98*2^($B$61-2))),"")', NUMBER, "DOE p. 67")


def _effect_row(ws: Worksheet, mask: int) -> None:
    """One row of the effects table: contrast, effect, coefficient, SS, F-test and effect ± 2 s.e."""
    r, first, last = effect_row(mask), run_row(0), run_row(RUNS - 1)
    signs = get_column_letter(SIGN_FIRST_COLUMN + mask - 1)
    ws[f"A{r}"] = effect_name(mask)
    ws[f"A{r}"].font = font(bold=True)
    ws[f"B{r}"] = bin(mask).count("1")
    ws[f"B{r}"].font = font()
    in_design = f'AND($B$99="ja",{mask}<2^$B$61)'
    output_cell(ws, f"C{r}", f'=IF({in_design},SUMPRODUCT({signs}{first}:{signs}{last},M{first}:M{last}),"")', "0.0000")
    output_cell(ws, f"D{r}", f'=IF(ISNUMBER(C{r}),C{r}/($B$98*2^($B$61-1)),"")', "0.0000")
    output_cell(ws, f"E{r}", f'=IF(ISNUMBER(D{r}),D{r}/2,"")', "0.0000")
    output_cell(ws, f"F{r}", f'=IF(ISNUMBER(C{r}),C{r}^2/($B$98*2^$B$61),"")', "0.0000")
    output_cell(ws, f"G{r}", f'=IF(ISNUMBER(C{r}),IF(AND(ISNUMBER($B$62),$B$62>=2,B{r}>=$B$62),'
                             f'"gepoold in de fout","in het model"),"")')
    tested = f'AND(G{r}="in het model",ISNUMBER($B$106),N($B$106)>0)'
    output_cell(ws, f"H{r}", f'=IF({tested},F{r}/$B$106,"")', "0.0000")
    output_cell(ws, f"I{r}", f'=IF(ISNUMBER(H{r}),_xlfn.F.DIST.RT(H{r},1,$B$103+$B$105),"")', "0.000000")
    output_cell(ws, f"J{r}", DECISION.format(p=f"I{r}"))
    output_cell(ws, f"K{r}", f'=IF(AND(ISNUMBER(D{r}),ISNUMBER($B$107)),D{r}-2*$B$107,"")', "0.0000")
    output_cell(ws, f"L{r}", f'=IF(AND(ISNUMBER(D{r}),ISNUMBER($B$107)),D{r}+2*$B$107,"")', "0.0000")


def _effects(ws: Worksheet) -> None:
    """Rows 109-141: the table of all 31 effects (only those of the chosen k fill in)."""
    column_titles(ws, 109, ["Effect", "orde", "contrast", "effect = contrast / (n 2^(k−1))",
                            "coëfficiënt = effect / 2 (extra, Dummies; niet te kennen)", "SS = contrast² / (n 2^k)",
                            "in het model of gepoold (pooled)", "F0 = SS / MS_E", "p-waarde", "Besluit bij α",
                            "effect − 2 s.e.", "effect + 2 s.e."])
    for mask in range(1, RUNS):
        _effect_row(ws, mask)
    label(ws, 141, 1, "Effect = gemiddelde bij +1 − gemiddelde bij −1 (DOE p. 48, 66); effect ± 2 s.e. ≈ 95 %-BI: "
                      "bevat het 0, dan niet significant bij 5 % (DOE p. 68). Coëfficiënt = effect / 2, Dummies p. 233 "
                      "(extra, Dummies; niet te kennen).", italic=True)


def _model_table(ws: Worksheet) -> None:
    """Rows 143-149: ANOVA of the model (effects in model) against the error, R² and both R²_adj."""
    ss = f"F{FIRST_EFFECT}:F{effect_row(RUNS - 1)}"
    ok = '$B$99="ja"'
    column_titles(ws, 143, ["Bron (source)", "SS", "df", "MS", "F0", "p-waarde", "Besluit bij α"])
    rows = {
        144: ("Model (alle effecten in het model)", f"SUM({ss})-$B$104", "2^$B$61-1-$B$105"),
        145: ("Fout (error: zuivere fout + gepoold)", "$B$102+$B$104", "$B$103+$B$105"),
        146: ("Totaal", f"SUM({ss})+$B$102", "$B$100-1"),
    }
    for row, (text, sum_sq, df) in rows.items():
        label(ws, row, 1, text)
        output_cell(ws, f"B{row}", f'=IF({ok},{sum_sq},"")', "0.0000")
        output_cell(ws, f"C{row}", f'=IF({ok},{df},"")', "0")
    output_cell(ws, "D144", '=IF(AND(ISNUMBER(B144),N(C144)>0),B144/C144,"")', "0.0000")
    output_cell(ws, "D145", '=IF(ISNUMBER($B$106),$B$106,"")', "0.0000")
    output_cell(ws, "E144", '=IF(AND(ISNUMBER(D144),ISNUMBER(D145),N(D145)>0),D144/D145,"")', "0.0000")
    output_cell(ws, "F144", '=IF(ISNUMBER(E144),_xlfn.F.DIST.RT(E144,C144,C145),"")', "0.000000")
    output_cell(ws, "G144", DECISION.format(p="F144"))
    label(ws, 145, 5, "zoals de Design-Expert-output van de cursus, DOE p. 61", italic=True)
    result_row(ws, 147, "R² = SS_model / SS_totaal", '=IF(AND(ISNUMBER(B146),N(B146)>0),B144/B146,"")', "0.0000",
               "DOE p. 61")
    result_row(ws, 148, "R²_adj = 1 − (1 − R²)(N − 1)/(N − p − 1), p = df van het model",
               '=IF(AND(ISNUMBER(B147),N(C145)>0),1-(1-B147)*C146/C145,"")', "0.0000",
               "zoals de outputs van de cursus (DOE p. 61; Regression p. 22, 57)")
    result_row(ws, 149, "R²_adj zoals gedrukt op Regression p. 56: 1 − (1 − R²)(N − 1)/(N − p − 2)",
               '=IF(AND(ISNUMBER(B147),N(C145)>1),1-(1-B147)*C146/(C145-1),"")', "0.0000",
               "Regression p. 56 (verschilt van de outputs van de cursus)")


def _factorial(ws: Worksheet) -> None:
    """Section 2: 2^k factorial design, effects and ANOVA."""
    section_title(ws, 60, "2. 2^k-factoriële proefopzet (factorial design); standaardvolgorde (standard order): A "
                          "wisselt elke run, B om de 2 runs, C om de 4, …")
    input_row(ws, 61, "k = aantal factoren (2 tot 5)",
              "een fractie 2^(k−p) (fractional factorial): voer ze in als de volledige proefopzet van haar k − p "
              "basisfactoren; elk effect is dan een aliasketen (alias chain) (DOE p. 81-82, 88-90)", "0")
    input_row(ws, 62, "Interacties van deze orde en hoger in de fout poolen (optioneel, 2 tot 5)",
              "één herhaling (single replicate): nodig voor F-toetsen, bv. 3 zoals DOE p. 77", "0")
    label(ws, 63, 1, "Typ elke respons in de rij waarvan de tekens A … E overeenkomen met je tabel (DOE p. 70, 74 "
                     "gebruiken deze volgorde); één kolom per herhaling (replicate).", italic=True)
    _runs(ws)
    _error_estimate(ws)
    _effects(ws)
    _model_table(ws)


def _regression_inputs(ws: Worksheet) -> None:
    """Rows 152-156 and the data block: x0, H0 values, completeness of the pairs, 200 (x, y) rows."""
    section_title(ws, 152, f"3. Enkelvoudige lineaire regressie (simple linear regression) y = b0 + b1 x (paren vanaf "
                           f"rij {FIRST_PAIR}: x in B, y in C)")
    input_row(ws, 153, "x0 voor de gefitte waarde, het BI van de gemiddelde respons en het predictie-interval", "",
              NUMBER)
    input_row(ws, 154, "β1,0 = helling (slope) onder H0", "0 = toets op significantie van de regressie "
                                                          "(Regression p. 30, 33)", NUMBER)
    input_row(ws, 155, "β0,0 = intercept onder H0", "Regression p. 31", NUMBER)
    ws["B154"] = 0
    ws["B155"] = 0
    count = f"COUNT({X_DATA})"
    both = f"SUMPRODUCT(ISNUMBER({X_DATA})*ISNUMBER({Y_DATA}))"
    result_row(ws, 156, "Paren volledig (elke rij heeft x én y, minstens 3 rijen)?",
               f'=IF({count}+COUNT({Y_DATA})=0,"",IF(AND({count}=COUNT({Y_DATA}),{both}={count},{count}>2),"ja",'
               f'"NEE: elke rij heeft x én y nodig, minstens 3 rijen"))')
    column_titles(ws, FIRST_PAIR - 1, ["#", "x", "y"])
    for i in range(PAIRS):
        ws[f"A{FIRST_PAIR + i}"] = i + 1
        ws[f"A{FIRST_PAIR + i}"].font = font()
        for cell in pair_cells(i):
            input_cell(ws, cell)


def _regression_fit(ws: Worksheet) -> None:
    """Rows 157-178: estimates, ANOVA, R², F-test and standard errors."""
    ok = '$B$156="ja"'
    rows = [
        (157, "n = aantal paren", f'=IF({ok},COUNT({X_DATA}),"")', "0", ""),
        (158, "x̄", f'=IF({ok},AVERAGE({X_DATA}),"")', NUMBER, ""),
        (159, "ȳ", f'=IF({ok},AVERAGE({Y_DATA}),"")', NUMBER, ""),
        (160, "S_xx = Σ (x − x̄)²", f'=IF({ok},DEVSQ({X_DATA}),"")', NUMBER, ""),
        (161, "b1 = S_xy / S_xx (helling, slope)", f'=IF(AND({ok},N(B160)>0),SLOPE({Y_DATA},{X_DATA}),"")', NUMBER,
         "Regression p. 17-19"),
        (162, "b0 = ȳ − b1 x̄ (intercept)", f'=IF(ISNUMBER(B161),INTERCEPT({Y_DATA},{X_DATA}),"")', NUMBER, ""),
        (163, "SS_T = Σ (y − ȳ)², totale kwadratensom (sum of squares), df n − 1",
         f'=IF(ISNUMBER(B161),DEVSQ({Y_DATA}),"")', NUMBER, "Regression p. 24-27"),
        (164, "SS_R = Σ (ŷ − ȳ)² = b1² S_xx, df 1", '=IF(ISNUMBER(B161),B161^2*B160,"")', NUMBER, ""),
        (165, "SS_E = Σ (y − ŷ)² = SS_T − SS_R, df n − 2", '=IF(ISNUMBER(B161),B163-B164,"")', NUMBER, ""),
        (166, "σ̂² = MS_E = SS_E / (n − 2)", '=IF(ISNUMBER(B165),B165/(B157-2),"")', NUMBER, "Regression p. 28"),
        (167, "σ̂ = √MS_E (Minitab 'S')", '=IF(ISNUMBER(B166),SQRT(B166),"")', NUMBER, ""),
        (168, "R² = SS_R / SS_T", '=IF(AND(ISNUMBER(B164),N(B163)>0),B164/B163,"")', "0.0000", "Regression p. 27"),
        (169, "R²_adj = 1 − (1 − R²)(n − 1)/(n − 2)", '=IF(ISNUMBER(B168),1-(1-B168)*(B157-1)/(B157-2),"")', "0.0000",
         "zoals de Minitab-output van de cursus (Regression p. 22)"),
        (170, "R²_adj zoals gedrukt op Regression p. 56: 1 − (1 − R²)(n − 1)/(n − 3)",
         '=IF(AND(ISNUMBER(B168),N(B157)>3),1-(1-B168)*(B157-1)/(B157-3),"")', "0.0000",
         "Regression p. 56 met k = 1 (verschilt van de outputs van de cursus)"),
        (171, "F0 = MS_R / MS_E, df (1, n − 2)", '=IF(AND(ISNUMBER(B166),N(B166)>0),B164/B166,"")', "0.0000",
         "Regression p. 33"),
        (172, "p-waarde van F0 (H0: β1 = 0)", '=IF(ISNUMBER(B171),_xlfn.F.DIST.RT(B171,1,B157-2),"")', "0.000000",
         ""),
        (174, "s.e.(b1) = √(MS_E / S_xx)", '=IF(ISNUMBER(B166),SQRT(B166/B160),"")', NUMBER, "Regression p. 29-30"),
        (175, "s.e.(b0) = √(MS_E (1/n + x̄²/S_xx))", '=IF(ISNUMBER(B166),SQRT(B166*(1/B157+B158^2/B160)),"")', NUMBER,
         "Regression p. 29, 31"),
        (176, "ŷ0 = b0 + b1 x0", '=IF(AND(ISNUMBER(B161),ISNUMBER($B$153)),B162+B161*$B$153,"")', NUMBER,
         "Regression p. 35"),
        (177, "s.e.(ŷ0) = √(MS_E (1/n + (x0 − x̄)²/S_xx))",
         '=IF(ISNUMBER(B176),SQRT(B166*(1/B157+($B$153-B158)^2/B160)),"")', NUMBER, "Regression p. 36"),
        (178, "s.e.(e0) = √(MS_E (1 + 1/n + (x0 − x̄)²/S_xx))",
         '=IF(ISNUMBER(B176),SQRT(B166*(1+1/B157+($B$153-B158)^2/B160)),"")', NUMBER, "Regression p. 38"),
    ]
    for row, text, formula, fmt, source in rows:
        result_row(ws, row, text, formula, fmt, source)
    output_cell(ws, "D172", DECISION.format(p="B172"))


def _regression_tests(ws: Worksheet) -> None:
    """Rows 180-182: t-tests of H0: β1 = β1,0 and H0: β0 = β0,0, all three alternatives (decision 6)."""
    column_titles(ws, 180, ["t-toets (t-test), df n − 2 (Regression p. 30-31)", "schatting", "H0-waarde", "t0",
                            "p (HA: ≠)", "p (HA: >)", "p (HA: <)", "Besluit (≠)", "Besluit (>)", "Besluit (<)"])
    df = "$B$157-2"
    for key, (text, estimate, h0, se) in {"b1": ("helling β1", "B161", "$B$154", "B174"),
                                          "b0": ("intercept β0", "B162", "$B$155", "B175")}.items():
        r = T_TESTS[key]
        label(ws, r, 1, text)
        output_cell(ws, f"B{r}", f'=IF(ISNUMBER({estimate}),{estimate},"")', NUMBER)
        output_cell(ws, f"C{r}", f"=N({h0})", NUMBER)
        output_cell(ws, f"D{r}", f'=IF(AND(ISNUMBER({se}),N({se})>0),(B{r}-C{r})/{se},"")', "0.0000")
        output_cell(ws, f"E{r}", f'=IF(ISNUMBER(D{r}),_xlfn.T.DIST.2T(ABS(D{r}),{df}),"")', "0.000000")
        output_cell(ws, f"F{r}", f'=IF(ISNUMBER(D{r}),_xlfn.T.DIST.RT(D{r},{df}),"")', "0.000000")
        output_cell(ws, f"G{r}", f'=IF(ISNUMBER(D{r}),_xlfn.T.DIST(D{r},{df},TRUE),"")', "0.000000")
        for p, decision in zip("EFG", "HIJ"):
            output_cell(ws, f"{decision}{r}", DECISION.format(p=f"{p}{r}"))


def _regression_intervals(ws: Worksheet) -> None:
    """Rows 184-188: CIs of β1, β0, the mean response at x0 and the prediction interval, one- and two-sided."""
    column_titles(ws, 184, ["Betrouwbaarheidsinterval (confidence interval, BI) 1 − α, t met n − 2 df", "centrum",
                            "s.e.", "tweezijdig: van", "tot", "alleen ondergrens (minstens …)",
                            "alleen bovengrens (hoogstens …)", "Bron in de cursus"])
    two, one = f"_xlfn.T.INV(1-{ALPHA}/2,$B$157-2)", f"_xlfn.T.INV(1-{ALPHA},$B$157-2)"
    spec = {
        "b1": ("BI voor de helling β1", "B161", "B174", "Regression p. 34"),
        "b0": ("BI voor het intercept β0", "B162", "B175", "Regression p. 34"),
        "mean": ("BI voor de gemiddelde respons (mean response) bij x0", "B176", "B177", "Regression p. 36"),
        "prediction": ("Predictie-interval (prediction interval, PI) voor een nieuwe y bij x0", "B176", "B178",
                       "Regression p. 38"),
    }
    for key, (text, centre, se, source) in spec.items():
        r = INTERVALS[key]
        label(ws, r, 1, text)
        output_cell(ws, f"B{r}", f'=IF(AND(ISNUMBER({centre}),ISNUMBER({se})),{centre},"")', NUMBER)
        output_cell(ws, f"C{r}", f'=IF(ISNUMBER(B{r}),{se},"")', NUMBER)
        output_cell(ws, f"D{r}", f'=IF(ISNUMBER(B{r}),B{r}-{two}*C{r},"")', NUMBER)
        output_cell(ws, f"E{r}", f'=IF(ISNUMBER(B{r}),B{r}+{two}*C{r},"")', NUMBER)
        output_cell(ws, f"F{r}", f'=IF(ISNUMBER(B{r}),B{r}-{one}*C{r},"")', NUMBER)
        output_cell(ws, f"G{r}", f'=IF(ISNUMBER(B{r}),B{r}+{one}*C{r},"")', NUMBER)
        label(ws, r, 8, source, italic=True)


def _regression(ws: Worksheet) -> None:
    """Section 3: simple linear regression of y on x."""
    _regression_inputs(ws)
    _regression_fit(ws)
    _regression_tests(ws)
    _regression_intervals(ws)
    label(ws, 189, 1, "Meervoudige regressie (multiple regression, Regression p. 46-61) staat niet op dit blad.",
          italic=True)


def _validation(ws: Worksheet) -> None:
    """k and the pooling order: whole numbers 2 to 5; α a fraction."""
    whole = DataValidation(type="whole", operator="between", formula1="2", formula2="5", allow_blank=True,
                           showErrorMessage=True, errorTitle="k of orde voor poolen",
                           error="Een geheel getal van 2 tot 5.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0.0000001", formula2="0.9999999",
                              allow_blank=True, showErrorMessage=True, errorTitle="α", error="α ligt tussen 0 en 1.")
    for rule, cells in ((whole, ("B61", "B62")), (fraction, ("B9",))):
        ws.add_data_validation(rule)
        for cell in cells:
            rule.add(cell)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the ANOVA, DOE and regression calculator."""
    write_header(ws, HEADER)
    _settings(ws)
    _one_way(ws)
    _factorial(ws)
    _regression(ws)
    _validation(ws)
    ws.column_dimensions["A"].width = 58
    for column in range(2, SIGN_FIRST_COLUMN - 1):
        ws.column_dimensions[get_column_letter(column)].width = 14
    for column in range(SIGN_FIRST_COLUMN, SIGN_FIRST_COLUMN + RUNS - 1):
        ws.column_dimensions[get_column_letter(column)].width = 6
