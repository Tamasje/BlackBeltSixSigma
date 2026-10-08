"""Tests for bbtools.sheet_conditional, evaluated by LibreOffice headless.

Expected values: the course's worked exercise S02-WE01 (Data p. 24-25: 500 products of two lines, quality
Accepted / Downgraded / Rejected), typed as a cross table with its totals and as 500 raw observations, compared at
printed precision (decision 10). Independent cross-check: scipy's χ²-test of a random table.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import pytest
from scipy import stats

from bbtools.sheet_conditional import (
    ANSWERS,
    COLUMNS,
    INDEPENDENCE,
    QUESTION,
    SHEET,
    STATUS,
    TYPED_FIRST,
    TYPED_HEADER,
    first_row,
    last_row,
    raw_cells,
    table_cell,
    typed_cell,
)

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, Any]], Any]


def course_table(given: str) -> tuple[list[str], list[str], list[list[int]]]:
    """Row names, column names and counts of 'Lijn 1: Accepted=200, …; Totaal: …' (totals kept, as printed)."""
    rows = [part.split(":") for part in given.split(";")]
    columns = [cell.split("=")[0].strip() for cell in rows[0][1].split(",")]
    counts = [[int(cell.split("=")[1]) for cell in values.split(",")] for _, values in rows]
    return [name.strip() for name, _ in rows], columns, counts


def typed(names: list[str], columns: list[str], counts: list[list[int]]) -> dict[str, Any]:
    """Input cells of a typed cross table with its names."""
    cells: dict[str, Any] = {f"{COLUMNS[j]}{TYPED_HEADER}": name for j, name in enumerate(columns)}
    for i, (name, row) in enumerate(zip(names, counts, strict=True)):
        cells[f"A{TYPED_FIRST + i}"] = name
        cells |= {typed_cell(i, j): n for j, n in enumerate(row)}
    return cells


def raw(names: list[str], columns: list[str], counts: list[list[int]]) -> dict[str, Any]:
    """Input cells of the same table as raw observations, one per row (totals left out)."""
    observations = [(x, y) for x, row in zip(names, counts, strict=True) for y, n in zip(columns, row, strict=True)
                    for _ in range(n)]
    cells: dict[str, Any] = {}
    for i, (x, y) in enumerate(observations):
        cell_x, cell_y = raw_cells(i)
        cells[cell_x], cells[cell_y] = x, y
    return cells


def question(asked: tuple[str, str, str], given: tuple[str, str, str] | None) -> dict[str, Any]:
    """The dropdown cells: (variable, 'is' or 'is niet', category) of E and of G."""
    cells = dict(zip(("e_var", "e_is", "e_cat"), asked, strict=True))
    if given:
        cells |= dict(zip(("g_var", "g_is", "g_cat"), given, strict=True))
    return {QUESTION[key]: value for key, value in cells.items()}


def half_up(x: float, decimals: int) -> str:
    """x rounded half-up to the printed precision, with a decimal comma (decision 10)."""
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)).replace(".", ",")


@pytest.mark.parametrize("entry", ["typed", "raw"])
def test_production_lines_s02_we01(entry: str, oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- p. 24 table; typed with its 'Totaal' row and column (they must not count), or as raw data
    example = oracle["S02-WE01"]
    names, columns, counts = course_table(example["given"]["table"])
    data = typed(names, columns, counts) if entry == "typed" else raw(names[:-1], columns[:-1],
                                                                       [row[:-1] for row in counts[:-1]])
    cells = data | {"B10": "L", "B11": "K"} | question(("K", "is", "Accepted"), ("L", "is", "Lijn 2"))
    stated = example["stated_answers"]
    # act
    ws = evaluate(SHEET, cells)
    # assert -- p. 25: joint, marginal and conditional answers as printed, and "Niet onafhankelijk"
    assert "= " + half_up(ws[f"B{ANSWERS['p_eg']}"].value, 2) in stated["P(L=lijn2, K=Accepted)"]
    for j, key in enumerate(("P(Acc.)", "P(Down.)", "P(Rej.)")):
        assert "= " + half_up(ws[f"{COLUMNS[j]}{last_row('joint') + 1}"].value, 2) in stated[key]
    for j, key in enumerate(("P(Acc. | lijn1)", "P(Down. | lijn1)", "P(Rej. | lijn1)")):
        assert "≈ " + half_up(ws[table_cell("given_x", 0, j)].value, 2) in stated[key]
    assert stated["onafhankelijkheid"].startswith("Niet onafhankelijk")
    assert ws[INDEPENDENCE["verdict"]].value.startswith("afhankelijk")
    # the chosen question: P(K = Accepted | L = Lijn 2) = 150 / 230, and its parts
    answer = ANSWERS["conditional"]
    assert ws[f"A{answer}"].value.startswith("P(K = Accepted | L = Lijn 2)")
    assert (ws[f"C{answer}"].value, ws[f"D{answer}"].value) == (150, 230)
    assert ws[f"B{answer}"].value == pytest.approx(150 / 230, rel=1e-12)
    assert ws[f"B{ANSWERS['reverse']}"].value == pytest.approx(150 / 350, rel=1e-12)
    assert ws[f"E{ANSWERS['product']}"].value.startswith("E en G afhankelijk")
    assert ws["A54"].value == "Lijn 1" and ws[f"{COLUMNS[2]}{first_row('counts') - 1}"].value == "Rejected"
    assert ws[f"{COLUMNS[3]}{first_row('counts') - 1}"].value is None   # the 'Totaal' column is left out
    assert ws[STATUS["source"]].value == ("de getypte kruistabel" if entry == "typed"
                                          else "ruwe data (kolommen W en X): 500 waarnemingen")


def test_complement_and_nothing_given(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- P(K ≠ Rejected), nothing given: (350 + 90) / 500
    names, columns, counts = course_table(oracle["S02-WE01"]["given"]["table"])
    cells = typed(names, columns, counts) | question(("Y", "is niet", "Rejected"), None)
    # act
    ws = evaluate(SHEET, cells)
    # assert
    answer = ANSWERS["conditional"]
    assert (ws[f"C{answer}"].value, ws[f"D{answer}"].value) == (440, 500)
    assert ws[f"B{answer}"].value == pytest.approx(440 / 500, rel=1e-12)


def test_independent_table_and_chi_square_match_scipy(evaluate: Evaluate) -> None:
    # arrange -- a table with proportional rows (independent) and a random 4 × 5 table
    independent = [[10, 20, 30], [20, 40, 60]]
    rng = random.Random(4)
    table = [[rng.randint(5, 40) for _ in range(5)] for _ in range(4)]
    names = [f"r{i}" for i in range(4)]
    columns = [f"k{j}" for j in range(5)]
    expected = stats.chi2_contingency(table, correction=False)
    # act
    ws_independent = evaluate(SHEET, typed(["a", "b"], ["x", "y", "z"], independent))
    ws = evaluate(SHEET, typed(names, columns, table))
    # assert
    assert ws_independent[INDEPENDENCE["verdict"]].value.startswith("onafhankelijk")
    assert ws[INDEPENDENCE["chi2"]].value == pytest.approx(expected.statistic, rel=1e-9)
    assert ws[INDEPENDENCE["df"]].value == expected.dof
    assert ws[INDEPENDENCE["p"]].value == pytest.approx(expected.pvalue, rel=1e-7)


def test_two_by_two_yates_matches_scipy(evaluate: Evaluate) -> None:
    # arrange
    table = [[12, 30], [25, 18]]
    expected = stats.chi2_contingency(table, correction=True)
    # act
    ws = evaluate(SHEET, typed(["a", "b"], ["x", "y"], table))
    # assert
    assert ws[INDEPENDENCE["yates"]].value == pytest.approx(expected.statistic, rel=1e-9)


def test_raw_data_problems_are_reported(evaluate: Evaluate) -> None:
    # arrange -- 3 complete observations and one with only X; a typed table next to it is ignored
    cells = {"W257": "a", "X257": "x", "W258": "a", "X258": "y", "W259": "b", "X259": "x", "W260": "b",
             "B256": "x", "A257": "a", "B257": 5}
    # act
    ws = evaluate(SHEET, cells)
    # assert
    assert ws[STATUS["source"]].value == "ruwe data (kolommen W en X): 3 waarnemingen"
    assert "1 regel(s) met maar één categorie" in ws[STATUS["warning"]].value
    assert "De getypte tabel telt niet" in ws[STATUS["warning"]].value
    assert ws[f"V{last_row('counts') + 1}"].value == 3
