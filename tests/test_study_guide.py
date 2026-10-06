"""The study guide (study/studiegids.html) assembles without problems.

study/build_study.py --check validates the whole page without writing it: links to existing files and PDF pages in
range, unique ids, no http, every exercise with a solution and a numeric answer, every clickable variable defined in
its part's NN_symbols.tsv with an existing anchor, pitfall boxes well-formed. This test also requires every formula
block to contain a clickable variable.
"""
from __future__ import annotations

import subprocess
import sys

from bbtools.constants import ROOT


def test_study_guide_builds_without_problems() -> None:
    # arrange
    script = ROOT / "study" / "build_study.py"
    # act
    result = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True, cwd=ROOT)
    # assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert "formula blocks without a clickable variable: none" in result.stdout, result.stdout
