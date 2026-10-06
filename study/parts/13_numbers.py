"""Numbers for Deel 13 (example exam, source/exam/20251009_voorbeeldexamen six sigma.pdf): every value the model
answers compute. The exam has no answer key; the inputs are the numbers printed in the questions.
Run from the project root: python3 study/parts/13_numbers.py
"""
from __future__ import annotations

from scipy import stats


def show(label: str, value: float | str) -> None:
    """Print one result line."""
    text = f"{value:.6g}" if isinstance(value, float) else str(value)
    print(f"  {label:<58} {text}")


def q2() -> None:
    """Q2: one-sided 95 % CI for sigma2^2/sigma1^2 with (s1^2/s2^2)(sigma2^2/sigma1^2) ~ F(n1-1, n2-1), n1 = 10, n2 = 15."""
    print("Q2 (data file not in the course files: only the critical value)")
    f05 = float(stats.f.ppf(0.05, 9, 14))
    show("F.INV(0.05; 9; 14)", f05)
    show("F.INV(0.95; 9; 14)", float(stats.f.ppf(0.95, 9, 14)))
    show("lower bound = F.INV(0.05; 9; 14) * s2^2/s1^2 -> factor", f05)


def q3() -> None:
    """Q3: spec 1400-1460 mm, mean 1440, sd 10."""
    print("Q3")
    lsl, usl, mu, sd = 1400.0, 1460.0, 1440.0, 10.0
    cp = (usl - lsl) / (6 * sd)
    cpu, cpl = (usl - mu) / (3 * sd), (mu - lsl) / (3 * sd)
    above, below = float(stats.norm.sf((usl - mu) / sd)), float(stats.norm.cdf((lsl - mu) / sd))
    show("Cp", cp)
    show("Cpu / Cpl", f"{cpu:.4f} / {cpl:.4f}")
    show("Cpk", min(cpu, cpl))
    show("% above USL (z = 2)", 100 * above)
    show("% below LSL (z = -4)", 100 * below)
    show("% out of spec total", 100 * (above + below))
    show("centred at 1430: % out of spec", 100 * 2 * float(stats.norm.sf(30 / sd)))
    show("sd needed for Cp = 2 (tolerance 60): 60/12", 60 / 12)


def q5() -> None:
    """Q5: train/test confusion matrices of three trees (rows actual Goed/Slecht, columns predicted)."""
    print("Q5 accuracies")
    models = {"A": ((480, 20, 15, 485), (180, 120, 110, 190)),
              "B": ((380, 120, 140, 360), (190, 110, 120, 180)),
              "C": ((420, 80, 70, 430), (200, 100, 85, 215))}
    for name, (train, test) in models.items():
        acc = [(m[0] + m[3]) / sum(m) for m in (train, test)]
        show(f"model {name}: train / test accuracy / gap", f"{acc[0]:.4f} / {acc[1]:.4f} / {acc[1] - acc[0]:.4f}")


def q6() -> None:
    """Q6: elco's. 2 in 40 non-conform (C < 720), mean capacity 820; 175.3 orders per week, 3.6 lots per order, lots of 100."""
    print("Q6")
    p = 2 / 40
    show("E[X] = p", p)
    show("E[D] = 100 p", 100 * p)
    show("E[B] (orders per week)", 175.3)
    show("E[T] = 1/175.3 week", 1 / 175.3)
    show("E[T] in hours (168 h per week)", 168 / 175.3)
    show("E[T] in minutes", 168 * 60 / 175.3)
    z = float(stats.norm.ppf(p))
    sigma = (720 - 820) / z
    show("z for P(C < 720) = 0.05", z)
    show("sigma = (720 - 820)/z", sigma)
    show("Var[C] = sigma^2", sigma ** 2)
    show("Var[X] = p(1-p)", p * (1 - p))
    show("Var[D] = 100 p (1-p)", 100 * p * (1 - p))


if __name__ == "__main__":
    q2()
    q3()
    q5()
    q6()
