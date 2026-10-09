"""Tests for the plain-language verdicts on the Regressie and ANOVA sheets ("is it significant?"), via LibreOffice.

The verdict sentences repeat the F-test the sheets already compute: a clear linear trend and clearly different group
means are significant; noise around a flat line and equal group means are not. The p-values come from scipy.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from scipy import stats

from bbtools import sheet_anova, sheet_regression

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]


def regression_cells(xs: list[float], ys: list[float]) -> dict[str, float]:
    """Cells holding the pairs (x in B, y in C) from the first pair row down."""
    first = sheet_regression.FIRST_PAIR
    return {**{f"B{first + i}": x for i, x in enumerate(xs)}, **{f"C{first + i}": y for i, y in enumerate(ys)}}


def test_regression_verdict_says_yes_for_a_clear_trend_and_no_for_noise(evaluate: Evaluate) -> None:
    # arrange
    xs = [1, 2, 3, 4, 5, 6, 7, 8]
    trend = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2, 13.9, 16.1]
    noise = [5.1, 4.8, 5.3, 4.9, 5.2, 4.7, 5.0, 5.1]
    # act
    significant = evaluate(sheet_regression.SHEET, regression_cells(xs, trend))["B13"].value
    flat = evaluate(sheet_regression.SHEET, regression_cells(xs, noise))["B13"].value
    # assert
    assert significant.startswith("JA, de regressie is significant") and "lineair verband" in significant
    assert flat.startswith("NEE, de regressie is niet significant")
    assert stats.linregress(xs, noise).pvalue > 0.05


def test_anova_verdict_says_yes_for_different_group_means_and_no_for_equal_ones(evaluate: Evaluate) -> None:
    # arrange -- three groups in columns B, C, D from the first value row down
    first = sheet_anova.FIRST_GROUP_ROW
    different = {"B": [10.0, 10.2, 9.9, 10.1], "C": [12.0, 12.2, 11.9, 12.1], "D": [14.1, 13.9, 14.0, 14.2]}
    equal = {"B": [10.0, 10.4, 9.8, 10.2], "C": [10.1, 9.9, 10.3, 10.0], "D": [10.2, 9.7, 10.1, 10.0]}
    cells = lambda groups: {f"{column}{first + i}": v for column, values in groups.items() for i, v in enumerate(values)}
    # act
    yes = evaluate(sheet_anova.SHEET, cells(different))["B24"].value
    no = evaluate(sheet_anova.SHEET, cells(equal))["B24"].value
    # assert
    assert yes.startswith("JA, significant") and "minstens één groepsgemiddelde verschilt" in yes
    assert no.startswith("NEE, niet significant")
    assert stats.f_oneway(*equal.values()).pvalue > 0.05 > stats.f_oneway(*different.values()).pvalue
