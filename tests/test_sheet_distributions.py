"""Tests for bbtools.sheet_distributions, evaluated by LibreOffice headless.

Expected values: course worked examples S04-WE02 (Acceptance Sampling.xlsm 'defective probabilities'),
S03-WE19 ('sampling distribution d') and S03-WE21 ('OC-curve (hypergeometric)'), Excel cached floats compared
with rel=1e-9; scipy.stats for every block with random inputs (the only check for Bernoulli, Poisson,
exponential and uniform, which have no course worked example).
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools.sheet_distributions import INPUTS, RESULTS, SHEET

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names onto the sheet's input cells."""
    return {INPUTS[name]: v for name, v in values.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


@pytest.mark.parametrize(("p_key", "mean_key"), [
    ("C3 (3sigma, 1-B3, fraction defective)", "J1 (=SUM(F*G), E[i] for 3sigma)"),
    ("C4 (4sigma, fraction defective)", "K1 (=SUM(F*H), E[i] for 4sigma)"),
])
def test_expected_defectives_in_a_lot_s04_we02(p_key: str, mean_key: str, oracle: dict[str, Any],
                                               evaluate: Evaluate) -> None:
    # arrange -- Acceptance Sampling.xlsm: lot N = 10000, fraction defective of a 3-sigma / 4-sigma process
    answers = oracle["S04-WE02"]["stated_answers"]
    ws = evaluate(SHEET, cells({"bin_n": 10000, "bin_p": float(answers[p_key])}))
    # act / assert -- the workbook sums i*P[i] over i = 0..100, which equals n*p to float round-off (rel=1e-9)
    assert value(ws, "bin_mean") == pytest.approx(float(answers[mean_key]), rel=1e-9)


def test_binomial_cumulative_probability_s03_we19(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.xlsx: n = 100, lot with 2 % defectives, P[d <= 4]
    stated = oracle["S03-WE19"]["stated_answers"]["P[d<=4] for P=2% (sum C6:C10, cross-checked)"]
    ws = evaluate(SHEET, cells({"bin_n": 100, "bin_p": 0.02, "bin_k": 4}))
    # act / assert -- Excel cached float, rel=1e-9
    assert value(ws, "bin_le") == pytest.approx(float(stated.split()[0]), rel=1e-9)


@pytest.mark.parametrize(("n", "k", "key"), [
    (100, 4, "P[d<=4] at pi=0.02 (N=10000,n=100,c=4) hypergeometric"),
    (5000, 111, "P[d<=111] at pi=0.02 (N=10000,n=5000,c=111)"),
])
def test_hypergeometric_oc_values_s03_we21(n: int, k: int, key: str, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- 'OC-curve (hypergeometric)': N = 10000, pi = 2 % -> D = 200 defectives in the lot
    ws = evaluate(SHEET, cells({"hyp_N": 10000, "hyp_D": 200, "hyp_n": n, "hyp_k": k}))
    # act / assert -- Excel cached float, rel=1e-9
    assert value(ws, "hyp_le") == pytest.approx(float(oracle["S03-WE21"]["stated_answers"][key]), rel=1e-9)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_every_block_matches_scipy(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    bern_p = rng.uniform(0, 1)
    bin_n, bin_p = rng.randint(1, 500), rng.uniform(0.001, 0.5)
    bin_k = rng.randint(0, bin_n)
    hyp_N = rng.randint(50, 5000)
    hyp_D, hyp_n = rng.randint(1, hyp_N // 2), rng.randint(1, hyp_N // 2)
    hyp_k = rng.randint(0, min(hyp_D, hyp_n))
    lam, poi_k = rng.uniform(0.1, 300), rng.randint(0, 400)
    rate, t = rng.uniform(0.1, 200), rng.uniform(0, 0.1)
    a = rng.uniform(-10, 10)
    b, x = a + rng.uniform(0.1, 20), a + rng.uniform(-2, 25)
    ws = evaluate(SHEET, cells({"bern_p": bern_p, "bin_n": bin_n, "bin_p": bin_p, "bin_k": bin_k,
                                "hyp_N": hyp_N, "hyp_D": hyp_D, "hyp_n": hyp_n, "hyp_k": hyp_k,
                                "poi_lambda": lam, "poi_k": poi_k, "exp_rate": rate, "exp_t": t,
                                "uni_a": a, "uni_b": b, "uni_x": x}))
    binom, hyper, poisson = stats.binom(bin_n, bin_p), stats.hypergeom(hyp_N, hyp_D, hyp_n), stats.poisson(lam)
    expon, uniform = stats.expon(scale=1 / rate), stats.uniform(a, b - a)
    expected = {
        "bern_mean": bern_p, "bern_var": bern_p * (1 - bern_p),
        "bin_mean": binom.mean(), "bin_var": binom.var(), "bin_sd": binom.std(), "bin_pk": binom.pmf(bin_k),
        "bin_le": binom.cdf(bin_k), "bin_ge": binom.sf(bin_k - 1),
        "hyp_mean": hyper.mean(), "hyp_var": hyper.var(), "hyp_pk": hyper.pmf(hyp_k), "hyp_le": hyper.cdf(hyp_k),
        "hyp_ge": hyper.sf(hyp_k - 1),
        "poi_mean": poisson.mean(), "poi_var": poisson.var(), "poi_pk": poisson.pmf(poi_k), "poi_le": poisson.cdf(poi_k),
        "poi_ge": poisson.sf(poi_k - 1),
        "exp_mean": expon.mean(), "exp_var": expon.var(), "exp_le": expon.cdf(t), "exp_gt": expon.sf(t),
        "uni_mean": uniform.mean(), "uni_var": uniform.var(), "uni_le": uniform.cdf(x),
    }
    # act / assert -- rel=1e-9 for library round-off; abs=1e-12 because 1 - cdf loses digits when the tail is tiny
    for name, target in expected.items():
        assert value(ws, name) == pytest.approx(target, rel=1e-9, abs=1e-12), name


def test_empty_inputs_leave_every_result_empty(evaluate: Evaluate) -> None:
    # act
    ws = evaluate(SHEET, {})
    # assert
    assert [name for name in RESULTS if value(ws, name) is not None] == []
