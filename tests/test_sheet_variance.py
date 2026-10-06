"""Tests for bbtools.sheet_variance, evaluated by LibreOffice headless.

Expected values: course worked examples S03-WE03 / S03-WE05 (Ottoy; Excel cached floats at rel=1e-9 and slide
values at printed precision), S08-WE10 (Dummies, printed precision), the Dummies χ² and F tables (p. 194, 196)
against their definitions, and scipy.stats for random inputs. S08-WE11 disagrees and is a strict xfail.
"""
from __future__ import annotations

import csv
import random
from collections.abc import Callable, Sequence
from typing import Any

import pytest
from scipy import stats

from bbtools.constants import CONSTANTS_DIR
from bbtools.printed import agrees_at_printed_precision
from bbtools.sheet_variance import (
    CHI2_TEST_ROWS,
    CI_ROWS,
    F_CI_ROWS,
    F_TEST_ROWS,
    INPUTS,
    RESULTS,
    SHEET,
)

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]
libreoffice = pytest.mark.libreoffice
TWO_SIGMA_ALPHA = 2 * stats.norm.sf(2)  # Dummies p. 192: '95 %' is the +/- 2 sigma level


def cells(values: dict[str, float], data_1: Sequence[float] = (), data_2: Sequence[float] = ()) -> dict[str, float]:
    """Input cells, plus raw data pasted into columns H and I from row 10."""
    mapped = {INPUTS[name]: v for name, v in values.items()}
    mapped |= {f"H{10 + i}": x for i, x in enumerate(data_1)}
    mapped |= {f"I{10 + i}": x for i, x in enumerate(data_2)}
    return mapped


def at(ws: Any, column: str, row: int) -> Any:
    """Cached value of one cell."""
    return ws[f"{column}{row}"].value


# ---------------------------------------------------------------- course tables vs their definitions (pure)

def test_dummies_f_table_is_the_5_percent_upper_tail_with_n_minus_1_degrees_of_freedom() -> None:
    # arrange -- Table 8-3 p. 196: row n2, column n1
    with (CONSTANTS_DIR / "S08_table_8_3_f_values_for_95_confidence.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    # act
    mismatches = [(row[""], column, row[column]) for row in rows for column in ("n1=2", "n1=5", "n1=10", "n1=25")
                  if not agrees_at_printed_precision(stats.f.isf(0.05, int(column[3:]) - 1, int(row[""][3:]) - 1),
                                                     row[column])]
    # assert -- one printed value is 2 units off in its last digit (definition 161.448)
    assert mismatches == [("n2=2", "n1=2", "161.446")]


def test_dummies_chi_square_table_uses_the_z_multiple_tails() -> None:
    # arrange -- Table 8-2 p. 194: '68 %, 95 %, 99.7 %' rows are the upper value for tail Phi(-Z), Z = 1, 2, 3;
    #            the unlabeled row under each is the lower value (the book's footnote: chi2_LOWER first, then UPPER)
    with (CONSTANTS_DIR / "S08_table_8_2_chi_square_values.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    mismatches = []
    for upper, lower in zip(rows[0::2], rows[1::2], strict=True):
        tail = stats.norm.sf(float(upper["Z"]))
        for column in ("n=2", "n=5", "n=10", "n=25"):
            df = int(column[2:]) - 1
            # act
            if not agrees_at_printed_precision(stats.chi2.isf(tail, df), upper[column]):
                mismatches.append((upper["Confidence"], column, "upper", upper[column]))
            if not agrees_at_printed_precision(stats.chi2.ppf(tail, df), lower[column]):
                mismatches.append((upper["Confidence"], column, "lower", lower[column]))
    # assert -- one printed value is 1 unit off in its last digit (definition 17.8006)
    assert mismatches == [("99.7%", "n=5", "upper", "17.800")]


# ---------------------------------------------------------------- the sheet (LibreOffice)

@libreoffice
def test_one_sided_ci_for_sigma_from_raw_data_s03_we03(oracle: dict[str, Any], printed: Printed,
                                                       evaluate: Evaluate) -> None:
    # arrange -- Confidence Intervals.pdf p. 16: 20 measurements, one-sided 98 %-CI for sigma
    data = oracle["S03-WE03"]["given"]["data (n=20)"]
    ws = evaluate(SHEET, cells({"alpha": 0.02}, data_1=data))
    answers = oracle["S03-WE03"]["stated_answers"]
    # act / assert -- VAR.S cached by Excel (rel=1e-9); the bound printed ']0.0088, +infinity['
    assert at(ws, "B", 17) == pytest.approx(float(answers["variance (Excel cached, VAR.S)"]), rel=1e-9)
    assert agrees_at_printed_precision(at(ws, "D", CI_ROWS["lower_only"]),
                                       printed("S03-WE03", "stated_answers", "one-sided 98%-CI (as printed on slide)", "0.0088"))
    assert at(ws, "E", CI_ROWS["lower_only"]) == "+∞"


@libreoffice
def test_chi_square_test_for_sigma_s03_we05(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.pdf p. 13: H0 sigma = 0.01 vs HA sigma > 0.01 at 2 %
    data = oracle["S03-WE03"]["given"]["data (n=20)"]
    ws = evaluate(SHEET, cells({"alpha": 0.02, "sigma0": 0.01}, data_1=data))
    answers = oracle["S03-WE05"]["stated_answers"]
    row = CHI2_TEST_ROWS["greater"]
    # act / assert -- Excel cached floats rel=1e-9; slide values at printed precision
    assert at(ws, "B", row) == pytest.approx(float(answers["test statistic (Excel cached, exact, =19*var/(0.01^2))"]), rel=1e-9)
    assert at(ws, "C", row) == pytest.approx(float(answers["critical value (Excel cached, exact)"]), rel=1e-9)
    assert at(ws, "E", row) == pytest.approx(float(answers["p-value (Excel cached, exact, via 1-CHISQ.DIST)"]), rel=1e-9)
    assert agrees_at_printed_precision(at(ws, "C", row), printed("S03-WE05", "stated_answers", "critical value (as printed on slide)", "33.69"))
    assert agrees_at_printed_precision(at(ws, "E", row) * 100, printed("S03-WE05", "stated_answers", "p-value (as printed on slide)", "13.6"))
    assert at(ws, "F", row) == "do not reject H0"


@libreoffice
def test_two_sided_ci_for_sigma_dummies_s08_we10(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 195: n = 5, s = 3.7, '95 %' = +/- 2 sigma (p. 192)
    ws = evaluate(SHEET, cells({"alpha": TWO_SIGMA_ALPHA, "n": 5, "s": 3.7}))
    row = CI_ROWS["two_sided"]
    # act / assert -- printed '[2.195, 10.907]'
    assert agrees_at_printed_precision(at(ws, "D", row), printed("S08-WE10", "stated_answers", "CI", "2.195"))
    assert agrees_at_printed_precision(at(ws, "E", row), printed("S08-WE10", "stated_answers", "CI", "10.907"))


@libreoffice
@pytest.mark.parametrize(("n1", "n2", "column"), [(5, 10, "n1=5"), (10, 5, "n1=10"), (25, 2, "n1=25")])
def test_f_critical_value_matches_dummies_table_8_3(n1: int, n2: int, column: str, evaluate: Evaluate) -> None:
    # arrange -- HA: sigma1 > sigma2 at alpha 5 % has critical value F.INV.RT(0.05; n1-1; n2-1)
    with (CONSTANTS_DIR / "S08_table_8_3_f_values_for_95_confidence.csv").open(encoding="utf-8", newline="") as fh:
        table = {row[""]: row for row in csv.DictReader(fh)}
    ws = evaluate(SHEET, cells({"alpha": 0.05, "n1": n1, "s1": 1, "n2": n2, "s2": 1}))
    # act / assert
    assert agrees_at_printed_precision(at(ws, "C", F_TEST_ROWS["greater"]), table[f"n2={n2}"][column])


@libreoffice
@pytest.mark.xfail(reason="Dummies p. 196 prints [0.147, 3.199] with the two F values swapped; "
                          "F(nA-1, nB-1) as in Test Recipes p. 12 gives [0.0889, 1.938]")
def test_ci_for_ratio_of_variances_dummies_s08_we11(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- A: n 10, variance 4; B: n 5, variance 7.5; the book's F values are 5 % upper tails -> alpha 0.10
    given = oracle["S08-WE11"]["given"]
    ws = evaluate(SHEET, cells({"alpha": 0.10, "n1": given["distribution_A"]["n"], "s1": given["distribution_A"]["variance"] ** 0.5,
                                "n2": given["distribution_B"]["n"], "s2": given["distribution_B"]["variance"] ** 0.5}))
    row = F_CI_ROWS["two_sided"]
    # act / assert
    assert agrees_at_printed_precision(at(ws, "B", row), printed("S08-WE11", "stated_answers", "CI_for_varA_over_varB", "0.147"))
    assert agrees_at_printed_precision(at(ws, "C", row), printed("S08-WE11", "stated_answers", "CI_for_varA_over_varB", "3.199"))


@libreoffice
def test_pasted_data_override_typed_n_and_s(evaluate: Evaluate) -> None:
    # arrange -- typed n = 99 and s = 99 must be ignored once column H holds data
    data = [1.0, 2.0, 4.0, 7.0]
    ws = evaluate(SHEET, cells({"n": 99, "s": 99, "n1": 99, "s1": 99}, data_1=data))
    # act / assert
    assert ws[RESULTS["n_used"]].value == 4 and ws[RESULTS["n1_used"]].value == 4
    assert ws[RESULTS["s_used"]].value == pytest.approx(stats.tstd(data), rel=1e-12)


@libreoffice
@pytest.mark.parametrize("seed", [1, 2])
def test_every_interval_and_test_matches_scipy(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    alpha = rng.choice([0.01, 0.02, 0.05, 0.10])
    n, s, sigma0 = rng.randint(3, 60), rng.uniform(0.1, 5), rng.uniform(0.1, 5)
    n1, s1, n2, s2 = rng.randint(3, 40), rng.uniform(0.1, 5), rng.randint(3, 40), rng.uniform(0.1, 5)
    ws = evaluate(SHEET, cells({"alpha": alpha, "n": n, "s": s, "sigma0": sigma0, "n1": n1, "s1": s1, "n2": n2, "s2": s2}))
    df, q = n - 1, (n - 1) * s**2
    chi2 = stats.chi2(df)
    v1, v2, f = n1 - 1, n2 - 1, s1**2 / s2**2
    fd = stats.f(v1, v2)
    stat = q / sigma0**2
    expected = {
        ("B", CI_ROWS["two_sided"]): q / chi2.isf(alpha / 2), ("C", CI_ROWS["two_sided"]): q / chi2.ppf(alpha / 2),
        ("B", CI_ROWS["lower_only"]): q / chi2.isf(alpha), ("C", CI_ROWS["upper_only"]): q / chi2.ppf(alpha),
        ("D", CI_ROWS["two_sided"]): (q / chi2.isf(alpha / 2)) ** 0.5,
        ("B", CHI2_TEST_ROWS["greater"]): stat, ("C", CHI2_TEST_ROWS["greater"]): chi2.isf(alpha),
        ("E", CHI2_TEST_ROWS["greater"]): chi2.sf(stat), ("E", CHI2_TEST_ROWS["less"]): chi2.cdf(stat),
        ("E", CHI2_TEST_ROWS["two_sided"]): 2 * min(chi2.cdf(stat), chi2.sf(stat)),
        ("B", F_CI_ROWS["two_sided"]): f / fd.isf(alpha / 2), ("C", F_CI_ROWS["two_sided"]): f / fd.ppf(alpha / 2),
        ("D", F_CI_ROWS["two_sided"]): fd.ppf(alpha / 2) / f, ("E", F_CI_ROWS["two_sided"]): fd.isf(alpha / 2) / f,
        ("B", F_CI_ROWS["ratio_at_least"]): f / fd.isf(alpha), ("C", F_CI_ROWS["ratio_at_most"]): f / fd.ppf(alpha),
        ("D", F_CI_ROWS["ratio_at_most"]): fd.ppf(alpha) / f,  # exam Q2: lower bound for sigma2^2/sigma1^2
        ("B", F_TEST_ROWS["greater"]): f, ("C", F_TEST_ROWS["greater"]): fd.isf(alpha),
        ("E", F_TEST_ROWS["greater"]): fd.sf(f), ("E", F_TEST_ROWS["less"]): fd.cdf(f),
        ("E", F_TEST_ROWS["two_sided"]): 2 * min(fd.cdf(f), fd.sf(f)),
    }
    # act / assert -- rel=1e-9 covers LibreOffice vs scipy quantile round-off
    for (column, row), target in expected.items():
        assert at(ws, column, row) == pytest.approx(target, rel=1e-9), (column, row)
    for row in (*CHI2_TEST_ROWS.values(), *F_TEST_ROWS.values()):
        p = at(ws, "E", row)
        assert at(ws, "F", row) == ("reject H0" if p < alpha else "do not reject H0")
