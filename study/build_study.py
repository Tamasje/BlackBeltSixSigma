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

import base64
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
FIGURES = STUDY / "figures"
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
                    "d2star": [[float(v) for v in row] for row in msa.d2_star],
                    "nu": [[float(v) for v in row] for row in msa.nu]}}


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
    "Data": "Les 1/20260522_naert_big data.pdf",
    "ML": "Les 2/20260529_naert.pdf",
    "CI": "Les 2/20260529_ottoy_Confidence Intervals.pdf",
    "LSS": "Les 1/20260521_van volsem.pdf",
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
                    (("SPC", 16, "SPC p. 16–19, 27"), ("Excel", 1, "Excel-functies p. 1–3")), "Normaal"),
    "ztabel": Tool("Z-tabel van de cursus (met zoekfunctie)",
                   "Z-tabel; Z table; standaardnormale tabel; standard normal table; kans links van z",
                   (("Ztable", 1, "Ztable.pdf p. 1–2"),)),
    "sigma": Tool("Rekenmachine sigmaniveau, DPO en DPMO",
                  "sigmaniveau; sigma level; DPMO; DPO; defecten per kans; defects per opportunity; yield; "
                  "1,5 sigma shift; verschuiving",
                  (("SPC", 20, "SPC p. 20–21, 37–40"),),
                  "Sigma & DPMO"),
    "sigmatabellen": Tool("Sigmatabellen zoals gedrukt in de cursus",
                          "sigmatabel; sigma table; sigma scale; DPMO-tabel; sigma level table; Z DPMO",
                          ()),
    "kwantielen": Tool("Rekenmachine kritieke waarden en p-waarden (z, t, χ², F)",
                       "kritieke waarde; critical value; kwantiel; quantile; p-waarde; p-value; t-verdeling; t distribution; "
                       "chi-kwadraat; chi-square; F-verdeling; F distribution; T.INV; CHISQ.INV; F.INV",
                       (("TR", 4, "Test Recipes p. 4–14"),)),
    "dummiestabellen": Tool("Extra (niet te kennen): t-, χ²- en F-tabellen van Six Sigma For Dummies",
                            "t-tabel; t table; chi-kwadraattabel; chi-square table; F-tabel; F table; Dummies",
                            (("Dummies", 192, "Dummies p. 192–196"),)),
    "gemiddelde": Tool("Rekenmachine één gemiddelde: BI en z- of t-toets",
                       "betrouwbaarheidsinterval gemiddelde; confidence interval mean; t-toets; t-test; z-toets; z-test; "
                       "eenzijdig; one-sided; tweezijdig; two-sided",
                       (("CI FR", 5, "CI Further Reading p. 5–8"), ("TR", 4, "Test Recipes p. 4"), ("TH FR", 10, "TH Further Reading p. 10–14")),
                       "Gemiddelde & proportie"),
    "tweegemiddelden": Tool("Rekenmachine twee gemiddelden: ongepaard (gepoold) en gepaard",
                            "twee gemiddelden; two means; gepaard; paired; ongepaard; unpaired; gepoolde variantie; pooled "
                            "variance; verschil; difference",
                            (("CI FR", 15, "CI Further Reading p. 15–19"), ("TR", 5, "Test Recipes p. 5–10")), "Gemiddelde & proportie"),
    "proportie": Tool("Rekenmachine proporties: BI (benaderd en exact) en Z-toets",
                      "proportie; proportion; fractie; fraction; Clopper-Pearson; exact; binomiaal; Z-toets; z-test; "
                      "twee proporties; two proportions",
                      (("CI FR", 20, "CI Further Reading p. 20"),), "Gemiddelde & proportie"),
    "variantie": Tool("Rekenmachine varianties: χ² (één σ) en F (twee σ's)",
                      "variantie; variance; standaardafwijking; standard deviation; chi-kwadraattoets; chi-square test; "
                      "F-toets; F-test; verhouding van varianties; variance ratio; nauwkeuriger; more precise",
                      (("CI FR", 21, "CI Further Reading p. 21"), ("TR", 11, "Test Recipes p. 11–14")), "Varianties BI & toetsen"),
    "verdelingen": Tool("Rekenmachine kansverdelingen: Bernoulli, binomiaal, hypergeometrisch, Poisson, exponentieel, uniform",
                        "kansverdeling; probability distribution; binomiaal; binomial; hypergeometrisch; hypergeometric; "
                        "Poisson; exponentieel; exponential; uniform; Bernoulli; verwachtingswaarde; expected value",
                        (("AS", 12, "AS p. 12, 16, 20"), ("Data", 5, "Data p. 5–10")), "Verdelingen"),
    "kruistabel": Tool("Rekenmachine kruistabel: gezamenlijke, marginale en voorwaardelijke kansen",
                       "kruistabel; contingency table; gezamenlijke kans; joint probability; marginale kans; marginal "
                       "probability; voorwaardelijke kans; conditional probability; onafhankelijk; independent",
                       (("Data", 22, "Data p. 22–23"),)),
    "steekproefplan": Tool("Rekenmachine aanvaardingssteekproef: OC, α, β, AOQ, AOQL, ATI, AQL/LQL van een plan, plan voor variabelen",
                           "aanvaardingssteekproef; acceptance sampling; OC-curve; operating characteristic; AQL; LQL; LTPD; "
                           "producentenrisico; producer's risk; consumentenrisico; consumer's risk; AOQ; AOQL; ATI",
                           (("AS FR", 2, "AS Further Reading p. 2–10"), ("TH", 5, "TH p. 5–11")), "Aanvaardingssteekproeven"),
    "regressie": Tool("Rekenmachine enkelvoudige regressie (ook uit sommen of kwadratensommen) en partiële F-toets",
                      "regressie; regression; kleinste kwadraten; least squares; R²; helling; slope; intercept; "
                      "predictie-interval; prediction interval; betrouwbaarheidsinterval; confidence interval",
                      (("REG", 16, "REG p. 16–38"),), "ANOVA DOE regressie"),
    "anova": Tool("Rekenmachine eenweg-ANOVA",
                  "ANOVA; variantieanalyse; analysis of variance; one-way; eenweg; F-toets; F-test; kwadratensom; sum of squares",
                  (("DOE", 3, "DOE p. 3–15"),), "ANOVA DOE regressie"),
    "factorieel": Tool("Rekenmachine 2^k-factorieel: effecten, SS en F-toetsen",
                       "factorieel; factorial; 2^k; effect; interactie; interaction; contrast; poolen; pooling; DOE; "
                       "proefopzet; design of experiments",
                       (("DOE", 46, "DOE p. 46–79"),), "ANOVA DOE regressie"),
    "aliassen": Tool("Rekenmachine fractioneel factorieel: generatoren, aliassen, resolutie",
                     "fractioneel; fractional factorial; alias; generator; resolutie; resolution; definiërende relatie; "
                     "defining relation; halve fractie; half fraction",
                     (("DOE", 80, "DOE p. 80–92"),)),
    "capabiliteit": Tool("Rekenmachine procescapabiliteit: Cp, Cpk, Pp, Ppk, % buiten specificatie",
                         "capabiliteit; capability; Cp; Cpk; Pp; Ppk; specificatie; specification; LSL; USL; ppm; uitval",
                         (("SPC", 33, "SPC p. 33–47"), ("tabellen SPC", 1, "tabellen SPC p. 1–2")), "Capabiliteit"),
    "regelkaart": Tool("Rekenmachine regelkaarten: X̄-R, X̄-s, standaardwaarden en Western Electric-regels",
                       "regelkaart; control chart; controlegrenzen; control limits; UCL; LCL; X-bar; R-kaart; s-kaart; "
                       "Western Electric; run rules; standaardwaarden; standard values",
                       (("SPC", 62, "SPC p. 62–74"), ("tabellen SPC", 2, "tabellen SPC p. 2")), "Regelkaarten"),
    "constanten": Tool("Constanten voor regelkaarten zoals gedrukt (Table 18, Table A, Six Sigma Demystified)",
                       "constanten; constants; regelkaartconstanten; control chart constants; A2; D3; D4; d2; c4; B3; B4; E2; A3; Table 18; tabel",
                       (), "Tabellen"),
    "grr": Tool("Rekenmachine Gage R&R: gemiddelde-en-spreidingsbreedte en ANOVA",
                "Gage R&R; GRR; meetsysteemanalyse; measurement system analysis; MSA; herhaalbaarheid; repeatability; "
                "reproduceerbaarheid; reproducibility; EV; AV; PV; %GRR",
                (("MSA", 34, "MSA p. 34–37"), ("tabel MSA", 1, "tabel MSA.pdf")), "Gage R&R"),
    "msatabel": Tool("Tabel d2* (distribution of the average range) zoals gedrukt",
                     "d2*; d2 ster; d2 star; tabel MSA; average range; spreidingsbreedte",
                     (("tabel MSA", 1, "tabel MSA.pdf p. 1"),), "Tabellen"),
    "steekproefgrootte": Tool("Rekenmachine steekproefgrootte voor een betrouwbaarheidsinterval",
                              "steekproefgrootte; sample size; nauwkeurigheid; accuracy; breedte; width; hoeveel metingen; "
                              "how many; foutmarge; margin of error",
                              (("CI", 7, "CI p. 7, 10"), ("CI FR", 3, "CI FR p. 3"))),
    "tolerantie": Tool("Rekenmachine tolerantie-intervallen (σ gekend, σ onbekend, verdelingsvrij)",
                       "tolerantie-interval; tolerance interval; LTL; UTL; percentiel; percentile; verdelingsvrij; "
                       "distribution-free; k-factor",
                       (("CI FR", 22, "CI FR p. 22–23"),)),
    "onderscheidingsvermogen": Tool("Rekenmachine β, onderscheidingsvermogen (power) en n van een toets",
                                    "beta; type-II-fout; type II error; onderscheidingsvermogen; power; OC-curve; kracht; "
                                    "steekproefgrootte toets; sample size test",
                                    (("TH FR", 7, "TH FR p. 7–14"), ("TR", 9, "Test Recipes p. 9–10"))),
    "chikwadraat": Tool("Rekenmachine χ²-frequentietoetsen: aanpassing (goodness of fit) en kruistabel",
                        "chi-kwadraattoets; chi-square test; goodness of fit; aanpassingstoets; kruistabel; contingency "
                        "table; onafhankelijkheid; independence; verwachte frequentie; expected count; Yates",
                        (("TR", 15, "Test Recipes p. 15–20"),)),
    "nietparametrisch": Tool("Rekenmachine niet-parametrische toetsen: Mann-Whitney, signed ranks, runs",
                             "niet-parametrisch; non-parametric; Wilcoxon; Mann-Whitney; rangsom; rank sum; signed rank; "
                             "tekenrang; runs; aselect; randomness; mediaan; median",
                             (("TR", 21, "Test Recipes p. 21–26"),)),
    "steekproefmethoden": Tool("Rekenmachine steekproefmethoden: SRS tegenover gestratificeerd",
                               "gestratificeerd; stratified; strata; SRS; enkelvoudige aselecte steekproef; simple random "
                               "sample; variantie van het gemiddelde; optimale verdeling; optimal allocation",
                               (("AS", 16, "AS p. 16–19"),)),
    "planontwerp": Tool("Rekenmachine steekproefplan (n, c) ontwerpen voor AQL en LQL",
                        "plan ontwerpen; design a plan; Peach; AQL; LQL; producentenrisico; consumentenrisico; "
                        "sampling plan; n en c",
                        (("AS FR", 4, "AS FR p. 4, 17"),), "Aanvaardingssteekproeven"),
    "dubbelplan": Tool("Rekenmachine dubbel steekproefplan: OC en ASN",
                       "dubbel steekproefplan; double sampling plan; ASN; average sample number; tweede steekproef; "
                       "second sample",
                       (("AS FR", 5, "AS FR p. 5"), ("AS", 24, "AS p. 24–25"))),
    "sprt": Tool("Rekenmachine sequentiële toets (SPRT) voor attributen",
                 "SPRT; sequentieel; sequential; Wald; ASN; aanvaardingslijn; verwerpingslijn; acceptance line",
                 (("AS FR", 6, "AS FR p. 6–8"),)),
    "variabelenplan": Tool("Rekenmachine plan voor variabelen met gegeven n (ξ, k, Q)",
                           "plan voor variabelen; variables sampling plan; k-factor; ondergrens; lower limit; Q-statistiek",
                           (("AS", 26, "AS p. 26–27"), ("AS FR", 9, "AS FR p. 9")), "Aanvaardingssteekproeven"),
    "skiplot": Tool("Rekenmachine skip-lot en het criterium van Deming",
                    "skip-lot; kwalificatie; qualification; Deming; break-even; geen inspectie; volledige inspectie; "
                    "100 % inspection",
                    (("AS FR", 11, "AS FR p. 11, 13–15"),)),
    "beschrijvend": Tool("Rekenmachine beschrijvende statistiek en correlatie",
                         "beschrijvende statistiek; descriptive statistics; gemiddelde; mean; mediaan; median; modus; "
                         "mode; standaardafwijking; standard deviation; bereik; range; correlatie; correlation; "
                         "covariantie; covariance",
                         (("LSS", 131, "LSS p. 131"), ("REG", 43, "REG p. 43"))),
    "meervoudig": Tool("Rekenmachine meervoudige lineaire regressie (ook polynomen)",
                       "meervoudige regressie; multiple regression; polynoom; polynomial; tweede orde; second order; "
                       "coëfficiënten; coefficients; R² adj; centreren; centring",
                       (("REG", 46, "REG p. 46–62"),)),
    "anova2": Tool("Rekenmachine tweewegs-ANOVA (met en zonder herhalingen)",
                   "tweewegs-ANOVA; two-way ANOVA; interactie; interaction; herhalingen; replication; Two-Factor",
                   (("MSA", 36, "MSA p. 36"),)),
    "bayes": Tool("Rekenmachine regel van Bayes en Beta-posterior",
                  "Bayes; voorwaardelijke kans; conditional probability; prior; posterior; likelihood; Beta-verdeling; "
                  "Beta distribution; odds",
                  (("Data", 18, "Data p. 18–20"), ("ML", 53, "ML p. 53"))),
    "meetsysteem": Tool("Rekenmachines meetsysteem: waargenomen Cp, GPC, onzekerheid, bias, meeteenheid",
                        "waargenomen Cp; observed Cp; gauge performance curve; GPC; meetonzekerheid; measurement "
                        "uncertainty; uc; dekkingsfactor; coverage factor; bias-toets; bias test; meeteenheid; "
                        "discrimination; resolutie",
                        (("MSA", 24, "MSA p. 24–32"),)),
    "sigma_extra": Tool("Extra (niet te kennen): DPU, yields, RTY en genormaliseerde yield",
                        "DPU; defects per unit; throughput yield; first-time yield; FTY; verborgen fabriek; hidden factory; "
                        "rolled throughput yield; RTY; normalized yield; genormaliseerde yield; Dummies; Harry",
                        (("Dummies", 147, "Dummies p. 147–161"), ("H&S", 3, "Harry & Schroeder p. 3–5")), "Extra (boeken)"),
    "regelkaart_extra": Tool("Extra (niet te kennen): I-MR-, p- en u-kaart",
                             "I-MR; individuals; moving range; p-kaart; p chart; u-kaart; u chart; attributen; attributes; Dummies",
                             (("Dummies", 249, "Dummies p. 249–256"),), "Extra (boeken)"),
    "sigmatabellen_extra": Tool("Extra (niet te kennen): sigmatabellen van Six Sigma For Dummies",
                                "sigma scale; sigma score table; Dummies; Table 1-2; Table 6-3",
                                (("Dummies", 41, "Dummies p. 41, 160"),)),
    "constanten_extra": Tool("Extra (niet te kennen): regelkaartconstanten van Six Sigma For Dummies (Table 10-2)",
                             "constanten Dummies; Table 10-2; control chart constants Dummies",
                             (("Dummies", 250, "Dummies p. 250"),)),
    "confusion": Tool("Rekenmachine confusion matrix (2 × 2 en k klassen): accuracy, recall, precision, F1",
                      "confusion matrix; verwarringsmatrix; accuracy; nauwkeurigheid; recall; precision; F1; overfitting; "
                      "underfitting; train; test",
                      (("ML", 19, "ML p. 19–32"),), "Confusion matrix"),
}

PART_TOOLS: dict[str, tuple[str, ...]] = {
    "01": ("sigmatabellen",),
    "02": ("beschrijvend", "verdelingen", "kruistabel", "bayes", "normaal", "ztabel"),
    "03": ("normaal", "ztabel", "sigma", "sigmatabellen"),
    "04": ("gemiddelde", "tweegemiddelden", "proportie", "variantie", "steekproefgrootte", "tolerantie", "kwantielen"),
    "05": ("gemiddelde", "tweegemiddelden", "proportie", "variantie", "onderscheidingsvermogen", "chikwadraat",
           "nietparametrisch", "kwantielen"),
    "06": ("steekproefplan", "planontwerp", "dubbelplan", "sprt", "variabelenplan", "skiplot", "steekproefmethoden",
           "verdelingen", "normaal"),
    "07": ("regressie", "meervoudig", "beschrijvend", "kwantielen"),
    "08": ("anova", "anova2", "factorieel", "aliassen", "kwantielen"),
    "09": ("capabiliteit", "normaal", "ztabel", "sigma", "constanten"),
    "10": ("regelkaart", "constanten", "normaal"),
    "11": ("grr", "meetsysteem", "msatabel", "regressie", "capabiliteit", "bayes"),
    "12": ("confusion", "bayes"),
    "14": ("sigma_extra", "regelkaart_extra", "sigmatabellen_extra", "dummiestabellen", "constanten_extra"),
    "13": ("variantie", "kwantielen", "capabiliteit", "normaal", "confusion", "verdelingen", "sigma", "regelkaart",
           "kruistabel"),
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


def chart_constants(extra: bool = False) -> str:
    """The control-chart constant tables as printed, with the table each calculator uses (decision 4).

    extra=False: the course tables (Table 18, Table A, Six Sigma Demystified); extra=True: the Dummies table (Deel 14).
    """
    blocks = []
    for table in load_all():
        if (table.source.key == "DUM") != extra:
            continue
        used = sorted(symbol for symbol, key in USED_TABLE.items() if key == table.source.key)
        head = "".join(f"<th>{html.escape(c)}</th>" for c in table.columns)
        body = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in table.rows)
        role = f"De rekenmachines gebruiken hieruit: {', '.join(used)}." if used else "Ter referentie."
        blocks.append(f'<p class="lbl">{html.escape(table.title)} — '
                      f'{source_link(table.source_file, table.source_page, Path(table.source_file).name + " p. " + str(table.source_page))}'
                      f'</p><p class="help">{role} Bron: {html.escape(table.source.origin)}.</p>'
                      f'<div class="scroll"><table class="out grid printed"><tr>{head}</tr>{body}</table></div>')
    if extra:
        return ('<p class="help">Uit Six Sigma For Dummies (niet te kennen voor het examen); ter vergelijking met de '
                'tabellen van de cursus.</p>' + "".join(blocks))
    return ('<p class="help">Beslissing 4: Table 18 eerst (de oefenwerkboeken van de cursus gebruiken die waarden), c4 en '
            'd3 uit Table A, A3, E2, B5 en B6 uit Six Sigma Demystified. Kleine verschillen tussen de tabellen staan in '
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
        "S01_sigma_level_defects_per_million_yield_tabel"))
    sigma = ('<p class="help">Beide tabellen rekenen met de 1,5σ-verschuiving (beslissing 3). 2σ: SPC p. 21 drukt 308,537 '
             'en LSS p. 7 308,000; correct afgerond is 308 538.</p>' + sigma)
    sigma_extra = ('<p class="help">Uit Six Sigma For Dummies (niet te kennen voor het examen), ook met de 1,5σ-verschuiving.</p>'
                   + "".join(printed_table(stem) for stem in ("S07_table_1_2_the_sigma_scale", "S08_table_6_3_sigma_score_table_z_dpmo")))
    dummies = ('<p class="calc-warn">Let op: Dummies noemt "95 %" wat ±2σ is (95,45 %, 2,275 % per staart) bij de χ²-tabel, '
               'en een rechterstaart van 5 % bij de F-tabel; de kolommen staan per n, niet per vrijheidsgraden. Gebruik voor '
               'de oefeningen van de cursus de rekenmachine voor kritieke waarden.</p>' + "".join(printed_table(stem) for stem in (
                   "S08_table_8_1_t_values", "S08_table_8_2_chi_square_values", "S08_table_8_3_f_values_for_95_confidence")))
    content = {"ztabel": z_table(), "sigmatabellen": sigma, "sigmatabellen_extra": sigma_extra, "dummiestabellen": dummies,
               "constanten": chart_constants(), "constanten_extra": chart_constants(extra=True), "msatabel": msa_table()}
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
    """Navigation: one foldable group per part (the part link in its summary, the unit links inside)."""
    lines = ['<a href="#zoek-resultaten" class="l1" id="toc-top">Zoeken ↑</a>']
    for part in parts:
        items = []
        if PART_TOOLS.get(part.number):
            items.append(f'<a class="l2 tools" href="#tools-d{part.number}">Hulpmiddelen: rekenmachines en tabellen</a>')
        for unit_id, title in re.findall(r'<section class="unit" id="([^"]+)"[^>]*>\s*<h3>(.*?)</h3>', part.html, re.S):
            label = re.sub(r"<a class=\"p\".*?</a>", "", title, flags=re.S)
            label = re.sub(r"<[^>]+>", "", label).strip()
            items.append(f'<a class="l2" href="#{unit_id}">{html.escape(html.unescape(label))}</a>')
        lines.append(f'<details class="toc-part"><summary><a class="l1" href="#d{part.number}">{html.escape(part.title)}</a>'
                     f'</summary>{"".join(items)}</details>')
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
    """Give every clickable variable of part `number` its part prefix: <var data-s="key"> and \\sym{key}{…} in a formula
    become data-s="NN:key" and \\sym{NN:key}{…}; 'MM:key' stays as written."""
    def prefix(key: str) -> str:
        return key if ":" in key else f"{number}:{key}"
    text = VAR.sub(lambda m: f'<var data-s="{prefix(m.group(1))}">', text)
    return SYM.sub(lambda m: f"\\sym{{{prefix(m.group(1))}}}{{", text)


# ---------- formulas in LaTeX: \( … \) inline, \[ … \] display; pandoc turns them into MathML at build time ----------
# MathML is drawn by the browser itself (Chrome, Edge, Safari, Firefox), so the guide stays one offline file without
# a JavaScript math library. \sym{key}{TeX} marks a clickable variable, like <var data-s="key"> in plain text.

MATH = re.compile(r"\\\((.+?)\\\)|\\\[(.+?)\\\]", re.S)
SYM = re.compile(r"\\sym\{([^{}]+)\}\{")
DATA_S = re.compile(r'data-s="([^"]*)"')


def split_symbols(tex: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace every \\sym{key}{body} by a text placeholder (one token for pandoc); return the TeX and the (key, body)
    pairs in order. The bodies are converted on their own and put back as a clickable <mrow>."""
    out, pairs, position = [], [], 0
    while (match := SYM.search(tex, position)):
        depth, end = 1, match.end()
        while depth and end < len(tex):
            depth += {"{": 1, "}": -1}.get(tex[end], 0)
            end += 1
        if depth:
            raise ValueError(f"unbalanced braces after \\sym{{{match.group(1)}}} in: {tex}")
        out.append(tex[position:match.start()] + f"\\text{{ZQS{len(pairs)}ZQ}}")
        pairs.append((match.group(1), tex[match.end():end - 1]))
        position = end
    return "".join(out) + tex[position:], pairs


def pandoc_mathml(items: list[tuple[str, bool]]) -> dict[tuple[str, bool], str | None]:
    """MathML (<math> element) for every (TeX, display) pair in one pandoc run; None where pandoc cannot read the TeX."""
    def delimit(tex: str, display: bool) -> str:
        fence = "$$" if display else "$"
        # a decimal comma written 1{,}96 would come out as the list "1, 96": pass the number through as one token
        tex = re.sub(r"(\d+)\{,\}(\d+)", r"\\text{ZQD\1C\2ZQ}", " ".join(tex.split()))
        return f"{fence}{tex}{fence}"
    doc = "\n\n".join(f"ZQSEP{i}ZQ {delimit(tex, display)}" for i, (tex, display) in enumerate(items))
    out = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--mathml", "--wrap=none"],
                         input=doc, capture_output=True, text=True, check=True).stdout
    chunks = re.split(r"ZQSEP(\d+)ZQ", out)
    result: dict[tuple[str, bool], str | None] = {}
    for index, chunk in zip(chunks[1::2], chunks[2::2]):
        match = re.search(r"<math\b.*?</math>", chunk, re.S)
        if not match:
            result[items[int(index)]] = None
            continue
        mathml = re.sub(r"</?semantics>|<annotation\b.*?</annotation>| xmlns=\"[^\"]*\"", "", match.group(0), flags=re.S)
        mathml = re.sub(r"<mtext[^>]*>ZQD(\d+)C(\d+)ZQ</mtext>", r"<mn>\1,\2</mn>", mathml)
        result[items[int(index)]] = mathml
    return result


def typeset(content: str) -> tuple[str, list[str]]:
    """Replace every \\( … \\) and \\[ … \\] in the content by MathML; the problems list names TeX that does not convert."""
    matches = list(MATH.finditer(content))
    if not matches:
        return content, []
    problems, plans, batch = [], [], {}
    for match in matches:
        tex = html.unescape(match.group(1) if match.group(1) is not None else match.group(2))
        display = match.group(2) is not None
        try:
            main, pairs = split_symbols(tex)
        except ValueError as error:
            problems.append(str(error))
            plans.append(None)
            continue
        plans.append((tex, display, main, pairs))
        batch[(main, display)] = None
        for _, body in pairs:
            batch[(body, False)] = None
    mathml = pandoc_mathml(list(batch))

    def build(plan: tuple[str, bool, str, list[tuple[str, str]]]) -> str:
        tex, display, main, pairs = plan
        out = mathml[(main, display)]
        if out is None:
            problems.append(f"TeX that pandoc cannot read: {main}")
            return html.escape(tex)
        out = out.replace('display="inline"', "") if not display else out
        for i, (key, body) in enumerate(pairs):
            inner = mathml[(body, False)]
            if inner is None:
                problems.append(f"TeX that pandoc cannot read (in \\sym{{{key}}}): {body}")
                continue
            inner = re.sub(r"^<math[^>]*>|</math>$", "", inner)
            out, n = re.subn(rf"<mtext[^>]*>ZQS{i}ZQ</mtext>",
                             lambda _: f'<mrow class="v" data-s="{key}" tabindex="0">{inner}</mrow>', out, count=1)
            if n != 1:
                problems.append(f"\\sym{{{key}}} lost in conversion of: {tex}")
        return out

    pieces, position = [], 0
    for match, plan in zip(matches, plans):
        pieces.append(content[position:match.start()])
        pieces.append(build(plan) if plan else match.group(0))
        position = match.end()
    pieces.append(content[position:])
    return "".join(pieces), problems


def anchor_titles(page: str) -> dict[str, str]:
    """Readable title of every part, unit, exercise and tool id: the text of its h2, h3, h4 or summary."""
    titles = {}
    for match in re.finditer(r'<(section|div|details) class="(?:part|unit|exercise|tool|tools)"[^>]*\sid="([^"]+)"[^>]*>\s*'
                             r'<(h2|h3|h4|summary)>(.*?)</\3>', page, re.S):
        text = re.sub(r'<a class="p".*?</a>', "", match.group(4), flags=re.S)
        titles[match.group(2)] = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
    return titles


def symbols_data(table: dict[str, dict[str, str]], page: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """What the page embeds for the variable pop-ups: symbol, meaning, how to get it (LaTeX typeset), link and its
    title; and the TeX that could not be typeset."""
    titles = anchor_titles(page)
    fields = [(key, field, row[column]) for key, row in table.items()
              for field, column in (("s", "symbool"), ("b", "betekenis"), ("h", "hoe"))]
    # one pandoc run for all pop-ups: join the fields with a character that never occurs in text or MathML
    typeset_text, problems = typeset("\x00".join(text for _, _, text in fields))
    data = {key: {"a": row["anchor"], "t": titles.get(row["anchor"], row["anchor"])} for key, row in table.items()}
    for (key, field, _), text in zip(fields, typeset_text.split("\x00")):
        data[key][field] = text
    return data, [f"symbol pop-up: {p}" for p in problems]


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
    for key in sorted(set(DATA_S.findall(content)) - set(table)):
        problems.append(f"part {key.split(':')[0]}: unknown symbol key {key!r} (not in its NN_symbols.tsv)")
    for key, row in table.items():
        if row["anchor"] not in idset:
            problems.append(f"part {key.split(':')[0]}: symbol {key!r} links to missing anchor #{row['anchor']}")
    problems += figure_problems(content)
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


FIGURE_IMG = re.compile(r'<img src="figures/([^"]+)"([^>]*)>')
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}


def figure_problems(content: str) -> list[str]:
    """Every image is a file in study/figures/ with a description (alt), inside a <figure class="fig"> with a caption."""
    problems = []
    for name, attrs in FIGURE_IMG.findall(content):
        if not (FIGURES / name).is_file():
            problems.append(f"missing figure file: study/figures/{name}")
        if Path(name).suffix.lower() not in MIME:
            problems.append(f"figure type not supported: {name}")
        if not re.search(r'alt="[^"]{5,}"', attrs):
            problems.append(f"figure without a description (alt): {name}")
    if len(re.findall(r"<img\b", content)) != len(FIGURE_IMG.findall(content)):
        problems.append("an <img> that does not load from figures/")
    for block in re.findall(r'<figure class="fig">(.*?)</figure>', content, re.S):
        if "<figcaption>" not in block:
            problems.append(f"figure without caption: {block[:60]}")
    return problems


def inline_figures(page: str) -> str:
    """Embed every figure as a data URI, so the guide stays one self-contained file that shows its figures anywhere."""
    def embed(match: re.Match[str]) -> str:
        path = FIGURES / match.group(1)
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'<img src="data:{MIME[path.suffix.lower()]};base64,{data}"{match.group(2)}>'
    return FIGURE_IMG.sub(embed, page)


def coverage(page: str) -> dict[str, int]:
    """Per part: formula blocks (<div class="f">) that contain no clickable variable."""
    missing: dict[str, int] = {}
    for part_id, body in re.findall(r'<section class="part" id="d(\d\d)".*?>(.*?)(?=<section class="part"|<!--APP-->)', page, re.S):
        for block in div_blocks(body, '<div class="f">'):
            if 'data-s="' not in block:
                missing[part_id] = missing.get(part_id, 0) + 1
    return missing


def render(parts: list[Part], table: dict[str, dict[str, str]]) -> tuple[str, list[str]]:
    """The complete page, with its formulas typeset, and the formulas that could not be typeset."""
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
  <button type="button" id="fold-all" title="Alle delen, onderdelen en oefeningen inklappen">Alles in</button>
  <button type="button" id="unfold-all" title="Alles uitklappen">Alles uit</button>
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
    head, sep, rest = page.partition("<main>")
    content, app, scripts = rest.partition("<!--APP-->")  # the scripts contain regular expressions such as \(
    content, problems = typeset(content)
    page = head + sep + content + app + scripts
    popups, popup_problems = symbols_data(table, page)
    data = json.dumps(popups, ensure_ascii=False).replace("</", "<\\/")
    return new_tab_links(page).replace("@SYMBOLS@", data, 1), problems + popup_problems


def new_tab_links(page: str) -> str:
    """Links in the content open in a new tab, so the tab you are reading in stays where it is: every link to a course
    file, and every cross-reference inside the text. The table of contents (and the top bar) keep navigating in place."""
    head, sep, rest = page.partition("<main>")
    content, sep2, tail = rest.partition("<!--APP-->")
    content = re.sub(r'<a ((?:class="[^"]*" )?)href="(\.\./[^"]+|#[^"]+)"(?! target)',
                     r'<a \1href="\2" target="_blank" rel="noopener"', content)
    return head + sep + content + sep2 + tail


def main() -> None:
    """Build, validate and write the study guide; with --check, validate only (nothing is written)."""
    parts = load_parts()
    if not parts:
        sys.exit("no parts found in study/parts")
    table, problems = symbols(parts)
    page, math_problems = render(parts, table)
    problems += math_problems + validate(page, table)
    if problems:
        print("\n".join(problems))
        sys.exit(f"{len(problems)} problem(s); {OUTPUT.name} not written")
    gaps = coverage(page)
    print(f"{len(table)} symbols; formula blocks without a clickable variable: "
          + (", ".join(f"Deel {k}: {v}" for k, v in sorted(gaps.items())) or "none"))
    if "--check" in sys.argv:
        print("check only: no problems")
        return
    OUTPUT.write_text(inline_figures(page), encoding="utf-8", newline="\n")
    exercises = page.count('<div class="exercise"')
    words = len(re.sub(r"<[^>]+>", " ", page.split("<!--APP-->")[0]).split())
    print(f"{OUTPUT}: {len(parts)} parts, {exercises} exercises, {words} words, "
          f"{len(re.findall(r'href=\"[.][.]/', page))} slide links")


if __name__ == "__main__":
    main()
