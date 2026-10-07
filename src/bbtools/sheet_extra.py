"""Extra (boeken) sheet: calculator blocks whose only source is Six Sigma For Dummies or Harry & Schroeder.

The user: those books (Les 4) are not examinable, so blocks that only they cover leave the main sheets and live
here. Moved from Sigma & DPMO: DPU, throughput yield, RTY ≈ e^(−DPU); traditional / first-time yield and the
hidden factory; RTY of step yields and normalized yield; RTY of k identical steps (dice); yield per defect
opportunity from a final yield. Moved from Capability: Cp, Cpk and % out of spec with σ̂ = MR̄ / d2(n = 2).
The formulas are unchanged from the sheets they came from; yields and fractions are stored as fractions, shown as %.
"""
from __future__ import annotations

from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.sheet_tables import lookup_formula
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    constant_row,
    font,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "Extra (boeken)"

DUMMIES = "source/course/Les 4/Six Sigma For Dummies.pdf"
HARRY = "source/course/Les 4/Six-Sigma Mikel Harry -  Richard Schroeder.pdf"

HEADER = HeaderBlock(
    tool="Extra: rekenblokken uit Six Sigma For Dummies en Harry & Schroeder (niet te kennen voor het examen)",
    source=f"{DUMMIES} p. 38-39, 114-116, 147-156; {HARRY} p. 3-5",
    convention="Formules zoals in het boek; yields als fracties (0,95 = 95 %). Sigmaniveau met de 1,5σ-verschuiving "
               "(1.5σ shift) van de cursus (deck p. 37, beslissing 3); d2 voor n = 2 uit Tabel 18 (beslissing 4).",
    status=Status.VERIFIED,
    status_detail="getest tegen de uitgewerkte voorbeelden uit de boeken S07-WE01, S08-WE01 tot S08-WE04, S09-WE01, "
                  "S09-WE03 tot S09-WE06; enkele gedrukte waarden wijken af (zie build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Rekenblokken die alleen uit Six Sigma For Dummies en Harry & Schroeder komen (niet te kennen voor het "
            "examen): DPU, throughput yield, RTY ≈ e^(−DPU); traditionele yield, first-time yield, verborgen fabriek "
            "(hidden factory); RTY uit stapyields, genormaliseerde yield en eenheden nodig per goede eenheid; RTY van "
            "k gelijke stappen (dobbelstenen); gemiddelde yield per defectkans; Cp, Cpk en % buiten specificatie met "
            "σ̂ = MR̄ / 1,128.",
    inputs="per blok: defecten en eenheden; eenheden in, uit, afgekeurd, herwerkt; tot 10 stapyields; een RTY en het "
           "aantal stappen; één stapyield en k; een eindyield en het aantal kansen; LSL, USL, gemiddelde en MR̄. "
           "Yields als fracties (0,95 = 95 %).",
    audit="niet nodig (er bestaan uitgewerkte voorbeelden in de boeken)",
    disagreements=(
        "Dummies p. 148 (S08-WE02): verborgen fabriek '98.6% - 70.7% = 27.9%' trekt afgeronde waarden af; niet "
        "afgerond 27,84 %.",
        "Harry & Schroeder p. 3 (S09-WE01): product B '(0.968)**(1/48) = 99.97%'; berekend 99,932 %, en 'about 3.5 "
        "sigma' (zonder verschuiving) geeft 3,20.",
        "Harry & Schroeder p. 5 (S09-WE05): genormaliseerde yield gedrukt als '(0.368)**(-10) = 0.9051'; de k-de "
        "machtswortel die de tekst definieert geeft 0,368^(1/10) = 0,9049.",
    ),
)

PERCENT = "0.0000%"
NUMBER = "0.0000"
MILLION = 1_000_000
INPUTS = {
    "defects": "B10", "units": "B11",
    "units_in": "B17", "units_out": "B18", "scrapped": "B19", "reworked": "B20",
    **{f"step_{i}": f"B{25 + i}" for i in range(1, 11)},
    "rty": "B41", "steps": "B42",
    "step_yield": "B51", "k": "B52",
    "final_yield": "B57", "defect_opportunities": "B58",
    "lsl": "B66", "usl": "B67", "mean": "B68", "mrbar": "B69",
}
RESULTS = {
    "dpu": "B12", "ty": "B13", "rty_from_dpu": "B14",
    "y": "B21", "fty": "B22", "hidden_factory": "B23",
    "n_steps": "B36", "rty_steps": "B37", "ny_steps": "B38",
    "rty_used": "B43", "steps_used": "B44", "ny": "B45", "dpu_from_rty": "B46", "units_repairable": "B47",
    "units_scrapped": "B48",
    "rty_k": "B53", "one_in": "B54",
    "yield_per_defect_opportunity": "B59", "dpmo_from_yield": "B60", "z_no_shift_from_yield": "B61",
    "sigma_shifted_from_yield": "B62",
    "d2": "B70", "sigma_mr": "B71", "cp": "B72", "cpu": "B73", "cpl": "B74", "cpk": "B75",
    "below_lsl": "B76", "above_usl": "B77", "out_total": "B78", "ppm_total": "B79",
}
SHIFT = "B63"


def _warning(ws: Worksheet) -> None:
    """The bold line under the header: these books are not examinable."""
    ws["A7"] = ("Six Sigma For Dummies en Harry & Schroeder zijn niet te kennen voor het examen. Deze blokken komen "
                "alleen uit die boeken; de cursus zelf (deck, tabellen, oefenwerkboeken) behandelt ze niet.")
    ws["A7"].font = font(bold=True, color="C00000")


def _defects_per_unit(ws: Worksheet) -> None:
    """Block 1: DPU, throughput yield and RTY ≈ e^(−DPU)."""
    section_title(ws, 9, "1. Defecten per eenheid (defects per unit, DPU) en throughput yield")
    input_row(ws, 10, "D = aantal waargenomen defecten")
    input_row(ws, 11, "N = aantal geïnspecteerde eenheden")
    have = "AND(ISNUMBER(B10),ISNUMBER(B11),B11>0)"
    result_row(ws, 12, "DPU = D / N", f'=IF({have},B10/B11,"")', NUMBER, "Dummies p. 152; Harry & Schroeder p. 5")
    result_row(ws, 13, "Throughput yield TY = 1 − DPU", '=IF(ISNUMBER(B12),1-B12,"")', PERCENT,
               "Harry & Schroeder p. 5 (defects/unit 5 % -> TY 95 %)")
    result_row(ws, 14, "RTY ≈ e^(−DPU)", '=IF(ISNUMBER(B12),EXP(-B12),"")', PERCENT,
               "Dummies p. 156 (geldig als DPU klein is, bv. < 0,10)")


def _yields(ws: Worksheet) -> None:
    """Block 2: traditional yield, first-time yield and the hidden factory."""
    section_title(ws, 16, "2. Traditionele yield (Y) en first-time yield (FTY)")
    input_row(ws, 17, "Eenheden in (units in)")
    input_row(ws, 18, "Eenheden uit (goed op het einde, na herwerking)")
    input_row(ws, 19, "Afgekeurde eenheden (scrapped)")
    input_row(ws, 20, "Herwerkte eenheden (reworked, daarna goed)")
    have_in = "AND(ISNUMBER(B17),B17>0)"
    result_row(ws, 21, "Traditionele yield Y = uit / in", f'=IF(AND({have_in},ISNUMBER(B18)),B18/B17,"")', PERCENT,
               "Dummies p. 147, 151")
    result_row(ws, 22, "First-time yield FTY = (in − afgekeurd − herwerkt) / in",
               f'=IF(AND({have_in},ISNUMBER(B19),ISNUMBER(B20)),(B17-B19-B20)/B17,"")', PERCENT, "Dummies p. 148, 151")
    result_row(ws, 23, "Verborgen fabriek (hidden factory) = Y − FTY", '=IF(AND(ISNUMBER(B21),ISNUMBER(B22)),B21-B22,"")',
               PERCENT, "Dummies p. 148; Harry & Schroeder p. 4")


def _rolled(ws: Worksheet) -> None:
    """Blocks 3-5: rolled throughput yield from steps, from a known RTY, and for k identical steps."""
    section_title(ws, 25, "3. Rolled throughput yield (RTY) uit de yield van elke stap (tot 10 stappen, als fracties)")
    for i in range(1, 11):
        input_row(ws, 25 + i, f"Yield van stap {i}", "bv. 0,95" if i == 1 else "")
    steps = "B26:B35"
    result_row(ws, 36, "Aantal stappen k", f'=IF(COUNT({steps})>0,COUNT({steps}),"")', "0")
    result_row(ws, 37, "RTY = product van de stapyields", f'=IF(COUNT({steps})>0,PRODUCT({steps}),"")', PERCENT,
               "Dummies p. 150; Harry & Schroeder p. 5")
    result_row(ws, 38, "Genormaliseerde yield (normalized yield) NY = k-de machtswortel van RTY",
               '=IF(ISNUMBER(B37),B37^(1/B36),"")', PERCENT, "Harry & Schroeder p. 5")

    section_title(ws, 40, "4. Uit een gekende RTY")
    input_row(ws, 41, "RTY", "leeg laten om de RTY van deel 3 te gebruiken", "0.0000")
    input_row(ws, 42, "Aantal stappen k", "leeg laten om k van deel 3 te gebruiken")
    result_row(ws, 43, "Gebruikte RTY", '=IF(ISNUMBER(B41),B41,IF(ISNUMBER(B37),B37,""))', PERCENT)
    result_row(ws, 44, "Gebruikte k", '=IF(ISNUMBER(B42),B42,IF(ISNUMBER(B36),B36,""))', "0")
    ok = "AND(ISNUMBER(B43),B43>0,B43<=1)"
    result_row(ws, 45, "Genormaliseerde yield NY = RTY^(1/k)", f'=IF(AND({ok},ISNUMBER(B44),B44>0),B43^(1/B44),"")',
               PERCENT, "Harry & Schroeder p. 5 ('kth root of RTY')")
    result_row(ws, 46, "DPU = −ln(RTY)", f'=IF({ok},-LN(B43),"")', NUMBER, "Dummies p. 156")
    result_row(ws, 47, "Eenheden nodig per defectvrije eenheid, defecten herstelbaar: 1 + (1 − RTY)",
               f'=IF({ok},1+(1-B43),"")', "0.000", "Harry & Schroeder p. 5")
    result_row(ws, 48, "Eenheden nodig per defectvrije eenheid, defecte stuks afgekeurd: 1 / RTY", f'=IF({ok},1/B43,"")',
               "0.000", "Harry & Schroeder p. 5")

    section_title(ws, 50, "5. k identieke stappen (bv. dobbelstenen: kans 5/6 per dobbelsteen op geen '1')")
    input_row(ws, 51, "Yield van één stap (fractie)", "", NUMBER)
    input_row(ws, 52, "Aantal stappen k")
    have = "AND(ISNUMBER(B51),ISNUMBER(B52))"
    result_row(ws, 53, "RTY = yield^k", f'=IF({have},B51^B52,"")', "0.0000000000%", "Dummies p. 38-39 (dobbelstenen)")
    result_row(ws, 54, "Dat is één op … (1 / RTY)", '=IF(AND(ISNUMBER(B53),B53>0),1/B53,"")', "#,##0.0")


def _per_opportunity(ws: Worksheet) -> None:
    """Block 6: average yield per defect opportunity (Harry & Schroeder p. 3)."""
    section_title(ws, 56, "6. Gemiddelde yield per defectkans (vergelijk producten van verschillende complexiteit)")
    input_row(ws, 57, "Eindyield van het product (fractie)", "bv. 0,85", NUMBER)
    input_row(ws, 58, "Aantal defectkansen (defect opportunities)", "bv. 600")
    ok = "AND(ISNUMBER(B57),B57>0,B57<=1,ISNUMBER(B58),B58>0)"
    result_row(ws, 59, "Yield per kans = yield^(1 / kansen)", f'=IF({ok},B57^(1/B58),"")', PERCENT,
               "Harry & Schroeder p. 3")
    result_row(ws, 60, "DPMO = (1 − yield per kans) · 1 000 000", f'=IF(ISNUMBER(B59),(1-B59)*{MILLION},"")', "#,##0.0")
    result_row(ws, 61, "Z zonder verschuiving", '=IF(AND(ISNUMBER(B59),B59<1),_xlfn.NORM.S.INV(B59),"")', "0.000",
               "Harry & Schroeder p. 3 gebruikt deze lezing ('about 3.5 sigma')")
    result_row(ws, 62, "Sigmaniveau met de 1,5σ-verschuiving", f'=IF(ISNUMBER(B61),B61+{SHIFT},"")', "0.000")
    constant_row(ws, 63, "Verschuiving die de cursus aanneemt (σ)", 1.5, "deck p. 37")


def _moving_range_capability(ws: Worksheet) -> None:
    """Block 7: Cp, Cpk and % out of spec with σ̂ = MR̄ / d2(n = 2), the Capability formulas for one σ."""
    section_title(ws, 65, "7. Capabiliteit met σ̂ = MR̄ / 1,128 (individuele waarden)")
    input_row(ws, 66, "Onderste specificatiegrens LSL", "leeg laten bij een eenzijdige specificatie")
    input_row(ws, 67, "Bovenste specificatiegrens USL", "leeg laten bij een eenzijdige specificatie")
    input_row(ws, 68, "Procesgemiddelde x̄")
    input_row(ws, 69, "MR̄ (MR-bar) = gemiddelde moving range van de individuele waarden")
    output_cell(ws, "B70", f'=IF(ISNUMBER(B69),{lookup_formula("d2", "2")},"")', NUMBER)
    label(ws, 70, 1, "d2 voor n = 2 (= 1,128), Tabel 18")
    label(ws, 70, 3, "___4.1 tabellen SPC.pdf p. 2", italic=True)
    # Reversed limits would give nonsense such as 197 % out of spec: blank σ, and with it every result below.
    result_row(ws, 71, "σ̂ = MR̄ / d2",
               '=IF(AND(ISNUMBER(B66),ISNUMBER(B67),B67<=B66),"",IF(AND(ISNUMBER(B69),ISNUMBER(B70)),B69/B70,""))',
               NUMBER, "Dummies p. 114-116 (σ_ST = R̄/1.128)")
    result_row(ws, 72, "Cp = (USL − LSL) / 6σ̂", '=IF(AND(ISNUMBER(B71),ISNUMBER(B66),ISNUMBER(B67)),(B67-B66)/(6*B71),"")',
               "0.000", "zoals blad Capabiliteit (deck p. 34)")
    result_row(ws, 73, "Cpu = (USL − gemiddelde) / 3σ̂",
               '=IF(AND(ISNUMBER(B71),ISNUMBER(B67),ISNUMBER(B68)),(B67-B68)/(3*B71),"")', "0.000")
    result_row(ws, 74, "Cpl = (gemiddelde − LSL) / 3σ̂",
               '=IF(AND(ISNUMBER(B71),ISNUMBER(B66),ISNUMBER(B68)),(B68-B66)/(3*B71),"")', "0.000")
    result_row(ws, 75, "Cpk = min(Cpu, Cpl)",
               '=IF(AND(ISNUMBER(B73),ISNUMBER(B74)),MIN(B73,B74),IF(ISNUMBER(B73),B73,IF(ISNUMBER(B74),B74,"")))',
               "0.000", "zoals blad Capabiliteit (deck p. 35)")
    # NORM.S.DIST(-z) rather than 1 - NORM.S.DIST(z): same value, no loss of digits in the far tail.
    result_row(ws, 76, "% onder LSL", '=IF(AND(ISNUMBER(B71),ISNUMBER(B66),ISNUMBER(B68)),'
               '_xlfn.NORM.S.DIST(-(B68-B66)/B71,TRUE),"")', "0.0000%")
    result_row(ws, 77, "% boven USL", '=IF(AND(ISNUMBER(B71),ISNUMBER(B67),ISNUMBER(B68)),'
               '_xlfn.NORM.S.DIST(-(B67-B68)/B71,TRUE),"")', "0.0000%")
    result_row(ws, 78, "% buiten specificatie (out of spec), totaal",
               '=IF(OR(ISNUMBER(B76),ISNUMBER(B77)),SUM(B76,B77),"")', "0.0000%")
    result_row(ws, 79, "ppm buiten specificatie, totaal", '=IF(ISNUMBER(B78),B78*1000000,"")', "#,##0.0")


def _validation(ws: Worksheet) -> None:
    """Yields must be fractions; MR̄ must be positive."""
    fraction = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True,
                              showErrorMessage=True, errorTitle="Yield", error="Typ een yield als fractie, 0 tot 1.")
    positive = DataValidation(type="decimal", operator="greaterThan", formula1="0", allow_blank=True,
                              showErrorMessage=True, errorTitle="Spreiding moet positief zijn",
                              error="MR̄ moet groter zijn dan 0.")
    ws.add_data_validation(fraction)
    ws.add_data_validation(positive)
    for name in [*(f"step_{i}" for i in range(1, 11)), "rty", "step_yield", "final_yield"]:
        fraction.add(INPUTS[name])
    positive.add(INPUTS["mrbar"])


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the book-only calculator blocks."""
    write_header(ws, HEADER)
    _warning(ws)
    _defects_per_unit(ws)
    _yields(ws)
    _rolled(ws)
    _per_opportunity(ws)
    _moving_range_capability(ws)
    _validation(ws)
    ws.column_dimensions["A"].width = 66
    ws.column_dimensions["B"].width = 16
    ws.column_dimensions["C"].width = 16
