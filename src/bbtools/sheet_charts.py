"""Regelkaarten sheet: X̄-R and X̄-s charts from subgroups, with out-of-limit flags and the Western Electric rules.

Course: X̄/R and X̄/s limits CL = X̿, X̿ ± A2·R̄, D3·R̄ … D4·R̄, X̿ ± A3·s̄, B3·s̄ … B4·s̄ (deck p. 74); σ = R̄/d2 and
σ(x̄) = σ/√n (deck p. 64 notes); Western Electric rules (deck p. 68-69). Constants from the Tabellen sheet
(decision 4: Table 18; c4 from Table A; A3 from Six Sigma Demystified). The I-MR, p and u charts come only from
Six Sigma For Dummies (not examinable) and live on the Extra (boeken) sheet.

Row plan: X̄-R / X̄-s summary 8-26 (how to fill, the rules and the constants beside it, from column J); subgroup
table from row 52
to the bottom: 1000 subgroups of up to 25 values (Table 18 stops at n = 25), so it can grow without moving anything.
"""
from __future__ import annotations

from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from bbtools.readme import SheetDoc
from bbtools.sheet_tables import lookup_formula, used_constants_table
from bbtools.xlsx_style import (
    HeaderBlock,
    Status,
    column_titles,
    input_block,
    input_row,
    label,
    output_cell,
    result_row,
    section_title,
    write_header,
)

SHEET = "Regelkaarten"

HEADER = HeaderBlock(
    tool="Regelkaarten (control charts): X̄-R- en X̄-s-kaart uit subgroepen, met markering van punten buiten de grenzen",
    source="source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 54-58, 62-74; ___4.1 tabellen SPC.pdf "
           "p. 1-2; Les 5/20260619_ottoy_Rheostat Knob Data.xls",
    convention="Beslissing 4: constanten uit Table 18 (A2, D3, D4, B3, B4, d2), Table A (c4), Six Sigma Demystified "
               "(A3); 3σ-grenzen. I-MR-, p- en u-kaart: blad Extra (boeken), niet te kennen.",
    status=Status.VERIFIED,
    status_detail="getest tegen de uitgewerkte voorbeelden van de cursus S06-WE03, S06-WE05, S06-WE06, S10-WE04a, "
                  "S10-WE04b (en S08-WE18 uit Dummies; extra, niet te kennen); enkele gedrukte waarden wijken af "
                  "(build/README.md)",
)

DOC = SheetDoc(
    sheet=SHEET,
    purpose="Controlegrenzen (control limits) en centrale lijnen van de X̄-R- en X̄-s-kaart, de σ-schattingen R̄/d2 en "
            "s̄/c4, en een markering voor elke subgroep buiten de grenzen; de Western Electric-regels om de kaart te lezen.",
    inputs="subgroepen als ruwe waarden (tot 10 per rij) of als getypte x̄ en R (en s) met n.",
    audit="niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)",
    disagreements=(
        "Rheostat Knob Data.xls (Les 5, S10-WE04a/b) rekent UCL_R met D4 = 2,114 (Six Sigma Demystified); de "
        "oefenwerkboeken van Les 4 gebruiken 2,115 (Table 18), wat het blad gebruikt (beslissing 4). De X̄-grenzen "
        "komen overeen.",
    ),
)

SUBGROUPS, FIRST_SUBGROUP, VALUES = 1000, 52, 25
NUMBER = "0.000000"
X_COLUMNS = [get_column_letter(2 + j) for j in range(VALUES)]  # x1 … x25 of a subgroup: B … Z
TYPED = {"xbar": "AA", "r": "AB", "s": "AC"}                       # or a subgroup typed as x̄, R (and s)
USED = {"n": "AD", "x": "AE", "r": "AF", "s": "AG"}                # what the sheet uses per subgroup
FLAGS = {"xbar_r": "AH", "r": "AI", "xbar_s": "AJ", "s": "AK"}     # 'boven UCL' / 'onder LCL'
CHECK = "AL"                                                       # per-row warning

INPUTS = {"n_typed": "B9"}
SUMMARY = {"k": "B12", "n": "B13", "equal": "B14", "xbarbar": "B15", "rbar": "B16", "sbar": "B17",
           "sigma_r": "B18", "d2": "C18", "sigma_s": "B19", "c4": "C19", "sigma_xbar": "B20"}
LIMITS = {"xbar_r": 23, "r": 24, "xbar_s": 25, "s": 26}  # columns B = LCL, C = CL, D = UCL, F/G = constants


def subgroup_row(index: int) -> int:
    """Row of subgroup `index` (0-based) in the X̄-R / X̄-s table."""
    return FIRST_SUBGROUP + index


def _constant(symbol: str, n_ref: str) -> str:
    """Formula for a table constant at subgroup size `n_ref`, or a message when n is outside the table."""
    return f'=IF(ISNUMBER({n_ref}),IFERROR({lookup_formula(symbol, n_ref)},"n niet in de tabel"),"")'


def _flag(value: str, low: str, high: str) -> str:
    """Formula: 'boven UCL' / 'onder LCL' / '' for a plotted value against its limits."""
    return (f'=IF(AND(ISNUMBER({value}),ISNUMBER({low}),ISNUMBER({high})),IF({value}>{high},"boven UCL",'
            f'IF({value}<{low},"onder LCL","")),"")')


def _subgroups(ws: Worksheet) -> None:
    """Section 1: X̄-R and X̄-s summary, limits and the subgroup table."""
    section_title(ws, 8, f"1. X̄-R- en X̄-s-kaart uit subgroepen (vul de tabel vanaf rij {FIRST_SUBGROUP}: ruwe waarden, of x̄ "
                         "en R; uitleg rechts)")
    input_row(ws, 9, "n = subgroepgrootte, als je subgroepen als x̄ en R typt", "ruwe waarden: n wordt per rij geteld")
    section_title(ws, 11, "Samenvatting van de subgroepen")
    first, last = subgroup_row(0), subgroup_row(SUBGROUPS - 1)
    col = {name: f"{letter}{first}:{letter}{last}" for name, letter in USED.items()}
    result_row(ws, 12, "k = aantal subgroepen", f'=IF(COUNT({col["x"]})>0,COUNT({col["x"]}),"")', "0")
    result_row(ws, 13, "gebruikte n (grootste subgroepgrootte)", f'=IF(COUNT({col["n"]})>0,MAX({col["n"]}),"")', "0")
    result_row(ws, 14, "Gelijke subgroepgroottes?", f'=IF(COUNT({col["n"]})>0,IF(MIN({col["n"]})=MAX({col["n"]}),"ja",'
               f'"NEE: de grenzen gebruiken de grootste n (deck p. 74: variable sample size)"),"")')
    result_row(ws, 15, "X̿ = gemiddelde van de subgroepgemiddelden", f'=IF(COUNT({col["x"]})>0,AVERAGE({col["x"]}),"")', NUMBER)
    result_row(ws, 16, "R̄ = gemiddelde spreidingsbreedte (range)", f'=IF(COUNT({col["r"]})>0,AVERAGE({col["r"]}),"")', NUMBER)
    result_row(ws, 17, "s̄ = gemiddelde standaardafwijking", f'=IF(COUNT({col["s"]})>0,AVERAGE({col["s"]}),"")', NUMBER)
    label(ws, 18, 1, "σ̂ = R̄ / d2  (d2 in kolom C)")
    output_cell(ws, "C18", _constant("d2", "B13"), "0.000")
    output_cell(ws, "B18", '=IF(AND(ISNUMBER(B16),ISNUMBER(C18)),B16/C18,"")', NUMBER)
    label(ws, 18, 4, "deck p. 64 (sprekersnotities)", italic=True)
    label(ws, 19, 1, "σ̂ = s̄ / c4  (c4 in kolom C)")
    output_cell(ws, "C19", _constant("c4", "B13"), "0.0000")
    output_cell(ws, "B19", '=IF(AND(ISNUMBER(B17),ISNUMBER(C19)),B17/C19,"")', NUMBER)
    label(ws, 19, 4, "___4.1 tabellen SPC.pdf p. 1", italic=True)
    result_row(ws, 20, "σ(x̄) = σ̂ / √n  (met R̄/d2)", '=IF(AND(ISNUMBER(B18),ISNUMBER(B13)),B18/SQRT(B13),"")', NUMBER,
               "deck p. 64 (notities)")

    column_titles(ws, 22, ["Kaart", "LCL", "CL", "UCL", "Constanten", "waarde", "waarde", "Bron in de cursus"])
    specs = {
        "xbar_r": ("X̄-kaart met R̄: X̿ ± A2·R̄", "A2", None, "B15", "B16", "deck p. 74"),
        "r": ("R-kaart: D3·R̄ … D4·R̄", "D3", "D4", "B16", "B16", "deck p. 74"),
        "xbar_s": ("X̄-kaart met s̄: X̿ ± A3·s̄", "A3", None, "B15", "B17", "deck p. 74; notities p. 73: s beter voor n > 10"),
        "s": ("s-kaart: B3·s̄ … B4·s̄", "B3", "B4", "B17", "B17", "deck p. 74"),
    }
    for key, (text, c1, c2, centre, spread, source) in specs.items():
        r = LIMITS[key]
        label(ws, r, 1, text)
        label(ws, r, 5, f"{c1}, {c2}" if c2 else c1)
        output_cell(ws, f"F{r}", _constant(c1, "$B$13"), "0.000")
        if c2:
            output_cell(ws, f"G{r}", _constant(c2, "$B$13"), "0.000")
        needed = [centre, f"F{r}"] + ([f"G{r}"] if c2 else [])
        ok = "AND(" + ",".join(f"ISNUMBER({cell})" for cell in needed) + ")"
        if c2:  # R and s charts: limits are constant × centre line
            output_cell(ws, f"B{r}", f'=IF({ok},F{r}*{centre},"")', NUMBER)
            output_cell(ws, f"D{r}", f'=IF({ok},G{r}*{centre},"")', NUMBER)
        else:   # X̄ charts: X̿ ± constant × spread
            output_cell(ws, f"B{r}", f'=IF(AND({ok},ISNUMBER({spread})),{centre}-F{r}*{spread},"")', NUMBER)
            output_cell(ws, f"D{r}", f'=IF(AND({ok},ISNUMBER({spread})),{centre}+F{r}*{spread},"")', NUMBER)
        output_cell(ws, f"C{r}", f'=IF(ISNUMBER({centre}),{centre},"")', NUMBER)
        label(ws, r, 8, source, italic=True)

    column_titles(ws, FIRST_SUBGROUP - 1, ["Subgroep", *[f"x{i}" for i in range(1, VALUES + 1)], "of: x̄ getypt",
                                            "R getypt", "s getypt", "n", "x̄", "R", "s", "x̄ t.o.v. X̄-R", "R t.o.v. R",
                                            "x̄ t.o.v. X̄-s", "s t.o.v. s", "controle"])
    lim = {key: (f"$B${r}", f"$D${r}") for key, r in LIMITS.items()}
    input_block(ws, (first, last), (2, 2 + VALUES - 1))
    input_block(ws, (first, last), (column_index_from_string(TYPED["xbar"]), column_index_from_string(TYPED["s"])))
    u, x = USED, TYPED
    for index in range(SUBGROUPS):
        r = subgroup_row(index)
        raw, typed = f"B{r}:{X_COLUMNS[-1]}{r}", f"{x['xbar']}{r}:{x['s']}{r}"
        ws[f"A{r}"] = index + 1
        output_cell(ws, f"{u['n']}{r}", f'=IF(COUNT({raw})>0,COUNT({raw}),IF(OR(ISNUMBER({x["xbar"]}{r}),'
                                        f'ISNUMBER({x["r"]}{r})),$B$9,""))', "0")
        output_cell(ws, f"{u['x']}{r}", f'=IF(COUNT({raw})>0,AVERAGE({raw}),IF(ISNUMBER({x["xbar"]}{r}),{x["xbar"]}{r},""))',
                    NUMBER)
        output_cell(ws, f"{u['r']}{r}", f'=IF(COUNT({raw})>1,MAX({raw})-MIN({raw}),IF(ISNUMBER({x["r"]}{r}),{x["r"]}{r},""))',
                    NUMBER)
        output_cell(ws, f"{u['s']}{r}", f'=IF(COUNT({raw})>1,_xlfn.STDEV.S({raw}),IF(ISNUMBER({x["s"]}{r}),{x["s"]}{r},""))',
                    NUMBER)
        output_cell(ws, f"{FLAGS['xbar_r']}{r}", _flag(f"{u['x']}{r}", *lim["xbar_r"]))
        output_cell(ws, f"{FLAGS['r']}{r}", _flag(f"{u['r']}{r}", *lim["r"]))
        output_cell(ws, f"{FLAGS['xbar_s']}{r}", _flag(f"{u['x']}{r}", *lim["xbar_s"]))
        output_cell(ws, f"{FLAGS['s']}{r}", _flag(f"{u['s']}{r}", *lim["s"]))
        output_cell(ws, f"{CHECK}{r}", f'=IF(AND(COUNT({raw})>0,COUNT({typed})>0),"ruwe waarden én getypt: getypte '
                                       f'genegeerd",IF(COUNTA({raw},{typed})>COUNT({raw},{typed}),"tekst telt niet mee",'
                                       f'IF(COUNT({raw})=1,"1 waarde: geen R of s","")))')


def _instructions(ws: Worksheet) -> None:
    """How to fill the subgroup table, beside the summary (column J), so the table below can grow."""
    lines = (
        ("Zo vul je de tabel in (vanaf rij {first})".format(first=FIRST_SUBGROUP), True),
        ("• Eén subgroep per rij, alleen GETALLEN. Ruwe waarden: x1, x2, … naast elkaar in kolommen B tot Z (tot 25 "
         "per subgroep).", False),
        ("• Of typ per subgroep x̄ en R (en s) in kolommen AA-AC en de subgroepgrootte n in B9.", False),
        (f"• Tot {SUBGROUPS} subgroepen; lege rijen tellen niet mee. Kolom AL zegt per rij wat er mis is.", False),
        ("• Plakken uit een ander bestand: Plakken speciaal → Waarden. Geen kop of tekst in de tabel.", False),
    )
    for offset, (text, bold) in enumerate(lines):
        label(ws, 8 + offset, 10, text, bold=bold, italic=not bold)


def _rules(ws: Worksheet) -> None:
    """How the course reads a control chart, beside the summary (column J)."""
    label(ws, 14, 10, "De kaart lezen: Western Electric-regels (deck p. 68-69)", bold=True)
    rules = (
        "1. Eén of meer punten buiten de controlegrenzen (gemarkeerd in de tabel hieronder).",
        "2. Twee van drie opeenvolgende punten buiten de 2σ-waarschuwingsgrenzen maar nog binnen de controlegrenzen.",
        "3. Vier van vijf opeenvolgende punten voorbij de 1σ-grenzen.",
        "4. Acht opeenvolgende punten aan één kant van de centrale lijn.",
        "Bij regels 2 en 3 zegt deck p. 68 niet of de punten aan dezelfde kant van de centrale lijn moeten liggen.",
        "Meer regels, zones A/B/C en overreageren (tampering) tegenover te laat reageren: deck p. 65-70.",
    )
    for offset, text in enumerate(rules):
        label(ws, 15 + offset, 10, text, italic=offset >= 4)


def build_sheet(ws: Worksheet) -> None:
    """Fill an empty worksheet with the control-chart calculator."""
    write_header(ws, HEADER)
    _subgroups(ws)
    _instructions(ws)
    _rules(ws)
    used_constants_table(ws, 22, 10, ("A2", "D3", "D4", "A3", "B3", "B4", "d2", "c4"), "X̄-R- en X̄-s-kaart")
    size = DataValidation(type="whole", operator="between", formula1="2", formula2="25", allow_blank=True,
                          showErrorMessage=True, errorTitle="Subgroepgrootte", error="n is een geheel getal van 2 tot 25.")
    ws.add_data_validation(size)
    size.add(INPUTS["n_typed"])
    ws.column_dimensions["A"].width = 44
    for column in range(2, column_index_from_string(CHECK)):
        ws.column_dimensions[get_column_letter(column)].width = 11
    ws.column_dimensions[CHECK].width = 30
