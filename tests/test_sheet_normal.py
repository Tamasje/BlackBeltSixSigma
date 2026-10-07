"""Tests for bbtools.sheet_normal, evaluated by LibreOffice headless.

Expected values: course worked examples S06-WE09 (__NormVerdeling Excel functies.xlsx, Excel cached floats,
rel=1e-9) and S06-WE10 (deck p. 19 notes, printed precision); the 68-95-99.7 rule (deck p. 19, printed
precision); the course Z table (___1.1 Ztable.pdf, printed precision); scipy.stats for random inputs.
"""
from __future__ import annotations

import csv
import random
from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools.constants import CONSTANTS_DIR
from bbtools.printed import agrees_at_printed_precision
from bbtools.sheet_normal import INPUTS, RESULTS, SHEET

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names onto the sheet's input cells."""
    return {INPUTS[name]: value for name, value in values.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


def test_norm_inv_and_norm_dist_workbook_s06_we09(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- mean 20, spread 0.5, '1 % afkeur (bovengrens)'; check value x = 21.1632
    given, answers = oracle["S06-WE09"]["given"], oracle["S06-WE09"]["stated_answers"]
    inputs = {"mu": float(given["Gemiddelde"]), "sigma": float(given["Spreiding"]), "p": 0.01, "x": 21.1632}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert -- Excel cached floats; rel=1e-9 allows LibreOffice's and Excel's inverse normal to differ in round-off
    assert value(ws, "x_upper_tail") == pytest.approx(float(answers["Norm.Inv(0.99,20,0.5)"]), rel=1e-9)
    assert value(ws, "below_x") == pytest.approx(float(answers["Norm.verd(21.1632,20,0.5,cumulatief=WAAR) check"]),
                                                 rel=1e-9)


def test_three_sigma_shoe_sizes_s06_we10(printed: Printed, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 19 notes: mean 42,5, spread 2,5, bounds 42,5 -/+ 3.2,5
    given = oracle["S06-WE10"]["given"]
    ws = evaluate(SHEET, cells({"mu": 42.5, "sigma": 2.5, "k": 3}))
    assert (given["gemiddelde"], given["spreiding"]) == ("42,5", "2,5")
    # act / assert -- printed '35 (42,5 - 3.2,5)' and '50 (42,5 + 3.2,5)'
    assert agrees_at_printed_precision(value(ws, "mu_minus_k"), printed("S06-WE10", "stated_answers", "3_sigma_ondergrens_grof", "35"))
    assert agrees_at_printed_precision(value(ws, "mu_plus_k"), printed("S06-WE10", "stated_answers", "3_sigma_bovengrens_grof", "50"))


def test_68_95_99_7_rule_of_deck_page_18(evaluate: Evaluate) -> None:
    # arrange -- deck p. 19: P[mu-sigma <= X <= mu+sigma] ~= 68 %, 2 sigma ~= 95 %, 3 sigma ~= 99.7 %
    ws = evaluate(SHEET, {})
    # act / assert -- printed precision
    assert agrees_at_printed_precision(value(ws, "rule_1") * 100, "68")
    assert agrees_at_printed_precision(value(ws, "rule_2") * 100, "95")
    assert agrees_at_printed_precision(value(ws, "rule_3") * 100, "99.7")


@pytest.mark.parametrize("z", [-3.41, -1.96, -0.5, 0.0, 1.0, 1.64, 2.33, 3.09])
def test_standard_normal_matches_the_course_z_table(z: float, evaluate: Evaluate) -> None:
    # arrange -- ___1.1 Ztable.pdf: row = z to one decimal, column = second decimal (subtracted for negative z)
    entry = z_table_entry(z)
    # act
    ws = evaluate(SHEET, cells({"mu": 0, "sigma": 1, "x": z}))
    # assert -- the table prints 4 decimals with a leading dot
    assert agrees_at_printed_precision(value(ws, "below_x"), entry)


def z_table_entry(z: float) -> str:
    """Printed Z-table value for z (two decimals), read from the transcribed course table."""
    row, column = f"{int(z * 10) / 10:.1f}", f".0{round(abs(z) * 100) % 10}"
    if z < 0 and row == "0.0":
        row = "-0.0"
    for stem in ("S06_standard_normal_probabilities_table_entry_area_to_the_left_o",
                 "S06_standard_normal_probabilities_table_entry_area_to_the_left_o_2"):
        with (CONSTANTS_DIR / f"{stem}.csv").open(encoding="utf-8", newline="") as fh:
            for record in csv.DictReader(fh):
                if record["z"] == row:
                    return record[column]
    raise KeyError(z)


@pytest.mark.parametrize("seed", [1, 2])
def test_every_block_matches_scipy_for_random_inputs(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    mu, sigma = rng.uniform(-100, 100), rng.uniform(0.1, 20)
    x, a = mu + rng.uniform(-3, 3) * sigma, mu - rng.uniform(0.1, 2) * sigma
    b, p, k = mu + rng.uniform(0.1, 2) * sigma, rng.uniform(0.001, 0.2), rng.uniform(0.5, 4)
    limit, f = mu - rng.uniform(0.5, 3) * sigma, rng.uniform(0.001, 0.3)
    ws = evaluate(SHEET, cells({"mu": mu, "sigma": sigma, "x": x, "a": a, "b": b, "p": p, "k": k,
                                "limit": limit, "fraction": f}))
    norm = stats.norm(mu, sigma)
    # act / assert -- same quantities by an independent implementation; rel=1e-9 covers library round-off
    expected = {
        "z": (x - mu) / sigma, "below_x": norm.cdf(x), "above_x": norm.sf(x),
        "between": norm.cdf(b) - norm.cdf(a), "outside": norm.cdf(a) + norm.sf(b),
        "x_lower_tail": norm.ppf(p), "x_upper_tail": norm.isf(p),
        "central_low": norm.ppf(p / 2), "central_high": norm.isf(p / 2),
        "mu_minus_k": mu - k * sigma, "mu_plus_k": mu + k * sigma,
        "inside_k": 1 - 2 * stats.norm.sf(k), "outside_k": 2 * stats.norm.sf(k),
        "sigma_if_below": (limit - mu) / stats.norm.ppf(f), "var_if_below": ((limit - mu) / stats.norm.ppf(f)) ** 2,
        "mu_if_below": limit - sigma * stats.norm.ppf(f), "mu_if_above": limit - sigma * stats.norm.isf(f),
    }
    for name, target in expected.items():
        assert value(ws, name) == pytest.approx(target, rel=1e-9), name
    # the limit lies below the mean, so 'f above L' cannot give a positive sigma
    assert value(ws, "sigma_if_above") == "niet mogelijk: L ligt aan de andere kant"


def test_sigma_from_tail_fraction_like_exam_q6(evaluate: Evaluate) -> None:
    # arrange -- exam Q6 situation (no answer key): 2 in 40 below 720 microfarad, mean 820
    ws = evaluate(SHEET, cells({"mu": 820, "limit": 720, "fraction": 2 / 40}))
    # act
    sigma = value(ws, "sigma_if_below")
    # assert -- independent: sigma = (720 - 820) / z_0.05
    assert sigma == pytest.approx(-100 / stats.norm.ppf(0.05), rel=1e-9)
    assert value(ws, "var_if_below") == pytest.approx(sigma**2, rel=1e-12)


def test_empty_inputs_leave_every_result_empty(evaluate: Evaluate) -> None:
    # act
    ws = evaluate(SHEET, {})
    # assert -- the rule table (section 6) needs no input; everything else waits for inputs
    assert [name for name in RESULTS if not name.startswith("rule_") and value(ws, name) is not None] == []
