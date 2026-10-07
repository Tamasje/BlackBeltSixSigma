"""Tests for bbtools.sheet_sigma, evaluated by LibreOffice headless.

Expected values: course worked examples (inventory/worked_examples.json, locked) at printed precision
(decision 10) via the `printed` fixture; the course sigma tables (deck p. 21, Dummies Tables 1-2 and 6-3,
Van Volsem p. 7, Harry & Schroeder) against the 1.5σ-shift definition; scipy for random inputs. Printed values
that disagree with the computation are strict xfails naming the page. The book-only blocks that moved to the
Extra sheet (DPU, yields, RTY) are tested in test_sheet_extra.py.
"""
from __future__ import annotations

import csv
import random
from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools.constants import CONSTANTS_DIR
from bbtools.printed import agrees_at_printed_precision, first_printed_number
from bbtools.sheet_sigma import INPUTS, RESULTS, SHEET

Evaluate = Callable[[str, dict[str, float]], Any]
Printed = Callable[[str, str, str, str], str]
libreoffice = pytest.mark.libreoffice


def cells(values: dict[str, float]) -> dict[str, float]:
    """Map input names onto the sheet's input cells."""
    return {INPUTS[name]: v for name, v in values.items()}


def value(ws: Any, name: str) -> Any:
    """Cached value of a named result cell."""
    return ws[RESULTS[name]].value


# ---------------------------------------------------------------- the course tables use the shifted reading

def shifted_dpmo(z: float) -> float:
    """Long-term DPMO for a short-term sigma level z: one tail beyond z - 1.5 (Dummies p. 159-160)."""
    return 1e6 * stats.norm.sf(z - 1.5)


def table_rows(stem: str, z_column: str, dpmo_column: str) -> list[tuple[str, str]]:
    """(sigma level, printed DPMO) pairs of one transcribed course table."""
    with (CONSTANTS_DIR / f"{stem}.csv").open(encoding="utf-8", newline="") as fh:
        return [(row[z_column], first_printed_number(row[dpmo_column])) for row in csv.DictReader(fh)]


TRUNCATED = "prints 308,537 for 308,537.5, which rounds to 308,538 (Dummies prints 308,538)"
SIGMA_TABLES = [
    ("S08_table_6_3_sigma_score_table_z_dpmo", "Z", "DPMO", ()),                                  # Dummies p. 160
    ("S07_table_1_2_the_sigma_scale", "Sigma", "Defects per Million", ()),                         # Dummies p. 41
    ("S06_voc_vs_vop_sigma_capability_defects_per_million_opportunitie", "Sigma Capability",
     "Defects per Million Opportunities", ("2",)),                                                 # deck p. 21
    ("S01_sigma_level_defects_per_million_yield_tabel", "Sigma Level", "Defects per Million", ("2",)),  # Van Volsem p. 7
    ("S09_the_cost_of_quality_sigma_level_vs_dpmo_vs_cost_of_quality", "Sigma Level",
     "Defects Per Million Opportunities", ("2",)),                                                 # Harry summary p. 2
    ("S09_cost_of_quality_sigma_level_vs_defects_million_vs_cost_of_qu", "sigma-level", "defects/million", ("2",)),
]


def sigma_table_cases() -> list[Any]:
    """One pytest param per printed table row; known truncations are strict xfails."""
    cases = []
    for stem, z_column, dpmo_column, truncated in SIGMA_TABLES:
        for z, dpmo in table_rows(stem, z_column, dpmo_column):
            marks = [pytest.mark.xfail(reason=f"{stem} {TRUNCATED}; Van Volsem's '308,000' is 309,000 to thousands")] \
                if z in truncated else []
            cases.append(pytest.param(z, dpmo, marks=marks, id=f"{stem[:12]}-{z}"))
    return cases


@pytest.mark.parametrize(("z", "dpmo"), sigma_table_cases())
def test_course_sigma_tables_pair_short_term_z_with_long_term_dpmo(z: str, dpmo: str) -> None:
    # act / assert -- DPMO printed with English thousands separators
    assert agrees_at_printed_precision(shifted_dpmo(float(z)), dpmo, thousands=True)


# ---------------------------------------------------------------- the sheet (LibreOffice)

@libreoffice
@pytest.mark.parametrize(("example_id", "given", "result_name", "key", "printed_value", "scale"), [
    ("S08-WE05", {"defects": 158, "units": 1, "opportunities": 14550}, "dpo", "DPO", "0.011", 1),
    ("S08-WE06", {"defects": 2, "units": 1, "opportunities": 173}, "dpo", "DPO", "0.012", 1),
    ("S08-WE07", {"defects": 2, "units": 1, "opportunities": 6_000_000}, "dpo", "DPO", "0.000000333", 1),
    ("S09-WE03", {"defects": 5, "units": 100, "opportunities": 20}, "dpo", "Defects/opportunity", "0.0025", 1),
    ("S09-WE03", {"defects": 5, "units": 100, "opportunities": 20}, "sigma_shifted", "Defects-per-million-opportunities",
     "4.3", 1),
])
def test_defect_rate_examples(example_id: str, given: dict[str, float], result_name: str, key: str,
                              printed_value: str, scale: int, printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 153-154 and Harry & Schroeder p. 5 (the sigma level comes from the section-1 DPMO)
    ws = evaluate(SHEET, cells(given))
    # act / assert
    assert agrees_at_printed_precision(value(ws, result_name) * scale,
                                       printed(example_id, "stated_answers", key, printed_value))


@libreoffice
def test_dpmo_2500_is_printed_as_2500_s09_we03(printed: Printed, evaluate: Evaluate) -> None:
    # arrange -- Harry & Schroeder p. 5
    ws = evaluate(SHEET, cells({"defects": 5, "units": 100, "opportunities": 20}))
    # act / assert
    assert agrees_at_printed_precision(value(ws, "dpmo_1"),
                                       printed("S09-WE03", "stated_answers", "Defects-per-million-opportunities", "2,500"),
                                       thousands=True)


@libreoffice
def test_sigma_level_for_20000_dpmo_s08_we08(printed: Printed, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- Dummies p. 161: 20,000 DPMO lies between Z 3.5 and 4.0 in Table 6-3 -> 'about 3.6'
    ws = evaluate(SHEET, cells({"dpmo": oracle["S08-WE08"]["given"]["DPMO"]}))
    # act / assert -- the table's (shifted) reading
    assert agrees_at_printed_precision(value(ws, "sigma_shifted"), printed("S08-WE08", "stated_answers", "approximate_Z", "3.6"))


@libreoffice
@pytest.mark.parametrize(("z", "stem", "z_column", "dpmo_column"), [
    ("2.0", "S08_table_6_3_sigma_score_table_z_dpmo", "Z", "DPMO"),
    ("4.5", "S08_table_6_3_sigma_score_table_z_dpmo", "Z", "DPMO"),
    ("6", "S01_sigma_level_defects_per_million_yield_tabel", "Sigma Level", "Defects per Million"),
])
def test_sheet_gives_the_course_table_dpmo_for_a_sigma_level(z: str, stem: str, z_column: str, dpmo_column: str,
                                                             evaluate: Evaluate) -> None:
    # arrange
    printed_dpmo = dict(table_rows(stem, z_column, dpmo_column))[z]
    # act
    ws = evaluate(SHEET, cells({"sigma_level": float(z)}))
    # assert
    assert agrees_at_printed_precision(value(ws, "dpmo_shifted"), printed_dpmo, thousands=True)


@libreoffice
def test_van_volsem_yield_for_five_sigma(evaluate: Evaluate) -> None:
    # arrange -- Van Volsem p. 7: 5 sigma -> yield 99.977 %
    with (CONSTANTS_DIR / "S01_sigma_level_defects_per_million_yield_tabel.csv").open(encoding="utf-8") as fh:
        printed_yield = {row["Sigma Level"]: row["Yield"] for row in csv.DictReader(fh)}["5"].rstrip("%")
    # act
    ws = evaluate(SHEET, cells({"sigma_level": 5}))
    # assert
    assert agrees_at_printed_precision(value(ws, "yield_shifted") * 100, printed_yield)


@libreoffice
@pytest.mark.parametrize("seed", [1, 2])
def test_every_block_matches_an_independent_computation(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    d, n, o = rng.randint(1, 50), rng.randint(50, 500), rng.randint(1, 30)
    z = rng.uniform(1, 6)
    ws = evaluate(SHEET, cells({"defects": d, "units": n, "opportunities": o, "sigma_level": z}))
    dpo = d / (n * o)
    # act / assert -- rel=1e-9: same arithmetic, LibreOffice vs scipy normal functions
    expected = {
        "dpo": dpo, "dpmo_1": dpo * 1e6, "yield_per_opportunity": 1 - dpo,
        "dpmo_used": dpo * 1e6, "z_no_shift": stats.norm.isf(dpo), "sigma_shifted": stats.norm.isf(dpo) + 1.5,
        "dpmo_shifted": shifted_dpmo(z), "dpmo_one_tail": 1e6 * stats.norm.sf(z), "dpmo_two_tails": 2e6 * stats.norm.sf(z),
    }
    for name, target in expected.items():
        assert value(ws, name) == pytest.approx(target, rel=1e-9), name
