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


def steel_dilution() -> None:
    """Measurement-error variance implied by alpha = 1 and alpha' = 0.94: Naert p. 57, notities p. 28-29."""
    print("Regression dilution staal (Naert p. 57; notities p. 28-29)")
    alpha, alpha_naive = 1.0, 0.94  # notities p. 29: "zelfs als alpha = 1 ... alpha' ~ 0.94"
    # alpha' = alpha Var(T1) / (Var(T1) + Var(e1))  =>  Var(e1)/Var(T1) = alpha/alpha' - 1
    ratio = alpha / alpha_naive - 1
    show("Var(T1)/Var(M1) = alpha'/alpha", alpha_naive / alpha, "zelf berekend")
    show("Var(e1)/Var(T1) = alpha/alpha' - 1", answer("ex-02-15", ratio), "zelf berekend")
    show("Var(e1)/Var(T1) in %", 100 * ratio, "zelf berekend")


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


def covid_simpson() -> None:
    """Shares and death rates of the COVID-19 table on Van Volsem p. 91 (S01-WE09), extra."""
    print("Simpson COVID-19 (VV p. 91, extra)")
    table = {r["Groep"]: r for r in rows("S01_simpson_s_paradox_covid_19_vaccineffectiviteit_uk_sept_2021")}

    def parse(cell: str) -> tuple[float, float]:
        """'33 op 1.536.353' -> (33, 1536353); the slide uses '.' as thousands separator."""
        deaths, people = cell.split(" op ")
        return float(deaths.replace(".", "")), float(people.replace(".", ""))

    rates = {}
    for group, printed in (("< 50 jaar", "41"), ("50+ jaar", "84"), ("Totaal (simpel)", "82")):
        dv, nv = parse(table[group]["Gevaccineerd – sterfgevallen"])
        du, nu = parse(table[group]["Niet-gevaccineerd – sterfgevallen"])
        share = 100 * dv / (dv + du)
        check(f"{group}: % sterfgevallen gevaccineerd", share, printed)
        rates[group] = (1e6 * dv / nv, 1e6 * du / nu)
        show(f"{group}: aandeel gevaccineerd in de groep (%)", 100 * nv / (nv + nu), "zelf berekend")
        show(f"{group}: sterfte per miljoen gevaccineerd", rates[group][0], "zelf berekend")
        show(f"{group}: sterfte per miljoen niet-gevaccineerd", rates[group][1], "zelf berekend")
        if group == "< 50 jaar":
            check("< 50 jaar: % sterfgevallen niet-gevaccineerd (p. 91: 59%)", 100 * du / (dv + du), "59")
    show("totaal: verhouding sterfte gevaccineerd / niet-gevaccineerd",
         rates["Totaal (simpel)"][0] / rates["Totaal (simpel)"][1], "zelf berekend")
    for group in ("< 50 jaar", "50+ jaar"):
        answer("ex-02-18", rates[group][0])
        answer("ex-02-18", rates[group][1])
    lower = all(v < u for v, u in (rates["< 50 jaar"], rates["50+ jaar"]))
    print(f"  {'OK' if lower else 'MISMATCH':<8} p. 91: 'binnen elke leeftijdsgroep beschermt het vaccin' "
          f"(sterfte gevaccineerd < niet-gevaccineerd in beide groepen: {lower})")
    # The totals of the table must be the sums of the two groups.
    for col in ("Gevaccineerd – sterfgevallen", "Niet-gevaccineerd – sterfgevallen"):
        a, b, t = (parse(table[g][col]) for g in ("< 50 jaar", "50+ jaar", "Totaal (simpel)"))
        ok = a[0] + b[0] == t[0] and a[1] + b[1] == t[1]
        print(f"  {'OK' if ok else 'MISMATCH':<8} totaal = som van de groepen ({col})")


def village_income() -> None:
    """Recompute the printed summary of the charity-village exercise from its raw data: VV p. 100 (S01-WE07)."""
    print("Dorpen Abora / Bladir / Curo (VV p. 95-100, extra)")
    raw = rows("S01_village_income_exercise_ruwe_data_per_geslacht_m_f_per_dorp")
    summary = {r["Metric"]: r for r in rows("S01_village_income_exercise_samenvattende_statistieken_per_dorp")}
    for village in ("Abora", "Bladir", "Curo"):
        data = [(r["gender"], float(r[village])) for r in raw if r[village].strip()]
        values = np.array([v for _, v in data])
        men = np.array([v for g, v in data if g == "m"])
        women = np.array([v for g, v in data if g == "f"])
        counts = {v: list(values).count(v) for v in values}
        computed = {
            "total village income": values.sum(),
            "average income": values.mean(),
            "median income": float(np.median(values)),
            "mode income": max(counts, key=counts.get),
            "max income": values.max(),
            "min income": values.min(),
            "% incomes below 50": 100 * np.mean(values < 50),
            "% incomes below 100": 100 * np.mean(values < 100),
            "average income m": men.mean(),
            "average income f": women.mean(),
        }
        show(f"{village}: aantal inwoners", float(len(values)), "zelf geteld")
        for metric, value in computed.items():
            check(f"{village}: {metric}", float(value), summary[metric][village])
        if village == "Bladir":
            answer("ex-02-16", float(values.mean()))
            answer("ex-02-16", float(np.median(values)))
            answer("ex-02-16", float(100 * np.mean(values < 50)))
        if village == "Curo":
            answer("ex-02-16", float(np.median(values)))
            answer("ex-02-16", float(women.mean()))


def holiday_percentages() -> None:
    """The five candidate conclusions about 14-to-17-year-olds: VV p. 100 (S01-WE08), extra."""
    print("Kinderen op vakantie zonder ouders (VV p. 100, extra)")
    share_2019, share_2023 = 0.43, 0.39  # p. 100: 43 % in 2019, 39 % in 2023
    pop_2019, pop_2023 = 1_092_979, 1_136_495  # p. 100: number of 14-to-17-year-olds
    kids_2019, kids_2023 = share_2019 * pop_2019, share_2023 * pop_2023
    drop = kids_2019 - kids_2023
    show("aantal 2019 = 0,43 x 1 092 979", kids_2019, "zelf berekend")
    show("aantal 2023 = 0,39 x 1 136 495", kids_2023, "zelf berekend")
    show("daling van het aantal", answer("ex-02-17", drop), "zelf berekend")
    show("daling van het aantal in % van 2019", answer("ex-02-17", 100 * drop / kids_2019), "zelf berekend")
    show("daling van het aandeel (procentpunt)", 100 * (share_2019 - share_2023), "zelf berekend")
    show("daling van het aandeel per jaar (pp/jaar, 2019-2023)", 100 * (share_2019 - share_2023) / 4,
         "zelf berekend")
    show("relatieve daling van het aandeel (%)", 100 * (share_2019 - share_2023) / share_2019, "zelf berekend")
    check("conclusie 4: 'dropped by 27 748'", drop, "27748")
    show("verschil gedrukt 27 748 - berekend", 27748 - round(drop), "zelf berekend")
    check("conclusie 5: 'dropped by 5.7 %'", 100 * drop / kids_2019, "5.7")
    check("conclusie 3: '9.3%' = relatieve daling van het aandeel", 100 * (share_2019 - share_2023) / share_2019,
          "9.3")


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
    steel_dilution()
    naert_simpson_slopes()
    covid_simpson()
    village_income()
    holiday_percentages()
    pitfall_numbers()
    choice_answers()
    return 0 if consistency() else 1


if __name__ == "__main__":
    sys.exit(main())
