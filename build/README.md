# bb_toolkit.xlsx

Offline rekenbladen (calculators) voor het Black Belt-examen. Gemaakt door `src/bbtools/` (`PYTHONPATH=src python3 -m bbtools.build_workbook`); nooit met de hand aanpassen.

**Gebruik:** typ alleen in de gele cellen; groene cellen zijn resultaten. Een resultaatrij blijft leeg tot de invoer die ze nodig heeft is ingevuld. Elk blad begint met de bron in de cursus, de gebruikte conventie en de verificatiestatus. Excel herberekent het hele bestand bij het openen.

**Extra (boeken):** het blad *Extra (boeken)* bevat de rekenblokken die alleen uit Six Sigma For Dummies en Harry & Schroeder komen. Die boeken zijn niet te kennen voor het examen.

**Cursusindex:** `index.html` naast dit bestand linkt elk onderwerp, elke formule en elke vraag van het voorbeeldexamen naar de pagina in de cursus (`PYTHONPATH=src python3 -m bbtools.build_index`). Houd `source/` naast `build/`.

## Capabiliteit: Procescapabiliteit (process capability): Cp, Cpk (Pp, Ppk) en % buiten specificatie (out of spec)

- **Doel:** Cp, Cpk (of Pp, Ppk), Z-afstanden en % / ppm buiten specificatie uit LSL, USL, gemiddelde en een spreiding; de twee lezingen van het '6 sigma'-criterium in de cursus; de Cp-niveaus van deck p. 40.
- **Invoer:** LSL en/of USL, gemiddelde; dan eender welke van: σ gegeven, R̄ (+ n), s̄ (+ n), totale s. Elke spreiding krijgt haar eigen resultaatrij, met de cursuspagina die ze gebruikt. MR̄ / 1,128 (alleen in Six Sigma For Dummies) staat op blad Extra (boeken).
- **Bron in de cursus:** source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 18-21, 32-47, 50, 64, 83; ___4.1 tabellen SPC.pdf p. 1-2; __Xbar R kaart data - berekeningen oefening 2.xlsx
- **Conventie:** Beslissingen 1-2: één resultaatrij per σ-schatting die de cursus gebruikt (er wordt niet voor je gekozen); het '6 sigma'-criterium in beide lezingen van de cursus.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte voorbeelden S06-WE01, S06-WE02, S06-WE04, S06-WE07, S06-WE08, S06-WE12, S06-WE13 uit de cursus; enkele gedrukte waarden op deck p. 46 en 50 wijken af van de berekening (zie build/README.md)
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - deck p. 46 (S06-WE01): Cp gedrukt als '1,166' (1,4/1,2 = 1,1667 rondt af op 1,167); gecentreerde Cpk idem.
  - deck p. 46 notities (S06-WE01): '5 % totaal' en '2,5 % per zijde' voor gemiddelde 71,8, σ 0,2, specificatie 71,4-72,8; de normale verdeling geeft 2,275 % onder LSL en 0,00003 % boven USL (2,275 % totaal).
  - deck p. 46 notities (S06-WE01, gecentreerd): '0,04 % / 400 ppm' tweezijdig verdubbelt de afgeronde 0,02 % / 200 ppm; berekend 0,0465 % / 465 ppm.
  - deck p. 50 (S06-WE12, Minitab): '% out of spec' 8,74 en 9,33 tegenover 8,731 en 9,315 berekend uit het gedrukte gemiddelde 0,14852; Minitab rekende met niet-afgeronde data. Pp, Ppk, Cp en Cpk kloppen.

## Normaal: Normale verdeling (normal distribution): kansen, waarden, μ ± kσ, σ of gemiddelde uit een staartfractie

- **Doel:** P(X < x), P(X > x), P(a < X < b); de waarde x bij een kans; μ ± kσ en het aandeel daarbinnen; σ (en variantie) of het gemiddelde uit een bekende staartfractie (tail fraction), bv. '2 op 40 onder 720 bij gemiddelde 820'.
- **Invoer:** gemiddelde μ en σ, dan per blok: x; a en b; een kans p; k; een grens L met de fractie f voorbij L.
- **Bron in de cursus:** source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 16-19, 27; ___1.1 Ztable.pdf; ___1.2 statistische functionaliteit in excel.pdf p. 1-3; __NormVerdeling Excel functies.xlsx
- **Conventie:** De normale functies van Excel zoals de cursus ze gebruikt (NORM.DIST = NORM.VERD, NORM.INV); kansen zijn fracties, weergegeven als %.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte cursusvoorbeelden (worked examples) S06-WE09 (werkmap NORM.INV / NORM.VERD) en S06-WE10 (notities bij deck p. 19), de 68-95-99,7-regel (deck p. 19) en de Z-tabel van de cursus
- **Audit:** niet nodig (er zijn uitgewerkte cursusvoorbeelden)

## Sigma & DPMO: Sigmaniveau, DPMO en yield: DPO, DPMO, Z met en zonder 1,5σ-verschuiving (1.5σ shift)

- **Doel:** Discrete data: DPO, DPMO en yield per kans (opportunity); sigmaniveau uit een DPMO en DPMO uit een sigmaniveau, in beide lezingen van de cursus.
- **Invoer:** per blok: defecten, eenheden en kansen per eenheid; een DPMO; een sigmaniveau. De rekenblokken die alleen uit de boeken komen (DPU, throughput yield, FTY, RTY, genormaliseerde yield) staan op blad Extra (boeken).
- **Bron in de cursus:** source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 19-21, 37-40; Les 1/20260521_van volsem.pdf p. 7
- **Conventie:** Beslissing 3: sigmaniveau ↔ DPMO getoond met de 1,5σ-verschuiving (zoals in elke cursustabel) en zonder.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte voorbeelden S08-WE05 tot S08-WE08 en S09-WE03 en tegen de sigmatabellen van de cursus (deck p. 21, Van Volsem p. 7); één gedrukte waarde wijkt af (zie build/README.md)
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - deck p. 21 en Harry & Schroeder (samenvatting p. 2, outline p. 1): 2σ = '308,537' DPMO; 308 537,5 rondt af op 308 538 (zoals Dummies drukt). Van Volsem p. 7: '308,000' (308 538 op duizendtallen is 309 000).

## Varianties BI & toetsen: Varianties: betrouwbaarheidsinterval (confidence interval, BI) en toets voor σ² en σ (χ²), BI en toets voor een verhouding van twee varianties (F)

- **Doel:** Eén steekproef: betrouwbaarheidsinterval (BI) voor σ² en σ, χ²-toets van σ = σ0. Twee steekproeven: BI voor σ1²/σ2² en σ2²/σ1², F-toets van σ1 = σ2 (bv. examenvraag Q2: werkt machine M1 nauwkeuriger dan M2?). Elk resultaat tweezijdig, alleen ondergrens en alleen bovengrens.
- **Invoer:** α; n en s per steekproef, of de ruwe waarden geplakt in kolommen H (steekproef 1) en I (steekproef 2); σ0 voor de χ²-toets.
- **Bron in de cursus:** source/course/Les 2/20260529_ottoy_Confidence Intervals - Further Reading (Dutch).pdf p. 21; Confidence Intervals.pdf p. 16; Testing of Hypotheses.pdf p. 13; Test Recipes - Further Reading (Dutch).pdf p. 11-14
- **Conventie:** Conventiebeslissingen 5-7: invoer α vooraf ingevuld op 0,05; tweezijdig, alleen ondergrens en alleen bovengrens naast elkaar; F uit F.INV / F.INV.RT, zowel σ1²/σ2² als σ2²/σ1².
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen uitgewerkte cursusvoorbeelden (worked examples) S03-WE03, S03-WE05; ook tegen S08-WE10 en de χ²- en F-tabellen van Dummies (p. 194, 196) (extra, Dummies; niet te kennen); het F-intervalvoorbeeld S08-WE11 van Dummies klopt niet (build/README.md)
- **Audit:** stats-auditor PASS (2026-09-28) voor het F-deel: alle 28 waarden (BI's in beide richtingen, F-toetsen ≠, >, <) voor één invoer kloppen met een onafhankelijke berekening uit Test Recipes p. 12-14, CI Further Reading p. 21 en de hint van examenvraag Q2. Opmerking: de cursus drukt geen expliciet BI voor de verhouding van twee varianties; het volgt uit de F-pivot van p. 12, omgekeerd zoals op p. 21.
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - Dummies p. 196 (S08-WE11): BI voor σA²/σB² gedrukt als '[(1/3.633)(4/7.5), 5.999(4/7.5)] = [0.147, 3.199]'. Met (sA²/σA²)/(sB²/σB²) ~ F(nA−1, nB−1) (Test Recipes p. 12, hint van examenvraag Q2) geven dezelfde staartwaarden van 5 % [0,0889; 1,938]: het boek verwisselt de twee F-waarden. De tabelwaarden zelf (Table 8-3) kloppen wel (extra, Dummies; niet te kennen).
  - Dummies p. 192-196 noemt '95 %' wat ±2σ is (95,45 %, 2,275 % per staart) voor χ², en een rechterstaart van 5 % voor F. Gebruik α = 0,0455 om zijn χ²-voorbeeld (S08-WE10) na te rekenen (extra, Dummies; niet te kennen).
  - Dummies Table 8-3 p. 196: F voor n1 = n2 = 2 gedrukt als '161.446' (definitie 161,448). Table 8-2 p. 194: bovenwaarde bij 99,7 % voor n = 5 gedrukt als '17.800' (definitie 17,8006). Alle andere waarden kloppen (extra, Dummies; niet te kennen).

## Confusion matrix: Confusion matrix: nauwkeurigheid (accuracy), sensitiviteit (recall), precisie (precision), F1 (trainingsset vs testset, tot drie modellen)

- **Doel:** Maten van 2x2-confusion matrices voor de trainingsset en de testset van tot drie modellen, naast elkaar, om underfitting en overfitting te beoordelen zoals in examenvraag Q5.
- **Invoer:** optioneel de klassenamen; per model de vier aantallen van de matrix van de trainingsset en van de testset (rijen = werkelijke klasse, kolommen = voorspelde klasse).
- **Bron in de cursus:** source/course/Les 2/20260529_naert.pdf p. 19-32 (train/test, underfitting/overfitting, bias-variance, confusion matrix en haar maten)
- **Conventie:** Sensitiviteit (recall), precisie en F1 getoond met elke klasse als de positieve klasse (de cursus laat die keuze aan het domein); geen automatisch bias/variance-label.
- **Status:** NIET GEVERIFIEERD (UNVERIFIED): geen uitgewerkt cursusvoorbeeld drukt deze maten af; gecontroleerd tegen een onafhankelijke berekening en door de stats-auditor (build/README.md)
- **Audit:** stats-auditor PASS (2026-09-28): alle 26 waarden voor één invoer (model A, trainingsset en testset) komen overeen met een onafhankelijke berekening uit 20260529_naert.pdf p. 29-32. Opmerking: 'foutenpercentage' (error rate) staat niet op die pagina's; het blad toont het als 1 − nauwkeurigheid.

## Verdelingen: Verdelingen (distributions): E[X], Var[X] en kansen (Bernoulli, binomiaal, hypergeometrisch, Poisson, exponentieel, uniform)

- **Doel:** Gemiddelde, variantie en punt- en cumulatieve kansen van de verdelingsfamilies uit de cursus en uit examenvraag Q6 (Bernoulli, binomiaal, hypergeometrisch, Poisson, exponentieel, uniform).
- **Invoer:** per blok: p; n, p, k; N, D, n, k; λ, k; intensiteit (rate) λ, t; a, b, x.
- **Bron in de cursus:** source/course/Les 2/20260529_ottoy_Acceptance Sampling.pdf p. 12, 16, 20; Acceptance Sampling.xlsm; Testing of Hypotheses.xlsx; Les 1/20260522_naert_big data.pdf p. 5-10
- **Conventie:** De verdelingsfuncties van Excel zoals de werkmappen van de cursus ze gebruiken; aantallen k zijn gehele getallen; P(X ≥ k) = 1 − P(X ≤ k − 1).
- **Status:** GEVERIFIEERD (VERIFIED): binomiaal en hypergeometrisch blok getest tegen de uitgewerkte cursusvoorbeelden (worked examples) S04-WE02, S03-WE19, S03-WE21, het Poisson-blok tegen S02-WE09; Bernoulli, Poisson, exponentieel en uniform gebruiken standaarddefinities die niet in de cursus gedrukt staan (beslissing 20; geaudit)
- **Audit:** stats-auditor PASS (2026-09-28) voor de blokken Bernoulli, Poisson, exponentieel en uniform: alle 14 waarden voor één invoer kloppen met een onafhankelijke berekening. De geciteerde pagina's drukken echter geen algemene formule voor deze vier families (Naert Les 1 p. 7-9 noemt alleen Poisson voor tellingen en exponentieel voor wachttijden; Acceptance Sampling.xlsm 'distributions' berekent EXPON.DIST met een intensiteit (rate) en een uniforme dichtheid op [1, 2]); het blad gebruikt de standaarddefinities, als zodanig aangeduid (beslissing 20).

## Gemiddelde & proportie: Gemiddelden en proporties: betrouwbaarheidsintervallen (confidence intervals, BI) en toetsen (z, t, ongepaarde en gepaarde t, proportie exact en benaderd, Z-toets)

- **Doel:** Betrouwbaarheidsintervallen (BI) en toetsen voor één gemiddelde (σ gekend: z; σ ongekend: t), het verschil van twee gemiddelden (ongepaarde gepoolde t, gepaarde t), één proportie (normale benadering, exact binomiaal, Z-toets) en twee proporties.
- **Invoer:** α; per blok n, gemiddelde, s of σ, μ0 / d0 / π0; of ruwe data geplakt in kolommen L en M (gepaard: L en M rij per rij). Proporties: n en het aantal successen x.
- **Bron in de cursus:** source/course/Les 2/20260529_ottoy_Confidence Intervals.pdf p. 4, 9-15; Confidence Intervals - Further Reading (Dutch).pdf p. 5-20; Testing of Hypotheses.pdf p. 12; Testing of Hypotheses - Further Reading (Dutch).pdf p. 10-14; Test Recipes - Further Reading (Dutch).pdf p. 4-10
- **Conventie:** Conventiebeslissingen 5, 6, 8: invoer α vooraf ingevuld op 0,05; tweezijdig, alleen ondergrens en alleen bovengrens naast elkaar; gepoolde variantie (pooled variance) met n1 + n2 − 2.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen uitgewerkte cursusvoorbeelden (worked examples) S03-WE01, S03-WE02, S03-WE04, S03-WE10, S03-WE13, S03-WE14, S03-WE15; ook tegen S08-WE12, S08-WE13 uit Dummies p. 197 (extra, Dummies; niet te kennen)
- **Audit:** niet nodig (er bestaan uitgewerkte cursusvoorbeelden)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - CI Further Reading (Dutch) p. 15 drukt de gepoolde variantie met noemer n1 + n2 − 1; het blad gebruikt n1 + n2 − 2 zoals Test Recipes p. 5 en de t(n1 + n2 − 2) van dezelfde slide (conventiebeslissing 8). Het uitgewerkte cursusvoorbeeld S03-WE13 (s_p = 6,59) klopt met n1 + n2 − 2.
  - Confidence Intervals.xlsx 'example t-test' F13 deelt door SQRT(19) met n = 20 (conventiebeslissing 9); geen testdoel.
  - Dummies p. 197 (S08-WE13): '0.08 ± 0.076 = [0.004, 0.156]' kapt de halve breedte 0,0765 af; onafgerond [0,0035; 0,1565] (extra, Dummies; niet te kennen).

## Regelkaarten: Regelkaarten (control charts): X̄-R- en X̄-s-kaart uit subgroepen, met markering van punten buiten de grenzen

- **Doel:** Controlegrenzen (control limits) en centrale lijnen van de X̄-R- en X̄-s-kaart, de σ-schattingen R̄/d2 en s̄/c4, en een markering voor elke subgroep buiten de grenzen; de Western Electric-regels om de kaart te lezen.
- **Invoer:** subgroepen als ruwe waarden (tot 10 per rij) of als getypte x̄ en R (en s) met n.
- **Bron in de cursus:** source/course/Les 4/2026 Lean - Six Sigma v13 - Capabiliteit - SPC.pdf p. 54-58, 62-74; ___4.1 tabellen SPC.pdf p. 1-2; Les 5/20260619_ottoy_Rheostat Knob Data.xls
- **Conventie:** Beslissing 4: constanten uit Table 18 (A2, D3, D4, B3, B4, d2), Table A (c4), Six Sigma Demystified (A3); 3σ-grenzen. I-MR-, p- en u-kaart: blad Extra (boeken), niet te kennen.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte voorbeelden van de cursus S06-WE03, S06-WE05, S06-WE06, S10-WE04a, S10-WE04b (en S08-WE18 uit Dummies; extra, niet te kennen); enkele gedrukte waarden wijken af (build/README.md)
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - Rheostat Knob Data.xls (Les 5, S10-WE04a/b) rekent UCL_R met D4 = 2,114 (Six Sigma Demystified); de oefenwerkboeken van Les 4 gebruiken 2,115 (Table 18), wat het blad gebruikt (beslissing 4). De X̄-grenzen komen overeen.

## Gage R&R: Gage R&R: gemiddelde-en-spreidingsbreedtemethode (average and range method) en ANOVA-methode (EV, AV, PV, GRR, TV, %GRR)

- **Doel:** Herhaalbaarheid (repeatability, EV), reproduceerbaarheid (reproducibility, AV), variatie tussen de delen (part variation, PV), GRR, TV en %GRR met de gemiddelde-en-spreidingsbreedtemethode (average and range method) en met de ANOVA-methode, met het oordeel 10 % / 30 % van de cursus; de ANOVA met de interactieterm.
- **Invoer:** de metingen van een volledige gekruiste studie (crossed study): tot 3 operators × 3 herhalingen (trials, rijen) × 10 delen (parts, kolommen); optioneel de tolerantie USL − LSL en α voor de F-toetsen.
- **Bron in de cursus:** source/course/Les 5/20260619_ottoy_Black Belt in Six Sigma - Measurement System Analysis.pdf p. 18, 24, 34-38; 20260619_ottoy_tabel MSA.pdf; 20260619_ottoy_GRR - ANOVA - avegage and range - 2.xlsx
- **Conventie:** Beslissing 11: vermenigvuldigingsfactor (multiplier) 6; %GRR t.o.v. totale variatie en tolerantie; ANOVA van de cursus = model zonder interactie (interactie ook getoond); constanten uit tabel MSA.pdf; ndc niet in de cursus.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte cursusvoorbeelden (worked examples) S10-WE02 (ANOVA) en S10-WE03 (gemiddelde-en-spreidingsbreedtemethode) op de eigen studiedata van de cursus
- **Audit:** niet nodig (er bestaan uitgewerkte cursusvoorbeelden)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - GRR-werkboek, blad '2way anova', K45 typt '=412.5+296.667' (de interactie-SS 296,6667 afgerond), dus is zijn EV² 30,8333478 in plaats van 30,8333333; zijn AV, PV, TV en %GRR verschuiven in het 7e cijfer. Het blad rekent vanuit de data; de tests vergelijken met een tolerantie die precies dit toelaat.

## Aanvaardingssteekproeven: Aanvaardingssteekproeven (acceptance sampling): OC-curve van een plan (n, c), producenten-/consumentenrisico, AOQ, AOQL, ATI, plan voor variabelen

- **Doel:** Aanvaardingskans OC(p) van een enkelvoudig steekproefplan (single-stage plan) (n, c), α bij AQL en β bij LQL, AOQ, AOQL en ATI bij rectificerende inspectie (rectifying inspection), een OC/AOQ/ATI-tabel, en het plan voor variabelen (variables plan) (k, n) uit AQL en LQL.
- **Invoer:** n, c, lotgrootte N (optioneel: exacte hypergeometrische OC, AOQ, ATI), AQL, LQL, α, β, een fractie p, de stapgrootte van de tabel.
- **Bron in de cursus:** source/course/Les 2/20260529_ottoy_Acceptance Sampling - Further Reading.pdf p. 2-10; Acceptance Sampling.pdf p. 23-27; Testing of Hypotheses.pdf p. 5-11; Testing of Hypotheses.xlsx
- **Conventie:** Beslissing 12: invoer α en β vooraf ingevuld op 5 % en 10 % (p. 4; de uitgewerkte voorbeelden daar gebruiken β = 5 %); hypergeometrische OC met M = [Np] als N gegeven is, binomiale OC altijd getoond.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen uitgewerkte voorbeelden van de cursus S03-WE06, S03-WE07, S03-WE20, S03-WE21, S04-WE12, S04-WE16, S04-WE18
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - Further Reading p. 4 ontwerpt (n, c) met de tabel van Peach ('tabellen AS.pdf'), die niet in de cursusbestanden zit; het blad controleert daarom een plan. Het voorbeeldplan (164, 2) voor (0,5 %, 95 %) en (3,5 %, 5 %) heeft OC(0,5 %) = 95 % maar OC(3,5 %) = 7,1 % (binomiaal): de methode van Peach is benaderend, zoals de pagina zegt.
  - Further Reading p. 10: 'AOQL approximately 1.3 %, at about 1.8 %' voor (250, 5), N = 1000 klopt met de benadering p·OC(p) (1,30 % bij 1,7 %), niet met de exacte formule op dezelfde slide (1,03 % bij 1,7 %), hoewel n/N = 0,25 niet klein is.

## ANOVA DOE regressie: Eenwegs-ANOVA (one-way ANOVA), effecten en ANOVA van een 2^k-factoriële proefopzet (factorial design, k = 2 tot 5), enkelvoudige lineaire regressie (simple linear regression)

- **Doel:** Eenwegs-ANOVA-tabel; effecten, coëfficiënten (extra, Dummies; niet te kennen), kwadratensommen (SS), F-toetsen en intervallen ±2 s.e. van een 2^k-factoriële proefopzet met zuivere fout (pure error) uit herhalingen en/of gepoolde interacties van hogere orde, de ANOVA van het model en R²; enkelvoudige lineaire regressie met ANOVA, R², t-toetsen, BI's van β0 en β1, en het BI van de gemiddelde respons en het predictie-interval bij x0.
- **Invoer:** α; ANOVA: tot 8 groepen van elk tot 30 waarden (één kolom per groep); factorieel: k, optioneel de orde vanaf waar gepoold wordt, tot 4 herhalingen per run in standaardvolgorde; regressie: tot 200 paren (x, y), x0 en de H0-waarden van β1 en β0.
- **Bron in de cursus:** source/course/Les 3/20260605_de vuyst_BB_DOE.pdf p. 3-15, 46-92; 20260605_de vuyst_BB_Regression.pdf p. 16-38, 56-57
- **Conventie:** Invoer α vooraf ingevuld op 0,05 (beslissing 5); BI's en t-toetsen van de regressie eenzijdig en tweezijdig naast elkaar (beslissing 6); factoren gecodeerd −1/+1 in standaardvolgorde (standard order; DOE p. 46, 70, 74); één herhaling (single replicate): interacties van een gekozen orde en hoger in de fout poolen (DOE p. 72, 77); R²_adj op beide manieren getoond.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen uitgewerkte voorbeelden van de cursus S05-WE01, S05-WE02, S05-WE05 tot S05-WE09, S05-WE17, S05-WE18, en tegen S08-WE16 (extra, Dummies; niet te kennen); gedrukte waarden die niet kloppen staan in build/README.md
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de cursus)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - DOE p. 50 (S05-WE05): '[AB] = 5,78 – 4,92 = 0,857'; het exacte effect is 0,8583 (gemiddelden 5,7767 en 4,9183).
  - DOE p. 71 (S05-WE08): SS_ABC (en MS) gedrukt als 5,5625; de gegevens op p. 70 geven contrast 9 en SS 81/16 = 5,0625, wat ook de gedrukte F0 2,08, P 0,19 en het totaal 92,9375 impliceren. De gedrukte P van A, 2,54 × 10^-3, is 2,534 × 10^-3 voor F0 18,69 op F(1, 8).
  - DOE p. 53 (S05-WE06): 'AB = (52 + 20)/2 − (30 + 40)/2 = −1'; die uitdrukking is gelijk aan +1, wat het blad geeft.
  - Regression p. 56 drukt R²_adj = 1 − (1 − R²)(n − 1)/(n − k − 2); de eigen outputs van de cursus gebruiken n − k − 1 (Regression p. 22 Minitab R-Sq(adj) 87,1 %; DOE p. 61 Adj R-Squared 0,8666; σ̂ op Regression p. 57). Het blad toont beide, met label.
  - Regression p. 21 (S05-WE17): de gefitte rechte 'ŷ = 74.20 + 14.97x' van Figure 11-4 verschilt van de kleinste-kwadratenwaarden (least squares) 74,283 en 14,947 van de Minitab-output op p. 22, die het blad reproduceert.

## Extra (boeken): Extra: rekenblokken uit Six Sigma For Dummies en Harry & Schroeder (niet te kennen voor het examen)

- **Doel:** Rekenblokken die alleen uit Six Sigma For Dummies en Harry & Schroeder komen (niet te kennen voor het examen): DPU, throughput yield, RTY ≈ e^(−DPU); traditionele yield, first-time yield, verborgen fabriek (hidden factory); RTY uit stapyields, genormaliseerde yield en eenheden nodig per goede eenheid; RTY van k gelijke stappen (dobbelstenen); gemiddelde yield per defectkans; Cp, Cpk en % buiten specificatie met σ̂ = MR̄ / 1,128; regelkaarten voor individuele waarden (I-MR), p-kaart en u-kaart.
- **Invoer:** per blok: defecten en eenheden; eenheden in, uit, afgekeurd, herwerkt; tot 10 stapyields; een RTY en het aantal stappen; één stapyield en k; een eindyield en het aantal kansen; LSL, USL, gemiddelde en MR̄; individuele waarden; subgroepgroottes met defecte stuks (p) of defecten (u). Yields als fracties (0,95 = 95 %).
- **Bron in de cursus:** source/course/Les 4/Six Sigma For Dummies.pdf p. 38-39, 114-116, 147-156, 249-256; source/course/Les 4/Six-Sigma Mikel Harry -  Richard Schroeder.pdf p. 3-5
- **Conventie:** Formules zoals in het boek; yields als fracties (0,95 = 95 %). Sigmaniveau met de 1,5σ-verschuiving (1.5σ shift) van de cursus (deck p. 37, beslissing 3); d2, D3, D4 voor n = 2 uit Tabel 18, E2 uit Six Sigma Demystified (beslissing 4); een negatieve ondergrens wordt 0.
- **Status:** GEVERIFIEERD (VERIFIED): getest tegen de uitgewerkte voorbeelden uit de boeken S07-WE01, S08-WE01 tot S08-WE04, S08-WE21, S09-WE01, S09-WE03 tot S09-WE06; enkele gedrukte waarden wijken af (zie build/README.md)
- **Audit:** niet nodig (er bestaan uitgewerkte voorbeelden in de boeken)
- **Gedrukte cursuswaarden die niet kloppen met de berekening** (zoals gedrukt bewaard in het orakel; getest als strikte verwachte mislukkingen, strict xfail):
  - Dummies p. 148 (S08-WE02): verborgen fabriek '98.6% - 70.7% = 27.9%' trekt afgeronde waarden af; niet afgerond 27,84 %.
  - Harry & Schroeder p. 3 (S09-WE01): product B '(0.968)**(1/48) = 99.97%'; berekend 99,932 %, en 'about 3.5 sigma' (zonder verschuiving) geeft 3,20.
  - Dummies p. 256 (S08-WE21): bovengrens van de u-kaart gedrukt als '2379' zonder decimaalteken; berekend 2,379 voor de laatste subgroep (n = 65). Centrale lijn en ondergrens komen overeen.
  - Dummies p. 251 en 255 (S08-WE19, S08-WE20): afgelezen kaarten zonder de gegevens of subgroepgrootte erachter; niet gebruikt als testdoel.
  - Harry & Schroeder p. 5 (S09-WE05): genormaliseerde yield gedrukt als '(0.368)**(-10) = 0.9051'; de k-de machtswortel die de tekst definieert geeft 0,368^(1/10) = 0,9049.

## Tabellen: Tabellen: constanten voor regelkaarten (control charts), capabiliteit en MSA

- **Doel:** Elke constantentabel voor regelkaarten uit de cursus, precies zoals gedrukt, met de opzoekbereiken (lookup ranges) die de rekenbladen gebruiken. Oranje cellen verschillen meer dan afronding van een andere gedrukte bron (beweeg erover voor de waarden). Six Sigma For Dummies Table 10-2 staat onderaan als extra (niet te kennen voor het examen).
- **Invoer:** geen (naslagblad)
- **Bron in de cursus:** source/course/Les 4/___4.1 tabellen SPC.pdf p. 1-2; Control charts - constants.pdf p. 1-2; Les 5/20260619_ottoy_tabel MSA.pdf p. 1; extra (niet te kennen): Six Sigma For Dummies.pdf p. 250
- **Conventie:** Beslissing 4: de rekenbladen gebruiken Table 18; c4 en d3 uit Table A; A3, E2, B5, B6 uit Six Sigma Demystified. Elke bron staat er volledig, zoals gedrukt.
- **Status:** GEVERIFIEERD (VERIFIED): transcripties van beide gescande tabellen cel per cel dubbel gecontroleerd; waarden vergeleken met hun wiskundige definities in tests/test_constants.py
- **Audit:** niet nodig (transcripties dubbel gecontroleerd; waarden vergeleken met hun definities)

## Constanten die afwijken van hun wiskundige definitie

Elke gedrukte constante is vergeleken met haar definitie (tests/test_constant_definitions.py). Verschillen van hoogstens één eenheid in het laatste gedrukte cijfer (afronding van afgeronde invoer) staan hier niet. De rekenbladen gebruiken nog steeds de gedrukte waarden (conventiebeslissing 4); niets is overschreven.

| Tabel | Constante | n | Gedrukt | Definitie | Verschil (eenheden van het laatste cijfer) |
|---|---|---|---|---|---|
| T18 | A0 | 10 | 3.085 | 3.08264 | 2.36 |
| T18 | 1/d2 | 2 | 0.8865 | 0.88623 | 2.73 |
| T18 | 1/d2 | 3 | 0.5907 | 0.59082 | 1.18 |
| T18 | D1 | 11 | 0.812 | 0.81093 | 1.07 |
| T18 | D1 | 13 | 1.026 | 1.02473 | 1.27 |
| T18 | D1 | 14 | 1.121 | 1.11769 | 3.31 |
| T18 | D1 | 15 | 1.207 | 1.20319 | 3.81 |
| T18 | D1 | 16 | 1.285 | 1.28226 | 2.74 |
| T18 | D1 | 17 | 1.359 | 1.35573 | 3.27 |
| T18 | D1 | 18 | 1.426 | 1.42429 | 1.71 |
| T18 | D1 | 19 | 1.490 | 1.48852 | 1.48 |
| T18 | D1 | 25 | 1.804 | 1.80531 | 1.31 |
| T18 | D2 | 12 | 5.592 | 5.59389 | 1.89 |
| T18 | D2 | 13 | 5.646 | 5.64723 | 1.23 |
| T18 | D2 | 14 | 5.693 | 5.69583 | 2.83 |
| T18 | D2 | 15 | 5.737 | 5.74046 | 3.46 |
| T18 | D2 | 16 | 5.779 | 5.78171 | 2.71 |
| T18 | D2 | 17 | 5.817 | 5.82004 | 3.04 |
| T18 | D2 | 18 | 5.854 | 5.85584 | 1.84 |
| T18 | D2 | 19 | 5.888 | 5.88941 | 1.41 |
| T18 | D2 | 25 | 6.058 | 6.05595 | 2.05 |
| T18 | D3 | 15 | 0.348 | 0.34656 | 1.44 |
| T18 | D3 | 17 | 0.379 | 0.37786 | 1.14 |
| T18 | D4 | 15 | 1.652 | 1.65344 | 1.44 |
| T18 | D4 | 17 | 1.621 | 1.62214 | 1.14 |
| TA | c2 | 25 | 0.9695 | 0.96965 | 1.46 |
| TA | d3 | 21 | 0.7272 | 0.72417 | 30.27 |
| SSD1 | B6 | 2 | 3.267 | 2.60632 | 660.68 |
| SSD2 | 1/d2 | 2 | 0.8865 | 0.88623 | 2.73 |
| SSD2 | 1/d2 | 3 | 0.5907 | 0.59082 | 1.18 |
| SSD2 | D1 | 12 | 0.922 | 0.92302 | 1.02 |
| SSD2 | D1 | 19 | 1.487 | 1.48852 | 1.52 |
| SSD2 | D2 | 19 | 5.891 | 5.88941 | 1.59 |
| SSD2 | E2 | 2 | 2.660 | 2.65868 | 1.32 |

Tabellen: T18 (E.L. Crow, F.A. Davis, M.W. Maxfield, Statistics Manual, 1960 (adapted from ASTM, 1951)); TA (D.J. Wheeler, Understanding Industrial Experimentation, 1987); SSD1 (Six Sigma Demystified, 2nd edition); SSD2 (Six Sigma Demystified, 2nd edition); DUM (Six Sigma For Dummies, Table 10-2).
