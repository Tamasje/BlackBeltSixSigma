# PROGRESS

Resume from this file after /compact or in a fresh session. The full brief (phases 0–3, STOPs,
acceptance list) was pasted by the user in the first message of session 2026-09-28; CLAUDE.md
holds the standing rules.

## Current phase
Study guide STOP, 2026-10-06: study/studiegids.html (Dutch study guide of the whole course, bilingual search,
202 interactive exercises, a "Hulpmiddelen" dropdown with calculators and course tables per part, clickable
variables in every formula, "Valkuilen en strikvragen" boxes) is built and tested; waiting for the user's review
before committing study/ and Phase 3.
Phase 3 (index) STOP since 2026-10-05: build/index.html waits for the user's offline link test.
Phase 2 complete: all 11 approved tools have a sheet; stats-auditor run; build/README.md and /add-calculator exist.
Decisions 18-20 (2026-10-05) in inventory/conventions.md; oracle updated once with the user's approval (commit
3cad3e4: S02-WE09 added, S05-WE09 corrected) and re-tagged `oracle-approved` there.

## Open items for the user
1. Review study/studiegids.html (open it from the folder; keep source/ next to study/), then approve the commit of
   study/, tests/test_study_tools.py and Phase 3.
2. Test the index links offline (Phase 3 STOP).
3. Still pending from earlier: activate the guard hook in /hooks; set the /goal line.
4. S11 worked examples (S11-WE01..06) are in inventory/raw/S11.json but not in the oracle (locked). None needs
   a calculator: Beta(2,8) figure, Poisson (= S02-WE09), the production-lines exercise (= S02-WE01, now with
   answers), the copper exercise (qualitative), regression dilution (α' ≈ 0.94), Beta-binomial coin.
5. Oracle remarks from the study-guide writers (oracle not edited; needs approval to change): S03-WE11 'true mean
   1270' (TH FR p. 9 figure and the stated β 16 % / 1 % imply 1300); S03-WE15 cites CI FR p. 20 for [0.53, 0.67],
   which is on TH FR p. 20; S03-WE16 lists UTL 5.55, which does not follow from the printed Ȳ + kσ (6.06);
   S06-WE05/WE06 R̄ label (0.0001767 printed vs the workbook's named range 0.0001748).
6. Calculator conventions chosen where the course is silent (labelled in the tools; change on request): covariance
   shown with n − 1 and n; no t-test on r; run rules 2-3 count points on one side (Dummies p. 246 is stricter);
   confusion matrix rows = actual by default; Beta mode/median as in the course figure; bias test d2 from tabel MSA;
   two-sided β from the course procedure (graph only in the course); no t-test β; σ-unknown sample size omitted.

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
| S11 | ugain.naert.net prints (2026-10-05): Les 1 web lecture 1 notes 1–30, Les 2 web lecture 2 notes 1–25, Les 2 web lecture 2 slides 1–59 | 114 |

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
  course values on deck p. 46 and p. 50 that disagree with the computation; listed in build/README.md).
- Constant check: 94 of 991 printed constants differ from their definition at printed precision; 60 by <= 1
  unit of the last digit, 34 more (pinned in tests/test_constant_definitions.py, listed in build/README.md):
  Table 18 D1-D4 for n >= 11 (up to 4 units), Table A d3(21) = 0.7272 (def. 0.7242), Six Sigma Demystified
  B6(2) = 3.267 (def. 2.606, printed on a stray row). Transcriptions never changed.
- ruff/mypy not installed; not run.

### Phase 2, tools 2-11 (2026-09-28)
- One commit per tool (9c794c9 … ea75931): Normal, Sigma & DPMO, Variance CI & tests, Confusion matrix,
  Distributions, Mean & proportion, Control charts, Gage R&R (+ MSA d2* table on Tables), Acceptance sampling,
  ANOVA DOE regression. Build: 3,334 formulas, 0 LibreOffice errors.
- pytest: 255 passed, 31 strict xfails (printed course values that disagree with the computation, each with
  file + page, listed per sheet in build/README.md); oracle diff against `oracle-approved` empty.
- stats-auditor (.claude/agents/stats-auditor.md; run as a sonnet general-purpose agent with that file's
  instructions, since new agent types load only in a new session): PASS for Confusion matrix (26 values),
  Variance F part (28), Distributions Bernoulli/Poisson/exponential/uniform (14); see open question 1.
- .claude/commands/add-calculator.md: gate on approved_tools.md and the oracle, build, test, STOP for review,
  commit, audit.

### Phase 3 (2026-09-28, awaiting link test)
- src/bbtools/build_index.py -> build/index.html (run: `PYTHONPATH=src python3 -m bbtools.build_index`): one
  static file, inline CSS + a filter box; calculators, exam question map (question -> course pages ->
  calculator sheet), 582 topics and 300 formulas with relative links `../source/...pdf#page=N`; Les 6 flagged.
- tests/test_build_index.py: no http(s) or external resources; every link resolves to an existing file and a
  PDF page within its page count (pdfinfo); every topic, formula and question listed; Les 6 flagged.
- Dummies pages in the inventory are PDF page indices (checked: PDF p. 233 = printed p. 215), so links land.
- Full suite 2026-10-05 (after S11): 261 passed, 29 strict xfails, exit 0; oracle diff against the new tag empty.

### ugain.naert.net (2026-10-05, decisions 18-20)
- Site = Naert's 3 lectures (slides + full notes). Lecture 1 and 3 decks identical to the course PDFs (59, 38
  slides); lecture 2 deck has 59 slides vs 57 (new: 46 "Trainingskeuzes bij beslissingsbomen", 55 "Bayesiaanse
  inferentie"). Lecture 3 study guide: "niet te kennen voor het examen" (not saved).
- Printed with local headless Chrome (throwaway profile) into source/course/ (lock lifted per folder and
  restored): Les 1/20261005_naert_web_lecture 1 notes.pdf (30 p; the 5 collapsed boxes expanded before
  printing, so exercises and answers are included), Les 2/20261005_naert_web_lecture 2 notes.pdf (25 p, no
  collapsed boxes), Les 2/20261005_naert_web_lecture 2 slides.pdf (59 p).
- Slice S11 extracted (54 topics, 41 formulas, 27 tables, 6 worked examples, 68 conventions incl. both
  study guides, 19 ambiguities); numbers in non-figure tables and examples checked against the text layer.
  Merge with the oracle locked: 636 topics, 341 formulas, 124 tables; oracle unchanged.

### Study guide (2026-10-06, awaiting review)
- study/parts/NN_*.html (Deel 00-13, Dutch prose + English terms, written per lecturer/topic from
  source/course_reduced's presented slides; links to source/course PDF pages), NN_numbers.py (every computed
  value and every exercise answer; all 13 exit 0), NN_glossary/formulas/errata.tsv.
- study/build_study.py -> study/studiegids.html: 14 parts, 202 exercises, 2,223 slide links, validated (files,
  PDF page ranges, ids, no http, every exercise has a solution).
- Hulpmiddelen per part (2026-10-06, user request): study/assets/stats.js (distributions; vs scipy 1e-7),
  calc.js (23 calculators porting the workbook formulas, constants per decision 4 and tabel MSA), tools.js (UI),
  course tables as printed in <template>s (Z table, sigma tables, Dummies t/χ²/F, control-chart constants, d2*).
  tests/test_study_tools.py: 37 passed (course worked examples S03-WE13/20/21, S04-WE16/18, S05-WE01/07/17,
  S06-WE03, S10-WE02/03, the course sigma tables; scipy/statsmodels for random inputs). Browser-checked.
- Les 4 citations (user request 'everywhere'): deck footer = PDF page − 1 fixed in 93eccda; 2026-10-06 also
  Dummies Table 1-2 p. 42 -> 41 (raw S07 + merge, conventions decision 3, sheet_sigma), decision 13 '25
  subgroups' Dummies p. 248 -> 244, Gage R&R sheet 'Gauge R&R ≤ 20 % of tolerance' deck p. 60 -> 61.
  Workbook rebuilt (3,334 formulas, 0 errors); affected suites 118 passed, 8 strict xfails; oracle unchanged.

### Study guide: clickable variables and pitfalls (2026-10-06, user request)
- Every variable in every formula (formula blocks, inline formulas, exercises, solutions, NN_formulas.tsv) is a
  <var data-s="key">; clicking it shows NN_symbols.tsv's meaning, how to get it, and a link to the explaining unit
  (831 symbols, 11,733 vars; build validates keys and anchors; tests/test_study_guide.py requires every formula block
  to have one). 173 "Valkuilen en strikvragen" boxes (Juist/Fout statements and computing traps, course page links;
  general statistics marked "algemeen"), collected in the #valkuilen overview. Done per part by agents; a checker
  proved the existing text unchanged (markup only). Formula font Georgia (Cambria Math drew X̿/R̿ as boxes).
- Search: a multi-word query now translates glossary terms in place ("pitfall p-value" -> "valkuil p-waarde").
- Small fixes found on the way: exercise 12.11(e) option; Deel 13 Q4c link p. 73; Deel 08 unit 8.9 n -> r (MSA
  notation); Deel 04/05 Dummies labels now PDF pages (were printed pages); Dummies F-interval upper bound 1.938
  (was 1.937; 0.5333 × 3.633 = 1.93765) in Deel 04, sheet_variance DOC/README and a test reason; AS p. 26
  'non-defectives' added to 06_errata.tsv.

### Study guide: all calculators the exercises need (2026-10-06, user: "include all calculators i would need")
- Audit of all 202 exercises against the calculators; course formulas, conventions and test values specified per
  calculator from the course pages (scratch specs), then implemented in study/assets/calc.js + tools.js:
  sample size (full width, CI p. 7/10), tolerance intervals (σ known/unknown, distribution-free; CI FR p. 22-23),
  β/power/n of Z-tests for µ and π (TH FR p. 7-14), χ² goodness of fit and contingency with Yates (TR p. 15-20),
  Mann-Whitney, signed ranks, runs (TR p. 21-26, no tie correction; z with and without continuity correction),
  stratified vs SRS variances (AS p. 16-19), inverse OC (AQL/LQL of a plan), (n, c) plan search (binomial, as the
  guide; Peach table not in the course files), double plan OC/ASN (AS FR p. 5), SPRT (AS FR p. 6-8), variables plan
  for a given n (AS p. 26-27), skip-lot and Deming (AS FR p. 11-15); descriptives and correlation (covariance with n-1
  and n, labelled), regression from sums/SS/summary values, partial F (REG p. 61), multiple regression with
  second-order/polynomial terms and centring (REG p. 46-62), two-way ANOVA with/without replication (GRR workbook
  layout, + pooled table), limits from standard values (Table 7.2), Western Electric rules 1-8 (SPC p. 68; rules 2-3
  per side as the linked WE rules), observed vs actual Cp (MSA p. 24-26), gauge performance curve (p. 27),
  uncertainty budget and propagation (p. 28-29, steel strip), bias test (p. 31-32, tabel MSA ν/d2*), discrimination
  rule (p. 30), Bayes and Beta posterior (ML p. 53, web slides p. 55), k-class confusion matrix (orientation switch).
  The four guide-only calculators of the earlier question are kept (user: include all calculators needed).
- tests/test_study_tools.py: 62 tests (course printed values, course workbook cells, scipy/statsmodels).

### Study guide: folding and ranked search (2026-10-07, user request)
- Every part, unit and exercise folds by clicking its heading; "Alles in" / "Alles uit" in the top bar; links, search
  results, symbol pop-ups and the contents unfold what they point to. The contents is foldable per part.
- Search ranks by relevance: phrase or words in the title (10/4), in the author keywords (6/2), occurrences in the body
  (capped), +4 when the part title contains it; the query and its exact translation weigh 1, in-place translations 0.9,
  longer glossary terms containing the query 0.6; units 1, calculators 0.9, exercises 0.85, table rows 0.5. Shows at
  most 8 best hits (>= half of the top score, no table rows, each calculator once with "ook in"), the rest folded per
  part. One- and two-letter words (t, z, F) must stand alone. Example: "t-test" -> 8 best of 44.

### Study guide: standalone text and figures (2026-10-07, commit 446b13b)
- No lecturer names or slide-dependent phrasing; 270 course figures placed where the text discusses them.

### Study guide: formulas in LaTeX (2026-10-07, user request step 2; cloud session without source/)
- Every typed formula in study/parts (HTML fragments, NN_formulas.tsv formule_html, NN_symbols.tsv symbool/betekenis/hoe)
  is now LaTeX: \( … \) inline, \[ … \] in formula blocks and the formula sheet; the build turns it into MathML (pandoc).
  a / b → \frac, √ → \sqrt, accents → \bar/\hat, Excel calls → \operatorname{T.INV}; every <var data-s="key"> became
  \sym{key}{…}, so variables stay clickable. 9,424 formulas converted by a one-off script; a checker rendered each one
  with pandoc and proved every letter and digit and every variable key survives in order (0 problems). The "Wat"
  column of the formula sheet stays plain text (it is also a search attribute).
- Build validated with links into source/ not checkable (source/ absent in the cloud container); all other checks pass.
  pytest, scipy and openpyxl are not installed there, so tests/ was not run; rerun `pytest` locally.

### Study guide: tools deduplicated, calculators in every direction (2026-10-07, user request step 1)
- Tables that repeated each other are now one table each: the four sigma tables (SPC p. 21, LSS p. 7, Dummies p. 41,
  160) → one row per sigma level, each printed DPMO/yield once with its source where they differ; the five
  control-chart constant tables (Table 18, Table A, SSD p. 1-2, Dummies Table 10-2) → one column per symbol with the
  value the calculators use (decision 4) and a grouped list of the places where printed tables differ beyond rounding.
  The Z table moved into the normal-distribution tool (the cell of the computed z is highlighted); the Dummies t/χ²/F
  tables are gone (the quantile calculator gives both directions). Tools removed: ztabel, sigmatabellen,
  sigmatabellen_extra, dummiestabellen, constanten_extra (their search keywords moved to the tools that replace them).
- New solvers (study/assets/calc.js), each fills in whatever is missing: sigmaSolve (D, N, O, DPO, DPMO, yield, Z,
  sigma level), normalInterval (µ, σ, a, b, k, fraction inside/outside), capabilitySolve (LSL, USL, µ, σ, Cp, Cpk,
  ppm; one-sided and centred cases), limitsInverse (control limits → X̿, R̄, s̄, σ̂), sampleSizeSolve (two of α, W, n),
  detectableShift (smallest µ1 for a β), binomial/Poisson/hypergeometric quantiles, exponentialSolve; σ/√n any two of
  three; quantile and p-value blocks merged into one block.
- tests/test_study_tools.py: 10 new tests (course sigma table both ways, SPC p. 40 Cp = 2 → 0.002 ppm, TH FR p. 9
  n = 195 → 1300, merged tables keep every printed number, scipy cross-checks). Not run here (no pytest/scipy); the
  same assertions were replayed in node with stdlib expected values: all pass. Browser check: panels compute, no errors.

### Study guide: "Fouten in de slides" and the NL ↔ EN glossary removed (2026-10-07, user request step 3)
- Both end sections and their contents entries are gone; the 13 links to #fouten in the parts and two tool notes were
  rewritten (each erratum is still explained where the text discusses it). NN_glossary.tsv stays: the search still
  translates Dutch ↔ English with it (checked in the browser). NN_errata.tsv files are no longer read by the build;
  not deleted (CLAUDE.md: ask before deleting outside build/).

### Verification with source/ present (2026-10-07, cloud session; user pushed source/ to main)
- main merged into the branch (49ed52b); main also carried an unfinished earlier copy of the solvers and of the
  Deel 05/11 LaTeX conversion: this branch's finished versions kept. study/parts/extra/ (draft Deel 14 fragments, all
  already in 14_extra_boeken.html, not read by the build) kept as pushed.
- pytest (installed in the container, plus scipy, statsmodels, pandas, openpyxl, xlrd, matplotlib): 344 passed,
  29 strict xfails (the printed course errors, unchanged); 2 failures only because tag oracle-approved is not on
  GitHub (tags were not pushed); worked_examples.json unchanged since 93eccda. build_study.py with full link and
  page-range validation: no problems.
- Figure gaps closed: 11.x linearity exercise now shows the plot of linearity.txt (11_numbers.py --figures writes
  study/figures/11_lineariteit_oefening.png); 09.x "de figuur op SPC p. 41" now points to the figure in 09.5.
- Formulas in the Hulpmiddelen: every calculator block (82) now opens with a "Formules en betekenis van de
  symbolen" panel from study/tool_formulas.html: the formula in LaTeX, each symbol clickable with meaning, "Hoe bekom
  je het?" and "Meer uitleg", as in the formula sheet; formulas the course does not print are marked algemeen.
  build_study.py validates every symbol; a test checks that every calculator block has its formulas. Help texts and
  labels that repeated the formula were shortened (e.g. hypergeometric k = number of defectives in the sample).
- Sharing: no absolute paths or OneDrive references in the repo; all links are relative (../source/...). All 45
  linked course files open in Chromium from file://. ERR_ACCESS_DENIED on the user's Mac comes from OneDrive
  (online-only files) or macOS file permissions; 00_start.html now explains the fix.
- Calculators in the study guide: a field the calculator derives from the others is filled in, turns red and is
  locked (read-only); emptying a given field unlocks it; every block has a "Wis alles" button. Pasted data also
  fill and lock the summary fields (n, x̄, s). Node test: blocks report only fields that were left empty.
- New tool 12, conditional probabilities (user request 2026-10-08; inventory/approved_tools.md): in the guide (part 02)
  and as Excel sheet "Voorwaardelijke kansen": cross table (names, Totaal ignored) or raw data, P(asked | given) from
  dropdowns (complements included) with numerator and denominator, marginals, P(Y | X), P(X | Y), P(X)·P(Y),
  independence as in Data p. 25 and the χ²-test (Test Recipes p. 18-20). Tested against S02-WE01 and scipy.
- Excel data areas open-ended: raw value columns read to row 100 000 (variances, means, ANOVA groups, regression
  pairs); per-row tables pre-filled: control charts 1000 subgroups × 25 values, I-MR / p / u 2000 rows each side by
  side, conditional raw data 10 000 rows; Gage R&R reads k (≤ 20 operators, names in column A), n (≤ 50 parts) and
  r from the data (MSA K3 needs n ≤ 20, else that component stays empty). "ANOVA DOE regressie" split into
  "ANOVA (eenweg)" (50 groups), "DOE 2^k" (20 replicates) and "Regressie" (one tool per sheet), data blocks last.
  Every paste area has a "Zo vul je … in" block (text vs numbers, where, how to clear) and checks that count the
  numbers and report text. Sheet tests build only their sheet plus Tabellen; the whole workbook is recalculated in
  test_build_workbook (92 127 formulas, 0 errors).
- Constants where they are used: Regelkaarten (A2, D3, D4, A3, B3, B4, d2, c4), Capabiliteit (d2, c4) and Gage R&R
  (tabel MSA d2*) show the values the sheet computes with (lookups into Tabellen; tested against the printed
  tables). Guide: the constants table also in parts 11 and 13.
- Layout for sharing (user request 2026-10-08): the top of the folder holds only studiegids.html and bb_toolkit.xlsx;
  everything else moved (git mv) into resources/ (source/, study/, src/, tests/, inventory/, build/). Guide links are
  written relative to study/, checked there, and rebased on output (resources/source/…). Claude files (CLAUDE.md,
  .claude/, PROGRESS.md) are git-ignored and no longer tracked; run builds and tests from resources/.

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
