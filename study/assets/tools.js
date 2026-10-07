/* "Hulpmiddelen" panels of the study guide: renders each calculator (Calc, calc.js) and each course table
   (<template id="tpl-…"> written by build_study.py) into its <details class="tool" data-tool="…"> on first opening.
   Inputs: yellow; results: green. Decimal comma or point; lists separated by spaces, tabs, new lines or ';'. */
(function () {
  'use strict';
  if (typeof document === 'undefined') return;
  var DATA = JSON.parse(document.getElementById('constants-data').textContent);
  var T = Calc.tables(DATA), K = T.K, M = T.M;

  /* ---------- input ---------- */
  function parseNumber(text) {
    var t = String(text).trim().replace(/\s/g, '').replace(/%$/, '').replace(/^−/, '-');
    if (t === '') return null;
    if (/^-?\d{1,3}(\.\d{3})+,\d+$/.test(t)) t = t.replace(/\./g, '');   // 1.234,5 (Dutch thousands)
    t = t.replace(',', '.');
    if (!/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(t)) return NaN;
    return parseFloat(t);
  }
  function tokens(line) { return line.trim() === '' ? [] : line.trim().split(/[\s;]+/); }
  function parseList(text) {
    var out = [], bad = [];
    tokens(String(text || '').replace(/\n/g, ' ')).forEach(function (t) { var x = parseNumber(t); if (isNaN(x) || x === null) bad.push(t); else out.push(x); });
    if (bad.length) throw new Error('kan niet lezen: ' + bad.slice(0, 3).join(' '));
    return out;
  }
  function parseRows(text) {
    return String(text || '').split('\n').filter(function (l) { return l.trim() !== ''; }).map(function (l) { return parseList(l); });
  }

  /* ---------- output ---------- */
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function f(x, sig) {
    if (x === null || x === undefined || (typeof x === 'number' && isNaN(x))) return '–';
    if (typeof x !== 'number') return esc(x);
    if (x === Infinity) return '+∞';
    if (x === -Infinity) return '−∞';
    var a = Math.abs(x), s;
    sig = sig || 6;
    if (a !== 0 && (a < 1e-4 || a >= 1e10)) s = x.toExponential(sig - 1).replace(/\.?0+e/, 'e').replace('e+', 'e');
    else s = String(+x.toPrecision(sig));
    return s.replace('.', ',').replace(/-/g, '−');
  }
  function pc(x) { return x === null || x === undefined || isNaN(x) ? '–' : f(100 * x) + ' %'; }
  function fp(x) { return x === null || x === undefined || isNaN(x) ? '–' : f(x) + ' <span class="aux">(' + pc(x) + ')</span>'; }
  function iv(r) { return r ? '[' + f(r[0]) + ' ; ' + f(r[1]) + ']' : '–'; }
  function out(rows) {
    return '<table class="out">' + rows.filter(Boolean).map(function (r) {
      if (typeof r === 'string') return '<tr><th colspan="3" class="sub">' + r + '</th></tr>';
      return '<tr><td>' + r[0] + '</td><td class="v">' + (r[1] === undefined ? '–' : r[1]) + '</td><td class="note">' + (r[2] || '') + '</td></tr>';
    }).join('') + '</table>';
  }
  function grid(head, rows) {
    return '<div class="scroll"><table class="out grid"><tr>' + head.map(function (h) { return '<th>' + h + '</th>'; }).join('') + '</tr>' +
      rows.map(function (r) { return '<tr>' + r.map(function (c) { return '<td class="v">' + c + '</td>'; }).join('') + '</tr>'; }).join('') + '</table></div>';
  }
  function warn(text) { return '<p class="calc-warn">' + text + '</p>'; }
  function testRows(t, df) {
    var name = df === null ? 'z' : 't';
    return grid(['H<sub>A</sub>', 'toetsgrootheid ' + name, 'kritieke waarde(n)', 'p-waarde', 'besluit'], [
      ['≠', f(t.stat), t.ne.crit.map(function (c) { return f(c); }).join(' en '), fp(t.ne.p), t.ne.d],
      ['>', f(t.stat), f(t.gt.crit[0]), fp(t.gt.p), t.gt.d],
      ['<', f(t.stat), f(t.lt.crit[0]), fp(t.lt.p), t.lt.d]]);
  }
  function ciRows(ci, what) {
    return grid(['betrouwbaarheidsinterval voor ' + what, 'van', 'tot'], [
      ['tweezijdig', f(ci.two[0]), f(ci.two[1])],
      ['enkel ondergrens ("minstens …")', f(ci.lower[0]), f(ci.lower[1])],
      ['enkel bovengrens ("hoogstens …")', f(ci.upper[0]), f(ci.upper[1])]]);
  }

  /* ---------- form pieces ---------- */
  function inp(name, label, ph, value) {
    return '<label class="fld"><span>' + label + '</span><input name="' + name + '" autocomplete="off" spellcheck="false"' +
      (ph ? ' placeholder="' + ph + '"' : '') + (value !== undefined ? ' value="' + value + '"' : '') + '></label>';
  }
  function area(name, label, ph, rows) {
    return '<label class="fld wide"><span>' + label + '</span><textarea name="' + name + '" rows="' + (rows || 4) +
      '" spellcheck="false"' + (ph ? ' placeholder="' + ph + '"' : '') + '></textarea></label>';
  }
  function sel(name, label, options) {
    return '<label class="fld"><span>' + label + '</span><select name="' + name + '">' + options.map(function (o) {
      return '<option value="' + o[0] + '">' + o[1] + '</option>'; }).join('') + '</select></label>';
  }
  var ALPHA = inp('alpha', 'α (significantieniveau)', '', '0,05');

  /* ---------- the calculators: blocks of {title, help, form, run(v) → html} ---------- */
  var TOOLS = {};

  TOOLS.normaal = [
    { title: 'Alles uit alles: µ, σ, x, z en de kansen',
      help: 'Vul in wat gegeven is en laat de rest leeg. µ, σ en x geven z en de kansen; µ, x en een staartkans geven σ; ' +
            'σ, x en een staartkans geven µ; µ, σ en een kans geven x; een kans alleen geeft z (standaardnormaal).',
      form: inp('mu', 'µ (gemiddelde)') + inp('sigma', 'σ (standaardafwijking)') + inp('x', 'x (waarde, grens)') +
            inp('z', 'z = (x − µ)/σ') + inp('pl', 'P(X ≤ x) (fractie of %)') + inp('pr', 'P(X > x) (fractie of %)'),
      run: function (v) {
        var r = Calc.normalSolve({ mu: v.mu, sigma: v.sigma, x: v.x, z: v.z, pl: v.pl, pr: v.pr });
        var mark = function (key) { return r.solved.indexOf(key) >= 0 ? 'berekend' : ''; };
        return out([['µ', f(r.mu), mark('mu')], ['σ', f(r.sigma), mark('sigma')], ['σ² (variantie)', f(num(r.sigma) ? r.sigma * r.sigma : null)],
                    ['x', f(r.x), mark('x')], ['z', f(r.z), mark('z')], ['P(X ≤ x)', fp(r.pl), mark('pl')],
                    ['P(X > x)', fp(r.pr), mark('pr')], ['ppm boven x / onder x', f(num(r.pr) ? r.pr * 1e6 : null) + ' / ' + f(num(r.pl) ? r.pl * 1e6 : null)]]) +
          (r.notes.length ? warn(r.notes.join('; ')) : '') +
          '<p class="xl">Excel: NORM.DIST(x; µ; σ; TRUE) = P(X ≤ x) (NL: NORM.VERD) · NORM.INV(p; µ; σ) · NORM.S.DIST(z; TRUE) · NORM.S.INV(p) · STANDARDIZE(x; µ; σ) (NL: NORMALISEREN)</p>';
      }, pct: ['pl', 'pr'] },
    { title: 'Kans tussen twee grenzen (bv. LSL en USL)',
      form: inp('mu', 'µ') + inp('sigma', 'σ') + inp('a', 'ondergrens a') + inp('b', 'bovengrens b'),
      run: function (v) {
        var r = Calc.normalBetween(v.mu, v.sigma, v.a, v.b);
        return r ? out([['z van a / z van b', f(r.za) + ' / ' + f(r.zb)], ['P(X < a)', fp(r.below)], ['P(a < X < b)', fp(r.between)],
                        ['P(X > b)', fp(r.above)], ['buiten [a ; b]', fp(r.outside), f(r.outside * 1e6) + ' ppm']]) : '';
      } },
    { title: 'µ ± k·σ en de bijhorende fractie (68-95-99,7)',
      form: inp('mu', 'µ') + inp('sigma', 'σ') + inp('k', 'k (aantal σ)'),
      run: function (v) {
        var r = Calc.normalKSigma(v.mu, v.sigma, v.k);
        return r ? out([['µ − kσ … µ + kσ', iv([r.lo, r.hi])], ['binnen', fp(r.inside)], ['buiten (beide staarten)', fp(r.outside), f(r.outside * 1e6) + ' ppm']]) : '';
      } },
    { title: 'Centraal interval met een gegeven kans',
      form: inp('mu', 'µ') + inp('sigma', 'σ') + inp('c', 'kans in het midden (bv. 0,95)'),
      run: function (v) {
        var r = Calc.normalCentral(v.mu, v.sigma, v.c);
        return r ? out([['z', f(r.z)], ['interval', iv([r.lo, r.hi])]]) : '';
      }, pct: ['c'] },
    { title: 'Gemiddelde van n waarnemingen: σ<sub>x̄</sub> = σ / √n',
      help: 'Gebruik σ/√n daarna als σ in het blok "alles uit alles" voor kansen op x̄ (centrale limietstelling, SPC p. 62–63).',
      form: inp('sigma', 'σ (van één waarneming)') + inp('n', 'n'),
      run: function (v) { return num(v.sigma) && num(v.n) && v.n > 0 ? out([['σ / √n', f(v.sigma / Math.sqrt(v.n))]]) : ''; } }
  ];

  TOOLS.ztabel = [
    { title: 'Zoek in de Z-tabel', help: 'Geef z (2 decimalen) of een kans: de cel wordt gemarkeerd in de tabel hieronder.',
      form: inp('z', 'z') + inp('p', 'kans links van z'),
      run: function (v, box) {
        var cells = box.querySelectorAll('td[data-z]'), best = null, bestd = Infinity;
        cells.forEach(function (c) { c.classList.remove('hit'); });
        if (num(v.z)) {
          var key = (Math.round(v.z * 100) / 100).toFixed(2);
          cells.forEach(function (c) { if (c.dataset.z === key || (key === '0.00' && c.dataset.z === '-0.00')) best = c; });
          if (best) { best.classList.add('hit'); return out([['tabel: P(Z ≤ ' + f(+key) + ')', best.textContent, 'exact: ' + f(Stats.normCdf(+key), 6)]]); }
          return warn('z = ' + f(v.z) + ' staat niet in de tabel (−3,49 … 3,49); exact P(Z ≤ z) = ' + f(Stats.normCdf(v.z)));
        }
        if (num(v.p)) {
          cells.forEach(function (c) { var d = Math.abs(parseFloat(c.textContent) - v.p); if (d < bestd) { bestd = d; best = c; } });
          if (best) best.classList.add('hit');
          return out([['dichtste cel', best ? best.textContent + ' bij z = ' + f(+best.dataset.z) : '–'], ['exact z', f(Stats.normInv(v.p))]]);
        }
        return '';
      }, pct: ['p'] }
  ];

  TOOLS.sigma = [
    { title: 'Defecten: DPO en DPMO', help: 'SPC p. 20: DPO = defecten per kans (defects per opportunity), DPMO = DPO · 10⁶, yield = 1 − DPO.',
      form: inp('D', 'D = aantal defecten') + inp('N', 'N = aantal eenheden') + inp('O', 'O = kansen (opportunities) per eenheid'),
      run: function (v) {
        var r = Calc.defects(v.D, v.N, v.O);
        return r ? out([['DPO = D / (N·O)', f(r.dpo)], ['DPMO = DPO · 10⁶', f(r.dpmo)], ['yield per kans = 1 − DPO', fp(r.ypo)]]) : '';
      } },
    { title: 'Van DPMO naar sigmaniveau (beide lezingen)',
      form: inp('dpmo', 'DPMO'),
      run: function (v) {
        var r = Calc.sigmaFromDpmo(v.dpmo);
        return r ? out([['yield = 1 − DPMO/10⁶', fp(r.yield)], ['Z zonder verschuiving (één staart)', f(r.z)],
                        ['sigmaniveau met 1,5σ-verschuiving = Z + 1,5', f(r.level), 'zoals de tabellen van de cursus (SPC p. 21)']]) : '';
      } },
    { title: 'Van sigmaniveau naar DPMO (beide lezingen)',
      form: inp('Z', 'sigmaniveau Z (bv. 6)'),
      run: function (v) {
        var r = Calc.dpmoFromSigma(v.Z);
        return r ? out([['DPMO met 1,5σ-verschuiving (staart voorbij Z − 1,5)', f(r.shifted), 'cursustabellen: 6σ → 3,4'],
                        ['yield met verschuiving', fp(r.yieldShifted)], ['DPMO zonder verschuiving, één staart', f(r.oneTail)],
                        ['DPMO zonder verschuiving, beide staarten (gecentreerd, Cp = Z/3)', f(r.twoTails), 'SPC p. 40: Cp = 2 → 2 per miljard']]) : '';
      } }
  ];

  TOOLS.kwantielen = [
    { title: 'Kritieke waarden', help: 'Links: P(X ≤ q) = α. Rechts: P(X > q) = α. Tweezijdig: α/2 in elke staart.',
      form: sel('dist', 'verdeling', [['z', 'z (standaardnormaal)'], ['t', 't'], ['chi2', 'χ²'], ['F', 'F']]) +
            inp('d1', 'vrijheidsgraden (F: teller)') + inp('d2', 'F: vrijheidsgraden noemer') + ALPHA,
      run: function (v) {
        var r = Calc.quantiles(v.text.dist, v.d1, v.d2, v.alpha);
        if (!r) return '';
        var xl = { z: ['NORM.S.INV(α)', 'NORM.S.INV(1−α)'], t: ['T.INV(α; df)', 'T.INV(1−α; df) of T.INV.2T(2α; df)'],
                   chi2: ['CHISQ.INV(α; df)', 'CHISQ.INV.RT(α; df)'], F: ['F.INV(α; df1; df2)', 'F.INV.RT(α; df1; df2)'] }[v.text.dist];
        return out([['linkse kritieke waarde', f(r.left), xl[0]], ['rechtse kritieke waarde', f(r.right), xl[1]],
                    ['tweezijdig: α/2 links en rechts', f(r.twoLo) + ' en ' + f(r.twoHi)]]);
      } },
    { title: 'p-waarde van een toetsgrootheid',
      form: sel('dist', 'verdeling', [['z', 'z'], ['t', 't'], ['chi2', 'χ²'], ['F', 'F']]) + inp('d1', 'vrijheidsgraden (F: teller)') +
            inp('d2', 'F: noemer') + inp('stat', 'waarde van de toetsgrootheid'),
      run: function (v) {
        var r = Calc.pValues(v.text.dist, v.d1, v.d2, v.stat);
        return r ? out([['P(X ≤ waarde) (H<sub>A</sub>: <)', fp(r.left)], ['P(X > waarde) (H<sub>A</sub>: >)', fp(r.right)],
                        ['tweezijdig (H<sub>A</sub>: ≠)', fp(r.two), v.text.dist === 'z' || v.text.dist === 't' ? '2 · P(X > |waarde|)' : '2 · kleinste staart']]) : '';
      } }
  ];

  function summary(v, area, n, m, s) {
    var xs = parseList(v.text[area]);
    if (xs.length >= 2) { var d = Calc.describe(xs); return { n: d.n, mean: d.mean, s: d.s, fromData: true }; }
    return { n: v[n], mean: v[m], s: v[s], fromData: false };
  }
  TOOLS.gemiddelde = [
    { title: 'Eén gemiddelde µ: BI en toets (z met σ, t met s)',
      help: 'Plak ruwe data óf vul n, x̄ en s (of σ) in. σ gekend → z; σ onbekend → t met n − 1 vrijheidsgraden.',
      form: ALPHA + area('data', 'ruwe data (optioneel)', '', 3) + inp('n', 'n') + inp('m', 'x̄') + inp('s', 's (steekproef)') +
            inp('sigma', 'σ (gekend)') + inp('mu0', 'µ0 (H0: µ = µ0)'),
      run: function (v) {
        var d = summary(v, 'data', 'n', 'm', 's'), r = Calc.oneMean(d.n, d.mean, d.s, v.sigma, v.mu0, v.alpha);
        if (!r) return '';
        var h = out([d.fromData ? 'uit de data' : null, ['n', f(d.n)], ['x̄', f(d.mean)], ['s', f(d.s)],
                     ['s.e. met σ: σ/√n', f(r.seZ)], ['s.e. met s: s/√n', f(r.seT)], ['vrijheidsgraden n − 1', f(r.df)]]);
        if (r.ciZ) h += ciRows(r.ciZ, 'µ (z, σ gekend)');
        if (r.ciT) h += ciRows(r.ciT, 'µ (t, σ onbekend)');
        if (r.testZ) h += '<p class="lbl">z-toets van H0: µ = µ0</p>' + testRows(r.testZ, null);
        if (r.testT) h += '<p class="lbl">t-toets van H0: µ = µ0</p>' + testRows(r.testT, r.df);
        return h;
      } }
  ];
  TOOLS.tweegemiddelden = [
    { title: 'Twee onafhankelijke steekproeven: µ1 − µ2 (gepoolde s, t met n1 + n2 − 2)',
      help: 'CI Further Reading p. 15–17; Test Recipes p. 5. Plak beide reeksen óf vul de samenvattingen in.',
      form: ALPHA + area('d1', 'data steekproef 1 (optioneel)', '', 2) + area('d2', 'data steekproef 2 (optioneel)', '', 2) +
            inp('n1', 'n1') + inp('m1', 'x̄1') + inp('s1', 's1') + inp('n2', 'n2') + inp('m2', 'x̄2') + inp('s2', 's2') + inp('d0', 'H0: µ1 − µ2 = (standaard 0)'),
      run: function (v) {
        var a = summary(v, 'd1', 'n1', 'm1', 's1'), b = summary(v, 'd2', 'n2', 'm2', 's2');
        var r = Calc.twoMeansPooled(a.n, a.mean, a.s, b.n, b.mean, b.s, v.d0, v.alpha);
        if (!r) return '';
        return out([['steekproef 1: n, x̄, s', f(a.n) + ' ; ' + f(a.mean) + ' ; ' + f(a.s)], ['steekproef 2: n, x̄, s', f(b.n) + ' ; ' + f(b.mean) + ' ; ' + f(b.s)],
                    ['x̄1 − x̄2', f(r.diff)], ['gepoolde s_p', f(r.sp)], ['s.e. = s_p √(1/n1 + 1/n2)', f(r.se)], ['vrijheidsgraden', f(r.df)]]) +
          ciRows(r.ci, 'µ1 − µ2') + '<p class="lbl">t-toets van H0: µ1 − µ2 = d0</p>' + testRows(r.test, r.df);
      } },
    { title: 'Gepaarde waarnemingen: verschillen v = x1 − x2 (t met n − 1)',
      help: 'Plak per regel een paar "x1 x2", of enkel de verschillen, of vul n, v̄ en s_v in.',
      form: ALPHA + area('pairs', 'paren x1 x2 (één paar per regel) of verschillen', '', 3) + inp('n', 'n') + inp('m', 'v̄') + inp('s', 's_v') +
            inp('d0', 'H0: µ_v = (standaard 0)'),
      run: function (v) {
        var rows = parseRows(v.text.pairs), diffs = rows.length && rows.every(function (r) { return r.length === 2; })
          ? rows.map(function (r) { return r[0] - r[1]; }) : [].concat.apply([], rows);
        var d = diffs.length >= 2 ? Calc.describe(diffs) : { n: v.n, mean: v.m, s: v.s };
        var r = Calc.paired(d.n, d.mean, d.s, v.d0, v.alpha);
        return r ? out([['n', f(d.n)], ['v̄', f(d.mean)], ['s_v', f(d.s)], ['s.e. = s_v/√n', f(r.se)], ['vrijheidsgraden', f(r.df)]]) +
          ciRows(r.ci, 'µ_v') + '<p class="lbl">gepaarde t-toets</p>' + testRows(r.test, r.df) : '';
      } }
  ];
  TOOLS.proportie = [
    { title: 'Eén proportie π: BI (normale benadering en exact) en Z-toets',
      help: 'CI Further Reading p. 20 (exact = R binom.test); Testing of Hypotheses FR p. 10–14. Voorwaarde Z-toets: n·π0 > 5.',
      form: ALPHA + inp('n', 'n') + inp('x', 'x = aantal successen (bv. defecten)') + inp('pi0', 'π0 (H0: π = π0)'),
      run: function (v) {
        var r = Calc.oneProportion(v.n, v.x, v.pi0, v.alpha);
        if (!r) return '';
        var h = out([['p = x / n', fp(r.p)], ['s.e. = √(p(1 − p)/n)', f(r.se)]]) + ciRows(r.ci, 'π (normale benadering)') +
          grid(['exact BI (Clopper-Pearson)', 'van', 'tot'], [['tweezijdig', fp(r.exact.two[0]), fp(r.exact.two[1])],
            ['enkel ondergrens', fp(r.exact.lower[0]), '+∞'], ['enkel bovengrens', fp(r.exact.upper[0]), fp(r.exact.upper[1])]]);
        if (r.test) h += '<p class="lbl">Z-toets van H0: π = π0 — z = (p − π0)/√(π0(1 − π0)/n); voorwaarde n·π0 > 5: ' +
          (r.condition ? 'ja' : '<b>nee</b>') + '</p>' + testRows(r.test, null);
        return h;
      }, pct: ['pi0'] },
    { title: 'Twee proporties: π1 − π2 (normale benadering)', help: 'CI Further Reading p. 20.',
      form: ALPHA + inp('n1', 'n1') + inp('x1', 'x1') + inp('n2', 'n2') + inp('x2', 'x2'),
      run: function (v) {
        var r = Calc.twoProportions(v.n1, v.x1, v.n2, v.x2, v.alpha);
        return r ? out([['p1', fp(r.p1)], ['p2', fp(r.p2)], ['p1 − p2', fp(r.diff)], ['s.e.', f(r.se)]]) + ciRows(r.ci, 'π1 − π2') : '';
      } }
  ];
  TOOLS.variantie = [
    { title: 'Eén variantie σ²: BI (σ² en σ) en χ²-toets (n − 1 vrijheidsgraden)',
      help: 'CI Further Reading p. 21; Test Recipes p. 11. Plak ruwe data óf vul n en s in.',
      form: ALPHA + area('data', 'ruwe data (optioneel)', '', 2) + inp('n', 'n') + inp('s', 's') + inp('sigma0', 'σ0 (H0: σ = σ0)'),
      run: function (v) {
        var d = summary(v, 'data', 'n', 'm', 's'), r = Calc.oneVariance(d.n, d.s, v.sigma0, v.alpha);
        if (!r) return '';
        var sq = function (x) { return x === Infinity ? Infinity : Math.sqrt(x); };
        var h = out([['n', f(d.n)], ['s', f(d.s)], ['s²', f(r.s2)], ['vrijheidsgraden', f(r.df)]]) +
          grid(['BI', 'σ² van', 'σ² tot', 'σ van', 'σ tot'], [
            ['tweezijdig', f(r.ci.two[0]), f(r.ci.two[1]), f(sq(r.ci.two[0])), f(sq(r.ci.two[1]))],
            ['enkel ondergrens (σ minstens …; H<sub>A</sub>: σ > σ0)', f(r.ci.lower[0]), '+∞', f(sq(r.ci.lower[0])), '+∞'],
            ['enkel bovengrens (σ hoogstens …; H<sub>A</sub>: σ < σ0)', '0', f(r.ci.upper[1]), '0', f(sq(r.ci.upper[1]))]]);
        if (r.test) {
          var t = r.test;
          h += '<p class="lbl">χ²-toets: χ² = (n − 1)s²/σ0²</p>' + grid(['H<sub>A</sub>', 'χ²', 'kritieke waarde(n)', 'p-waarde', 'besluit'], [
            ['σ ≠ σ0', f(t.stat), f(t.ne.crit[0]) + ' en ' + f(t.ne.crit[1]), fp(t.ne.p), t.ne.d],
            ['σ > σ0', f(t.stat), f(t.gt.crit[0]), fp(t.gt.p), t.gt.d], ['σ < σ0', f(t.stat), f(t.lt.crit[0]), fp(t.lt.p), t.lt.d]]);
        }
        return h;
      } },
    { title: 'Twee varianties: BI voor σ1²/σ2² en F-toets (F(n1 − 1, n2 − 1))',
      help: 'Test Recipes p. 12–14; examenvraag 2. (s1²/σ1²)/(s2²/σ2²) ~ F(n1 − 1, n2 − 1).',
      form: ALPHA + area('d1', 'data 1 (optioneel)', '', 2) + area('d2', 'data 2 (optioneel)', '', 2) + inp('n1', 'n1') + inp('s1', 's1') +
            inp('n2', 'n2') + inp('s2', 's2'),
      run: function (v) {
        var a = summary(v, 'd1', 'n1', 'x', 's1'), b = summary(v, 'd2', 'n2', 'x', 's2');
        var r = Calc.twoVariances(a.n, a.s, b.n, b.s, v.alpha);
        if (!r) return '';
        var t = r.test;
        return out([['n1, s1', f(a.n) + ' ; ' + f(a.s)], ['n2, s2', f(b.n) + ' ; ' + f(b.s)], ['F = s1²/s2²', f(r.F)], ['vrijheidsgraden', f(r.v1) + ' en ' + f(r.v2)]]) +
          grid(['BI', 'σ1²/σ2² van', 'tot', 'σ2²/σ1² van', 'tot'], [
            ['tweezijdig', f(r.ci.two[0]), f(r.ci.two[1]), f(r.ciInv.two[0]), f(r.ciInv.two[1])],
            ['σ1²/σ2² minstens … (σ2²/σ1² hoogstens …)', f(r.ci.lower[0]), '+∞', '0', f(r.ciInv.upper[1])],
            ['σ1²/σ2² hoogstens … (σ2²/σ1² minstens …)', '0', f(r.ci.upper[1]), f(r.ciInv.lower[0]), '+∞']]) +
          '<p class="lbl">F-toets van H0: σ1 = σ2</p>' + grid(['H<sub>A</sub>', 'F', 'kritieke waarde(n)', 'p-waarde', 'besluit'], [
            ['σ1 ≠ σ2', f(t.stat), f(t.ne.crit[0]) + ' en ' + f(t.ne.crit[1]), fp(t.ne.p), t.ne.d],
            ['σ1 > σ2', f(t.stat), f(t.gt.crit[0]), fp(t.gt.p), t.gt.d], ['σ1 < σ2', f(t.stat), f(t.lt.crit[0]), fp(t.lt.p), t.lt.d]]);
      } }
  ];

  function moments(r) { return [['E[X]', f(r.mean)], ['Var[X]', f(r.variance)], ['σ = √Var', f(Math.sqrt(r.variance))]]; }
  function probs(r) { return [['P(X = k)', fp(r.eq)], ['P(X ≤ k)', fp(r.le)], ['P(X ≥ k) = 1 − P(X ≤ k − 1)', fp(r.ge)], ['P(X > k)', fp(num(r.le) ? 1 - r.le : null)]]; }
  TOOLS.verdelingen = [
    { title: 'Bernoulli (één item: X = 1 met kans p)', form: inp('p', 'p'),
      run: function (v) { var r = Calc.bernoulli(v.p); return r ? out(moments(r)) : ''; }, pct: ['p'] },
    { title: 'Binomiaal: aantal successen in n onafhankelijke pogingen', help: 'Excel: BINOM.DIST(k; n; p; FALSE/TRUE).',
      form: inp('n', 'n') + inp('p', 'p') + inp('k', 'k'),
      run: function (v) { var r = Calc.binomial(v.n, v.p, v.k); return r ? out(moments(r).concat(num(v.k) ? probs(r) : [])) : ''; }, pct: ['p'] },
    { title: 'Hypergeometrisch: defecten in een steekproef zonder teruglegging',
      help: 'Excel: HYPGEOM.DIST(k; n; D; N; FALSE/TRUE).',
      form: inp('N', 'N = lotgrootte') + inp('D', 'D = defecten in het lot') + inp('n', 'n = steekproefgrootte') + inp('k', 'k'),
      run: function (v) { var r = Calc.hypergeometric(v.N, v.D, v.n, v.k); return r ? out(moments(r).concat(num(v.k) ? probs(r) : [])) : ''; } },
    { title: 'Poisson: aantal gebeurtenissen in een vast interval', help: 'Excel: POISSON.DIST(k; λ; FALSE/TRUE).',
      form: inp('lam', 'λ (gemiddeld aantal)') + inp('k', 'k'),
      run: function (v) { var r = Calc.poisson(v.lam, v.k); return r ? out(moments(r).concat(num(v.k) ? probs(r) : [])) : ''; } },
    { title: 'Exponentieel: wachttijd tussen gebeurtenissen (rate λ)', help: 'Excel: EXPON.DIST(t; λ; TRUE).',
      form: inp('rate', 'λ (gebeurtenissen per tijdseenheid)') + inp('t', 't'),
      run: function (v) {
        var r = Calc.exponential(v.rate, v.t);
        return r ? out(moments(r).concat(num(v.t) ? [['P(T ≤ t) = 1 − e^(−λt)', fp(r.le)], ['P(T > t) = e^(−λt)', fp(r.gt)]] : [])) : '';
      } },
    { title: 'Uniform op [a, b]', form: inp('a', 'a') + inp('b', 'b') + inp('x', 'x'),
      run: function (v) { var r = Calc.uniform(v.a, v.b, v.x); return r ? out(moments(r).concat(num(v.x) ? [['P(X ≤ x)', fp(r.le)]] : [])) : ''; } }
  ];

  TOOLS.kruistabel = [
    { title: 'Kruistabel: gezamenlijke, marginale en voorwaardelijke kansen',
      help: 'Eén rij per regel, aantallen gescheiden door spaties (plak gerust uit Excel). Onafhankelijk ⇔ P(A en B) = P(A)·P(B) voor elke cel (Data p. 22–23).',
      form: area('t', 'aantallen (rijen = categorieën van A, kolommen = categorieën van B)', '120 30\n80 270', 4),
      run: function (v) {
        var rows = parseRows(v.text.t), r = Calc.contingency(rows);
        if (!r) return rows.length ? warn('elke rij moet evenveel getallen hebben') : '';
        var head = function (t) { return [t].concat(r.colTotals.map(function (x, j) { return 'B' + (j + 1); })).concat(['totaal']); };
        var body = function (m, rowExtra, colExtra) {
          var rs = m.map(function (row, i) { return ['A' + (i + 1)].concat(row.map(function (x) { return f(x, 4); })).concat(rowExtra ? [f(rowExtra[i], 4)] : ['']); });
          if (colExtra) rs.push(['totaal'].concat(colExtra.map(function (x) { return f(x, 4); })).concat(['1']));
          return rs;
        };
        return '<p class="lbl">aantallen (N = ' + f(r.N) + ')</p>' + grid(head(''), body(rows, r.rowTotals, r.colTotals).map(function (x, i, a) { if (i === a.length - 1) x[x.length - 1] = f(r.N); return x; })) +
          '<p class="lbl">gezamenlijke kansen P(A en B) met marginale kansen in de randen</p>' + grid(head(''), body(r.joint, r.pRow, r.pCol)) +
          '<p class="lbl">P(B | A): per rij</p>' + grid(head(''), body(r.colGivenRow)) +
          '<p class="lbl">P(A | B): per kolom</p>' + grid(head(''), body(r.rowGivenCol)) +
          '<p class="lbl">P(A)·P(B): zo zou P(A en B) zijn bij onafhankelijkheid</p>' + grid(head(''), body(r.product));
      } }
  ];

  TOOLS.steekproefplan = [
    { title: 'Plan (n, c): OC bij AQL en LQL, producenten- en consumentenrisico',
      help: 'OC(p) = P(X ≤ c). Binomiaal; hypergeometrisch met M = [Np] als N gegeven is (Further Reading p. 4). α-doel 5 %, β-doel 10 % (p. 4).',
      form: inp('n', 'n') + inp('c', 'c (aanvaard als defecten ≤ c)') + inp('N', 'N = lotgrootte (optioneel)') + inp('aql', 'AQL') + inp('lql', 'LQL (LTPD)') +
            inp('at', 'doel α', '', '0,05') + inp('bt', 'doel β', '', '0,10'),
      run: function (v) {
        var r = Calc.samplingRisks(v.n, v.c, v.N, v.aql, v.lql, v.at, v.bt);
        return r ? grid(['', 'binomiaal', 'hypergeometrisch'], [['OC(AQL)', fp(r.ocAqlBin), fp(r.ocAqlHyp)], ['producentenrisico α = 1 − OC(AQL)', fp(r.alphaBin), fp(r.alphaHyp)],
                    ['consumentenrisico β = OC(LQL)', fp(r.betaBin), fp(r.betaHyp)], ['haalt beide doelen?', f(r.meetsBin), f(r.meetsHyp)]]) : '';
      }, pct: ['aql', 'lql', 'at', 'bt'] },
    { title: 'Eén lotkwaliteit p: OC, AOQ, ATI', help: 'Further Reading p. 10: AOQ = p·OC·(1 − (n/N)·Rs*), ATI = n·OC + N·(1 − OC).',
      form: inp('n', 'n') + inp('c', 'c') + inp('N', 'N (voor exact AOQ en ATI)') + inp('p', 'p = fractie defect in het lot'),
      run: function (v) {
        var r = Calc.samplingPoint(v.n, v.c, v.N, v.p);
        return r ? out([['OC(p) binomiaal', fp(r.ocBin)], ['OC(p) hypergeometrisch', fp(r.ocHyp)], ['AOQ exact', fp(r.aoq)],
                        ['AOQ ≈ p·OC(p)', fp(r.aoqApprox)], ['ATI', f(r.ati)]]) : '';
      }, pct: ['p'] },
    { title: 'AOQL = hoogste AOQ', help: 'Met N: alle lotfracties M/N; zonder N: binomiaal, p in stappen van 0,0001.',
      form: inp('n', 'n') + inp('c', 'c') + inp('N', 'N (optioneel)'),
      run: function (v) {
        var r = Calc.aoql(v.n, v.c, v.N);
        return r ? out([['AOQL ≈ max p·OC(p)', fp(r.approx), 'bij p = ' + pc(r.pApprox)], ['AOQL exact (formule p. 10)', fp(r.exact), num(r.pExact) ? 'bij p = ' + pc(r.pExact) : '']]) : '';
      } },
    { title: 'OC-tabel', form: inp('n', 'n') + inp('c', 'c') + inp('N', 'N (optioneel)') + inp('step', 'stap in p', '', '0,01') + inp('to', 'tot p', '', '0,1'),
      run: function (v) {
        if (!num(v.n) || !num(v.c) || !num(v.step) || !num(v.to) || v.step <= 0) return '';
        var rows = [];
        for (var i = 0; i * v.step <= v.to + 1e-12 && rows.length < 201; i++) {
          var p = i * v.step, r = Calc.samplingPoint(v.n, v.c, v.N, p);
          rows.push([pc(p), pc(r.ocBin), pc(r.ocHyp), pc(r.aoq), pc(r.aoqApprox), f(r.ati)]);
        }
        return grid(['p', 'OC binomiaal', 'OC hypergeom.', 'AOQ exact', 'AOQ ≈ p·OC', 'ATI'], rows);
      }, pct: ['step', 'to'] },
    { title: 'Plan voor variabelen (k, n) uit AQL, LQL, α en β', help: 'Further Reading p. 9; aanvaard als (x̄ − grens)/s ≥ k.',
      form: inp('p0', 'AQL = p0') + inp('pt', 'LQL = pt') + inp('a', 'α', '', '0,05') + inp('b', 'β', '', '0,10'),
      run: function (v) {
        var r = Calc.variablesPlan(v.p0, v.pt, v.a, v.b);
        return r ? out([['k = (z_pt z_α + z_p0 z_β)/(z_(1−α) + z_(1−β))', f(r.k)], ['n = (z_(1−α) + z_(1−β))² (1 + k²/2)/(z_pt − z_p0)²', f(r.n)],
                        ['n naar boven afgerond', f(r.nUp)], ['OC(AQL) van dit plan', fp(r.ocAql)], ['OC(LQL) van dit plan', fp(r.ocLql)]]) : '';
      }, pct: ['p0', 'pt', 'a', 'b'] }
  ];

  TOOLS.regressie = [
    { title: 'Enkelvoudige lineaire regressie: schatting, ANOVA, toetsen, BI en PI',
      help: 'Eén paar "x y" per regel (plak twee kolommen uit Excel). Regression p. 17–38.',
      form: ALPHA + area('xy', 'x y (één paar per regel)', '', 5) + inp('x0', 'x0 (voor BI/PI)') + inp('b1', 'H0: β1 = (standaard 0)') + inp('b0', 'H0: β0 = (standaard 0)'),
      run: function (v) {
        var rows = parseRows(v.text.xy);
        if (rows.some(function (r) { return r.length !== 2; })) return warn('elke regel moet precies twee getallen hebben: x en y');
        var r = Calc.regression(rows.map(function (q) { return q[0]; }), rows.map(function (q) { return q[1]; }), v.x0, v.b1, v.b0, v.alpha);
        if (!r) return rows.length ? warn('minstens 3 paren en niet alle x gelijk') : '';
        var h = out([['n', f(r.n)], ['x̄ ; ȳ', f(r.xbar) + ' ; ' + f(r.ybar)], ['S_xx ; S_xy', f(r.sxx) + ' ; ' + f(r.sxy)],
                     ['b1 = S_xy/S_xx (helling)', f(r.b1)], ['b0 = ȳ − b1 x̄ (intercept)', f(r.b0)],
                     ['σ̂² = MS_E = SS_E/(n − 2)', f(r.mse)], ['σ̂ (Minitab S)', f(r.sigma)], ['R² = SS_R/SS_T', f(r.r2)],
                     ['R²_adj met n − 2 (zoals de Minitab-output)', f(r.r2adj)], ['R²_adj zoals gedrukt op Regression p. 56 (n − 3)', f(r.r2adjP56)]]) +
          grid(['bron', 'SS', 'df', 'MS', 'F0', 'p'], [['regressie', f(r.ssr), '1', f(r.ssr), f(r.F), fp(r.pF)],
            ['fout', f(r.sse), f(r.df), f(r.mse), '', ''], ['totaal', f(r.sst), f(r.n - 1), '', '', '']]) +
          '<p class="lbl">t-toetsen (n − 2 vrijheidsgraden)</p>' +
          grid(['', 'schatting', 's.e.', 't0', 'p (≠)', 'p (>)', 'p (<)'], [
            ['β1', f(r.b1), f(r.seB1), f(r.tB1.stat), fp(r.tB1.ne.p), fp(r.tB1.gt.p), fp(r.tB1.lt.p)],
            ['β0', f(r.b0), f(r.seB0), f(r.tB0.stat), fp(r.tB0.ne.p), fp(r.tB0.gt.p), fp(r.tB0.lt.p)]]);
        var ivRows = [['β1', r.ciB1], ['β0', r.ciB0]];
        if (r.ciMean) ivRows.push(['gemiddelde respons bij x0 (ŷ0 = ' + f(r.y0) + ')', r.ciMean], ['nieuwe waarneming bij x0 (PI)', r.pi]);
        return h + grid(['interval (1 − α)', 'tweezijdig', 'enkel ondergrens', 'enkel bovengrens'], ivRows.map(function (q) {
          return [q[0], iv(q[1].two), f(q[1].lower[0]) + ' … +∞', '−∞ … ' + f(q[1].upper[1])]; }));
      } }
  ];
  TOOLS.anova = [
    { title: 'Eénweg-ANOVA (one-way)', help: 'Eén groep per regel (de waarnemingen van één niveau). DOE p. 3–15.',
      form: ALPHA + area('g', 'groepen: één regel per niveau', '', 5),
      run: function (v) {
        var r = Calc.anova1(parseRows(v.text.g), v.alpha);
        if (!r) return '';
        return grid(['groep', 'n', 'gemiddelde', 's'], r.groups.map(function (g, i) { return [String(i + 1), f(g.n), f(g.mean), f(g.s)]; })) +
          grid(['bron', 'SS', 'df', 'MS', 'F0', 'p', 'F-kritiek'], [['behandeling', f(r.sstr), f(r.dfTr), f(r.msTr), f(r.F), fp(r.p), f(r.Fcrit)],
            ['fout', f(r.sse), f(r.dfE), f(r.msE), '', '', ''], ['totaal', f(r.sst), f(r.N - 1), '', '', '', '']]) +
          out([['algemeen gemiddelde', f(r.grandMean)], ['gepoolde s = √MS_E', f(r.pooledSd)], ['besluit bij α', r.d]]);
      } }
  ];
  TOOLS.factorieel = [
    { title: '2^k-factorieel: effecten, kwadratensommen, F-toetsen',
      help: 'Eén regel per run in standaardvolgorde ((1), a, b, ab, c, …), herhalingen naast elkaar. Bij één replicatie: pool interacties vanaf een orde in de fout (DOE p. 72, 77).',
      form: ALPHA + inp('k', 'k (aantal factoren)') + inp('pool', 'pool interacties vanaf orde (optioneel)') + area('runs', 'responsen per run', '', 8),
      run: function (v) {
        var rows = parseRows(v.text.runs);
        if (!num(v.k) || !rows.length) return '';
        var r = Calc.factorial(v.k, rows, v.pool, v.alpha);
        if (r.error) return warn(r.error);
        return out([['n herhalingen ; N', f(r.n) + ' ; ' + f(r.N)], ['β0 = algemeen gemiddelde', f(r.beta0)],
                    ['SS zuivere fout (df)', f(r.sspe) + ' (' + r.dfPE + ')'], ['SS gepoolde interacties (df)', f(r.ssPool) + ' (' + r.dfPool + ')'],
                    ['σ̂² = MS_E', f(r.mse)], ['s.e.(effect) = √(σ̂²/(n 2^(k−2)))', f(r.se)]]) +
          grid(['effect', 'contrast', 'effect', 'coëfficiënt = effect/2', 'SS', 'F0', 'p', 'effect ± 2 s.e.', ''], r.effects.map(function (e) {
            return [e.name, f(e.contrast), f(e.effect), f(e.coef), f(e.ss), f(e.F), fp(e.p), num(e.lo) ? iv([e.lo, e.hi]) : '–', e.pooled ? 'gepoold' : ''];
          })) + grid(['bron', 'SS', 'df', 'F0', 'p'], [['model', f(r.ssModel), f(r.dfModel), f(r.Fmodel), fp(r.pModel)],
            ['fout', f(r.ssE), f(r.dfE), '', ''], ['totaal', f(r.sst), f(r.dfT), '', '']]) +
          out([['R² = SS_model/SS_totaal', f(r.r2)], ['R²_adj met N − p − 1 (zoals de cursusoutputs)', f(r.r2adj)], ['R²_adj zoals gedrukt op Regression p. 56', f(r.r2adjP56)]]);
      } }
  ];
  TOOLS.aliassen = [
    { title: 'Fractioneel factorieel: definiërende relatie, resolutie, aliassen',
      help: 'Generatoren zoals D=ABC of D=AB; E=AC (DOE p. 80–92). Een minteken mag: D=−ABC.',
      form: inp('gen', 'generatoren', 'D=ABC'),
      run: function (v) {
        var r = Calc.aliases(v.text.gen.replace(/−/g, '-'));
        if (!r) return '';
        if (r.error) return warn(r.error);
        var roman = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][r.resolution] || String(r.resolution);
        return out([['ontwerp', '2<sup>' + r.k + '−' + r.p + '</sup> = ' + r.runs + ' runs; basisfactoren ' + r.base], ['definiërende relatie', 'I = ' + r.relation.join(' = ')],
                    ['resolutie', roman + ' (kortste woord)']]) +
          grid(['effect', 'gealiast met'], r.chains.map(function (c) { return [c.effect, c.aliases.join(' = ')]; }));
      } }
  ];

  TOOLS.capabiliteit = [
    { title: 'Cp, Cpk (Pp, Ppk) en % buiten specificatie, per σ-schatting',
      help: 'Vul de specificatie en het gemiddelde in, en elke spreiding die je hebt; elke σ-schatting krijgt een eigen rij (beslissing 1). Constanten: d2 uit Table 18, c4 uit Table A.',
      form: inp('lsl', 'LSL (leeg = eenzijdig)') + inp('usl', 'USL (leeg = eenzijdig)') + inp('mean', 'gemiddelde x̄ of X̿') + inp('sigma', 'σ gegeven') +
            inp('rbar', 'R̄') + inp('sbar', 's̄') + inp('n', 'n (subgroepgrootte voor R̄, s̄)') + inp('overall', 'totale s (lange termijn)'),
      run: function (v) {
        var rows = Calc.capability({ lsl: v.lsl, usl: v.usl, mean: v.mean, sigma: v.sigma, rbar: v.rbar, sbar: v.sbar, n: v.n, overall: v.overall }, K);
        if (!rows.length) return (num(v.rbar) || num(v.sbar)) && !num(v.n) ? warn('geef n voor R̄/d2 of s̄/c4') : '';
        var lines = [['σ', 'sigma', f], ['Cp = (USL − LSL)/6σ', 'cp', f], ['niveau (SPC p. 40)', 'level', f], ['Cpu = (USL − x̄)/3σ', 'cpu', f],
                     ['Cpl = (x̄ − LSL)/3σ', 'cpl', f], ['Cpk = min(Cpu, Cpl)', 'cpk', f], ['Cpk ≥ 1,33 ("Good", SPC p. 41)?', 'capable', f], ['Z tot LSL', 'zLsl', f],
                     ['Z tot USL', 'zUsl', f], ['onder LSL', 'below', pc], ['boven USL', 'above', pc], ['totaal buiten specificatie', 'out', pc], ['ppm', 'ppm', f]];
        return grid(['σ-schatting →'].concat(rows.map(function (r) { return r.label + (r.constant ? '<br><span class="aux">' + esc(r.constant).replace('.', ',') + '</span>' : ''); })),
          lines.map(function (l) { return [l[0]].concat(rows.map(function (r) { return l[2](r[l[1]]); })); }));
      } },
    { title: 'Omgekeerd: welke σ of welk gemiddelde is nodig?',
      help: 'Uit Cp = (USL − LSL)/6σ en Cpk = min((USL − x̄)/3σ, (x̄ − LSL)/3σ) (SPC p. 34–35).',
      form: inp('lsl', 'LSL') + inp('usl', 'USL') + inp('cp', 'gewenste Cp') + inp('sigma', 'σ') + inp('cpk', 'gewenste Cpk'),
      run: function (v) {
        var r = Calc.capabilityInverse(v.lsl, v.usl, v.cp, v.sigma, v.cpk);
        return out([['σ nodig voor die Cp = (USL − LSL)/(6·Cp)', f(r.sigmaForCp)],
                    ['gemiddelde minstens LSL + 3·Cpk·σ', f(r.meanMin)], ['gemiddelde hoogstens USL − 3·Cpk·σ', f(r.meanMax)]]);
      } }
  ];

  TOOLS.regelkaart = [
    { title: 'Grenzen uit X̿, R̄ en/of s̄ (X̄-R en X̄-s)', help: 'SPC p. 74. Constanten voor n uit Table 18 (A2, D3, D4, B3, B4, d2), Table A (c4) en Six Sigma Demystified (A3).',
      form: inp('n', 'n (subgroepgrootte)') + inp('xbb', 'X̿') + inp('rbar', 'R̄') + inp('sbar', 's̄'),
      run: function (v) {
        if (!num(v.n)) return '';
        var r = Calc.limitsSummary(v.n, v.xbb, v.rbar, v.sbar, K);
        return limitsTable(r);
      } },
    { title: 'Subgroepen: ruwe data → X̿, R̄, s̄, grenzen en signalen', help: 'Eén subgroep per regel, alle subgroepen even groot.',
      form: area('g', 'subgroepen (één per regel)', '', 6),
      run: function (v) {
        var r = Calc.subgroupChart(parseRows(v.text.g), K);
        if (!r) return '';
        if (r.error) return warn(r.error);
        return out([['k subgroepen van n', f(r.k) + ' × ' + f(r.n)], ['X̿', f(r.xbarbar)], ['R̄', f(r.rbar)], ['s̄', f(r.sbar)]]) + limitsTable(r) +
          grid(['#', 'x̄', 'R', 's', 'x̄ (R-grenzen)', 'R', 'x̄ (s-grenzen)', 's'], r.groups.map(function (g, i) {
            return [String(i + 1), f(g.mean), f(g.range), f(g.s), flagged(g.fxR), flagged(g.fR), flagged(g.fxS), flagged(g.fS)]; }));
      } }
  ];
  function flagged(s) { return s ? '<b class="flag">' + s + '</b>' : ''; }
  function limitsTable(r) {
    var rows = [];
    if (r.xR) rows.push(['X̄ (met R̄)', f(r.xR[0]), f(r.xR[1]), f(r.xR[2]), 'A2 = ' + f(r.A2)]);
    if (r.R) rows.push(['R', f(r.R[0]), f(r.R[1]), f(r.R[2]), 'D3 = ' + f(r.D3) + ', D4 = ' + f(r.D4)]);
    if (r.xS) rows.push(['X̄ (met s̄)', f(r.xS[0]), f(r.xS[1]), f(r.xS[2]), 'A3 = ' + f(r.A3)]);
    if (r.S) rows.push(['s', f(r.S[0]), f(r.S[1]), f(r.S[2]), 'B3 = ' + f(r.B3) + ', B4 = ' + f(r.B4)]);
    var extra = [];
    if (num(r.sigmaR)) extra.push(['σ̂ = R̄/d2', f(r.sigmaR), 'd2 = ' + f(r.d2)], ['σ(x̄) = σ̂/√n', f(r.sigmaXbar)]);
    if (num(r.sigmaS)) extra.push(['σ̂ = s̄/c4', f(r.sigmaS), 'c4 = ' + f(r.c4)]);
    if (!rows.length && !extra.length) return num(r.n) && !num(r.A2) ? warn('n = ' + f(r.n) + ' staat niet in de tabel') : '';
    return grid(['kaart', 'LCL', 'CL', 'UCL', 'constanten'], rows) + out(extra);
  }

  TOOLS.grr = [
    { title: 'Gage R&R: gemiddelde-en-spreidingsbreedte en ANOVA',
      help: 'k operatoren, r herhalingen, n delen. Eén regel per operator en herhaling (A herhaling 1, A herhaling 2, …, B herhaling 1, …), met de n delen naast elkaar. MSA p. 34–37; constanten uit tabel MSA.pdf.',
      form: inp('k', 'k (operatoren)') + inp('r', 'r (herhalingen)') + inp('tol', 'tolerantie USL − LSL (optioneel)') + ALPHA + area('d', 'metingen', '', 9),
      run: function (v) {
        var rows = parseRows(v.text.d);
        if (!rows.length || !num(v.k) || !num(v.r)) return '';
        var r = Calc.grr(rows, v.k, v.r, v.tol, v.alpha, M);
        if (r.error) return warn(r.error);
        var keys = [['ev', 'EV (herhaalbaarheid)', f], ['av', 'AV (reproduceerbaarheid)', f], ['pv', 'PV (delen)', f], ['grr', 'GRR = √(EV² + AV²)', f],
                    ['tv', 'TV = √(GRR² + PV²)', f], ['pctTv', '%GRR van TV', pc], ['pctTol', '%GRR van tolerantie = 6·GRR/TOL', pc], ['verdict', 'oordeel (MSA p. 35)', f]];
        var a = r.anova, x = r.interaction, h = out([['k × n × r', r.k + ' × ' + r.n + ' × ' + r.r], ['R̿', f(r.rbarbar)], ['X̄_DIFF (operatoren)', f(r.xdiff)],
          ['R_p (delen)', f(r.rp)], ['d2 (m = r, g → ∞) ; d2* (m = k) ; d2* (m = n), g = 1', f(r.d2) + ' ; ' + f(r.d2k) + ' ; ' + f(r.d2n)]]);
        h += grid(['', 'gemiddelde en spreidingsbreedte (MSA p. 34–35)', 'ANOVA zonder interactie (MSA p. 36–37)'], keys.map(function (q) {
          return [q[1], r.ar ? q[2](r.ar[q[0]]) : 'tabel MSA heeft geen constante voor deze k, n of r', q[2](a[q[0]])]; }));
        h += '<p class="lbl">ANOVA zonder interactie (zoals de cursus, MSA p. 36)</p>' + grid(['bron', 'SS', 'df', 'MS', 'F', 'p'], [
          ['operator', f(a.ssOp), f(a.dfOp), f(a.msOp), f(a.fOp), fp(a.pOp)], ['deel', f(a.ssPart), f(a.dfPart), f(a.msPart), f(a.fPart), fp(a.pPart)],
          ['fout', f(a.ssErr), f(a.dfErr), f(a.msErr), '', ''], ['totaal', f(a.sst), f(a.dfT), '', '', '']]);
        h += '<p class="lbl">Met interactieterm (ter controle: een grote p voor de interactie steunt het poolen)</p>' + grid(['bron', 'SS', 'df', 'MS', 'F', 'p'], [
          ['operator × deel', f(x.ssInt), f(x.dfInt), f(x.msInt), f(x.fInt), fp(x.pInt)], ['binnen (herhaalbaarheid)', f(x.ssWithin), f(x.dfWithin), f(x.msWithin), '', '']]);
        return h;
      } }
  ];

  TOOLS.confusion = [
    { title: 'Confusion matrix: accuracy, recall, precision, F1 (train en test)',
      help: 'Rijen = werkelijke klasse, kolommen = voorspelde klasse (ML p. 29–32). Vul per model de vier aantallen in, rij per rij.',
      form: ['A', 'B', 'C'].map(function (m) {
        return inp(m + 'tr', 'model ' + m + ' train: a b c d', '480 20 15 485') + inp(m + 'te', 'model ' + m + ' test: a b c d', '180 120 110 190');
      }).join(''),
      run: function (v) {
        var rows = [];
        ['A', 'B', 'C'].forEach(function (m) {
          ['tr', 'te'].forEach(function (s) {
            var xs = parseList(v.text[m + s]);
            if (xs.length !== 4) return;
            var r = Calc.confusion([[xs[0], xs[1]], [xs[2], xs[3]]]);
            if (r) rows.push([m + (s === 'tr' ? ' train' : ' test'), f(r.N), f(r.accuracy, 4), f(r.error, 4), f(r.c1.recall, 4), f(r.c1.precision, 4), f(r.c1.f1, 4),
                              f(r.c2.recall, 4), f(r.c2.precision, 4), f(r.c2.f1, 4)]);
          });
        });
        return rows.length ? grid(['', 'N', 'accuracy', 'foutratio', 'recall klasse 1', 'precision 1', 'F1 1', 'recall klasse 2', 'precision 2', 'F1 2'], rows) +
          '<p class="xl">Grote kloof train ↔ test: overfitting (variantie). Beide laag: underfitting (bias). ML p. 19–28.</p>' : '';
      } }
  ];

  /* ---------- Les 2 (CI, TH, AS): sample size, tolerance, β/power, χ² frequencies, rank tests, sampling plans ---------- */
  TOOLS.steekproefgrootte = [
    { title: 'Steekproefgrootte voor een betrouwbaarheidsinterval',
      help: 'De cursus noemt "nauwkeurigheid" de VOLLEDIGE breedte van het interval (bovengrens − ondergrens, CI p. 7). ' +
            'n volgt uit de BI-formules van CI p. 10 en CI FR p. 3, opgelost naar n, en wordt naar boven afgerond. ' +
            'Voor σ onbekend geeft de cursus geen formule.',
      form: ALPHA + inp('W', 'gewenste volledige breedte W') + inp('p', 'geschatte proportie p (leeg = 0,5, slechtste geval)') + inp('sigma', 'σ (voor een gemiddelde)'),
      run: function (v) {
        var r = Calc.sampleSize(v.alpha, v.W, v.p, v.sigma);
        if (!r) return '';
        return out([['z = NORM.S.INV(1 − α/2)', f(r.z)], 'proportie: n = (2·z·√(p(1 − p))/W)²',
                    ['n (exact)', f(r.nProp)], ['n naar boven afgerond', f(r.nPropUp)], ['breedte bij die n', pc(r.widthProp)],
                    ['verwacht aantal defecten n·p (CI p. 10: minstens 5)', f(r.defectives)],
                    num(r.nMean) ? 'gemiddelde, σ gekend: n = (2·z·σ/W)² = (z·σ/E)², E = W/2' : null,
                    num(r.nMean) ? ['n (exact)', f(r.nMean)] : null, num(r.nMean) ? ['n naar boven afgerond', f(r.nMeanUp)] : null,
                    num(r.nMean) ? ['breedte bij die n', f(r.widthMean)] : null]) +
          '<p class="xl">Valkuil: een halve breedte van 5 % (± 5 %) is een volledige breedte van 10 %. Relatieve nauwkeurigheid eerst omzetten: 10 % van 10 % is W = 2 % (CI p. 7).</p>';
      }, pct: ['W', 'p'] }
  ];
  TOOLS.tolerantie = [
    { title: 'Tolerantie-interval, σ gekend (CI FR p. 22)',
      help: 'β is hier de staartfractie van de verdeling (bv. 0,10 voor "90 % van de stuks"), niet het type-II-risico. Eenzijdig: k = z<sub>1−α</sub>/√n + z<sub>1−β</sub>; tweezijdig: k* = z<sub>1−α/2</sub>/√n + z<sub>1−β/2</sub>. Werk op de getransformeerde variabele (bv. Y = ln X) als de opgave dat doet.',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n') + inp('m', 'Ȳ') + inp('s', 'σ'),
      run: function (v) {
        var r = Calc.tolerance(v.n, v.m, v.s, v.alpha, v.beta, true);
        return r ? out([['k (eenzijdig)', f(r.k1)], ['LTL = Ȳ − kσ', f(r.ltl)], ['UTL = Ȳ + kσ', f(r.utl), 'CI FR p. 22 drukt 5,55: drukfout, zie Fouten'],
                        ['k* (tweezijdig)', f(r.k2)], ['tweezijdig interval', iv(r.two)]]) +
          '<p class="xl">Ligt de eis (bv. ln 240) binnen [LTL; +∞[, dan is ze niet aangetoond (CI FR p. 22).</p>' : '';
      }, pct: ['beta'] },
    { title: 'Tolerantie-interval, σ onbekend (CI FR p. 23)',
      help: 'k ≈ t(α, β, n) = [z<sub>1−β</sub> + z<sub>1−α</sub>·√(1/n + z<sub>1−β</sub>²/(2n) − z<sub>1−α</sub>²/(2n²))] / (1 − z<sub>1−α</sub>²/(2n)); tweezijdig k′ = t(α/2, β/2, n).',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n') + inp('m', 'Ȳ') + inp('s', 's'),
      run: function (v) {
        var r = Calc.tolerance(v.n, v.m, v.s, v.alpha, v.beta, false);
        return r ? out([['k = t(α, β, n) (eenzijdig)', f(r.k1)], ['LTL = Ȳ − ks', f(r.ltl)], ['UTL = Ȳ + ks', f(r.utl)],
                        ["k′ = t(α/2, β/2, n) (tweezijdig)", f(r.k2)], ['tweezijdig interval', iv(r.two)]]) : '';
      }, pct: ['beta'] },
    { title: 'Verdelingsvrij tolerantie-interval [x<sub>(1)</sub>; x<sub>(n)</sub>] (CI FR p. 23)',
      help: 'Kleinste n met (1 − β/2)<sup>n</sup> − ½(1 − β)<sup>n</sup> ≤ α/2; voor een gegeven n de betrouwbaarheid 1 − 2(1 − β/2)<sup>n</sup> + (1 − β)<sup>n</sup>.',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n (optioneel)'),
      run: function (v) {
        var r = Calc.toleranceFree(v.alpha, v.beta, v.n);
        return r ? out([['kleinste n', f(r.nMin)], ['betrouwbaarheid bij de gegeven n', fp(r.confidence)]]) : '';
      }, pct: ['beta'] }
  ];
  TOOLS.onderscheidingsvermogen = [
    { title: 'β en onderscheidingsvermogen (power) van de Z-toets voor µ',
      help: 'De kritieke waarde ligt op de verdeling onder H0; β is de kans om toch in het aanvaardingsgebied te vallen als het ware gemiddelde µ1 is (TH FR p. 7–9). Power = 1 − β (TH FR p. 8). Tweezijdig toont de cursus alleen als grafiek (TH FR p. 14); de waarde volgt uit dezelfde procedure. Voor de t-toets geeft de cursus geen β.',
      form: ALPHA + inp('mu0', 'µ0 (H0)') + inp('mu1', 'ware µ1') + inp('sigma', 'σ') + inp('n', 'n') + inp('tb', 'gewenste β (voor n, optioneel)'),
      run: function (v) {
        var r = Calc.powerMean(v.mu0, v.mu1, v.sigma, v.n, v.alpha, v.tb);
        if (!r) return '';
        return out([['σ/√n', f(r.se)]]) + grid(['H<sub>A</sub>', 'kritieke waarde(n) x̄', 'β (H0 ten onrechte aanvaarden)', 'power = 1 − β'], [
            ['µ > µ0', f(r.gt.crit[0]), fp(r.gt.beta), fp(r.gt.power)], ['µ < µ0', f(r.lt.crit[0]), fp(r.lt.beta), fp(r.lt.power)],
            ['µ ≠ µ0', f(r.ne.crit[0]) + ' en ' + f(r.ne.crit[1]), fp(r.ne.beta), fp(r.ne.power)]]) +
          (num(r.nOneSided) ? out([['n voor die β, eenzijdig: ((z<sub>1−α</sub> + z<sub>1−β</sub>)σ/|µ1 − µ0|)²', f(r.nOneSided)], ['naar boven afgerond', f(r.nOneSidedUp), 'TH FR p. 9: n = 195']]) : '');
      }, pct: ['tb'] },
    { title: 'β van de Z-toets voor een proportie π',
      help: 'Kritieke waarde met π0 onder de wortel (TR p. 9), β onder de ware π1 (zoals oefening 05.12). Voorwaarde n·π0 > 5 (TR p. 10).',
      form: ALPHA + inp('p0', 'π0 (H0)') + inp('p1', 'ware π1') + inp('n', 'n') + inp('tb', 'gewenste β (voor n, optioneel)'),
      run: function (v) {
        var r = Calc.powerProportion(v.p0, v.p1, v.n, v.alpha, v.tb);
        if (!r) return '';
        return out([['√(π0(1 − π0)/n)', f(r.se0)], ['voorwaarde n·π0 > 5', r.condition ? 'ja' : '<b>nee</b>']]) +
          grid(['H<sub>A</sub>', 'kritieke p', 'β', 'power'], [['π > π0', fp(r.gt.crit), fp(r.gt.beta), fp(r.gt.power)],
            ['π < π0', fp(r.lt.crit), fp(r.lt.beta), fp(r.lt.power)]]) +
          (num(r.nFormula) ? out([['n uit de formule', f(r.nFormula)], ['kleinste n met β kleiner dan het doel', f(r.nSearch)]]) : '');
      }, pct: ['p0', 'p1', 'tb'] }
  ];
  TOOLS.chikwadraat = [
    { title: 'χ²-aanpassingstoets (goodness of fit)',
      help: 'TR p. 15–17: e<sub>k</sub> = n·π<sub>k</sub>, χ² = Σ(e<sub>k</sub> − n<sub>k</sub>)²/e<sub>k</sub>, vrijheidsgraden r − g − 1 (g = geschatte parameters), alleen de rechterstaart. Voorwaarde e<sub>k</sub> > 5, anders klassen samenvoegen. Excel CHISQ.TEST past de vrijheidsgraden NIET aan voor g.',
      form: ALPHA + area('o', 'waargenomen aantallen n<sub>k</sub> per klasse', '', 2) + area('e', 'verwachte kansen π<sub>k</sub> (of verwachte aantallen)', '', 2) + inp('g', 'g = aantal geschatte parameters', '', '0'),
      run: function (v) {
        var o = parseList(v.text.o), e = parseList(v.text.e);
        if (!o.length || !e.length) return '';
        if (o.length !== e.length) return warn('evenveel waargenomen als verwachte waarden nodig');
        var r = Calc.chi2Fit(o, e, v.g, v.alpha);
        return grid(['klasse', 'n<sub>k</sub>', 'e<sub>k</sub>'], o.map(function (x, i) { return [String(i + 1), f(x), f(r.e[i])]; })) +
          out([['χ²', f(r.chi2)], ['vrijheidsgraden r − g − 1', f(r.df)], ['kritieke waarde CHISQ.INV.RT(α; df)', f(r.crit)],
               ['p-waarde CHISQ.DIST.RT', fp(r.p)], ['besluit', num(r.p) ? (r.p < v.alpha ? 'verwerp H0' : 'H0 niet verwerpen') : '–'],
               r.small ? ['<b>' + r.small + ' klasse(n) met e ≤ 5</b>', 'klassen samenvoegen (TR p. 17)'] : null]);
      } },
    { title: 'χ²-toets op onafhankelijkheid (kruistabel)',
      help: 'TR p. 18–20: e<sub>kl</sub> = n<sub>k.</sub>·n<sub>.l</sub>/n, vrijheidsgraden (r − 1)(s − 1), voorwaarde e<sub>kl</sub> > 5. Bij een 2×2-tabel de continuïteitscorrectie van Yates.',
      form: ALPHA + area('t', 'aantallen: één rij per regel', '', 4),
      run: function (v) {
        var rows = parseRows(v.text.t), r = Calc.chi2Table(rows, v.alpha);
        if (!r) return rows.length ? warn('elke rij moet evenveel getallen hebben') : '';
        return '<p class="lbl">verwachte aantallen e<sub>kl</sub></p>' + grid([''].concat(r.e[0].map(function (_, j) { return 'B' + (j + 1); })),
            r.e.map(function (row, i) { return ['A' + (i + 1)].concat(row.map(function (x) { return f(x); })); })) +
          out([['χ²', f(r.chi2)], ['vrijheidsgraden', f(r.df)], ['kritieke waarde', f(r.crit)], ['p-waarde', fp(r.p)],
               ['besluit', r.p < v.alpha ? 'verwerp H0 (afhankelijk)' : 'H0 (onafhankelijk) niet verwerpen'],
               num(r.yates) ? ['χ² met Yates (2×2)', f(r.yates)] : null, num(r.yates) ? ['p-waarde met Yates', fp(r.pYates)] : null,
               r.small ? ['<b>' + r.small + ' cel(len) met e ≤ 5</b>', 'voorwaarde niet voldaan'] : null]);
      } }
  ];
  function rankOut(r, statName) {
    return out([[statName, f(r.W !== undefined ? r.W : (r.T !== undefined ? r.T : r.R))], ['verwachting onder H0', f(r.mean)], ['standaardafwijking onder H0', f(r.sd)]]) +
      grid(['', 'z', 'p links', 'p rechts', 'p tweezijdig'], [['zonder continuïteitscorrectie (zoals de gids)', f(r.z), fp(r.p.left), fp(r.p.right), fp(r.p.two)],
        ['met continuïteitscorrectie (½ eenheid naar E)', f(r.zcc), fp(r.pcc.left), fp(r.pcc.right), fp(r.pcc.two)]]) +
      (r.small ? warn('Kleine steekproef: de cursus schrijft een tabel met kritieke waarden voor; die zit niet in de cursusbestanden, dus z is alleen een indicatie.') : '');
  }
  TOOLS.nietparametrisch = [
    { title: 'Wilcoxon-Mann-Whitney (twee onafhankelijke steekproeven)',
      help: 'TR p. 21–22: rangschik alle waarden samen (gelijke waarden: gemiddelde rang); W = rangsom van steekproef 1; E(W) = n1(N + 1)/2; σ²(W) = n1·n2·(N + 1)/12 (zonder correctie voor ties, zoals de cursus). Grote W ↔ mediaan 1 > mediaan 2.',
      form: area('a', 'steekproef 1', '', 2) + area('b', 'steekproef 2', '', 2),
      run: function (v) {
        var r = Calc.rankSum(parseList(v.text.a), parseList(v.text.b));
        return r ? out([['rangen van steekproef 1', r.ranks1.map(function (x) { return f(x); }).join(' ')]]) + rankOut(r, 'W = rangsom steekproef 1') : '';
      } },
    { title: 'Wilcoxon signed ranks (gepaarde waarnemingen)',
      help: 'TR p. 23–24: v = x1 − x2; v = 0 weglaten en n aanpassen; rangschik |v| (gelijke: gemiddelde rang); T+ = som van de rangen van de positieve v; E = n(n + 1)/4; σ² = n(n + 1)(2n + 1)/24.',
      form: area('pairs', 'paren x1 x2 per regel, of de verschillen', '', 3),
      run: function (v) {
        var rows = parseRows(v.text.pairs), d = rows.length && rows.every(function (q) { return q.length === 2; })
          ? rows.map(function (q) { return q[0] - q[1]; }) : [].concat.apply([], rows);
        var r = Calc.signedRank(d);
        return r ? out([['n na weglaten van ' + r.dropped + ' nulverschil(len)', f(r.n)]]) + rankOut(r, 'T+ = som van de positieve rangen') : '';
      } },
    { title: 'Runs-toets op aselectheid (Wald-Wolfowitz)',
      help: 'TR p. 25–26: tel de runs boven en onder de mediaan in de volgorde van de steekproef; E(R) ≈ (n + 2)/2; σ²(R) ≈ (n − 1)/4. Waarden gelijk aan de mediaan worden weggelaten (de cursus zegt er niets over).',
      form: area('x', 'waarden in de volgorde van de steekproef', '', 3),
      run: function (v) {
        var r = Calc.runsTest(parseList(v.text.x));
        return r ? out([['mediaan', f(r.median)], ['tekens (+ boven, − onder)', r.signs], ['n (zonder waarden gelijk aan de mediaan)', f(r.n)]]) + rankOut(r, 'R = aantal runs') : '';
      } }
  ];
  TOOLS.steekproefmethoden = [
    { title: 'Proportie: SRS tegenover gestratificeerd (twee strata, AS p. 16–18)',
      help: 'σ²[P] = π(1 − π)/n (SRS); proportioneel gestratificeerd σ²[P<sub>s</sub>] = (W<sub>A</sub>σ<sub>A</sub>² + W<sub>B</sub>σ<sub>B</sub>²)/n; optimale verdeling n<sub>A</sub> = W<sub>A</sub>σ<sub>A</sub>/(W<sub>A</sub>σ<sub>A</sub> + W<sub>B</sub>σ<sub>B</sub>)·n. Laat π<sub>B</sub> leeg voor alleen SRS.',
      form: inp('piA', 'π<sub>A</sub> (of π voor SRS)') + inp('piB', 'π<sub>B</sub>') + inp('wA', 'W<sub>A</sub> = N<sub>A</sub>/N', '', '1') + inp('n', 'n'),
      run: function (v) {
        var r = Calc.samplingVariance(v.piA, v.piB, v.wA, v.n);
        if (!r) return '';
        if (!num(r.strat)) return out([['σ²[P] = π(1 − π)/n', f(r.srs)], ['σ[P]', f(Math.sqrt(r.srs))]]);
        return out([['π = W<sub>A</sub>π<sub>A</sub> + W<sub>B</sub>π<sub>B</sub>', fp(r.pi)], ['σ<sub>A</sub>² ; σ<sub>B</sub>²', f(r.sA2) + ' ; ' + f(r.sB2)],
                    ['σ²[P] (SRS)', f(r.srs)], ['σ²[P<sub>s</sub>] (proportioneel gestratificeerd)', f(r.strat)],
                    ['n<sub>A</sub> proportioneel', f(r.nAprop)], ['n<sub>A</sub> optimaal ; n<sub>B</sub> optimaal', f(r.nAopt) + ' ; ' + f(r.nBopt)]]);
      }, pct: ['piA', 'piB', 'wA'] },
    { title: 'Gemiddelde: twee even grote normale strata (AS p. 19, notities)',
      help: 'W<sub>A</sub> = W<sub>B</sub> = ½ en gemeenschappelijke σ<sub>S</sub>²: σ²[X̄<sub>S</sub>] = σ<sub>S</sub>²/n; σ²[X̄] = σ<sub>S</sub>²/n + (µ<sub>A</sub> − µ<sub>B</sub>)²/(4n).',
      form: inp('a', 'µ<sub>A</sub>') + inp('b', 'µ<sub>B</sub>') + inp('s2', 'σ<sub>S</sub>² (binnen een stratum)') + inp('n', 'n'),
      run: function (v) {
        var r = Calc.samplingMeans(v.a, v.b, v.s2, v.n);
        return r ? out([['µ', f(r.mu)], ['σ² van de hele populatie', f(r.sigma2)], ['σ²[X̄] (SRS)', f(r.srs)], ['σ²[X̄<sub>S</sub>] (gestratificeerd)', f(r.strat)]]) : '';
      } }
  ];
  TOOLS.steekproefplan.push(
    { title: 'Bij welke p haalt een plan (n, c) een gegeven OC? (AQL, LQL van een plan)',
      help: 'AQL = p met OC(p) = 1 − α; LQL = p met OC(p) = β (AS FR p. 4, p. 17). Binomiaal; opgelost door bisectie.',
      form: inp('n', 'n') + inp('c', 'c') + inp('t', 'gewenste OC (bv. 0,95 of 0,10)'),
      run: function (v) { var p = Calc.inverseOC(v.n, v.c, v.t); return num(p) ? out([['p met OC(p) = ' + pc(v.t), fp(p)]]) : ''; }, pct: ['t'] });
  TOOLS.planontwerp = [
    { title: 'Plan (n, c) zoeken voor (AQL; 1 − α) en (LQL; β)',
      help: 'De cursus ontwerpt met de tabel van Peach (R<sub>0</sub> = LQL/AQL, AS FR p. 4), maar die tabel zit niet in de cursusbestanden. Deze zoektocht (zoals de gids): de kleinste c waarvoor de kleinste n met OC(LQL) ≤ β ook OC(AQL) ≥ 1 − α haalt, binomiaal. Peach geeft bv. (164, 2) voor (0,5 %; 95 %), (3,5 %; 5 %), met β = 7,1 % (zie Fouten).',
      form: inp('aql', 'AQL') + inp('lql', 'LQL') + inp('a', 'α', '', '0,05') + inp('b', 'β', '', '0,10'),
      run: function (v) {
        var r = Calc.planSearch(v.aql, v.lql, v.a, v.b);
        return r ? out([['plan (n, c)', '(' + r.n + ', ' + r.c + ')'], ['n mag tot', f(r.nMax), 'met dezelfde c'], ['OC(AQL)', fp(r.ocAql)],
                        ['OC(LQL)', fp(r.ocLql)], ['R<sub>0</sub> = LQL/AQL (voor de tabel van Peach)', f(r.r0)]]) : '';
      }, pct: ['aql', 'lql', 'a', 'b'] }
  ];
  TOOLS.dubbelplan = [
    { title: 'Dubbel plan (n1, c1, c2) + (n2, c3): OC, Π en ASN',
      help: 'AS FR p. 5: aanvaard als X1 ≤ c1, verwerp als X1 ≥ c2, anders tweede steekproef en aanvaard als X1 + X2 ≤ c3. Binomiaal; hypergeometrisch met M = [Np] als N gegeven is.',
      form: inp('n1', 'n1') + inp('c1', 'c1') + inp('c2', 'c2 (verwerp bij X1 ≥ c2)') + inp('n2', 'n2') + inp('c3', 'c3 (op X1 + X2)') + inp('p', 'p') + inp('N', 'N (optioneel)'),
      run: function (v) {
        var r = Calc.doublePlan(v.n1, v.c1, v.c2, v.n2, v.c3, v.p, v.N);
        return r ? out([['aanvaard na steekproef 1: P(X1 ≤ c1)', fp(r.acc1)], ['verwerp na steekproef 1: P(X1 ≥ c2)', fp(r.rej1)],
                        ['Π(p) = beslist na steekproef 1', fp(r.decided1)], ['OC(p)', fp(r.oc)], ['ASN(p) = n1·Π + (n1 + n2)(1 − Π)', f(r.asn)],
                        ['verdeling', r.hyper ? 'hypergeometrisch' : 'binomiaal']]) : '';
      }, pct: ['p'] }
  ];
  TOOLS.sprt = [
    { title: 'Sequentieel plan (SPRT) voor attributen',
      help: 'AS FR p. 6–8: verwerp als X<sub>n</sub> ≥ h2 + s·n, aanvaard als X<sub>n</sub> ≤ −h1 + s·n, anders verder. OC en ASN volgen uit de parameter τ (p(τ)); ASN(s) = h1·h2/(s(1 − s)).',
      form: inp('p0', 'p0 (AQL)') + inp('pt', 'pt (LQL)') + inp('a', 'α', '', '0,05') + inp('b', 'β', '', '0,10') + inp('n', 'n tot nu toe (optioneel)') + inp('x', 'defecten tot nu toe X<sub>n</sub>'),
      run: function (v) {
        var r = Calc.sprt(v.p0, v.pt, v.a, v.b, v.n, v.x);
        if (!r) return '';
        return out([['h1', f(r.h1)], ['h2', f(r.h2)], ['s (helling)', f(r.s)], ['kortste weg naar aanvaarden: [h1/s] + 1', f(r.nAccept)],
                    ['kortste weg naar verwerpen: [h2/(1 − s)] + 1', f(r.nReject)], ['ASN(0)', f(r.asn0)], ['ASN(s)', f(r.asnS)],
                    r.decision ? ['aanvaardingslijn ; verwerpingslijn bij n', f(r.acceptLine) + ' ; ' + f(r.rejectLine)] : null,
                    r.decision ? ['beslissing', r.decision] : null]) +
          grid(['τ', 'p(τ)', 'OC', 'ASN'], r.table.map(function (q) { return [f(q.tau), pc(q.p), q.oc === null ? '–' : pc(q.oc), f(q.asn)]; }));
      }, pct: ['p0', 'pt', 'a', 'b'] }
  ];
  TOOLS.variabelenplan = [
    { title: 'Plan voor variabelen met gegeven n: ξ, k = t(1 − α, p0, n), Q en beslissing',
      help: 'AS p. 26–27, AS FR p. 9: aanvaard als Q = (X̄ − ξ)/s ≥ k. k = t(1 − α, p0, n) = [Z<sub>1−p0</sub> + Z<sub>α</sub>·√(1/n + Z<sub>1−p0</sub>²/(2n) − Z<sub>α</sub>²/(2n²))]/(1 − Z<sub>α</sub>²/(2n)) met Z<sub>α</sub> NEGATIEF (bv. −1,645). Ondergrens ξ direct of als ξ = NORM.INV(p0; µ; σ) zoals het werkboek.',
      form: inp('p0', 'p0 (AQL)') + ALPHA + inp('n', 'n') + inp('xi', 'ξ (ondergrens)') + inp('mu', 'of µ (voor ξ = NORM.INV(p0; µ; σ))') + inp('sg', 'σ (idem)') +
            inp('m', 'X̄ van de steekproef') + inp('s', 's van de steekproef') + inp('k', 'k (leeg = t)'),
      run: function (v) {
        var xi = num(v.xi) ? v.xi : (num(v.mu) && num(v.sg) && num(v.p0) ? v.mu + v.sg * Stats.normInv(v.p0) : null);
        var r = Calc.variablesGivenN(v.p0, v.alpha, v.n, xi, v.m, v.s, v.k);
        return r ? out([['Z<sub>1−p0</sub> ; Z<sub>α</sub>', f(r.zP) + ' ; ' + f(r.zA)], ['t(1 − α, p0, n)', f(r.t)], ['ξ', f(r.xi)], ['k gebruikt', f(r.k)],
                        ['Q = (X̄ − ξ)/s', f(r.Q)], ['beslissing (Q ≥ k)', f(r.accept)], ['OC(p0) met deze k', fp(r.ocP0)]]) : '';
      }, pct: ['p0'] }
  ];
  TOOLS.skiplot = [
    { title: 'Kwalificatie voor skip-lot (AS FR p. 11, notities)',
      help: 'Voorbeeld van de cursus: plan (80, 2), de laatste 10 loten aanvaard: de eerste 8 steekproeven samen hoogstens 3 defecten en de laatste 2 zonder defect: P<sub>q</sub> = B(3; 640, p)·B(0; 80, p)².',
      form: inp('p', 'p') + inp('n', 'n per steekproef', '', '80') + inp('lots', 'aantal eerste steekproeven', '', '8') + inp('d', 'hoogstens d defecten samen', '', '3') + inp('last', 'laatste steekproeven zonder defect', '', '2'),
      run: function (v) {
        var r = Calc.skipLot(v.p, v.n, v.lots, v.d, v.last);
        return r ? out([['B(d; aantal·n, p)', fp(r.first)], ['B(0; n, p)', fp(r.lastOne)], ['P<sub>q</sub>', fp(r.pq), 'cursus: 2,4 % bij 1 %, 85 % bij 0,1 %']]) : '';
      }, pct: ['p'] },
    { title: 'Criterium van Deming: geen of volledige inspectie (AS FR p. 13–15)',
      help: 'Stabiel proces met fractie defect p, inspectiekost per stuk k1, kost van een defect in de assemblage k2: p < k1/k2 → geen inspectie; p > k1/k2 → alles inspecteren.',
      form: inp('p', 'p') + inp('k1', 'k1 (inspectiekost per stuk)') + inp('k2', 'k2 (kost van een defect stuk verder in het proces)'),
      run: function (v) {
        var r = Calc.deming(v.p, v.k1, v.k2);
        return r ? out([['break-even k1/k2', fp(r.breakEven)], ['beslissing', r.decision]]) +
          '<p class="xl">Uit de kostformule van AS FR p. 14 volgt het exacte omslagpunt p(1 − p) = k1/k2; de regel p = k1/k2 van p. 15 is de benadering voor kleine p.</p>' : '';
      }, pct: ['p'] }
  ];

  /* ---------- Deel 14 (extra, niet te kennen): blocks that only the books Six Sigma For Dummies and Harry & Schroeder give ---------- */
  TOOLS.sigma_extra = [
    { title: 'DPU, throughput yield en RTY ≈ e^(−DPU)', help: 'Dummies p. 152–156; Harry & Schroeder p. 5. DPU = defecten per eenheid (defects per unit); TY = 1 − DPU; RTY ≈ e^(−DPU) als DPU klein is.',
      form: inp('D', 'D = aantal defecten') + inp('N', 'N = aantal eenheden'),
      run: function (v) {
        var r = Calc.defects(v.D, v.N, null);
        return r ? out([['DPU = D / N', f(r.dpu)], ['throughput yield = 1 − DPU', fp(r.ty)], ['RTY ≈ e^(−DPU)', fp(r.rtyApprox), 'Dummies p. 156: als DPU klein is']]) : '';
      } },
    { title: 'Traditionele yield, first-time yield, verborgen fabriek', help: 'Dummies p. 147–151.',
      form: inp('in', 'eenheden in') + inp('out', 'eenheden uit (goed, na herwerk)') + inp('scrap', 'afgekeurd (scrap)') + inp('rework', 'herwerkt'),
      run: function (v) {
        var r = Calc.yields(v.in, v.out, v.scrap, v.rework);
        return r ? out([['Y = uit / in', fp(r.y)], ['FTY = (in − scrap − herwerk) / in', fp(r.fty)], ['verborgen fabriek = Y − FTY', fp(r.hidden)]]) : '';
      } },
    { title: 'Rolled throughput yield uit de yields per stap',
      form: area('steps', 'yield per stap (fracties of %, gescheiden door spaties of regels)', '0,98 0,95 0,99', 2),
      run: function (v) {
        var ys = parseList(v.text.steps).map(function (y) { return y > 1 ? y / 100 : y; });
        var r = Calc.rolled(ys);
        return r ? out([['k stappen', f(r.k)], ['RTY = product', fp(r.rty)], ['genormaliseerde yield NY = RTY^(1/k)', fp(r.ny)],
                        ['DPU = −ln(RTY)', f(r.dpu)], ['eenheden per goede eenheid, herstelbaar: 1 + (1 − RTY)', f(r.repairable)],
                        ['eenheden per goede eenheid, afgekeurd: 1 / RTY', f(r.scrapped)]]) : '';
      } },
    { title: 'Zelfde yield per stap: RTY = yield^k',
      form: inp('y', 'yield per stap') + inp('k', 'aantal stappen k'),
      run: function (v) { var r = Calc.yieldPower(v.y, v.k); return r ? out([['RTY', fp(r.rty)], ['één goede op …', f(r.oneIn)]]) : ''; }, pct: ['y'] },
    { title: 'Yield per kans uit de eindyield', help: 'Harry & Schroeder p. 3–5.',
      form: inp('y', 'eindyield') + inp('o', 'aantal kansen'),
      run: function (v) {
        var r = Calc.perOpportunity(v.y, v.o);
        return r ? out([['yield per kans = yield^(1/kansen)', fp(r.ypo)], ['DPMO', f(r.dpmo)], ['Z zonder verschuiving', f(r.z)],
                        ['sigmaniveau met 1,5σ-verschuiving', f(r.level)]]) : '';
      }, pct: ['y'] }
  ];
  TOOLS.regelkaart_extra = [
    { title: 'Individuele waarden en moving range (I-MR)', help: 'Dummies p. 249: X̄ ± E2·MR̄, D3·MR̄ … D4·MR̄ (n = 2).',
      form: area('x', 'waarden in volgorde', '', 4),
      run: function (v) {
        var r = Calc.individuals(parseList(v.text.x), K);
        if (!r) return '';
        return out([['k', f(r.k)], ['X̄', f(r.xbar)], ['MR̄', f(r.mrbar)], ['σ̂ = MR̄/d2(2)', f(r.sigma), 'd2 = ' + f(r.d2)]]) +
          grid(['kaart', 'LCL', 'CL', 'UCL', 'constanten'], [['X', f(r.X[0]), f(r.X[1]), f(r.X[2]), 'E2 = ' + f(r.E2)],
            ['MR', f(r.MR[0]), f(r.MR[1]), f(r.MR[2]), 'D3 = ' + f(r.D3) + ', D4 = ' + f(r.D4)]]) +
          grid(['#', 'x', 'MR', 'x-signaal', 'MR-signaal'], r.points.map(function (p, i) { return [String(i + 1), f(p.x), f(p.mr), flagged(p.fx), flagged(p.fmr)]; }));
      } },
    { title: 'p-kaart (fractie defect) of u-kaart (defecten per eenheid)', help: 'Dummies p. 254. Per regel: subgroepgrootte n_i en aantal. Grenzen per subgroep; negatieve LCL → 0.',
      form: sel('kind', 'kaart', [['p', 'p-kaart (defectieven)'], ['u', 'u-kaart (defecten)']]) + area('d', 'n_i en aantal per regel', '', 5),
      run: function (v) {
        var r = Calc.attributeChart(v.text.kind, parseRows(v.text.d));
        if (!r) return '';
        return out([['totaal geïnspecteerd', f(r.total)], ['totaal aantal', f(r.count)], [v.text.kind === 'p' ? 'p̄ = totaal defectieven / totaal' : 'ū = totaal defecten / totaal eenheden', f(r.centre)]]) +
          grid(['#', 'n_i', 'aantal', v.text.kind + '_i', 'LCL_i', 'UCL_i', 'signaal'], r.rows.map(function (q, i) {
            return [String(i + 1), f(q.n), f(q.count), f(q.value), f(q.lcl), f(q.ucl), flagged(q.flag)]; }));
      } }
  ];

  /* ---------- descriptives, regression extras, multiple regression, two-way ANOVA ---------- */
  function modes(xs) {
    var c = {}, best = 0;
    xs.forEach(function (x) { c[x] = (c[x] || 0) + 1; best = Math.max(best, c[x]); });
    if (best < 2) return 'geen (elke waarde komt één keer voor)';
    return Object.keys(c).filter(function (k) { return c[k] === best; }).map(function (k) { return f(+k); }).join(' ; ') + ' (' + best + '×)';
  }
  TOOLS.beschrijvend = [
    { title: 'Beschrijvende statistiek van één reeks',
      help: 'LSS p. 131: gemiddelde, mediaan (middelste waarde; bij even n het gemiddelde van de twee middelste), modus, s met n − 1, bereik. Excel: AVERAGE, MEDIAN, MODE, STDEV.S (n − 1) en STDEV.P (n).',
      form: area('x', 'waarden', '', 3),
      run: function (v) {
        var xs = parseList(v.text.x), r = Calc.descriptives(xs);
        return r ? out([['n', f(r.n)], ['som', f(r.sum)], ['gemiddelde x̄', f(r.mean)], ['mediaan', f(r.median)], ['modus', modes(xs)],
                        ['minimum ; maximum', f(r.min) + ' ; ' + f(r.max)], ['bereik R = max − min', f(r.range)],
                        ['s (n − 1, steekproef)', f(r.sd)], ['s² (n − 1)', f(r.variance)], ['s/√n (standaardfout)', f(r.se)],
                        ['σ met deler n (STDEV.P) ; σ²', f(r.sdPop) + ' ; ' + f(r.variancePop)]]) : '';
      } },
    { title: 'Correlatie en covariantie van paren (x, y)',
      help: 'r = S<sub>xy</sub>/√(S<sub>xx</sub>S<sub>yy</sub>); R² = r² (REG p. 43). De cursus noemt de deler van de covariantie niet: beide staan hier (COVARIANCE.S met n − 1, COVAR/COVARIANTIE met n). Correlatie is geen oorzakelijkheid (Deel 02).',
      form: area('xy', 'x y per regel', '', 4),
      run: function (v) {
        var rows = parseRows(v.text.xy);
        if (rows.some(function (q) { return q.length !== 2; })) return warn('elke regel: x en y');
        var r = Calc.correlation(rows.map(function (q) { return q[0]; }), rows.map(function (q) { return q[1]; }));
        return r ? out([['n', f(r.n)], ['r (Pearson)', f(r.r)], ['R² = r²', f(r.r2)], ['covariantie met n − 1', f(r.cov)],
                        ['covariantie met n', f(r.cov * (r.n - 1) / r.n)]]) : '';
      } }
  ];
  TOOLS.regressie.push(
    { title: 'Helling en intercept uit sommen (REG p. 18)',
      help: 'S<sub>xx</sub> = Σx² − n·x̄², S<sub>xy</sub> = Σxy − n·x̄·ȳ, b1 = S<sub>xy</sub>/S<sub>xx</sub>, b0 = ȳ − b1·x̄. Met Σy² ook de kwadratensommen.',
      form: inp('n', 'n') + inp('sx', 'Σx') + inp('sy', 'Σy') + inp('sxx', 'Σx²') + inp('sxy', 'Σxy') + inp('syy', 'Σy² (optioneel)'),
      run: function (v) {
        var r = Calc.regSums(v.n, v.sx, v.sy, v.sxx, v.sxy, v.syy);
        return r ? out([['x̄ ; ȳ', f(r.xbar) + ' ; ' + f(r.ybar)], ['S<sub>xx</sub> ; S<sub>xy</sub>', f(r.Sxx) + ' ; ' + f(r.Sxy)], ['b1', f(r.b1)], ['b0', f(r.b0)],
                        num(r.sst) ? ['SS<sub>T</sub> ; SS<sub>R</sub> = b1·S<sub>xy</sub> ; SS<sub>E</sub>', f(r.sst) + ' ; ' + f(r.ssr) + ' ; ' + f(r.sse)] : null,
                        num(r.r2) ? ['R² ; MS<sub>E</sub> ; σ̂', f(r.r2) + ' ; ' + f(r.mse) + ' ; ' + f(r.s)] : null]) : '';
      } },
    { title: 'R², σ̂ en F uit de kwadratensommen (REG p. 27–33, 56)',
      help: 'k = aantal regressoren (1 bij enkelvoudige regressie). R²<sub>adj</sub> zoals de cursusoutputs (n − k − 1) en zoals gedrukt op REG p. 56 (n − k − 2).',
      form: ALPHA + inp('ssr', 'SS<sub>R</sub>') + inp('sse', 'SS<sub>E</sub>') + inp('n', 'n') + inp('k', 'k', '', '1'),
      run: function (v) {
        var r = Calc.regFromSS(v.ssr, v.sse, v.n, v.k, v.alpha);
        return r ? out([['SS<sub>T</sub>', f(r.sst)], ['R² = SS<sub>R</sub>/SS<sub>T</sub>', f(r.r2)], ['MS<sub>R</sub> ; MS<sub>E</sub>', f(r.msr) + ' ; ' + f(r.mse)],
                        ['σ̂ = √MS<sub>E</sub>', f(r.s)], ['F0 ; vrijheidsgraden', f(r.F) + ' ; (' + f(v.k || 1) + ', ' + f(r.dfE) + ')'], ['p-waarde', fp(r.p)],
                        ['F-kritiek', f(r.Fcrit)], ['R²<sub>adj</sub> (n − k − 1)', f(r.r2adj)], ['R²<sub>adj</sub> zoals REG p. 56 (n − k − 2)', f(r.r2adjP56)]]) : '';
      } },
    { title: 'Toetsen, BI en PI uit samenvattende waarden (REG p. 30–38)',
      form: ALPHA + inp('b1', 'b1') + inp('b0', 'b0') + inp('mse', 'MS<sub>E</sub>') + inp('sxx', 'S<sub>xx</sub>') + inp('n', 'n') + inp('xb', 'x̄') + inp('x0', 'x0') +
            inp('h1', 'H0: β1 = (standaard 0)') + inp('h0', 'H0: β0 = (standaard 0)'),
      run: function (v) {
        var r = Calc.regTests(v.b1, v.b0, v.mse, v.sxx, v.n, v.xb, v.x0, v.alpha, v.h1, v.h0);
        if (!r) return '';
        var rows = [['β1', r.ciB1, r.seB1, r.tB1]];
        if (r.ciB0) rows.push(['β0', r.ciB0, r.seB0, r.tB0]);
        var h = out([['t-kritiek T.INV(1 − α/2; n − 2)', f(r.tcrit)], ['F0 = t0² (enkelvoudig)', f(r.F)]]) +
          grid(['', 's.e.', 't0', 'p (≠)', 'BI tweezijdig'], rows.map(function (q) { return [q[0], f(q[2]), f(q[3].stat), fp(q[3].ne.p), iv(q[1].two)]; }));
        if (num(r.y0)) h += out([['ŷ0', f(r.y0)], ['s.e. gemiddelde respons ; BI', f(r.seMean) + ' ; ' + iv(r.ciMean.two)],
                                 ['s.e. nieuwe waarneming ; PI', f(r.sePred) + ' ; ' + iv(r.pi.two)]]);
        return h;
      } },
    { title: 'Partiële F-toets: helpen de extra termen? (REG p. 61)',
      help: 'F0 = [(SS<sub>E</sub>(RM) − SS<sub>E</sub>(FM))/(k − r)] / [SS<sub>E</sub>(FM)/(n − p)]; RM = gereduceerd model, FM = volledig model, k − r = aantal toegevoegde termen, n − p = vrijheidsgraden van de fout van het volledige model.',
      form: ALPHA + inp('rm', 'SS<sub>E</sub>(RM)') + inp('fm', 'SS<sub>E</sub>(FM)') + inp('r', 'k − r (toegevoegde termen)') + inp('df', 'n − p (fout-df volledig model)'),
      run: function (v) {
        var r = Calc.partialF(v.rm, v.fm, v.r, v.df, v.alpha);
        return r ? out([['F0', f(r.F)], ['F-kritiek F.INV.RT(α; k − r; n − p)', f(r.Fcrit)], ['p-waarde', fp(r.p)], ['besluit', r.d]]) : '';
      } },
    { title: 'R²<sub>adj</sub> uit R²', form: inp('r2', 'R²') + inp('n', 'n') + inp('k', 'k (regressoren)'),
      run: function (v) { var r = Calc.r2adj(v.r2, v.n, v.k); return r ? out([['R²<sub>adj</sub> (n − k − 1, de cursusoutputs)', f(r.usual)], ['zoals gedrukt op REG p. 56 (n − k − 2)', f(r.p56)]]) : ''; }, pct: ['r2'] });

  // the regressor columns for the chosen model: as entered, second order (squares and products) or a polynomial in one x
  function designColumns(xs, model, centre) {
    var k = xs[0].length, means = [];
    for (var j = 0; j < k; j++) means.push(centre ? Stats.mean(xs.map(function (r) { return r[j]; })) : 0);
    var names = [];
    for (j = 0; j < k; j++) names.push('x' + (j + 1));
    function row(r) {
      var c = r.map(function (x, q) { return x - means[q]; }), cols = c.slice();
      if (model === 'second') {
        for (var a = 0; a < k; a++) for (var b = a; b < k; b++) cols.push(c[a] * c[b]);
      } else if ((model === 'poly2' || model === 'poly3') && k === 1) {
        cols.push(c[0] * c[0]); if (model === 'poly3') cols.push(c[0] * c[0] * c[0]);
      }
      return cols;
    }
    if (model === 'second') for (var a = 0; a < k; a++) for (var b = a; b < k; b++) names.push(a === b ? 'x' + (a + 1) + '²' : 'x' + (a + 1) + '·x' + (b + 1));
    if ((model === 'poly2' || model === 'poly3') && k === 1) { names.push('x1²'); if (model === 'poly3') names.push('x1³'); }
    return { row: row, names: names, means: means };
  }
  TOOLS.meervoudig = [
    { title: 'Meervoudige lineaire regressie (ook polynomen)',
      help: 'Eén regel per waarneming: y gevolgd door x1, x2, … (plak de kolommen uit Excel, y eerst). Uitvoer zoals Excel (REG p. 52). Tweede orde = kwadraten en kruisproducten; centreren op het gemiddelde zoals het acetyleenvoorbeeld (REG p. 60) verandert de coëfficiënten van de lagere termen, niet R², S of F. BI en PI bij x0 volgen de standaard kleinste-kwadratenformule; de cursus geeft ze alleen voor enkelvoudige regressie.',
      form: ALPHA + sel('model', 'model', [['lin', 'lineair in de ingevoerde x’en'], ['second', 'tweede orde (+ kwadraten en kruisproducten)'], ['poly2', 'polynoom graad 2 (één x)'], ['poly3', 'polynoom graad 3 (één x)']]) +
            sel('centre', 'x centreren op het gemiddelde', [['0', 'nee'], ['1', 'ja']]) + area('d', 'y x1 x2 … per regel', '', 6) + inp('x0', 'x0: waarden van x1 x2 … (optioneel)'),
      run: function (v) {
        var rows = parseRows(v.text.d);
        if (rows.length < 3) return '';
        if (rows.some(function (q) { return q.length !== rows[0].length || q.length < 2; })) return warn('elke regel: y en evenveel x-waarden');
        var design = designColumns(rows.map(function (q) { return q.slice(1); }), v.text.model, v.text.centre === '1');
        var data = rows.map(function (q) { return [q[0]].concat(design.row(q.slice(1))); });
        var x0 = parseList(v.text.x0), r = Calc.multipleRegression(data, x0.length === rows[0].length - 1 ? design.row(x0) : null, v.alpha);
        if (!r) return '';
        if (r.error) return warn(r.error);
        var names = ['intercept'].concat(design.names);
        return '<p class="lbl">Regressiestatistieken</p>' + out([['meervoudige R', f(Math.sqrt(r.r2))], ['R²', f(r.r2)], ['R²<sub>adj</sub> (n − k − 1, zoals Excel/Minitab)', f(r.r2adj)],
               ['R²<sub>adj</sub> zoals REG p. 56 (n − k − 2)', f(r.r2adjP56)], ['standaardfout S = √MS<sub>E</sub>', f(r.s)], ['waarnemingen', f(r.n)],
               v.text.centre === '1' ? ['gecentreerd rond', design.means.map(function (m) { return f(m); }).join(' ; ')] : null]) +
          grid(['', 'df', 'SS', 'MS', 'F', 'p (Significance F)'], [['regressie', f(r.dfR), f(r.ssr), f(r.msr), f(r.F), fp(r.pF)],
            ['fout (residual)', f(r.dfE), f(r.sse), f(r.mse), '', ''], ['totaal', f(r.n - 1), f(r.sst), '', '', '']]) +
          grid(['', 'coëfficiënt', 's.e.', 't', 'p', 'BI ' + pc(1 - v.alpha)], r.coef.map(function (c, i) {
            return [names[i], f(c.b), f(c.se), f(c.t), fp(c.p), iv([c.lo, c.hi])]; })) +
          (num(r.y0) ? out([['ŷ bij x0', f(r.y0)], ['BI gemiddelde respons', iv(r.ciMean)], ['PI nieuwe waarneming', iv(r.pi)]]) : '');
      } }
  ];
  TOOLS.anova2 = [
    { title: 'Tweewegs-ANOVA, met of zonder herhalingen (zoals Excel)',
      help: 'Excel-indeling (Excel-functies p. 4): kolommen = niveaus van factor B; per niveau van factor A r regels onder elkaar ("Rows per sample" = r). r = 1: zonder herhalingen, de interactie is dan de fout. De cursus print de Excel-uitvoer "With Replication" in het GRR-werkboek (blad 2way anova).',
      form: ALPHA + inp('r', 'r = regels per niveau van A (herhalingen)', '', '1') + area('d', 'metingen', '', 8),
      run: function (v) {
        var r = Calc.anova2(parseRows(v.text.d), v.r, v.alpha);
        if (!r || !num(v.r)) return '';
        if (r.error) return warn(r.error);
        var h = '<p class="lbl">celgemiddelden (rij = niveau van A, kolom = niveau van B)</p>' +
          grid(['A \\ B'].concat(r.colMeans.map(function (_, j) { return 'B' + (j + 1); })).concat(['gemiddelde']),
               r.cellMeans.map(function (row, i) { return ['A' + (i + 1)].concat(row.map(function (x) { return f(x); })).concat([f(r.rowMeans[i])]); })
               .concat([['gemiddelde'].concat(r.colMeans.map(function (x) { return f(x); })).concat([f(r.grandMean)])]));
        h += grid(['bron', 'SS', 'df', 'MS', 'F', 'p-waarde', 'F-kritiek'], r.table.map(function (q) {
          return [q.name, f(q.ss), f(q.df), num(q.ms) ? f(q.ms) : '', num(q.F) ? f(q.F) : '', num(q.p) ? fp(q.p) : '', num(q.Fcrit) ? f(q.Fcrit) : '']; }));
        if (v.r > 1) {   // interaction pooled into the error, as the GRR workbook's derived table (MSA p. 36)
          var A = r.table[0], B = r.table[1], I = r.table[2], W = r.table[3], ssE = I.ss + W.ss, dfE = I.df + W.df, msE = ssE / dfE;
          var line = function (q) { var F = q.ms / msE; return [q.name, f(q.ss), f(q.df), f(q.ms), f(F), fp(Stats.fSf(F, q.df, dfE)), f(Stats.fIsf(v.alpha, q.df, dfE))]; };
          h += '<p class="lbl">zonder interactieterm: interactie samengenomen met de fout (MSA p. 36)</p>' +
            grid(['bron', 'SS', 'df', 'MS', 'F', 'p-waarde', 'F-kritiek'], [line(A), line(B), ['fout (interactie + binnen)', f(ssE), f(dfE), f(msE), '', '', '']]);
        }
        return h;
      } }
  ];

  /* ---------- SPC extras: limits from standard values, run rules ---------- */
  TOOLS.regelkaart.push(
    { title: 'Grenzen uit gekende (standaard)waarden µ en σ (Tabellen SPC p. 2, Table 7.2)',
      help: 'X̄: µ ± A·σ (Table 18) of µ ± 3σ/√n (SPC p. 63–64); R: d2σ, D1σ, D2σ; s: c2√(n/(n − 1))σ, B1√(n/(n − 1))σ, B2√(n/(n − 1))σ (s met n − 1).',
      form: inp('mu', 'µ') + inp('sigma', 'σ (van één meting)') + inp('n', 'n (subgroepgrootte)'),
      run: function (v) {
        var r = Calc.standardLimits(v.mu, v.sigma, v.n, K);
        if (!r) return '';
        var rows = [['X̄: µ ± 3σ/√n', f(r.x3[0]), f(r.x3[1]), f(r.x3[2]), 'σ/√n = ' + f(r.sigmaXbar)]];
        if (r.xA) rows.push(['X̄: µ ± A·σ', f(r.xA[0]), f(r.xA[1]), f(r.xA[2]), 'A = ' + f(r.A)]);
        if (r.R) rows.push(['R', f(r.R[0]), f(r.R[1]), f(r.R[2]), 'd2 = ' + f(r.d2) + ', D1 = ' + f(r.D1) + ', D2 = ' + f(r.D2)]);
        if (r.S) rows.push(['s', f(r.S[0]), f(r.S[1]), f(r.S[2]), 'c2 = ' + f(r.c2) + ', B1 = ' + f(r.B1) + ', B2 = ' + f(r.B2)]);
        return grid(['kaart', 'LCL', 'CL', 'UCL', 'constanten'], rows);
      } },
    { title: 'Regels voor speciale oorzaken (Western Electric, SPC p. 68–69)',
      help: 'Zones: C binnen 1σ, B tussen 1σ en 2σ, A tussen 2σ en 3σ van de centrale lijn, met σ die van de uitgezette grootheid (bij een X̄-kaart σ/√n = (UCL − CL)/3). SPC p. 68 zegt bij regels 2 en 3 niet of de punten aan dezelfde kant van de centrale lijn moeten liggen (bij regel 4 wel); de rekenmachine toont beide lezingen. De Western Electric-regels waar SPC p. 69 naar verwijst, tellen aan dezelfde kant. Regels 9 en 10 (ongewoon patroon, punt dicht bij een grens) vragen een oordeel.',
      form: inp('cl', 'centrale lijn CL') + inp('s', 'σ van de uitgezette grootheid') + inp('ucl', 'of UCL (dan σ = (UCL − CL)/3)') + area('x', 'punten in volgorde', '', 3),
      run: function (v) {
        var s = num(v.s) ? v.s : (num(v.ucl) && num(v.cl) ? (v.ucl - v.cl) / 3 : null), r = Calc.runRules(parseList(v.text.x), v.cl, s);
        if (!r) return '';
        var names = ['', '1. één of meer punten buiten de controlegrenzen', '2. 2 van 3 opeenvolgende punten voorbij 2σ (zelfde kant)',
          '3. 4 van 5 opeenvolgende punten voorbij 1σ (zelfde kant)', '4. 8 opeenvolgende punten aan één kant van de centrale lijn',
          '5. 6 punten op rij stijgend of dalend', '6. 15 punten op rij in zone C', '7. 14 punten op rij afwisselend op en neer',
          '8. 8 punten op rij aan beide kanten zonder één in zone C'];
        names['2b'] = '2. letterlijk: 2 van 3 voorbij 2σ (eender welke kant)'; names['3b'] = '3. letterlijk: 4 van 5 voorbij 1σ (eender welke kant)';
        return grid(['regel', 'signaal bij punt (laatste punt van het venster)'], [1, 2, '2b', 3, '3b', 4, 5, 6, 7, 8].map(function (q) {
            return [names[q], r.hits[q].length ? '<b class="flag">' + r.hits[q].join(', ') + '</b>' : 'geen']; })) +
          grid(['#', 'z = (x − CL)/σ', 'zone'], r.z.map(function (z, i) { return [String(i + 1), f(z, 3), r.zones[i]]; }));
      } });

  /* ---------- Bayes, Beta, k-class confusion matrix ---------- */
  TOOLS.bayes = [
    { title: 'Regel van Bayes: voorwaardelijke kans omkeren',
      help: 'P(A|B) = P(B|A)·P(A)/P(B) (ML p. 53) met P(B) = P(B|A)·P(A) + P(B|niet A)·P(niet A) (marginaal plus productregel, Data p. 18–20). Let op: P(A|B) ≠ P(B|A).',
      form: inp('pa', 'P(A) (voorkennis, prior)') + inp('ba', 'P(B | A)') + inp('bn', 'P(B | niet A)'),
      run: function (v) {
        var r = Calc.bayes(v.pa, v.ba, v.bn);
        return r ? out([['P(B)', fp(r.pB)], ['P(A | B)', fp(r.pAgivenB)], ['P(niet A | B)', fp(r.pNotAgivenB)], ['P(A | niet B)', fp(r.pAgivenNotB)],
                        ['odds vooraf × likelihood-ratio = odds achteraf', f(r.priorOdds) + ' × ' + f(r.likelihoodRatio) + ' = ' + f(r.posteriorOdds)]]) : '';
      }, pct: ['pa', 'ba', 'bn'] },
    { title: 'Bayesiaans bijwerken van een proportie met een Beta-prior',
      help: 'Web slides p. 55: prior Beta(α, β), k successen in n pogingen → posterior Beta(α + k, β + n − k); gemiddelde α/(α + β); MLE k/n. Modus en mediaan zoals in de Beta(2, 8)-figuur (Data-notities p. 4): modus (α − 1)/(α + β − 2), mediaan BETA.INV(0,5; α; β).',
      form: inp('a', 'α (prior)', '', '1') + inp('b', 'β (prior)', '', '1') + inp('k', 'k successen') + inp('n', 'n pogingen'),
      run: function (v) {
        var r = Calc.betaPosterior(v.a, v.b, v.k, v.n);
        if (!r) return '';
        var row = function (name, q) { return [name, 'Beta(' + f(q.a) + ', ' + f(q.b) + ')', f(q.mean), f(q.mode), f(q.median)]; };
        return grid(['', 'verdeling', 'gemiddelde', 'modus', 'mediaan'], [row('prior', r.prior)].concat(r.posterior ? [row('posterior', r.posterior)] : [])) +
          (num(r.mle) ? out([['MLE = k/n', f(r.mle)]]) : '');
      } }
  ];
  TOOLS.confusion.push(
    { title: 'Confusion matrix met k klassen: metrics per klasse',
      help: 'Notities Les 2 p. 15: rij i = werkelijke klasse, kolom j = voorspelde klasse; precision en recall per klasse (die klasse tegen de rest). ML p. 30 zet de voorspelling in de rijen: kies dan de andere oriëntatie.',
      form: sel('o', 'rijen zijn', [['actual', 'de werkelijke klasse (ML p. 31, notities)'], ['pred', 'de voorspelde klasse (ML p. 30)']]) + area('m', 'k × k aantallen, één rij per regel', '', 4),
      run: function (v) {
        var r = Calc.confusionK(parseRows(v.text.m), v.text.o === 'actual');
        return r ? out([['N', f(r.N)], ['accuracy = spoor/N', f(r.accuracy, 4)], ['foutratio 1 − accuracy (niet in de cursus)', f(r.error, 4)]]) +
          grid(['klasse', 'TP', 'FP', 'FN', 'TN', 'precision', 'recall', 'F1', 'support'], r.classes.map(function (c, i) {
            return [String(i + 1), f(c.tp), f(c.fp), f(c.fn), f(c.tn), f(c.precision, 4), f(c.recall, 4), f(c.f1, 4), f(c.support)]; })) : '';
      } });

  /* ---------- MSA extras (Les 5) ---------- */
  var KINDS = [['', '—'], ['cert', 'certificaat: U met dekkingsfactor k'], ['uni', 'uniform: halve breedte a (a/√3)'], ['range', 'type A: R/d2, gemiddelde van n'],
               ['sd', 'type A: s, gemiddelde van n'], ['u', 'standaardonzekerheid u rechtstreeks']];
  TOOLS.meetsysteem = [
    { title: 'Waargenomen en werkelijke Cp bij een gegeven %GRR (MSA p. 24–26)',
      help: '1/C<sub>po</sub>² = 1/C<sub>pa</sub>² + 1/C<sub>pm</sub>². %GRR van de procesvariatie: C<sub>po</sub> = C<sub>pa</sub>·√(1 − %GRR²). %GRR van de tolerantie: 1/C<sub>po</sub>² = 1/C<sub>pa</sub>² + %GRR². Vul C<sub>pa</sub> of C<sub>po</sub> in.',
      form: sel('basis', '%GRR ten opzichte van', [['tol', 'de tolerantie (USL − LSL)'], ['process', 'de procesvariatie (TV)']]) + inp('grr', '%GRR') + inp('cpa', 'werkelijke C<sub>pa</sub>') + inp('cpo', 'waargenomen C<sub>po</sub>'),
      run: function (v) {
        var r = Calc.cpObserved(v.text.basis, v.grr, v.cpa, v.cpo);
        if (!r) return '';
        return num(r.cpo) || num(r.cpa) ? out([num(r.cpo) ? ['waargenomen C<sub>po</sub>', f(r.cpo)] : ['werkelijke C<sub>pa</sub>', f(r.cpa)]]) : warn('geen oplossing: %GRR te groot voor deze Cp');
      }, pct: ['grr'] },
    { title: 'Gauge performance curve: kans om een stuk te aanvaarden (MSA p. 27)',
      help: 'β(X<sub>r</sub>) = Φ((USL − (X<sub>r</sub> + b))/σ<sub>GRR</sub>) − Φ((LSL − (X<sub>r</sub> + b))/σ<sub>GRR</sub>), b = bias. Vergelijkbaar met een OC-curve.',
      form: inp('lsl', 'LSL') + inp('usl', 'USL') + inp('b', 'bias b', '', '0') + inp('s', 'σ<sub>GRR</sub>') + area('x', 'referentiewaarden X<sub>r</sub>', '', 2),
      run: function (v) {
        var r = Calc.gaugePerformance(v.lsl, v.usl, v.b, v.s, parseList(v.text.x));
        return r ? grid(['X<sub>r</sub>', 'P(aanvaard)', 'P(afgekeurd)'], r.map(function (q) { return [f(q.x), fp(q.accept), fp(q.reject)]; })) : '';
      } },
    { title: 'Onzekerheidsbudget: u<sub>c</sub> en U = k·u<sub>c</sub> (MSA p. 28–29, stalen band)',
      help: 'Per bron een standaardonzekerheid: certificaat U/k; uniform a/√3; type A R/d2 of s, gedeeld door √n als je het gemiddelde van n metingen gebruikt. Onafhankelijke bronnen: u<sub>c</sub> = √Σu²; U = k·u<sub>c</sub> met k = 2 (≈ 95 %).',
      form: [1, 2, 3, 4, 5, 6].map(function (i) {
        return '<div class="fld wide row">' + sel('kind' + i, 'bron ' + i, KINDS) + inp('a' + i, 'waarde (U, a, R, s of u)') + inp('b' + i, 'k (certificaat) of d2') + inp('c' + i, 'n (gemiddelde van n metingen)') + '</div>';
      }).join('') + inp('val', 'gemeten waarde (optioneel)') + inp('corr', 'correctie (af te trekken)', '', '0') + inp('k', 'dekkingsfactor k', '', '2'),
      run: function (v) {
        var src = [1, 2, 3, 4, 5, 6].map(function (i) { return { kind: v.text['kind' + i], a: v['a' + i], b: v['b' + i], c: v['c' + i] }; }).filter(function (s) { return s.kind; });
        var r = Calc.uncertaintyBudget(src, v.k);
        if (!r) return '';
        var h = grid(['bron', 'soort', 'u', 'u²'], r.rows.map(function (q, i) { return [String(i + 1), q.kind, f(q.u), num(q.u) ? f(q.u * q.u) : '–']; })) +
          out([['u<sub>c</sub> = √Σu²', f(r.uc)], ['U = k·u<sub>c</sub>', f(r.U)]]);
        if (num(v.val)) { var c = v.val - (num(v.corr) ? v.corr : 0); h += out([['gecorrigeerde waarde ± U', f(c) + ' ± ' + f(r.U)], ['interval', iv([c - r.U, c + r.U])]]); }
        return h;
      } },
    { title: 'Onzekerheid doorrekenen (MSA p. 29)',
      help: 'u(x̄) = u(x)/√n; u(x + y) = √(u²(x) + u²(y)); u(x·y)/(x·y) = √(u²(x)/x² + u²(y)/y²); u(x²)/x² = 2u(x)/x; u(√x)/√x = u(x)/(2x).',
      form: inp('x', 'x') + inp('ux', 'u(x)') + inp('y', 'y (optioneel)') + inp('uy', 'u(y)') + inp('n', 'n (voor x̄, optioneel)'),
      run: function (v) {
        if (!num(v.x) || !num(v.ux)) return '';
        var rows = [['x² ± u', f(v.x * v.x) + ' ± ' + f(2 * v.ux * Math.abs(v.x))], ['√x ± u', v.x > 0 ? f(Math.sqrt(v.x)) + ' ± ' + f(Math.sqrt(v.x) * v.ux / (2 * v.x)) : '–']];
        if (num(v.n) && v.n > 0) rows.push(['u(x̄) = u(x)/√n', f(v.ux / Math.sqrt(v.n))]);
        if (num(v.y) && num(v.uy)) {
          rows.push(['x + y ± u', f(v.x + v.y) + ' ± ' + f(Math.sqrt(v.ux * v.ux + v.uy * v.uy))]);
          rows.push(['x·y ± u', f(v.x * v.y) + ' ± ' + f(Math.abs(v.x * v.y) * Math.sqrt(v.ux * v.ux / (v.x * v.x) + v.uy * v.uy / (v.y * v.y)))]);
        }
        return out(rows);
      } },
    { title: 'Bias-toets van een meetsysteem (MSA p. 31–32)',
      help: 'bias = X̿ − referentiewaarde; σ<sub>r</sub> = R̄/d2; t = bias/σ<sub>r</sub>·√(gm)·d2*/d2 met ν vrijheidsgraden; BI: bias ± σ<sub>r</sub>·d2/(d2*√(gm))·t<sub>1−α/2; ν</sub>. g subgroepen van m metingen; d2 (g → ∞), d2* en ν uit tabel MSA.pdf. De bias is significant als 0 niet in het interval ligt.',
      form: ALPHA + inp('ref', 'referentiewaarde') + area('d', 'metingen: één subgroep per regel (of vul hieronder in)', '', 3) + inp('xbb', 'X̿') + inp('rbar', 'R̄') + inp('g', 'g (subgroepen)') + inp('m', 'm (metingen per subgroep)'),
      run: function (v) {
        var rows = parseRows(v.text.d), xbb = v.xbb, rbar = v.rbar, g = v.g, m = v.m;
        if (rows.length) {
          if (rows.some(function (q) { return q.length !== rows[0].length || q.length < 2; })) return warn('elke subgroep even groot (m ≥ 2)');
          g = rows.length; m = rows[0].length; xbb = Stats.mean([].concat.apply([], rows));
          rbar = Stats.mean(rows.map(function (q) { return Math.max.apply(null, q) - Math.min.apply(null, q); }));
        }
        var r = Calc.biasTest(xbb, rbar, g, m, v.ref, v.alpha, M);
        if (!r) return '';
        if (r.error) return warn(r.error);
        return out([['g × m', f(g) + ' × ' + f(m)], ['X̿ ; R̄', f(xbb) + ' ; ' + f(rbar)], ['bias', f(r.bias)], ['d2 ; d2* ; ν', f(r.d2) + ' ; ' + f(r.d2s) + ' ; ' + f(r.nu)],
                    ['σ<sub>r</sub> = R̄/d2', f(r.sr)], ['t', f(r.t)], ['t-kritiek (1 − α/2; ν)', f(r.tcrit)], ['p-waarde (tweezijdig)', fp(r.p)],
                    ['BI voor de bias', iv(r.ci)], ['besluit', r.significant ? 'bias significant (0 ligt niet in het BI)' : 'geen significante bias']]);
      } },
    { title: 'Is de meeteenheid fijn genoeg? (MSA p. 30)',
      help: 'Tel de mogelijke waarden van de spreidingsbreedte (veelvouden van de meeteenheid MU) binnen de grenzen van de R-kaart (D3·R̄ … D4·R̄, Table 18). Te grof als er hoogstens 3 zijn (n = 2) of hoogstens 4 (n ≥ 3). Zonder R̄: het grensgeval σ = MU (R̄ = d2·MU).',
      form: inp('n', 'n (subgroepgrootte)') + inp('mu', 'meeteenheid MU') + inp('rbar', 'R̄ (optioneel)'),
      run: function (v) {
        var r = Calc.discrimination(v.n, v.mu, v.rbar, K);
        if (!r) return '';
        if (r.error) return warn(r.error);
        return out([[r.borderline ? 'R̄ = d2·MU (grensgeval σ = MU)' : 'R̄', f(r.rbar)], ['LCL<sub>R</sub> ; UCL<sub>R</sub>', f(r.lcl) + ' ; ' + f(r.ucl)],
                    ['breedte in MU', f(r.width)], ['mogelijke waarden', r.values.map(function (x) { return f(x); }).join(' ; ') + ' (' + r.values.length + ')'],
                    ['oordeel', r.tooCoarse ? '<b class="flag">meeteenheid te grof</b> (≤ ' + r.limit + ' waarden)' : 'voldoende (meer dan ' + r.limit + ' waarden)']]);
      } }
  ];

  /* ---------- wiring ---------- */
  function num(x) { return typeof x === 'number' && isFinite(x); }
  function values(form, pctNames) {
    var v = { text: {} };
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name) return;
      v.text[el.name] = el.value;
      if (el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') return;
      var x = parseNumber(el.value);
      if (x !== null && !isNaN(x) && (pctNames || []).indexOf(el.name) >= 0 && /%\s*$/.test(el.value)) x = x / 100;
      v[el.name] = x === null || isNaN(x) ? null : x;
      el.classList.toggle('bad', isNaN(x));
    });
    return v;
  }
  function mount(details) {
    if (details.dataset.ready) return;
    details.dataset.ready = '1';
    var body = details.querySelector('.tool-body'), name = details.dataset.tool;
    var tpl = document.getElementById('tpl-' + name);
    var blocks = TOOLS[name] || [];
    blocks.forEach(function (b) {
      var box = document.createElement('div');
      box.className = 'calc';
      box.innerHTML = '<h5>' + b.title + '</h5>' + (b.help ? '<p class="help">' + b.help + '</p>' : '') +
        '<form autocomplete="off">' + b.form + '</form><div class="calc-out"></div>';
      body.appendChild(box);
      var form = box.querySelector('form'), res = box.querySelector('.calc-out');
      function run() {
        try { res.innerHTML = b.run(values(form, b.pct), body) || ''; }
        catch (e) { res.innerHTML = warn(esc(e.message)); }
      }
      form.addEventListener('input', run);
      form.addEventListener('change', run);
      form.addEventListener('submit', function (e) { e.preventDefault(); });
      run();
    });
    if (tpl) body.appendChild(document.importNode(tpl.content, true));
  }
  document.querySelectorAll('details.tool').forEach(function (d) {
    d.addEventListener('toggle', function () { if (d.open) mount(d); });
    if (d.open) mount(d);
  });
  // a link or search result to a tool (or into a closed panel) opens the panels around it
  function openTarget() {
    var id = decodeURIComponent(location.hash.slice(1)), el = id && document.getElementById(id);
    for (var p = el; p; p = p.parentElement) if (p.tagName === 'DETAILS') p.open = true;
    if (el) el.scrollIntoView();
  }
  window.addEventListener('hashchange', openTarget);
  if (location.hash) openTarget();
})();
