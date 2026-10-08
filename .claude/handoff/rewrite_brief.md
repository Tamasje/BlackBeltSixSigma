# Brief: fluent rewrite of one part of the Dutch study guide

Repo: /home/user/BlackBeltSixSigma/resources (run commands from there). Offline Six Sigma Black Belt exam guide.
Your part file(s): `study/parts/NN_*.html` and `study/parts/NN_symbols.tsv` (you may also fix `NN_formulas.tsv`).
Do NOT run git, do NOT write `../studiegids.html` (no full build), do NOT edit other parts, `study/assets/*`,
`study/tool_formulas.html`, `study/build_study.py` or anything in `src/`. Another agent edits the calculators and the
Excel workbook at the same time.

## What the user asked
"4.4 contains very weird text instead of being fluent. This needs adjustment and easy connection with the parts before and
after it. Check each part for such weak texts and adjust." and "make the explanation about [the topic] and the definition
of the various symbols more clear in the text. Now it's very vague." Part 04 has just been rewritten this way; read
`study/parts/04_betrouwbaarheidsintervallen.html` units 04.1 (box "De bouwstenen van elk betrouwbaarheidsinterval"),
04.2 ("De breedte W: absoluut en relatief") and 04.4–04.8 as the model to follow.

## How to rewrite each unit's theory (the text between its <h3> and its first exercise)
1. Open with one sentence that connects to the previous unit or says why this unit matters ("04.1 gaf … Hier …").
2. Then explain plainly, in short Dutch sentences, in a logical order: the situation → what you know/assume → which
   distribution or method → the formula → how to read the result → assumptions/conditions. Define each symbol in words
   the first time it appears (what it is, where it comes from: given in the question, computed from data, read in a table).
3. Remove: copied note fragments and odd quotes (e.g. '"gebruik Z voor BI µ onrealistisch: σ ??"'), derivations and side
   facts that are not needed to use the method (keep at most one sentence saying why, if it helps understanding),
   duplicated statements, remarks about misprints/errors in the course or books, rounding-difference remarks, and pure
   pointers ("zie Deel 3"). Short in-sentence links that carry content may stay.
4. Keep, unchanged in meaning: every figure (<figure>), every `<div class="calc-here" …>` marker, every
   `<div class="box tool">` (Rekentool) box, every exercise (`<div class="exercise" …>` with its questions, `data-answer`,
   hints and solutions), the studiewijzer unit, every course citation link `<a class="p" href="../source/…">` that supports
   a statement you keep, the "Uit de boeken" extra-ref lines, and the pitfall boxes (`box pit`) — but do tidy pitfall
   wording if it is broken, and delete pitfall bullets that only repeat the unit text or only report a course misprint.
   Method warning boxes (`box warn`) about using a method stay.
5. Formulas: use the existing `\sym{key}{TeX}` keys of your part (see `NN_symbols.tsv`, columns key, symbool, betekenis,
   hoe, anchor). If you need a new symbol, add a row to `NN_symbols.tsv` (5 tab-separated columns, unique key, anchor =
   the unit id where it is explained). Formula blocks: `<div class="f"><div>…</div></div>` as in part 04. Math is LaTeX in
   `\( … \)` (inline) or `\[ … \]` (display); decimal comma written `0{,}05`.
6. Never change an id, a unit number or heading number, a `data-answer`/`data-tol`, or a number taken from the course.
   NEVER invent numbers. If you add a computed value, compute it with python/scipy and mark it
   `<span class="computed">zelf berekend</span>`; every statement of fact keeps or gets a citation of the course page it
   comes from (reuse the links already in the part). Do not add new course facts you have not read in `source/course/`.
7. Keep the guide's voice: Dutch, short sentences, English course terms in parentheses at first use, no filler.

## When done
- Run `python3 study/build_study.py --check` (must print "check only: no problems") and
  `python3 study/parts/NN_numbers.py` (exit code 0; it checks the answers in your part).
- Report briefly: per unit what you changed (one line), anything you deleted that was not trivial, any new symbol rows,
  any computed values, and anything you were unsure about.
