"""Tests for bbtools.sheet_extra (the book-only blocks), evaluated by LibreOffice headless.

These tests moved here with their blocks, unchanged in what they expect: from tests/test_sheet_sigma.py (DPU,
yields, RTY; Six Sigma For Dummies and Harry & Schroeder worked examples in inventory/worked_examples.json, at
printed precision via the `printed` fixture), from tests/test_sheet_capability.py (σ̂ = MR̄ / 1.128) and from
tests/test_sheet_charts.py (I-MR, p and u charts; Dummies S08-WE21). Printed values that disagree with the computation
are strict xfails naming the page; scipy and plain Python cross-check random inputs.
"""
from __future__ import annotations

import math
import random
import statistics
from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools.build_workbook import build_workbook
from bbtools.printed import agrees_at_printed_precision
from bbtools.sheet_extra import FIRST_INDIVIDUAL, FIRST_P, FIRST_U, IMR, INPUTS, RESULTS, SHEET, U_CHART

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]
libreoffice = pytest.mark.libreoffice


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names onto the sheet's input cells."""
    return {INPUTS[name]: v for name, v in values.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


def test_sheet_says_under_the_header_that_the_books_are_not_examinable() -> None:
    # arrange
    ws = build_workbook()[SHEET]
    # act / assert -- the user: these books are not to be known for the exam
    assert "niet te kennen voor het examen" in ws["A7"].value
    assert ws["A7"].font.bold


# ---------------------------------------------------------------- from Sigma & DPMO

@libreoffice
@pytest.mark.parametrize(("example_id", "given", "result_name", "key", "printed_value", "scale"), [
    ("S08-WE04", {"defects": 11, "units": 23}, "dpu", "DPU", "0.478", 1),
    ("S09-WE03", {"defects": 5, "units": 100}, "dpu", "Defects/unit", "5", 100),
    ("S09-WE03", {"defects": 5, "units": 100}, "ty", "Throughput yield", "95", 100),
])
def test_dpu_and_throughput_yield_examples(example_id: str, given: dict[str, float], result_name: str, key: str,
                                           printed_value: str, scale: int, printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 152 and Harry & Schroeder p. 5
    ws = evaluate(SHEET, cells(given))
    # act / assert
    assert agrees_at_printed_precision(value(ws, result_name) * scale,
                                       printed(example_id, "stated_answers", key, printed_value))


@libreoffice
def test_traditional_and_first_time_yield_s08_we01_we02(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 147-148: 352 cars in, 347 out, 5 scrapped, 98 reworked
    ws = evaluate(SHEET, cells({"units_in": 352, "units_out": 347, "scrapped": 5, "reworked": 98}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "y"), printed("S08-WE01", "stated_answers", "Y", "0.986"))
    assert agrees_at_printed_precision(value(ws, "fty"), printed("S08-WE02", "stated_answers", "FTY", "0.707"))


@libreoffice
@pytest.mark.xfail(reason="Dummies p. 148: '98.6% - 70.7% = 27.9%' subtracts rounded values; unrounded 27.84 %")
def test_hidden_factory_s08_we02(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells({"units_in": 352, "units_out": 347, "scrapped": 5, "reworked": 98}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "hidden_factory") * 100,
                                       printed("S08-WE02", "stated_answers", "hidden_factory", "27.9"))


@libreoffice
@pytest.mark.parametrize(("example_id", "steps", "printed_value"), [
    ("S08-WE03", [0.75, 0.95, 0.85, 0.95, 0.90], "0.518"),
    ("S09-WE04", [0.98, 0.93, 0.95, 0.98, 0.94], "0.7976"),
])
def test_rolled_throughput_yield_from_steps(example_id: str, steps: list[float], printed_value: str, printed: Printed,
                                            evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 149; Harry & Schroeder p. 5
    ws = evaluate(SHEET, cells({f"step_{i}": y for i, y in enumerate(steps, start=1)}))
    # act / assert
    assert value(ws, "n_steps") == len(steps)
    assert agrees_at_printed_precision(value(ws, "rty_steps"), printed(example_id, "stated_answers", "RTY", printed_value))


@libreoffice
def test_units_needed_for_one_good_unit_s09_we06(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Harry & Schroeder p. 5: RTY = 70 %
    ws = evaluate(SHEET, cells({"rty": 0.7}))
    # act / assert
    stated = "stated_answers"
    assert agrees_at_printed_precision(value(ws, "units_repairable"),
                                       printed("S09-WE06", stated, "Assuming defects are repairable", "1.3"))
    assert agrees_at_printed_precision(value(ws, "units_scrapped"),
                                       printed("S09-WE06", stated, "Assuming defectives are scrapped", "1.43"))


@libreoffice
@pytest.mark.xfail(reason="Harry & Schroeder p. 5 prints '(0.368)**(-10) = 0.9051'; the k-th root it defines gives 0.9049")
def test_normalized_yield_s09_we05(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- 10-step process, RTY 36.8 %
    ws = evaluate(SHEET, cells({"rty": 0.368, "steps": 10}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "ny"), printed("S09-WE05", "stated_answers", "NY", "0.9051"))


@libreoffice
@pytest.mark.parametrize(("k", "key", "printed_value"), [
    (2, "two_dice_defect_free_probability", "69"),
    (3, "three_dice_defect_free_probability", "58"),
])
def test_dice_rolled_throughput_yield_s07_we01(k: int, key: str, printed_value: str, printed: Printed,
                                               evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 38-39: no '1' on one die = 5/6
    ws = evaluate(SHEET, cells({"step_yield": 5 / 6, "k": k}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "rty_k") * 100, printed("S07-WE01", "stated_answers", key, printed_value))


@libreoffice
def test_hundred_dice_is_less_than_one_in_82_million_s07_we01(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    printed("S07-WE01", "stated_answers", "hundred_dice_defect_free_probability", "less than one in 82 million")
    # act
    ws = evaluate(SHEET, cells({"step_yield": 5 / 6, "k": 100}))
    # assert -- a statement, not a number: the probability is below 1/82 000 000
    assert value(ws, "rty_k") < 1 / 82_000_000
    assert value(ws, "one_in") > 82_000_000


@libreoffice
def test_yield_per_defect_opportunity_product_a_s09_we01(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Harry & Schroeder p. 3: product A, final yield 85 %, 600 opportunities
    ws = evaluate(SHEET, cells({"final_yield": 0.85, "defect_opportunities": 600}))
    stated = printed("S09-WE01", "stated_answers", "Product A avg yield per defect opportunity", "99.97")
    # act / assert -- '99.97% (or about 3.5 sigma)': the unshifted reading
    assert agrees_at_printed_precision(value(ws, "yield_per_defect_opportunity") * 100, stated)
    assert agrees_at_printed_precision(value(ws, "z_no_shift_from_yield"), "3.5")


@libreoffice
@pytest.mark.xfail(reason="Harry & Schroeder p. 3: product B '(0.968)**(1/48) = 99.97%'; computed 99.932 %")
def test_yield_per_defect_opportunity_product_b_s09_we01(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- product B, final yield 96.8 %, 48 opportunities
    ws = evaluate(SHEET, cells({"final_yield": 0.968, "defect_opportunities": 48}))
    stated = printed("S09-WE01", "stated_answers", "Product B avg yield per defect opportunity", "99.97")
    # act / assert
    assert agrees_at_printed_precision(value(ws, "yield_per_defect_opportunity") * 100, stated)


@libreoffice
@pytest.mark.parametrize("seed", [1, 2])
def test_every_yield_block_matches_an_independent_computation(seed: int, evaluate: Evaluate) -> None:
    # arrange -- same draws, in the same order, as the former Sigma & DPMO test, so each seed gives the same inputs
    # (o and z belong to blocks that stayed on Sigma & DPMO and are not used here)
    rng = random.Random(seed)
    d, n, _o = rng.randint(1, 50), rng.randint(50, 500), rng.randint(1, 30)
    _z = rng.uniform(1, 6)
    units_in = rng.randint(200, 1000)
    scrapped, reworked = rng.randint(0, 20), rng.randint(0, 100)
    steps = [rng.uniform(0.8, 1.0) for _ in range(rng.randint(2, 10))]
    p, k = rng.uniform(0.5, 1.0), rng.randint(1, 40)
    final, opps = rng.uniform(0.5, 1.0), rng.randint(2, 900)
    ws = evaluate(SHEET, cells({"defects": d, "units": n, "units_in": units_in, "units_out": units_in - scrapped,
                                "scrapped": scrapped, "reworked": reworked,
                                **{f"step_{i}": y for i, y in enumerate(steps, 1)},
                                "step_yield": p, "k": k, "final_yield": final, "defect_opportunities": opps}))
    rty = math.prod(steps)
    per_opportunity = final ** (1 / opps)
    # act / assert -- rel=1e-9: same arithmetic, LibreOffice vs scipy normal functions
    expected = {
        "dpu": d / n, "ty": 1 - d / n, "rty_from_dpu": math.exp(-d / n),
        "y": (units_in - scrapped) / units_in, "fty": (units_in - scrapped - reworked) / units_in,
        "rty_steps": rty, "ny_steps": rty ** (1 / len(steps)), "rty_used": rty, "ny": rty ** (1 / len(steps)),
        "dpu_from_rty": -math.log(rty), "units_repairable": 2 - rty, "units_scrapped": 1 / rty,
        "rty_k": p**k, "yield_per_defect_opportunity": per_opportunity,
        "dpmo_from_yield": (1 - per_opportunity) * 1e6, "z_no_shift_from_yield": stats.norm.ppf(per_opportunity),
    }
    for name, target in expected.items():
        assert value(ws, name) == pytest.approx(target, rel=1e-9), name


# ---------------------------------------------------------------- from Capability: σ̂ = MR̄ / 1.128

@libreoffice
def test_mr_bar_uses_d2_for_n_2_from_the_tables_sheet(evaluate: Evaluate) -> None:
    # arrange -- MR uses d2 for n = 2, 1.128 (Table 18)
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 10, "mean": 5, "mrbar": 1.128}))
    # act / assert
    assert value(ws, "sigma_mr") == pytest.approx(1.0)


@libreoffice
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_mr_bar_capability_matches_scipy_for_random_inputs(seed: int, evaluate: Evaluate) -> None:
    # arrange -- same draws, in the same order, as the former Capability test, so each seed gives the same MR̄ input
    rng = random.Random(seed)
    lsl = rng.uniform(-50, 50)
    usl = lsl + rng.uniform(1, 40)
    mean = rng.uniform(lsl - 5, usl + 5)
    rng.choice([2, 3, 4, 5, 6, 8, 10, 15, 20, 25])  # n: R̄ and s̄ rows, which stayed on Capability
    raw = {"sigma_given": rng.uniform(0.1, 10), "rbar": rng.uniform(0.1, 10), "sbar": rng.uniform(0.1, 10),
           "mrbar": rng.uniform(0.1, 10), "s_overall": rng.uniform(0.1, 10)}
    ws = evaluate(SHEET, cells({"lsl": lsl, "usl": usl, "mean": mean, "mrbar": raw["mrbar"]}))
    # act / assert -- sigma uses the sheet's own looked-up d2 (checked in test_constants)
    sigma = value(ws, "sigma_mr")
    expected_below = stats.norm.cdf(lsl, loc=mean, scale=sigma)
    expected_above = stats.norm.sf(usl, loc=mean, scale=sigma)
    # same formula on the same inputs; rel=1e-9 covers LibreOffice's normal cdf vs scipy's
    assert value(ws, "cp") == pytest.approx((usl - lsl) / (6 * sigma), rel=1e-9)
    assert value(ws, "cpk") == pytest.approx(min(usl - mean, mean - lsl) / (3 * sigma), rel=1e-9)
    assert value(ws, "below_lsl") == pytest.approx(expected_below, rel=1e-9, abs=1e-300)
    assert value(ws, "above_usl") == pytest.approx(expected_above, rel=1e-9, abs=1e-300)
    assert value(ws, "out_total") == pytest.approx(expected_below + expected_above, rel=1e-9, abs=1e-300)


@libreoffice
def test_mr_bar_results_stay_empty_until_mr_bar_is_filled(evaluate: Evaluate) -> None:
    # arrange -- limits and mean, no MR̄
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 6, "mean": 3}))
    # act / assert
    assert value(ws, "sigma_mr") is None and value(ws, "cp") is None


# ---------------------------------------------------------------- from Control charts: I-MR, p chart, u chart

def u_chart_cells(oracle: dict[str, Any]) -> dict[str, float]:
    """Dummies p. 256 data table: subgroup sizes and defects of 20 subgroups."""
    rows = oracle["S08-WE21"]["given"]["data_table"]["rows"]
    return {**{f"B{FIRST_U + i}": size for i, (_, size, _) in enumerate(rows)},
            **{f"C{FIRST_U + i}": defects for i, (_, _, defects) in enumerate(rows)}}


@libreoffice
def test_dummies_u_chart_s08_we21(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- insurance claim forms, 20 subgroups; the chart shows the limits of the last subgroup (n = 65)
    answers = oracle["S08-WE21"]["stated_answers"]
    ws = evaluate(SHEET, u_chart_cells(oracle))
    last = FIRST_U + 19
    # act / assert -- printed 'ubar = 1.870' and '-3.0SL = 1.361'
    assert agrees_at_printed_precision(ws[U_CHART["ubar"]].value, str(answers["ubar"]))
    assert agrees_at_printed_precision(ws[f"E{last}"].value, str(answers["LCL_neg3.0SL"]))


@libreoffice
@pytest.mark.xfail(reason="Dummies p. 256 prints the upper limit as '2379' (no decimal point); computed 2.379")
def test_dummies_u_chart_upper_limit_s08_we21(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, u_chart_cells(oracle))
    # act / assert
    assert agrees_at_printed_precision(ws[f"F{FIRST_U + 19}"].value, "2379")


@libreoffice
@pytest.mark.parametrize("seed", [1, 2])
def test_imr_p_and_u_charts_match_an_independent_computation(seed: int, evaluate: Evaluate) -> None:
    # arrange -- same draws, in the same order, as the former Control charts test, so each seed gives the same inputs
    # (n and the subgroups belong to the X̄-R / X̄-s charts, which stayed on Regelkaarten)
    rng = random.Random(seed)
    n = rng.choice([2, 3, 4, 5, 6, 8, 10])
    _subgroups = [[rng.gauss(50, 3) for _ in range(n)] for _ in range(rng.randint(5, 30))]
    individuals = [rng.gauss(10, 1) for _ in range(rng.randint(5, 60))]
    p_rows = [(rng.randint(50, 200), rng.randint(0, 20)) for _ in range(rng.randint(5, 30))]
    u_rows = [(rng.randint(20, 80), rng.randint(20, 150)) for _ in range(rng.randint(5, 30))]
    cells_in = {f"B{FIRST_INDIVIDUAL + i}": x for i, x in enumerate(individuals)}
    cells_in |= {f"B{FIRST_P + i}": size for i, (size, _) in enumerate(p_rows)}
    cells_in |= {f"C{FIRST_P + i}": d for i, (_, d) in enumerate(p_rows)}
    cells_in |= {f"B{FIRST_U + i}": size for i, (size, _) in enumerate(u_rows)}
    cells_in |= {f"C{FIRST_U + i}": c for i, (_, c) in enumerate(u_rows)}
    ws = evaluate(SHEET, cells_in)
    mrs = [abs(b - a) for a, b in zip(individuals, individuals[1:])]
    xbar_i, mrbar = statistics.mean(individuals), statistics.mean(mrs)
    e2 = ws[f"F{IMR['x_row']}"].value
    pbar = sum(d for _, d in p_rows) / sum(size for size, _ in p_rows)
    ubar = sum(c for _, c in u_rows) / sum(size for size, _ in u_rows)
    # act / assert -- same arithmetic in Python; rel=1e-9 covers summation order
    assert ws[f"D{IMR['x_row']}"].value == pytest.approx(xbar_i + e2 * mrbar, rel=1e-9)
    assert ws[f"D{IMR['mr_row']}"].value == pytest.approx(ws[f"G{IMR['mr_row']}"].value * mrbar, rel=1e-9)
    for i, (size, d) in enumerate(p_rows):
        half = 3 * (pbar * (1 - pbar) / size) ** 0.5
        assert ws[f"F{FIRST_P + i}"].value == pytest.approx(pbar + half, rel=1e-9)
        assert ws[f"E{FIRST_P + i}"].value == pytest.approx(max(0.0, pbar - half), rel=1e-9, abs=1e-12)
    for i, (size, c) in enumerate(u_rows):
        assert ws[f"F{FIRST_U + i}"].value == pytest.approx(ubar + 3 * (ubar / size) ** 0.5, rel=1e-9)
