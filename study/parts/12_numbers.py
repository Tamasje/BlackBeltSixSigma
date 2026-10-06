#!/usr/bin/env python3
"""Numbers for Deel 12 (Machine learning en big data, Naert lecture 2, Les 2).

Prints every number that study/parts/12_machine_learning.html marks "zelf berekend", every exercise answer
(data-answer), and re-checks the printed course results that the text quotes (OK / MISMATCH).
Course data are read from inventory/constants/*.csv (rows carry file + page); a few small values
are transcribed from a slide, with the page in a comment. Exits 0 when every check passes.
"""
from __future__ import annotations

import ast
import csv
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONST = ROOT / "inventory" / "constants"

FAILURES: list[str] = []


def check(label: str, computed: float, printed: float, tol: float) -> None:
    """Compare a computed value with a printed course value and print OK or MISMATCH."""
    ok = abs(computed - printed) <= tol
    print(f"{'OK      ' if ok else 'MISMATCH'} {label}: computed {computed:.6g}, printed {printed:g}")
    if not ok:
        FAILURES.append(label)


def show(label: str, value: float | Fraction | int, digits: int = 4) -> None:
    """Print one computed number (fractions also as a decimal)."""
    if isinstance(value, Fraction):
        print(f"  {label} = {value.numerator}/{value.denominator} = {float(value):.{digits}f}")
    elif isinstance(value, int):
        print(f"  {label} = {value}")
    else:
        print(f"  {label} = {value:.{digits}f}")


def ratio(label: str, num: int, den: int, digits: int = 4) -> None:
    """Print an unreduced ratio of counts and its decimal value."""
    print(f"  {label} = {num}/{den} = {num / den:.{digits}f}")


def read_rows(name: str) -> list[dict[str, str]]:
    """Read one inventory constants CSV as a list of dicts."""
    with open(CONST / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- 4x4 confusion matrix
def confusion_4x4() -> list[list[int]]:
    """4x4 example matrix of ML p. 30 / web-slides p. 30: rows = Predicted, columns = Expected."""
    rows = read_rows("S11_confusion_matrix_example_4_x_4_figure_rows_predicted_columns.csv")
    return [[int(r[c]) for c in ("1", "2", "3", "4")] for r in rows]


def per_class_counts(m: list[list[int]], k: int) -> tuple[int, int, int, int]:
    """TP, FP, FN, TN with class k as the positive class (rows predicted, columns actual)."""
    total = sum(map(sum, m))
    tp = m[k][k]
    fp = sum(m[k]) - tp                      # predicted k, actually another class
    fn = sum(m[i][k] for i in range(4)) - tp  # actually k, predicted another class
    return tp, fp, fn, total - tp - fp - fn


def section_confusion() -> None:
    """Accuracy and per-class precision, recall, F1 of the 4x4 matrix; one-vs-rest 2x2 for class 1."""
    print("\n=== 12.10 / ex-12-7, ex-12-8: confusion matrix ML p. 30 (rows Predicted, cols Expected)")
    m = confusion_4x4()
    total = sum(map(sum, m))
    diag = sum(m[i][i] for i in range(4))
    show("total observations", total)
    print(f"  row sums (predicted 1..4) = {[sum(r) for r in m]}")
    print(f"  column sums (expected 1..4) = {[sum(m[i][j] for i in range(4)) for j in range(4)]}")
    show("diagonal (correct)", diag)
    ratio("accuracy = diag/total [ex-12-7]", diag, total)
    for k in range(4):
        tp, fp, fn, tn = per_class_counts(m, k)
        p, r = Fraction(tp, tp + fp), Fraction(tp, tp + fn)
        f1 = 2 * p * r / (p + r)
        print(f"  class {k + 1} positive: TP={tp} FP={fp} FN={fn} TN={tn}")
        ratio(f"    precision class {k + 1} [ex-12-7]", tp, tp + fp)
        ratio(f"    recall class {k + 1} [ex-12-7]", tp, tp + fn)
        show(f"    F1 = 2PR/(P+R) class {k + 1} [ex-12-7]", float(f1))
    # largest off-diagonal cell: which confusion is most frequent
    off = max(((m[i][j], i + 1, j + 1) for i in range(4) for j in range(4) if i != j))
    print(f"  largest off-diagonal cell: {off[0]} (predicted {off[1]}, expected {off[2]})")

    print("\n--- ex-12-8: one-vs-rest 2x2 for class 1 (rows actual, as on ML p. 31)")
    tp, fp, fn, tn = per_class_counts(m, 0)
    print(f"  actual 1: TP={tp}, FN={fn}; actual not-1: FP={fp}, TN={tn}  [ex-12-8 TN answer = {tn}]")
    ratio("accuracy 2x2 (class 1 vs rest) [ex-12-8]", tp + tn, total)
    p1, r1 = Fraction(tp, tp + fp), Fraction(tp, tp + fn)
    ratio("precision, class 1 positive", tp, tp + fp)
    ratio("recall, class 1 positive", tp, tp + fn)
    show("F1, class 1 positive", float(2 * p1 * r1 / (p1 + r1)))
    # same 2x2 with 'not class 1' as the positive class: roles swap (TP<->TN, FP<->FN)
    p2, r2 = Fraction(tn, tn + fn), Fraction(tn, tn + fp)
    ratio("precision, 'rest' positive [ex-12-8]", tn, tn + fn)
    ratio("recall, 'rest' positive [ex-12-8]", tn, tn + fp)
    show("F1, 'rest' positive [ex-12-8]", float(2 * p2 * r2 / (p2 + r2)))


# ---------------------------------------------------------------- decision tree ML p. 44
def tree_nodes() -> dict[str, tuple[int, int, int, str]]:
    """Node -> (samples, n_not_survived, n_survived, printed class), from notes p. 19 = ML p. 44."""
    out = {}
    for r in read_rows("S11_decision_tree_example_figure_same_figure_on_slide_44_node_co.csv"):
        v = [int(float(x)) for x in ast.literal_eval(r["value"])]
        out[r["node (level, position left to right)"]] = (int(r["samples"]), v[0], v[1], r["class"])
    return out


def section_tree() -> None:
    """Consistency of the printed tree; training accuracy when the tree is cut after each level."""
    print("\n=== 12.14 / ex-12-11, ex-12-12: decision tree ML p. 44 (Titanic training data)")
    n = tree_nodes()
    parent_children = {
        "root": ["level 2, left (True branch)", "level 2, right (False branch)"],
        "level 2, left (True branch)": ["level 3, 1st", "level 3, 2nd"],
        "level 2, right (False branch)": ["level 3, 3rd", "level 3, 4th"],
        "level 3, 1st": ["leaf 1", "leaf 2"],
        "level 3, 2nd": ["leaf 3", "leaf 4"],
        "level 3, 3rd": ["leaf 5", "leaf 6"],
        "level 3, 4th": ["leaf 7", "leaf 8"],
    }
    for par, kids in parent_children.items():
        for idx in range(3):  # samples, not survived, survived must add up
            check(f"tree: {par} = sum of its children (field {idx})",
                  sum(n[k][idx] for k in kids), n[par][idx], 0)
    for name, (s, a, b, cls) in n.items():
        majority = "Did not survive" if a > b else "Survived"
        check(f"tree: printed class of {name} is the majority class ({cls})",
              1.0 if majority == cls else 0.0, 1.0, 0)
        check(f"tree: samples of {name} = value sum", a + b, s, 0)

    levels = {
        0: ["root"],
        1: ["level 2, left (True branch)", "level 2, right (False branch)"],
        2: ["level 3, 1st", "level 3, 2nd", "level 3, 3rd", "level 3, 4th"],
        3: [f"leaf {i}" for i in range(1, 9)],
    }
    total = n["root"][0]
    for depth, nodes in levels.items():
        correct = sum(max(n[k][1], n[k][2]) for k in nodes)
        ratio(f"training accuracy, tree cut after depth {depth} [ex-12-12]", correct, total)
    # root only: everybody 'Did not survive' -> recall of the class 'Survived'
    ratio("root only: recall with 'Survived' positive [ex-12-12]", 0, n["root"][2])
    ratio("share 'Did not survive' at the root", n["root"][1], total)
    # ex-12-11: path True / False / False = Sex<=0.5 true, Pclass<=1.5 false, Age<=3.5 false -> leaf 4
    # ex-12-11: True = left branch, False = right branch (ML p. 44)
    for path, leaf in (("(a) T, F, F", "leaf 4"), ("(c) F, T, T", "leaf 5"), ("(d) F, F, T", "leaf 7")):
        s_, d_, v_, c_ = n[leaf]
        print(f"  ex-12-11 {path} ends in {leaf}: value [{d_}, {v_}], class {c_}, samples = {s_}")


# ---------------------------------------------------------------- Bayesian coin web-slides p. 55
def section_bayes() -> None:
    """Coin example (prior Beta(1,1), H H T H T) and a variant with the Beta(2,8) prior of Les 1."""
    print("\n=== 12.17 / ex-12-14: Bayesian coin, web-slides p. 55")
    rows = {r["panel"]: r["printed content"] for r in
            read_rows("S11_bayesian_inference_coin_example_figure_4_panels.csv")}
    seq = rows["Data"].split("Observed sequence:")[1].split(";")[0].split()
    k, n = seq.count("H"), len(seq)
    a0, b0 = 1, 1  # prior Beta(1, 1), web-slides p. 55
    show("heads k", k)
    show("tosses n", n)
    ratio("prior mean of Beta(1, 1), alpha/(alpha+beta)", a0, a0 + b0)
    mle = Fraction(k, n)
    ratio("MLE k/n [ex-12-14]", k, n)
    check("web-slides p. 55: MLE = 0.60", float(mle), 0.60, 0.005)
    a1, b1 = a0 + k, b0 + n - k
    show("posterior alpha [ex-12-14]", a1)
    show("posterior beta [ex-12-14]", b1)
    check("web-slides p. 55: posterior Beta(4, 3), alpha", a1, 4, 0)
    check("web-slides p. 55: posterior Beta(4, 3), beta", b1, 3, 0)
    mean = Fraction(a1, a1 + b1)
    ratio("posterior mean alpha/(alpha+beta) [ex-12-14]", a1, a1 + b1)
    check("web-slides p. 55: posterior mean 4/7 = 0.57", float(mean), 0.57, 0.005)
    # likelihood p^3 (1-p)^2 peaks at the MLE (grid check)
    grid = [i / 10000 for i in range(10001)]
    peak = max(grid, key=lambda p: p ** k * (1 - p) ** (n - k))
    check("web-slides p. 55: likelihood p^3(1-p)^2 peaks at MLE 0.6", peak, 0.6, 1e-4)

    print("\n--- ex-12-14 variant: prior Beta(2, 8) (Les 1 notes p. 4), same data")
    check("Les 1 notes p. 4: mean of Beta(2, 8) = 0.200", 2 / (2 + 8), 0.200, 0.0005)
    a2, b2 = 2 + k, 8 + n - k
    show("variant posterior alpha [ex-12-14]", a2)
    show("variant posterior beta [ex-12-14]", b2)
    ratio("variant posterior mean [ex-12-14]", a2, a2 + b2)


# ---------------------------------------------------------------- loss functions ML p. 11-12
def section_loss() -> None:
    """Squared versus absolute loss at the errors on the axis of the ML p. 11 figure."""
    print("\n=== 12.4 / ex-12-2: loss per observation (ML p. 11 figure, x-axis from -3 to 3)")
    for e in (1, 3):
        show(f"squared loss e^2 at e = {e} [ex-12-2]", e ** 2)
        show(f"absolute loss |e| at e = {e} [ex-12-2]", abs(e))
    check("ML p. 11: squared and absolute loss cross at |e| = 1 (loss 1)", 1 ** 2, abs(1), 0)


# ---------------------------------------------------------------- data split, cross-validation
def section_cv() -> None:
    """Split shares of ML p. 20 and the k-fold bookkeeping of notes p. 9."""
    print("\n=== 12.7 / ex-12-4: train/validation/test and k-fold")
    rows = read_rows("S11_data_split_figure_simple_train_validation_test_split_paradig.csv")
    shares = [float(r["share as printed"].rstrip("%")) for r in rows if not r["part"].startswith("Full")]
    check("ML p. 20 figure: 70 % + 15 % + 15 % = 100 %", sum(shares), 100, 0)
    k = 5  # notes p. 9: typical k = 5 or k = 10
    show("k = 5: number of trainings [ex-12-4]", k)
    show("k = 5: folds used for training per round (k - 1) [ex-12-4]", k - 1)
    ratio("k = 5: share of the data used for training per round [ex-12-4]", k - 1, k)
    ratio("3-fold (ML p. 21): share of non-test data used for training per round", 2, 3)


# ---------------------------------------------------------------- neural network ML p. 38
def section_nn() -> None:
    """Weights and biases of the 3-4-4-1 network on ML p. 38 (notes p. 17)."""
    print("\n=== 12.13 / ex-12-10: network ML p. 38")
    dims = {}
    for r in read_rows("S11_network_figure_weight_matrix_dimensions_same_figure_on_slide.csv"):
        a, b = r["dimension as printed"].strip("()").split("x")
        dims[r["matrix"]] = (int(a), int(b))
    layers = [3, 4, 4, 1]  # neurons per layer as drawn on ML p. 38: input 3, hidden 4, hidden 4, output 1
    for i, w in enumerate(("W1", "W2", "W3")):
        check(f"ML p. 38: {w} {dims[w]} = (next layer x previous layer)",
              1.0 if dims[w] == (layers[i + 1], layers[i]) else 0.0, 1.0, 0)
    n_w = sum(a * b for a, b in dims.values())
    n_b = sum(layers[1:])  # one bias b per neuron (ML p. 37), not for the input nodes
    show("hidden layers [ex-12-10]", len(layers) - 2)
    show("weights in W1 [ex-12-10]", dims["W1"][0] * dims["W1"][1])
    show("all weights W1 + W2 + W3 [ex-12-10]", n_w)
    show("biases (one per hidden/output neuron)", n_b)
    show("trainable parameters, weights + biases [ex-12-10]", n_w + n_b)


def main() -> int:
    """Run all sections and return 1 if any re-check failed."""
    print("Deel 12 — numbers (Naert, Inleiding tot Machine Learning)")
    section_loss()
    section_cv()
    section_confusion()
    section_nn()
    section_tree()
    section_bayes()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} MISMATCH(ES): " + "; ".join(FAILURES))
        return 1
    print("All re-checks OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
