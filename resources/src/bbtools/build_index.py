"""Generate build/index.html: the offline exam-time index into the course material.

One static file with no external resources (inline CSS and a few lines of inline JavaScript for the filter box;
without JavaScript everything stays visible). Sections: the calculator sheets of build/bb_toolkit.xlsx, the
example-exam question map, topics per module with links to their PDF pages, and every formula with its source
page. Links are relative to build/ ('../source/...pdf#page=N'), so the index keeps working wherever the project
folder is copied, as long as source/ sits next to build/. Les 6 carries the flag of decision 14.

Everything comes from inventory/ (topic_index.json, raw/S*.json formulas, exam_map.json) and the sheet modules'
headers, so the index cannot drift from them.

Run: python3 -m bbtools.build_index   (from the project root, with src/ on PYTHONPATH)
"""
from __future__ import annotations

import os
import html
import json
from itertools import groupby
from pathlib import Path
from urllib.parse import quote

from bbtools import sheet_capability, sheet_confusion, sheet_distributions, sheet_normal, sheet_variance
from bbtools.build_workbook import OUTPUT as WORKBOOK
from bbtools.build_workbook import TOOL_SHEETS
from bbtools.constants import ROOT
from bbtools.merge_inventory import load_slices, module_of, ordered, tagged

INDEX = ROOT / "build" / "index.html"
TOPICS = ROOT / "inventory" / "topic_index.json"
EXAM_MAP = ROOT / "inventory" / "exam_map.json"
NOT_FOR_EXAM = {"Les 6": "Niet te kennen voor het examen"}  # decision 14
# exam_map.json names calculators by their proposed-tool id; these are the sheets that implement them.
CALCULATOR_SHEETS = {
    "ci-variance-ratio-f": sheet_variance.SHEET,
    "capability-normal": sheet_capability.SHEET,
    "confusion-matrix-metrics": sheet_confusion.SHEET,
    "normal-probability": sheet_normal.SHEET,
    "distribution-moments": sheet_distributions.SHEET,
}

STYLE = """
body { font-family: Arial, Helvetica, sans-serif; font-size: 14px; margin: 0 auto; max-width: 1100px; padding: 0 16px 48px;
       color: #1a1a1a; background: #fff; }
nav { position: sticky; top: 0; background: #fff; border-bottom: 1px solid #ccc; padding: 8px 0; z-index: 1; }
nav a { margin-right: 16px; font-weight: bold; }
input { font-size: 14px; padding: 4px 8px; width: 320px; margin-left: 8px; }
h1 { font-size: 22px; } h2 { font-size: 18px; margin-top: 32px; border-bottom: 2px solid #1f4e79; }
h3 { font-size: 16px; margin-bottom: 4px; } h4 { font-size: 14px; margin: 12px 0 4px; color: #444; }
a { color: #1f4e79; } table { border-collapse: collapse; width: 100%; table-layout: fixed; }
th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; vertical-align: top; overflow-wrap: break-word; }
col.sheet { width: 18%; } col.tool { width: 28%; } col.source { width: 39%; } col.status { width: 15%; }
th { background: #d9e1f2; } ul { margin: 4px 0; padding-left: 20px; } li { margin: 2px 0; }
pre { background: #f4f4f4; padding: 4px 8px; margin: 4px 0; white-space: pre-wrap; font-size: 13px; }
.flag { color: #c00000; font-weight: bold; } .note { color: #555; font-size: 12px; }
.formula { border-top: 1px solid #eee; padding: 4px 0; }
"""

FILTER_SCRIPT = """
function filterIndex(q) {
  q = q.toLowerCase();
  document.querySelectorAll('[data-filter]').forEach(function (el) {
    el.style.display = el.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
  });
}
"""


def e(text: object) -> str:
    """HTML-escaped text."""
    return html.escape(str(text))


def href(file: str, page: int | None = None) -> str:
    """Relative link from build/ to a course file, with '#page=N' for PDF pages."""
    target = "../" + quote(file)
    return f"{target}#page={page}" if page and file.lower().endswith(".pdf") else target


def page_links(file: str, pages: list[int]) -> str:
    """'p. 3, 6, 7' with each page a link into the PDF."""
    return "p. " + ", ".join(f'<a href="{href(file, p)}">{p}</a>' for p in pages)


def source_link(item: dict) -> str:
    """Link to a formula's source: file name plus page, or the spreadsheet and sheet."""
    name = Path(item["file"]).name
    if item.get("sheet"):
        return f'<a href="{href(item["file"])}">{e(name)}</a>, sheet \'{e(item["sheet"])}\''
    notes = " (speaker notes)" if item.get("notes") else ""
    return f'<a href="{href(item["file"], item.get("page"))}">{e(name)} p. {e(item.get("page"))}</a>{notes}'


def module_heading(module: str) -> str:
    """Module heading, with the decision-14 flag where it applies."""
    flag = f' <span class="flag">{e(NOT_FOR_EXAM[module])}</span>' if module in NOT_FOR_EXAM else ""
    return f"<h3>{e(module)}{flag}</h3>"


def calculators_section() -> str:
    """Table of the workbook's calculator sheets with their course sources and status."""
    rows = "".join(
        f"<tr><td><b>{e(m.SHEET)}</b></td><td>{e(m.HEADER.tool)}</td><td>{e(m.HEADER.source)}</td>"
        f"<td>{e(m.HEADER.status.value)}</td></tr>" for m in TOOL_SHEETS)
    workbook = Path(os.path.relpath(WORKBOOK, INDEX.parent)).as_posix()
    return (f'<h2 id="calculators">Calculators</h2><p>Workbook: <a href="{workbook}">{WORKBOOK.name}</a> '
            f"(one sheet per tool; yellow = input, green = result). Details per sheet: README.md.</p>"
            f'<table><colgroup><col class="sheet"><col class="tool"><col class="source"><col class="status"></colgroup>'
            f"<tr><th>Sheet</th><th>Tool</th><th>Course source</th><th>Status</th></tr>{rows}</table>")


def exam_section(exam_map: dict) -> str:
    """The example-exam questions with their course pages and the calculator sheet to use."""
    exam = exam_map["exam"]
    parts = [f'<h2 id="exam">Example exam: question map</h2><p><a href="{href(exam["file"])}">{e(exam["title_as_printed"])}'
             f"</a> ({e(exam['questions'])} questions, {e(exam['total_points'])} points; no answer key).</p>"]
    for q in exam_map["questions"]:
        pages = "".join(f"<li>{page_links(c['file'], c['pages'])} of {e(Path(c['file']).name)}: {e(c['why'])}</li>"
                        for c in q["course_pages"])
        calculators = [c.strip() for c in (q.get("calculator") or "").split(";") if c.strip()]
        sheet = ", ".join(e(CALCULATOR_SHEETS[c]) for c in calculators) or "none (conceptual)"
        parts.append(
            f'<div data-filter><h3>Q{e(q["q"])} ({e(q["points"])} points, {e(q["type"])}; '
            f'exam {page_links(exam["file"], q["exam_pages"])})</h3><p>{e(q["summary"])}</p>'
            f"<p><b>Calculator sheet:</b> {sheet}</p><p><b>Topics:</b> {e('; '.join(q['topics']))}</p>"
            f"<ul>{pages}</ul></div>")
    return "".join(parts)


def topics_section(topics: list[dict]) -> str:
    """Topics grouped by module and file (one list per file), each with its page links."""
    parts, module = ['<h2 id="topics">Topics</h2>'], None
    for (topic_module, file), group in groupby(topics, key=lambda t: (t["module"], t["file"])):
        if topic_module != module:
            module = topic_module
            parts.append(module_heading(module))
        items = "".join(f'<li data-filter>{e(t["topic"])}: {page_links(file, t["pages"])}</li>' for t in group)
        parts.append(f'<h4><a href="{href(file)}">{e(Path(file).name)}</a></h4><ul>{items}</ul>')
    return "".join(parts)


def formulas_section(formulas: list[dict]) -> str:
    """Every formula in the course's notation, grouped by module, with its source link."""
    parts, module = ['<h2 id="formulas">Formulas</h2>'], None
    for f in formulas:
        if module_of(f["file"]) != module:
            module = module_of(f["file"])
            parts.append(module_heading(module))
        symbols = "; ".join(f"{e(s)}: {e(m)}" for s, m in (f.get("symbols") or {}).items())
        conditions = f"<br>Conditions: {e(f['conditions'])}" if f.get("conditions") else ""
        parts.append(f'<div class="formula" data-filter><b>{e(f["name"])}</b> ({source_link(f)})'
                     f'<pre>{e(f["expression"])}</pre><span class="note">{symbols}{conditions}</span></div>')
    return "".join(parts)


def render(topics: list[dict], formulas: list[dict], exam_map: dict) -> str:
    """The complete index page."""
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Black Belt course index</title>'
        f"<style>{STYLE}</style><script>{FILTER_SCRIPT}</script></head><body>"
        "<h1>Six Sigma Black Belt: course index</h1>"
        '<p class="note">Offline index generated from inventory/ by src/bbtools/build_index.py. Page links open the '
        "course PDF at that page (#page=N) in browsers whose PDF viewer supports it; test them on the exam laptop.</p>"
        '<nav><a href="#calculators">Calculators</a><a href="#exam">Exam questions</a><a href="#topics">Topics</a>'
        '<a href="#formulas">Formulas</a>Filter:<input type="search" oninput="filterIndex(this.value)" '
        'placeholder="e.g. Cpk, ANOVA, Poisson"></nav>'
        f"{calculators_section()}{exam_section(exam_map)}{topics_section(topics)}{formulas_section(formulas)}"
        "</body></html>\n"
    )


def load_inventory() -> tuple[list[dict], list[dict], dict]:
    """Topics, formulas (ordered like the course) and the exam map from inventory/."""
    topics = json.loads(TOPICS.read_text(encoding="utf-8"))
    formulas = ordered(tagged(load_slices(), "formulas"))
    exam_map = json.loads(EXAM_MAP.read_text(encoding="utf-8"))
    return topics, formulas, exam_map


def write_index(path: Path = INDEX) -> Path:
    """Write the index page and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(*load_inventory()), encoding="utf-8", newline="\n")
    return path


def main() -> None:
    """Build build/index.html."""
    print(f"{write_index()}: written")


if __name__ == "__main__":
    main()
