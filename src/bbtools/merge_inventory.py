"""Merge the per-slice extraction files `inventory/raw/S*.json` into the inventory deliverables.

Outputs (all under `inventory/`):
- `formulas.md`            every formula, grouped by module and file, with its source page
- `constants/<table>.csv`  one CSV per transcribed table; every row carries source_file/source_page
- `worked_examples.json`   the test oracle (course worked examples; exam answer-key items are added by hand)
- `conventions.md`         every convention statement, grouped by theme; hand-written sections survive reruns
- `topic_index.json`       topic -> file + pages, for the exam-time index
- `review_items.md`        provenance gaps, cross-source numeric conflicts, ragged tables, ambiguities

Nothing is chosen between disagreeing sources: conflicts are listed with every version and its source.

Run: python3 -m bbtools.merge_inventory   (from the project root, with src/ on PYTHONPATH)
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "inventory"
RAW = INVENTORY / "raw"
ARRAYS = ("topics", "formulas", "constant_tables", "worked_examples", "conventions", "ambiguities")

GENERATED_BEGIN = "<!-- BEGIN GENERATED (merge_inventory.py) -->"
GENERATED_END = "<!-- END GENERATED -->"

# Symbols of control-chart / MSA constants. Case matters: d3 (range spread) is not D3 (limit factor).
CONSTANT_SYMBOLS = {
    "A", "A0", "A1", "A2", "A3", "c2", "1/c2", "c4", "1/c4", "B1", "B2", "B3", "B4", "B5", "B6",
    "d2", "1/d2", "d3", "D1", "D2", "D3", "D4", "E2", "d2*",
}

# Convention themes, checked in order; the first matching theme wins.
CONVENTION_THEMES: list[tuple[str, str]] = [
    ("MSA / Gage R&R", r"gage|grr|r&r|\bmsa\b|repeatab|reproduc|\bndc\b|linearit|meetsyste|measurement.system"),
    ("Acceptance sampling", r"\baql\b|ltpd|\brql\b|oc-curve|oc curve|acceptance|steekproefplan|\baoq|\bati\b"),
    ("Sigma level, 1.5σ shift, DPMO", r"1[.,]5\s*(σ|sigma)|shift|dpmo|sigma level|sigma-niveau|defects per million|\bppm\b|yield"),
    ("Capability indices and σ estimate", r"capab|\bcpk?\b|\bppk?\b|\bcpm\b"),
    ("Control charts / SPC", r"control chart|control limit|regelkaart|\bspc\b|western electric|nelson|run rule|subgroup|subgroep|x̄|xbar"),
    ("Hypothesis tests and confidence intervals", r"alpha|α|signific|eenzijdig|tweezijdig|one-sided|two-sided|tailed|confidence|betrouwbaar|p-value|p-waarde|hypothe|toets"),
    ("DOE / ANOVA / regression", r"anova|\bdoe\b|factorial|factor|effect|interact|regress|r²|alias|resolution"),
    ("Standard deviation (n vs n−1)", r"n\s*[-−]\s*1|stdev|standaardafwijking|standard deviation"),
    ("Excel functions", r"excel|norm\.|t\.inv|f\.inv|chisq|t\.dist|f\.dist"),
    ("Machine learning / data science", r"machine learning|confusion|precision|recall|overfit|bias-variance|cross-valid|training|test ?set|examen"),
    ("Rounding", r"round|afrond|decima"),
    ("Project, DMAIC and organisation", r"dmaic|belt|project|champion|sponsor|define|smart|lean"),
]


def load_slices(raw_dir: Path = RAW) -> list[dict]:
    """Load every per-slice JSON file, sorted by slice id, so outputs are deterministic."""
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("S*.json"))]


def module_of(file: str) -> str:
    """Return the course module ('Les 4') a source path belongs to, or 'exam'/'other'."""
    match = re.search(r"source/course/(Les \d+)/", file)
    if match:
        return match.group(1)
    return "exam" if file.startswith("source/exam/") else "other"


def slugify(text: str, limit: int = 60) -> str:
    """ASCII, lowercase, underscore-separated file-name stem."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")[:limit].rstrip("_") or "table"


def provenance_gaps(slices: list[dict]) -> list[str]:
    """List every item without a file, or without a page (topics: without a non-empty pages list)."""
    gaps = []
    for sl in slices:
        for array in ARRAYS:
            for i, item in enumerate(sl.get(array, [])):
                has_page = bool(item.get("pages")) if array == "topics" else item.get("page") not in (None, "")
                if not item.get("file") or not has_page:
                    label = item.get("name") or item.get("topic") or item.get("id") or item.get("issue", "")[:60]
                    gaps.append(f"{sl['slice_id']} {array}[{i}] {label!r}: file={item.get('file')!r} page={item.get('page', item.get('pages'))!r}")
    return gaps


def source_ref(item: dict) -> str:
    """Human-readable 'file p. N [sheet]' reference for markdown outputs."""
    ref = f"{item['file']} p. {item.get('page')}"
    if item.get("sheet"):
        ref += f" (sheet '{item['sheet']}'{', ' + item['cells'] if item.get('cells') else ''})"
    if item.get("notes"):
        ref += " (speaker notes)"
    return ref


def ordered(items: list[dict]) -> list[dict]:
    """Sort items by module, file and page so every output reads like the course."""
    def key(it: dict) -> tuple:
        page = it.get("page") if it.get("page") is not None else (it.get("pages") or [0])[0]
        return (module_of(it.get("file", "")), it.get("file", ""), page if isinstance(page, int) else 0)
    return sorted(items, key=key)


def tagged(slices: list[dict], array: str) -> list[dict]:
    """All items of one array across slices, each tagged with its slice id."""
    return [{**item, "slice": sl["slice_id"]} for sl in slices for item in sl.get(array, [])]


# ---------------------------------------------------------------- topic index, formulas, examples

def write_topic_index(slices: list[dict], path: Path) -> int:
    """Write topic -> file + pages as a flat JSON list ordered like the course."""
    topics = [{"topic": t["topic"], "module": module_of(t["file"]), "file": t["file"], "pages": t["pages"], "slice": t["slice"]}
              for t in ordered(tagged(slices, "topics"))]
    path.write_text(json.dumps(topics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(topics)


def write_formulas_md(slices: list[dict], path: Path) -> int:
    """Write every formula, grouped by module and file, in the course's own notation."""
    formulas = ordered(tagged(slices, "formulas"))
    lines = ["# Formulas", "", "Generated by `src/bbtools/merge_inventory.py` from `inventory/raw/`. Do not hand-edit.", ""]
    current_module, current_file = None, None
    for f in formulas:
        if module_of(f["file"]) != current_module:
            current_module = module_of(f["file"])
            lines += [f"## {current_module}", ""]
        if f["file"] != current_file:
            current_file = f["file"]
            lines += [f"### {Path(current_file).name}", ""]
        lines += [f"#### {f['name']} ({source_ref(f)}, {f['slice']})", "", "```", f["expression"], "```"]
        for symbol, meaning in (f.get("symbols") or {}).items():
            lines.append(f"- `{symbol}`: {meaning}")
        if f.get("conditions"):
            lines.append(f"- Conditions: {f['conditions']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(formulas)


def oracle_locked() -> bool:
    """True once the git tag 'oracle-approved' exists; the oracle is then only extended by the user."""
    result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "-q", "--verify", "refs/tags/oracle-approved"],
                            capture_output=True)
    return result.returncode == 0


def write_worked_examples(slices: list[dict], path: Path) -> int:
    """Write the oracle: every course worked example with its slice and source, unchanged otherwise.

    Once the oracle is locked the file is left untouched (the guard hook only covers Claude's editors).
    """
    examples = ordered(tagged(slices, "worked_examples"))
    if oracle_locked():
        print(f"oracle-approved tag exists: {path.name} left unchanged")
        return len(examples)
    for ex in examples:
        ex["source_kind"] = "course"
    doc = {
        "description": "Test oracle. Values are transcribed strings exactly as printed. "
                       "Locked by git tag 'oracle-approved'; only the user extends it.",
        "examples": examples,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(examples)


# ---------------------------------------------------------------- constant tables

def write_constant_tables(slices: list[dict], out_dir: Path) -> tuple[list[Path], list[str]]:
    """Write one CSV per table with provenance columns; return the paths and any ragged-table notes.

    Short rows are padded with empty cells (never with values) so provenance stays in its column.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths, ragged = [], []
    for table in tagged(slices, "constant_tables"):
        stem = f"{table['slice']}_{slugify(table['name'])}"
        path = out_dir / f"{stem}.csv"
        suffix = 2
        while path in paths:  # two tables with the same name in one slice
            path = out_dir / f"{stem}_{suffix}.csv"
            suffix += 1
        width = max([len(table["columns"])] + [len(r) for r in table["rows"]])
        if any(len(r) != len(table["columns"]) for r in table["rows"]):
            ragged.append(f"{path.name}: {len(table['columns'])} columns, row lengths {sorted({len(r) for r in table['rows']})} ({source_ref(table)})")
        header = list(table["columns"]) + [f"extra_{i}" for i in range(len(table["columns"]), width)]
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header + ["source_file", "source_page", "table_name"])
            for row in table["rows"]:
                writer.writerow(list(row) + [""] * (width - len(row)) + [table["file"], table["page"], table["name"]])
        paths.append(path)
    return paths, ragged


def normalise_symbol(label: str) -> str:
    """Map a column label such as 'd₂', 'D_4' or 'A 2' onto a CONSTANT_SYMBOLS spelling."""
    text = unicodedata.normalize("NFKC", label)  # turns subscript digits into plain digits
    return re.sub(r"[\s_{}$]", "", text)


def key_column(columns: list[str], pattern: str) -> int | None:
    """Index of the first column whose label matches `pattern` (case-insensitive), if any."""
    for i, col in enumerate(columns):
        if re.search(pattern, col, re.IGNORECASE):
            return i
    return None


def parse_decimal(text: str) -> float | None:
    """Parse a constant such as '2.326' or Dutch '2,326'; None for dashes, blanks and words."""
    cleaned = text.strip().replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_count(text: str) -> float | None:
    """Parse a DPMO count such as '691,462' or '3.4' (commas here are thousands separators)."""
    cleaned = text.strip().replace(" ", "").replace(" ", "")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", cleaned):
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned.replace(",", "."))
    except ValueError:
        return None


def collect_family_values(slices: list[dict]) -> dict[tuple[str, str, str], list[tuple[str, str, dict]]]:
    """Gather (family, symbol, key) -> [(printed value, table name, table)] across all tables.

    Families: 'constant' (control-chart/MSA factors keyed by n) and 'dpmo' (defects per million
    keyed by sigma level). Only these can be compared mechanically; other tables are reviewed by hand.
    """
    values: dict[tuple[str, str, str], list[tuple[str, str, dict]]] = defaultdict(list)
    for table in tagged(slices, "constant_tables"):
        cols = table["columns"]
        n_col = key_column(cols, r"^\s*n\s*$|sample|subgroup|observations|steekproef|grootte|\bm\b")
        symbol_cols = {i: normalise_symbol(c) for i, c in enumerate(cols) if normalise_symbol(c) in CONSTANT_SYMBOLS}
        # A lone match is usually a DOE factor column named 'A'; real constant tables carry several symbols.
        if len(symbol_cols) >= 2:
            n_col = 0 if n_col is None else n_col
            for row in table["rows"]:
                if n_col >= len(row):
                    continue
                for i, symbol in symbol_cols.items():
                    if i < len(row) and row[i].strip():
                        values[("constant", symbol, row[n_col].strip())].append((row[i], table["name"], table))
        sigma_col = key_column(cols, r"sigma")
        dpmo_col = key_column(cols, r"dpmo|defects per million|per million|ppm")
        if sigma_col is not None and dpmo_col is not None and sigma_col != dpmo_col:
            for row in table["rows"]:
                if max(sigma_col, dpmo_col) < len(row):
                    values[("dpmo", "DPMO", row[sigma_col].strip())].append((row[dpmo_col], table["name"], table))
    return values


def as_decimal(text: str) -> Decimal:
    """Exact decimal of a printed number ('2,326', '691,462', '0.7971'); floats would blur the last digit."""
    cleaned = text.strip().replace(" ", "")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", cleaned):
        cleaned = cleaned.replace(",", "")
    return Decimal(cleaned.replace(",", "."))


def resolution_exponent(text: str) -> int:
    """Power of ten of the last printed digit: -3 for '0.797', 4 for '690,000', 0 for '0'."""
    value = as_decimal(text)
    if value == 0:
        return 0
    exponent = value.as_tuple().exponent
    if exponent < 0:
        return exponent
    digits = str(abs(int(value)))
    return len(digits) - len(digits.rstrip("0"))


def rounding_consistent(printed: list[str]) -> bool:
    """True if every pair agrees once rounded half-up to the coarser printed resolution.

    '0.7971' and '0.797' agree; '0.8525' and '0.853' agree; '0.7272' and '0.724' do not;
    '690,000' and '691,462' agree (the former is printed to 2 significant figures).
    """
    for i in range(len(printed)):
        for j in range(i + 1, len(printed)):
            quantum = Decimal(1).scaleb(max(resolution_exponent(printed[i]), resolution_exponent(printed[j])))
            a = as_decimal(printed[i]).quantize(quantum, rounding=ROUND_HALF_UP)
            b = as_decimal(printed[j]).quantize(quantum, rounding=ROUND_HALF_UP)
            if a != b:
                return False
    return True


def numeric_conflicts(slices: list[dict]) -> tuple[list[str], list[str]]:
    """Compare every (symbol, key) across sources; return (real conflicts, rounding-only differences).

    Nothing is resolved: every printed version is listed with its source.
    """
    conflicts, rounding_only = [], []
    for (family, symbol, key), entries in sorted(collect_family_values(slices).items()):
        parse = parse_decimal if family == "constant" else parse_count
        numeric = [(v, name, t, parse(v)) for v, name, t in entries if parse(v) is not None]
        if len({n for *_, n in numeric}) < 2:
            continue
        versions = "; ".join(f"'{v}' in {name} ({t['file']} p. {t['page']})" for v, name, t, _ in numeric)
        line = f"{symbol} at {'n' if family == 'constant' else 'sigma'}={key}: {versions}"
        if rounding_consistent([v for v, *_ in numeric]):
            rounding_only.append(line)
        else:
            conflicts.append(line)
    return conflicts, rounding_only


# ---------------------------------------------------------------- conventions and review

def theme_of(convention: dict) -> str:
    """Assign a convention statement to the first matching theme, for readable grouping only."""
    text = f"{convention.get('topic', '')} {convention.get('as_stated', '')}".lower()
    for theme, pattern in CONVENTION_THEMES:
        if re.search(pattern, text):
            return theme
    return "Other"


def generated_conventions(slices: list[dict]) -> str:
    """Markdown body listing every convention statement verbatim, grouped by theme."""
    by_theme: dict[str, list[dict]] = defaultdict(list)
    for conv in ordered(tagged(slices, "conventions")):
        by_theme[theme_of(conv)].append(conv)
    lines = ["## Conventions as stated in the course", "",
             "Verbatim statements, grouped by theme. Generated; do not edit between the markers.", ""]
    for theme in [t for t, _ in CONVENTION_THEMES] + ["Other"]:
        if not by_theme.get(theme):
            continue
        lines += [f"### {theme}", ""]
        for conv in by_theme[theme]:
            lines.append(f"- **{conv['topic']}**: {conv['as_stated']} ({source_ref(conv)}, {conv['slice']})")
        lines.append("")
    return "\n".join(lines)


def write_conventions_md(slices: list[dict], path: Path) -> int:
    """Refresh the generated block of conventions.md, keeping the hand-written sections around it."""
    block = f"{GENERATED_BEGIN}\n{generated_conventions(slices)}\n{GENERATED_END}"
    if path.exists() and GENERATED_BEGIN in path.read_text(encoding="utf-8"):
        text = path.read_text(encoding="utf-8")
        head, rest = text.split(GENERATED_BEGIN, 1)
        tail = rest.split(GENERATED_END, 1)[1]
        path.write_text(head + block + tail, encoding="utf-8")
    else:
        path.write_text(
            "# Conventions\n\n"
            "## Decisions (user)\n\nNone yet. Filled in from the user's answers at the inventory-review STOP.\n\n"
            "## Conflicts and gaps (flagged by Claude, not resolved)\n\nNone recorded yet.\n\n"
            f"{block}\n",
            encoding="utf-8",
        )
    return sum(len(sl.get("conventions", [])) for sl in slices)


def write_review_md(slices: list[dict], gaps: list[str], conflicts: list[str], rounding_only: list[str],
                    ragged: list[str], path: Path) -> None:
    """Write everything a human must look at: provenance gaps, numeric conflicts, ragged tables, ambiguities."""
    lines = ["# Items needing review", "", "Generated by `src/bbtools/merge_inventory.py`. Nothing here has been resolved.", ""]
    sections = [
        ("Items missing file or page", gaps),
        ("Numeric conflicts between sources (same constant, values disagree beyond rounding)", conflicts),
        ("Rounding-only differences (values agree at the coarser printed precision)", rounding_only),
        ("Tables whose rows do not match the header width", ragged),
    ]
    for title, items in sections:
        lines += [f"## {title} ({len(items)})", ""] + ([f"- {i}" for i in items] or ["- none"]) + [""]
    ambiguities = ordered(tagged(slices, "ambiguities"))
    lines += [f"## Extractor ambiguities ({len(ambiguities)})", ""]
    lines += [f"- {a['slice']} · {source_ref(a)}: {a['issue']}" for a in ambiguities] or ["- none"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Run the full merge and print item counts."""
    slices = load_slices()
    gaps = provenance_gaps(slices)
    tables, ragged = write_constant_tables(slices, INVENTORY / "constants")
    conflicts, rounding_only = numeric_conflicts(slices)
    counts = {
        "slices": len(slices),
        "topics": write_topic_index(slices, INVENTORY / "topic_index.json"),
        "formulas": write_formulas_md(slices, INVENTORY / "formulas.md"),
        "tables": len(tables),
        "worked_examples": write_worked_examples(slices, INVENTORY / "worked_examples.json"),
        "conventions": write_conventions_md(slices, INVENTORY / "conventions.md"),
        "ambiguities": sum(len(sl.get("ambiguities", [])) for sl in slices),
        "provenance_gaps": len(gaps),
        "numeric_conflicts": len(conflicts),
        "rounding_only_differences": len(rounding_only),
        "ragged_tables": len(ragged),
    }
    write_review_md(slices, gaps, conflicts, rounding_only, ragged, INVENTORY / "review_items.md")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
