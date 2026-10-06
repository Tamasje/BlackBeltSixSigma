"""Numbers for Deel 05 (testing of hypotheses and test recipes, Ottoy, Les 2): every value that
study/parts/05_hypothesetoetsen.html marks "zelf berekend", every exercise answer (data-answer), and a re-check of every
printed course result the text quotes.

Data come from inventory/constants (rows carry file + page), from the course spreadsheet
source/course/Les 2/20260529_ottoy_Testing of Hypotheses.xlsx (read-only, openpyxl), or are transcribed from the slide
named in the comment next to them. Nothing is taken from memory.

Check lines: "OK" = equal after half-up rounding to the printed precision; "MISMATCH (erratum)" = known disagreement,
listed in 05_errata.tsv; "approx OK" = the course states the value as approximate ("≅", "about").
An unexpected mismatch makes the script exit 1. Run from the project root:  python3 study/parts/05_numbers.py
"""
from __future__ import annotations

import csv
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import openpyxl
from scipy import stats

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
    return [float(c.value) for row in wb[sheet][cells] for c in row]


def show(label: str, value: float | str, note: str = "") -> None:
    """Print one result line."""
    text = f"{value:.6g}" if isinstance(value, (float, np.floating)) else str(value)
    print(f"  {label:<62} {text:>14}  {note}")


def half_up(value: float, decimals: int) -> Decimal:
    """Half-up rounding (decision 10: compare at the printed precision)."""
    return Decimal(repr(float(value))).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def check(label: str, printed: str, computed: float, erratum: bool = False) -> None:
    """Compare a printed course value with the computation at the printed precision."""
    decimals = len(printed.split(".")[1]) if "." in printed else 0
    same = half_up(computed, decimals) == Decimal(printed)
    status = "OK" if same else ("MISMATCH (erratum)" if erratum else "MISMATCH")
    if not same and not erratum:
        UNEXPECTED.append(label)
    print(f"  [{status}] {label}: printed {printed}, computed {computed:.6g}")


def approx(label: str, printed: float, computed: float, tol: float) -> None:
    """Check a value the course itself states as approximate."""
    ok = abs(printed - computed) <= tol
    if not ok:
        UNEXPECTED.append(label)
    print(f"  [{'approx OK' if ok else 'MISMATCH'}] {label}: printed ≈{printed:g}, computed {computed:.6g} (tol {tol:g})")


def tiles() -> None:
    """05.2: acceptance sampling of tiles as a test (TH p. 5-10): binomial, n = 100 / 130."""
    print("05.2 Tiles: lot of 10000, AQL 2 % (TH p. 3-10)")
    acc_h0 = float(stats.binom.cdf(4, 100, 0.02))
    acc_ha = float(stats.binom.cdf(4, 100, 0.08))
    approx("TH p. 5: P[d <= 4] at P = 2 %", 0.95, acc_h0, 0.005)
    approx("TH p. 5: P[d <= 4] at P = 8 %", 0.10, acc_ha, 0.01)
    check("TH p. 7: beta at P = 8 % (in %)", "9", 100 * acc_ha)
    check("TH p. 6: alpha = P[d >= 5] at AQL (in %)", "5", 100 * (1 - acc_h0))
    check("TH p. 6: c = 5 -> alpha (in %)", "1.5", 100 * float(stats.binom.sf(5, 100, 0.02)))
    approx("TH p. 5 notes: P[d = 4] at 2 % 'almost 10 %'", 0.10, float(stats.binom.pmf(4, 100, 0.02)), 0.01)
    check("TH p. 5 notes: P[d = 4] at 8 % (in %)", "5", 100 * float(stats.binom.pmf(4, 100, 0.08)))
    check("TH p. 8: (130, 5) alpha (in %)", "5", 100 * float(stats.binom.sf(5, 130, 0.02)))
    check("TH p. 8: (130, 5) beta at 8 % (in %)", "5", 100 * float(stats.binom.cdf(5, 130, 0.08)))
    check("TH p. 9: 130 = share of the lot (in %)", "1.3", 100 * 130 / 10000)
    pval = float(stats.binom.sf(3, 130, 0.02))
    show("TH p. 10: p-value P[d >= 4 | n = 130, pi = 2 %]  [ex-05-4]", pval)
    show("  in %  [ex-05-4]", 100 * pval)


def picture_tubes() -> None:
    """05.2-05.5: TH FR p. 7-15, picture tubes: mu0 = 1200, sigma = 300, n = 100 (S03-WE10, S03-WE11)."""
    print("05.2-05.5 Picture tubes (TH FR p. 7-15)")
    se = 300 / np.sqrt(100)
    z99, z995, z95, z975 = (float(stats.norm.ppf(q)) for q in (0.99, 0.995, 0.95, 0.975))
    show("sigma/sqrt(n)", float(se))
    show("z_0.99 / z_0.995 / z_0.95 / z_0.975", f"{z99:.4f} / {z995:.4f} / {z95:.4f} / {z975:.4f}")
    crit = 1200 + z99 * se
    check("TH FR p. 10: critical value one-sided alpha 1 %  [ex-05-2]", "1270", crit)
    check("TH FR p. 10: printed multiplier 2.3: 1200 + 2.3*30", "1270", 1200 + 2.3 * 30, erratum=True)
    p1 = float(stats.norm.sf((1265 - 1200) / se))
    show("z of 1265 / one-sided p-value  [ex-05-2]", f"{(1265-1200)/se:.4f} / {p1:.5f}")
    check("TH FR p. 11: one-sided p-value (in %)", "1.5", 100 * p1)
    check("TH FR p. 15: two-sided p-value (in %)  [ex-05-6]", "3.0", 200 * p1)
    check("TH FR p. 15: mirror point 1200 - 65", "1135", 1200 - 65)
    check("TH FR p. 12: two-sided alpha 5 %: left critical value", "1141", 1200 - z975 * se)
    check("TH FR p. 12: two-sided alpha 5 %: right critical value", "1259", 1200 + z975 * se)
    check("TH FR p. 13: left critical value alpha 1 %  [ex-05-6]", "1123", 1200 - z995 * se)
    check("TH FR p. 13: right critical value alpha 1 %  [ex-05-6]", "1277", 1200 + z995 * se)
    check("TH FR p. 13: printed multiplier 2.6: 1200 - 2.6*30", "1123", 1200 - 2.6 * 30, erratum=True)
    check("TH FR p. 13: printed multiplier 2.6: 1200 + 2.6*30", "1277", 1200 + 2.6 * 30, erratum=True)
    crit5 = 1200 + z95 * se
    beta = float(stats.norm.cdf((crit5 - 1270) / se))
    show("TH FR p. 7: critical value alpha 5 %, beta at mu = 1270  [ex-05-3]", f"{crit5:.2f} / {beta:.4f}")
    show("z-values for beta: (k - 1270)/30, (k - 1300)/30, n = 195: (k - 1300)/(300/sqrt(195))",
         f"{(crit5-1270)/se:.3f} / {(crit-1300)/se:.3f} / {(1200 + z99*300/np.sqrt(195) - 1300)/(300/np.sqrt(195)):.3f}")
    check("TH FR p. 7: beta (in %)", "25", 100 * beta)
    beta100 = float(stats.norm.cdf((crit - 1300) / se))
    check("TH FR p. 9: beta at mu = 1300, n = 100, alpha 1 % (in %)  [ex-05-3]", "16", 100 * beta100)
    se195 = 300 / np.sqrt(195)
    crit195 = 1200 + z99 * se195
    beta195 = float(stats.norm.cdf((crit195 - 1300) / se195))
    show("TH FR p. 9: n = 195: sigma/sqrt(n) / critical value / beta", f"{se195:.3f} / {crit195:.2f} / {beta195:.5f}")
    check("TH FR p. 9: beta at n = 195 (in %)  [ex-05-3]", "1", 100 * beta195)
    check("TH FR p. 9: critical value at n = 195 drawn at", "1250", crit195)
    show("TH FR p. 11 notes (Brainstorm): expected 'significant' studies of 100 at 5 %  [ex-05-5]", 100 * 0.05)


def t_and_chi2_examples() -> None:
    """05.7-05.8: TH p. 12-13, sheets 'example t-test' and 'example chi²-test' (S03-WE04, S03-WE05)."""
    print("05.7 t-test (TH p. 12)")
    data = sheet_column("20260529_ottoy_Testing of Hypotheses.xlsx", "example t-test", "B3:B22")
    n = len(data)
    xbar, s = float(np.mean(data)), float(np.std(data, ddof=1))
    t = (xbar - 10) / (s / np.sqrt(n))
    crit = float(stats.t.ppf(0.02, n - 1))
    pval = float(stats.t.cdf(t, n - 1))
    show("n / xbar / s  [ex-05-8]", f"{n} / {xbar:.4f} / {s:.5f}")
    show("t = (xbar - 10)/(s/sqrt(n))  [ex-05-8]", t)
    check("TH p. 12 test statistic", "-2.95", t)
    check("TH p. 12 critical value T.INV(0.02;19)  [ex-05-8]", "-2.20", crit)
    check("TH p. 12 p-value (in %)  [ex-05-8]", "0.4", 100 * pval)
    show("p-value T.DIST(t;19;TRUE)", pval)
    slide = [10.06, 9.89, 9.90, 9.99, 9.87, 9.88, 9.93, 9.98, 10.12, 9.86,
             9.89, 9.81, 9.95, 9.92, 10.07, 9.98, 10.02, 9.62, 9.96, 9.86]  # TH p. 12, data rounded on the slide
    xs, ss = float(np.mean(slide)), float(np.std(slide, ddof=1))
    ts = (xs - 10) / (ss / np.sqrt(20))
    show("slide-rounded data: xbar / s / t / p", f"{xs:.4f} / {ss:.5f} / {ts:.4f} / {stats.t.cdf(ts, 19):.5f}")
    med = float(np.median(data))
    signs = ["+" if v > med else "-" for v in data]
    runs = 1 + sum(a != b for a, b in zip(signs, signs[1:]))
    e_r, sd_r = (n + 2) / 2, np.sqrt((n - 1) / 4)
    show("runs test (Test Recipes p. 25-26): median / sign sequence", f"{med:.4f} / {''.join(signs)}")
    show("R / E(R) = (n+2)/2 / sd = sqrt((n-1)/4) / z  [ex-05-18]", f"{runs} / {e_r:g} / {sd_r:.4f} / {(runs-e_r)/sd_r:.4f}")
    print("05.8 chi2-test (TH p. 13)")
    data = sheet_column("20260529_ottoy_Testing of Hypotheses.xlsx", "example chi²-test", "B3:B22")
    var = float(np.var(data, ddof=1))
    chi = 19 * var / 0.01**2
    crit = float(stats.chi2.ppf(0.98, 19))
    pval = float(stats.chi2.sf(chi, 19))
    show("s^2 / s  [ex-05-9]", f"{var:.6e} / {np.sqrt(var):.6f}")
    show("chi2 = 19 s^2 / 0.01^2  [ex-05-9]", chi)
    check("TH p. 13 critical value CHISQ.INV(0.98;19)  [ex-05-9]", "33.69", crit)
    check("TH p. 13 p-value (in %)  [ex-05-9]", "13.6", 100 * pval)


def recipes_t() -> None:
    """05.10: Test Recipes p. 4-8 applied to the shoe-sole data of CI FR p. 17-18."""
    print("05.10 Unpaired and paired t-test on the shoe soles (CI FR p. 17-18)")
    un = rows("S03_niet_paarsgewijze_schoenzool_experiment_ruwe_data_rs1_en_rs2")
    a = np.array([float(r["LD1"]) for r in un])
    b = np.array([float(r["LD2"]) for r in un])
    sp = np.sqrt((9 * a.var(ddof=1) + 9 * b.var(ddof=1)) / 18)
    t = (a.mean() - b.mean()) / (sp * np.sqrt(0.2))
    show("unpaired: s_p / t / t_0.975,18 / two-sided p  [ex-05-10]",
         f"{sp:.4f} / {t:.4f} / {stats.t.ppf(0.975, 18):.4f} / {2*stats.t.sf(abs(t), 18):.4f}")
    ranks = stats.rankdata(np.concatenate([a, b]))
    w = float(ranks[:10].sum())
    e_w, sd_w = 10 * 21 / 2, np.sqrt(10 * 10 * 21 / 12)
    show("Mann-Whitney: W_X1 / E / sd / z (Test Recipes p. 21-22)  [ex-05-17]",
         f"{w:g} / {e_w:g} / {sd_w:.4f} / {(w-e_w)/sd_w:.4f}")
    s1, s2 = a.std(ddof=1), b.std(ddof=1)
    f = s2**2 / s1**2
    show("F-test equal spreads: F = s2^2/s1^2 / F.INV.RT(0.025;9;9) / two-sided p  [ex-05-13]",
         f"{f:.4f} / {stats.f.isf(0.025, 9, 9):.4f} / {2*stats.f.sf(f, 9, 9):.4f}")
    pa = rows("S03_paarsgewijze_schoenzool_experiment_ruwe_data_10_jongens_ld1")
    v = np.array([float(r["LD1"]) - float(r["LD2"]) for r in pa])
    tv = v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))
    show("paired: t / t_0.975,9 / two-sided p  [ex-05-11]",
         f"{tv:.4f} / {stats.t.ppf(0.975, 9):.4f} / {2*stats.t.sf(abs(tv), 9):.5f}")
    nz = v[v != 0]
    r = stats.rankdata(np.abs(nz))
    t_plus = float(r[nz > 0].sum())
    m = len(nz)
    e_t, sd_t = m * (m + 1) / 4, np.sqrt(m * (m + 1) * (2 * m + 1) / 24)
    show("signed ranks: n (zeros removed) / T+ / E / sd / z (Test Recipes p. 23-24)  [ex-05-16]",
         f"{m} / {t_plus:g} / {e_t:g} / {sd_t:.4f} / {(t_plus-e_t)/sd_t:.4f}")


def proportion_test() -> None:
    """05.11: TH FR p. 22 exercise (S03-WE12) with the Z-test for pi (Test Recipes p. 9-10); alpha = 5 % assumed."""
    print("05.11 Z-test for pi (TH FR p. 22)")
    n, d, pi0, pi1, alpha = 400, 10, 0.02, 0.03, 0.05
    p = d / n
    se0 = np.sqrt(pi0 * (1 - pi0) / n)
    z = (p - pi0) / se0
    zc = (p - 1 / (2 * n) - pi0) / se0
    show("n*pi0 (condition > 5)", n * pi0)
    show("p / se0 / z  [ex-05-12]", f"{p:.4f} / {se0:.5f} / {z:.4f}")
    show("z with continuity correction (right: p - 1/(2n))", float(zc))
    show("p-value (normal) / with continuity correction / exact binomial  [ex-05-12]",
         f"{stats.norm.sf(z):.4f} / {stats.norm.sf(zc):.4f} / {stats.binom.sf(d - 1, n, pi0):.4f}")
    z95 = float(stats.norm.ppf(1 - alpha))
    crit = pi0 + z95 * se0
    se1 = np.sqrt(pi1 * (1 - pi1) / n)
    beta = float(stats.norm.cdf((crit - pi1) / se1))
    show("critical fraction pi0 + z_0.95*se0 / as a count  [ex-05-12]", f"{crit:.5f} / {crit*n:.3f}")
    show("se1 = sqrt(0.03*0.97/400) / z = (crit - 0.03)/se1", f"{se1:.5f} / {(crit - pi1)/se1:.4f}")
    show("P(accept H0 | pi = 3 %) normal approx  [ex-05-12]", beta)
    show("P(accept H0 | pi = 3 %) exact binomial with d <= 12", float(stats.binom.cdf(12, n, pi1)))
    z90 = float(stats.norm.ppf(0.90))
    n_formula = ((z95 * np.sqrt(pi0 * (1 - pi0)) + z90 * np.sqrt(pi1 * (1 - pi1))) / (pi1 - pi0)) ** 2
    show("sqrt(n) = (z_0.95*sqrt(pi0(1-pi0)) + z_0.90*sqrt(pi1(1-pi1)))/0.01", float(np.sqrt(n_formula)))
    show("n from z_0.95*sqrt(pi0(1-pi0)/n) + z_0.90*sqrt(pi1(1-pi1)/n) = 0.01", float(n_formula))
    def beta_at(m: int) -> float:
        """P(accept H0) at pi = 3 % for sample size m (normal approximation)."""
        c = pi0 + z95 * np.sqrt(pi0 * (1 - pi0) / m)
        return float(stats.norm.cdf((c - pi1) / np.sqrt(pi1 * (1 - pi1) / m)))
    need = next(m for m in range(400, 5000) if beta_at(m) < 0.10)
    show("smallest n with P(accept | 3 %) < 10 %  [ex-05-12]", need)
    show("  beta at n-1 / n", f"{beta_at(need - 1):.5f} / {beta_at(need):.5f}")


def f_test() -> None:
    """05.12: F distribution (Test Recipes p. 12) and the F-test on the Dummies data (PDF p. 196)."""
    print("05.12 F-test")
    f = 7.5 / 4.0
    crit = float(stats.f.isf(0.05, 4, 9))
    show("F = sB^2/sA^2 / F.INV.RT(0.05;4;9) / p = F.DIST.RT  [ex-05-14]", f"{f:.4f} / {crit:.4f} / {stats.f.sf(f, 4, 9):.4f}")
    check("Dummies Table 8-3 value used as critical value", "3.633", crit)
    show("Test Recipes p. 12: E(F(30,60)) = 60/58 / mode = 28*60/(30*62)", f"{60/58:.4f} / {28*60/(30*62):.4f}")


def z_quantiles() -> None:
    """05_symbols.tsv pop-ups: the standard-normal quantiles they quote (1.282 = z_0.90 is used in ex-05-12 e)."""
    print("Z quantiles quoted in 05_symbols.tsv")
    for q in (0.90, 0.95, 0.975, 0.99, 0.995):
        show(f"NORM.S.INV({q})", float(stats.norm.ppf(q)))


def main() -> None:
    """Run every block; exit 1 on an unexpected mismatch."""
    tiles()
    picture_tubes()
    t_and_chi2_examples()
    recipes_t()
    proportion_test()
    f_test()
    z_quantiles()
    if UNEXPECTED:
        print("UNEXPECTED MISMATCHES:", UNEXPECTED)
        sys.exit(1)
    print("Done: no unexpected mismatches.")


if __name__ == "__main__":
    main()
