"""Tests for bbtools.sheet_capability, evaluated by LibreOffice headless.

Expected values:
- Course worked examples from inventory/worked_examples.json (locked by tag oracle-approved), via the `printed`
  fixture, which asserts the oracle really prints each value it returns.
  * Exercise workbooks (S06-WE02, S06-WE04, S06-WE07) are Excel cached floats: compared with rel=1e-9, since
    the same formula on the same inputs differs only by float round-off.
  * Slide values (S06-WE01, S06-WE08, S06-WE12, S06-WE13) are compared at their printed precision
    (convention decision 10: half-up rounding to the last printed digit).
  * Printed values that disagree with the computation are strict xfails naming the page, never adjusted.
- An independent scipy.stats computation for random inputs.
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
from bbtools.sheet_capability import CRITERION_ROWS, INPUTS, RESULT_COLUMNS, RESULT_ROWS, SHEET

pytestmark = pytest.mark.libreoffice

Printed = Callable[[str, str, str, str], str]
Evaluate = Callable[[str, dict[str, float]], Any]


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names ('lsl', 'rbar', ...) onto the sheet's input cells."""
    return {INPUTS[name]: value for name, value in values.items()}


def result(ws: Any, row: str, column: str) -> Any:
    """Cached value of one result cell, e.g. result(ws, 'rbar_d2', 'cpk')."""
    return ws[f"{RESULT_COLUMNS[column]}{RESULT_ROWS[row]}"].value


def num(text: str) -> float:
    """A float from an oracle string such as '1.1666666666666594 (…)' or '26.5 (=662.5/25)'."""
    return float(text.split()[0].replace(",", "."))


# ---------------------------------------------------------------- exercise workbooks (Excel cached values)

@pytest.mark.parametrize(("case", "mean_key"), [("case1", "case1_mean"), ("case2", "case2_mean")])
def test_exercise_axis_workbook_s06_we02(case: str, mean_key: str, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Exercise axis - vizualisation.xlsx: shaft 71.4-72.8 mm, sigma 0.2, mean 71.8 or 72.1
    given, answers = oracle["S06-WE02"]["given"], oracle["S06-WE02"]["stated_answers"]
    inputs = {"lsl": num(given["LSL"]), "usl": num(given["USL"]), "mean": num(given[mean_key]),
              "sigma_given": num(given["sigma"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert -- Excel cached floats, rel=1e-9 (float round-off only)
    assert result(ws, "given", "cp") == pytest.approx(num(answers[f"Cp_{case}"]), rel=1e-9)
    assert result(ws, "given", "cpu") == pytest.approx(num(answers[f"Cpk_{case}_upper"]), rel=1e-9)
    assert result(ws, "given", "cpl") == pytest.approx(num(answers[f"Cpk_{case}_lower"]), rel=1e-9)
    assert result(ws, "given", "cpk") == pytest.approx(num(answers[f"Cpk_{case}_min"]), rel=1e-9)


def test_oefening_2_workbook_s06_we04(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- __Xbar R kaart ... oefening 2.xlsx: specs 16,2 +/- 0,5, sigma = Rbar/d2 as computed there
    given, answers = oracle["S06-WE04"]["given"], oracle["S06-WE04"]["stated_answers"]
    inputs = {"lsl": num(given["LSL"]), "usl": num(given["USL"]), "mean": num(given["Xbarbar"]),
              "sigma_given": num(given["sigma_estimate"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert -- Excel cached floats, rel=1e-9
    assert result(ws, "given", "cp") == pytest.approx(num(answers["Cp"]), rel=1e-9)
    assert result(ws, "given", "cpl") == pytest.approx(num(answers["CpkL_calc"]), rel=1e-9)
    assert result(ws, "given", "cpu") == pytest.approx(num(answers["CpkH_calc"]), rel=1e-9)
    assert result(ws, "given", "cpk") == pytest.approx(num(answers["Cpk"]), rel=1e-9)


@pytest.mark.parametrize(("mean_key", "cpk_key", "out_key"), [
    ("Xbarbarbar", "geval1_mean=26.5__Cpk_min", "geval1_mean=26.5__totaal_uitval"),
    (None, "geval2_mean=26.4(centered)__Cpk", "geval2_mean=26.4(centered)__totaal_uitval"),
])
def test_oefening_5_workbook_s06_we07(mean_key: str | None, cpk_key: str, out_key: str, oracle: dict[str, Any],
                                      evaluate: Evaluate) -> None:
    # arrange -- __Xbar R kaart ... oefening 5.xlsx: 25 samples of n = 5, Rbar = 9/25, specs 26,40 +/- 0,50
    given, answers = oracle["S06-WE07"]["given"], oracle["S06-WE07"]["stated_answers"]
    mean = num(answers[mean_key]) if mean_key else 26.4  # case 2: the workbook centres the mean on 26.4
    inputs = {"lsl": num(given["LSL"]), "usl": num(given["USL"]), "mean": mean,
              "rbar": num(answers["Rbar"]), "n": num(given["n"])}
    # act -- the sheet looks d2 up in Table 18
    ws = evaluate(SHEET, cells(inputs))
    # assert -- Excel cached floats, rel=1e-9
    assert result(ws, "rbar_d2", "sigma") == pytest.approx(num(answers["sigma_estimate"]), rel=1e-9)
    assert result(ws, "rbar_d2", "cp") == pytest.approx(num(answers["geval1_mean=26.5__Cp"]), rel=1e-9)
    assert result(ws, "rbar_d2", "cpk") == pytest.approx(num(answers[cpk_key]), rel=1e-9)
    assert result(ws, "rbar_d2", "out_total") == pytest.approx(num(answers[out_key]), rel=1e-9)


# ---------------------------------------------------------------- slides (printed precision, decision 10)

def test_oefening_6_slide_s06_we08(printed: Printed, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 87 (SPC oefening 6): specs 100 +/- 10, Xbarbar 104, Rbar 9,30, n 5
    given = oracle["S06-WE08"]["given"]
    inputs = {"lsl": num(given["LSL"]), "usl": num(given["USL"]), "mean": num(given["Xbarbar"]),
              "rbar": num(given["Rbar"]), "n": num(given["n"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert -- printed '20/24 = 0,83' and 'min [ 1,17 ; 0,5 ] = 0,5'
    assert agrees_at_printed_precision(result(ws, "rbar_d2", "cp"), printed("S06-WE08", "stated_answers", "Cp_as_printed", "0,83"))
    assert agrees_at_printed_precision(result(ws, "rbar_d2", "cpl"), printed("S06-WE08", "stated_answers", "Cpk_as_printed", "1,17"))
    assert agrees_at_printed_precision(result(ws, "rbar_d2", "cpk"), printed("S06-WE08", "stated_answers", "Cpk_as_printed", "0,5"))


S06_WE01_OFF_CENTRE = [  # (column, answer key, printed value, scale from fraction to the printed unit)
    ("cpk", "Cpk_offcenter", "0,67", 1),
    ("cpu", "Cpk_offcenter", "1,67", 1),
    pytest.param("cp", "Cp", "1,166", 1, marks=pytest.mark.xfail(
        reason="deck p. 46 prints Cp = 1,4/1,2 as '1,166' (truncated); 1.1667 rounds to 1,167")),
    pytest.param("out_total", "defect_offcenter_2sided", "5", 100, marks=pytest.mark.xfail(
        reason="deck p. 46 notes: '5 % totaal'; the normal distribution gives 2.275 % (the NORM.VERD check the "
               "notes name, NORM.VERD(71,4; 71,8; 0,2; waar), evaluates to 2.275 % below LSL alone)")),
    pytest.param("below_lsl", "defect_offcenter_1sided", "2,5", 100, marks=pytest.mark.xfail(
        reason="deck p. 46 notes: '2,5 % per zijde'; computed 2.275 % below LSL and 0.00003 % above USL")),
]


@pytest.mark.parametrize(("column", "key", "value", "scale"), S06_WE01_OFF_CENTRE)
def test_shaft_exercise_slide_s06_we01_off_centre(column: str, key: str, value: str, scale: int, printed: Printed,
                                                  oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 46 (+ speaker notes): shaft 71,4-72,8 mm, Xbar 71,8, sbar 0,2 used directly as sigma
    given = oracle["S06-WE01"]["given"]
    inputs = {"lsl": 71.4, "usl": 72.8, "mean": num(given["Xbar"]), "sbar": num(given["sbar"])}
    assert given["context"].count("71,4") and given["context"].count("72,8")
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert
    assert agrees_at_printed_precision(result(ws, "sbar", column) * scale, printed("S06-WE01", "stated_answers", key, value))


S06_WE01_CENTRED = [
    ("below_lsl", "defect_centered_1sided", "0,02", 100),
    ("below_lsl", "defect_centered_1sided", "200", 1_000_000),
    pytest.param("cpk", "Cpk_centered", "1,166", 1, marks=pytest.mark.xfail(
        reason="deck p. 46 notes print Cpk = 0,7/0,6 as '1,166' (truncated); 1.1667 rounds to 1,167")),
    pytest.param("out_total", "defect_centered_2sided", "0,04", 100, marks=pytest.mark.xfail(
        reason="deck p. 46 notes: '0,04 %' doubles the rounded 0,02 %; computed 2 x 0.02326 % = 0.0465 %")),
    pytest.param("out_total", "defect_centered_2sided", "400", 1_000_000, marks=pytest.mark.xfail(
        reason="deck p. 46 notes: '400 ppm' doubles the rounded 200 ppm; computed 465 ppm")),
]


@pytest.mark.parametrize(("column", "key", "value", "scale"), S06_WE01_CENTRED)
def test_shaft_exercise_slide_s06_we01_centred(column: str, key: str, value: str, scale: int, printed: Printed,
                                               oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 46 notes, second case: mean moved to 72,1 (the middle of the specification)
    printed("S06-WE01", "stated_answers", "case_centered_mean", "72,1")
    inputs = {"lsl": 71.4, "usl": 72.8, "mean": 72.1, "sbar": num(oracle["S06-WE01"]["given"]["sbar"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert
    assert agrees_at_printed_precision(result(ws, "sbar", column) * scale, printed("S06-WE01", "stated_answers", key, value))


MINITAB_ROUNDED_INPUTS = ("Minitab computed from unrounded data; the slide prints the mean to 5 decimals, which "
                          "moves the tail area in the 3rd digit (computed 8.731 % / 9.315 %)")


@pytest.mark.parametrize(("row", "column", "key", "value", "scale"), [
    ("overall", "cp", "Pp", "0,66", 1),
    ("overall", "cpk", "Ppk", "0,46", 1),
    ("given", "cp", "Potential(within)__Cp", "0,64", 1),
    ("given", "cpk", "Potential(within)__Cpk", "0,45", 1),
    pytest.param("overall", "out_total", "%_Out_of_spec", "8,74", 100,
                 marks=pytest.mark.xfail(reason=f"deck p. 50: {MINITAB_ROUNDED_INPUTS}")),
    pytest.param("given", "out_total", "Potential(within)__%_Out_of_spec_expected", "9,33", 100,
                 marks=pytest.mark.xfail(reason=f"deck p. 50: {MINITAB_ROUNDED_INPUTS}")),
])
def test_minitab_report_slide_s06_we12(row: str, column: str, key: str, value: str, scale: int, printed: Printed,
                                       oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 50: Minitab capability report; overall s -> Pp/Ppk, within s (typed as sigma given) -> Cp/Cpk
    answers = oracle["S06-WE12"]["stated_answers"]
    inputs = {"lsl": num(oracle["S06-WE12"]["given"]["LSL"]), "usl": num(oracle["S06-WE12"]["given"]["USL"]),
              "mean": num(answers["Mean"]), "s_overall": num(answers["StdDev(overall)"]),
              "sigma_given": num(answers["StdDev(within)"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert
    assert agrees_at_printed_precision(result(ws, row, column) * scale, printed("S06-WE12", "stated_answers", key, value))


def test_minitab_report_slide_s06_we13(printed: Printed, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- deck p. 83: Minitab re-run of oefening 2 with the overall standard deviation
    answers = oracle["S06-WE13"]["stated_answers"]
    inputs = {"lsl": num(oracle["S06-WE13"]["given"]["LSL"]), "usl": num(oracle["S06-WE13"]["given"]["USL"]),
              "mean": num(answers["Mean"]), "s_overall": num(answers["StdDev(overall)"])}
    # act
    ws = evaluate(SHEET, cells(inputs))
    # assert -- printed Pp 0,82, Ppk 0,72, expected 1,84 % and 18440 ppm out of spec
    stated = "stated_answers"
    assert agrees_at_printed_precision(result(ws, "overall", "cp"), printed("S06-WE13", stated, "Pp", "0,82"))
    assert agrees_at_printed_precision(result(ws, "overall", "cpk"), printed("S06-WE13", stated, "Ppk", "0,72"))
    assert agrees_at_printed_precision(result(ws, "overall", "out_total") * 100,
                                       printed("S06-WE13", stated, "%_Out_of_spec_expected", "1,84"))
    assert agrees_at_printed_precision(result(ws, "overall", "ppm_total"),
                                       printed("S06-WE13", stated, "PPM(DPMO)_expected", "18440"))


# ---------------------------------------------------------------- 6 sigma criterion (decision 2)

def test_six_sigma_criterion_long_term_matches_the_course_sigma_table(evaluate: Evaluate) -> None:
    # arrange -- deck p. 21 table: sigma capability 6 -> 3.4 defects per million opportunities
    table = CONSTANTS_DIR / "S06_voc_vs_vop_sigma_capability_defects_per_million_opportunitie.csv"
    with table.open(encoding="utf-8", newline="") as fh:
        dpmo = {row["Sigma Capability"]: row["Defects per Million Opportunities"] for row in csv.DictReader(fh)}
    # act
    ws = evaluate(SHEET, {})
    # assert
    assert agrees_at_printed_precision(ws[f"D{CRITERION_ROWS['long_term_shift']}"].value, dpmo["6"])


def test_six_sigma_criterion_short_term_is_two_per_billion(evaluate: Evaluate) -> None:
    # arrange -- deck p. 40: 'CP = 2  6 Sigma quality level – 2 defect per billion of opportunities (short term)'
    # act
    ws = evaluate(SHEET, {})
    ppm = ws[f"D{CRITERION_ROWS['short_term_centred']}"].value
    # assert -- 2 per billion = 0.002 ppm, printed to one significant figure
    assert agrees_at_printed_precision(ppm * 1000, "2")


# ---------------------------------------------------------------- independent cross-check and edge cases

@pytest.mark.parametrize("seed", [1, 2, 3])
def test_every_row_matches_scipy_for_random_inputs(seed: int, evaluate: Evaluate) -> None:
    # arrange -- six different sigmas at once, one per result row
    rng = random.Random(seed)
    lsl = rng.uniform(-50, 50)
    usl = lsl + rng.uniform(1, 40)
    mean = rng.uniform(lsl - 5, usl + 5)
    n = rng.choice([2, 3, 4, 5, 6, 8, 10, 15, 20, 25])
    raw = {"sigma_given": rng.uniform(0.1, 10), "rbar": rng.uniform(0.1, 10), "sbar": rng.uniform(0.1, 10),
           "mrbar": rng.uniform(0.1, 10), "s_overall": rng.uniform(0.1, 10)}
    ws = evaluate(SHEET, cells({"lsl": lsl, "usl": usl, "mean": mean, "n": n, **raw}))
    # act / assert -- sigma per row uses the sheet's own looked-up constant (column Q), checked in test_constants
    for row in RESULT_ROWS:
        sigma = result(ws, row, "sigma")
        expected_below = stats.norm.cdf(lsl, loc=mean, scale=sigma)
        expected_above = stats.norm.sf(usl, loc=mean, scale=sigma)
        # same formula on the same inputs; rel=1e-9 covers LibreOffice's normal cdf vs scipy's
        assert result(ws, row, "cp") == pytest.approx((usl - lsl) / (6 * sigma), rel=1e-9)
        assert result(ws, row, "cpk") == pytest.approx(min(usl - mean, mean - lsl) / (3 * sigma), rel=1e-9)
        assert result(ws, row, "below_lsl") == pytest.approx(expected_below, rel=1e-9, abs=1e-300)
        assert result(ws, row, "above_usl") == pytest.approx(expected_above, rel=1e-9, abs=1e-300)
        assert result(ws, row, "out_total") == pytest.approx(expected_below + expected_above, rel=1e-9, abs=1e-300)


def test_sigma_rows_use_the_constants_from_the_tables_sheet(evaluate: Evaluate) -> None:
    # arrange -- n = 5: d2 2.326 (Table 18), c4 .9400 (Table A); MR uses d2 for n = 2, 1.128
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 10, "mean": 5, "rbar": 2.326, "sbar": 0.94, "n": 5, "mrbar": 1.128}))
    # act / assert
    assert result(ws, "rbar_d2", "sigma") == pytest.approx(1.0)
    assert result(ws, "sbar_c4", "sigma") == pytest.approx(1.0)
    assert result(ws, "mrbar", "sigma") == pytest.approx(1.0)


def test_one_sided_specification_gives_only_the_one_sided_indices(evaluate: Evaluate) -> None:
    # arrange -- no LSL
    ws = evaluate(SHEET, cells({"usl": 10, "mean": 4, "sigma_given": 2}))
    # act / assert -- Cp needs both limits; Cpk falls back to Cpu; only the upper tail counts
    assert result(ws, "given", "cp") is None
    assert result(ws, "given", "cpk") == pytest.approx(1.0)
    assert result(ws, "given", "below_lsl") is None
    assert result(ws, "given", "out_total") == pytest.approx(stats.norm.sf(3), rel=1e-9)


def test_rows_stay_empty_until_their_input_is_filled(evaluate: Evaluate) -> None:
    # arrange -- only the given sigma is filled
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 6, "mean": 3, "sigma_given": 1}))
    # act / assert
    assert result(ws, "given", "cp") == pytest.approx(1.0)
    for row in ("rbar_d2", "sbar", "sbar_c4", "mrbar", "overall"):
        assert result(ws, row, "sigma") is None and result(ws, row, "cp") is None


def test_reversed_limits_blank_the_results_and_show_a_warning(evaluate: Evaluate) -> None:
    # arrange -- LSL above USL
    ws = evaluate(SHEET, cells({"lsl": 1460, "usl": 1400, "mean": 1440, "sigma_given": 10}))
    # act / assert
    assert ws["A12"].value == "Check: USL must be above LSL"
    assert result(ws, "given", "sigma") is None and result(ws, "given", "out_total") is None


def test_subgroup_size_outside_table_18_is_reported_not_computed(evaluate: Evaluate) -> None:
    # arrange -- Table 18 stops at n = 25
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 6, "mean": 3, "rbar": 4, "n": 30}))
    # act / assert
    assert ws[f"Q{RESULT_ROWS['rbar_d2']}"].value == "n not in Table 18"
    assert result(ws, "rbar_d2", "sigma") is None


@pytest.mark.parametrize(("cp_sigma", "level"), [
    (1.2, "not capable"), (1.0, "just capable"), (0.75, "acceptable"), (0.59, "good"), (0.5, "6 Sigma quality level"),
])
def test_cp_level_follows_deck_page_39(cp_sigma: float, level: str, evaluate: Evaluate) -> None:
    # arrange -- spec width 6, so Cp = 1/sigma: 0.83, 1.0, 1.33, 1.69, 2.0
    ws = evaluate(SHEET, cells({"lsl": 0, "usl": 6, "mean": 3, "sigma_given": cp_sigma}))
    # act / assert
    assert result(ws, "given", "cp_level") == level
