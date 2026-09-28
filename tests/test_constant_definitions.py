"""Tests for bbtools.constant_definitions: independent definitions of the constants versus the printed tables.

CLAUDE.md: where a transcribed constant has an independent definition, compare the two, report mismatches and
never overwrite the transcribed value. The comparison pins the full list of printed values that differ from
their definition by more than one unit of their last printed digit, so any change in a transcription fails.
"""
from __future__ import annotations

import math

import pytest
from scipy import integrate, special

from bbtools.constant_definitions import c2, c4, d2, d3, definition, differences
from bbtools.constants import load_all

# Printed values more than one unit of their last digit away from the definition: (table, symbol, n, printed).
# Found 2026-09-28; reported to the user at the sheet-1 STOP. Likely causes, not verdicts:
#   T18 (Crow/ASTM 1951): D1-D4 for n >= 11 and A0(10) — older range tables; 1/d2 computed from rounded d2.
#   TA  (Wheeler 1987):   d3(21) = 0.7272 (definition 0.7242, probably a misprint); c2(25) last digit.
#   SSD1 (Six Sigma Demystified p. 1): B6(2) = 3.267 (definition 2.606, the '2.606' printed on a stray row).
#   SSD2 (Six Sigma Demystified p. 2): 1/d2 and E2 computed from rounded d2; D1, D2 at n = 12, 19.
KNOWN_LARGER_DIFFERENCES = {
    ("T18", "A0", 10, "3.085"), ("T18", "1/d2", 2, "0.8865"), ("T18", "1/d2", 3, "0.5907"),
    ("T18", "D1", 11, "0.812"), ("T18", "D1", 13, "1.026"), ("T18", "D1", 14, "1.121"), ("T18", "D1", 15, "1.207"),
    ("T18", "D1", 16, "1.285"), ("T18", "D1", 17, "1.359"), ("T18", "D1", 18, "1.426"), ("T18", "D1", 19, "1.490"),
    ("T18", "D1", 25, "1.804"),
    ("T18", "D2", 12, "5.592"), ("T18", "D2", 13, "5.646"), ("T18", "D2", 14, "5.693"), ("T18", "D2", 15, "5.737"),
    ("T18", "D2", 16, "5.779"), ("T18", "D2", 17, "5.817"), ("T18", "D2", 18, "5.854"), ("T18", "D2", 19, "5.888"),
    ("T18", "D2", 25, "6.058"),
    ("T18", "D3", 15, "0.348"), ("T18", "D3", 17, "0.379"), ("T18", "D4", 15, "1.652"), ("T18", "D4", 17, "1.621"),
    ("TA", "c2", 25, "0.9695"), ("TA", "d3", 21, "0.7272"),
    ("SSD1", "B6", 2, "3.267"),
    ("SSD2", "1/d2", 2, "0.8865"), ("SSD2", "1/d2", 3, "0.5907"), ("SSD2", "D1", 12, "0.922"),
    ("SSD2", "D1", 19, "1.487"), ("SSD2", "D2", 19, "5.891"), ("SSD2", "E2", 2, "2.660"),
}


def test_d2_and_d3_match_their_closed_forms_for_two_values() -> None:
    # arrange -- for n = 2 the range is |X1 - X2| ~ half-normal with scale sqrt(2): E = 2/sqrt(pi), Var = 2 - 4/pi
    # act / assert -- the Simpson grids are accurate to ~1e-8; 1e-9 relative is loose enough to be stable
    assert d2(2) == pytest.approx(2 / math.sqrt(math.pi), rel=1e-9)
    assert d3(2) == pytest.approx(math.sqrt(2 - 4 / math.pi), rel=1e-9)


def test_c4_and_c2_match_their_closed_forms_for_two_values() -> None:
    # act / assert -- Gamma(1)/Gamma(1/2) = 1/sqrt(pi)
    assert c4(2) == pytest.approx(math.sqrt(2 / math.pi), rel=1e-12)
    assert c2(2) == pytest.approx(math.sqrt(1 / math.pi), rel=1e-12)


@pytest.mark.parametrize("n", [3, 10, 25, 100])
def test_d2_agrees_with_adaptive_quadrature(n: int) -> None:
    # arrange -- independent method: d2 = integral of 1 - Phi(x)^n - (1 - Phi(x))^n over the real line
    expected = integrate.quad(lambda x: 1 - special.ndtr(x) ** n - (1 - special.ndtr(x)) ** n, -12, 12,
                              limit=200, epsabs=1e-12)[0]
    # act / assert -- quad's absolute error bound is 1e-12; the grid is good to ~1e-8
    assert d2(n) == pytest.approx(expected, rel=1e-8)


def test_d3_agrees_with_adaptive_double_quadrature_for_five_values() -> None:
    # arrange -- independent method: E[R^2] = 2 * double integral over x < y of
    #            1 - Phi(y)^n - (1 - Phi(x))^n + (Phi(y) - Phi(x))^n
    n, F = 5, special.ndtr
    second = 2 * integrate.dblquad(lambda y, x: 1 - F(y) ** n - (1 - F(x)) ** n + (F(y) - F(x)) ** n,
                                   -10, 10, lambda x: x, lambda x: 10, epsabs=1e-11, epsrel=1e-11)[0]
    # act / assert
    assert d3(n) == pytest.approx(math.sqrt(second - d2(n) ** 2), rel=1e-7)


def test_a0_relation_printed_under_table_18_holds_for_the_definition() -> None:
    # arrange -- footnote of Table 18 (___4.1 tabellen SPC.pdf p. 2): 'The relation A0 = 3 sqrt(n) / d2 holds'
    # act / assert
    assert definition("A0", 4) == pytest.approx(3 * 2 / d2(4))


def test_printed_constants_match_their_definitions_except_known_differences() -> None:
    # arrange
    found = differences(load_all())
    # act
    larger = {(d.table, d.symbol, d.n, d.printed) for d in found if not d.rounding_only}
    # assert -- every other printed value is within one unit of its last digit of the definition
    assert larger == KNOWN_LARGER_DIFFERENCES
