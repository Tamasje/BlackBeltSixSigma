# PROGRESS

Resume from this file after /compact or in a fresh session. The full brief (phases 0–3, STOPs,
acceptance list) was pasted by the user in the first message of session 2026-09-28; CLAUDE.md
holds the standing rules.

## Current phase
Phase 1 (inventory), in progress. Next STOP: inventory review.

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

## Open questions
- (none yet; convention questions are collected at the inventory-review STOP)
