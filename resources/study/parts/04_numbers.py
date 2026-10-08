"""Numbers for Deel 04 (confidence intervals, Ottoy, Les 2): every value that study/parts/04_betrouwbaarheidsintervallen.html
marks "zelf berekend", every exercise answer (data-answer), and a re-check of every printed course result the text quotes.

Data come from inventory/constants (rows carry file + page), from the course spreadsheet
source/course/Les 2/20260529_ottoy_Confidence Intervals.xlsx (read-only, openpyxl), or are transcribed from the slide
named in the comment next to them. Nothing is taken from memory.

Check lines: "OK" = the computed value equals the printed one after half-up rounding to the printed precision;
"MISMATCH (erratum)" = a known disagreement that the guide text explains; "approx OK" = the course states the value as
approximate ("about", "≅") and it agrees within the stated tolerance. An unexpected mismatch makes the script exit 1.
Run from the project root:  python3 study/parts/04_numbers.py
"""
from __future__ import annotations

import csv
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import openpyxl
from scipy import stats
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = ROOT / "inventory" / "constants"
LES2 = ROOT / "source" / "course" / "Les 2"
UNEXPECTED: list[str] = []


def rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table in inventory/constants (each row names its file and page)."""
    with (CONSTANTS / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sheet_column(workbook: str, sheet: str, cells: str) -> list[float]:
    """Numeric values of a cell range in a course spreadsheet (cached values, read-only)."""
    wb = openpyxl.load_workbook(LES2 / workbook, data_only=True, read_only=True)
    values = [c.value for row in wb[sheet][cells] for c in row]
    return [float(v) for v in values]


def show(label: str, value: float | str, note: str = "") -> None:
    """Print one result line."""
    text = f"{value:.6g}" if isinstance(value, (float, np.floating)) else str(value)
    print(f"  {label:<60} {text:>14}  {note}")


def half_up(value: float, decimals: int) -> Decimal:
    """Half-up rounding (decision 10: compare at the printed precision)."""
    quantum = Decimal(1).scaleb(-decimals)
    return Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_UP)


def check(label: str, printed: str, computed: float, erratum: bool = False) -> None:
    """Compare a printed course value with the computation at the printed precision."""
    decimals = len(printed.split(".")[1]) if "." in printed else 0
    same = half_up(computed, decimals) == Decimal(printed)
    if same:
        status = "OK"
    elif erratum:
        status = "MISMATCH (erratum)"
    else:
        status = "MISMATCH"
        UNEXPECTED.append(label)
    print(f"  [{status}] {label}: printed {printed}, computed {computed:.6g}")


def approx(label: str, printed: float, computed: float, tol: float) -> None:
    """Check a value the course itself states as approximate."""
    ok = abs(printed - computed) <= tol
    if not ok:
        UNEXPECTED.append(label)
    print(f"  [{'approx OK' if ok else 'MISMATCH'}] {label}: printed ≈{printed:g}, computed {computed:.6g} (tol {tol:g})")


def exact_ci(x: int, n: int, conf: float) -> tuple[float, float]:
    """Exact two-sided binomial CI by inverting the binomial c.d.f. (what R's binom.test returns, TH FR p. 20)."""
    a = 1 - conf
    lo = 0.0 if x == 0 else float(stats.beta.ppf(a / 2, x, n - x + 1))
    hi = 1.0 if x == n else float(stats.beta.ppf(1 - a / 2, x + 1, n - x))
    return lo, hi


def grid_ci(x: int, n: int, conf: float) -> tuple[float, float]:
    """CI read from the nomogram of sheet 'Nomogram fraction defectives' (BINOM.INV quantile curves, π in steps of 0.001)."""
    grid = np.round(np.arange(0, 1.0005, 0.001), 3)
    lo_q, hi_q = (1 - conf) / 2, conf + (1 - conf) / 2
    lower = min(p for p in grid if stats.binom.ppf(hi_q, n, p) >= x)
    upper = max(p for p in grid if stats.binom.ppf(lo_q, n, p) <= x)
    return float(lower), float(upper)


def pct(text: str) -> str:
    """'1,1%' or '1.10%' -> '1.1' / '1.10' (printed percentage as a decimal string)."""
    return text.replace("%", "").replace(",", ".").strip()


def point_vs_interval() -> None:
    """04.1: CI FR p. 2 (hypergeometric 40 %), CI FR p. 3 notes (student heights), CI p. 4-5."""
    print("04.1 Point estimate versus interval")
    p_one = float(stats.hypergeom.pmf(1, 100, 10, 10))
    approx("CI FR p. 2: P(sample of 10 from 100 with 10 defectives has 1 defective)", 0.40, p_one, 0.01)
    # CI FR p. 3 notes: sigma = 5 cm, RSWOR of size 10; z_0.975 = 1.96 as printed on CI p. 10 notes.
    sigma, n = 5.0, 10
    z_ratio = 5.0 / (sigma / np.sqrt(n))
    show("student heights: 5 / (sigma/sqrt(n))", float(z_ratio))
    show("P(|Xbar - mu| <= 5 cm)  [ex-04-1]", float(2 * stats.norm.cdf(z_ratio) - 1))
    show("95 % half-width 1.96 * 5 / sqrt(10) (cm)  [ex-04-1]", float(1.96 * sigma / np.sqrt(n)))
    approx("CI p. 5 notes: lot with 2 %, n = 100: P(0 <= d <= 7) ('in practice')", 1.0,
           float(stats.binom.cdf(7, 100, 0.02)), 0.001)
    print("  CI p. 5 / p. 4: 95 % CIs for d defectives out of n = 100")
    for r in rows("S03_95_ci_for_lot_percentage_defectives_for_different_observed_d"):
        x = int(r["defectives in sample"])
        lo, hi = exact_ci(x, 100, 0.95)
        glo, ghi = grid_ci(x, 100, 0.95)
        show(f"d = {x}: exact / nomogram grid", f"[{100*lo:.2f}, {100*hi:.2f}] / [{100*glo:.1f}, {100*ghi:.1f}] %")
        check(f"CI p. 5 d = {x} lower (exact)", pct(r["95% CI lower"]), 100 * lo, erratum=(x == 2))
        check(f"CI p. 5 d = {x} upper (exact)", pct(r["95% CI upper"]), 100 * hi)


def confidence_vs_accuracy() -> None:
    """04.2: CI p. 6 table, CI p. 7 widths."""
    print("04.2 Confidence, accuracy and sample size")
    for r in rows("S03_ci_for_the_sample_n_100_4_defectives_at_different_confidence"):
        conf = float(pct(r["confidence"])) / 100
        if conf in (0.0, 1.0):
            show(f"conf {conf:.3f}", "limit case: [p, p] resp. [0, 100 %] (definition)")
            continue
        lo, hi = exact_ci(4, 100, conf)
        glo, ghi = grid_ci(4, 100, conf)
        show(f"conf {conf:.3f}: exact / nomogram grid",
             f"[{100*lo:.2f}, {100*hi:.2f}] / [{100*glo:.1f}, {100*ghi:.1f}] %")
        check(f"CI p. 6 conf {conf} lower (exact)", pct(r["CI lower"]), 100 * lo, erratum=(conf == 0.70))
        check(f"CI p. 6 conf {conf} upper (exact)", pct(r["CI upper"]), 100 * hi, erratum=(conf == 0.99))
    # CI p. 7: width of the 95 % CI at p = 50 % with the formula of CI p. 10 (pi = P +- 1.96 sqrt(P(1-P)/n)).
    for r in rows("S03_sample_size_vs_width_of_95_ci_for_a_proportion_worst_case_p"):
        n = int(r["sample size"])
        width = 2 * 1.96 * np.sqrt(0.25 / n)
        show(f"n = {n}: width 2*1.96*sqrt(0.25/n) (%)  [ex-04-3]", float(100 * width))
        check(f"CI p. 7 width at n = {n} (formula of p. 10)", pct(r["CI width"]), 100 * width)
    check("CI p. 7 notes: 10 % relative accuracy on 10 % -> width (in %)", "2", 100 * 2 * 0.10 * 0.10)
    n_for_5 = (2 * 1.96 * 0.5 / 0.05) ** 2
    show("n for a width of exactly 5 %: (2*1.96*0.5/0.05)^2", float(n_for_5))
    show("  rounded up  [ex-04-3]", int(np.ceil(n_for_5)))
    # Exact interval for a finite lot of N = 10000 (CI p. 8: 'finite population'), x = n/2.
    big_n, n = 10000, 1350
    m = np.arange(big_n + 1)
    sf = stats.hypergeom.sf(n // 2 - 1, big_n, m, n)
    cdf = stats.hypergeom.cdf(n // 2, big_n, m, n)
    width = (m[cdf > 0.025].max() - m[sf > 0.025].min()) / big_n
    show("n = 1350 from a lot of 10000 (hypergeometric, exact): width (%)", float(100 * width))


def inversion() -> None:
    """04.3: CI p. 8 and p. 11 notes (sampling distribution for pi = 10 %, n = 100, N = 10000)."""
    print("04.3 Function inversion")
    q = stats.hypergeom.ppf([0.025, 0.975], 10000, 1000, 100)
    check("CI p. 8 notes: 2.5 % point of P (pi = 10 %) in %", "5", float(q[0]))
    check("CI p. 8 notes: 97.5 % point of P in %", "16", float(q[1]))
    check("CI p. 11: upper 10 % point of P in %", "14", float(stats.hypergeom.ppf(0.9, 10000, 1000, 100)))
    approx("CI p. 11 notes: P(P >= 14 %) 'around 12 %'", 0.12, float(stats.hypergeom.sf(13, 10000, 1000, 100)), 0.005)


def mean_ci() -> None:
    """04.4: z and t intervals; CI FR p. 8 notes exercise; sheet 'Confidence interval mean'; CI p. 15 (S03-WE02)."""
    print("04.4 CI for the mean")
    for k in (1, 2, 3):
        show(f"coverage of +-{k} sigma (Dummies '68/95/99.7 %')", float(1 - 2 * stats.norm.sf(k)))
    show("tail beyond 2 sigma P(Z > 2)", float(stats.norm.sf(2)))
    show("z_0.975 = NORM.S.INV(0.975)", float(stats.norm.ppf(0.975)))
    for n in (5, 10, 20):
        t = float(stats.t.ppf(0.975, n - 1))
        show(f"n = {n}: t_0.975,{n-1} and ratio t/1.96  [ex-04-4]", f"{t:.4f} / {t/1.96:.4f}")
    show("sheet 'Confidence interval mean': T.INV(0.975; 9)  [ex-04-2]", float(stats.t.ppf(0.975, 9)))
    data = sheet_column("20260529_ottoy_Confidence Intervals.xlsx", "example t-test", "B3:B22")
    n = len(data)
    xbar, s = float(np.mean(data)), float(np.std(data, ddof=1))
    t02 = float(stats.t.ppf(0.02, n - 1))
    upper = xbar - t02 * s / np.sqrt(n)
    upper19 = xbar - t02 * s / np.sqrt(19)
    show("CI p. 15 spreadsheet data: n / xbar / s  [ex-04-5]", f"{n} / {xbar:.4f} / {s:.5f}")
    show("T.INV(0.02; 19)  [ex-04-5]", t02)
    show("one-sided 98 % upper bound xbar - T.INV(0.02;19)*s/sqrt(20)  [ex-04-5]", float(upper))
    check("CI p. 15 upper bound", "9.98", float(upper))
    show("CI.xlsx 'example t-test' F13 with SQRT(19) (spreadsheet error)", float(upper19))
    check("CI.xlsx F13 cached value 9.983291 (SQRT(19)) vs SQRT(20)", "9.983291", float(upper), erratum=True)
    # CI p. 15 prints the data rounded to 2 decimals (transcribed from the slide).
    slide = [10.06, 9.89, 9.90, 9.99, 9.87, 9.88, 9.93, 9.98, 10.12, 9.86,
             9.89, 9.81, 9.95, 9.92, 10.07, 9.98, 10.02, 9.62, 9.96, 9.86]
    xs, ss = float(np.mean(slide)), float(np.std(slide, ddof=1))
    show("slide-rounded data: xbar / s / upper bound", f"{xs:.4f} / {ss:.5f} / {xs - t02 * ss / np.sqrt(20):.4f}")


def proportion_ci() -> None:
    """04.5: tiles 4/100 (CI p. 4, 10), TH FR p. 20 (S03-WE15), Dummies p. 197 (S08-WE12, S08-WE13)."""
    print("04.5 CI for a proportion")
    p, n = 0.04, 100
    half = 1.96 * np.sqrt(p * (1 - p) / n)
    show("tiles 4/100 normal approx: half-width / lower / upper (%)  [ex-04-6]",
         f"{100*half:.3f} / {100*(p-half):.3f} / {100*(p+half):.3f}")
    lo, hi = exact_ci(4, 100, 0.95)
    show("tiles 4/100 exact (binom.test)  [ex-04-6]", f"[{100*lo:.3f}, {100*hi:.3f}] %")
    check("CI p. 10 notes: at least 5 defectives at 1 % -> n", "500", 5 / 0.01)
    # TH FR p. 20: p = 0.6, n = 200 (binom.test(120, 200) -> [0.53, 0.67]).
    lo, hi = exact_ci(120, 200, 0.95)
    check("TH FR p. 20 exact lower", "0.53", lo)
    check("TH FR p. 20 exact upper", "0.67", hi)
    half = 1.96 * np.sqrt(0.6 * 0.4 / 200)
    show("p = 0.6, n = 200 normal approx: lower / upper  [ex-04-7]", f"{0.6-half:.4f} / {0.6+half:.4f}")
    # Dummies PDF p. 197 (printed 179): 4 of 5 dentists, 90 %, Z = 1.645.
    half = 1.645 * np.sqrt(0.8 * 0.2 / 5)
    show("Dummies 4/5 at 90 %: half-width  [ex-04-8]", float(half))
    check("Dummies p. 179 half-width", "0.294", float(half))
    show("Dummies 4/5: interval, upper clipped at 1 (Dummies tip)", f"[{0.8-half:.3f}, {min(0.8+half, 1):.3f}]")
    show("Dummies 4/5: n*p = 4 defect-free 'successes', n*(1-p) = 1", "4 / 1")
    # Dummies PDF p. 197-198 (printed 179-180): Toledo 213/300 vs Buffalo 189/300, Z = 2.
    p1, p2 = 213 / 300, 189 / 300
    half = 2 * np.sqrt(p1 * (1 - p1) / 300 + p2 * (1 - p2) / 300)
    show("Toledo - Buffalo: difference / half-width  [ex-04-9]", f"{p1-p2:.4f} / {half:.5f}")
    check("Dummies p. 179 half-width 0.076", "0.076", float(half), erratum=True)
    check("Dummies p. 180 lower 0.004", "0.004", float(p1 - p2 - half), erratum=True)
    check("Dummies p. 180 upper 0.156", "0.156", float(p1 - p2 + half), erratum=True)
    show("Toledo - Buffalo unrounded interval", f"[{p1-p2-half:.4f}, {p1-p2+half:.4f}]")


def two_means() -> None:
    """04.6: shoe soles, CI FR p. 17-19 (S03-WE13, S03-WE14)."""
    print("04.6 Difference of two means")
    un = rows("S03_niet_paarsgewijze_schoenzool_experiment_ruwe_data_rs1_en_rs2")
    ld1 = np.array([float(r["LD1"]) for r in un])
    ld2 = np.array([float(r["LD2"]) for r in un])
    n1, n2 = len(ld1), len(ld2)
    x1, x2, s1, s2 = ld1.mean(), ld2.mean(), ld1.std(ddof=1), ld2.std(ddof=1)
    sp = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    sp_printed_formula = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 1))
    t18 = float(stats.t.ppf(0.975, n1 + n2 - 2))
    half = t18 * sp * np.sqrt(1 / n1 + 1 / n2)
    check("CI FR p. 17 xbar1", "28.7", float(x1))
    check("CI FR p. 17 s1", "5.50", float(s1))
    check("CI FR p. 17 xbar2", "34.3", float(x2))
    check("CI FR p. 17 s2", "7.53", float(s2))
    check("CI FR p. 17 s_p (denominator n1+n2-2)", "6.59", float(sp))
    check("CI FR p. 15 formula with n1+n2-1 would give s_p", "6.59", float(sp_printed_formula), erratum=True)
    check("CI FR p. 17 t_18,0.025", "2.10", t18)
    check("CI FR p. 17 half-width", "6.19", float(half))
    show("unpaired: sp / sp(n1+n2-1) / t18 / half-width  [ex-04-10]",
         f"{sp:.4f} / {sp_printed_formula:.4f} / {t18:.4f} / {half:.4f}")
    show("unpaired 95 % CI for mu1 - mu2", f"[{x1-x2-half:.2f}, {x1-x2+half:.2f}]")
    pa = rows("S03_paarsgewijze_schoenzool_experiment_ruwe_data_10_jongens_ld1")
    a = np.array([float(r["LD1"]) for r in pa])
    b = np.array([float(r["LD2"]) for r in pa])
    v = a - b
    n = len(v)
    t9 = float(stats.t.ppf(0.975, n - 1))
    half_p = t9 * v.std(ddof=1) / np.sqrt(n)
    check("CI FR p. 18 vbar", "-3.3", float(v.mean()))
    check("CI FR p. 18 s_v", "2.41", float(v.std(ddof=1)))
    check("CI FR p. 18 t_9,0.025", "2.26", t9)
    check("CI FR p. 18 half-width", "1.72", float(half_p))
    show("paired: vbar / s_v / t9 / half-width  [ex-04-11]", f"{v.mean():.2f} / {v.std(ddof=1):.4f} / {t9:.4f} / {half_p:.4f}")
    show("paired 95 % CI for mu1 - mu2", f"[{v.mean()-half_p:.2f}, {v.mean()+half_p:.2f}]")
    check("CI FR p. 19 ratio 1.72/6.19", "0.28", 1.72 / 6.19)
    rho = float(np.corrcoef(a, b)[0, 1])
    show("sample correlation LD1-LD2 in the paired data", rho)
    show("sqrt(1 - 0.93) / sqrt(1 - sample rho)", f"{np.sqrt(1-0.93):.3f} / {np.sqrt(1-rho):.3f}")
    check("CI FR p. 19 rho = 0.93 vs sample correlation of the p. 18 data", "0.93", rho, erratum=True)


def variance_ci() -> None:
    """04.7: CI FR p. 21, CI p. 16 (S03-WE03), Dummies p. 176-177 (S08-WE10, Table 8-2)."""
    print("04.7 CI for sigma^2 and sigma")
    data = sheet_column("20260529_ottoy_Confidence Intervals.xlsx", "example chi²-test", "B3:B22")
    n = len(data)
    var = float(np.var(data, ddof=1))
    chi98 = float(stats.chi2.ppf(0.98, n - 1))
    lower = np.sqrt((n - 1) * var / chi98)
    show("CI p. 16: n / s^2 (VAR.S) / s  [ex-04-13]", f"{n} / {var:.6e} / {np.sqrt(var):.6f}")
    show("CHISQ.INV(0.98; 19)  [ex-04-13]", chi98)
    show("lower bound sqrt(19 s^2 / CHISQ.INV(0.98;19))  [ex-04-13]", float(lower))
    check("CI p. 16 lower bound", "0.0088", float(lower))
    # Dummies PDF p. 195 (printed 177): n = 5, s = 3.7, chi2 values from Table 8-2 ('95 %' = +-2 sigma).
    tail = float(stats.norm.sf(2))
    chi_up, chi_lo = float(stats.chi2.isf(tail, 4)), float(stats.chi2.ppf(tail, 4))
    lo, hi = np.sqrt(4 * 3.7**2 / chi_up), np.sqrt(4 * 3.7**2 / chi_lo)
    check("Dummies p. 177 lower (unrounded chi2 of Table 8-2)", "2.195", float(lo))
    check("Dummies p. 177 upper (unrounded chi2 of Table 8-2)", "10.907", float(hi))
    show("Dummies upper with the rounded 0.460", float(np.sqrt(4 * 3.7**2 / 0.460)))
    check("Dummies Table 8-2 chi2 upper n = 5 '95 %' (tail = P(Z > 2))", "11.365", float(stats.chi2.isf(tail, 4)))
    check("Dummies Table 8-2 chi2 lower n = 5 '95 %'", "0.460", float(stats.chi2.ppf(tail, 4)))
    check("Dummies Table 8-2 chi2 upper n = 5 at 2.5 % (a true 95 % CI)", "11.365", float(stats.chi2.isf(0.025, 4)),
          erratum=True)
    t3 = float(stats.norm.sf(3))
    check("Dummies Table 8-2 99.7 % upper n = 5", "17.800", float(stats.chi2.isf(t3, 4)), erratum=True)
    lo95, hi95 = np.sqrt(4 * 3.7**2 / stats.chi2.isf(0.025, 4)), np.sqrt(4 * 3.7**2 / stats.chi2.ppf(0.025, 4))
    show("Dummies n = 5, s = 3.7: true 95 % CI (2.5 % tails)  [ex-04-14]", f"[{lo95:.3f}, {hi95:.3f}]")
    show("chi2 2.5 % tails df 4: upper / lower", f"{stats.chi2.isf(0.025, 4):.3f} / {stats.chi2.ppf(0.025, 4):.4f}")


def ratio_ci() -> None:
    """04.8: Test Recipes p. 12 (F), Dummies p. 178 (S08-WE11, Table 8-3)."""
    print("04.8 CI for a ratio of variances (F)")
    f_up_94 = float(stats.f.isf(0.05, 9, 4))
    f_up_49 = float(stats.f.isf(0.05, 4, 9))
    check("Dummies Table 8-3 F(n1=10, n2=5) = F.INV.RT(0.05; 9; 4)", "5.999", f_up_94)
    check("Dummies Table 8-3 F(n1=5, n2=10) = F.INV.RT(0.05; 4; 9)", "3.633", f_up_49)
    check("Dummies Table 8-3 F(n1=2, n2=2) = F.INV.RT(0.05; 1; 1)", "161.446", float(stats.f.isf(0.05, 1, 1)),
          erratum=True)
    show("Test Recipes p. 12: F.INV(0.05; 9; 4) and 1/F.INV(0.95; 4; 9)",
         f"{stats.f.ppf(0.05, 9, 4):.6f} / {1/stats.f.ppf(0.95, 4, 9):.6f}")
    ratio = 4.0 / 7.5
    printed_lo, printed_hi = ratio / f_up_49, ratio * f_up_94
    lo, hi = ratio / f_up_94, ratio * f_up_49
    check("Dummies p. 178 printed lower 0.147 (= ratio / 3.633)", "0.147", float(printed_lo))
    check("Dummies p. 178 printed lower 0.147 vs correct ratio / F.INV.RT(0.05;9;4)", "0.147", float(lo), erratum=True)
    check("Dummies p. 178 printed upper 3.199 vs correct ratio * F.INV.RT(0.05;4;9)", "3.199", float(hi), erratum=True)
    show("printed-style interval (F values swapped)", f"[{printed_lo:.4f}, {printed_hi:.4f}]")
    show("correct interval for sigmaA^2/sigmaB^2, 5 % per tail  [ex-04-15]", f"[{lo:.4f}, {hi:.4f}]")
    show("F.INV(0.05; 9; 4)  [ex-04-15]", float(stats.f.ppf(0.05, 9, 4)))
    lb = float(stats.f.ppf(0.05, 9, 4)) * 7.5 / 4.0
    show("one-sided 95 % lower bound sigmaB^2/sigmaA^2 = F.INV(0.05;9;4)*7.5/4  [ex-04-15]", lb)


def duality() -> None:
    """04.9: Z values used in the text; CI p. 14 OC points and one-sided 90 % table; TH FR p. 18."""
    print("04.9 Duality tests <-> intervals")
    for q in (0.95, 0.975, 0.99, 0.995):
        show(f"NORM.S.INV({q})" + ("  [ex-05-19]" if q == 0.99 else ""), float(stats.norm.ppf(q)))
    for p, printed in ((0.013, "0.99"), (0.0245, "0.90"), (0.0785, "0.10")):
        check(f"CI p. 14 OC (100, 4) at pi = {p}", printed, float(stats.binom.cdf(4, 100, p)))
    z = float(stats.norm.ppf(0.9))
    print("  CI p. 14 one-sided 90 % CI table: printed vs normal approximation vs exact binomial")
    for r in rows("S03_one_sided_90_ci_based_on_sample_size_100_for_various_observe"):
        x = int(pct(r["P (observed)"]))
        printed = r["one-sided 90%-CI"].split(",")[0].strip("[ ").replace("%", "")
        if x == 0:
            show("P = 0 %", "printed [0 %, 100 %]")
            continue
        normal = brentq(lambda pi: pi + z * np.sqrt(pi * (1 - pi) / 100) - x / 100, 1e-9, x / 100)
        exact = float(stats.beta.ppf(0.10, x, 100 - x + 1))
        show(f"P = {x} %: printed / normal approx / exact (%)", f"{printed} / {100*normal:.3f} / {100*exact:.3f}")
        check(f"CI p. 14 lower bound for P = {x} % (normal approx)", printed, 100 * normal, erratum=(x >= 2))
    show("CI p. 14: exact one-sided 90 % lower bound for P = 5 % (%)", float(100 * stats.beta.ppf(0.10, 5, 96)))
    show("TH FR p. 18: Z_0.05 (correct) vs Z_0.025 (printed) upper-tail values",
         f"{stats.norm.isf(0.05):.4f} vs {stats.norm.isf(0.025):.4f}")


def tolerance() -> None:
    """04.9: CI FR p. 22-23 (S03-WE16, S03-WE17), alpha = 5 %, beta = 10 % as in the p. 23 exercise."""
    print("04.9 Tolerance intervals")
    z10 = float(stats.norm.ppf(0.10))
    check("CI FR p. 22: 5.75 + Z_0.1 * 0.2", "5.49", 5.75 + z10 * 0.2)
    check("CI FR p. 22: ln(240)", "5.48", float(np.log(240)))
    za, zb = float(stats.norm.ppf(0.95)), float(stats.norm.ppf(0.90))
    k = za / np.sqrt(20) + zb
    ltl, utl = 5.732 - k * 0.2, 5.732 + k * 0.2
    show("situation 2 (alpha 5 %, beta 10 %): z_0.95/sqrt(20), k  [ex-04-17]", f"{za/np.sqrt(20):.4f} / {k:.4f}")
    show("LTL = 5.732 - k*0.2  [ex-04-17]", float(ltl))
    check("CI FR p. 22 LTL", "5.40", float(ltl))
    check("CI FR p. 22 UTL = Ybar + k sigma", "5.55", float(utl), erratum=True)
    other = 5.732 - (zb - za / np.sqrt(20)) * 0.2
    check("CI FR p. 22 UTL as upper bound of the 10 % point: Ybar - (z_0.9 - z_0.95/sqrt(20)) sigma", "5.55", float(other))
    n = 10
    d = 1 - za**2 / (2 * n)
    k10 = zb / d + za * np.sqrt(1 + z10**2 / 2 - za**2 / (2 * n)) / (np.sqrt(n) * d)
    show("situation 3 intermediates: Z_beta^2 / Z_1-a^2/2n / 1 - Z_1-a^2/2n", f"{z10**2:.4f} / {za**2/(2*n):.4f} / {d:.4f}")
    show("situation 3 terms: Z_1-b/d and second term", f"{zb/d:.4f} / {za*np.sqrt(1 + z10**2/2 - za**2/(2*n))/(np.sqrt(n)*d):.4f}")
    show("situation 3, n = 10: t(alpha, beta, n) approx  [ex-04-18]", float(k10))
    show("LTL = 5.8 - k*0.15  [ex-04-18]", float(5.8 - k10 * 0.15))
    need = next(m for m in range(1, 1000) if (1 - 0.10 / 2) ** m - 0.5 * (1 - 0.10) ** m <= 0.05 / 2)
    show("distribution-free: smallest n with (1-b/2)^n - (1-b)^n/2 <= a/2  [ex-04-19]", need)
    for m in (need - 1, need):
        show(f"  n = {m}: left side", float((0.95) ** m - 0.5 * 0.9 ** m))


def main() -> None:
    """Run every block; exit 1 on an unexpected mismatch."""
    point_vs_interval()
    confidence_vs_accuracy()
    inversion()
    mean_ci()
    proportion_ci()
    two_means()
    variance_ci()
    ratio_ci()
    duality()
    tolerance()
    if UNEXPECTED:
        print("UNEXPECTED MISMATCHES:", UNEXPECTED)
        sys.exit(1)
    print("Done: no unexpected mismatches.")


if __name__ == "__main__":
    main()
