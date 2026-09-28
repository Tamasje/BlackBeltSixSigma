"""Tests for bbtools.constants: the transcribed tables load unchanged, with provenance, as the course prints them.

Oracle values come from inventory/worked_examples.json (locked). Table contents come from
inventory/constants/*.csv, written by merge_inventory.py from the extractor output; both scanned tables
(___4.1 tabellen SPC.pdf) were transcribed a second time by hand with 0 differences (PROGRESS.md).
"""
from __future__ import annotations

from collections.abc import Callable

import pytest

from bbtools.constants import TABLE_SOURCES, USED_TABLE, load_all


def test_load_all_returns_every_table_with_its_source_page() -> None:
    # act
    tables = {t.source.key: t for t in load_all()}
    # assert -- provenance as recorded by the extractors
    assert set(tables) == {s.key for s in TABLE_SOURCES}
    assert (tables["T18"].source_file, tables["T18"].source_page) == ("source/course/Les 4/___4.1 tabellen SPC.pdf", 2)
    assert (tables["TA"].source_file, tables["TA"].source_page) == ("source/course/Les 4/___4.1 tabellen SPC.pdf", 1)
    assert tables["DUM"].source_page == 250


def test_values_keep_their_printed_form() -> None:
    # arrange
    tables = {t.source.key: t for t in load_all()}
    # act / assert -- strings, not floats: leading dot and trailing zeros survive
    assert tables["T18"].value("d2", 5) == "2.326"
    assert tables["TA"].value("c4", 2) == ".7979"
    assert tables["T18"].value("c2", 25) == "0.9696"
    assert tables["TA"].value("c2", 25) == "0.9695"
    assert tables["T18"].value("A2", 30) is None


def test_six_sigma_demystified_stray_row_is_kept_as_printed() -> None:
    # arrange -- Control charts - constants.pdf p. 1 prints '0 | 2.606' right after n = 2
    ssd1 = next(t for t in load_all() if t.source.key == "SSD1")
    # act
    stray = [row for row in ssd1.rows if row[0] == "0"]
    # assert
    assert stray == [("0", "2.606", "", "", "", "", "", "", "", "")]


def test_every_used_symbol_exists_in_the_table_it_is_taken_from() -> None:
    # arrange
    tables = {t.source.key: t for t in load_all()}
    # act
    missing = [(symbol, key) for symbol, key in USED_TABLE.items() if symbol not in tables[key].symbol_columns()]
    # assert
    assert missing == []


@pytest.mark.parametrize(("example_id", "key", "value", "symbol", "n"), [
    ("S06-WE07", "d2", "2.326", "d2", 5),                        # oefening 5 workbook: sigma = Rbar / 2.326
])
def test_table_18_matches_the_constant_the_lecturer_uses(example_id: str, key: str, value: str, symbol: str, n: int,
                                                         printed: Callable[[str, str, str, str], str]) -> None:
    # arrange
    t18 = next(t for t in load_all() if t.source.key == "T18")
    # act / assert -- the exercise workbook's constant equals Table 18, as decision 4 relies on
    assert t18.value(symbol, n) == printed(example_id, "given", key, value)
