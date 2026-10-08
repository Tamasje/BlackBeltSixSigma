# Six Sigma Black Belt exam toolkit

Purpose: an offline toolkit for an open-book Black Belt exam on a laptop with no internet:
(1) an Excel workbook of verified calculators, (2) a static HTML index into the course material.
Claude is NOT available during the exam: everything must work offline, without macros, and be
usable by a human under time pressure.

## Numerical integrity (highest priority)
- Never invent numbers. Every constant, table value, default (e.g. α) and expected test value
  comes from the course in `source/` (cite file + page) or is computed by code in this repo.
  Nothing from memory or general textbooks.
- The course's conventions override textbook conventions. If the course is silent or
  inconsistent (σ estimate for capability, 1.5σ shift, Gage R&R method, one- vs two-tailed
  defaults, rounding), stop and ask me. Record decisions in `inventory/conventions.md`.
- `inventory/worked_examples.json` is the test oracle. Never edit it to make a test pass. If the
  course's stated answer and an independent computation disagree, stop and report both with
  the source page.

## Layout
The top of the project folder holds only the two deliverables, `studiegids.html` and `bb_toolkit.xlsx`
(generated, never hand-edited). Everything else lives in `resources/`; paths below and in `.claude/` are relative to
it (run tests and builds from `resources/`).
- `source/course/`, `source/exam/`: read-only. Never modify, move or delete.
- `inventory/`: extraction output (`raw/` per slice; merged files at top level).
- `src/bbtools/`: Python package that generates the workbook and the index.
- `study/`: the study guide's parts and build script (writes `../studiegids.html`).
- `tests/`: pytest.
- `build/`: generated `index.html` and `README.md`. Never hand-edited.
- Claude files (`CLAUDE.md`, `.claude/`, `PROGRESS.md`) are git-ignored: local only.

## Excel rules
- `.xlsx`, formulas only. No VBA, no external links. No spilling/dynamic-array functions (LET,
  LAMBDA, XLOOKUP, FILTER, SORT, UNIQUE, SEQUENCE) until I confirm the exam machine's Excel version.
- Post-2007 function names written through openpyxl (NORM.S.INV, T.INV.2T, CHISQ.INV.RT,
  F.INV.RT, STDEV.S, …) need the `_xlfn.` prefix or Excel shows #NAME?.
- Use only functions that both Excel for Mac and LibreOffice evaluate (LibreOffice is the
  test-time recalc engine).
- One tool per sheet. Header block on each sheet: tool name, course source (file + pages),
  convention used, status VERIFIED / UNVERIFIED.
- Inputs in one fill colour, outputs in another.
- VERIFIED = at least one passing test against a course worked example or example-exam answer.

## Code
- Python 3, type hints, a docstring stating each function's purpose, small single-purpose
  functions, comments that explain why.
- pytest. Each sheet is tested against course worked examples and an independent
  scipy/statsmodels cross-check.
- Recalculate with LibreOffice headless before reading values back (openpyxl writes no
  cached values).
- Make only the changes required for the task. No extra features, sheets, abstractions or files.

## Stop and ask before
- Installing anything (pip, brew) or any network use.
- Deleting or overwriting anything outside `build/`.
- Adding a tool not listed in `inventory/approved_tools.md`.
- Any convention the course does not state.
- The same error surviving 2 fix attempts.

Commit after each checkpoint I approve.