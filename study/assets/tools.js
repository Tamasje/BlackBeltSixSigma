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
    { title: 'Defecten: DPU, DPO, DPMO', help: 'SPC p. 20; Dummies p. 152–156.',
      form: inp('D', 'D = aantal defecten') + inp('N', 'N = aantal eenheden') + inp('O', 'O = kansen (opportunities) per eenheid'),
      run: function (v) {
        var r = Calc.defects(v.D, v.N, v.O);
        return r ? out([['DPU = D / N', f(r.dpu)], ['DPO = D / (N·O)', f(r.dpo)], ['DPMO = DPO · 10⁶', f(r.dpmo)],
                        ['yield per kans = 1 − DPO', fp(r.ypo)], ['throughput yield = 1 − DPU', fp(r.ty)],
                        ['RTY ≈ e^(−DPU)', fp(r.rtyApprox), 'Dummies p. 156: als DPU klein is']]) : '';
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
    { title: 'Twee proporties: π1 − π2 (normale benadering)', help: 'CI Further Reading p. 20; Dummies p. 197.',
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
      help: 'Eén rij per regel, aantallen gescheiden door spaties (plak gerust uit Excel). Onafhankelijk ⇔ P(A en B) = P(A)·P(B) voor elke cel (Naert Les 1 p. 22–23).',
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
            inp('rbar', 'R̄') + inp('sbar', 's̄') + inp('n', 'n (subgroepgrootte voor R̄, s̄)') + inp('mrbar', 'MR̄') + inp('overall', 'totale s (lange termijn)'),
      run: function (v) {
        var rows = Calc.capability({ lsl: v.lsl, usl: v.usl, mean: v.mean, sigma: v.sigma, rbar: v.rbar, sbar: v.sbar, n: v.n, mrbar: v.mrbar, overall: v.overall }, K);
        if (!rows.length) return (num(v.rbar) || num(v.sbar)) && !num(v.n) ? warn('geef n voor R̄/d2 of s̄/c4') : '';
        var lines = [['σ', 'sigma', f], ['Cp = (USL − LSL)/6σ', 'cp', f], ['niveau (SPC p. 40)', 'level', f], ['Cpu = (USL − x̄)/3σ', 'cpu', f],
                     ['Cpl = (x̄ − LSL)/3σ', 'cpl', f], ['Cpk = min(Cpu, Cpl)', 'cpk', f], ['Cpk > 1,33?', 'capable', f], ['Z tot LSL', 'zLsl', f],
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
      } },
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
      help: 'Rijen = werkelijke klasse, kolommen = voorspelde klasse (Naert Les 2 p. 29–32). Vul per model de vier aantallen in, rij per rij.',
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
          '<p class="xl">Grote kloof train ↔ test: overfitting (variantie). Beide laag: underfitting (bias). Naert Les 2 p. 19–28.</p>' : '';
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
