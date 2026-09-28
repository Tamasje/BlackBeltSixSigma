"""Independent mathematical definitions of the control-chart constants, used only to check transcriptions.

The workbook never uses these numbers: calculators take every constant from the course's printed tables.
This module recomputes each constant from its definition so tests and build/README.md can report where a
printed value differs from it (CLAUDE.md: report mismatches, never overwrite the transcribed value).

Definitions, for subgroup size n of a standard normal variable (Φ = cdf, W = cdf of the range R):
  W(r) = n ∫ φ(x) [Φ(x + r) − Φ(x)]^(n−1) dx
  d2 = E[R] = ∫₀^∞ (1 − W(r)) dr ;  d3² = Var R = 2 ∫₀^∞ r (1 − W(r)) dr − d2²
  c4 = √(2/(n−1)) Γ(n/2)/Γ((n−1)/2) ;  c2 = √(2/n) Γ(n/2)/Γ((n−1)/2)
Factors built from them are listed in `definition`. The A0 relation is printed under Table 18 itself.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy import integrate, special

from bbtools.constants import ConstantTable
from bbtools.printed import parse_printed, resolution_exponent

# Integration grids: φ is negligible beyond |x| = 9 and the range of n ≤ 100 normals beyond 20.
# Simpson with step 0.01 is accurate to ~1e-8, far below the 4th decimal the tables print
# (checked against adaptive quadrature and the closed forms d2(2) = 2/√π, d3(2) = √(2 − 4/π)).
_X = np.linspace(-9.0, 9.0, 1801)
_R = np.linspace(0.0, 20.0, 2001)


@lru_cache(maxsize=None)
def _range_moments(n: int) -> tuple[float, float]:
    """(E[R], E[R²]) of the range of n independent standard normal values."""
    phi = np.exp(-_X**2 / 2) / math.sqrt(2 * math.pi)
    cdf_x = special.ndtr(_X)
    cdf_xr = special.ndtr(_X[None, :] + _R[:, None])          # shape (len(_R), len(_X))
    w = n * integrate.simpson(phi * (cdf_xr - cdf_x) ** (n - 1), x=_X, axis=1)
    survival = 1.0 - w
    return float(integrate.simpson(survival, x=_R)), float(2 * integrate.simpson(_R * survival, x=_R))


def d2(n: int) -> float:
    """Mean range of n standard normal values."""
    return _range_moments(n)[0]


def d3(n: int) -> float:
    """Standard deviation of the range of n standard normal values."""
    mean, second = _range_moments(n)
    return math.sqrt(second - mean**2)


def c4(n: int) -> float:
    """E[s]/σ for the sample standard deviation with divisor n − 1."""
    return math.sqrt(2 / (n - 1)) * math.exp(special.gammaln(n / 2) - special.gammaln((n - 1) / 2))


def c2(n: int) -> float:
    """E[s_n]/σ for the standard deviation with divisor n (the older ASTM convention of Table 18)."""
    return math.sqrt(2 / n) * math.exp(special.gammaln(n / 2) - special.gammaln((n - 1) / 2))


def definition(symbol: str, n: int) -> float:
    """Value of one constant from its definition, for subgroup size n ≥ 2."""
    d2n, d3n, c4n, c2n = d2(n), d3(n), c4(n), c2(n)
    k4 = math.sqrt(1 - c4n**2)
    k2 = math.sqrt((n - 1) / n - c2n**2)
    values = {
        "d2": d2n, "1/d2": 1 / d2n, "d3": d3n, "c4": c4n, "1/c4": 1 / c4n, "c2": c2n, "1/c2": 1 / c2n,
        "A": 3 / math.sqrt(n), "A0": 3 * math.sqrt(n) / d2n, "A1": 3 / (c2n * math.sqrt(n)),
        "A2": 3 / (d2n * math.sqrt(n)), "A3": 3 / (c4n * math.sqrt(n)),
        "B1": max(0.0, c2n - 3 * k2), "B2": c2n + 3 * k2,
        "B3": max(0.0, 1 - 3 * k4 / c4n), "B4": 1 + 3 * k4 / c4n,
        "B5": max(0.0, c4n - 3 * k4), "B6": c4n + 3 * k4,
        "D1": max(0.0, d2n - 3 * d3n), "D2": d2n + 3 * d3n,
        "D3": max(0.0, 1 - 3 * d3n / d2n), "D4": 1 + 3 * d3n / d2n, "E2": 3 / d2n,
    }
    return values[symbol]


@dataclass(frozen=True)
class Difference:
    """A printed constant that does not equal its definition at the printed precision."""

    table: str        # TableSource.key
    symbol: str
    n: int
    printed: str
    definition: float
    units: float      # |printed − definition| in units of the last printed digit

    @property
    def rounding_only(self) -> bool:
        """True if the printed value is at most one unit off: typical of factors computed from rounded d2, d3."""
        return self.units <= 1.0


def differences(tables: tuple[ConstantTable, ...]) -> list[Difference]:
    """Every printed constant (n ≥ 2) whose value differs from its definition once rounded half-up."""
    found = []
    for table in tables:
        for symbol, column in table.symbol_columns().items():
            for row in table.rows:
                n_text, printed = row[0].strip(), row[column].strip()
                if not n_text.isdigit() or int(n_text) < 2 or not printed:
                    continue
                try:
                    value = parse_printed(printed)
                except ValueError:
                    continue  # '**', '3/sqrt(n)': formulas, not numbers
                exact = definition(symbol, int(n_text))
                step = 10.0 ** resolution_exponent(printed)
                units = abs(float(value) - exact) / step
                if units > 0.5 + 1e-9:  # beyond half a unit means half-up rounding gives another digit
                    found.append(Difference(table.source.key, symbol, int(n_text), printed, exact, round(units, 2)))
    return found
