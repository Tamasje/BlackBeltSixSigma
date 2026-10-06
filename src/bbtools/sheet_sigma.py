"""Sigma & DPMO sheet: DPU, DPO, DPMO, sigma level (with and without the 1.5σ shift), yields and RTY.

Convention decision 3 (inventory/conventions.md): sigma level ↔ DPMO is shown in both readings. The course
tables (deck p. 21; Dummies Table 1-2 p. 41 and Table 6-3 p. 160; Van Volsem p. 7; Harry & Schroeder) pair a
short-term sigma level Z with the long-term DPMO of one tail beyond Z − 1.5. Harry & Schroeder p. 3 quote a
sigma level without the shift ("99.97 % ... about 3.5 sigma"), p. 5 with it ("2,500 DPMO ... about 4.3 sigma").
All yields and fractions are stored as fractions and shown as %.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    constant_row,
    input_row,
    result_row,
    section_title,
    write_header,
)

SHEET = "Sigma & DPMO"

HEADER = HeaderBlock(
    tool="Sigma level, DPMO and yield: DPU, DPO, DPMO, Z with and without 1.5σ shift, Y, FTY, RTY",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 20-21, 37-40; "
           "Six Sigma For Dummies.pdf p. 41, 147-161; Six-Sigma Mikel Harry - Richard Schroeder.pdf p. 3-5; "
           "20260521_van volsem.pdf p. 7",
    convention="Decision 3: sigma level ↔ DPMO shown both with the 1.5σ shift (as in every course table) and without.",
    status=Status.VERIFIED,
    status_detail="tested against course worked examples S07-WE01, S08-WE01 to S08-WE08, S09-WE01, S09-WE03 to "
                  "S09-WE06 and the course sigma tables; a few printed values disagree (listed in build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Discrete-data capability: DPU, DPO, DPMO and yield; sigma level from DPMO and DPMO from a sigma level "
            "(both course readings); traditional yield, first-time yield, hidden factory; RTY, normalized yield and "
            "units needed per good unit; average yield per defect opportunity.",
    inputs="per block: defects, units, opportunities per unit; a DPMO; a sigma level; units in, out, scrapped, "
           "reworked; up to 10 step yields; an RTY and number of steps; one step yield and k; a final yield and "
           "number of opportunities. Yields as fractions (0.95 = 95 %).",
    audit="not needed (course worked examples exist)",
    disagreements=(
        "Dummies p. 148 (S08-WE02): hidden factory '98.6% - 70.7% = 27.9%' subtracts rounded values; 27.84 % unrounded.",
        "Harry & Schroeder p. 3 (S09-WE01): product B '(0.968)**(1/48) = 99.97%'; computed 99.932 %, "
        "and 'about 3.5 sigma' (no shift) gives 3.20.",
        "Harry & Schroeder p. 5 (S09-WE05): normalized yield printed '(0.368)**(-10) = 0.9051'; the kth root the "
        "text defines gives 0.368^(1/10) = 0.9049.",
        "deck p. 21 and Harry & Schroeder (summary p. 2, outline p. 1): 2σ = '308,537' DPMO; 308,537.5 rounds to "
        "308,538 (as Dummies prints). Van Volsem p. 7: '308,000' (308,538 to thousands is 309,000).",
    ),
)

PERCENT = "0.0000%"
MILLION = 1_000_000
INPUTS = {
    "defects": "B9", "units": "B10", "opportunities": "B11",
    "dpmo": "B20", "sigma_level": "B27",
    "units_in": "B34", "units_out": "B35", "scrapped": "B36", "reworked": "B37",
    **{f"step_{i}": f"B{42 + i}" for i in range(1, 11)},
    "rty": "B61", "steps": "B62",
    "step_yield": "B70", "k": "B71",
    "final_yield": "B76", "defect_opportunities": "B77",
}
RESULTS = {
    "dpu": "B12", "dpo": "B13", "dpmo_1": "B14", "yield_per_opportunity": "B15", "ty": "B16", "rty_from_dpu": "B17",
    "dpmo_used": "B21", "yield_2": "B22", "z_no_shift": "B23", "sigma_shifted": "B24",
    "dpmo_shifted": "B28", "dpmo_one_tail": "B29", "dpmo_two_tails": "B30", "yield_shifted": "B31",
    "y": "B38", "fty": "B39", "hidden_factory": "B40",
    "n_steps": "B53", "rty_steps": "B54", "ny_steps": "B55",
    "rty_used": "B63", "steps_used": "B64", "ny": "B65", "dpu_from_rty": "B66", "units_repairable": "B67",
    "units_scrapped": "B68",
    "rty_k": "B72", "one_in": "B73",
    "yield_per_defect_opportunity": "B78", "dpmo_8": "B79", "z_no_shift_8": "B80", "sigma_shifted_8": "B81",
}
SHIFT = "B83"


def _defects(ws: Worksheet) -> None:
    """Section 1: defects, units and opportunities."""
    section_title(ws, 8, "1. Defects, units and opportunities (discrete data)")
    input_row(ws, 9, "D = number of defects observed")
    input_row(ws, 10, "N = number of units inspected", "for one item with many opportunities: N = 1")
    input_row(ws, 11, "O = opportunities (CTQs) per unit", "1 if every unit is one opportunity")
    have = "AND(ISNUMBER(B9),ISNUMBER(B10),B10>0)"
    have_o = f"AND({have},ISNUMBER(B11),B11>0)"
    result_row(ws, 12, "DPU = D / N", f'=IF({have},B9/B10,"")', "0.0000", "Dummies p. 152; Harry & Schroeder p. 5")
    result_row(ws, 13, "DPO = D / (N · O)", f'=IF({have_o},B9/(B10*B11),"")', "0.000000000", "deck p. 20; Dummies p. 153")
    result_row(ws, 14, "DPMO = DPO · 1 000 000", f'=IF(ISNUMBER(B13),B13*{MILLION},"")', "#,##0.0",
               "deck p. 20; Dummies p. 155")
    result_row(ws, 15, "Yield per opportunity = 1 − DPO", '=IF(ISNUMBER(B13),1-B13,"")', PERCENT, "deck p. 20")
    result_row(ws, 16, "Throughput yield TY = 1 − DPU", '=IF(ISNUMBER(B12),1-B12,"")', PERCENT,
               "Harry & Schroeder p. 5 (defects/unit 5 % -> TY 95 %)")
    result_row(ws, 17, "RTY ≈ e^(−DPU)", '=IF(ISNUMBER(B12),EXP(-B12),"")', PERCENT,
               "Dummies p. 156 (valid when DPU is small, e.g. < 0.10)")


def _sigma(ws: Worksheet) -> None:
    """Sections 2-3: DPMO ↔ sigma level in both readings."""
    section_title(ws, 19, "2. From DPMO to sigma level (both course readings)")
    input_row(ws, 20, "DPMO", "leave empty to use the DPMO of section 1", "#,##0.0")
    result_row(ws, 21, "DPMO used", '=IF(ISNUMBER(B20),B20,IF(ISNUMBER(B14),B14,""))', "#,##0.0")
    ok = f"AND(ISNUMBER(B21),B21>0,B21<{MILLION})"
    result_row(ws, 22, "Yield = 1 − DPMO / 1 000 000", f'=IF({ok},1-B21/{MILLION},"")', PERCENT)
    result_row(ws, 23, "Z without shift (one tail beyond Z)", f'=IF({ok},_xlfn.NORM.S.INV(1-B21/{MILLION}),"")', "0.000",
               "Dummies p. 158 (Z_LT); Harry & Schroeder p. 3 reads sigma this way")
    result_row(ws, 24, "Sigma level with the 1.5σ shift = Z + 1.5  (course tables)", f'=IF(ISNUMBER(B23),B23+{SHIFT},"")',
               "0.000", "deck p. 21; Dummies Table 6-3 p. 160 ('long-term DPMO, short-term Z'); Harry & Schroeder p. 5")

    section_title(ws, 26, "3. From sigma level to DPMO (both course readings)")
    input_row(ws, 27, "Sigma level Z", "e.g. 6")
    have = "ISNUMBER(B27)"
    result_row(ws, 28, "DPMO with the 1.5σ shift (one tail beyond Z − 1.5)  (course tables)",
               f'=IF({have},{MILLION}*_xlfn.NORM.S.DIST(-(B27-{SHIFT}),TRUE),"")', "#,##0.000",
               "deck p. 21; Dummies p. 41, 160; Van Volsem p. 7: 6 -> 3.4")
    result_row(ws, 29, "DPMO without shift, one tail beyond Z", f'=IF({have},{MILLION}*_xlfn.NORM.S.DIST(-B27,TRUE),"")',
               "#,##0.000")
    result_row(ws, 30, "DPMO without shift, both tails beyond ±Z (centred, Cp = Z / 3)",
               f'=IF({have},2*{MILLION}*_xlfn.NORM.S.DIST(-B27,TRUE),"")', "#,##0.000",
               "deck p. 40: CP = 2 (Z = 6) -> 2 defect per billion")
    result_row(ws, 31, "Yield with the 1.5σ shift", f'=IF({have},1-B28/{MILLION},"")', "0.00000%",
               "deck p. 21; Van Volsem p. 7")


def _yields(ws: Worksheet) -> None:
    """Section 4: traditional yield, first-time yield and the hidden factory."""
    section_title(ws, 33, "4. Traditional yield and first-time yield")
    input_row(ws, 34, "Units in")
    input_row(ws, 35, "Units out (good at the end, after rework)")
    input_row(ws, 36, "Units scrapped")
    input_row(ws, 37, "Units reworked (and then good)")
    have_in = "AND(ISNUMBER(B34),B34>0)"
    result_row(ws, 38, "Traditional yield Y = out / in", f'=IF(AND({have_in},ISNUMBER(B35)),B35/B34,"")', PERCENT,
               "Dummies p. 147, 151")
    result_row(ws, 39, "First-time yield FTY = (in − scrap − rework) / in",
               f'=IF(AND({have_in},ISNUMBER(B36),ISNUMBER(B37)),(B34-B36-B37)/B34,"")', PERCENT, "Dummies p. 148, 151")
    result_row(ws, 40, "Hidden factory = Y − FTY", '=IF(AND(ISNUMBER(B38),ISNUMBER(B39)),B38-B39,"")', PERCENT,
               "Dummies p. 148; Harry & Schroeder p. 4")


def _rolled(ws: Worksheet) -> None:
    """Sections 5-7: rolled throughput yield from steps, from a known RTY, and for k equal steps."""
    section_title(ws, 42, "5. Rolled throughput yield from the yield of each step (up to 10 steps, as fractions)")
    for i in range(1, 11):
        input_row(ws, 42 + i, f"Yield of step {i}", "e.g. 0.95" if i == 1 else "")
    steps = "B43:B52"
    result_row(ws, 53, "Number of steps k", f'=IF(COUNT({steps})>0,COUNT({steps}),"")', "0")
    result_row(ws, 54, "RTY = product of the step yields", f'=IF(COUNT({steps})>0,PRODUCT({steps}),"")', PERCENT,
               "Dummies p. 150; Harry & Schroeder p. 5")
    result_row(ws, 55, "Normalized yield NY = k-th root of RTY", '=IF(ISNUMBER(B54),B54^(1/B53),"")', PERCENT,
               "Harry & Schroeder p. 5")

    section_title(ws, 60, "6. From a known RTY")
    input_row(ws, 61, "RTY", "leave empty to use the RTY of section 5", "0.0000")
    input_row(ws, 62, "Number of steps k", "leave empty to use k of section 5")
    result_row(ws, 63, "RTY used", '=IF(ISNUMBER(B61),B61,IF(ISNUMBER(B54),B54,""))', PERCENT)
    result_row(ws, 64, "k used", '=IF(ISNUMBER(B62),B62,IF(ISNUMBER(B53),B53,""))', "0")
    ok = "AND(ISNUMBER(B63),B63>0,B63<=1)"
    result_row(ws, 65, "Normalized yield NY = RTY^(1/k)", f'=IF(AND({ok},ISNUMBER(B64),B64>0),B63^(1/B64),"")', PERCENT,
               "Harry & Schroeder p. 5 ('kth root of RTY')")
    result_row(ws, 66, "DPU = −ln(RTY)", f'=IF({ok},-LN(B63),"")', "0.0000", "Dummies p. 156")
    result_row(ws, 67, "Units needed per defect-free unit, defects repairable: 1 + (1 − RTY)", f'=IF({ok},1+(1-B63),"")',
               "0.000", "Harry & Schroeder p. 5")
    result_row(ws, 68, "Units needed per defect-free unit, defectives scrapped: 1 / RTY", f'=IF({ok},1/B63,"")', "0.000",
               "Harry & Schroeder p. 5")

    section_title(ws, 69, "7. k identical steps (e.g. dice: 5/6 chance per die of no '1')")
    input_row(ws, 70, "Yield of one step (fraction)", "", "0.0000")
    input_row(ws, 71, "Number of steps k")
    have = "AND(ISNUMBER(B70),ISNUMBER(B71))"
    result_row(ws, 72, "RTY = yield^k", f'=IF({have},B70^B71,"")', "0.0000000000%", "Dummies p. 38-39 (dice example)")
    result_row(ws, 73, "That is one in … (1 / RTY)", '=IF(AND(ISNUMBER(B72),B72>0),1/B72,"")', "#,##0.0")


def _per_opportunity(ws: Worksheet) -> None:
    """Section 8: average yield per defect opportunity (Harry & Schroeder p. 3)."""
    section_title(ws, 75, "8. Average yield per defect opportunity (compare products of different complexity)")
    input_row(ws, 76, "Final yield of the product (fraction)", "e.g. 0.85", "0.0000")
    input_row(ws, 77, "Number of defect opportunities", "e.g. 600")
    ok = "AND(ISNUMBER(B76),B76>0,B76<=1,ISNUMBER(B77),B77>0)"
    result_row(ws, 78, "Yield per opportunity = yield^(1 / opportunities)", f'=IF({ok},B76^(1/B77),"")', PERCENT,
               "Harry & Schroeder p. 3")
    result_row(ws, 79, "DPMO = (1 − yield per opportunity) · 1 000 000", f'=IF(ISNUMBER(B78),(1-B78)*{MILLION},"")',
               "#,##0.0")
    result_row(ws, 80, "Z without shift", '=IF(AND(ISNUMBER(B78),B78<1),_xlfn.NORM.S.INV(B78),"")', "0.000",
               "Harry & Schroeder p. 3 quotes this reading ('about 3.5 sigma')")
    result_row(ws, 81, "Sigma level with the 1.5σ shift", f'=IF(ISNUMBER(B80),B80+{SHIFT},"")', "0.000")
    constant_row(ws, 83, "Shift assumed by the course (σ)", 1.5, "deck p. 37; Dummies p. 159-160 ('Zlt = Zst - 1.5')")


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the sigma-level / DPMO / yield calculator."""
    write_header(ws, HEADER)
    _defects(ws)
    _sigma(ws)
    _yields(ws)
    _rolled(ws)
    _per_opportunity(ws)
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Yield", error="Type a yield as a fraction, 0 to 1.")
    ws.add_data_validation(fraction)
    for coordinate in [*(f"B{42 + i}" for i in range(1, 11)), "B61", "B70", "B76"]:
        fraction.add(coordinate)
    ws.column_dimensions["A"].width = 66
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
