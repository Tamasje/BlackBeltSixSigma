"""Tests for bbtools.sheet_confusion, evaluated by LibreOffice headless.

No course worked example prints accuracy, recall, precision or F1 (the sheet is UNVERIFIED). Expected values
are an independent computation of the course definitions (20260529_naert.pdf p. 31) on the course's own
matrices: the Titanic test sets (S02-WE04, 20260626_naert.pdf p. 27) and the three models of exam Q5
(no answer key), plus random matrices.
"""
from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest

from bbtools.sheet_confusion import METRICS, SHEET, matrix_cells, metric_cell

pytestmark = pytest.mark.libreoffice

Evaluate = Callable[[str, dict[str, float]], Any]
Matrix = tuple[int, int, int, int]  # (actual 1 predicted 1, actual 1 predicted 2, actual 2 predicted 1, actual 2 predicted 2)


def expected(m: Matrix) -> dict[str, float]:
    """Course metrics of one matrix, computed directly in Python."""
    a1p1, a1p2, a2p1, a2p2 = m
    total = sum(m)
    p1, r1 = a1p1 / (a1p1 + a2p1), a1p1 / (a1p1 + a1p2)
    p2, r2 = a2p2 / (a2p2 + a1p2), a2p2 / (a2p2 + a2p1)
    return {"accuracy": (a1p1 + a2p2) / total, "error_rate": (a1p2 + a2p1) / total,
            "recall_1": r1, "precision_1": p1, "f1_1": 2 * p1 * r1 / (p1 + r1),
            "recall_2": r2, "precision_2": p2, "f1_2": 2 * p2 * r2 / (p2 + r2), "total": total}


def cells(models: list[tuple[Matrix, Matrix]]) -> dict[str, float]:
    """Input cells for up to three (training, test) matrix pairs."""
    typed: dict[str, float] = {}
    for index, pair in enumerate(models):
        for dataset, matrix in zip(("train", "test"), pair, strict=True):
            typed |= dict(zip(matrix_cells(index, dataset).values(), matrix, strict=True))
    return typed


def assert_metrics(ws: Any, models: list[tuple[Matrix, Matrix]]) -> None:
    """Every metric, and the test - training gap, equals the independent computation (rel=1e-12: same arithmetic)."""
    for index, (train, test) in enumerate(models):
        want_train, want_test = expected(train), expected(test)
        for metric in METRICS:
            assert ws[metric_cell(index, "train", metric)].value == pytest.approx(want_train[metric], rel=1e-12)
            assert ws[metric_cell(index, "test", metric)].value == pytest.approx(want_test[metric], rel=1e-12)
            if metric != "total":
                assert ws[metric_cell(index, "gap", metric)].value == pytest.approx(
                    want_test[metric] - want_train[metric], rel=1e-9, abs=1e-12)


def test_titanic_test_sets_s02_we04(oracle: dict[str, Any], evaluate: Evaluate) -> None:
    # arrange -- p. 27: rows actual (not survived, survived), columns predicted; counts from the oracle
    answers = oracle["S02-WE04"]["stated_answers"]
    assert "TN(not survived/not survived)=128, FP(not survived/survived)=9" in answers["shallow_tree"]
    assert "TN=127, FP=10, FN=37, TP=49" in answers["random_forest"]
    shallow, forest = (128, 9, 41, 45), (127, 10, 37, 49)
    models = [(shallow, shallow), (forest, forest)]  # only test sets are printed; used for both columns
    # act
    ws = evaluate(SHEET, cells(models))
    # assert
    assert_metrics(ws, models)


def test_exam_q5_three_decision_trees(evaluate: Evaluate) -> None:
    # arrange -- exam Q5 (source/exam, p. 4-5), rows Werkelijk Goed/Slecht, columns Voorspeld Goed/Slecht
    models = [((480, 20, 15, 485), (180, 120, 110, 190)),
              ((380, 120, 140, 360), (190, 110, 120, 180)),
              ((420, 80, 70, 430), (200, 100, 85, 215))]
    # act
    ws = evaluate(SHEET, cells(models))
    # assert
    assert_metrics(ws, models)


@pytest.mark.parametrize("seed", [1, 2])
def test_random_matrices(seed: int, evaluate: Evaluate) -> None:
    # arrange
    rng = random.Random(seed)
    models = [tuple(tuple(rng.randint(1, 900) for _ in range(4)) for _ in range(2)) for _ in range(3)]
    # act
    ws = evaluate(SHEET, cells(models))
    # assert
    assert_metrics(ws, models)


def test_incomplete_matrix_leaves_its_metrics_empty(evaluate: Evaluate) -> None:
    # arrange -- only three of the four training counts of model A
    first = matrix_cells(0, "train")
    ws = evaluate(SHEET, {first["a1p1"]: 5, first["a1p2"]: 3, first["a2p1"]: 2})
    # act / assert
    assert all(ws[metric_cell(0, "train", metric)].value is None for metric in METRICS)
