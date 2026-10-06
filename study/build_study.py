"""Assemble study/studiegids.html: the offline study guide for the open-book exam.

Input: one fragment per part in study/parts/NN_slug.html plus NN_glossary.tsv, NN_formulas.tsv, NN_errata.tsv.
Output: a single self-contained HTML file (inline CSS and JavaScript, no external resources) with
- a table of contents grouped by part,
- a search box that matches Dutch and English: every query word is expanded with its translations from the glossary,
  results are listed and highlighted,
- interactive exercises (answer check with tolerance, hint and solution hidden in <details>),
- a Dutch↔English glossary, a formula sheet and a list of errors in the slides, all generated from the TSV files,
- clickable variables: every <var data-s="key"> in a formula opens a short explanation (what it is, how to get it)
  with a link to the section that explains it; the explanations come from NN_symbols.tsv,
- a collected list of the "Valkuilen en strikvragen" boxes (<div class="box pit">) of all parts.

The build validates what it assembles and stops on the first class of error: links to missing files or to pages
beyond a PDF's page count, duplicate ids, http(s) references, exercises without a solution, malformed TSV rows.
Run from the project root:  python3 study/build_study.py
"""
from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, unquote

STUDY = Path(__file__).resolve().parent
PARTS = STUDY / "parts"
OUTPUT = STUDY / "studiegids.html"
FRAGMENT = re.compile(r"^(\d\d)_(?!numbers).+\.html$")
sys.path.insert(0, str(STUDY.parent / "src"))

from bbtools.constants import USED_TABLE, load_all, load_average_range_table  # noqa: E402


def constants_data() -> dict[str, object]:
    """The constants the calculators use, as numbers: chart constants per decision 4 and the MSA d2 / d2* table.

    Same sources as the workbook (bbtools.constants): {"chart": {symbol: {n: value}}, "msa": {m, g, d2, d2star}}.
    """
    tables = {table.source.key: table for table in load_all()}
    chart: dict[str, dict[str, float]] = {}
    for symbol, key in USED_TABLE.items():
        column = tables[key].symbol_columns()[symbol]
        # rows with a numeric n and a printed number; 'over 25' rows print formulas such as 3/sqrt(n)
        chart[symbol] = {row[0].strip(): float(row[column]) for row in tables[key].rows
                         if row[0].strip().isdigit() and re.fullmatch(r"-?\d*\.?\d+", row[column].strip())}
    msa = load_average_range_table()
    return {"chart": chart,
            "msa": {"m": list(msa.m), "g": list(msa.g), "d2": [float(v) for v in msa.d2],
                    "d2star": [[float(v) for v in row] for row in msa.d2_star]}}


# ---------- "Hulpmiddelen" panels: calculators (assets/tools.js) and course tables, per part ----------

CONSTANTS_DIR = STUDY.parent / "inventory" / "constants"
DOCS = {  # short name -> PDF under source/course/
    "SPC": "Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf",
    "Ztable": "Les 4/___1.1 Ztable.pdf",
    "Excel": "Les 4/___1.2 statistische functionaliteit in excel.pdf",
    "tabellen SPC": "Les 4/___4.1 tabellen SPC.pdf",
    "Dummies": "Les 4/Six Sigma For Dummies.pdf",
    "H&S": "Les 4/Six-Sigma Mikel Harry -  Richard Schroeder.pdf",
    "CI FR": "Les 2/20260529_ottoy_Confidence Intervals - Further Reading (Dutch).pdf",
    "TR": "Les 2/20260529_ottoy_Test Recipes - Further Reading (Dutch).pdf",
    "TH FR": "Les 2/20260529_ottoy_Testing of Hypotheses - Further Reading (Dutch).pdf",
    "TH": "Les 2/20260529_ottoy_Testing of Hypotheses.pdf",
    "AS": "Les 2/20260529_ottoy_Acceptance Sampling.pdf",
    "AS FR": "Les 2/20260529_ottoy_Acceptance Sampling - Further Reading.pdf",
    "Naert L1": "Les 1/20260522_naert_big data.pdf",
    "Naert L2": "Les 2/20260529_naert.pdf",
    "REG": "Les 3/20260605_de vuyst_BB_Regression.pdf",
    "DOE": "Les 3/20260605_de vuyst_BB_DOE.pdf",
    "MSA": "Les 5/20260619_ottoy_Black Belt in Six Sigma - Measurement System Analysis.pdf",
    "tabel MSA": "Les 5/20260619_ottoy_tabel MSA.pdf",
}


@dataclass(frozen=True)
class Tool:
    """One entry of a Hulpmiddelen panel: title, search keywords, course pages, workbook sheet."""

    title: str
    keywords: str
    sources: tuple[tuple[str, int, str], ...]  # (DOCS key, first page to open, label)
    sheet: str = ""


TOOLS: dict[str, Tool] = {
    "normaal": Tool("Rekenmachine normale verdeling: µ, σ, x, z en kansen uit elkaar",
                    "normale verdeling; normal distribution; z-waarde; z-score; kans; probability; NORM.DIST; NORM.INV; "
                    "standaardnormaal; standard normal; staartkans; tail; rekenmachine; calculator",
                    (("SPC", 16, "SPC p. 16–19, 27"), ("Excel", 1, "Excel-functies p. 1–3")), "Normal"),
    "ztabel": Tool("Z-tabel van de cursus (met zoekfunctie)",
                   "Z-tabel; Z table; standaardnormale tabel; standard normal table; kans links van z",
                   (("Ztable", 1, "Ztable.pdf p. 1–2"),)),
    "sigma": Tool("Rekenmachine sigmaniveau, DPMO en yield",
                  "sigmaniveau; sigma level; DPMO; DPU; DPO; yield; RTY; rolled throughput yield; FTY; first-time yield; "
                  "verborgen fabriek; hidden factory; 1,5 sigma shift; verschuiving",
                  (("SPC", 20, "SPC p. 20–21, 37–40"), ("Dummies", 147, "Dummies p. 147–161"), ("H&S", 3, "Harry & Schroeder p. 3–5")),
                  "Sigma & DPMO"),
    "sigmatabellen": Tool("Sigmatabellen zoals gedrukt in de cursus",
                          "sigmatabel; sigma table; sigma scale; DPMO-tabel; sigma level table; Z DPMO",
                          ()),
    "kwantielen": Tool("Rekenmachine kritieke waarden en p-waarden (z, t, χ², F)",
                       "kritieke waarde; critical value; kwantiel; quantile; p-waarde; p-value; t-verdeling; t distribution; "
                       "chi-kwadraat; chi-square; F-verdeling; F distribution; T.INV; CHISQ.INV; F.INV",
                       (("TR", 4, "Test Recipes p. 4–14"),)),
    "dummiestabellen": Tool("t-, χ²- en F-tabellen van Six Sigma For Dummies",
                            "t-tabel; t table; chi-kwadraattabel; chi-square table; F-tabel; F table; Dummies",
                            (("Dummies", 192, "Dummies p. 192–196"),)),
    "gemiddelde": Tool("Rekenmachine één gemiddelde: BI en z- of t-toets",
                       "betrouwbaarheidsinterval gemiddelde; confidence interval mean; t-toets; t-test; z-toets; z-test; "
                       "eenzijdig; one-sided; tweezijdig; two-sided",
                       (("CI FR", 5, "CI Further Reading p. 5–8"), ("TR", 4, "Test Recipes p. 4"), ("TH FR", 10, "TH Further Reading p. 10–14")),
                       "Mean & proportion"),
    "tweegemiddelden": Tool("Rekenmachine twee gemiddelden: ongepaard (gepoold) en gepaard",
                            "twee gemiddelden; two means; gepaard; paired; ongepaard; unpaired; gepoolde variantie; pooled "
                            "variance; verschil; difference",
                            (("CI FR", 15, "CI Further Reading p. 15–19"), ("TR", 5, "Test Recipes p. 5–10")), "Mean & proportion"),
    "proportie": Tool("Rekenmachine proporties: BI (benaderd en exact) en Z-toets",
                      "proportie; proportion; fractie; fraction; Clopper-Pearson; exact; binomiaal; Z-toets; z-test; "
                      "twee proporties; two proportions",
                      (("CI FR", 20, "CI Further Reading p. 20"), ("Dummies", 197, "Dummies p. 197")), "Mean & proportion"),
    "variantie": Tool("Rekenmachine varianties: χ² (één σ) en F (twee σ's)",
                      "variantie; variance; standaardafwijking; standard deviation; chi-kwadraattoets; chi-square test; "
                      "F-toets; F-test; verhouding van varianties; variance ratio; nauwkeuriger; more precise",
                      (("CI FR", 21, "CI Further Reading p. 21"), ("TR", 11, "Test Recipes p. 11–14")), "Variance CI & tests"),
    "verdelingen": Tool("Rekenmachine kansverdelingen: Bernoulli, binomiaal, hypergeometrisch, Poisson, exponentieel, uniform",
                        "kansverdeling; probability distribution; binomiaal; binomial; hypergeometrisch; hypergeometric; "
                        "Poisson; exponentieel; exponential; uniform; Bernoulli; verwachtingswaarde; expected value",
                        (("AS", 12, "AS p. 12, 16, 20"), ("Naert L1", 5, "Naert Les 1 p. 5–10")), "Distributions"),
    "kruistabel": Tool("Rekenmachine kruistabel: gezamenlijke, marginale en voorwaardelijke kansen",
                       "kruistabel; contingency table; gezamenlijke kans; joint probability; marginale kans; marginal "
                       "probability; voorwaardelijke kans; conditional probability; onafhankelijk; independent",
                       (("Naert L1", 22, "Naert Les 1 p. 22–23"),)),
    "steekproefplan": Tool("Rekenmachine aanvaardingssteekproef: OC, α, β, AOQ, AOQL, ATI, plan voor variabelen",
                           "aanvaardingssteekproef; acceptance sampling; OC-curve; operating characteristic; AQL; LQL; LTPD; "
                           "producentenrisico; producer's risk; consumentenrisico; consumer's risk; AOQ; AOQL; ATI",
                           (("AS FR", 2, "AS Further Reading p. 2–10"), ("TH", 5, "TH p. 5–11")), "Acceptance sampling"),
    "regressie": Tool("Rekenmachine enkelvoudige lineaire regressie",
                      "regressie; regression; kleinste kwadraten; least squares; R²; helling; slope; intercept; "
                      "predictie-interval; prediction interval; betrouwbaarheidsinterval; confidence interval",
                      (("REG", 16, "REG p. 16–38"),), "ANOVA DOE regression"),
    "anova": Tool("Rekenmachine eenweg-ANOVA",
                  "ANOVA; variantieanalyse; analysis of variance; one-way; eenweg; F-toets; F-test; kwadratensom; sum of squares",
                  (("DOE", 3, "DOE p. 3–15"),), "ANOVA DOE regression"),
    "factorieel": Tool("Rekenmachine 2^k-factorieel: effecten, SS en F-toetsen",
                       "factorieel; factorial; 2^k; effect; interactie; interaction; contrast; poolen; pooling; DOE; "
                       "proefopzet; design of experiments",
                       (("DOE", 46, "DOE p. 46–79"),), "ANOVA DOE regression"),
    "aliassen": Tool("Rekenmachine fractioneel factorieel: generatoren, aliassen, resolutie",
                     "fractioneel; fractional factorial; alias; generator; resolutie; resolution; definiërende relatie; "
                     "defining relation; halve fractie; half fraction",
                     (("DOE", 80, "DOE p. 80–92"),)),
    "capabiliteit": Tool("Rekenmachine procescapabiliteit: Cp, Cpk, Pp, Ppk, % buiten specificatie",
                         "capabiliteit; capability; Cp; Cpk; Pp; Ppk; specificatie; specification; LSL; USL; ppm; uitval",
                         (("SPC", 33, "SPC p. 33–47"), ("tabellen SPC", 1, "tabellen SPC p. 1–2")), "Capability"),
    "regelkaart": Tool("Rekenmachine regelkaarten: X̄-R, X̄-s, I-MR, p, u",
                       "regelkaart; control chart; controlegrenzen; control limits; UCL; LCL; X-bar; R-kaart; s-kaart; "
                       "I-MR; individuals; p-kaart; p chart; u-kaart; u chart",
                       (("SPC", 62, "SPC p. 62–74"), ("Dummies", 249, "Dummies p. 249–254")), "Control charts"),
    "constanten": Tool("Constanten voor regelkaarten zoals gedrukt (Table 18, Table A, Six Sigma Demystified, Dummies)",
                       "constanten; constants; regelkaartconstanten; control chart constants; A2; D3; D4; d2; c4; B3; B4; E2; A3; Table 18; tabel",
                       (), "Tables"),
    "grr": Tool("Rekenmachine Gage R&R: gemiddelde-en-spreidingsbreedte en ANOVA",
                "Gage R&R; GRR; meetsysteemanalyse; measurement system analysis; MSA; herhaalbaarheid; repeatability; "
                "reproduceerbaarheid; reproducibility; EV; AV; PV; %GRR",
                (("MSA", 34, "MSA p. 34–37"), ("tabel MSA", 1, "tabel MSA.pdf")), "Gage R&R"),
    "msatabel": Tool("Tabel d2* (distribution of the average range) zoals gedrukt",
                     "d2*; d2 ster; d2 star; tabel MSA; average range; spreidingsbreedte",
                     (("tabel MSA", 1, "tabel MSA.pdf p. 1"),), "Tables"),
    "confusion": Tool("Rekenmachine confusion matrix: accuracy, recall, precision, F1",
                      "confusion matrix; verwarringsmatrix; accuracy; nauwkeurigheid; recall; precision; F1; overfitting; "
                      "underfitting; train; test",
                      (("Naert L2", 19, "Naert Les 2 p. 19–32"),), "Confusion matrix"),
}

PART_TOOLS: dict[str, tuple[str, ...]] = {
    "01": ("sigmatabellen",),
    "02": ("verdelingen", "kruistabel", "normaal", "ztabel"),
    "03": ("normaal", "ztabel", "sigma", "sigmatabellen"),
    "04": ("gemiddelde", "tweegemiddelden", "proportie", "variantie", "kwantielen", "dummiestabellen"),
    "05": ("gemiddelde", "tweegemiddelden", "proportie", "variantie", "kwantielen", "dummiestabellen"),
    "06": ("steekproefplan", "verdelingen", "normaal"),
    "07": ("regressie", "kwantielen"),
    "08": ("anova", "factorieel", "aliassen", "kwantielen"),
    "09": ("capabiliteit", "normaal", "ztabel", "sigma", "constanten"),
    "10": ("regelkaart", "constanten", "normaal"),
    "11": ("grr", "msatabel", "capabiliteit"),
    "12": ("confusion",),
    "13": ("variantie", "kwantielen", "capabiliteit", "normaal", "confusion", "verdelingen", "sigma"),
}


def pdf_link(doc: str, page: int, label: str) -> str:
    """Link to a page of a course PDF, relative to study/studiegids.html."""
    return f'<a class="p" href="../source/course/{quote(DOCS[doc], safe="/()")}#page={page}">{html.escape(label)}</a>'


def source_link(source_file: str, page: int, label: str) -> str:
    """Link to a page of any file under source/, given its repository path."""
    return f'<a class="p" href="../{quote(source_file, safe="/()")}#page={page}">{html.escape(label)}</a>'


def read_constant_csv(stem: str) -> tuple[list[str], list[list[str]], str, int, str]:
    """A transcribed course table: header, rows (printed strings), source file, page and title."""
    with (CONSTANTS_DIR / f"{stem}.csv").open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.reader(handle) if row]
    header, body = rows[0], rows[1:]
    width = len(header) - 3
    return header[:width], [row[:width] for row in body], body[0][width], int(body[0][width + 1]), body[0][width + 2]


def printed_table(stem: str, note: str = "") -> str:
    """One course table exactly as printed, with its source link."""
    header, rows, source_file, page, title = read_constant_csv(stem)
    head = "".join(f"<th>{html.escape(h)}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in rows)
    return (f'<p class="lbl">{html.escape(title)} — {source_link(source_file, page, Path(source_file).name + " p. " + str(page))}'
            f'</p>{note}<div class="scroll"><table class="out grid printed"><tr>{head}</tr>{body}</table></div>')


def z_table() -> str:
    """The course Z table (Ztable.pdf p. 1-2) with data-z on every cell for the lookup in tools.js."""
    parts = []
    for stem in ("S06_standard_normal_probabilities_table_entry_area_to_the_left_o",
                 "S06_standard_normal_probabilities_table_entry_area_to_the_left_o_2"):
        header, rows, source_file, page, title = read_constant_csv(stem)
        lines = []
        for row in rows:
            cells = []
            for column, cell in zip(header[1:], row[1:]):
                z = float(row[0]) - float(column) if row[0].startswith("-") else float(row[0]) + float(column)
                key = f"{z:.2f}" if not (row[0].startswith("-") and z == 0) else "-0.00"
                cells.append(f'<td data-z="{key}">{html.escape(cell)}</td>')
            lines.append(f"<tr><th>{html.escape(row[0])}</th>{''.join(cells)}</tr>")
        head = "".join(f"<th>{html.escape(h)}</th>" for h in header)
        parts.append(f'<p class="lbl">{html.escape(title)} — {source_link(source_file, page, "Ztable.pdf p. " + str(page))}</p>'
                     f'<div class="scroll"><table class="out grid printed ztab"><tr>{head}</tr>{"".join(lines)}</table></div>')
    return "".join(parts)


def chart_constants() -> str:
    """Every control-chart constant table as printed, with the table each calculator uses (decision 4)."""
    blocks = []
    for table in load_all():
        used = sorted(symbol for symbol, key in USED_TABLE.items() if key == table.source.key)
        head = "".join(f"<th>{html.escape(c)}</th>" for c in table.columns)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in table.rows)
        role = f"De rekenmachines gebruiken hieruit: {', '.join(used)}." if used else "Ter referentie."
        blocks.append(f'<p class="lbl">{html.escape(table.title)} — '
                      f'{source_link(table.source_file, table.source_page, Path(table.source_file).name + " p. " + str(table.source_page))}'
                      f'</p><p class="help">{role} Bron: {html.escape(table.source.origin)}.</p>'
                      f'<div class="scroll"><table class="out grid printed"><tr>{head}</tr>{body}</table></div>')
    return ('<p class="help">Beslissing 4: Table 18 eerst (de oefenwerkboeken van de docent gebruiken die waarden), c4 en d3 uit '
            'Table A, A3, E2, B5 en B6 uit Six Sigma Demystified. Kleine verschillen tussen de tabellen staan in '
            'build/README.md.</p>' + "".join(blocks))


def msa_table() -> str:
    """The d2* table of tabel MSA.pdf as printed: every cell shows ν over d2*."""
    msa = load_average_range_table()
    head = "<th>g \\ m</th>" + "".join(f"<th>{m}</th>" for m in msa.m)
    body = "".join(f"<tr><th>{g}</th>" + "".join(f"<td>{nu}<br>{d}</td>" for nu, d in zip(msa.nu[i], msa.d2_star[i])) + "</tr>"
                   for i, g in enumerate(msa.g))
    body += "<tr><th>d2 (g → ∞)<br>cd</th>" + "".join(f"<td>{d}<br>{c}</td>" for d, c in zip(msa.d2, msa.cd)) + "</tr>"
    return (f'<p class="lbl">{html.escape(msa.title)} — {source_link(msa.source_file, msa.source_page, "tabel MSA.pdf p. 1")}</p>'
            '<p class="help">Elke cel: bovenaan ν (vrijheidsgraden), onderaan d2*. g = aantal subgroepen, m = subgroepgrootte. '
            'De Gage R&amp;R-rekenmachine neemt d2 uit de laatste rij (m = r) en d2* uit de rij g = 1 (m = k en m = n), '
            'zoals het werkboek van de cursus.</p>'
            f'<div class="scroll"><table class="out grid printed msa"><tr>{head}</tr>{body}</table></div>')


def templates() -> str:
    """<template> elements with the static tables; tools.js copies them into a panel when it is opened."""
    sigma = "".join(printed_table(stem) for stem in (
        "S06_voc_vs_vop_sigma_capability_defects_per_million_opportunitie",
        "S01_sigma_level_defects_per_million_yield_tabel",
        "S07_table_1_2_the_sigma_scale",
        "S08_table_6_3_sigma_score_table_z_dpmo"))
    sigma = ('<p class="help">Alle tabellen rekenen met de 1,5σ-verschuiving (beslissing 3). 2σ: de slides en Harry &amp; '
             'Schroeder drukken 308,537 en Van Volsem 308,000; correct afgerond is 308 538.</p>' + sigma)
    dummies = ('<p class="calc-warn">Let op: Dummies noemt "95 %" wat ±2σ is (95,45 %, 2,275 % per staart) bij de χ²-tabel, '
               'en een rechterstaart van 5 % bij de F-tabel; de kolommen staan per n, niet per vrijheidsgraden. Gebruik voor '
               'de oefeningen van Ottoy de rekenmachine voor kritieke waarden.</p>' + "".join(printed_table(stem) for stem in (
                   "S08_table_8_1_t_values", "S08_table_8_2_chi_square_values", "S08_table_8_3_f_values_for_95_confidence")))
    content = {"ztabel": z_table(), "sigmatabellen": sigma, "dummiestabellen": dummies, "constanten": chart_constants(),
               "msatabel": msa_table()}
    return "\n".join(f'<template id="tpl-{name}">{body}</template>' for name, body in content.items())


def tools_panel(number: str) -> str:
    """The Hulpmiddelen dropdown of one part."""
    items = []
    for name in PART_TOOLS.get(number, ()):
        tool = TOOLS[name]
        links = " · ".join(pdf_link(doc, page, label) for doc, page, label in tool.sources)
        sheet = f' · werkblad <i>{html.escape(tool.sheet)}</i>' if tool.sheet else ""
        items.append(f'<details class="tool" id="tool-d{number}-{name}" data-tool="{name}" data-kw="{html.escape(tool.keywords)}">'
                     f'<summary>{html.escape(tool.title)}</summary><p class="src">{links}{sheet}</p>'
                     '<div class="tool-body"></div></details>')
    if not items:
        return ""
    return (f'<details class="tools" id="tools-d{number}"><summary>Hulpmiddelen bij dit deel: rekenmachines en tabellen</summary>'
            '<p class="help">Gele velden invullen (komma of punt), groene resultaten verschijnen meteen. Lijsten: getallen '
            'gescheiden door spaties, tabs of nieuwe regels; je kunt kolommen uit Excel plakken. De rekenmachines gebruiken '
            'dezelfde formules als <code>build/bb_toolkit.xlsx</code>.</p>' + "".join(items) + "</details>")


def with_tools(part_html: str, number: str) -> str:
    """Insert the part's Hulpmiddelen panel after its title and introduction."""
    panel = tools_panel(number)
    if not panel:
        return part_html
    match = re.search(r"</h2>\s*(<p class=\"intro\">.*?</p>)?", part_html, re.S)
    if not match:
        raise ValueError(f"part {number}: no <h2> to place the Hulpmiddelen panel after")
    return part_html[:match.end()] + "\n" + panel + part_html[match.end():]


@dataclass(frozen=True)
class Part:
    """One assembled part: number, title, lecturer, lesson and its HTML fragment."""

    number: str
    title: str
    lecturer: str
    lesson: str
    html: str


def read_tsv(path: Path, header: list[str]) -> list[dict[str, str]]:
    """Rows of a part's TSV file; the header must match exactly."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows or [c.strip() for c in rows[0]] != header:
        raise ValueError(f"{path.name}: header must be {header}, found {rows[0] if rows else 'nothing'}")
    out = []
    for i, row in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in row):
            continue
        if len(row) != len(header):
            raise ValueError(f"{path.name} line {i}: {len(row)} fields, expected {len(header)}")
        out.append({k: v.strip() for k, v in zip(header, row)})
    return out


def load_parts() -> list[Part]:
    """All fragments in part order."""
    parts = []
    for path in sorted(PARTS.iterdir()):
        match = FRAGMENT.match(path.name)
        if not match:
            continue
        text = path.read_text(encoding="utf-8")
        head = re.search(r'<section class="part" id="d(\d\d)"([^>]*)>', text)
        if not head or head.group(1) != match.group(1):
            raise ValueError(f"{path.name}: must start with <section class=\"part\" id=\"d{match.group(1)}\" …>")
        attrs = dict(re.findall(r'data-(\w+)="([^"]*)"', head.group(2)))
        parts.append(Part(match.group(1), html.unescape(attrs.get("title", "")), attrs.get("lecturer", ""),
                          attrs.get("les", ""), text))
    return parts


def toc(parts: list[Part]) -> str:
    """Navigation: parts with their units."""
    lines = ['<a href="#zoek-resultaten" class="l1" id="toc-top">Zoeken ↑</a>']
    for part in parts:
        lines.append(f'<a class="l1" href="#d{part.number}">{html.escape(part.title)}</a>')
        if PART_TOOLS.get(part.number):
            lines.append(f'<a class="l2 tools" href="#tools-d{part.number}">Hulpmiddelen: rekenmachines en tabellen</a>')
        for unit_id, title in re.findall(r'<section class="unit" id="([^"]+)"[^>]*>\s*<h3>(.*?)</h3>', part.html, re.S):
            label = re.sub(r"<a class=\"p\".*?</a>", "", title, flags=re.S)
            label = re.sub(r"<[^>]+>", "", label).strip()
            lines.append(f'<a class="l2" href="#{unit_id}">{html.escape(html.unescape(label))}</a>')
    for anchor, title in (("woordenlijst", "Woordenlijst NL ↔ EN"), ("formuleblad", "Formuleblad"),
                          ("valkuilen", "Valkuilen en strikvragen"),
                          ("fouten", "Fouten in de slides")):
        lines.append(f'<a class="l1" href="#{anchor}">{title}</a>')
    return "\n".join(lines)


def glossary(parts: list[Part]) -> tuple[str, list[list[str]]]:
    """Glossary section (sorted by Dutch term) and the NL/EN pairs used for search expansion."""
    rows, seen = [], set()
    for part in parts:
        for row in read_tsv(PARTS / f"{part.number}_glossary.tsv", ["nl", "en", "anchor"]):
            key = (row["nl"].lower(), row["en"].lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda r: r["nl"].lower())
    body = "".join(
        f'<tr data-kw="{html.escape(r["nl"])}; {html.escape(r["en"])}"><td>{html.escape(r["nl"])}</td>'
        f'<td>{html.escape(r["en"])}</td><td><a href="#{html.escape(r["anchor"])}">uitleg</a></td></tr>'
        for r in rows)
    section = ('<section class="part" id="woordenlijst"><h2>Woordenlijst Nederlands ↔ English</h2>'
               '<p class="intro">Elke term met de uitleg in de gids. De zoekfunctie gebruikt deze lijst om in beide '
               'talen te zoeken.</p><table class="gloss"><tr><th>Nederlands</th><th>English</th><th></th></tr>'
               f"{body}</table></section>")
    return section, [[r["nl"], r["en"]] for r in rows]


SYMBOL_HEADER = ["key", "symbool", "betekenis", "hoe", "anchor"]
VAR = re.compile(r'<var data-s="([^"]*)">')


def symbols(parts: list[Part]) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Every part's symbol dictionary (NN_symbols.tsv), keyed 'NN:key', and the problems found in those files."""
    table: dict[str, dict[str, str]] = {}
    problems = []
    for part in parts:
        try:
            rows = read_tsv(PARTS / f"{part.number}_symbols.tsv", SYMBOL_HEADER)
        except ValueError as error:  # one broken file must not hide the problems of the other parts
            problems.append(f"part {part.number}: {error}")
            continue
        for row in rows:
            key = f"{part.number}:{row['key']}"
            if not re.fullmatch(r"[a-z0-9_]+", row["key"]) or key in table or not all(row.values()):
                problems.append(f"part {part.number}: {part.number}_symbols.tsv row {row['key']!r}: bad or duplicate key, "
                                "or an empty field")
                continue
            table[key] = row
    return table, problems


def qualify(text: str, number: str) -> str:
    """Give every <var data-s="key"> of part `number` its part prefix (data-s="NN:key"); 'MM:key' stays as written."""
    return VAR.sub(lambda m: f'<var data-s="{m.group(1) if ":" in m.group(1) else number + ":" + m.group(1)}">', text)


def anchor_titles(page: str) -> dict[str, str]:
    """Readable title of every part, unit, exercise and tool id: the text of its h2, h3, h4 or summary."""
    titles = {}
    for match in re.finditer(r'<(section|div|details) class="(?:part|unit|exercise|tool|tools)"[^>]*\sid="([^"]+)"[^>]*>\s*'
                             r'<(h2|h3|h4|summary)>(.*?)</\3>', page, re.S):
        text = re.sub(r'<a class="p".*?</a>', "", match.group(4), flags=re.S)
        titles[match.group(2)] = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
    return titles


def symbols_data(table: dict[str, dict[str, str]], page: str) -> dict[str, dict[str, str]]:
    """What the page embeds for the variable pop-ups: symbol, meaning, how to get it, link and its title."""
    titles = anchor_titles(page)
    return {key: {"s": row["symbool"], "b": row["betekenis"], "h": row["hoe"], "a": row["anchor"],
                  "t": titles.get(row["anchor"], row["anchor"])} for key, row in table.items()}


PIT = re.compile(r'<div class="box pit">(.*?)</div>', re.S)


def pitfalls(parts: list[Part]) -> str:
    """All "Valkuilen en strikvragen" boxes, per part and unit, each with a link back to its unit."""
    blocks = []
    for part in parts:
        units = []
        for unit_id, body in re.findall(r'<section class="unit" id="([^"]+)"[^>]*>(.*?)</section>', part.html, re.S):
            boxes = PIT.findall(body)
            if not boxes:
                continue
            title = re.search(r"<h3>(.*?)</h3>", body, re.S)
            label = re.sub(r"<[^>]+>", "", re.sub(r'<a class="p".*?</a>', "", title.group(1), flags=re.S)).strip() if title else unit_id
            items = "".join(re.sub(r'<span class="t">.*?</span>', "", box, count=1, flags=re.S) for box in boxes)
            units.append(f'<h4><a href="#{unit_id}">{label}</a></h4>{qualify(items, part.number)}')
        if units:
            blocks.append(f"<h3>{html.escape(part.title)}</h3>" + "".join(units))
    return ('<section class="part" id="valkuilen"><h2>Valkuilen en strikvragen</h2><p class="intro">Alle valkuilen uit de '
            'delen samen, om snel na te lopen voor een strikvraag. Klik de titel voor de uitleg.</p>'
            + "".join(blocks) + "</section>")


def formula_sheet(parts: list[Part]) -> str:
    """Formula sheet grouped by part."""
    blocks = []
    for part in parts:
        rows = read_tsv(PARTS / f"{part.number}_formulas.tsv", ["wat", "formule_html", "bron", "href"])
        if not rows:
            continue
        body = "".join(f'<tr data-kw="{html.escape(r["wat"])}"><td>{html.escape(r["wat"])}</td><td>{qualify(r["formule_html"], part.number)}</td>'
                       f'<td><a class="p" href="{html.escape(r["href"])}">{html.escape(r["bron"])}</a></td></tr>'
                       for r in rows)
        blocks.append(f'<h3>{html.escape(part.title)}</h3><table><tr><th>Wat</th><th>Formule</th><th>Bron</th></tr>'
                      f"{body}</table>")
    return '<section class="part" id="formuleblad"><h2>Formuleblad</h2>' + "".join(blocks) + "</section>"


def errata(parts: list[Part]) -> str:
    """Printed course values that disagree with a computation, per part."""
    body = []
    for part in parts:
        for r in read_tsv(PARTS / f"{part.number}_errata.tsv", ["bron", "href", "gedrukt", "correct", "toelichting"]):
            body.append(f'<tr data-kw="fout; erratum; error; {html.escape(r["bron"])}"><td>{html.escape(part.title)}</td>'
                        f'<td><a class="p" href="{html.escape(r["href"])}">{html.escape(r["bron"])}</a></td>'
                        f'<td>{html.escape(r["gedrukt"])}</td><td>{html.escape(r["correct"])}</td>'
                        f'<td>{html.escape(r["toelichting"])}</td></tr>')
    return ('<section class="part" id="fouten"><h2>Fouten in de slides</h2><p class="intro">Gedrukte waarden die niet '
            'kloppen met een herberekening van de eigen gegevens van de cursus. Gebruik de correcte waarde.</p>'
            '<table><tr><th>Deel</th><th>Bron</th><th>Gedrukt</th><th>Correct</th><th>Toelichting</th></tr>'
            + "".join(body) + "</table></section>")


@lru_cache(maxsize=None)
def pdf_pages(path: Path) -> int:
    """Number of pages of a PDF (pdfinfo)."""
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if not match:
        raise ValueError(f"cannot read the page count of {path}")
    return int(match.group(1))


def validate(page: str, table: dict[str, dict[str, str]]) -> list[str]:
    """Problems in the assembled page (empty list = fine)."""
    problems = []
    if re.search(r"https?:", page, re.I):
        problems += [f"external reference: …{m.group(0)}…" for m in re.finditer(r".{30}https?:.{30}", page, re.I)][:5]
    ids = re.findall(r'\sid="([^"]+)"', page)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"duplicate ids: {dupes[:20]}")
    idset = set(ids)
    for href in re.findall(r'href="([^"]+)"', page.split("<!--APP-->")[0]):  # content only, not the scripts
        if href.startswith("#"):
            if href[1:] not in idset:
                problems.append(f"anchor without target: {href}")
            continue
        target, _, fragment = unquote(html.unescape(href)).partition("#")
        path = (STUDY / target).resolve()
        if not path.exists():
            problems.append(f"missing file: {href}")
        elif fragment:
            if not fragment.startswith("page=") or not fragment[5:].isdigit():
                problems.append(f"bad fragment: {href}")
            elif not 1 <= int(fragment[5:]) <= pdf_pages(path):
                problems.append(f"page out of range: {href}")
    for exercise in re.findall(r'<div class="exercise".*?(?=<div class="exercise"|</section>)', page, re.S):
        ex_id = re.search(r'id="([^"]+)"', exercise).group(1)
        if 'class="solution"' not in exercise:
            problems.append(f"exercise without solution: {ex_id}")
        for answer in re.findall(r'<div class="q"([^>]*)>', exercise):
            if 'data-type="choice"' in answer:
                continue
            value = re.search(r'data-answer="([^"]*)"', answer)
            if not value or not re.fullmatch(r"-?\d+(\.\d+)?([eE]-?\d+)?", value.group(1)):
                problems.append(f"numeric answer not a number in {ex_id}: {answer.strip()}")
    if re.search(r"<script(?! id=\"app\")", page.split("<!--APP-->")[0]):
        problems.append("a fragment contains <script>")
    content = page.split("<!--APP-->")[0]
    if re.search(r'<var(?! data-s=")', content):
        problems.append(f"<var> without data-s: …{re.search(r'.{40}<var(?! data-s=).{40}', content, re.S).group(0)}…")
    for key in sorted(set(VAR.findall(content)) - set(table)):
        problems.append(f"part {key.split(':')[0]}: unknown symbol key {key!r} (not in its NN_symbols.tsv)")
    for key, row in table.items():
        if row["anchor"] not in idset:
            problems.append(f"part {key.split(':')[0]}: symbol {key!r} links to missing anchor #{row['anchor']}")
    for box in re.findall(r'<div class="box pit">(.*?)</div>', content, re.S):
        if "<div" in box or 'id="' in box:
            problems.append(f"a pitfall box contains a <div> or an id: {box[:80]}…")
    return problems


def div_blocks(text: str, opening: str) -> list[str]:
    """Every element that starts with `opening` (a <div …> tag), up to its matching </div>, nested divs included."""
    blocks = []
    for start in (m.start() for m in re.finditer(re.escape(opening), text)):
        depth, position = 0, start
        for tag in re.finditer(r"<div\b|</div>", text[start:]):
            depth += 1 if tag.group(0) == "<div" else -1
            if depth == 0:
                position = start + tag.end()
                break
        blocks.append(text[start:position])
    return blocks


def coverage(page: str) -> dict[str, int]:
    """Per part: formula blocks (<div class="f">) that contain no clickable variable."""
    missing: dict[str, int] = {}
    for part_id, body in re.findall(r'<section class="part" id="d(\d\d)".*?>(.*?)(?=<section class="part"|<!--APP-->)', page, re.S):
        for block in div_blocks(body, '<div class="f">'):
            if "<var" not in block:
                missing[part_id] = missing.get(part_id, 0) + 1
    return missing


def render(parts: list[Part], table: dict[str, dict[str, str]]) -> str:
    """The complete page."""
    gloss_html, pairs = glossary(parts)
    css = (STUDY / "assets" / "studiegids.css").read_text(encoding="utf-8")
    js = "\n".join((STUDY / "assets" / name).read_text(encoding="utf-8")
                   for name in ("stats.js", "calc.js", "studiegids.js", "tools.js"))
    body = "\n".join(with_tools(qualify(p.html, p.number), p.number) for p in parts)
    page = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Studiegids Black Belt</title>
<style>{css}</style>
</head>
<body>
<header id="topbar">
  <span class="brand">Studiegids Black Belt</span>
  <input id="q" type="search" placeholder="Zoek (NL of EN): betrouwbaarheidsinterval, confidence interval, Cpk, regelkaart…" autocomplete="off">
  <span id="hits"></span>
  <button type="button" id="clear">Wis</button>
</header>
<div class="wrap">
<nav id="toc">
{toc(parts)}
</nav>
<main>
<section id="zoek-resultaten" hidden><h2>Zoekresultaten</h2><ol id="results"></ol></section>
{body}
{gloss_html}
{formula_sheet(parts)}
{pitfalls(parts)}
{errata(parts)}
</main>
</div>
{templates()}
<!--APP-->
<script id="constants-data" type="application/json">{json.dumps(constants_data())}</script>
<script id="glossary-data" type="application/json">{json.dumps(pairs, ensure_ascii=False).replace("</", "<\\/")}</script>
<script id="symbols-data" type="application/json">@SYMBOLS@</script>
<script id="app">{js}</script>
</body>
</html>
"""
    data = json.dumps(symbols_data(table, page), ensure_ascii=False).replace("</", "<\\/")
    return page.replace("@SYMBOLS@", data, 1)


def main() -> None:
    """Build, validate and write the study guide; with --check, validate only (nothing is written)."""
    parts = load_parts()
    if not parts:
        sys.exit("no parts found in study/parts")
    table, problems = symbols(parts)
    page = render(parts, table)
    problems += validate(page, table)
    if problems:
        print("\n".join(problems))
        sys.exit(f"{len(problems)} problem(s); {OUTPUT.name} not written")
    gaps = coverage(page)
    print(f"{len(table)} symbols; formula blocks without a clickable variable: "
          + (", ".join(f"Deel {k}: {v}" for k, v in sorted(gaps.items())) or "none"))
    if "--check" in sys.argv:
        print("check only: no problems")
        return
    OUTPUT.write_text(page, encoding="utf-8", newline="\n")
    exercises = page.count('<div class="exercise"')
    words = len(re.sub(r"<[^>]+>", " ", page.split("<!--APP-->")[0]).split())
    print(f"{OUTPUT}: {len(parts)} parts, {exercises} exercises, {words} words, "
          f"{len(re.findall(r'href=\"[.][.]/', page))} slide links")


if __name__ == "__main__":
    main()
