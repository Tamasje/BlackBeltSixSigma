# PROGRESS

Resume from this file after /compact or in a fresh session. The full brief (phases 0–3, STOPs,
acceptance list) was pasted by the user in the first message of session 2026-09-28; CLAUDE.md
holds the standing rules.

## Current phase
Phase 2 (workbook): sheet 1 (Tables + Capability) APPROVED and committed 2026-09-28; building tools 2-11 in approved order.
Phase 1 approved 2026-09-28 ("For all, do it so its just as clear as possible for me"); decisions in
inventory/conventions.md "Decisions (user)"; tools in inventory/approved_tools.md; oracle tagged `oracle-approved`.

## Done
### Phase 0 (approved 2026-09-28)
- Answers: example exam added; move Les folders into source/ OK; slices S01 (162 p) and S05
  (161 p) kept as is despite > ~150 p; Dummies + Harry & Schroeder extracted as course material
  (conflicts with lecture slides flagged, never resolved by Claude).
- User deleted the 5 zips (they were byte-identical to Les 1–5) and added `Les 6` (Naert lecture 3).

### Phase 1 setup (2026-09-28)
- Installed at user's request: pytest 9.1.1 (`python3 -m pip`, miniconda base 3.13.13),
  LibreOffice 26.8.0.3 (`brew install --cask libreoffice`; `soffice` at /opt/homebrew/bin).
- `git init`; layout from CLAUDE.md; `.gitignore` = source/, .DS_Store, __pycache__/, .pytest_cache/.
- Moved `Les 1`–`Les 6` to `source/course/`, exam DOCX to `source/exam/`.
- Derived PDFs added to source/ before locking it (user asked Claude to do the exports):
  - `Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf`: PowerPoint export of a scratch
    copy with all 14 hidden slides (4, 48–52, 76–83) unhidden, 89 pages, PDF page = slide number.
  - `Les 4/Control charts - constants.pdf` (2 p) and `source/exam/20251009_voorbeeldexamen six sigma.pdf`
    (9 p): LibreOffice export (Word's AppleScript export hung on a dialog).
- `chmod -R a-w source/`.
- Guard hook `.claude/hooks/protect_paths.py` + PreToolUse entry in `.claude/settings.json`
  (matcher Edit|Write|MultiEdit). Tested: blocks source/ (abs, rel, `..`, wrong case) and
  worked_examples.json only while tag `oracle-approved` exists. User must review/activate it in
  /hooks (interactive `claude` terminal) or restart the session.

## Source facts (verified)
- Dummies PDF: garbled text layer (font encoding), read visually. PDF page = printed page + 18.
- `___4.1 tabellen SPC.pdf`, `tabel MSA.pdf`: image-only scans. Constants DOCX = 4 JPEGs
  (table credited to "Six Sigma Demystified", 2nd ed.).
- Exam Q2 refers to an Excel data file ("het excel bestand ...") that is not in source/exam/.

## Slices (Phase 1)
| Slice | Files (all under source/course/) | Pages |
|---|---|---|
| S01 | Les 1: van volsem.pdf 1–162, ToC.html | 162 |
| S02 | Les 1 naert_big data 1–59, Les 2 naert 1–57, Les 6 naert 1–38, Les 6 ToC.html | 154 |
| S03 | Les 2: CI 1–16, CI FR 1–23, TH 1–13, TH FR 1–22, Test Recipes 1–26, CI.xlsx, TH.xlsx, ToC.html | 100 |
| S04 | Les 2: Acceptance Sampling 1–28, AS FR 1–18, AS.xlsm | 46 |
| S05 | Les 3: BB_DOE 1–94, BB_Regression 1–67, DOE_demo.xlsx, Regression_demo.xlsx, ToC.html | 161 |
| S06 | Les 4: deck PDF 1–89 (+pptx notes), Ztable 1–2, stat. functionaliteit 1–6, tabellen SPC 1–2, constants PDF 1–2, 6 xlsx, ToC.html | 101 |
| S07 | Les 4: Dummies 1–140 | 140 |
| S08 | Les 4: Dummies 141–258 | 118 |
| S09 | Les 4: Dummies 259–362, Harry-Schroeder 1–12, book summary 1–8 | 124 |
| S10 | Les 5: MSA 1–38, steel strip 1–2, meter unit 1–5, GRR theory 1–2, tabel MSA 1, GRR xlsx, Rheostat xls, linearity.txt, ToC.html | 48 |

### Phase 1 extraction and merge (2026-09-28)
- 10 course-extractor agents ran; all `inventory/raw/S01..S10.json` parse. 48 of 48 course files read, each in
  exactly one slice (Dummies split by disjoint page ranges); 1,154 PDF pages + 13 spreadsheets.
- `src/bbtools/merge_inventory.py` (run: `PYTHONPATH=src python3 -m bbtools.merge_inventory`) writes formulas.md,
  constants/*.csv (97 tables, provenance on every row), worked_examples.json (151), conventions.md (125 statements;
  hand-written sections outside the GENERATED markers survive reruns), topic_index.json (582), review_items.md
  (0 provenance gaps, 55 cross-source numeric conflicts, 23 rounding-only differences, 58 extractor ambiguities).
- Double transcription by Claude of both scans: `___4.1 tabellen SPC.pdf` (520 cells) and `tabel MSA.pdf`
  (798 values): 0 differences vs S06/S10. Remaining constant conflicts are between printed sources.
- `inventory/exam_map.json` (7 questions, 20 points, no answer key; 2 computational, 1 mixed, 4 conceptual)
  and `inventory/proposed_tools.md` (11 ranked tools) written by Claude.

### Phase 2, sheet 1 (2026-09-28, awaiting review)
- Code in src/bbtools/: printed.py (printed-number parsing, decision 10), constants.py (tables + decision 4
  USED_TABLE), constant_definitions.py (d2/d3 by integration, c4/c2 by gamma; used only for checks),
  recalc.py (LibreOffice headless, throwaway profile, xlsx-skill approach), xlsx_style.py (header block,
  input yellow / output green), sheet_tables.py, sheet_capability.py, readme.py, build_workbook.py.
  Build: `PYTHONPATH=src python3 -m bbtools.build_workbook` -> build/bb_toolkit.xlsx (openpyxl file,
  fullCalcOnLoad; LibreOffice recalculates a copy: 88 formulas, 0 errors) + build/README.md.
- pytest (pyproject.toml; importlib mode, strict markers, xfail_strict): 84 passed, 8 strict xfails (printed
  course values on deck p. 46 and p. 49 that disagree with the computation; listed in build/README.md).
- Constant check: 94 of 991 printed constants differ from their definition at printed precision; 60 by <= 1
  unit of the last digit, 34 more (pinned in tests/test_constant_definitions.py, listed in build/README.md):
  Table 18 D1-D4 for n >= 11 (up to 4 units), Table A d3(21) = 0.7272 (def. 0.7242), Six Sigma Demystified
  B6(2) = 3.267 (def. 2.606, printed on a stray row). Transcriptions never changed.
- ruff/mypy not installed; not run.

## Answered questions (inventory-review STOP; decisions in inventory/conventions.md)
Convention questions (details and sources in inventory/conventions.md, "Conflicts and gaps"):
1. σ for capability from data: R̄/d2; s̄ directly (deck p. 46) or s̄/c4; overall STDEV.S for Pp/Ppk; MR̄/1.128 for individuals?
2. "6 sigma criterion" (exam Q3d): 3.4 ppm (1.5σ shift) or 0.002 ppm (Cp = 2, short term), or show both?
3. Sigma level ↔ DPMO: apply the 1.5σ shift by default, show unshifted too?
4. Constants source for the Tables sheet: Table 18 (Crow/ASTM, used by lecturer's workbooks) + Table A (Wheeler), or Six Sigma Demystified, or all side by side?
5. Default α: required input with no default, or prefilled 0.05?
6. One- vs two-sided: show lower, upper and two-sided side by side?
7. F intervals: use F.INV/F.INV.RT directly and show both ratio orientations?
8. Pooled variance denominator: n1+n2−2 (consistent with the slide's t df) despite the printed n1+n2−1?
9. √19 cell in Confidence Intervals.xlsx: test against the slide's 9.98 and TH.xlsx, exclude the CI.xlsx cached value?
10. Test tolerance: match stated answers after half-up rounding to their printed precision?
11. Gage R&R (if approved): multiplier 6 vs 5.15; %GRR basis; thresholds; interaction-pooling α; ndc omitted?
12. Acceptance sampling β default (if approved): 10 % or 5 %?
13. Minimum subgroups note: 20 or 25?
14. Les 6 (not examinable): keep in the index flagged, or drop?
Other:
15. Which tools to approve, in what order (proposed_tools.md)?
16. stats-auditor for tools without a course worked example (confusion-matrix metrics; Poisson/exponential parts of distribution moments)?
17. Exam Q2 refers to an Excel data file that is not in source/exam/: do you have it?
