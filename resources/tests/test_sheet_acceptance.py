"""Tests for bbtools.sheet_acceptance, evaluated by LibreOffice headless.

Expected values: course worked examples (Testing of Hypotheses.xlsx cached floats at rel=1e-9; Ottoy slide and
Further Reading values at printed precision). AOQ is checked against the course's second formula on the same page
(Further Reading p. 10: AOQ(p) = Σ_{i≤c} (p − i/N) h(i; N, [Np], n)) computed in Python, OC against scipy.stats.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools.printed import agrees_at_printed_precision
from bbtools.sheet_acceptance import INPUTS, RESULTS, SHEET, TABLE_FIRST, TABLE_ROWS

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names onto the sheet's input cells."""
    return {INPUTS[name]: v for name, v in values.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


@pytest.mark.parametrize(("n", "c", "key"), [(100, 4, "P[d<=4] at pi=0.02 (n=100,c=4)"),
                                             (130, 5, "P[d<=5] at pi=0.02 (n=130,c=5)")])
def test_binomial_oc_at_aql_s03_we20(n: int, c: int, key: str, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.xlsx 'OC-curve (binomial)', AQL 2 %
    ws = evaluate(SHEET, cells({"n": n, "c": c, "aql": 0.02}))
    # act / assert -- Excel cached float, rel=1e-9
    assert value(ws, "oc_binom_aql") == pytest.approx(float(oracle["S03-WE20"]["stated_answers"][key]), rel=1e-9)


def test_risks_of_plan_100_4_s03_we06(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.pdf p. 5: plan (100, 4), AQL 2 %, bad lot 8 %
    ws = evaluate(SHEET, cells({"n": 100, "c": 4, "aql": 0.02, "lql": 0.08}))
    stated = "stated_answers"
    # act / assert -- printed '≅ 95%', 'alpha 5%', 'beta 9%'
    assert agrees_at_printed_precision(value(ws, "oc_binom_aql") * 100, printed("S03-WE06", stated, "P[d<=4] under H0 (pi=2%)", "95"))
    assert agrees_at_printed_precision(value(ws, "alpha_binom") * 100, printed("S03-WE06", stated, "alpha (for limit case pi=AQL=2%)", "5"))
    assert agrees_at_printed_precision(value(ws, "beta_binom") * 100, printed("S03-WE06", stated, "beta (for pi=8%)", "9"))


def test_alpha_of_plan_100_5_s03_we06(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- same page: 'c=5 => alpha=1.5%'
    ws = evaluate(SHEET, cells({"n": 100, "c": 5, "aql": 0.02}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "alpha_binom") * 100,
                                       printed("S03-WE06", "stated_answers", "critical value if alpha reduced", "1.5"))


def test_larger_plan_keeps_alpha_and_lowers_beta_s03_we07(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Testing of Hypotheses.pdf p. 8: plan (130, 5)
    ws = evaluate(SHEET, cells({"n": 130, "c": 5, "aql": 0.02, "lql": 0.08}))
    stated = "stated_answers"
    # act / assert -- 'alpha maintained 5%', 'beta reduced to 5%'
    assert agrees_at_printed_precision(value(ws, "alpha_binom") * 100, printed("S03-WE07", stated, "alpha maintained", "5"))
    assert agrees_at_printed_precision(value(ws, "beta_binom") * 100, printed("S03-WE07", stated, "beta at n=130 (after)", "5"))


@pytest.mark.parametrize(("n", "c", "key"), [(100, 4, "P[d<=4] at pi=0.02 (N=10000,n=100,c=4) hypergeometric"),
                                             (5000, 111, "P[d<=111] at pi=0.02 (N=10000,n=5000,c=111)")])
def test_hypergeometric_oc_at_aql_s03_we21(n: int, c: int, key: str, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- 'OC-curve (hypergeometric)': N = 10000, AQL 2 % -> M = [Np] = 200
    ws = evaluate(SHEET, cells({"n": n, "c": c, "N": 10000, "aql": 0.02}))
    # act / assert -- Excel cached float, rel=1e-9
    assert value(ws, "oc_hyp_aql") == pytest.approx(float(oracle["S03-WE21"]["stated_answers"][key]), rel=1e-9)


def test_peach_plan_164_2_meets_its_targets_s04_we12(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Further Reading p. 4: (0.5 %, 95 %) and (3.5 %, 5 %) -> c = 2, n = 164 from the Peach table
    printed("S04-WE12", "stated_answers", "n", "164")
    printed("S04-WE12", "stated_answers", "c", "2")
    ws = evaluate(SHEET, cells({"n": 164, "c": 2, "aql": 0.005, "lql": 0.035}))
    # act / assert -- the plan's OC at p1, at the printed precision of the target
    assert agrees_at_printed_precision(value(ws, "oc_binom_aql") * 100, printed("S04-WE12", "given", "1-alpha (target OC at p1)", "95"))


@pytest.mark.xfail(reason="Further Reading p. 4: the Peach plan (164, 2) gives OC(3.5 %) = 7.1 % (binomial), not the "
                          "5 % target; the page calls the method approximate")
def test_peach_plan_164_2_consumer_risk_s04_we12(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells({"n": 164, "c": 2, "aql": 0.005, "lql": 0.035}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "beta_binom") * 100, printed("S04-WE12", "given", "beta (target OC at p2)", "5"))


def test_aoql_of_plan_250_5_in_lots_of_1000_s04_we18(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Further Reading p. 10: 'AOQL approximately 1.3 %, at about 1.8 %'; a 0.001 table step
    ws = evaluate(SHEET, cells({"n": 250, "c": 5, "N": 1000, "step": 0.001}))
    stated = "stated_answers"
    # act / assert -- printed to one decimal of a percent; the course value is the approximation p·OC(p)
    assert agrees_at_printed_precision(value(ws, "aoql_approx") * 100, printed("S04-WE18", stated, "AOQL", "1.3"))


@pytest.mark.xfail(reason="Further Reading p. 10: the exact AOQ formula on the slide gives AOQL 1.03 % for (250, 5), "
                          "N = 1000; the stated 1.3 % is the approximation p·OC(p) although n/N = 0.25")
def test_exact_aoql_of_plan_250_5_s04_we18(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells({"n": 250, "c": 5, "N": 1000, "step": 0.001}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "aoql") * 100, printed("S04-WE18", "stated_answers", "AOQL", "1.3"))


@pytest.mark.xfail(reason="Further Reading p. 10: 'at about 1.8 %' read off the chart; the AOQ maximum lies at 1.7 % "
                          "(exact and approximate, table step 0.001)")
def test_p_at_aoql_of_plan_250_5_s04_we18(printed: Printed, evaluate: Evaluate) -> None:
    # arrange
    ws = evaluate(SHEET, cells({"n": 250, "c": 5, "N": 1000, "step": 0.001}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "p_at_aoql_approx") * 100,
                                       printed("S04-WE18", "stated_answers", "original % defectives at which AOQL occurs", "1.8"))


def test_variables_plan_s04_we16(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Further Reading p. 9: p0 0.5 %, 1 - alpha 95 %, pt 3.5 %, beta 5 %
    ws = evaluate(SHEET, cells({"aql": 0.005, "lql": 0.035, "alpha": 0.05, "beta": 0.05}))
    # act / assert -- printed 'k = 2.1939', 'n = 64'
    assert agrees_at_printed_precision(value(ws, "k"), printed("S04-WE16", "stated_answers", "k", "2.1939"))
    assert value(ws, "n_up") == int(printed("S04-WE16", "stated_answers", "n", "64"))


def aoq_by_sum(p: float, n: int, c: int, lot: int) -> float:
    """Further Reading p. 10, second form: AOQ(p) = sum over i <= c of (p - i/N) h(i; N, [Np], n)."""
    defectives = int(p * lot)
    h = stats.hypergeom(lot, defectives, n)
    return sum((p - i / lot) * h.pmf(i) for i in range(c + 1))


@pytest.mark.parametrize("seed", [1, 2])
def test_oc_aoq_ati_table_matches_independent_formulas(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    lot = 1000 * rng.randint(1, 5)  # N·p whole for every table p: then the slide's AOQ equals the sum form exactly
    n, c = rng.randint(10, lot // 4), rng.randint(0, 8)
    step = rng.choice([0.002, 0.005, 0.01])
    ws = evaluate(SHEET, cells({"n": n, "c": c, "N": lot, "step": step}))
    # act / assert -- every table row; rel=1e-9 plus a tiny abs for values that underflow to ~0
    for i in range(TABLE_ROWS + 1):
        r, p = TABLE_FIRST + i, i * step
        oc_b = stats.binom.cdf(c, n, p)
        oc_h = stats.hypergeom(lot, int(p * lot), n).cdf(c)
        assert ws[f"B{r}"].value == pytest.approx(oc_b, rel=1e-9, abs=1e-15)
        assert ws[f"C{r}"].value == pytest.approx(oc_h, rel=1e-9, abs=1e-15)
        assert ws[f"E{r}"].value == pytest.approx(aoq_by_sum(p, n, c, lot), rel=1e-9, abs=1e-15)
        assert ws[f"F{r}"].value == pytest.approx(n * oc_h + lot * (1 - oc_h), rel=1e-9)
        assert ws[f"D{r}"].value == pytest.approx(p * oc_h, rel=1e-9, abs=1e-15)
