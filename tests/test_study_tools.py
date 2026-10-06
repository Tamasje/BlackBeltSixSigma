"""Tests for the study guide's calculators (study/assets/stats.js and calc.js), run in node.

Expected values: course worked examples from the oracle (S03-WE13, S03-WE20, S03-WE21, S04-WE16, S04-WE18, S05-WE01,
S05-WE07, S05-WE17, S06-WE03, S10-WE02, S10-WE03) on the course's own data, the course sigma tables, and independent
scipy / statsmodels computations for random inputs. The calculators port the workbook's formulas, so the same
course pages and conventions apply (build/README.md).
"""
from __future__ import annotations

import csv
import functools
import importlib.util
import itertools
import json
import math
import random
import shutil
import subprocess
import sys
from typing import Any

import numpy as np
import openpyxl
import pandas as pd
import pytest
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from bbtools.constants import ROOT, USED_TABLE, load_all, load_average_range_table
from bbtools.printed import agrees_at_printed_precision

ASSETS = ROOT / "study" / "assets"
CONSTANTS_DIR = ROOT / "inventory" / "constants"
COURSE = ROOT / "source" / "course"
GRR_WORKBOOK = COURSE / "Les 5" / "20260619_ottoy_GRR - ANOVA - avegage and range - 2.xlsx"
# The GRR workbook types the interaction SS rounded ('=412.5+296.667'); 1e-5 allows exactly that (test_sheet_grr.py).
TYPED_ROUNDING = 1e-5


@functools.lru_cache(maxsize=None)
def build_module() -> Any:
    """study/build_study.py as a module (it is a script, not part of the bbtools package)."""
    spec = importlib.util.spec_from_file_location("build_study", ROOT / "study" / "build_study.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclasses look their module up while being created
    spec.loader.exec_module(module)
    return module


def finite(value: Any) -> Any:
    """Undo the node side's encoding of ±Infinity and NaN as strings."""
    if isinstance(value, dict):
        return {k: finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite(v) for v in value]
    if value in ("Infinity", "-Infinity", "NaN"):
        return float(value.replace("Infinity", "inf"))
    return value


def run_js(calls: list[tuple[str, list[Any]]]) -> list[Any]:
    """Evaluate Calc.<name>(*args) or Stats.<name>(*args) in node, in order. "@K" / "@M" stand for the constant tables."""
    node = shutil.which("node")
    assert node, "node is needed to test the study guide's calculators"
    script = f"""
global.Stats = require({json.dumps(str(ASSETS / "stats.js"))});
const Calc = require({json.dumps(str(ASSETS / "calc.js"))});
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const T = Calc.tables(input.constants);
const out = input.calls.map(([name, args]) => {{
  const [lib, fn] = name.split('.');
  const real = args.map(a => a === '@K' ? T.K : a === '@M' ? T.M : a);
  return (lib === 'Stats' ? Stats : Calc)[fn](...real);
}});
process.stdout.write(JSON.stringify(out, (k, v) => typeof v === 'number' && !isFinite(v) ? String(v) : v));
"""
    payload = json.dumps({"constants": build_module().constants_data(), "calls": calls})
    result = subprocess.run([node, "-e", script], input=payload, capture_output=True, text=True, check=True)
    return finite(json.loads(result.stdout))


def course_rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table extracted to inventory/constants/<stem>.csv."""
    with (CONSTANTS_DIR / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# ---------- distributions ----------

def test_stats_functions_match_scipy() -> None:
    # arrange -- random arguments over the ranges the calculators meet, tails included
    rng = random.Random(7)
    cases = []
    for _ in range(40):
        p = rng.choice([1e-7, 0.001, 0.005, 0.025, 0.05, 0.1, 0.5, 0.9, 0.95, 0.975, 0.995, rng.random()])
        df, d2 = rng.choice([1, 2, 4, 9, 14, 19, 30, 120]), rng.choice([1, 3, 9, 14, 40])
        z, t, x, f = rng.uniform(-7, 7), rng.uniform(-6, 6), rng.uniform(0.01, 50), rng.uniform(0.01, 12)
        n, k, q = rng.randint(1, 400), 0, rng.random()
        k = rng.randint(0, n)
        big_n = rng.randint(50, 3000)
        defect, sample = rng.randint(0, big_n), rng.randint(1, min(big_n, 250))
        lam = rng.uniform(0.2, 150)
        cases += [
            ("Stats.normCdf", [z], stats.norm.cdf(z)), ("Stats.normInv", [p], stats.norm.ppf(p)),
            ("Stats.tCdf", [t, df], stats.t.cdf(t, df)), ("Stats.tInv", [p, df], stats.t.ppf(p, df)),
            ("Stats.chi2Cdf", [x, df], stats.chi2.cdf(x, df)), ("Stats.chi2Sf", [x, df], stats.chi2.sf(x, df)),
            ("Stats.chi2Inv", [p, df], stats.chi2.ppf(p, df)), ("Stats.chi2Isf", [p, df], stats.chi2.isf(p, df)),
            ("Stats.fCdf", [f, df, d2], stats.f.cdf(f, df, d2)), ("Stats.fSf", [f, df, d2], stats.f.sf(f, df, d2)),
            ("Stats.fInv", [p, df, d2], stats.f.ppf(p, df, d2)), ("Stats.fIsf", [p, df, d2], stats.f.isf(p, df, d2)),
            ("Stats.binomCdf", [k, n, q], stats.binom.cdf(k, n, q)), ("Stats.binomPmf", [k, n, q], stats.binom.pmf(k, n, q)),
            ("Stats.hypergeomCdf", [min(k, sample), big_n, defect, sample], stats.hypergeom.cdf(min(k, sample), big_n, defect, sample)),
            ("Stats.poissonCdf", [k % 200, lam], stats.poisson.cdf(k % 200, lam)),
            ("Stats.betaInv", [p, 1 + k % 30, 1 + n % 40], stats.beta.ppf(p, 1 + k % 30, 1 + n % 40)),
        ]
    # act
    got = run_js([(name, args) for name, args, _ in cases])
    # assert -- double precision libraries; 1e-7 relative leaves room for bisection and continued fractions only
    for (name, args, expected), value in zip(cases, got):
        assert value == pytest.approx(float(expected), rel=1e-7, abs=1e-15), (name, args)


# ---------- normal distribution ----------

def test_normal_solver_recovers_every_unknown() -> None:
    # arrange -- µ, σ, x random; each run leaves one or two of them out
    rng = random.Random(3)
    calls, expected = [], []
    for _ in range(25):
        mu, sigma, x = rng.uniform(-50, 900), rng.uniform(0.01, 80), 0.0
        x = mu + rng.uniform(-3.5, 3.5) * sigma
        pl = float(stats.norm.cdf(x, mu, sigma))
        pr = float(stats.norm.sf(x, mu, sigma))
        calls += [("Calc.normalSolve", [{"mu": mu, "sigma": sigma, "x": x}]),
                  ("Calc.normalSolve", [{"mu": mu, "x": x, "pl": pl}]),
                  ("Calc.normalSolve", [{"sigma": sigma, "x": x, "pr": pr}]),
                  ("Calc.normalSolve", [{"mu": mu, "sigma": sigma, "pl": pl}])]
        expected += [("pl", pl), ("sigma", sigma), ("mu", mu), ("x", x)]
    # act
    got = run_js(calls)
    # assert
    for (key, value), result in zip(expected, got):
        assert result[key] == pytest.approx(value, rel=1e-7, abs=1e-9), key


def test_sigma_from_a_tail_fraction_exam_q6() -> None:
    # arrange -- example exam Q6: 2 in 40 below 720 with mean 820 (study/parts/13_numbers.py)
    expected_sigma = (720 - 820) / stats.norm.ppf(2 / 40)
    # act
    result = run_js([("Calc.normalSolve", [{"mu": 820, "x": 720, "pl": 2 / 40}])])[0]
    # assert
    assert result["sigma"] == pytest.approx(expected_sigma, rel=1e-10)
    assert result["solved"] == ["z", "sigma", "pr"]


def test_contradictory_inputs_are_reported() -> None:
    # arrange -- z = 1 cannot go with µ = 0, σ = 1, x = 2
    # act
    result = run_js([("Calc.normalSolve", [{"mu": 0, "sigma": 1, "x": 2, "z": 1}])])[0]
    # assert
    assert result["notes"] and result["z"] == 2


# ---------- sigma level ----------

@pytest.mark.parametrize("stem, level_column, dpmo_column", [
    ("S06_voc_vs_vop_sigma_capability_defects_per_million_opportunitie", "Sigma Capability", "Defects per Million Opportunities"),
    ("S07_table_1_2_the_sigma_scale", "Sigma", "Defects per Million"),
    ("S08_table_6_3_sigma_score_table_z_dpmo", "Z", "DPMO"),
])
def test_dpmo_with_shift_reproduces_the_course_sigma_tables(stem: str, level_column: str, dpmo_column: str) -> None:
    # arrange -- every course table pairs a sigma level with the one-tail DPMO beyond level − 1.5 (decision 3)
    rows = course_rows(stem)
    # act
    got = run_js([("Calc.dpmoFromSigma", [float(r[level_column])]) for r in rows])
    # assert -- at printed precision; deck p. 21 prints 2σ as 308,537 (308,537.5 rounds to 308,538: build/README.md)
    for row, result in zip(rows, got):
        printed = row[dpmo_column]
        if printed == "308,537":
            assert round(result["shifted"]) == 308538
            continue
        assert agrees_at_printed_precision(result["shifted"], printed, thousands=True), (stem, row[level_column])


def test_sigma_level_from_dpmo_matches_scipy() -> None:
    # arrange
    values = [3.4, 233, 6210, 66807, 308538, 500000]
    # act
    got = run_js([("Calc.sigmaFromDpmo", [v]) for v in values])
    # assert
    for dpmo, result in zip(values, got):
        assert result["z"] == pytest.approx(stats.norm.isf(dpmo / 1e6), rel=1e-9)
        assert result["level"] == pytest.approx(stats.norm.isf(dpmo / 1e6) + 1.5, rel=1e-9)


# ---------- means, proportions, variances ----------

def test_one_mean_ci_and_tests_match_scipy() -> None:
    # arrange
    rng = np.random.default_rng(11)
    xs = rng.normal(10, 2, 15)
    n, mean, s, sigma, mu0, alpha = len(xs), xs.mean(), xs.std(ddof=1), 1.8, 9.2, 0.05
    # act
    r = run_js([("Calc.oneMean", [n, mean, s, sigma, mu0, alpha])])[0]
    # assert
    t_lo, t_hi = stats.t.interval(1 - alpha, n - 1, loc=mean, scale=s / math.sqrt(n))
    assert r["ciT"]["two"] == pytest.approx([t_lo, t_hi], rel=1e-9)
    assert r["ciT"]["lower"][0] == pytest.approx(mean - stats.t.ppf(1 - alpha, n - 1) * s / math.sqrt(n), rel=1e-9)
    z_lo, z_hi = stats.norm.interval(1 - alpha, loc=mean, scale=sigma / math.sqrt(n))
    assert r["ciZ"]["two"] == pytest.approx([z_lo, z_hi], rel=1e-9)
    for key, alternative in (("ne", "two-sided"), ("gt", "greater"), ("lt", "less")):
        expected = stats.ttest_1samp(xs, mu0, alternative=alternative)
        assert r["testT"]["stat"] == pytest.approx(expected.statistic, rel=1e-9)
        assert r["testT"][key]["p"] == pytest.approx(expected.pvalue, rel=1e-7)


def test_unpaired_shoe_soles_s03_we13(oracle: dict[str, Any]) -> None:
    # arrange -- CI Further Reading p. 16-17: LD1 and LD2 of the unpaired experiment
    given, stated = oracle["S03-WE13"]["given"], oracle["S03-WE13"]["stated_answers"]
    a, b = np.array(given["LD1"], float), np.array(given["LD2"], float)
    # act
    r = run_js([("Calc.twoMeansPooled", [len(a), a.mean(), a.std(ddof=1), len(b), b.mean(), b.std(ddof=1), 0, 0.05])])[0]
    # assert -- printed '−5.6 ± 6.19', s_p 6.59; and scipy's pooled t-test
    assert agrees_at_printed_precision(r["sp"], stated["s_p"])
    assert agrees_at_printed_precision(r["diff"], "-5.6")
    assert agrees_at_printed_precision(r["ci"]["half2"], "6.19")
    assert r["test"]["ne"]["p"] == pytest.approx(stats.ttest_ind(a, b, equal_var=True).pvalue, rel=1e-7)


def test_paired_t_matches_scipy() -> None:
    # arrange
    rng = np.random.default_rng(5)
    a = rng.normal(30, 5, 12)
    b = a + rng.normal(1, 2, 12)
    d = a - b
    # act
    r = run_js([("Calc.paired", [len(d), d.mean(), d.std(ddof=1), 0, 0.05])])[0]
    # assert
    for key, alternative in (("ne", "two-sided"), ("gt", "greater"), ("lt", "less")):
        assert r["test"][key]["p"] == pytest.approx(stats.ttest_rel(a, b, alternative=alternative).pvalue, rel=1e-7)


@pytest.mark.parametrize("n, x", [(100, 4), (50, 0), (30, 30), (200, 37)])
def test_exact_proportion_interval_matches_clopper_pearson(n: int, x: int) -> None:
    # arrange -- CI Further Reading p. 20: exact interval = R binom.test (Clopper-Pearson)
    expected = stats.binomtest(x, n).proportion_ci(0.95, method="exact")
    # act
    r = run_js([("Calc.oneProportion", [n, x, None, 0.05])])[0]
    # assert
    assert r["exact"]["two"] == pytest.approx([expected.low, expected.high], rel=1e-8, abs=1e-12)


def test_variance_intervals_and_tests_match_scipy() -> None:
    # arrange
    n1, s1, n2, s2, sigma0, alpha = 20, 0.0125, 15, 0.009, 0.01, 0.05
    # act
    one, two = run_js([("Calc.oneVariance", [n1, s1, sigma0, alpha]), ("Calc.twoVariances", [n1, s1, n2, s2, alpha])])
    # assert -- χ² pivot (n − 1)s²/σ² and F pivot (s1²/σ1²)/(s2²/σ2²) ~ F(n1 − 1, n2 − 1)
    q = (n1 - 1) * s1 ** 2
    assert one["ci"]["two"] == pytest.approx([q / stats.chi2.isf(alpha / 2, n1 - 1), q / stats.chi2.ppf(alpha / 2, n1 - 1)], rel=1e-9)
    assert one["test"]["gt"]["p"] == pytest.approx(stats.chi2.sf(q / sigma0 ** 2, n1 - 1), rel=1e-9)
    f = s1 ** 2 / s2 ** 2
    assert two["ci"]["two"] == pytest.approx([f / stats.f.isf(alpha / 2, n1 - 1, n2 - 1), f / stats.f.ppf(alpha / 2, n1 - 1, n2 - 1)], rel=1e-9)
    assert two["ciInv"]["two"] == pytest.approx([1 / two["ci"]["two"][1], 1 / two["ci"]["two"][0]], rel=1e-12)
    assert two["test"]["gt"]["p"] == pytest.approx(stats.f.sf(f, n1 - 1, n2 - 1), rel=1e-9)


def test_discrete_and_continuous_distributions_match_scipy() -> None:
    # arrange
    calls = [("Calc.binomial", [100, 0.05, 5]), ("Calc.hypergeometric", [1000, 50, 100, 5]), ("Calc.poisson", [2.959, 7]),
             ("Calc.exponential", [175.3, 0.01]), ("Calc.uniform", [1, 2, 1.25])]
    # act
    binom, hyper, pois, expo, unif = run_js(calls)
    # assert
    assert (binom["eq"], binom["le"], binom["ge"]) == pytest.approx(
        (stats.binom.pmf(5, 100, 0.05), stats.binom.cdf(5, 100, 0.05), stats.binom.sf(4, 100, 0.05)), rel=1e-9)
    assert (hyper["mean"], hyper["variance"], hyper["le"]) == pytest.approx(
        (stats.hypergeom.mean(1000, 50, 100), stats.hypergeom.var(1000, 50, 100), stats.hypergeom.cdf(5, 1000, 50, 100)), rel=1e-9)
    assert pois["ge"] == pytest.approx(stats.poisson.sf(6, 2.959), rel=1e-9)
    assert expo["le"] == pytest.approx(stats.expon.cdf(0.01, scale=1 / 175.3), rel=1e-12)
    assert (unif["mean"], unif["variance"], unif["le"]) == pytest.approx((1.5, 1 / 12, 0.25))


def test_contingency_table_probabilities() -> None:
    # arrange
    table = np.array([[120, 30], [80, 270]], float)
    # act
    r = run_js([("Calc.contingency", [table.tolist()])])[0]
    # assert
    total = table.sum()
    assert np.allclose(r["joint"], table / total)
    assert np.allclose(r["colGivenRow"], table / table.sum(axis=1, keepdims=True))
    assert np.allclose(r["rowGivenCol"], table / table.sum(axis=0, keepdims=True))
    assert np.allclose(r["product"], np.outer(table.sum(axis=1), table.sum(axis=0)) / total ** 2)


# ---------- acceptance sampling ----------

def test_oc_values_of_the_course_workbook_s03_we20_s03_we21(oracle: dict[str, Any]) -> None:
    # arrange -- Testing of Hypotheses.xlsx OC sheets, Excel cached floats
    binomial, hyper = oracle["S03-WE20"]["stated_answers"], oracle["S03-WE21"]["stated_answers"]
    # act
    got = run_js([("Calc.samplingPoint", [100, 4, None, 0.02]), ("Calc.samplingPoint", [130, 5, None, 0.02]),
                  ("Calc.samplingPoint", [100, 4, 10000, 0.02]), ("Calc.samplingPoint", [5000, 111, 10000, 0.02])])
    # assert
    assert got[0]["ocBin"] == pytest.approx(float(binomial["P[d<=4] at pi=0.02 (n=100,c=4)"]), rel=1e-9)
    assert got[1]["ocBin"] == pytest.approx(float(binomial["P[d<=5] at pi=0.02 (n=130,c=5)"]), rel=1e-9)
    assert got[2]["ocHyp"] == pytest.approx(float(hyper["P[d<=4] at pi=0.02 (N=10000,n=100,c=4) hypergeometric"]), rel=1e-9)
    assert got[3]["ocHyp"] == pytest.approx(float(hyper["P[d<=111] at pi=0.02 (N=10000,n=5000,c=111)"]), rel=1e-9)


def test_aoql_of_plan_250_5_s04_we18(oracle: dict[str, Any]) -> None:
    # arrange -- Further Reading p. 10: 'approximately 1.3 %' is the approximation p·OC(p) (build/README.md)
    stated = oracle["S04-WE18"]["stated_answers"]
    # act
    r = run_js([("Calc.aoql", [250, 5, 1000])])[0]
    # assert -- the maximum lies at 1.7 % (the slide reads 'about 1.8 %' off its chart); exact formula gives 1.03 %
    assert agrees_at_printed_precision(r["approx"] * 100, "1.3") and stated["AOQL"] == "approximately 1.3%"
    assert r["pApprox"] == pytest.approx(0.017) and r["pExact"] == pytest.approx(0.017)
    assert agrees_at_printed_precision(r["exact"] * 100, "1.03")


def test_variables_plan_s04_we16(oracle: dict[str, Any]) -> None:
    # arrange -- Further Reading p. 9: AQL 0.5 %, LQL 3.5 %, α = β = 5 %
    stated = oracle["S04-WE16"]["stated_answers"]
    # act
    r = run_js([("Calc.variablesPlan", [0.005, 0.035, 0.05, 0.05])])[0]
    # assert
    assert agrees_at_printed_precision(r["k"], stated["k"])
    assert r["nUp"] == int(stated["n"])


# ---------- regression, ANOVA, factorial ----------

def test_regression_oxygen_purity_s05_we17(oracle: dict[str, Any]) -> None:
    # arrange -- Regression p. 2 Table 11-1 and the Minitab output of p. 22
    rows = course_rows("S05_table_11_1_oxygen_and_hydrocarbon_levels")
    xs, ys = [float(r["Hydrocarbon Level x (%)"]) for r in rows], [float(r["Purity y (%)"]) for r in rows]
    stated = oracle["S05-WE17"]["stated_answers"]
    # act
    r = run_js([("Calc.regression", [xs, ys, 1.0, 0, 0, 0.05])])[0]
    # assert -- printed values, then statsmodels for the intervals
    for key, name in (("b0", "beta0hat_minitab"), ("b1", "beta1hat_minitab"), ("seB0", "SE_beta0"), ("seB1", "SE_beta1"),
                      ("sigma", "S")):
        assert agrees_at_printed_precision(r[key], stated[name]), key
    assert agrees_at_printed_precision(r["F"], "128.86") and agrees_at_printed_precision(r["r2"] * 100, "87.7")
    fit = sm.OLS(ys, sm.add_constant(xs)).fit()
    frame = fit.get_prediction(np.array([[1.0, 1.0]])).summary_frame(alpha=0.05)
    assert r["ciMean"]["two"] == pytest.approx([frame["mean_ci_lower"][0], frame["mean_ci_upper"][0]], rel=1e-9)
    assert r["pi"]["two"] == pytest.approx([frame["obs_ci_lower"][0], frame["obs_ci_upper"][0]], rel=1e-9)
    assert r["ciB1"]["two"] == pytest.approx(list(fit.conf_int(0.05)[1]), rel=1e-9)


def test_one_way_anova_paper_strength_s05_we01(oracle: dict[str, Any]) -> None:
    # arrange -- DOE p. 4 Table 4.4, α = 0.01
    groups = [[float(r[f"Obs{i}"]) for i in range(1, 7)]
              for r in course_rows("S05_table_4_4_tensile_strength_of_paper_psi") if r["Obs1"]]
    stated = oracle["S05-WE01"]["stated_answers"]
    # act
    r = run_js([("Calc.anova1", [groups, 0.01])])[0]
    # assert
    for key, name in (("sst", "SS_T"), ("sstr", "SS_Treatments"), ("sse", "SS_E"), ("msTr", "MS_Treatments"), ("msE", "MS_E"),
                      ("F", "F0"), ("Fcrit", "F_crit(0.01,3,20)")):
        assert agrees_at_printed_precision(r[key], stated[name]), key
    assert r["p"] == pytest.approx(stats.f_oneway(*groups).pvalue, rel=1e-8)


def test_factorial_chemical_process_s05_we07(oracle: dict[str, Any]) -> None:
    # arrange -- DOE p. 59-61: 2^2, 3 replicates, runs in standard order (1), a, b, ab
    rows = {(r["A"], r["B"]): [float(r[f"Rep {i}"]) for i in ("I", "II", "III")]
            for r in course_rows("S05_chemical_process_example_treatment_combinations_and_replicat")}
    runs = [rows[(a, b)] for b in "-+" for a in "-+"]
    stated = oracle["S05-WE07"]["stated_answers"]
    # act
    r = run_js([("Calc.factorial", [2, runs, None, 0.05])])[0]
    # assert
    effects = {e["name"]: e for e in r["effects"]}
    for name in ("A", "B", "AB"):
        assert agrees_at_printed_precision(effects[name]["effect"], stated[name]), name
    assert agrees_at_printed_precision(effects["A"]["F"], "53.19") and agrees_at_printed_precision(r["Fmodel"], "24.82")
    assert agrees_at_printed_precision(r["sspe"], "31.33") and agrees_at_printed_precision(r["r2adj"], stated["Adj_R-Squared"])


def test_factorial_with_pooling_matches_statsmodels() -> None:
    # arrange -- 2^4 single replicate, three- and four-factor interactions pooled into the error (DOE p. 72, 77)
    rng = np.random.default_rng(2)
    k = 4
    design = pd.DataFrame([[1 if run >> j & 1 else -1 for j in range(k)] for run in range(2 ** k)], columns=list("ABCD"))
    design["y"] = 50 + 4 * design.A - 3 * design.C + 2 * design.A * design.C + rng.normal(0, 1, 2 ** k)
    # act
    r = run_js([("Calc.factorial", [k, [[y] for y in design.y], 3, 0.05])])[0]
    # assert -- effect = 2 × coded coefficient; the model with all main effects and two-factor interactions
    fit = smf.ols("y ~ (A + B + C + D) ** 2", design).fit()
    effects = {e["name"]: e for e in r["effects"]}
    for term, coefficient in fit.params.items():
        if term == "Intercept":
            continue
        name = "".join(sorted(term.replace(":", "")))
        assert effects[name]["effect"] == pytest.approx(2 * coefficient, rel=1e-9)
        assert effects[name]["p"] == pytest.approx(fit.pvalues[term], rel=1e-6)
    assert r["dfE"] == fit.df_resid and r["mse"] == pytest.approx(fit.mse_resid, rel=1e-9)


def aliases_by_brute_force(generators: dict[str, str]) -> tuple[set[str], int]:
    """Defining relation (words) and resolution of a fractional design, by multiplying generator words out."""
    words = [frozenset(left + right) for left, right in generators.items()]
    relation = set()
    for size in range(1, len(words) + 1):
        for subset in itertools.combinations(words, size):
            product: frozenset[str] = frozenset()
            for word in subset:
                product = product ^ word
            relation.add("".join(sorted(product)))
    return relation, min(len(w) for w in relation)


@pytest.mark.parametrize("text, generators", [
    ("D=ABC", {"D": "ABC"}), ("D=AB; E=AC", {"D": "AB", "E": "AC"}), ("E=ABC, F=BCD", {"E": "ABC", "F": "BCD"}),
    ("D=AB; E=AC; F=BC; G=ABC", {"D": "AB", "E": "AC", "F": "BC", "G": "ABC"}),
])
def test_alias_structure_matches_word_multiplication(text: str, generators: dict[str, str]) -> None:
    # arrange
    relation, resolution = aliases_by_brute_force(generators)
    # act
    r = run_js([("Calc.aliases", [text])])[0]
    # assert
    assert set(r["relation"]) == relation and r["resolution"] == resolution
    assert r["runs"] == 2 ** (len(set("".join(generators.values())) | set(generators)) - len(generators))


# ---------- capability and control charts ----------

def table_constant(symbol: str, n: int) -> float:
    """A printed constant from the table convention decision 4 assigns to it."""
    table = next(t for t in load_all() if t.source.key == USED_TABLE[symbol])
    return float(table.value(symbol, n))


def test_capability_rows_use_the_decision_4_constants() -> None:
    # arrange -- example exam Q3 numbers plus R̄, s̄, MR̄ and an overall s
    lsl, usl, mean, n = 1400.0, 1460.0, 1440.0, 5
    spreads = {"given": 10.0, "rbar_d2": 23.0 / table_constant("d2", n), "sbar": 9.4, "sbar_c4": 9.4 / table_constant("c4", n),
               "mrbar": 11.0 / table_constant("d2", 2), "overall": 11.5}
    # act
    rows = run_js([("Calc.capability", [{"lsl": lsl, "usl": usl, "mean": mean, "sigma": 10.0, "rbar": 23.0, "sbar": 9.4, "n": n,
                                         "mrbar": 11.0, "overall": 11.5}, "@K"])])[0]
    # assert
    assert [r["key"] for r in rows] == list(spreads)
    for row in rows:
        sigma = spreads[row["key"]]
        cpu, cpl = (usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma)
        out = stats.norm.sf((usl - mean) / sigma) + stats.norm.cdf((lsl - mean) / sigma)
        assert (row["sigma"], row["cp"], row["cpk"], row["out"]) == pytest.approx(((sigma, (usl - lsl) / (6 * sigma), min(cpu, cpl), out)), rel=1e-9)
    assert rows[0]["level"] == "just capable" and rows[0]["capable"] == "nee"


def oefening_2_data() -> list[list[float]]:
    """__Gegevens oefeningen.xlsx 'Gegevens oefening 2'!B5:F24: 20 subgroups of 5 net weights (S06-WE03 data_ref)."""
    ws = openpyxl.load_workbook(COURSE / "Les 4" / "__Gegevens oefeningen.xlsx", data_only=True)["Gegevens oefening 2"]
    return [[ws.cell(r, c).value for c in range(2, 7)] for r in range(5, 25)]


def test_xbar_r_chart_oefening_2_s06_we03(oracle: dict[str, Any]) -> None:
    # arrange -- SPC oefening 2 workbook (Excel cached floats, A2 0.577, D3 0, D4 2.115, d2 2.326)
    stated = oracle["S06-WE03"]["stated_answers"]
    # act
    r = run_js([("Calc.subgroupChart", [oefening_2_data(), "@K"])])[0]
    # assert
    assert r["xbarbar"] == pytest.approx(float(stated["Xbarbar (X_streep_streep)"]), rel=1e-12)
    assert r["rbar"] == pytest.approx(float(stated["Rbar (R_streep)"]), rel=1e-12)
    assert r["xR"] == pytest.approx([float(stated["LCL_xbar"]), r["xbarbar"], float(stated["UCL_xbar"])], rel=1e-12)
    assert r["R"] == pytest.approx([0, r["rbar"], float(stated["UCL_R"])], rel=1e-12)
    assert r["sigmaR"] == pytest.approx(float(stated["sigma_estimate_Rbar_over_d2"]), rel=1e-12)


def test_individuals_and_attribute_charts() -> None:
    # arrange
    xs = [10.0, 12.0, 11.0, 13.0, 12.0, 30.0]
    pairs = [[100, 5], [100, 3], [80, 14]]  # 14/80 = 0.175 lies above its UCL 0.169
    # act
    imr, pchart = run_js([("Calc.individuals", [xs, "@K"]), ("Calc.attributeChart", ["p", pairs])])
    # assert -- Dummies p. 249 and 254 with E2 (n = 2) from Six Sigma Demystified and D4 (n = 2) from Table 18
    mrbar = np.mean(np.abs(np.diff(xs)))
    assert imr["X"] == pytest.approx([np.mean(xs) - table_constant("E2", 2) * mrbar, np.mean(xs), np.mean(xs) + table_constant("E2", 2) * mrbar])
    assert imr["MR"][2] == pytest.approx(table_constant("D4", 2) * mrbar)
    assert imr["points"][-1]["fx"] == "boven UCL"
    pbar = 22 / 280
    assert pchart["rows"][2]["ucl"] == pytest.approx(pbar + 3 * math.sqrt(pbar * (1 - pbar) / 80))
    assert pchart["rows"][2]["flag"] == "boven UCL"


# ---------- Gage R&R ----------

def course_grr_rows() -> list[list[float]]:
    """measurements!D4:F13 (S10-WE02 data_ref) as k·r lines: operator A trial 1, A trial 2, B trial 1, …, 5 parts each."""
    ws = openpyxl.load_workbook(GRR_WORKBOOK, data_only=True)["measurements"]
    value = {(operator, (row - 4) % 2, (row - 4) // 2): ws.cell(row, 4 + operator).value
             for row in range(4, 14) for operator in range(3)}
    return [[value[(operator, trial, part)] for part in range(5)] for operator in range(3) for trial in range(2)]


def test_gage_rr_average_and_range_s10_we03(oracle: dict[str, Any]) -> None:
    # arrange -- 'ranges' sheet of the course workbook: d2 1.12838, d2* 1.91155 and 2.48124 (tabel MSA.pdf)
    answers = oracle["S10-WE03"]["stated_answers"]
    # act
    r = run_js([("Calc.grr", [course_grr_rows(), 3, 2, None, 0.05, "@M"])])[0]
    # assert -- Excel cached floats, same formulas and constants
    assert (r["d2"], r["d2k"], r["d2n"]) == (1.12838, 1.91155, 2.48124)
    for key, name in (("ev", "EV"), ("av", "AV"), ("pv", "PV"), ("tv", "TV"), ("pctTv", "%GRR (formula sqrt((EV^2+AV^2)/TV^2))")):
        assert r["ar"][key] == pytest.approx(float(answers[name]), rel=1e-9), key


def test_gage_rr_anova_s10_we02(oracle: dict[str, Any]) -> None:
    # arrange -- '2way anova' sheet, model without interaction
    answers = oracle["S10-WE02"]["stated_answers"]
    # act
    r = run_js([("Calc.grr", [course_grr_rows(), 3, 2, None, 0.05, "@M"])])[0]
    # assert
    for key, name in (("ev", "EV"), ("av", "AV"), ("pv", "PV"), ("tv", "TV"), ("pctTv", "%GRR (formula sqrt((EV^2+AV^2)/TV^2))")):
        assert r["anova"][key] == pytest.approx(float(answers[name]), rel=TYPED_ROUNDING), key
    assert r["anova"]["verdict"].startswith("niet aanvaardbaar")


def test_gage_rr_anova_tables_match_statsmodels() -> None:
    # arrange -- a random complete study, 3 operators × 2 trials × 6 parts
    rng = np.random.default_rng(9)
    rows = [[round(float(v), 3) for v in 20 + np.arange(6) + rng.normal(0, 0.5, 6) + 0.3 * op] for op in range(3) for _ in range(2)]
    frame = pd.DataFrame([{"op": i // 2, "part": j, "y": rows[i][j]} for i in range(6) for j in range(6)])
    # act
    r = run_js([("Calc.grr", [rows, 3, 2, 1.5, 0.05, "@M"])])[0]
    # assert
    additive = sm.stats.anova_lm(smf.ols("y ~ C(op) + C(part)", frame).fit())
    full = sm.stats.anova_lm(smf.ols("y ~ C(op) * C(part)", frame).fit())
    assert r["anova"]["msErr"] == pytest.approx(additive["mean_sq"]["Residual"], rel=1e-9)
    assert r["anova"]["pOp"] == pytest.approx(additive["PR(>F)"]["C(op)"], rel=1e-7)
    assert r["interaction"]["pInt"] == pytest.approx(full["PR(>F)"]["C(op):C(part)"], rel=1e-7)
    assert r["anova"]["pctTol"] == pytest.approx(6 * r["anova"]["grr"] / 1.5)


def test_embedded_constants_are_the_printed_tables() -> None:
    # arrange
    msa = load_average_range_table()
    # act -- the JSON the page embeds for the calculators
    data = build_module().constants_data()
    # assert -- exactly the printed numbers, from the table decision 4 assigns to each symbol
    assert data["msa"]["d2"] == [float(v) for v in msa.d2]
    assert data["msa"]["d2star"] == [[float(v) for v in row] for row in msa.d2_star]
    for symbol in ("A2", "D3", "D4", "d2", "c4", "A3", "B3", "B4", "E2"):
        for n in (2, 5, 10):
            assert data["chart"][symbol][str(n)] == table_constant(symbol, n), (symbol, n)


# ---------- confusion matrix ----------

def test_confusion_metrics_exam_q5() -> None:
    # arrange -- example exam Q5, model A (study/parts/13_numbers.py): train and test matrices
    train, test = [[480, 20], [15, 485]], [[180, 120], [110, 190]]
    # act
    a_train, a_test = run_js([("Calc.confusion", [train]), ("Calc.confusion", [test])])
    # assert
    assert a_train["accuracy"] == pytest.approx(965 / 1000) and a_test["accuracy"] == pytest.approx(370 / 600)
    assert a_test["c1"]["recall"] == pytest.approx(180 / 300) and a_test["c1"]["precision"] == pytest.approx(180 / 290)
    assert a_test["c2"]["f1"] == pytest.approx(2 * (190 / 300) * (190 / 310) / (190 / 300 + 190 / 310))
