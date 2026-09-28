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

SHEET = "ANOVA DOE regression"

HEADER = HeaderBlock(
    tool="One-way ANOVA, 2^k factorial effects and ANOVA (k = 2 to 5), simple linear regression",
    source="source/course/Les 3/20260605_de vuyst_BB_DOE.pdf p. 3-15, 46-92; 20260605_de vuyst_BB_Regression.pdf "
           "p. 16-38, 56-57; Les 4/Six Sigma For Dummies.pdf p. 222-233",
    convention="α input prefilled 0.05 (decision 5); regression CIs and t-tests one- and two-sided side by side "
               "(decision 6); factors coded −1/+1 in standard order (DOE p. 46, 70, 74); single replicate: pool "
               "interactions of a chosen order and higher into the error (DOE p. 72, 77); R²_adj shown both ways.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S05-WE01, S05-WE02, S05-WE05 to S05-WE09, S05-WE17, "
                  "S05-WE18, S08-WE16; printed values that disagree are listed in build/README.md",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="One-way ANOVA table; effects, coefficients, sums of squares, F-tests and ±2 s.e. intervals of a 2^k "
            "factorial with pure error from replicates and/or pooled higher-order interactions, its model ANOVA and "
            "R²; simple linear regression with ANOVA, R², t-tests, CIs of β0 and β1, and the CI of the mean response "
            "and prediction interval at x0.",
    inputs="α; ANOVA: up to 8 groups of up to 30 values (one column per group); factorial: k, optional pooling order, "
           "up to 4 replicate responses per run in standard order; regression: up to 200 (x, y) pairs, x0 and the H0 "
           "values of β1 and β0.",
    audit="not needed (course worked examples exist)",
    disagreements=(
        "DOE p. 50 (S05-WE05): '[AB] = 5,78 – 4,92 = 0,857'; the exact effect is 0.8583 (means 5.7767 and 4.9183).",
        "DOE p. 71 (S05-WE08): SS_ABC (and MS) printed 5.5625; the data on p. 70 give contrast 9 and SS 81/16 = "
        "5.0625, which the printed F0 2.08, P 0.19 and total 92.9375 also imply. The printed P of A, 2.54 × 10^-3, is "
        "2.534 × 10^-3 for F0 18.69 on F(1, 8).",
        "DOE p. 53 (S05-WE06): 'AB = (52 + 20)/2 − (30 + 40)/2 = −1'; that expression equals +1, which the sheet "
        "gives.",
        "Regression p. 56 prints R²_adj = 1 − (1 − R²)(n − 1)/(n − k − 2); the course's own outputs use n − k − 1 "
        "(Regression p. 22 Minitab R-Sq(adj) 87.1 %; DOE p. 61 Adj R-Squared 0.8666; σ̂ on Regression p. 57). The "
        "sheet shows both, labelled.",
        "Inventory transcription, not the course: worked_examples.json S05-WE09 and the constants CSV give P 0.757016 "
        "(C) and 0.741315 (A:B); DOE p. 77 prints 0.757069 and 0.741351, which the sheet gives. The locked oracle "
        "was not edited.",
        "Regression p. 21 (S05-WE17): the fitted line 'ŷ = 74.20 + 14.97x' of Figure 11-4 differs from the least "
        "squares values 74.283 and 14.947 of the Minitab output on p. 22, which the sheet reproduces.",
    ),
)

ALPHA = "$B$9"
NUMBER = "0.000000"
DECISION = '=IF(ISNUMBER({p}),IF({p}<' + ALPHA + ',"reject H0","do not reject H0"),"")'

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
    section_title(ws, 8, "Settings")
    input_row(ws, 9, "Significance α (confidence = 1 − α)",
              "course has no default; most course examples use 5 %; use the value the question gives", "0.0000")
    ws["B9"] = 0.05


def _group_statistics(ws: Worksheet) -> None:
    """Rows 45-49: per group n, mean, s and the two terms of SS_Treatment and SS_Error."""
    for row, text in ((45, "n_i"), (46, "mean Ȳ_i"), (47, "standard deviation s_i"), (48, "n_i (Ȳ_i − Ȳ)²"),
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
    section_title(ws, 11, "1. One-way ANOVA: one column per group (factor level), its values below (rows 14-43)")
    label(ws, 12, 1, "Row 13: a name for each group if you like. Groups may have different sizes.", italic=True)
    label(ws, 13, 1, "group name", bold=True)
    for letter in GROUP_COLUMNS:
        input_cell(ws, f"{letter}13")
        for row in range(FIRST_GROUP_ROW, LAST_GROUP_ROW + 1):
            input_cell(ws, f"{letter}{row}")
    _group_statistics(ws)
    everything = f"B{FIRST_GROUP_ROW}:I{LAST_GROUP_ROW}"
    ok = "AND(ISNUMBER($B$57),$B$57>=2,SUM(B45:I45)>$B$57)"  # at least 2 groups and error df > 0
    column_titles(ws, 51, ["Source", "SS", "df", "MS", "F0", "p-value", "F crit at α", "Decision at α"])
    rows = {
        52: ("Treatments (between groups)", "SUM(B48:I48)", "$B$57-1"),
        53: ("Error (within groups)", "SUM(B49:I49)", "SUM(B45:I45)-$B$57"),
        54: ("Total", f"DEVSQ({everything})", "SUM(B45:I45)-1"),
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
    label(ws, 53, 5, "H0: all group means equal (DOE p. 7-8, Table 4.6)", italic=True)
    result_row(ws, 55, "grand mean Ȳ", f'=IF(COUNT({everything})>0,AVERAGE({everything}),"")', NUMBER)
    result_row(ws, 56, "pooled standard deviation √MS_E", '=IF(ISNUMBER(D53),SQRT(D53),"")', NUMBER)
    result_row(ws, 57, "a = number of groups", '=IF(COUNT(B45:I45)>0,COUNT(B45:I45),"")', "0")


def _runs(ws: Worksheet) -> None:
    """Rows 64-96: the 32 standard-order runs, their replicate inputs and per-run summaries."""
    column_titles(ws, 64, ["Run", *FACTORS, "y rep 1", "y rep 2", "y rep 3", "y rep 4", "n", "run mean", "run sum",
                           "Σ (y − run mean)²", "in design (1/0)"])
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
    label(ws, 63, SIGN_FIRST_COLUMN, "Sign (−1/+1) of every effect in every run: used by the contrast formulas",
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
    result_row(ws, 98, "n = replicates per run", f'=IF(COUNT({n_col})>0,MAX({n_col}),"")', "0")
    result_row(ws, 99, "Complete design (runs 1 … 2^k each have n responses)?",
               f'=IF(COUNT({n_col})=0,"",IF(AND(COUNT({n_col})=SUM({in_design}),MIN({n_col})=MAX({n_col})),"yes",'
               f'"NO: fill runs 1 … 2^k, each with the same number of replicates"))')
    ok = '$B$99="yes"'
    pooling = "AND(ISNUMBER($B$62),$B$62>=2)"
    ss, order = f"F{FIRST_EFFECT}:F{effect_row(RUNS - 1)}", f"B{FIRST_EFFECT}:B{effect_row(RUNS - 1)}"
    result_row(ws, 100, "N = 2^k · n observations", f'=IF({ok},2^$B$61*$B$98,"")', "0")
    result_row(ws, 101, "grand mean = β0", f'=IF({ok},SUM(M{first}:M{last})/$B$100,"")', NUMBER, "Dummies p. 233")
    result_row(ws, 102, "SS pure error (between replicates)", f'=IF({ok},SUM(N{first}:N{last}),"")', "0.0000")
    result_row(ws, 103, "df pure error = 2^k (n − 1)", f'=IF({ok},2^$B$61*($B$98-1),"")', "0")
    result_row(ws, 104, "SS pooled interactions (order ≥ B62)",
               f'=IF({ok},IF({pooling},SUMIFS({ss},{order},">="&$B$62),0),"")', "0.0000", "DOE p. 72, 77")
    result_row(ws, 105, "df pooled interactions",
               f'=IF({ok},IF({pooling},COUNTIFS({order},">="&$B$62,{ss},">=0"),0),"")', "0")
    result_row(ws, 106, "σ̂² = MS_E = (SS pure error + SS pooled) / (df + df)",
               f'=IF(AND({ok},N($B$103)+N($B$105)>0),($B$102+$B$104)/($B$103+$B$105),"")', NUMBER)
    result_row(ws, 107, "s.e.(effect) = √(σ̂² / (n 2^(k−2)))",
               '=IF(ISNUMBER($B$106),SQRT($B$106/($B$98*2^($B$61-2))),"")', NUMBER, "DOE p. 67")


def _effect_row(ws: Worksheet, mask: int) -> None:
    """One row of the effects table: contrast, effect, coefficient, SS, F-test and effect ± 2 s.e."""
    r, first, last = effect_row(mask), run_row(0), run_row(RUNS - 1)
    signs = get_column_letter(SIGN_FIRST_COLUMN + mask - 1)
    ws[f"A{r}"] = effect_name(mask)
    ws[f"A{r}"].font = font(bold=True)
    ws[f"B{r}"] = bin(mask).count("1")
    ws[f"B{r}"].font = font()
    in_design = f'AND($B$99="yes",{mask}<2^$B$61)'
    output_cell(ws, f"C{r}", f'=IF({in_design},SUMPRODUCT({signs}{first}:{signs}{last},M{first}:M{last}),"")', "0.0000")
    output_cell(ws, f"D{r}", f'=IF(ISNUMBER(C{r}),C{r}/($B$98*2^($B$61-1)),"")', "0.0000")
    output_cell(ws, f"E{r}", f'=IF(ISNUMBER(D{r}),D{r}/2,"")', "0.0000")
    output_cell(ws, f"F{r}", f'=IF(ISNUMBER(C{r}),C{r}^2/($B$98*2^$B$61),"")', "0.0000")
    output_cell(ws, f"G{r}", f'=IF(ISNUMBER(C{r}),IF(AND(ISNUMBER($B$62),$B$62>=2,B{r}>=$B$62),'
                             f'"pooled into error","in model"),"")')
    tested = f'AND(G{r}="in model",ISNUMBER($B$106),N($B$106)>0)'
    output_cell(ws, f"H{r}", f'=IF({tested},F{r}/$B$106,"")', "0.0000")
    output_cell(ws, f"I{r}", f'=IF(ISNUMBER(H{r}),_xlfn.F.DIST.RT(H{r},1,$B$103+$B$105),"")', "0.000000")
    output_cell(ws, f"J{r}", DECISION.format(p=f"I{r}"))
    output_cell(ws, f"K{r}", f'=IF(AND(ISNUMBER(D{r}),ISNUMBER($B$107)),D{r}-2*$B$107,"")', "0.0000")
    output_cell(ws, f"L{r}", f'=IF(AND(ISNUMBER(D{r}),ISNUMBER($B$107)),D{r}+2*$B$107,"")', "0.0000")


def _effects(ws: Worksheet) -> None:
    """Rows 109-141: the table of all 31 effects (only those of the chosen k fill in)."""
    column_titles(ws, 109, ["Effect", "order", "contrast", "effect = contrast / (n 2^(k−1))", "coefficient = effect / 2",
                            "SS = contrast² / (n 2^k)", "in model or pooled", "F0 = SS / MS_E", "p-value",
                            "Decision at α", "effect − 2 s.e.", "effect + 2 s.e."])
    for mask in range(1, RUNS):
        _effect_row(ws, mask)
    label(ws, 141, 1, "Effect = mean at +1 − mean at −1 (DOE p. 48, 66); coefficient = effect / 2 (Dummies p. 233); "
                      "effect ± 2 s.e. ≈ 95 % CI: contains 0 = not significant at 5 % (DOE p. 68).", italic=True)


def _model_table(ws: Worksheet) -> None:
    """Rows 143-149: ANOVA of the model (effects in model) against the error, R² and both R²_adj."""
    ss = f"F{FIRST_EFFECT}:F{effect_row(RUNS - 1)}"
    ok = '$B$99="yes"'
    column_titles(ws, 143, ["Source", "SS", "df", "MS", "F0", "p-value", "Decision at α"])
    rows = {
        144: ("Model (all effects in model)", f"SUM({ss})-$B$104", "2^$B$61-1-$B$105"),
        145: ("Error (pure error + pooled)", "$B$102+$B$104", "$B$103+$B$105"),
        146: ("Total", f"SUM({ss})+$B$102", "$B$100-1"),
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
    label(ws, 145, 5, "as the course's Design-Expert output, DOE p. 61", italic=True)
    result_row(ws, 147, "R² = SS_model / SS_total", '=IF(AND(ISNUMBER(B146),N(B146)>0),B144/B146,"")', "0.0000",
               "DOE p. 61")
    result_row(ws, 148, "R²_adj = 1 − (1 − R²)(N − 1)/(N − p − 1), p = model df",
               '=IF(AND(ISNUMBER(B147),N(C145)>0),1-(1-B147)*C146/C145,"")', "0.0000",
               "as the course's outputs (DOE p. 61; Regression p. 22, 57)")
    result_row(ws, 149, "R²_adj as printed on Regression p. 56: 1 − (1 − R²)(N − 1)/(N − p − 2)",
               '=IF(AND(ISNUMBER(B147),N(C145)>1),1-(1-B147)*C146/(C145-1),"")', "0.0000",
               "Regression p. 56 (differs from the course's outputs)")


def _factorial(ws: Worksheet) -> None:
    """Section 2: 2^k factorial design, effects and ANOVA."""
    section_title(ws, 60, "2. 2^k factorial design (standard order: A changes every run, B every 2 runs, C every 4, …)")
    input_row(ws, 61, "k = number of factors (2 to 5)",
              "a fraction 2^(k−p): enter it as the full design of its k − p base factors; each effect is then an "
              "alias chain (DOE p. 81-82, 88-90)", "0")
    input_row(ws, 62, "Pool interactions of this order and higher into the error (optional, 2 to 5)",
              "single replicate: needed for F-tests, e.g. 3 as DOE p. 77", "0")
    label(ws, 63, 1, "Type each response in the row whose A … E signs match your table (DOE p. 70, 74 use this order); "
                     "one column per replicate.", italic=True)
    _runs(ws)
    _error_estimate(ws)
    _effects(ws)
    _model_table(ws)


def _regression_inputs(ws: Worksheet) -> None:
    """Rows 152-156 and the data block: x0, H0 values, completeness of the pairs, 200 (x, y) rows."""
    section_title(ws, 152, f"3. Simple linear regression y = b0 + b1 x (pairs from row {FIRST_PAIR}: x in B, y in C)")
    input_row(ws, 153, "x0 for the fitted value, CI of the mean response and prediction interval", "", NUMBER)
    input_row(ws, 154, "β1,0 = slope under H0", "0 = test of significance of regression (Regression p. 30, 33)", NUMBER)
    input_row(ws, 155, "β0,0 = intercept under H0", "Regression p. 31", NUMBER)
    ws["B154"] = 0
    ws["B155"] = 0
    count = f"COUNT({X_DATA})"
    both = f"SUMPRODUCT(ISNUMBER({X_DATA})*ISNUMBER({Y_DATA}))"
    result_row(ws, 156, "Pairs complete (every row has both x and y, at least 3 rows)?",
               f'=IF({count}+COUNT({Y_DATA})=0,"",IF(AND({count}=COUNT({Y_DATA}),{both}={count},{count}>2),"yes",'
               f'"NO: every row needs both x and y, at least 3 rows"))')
    column_titles(ws, FIRST_PAIR - 1, ["#", "x", "y"])
    for i in range(PAIRS):
        ws[f"A{FIRST_PAIR + i}"] = i + 1
        ws[f"A{FIRST_PAIR + i}"].font = font()
        for cell in pair_cells(i):
            input_cell(ws, cell)


def _regression_fit(ws: Worksheet) -> None:
    """Rows 157-178: estimates, ANOVA, R², F-test and standard errors."""
    ok = '$B$156="yes"'
    rows = [
        (157, "n = number of pairs", f'=IF({ok},COUNT({X_DATA}),"")', "0", ""),
        (158, "x̄", f'=IF({ok},AVERAGE({X_DATA}),"")', NUMBER, ""),
        (159, "ȳ", f'=IF({ok},AVERAGE({Y_DATA}),"")', NUMBER, ""),
        (160, "S_xx = Σ (x − x̄)²", f'=IF({ok},DEVSQ({X_DATA}),"")', NUMBER, ""),
        (161, "b1 = S_xy / S_xx (slope)", f'=IF(AND({ok},N(B160)>0),SLOPE({Y_DATA},{X_DATA}),"")', NUMBER,
         "Regression p. 17-19"),
        (162, "b0 = ȳ − b1 x̄ (intercept)", f'=IF(ISNUMBER(B161),INTERCEPT({Y_DATA},{X_DATA}),"")', NUMBER, ""),
        (163, "SS_T = Σ (y − ȳ)², df n − 1", f'=IF(ISNUMBER(B161),DEVSQ({Y_DATA}),"")', NUMBER, "Regression p. 24-27"),
        (164, "SS_R = Σ (ŷ − ȳ)² = b1² S_xx, df 1", '=IF(ISNUMBER(B161),B161^2*B160,"")', NUMBER, ""),
        (165, "SS_E = Σ (y − ŷ)² = SS_T − SS_R, df n − 2", '=IF(ISNUMBER(B161),B163-B164,"")', NUMBER, ""),
        (166, "σ̂² = MS_E = SS_E / (n − 2)", '=IF(ISNUMBER(B165),B165/(B157-2),"")', NUMBER, "Regression p. 28"),
        (167, "σ̂ = √MS_E (Minitab 'S')", '=IF(ISNUMBER(B166),SQRT(B166),"")', NUMBER, ""),
        (168, "R² = SS_R / SS_T", '=IF(AND(ISNUMBER(B164),N(B163)>0),B164/B163,"")', "0.0000", "Regression p. 27"),
        (169, "R²_adj = 1 − (1 − R²)(n − 1)/(n − 2)", '=IF(ISNUMBER(B168),1-(1-B168)*(B157-1)/(B157-2),"")', "0.0000",
         "as the course's Minitab output (Regression p. 22)"),
        (170, "R²_adj as printed on Regression p. 56: 1 − (1 − R²)(n − 1)/(n − 3)",
         '=IF(AND(ISNUMBER(B168),N(B157)>3),1-(1-B168)*(B157-1)/(B157-3),"")', "0.0000",
         "Regression p. 56 with k = 1 (differs from the course's outputs)"),
        (171, "F0 = MS_R / MS_E, df (1, n − 2)", '=IF(AND(ISNUMBER(B166),N(B166)>0),B164/B166,"")', "0.0000",
         "Regression p. 33"),
        (172, "p-value of F0 (H0: β1 = 0)", '=IF(ISNUMBER(B171),_xlfn.F.DIST.RT(B171,1,B157-2),"")', "0.000000", ""),
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
    column_titles(ws, 180, ["t-test, df n − 2 (Regression p. 30-31)", "estimate", "H0 value", "t0",
                            "p (HA: ≠)", "p (HA: >)", "p (HA: <)", "Decision (≠)", "Decision (>)", "Decision (<)"])
    df = "$B$157-2"
    for key, (text, estimate, h0, se) in {"b1": ("slope β1", "B161", "$B$154", "B174"),
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
    column_titles(ws, 184, ["Interval (1 − α), t with n − 2 df", "centre", "s.e.", "two-sided: from", "to",
                            "lower bound only (at least …)", "upper bound only (at most …)", "Course source"])
    two, one = f"_xlfn.T.INV(1-{ALPHA}/2,$B$157-2)", f"_xlfn.T.INV(1-{ALPHA},$B$157-2)"
    spec = {
        "b1": ("CI for the slope β1", "B161", "B174", "Regression p. 34"),
        "b0": ("CI for the intercept β0", "B162", "B175", "Regression p. 34"),
        "mean": ("CI for the mean response at x0", "B176", "B177", "Regression p. 36"),
        "prediction": ("Prediction interval for a new y at x0", "B176", "B178", "Regression p. 38"),
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
    label(ws, 189, 1, "Multiple regression (Regression p. 46-61) is not on this sheet.", italic=True)


def _validation(ws: Worksheet) -> None:
    """k and the pooling order: whole numbers 2 to 5; α a fraction."""
    whole = DataValidation(type="whole", operator="between", formula1="2", formula2="5", allow_blank=True,
                           showErrorMessage=True, errorTitle="k or pooling order", error="A whole number from 2 to 5.")
    fraction = DataValidation(type="decimal", operator="between", formula1="0.0000001", formula2="0.9999999",
                              allow_blank=True, showErrorMessage=True, errorTitle="α", error="α is between 0 and 1.")
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
