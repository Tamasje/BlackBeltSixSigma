"""Tests for bbtools.sheet_grr, evaluated by LibreOffice headless.

Expected values: the course's GRR study (steering-mechanism part, 3 operators × 5 parts × 2 trials) read from the
course workbook named by the oracle's data_ref, and its worked solutions S10-WE02 (ANOVA) and S10-WE03 (average and
range), Excel cached floats. statsmodels' two-way ANOVA for random complete studies.
"""
from __future__ import annotations

import itertools
import random
from collections.abc import Callable
from typing import Any

import openpyxl
import pandas as pd
import pytest
import statsmodels.api as sm
import statsmodels.formula.api as smf

from bbtools.constants import ROOT
from bbtools.sheet_grr import ANOVA_ROWS, INTERACTION_ROWS, RESULTS, SHEET, data_cell

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]
Study = dict[tuple[int, int, int], float]  # (operator, trial, part) -> value, all 0-based
WORKBOOK = ROOT / "source" / "course" / "Les 5" / "20260619_ottoy_GRR - ANOVA - avegage and range - 2.xlsx"
# The workbook types the interaction SS rounded ('=412.5+296.667'), which moves its EV² by 4.7e-7 relative;
# 1e-5 allows exactly that shift and nothing coarser.
TYPED_ROUNDING = 1e-5


def course_study() -> Study:
    """measurements!D4:F13: rows = part 1..5 × trial 1..2, columns = operators A, B, C (S10-WE02 data_ref)."""
    ws = openpyxl.load_workbook(WORKBOOK, data_only=True)["measurements"]
    return {(operator, (row - 4) % 2, (row - 4) // 2): ws.cell(row, 4 + operator).value
            for row in range(4, 14) for operator in range(3)}


def cells(study: Study) -> dict[str, float]:
    """Input cells of a study."""
    return {data_cell(*key): value for key, value in study.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


def test_study_size_is_derived_from_the_data(evaluate: Evaluate) -> None:
    # act
    ws = evaluate(SHEET, cells(course_study()))
    # assert -- 3 operators, 5 parts, 2 trials, 30 values
    assert [value(ws, name) for name in ("k", "n", "r", "count", "complete")] == [3, 5, 2, 30, "ja"]


def test_average_and_range_method_s10_we03(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- 'ranges' sheet: K1 = 1/1.12838, K2 = 1/1.91155, K3 = 1/2.48124 (tabel MSA.pdf)
    answers = oracle["S10-WE03"]["stated_answers"]
    ws = evaluate(SHEET, cells(course_study()))
    # act / assert -- Excel cached floats, same formulas and constants: rel=1e-9
    assert value(ws, "d2") == 1.12838 and value(ws, "d2star_k") == 1.91155 and value(ws, "d2star_n") == 2.48124
    for name, key in (("ev_ar", "EV"), ("av_ar", "AV"), ("pv_ar", "PV"), ("tv_ar", "TV"),
                      ("pct_ar", "%GRR (formula sqrt((EV^2+AV^2)/TV^2))")):
        assert value(ws, name) == pytest.approx(float(answers[key]), rel=1e-9), name


def test_anova_method_s10_we02(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- '2way anova' sheet: additive model (interaction pooled), EV, AV, PV, TV, %GRR
    answers = oracle["S10-WE02"]["stated_answers"]
    ws = evaluate(SHEET, cells(course_study()))
    # act / assert -- the workbook's typed rounding (see TYPED_ROUNDING) is the only difference
    for name, key in (("ev_anova", "EV"), ("av_anova", "AV"), ("pv_anova", "PV"), ("tv_anova", "TV"),
                      ("pct_anova", "%GRR (formula sqrt((EV^2+AV^2)/TV^2))")):
        assert value(ws, name) == pytest.approx(float(answers[key]), rel=TYPED_ROUNDING), name
    assert answers["conclusion"].startswith("niet geschikt")
    assert ws[f"D{69}"].value == "niet aanvaardbaar (not acceptable, > 30 %)"


@pytest.mark.xfail(reason="GRR workbook '2way anova' K45 types '=412.5+296.667' (interaction SS 296.6667 rounded): "
                          "its EV² 30.8333478 differs from the exact 30.8333333 in the 7th digit")
def test_anova_method_s10_we02_at_full_precision(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells(course_study()))
    # act / assert
    assert value(ws, "ev_anova") == pytest.approx(float(oracle["S10-WE02"]["stated_answers"]["EV"]), rel=1e-9)


def test_anova_with_interaction_matches_the_course_excel_output_s10_we02(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Excel 'Anova: Two-Factor With Replication' output in the course workbook (exact)
    table = oracle["S10-WE02"]["given"]["anova_table_with_interaction"]
    ws = evaluate(SHEET, cells(course_study()))
    rows = {"parts": "Sample(part)", "operators": "Columns(operator)", "interaction": "Interaction",
            "within": "Within", "total": "Total"}
    # act / assert -- rel=1e-9: same sums of squares, different summation order
    for key, source in rows.items():
        r, printed = INTERACTION_ROWS[key], table[source]
        assert ws[f"B{r}"].value == pytest.approx(float(printed["SS"]), rel=1e-9), key
        assert ws[f"C{r}"].value == printed["df"], key
        if "MS" in printed:
            assert ws[f"D{r}"].value == pytest.approx(float(printed["MS"]), rel=1e-9), key
        if "F" in printed:
            assert ws[f"E{r}"].value == pytest.approx(float(printed["F"]), rel=1e-9), key
            assert ws[f"F{r}"].value == pytest.approx(float(printed["P-value"]), rel=1e-7), key
            assert ws[f"G{r}"].value == pytest.approx(float(printed["F_crit"]), rel=1e-9), key


def statsmodels_anova(study: Study, interaction: bool) -> pd.DataFrame:
    """Type-I two-way ANOVA of a balanced study by statsmodels (independent implementation)."""
    frame = pd.DataFrame([{"y": y, "operator": o, "part": p} for (o, _, p), y in study.items()])
    model = smf.ols("y ~ C(part) * C(operator)" if interaction else "y ~ C(part) + C(operator)", frame).fit()
    return sm.stats.anova_lm(model, typ=1)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_both_anova_tables_match_statsmodels(seed: int, evaluate: Evaluate) -> None:
    # arrange -- a random complete study
    rng = random.Random(seed)
    k, n, r = rng.randint(2, 3), rng.randint(2, 10), rng.randint(2, 3)
    part_effect = [rng.gauss(0, 10) for _ in range(n)]
    operator_effect = [rng.gauss(0, 3) for _ in range(k)]
    study = {(o, t, p): 50 + part_effect[p] + operator_effect[o] + rng.gauss(0, 2)
             for o, t, p in itertools.product(range(k), range(r), range(n))}
    ws = evaluate(SHEET, cells(study))
    additive, full = statsmodels_anova(study, False), statsmodels_anova(study, True)
    # act / assert -- rel=1e-9: same sums of squares by a different algorithm (QR least squares)
    for key, term in (("parts", "C(part)"), ("operators", "C(operator)"), ("error", "Residual")):
        r_ = ANOVA_ROWS[key]
        assert ws[f"B{r_}"].value == pytest.approx(additive.loc[term, "sum_sq"], rel=1e-9), key
        assert ws[f"C{r_}"].value == additive.loc[term, "df"], key
    for key, term in (("parts", "C(part)"), ("operators", "C(operator)"),
                      ("interaction", "C(part):C(operator)"), ("within", "Residual")):
        r_ = INTERACTION_ROWS[key]
        assert ws[f"B{r_}"].value == pytest.approx(full.loc[term, "sum_sq"], rel=1e-9), key
    assert ws[f"F{INTERACTION_ROWS['interaction']}"].value == pytest.approx(
        full.loc["C(part):C(operator)", "PR(>F)"], rel=1e-7)
    # and the course's EV from the additive model
    assert value(ws, "ev_anova") == pytest.approx(additive.loc["Residual", "mean_sq"] ** 0.5, rel=1e-9)


def test_incomplete_study_is_refused(evaluate: Evaluate) -> None:
    # arrange -- drop one measurement from the course study
    study = course_study()
    del study[(2, 1, 4)]
    ws = evaluate(SHEET, cells(study))
    # act / assert
    assert value(ws, "complete").startswith("NEE")
    assert value(ws, "ev_ar") is None and value(ws, "ev_anova") is None


def test_percent_grr_of_tolerance(evaluate: Evaluate) -> None:
    # arrange -- MSA p. 24: %GRR = 6 sigma_m / TOL
    ws = evaluate(SHEET, {**cells(course_study()), "B9": 100})
    # act / assert
    assert value(ws, "pct_tol_ar") == pytest.approx(6 * value(ws, "grr_ar") / 100, rel=1e-12)
    assert value(ws, "pct_tol_anova") == pytest.approx(6 * value(ws, "grr_anova") / 100, rel=1e-12)
