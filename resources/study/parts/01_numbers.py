"""Numbers behind study/parts/01_kader_dmaic_define_team.html (Deel 01).

Deel 01 computes nothing itself: every number in it is quoted from Van Volsem's slides. This script therefore
(1) re-checks each quoted number against the text layer of the cited PDF page (OK / MISMATCH), (2) confirms that the
fragment marks nothing "zelf berekend" and has no numeric exercise answers, and (3) prints every exercise answer
(all are choice questions). Run from anywhere:
    python3 study/parts/01_numbers.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECK = ROOT / "source" / "course" / "Les 1" / "20260521_van volsem.pdf"
FRAGMENT = Path(__file__).resolve().parent / "01_kader_dmaic_define_team.html"

# (PDF page, text as printed on that page) for every number the fragment quotes.
QUOTED: list[tuple[int, str]] = [
    (13, "95%"),  # "Typically 95% of all lead time is non-value added" (extra)
    (63, "20%"), (63, "30%"), (63, "79"), (63, "5 months"), (63, "50%"), (63, "70%"), (63, "Q2 2025"),
    (63, "98%"), (63, "90%"), (63, "80%"),  # goal-statement examples
    (72, "2-5 months"), (72, "6-9 months"),  # project duration Green Belt / Black Belt
    (73, "> 100 Xs"), (73, "≤ 20 Xs"), (73, "≤ 6 Xs"), (73, "≤ 4 Xs"), (73, "≤ 3 Xs"),  # funnel (extra)
]


def page_text(page: int) -> str | None:
    """Text layer of one page of the Van Volsem deck, or None if pdftotext is not available."""
    if shutil.which("pdftotext") is None:
        return None
    result = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(DECK), "-"],
                            capture_output=True, text=True, check=True)
    return result.stdout


def check_quotes() -> None:
    """Every quoted number must appear on the page it is cited from."""
    print("Geciteerde getallen tegen de tekstlaag van de slide")
    cache: dict[int, str | None] = {}
    for page, text in QUOTED:
        if page not in cache:
            cache[page] = page_text(page)
        layer = cache[page]
        if layer is None:
            print(f"  SKIP     VV p. {page}: '{text}' (pdftotext niet gevonden)")
            continue
        found = text in " ".join(layer.split())
        print(f"  {'OK' if found else 'MISMATCH':<8} VV p. {page}: '{text}'")


def exercise_answers() -> bool:
    """Print every data-answer per exercise; Deel 01 must have only choice questions and nothing computed."""
    html = FRAGMENT.read_text(encoding="utf-8")
    ok = "zelf berekend" not in html
    print(f"Geen 'zelf berekend' in het fragment: {'OK' if ok else 'FOUT'}")
    print("Antwoorden per oefening")
    for block in re.split(r'(?=<div class="exercise")', html)[1:]:
        ex_id = re.match(r'<div class="exercise" id="([^"]+)"', block).group(1)
        answers = []
        for attrs in re.findall(r'<div class="q"([^>]*)>', block):
            choice = 'data-type="choice"' in attrs
            ok &= choice
            answers.append(re.search(r'data-answer="([^"]+)"', attrs).group(1) + ("" if choice else " (NUMERIEK!)"))
        print(f"  {ex_id}: {', '.join(answers)}")
    return ok


def main() -> int:
    """Run both checks; exit 1 only if the fragment contains computed or numeric answers."""
    check_quotes()
    return 0 if exercise_answers() else 1


if __name__ == "__main__":
    sys.exit(main())
