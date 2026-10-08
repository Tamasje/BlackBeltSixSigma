"""Tests for bbtools.sheet_anova, sheet_doe and sheet_regression, evaluated by LibreOffice headless.

Expected values: course worked examples S05-WE01, S05-WE02 (one-way ANOVA), S05-WE05 to S05-WE09 (2^k effects and
ANOVA), S08-WE16 (Dummies 2^3 effects and coefficients), S05-WE17, S05-WE18 (regression), all at printed precision;
data from the course tables in inventory/constants (each row cites its source page). Independent cross-checks:
statsmodels OLS / anova_lm for random data. Printed values that disagree are strict xfails citing the page.
"""
from __future__ import annotations

import csv
import random
import re
from collections.abc import Callable
from typing import Any

import pandas as pd
import pytest
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from bbtools.constants import CONSTANTS_DIR
from bbtools.printed import agrees_at_printed_precision
from bbtools import sheet_anova, sheet_doe, sheet_regression
from bbtools.sheet_anova import ANOVA_ROWS, GROUP_COLUMNS, GROUP_STATS, group_cell
from bbtools.sheet_doe import FACTORS, MODEL_ROWS, effect_name, effect_row, response_cell, sign
from bbtools.sheet_regression import INTERVALS, T_TESTS, pair_cells

pytestmark = pytest.mark.libreoffice

# the three calculators share α in B9; their other cells have distinct names
INPUTS = {**sheet_anova.INPUTS, **sheet_doe.INPUTS, **sheet_regression.INPUTS}
RESULTS = {**sheet_anova.RESULTS, **sheet_doe.RESULTS, **sheet_regression.RESULTS}

Evaluate = Callable[[str, dict[str, Any]], Any]
Printed = Callable[[str, str, str, str], str]
TOKEN = re.compile(r"(\w+)([=<])(\S+)")


def course_rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table extracted to inventory/constants/<stem>.csv."""
    with (CONSTANTS_DIR / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def anova_terms(text: str) -> dict[str, dict[str, str]]:
    """Parse an oracle ANOVA string such as 'A SS=45.5625 df=1 F0=18.69 P=0.07; B …' into {term: {key: printed}}.

    A '<' relation (P<0.0001) keeps its sign in the value ('<0.0001').
    """
    terms = {}
    for part in text.split(";"):
        first = TOKEN.search(part)
        name = part[:first.start()].strip().rstrip(":")
        terms[name] = {m.group(1): m.group(3) if m.group(2) == "=" else "<" + m.group(3) for m in TOKEN.finditer(part)}
    return terms


def agrees_scientific(computed: float, printed: str) -> bool:
    """Printed-precision check of a number printed as '3.59 x 10^-6', '2.54x10^-3', '9.12794E-06' or '3.903e-05'."""
    match = re.fullmatch(r"\s*([0-9.]+)\s*(?:x\s*10\^|[eE])([-+]?\d+)\s*", printed)
    assert match, printed
    return agrees_at_printed_precision(computed / 10 ** int(match.group(2)), match.group(1))


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


# --- input builders -------------------------------------------------------------------------------------------


def one_way_cells(groups: list[list[float]], alpha: float | None = None) -> dict[str, Any]:
    """Input cells of a one-way ANOVA: one list of values per group."""
    cells = {group_cell(g, i): y for g, values in enumerate(groups) for i, y in enumerate(values)}
    return cells | ({INPUTS["alpha"]: alpha} if alpha is not None else {})


def factorial_cells(k: int, runs: list[list[float]], pool: int | None = None) -> dict[str, Any]:
    """Input cells of a 2^k design: runs[r] = the replicate responses of standard-order run r."""
    cells: dict[str, Any] = {INPUTS["k"]: k}
    if pool is not None:
        cells[INPUTS["pool_order"]] = pool
    cells |= {response_cell(r, i): y for r, ys in enumerate(runs) for i, y in enumerate(ys)}
    return cells


def regression_cells(xs: list[float], ys: list[float], x0: float | None = None) -> dict[str, Any]:
    """Input cells of a simple regression: pairs (x, y) and optionally x0."""
    cells: dict[str, Any] = {}
    for i, (x, y) in enumerate(zip(xs, ys)):
        cell_x, cell_y = pair_cells(i)
        cells[cell_x], cells[cell_y] = x, y
    return cells | ({INPUTS["x0"]: x0} if x0 is not None else {})


def effect(ws: Any, name: str, column: str) -> Any:
    """Cached value of column `column` of the effects-table row of effect `name` ('A', 'AB', …)."""
    mask = sum(1 << FACTORS.index(letter) for letter in name)
    return ws[f"{column}{effect_row(mask)}"].value


# --- one-way ANOVA --------------------------------------------------------------------------------------------


def paper_strength() -> list[list[float]]:
    """DOE p. 4 Table 4.4: tensile strength at 5, 10, 15, 20 % hardwood, 6 observations each."""
    rows = [r for r in course_rows("S05_table_4_4_tensile_strength_of_paper_psi") if r["Obs1"]]
    return [[float(r[f"Obs{i}"]) for i in range(1, 7)] for r in rows]


def test_one_way_anova_paper_strength_s05_we01(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- DOE p. 9-10: α = 0.01
    stated = oracle["S05-WE01"]["stated_answers"]
    ws = evaluate(sheet_anova.SHEET, one_way_cells(paper_strength(), alpha=float(oracle["S05-WE01"]["given"]["alpha"])))
    tr, err, tot = ANOVA_ROWS["treatments"], ANOVA_ROWS["error"], ANOVA_ROWS["total"]
    # act / assert -- the ANOVA table at printed precision
    for cell, key in ((f"B{tot}", "SS_T"), (f"B{tr}", "SS_Treatments"), (f"B{err}", "SS_E"),
                      (f"D{tr}", "MS_Treatments"), (f"D{err}", "MS_E"), (f"E{tr}", "F0"),
                      (f"G{tr}", "F_crit(0.01,3,20)")):
        assert agrees_at_printed_precision(ws[cell].value, stated[key]), (key, ws[cell].value)
    assert [ws[f"C{r}"].value for r in (tr, err, tot)] == [3, 20, 23]
    assert agrees_scientific(ws[f"F{tr}"].value, printed("S05-WE01", "stated_answers", "P_value", "3.59 x 10^-6"))
    assert stated["conclusion"].startswith("reject H0") and ws[f"H{tr}"].value == "verwerp H0"


def test_one_way_group_statistics_s05_we01(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- DOE p. 10 Minitab output: level means, StDev and pooled StDev
    text = oracle["S05-WE01"]["stated_answers"]["level_means_StDev"]
    levels = re.findall(r"level\d+: mean ([\d.]+) StDev ([\d.]+)", text)
    pooled = re.search(r"Pooled StDev ([\d.]+)", text).group(1)
    ws = evaluate(sheet_anova.SHEET, one_way_cells(paper_strength()))
    # act / assert
    assert len(levels) == 4
    for letter, (mean, sd) in zip(GROUP_COLUMNS, levels):
        assert agrees_at_printed_precision(ws[f"{letter}{GROUP_STATS['mean']}"].value, mean)
        assert agrees_at_printed_precision(ws[f"{letter}{GROUP_STATS['sd']}"].value, sd)
    assert agrees_at_printed_precision(value(ws, "pooled_sd"), pooled)


def test_one_way_anova_fibre_strength_s05_we02(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- DOE p. 14-15 (Table 3-1, Excel ANOVA output), α 0.05 as prefilled
    stated = oracle["S05-WE02"]["stated_answers"]
    rows = [r for r in course_rows("S05_table_3_1_data_in_lb_in_2_from_the_tensile_strength_experime") if r["Obs1"]]
    ws = evaluate(sheet_anova.SHEET, one_way_cells([[float(r[f"Obs{i}"]) for i in range(1, 6)] for r in rows]))
    tr, err, tot = ANOVA_ROWS["treatments"], ANOVA_ROWS["error"], ANOVA_ROWS["total"]
    # act / assert
    for cell, key in ((f"B{tr}", "SS_between_groups"), (f"D{tr}", "MS_between"), (f"E{tr}", "F"),
                      (f"G{tr}", "F_crit"), (f"B{err}", "SS_within_groups"), (f"D{err}", "MS_within"),
                      (f"B{tot}", "SS_total")):
        assert agrees_at_printed_precision(ws[cell].value, stated[key]), (key, ws[cell].value)
    assert [ws[f"C{r}"].value for r in (tr, err, tot)] == [int(stated[k]) for k in ("df_between", "df_within", "df_total")]
    assert agrees_scientific(ws[f"F{tr}"].value, printed("S05-WE02", "stated_answers", "P_value", "9.12794E-06"))
    assert agrees_at_printed_precision(value(ws, "grand_mean"), printed("S05-WE02", "stated_answers", "group_means", "15.04"))


@pytest.mark.parametrize("seed", [1, 2])
def test_one_way_anova_matches_statsmodels(seed: int, evaluate: Evaluate) -> None:
    # arrange -- random unbalanced groups
    rng = random.Random(seed)
    groups = [[rng.gauss(50 + 3 * g, 4) for _ in range(rng.randint(2, 30))] for g in range(rng.randint(2, 8))]
    frame = pd.DataFrame([{"y": y, "g": g} for g, ys in enumerate(groups) for y in ys])
    table = sm.stats.anova_lm(smf.ols("y ~ C(g)", frame).fit(), typ=1)
    alpha = rng.choice([0.01, 0.05, 0.10])
    ws = evaluate(sheet_anova.SHEET, one_way_cells(groups, alpha))
    tr, err = ANOVA_ROWS["treatments"], ANOVA_ROWS["error"]
    # act / assert -- rel=1e-9: same sums of squares by QR least squares
    assert ws[f"B{tr}"].value == pytest.approx(table.loc["C(g)", "sum_sq"], rel=1e-9)
    assert ws[f"B{err}"].value == pytest.approx(table.loc["Residual", "sum_sq"], rel=1e-9)
    assert ws[f"C{err}"].value == table.loc["Residual", "df"]
    assert ws[f"E{tr}"].value == pytest.approx(table.loc["C(g)", "F"], rel=1e-9)
    assert ws[f"F{tr}"].value == pytest.approx(table.loc["C(g)", "PR(>F)"], rel=1e-7)
    df1, df2 = table.loc["C(g)", "df"], table.loc["Residual", "df"]
    assert ws[f"G{tr}"].value == pytest.approx(stats.f.isf(alpha, df1, df2), rel=1e-9)


def test_many_groups_of_many_values(evaluate: Evaluate) -> None:
    # arrange -- 12 groups of 300 values each (the old block held 8 × 30), unequal means
    rng = random.Random(21)
    groups = [[rng.gauss(50 + g % 3, 4) for _ in range(300)] for g in range(12)]
    expected = stats.f_oneway(*groups)
    # act
    ws = evaluate(sheet_anova.SHEET, one_way_cells(groups))
    # assert -- scipy's one-way ANOVA; rel=1e-9 (same sums of squares, different order)
    assert value(ws, "groups") == 12
    assert ws[f"E{ANOVA_ROWS['treatments']}"].value == pytest.approx(expected.statistic, rel=1e-9)
    assert ws[f"F{ANOVA_ROWS['treatments']}"].value == pytest.approx(expected.pvalue, rel=1e-7)
    assert ws[f"C{ANOVA_ROWS['error']}"].value == 12 * 300 - 12


# --- 2^k factorial --------------------------------------------------------------------------------------------


def test_effects_of_the_coded_example_s05_we05(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- DOE p. 47-49: 2^2, n = 3, printed [A] and [B]
    given, stated = oracle["S05-WE05"]["given"], oracle["S05-WE05"]["stated_answers"]
    runs = [[float(v) for v in given[f"A={a},B={b}"].split(",")] for b in ("-1", "+1") for a in ("-1", "+1")]
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, runs))
    # act / assert
    assert agrees_at_printed_precision(effect(ws, "A", "D"), stated["[A]"])
    assert agrees_at_printed_precision(effect(ws, "B", "D"), stated["[B]"])


@pytest.mark.xfail(reason="DOE p. 50 prints '[AB] = 5,78 – 4,92 = 0,857'; the exact effect is 0.8583 "
                          "(means 5.7767 − 4.9183)")
def test_interaction_of_the_coded_example_s05_we05(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    given = oracle["S05-WE05"]["given"]
    runs = [[float(v) for v in given[f"A={a},B={b}"].split(",")] for b in ("-1", "+1") for a in ("-1", "+1")]
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, runs))
    # act / assert
    assert agrees_at_printed_precision(effect(ws, "AB", "D"), oracle["S05-WE05"]["stated_answers"]["[AB]"])


CORNER_FIGURES = {"no_interaction_case": "description", "interaction_case": "figure_5-2/5-4_(interaction case)"}


def corner_runs(oracle: dict[str, Any], case: str) -> list[list[float]]:
    """DOE p. 53-54: one response per corner of a 2^2, in standard order (1), a, b, ab."""
    text = oracle["S05-WE06"]["given"][CORNER_FIGURES[case]]
    corners = {(a, b): float(y) for a, b, y in re.findall(r"A([+-])B([+-])=(\d+)", text)}
    return [[corners[(a, b)]] for b in "-+" for a in "-+"]


@pytest.mark.parametrize(("case", "names"), [("no_interaction_case", ("A", "B")),
                                             ("interaction_case", ("A", "B", "AB"))])
def test_effects_of_the_corner_figures_s05_we06(case: str, names: tuple[str, ...], oracle: dict[str, Any],
                                                evaluate: Evaluate) -> None:
    # arrange
    stated = oracle["S05-WE06"]["stated_answers"]
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, corner_runs(oracle, case)))
    # act / assert -- whole numbers, exact
    for name in names:
        assert effect(ws, name, "D") == float(stated[f"{case}_{name}"]), name


@pytest.mark.xfail(reason="DOE p. 53 prints 'AB = (52 + 20)/2 − (30 + 40)/2 = −1'; that expression is 36 − 35 = +1")
def test_interaction_of_the_no_interaction_figure_s05_we06(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, corner_runs(oracle, "no_interaction_case")))
    # act / assert
    assert effect(ws, "AB", "D") == float(oracle["S05-WE06"]["stated_answers"]["no_interaction_case_AB"])


def chemical_process() -> list[list[float]]:
    """DOE p. 59: recovery at the 4 corners (rows in standard order (1), a, b, ab), 3 replicates."""
    rows = {(r["A"], r["B"]): [float(r[f"Rep {i}"]) for i in ("I", "II", "III")]
            for r in course_rows("S05_chemical_process_example_treatment_combinations_and_replicat")}
    return [rows[(a, b)] for b in "-+" for a in "-+"]


def test_chemical_process_effects_and_anova_s05_we07(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- DOE p. 60-61
    stated = oracle["S05-WE07"]["stated_answers"]
    terms = anova_terms(stated["ANOVA"])
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, chemical_process()))
    # act / assert -- effects, SS, F, p
    for name in ("A", "B", "AB"):
        assert agrees_at_printed_precision(effect(ws, name, "D"), stated[name]), name
        assert agrees_at_printed_precision(effect(ws, name, "F"), terms[name]["SS"]), name
        assert agrees_at_printed_precision(effect(ws, name, "H"), terms[name]["F"]), name
    assert terms["A"]["P"] == "<0.0001" and effect(ws, "A", "I") < 0.0001
    assert agrees_at_printed_precision(effect(ws, "B", "I"), terms["B"]["P"])
    assert agrees_at_printed_precision(effect(ws, "AB", "I"), terms["AB"]["P"])
    # model, pure error and total rows
    model, error, total = MODEL_ROWS["model"], MODEL_ROWS["error"], MODEL_ROWS["total"]
    for cell, printed in ((f"B{model}", terms["Model"]["SS"]), (f"D{model}", terms["Model"]["MS"]),
                          (f"E{model}", terms["Model"]["F"]), (f"F{model}", terms["Model"]["P"]),
                          (f"B{error}", terms["Pure Error"]["SS"]), (f"D{error}", terms["Pure Error"]["MS"]),
                          (f"B{total}", terms["Cor Total"]["SS"])):
        assert agrees_at_printed_precision(ws[cell].value, printed), cell
    assert [ws[f"C{r}"].value for r in (model, error, total)] == [3, 8, 11]
    assert agrees_at_printed_precision(value(ws, "r2_doe"), stated["R-Squared"])
    assert agrees_at_printed_precision(value(ws, "r2_adj_doe"), stated["Adj_R-Squared"])


def surface_finish() -> list[list[float]]:
    """DOE p. 70: surface finish, 2^3 in standard order (rows (1), a, b, ab, c, …), 2 replicates."""
    rows = course_rows("S05_surface_finish_quality_example_data_2_3_design_n_2")
    for run, row in enumerate(rows):  # the printed signs are the standard order of the sheet
        assert [int(row[f]) for f in "ABC"] == [sign(run, 1 << j) for j in range(3)]
    return [[float(v) for v in row["Surface Finish obs1,obs2"].split(",")] for row in rows]


def test_surface_finish_anova_s05_we08(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- DOE p. 71
    terms = anova_terms(oracle["S05-WE08"]["stated_answers"]["ANOVA"])
    ws = evaluate(sheet_doe.SHEET, factorial_cells(3, surface_finish()))
    # act / assert
    for name in ("A", "B", "C", "AB", "AC", "BC"):
        assert agrees_at_printed_precision(effect(ws, name, "F"), terms[name]["SS"]), name
    for name in ("B", "C", "AB", "AC", "BC", "ABC"):
        assert agrees_at_printed_precision(effect(ws, name, "H"), terms[name]["F0"]), name
        assert agrees_at_printed_precision(effect(ws, name, "I"), terms[name]["P"]), name
    assert agrees_at_printed_precision(effect(ws, "A", "H"), terms["A"]["F0"])
    error, total = MODEL_ROWS["error"], MODEL_ROWS["total"]
    assert agrees_at_printed_precision(ws[f"B{error}"].value, terms["Error"]["SS"])
    assert agrees_at_printed_precision(ws[f"D{error}"].value, terms["Error"]["MS"])
    assert agrees_at_printed_precision(ws[f"B{total}"].value, terms["Total"]["SS"])
    assert [ws[f"C{error}"].value, ws[f"C{total}"].value] == [8, 15]
    assert [effect(ws, name, "J") for name in ("A", "B", "C")] == ["verwerp H0", "H0 niet verwerpen",
                                                                    "H0 niet verwerpen"]


@pytest.mark.xfail(reason="DOE p. 71 prints SS_ABC 5.5625; the data of p. 70 give contrast 9, SS 81/16 = 5.0625, "
                          "which the printed F0 2.08, P 0.19 and total 92.9375 also imply")
def test_surface_finish_abc_ss_s05_we08(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    terms = anova_terms(oracle["S05-WE08"]["stated_answers"]["ANOVA"])
    ws = evaluate(sheet_doe.SHEET, factorial_cells(3, surface_finish()))
    # act / assert
    assert agrees_at_printed_precision(effect(ws, "ABC", "F"), terms["ABC"]["SS"])


@pytest.mark.xfail(reason="DOE p. 71 prints P 2.54 x 10^-3 for A; F0 = 45.5625 / 2.4375 = 18.69 on F(1, 8) gives "
                          "2.534 x 10^-3 (2.53 x 10^-3)")
def test_surface_finish_p_of_a_s05_we08(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    terms = anova_terms(oracle["S05-WE08"]["stated_answers"]["ANOVA"])
    ws = evaluate(sheet_doe.SHEET, factorial_cells(3, surface_finish()))
    # act / assert
    assert agrees_scientific(effect(ws, "A", "I"), terms["A"]["P"])


def etch_rate() -> list[list[float]]:
    """DOE p. 74: etch rate, single replicate 2^4 in standard order."""
    rows = course_rows("S05_etch_rate_example_data_single_replicate_2_4_design")
    columns = ["A (Gap)", "B (Pressure)", "C (C2F6 Flow)", "D (Power)"]
    for run, row in enumerate(rows):
        assert [int(row[c]) for c in columns] == [sign(run, 1 << j) for j in range(4)]
    return [[float(row["Etch Rate (Angstrom/min)"])] for row in rows]


def test_etch_rate_effects_s05_we09(evaluate: Evaluate) -> None:
    # arrange -- DOE p. 75: all 15 estimated effects (course table, exact to 3 decimals)
    ws = evaluate(sheet_doe.SHEET, factorial_cells(4, etch_rate(), pool=3))
    # act / assert
    for row in course_rows("S05_etch_rate_example_estimated_effects_2_4_single_replicate"):
        assert agrees_at_printed_precision(effect(ws, row["Effect"], "D"), row["Estimate"]), row["Effect"]


def test_etch_rate_pooled_anova_s05_we09(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- DOE p. 77: model (A+B+C+D)^2, the 3- and 4-factor interactions pooled into the error (df 5)
    terms = anova_terms(oracle["S05-WE09"]["stated_answers"]["pooled_model_(A+B+C+D)^2_R_ANOVA"])
    ws = evaluate(sheet_doe.SHEET, factorial_cells(4, etch_rate(), pool=3))
    # act / assert
    for term, printed in terms.items():
        if term == "Residuals":
            continue
        name = term.replace(":", "")
        assert effect(ws, name, "G") == "in het model"
        assert agrees_at_printed_precision(effect(ws, name, "H"), printed["F"]), term
        if term == "D":
            assert agrees_scientific(effect(ws, name, "I"), printed["P"])
        else:
            assert agrees_at_printed_precision(effect(ws, name, "I"), printed["P"]), term
    assert value(ws, "df_pool") == int(terms["Residuals"]["df"]) and value(ws, "df_pe") == 0
    assert agrees_at_printed_precision(value(ws, "ss_pool"), terms["Residuals"]["SS"])
    assert agrees_at_printed_precision(value(ws, "mse"), terms["Residuals"]["MS"])
    assert effect(ws, "ABCD", "G") == "gepoold in de fout" and effect(ws, "ABCD", "H") is None


def test_ice_cream_effects_and_coefficients_s08_we16(oracle: dict[str, Any], printed: Printed,
                                                     evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 225-233: Table 9-3 (runs in standard order), X1 = A, X2 = B, X3 = C
    rows = oracle["S08-WE16"]["given"]["Table_9-3_plan_and_results"]["rows"]
    for run, row in enumerate(rows):
        assert row[2:5] == [sign(run, 1 << j) for j in range(3)]
    ws = evaluate(sheet_doe.SHEET, factorial_cells(3, [[float(row[5])] for row in rows]))
    stated = "stated_answers"
    # act / assert -- effects E1 … E123
    for key, name, shown in (("E1", "A", "11.5"), ("E2", "B", "1.5"), ("E3", "C", "-2.5"), ("E12", "AB", "-1.0"),
                             ("E13", "AC", "0.0"), ("E23", "BC", "14.0"), ("E123", "ABC", "1.5")):
        assert agrees_at_printed_precision(effect(ws, name, "D"), printed("S08-WE16", stated, key, shown)), key
    # β0 = mean of all runs; β = E / 2
    assert agrees_at_printed_precision(value(ws, "beta0"), printed("S08-WE16", stated, "beta_0", "1,237.5"),
                                       thousands=True)
    assert agrees_at_printed_precision(effect(ws, "A", "E"), printed("S08-WE16", stated, "beta_1", "5.75"))
    assert agrees_at_printed_precision(effect(ws, "BC", "E"), printed("S08-WE16", stated, "beta_23", "7.0"))


def statsmodels_factorial(k: int, runs: list[list[float]], pool: int | None) -> Any:
    """OLS fit of the coded 2^k model by statsmodels: all effects of order < pool (or all effects)."""
    names = FACTORS[:k]
    frame = pd.DataFrame([{**{f: sign(r, 1 << j) for j, f in enumerate(names)}, "y": y}
                          for r, ys in enumerate(runs) for y in ys])
    order = (pool - 1) if pool else k
    return smf.ols(f"y ~ ({'+'.join(names)})**{order}", frame).fit()


@pytest.mark.parametrize(("k", "n", "pool"), [(2, 4, None), (3, 1, 2), (4, 2, 3), (5, 4, None), (5, 1, 3),
                                          (3, 8, None)])  # 8 replicates: beyond the old 4 columns
def test_factorial_matches_statsmodels(k: int, n: int, pool: int | None, evaluate: Evaluate) -> None:
    # arrange -- random responses
    rng = random.Random(10 * k + n)
    runs = [[rng.gauss(100 + 5 * sign(r, 1) - 3 * sign(r, 3), 2) for _ in range(n)] for r in range(2 ** k)]
    fit = statsmodels_factorial(k, runs, pool)
    table = sm.stats.anova_lm(fit, typ=1)
    ws = evaluate(sheet_doe.SHEET, factorial_cells(k, runs, pool))
    # act / assert -- rel=1e-9 for sums of squares and effects (= 2 × OLS coefficient), 1e-7 for p-values
    for mask in range(1, 2 ** k):
        term = ":".join(effect_name(mask))
        if term in table.index:
            assert effect(ws, effect_name(mask), "D") == pytest.approx(2 * fit.params[term], rel=1e-9, abs=1e-9)
            assert effect(ws, effect_name(mask), "F") == pytest.approx(table.loc[term, "sum_sq"], rel=1e-9, abs=1e-12)
            assert effect(ws, effect_name(mask), "I") == pytest.approx(table.loc[term, "PR(>F)"], rel=1e-7)
        else:
            assert effect(ws, effect_name(mask), "G") == "gepoold in de fout"
    assert value(ws, "mse") == pytest.approx(fit.mse_resid, rel=1e-9)
    assert value(ws, "beta0") == pytest.approx(fit.params["Intercept"], rel=1e-12)
    assert value(ws, "r2_doe") == pytest.approx(fit.rsquared, rel=1e-9)
    assert value(ws, "r2_adj_doe") == pytest.approx(fit.rsquared_adj, rel=1e-9)
    assert value(ws, "se_effect") == pytest.approx(2 * fit.bse["A"], rel=1e-9)  # DOE p. 67 = 2 s.e.(coefficient)
    for mask in range(2 ** k, 32):  # effects outside the design stay empty
        assert effect(ws, effect_name(mask), "D") is None


def test_incomplete_design_is_refused(evaluate: Evaluate) -> None:
    # arrange -- the chemical process example with one response missing
    runs = chemical_process()
    runs[3] = runs[3][:2]
    ws = evaluate(sheet_doe.SHEET, factorial_cells(2, runs))
    # act / assert
    assert value(ws, "complete").startswith("NEE")
    assert effect(ws, "A", "D") is None and value(ws, "mse") is None


# --- simple linear regression ---------------------------------------------------------------------------------


def oxygen_purity() -> tuple[list[float], list[float]]:
    """Regression p. 2 Table 11-1: hydrocarbon level x (%) and oxygen purity y (%), n = 20."""
    rows = course_rows("S05_table_11_1_oxygen_and_hydrocarbon_levels")
    return [float(r["Hydrocarbon Level x (%)"]) for r in rows], [float(r["Purity y (%)"]) for r in rows]


def test_regression_oxygen_purity_s05_we17(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Regression p. 22, Minitab Table 11-2
    stated = oracle["S05-WE17"]["stated_answers"]
    terms = anova_terms(stated["ANOVA"])
    ws = evaluate(sheet_regression.SHEET, regression_cells(*oxygen_purity()))
    b1, b0 = T_TESTS["b1"], T_TESTS["b0"]
    # act / assert
    for name, key in (("b0", "beta0hat_minitab"), ("b1", "beta1hat_minitab"), ("se_b0", "SE_beta0"),
                      ("se_b1", "SE_beta1"), ("s", "S")):
        assert agrees_at_printed_precision(value(ws, name), stated[key]), name
    assert agrees_at_printed_precision(ws[f"D{b0}"].value, stated["T_beta0"])
    assert agrees_at_printed_precision(ws[f"D{b1}"].value, stated["T_beta1"])
    assert agrees_at_printed_precision(ws[f"E{b1}"].value, stated["P"])
    assert agrees_at_printed_precision(value(ws, "r2") * 100, stated["R-Sq"].rstrip("%"))
    assert agrees_at_printed_precision(value(ws, "r2_adj") * 100, stated["R-Sq(adj)"].rstrip("%"))
    for name, printed in (("ssr", terms["Regression"]["SS"]), ("sse", terms["Residual Error"]["SS"]),
                          ("sst", terms["Total"]["SS"]), ("F", terms["Regression"]["F"]),
                          ("mse_reg", terms["Residual Error"]["MS"]), ("p_F", terms["Regression"]["P"])):
        assert agrees_at_printed_precision(value(ws, name), printed), name
    assert value(ws, "n") - 2 == int(terms["Residual Error"]["df"])


@pytest.mark.xfail(reason="Regression p. 21 Figure 11-4 prints ŷ = 74.20 + 14.97x; the least squares values on "
                          "p. 22 are 74.283 and 14.947")
def test_regression_figure_line_s05_we17(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    line = re.findall(r"\d+\.\d+", oracle["S05-WE17"]["stated_answers"]["fitted_line_fig11-4"])
    ws = evaluate(sheet_regression.SHEET, regression_cells(*oxygen_purity()))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "b0"), line[0])
    assert agrees_at_printed_precision(value(ws, "b1"), line[1])


def test_prediction_at_x0_s05_we18(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Regression p. 22: new observation at HC level 1.00, 95 % (α 0.05 as prefilled)
    example = oracle["S05-WE18"]
    stated = example["stated_answers"]
    ws = evaluate(sheet_regression.SHEET, regression_cells(*oxygen_purity(), x0=float(example["given"]["x0"])))
    mean, prediction = INTERVALS["mean"], INTERVALS["prediction"]
    # act / assert
    assert agrees_at_printed_precision(value(ws, "fit"), stated["Fit"])
    assert agrees_at_printed_precision(value(ws, "se_fit"), stated["SE_Fit"])
    for row, key in ((mean, "95%_CI"), (prediction, "95%_PI")):
        low, high = re.findall(r"\d+\.\d+", stated[key])
        assert agrees_at_printed_precision(ws[f"D{row}"].value, low), key
        assert agrees_at_printed_precision(ws[f"E{row}"].value, high), key


@pytest.mark.parametrize("seed", [1, 2])
def test_regression_matches_statsmodels(seed: int, evaluate: Evaluate) -> None:
    # arrange -- random data, random α, x0 and H0 values
    rng = random.Random(seed)
    n = rng.randint(5, 200)
    xs = [rng.uniform(0, 10) for _ in range(n)]
    ys = [2 + 0.5 * x + rng.gauss(0, 1) for x in xs]
    alpha, x0 = rng.choice([0.01, 0.05, 0.10]), rng.uniform(0, 10)
    h0 = {"beta1_0": rng.uniform(-1, 1), "beta0_0": rng.uniform(-1, 3)}
    fit = sm.OLS(ys, sm.add_constant(xs)).fit()
    frame = fit.get_prediction([[1.0, x0]]).summary_frame(alpha=alpha)
    ws = evaluate(sheet_regression.SHEET, regression_cells(xs, ys, x0) | {INPUTS["alpha"]: alpha} | {INPUTS[k]: v for k, v in h0.items()})
    # act / assert -- estimates, ANOVA and R² at rel=1e-9
    assert value(ws, "b0") == pytest.approx(fit.params[0], rel=1e-9)
    assert value(ws, "b1") == pytest.approx(fit.params[1], rel=1e-9)
    assert value(ws, "se_b0") == pytest.approx(fit.bse[0], rel=1e-9)
    assert value(ws, "se_b1") == pytest.approx(fit.bse[1], rel=1e-9)
    assert value(ws, "sse") == pytest.approx(fit.ssr, rel=1e-9)
    assert value(ws, "r2") == pytest.approx(fit.rsquared, rel=1e-9)
    assert value(ws, "r2_adj") == pytest.approx(fit.rsquared_adj, rel=1e-9)
    assert value(ws, "F") == pytest.approx(fit.fvalue, rel=1e-9)
    assert value(ws, "p_F") == pytest.approx(fit.f_pvalue, rel=1e-7)
    # the p. 56 version, computed from its printed formula with k = 1
    assert value(ws, "r2_adj_p56") == pytest.approx(1 - (1 - fit.rsquared) * (n - 1) / (n - 3), rel=1e-9)
    # t-tests against the H0 values, three alternatives (decision 6)
    df = n - 2
    for key, i, h in (("b1", 1, h0["beta1_0"]), ("b0", 0, h0["beta0_0"])):
        r, t = T_TESTS[key], (fit.params[i] - h) / fit.bse[i]
        assert ws[f"D{r}"].value == pytest.approx(t, rel=1e-9)
        assert ws[f"E{r}"].value == pytest.approx(2 * stats.t.sf(abs(t), df), rel=1e-7)
        assert ws[f"F{r}"].value == pytest.approx(stats.t.sf(t, df), rel=1e-7)
        assert ws[f"G{r}"].value == pytest.approx(stats.t.cdf(t, df), rel=1e-7)
    # intervals: two-sided from statsmodels, one-sided bounds from scipy's t quantile
    ci = fit.conf_int(alpha)
    one = stats.t.ppf(1 - alpha, df)
    expected = {
        "b0": (ci[0][0], ci[0][1], fit.params[0], fit.bse[0]),
        "b1": (ci[1][0], ci[1][1], fit.params[1], fit.bse[1]),
        "mean": (frame["mean_ci_lower"].iloc[0], frame["mean_ci_upper"].iloc[0], frame["mean"].iloc[0], frame["mean_se"].iloc[0]),
        "prediction": (frame["obs_ci_lower"].iloc[0], frame["obs_ci_upper"].iloc[0], frame["mean"].iloc[0],
                       (frame["mean_se"].iloc[0] ** 2 + fit.mse_resid) ** 0.5),
    }
    for key, (low, high, centre, se) in expected.items():
        r = INTERVALS[key]
        assert ws[f"D{r}"].value == pytest.approx(low, rel=1e-9), key
        assert ws[f"E{r}"].value == pytest.approx(high, rel=1e-9), key
        assert ws[f"F{r}"].value == pytest.approx(centre - one * se, rel=1e-9), key
        assert ws[f"G{r}"].value == pytest.approx(centre + one * se, rel=1e-9), key


def test_unpaired_rows_are_refused(evaluate: Evaluate) -> None:
    # arrange -- the oxygen data with one y moved to a row without x
    xs, ys = oxygen_purity()
    cells = regression_cells(xs[:-1], ys[:-1]) | {pair_cells(len(xs))[1]: ys[-1]}
    ws = evaluate(sheet_regression.SHEET, cells)
    # act / assert
    assert value(ws, "pairs").startswith("NEE")
    assert value(ws, "b1") is None


def test_many_pairs(evaluate: Evaluate) -> None:
    # arrange -- 3000 pairs (the old block held 200)
    rng = random.Random(8)
    xs = [rng.uniform(0, 10) for _ in range(3000)]
    ys = [2 + 0.5 * x + rng.gauss(0, 1) for x in xs]
    fit = stats.linregress(xs, ys)
    # act
    ws = evaluate(sheet_regression.SHEET, regression_cells(xs, ys))
    # assert
    assert value(ws, "n") == 3000
    assert value(ws, "b1") == pytest.approx(fit.slope, rel=1e-9)
    assert value(ws, "b0") == pytest.approx(fit.intercept, rel=1e-9)
    assert value(ws, "r2") == pytest.approx(fit.rvalue ** 2, rel=1e-9)
