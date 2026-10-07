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
    tool="Confusion matrix: nauwkeurigheid (accuracy), sensitiviteit (recall), precisie (precision), F1 "
         "(trainingsset vs testset, tot drie modellen)",
    source="source/course/Les 2/20260529_naert.pdf p. 19-32 (train/test, underfitting/overfitting, bias-variance, "
           "confusion matrix en haar maten)",
    convention="Sensitiviteit (recall), precisie en F1 getoond met elke klasse als de positieve klasse (de cursus "
               "laat die keuze aan het domein); geen automatisch bias/variance-label.",
    status=Status.UNVERIFIED,
    status_detail="geen uitgewerkt cursusvoorbeeld drukt deze maten af; gecontroleerd tegen een onafhankelijke "
                  "berekening en door de stats-auditor (build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Maten van 2x2-confusion matrices voor de trainingsset en de testset van tot drie modellen, naast elkaar, "
            "om underfitting en overfitting te beoordelen zoals in examenvraag Q5.",
    inputs="optioneel de klassenamen; per model de vier aantallen van de matrix van de trainingsset en van de testset "
           "(rijen = werkelijke klasse, kolommen = voorspelde klasse).",
    audit="stats-auditor PASS (2026-09-28): alle 26 waarden voor één invoer (model A, trainingsset en testset) komen "
          "overeen met een onafhankelijke berekening uit 20260529_naert.pdf p. 29-32. Opmerking: 'foutenpercentage' "
          "(error rate) staat niet op die pagina's; het blad toont het als 1 − nauwkeurigheid.",
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
    column_titles(ws, top + 1, ["aantallen (rijen = werkelijk)", "Trainingsset: voorspeld klasse 1",
                                "voorspeld klasse 2", "", "Testset: voorspeld klasse 1", "voorspeld klasse 2"])
    for offset, text in ((2, "werkelijk klasse 1"), (3, "werkelijk klasse 2")):
        label(ws, top + offset, 1, text, bold=True)
    for dataset in ("train", "test"):
        for coordinate in matrix_cells(index, dataset).values():
            input_cell(ws, coordinate, "0")
    column_titles(ws, top + 4, ["Maat (metric)", "Trainingsset", "Testset", "Testset − trainingsset",
                                "Bron in de cursus"])
    texts = {
        "accuracy": ("Nauwkeurigheid (accuracy) = (juist) / (alle)", "p. 31 ('Misleidend bij onevenwicht.')"),
        "error_rate": ("Foutenpercentage (error rate) = 1 − nauwkeurigheid", ""),
        "recall_1": ("Sensitiviteit (recall), klasse 1 positief = TP / (TP + FN)", "p. 31"),
        "precision_1": ("Precisie (precision), klasse 1 positief = TP / (TP + FP)", "p. 31"),
        "f1_1": ("F1, klasse 1 positief = 2·P·R / (P + R)", "p. 31"),
        "recall_2": ("Sensitiviteit (recall), klasse 2 positief", "p. 31"),
        "precision_2": ("Precisie, klasse 2 positief", "p. 31"),
        "f1_2": ("F1, klasse 2 positief", "p. 31"),
        "total": ("Aantal items", ""),
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
    section_title(ws, top, f"{len(MODEL_NAMES) + 2}. Vergelijking en hoe de cursus ze leest")
    column_titles(ws, top + 1, ["Model", "Nauwkeurigheid trainingsset", "Nauwkeurigheid testset",
                                "Testset − trainingsset"])
    for index, name in enumerate(MODEL_NAMES):
        row = top + 2 + index
        label(ws, row, 1, f"Model {name}", bold=True)
        for column, dataset in (("B", "train"), ("C", "test"), ("D", "gap")):
            output_cell(ws, f"{column}{row}", f"={metric_cell(index, dataset, 'accuracy')}", PERCENT)
    notes = (
        "Underfitting: hoge bias, lage variantie (variance); hoog verlies (loss) op trainingsset en testset, dus beide "
        "nauwkeurigheden laag.",
        "Overfitting: lage bias, hoge variantie; laag verlies op de trainingsset, hoog op de testset, dus nauwkeurigheid "
        "trainingsset hoog en nauwkeurigheid testset duidelijk lager.",
        "Goede fit: lage bias, lage variantie; laag verlies op trainingsset en testset. Optimum bij het minimum van "
        "bias² + variantie.",
        "Bron: 20260529_naert.pdf p. 22-28 (underfitting, overfitting, bias-variance-afweging, trade-off); "
        "beslissingsbomen (decision trees) p. 43-46.",
    )
    for offset, text in enumerate(notes):
        label(ws, top + 6 + offset, 1, text, italic=offset == 3)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the confusion-matrix calculator."""
    write_header(ws, HEADER)
    section_title(ws, 8, "1. Klassenamen (optioneel, voor eigen gebruik)")
    input_row(ws, 9, "Klasse 1", "bv. Goed")
    input_row(ws, 10, "Klasse 2", "bv. Slecht")
    counts = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
                            showErrorMessage=True, errorTitle="Aantal", error="Een aantal is een geheel getal, 0 of meer.")
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
