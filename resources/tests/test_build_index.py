"""Tests for bbtools.build_index: build/index.html is self-contained and every link points at a real course page."""
from __future__ import annotations

import html
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote

import pytest

from bbtools.build_index import CALCULATOR_SHEETS, EXAM_MAP, NOT_FOR_EXAM, TOPICS, load_inventory, render
from bbtools.build_workbook import TOOL_SHEETS
from bbtools.constants import ROOT

BUILD = ROOT / "build"
HREF = re.compile(r'href="([^"]*)"')


@pytest.fixture(scope="module")
def page() -> str:
    """The rendered index page."""
    return render(*load_inventory())


@lru_cache(maxsize=None)
def pdf_pages(path: Path) -> int:
    """Number of pages of a PDF, by pdfinfo."""
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE).group(1))


def test_index_has_no_external_references(page: str) -> None:
    # act / assert -- no http(s), no protocol-relative URLs, no external scripts, styles or images
    assert not re.search(r"https?:", page, re.IGNORECASE)
    assert "//" not in "".join(HREF.findall(page))
    assert not re.search(r"<(script|link|img|iframe)[^>]*\b(src|href)=", page, re.IGNORECASE)


def test_every_link_points_at_an_existing_file_and_page(page: str) -> None:
    # arrange
    links = HREF.findall(page)
    # act / assert -- in-page anchors exist; file links resolve from build/; PDF pages are within the file
    assert len(links) > 1000
    for link in links:
        if link.startswith("#"):
            assert f'id="{link[1:]}"' in page, link
            continue
        target, _, fragment = unquote(link).partition("#")
        path = (BUILD / target).resolve()
        assert path.exists(), link
        if fragment:
            number = int(fragment.removeprefix("page="))
            assert 1 <= number <= pdf_pages(path), link


def test_every_topic_formula_and_question_is_listed(page: str) -> None:
    # arrange
    topics, formulas, exam_map = load_inventory()
    # act / assert -- one filterable entry per topic, formula and question
    assert len(topics) == len(json.loads(TOPICS.read_text(encoding="utf-8")))
    assert page.count("<li data-filter>") == len(topics)
    assert page.count('<div class="formula" data-filter>') == len(formulas)
    assert page.count("<div data-filter><h3>Q") == len(exam_map["questions"])
    for module in TOOL_SHEETS:
        assert f"<b>{html.escape(module.SHEET)}</b>" in page


def test_every_exam_calculator_maps_to_a_sheet() -> None:
    # arrange
    exam_map = json.loads(EXAM_MAP.read_text(encoding="utf-8"))
    sheets = {module.SHEET for module in TOOL_SHEETS}
    # act
    named = {c.strip() for q in exam_map["questions"] for c in (q.get("calculator") or "").split(";") if c.strip()}
    # assert
    assert named <= set(CALCULATOR_SHEETS)
    assert set(CALCULATOR_SHEETS.values()) <= sheets


def test_les_6_is_flagged(page: str) -> None:
    # act / assert -- decision 14
    assert NOT_FOR_EXAM == {"Les 6": "Niet te kennen voor het examen"}
    assert page.count('Les 6 <span class="flag">Niet te kennen voor het examen</span>') == 2
