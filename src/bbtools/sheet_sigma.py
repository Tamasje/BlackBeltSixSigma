"""Sigma & DPMO sheet: DPO, DPMO, yield per opportunity and sigma level (with and without the 1.5σ shift).

Convention decision 3 (inventory/conventions.md): sigma level ↔ DPMO is shown in both readings. The course
tables (deck p. 21; Van Volsem p. 7) pair a short-term sigma level Z with the long-term DPMO of one tail beyond
Z − 1.5; deck p. 40 reads Cp = 2 (Z = 6) without the shift, both tails.
The blocks whose only source is Six Sigma For Dummies or Harry & Schroeder (DPU, throughput / first-time /
rolled yield, hidden factory, normalized yield, yield per defect opportunity) live on the Extra sheet
(bbtools.sheet_extra): those books are not examinable. All yields and fractions are stored as fractions, shown as %.
"""
from __future__ import annotations

from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    constant_row,
    input_row,
    label,
    result_row,
    section_title,
    write_header,
)

SHEET = "Sigma & DPMO"

HEADER = HeaderBlock(
    tool="Sigmaniveau, DPMO en yield: DPO, DPMO, Z met en zonder 1,5σ-verschuiving (1.5σ shift)",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 19-21, 37-40; "
           "Les 1/20260521_van volsem.pdf p. 7",
    convention="Beslissing 3: sigmaniveau ↔ DPMO getoond met de 1,5σ-verschuiving (zoals in elke cursustabel) en zonder.",
    status=Status.VERIFIED,
    status_detail="getest tegen de uitgewerkte voorbeelden S08-WE05 tot S08-WE08 en S09-WE03 en tegen de sigmatabellen "
                  "van de cursus (deck p. 21, Van Volsem p. 7); één gedrukte waarde wijkt af (zie build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Discrete data: DPO, DPMO en yield per kans (opportunity); sigmaniveau uit een DPMO en DPMO uit een "
            "sigmaniveau, in beide lezingen van de cursus.",
    inputs="per blok: defecten, eenheden en kansen per eenheid; een DPMO; een sigmaniveau. De rekenblokken die alleen "
           "uit de boeken komen (DPU, throughput yield, FTY, RTY, genormaliseerde yield) staan op blad Extra (boeken).",
    audit="niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)",
    disagreements=(
        "deck p. 21 en Harry & Schroeder (samenvatting p. 2, outline p. 1): 2σ = '308,537' DPMO; 308 537,5 rondt af op "
        "308 538 (zoals Dummies drukt). Van Volsem p. 7: '308,000' (308 538 op duizendtallen is 309 000).",
    ),
)

PERCENT = "0.0000%"
MILLION = 1_000_000
INPUTS = {"defects": "B9", "units": "B10", "opportunities": "B11", "dpmo": "B17", "sigma_level": "B24"}
RESULTS = {
    "dpo": "B12", "dpmo_1": "B13", "yield_per_opportunity": "B14",
    "dpmo_used": "B18", "yield_2": "B19", "z_no_shift": "B20", "sigma_shifted": "B21",
    "dpmo_shifted": "B25", "dpmo_one_tail": "B26", "dpmo_two_tails": "B27", "yield_shifted": "B28",
}
SHIFT = "B30"


def _defects(ws: Worksheet) -> None:
    """Section 1: defects, units and opportunities."""
    section_title(ws, 8, "1. Defecten (defects), eenheden (units) en kansen (opportunities): discrete data")
    input_row(ws, 9, "D = aantal waargenomen defecten")
    input_row(ws, 10, "N = aantal geïnspecteerde eenheden", "voor één item met veel kansen: N = 1")
    input_row(ws, 11, "O = kansen (opportunities, CTQ's) per eenheid", "1 als elke eenheid één kans is")
    have_o = "AND(ISNUMBER(B9),ISNUMBER(B10),B10>0,ISNUMBER(B11),B11>0)"
    result_row(ws, 12, "DPO = D / (N · O)  (defects per opportunity)", f'=IF({have_o},B9/(B10*B11),"")', "0.000000000",
               "deck p. 20")
    result_row(ws, 13, "DPMO = DPO · 1 000 000  (defects per million opportunities)",
               f'=IF(ISNUMBER(B12),B12*{MILLION},"")', "#,##0.0", "deck p. 20")
    result_row(ws, 14, "Yield per kans (opportunity) = 1 − DPO", '=IF(ISNUMBER(B12),1-B12,"")', PERCENT, "deck p. 20")


def _sigma(ws: Worksheet) -> None:
    """Sections 2-3: DPMO ↔ sigma level in both readings."""
    section_title(ws, 16, "2. Van DPMO naar sigmaniveau (beide lezingen van de cursus)")
    input_row(ws, 17, "DPMO", "leeg laten om de DPMO van deel 1 te gebruiken", "#,##0.0")
    result_row(ws, 18, "Gebruikte DPMO", '=IF(ISNUMBER(B17),B17,IF(ISNUMBER(B13),B13,""))', "#,##0.0")
    ok = f"AND(ISNUMBER(B18),B18>0,B18<{MILLION})"
    result_row(ws, 19, "Yield = 1 − DPMO / 1 000 000", f'=IF({ok},1-B18/{MILLION},"")', PERCENT)
    result_row(ws, 20, "Z zonder verschuiving (één staart voorbij Z)", f'=IF({ok},_xlfn.NORM.S.INV(1-B18/{MILLION}),"")',
               "0.000", "standaardnormale verdeling, Z-score (deck p. 19-20)")
    result_row(ws, 21, "Sigmaniveau met de 1,5σ-verschuiving = Z + 1,5  (cursustabellen)",
               f'=IF(ISNUMBER(B20),B20+{SHIFT},"")', "0.000", "deck p. 21, 37")

    section_title(ws, 23, "3. Van sigmaniveau naar DPMO (beide lezingen van de cursus)")
    input_row(ws, 24, "Sigmaniveau Z", "bv. 6")
    have = "ISNUMBER(B24)"
    result_row(ws, 25, "DPMO met de 1,5σ-verschuiving (één staart voorbij Z − 1,5)  (cursustabellen)",
               f'=IF({have},{MILLION}*_xlfn.NORM.S.DIST(-(B24-{SHIFT}),TRUE),"")', "#,##0.000",
               "deck p. 21; Van Volsem p. 7: 6 -> 3,4")
    result_row(ws, 26, "DPMO zonder verschuiving, één staart voorbij Z",
               f'=IF({have},{MILLION}*_xlfn.NORM.S.DIST(-B24,TRUE),"")', "#,##0.000")
    result_row(ws, 27, "DPMO zonder verschuiving, beide staarten voorbij ±Z (gecentreerd, Cp = Z / 3)",
               f'=IF({have},2*{MILLION}*_xlfn.NORM.S.DIST(-B24,TRUE),"")', "#,##0.000",
               "deck p. 40: CP = 2 (Z = 6) -> '2 defect per billion'")
    result_row(ws, 28, "Yield met de 1,5σ-verschuiving", f'=IF({have},1-B25/{MILLION},"")', "0.00000%",
               "deck p. 21; Van Volsem p. 7")
    constant_row(ws, 30, "Verschuiving die de cursus aanneemt (σ)", 1.5, "deck p. 37")
    label(ws, 32, 1, "DPU, throughput yield, first-time yield, verborgen fabriek (hidden factory), RTY, genormaliseerde "
                     "yield en yield per defectkans komen alleen uit de boeken: zie blad 'Extra (boeken)' (niet te "
                     "kennen voor het examen).", italic=True)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the sigma-level / DPMO calculator."""
    write_header(ws, HEADER)
    _defects(ws)
    _sigma(ws)
    ws.column_dimensions["A"].width = 66
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
