"""Tests for bbtools.printed: parsing course-printed numbers and comparing at printed precision (decision 10)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from bbtools.printed import (
    agrees_at_printed_precision,
    decimals_printed,
    first_printed_number,
    parse_printed,
    resolution_exponent,
    rounding_consistent,
)


@pytest.mark.parametrize(("text", "thousands", "expected"), [
    ("2,326", False, Decimal("2.326")),     # Dutch decimal comma (slides)
    ("691,462", True, Decimal("691462")),   # thousands separator (English DPMO tables)
    (".7979", False, Decimal("0.7979")),    # leading dot, as in Table A
    ("0.00034", False, Decimal("0.00034")),
    ("-1.5", False, Decimal("-1.5")),
])
def test_parse_printed_reads_course_notations_exactly(text: str, thousands: bool, expected: Decimal) -> None:
    # act / assert
    assert parse_printed(text, thousands) == expected


def test_parse_printed_refuses_to_guess_when_both_separators_appear() -> None:
    # act / assert -- '1,234.5' only makes sense with thousands=True
    with pytest.raises(ValueError, match="ambiguous"):
        parse_printed("1,234.5")


def test_parse_printed_rejects_text_that_is_not_a_number() -> None:
    # act / assert
    with pytest.raises(ValueError, match="not a printed number"):
        parse_printed("3/sqrt(n)")


def test_first_printed_number_takes_the_leading_value_of_a_stated_answer() -> None:
    # act / assert
    assert first_printed_number("0,67 (= min[1,67 ; 0,67])") == "0,67"


@pytest.mark.parametrize(("text", "thousands", "decimals", "exponent"), [
    ("0.5642", False, 4, -4), ("3", False, 0, 0), ("690,000", True, 0, 4), ("200", False, 0, 2), ("0", False, 0, 0),
    ("1,166", False, 3, -3),
])
def test_precision_of_printed_numbers(text: str, thousands: bool, decimals: int, exponent: int) -> None:
    # act / assert
    assert decimals_printed(text, thousands) == decimals
    assert resolution_exponent(text, thousands) == exponent


@pytest.mark.parametrize(("computed", "text", "expected"), [
    (0.66666, "0,67", True),      # rounds half-up to the printed 2 decimals
    (1.1666667, "1,166", False),  # the slide truncates; 1.16667 rounds to 1,167
    (233.0, "200", True),         # printed to one significant figure
    (0.8525, "0.853", True),      # half-up, not banker's rounding
])
def test_agrees_at_printed_precision(computed: float, text: str, expected: bool) -> None:
    # act / assert
    assert agrees_at_printed_precision(computed, text) is expected


@pytest.mark.parametrize(("values", "thousands", "expected"), [
    (["0.7971", "0.797"], False, True), (["0.8525", "0.853"], False, True), (["0.7272", "0.724"], False, False),
    (["690,000", "691,462"], True, True), (["2.115", "2.114"], False, False),
])
def test_rounding_consistent(values: list[str], thousands: bool, expected: bool) -> None:
    # act / assert
    assert rounding_consistent(values, thousands) is expected
