---
description: Add one approved calculator sheet to build/bb_toolkit.xlsx (build, test, review, commit, audit)
argument-hint: <tool name as listed in inventory/approved_tools.md>
---
Add the calculator named "$ARGUMENTS" to the toolkit, following CLAUDE.md. Work on this one tool only.

## 0. Gate (stop here if any check fails)
1. Read `inventory/approved_tools.md`. If "$ARGUMENTS" is not listed there, STOP and say so. Do not build a
   tool that is not approved.
2. Read `inventory/conventions.md` (decisions) and find the course pages for the tool in `inventory/formulas.md`
   and `inventory/topic_index.json`.
3. Find the worked examples for the tool in `inventory/worked_examples.json` (the locked oracle). If the tool
   needs a worked example that is not in the oracle, STOP and say which one; never add to or edit the oracle.
   If there is none at all, the sheet will be UNVERIFIED and gets the stats-auditor (step 4).
4. If the tool needs a convention the course does not state, or the course is inconsistent, STOP and ask.

## 1. Build the sheet
- New module `src/bbtools/sheet_<name>.py` exposing `SHEET`, `HEADER`, `DOC`, `INPUTS`, `RESULTS` and
  `build_sheet(ws)`, in the style of the existing sheet modules. Register it at the end of `TOOL_SHEETS` in
  `src/bbtools/build_workbook.py`.
- Header block complete: tool name, course source (file + pages), convention used, VERIFIED / UNVERIFIED.
- Formulas only; inputs yellow, outputs green (`bbtools.xlsx_style`). No VBA, no external links, no LET, LAMBDA,
  XLOOKUP, FILTER, SORT, UNIQUE, SEQUENCE; `_xlfn.` prefix on post-2007 functions; only functions LibreOffice
  also evaluates.
- Constants come from the Tables sheet by workbook name (`bbtools.sheet_tables.lookup_formula`). If the tool
  needs a constant table that is not there yet, add it from `inventory/constants/` with a test that compares
  every printed value with its definition; report mismatches, never overwrite a printed value.

## 2. Test
- `tests/test_sheet_<name>.py`: each worked example at printed precision (decision 10) or, for Excel cached
  floats, rel=1e-9; plus an independent scipy/statsmodels cross-check on random inputs.
- A printed value that disagrees with the computation is a strict xfail whose reason cites file and page, and a
  line in the module's `DOC.disagreements`. Stop and report it; do not adjust the sheet to match it.
- Rebuild: `PYTHONPATH=src python3 -m bbtools.build_workbook` must report 0 formula errors.
- Run `python3 -m pytest -q`: it must exit 0, and `git diff oracle-approved -- inventory/worked_examples.json`
  must be empty.

## 3. Review and commit
- STOP and show the sheet (inputs, outputs, sources, any disagreements) for approval.
- After approval: update `PROGRESS.md`, commit as "Phase 2 tool: <name> …", and print ✅ <sheet name>.

## 4. Audit (UNVERIFIED sheets and blocks without a course worked example)
- Run the `stats-auditor` agent. Give it only the course files and pages the sheet cites, one test input and the
  values the sheet produced for it. No generator code, no sheet formulas.
- FAIL: fix and re-audit, at most 2 fix rounds; then stop and report.
- Record the result (PASS, or FAIL with the discrepancy) in the module's `DOC.audit`; rebuild so it reaches
  `build/README.md`. An audit does not make a sheet VERIFIED.
