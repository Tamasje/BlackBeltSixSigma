"""Numbers behind study/parts/02_data_kansen_causaliteit.html (Deel 02).

Prints every value the fragment marks "zelf berekend", every numeric exercise answer (data-answer), and re-checks
the printed course results the fragment quotes (OK / MISMATCH lines). At the end it reads the fragment and checks
that every numeric data-answer equals the value computed here, so text and script cannot drift apart.

Data come from inventory/constants (each row carries its course file and page) or are transcribed from the page
cited in a comment. Nothing is taken from memory. Run from anywhere:
    python3 study/parts/02_numbers.py
"""
from __future__ import annotations

import csv
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = ROOT / "inventory" / "constants"
FRAGMENT = Path(__file__).resolve().parent / "02_data_kansen_causaliteit.html"

# Exercise answers computed below, in the order the fragment's .q inputs appear: {exercise id: [values]}.
ANSWERS: dict[str, list[float]] = {}


def rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table in inventory/constants."""
    with (CONSTANTS / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def show(label: str, value: float | str, note: str = "") -> None:
    """Print one result line."""
    text = f"{value:.6g}" if isinstance(value, (float, np.floating)) else str(value)
    print(f"  {label:<58} {text:>14}  {note}")


def round_half_up(value: float, decimals: int) -> float:
    """Half-up rounding to a printed precision (decision 10 of inventory/conventions.md)."""
    quantum = Decimal(1).scaleb(-decimals)
    return float(Decimal(repr(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def check(label: str, computed: float, printed: str) -> None:
    """Compare a computed value with a printed course value at the printed precision."""
    decimals = len(printed.split(".")[1]) if "." in printed else 0
    status = "OK" if round_half_up(computed, decimals) == float(printed) else "MISMATCH"
    print(f"  {status:<8} {label:<50} computed {computed:.6g}  printed {printed}")


def answer(exercise: str, value: float) -> float:
    """Record an exercise answer for the consistency check against the fragment."""
    ANSWERS.setdefault(exercise, []).append(value)
    return value


def production_quality() -> None:
    """Joint, marginal and conditional probabilities: Naert p. 24-25, Naert notities p. 12 (S02-WE01)."""
    print("Productiekwaliteit per lijn (Naert p. 24-25; notities p. 12)")
    table = {r[""]: r for r in rows("S02_oefening_productiekwaliteit_per_lijn")}
    classes = ["Accepted", "Downgraded", "Rejected"]
    n = {(line, k): float(table[line][k]) for line in ("Lijn 1", "Lijn 2") for k in classes}
    total = float(table["Totaal"]["Totaal"])
    line_tot = {line: float(table[line]["Totaal"]) for line in ("Lijn 1", "Lijn 2")}
    k_tot = {k: float(table["Totaal"][k]) for k in classes}
    # The table's totals must add up before anything is divided by them.
    assert sum(n.values()) == total and sum(line_tot.values()) == total and sum(k_tot.values()) == total

    joint = n[("Lijn 2", "Accepted")] / total
    check("P(L = lijn 2, K = Acc.) (p. 25: 0,30)", answer("ex-02-10", joint), "0.30")
    for k, printed in zip(classes, ("0.70", "0.18", "0.12")):
        check(f"P(K = {k}) (p. 25)", answer("ex-02-10", k_tot[k] / total), printed)
    for k, printed in zip(classes, ("0.74", "0.19", "0.07")):
        check(f"P(K = {k} | lijn 1) (p. 25)", answer("ex-02-10", n[("Lijn 1", k)] / line_tot["Lijn 1"]), printed)
    for k in classes:
        show(f"P(K = {k} | lijn 2)", n[("Lijn 2", k)] / line_tot["Lijn 2"], "zelf berekend")
    check("afkeur lijn 2 (notities p. 12: ~17%)", 100 * n[("Lijn 2", "Rejected")] / line_tot["Lijn 2"], "17")
    show("P(L = lijn 1)", line_tot["Lijn 1"] / total, "zelf berekend")
    check("P(L = lijn 1, K = Goedgekeurd) (notities p. 12)", n[("Lijn 1", "Accepted")] / total, "0.40")
    product = line_tot["Lijn 1"] / total * k_tot["Accepted"] / total
    check("P(L = lijn 1) * P(K = Goedgekeurd) (notities p. 12)", answer("ex-02-10", product), "0.378")
    show("verwachte telling lijn 1 & Goedgekeurd bij onafhankelijkheid", product * total, "zelf berekend")


def poisson_customers() -> None:
    """P(more than 7 customers per minute) for lambda = 2.959: Naert p. 9-10, notities p. 5 (S02-WE09)."""
    print("Poisson klantenstromen (Naert p. 9-10; notities p. 5)")
    lam = 2.959  # Naert p. 9: "Poisson-verdeling P(2.959) met lambda = 2.959 klanten / minuut"
    p_le7 = float(stats.poisson.cdf(7, lam))
    p_gt7 = float(stats.poisson.sf(7, lam))
    show("P(X <= 7) = POISSON.DIST(7; 2,959; WAAR)", answer("ex-02-4", p_le7), "zelf berekend")
    show("P(X > 7) = 1 - P(X <= 7)", answer("ex-02-4", p_gt7), "zelf berekend")
    show("P(X > 7) in %", 100 * p_gt7, "zelf berekend")
    print(f"  {'OK' if p_gt7 < 0.02 else 'MISMATCH':<8} p. 10: 'minder dan 2% kans' op meer dan 7 klanten")


def beta_figure() -> None:
    """Mode, mean and median of Beta(2, 8) as annotated in the figure of Naert notities p. 4 (S11-WE01)."""
    print("Beta(2, 8) (Naert notities p. 4)")
    a, b = 2.0, 8.0
    check("modus (a - 1)/(a + b - 2)", (a - 1) / (a + b - 2), "0.125")
    check("gemiddelde", float(stats.beta.mean(a, b)), "0.200")
    check("mediaan", float(stats.beta.median(a, b)), "0.180")


def anscombe() -> None:
    """Summary statistics of Anscombe's four data sets: Van Volsem p. 134-137 (S01-WE11)."""
    print("Anscombe (VV p. 134, 136)")
    one = rows("S01_anscombe_s_quartet_dataset_1_ruwe_data")
    rest = rows("S01_anscombe_s_quartet_datasets_2_3_4_ruwe_data")
    sets = {"1": ([float(r["X"]) for r in one], [float(r["Y"]) for r in one])}
    for k in "234":
        sets[k] = ([float(r[f"X{k}"]) for r in rest], [float(r[f"Y{k}"]) for r in rest])
    for k, (xs, ys) in sets.items():
        x, y = np.asarray(xs), np.asarray(ys)
        fit = stats.linregress(x, y)
        residual_sd = float(np.sqrt(np.sum((y - fit.intercept - fit.slope * x) ** 2) / (len(x) - 2)))
        print(f"  dataset {k}")
        check("N", float(len(x)), "11")
        check("Mean of X", float(x.mean()), "9.0")
        check("Mean of Y", float(y.mean()), "7.5")
        check("Intercept", float(fit.intercept), "3")
        check("Slope", float(fit.slope), "0.5")
        check("Residual standard deviation", residual_sd, "1.237")
        check("Correlation", float(fit.rvalue), "0.816")
        if k == "3":
            for value in (fit.slope, fit.intercept, residual_sd, fit.rvalue):
                answer("ex-02-7", float(value))
            show("R^2 dataset 3", float(fit.rvalue**2), "zelf berekend")


def naert_simpson_slopes() -> None:
    """Sign of the subgroup slopes printed in the Simpson figure (Naert p. 38, notities p. 20)."""
    print("Simpson's paradox medicijn (Naert p. 37-38; notities p. 19-20)")
    pooled = float(rows("S11_simpson_s_paradox_pooled_regression_slope_figure_legend_ogen")[0]["slope as printed"])
    groups = rows("S11_simpson_s_paradox_regression_slopes_per_severity_group_figur")
    slopes = {r["legend entry"]: float(r["slope as printed"]) for r in groups}
    show("helling alle patienten samen (p. 37)", pooled, "gedrukt")
    for name, slope in slopes.items():
        show(f"helling {name}", slope, "gedrukt")
    negative = [name for name, slope in slopes.items() if slope < 0]
    status = "OK" if not negative else "MISMATCH"
    print(f"  {status:<8} 'In elke subgroep helpt het medicijn wel' (p. 38): negatieve hellingen bij {negative}")


def pitfall_numbers() -> None:
    """Numbers quoted only in the pitfall boxes: '7 or more' customers, and a reversed conditional probability."""
    print("Valkuilen (zelf berekend)")
    lam = 2.959  # Naert p. 9
    # "7 of meer" includes 7, so it is 1 - P(X <= 6), not 1 - P(X <= 7) ("meer dan 7").
    show("P(X >= 7) = 1 - P(X <= 6)  ('7 of meer')", float(stats.poisson.sf(6, lam)), "zelf berekend")
    table = {r[""]: r for r in rows("S02_oefening_productiekwaliteit_per_lijn")}
    rejected_line2 = float(table["Lijn 2"]["Rejected"])
    # Same cell, two different denominators: the row total of lijn 2 versus the column total of Rejected.
    show("P(K = Rejected | L = lijn 2) = 40/230", rejected_line2 / float(table["Lijn 2"]["Totaal"]), "zelf berekend")
    show("P(L = lijn 2 | K = Rejected) = 40/60", rejected_line2 / float(table["Totaal"]["Rejected"]), "zelf berekend")


def fragment_answers() -> dict[str, list[tuple[float, float]]]:
    """Numeric data-answer values (with data-tol) per exercise id, in document order."""
    html = FRAGMENT.read_text(encoding="utf-8")
    found: dict[str, list[tuple[float, float]]] = {}
    for block in re.split(r'(?=<div class="exercise")', html)[1:]:
        ex_id = re.match(r'<div class="exercise" id="([^"]+)"', block).group(1)
        for attrs in re.findall(r'<div class="q"([^>]*)>', block):
            if 'data-type="choice"' in attrs:
                continue
            value = float(re.search(r'data-answer="([^"]+)"', attrs).group(1))
            tol = float(re.search(r'data-tol="([^"]+)"', attrs).group(1))
            found.setdefault(ex_id, []).append((value, tol))
    return found


def choice_answers() -> None:
    """Print the expected option of every choice question, per exercise."""
    print("Keuzevragen: verwachte optie per oefening")
    html = FRAGMENT.read_text(encoding="utf-8")
    for block in re.split(r'(?=<div class="exercise")', html)[1:]:
        ex_id = re.match(r'<div class="exercise" id="([^"]+)"', block).group(1)
        options = [re.search(r'data-answer="([^"]+)"', attrs).group(1)
                   for attrs in re.findall(r'<div class="q"([^>]*)>', block) if 'data-type="choice"' in attrs]
        print(f"  {ex_id}: {', '.join(options) if options else '(geen keuzevragen)'}")


def consistency() -> bool:
    """Every numeric data-answer in the fragment must equal the value computed here (within half its tolerance)."""
    print("Controle: numerieke data-answer in het fragment versus berekening")
    found, ok = fragment_answers(), True
    for ex_id in sorted(set(found) | set(ANSWERS)):
        typed, computed = found.get(ex_id, []), ANSWERS.get(ex_id, [])
        if len(typed) != len(computed):
            print(f"  FOUT     {ex_id}: {len(typed)} numerieke vragen in het fragment, {len(computed)} berekend")
            ok = False
            continue
        for (value, tol), exact in zip(typed, computed):
            good = abs(value - exact) <= tol / 2
            ok &= good
            print(f"  {'OK' if good else 'FOUT':<8} {ex_id}: data-answer {value:g} (tol {tol:g}) vs {exact:.6g}")
    return ok


def main() -> int:
    """Run every block; exit 1 only if the fragment's answers drift from the computed ones."""
    production_quality()
    poisson_customers()
    beta_figure()
    anscombe()
    naert_simpson_slopes()
    pitfall_numbers()
    choice_answers()
    return 0 if consistency() else 1


if __name__ == "__main__":
    sys.exit(main())
