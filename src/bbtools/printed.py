"""Printed numbers: parse values exactly as the course prints them and compare at their printed precision.

The course mixes Dutch decimal commas ('2,326' = 2.326), English thousands separators in DPMO tables
('691,462' = 691462), leading dots ('.7979') and float-exact spreadsheet values. '2,326' cannot be told apart
by syntax, so the caller says which convention applies: comma = decimal separator by default, comma =
thousands separator with `thousands=True` (DPMO and ppm counts). Decimal is used throughout because binary
floats blur the last digit, and the last digit is what a transcription check is about.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_FIRST_NUMBER = re.compile(r"-?(?:\d+[.,]?\d*|[.,]\d+)(?:[eE][-+]?\d+)?")


def parse_printed(text: str, thousands: bool = False) -> Decimal:
    """Exact value of one printed number.

    thousands=False: '2,326' -> 2.326 and '2.326' -> 2.326 (comma is a decimal separator, as on Dutch slides).
    thousands=True:  '691,462' -> 691462 (comma groups thousands, as in the English DPMO tables).
    Raises ValueError naming the text when it is not a single number or mixes both separators.
    """
    cleaned = text.strip().replace(" ", "").replace(" ", "")
    if thousands:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned and "." in cleaned:
        raise ValueError(f"ambiguous printed number (both ',' and '.'): {text!r}")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"not a printed number: {text!r}") from exc


def first_printed_number(text: str) -> str:
    """The first number in a stated answer such as '0,67 (= min[...])', returned as printed."""
    match = _FIRST_NUMBER.search(text)
    if match is None:
        raise ValueError(f"no number in stated answer {text!r}")
    return match.group(0)


def decimals_printed(text: str, thousands: bool = False) -> int:
    """Number of digits after the decimal separator as printed ('0.5642' -> 4, '3' -> 0)."""
    exponent = parse_printed(text, thousands).as_tuple().exponent
    return -exponent if isinstance(exponent, int) and exponent < 0 else 0


def resolution_exponent(text: str, thousands: bool = False) -> int:
    """Power of ten of the last printed digit: -3 for '0.797', 4 for '690,000' (thousands), 0 for '0'."""
    value = parse_printed(text, thousands)
    if value == 0:
        return 0
    exponent = value.as_tuple().exponent
    if isinstance(exponent, int) and exponent < 0:
        return exponent
    digits = str(abs(int(value)))
    return len(digits) - len(digits.rstrip("0"))


def round_half_up(value: float | int | Decimal, exponent: int) -> Decimal:
    """Round to 10**exponent the way a person rounds (half away from zero), not banker's rounding.

    Spreadsheet engines return exact results such as 35 as int, and scipy returns numpy floats whose repr
    ('np.float64(3.4)') Decimal cannot read, so every non-Decimal goes through int or float explicitly.
    """
    if isinstance(value, Decimal):
        exact = value
    elif isinstance(value, int):
        exact = Decimal(value)
    else:
        exact = Decimal(repr(float(value)))
    return exact.quantize(Decimal(1).scaleb(exponent), rounding=ROUND_HALF_UP)


def agrees_at_printed_precision(computed: float | int, printed: str, thousands: bool = False) -> bool:
    """True if `computed`, rounded half-up to the printed number's last digit, equals the printed number.

    This is convention decision 10 (inventory/conventions.md): '0,67' accepts 0.6667, '1,166' rejects 1.16667.
    """
    exponent = resolution_exponent(printed, thousands)
    target = parse_printed(printed, thousands).quantize(Decimal(1).scaleb(exponent))
    return round_half_up(computed, exponent) == target


def rounding_consistent(printed: list[str], thousands: bool = False) -> bool:
    """True if every pair of printed values agrees once rounded half-up to the coarser resolution.

    '0.7971' and '0.797' agree; '0.8525' and '0.853' agree; '0.7272' and '0.724' do not;
    with thousands=True, '690,000' and '691,462' agree (the former is printed to 2 significant figures).
    """
    for i in range(len(printed)):
        for j in range(i + 1, len(printed)):
            exponent = max(resolution_exponent(printed[i], thousands), resolution_exponent(printed[j], thousands))
            a = round_half_up(parse_printed(printed[i], thousands), exponent)
            b = round_half_up(parse_printed(printed[j], thousands), exponent)
            if a != b:
                return False
    return True
