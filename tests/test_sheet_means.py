"""Tests for bbtools.sheet_means, evaluated by LibreOffice headless.

Expected values: course worked examples (inventory/worked_examples.json, locked). Excel cached floats (S03-WE02,
S03-WE04) at rel=1e-9; slide values at printed precision (decision 10). scipy.stats for random inputs.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from typing import Any

import pytest
from scipy import stats

from bbtools.printed import agrees_at_printed_precision
from bbtools.sheet_means import (
    INPUTS,
    ONE_MEAN_CI,
    PAIRED_CI,
    PROPORTION_CI,
    PROPORTION_TEST,
    RESULTS,
    SHEET,
    T_TEST,
    TWO_PROPORTION_CI,
    UNPAIRED_CI,
    UNPAIRED_TEST,
    Z_TEST,
)

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]
TWO_SIGMA_ALPHA = 2 * stats.norm.sf(2)  # Dummies p. 192: '95 %' is the +/- 2 sigma level


def cells(values: dict[str, float], data_1: Sequence[float] = (), data_2: Sequence[float] = ()) -> dict[str, float]:
    """Input cells, plus raw data pasted into columns L and M from row 10."""
    mapped = {INPUTS[name]: v for name, v in values.items()}
    mapped |= {f"L{10 + i}": x for i, x in enumerate(data_1)}
    mapped |= {f"M{10 + i}": x for i, x in enumerate(data_2)}
    return mapped


def at(ws: Any, column: str, row: int) -> Any:
    """Cached value of one cell."""
    return ws[f"{column}{row}"].value


def test_one_sided_ci_for_the_mean_s03_we02(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Confidence Intervals.pdf p. 15: 20 values, HA mu < 10 at 2 %, one-sided 98 %-CI
    example = oracle["S03-WE02"]
    ws = evaluate(SHEET, cells({"alpha": 0.02, "mu0": 10}, data_1=example["given"]["data (n=20)"]))
    answers = example["stated_answers"]
    # act / assert -- Excel cached floats rel=1e-9; the bound printed ']-infinity, 9.98['
    assert ws[RESULTS["mean_used"]].value == pytest.approx(float(answers["X_bar (Excel cached)"]), rel=1e-9)
    assert ws[RESULTS["s_used"]].value == pytest.approx(float(answers["s (Excel cached, STDEV.S)"]), rel=1e-9)
    assert agrees_at_printed_precision(at(ws, "E", ONE_MEAN_CI["upper_only"]),
                                       printed("S03-WE02", "stated_answers", "one-sided 98%-CI (as printed on slide)", "9.98"))


def test_t_test_for_the_mean_s03_we04(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.pdf p. 12: same data, H0 mu = 10 vs HA mu < 10 at 2 %
    ws = evaluate(SHEET, cells({"alpha": 0.02, "mu0": 10}, data_1=oracle["S03-WE02"]["given"]["data (n=20)"]))
    answers, row = oracle["S03-WE04"]["stated_answers"], T_TEST["less"]
    stated = "stated_answers"
    # act / assert -- Excel cached floats rel=1e-9, slide values at printed precision
    assert at(ws, "B", row) == pytest.approx(float(answers["test statistic (Excel cached, exact)"]), rel=1e-9)
    assert at(ws, "C", row) == pytest.approx(float(answers["critical value (Excel cached, exact)"]), rel=1e-9)
    assert at(ws, "G", row) == pytest.approx(float(answers["p-value (Excel cached, exact, via T.DIST)"]), rel=1e-9)
    assert agrees_at_printed_precision(at(ws, "B", row), printed("S03-WE04", stated, "test statistic (as printed on slide, rounded)", "-2.95"))
    assert agrees_at_printed_precision(at(ws, "C", row), printed("S03-WE04", stated, "critical value (as printed on slide)", "-2.20"))
    assert agrees_at_printed_precision(at(ws, "G", row) * 100, printed("S03-WE04", stated, "p-value (as printed on slide)", "0.4"))
    assert at(ws, "H", row) == "reject H0"  # 'H0 cannot be accepted at 2% significance'


def test_z_test_with_known_sigma_s03_we10(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses Further Reading p. 10: mu0 1200, sigma 300, n 100, alpha 1 %, x-bar 1265
    ws = evaluate(SHEET, cells({"alpha": 0.01, "n": 100, "mean": 1265, "sigma": 300, "mu0": 1200}))
    stated = "stated_answers"
    # act / assert -- critical values on the x-bar scale as the course prints them; p-values in %
    assert agrees_at_printed_precision(at(ws, "E", Z_TEST["greater"]), printed("S03-WE10", stated, "kritische waarde (eenzijdig)", "1270"))
    assert agrees_at_printed_precision(at(ws, "E", Z_TEST["two_sided"]), printed("S03-WE10", stated, "kritische waarden (dubbelzijdig, alpha=1%)", "1123"))
    assert agrees_at_printed_precision(at(ws, "F", Z_TEST["two_sided"]), printed("S03-WE10", stated, "kritische waarden (dubbelzijdig, alpha=1%)", "1277"))
    assert agrees_at_printed_precision(at(ws, "G", Z_TEST["greater"]) * 100, printed("S03-WE10", stated, "p-waarde (eenzijdig) van 1265", "1.5"))
    assert agrees_at_printed_precision(at(ws, "G", Z_TEST["two_sided"]) * 100, printed("S03-WE10", stated, "p-waarde (dubbelzijdig)", "3.0"))
    assert at(ws, "H", Z_TEST["greater"]) == "do not reject H0" and at(ws, "H", Z_TEST["two_sided"]) == "do not reject H0"


def test_unpaired_shoe_sole_experiment_s03_we13(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- CI Further Reading p. 17: LD1 and LD2 of two independent groups of 10
    given = oracle["S03-WE13"]["given"]
    ws = evaluate(SHEET, cells({"alpha": 0.05}, data_1=given["LD1"], data_2=given["LD2"]))
    row, stated = UNPAIRED_CI["two_sided"], "stated_answers"
    # act / assert -- printed x1 28.7, s1 5.50, x2 34.3, s2 7.53, s_p 6.59, t 2.10, CI -5.6 +/- 6.19
    for name, key, value in (("mean1_used", "x1_bar", "28.7"), ("s1_used", "s1", "5.50"), ("mean2_used", "x2_bar", "34.3"),
                             ("s2_used", "s2", "7.53"), ("sp", "s_p", "6.59")):
        assert agrees_at_printed_precision(ws[RESULTS[name]].value, printed("S03-WE13", stated, key, value))
    assert agrees_at_printed_precision(at(ws, "E", row), printed("S03-WE13", stated, "t_18,0.025", "2.10"))
    assert agrees_at_printed_precision((at(ws, "B", row) + at(ws, "C", row)) / 2, printed("S03-WE13", stated, "BI95 voor mu1-mu2", "-5.6"))
    assert agrees_at_printed_precision(at(ws, "D", row), printed("S03-WE13", stated, "BI95 voor mu1-mu2", "6.19"))
    assert at(ws, "H", UNPAIRED_TEST["two_sided"]) == "do not reject H0"  # '0 in BI95 => geen verschil'


def test_paired_shoe_sole_experiment_s03_we14(oracle: dict[str, Any], printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- CI Further Reading p. 18: each boy wears both materials; pairs pasted row by row
    given = oracle["S03-WE14"]["given"]
    ws = evaluate(SHEET, cells({"alpha": 0.05}, data_1=given["LD1"], data_2=given["LD2"]))
    row, stated = PAIRED_CI["two_sided"], "stated_answers"
    # act / assert -- printed v-bar -3.3, s_v 2.41, t 2.26, CI -3.3 +/- 1.72
    assert agrees_at_printed_precision(ws[RESULTS["vbar_used"]].value, printed("S03-WE14", stated, "v_bar", "-3.3"))
    assert agrees_at_printed_precision(ws[RESULTS["sv_used"]].value, printed("S03-WE14", stated, "s_v", "2.41"))
    assert agrees_at_printed_precision(at(ws, "E", row), printed("S03-WE14", stated, "t_9,0.025", "2.26"))
    assert agrees_at_printed_precision(at(ws, "D", row), printed("S03-WE14", stated, "BI95 voor mu1-mu2", "1.72"))


@pytest.mark.parametrize(("example_id", "n", "x", "key", "low", "high", "scale"), [
    ("S03-WE15", 200, 120, "95% BI voor pi", "0.53", "0.67", 1),
    ("S03-WE01", 100, 4, "95% CI for lot fraction defectives", "1.1", "9.9", 100),
])
def test_exact_binomial_interval_for_a_proportion(example_id: str, n: int, x: int, key: str, low: str, high: str,
                                                  scale: int, printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- CI Further Reading p. 20 (cross-checked there with R binom.test) and Confidence Intervals.pdf p. 4
    ws = evaluate(SHEET, cells({"alpha": 0.05, "pn": n, "px": x}))
    row = PROPORTION_CI["two_sided"]
    # act / assert
    assert agrees_at_printed_precision(at(ws, "D", row) * scale, printed(example_id, "stated_answers", key, low))
    assert agrees_at_printed_precision(at(ws, "E", row) * scale, printed(example_id, "stated_answers", key, high))


def test_normal_approximation_for_a_proportion_s08_we12(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 197: 4 of 5 dentists, 90 % (Z = 1.645)
    ws = evaluate(SHEET, cells({"alpha": 0.10, "pn": 5, "px": 4}))
    row = PROPORTION_CI["two_sided"]
    # act / assert -- printed '4/5 +/- 0.294'
    half = (at(ws, "C", row) - at(ws, "B", row)) / 2
    assert agrees_at_printed_precision(half, printed("S08-WE12", "stated_answers", "CI", "0.294"))


def test_difference_of_two_proportions_s08_we13(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 197: Toledo 213/300, Buffalo 189/300, '95 %' with Z = 2 (p. 192)
    ws = evaluate(SHEET, cells({"alpha": TWO_SIGMA_ALPHA, "qn1": 300, "qx1": 213, "qn2": 300, "qx2": 189}))
    row, stated = TWO_PROPORTION_CI["two_sided"], "stated_answers"
    # act / assert -- printed '0.08 +/- 0.076, or equivalently [0.004, 0.156]': the difference agrees
    assert agrees_at_printed_precision(ws[RESULTS["qdiff"]].value, printed("S08-WE13", stated, "CI", "0.08"))
    assert at(ws, "D", row) == pytest.approx(0.0765, abs=5e-5)  # unrounded half-width, see the xfail below


@pytest.mark.xfail(reason="Dummies p. 197 truncates the half-width 0.0765 to 0.076 and builds [0.004, 0.156] from it; "
                          "unrounded: 0.0765, [0.0035, 0.1565] -> 0.077, [0.003, 0.157]")
def test_difference_of_two_proportions_bounds_s08_we13(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells({"alpha": TWO_SIGMA_ALPHA, "qn1": 300, "qx1": 213, "qn2": 300, "qx2": 189}))
    row, stated = TWO_PROPORTION_CI["two_sided"], "stated_answers"
    # act / assert
    assert agrees_at_printed_precision(at(ws, "D", row), printed("S08-WE13", stated, "CI", "0.076"))
    assert agrees_at_printed_precision(at(ws, "B", row), printed("S08-WE13", stated, "CI", "0.004"))
    assert agrees_at_printed_precision(at(ws, "C", row), printed("S08-WE13", stated, "CI", "0.156"))


@pytest.mark.parametrize("seed", [1, 2])
def test_every_block_matches_scipy(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    alpha = rng.choice([0.01, 0.02, 0.05, 0.10])
    n, mean, s, sigma, mu0 = rng.randint(3, 80), rng.uniform(-50, 50), rng.uniform(0.5, 9), rng.uniform(0.5, 9), rng.uniform(-50, 50)
    n1, m1, s1, n2, m2, s2 = rng.randint(3, 40), rng.uniform(0, 10), rng.uniform(0.5, 3), rng.randint(3, 40), rng.uniform(0, 10), rng.uniform(0.5, 3)
    npairs, vbar, sv = rng.randint(3, 40), rng.uniform(-3, 3), rng.uniform(0.5, 3)
    pn = rng.randint(20, 500)
    px, pi0 = rng.randint(1, pn - 1), rng.uniform(0.05, 0.95)
    qn1, qn2 = rng.randint(20, 500), rng.randint(20, 500)
    qx1, qx2 = rng.randint(1, qn1 - 1), rng.randint(1, qn2 - 1)
    ws = evaluate(SHEET, cells({"alpha": alpha, "n": n, "mean": mean, "s": s, "sigma": sigma, "mu0": mu0,
                                "n1": n1, "mean1": m1, "s1": s1, "n2": n2, "mean2": m2, "s2": s2,
                                "np": npairs, "vbar": vbar, "sv": sv, "pn": pn, "px": px, "pi0": pi0,
                                "qn1": qn1, "qx1": qx1, "qn2": qn2, "qx2": qx2}))
    z2, z1 = stats.norm.isf(alpha / 2), stats.norm.isf(alpha)
    t = stats.t(n - 1)
    se_z, se_t = sigma / math.sqrt(n), s / math.sqrt(n)
    sp = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    se_u, tu = sp * math.sqrt(1 / n1 + 1 / n2), stats.t(n1 + n2 - 2)
    se_p, tp = sv / math.sqrt(npairs), stats.t(npairs - 1)
    p = px / pn
    se_prop = math.sqrt(p * (1 - p) / pn)
    zp = (p - pi0) / math.sqrt(pi0 * (1 - pi0) / pn)
    q1, q2 = qx1 / qn1, qx2 / qn2
    qse = math.sqrt(q1 * (1 - q1) / qn1 + q2 * (1 - q2) / qn2)
    tz, tt = (mean - mu0) / se_z, (mean - mu0) / se_t
    tu_stat, tp_stat = (m1 - m2) / se_u, vbar / se_p
    expected = {
        ("B", ONE_MEAN_CI["two_sided"]): mean - z2 * se_z, ("C", ONE_MEAN_CI["upper_only"]): mean + z1 * se_z,
        ("D", ONE_MEAN_CI["two_sided"]): mean - t.isf(alpha / 2) * se_t, ("E", ONE_MEAN_CI["upper_only"]): mean + t.isf(alpha) * se_t,
        ("B", Z_TEST["greater"]): tz, ("G", Z_TEST["greater"]): stats.norm.sf(tz),
        ("G", Z_TEST["two_sided"]): 2 * stats.norm.sf(abs(tz)), ("E", Z_TEST["greater"]): mu0 + z1 * se_z,
        ("B", T_TEST["less"]): tt, ("G", T_TEST["less"]): t.cdf(tt), ("G", T_TEST["two_sided"]): 2 * t.sf(abs(tt)),
        ("C", T_TEST["less"]): -t.isf(alpha),
        ("B", UNPAIRED_CI["two_sided"]): (m1 - m2) - tu.isf(alpha / 2) * se_u,
        ("C", UNPAIRED_CI["upper_only"]): (m1 - m2) + tu.isf(alpha) * se_u,
        ("G", UNPAIRED_TEST["greater"]): tu.sf(tu_stat),
        ("B", PAIRED_CI["two_sided"]): vbar - tp.isf(alpha / 2) * se_p,
        ("B", PROPORTION_CI["two_sided"]): p - z2 * se_prop,
        ("D", PROPORTION_CI["two_sided"]): stats.beta.ppf(alpha / 2, px, pn - px + 1),
        ("E", PROPORTION_CI["two_sided"]): stats.beta.ppf(1 - alpha / 2, px + 1, pn - px),
        ("B", PROPORTION_TEST["greater"]): zp, ("G", PROPORTION_TEST["less"]): stats.norm.cdf(zp),
        ("B", TWO_PROPORTION_CI["two_sided"]): (q1 - q2) - z2 * qse, ("C", TWO_PROPORTION_CI["two_sided"]): (q1 - q2) + z2 * qse,
    }
    # act / assert -- rel=1e-9 covers LibreOffice vs scipy quantile round-off
    for (column, row), target in expected.items():
        assert at(ws, column, row) == pytest.approx(target, rel=1e-9), (column, row)
    assert ws[RESULTS["sp"]].value == pytest.approx(sp, rel=1e-12)
    assert at(ws, "B", 66) == pytest.approx(tu_stat, rel=1e-9) and at(ws, "B", 89) == pytest.approx(tp_stat, rel=1e-9)
