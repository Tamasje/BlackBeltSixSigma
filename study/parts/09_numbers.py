"""Numbers for study/parts/09_procescapabiliteit.html (Deel 09: procescapabiliteit).

Prints every value the fragment marks "zelf berekend", every exercise answer (data-answer) and re-checks every
printed course value the fragment quotes. Course data: the capability exercise of SPC p. 46 (slide text and speaker
notes) and its workbook "Exercise axis - vizualisation.xlsx" (read-only, openpyxl); the Cp levels of SPC p. 40; the
technical definition of SPC p. 37; the hidden Minitab example of SPC p. 50-51; Table A of ___4.1 tabellen SPC.pdf
p. 1 (inventory/constants). Page numbers are PDF page numbers (Les 4 deck: PDF page = pptx slide number).

Each re-check has an expected status: "OK" (agrees after rounding to the printed precision) or "MISMATCH" (a known
printed error, explained in the guide text). The script exits 1 if any check does not have its expected status.
Run from the project root:  python3 study/parts/09_numbers.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = ROOT / "inventory" / "constants"
LES4 = ROOT / "source" / "course" / "Les 4"
PHI = stats.norm.cdf
PHI_INV = stats.norm.ppf
FAILURES: list[str] = []


def rows(stem: str) -> list[dict[str, str]]:
    """Rows of a course table in inventory/constants."""
    with (CONSTANTS / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def show(label: str, value: float | str, note: str = "") -> None:
    """Print one computed value."""
    text = f"{value:.6g}" if isinstance(value, float) else str(value)
    print(f"  {label:<62} {text:>16}  {note}")


def check(label: str, printed: float, computed: float, decimals: int, expected: str = "OK", note: str = "") -> None:
    """Compare a printed course value with a computation rounded to the printed number of decimals."""
    status = "OK" if round(computed, decimals) == round(printed, decimals) else "MISMATCH"
    if status != expected:
        FAILURES.append(f"{label}: expected {expected}, got {status}")
    flag = "" if status == expected else "   <-- UNEXPECTED"
    print(f"  {status:<8} {label:<56} printed {printed:>12g}  computed {computed:.8g}  {note}{flag}")


def section(title: str) -> None:
    """Print a section header."""
    print(f"\n== {title}")


def capability(lsl: float, usl: float, mean: float, sigma: float) -> dict[str, float]:
    """Cp, CPL, CPU, Cpk (SPC p. 34-35) and the normal tail fractions below LSL and above USL."""
    return {
        "Cp": (usl - lsl) / (6 * sigma),
        "CPL": (mean - lsl) / (3 * sigma),
        "CPU": (usl - mean) / (3 * sigma),
        "Cpk": min(mean - lsl, usl - mean) / (3 * sigma),
        "zL": (mean - lsl) / sigma,
        "zU": (usl - mean) / sigma,
        "pL": PHI(-(mean - lsl) / sigma),
        "pU": PHI(-(usl - mean) / sigma),
    }


def axis_exercise() -> None:
    """SPC p. 46 (slide + notes) and Exercise axis - vizualisation.xlsx: LSL 71,4, USL 72,8, mean 71,8, s-bar 0,2."""
    section("Oefening as (SPC p. 46): s-bar = 0,2 rechtstreeks als sigma, zoals de cursus")
    lsl, usl, sbar = 71.4, 72.8, 0.2
    off = capability(lsl, usl, 71.8, sbar)
    for key in ("Cp", "CPL", "CPU", "Cpk", "zL", "zU"):
        show(f"gemiddelde 71,8: {key}", off[key], "zelf berekend")
    show("% onder LSL", 100 * off["pL"], "zelf berekend")
    show("ppm boven USL", 1e6 * off["pU"], "zelf berekend")
    show("ex-09-8a: Cp", off["Cp"], "data-answer 1.1667")
    show("ex-09-8b: Cpk", off["Cpk"], "data-answer 0.667")
    show("ex-09-8d: % totaal buiten specificatie", 100 * (off["pL"] + off["pU"]), "data-answer 2.28")
    show("ppm totaal", 1e6 * (off["pL"] + off["pU"]), "zelf berekend")
    check("notes p. 46: Cp '1,166'", 1.166, off["Cp"], 3, "MISMATCH", "(1,4/1,2 = 1,1667)")
    check("notes p. 46: Cpk 0,67", 0.67, off["Cpk"], 2)
    check("notes p. 46: CPU 1,67", 1.67, off["CPU"], 2)
    check("notes p. 46: '5 % uitval' (totaal)", 5.0, 100 * (off["pL"] + off["pU"]), 0, "MISMATCH")
    check("notes p. 46: '2,5 %' (1 zijdig)", 2.5, 100 * off["pL"], 1, "MISMATCH")
    check("notes p. 46: '50.000 ppm'", 50000, 1e6 * (off["pL"] + off["pU"]), -3, "MISMATCH")
    check("xlsx P26: andere kant 5 sigma, '0,29 ppm'", 0.29, 1e6 * off["pU"], 2)
    show("Z-tabel: P(Z < -2,00) = .0228 -> %", 2.28, "tabel")

    section("Gecentreerd: gemiddelde 72,1")
    mid = (lsl + usl) / 2
    cen = capability(lsl, usl, mid, sbar)
    show("ex-09-8e: midden van de tolerantie", mid, "data-answer 72.1")
    for key in ("Cp", "Cpk", "zL"):
        show(f"gecentreerd: {key}", cen[key], "zelf berekend")
    show("ex-09-8f: Cpk gecentreerd", cen["Cpk"], "data-answer 1.1667")
    show("% per zijde", 100 * cen["pL"], "zelf berekend")
    show("ppm per zijde", 1e6 * cen["pL"], "zelf berekend")
    show("% totaal (2 zijden)", 100 * 2 * cen["pL"], "zelf berekend; data-answer ex-09-8g 0.0465")
    show("ppm totaal (2 zijden)", 1e6 * 2 * cen["pL"], "zelf berekend; data-answer ex-09-8h 465")
    check("notes p. 46: gecentreerd Cpk '1,166'", 1.166, cen["Cpk"], 3, "MISMATCH")
    check("notes p. 46: 3,5 sigma eenzijdig", 3.5, cen["zL"], 1)
    check("notes p. 46: '0,02 %' 1 zijdig", 0.02, 100 * cen["pL"], 2)
    check("notes p. 46: '200 ppm' 1 zijdig", 200, 1e6 * cen["pL"], 0, "MISMATCH")
    check("notes p. 46: '0,04 %' 2 zijdig", 0.04, 100 * 2 * cen["pL"], 2, "MISMATCH")
    check("notes p. 46: '400 ppm' 2 zijdig", 400, 1e6 * 2 * cen["pL"], 0, "MISMATCH")

    section("Exercise axis - vizualisation.xlsx: cached waarden")
    wb = openpyxl.load_workbook(LES4 / "Exercise axis - vizualisation.xlsx", data_only=True, read_only=True)
    ws = wb["Blad1"]
    cached = {name: float(ws[cell].value) for name, cell in
              (("Cp", "Q15"), ("CPU", "Q16"), ("CPL", "R16"), ("Cpk", "S16"), ("Cpk_c", "S19"),
               ("density_peak", "B12"))}
    wb.close()
    check("Q15 Cp", cached["Cp"], off["Cp"], 9)
    check("Q16 CPU", cached["CPU"], off["CPU"], 9)
    check("R16 CPL", cached["CPL"], off["CPL"], 9)
    check("S19 Cpk gecentreerd", cached["Cpk_c"], cen["Cpk"], 9)
    check("B12 NORMDIST(71,8;71,8;0,2;ONWAAR) piekhoogte", cached["density_peak"],
          stats.norm.pdf(71.8, 71.8, 0.2), 9)

    section("Zelfde oefening met sigma = s-bar / c4 (Table A, n = 5)")
    c4 = next(float(r["c4"]) for r in rows("S06_table_a_bias_correction_factors_for_estimating_standard_devi")
              if r["Subgroup Size"].strip() == "5")
    sigma_c4 = sbar / c4
    alt = capability(lsl, usl, 71.8, sigma_c4)
    show("c4 (n = 5), Tabellen SPC p. 1", c4, "")
    show("ex-09-9a: sigma = 0,2 / c4", sigma_c4, "data-answer 0.2128")
    show("ex-09-9b: Cp", alt["Cp"], "data-answer 1.097")
    show("ex-09-9c: Cpk", alt["Cpk"], "data-answer 0.627")
    show("ex-09-9d: % onder LSL", 100 * alt["pL"], "data-answer 3.01")
    show("z onder met s-bar/c4", alt["zL"], "zelf berekend")
    show("sigma-verhouding 1/c4", 1 / c4, "zelf berekend")
    table18 = {r["Sample size n"].strip(): r["d2"] for r in rows("S06_table_18_factors_for_computing_control_chart_lines")}
    table_a = {r["Subgroup Size"].strip(): r["d2"] for r in rows("S06_table_a_bias_correction_factors_for_estimating_standard_devi")}
    same = all(float(table18[k]) == float(table_a[k]) for k in map(str, range(2, 11)))
    show("d2 n = 2..10 gelijk in Table 18 en Table A", str(same), "")
    if not same:
        FAILURES.append("d2 Table 18 vs Table A differ for n = 2..10")


def cp_levels() -> None:
    """SPC p. 40: centred process, spec width 6, 8, 10 and 12 sigma."""
    section("Cp-niveaus gecentreerd (SPC p. 40)")
    for cp in (1.0, 4 / 3, 5 / 3, 2.0):
        z = 3 * cp
        out = 2 * PHI(-z)
        show(f"Cp = {cp:.4g}: +-{z:g} sigma, % binnen / ppm buiten", f"{100 * (1 - out):.7f} / {1e6 * out:.4g}",
             "zelf berekend")
    show("een staart z = 3 / z = 4", f"{PHI(-3):.5f} / {PHI(-4):.7f}", "zelf berekend")
    show("Z-tabel P(Z < -1,88)", 0.0301, "tabel; exact " + f"{PHI(-1.88):.4f}")
    check("p. 40: Cp=1 '2700' per 10^6", 2700, 1e6 * 2 * PHI(-3), -2)
    check("p. 40: Cp=1 '99.73%'", 99.73, 100 * (1 - 2 * PHI(-3)), 2)
    check("p. 40: Cp=1,33 '~60' per 10^6", 60, 1e6 * 2 * PHI(-4), -1)
    check("p. 40: Cp=1,33 '64ppm'", 64, 1e6 * 2 * PHI(-4), 0, "MISMATCH")
    check("p. 40: Cp=1,33 '99.9936%'", 99.9936, 100 * (1 - 2 * PHI(-4)), 4, "MISMATCH")
    check("p. 40: Cp=1,67 '0,57' per 10^6", 0.57, 1e6 * 2 * PHI(-5), 2)
    check("p. 40: Cp=1,67 '99.999943%'", 99.999943, 100 * (1 - 2 * PHI(-5)), 6)
    check("p. 40: Cp=2 '2 per billion'", 2, 1e9 * 2 * PHI(-6), 0)
    show("ex-09-3a: ppm buiten bij Cp = 1", 1e6 * 2 * PHI(-3), "data-answer 2700")
    show("ex-09-3b: ppm buiten bij Cp = 4/3 (+-4 sigma)", 1e6 * 2 * PHI(-4), "data-answer 63.3")
    show("ex-09-3c: ppm buiten bij Cp = 5/3 (+-5 sigma)", 1e6 * 2 * PHI(-5), "data-answer 0.573")
    show("ex-09-3d: ppm buiten bij Cp = 2 (+-6 sigma)", 1e6 * 2 * PHI(-6), "data-answer 0.00197")
    show("Cp = 1,33 exact (z = 3,99): ppm", 1e6 * 2 * PHI(-3.99), "zelf berekend")


def six_sigma_definition() -> None:
    """SPC p. 37 (Cp = 2, Cpk = 1,5 after a 1,5 sigma shift: 3,4 DPMO) and p. 40 (Cp = 2: 2 per billion)."""
    section("Technische definitie Six Sigma (SPC p. 37) en de twee lezingen (beslissing 2)")
    cp, shift = 2.0, 1.5
    cpk = (3 * cp - shift) / 3
    show("Cpk na 1,5 sigma verschuiving", cpk, "zelf berekend")
    near = 1e6 * PHI(-(3 * cp - shift))
    far = 1e6 * PHI(-(3 * cp + shift))
    check("p. 37: Cpk = 1,5", 1.5, cpk, 1)
    check("p. 37: '3.4 DPMO' (dichtste grens, z = 4,5)", 3.4, near, 1)
    show("verre grens (z = 7,5), ppm", far, "zelf berekend")
    show("ex-09-4a: ppm bij Cp 2 en Cpk 1,5", near, "data-answer 3.4")
    show("ex-09-4b: ppm bij Cp = Cpk = 2 (beide zijden)", 1e6 * 2 * PHI(-6), "data-answer 0.002")
    show("3,4 ppm in %", near / 1e4, "zelf berekend")
    show("0,002 ppm in %", 2 * PHI(-6) * 100, "zelf berekend")
    show("verhouding 3,4 ppm / 0,002 ppm", near / (1e6 * 2 * PHI(-6)), "zelf berekend")


def minitab_example() -> None:
    """Hidden slides SPC p. 50-51: LSL 0,145, USL 0,155, mean 0,14852, s overall 0,0025303, s within 0,0025891."""
    section("Minitab-voorbeeld (SPC p. 50-51, verborgen)")
    lsl, usl, mean = 0.145, 0.155, 0.14852
    overall = capability(lsl, usl, mean, 0.0025303)
    within = capability(lsl, usl, mean, 0.0025891)
    pp, ppk = overall["Cp"], overall["Cpk"]
    show("ex-09-10a: Pp", pp, "data-answer 0.66")
    show("ex-09-10b: Ppk", ppk, "data-answer 0.46")
    show("ex-09-10c: Cp (within)", within["Cp"], "data-answer 0.64")
    show("ex-09-10d: Cpk (within)", within["Cpk"], "data-answer 0.45")
    out_o = 100 * (overall["pL"] + overall["pU"])
    out_w = 100 * (within["pL"] + within["pU"])
    show("ex-09-10e: % buiten spec (overall)", out_o, "data-answer 8.73")
    show("  waarvan onder LSL / boven USL (%)", f"{100 * overall['pL']:.3f} / {100 * overall['pU']:.3f}",
         "zelf berekend")
    show("% buiten spec (within)", out_w, "zelf berekend")
    check("p. 51: Pp 0,66", 0.66, pp, 2)
    check("p. 51: Ppk 0,46", 0.46, ppk, 2)
    check("p. 51: Cp 0,64", 0.64, within["Cp"], 2)
    check("p. 51: Cpk 0,45", 0.45, within["Cpk"], 2)
    check("p. 51: % out of spec (expected) overall 8,74", 8.74, out_o, 2, "MISMATCH", "(afgerond gemiddelde)")
    check("p. 51: % out of spec (expected) within 9,33", 9.33, out_w, 2, "MISMATCH", "(afgerond gemiddelde)")
    check("p. 51: PPM (expected) overall 87445", 87445, 1e4 * out_o, 0, "MISMATCH")
    check("p. 51: PPM (expected) within 93282", 93282, 1e4 * out_w, 0, "MISMATCH")
    check("p. 51: Z.Bench overall 1,36 = -z(8,74 %)", 1.36, -PHI_INV(0.0874), 2)
    check("p. 51: Z.Bench within 1,32 = -z(9,33 %)", 1.32, -PHI_INV(0.0933), 2)
    check("p. 51: observed 8,89 % = 16/180", 8.89, 100 * 16 / 180, 2)
    check("p. 51: observed PPM 88889 = 16/180", 88889, 1e6 * 16 / 180, 0)
    show("aantal waarnemingen buiten spec = 8,89 % van 180", 0.0889 * 180, "zelf berekend")
    show("Z(LSL) overall = (mean - LSL)/s", overall["zL"], "zelf berekend")
    show("Z(USL) overall = (USL - mean)/s", overall["zU"], "zelf berekend")
    show("3 sigma overall", 3 * 0.0025303, "zelf berekend")


def main() -> int:
    """Run every block; exit 1 if a check did not have its expected status."""
    axis_exercise()
    cp_levels()
    six_sigma_definition()
    minitab_example()
    print()
    if FAILURES:
        print("FAILED:", *FAILURES, sep="\n  ")
        return 1
    print("All checks have their expected status (MISMATCH lines are printed errors the guide text explains).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
