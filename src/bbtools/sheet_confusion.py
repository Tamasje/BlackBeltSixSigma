"""Confusion-matrix sheet: accuracy, recall, precision and F1 for training and test sets of up to three models.

Course (Naert, Les 2, 20260529_naert.pdf p. 29-32): Accuracy = (TP+TN)/(TP+TN+FP+FN); Recall = TP/(TP+FN);
Precision = TP/(TP+FP); F1 = 2·P·R/(P+R). Which class is 'positive' is a domain decision (p. 31), so recall,
precision and F1 are shown with each class as the positive one. Under-/overfitting (p. 22-28): the sheet shows
training accuracy, test accuracy and their gap, and does not label models itself (the course gives no threshold).
Matrix layout as in exam Q5: rows = actual class, columns = predicted class.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    column_titles,
    input_cell,
    input_row,
    label,
    output_cell,
    section_title,
    write_header,
)

SHEET = "Confusion matrix"

HEADER = HeaderBlock(
    tool="Confusion matrix: accuracy, recall, precision, F1 (training vs test, up to three models)",
    source="source/course/Les 2/20260529_naert.pdf p. 19-32 (train/test, under-/overfitting, bias-variance, "
           "confusion matrix and its metrics)",
    convention="Recall, precision and F1 shown with each class as the positive class (the course leaves that "
               "choice to the domain); no automatic bias/variance label.",
    status=Status.UNVERIFIED,
    status_detail="no course worked example prints these metrics; checked against an independent computation "
                  "and by the stats-auditor (build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Metrics of 2x2 confusion matrices for the training and the test set of up to three models, side by "
            "side, to judge under- and overfitting as in exam Q5.",
    inputs="optional class names; per model the four counts of the training matrix and of the test matrix "
           "(rows = actual class, columns = predicted class).",
    audit="pending",
    disagreements=(),
)

MODEL_NAMES = ("A", "B", "C")
FIRST_MODEL_ROW = 12
MODEL_ROWS = 15
PERCENT = "0.00%"
METRICS = ("accuracy", "error_rate", "recall_1", "precision_1", "f1_1", "recall_2", "precision_2", "f1_2", "total")


def model_top(index: int) -> int:
    """Row of model `index`'s section title."""
    return FIRST_MODEL_ROW + MODEL_ROWS * index


def matrix_cells(index: int, dataset: str) -> dict[str, str]:
    """Input cells of one matrix: keys a1p1, a1p2, a2p1, a2p2 (actual class, predicted class)."""
    top = model_top(index)
    first, second = ("B", "C") if dataset == "train" else ("E", "F")
    return {"a1p1": f"{first}{top + 2}", "a1p2": f"{second}{top + 2}",
            "a2p1": f"{first}{top + 3}", "a2p2": f"{second}{top + 3}"}


def metric_cell(index: int, dataset: str, metric: str) -> str:
    """Result cell of one metric ('accuracy', 'recall_1', ...) for 'train', 'test' or 'gap'."""
    column = {"train": "B", "test": "C", "gap": "D"}[dataset]
    return f"{column}{model_top(index) + 5 + METRICS.index(metric)}"


def _metric_formulas(m: dict[str, str]) -> dict[str, str]:
    """Formulas for every metric of one matrix (without the leading '=' and the empty-input guard)."""
    a1p1, a1p2, a2p1, a2p2 = m["a1p1"], m["a1p2"], m["a2p1"], m["a2p2"]
    total = f"({a1p1}+{a1p2}+{a2p1}+{a2p2})"
    p1, r1 = f"{a1p1}/({a1p1}+{a2p1})", f"{a1p1}/({a1p1}+{a1p2})"
    p2, r2 = f"{a2p2}/({a2p2}+{a1p2})", f"{a2p2}/({a2p2}+{a2p1})"
    return {
        "accuracy": f"({a1p1}+{a2p2})/{total}",
        "error_rate": f"({a1p2}+{a2p1})/{total}",
        "recall_1": r1, "precision_1": p1, "f1_1": f"2*({p1})*({r1})/(({p1})+({r1}))",
        "recall_2": r2, "precision_2": p2, "f1_2": f"2*({p2})*({r2})/(({p2})+({r2}))",
        "total": total,
    }


def _model(ws: Worksheet, index: int) -> None:
    """One model: training and test matrices, then their metrics and the test − training gap."""
    top = model_top(index)
    section_title(ws, top, f"{index + 2}. Model {MODEL_NAMES[index]}")
    column_titles(ws, top + 1, ["counts (rows = actual)", "Training: predicted class 1", "predicted class 2", "",
                                "Test: predicted class 1", "predicted class 2"])
    for offset, text in ((2, "actual class 1"), (3, "actual class 2")):
        label(ws, top + offset, 1, text, bold=True)
    for dataset in ("train", "test"):
        for coordinate in matrix_cells(index, dataset).values():
            input_cell(ws, coordinate, "0")
    column_titles(ws, top + 4, ["Metric", "Training", "Test", "Test − training", "Course source"])
    texts = {
        "accuracy": ("Accuracy = (correct) / (all)", "p. 31 (misleading with unequal classes)"),
        "error_rate": ("Error rate = 1 − accuracy", ""),
        "recall_1": ("Recall, class 1 positive = TP / (TP + FN)", "p. 31"),
        "precision_1": ("Precision, class 1 positive = TP / (TP + FP)", "p. 31"),
        "f1_1": ("F1, class 1 positive = 2·P·R / (P + R)", "p. 31"),
        "recall_2": ("Recall, class 2 positive", "p. 31"),
        "precision_2": ("Precision, class 2 positive", "p. 31"),
        "f1_2": ("F1, class 2 positive", "p. 31"),
        "total": ("Number of items", ""),
    }
    for dataset in ("train", "test"):
        cells = matrix_cells(index, dataset)
        have = f"COUNT({','.join(cells.values())})=4"
        for metric, formula in _metric_formulas(cells).items():
            fmt = "0" if metric == "total" else PERCENT
            output_cell(ws, metric_cell(index, dataset, metric), f'=IFERROR(IF({have},{formula},""),"")', fmt)
    for metric in METRICS:
        row = model_top(index) + 5 + METRICS.index(metric)
        label(ws, row, 1, texts[metric][0])
        label(ws, row, 5, texts[metric][1], italic=True)
        if metric != "total":
            train, test = metric_cell(index, "train", metric), metric_cell(index, "test", metric)
            output_cell(ws, metric_cell(index, "gap", metric),
                        f'=IF(AND(ISNUMBER({train}),ISNUMBER({test})),{test}-{train},"")', PERCENT)


def _comparison(ws: Worksheet) -> None:
    """Last section: the three models' accuracies side by side, with the course's reading of them."""
    top = model_top(len(MODEL_NAMES))
    section_title(ws, top, f"{len(MODEL_NAMES) + 2}. Comparison and how the course reads it")
    column_titles(ws, top + 1, ["Model", "Training accuracy", "Test accuracy", "Test − training"])
    for index, name in enumerate(MODEL_NAMES):
        row = top + 2 + index
        label(ws, row, 1, f"Model {name}", bold=True)
        for column, dataset in (("B", "train"), ("C", "test"), ("D", "gap")):
            output_cell(ws, f"{column}{row}", f"={metric_cell(index, dataset, 'accuracy')}", PERCENT)
    notes = (
        "Underfitted model (high bias, low variance): high training loss and high test loss, i.e. both accuracies low.",
        "Overfitted model (low bias, high variance): low training loss, high test loss, i.e. training accuracy high "
        "and test accuracy clearly lower.",
        "Good fit (low bias, low variance): low training and test loss. Optimum at the minimum of bias² + variance.",
        "Source: 20260529_naert.pdf p. 22-28 (underfitting, overfitting, bias-variance trade-off); "
        "decision trees p. 43-46.",
    )
    for offset, text in enumerate(notes):
        label(ws, top + 6 + offset, 1, text, italic=offset == 3)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the confusion-matrix calculator."""
    write_header(ws, HEADER)
    section_title(ws, 8, "1. Class names (optional, for your own reference)")
    input_row(ws, 9, "Class 1", "e.g. Goed")
    input_row(ws, 10, "Class 2", "e.g. Slecht")
    counts = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                            showErrorMessage=True, errorTitle="Count", error="A count is a whole number, 0 or more.")
    ws.add_data_validation(counts)
    for index in range(len(MODEL_NAMES)):
        _model(ws, index)
        for dataset in ("train", "test"):
            for coordinate in matrix_cells(index, dataset).values():
                counts.add(coordinate)
    _comparison(ws)
    ws.column_dimensions["A"].width = 48
    for letter in "BCDEF":
        ws.column_dimensions[letter].width = 17
