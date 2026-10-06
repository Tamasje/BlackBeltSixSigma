"""Every number that study/les3_doe_regression.html derives itself (worked solutions, intermediate steps), computed
from the course data, plus a re-check of the course's printed results the text quotes.

Data come from inventory/constants (each row carries its course file and page) or, for the two data sets that only
exist in a figure, from the slide cited next to them. Nothing here is taken from memory. Run from the project root:
    python3 study/les3_numbers.py
"""
from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
CONSTANTS = ROOT / "inventory" / "constants"


def rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table in inventory/constants."""
    with (CONSTANTS / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def show(label: str, value: float | str, note: str = "") -> None:
    """Print one result line."""
    text = f"{value:.6g}" if isinstance(value, (float, np.floating)) else str(value)
    print(f"  {label:<46} {text:>14}  {note}")


def one_way(title: str, groups: list[list[float]], alpha: float) -> None:
    """One-way ANOVA table (DOE p. 6-8)."""
    print(title)
    y = np.concatenate([np.asarray(g, float) for g in groups])
    a, n_total = len(groups), len(y)
    means = [np.mean(g) for g in groups]
    ss_t = float(np.sum((y - y.mean()) ** 2))
    ss_tr = float(sum(len(g) * (m - y.mean()) ** 2 for g, m in zip(groups, means)))
    ss_e = ss_t - ss_tr
    df_tr, df_e = a - 1, n_total - a
    f0 = (ss_tr / df_tr) / (ss_e / df_e)
    show("group totals", str([float(np.sum(g)) for g in groups]))
    show("group means", str([round(float(m), 4) for m in means]))
    show("grand total / grand mean", f"{y.sum():g} / {y.mean():.4f}")
    show("SS_T  = sum of squares about grand mean", ss_t)
    show("SS_Tr = sum n (group mean - grand mean)^2", ss_tr)
    show("SS_E  = SS_T - SS_Tr", ss_e)
    show("df treatments / error / total", f"{df_tr} / {df_e} / {n_total - 1}")
    show("MS_Tr / MS_E", f"{ss_tr / df_tr:.4f} / {ss_e / df_e:.4f}")
    show("F0", f0)
    show("p-value P(F > F0)", float(stats.f.sf(f0, df_tr, df_e)))
    show(f"F crit at alpha = {alpha}", float(stats.f.isf(alpha, df_tr, df_e)))
    show("pooled sd = sqrt(MS_E)", float(np.sqrt(ss_e / df_e)))
    show("scale sqrt(MS_E / n) (DOE p. 19)", float(np.sqrt(ss_e / df_e / len(groups[0]))))


def signs(k: int) -> np.ndarray:
    """Coded design matrix of a 2^k in standard order (A changes fastest), shape (2^k, k)."""
    return np.array([[1 if r >> j & 1 else -1 for j in range(k)] for r in range(2 ** k)])


def effect_table(title: str, k: int, runs: list[list[float]]) -> dict[str, float]:
    """Contrast, effect and SS of every effect of a balanced 2^k (DOE p. 57, 66); returns the SS by name."""
    print(title)
    x, letters = signs(k), "ABCDE"[:k]
    n = len(runs[0])
    totals = np.array([sum(r) for r in runs])
    show("run totals in standard order", str([float(t) for t in totals]))
    ss = {}
    for size in range(1, k + 1):
        for combo in combinations(range(k), size):
            column = np.prod(x[:, combo], axis=1)
            contrast = float(column @ totals)
            name = "".join(letters[j] for j in combo)
            ss[name] = contrast ** 2 / (n * 2 ** k)
            show(f"{name}: contrast / effect / SS",
                 f"{contrast:g} / {contrast / (n * 2 ** (k - 1)):.4f} / {ss[name]:.4f}")
    y = np.concatenate([np.asarray(r, float) for r in runs])
    pure_error = float(sum(np.sum((np.asarray(r) - np.mean(r)) ** 2) for r in runs))
    show("SS total", float(np.sum((y - y.mean()) ** 2)))
    show("SS pure error (replicates)", pure_error)
    show("grand mean", float(y.mean()))
    return ss


def word_product(a: str, b: str) -> str:
    """Product of two effect words with A·A = I (DOE p. 81): the letters that occur in exactly one of them."""
    return "".join(sorted(set(a) ^ set(b))) or "I"


def defining_relation(generators: list[str]) -> list[str]:
    """All words of the complete defining relation from generator words (DOE p. 91)."""
    words = set()
    for size in range(1, len(generators) + 1):
        for combo in combinations(generators, size):
            word = "I"
            for g in combo:
                word = word_product(word if word != "I" else "", g)
            words.add(word)
    return sorted(words, key=lambda w: (len(w), w))


def regression(title: str, x: np.ndarray, y: np.ndarray, x0: float, alpha: float) -> None:
    """Simple linear regression quantities (Regression p. 17-38)."""
    print(title)
    n = len(x)
    sxx, sxy = float(np.sum((x - x.mean()) ** 2)), float(np.sum((x - x.mean()) * (y - y.mean())))
    b1 = sxy / sxx
    b0 = float(y.mean() - b1 * x.mean())
    fit = b0 + b1 * x
    sst, sse = float(np.sum((y - y.mean()) ** 2)), float(np.sum((y - fit) ** 2))
    ssr, mse = sst - sse, sse / (n - 2)
    se_b1, se_b0 = np.sqrt(mse / sxx), np.sqrt(mse * (1 / n + x.mean() ** 2 / sxx))
    t2 = float(stats.t.ppf(1 - alpha / 2, n - 2))
    for label, value in (("n, x-bar, y-bar", f"{n}, {x.mean():.4f}, {y.mean():.4f}"), ("Sxx", sxx), ("Sxy", sxy),
                         ("b1 = Sxy / Sxx", b1), ("b0 = y-bar - b1 x-bar", b0), ("SST", sst), ("SSR", ssr),
                         ("SSE", sse), ("MSE = SSE/(n-2)", mse), ("S = sqrt(MSE)", float(np.sqrt(mse))),
                         ("R^2", ssr / sst), ("R^2 adj, (n-1)/(n-2)", 1 - (1 - ssr / sst) * (n - 1) / (n - 2)),
                         ("se(b1) / se(b0)", f"{se_b1:.4f} / {se_b0:.4f}"), ("t0 for b1 / for b0",
                         f"{b1 / se_b1:.3f} / {b0 / se_b0:.3f}"), ("F0 = MSR/MSE", ssr / mse),
                         ("t0(b1)^2", (b1 / se_b1) ** 2), ("p-value of t0(b1)", float(2 * stats.t.sf(b1 / se_b1, n - 2))),
                         (f"t quantile 1-alpha/2, df {n - 2}", t2),
                         ("t quantile 0.995, df n-2 (p. 32: 2.88)", float(stats.t.ppf(0.995, n - 2))),
                         ("CI beta1", f"[{b1 - t2 * se_b1:.3f}, {b1 + t2 * se_b1:.3f}]"),
                         ("CI beta0", f"[{b0 - t2 * se_b0:.3f}, {b0 + t2 * se_b0:.3f}]")):
        show(label, value)
    y0 = b0 + b1 * x0
    se_fit = np.sqrt(mse * (1 / n + (x0 - x.mean()) ** 2 / sxx))
    se_pred = np.sqrt(mse * (1 + 1 / n + (x0 - x.mean()) ** 2 / sxx))
    show(f"fit at x0 = {x0}", y0)
    show("se(fit) / se(prediction error)", f"{se_fit:.4f} / {se_pred:.4f}")
    show("CI mean response", f"[{y0 - t2 * se_fit:.3f}, {y0 + t2 * se_fit:.3f}]")
    show("prediction interval", f"[{y0 - t2 * se_pred:.3f}, {y0 + t2 * se_pred:.3f}]")


def least_squares(columns: list[np.ndarray], y: np.ndarray) -> tuple[np.ndarray, float, float]:
    """OLS coefficients, SSE and SST for a model with intercept."""
    design = np.column_stack([np.ones(len(y)), *columns])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return beta, float(np.sum((y - design @ beta) ** 2)), float(np.sum((y - y.mean()) ** 2))


def main() -> None:
    """Print every derived number of the study text, in the order of its sections (regression first)."""
    oxygen = rows("S05_table_11_1_oxygen_and_hydrocarbon_levels")
    x = np.array([float(r["Hydrocarbon Level x (%)"]) for r in oxygen])
    y = np.array([float(r["Purity y (%)"]) for r in oxygen])
    regression("1.3-1.6 Oxygen purity (Regression p. 2, 20-22, 32), alpha 0.05", x, y, 1.00, 0.05)

    oil = rows("S05_oil_consumption_example_data_for_15_houses")
    y = np.array([float(r["Oil (Gal)"].replace(",", ".")) for r in oil])
    temp, ins = (np.array([float(r[c]) for r in oil]) for c in ("Temp", "Insulation"))
    beta, sse, sst = least_squares([temp, ins], y)
    print("2.1 Oil consumption (Regression p. 51-57)")
    n, k = len(y), 2
    r2 = 1 - sse / sst
    show("b0, b1 (Temp), b2 (Insulation)", ", ".join(f"{b:.6f}" for b in beta))
    show("SSE / MSE / sqrt(MSE)", f"{sse:.3f} / {sse / (n - k - 1):.4f} / {np.sqrt(sse / (n - k - 1)):.4f}")
    show("R^2", r2)
    show("adj R^2 with (n-1)/(n-k-1) (Excel)", 1 - (1 - r2) * (n - 1) / (n - k - 1))
    show("adj R^2 with (n-1)/(n-k-2) (p. 56 print)", 1 - (1 - r2) * (n - 1) / (n - k - 2))
    show("prediction at Temp 30, Insulation 6", float(beta @ [1, 30, 6]))
    show("same with the slide's rounded 562.15, 5.43, 20.01", 562.15 - 5.43 * 30 - 20.01 * 6)

    acet = rows("S05_table_6_9_the_acetylene_data")
    y = np.array([float(r["Yield Y"]) for r in acet])
    t, ratio = (np.array([float(r[c]) for r in acet]) for c in ("Temp T", "Ratio R"))
    _, sse_reduced, _ = least_squares([t, ratio], y)
    tc, rc = t - 1212.5, ratio - 12.444
    _, sse_full, _ = least_squares([tc, rc, tc * rc, tc ** 2, rc ** 2], y)
    print("2.3 Acetylene (Regression p. 58-62): reduced model T + R vs second-order model")
    show("SSE reduced (p. 59: 170.73) / full (p. 62: 11.37)", f"{sse_reduced:.2f} / {sse_full:.2f}")
    f0 = ((170.73 - 11.37) / (5 - 2)) / (11.37 / (16 - 6))
    show("partial F0 from the printed SSEs, df (3, 10)", f0)
    show("F crit 0.05 (3, 10) / p-value", f"{stats.f.isf(0.05, 3, 10):.3f} / {stats.f.sf(f0, 3, 10):.2e}")

    paper = [[float(r[f"Obs{i}"]) for i in range(1, 7)]
             for r in rows("S05_table_4_4_tensile_strength_of_paper_psi") if r["Obs1"]]
    one_way("3.5 Paper tensile strength (DOE p. 4, 9-10), alpha 0.01", paper, 0.01)
    fibre = [[float(r[f"Obs{i}"]) for i in range(1, 6)]
             for r in rows("S05_table_3_1_data_in_lb_in_2_from_the_tensile_strength_experime") if r["Obs1"]]
    one_way("3.6 Synthetic fibre (DOE p. 13-15, 19), alpha 0.05", fibre, 0.05)
    machines_rows = rows("S05_table_10_1_sample_outputs_of_three_machines")
    print("   machines table columns:", list(machines_rows[0])[:4])
    machines = [[float(r[c]) for r in machines_rows if r[c].strip().lstrip("-").replace(".", "").isdigit()]
                for c in list(machines_rows[0])[:3]]
    one_way("3.9 Three machines (DOE p. 20; the course gives no solution), alpha 0.05", machines, 0.05)

    print("4.2 Golf (DOE p. 27 figure: driver O/R, ball B/T, two scores per corner)")
    golf = {("O", "B"): [88, 90], ("R", "B"): [93, 91], ("O", "T"): [88, 91], ("R", "T"): [92, 94]}
    effect_table("   as a 2^2 with A = driver (O -1, R +1), B = ball (B -1, T +1), n = 2", 2,
                 [golf[("O", "B")], golf[("R", "B")], golf[("O", "T")], golf[("R", "T")]])
    print("4.4 Yield, second experiment (DOE p. 37 figure: A = concentration 0/12, B = duration 10/25)")
    effect_table("   runs (0,10)=17, (12,10)=16, (0,25)=24, (12,25)=23", 2, [[17], [16], [24], [23]])

    coded = [[5.94, 5.50, 6.10], [4.16, 6.72, 2.72], [5.50, 5.25, 5.16], [6.25, 5.90, 4.97]]
    effect_table("5.2 Coded example (DOE p. 47-50), standard order (1), a, b, ab", 2, coded)
    effect_table("5.3 Corners without interaction (DOE p. 53)", 2, [[20], [40], [30], [52]])
    effect_table("5.3 Corners with interaction (DOE p. 54)", 2, [[20], [50], [40], [12]])

    chem = {(r["A"], r["B"]): [float(r[f"Rep {i}"]) for i in ("I", "II", "III")]
            for r in rows("S05_chemical_process_example_treatment_combinations_and_replicat")}
    chem_runs = [chem[(a, b)] for b in "-+" for a in "-+"]
    ss = effect_table("5.5 Chemical process (DOE p. 59-61)", 2, chem_runs)
    pure = float(sum(np.sum((np.asarray(r) - np.mean(r)) ** 2) for r in chem_runs))
    mse = pure / 8
    model = sum(ss.values())
    show("MS_E = SS_PE / 8", mse)
    for name in ("A", "B", "AB"):
        show(f"F0 {name} / p", f"{ss[name] / mse:.3f} / {stats.f.sf(ss[name] / mse, 1, 8):.5f}")
    show("Model SS / F0 / p", f"{model:.3f} / {model / 3 / mse:.3f} / {stats.f.sf(model / 3 / mse, 3, 8):.5f}")
    total = model + pure
    show("R^2 / adj R^2 (df)", f"{model / total:.4f} / {1 - mse / (total / 11):.4f}")

    surface = [[float(v) for v in r["Surface Finish obs1,obs2"].split(",")]
               for r in rows("S05_surface_finish_quality_example_data_2_3_design_n_2")]
    ss = effect_table("5.6 Surface finish (DOE p. 69-71), n = 2", 3, surface)
    pure = float(sum(np.sum((np.asarray(r) - np.mean(r)) ** 2) for r in surface))
    mse = pure / 8
    se = float(np.sqrt(mse / (2 * 2 ** (3 - 2))))
    show("MS_E = SS_PE / 8", mse)
    show("s.e.(effect) = sqrt(MS_E / (n 2^(k-2)))", se)
    contrasts = {"A": 27, "B": 13, "C": 7, "AB": 11, "AC": 1, "BC": -5, "ABC": 9}  # printed by effect_table above
    for name, value in ss.items():
        f0, effect = value / mse, contrasts[name] / 8
        show(f"{name}: F0 / p / effect +- 2 s.e.",
             f"{f0:.3f} / {stats.f.sf(f0, 1, 8):.4f} / [{effect - 2 * se:.3f}, {effect + 2 * se:.3f}]")
    show("t quantile 0.975, df 8 (versus the rule's 2)", float(stats.t.ppf(0.975, 8)))

    etch = [[float(r["Etch Rate (Angstrom/min)"])] for r in rows("S05_etch_rate_example_data_single_replicate_2_4_design")]
    ss = effect_table("5.7 Etch rate (DOE p. 74-77), single replicate", 4, etch)
    pooled = sum(v for name, v in ss.items() if len(name) >= 3)
    show("SS pooled 3- and 4-factor interactions (df 5)", pooled)
    show("MS_E pooled", pooled / 5)
    for name in ("A", "D", "AD"):
        show(f"F0 {name}", ss[name] / (pooled / 5))

    print("6 Fractional factorials (DOE p. 80-93)")
    for effect in ("A", "B", "C", "AB", "AC", "BC"):
        show(f"I = ABC: alias of {effect}", word_product(effect, "ABC"))
    show("2^(6-2), E = ABC, F = BCD: defining relation", " = ".join(["I"] + defining_relation(["ABCE", "BCDF"])))
    show("2^(5-1), I = ABCDE: shortest word", min(len(w) for w in defining_relation(["ABCDE"])))
    relation = defining_relation(["ABD", "ACE"])
    show("2^(5-2), D = AB, E = AC: defining relation", " = ".join(["I"] + relation))
    show("2^(5-2): A is aliased with", ", ".join(word_product("A", w) for w in relation))
    show("k = 11: 2^11 runs / 32 runs as fraction", f"{2 ** 11} / 1/{2 ** 11 // 32}")

if __name__ == "__main__":
    main()
