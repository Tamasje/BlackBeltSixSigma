# Rules for the content pass (Dutch study guide, Six Sigma Black Belt course)

Repository: /home/user/BlackBeltSixSigma. Parts: `resources/study/parts/NN_*.html` (+ `NN_symbols.tsv`, `NN_formulas.tsv`).
Edit ONLY the files assigned to you. Other helpers edit the other parts at the same time. Never run git, never write
the built guide (`studiegids.html`). The student uses this guide at an open-book exam; they asked for the changes
below, in their words where quoted.

## 1. Delete the orange "errors in the slides" boxes
Orange boxes are `<div class="box warn">…</div>`. Delete every warn box whose subject is an error, typo, misprint,
inconsistency or ambiguity IN THE COURSE MATERIAL (titles like "Fout in de slide", "Drukfout in de cursus",
"Verwisselde F-waarden", "Twee onduidelijkheden in de tekst", or a box that says a slide/table prints a wrong value).
Keep warn boxes that warn about the METHOD (conventions, two notations, factor 6 vs 5,15, specs vs individual values).

## 2. Remove all Excel references and Excel function names
"All references to excel and functions in all parts … they are already in the workbook. Just reference the right
sheet if you want to." So:
- Delete explanations of Excel functions (NORM.VERD, NORM.INV, NORM.S.INV, T.INV, T.DIST, CHISQ.*, F.INV, F.DIST,
  BINOM.DIST, HYPGEOM.DIST, POISSON, EXPON, STDEV(.S/.P), AVERAGE, COUNTIF, …), Dutch/English function names, Excel
  syntax (; vs , decimal comma), Excel walkthroughs, "in Excel" tables, `<code>…</code>` with Excel formulas.
- Where a step needs the value, write the statistical formula or the table instead (e.g. \(z_{0{,}99}=2{,}326\) from
  the Z-table or the calculator), and/or mention the guide's calculator ("rekenmachine normale verdeling", see §5) or
  the workbook sheet ("werkblad Normaal in bb_toolkit.xlsx"). Existing `<div class="box tool">Rekentool: blad …` boxes stay.
- Exercise solutions: rewrite the Excel steps with formulas/table/calculator; keep every answer value unchanged.
  An exercise question that only tests Excel syntax is deleted; a statistics question stays.
- Course files that are Excel workbooks may stay as SOURCE citations (`<a class="p" href="….xlsx">…`); just no Excel
  instructions.
- In your `NN_symbols.tsv`: the "hoe" column (how you get a symbol) must not name Excel functions; say formula, table,
  "gegeven" or the calculator instead. Keep the TSV format (tabs, same columns, header untouched).

## 3. Delete pointers that add nothing
Delete sentences like "Hoe je x̄ en s berekent (met n−1 in de noemer van s) staat in Deel 02; hoe zeker zo'n schatting
is, in Deel 04." — sentences whose only content is where something else is explained (forward OR backward). Keep a
reference only if the current step cannot be done without it. Course-page citations (`<a class="p" …>`) always stay.

## 4. Remove repeated information
"You still have a lot of repeating information in various parts … just delete it from part 3 and keep it for [the
part where it is treated in detail]. Do similar reductions for all parts because this way it's just too confusing."
Each topic has one home part, where it is explained in detail:
01 Lean Six Sigma, DMAIC, Define, team · 02 data, meetschalen, beschrijvende statistiek, kansen, verdelingen
(binomiaal, Poisson, …), kruistabellen, EDA, causaliteit · 03 normale verdeling, Z, Z-tabel, VoC/VoP, DPO/DPMO/yield,
sigmaniveau en 1,5σ · 04 betrouwbaarheidsintervallen, steekproefgrootte, tolerantie-intervallen · 05 hypothesetoetsen,
β/power, χ²-toetsen, niet-parametrisch · 06 aanvaardingssteekproeven, OC, steekproefmethoden · 07 regressie ·
08 ANOVA en DOE · 09 procescapabiliteit (Cp, Cpk, % buiten specificatie) · 10 SPC en regelkaarten (LCL, UCL, CL,
regels, subgroepen) · 11 MSA en Gage R&R · 12 machine learning · 13 voorbeeldexamen (keeps worked solutions) ·
14 extra uit de boeken.
If your part explains a topic whose home is another part, delete that explanation here. Keep at most one short
sentence if the flow of your part needs it (no pointer). KEEP sentences that give insight by contrasting two
concepts — the student's example to keep: "Wat buiten LSL of USL valt, is een defect … Belangrijk: 'The Voice of the
Process is independent of the Voice of the Customer'. Het proces weet niet wat de klant vraagt; het maakt zijn eigen
spreiding." When unsure whether something is a duplicate, keep it and list it in your report.
The table of contents of all parts: /tmp/claude-0/-home-user-BlackBeltSixSigma/23a9eac6-d90c-58bb-aa02-f3d30d431e93/scratchpad/toc.txt

## 5. Put the calculators where the theory is
"Repeat/mention the calculators also at the location where the theory about it is actually discussed … so during
the exam I can just search for DPO and find the calculator quickly. Even if in different parts … the standard normal
one is needed in exercise 4.1." Insert the marker
`<div class="calc-here" data-tool="TOOL" data-blocks="I"></div>`
(TOOL and block number I from the list below; several blocks: data-blocks="0 2") at the end of the unit (before its
pitfalls box) where the theory of that calculator is explained, and inside an exercise (before its hint) whose solution
needs that calculator. One marker per place; only where it really helps. The build turns it into a fold-out
calculator. List of calculators (tool block: title):
/tmp/claude-0/-home-user-BlackBeltSixSigma/23a9eac6-d90c-58bb-aa02-f3d30d431e93/scratchpad/blocks.txt

## 6. Broken numbers in formulas
An earlier conversion split numbers around fraction bars, e.g. `1\ 000\ \frac{000\cdot D}{N\cdot O}` (must be
`\frac{10^{6}\cdot D}{N\cdot O}`) or `9\ 192\ 631\ \frac{770}{299}\ 792\ 458` (must be
`\frac{9\,192\,631\,770}{299\,792\,458}`). Fix every such case in your files (HTML and TSV).

## Never
- Never change a number, answer (`data-answer`), formula meaning, `\sym{key}{…}` symbol key, figure, or course
  citation that you keep. Never invent numbers or facts. If a rewritten solution needs a value that is not yet in the
  part, compute it with python/scipy, mark it `<span class="computed">zelf berekend</span>`, and list it in your report.
- Never renumber units or exercises (the lead does renumbering afterwards). Do not delete the studiewijzer unit at the
  end of the part; update its table if a unit it links to disappears.
- Keep the plain Dutch of the surrounding text; no new opinions.

## Check and report
From `/home/user/BlackBeltSixSigma/resources` run `python3 study/build_study.py --check` (validates only). Problems in
YOUR parts must be fixed; problems in other parts belong to other helpers. Report briefly: per rule, what you
deleted/changed (counts, notable cases), every id you deleted (so links elsewhere can be fixed), the calculators you
placed (unit → tool block), any new computed values, and anything you were unsure about and kept.
