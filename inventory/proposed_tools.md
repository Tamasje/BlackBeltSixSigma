# Proposed calculators

Ranked by how many questions of the example exam (`inventory/exam_map.json`) need a computation
from the tool, then by how much the course works with it (worked examples with a stated answer).
Only one example exam exists (7 questions, 5 of them mainly conceptual), so the lower ranks are
driven by course weight, not exam evidence.

A `Tables` sheet (constants from `inventory/constants/`) comes first in any case; the tools read
their constants from it. Which printed source it uses is convention question 4.

"Verifiable" = at least one course worked example with a stated numeric answer exists, so the
sheet can become VERIFIED. IDs refer to `inventory/worked_examples.json`.

| Rank | Tool | Exam questions | Course worked examples with answers | Verifiable |
|---|---|---|---|---|
| 1 | Process capability and % out of spec | Q3 (a, b, d) | 6 | yes |
| 2 | Normal probabilities and quantiles | Q3 (b), Q6 (c) | 3 | yes |
| 3 | Sigma level, DPMO, yield | Q3 (d) | 15 | yes |
| 4 | Variance CIs and tests (χ², F) | Q2 | 4 | yes (F: Dummies only) |
| 5 | Confusion-matrix metrics | Q5 | 0 (counts only, no metrics printed) | **no** |
| 6 | Distribution moments and probabilities | Q6 (a) | 2 (binomial only) | **partly** |
| 7 | CI and tests for mean and proportion (z, t) | (Q1, conceptual) | 9 | yes |
| 8 | Control charts (X̄-R, X̄-s, I-MR, p, u) | (Q4, conceptual) | 9 | yes |
| 9 | Gage R&R (average & range, ANOVA) | none | 2 | yes |
| 10 | Acceptance sampling (OC curve, AOQ) | none | 9 | yes |
| 11 | ANOVA, 2^k effects, simple regression | (Q7, conceptual) | 11 | yes |

## 1. Process capability and % out of spec

- Inputs: LSL, USL, mean, σ (given), or σ estimated from R̄/d2 or s̄ (convention 1).
- Outputs: Cp, Cpu, Cpl, Cpk; Z(LSL), Z(USL); % and ppm below LSL, above USL, total; Pp/Ppk when σ is overall.
- Formulas: Les 4 deck `2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf` p. 32–35 (Cp, Cpk), p. 39–40 (quality levels);
  Dummies p. 162–165 (Cp/Cpk/Pp/Ppk); `Acceptance Sampling.pdf` p. 10 (Cpk, within-subgroup σ).
- Worked examples: S06-WE01 (deck p. 46 + speaker notes: Cp 1,166, Cpk 0,67, 5 % total / 2,5 % per side);
  S06-WE04, S06-WE07, S06-WE08 (exercise workbooks); S06-WE12, S06-WE13 (Minitab Pp/Ppk, deck p. 49, 82).
- Verifiable: yes.

## 2. Normal probabilities and quantiles

- Outputs: P(X < x), P(X > x), P(a < X < b), x for a given tail probability, σ from a tail probability with a known mean (exam Q6c).
- Formulas: deck p. 18–19, 26 (standard normal, Z); `___1.1 Ztable.pdf` p. 1–2; `___1.2 statistische functionaliteit in excel.pdf` p. 1–3 (NORM.VERD, NORM.INV, NORMALISEREN).
- Worked examples: S06-WE09 (`__NormVerdeling Excel functies.xlsx`: NORM.INV(0.99; 20; 0.5) = 21.16317…);
  S06-WE10 (deck p. 19); S06-WE01 (Excel check NORM.VERD(71,4; 71,8; 0,2)).
- Verifiable: yes.

## 3. Sigma level, DPMO, yield

- Outputs: DPU, DPO, DPMO, first-time yield, RTY, normalized yield; Z ↔ DPMO with and without the 1.5σ shift (convention 3).
- Formulas: deck p. 19–20, 36; Dummies p. 150–160 (yield, DPU/DPO/DPMO, Z score, Table 6-3); Harry & Schroeder p. 3, 5.
- Worked examples: S08-WE01…S08-WE08; S09-WE01…S09-WE06; S07-WE01.
- Verifiable: yes. Note S09-WE05 prints an exponent that does not reproduce its own result (review_items.md).

## 4. Variance CIs and tests (χ², F)

- Outputs: CI for σ² and σ (χ²); CI for σ1²/σ2² (F); one-sided lower, one-sided upper, two-sided; F-test and χ²-test statistic and p-value.
- Formulas: `Test Recipes - Further Reading (Dutch).pdf` p. 11–14 (χ²-test σ, F distribution, F-test σ1/σ2);
  `Confidence Intervals - Further Reading (Dutch).pdf` p. 21 (CI σ²); `Confidence Intervals.pdf` p. 16; Dummies p. 194–196.
- Worked examples: S08-WE11 (Dummies p. 196, F CI [0.147, 3.199]); S08-WE10 (Dummies p. 195); S03-WE03 (CI deck p. 16, one-sided 98 %);
  S03-WE05 (TH deck p. 13).
- Verifiable: yes. The only F example is from Dummies; the Ottoy F material is a recipe without numbers.

## 5. Confusion-matrix metrics

- Outputs: accuracy, recall, precision, F1 for train and test, and the train–test gap.
- Formulas: `20260529_naert.pdf` p. 29–32.
- Worked examples: S02-WE04 (Les 6 p. 27) prints TN/FP/FN/TP only, no computed metrics. Les 6 is marked "Niet te kennen voor het examen".
- Verifiable: **no**. Needs `stats-auditor` or your acceptance as UNVERIFIED.

## 6. Distribution moments and probabilities

- Outputs: mean and variance of Bernoulli, binomial, Poisson, exponential, uniform and normal; P(X = k) and P(X ≤ k) via BINOM.DIST, POISSON.DIST, EXPON.DIST, HYPGEOM.DIST.
- Formulas: `20260522_naert_big data.pdf` p. 5–10, 26; `Acceptance Sampling.pdf` p. 12, 16, 20; `Acceptance Sampling.xlsm` sheet 'distributions'.
- Worked examples: S04-WE01, S04-WE02 (binomial defectives in a lot). None for Poisson or exponential.
- Verifiable: **partly** (binomial only).

## 7. CI and tests for mean and proportion (z, t)

- Outputs: CI for μ (σ known / unknown), for μ1 − μ2 (paired / unpaired), for π (normal approximation); z/t statistic, critical value, p-value; one- and two-sided.
- Formulas: `Confidence Intervals.pdf` p. 9–10; CI Further Reading p. 5–16, 20; Test Recipes p. 4–10; Dummies p. 189–198.
- Worked examples: S03-WE02, S03-WE04, S03-WE10, S03-WE13, S03-WE14, S03-WE15, S08-WE12, S08-WE13, S03-WE01.
- Verifiable: yes. Open issues: pooled-variance denominator (convention 8) and the √19 cell in `Confidence Intervals.xlsx` (convention 9).

## 8. Control charts (X̄-R, X̄-s, I-MR, p, u)

- Outputs: centre lines and control limits; σ = R̄/d2; limits from the Tables sheet.
- Formulas: deck p. 55, 62–63, 73 and speaker notes p. 64; `___4.1 tabellen SPC.pdf` p. 1–2; Dummies p. 116, 249, 254.
- Worked examples: S06-WE03, S06-WE05, S06-WE06 (exercise workbooks 2, 3, 5); S08-WE18…S08-WE21; S10-WE04a/b (Rheostat).
- Verifiable: yes.

## 9. Gage R&R (average & range, ANOVA)

- Outputs: EV, AV, GRR, PV, TV, %GRR vs TV and vs tolerance; ANOVA table with and without interaction.
- Formulas: `Black Belt in Six Sigma - Measurement System Analysis.pdf` p. 24–25, 34–37; `Theoretical background of a GRR study.pdf` p. 1–2; `tabel MSA.pdf` (d2*).
- Worked examples: S10-WE02 (ANOVA, %GRR 49.47 %), S10-WE03 (average & range).
- Verifiable: yes. Convention question 11.

## 10. Acceptance sampling (OC curve, AOQ)

- Outputs: P(accept) for (n, c) with binomial, hypergeometric or Poisson; AOQ, AOQL, ATI; plan from AQL/LQL.
- Formulas: `Acceptance Sampling - Further Reading.pdf` p. 4–11; `Acceptance Sampling.pdf` p. 16–27; `Testing of Hypotheses.pdf` p. 7–8.
- Worked examples: S03-WE06, S03-WE07, S03-WE20, S03-WE21, S04-WE10, S04-WE14, S04-WE15, S04-WE18, S04-WE19.
- Verifiable: yes. Convention question 12.

## 11. ANOVA, 2^k effects, simple regression

- Outputs: one-way ANOVA table; 2^k effects and coefficients; slope, intercept, R², CI for slope and mean response.
- Formulas: `20260605_de vuyst_BB_DOE.pdf` p. 3–11, 48–68; `20260605_de vuyst_BB_Regression.pdf` p. 16–37, 46–61; Dummies p. 202–233.
- Worked examples: S05-WE01, S05-WE02, S05-WE05…S05-WE09, S05-WE17, S05-WE18, S08-WE15, S08-WE16.
- Verifiable: yes. Several source inconsistencies (S05 and S08 ambiguities in review_items.md).
  Excel's Analysis ToolPak (an add-in, not VBA) also does ANOVA and regression, if the exam laptop has it.
