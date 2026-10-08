/* "Hulpmiddelen" panels of the study guide: renders each calculator (Calc, calc.js) and each course table
   (<template id="tpl-…"> written by build_study.py) into its <details class="tool" data-tool="…"> on first opening.
   Inputs: yellow; results: green; a field the calculator derived from the others: red and locked.
   Decimal comma or point; lists separated by spaces, tabs, new lines or ';'. */
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
  // a text field (names, labels): read as text, never flagged as an unreadable number
  function txt(name, label, ph) {
    return '<label class="fld"><span>' + label + '</span><input name="' + name + '" data-text="1" autocomplete="off" spellcheck="false"' +
      (ph ? ' placeholder="' + ph + '"' : '') + '></label>';
  }
  function area(name, label, ph, rows) {
    return '<label class="fld wide"><span>' + label + '</span><textarea name="' + name + '" rows="' + (rows || 4) +
      '" spellcheck="false"' + (ph ? ' placeholder="' + ph + '"' : '') + '></textarea></label>';
  }
  function sel(name, label, options) {
    return '<label class="fld"><span>' + label + '</span><select name="' + name + '">' + options.map(function (o) {
      return '<option value="' + o[0] + '">' + o[1] + '</option>'; }).join('') + '</select></label>';
  }
  // α or the confidence level: 0,05, 5 %, 0,95 and 95 % all mean α = 0,05 (values() turns a confidence into α)
  var ALPHA = inp('alpha', 'α of betrouwbaarheid (0,05 · 5 % · 95 %)', '', '0,05');
  function alphaRow(alpha) {
    return num(alpha) ? ['α ; betrouwbaarheid 1 − α', f(alpha) + ' ; ' + pc(1 - alpha)] : null;
  }
  // critical values and half widths before the centre is known: "x̄ ± h" (CI FR p. 9-15)
  function halfRows(q, alpha, sym, centre, spread) {
    if (!num(q.c2)) return [];
    return [['kritieke waarde tweezijdig ' + sym + '<sub>1−α/2</sub>', f(q.c2), 'P(' + sym + ' ≤ ' + f(q.c2, 4) + ') = ' + pc(1 - alpha / 2)],
            ['kritieke waarde eenzijdig ' + sym + '<sub>1−α</sub>', f(q.c1), 'P(' + sym + ' ≤ ' + f(q.c1, 4) + ') = ' + pc(1 - alpha)],
            ['BI tweezijdig: ' + centre + ' ± ' + sym + '<sub>1−α/2</sub>·' + spread, centre + ' ± ' + f(q.half2)],
            ['enkel ondergrens ("minstens …")', centre + ' − ' + f(q.half1) + ' … +∞'],
            ['enkel bovengrens ("hoogstens …")', '−∞ … ' + centre + ' + ' + f(q.half1)]];
  }

  /* ---------- the calculators: blocks of {title, help, form, run(v) → html} ---------- */
  var TOOLS = {};

  // "berekend" next to every value the solver derived (the others were typed in)
  function marker(r) { return function (key) { return r.solved.indexOf(key) >= 0 ? 'berekend' : ''; }; }
  // a block's result: its html plus the input fields it derived ({name: value}), which mount() locks
  function result(html, solved) { return { html: html, solved: solved || {} }; }
  // the fields a solver (r.solved) derived, with their values
  function derived(r) { var s = {}; r.solved.forEach(function (key) { s[key] = r[key]; }); return s; }
  function merge() {
    var s = {};
    Array.prototype.forEach.call(arguments, function (o) { Object.keys(o || {}).forEach(function (key) { s[key] = o[key]; }); });
    return s;
  }
  // mark the cell of the course Z table (below the calculators) that belongs to z, rounded to 2 decimals
  function highlightZ(box, z) {
    var cells = box.querySelectorAll('td[data-z]'), key = num(z) ? (Math.round(z * 100) / 100).toFixed(2) : null, hit = null;
    cells.forEach(function (c) {
      var on = key !== null && (c.dataset.z === key || (key === '0.00' && c.dataset.z === '-0.00'));
      c.classList.toggle('hit', on);
      if (on) hit = c;
    });
    return hit;
  }

  TOOLS.normaal = [
    { title: 'Alles uit alles: µ, σ, x, z en de kansen',
      help: 'Vul in wat gegeven is en laat de rest leeg. µ, σ en x geven z en de kansen; µ, x en een staartkans geven σ; ' +
            'σ, x en een staartkans geven µ; µ, σ en een kans geven x; een kans alleen geeft z (standaardnormaal). ' +
            'De cel van z wordt gemarkeerd in de Z-tabel van de cursus onderaan.',
      form: inp('mu', 'µ (gemiddelde)') + inp('sigma', 'σ (standaardafwijking)') + inp('x', 'x (waarde, grens)') +
            inp('z', 'z = (x − µ)/σ') + inp('pl', 'P(X ≤ x) (fractie of %)') + inp('pr', 'P(X > x) (fractie of %)'),
      run: function (v, box) {
        var r = Calc.normalSolve({ mu: v.mu, sigma: v.sigma, x: v.x, z: v.z, pl: v.pl, pr: v.pr }), mark = marker(r);
        var cell = highlightZ(box, r.z);
        return result(out([['µ', f(r.mu), mark('mu')], ['σ', f(r.sigma), mark('sigma')], ['σ² (variantie)', f(num(r.sigma) ? r.sigma * r.sigma : null)],
                    ['x', f(r.x), mark('x')], ['z', f(r.z), mark('z')], ['P(X ≤ x)', fp(r.pl), mark('pl')],
                    ['P(X > x)', fp(r.pr), mark('pr')], ['ppm boven x / onder x', f(num(r.pr) ? r.pr * 1e6 : null) + ' / ' + f(num(r.pl) ? r.pl * 1e6 : null)],
                    num(r.z) ? ['Z-tabel van de cursus bij z = ' + f(Math.round(r.z * 100) / 100), cell ? cell.textContent : 'buiten de tabel (−3,49 … 3,49)', 'kans links van z, 4 decimalen'] : null]) +
          (r.notes.length ? warn(r.notes.join('; ')) : ''), derived(r));
      }, pct: ['pl', 'pr'] },
    { title: 'Interval [a ; b]: kans binnen en buiten, µ ± kσ, of grenzen bij een kans',
      help: 'Vul in wat gegeven is: µ, σ, a en b geven de kansen; µ, σ en k geven de grenzen µ ± kσ (68-95-99,7); ' +
            'µ, σ en een kans geven het centrale interval; a, b en k of een kans geven µ en σ (symmetrisch interval); ' +
            'µ, één grens en k of een kans geven σ.',
      form: inp('mu', 'µ') + inp('sigma', 'σ') + inp('a', 'ondergrens a (bv. LSL)') + inp('b', 'bovengrens b (bv. USL)') +
            inp('k', 'k (grenzen µ ± kσ)') + inp('inside', 'kans binnen [a ; b]') + inp('outside', 'kans buiten [a ; b]'),
      run: function (v) {
        var r = Calc.normalInterval({ mu: v.mu, sigma: v.sigma, a: v.a, b: v.b, k: v.k, inside: v.inside, outside: v.outside }), mark = marker(r);
        if (!num(r.mu) && !num(r.sigma) && !num(r.k)) return r.notes.length ? warn(r.notes.join('; ')) : '';
        return result(out([['µ', f(r.mu), mark('mu')], ['σ', f(r.sigma), mark('sigma')], ['a', f(r.a), mark('a')], ['b', f(r.b), mark('b')],
                    ['k', f(r.k), mark('k')], ['z van a / z van b', f(r.za) + ' / ' + f(r.zb)], ['P(X < a)', fp(r.below)],
                    ['P(a < X < b) (binnen)', fp(r.inside), mark('inside')], ['P(X > b)', fp(r.above)],
                    ['buiten [a ; b]', fp(r.outside), (mark('outside') + ' ' + (num(r.outside) ? f(r.outside * 1e6) + ' ppm' : '')).trim()]]) +
          (r.notes.length ? warn(r.notes.join('; ')) : ''), derived(r));
      }, pct: ['inside', 'outside'] },
    { title: 'Gemiddelde van n waarnemingen: σ<sub>x̄</sub> = σ / √n (twee van de drie)',
      help: 'Gebruik σ/√n daarna als σ in het blok "alles uit alles" voor kansen op x̄ (centrale limietstelling, SPC p. 62–63).',
      form: inp('sigma', 'σ (van één waarneming)') + inp('n', 'n') + inp('se', 'σ<sub>x̄</sub>'),
      run: function (v) {
        var se, sigma, n;
        if (all2(v.sigma, v.n) && v.n > 0) return result(out([['σ<sub>x̄</sub> = σ / √n', f(se = v.sigma / Math.sqrt(v.n)), 'berekend']]), { se: se });
        if (all2(v.se, v.n) && v.n > 0) return result(out([['σ = σ<sub>x̄</sub> · √n', f(sigma = v.se * Math.sqrt(v.n)), 'berekend']]), { sigma: sigma });
        if (all2(v.sigma, v.se) && v.se > 0) return result(out([['n = (σ / σ<sub>x̄</sub>)²', f(n = Math.pow(v.sigma / v.se, 2)), 'naar boven afronden: ' + f(Math.ceil(n - 1e-9))]]), { n: n });
        return '';
      } }
  ];
  function all2(a, b) { return num(a) && num(b); }

  TOOLS.sigma = [
    { title: 'Alles uit alles: D, N, O, DPO, DPMO, yield, Z en sigmaniveau',
      help: 'Vul één grootheid in (of D, N en O) en de rest volgt; met DPO en twee van D, N, O volgt de derde. De tabel onderaan zet de gedrukte sigmatabellen naast elkaar.',
      form: inp('D', 'D = aantal defecten') + inp('N', 'N = aantal eenheden') + inp('O', 'O = kansen (opportunities) per eenheid') +
            inp('dpo', 'DPO') + inp('dpmo', 'DPMO') + inp('yield', 'yield = 1 − DPO (fractie of %)') + inp('z', 'Z (zonder verschuiving)') +
            inp('level', 'sigmaniveau (met 1,5σ-verschuiving)'),
      run: function (v) {
        var r = Calc.sigmaSolve({ D: v.D, N: v.N, O: v.O, dpo: v.dpo, dpmo: v.dpmo, yield: v.yield, z: v.z, level: v.level }), mark = marker(r);
        if (!num(r.dpo)) return r.notes.length ? warn(r.notes.join('; ')) : '';
        return result(out([[r.D, r.N, r.O].some(num) ? ['D ; N ; O', f(r.D) + ' ; ' + f(r.N) + ' ; ' + f(r.O), ['D', 'N', 'O'].filter(function (q) { return r.solved.indexOf(q) >= 0; }).map(function (q) { return q + ' berekend'; }).join(', ')] : null,
                    ['DPO = D / (N·O)', f(r.dpo), mark('dpo')], ['DPMO = DPO · 10⁶', f(r.dpmo), mark('dpmo')], ['yield = 1 − DPO', fp(r.yield), mark('yield')],
                    ['Z: P(Z ≤ Z) = 1 − DPO', f(r.z), mark('z')], ['sigmaniveau = Z + 1,5', f(r.level), mark('level')],
                    'hetzelfde sigmaniveau gelezen zonder verschuiving (SPC p. 40)',
                    ['DPMO, één staart voorbij het niveau', f(r.oneTail)], ['DPMO, beide staarten (gecentreerd, Cp = niveau/3)', f(r.twoTails), 'SPC p. 40: Cp = 2 → 2 per miljard']]) +
          (r.notes.length ? warn(r.notes.join('; ')) : ''), derived(r));
      }, pct: ['yield'] }
  ];

  TOOLS.kwantielen = [
    { title: 'Kritieke waarden ↔ staartkansen (z, t, χ², F)',
      help: 'Geef α voor de kritieke waarden, of de waarde van een toetsgrootheid voor de p-waarden; met beide ook het besluit.',
      form: sel('dist', 'verdeling', [['z', 'z (standaardnormaal)'], ['t', 't'], ['chi2', 'χ²'], ['F', 'F']]) +
            inp('d1', 'vrijheidsgraden (F: teller)') + inp('d2', 'F: vrijheidsgraden noemer') + ALPHA +
            inp('stat', 'waarde van de toetsgrootheid'),
      run: function (v) {
        var q = Calc.quantiles(v.text.dist, v.d1, v.d2, v.alpha), p = Calc.pValues(v.text.dist, v.d1, v.d2, v.stat), h = '';
        var sym = v.text.dist === 'z' || v.text.dist === 't';
        if (q) {
          h += out([alphaRow(v.alpha), ['linkse kritieke waarde', f(q.left), 'kans α links ervan'], ['rechtse kritieke waarde', f(q.right), 'kans α rechts ervan'],
                    ['tweezijdig: α/2 links en rechts', f(q.twoLo) + ' en ' + f(q.twoHi)]]);
        }
        if (p) {
          h += out([['P(X ≤ waarde) (H<sub>A</sub>: <)', fp(p.left), q ? (p.left < v.alpha ? 'verwerp H0' : 'H0 niet verwerpen') : ''],
                    ['P(X > waarde) (H<sub>A</sub>: >)', fp(p.right), q ? (p.right < v.alpha ? 'verwerp H0' : 'H0 niet verwerpen') : ''],
                    ['tweezijdig (H<sub>A</sub>: ≠)', fp(p.two), (sym ? '2 · P(X > |waarde|)' : '2 · kleinste staart') +
                      (q ? '; ' + (p.two < v.alpha ? 'verwerp H0' : 'H0 niet verwerpen') : '')]]);
        }
        return h;
      }, pct: ['alpha'] }
  ];

  // n, mean and s from pasted data (then those fields are derived and locked) or from the fields themselves
  function summary(v, area, n, m, s) {
    var xs = parseList(v.text[area]);
    if (xs.length >= 2) {
      var d = Calc.describe(xs), solved = {};
      solved[n] = d.n; solved[m] = d.mean; solved[s] = d.s;
      return { n: d.n, mean: d.mean, s: d.s, fromData: true, solved: solved };
    }
    return { n: v[n], mean: v[m], s: v[s], fromData: false, solved: {} };
  }
  TOOLS.gemiddelde = [
    { title: 'Eén gemiddelde µ: standaardfout, kansen, BI en toets (z met σ, t met s)',
      help: 'Vul in wat je hebt; elk resultaat verschijnt zodra zijn gegevens er zijn. n met σ (gekend, uit de opgave: z) of ' +
            's (uit de steekproef: t) geeft de standaardfout. Met d ook hoeveel standaardfouten d is en de kans dat x̄ binnen d ' +
            'van µ valt. Met α of de betrouwbaarheid de kritieke waarde en de halve breedte van het BI, ook zonder x̄ ("x̄ ± …"). ' +
            'Met x̄ het BI zelf. µ0 is het getal uit de bewering die je toetst, bv. "de machine vult gemiddeld 500 g": µ0 = 500 ' +
            '(H0: µ = 500); de toets geeft dan voor elke alternatieve hypothese (≠, >, <) de p-waarde en het besluit.',
      form: ALPHA + area('data', 'ruwe data (optioneel; geeft n, x̄ en s)', '', 3) + inp('n', 'n (steekproefgrootte)') +
            inp('m', 'x̄ (steekproefgemiddelde)') + inp('s', 's (uit de steekproef → t)') + inp('sigma', 'σ (gekend → z)') +
            inp('d', 'afstand d tot µ (bv. "hoogstens 5 cm van µ": 5)') + inp('mu0', 'µ0: waarde uit de bewering (H0: µ = µ0)'),
      run: function (v) {
        var d = summary(v, 'data', 'n', 'm', 's'), r = Calc.oneMean(d.n, d.mean, d.s, v.sigma, v.mu0, v.alpha, v.d);
        if (!r) return result(num(d.n) ? warn('geef σ (gekend) of s (uit de steekproef) voor de standaardfout') : '', d.solved);
        var h = out([d.fromData ? 'uit de data' : null, ['n', f(d.n)], num(d.mean) ? ['x̄', f(d.mean)] : null,
                     num(d.s) ? ['s', f(d.s)] : null, ['vrijheidsgraden n − 1 (voor t)', f(r.df)], alphaRow(v.alpha)]);
        [['z', 'σ gekend: z', 'σ/√n'], ['t', 's uit de steekproef (σ onbekend): t met n − 1 vrijheidsgraden', 's/√n']].forEach(function (m) {
          var q = r[m[0]], sym = m[0];
          if (!q) return;
          var centre = num(r.xbar) ? f(r.xbar) : 'x̄';
          h += '<p class="lbl">' + m[1] + '</p>' + out([
            ['standaardfout ' + m[2], f(q.se)],
            num(q.k) ? ['d in standaardfouten: d / (' + m[2] + ')', f(q.k)] : null,
            num(q.k) ? ['P(|x̄ − µ| ≤ d) = 2·P(' + sym + ' ≤ ' + f(q.k, 4) + ') − 1', fp(q.within)] : null,
            num(q.k) ? ['P(x̄ − µ > d) = P(' + sym + ' > ' + f(q.k, 4) + ')', fp(q.beyond), 'even groot als P(x̄ − µ < −d)'] : null]
            .concat(halfRows(q, v.alpha, sym, centre, m[2])));
          if (q.ci) h += ciRows(q.ci, 'µ (' + (sym === 'z' ? 'z, σ gekend' : 't, σ onbekend') + ')');
          if (q.test) h += '<p class="lbl">' + sym + '-toets van H0: µ = µ0 = ' + f(v.mu0) + ', toetsgrootheid (x̄ − µ0)/(' + m[2] + ')</p>' +
            testRows(q.test, sym === 'z' ? null : r.df);
        });
        if (!num(v.alpha)) h += '<p class="xl">Vul α of de betrouwbaarheid in voor de kritieke waarde en het BI.</p>';
        else if (num(v.mu0) && !num(r.xbar)) h += '<p class="xl">Vul x̄ in voor de toets van µ0.</p>';
        return result(h, d.solved);
      } }
  ];
  TOOLS.tweegemiddelden = [
    { title: 'Twee onafhankelijke steekproeven: µ1 − µ2 (gepoolde s, t met n1 + n2 − 2)',
      help: 'Plak beide reeksen óf vul de samenvattingen in. n en s van beide geven al de gepoolde s, de standaardfout en ' +
            '(met α) de halve breedte; met beide gemiddelden ook het BI en de toets. H0: µ1 − µ2 = d0, meestal 0 ("geen verschil").',
      form: ALPHA + area('d1', 'data steekproef 1 (optioneel)', '', 2) + area('d2', 'data steekproef 2 (optioneel)', '', 2) +
            inp('n1', 'n1') + inp('m1', 'x̄1') + inp('s1', 's1') + inp('n2', 'n2') + inp('m2', 'x̄2') + inp('s2', 's2') +
            inp('d0', 'd0 in H0: µ1 − µ2 = d0 (leeg = 0)'),
      run: function (v) {
        var a = summary(v, 'd1', 'n1', 'm1', 's1'), b = summary(v, 'd2', 'n2', 'm2', 's2');
        var r = Calc.twoMeansPooled(a.n, a.mean, a.s, b.n, b.mean, b.s, v.d0, v.alpha), solved = merge(a.solved, b.solved);
        if (!r) return result('', solved);
        var centre = num(r.diff) ? f(r.diff) : '(x̄1 − x̄2)';
        var h = out([['steekproef 1: n, x̄, s', f(a.n) + ' ; ' + f(a.mean) + ' ; ' + f(a.s)], ['steekproef 2: n, x̄, s', f(b.n) + ' ; ' + f(b.mean) + ' ; ' + f(b.s)],
                     alphaRow(v.alpha), num(r.diff) ? ['x̄1 − x̄2', f(r.diff)] : null, ['gepoolde s_p', f(r.sp)],
                     ['s.e. = s_p √(1/n1 + 1/n2)', f(r.se)], ['vrijheidsgraden n1 + n2 − 2', f(r.df)]].concat(halfRows(r, v.alpha, 't', centre, 's.e.')));
        if (r.ci) h += ciRows(r.ci, 'µ1 − µ2') + '<p class="lbl">t-toets van H0: µ1 − µ2 = ' + f(num(v.d0) ? v.d0 : 0) + '</p>' + testRows(r.test, r.df);
        return result(h, solved);
      } },
    { title: 'Gepaarde waarnemingen: verschillen v = x1 − x2 (t met n − 1)',
      help: 'Plak per regel een paar "x1 x2", of enkel de verschillen, of vul n, v̄ en s_v in. n en s_v geven al de standaardfout en ' +
            '(met α) de halve breedte. H0: µ_v = d0, meestal 0 ("geen verschil").',
      form: ALPHA + area('pairs', 'paren x1 x2 (één paar per regel) of verschillen', '', 3) + inp('n', 'n (aantal paren)') + inp('m', 'v̄') + inp('s', 's_v') +
            inp('d0', 'd0 in H0: µ_v = d0 (leeg = 0)'),
      run: function (v) {
        var rows = parseRows(v.text.pairs), diffs = rows.length && rows.every(function (r) { return r.length === 2; })
          ? rows.map(function (r) { return r[0] - r[1]; }) : [].concat.apply([], rows);
        var d = diffs.length >= 2 ? Calc.describe(diffs) : { n: v.n, mean: v.m, s: v.s };
        var r = Calc.paired(d.n, d.mean, d.s, v.d0, v.alpha), solved = diffs.length >= 2 ? { n: d.n, m: d.mean, s: d.s } : {};
        if (!r) return result('', solved);
        var h = out([['n', f(d.n)], num(d.mean) ? ['v̄', f(d.mean)] : null, ['s_v', f(d.s)], alphaRow(v.alpha), ['s.e. = s_v/√n', f(r.se)],
                     ['vrijheidsgraden n − 1', f(r.df)]].concat(halfRows(r, v.alpha, 't', num(d.mean) ? f(d.mean) : 'v̄', 's_v/√n')));
        if (r.ci) h += ciRows(r.ci, 'µ_v') + '<p class="lbl">gepaarde t-toets</p>' + testRows(r.test, r.df);
        return result(h, solved);
      } }
  ];
  TOOLS.proportie = [
    { title: 'Eén proportie π: BI (normale benadering en exact) en Z-toets',
      help: 'Vul in wat je hebt. n en x geven p en de standaardfout; met α of de betrouwbaarheid ook de BI. ' +
            'π0 is de fractie uit de bewering die je toetst (H0: π = π0, bv. "hoogstens 2 % defect": π0 = 0,02); n en π0 geven al ' +
            'de standaardfout onder H0 en (met α) de kritieke p, ook zonder x.',
      form: ALPHA + inp('n', 'n') + inp('x', 'x = aantal successen (bv. defecten)') + inp('pi0', 'π0: fractie uit de bewering (H0: π = π0)'),
      run: function (v) {
        var r = Calc.oneProportion(v.n, v.x, v.pi0, v.alpha);
        if (!r) return '';
        var h = out([alphaRow(v.alpha), num(r.p) ? ['p = x / n', fp(r.p)] : null, num(r.se) ? ['s.e. = √(p(1 − p)/n)', f(r.se)] : null,
                     num(r.se0) ? ['s.e. onder H0 = √(π0(1 − π0)/n)', f(r.se0)] : null,
                     num(r.se0) ? ['voorwaarde voor de Z-toets n·π0 > 5', r.condition ? 'ja' : '<b>nee</b>: gebruik het exacte interval'] : null]);
        if (r.ci) h += ciRows(r.ci, 'π (normale benadering)') +
          grid(['exact BI (Clopper-Pearson)', 'van', 'tot'], [['tweezijdig', fp(r.exact.two[0]), fp(r.exact.two[1])],
            ['enkel ondergrens', fp(r.exact.lower[0]), '+∞'], ['enkel bovengrens', fp(r.exact.upper[0]), fp(r.exact.upper[1])]]);
        if (r.critical && !r.test) h += '<p class="lbl">H0 verwerpen als p buiten deze grenzen valt</p>' + grid(['H<sub>A</sub>', 'kritieke p'], [
            ['π ≠ π0', fp(r.critical.ne[0]) + ' en ' + fp(r.critical.ne[1])], ['π > π0', fp(r.critical.gt)], ['π < π0', fp(r.critical.lt)]]);
        if (r.test) h += '<p class="lbl">Z-toets van H0: π = π0 — z = (p − π0)/√(π0(1 − π0)/n)</p>' + testRows(r.test, null);
        if (!num(v.alpha)) h += '<p class="xl">Vul α of de betrouwbaarheid in voor de BI en de toets.</p>';
        return h;
      }, pct: ['pi0'] },
    { title: 'Twee proporties: π1 − π2 (normale benadering)',
      help: 'n en x van beide geven p1, p2, het verschil en de standaardfout; met α ook de BI.',
      form: ALPHA + inp('n1', 'n1') + inp('x1', 'x1') + inp('n2', 'n2') + inp('x2', 'x2'),
      run: function (v) {
        var r = Calc.twoProportions(v.n1, v.x1, v.n2, v.x2, v.alpha);
        if (!r) return '';
        return out([alphaRow(v.alpha), ['p1', fp(r.p1)], ['p2', fp(r.p2)], ['p1 − p2', fp(r.diff)], ['s.e. = √(p1(1 − p1)/n1 + p2(1 − p2)/n2)', f(r.se)]]) +
          (r.ci ? ciRows(r.ci, 'π1 − π2') : '');
      } }
  ];
  // χ² or F critical values, and the limits they put on s or on F, before the data are known
  function critRows(c, sym) {
    return c ? [['kritieke waarden tweezijdig ' + sym + '<sub>α/2</sub> ; ' + sym + '<sub>1−α/2</sub>', f(c.lo2) + ' ; ' + f(c.hi2)],
                ['kritieke waarde eenzijdig ' + sym + '<sub>α</sub> (links) ; ' + sym + '<sub>1−α</sub> (rechts)', f(c.lo1) + ' ; ' + f(c.hi1)]] : [];
  }
  TOOLS.variantie = [
    { title: 'Eén variantie σ²: BI (σ² en σ) en χ²-toets (n − 1 vrijheidsgraden)',
      help: 'Vul in wat je hebt. n en α geven de χ²-kritieke waarden; met σ0 (de waarde uit de bewering, H0: σ = σ0) ook de s ' +
            'waarboven of waaronder je H0 verwerpt; met s (of ruwe data) de BI en de toets.',
      form: ALPHA + area('data', 'ruwe data (optioneel)', '', 2) + inp('n', 'n') + inp('s', 's') + inp('sigma0', 'σ0: waarde uit de bewering (H0: σ = σ0)'),
      run: function (v) {
        var d = summary(v, 'data', 'n', 'm', 's'), r = Calc.oneVariance(d.n, d.s, v.sigma0, v.alpha);
        if (!r) return result('', d.solved);
        var sq = function (x) { return x === Infinity ? Infinity : Math.sqrt(x); };
        var h = out([['n', f(d.n)], num(d.s) ? ['s', f(d.s)] : null, num(r.s2) ? ['s²', f(r.s2)] : null, ['vrijheidsgraden n − 1', f(r.df)],
                     alphaRow(v.alpha)].concat(critRows(r.crit, 'χ²')));
        if (r.sLimits && !r.test) h += '<p class="lbl">H0: σ = σ0 verwerpen als s buiten deze grenzen valt: s = σ0·√(χ²/(n − 1))</p>' +
          grid(['H<sub>A</sub>', 'kritieke s'], [['σ ≠ σ0', f(r.sLimits.ne[0]) + ' en ' + f(r.sLimits.ne[1])],
            ['σ > σ0', f(r.sLimits.gt)], ['σ < σ0', f(r.sLimits.lt)]]);
        if (r.ci) h += grid(['BI', 'σ² van', 'σ² tot', 'σ van', 'σ tot'], [
            ['tweezijdig', f(r.ci.two[0]), f(r.ci.two[1]), f(sq(r.ci.two[0])), f(sq(r.ci.two[1]))],
            ['enkel ondergrens (σ minstens …; H<sub>A</sub>: σ > σ0)', f(r.ci.lower[0]), '+∞', f(sq(r.ci.lower[0])), '+∞'],
            ['enkel bovengrens (σ hoogstens …; H<sub>A</sub>: σ < σ0)', '0', f(r.ci.upper[1]), '0', f(sq(r.ci.upper[1]))]]);
        if (r.test) {
          var t = r.test;
          h += '<p class="lbl">χ²-toets: χ² = (n − 1)s²/σ0²</p>' + grid(['H<sub>A</sub>', 'χ²', 'kritieke waarde(n)', 'p-waarde', 'besluit'], [
            ['σ ≠ σ0', f(t.stat), f(t.ne.crit[0]) + ' en ' + f(t.ne.crit[1]), fp(t.ne.p), t.ne.d],
            ['σ > σ0', f(t.stat), f(t.gt.crit[0]), fp(t.gt.p), t.gt.d], ['σ < σ0', f(t.stat), f(t.lt.crit[0]), fp(t.lt.p), t.lt.d]]);
        }
        if (!num(v.alpha)) h += '<p class="xl">Vul α of de betrouwbaarheid in voor de kritieke waarden, de BI en de toets.</p>';
        return result(h, d.solved);
      } },
    { title: 'Twee varianties: BI voor σ1²/σ2² en F-toets (F(n1 − 1, n2 − 1))',
      help: 'Plak beide reeksen óf vul n en s van elk in (zoals examenvraag 2). n1, n2 en α geven al de F-kritieke waarden; ' +
            'met s1 en s2 ook F, de BI en de toets van H0: σ1 = σ2.',
      form: ALPHA + area('d1', 'data 1 (optioneel)', '', 2) + area('d2', 'data 2 (optioneel)', '', 2) + inp('n1', 'n1') + inp('s1', 's1') +
            inp('n2', 'n2') + inp('s2', 's2'),
      run: function (v) {
        var a = summary(v, 'd1', 'n1', 'x', 's1'), b = summary(v, 'd2', 'n2', 'x', 's2'), solved = merge(a.solved, b.solved);
        var r = Calc.twoVariances(a.n, a.s, b.n, b.s, v.alpha);
        if (!r) return result('', solved);
        var h = out([['n1 ; s1', f(a.n) + ' ; ' + f(a.s)], ['n2 ; s2', f(b.n) + ' ; ' + f(b.s)], ['vrijheidsgraden n1 − 1 ; n2 − 1', f(r.v1) + ' ; ' + f(r.v2)],
                     alphaRow(v.alpha), num(r.F) ? ['F = s1²/s2²', f(r.F)] : null].concat(critRows(r.crit, 'F')));
        if (r.ci) {
          var t = r.test;
          h += grid(['BI', 'σ1²/σ2² van', 'tot', 'σ2²/σ1² van', 'tot'], [
              ['tweezijdig', f(r.ci.two[0]), f(r.ci.two[1]), f(r.ciInv.two[0]), f(r.ciInv.two[1])],
              ['σ1²/σ2² minstens … (σ2²/σ1² hoogstens …)', f(r.ci.lower[0]), '+∞', '0', f(r.ciInv.upper[1])],
              ['σ1²/σ2² hoogstens … (σ2²/σ1² minstens …)', '0', f(r.ci.upper[1]), f(r.ciInv.lower[0]), '+∞']]) +
            '<p class="lbl">F-toets van H0: σ1 = σ2</p>' + grid(['H<sub>A</sub>', 'F', 'kritieke waarde(n)', 'p-waarde', 'besluit'], [
              ['σ1 ≠ σ2', f(t.stat), f(t.ne.crit[0]) + ' en ' + f(t.ne.crit[1]), fp(t.ne.p), t.ne.d],
              ['σ1 > σ2', f(t.stat), f(t.gt.crit[0]), fp(t.gt.p), t.gt.d], ['σ1 < σ2', f(t.stat), f(t.lt.crit[0]), fp(t.lt.p), t.lt.d]]);
        }
        if (!num(v.alpha)) h += '<p class="xl">Vul α of de betrouwbaarheid in voor de kritieke waarden, de BI en de toets.</p>';
        return result(h, solved);
      } }
  ];

  function moments(r) { return [['E[X]', f(r.mean)], ['Var[X]', f(r.variance)], ['σ = √Var', f(Math.sqrt(r.variance))]]; }
  function inverseRow(k, q) { return num(k) ? [['kleinste k met P(X ≤ k) ≥ ' + pc(q), f(k), 'berekend']] : []; }
  // k typed: the 'kans' field shows P(X ≤ k); a kans typed: the k field shows the smallest k with P(X ≤ k) ≥ kans
  function discrete(r, v, inverse) {
    if (num(v.k)) return result(out(moments(r).concat(probs(r))), { q: r.le });
    return result(out(moments(r).concat(inverseRow(inverse, v.q))), num(inverse) ? { k: inverse } : {});
  }
  function probs(r) { return [['P(X = k)', fp(r.eq)], ['P(X ≤ k)', fp(r.le)], ['P(X ≥ k) = 1 − P(X ≤ k − 1)', fp(r.ge)], ['P(X > k)', fp(num(r.le) ? 1 - r.le : null)]]; }
  TOOLS.verdelingen = [
    { title: 'Bernoulli (één item: X = 1 met kans p)', form: inp('p', 'p = kans op 1 (bv. defect)'),
      run: function (v) { var r = Calc.bernoulli(v.p); return r ? out(moments(r)) : ''; }, pct: ['p'] },
    { title: 'Binomiaal: aantal successen in n onafhankelijke pogingen', help: 'Vul n, p en k in; of een kans voor de kleinste k.',
      form: inp('n', 'n = aantal pogingen (steekproefgrootte)') + inp('p', 'p = kans op succes per poging') + inp('k', 'k = aantal successen (bv. defecten)') + inp('q', 'of een kans: kleinste k met P(X ≤ k) ≥ kans'),
      run: function (v) {
        var r = Calc.binomial(v.n, v.p, v.k);
        return r ? discrete(r, v, Calc.binomialInv(v.n, v.p, v.q)) : '';
      }, pct: ['p', 'q'] },
    { title: 'Hypergeometrisch: defecten in een steekproef zonder teruglegging',
      help: 'Vul N, D, n en k in; of een kans voor de kleinste k.',
      form: inp('N', 'N = lotgrootte') + inp('D', 'D = defecten in het lot') + inp('n', 'n = steekproefgrootte') + inp('k', 'k = aantal defecten in de steekproef') +
            inp('q', 'of een kans: kleinste k met P(X ≤ k) ≥ kans'),
      run: function (v) {
        var r = Calc.hypergeometric(v.N, v.D, v.n, v.k);
        return r ? discrete(r, v, Calc.hypergeometricInv(v.N, v.D, v.n, v.q)) : '';
      }, pct: ['q'] },
    { title: 'Poisson: aantal gebeurtenissen in een vast interval', help: 'Vul λ en k in; of een kans voor de kleinste k.',
      form: inp('lam', 'λ (gemiddeld aantal)') + inp('k', 'k = aantal gebeurtenissen') + inp('q', 'of een kans: kleinste k met P(X ≤ k) ≥ kans'),
      run: function (v) {
        var r = Calc.poisson(v.lam, v.k);
        return r ? discrete(r, v, Calc.poissonInv(v.lam, v.q)) : '';
      }, pct: ['q'] },
    { title: 'Exponentieel: wachttijd tussen gebeurtenissen (rate λ)',
      help: 'Twee van λ, t en P(T ≤ t) geven de derde.',
      form: inp('rate', 'λ (gebeurtenissen per tijdseenheid)') + inp('t', 't = tijd') + inp('q', 'P(T ≤ t)'),
      run: function (v) {
        var e = Calc.exponentialSolve(v.rate, v.t, num(v.rate) && num(v.t) ? null : v.q);
        if (!e) { var m = Calc.exponential(v.rate, null); return m ? out(moments(m)) : ''; }
        var r = Calc.exponential(e.rate, e.t);
        return result(out(moments(r).concat([['λ', f(e.rate), num(v.rate) ? '' : 'berekend'], ['t', f(e.t), num(v.t) ? '' : 'berekend'],
                                      ['P(T ≤ t) = 1 − e^(−λt)', fp(r.le)], ['P(T > t) = e^(−λt)', fp(r.gt)]])),
                      { rate: num(v.rate) ? null : e.rate, t: num(v.t) ? null : e.t, q: num(v.q) ? null : e.le });
      }, pct: ['q'] },
    { title: 'Uniform op [a, b]', help: 'Vul a, b en x in, of a, b en een kans.',
      form: inp('a', 'a = kleinste waarde') + inp('b', 'b = grootste waarde') + inp('x', 'x = waarde') + inp('q', 'of een kans P(X ≤ x)'),
      run: function (v) {
        var x = num(v.x) ? v.x : (num(v.q) && num(v.a) && num(v.b) ? v.a + v.q * (v.b - v.a) : null);
        var r = Calc.uniform(v.a, v.b, x);
        return r ? result(out(moments(r).concat(num(x) ? [['x', f(x), num(v.x) ? '' : 'berekend'], ['P(X ≤ x)', fp(r.le)]] : [])),
                          num(v.x) ? { q: r.le } : { x: x }) : '';
      }, pct: ['q'] }
  ];

  // the events of a cross table for the 'gevraagd' and 'gegeven' lists: X = x, X ≠ x, Y = y, Y ≠ y
  function eventChoices(t, nx, ny, none) {
    var list = [['', none]];
    [['r', nx, t.rowLabels], ['c', ny, t.colLabels]].forEach(function (axis) {
      axis[2].forEach(function (label, k) {
        list.push([axis[0] + ':' + k, esc(axis[1] + ' = ' + label)], [axis[0] + '!:' + k, esc(axis[1] + ' ≠ ' + label + ' (niet ' + label + ')')]);
      });
    });
    return list;
  }
  function eventText(spec, t, nx, ny) {
    var m = /^([rc])(!?):(\d+)$/.exec(spec);
    return m ? (m[1] === 'r' ? nx : ny) + (m[2] ? ' ≠ ' : ' = ') + (m[1] === 'r' ? t.rowLabels : t.colLabels)[+m[3]] : '';
  }
  TOOLS.kruistabel = [
    { title: 'Voorwaardelijke kansen uit data: kruistabel of ruwe data, marginale verdelingen, (on)afhankelijkheid',
      help: 'Plak een kruistabel met aantallen (namen in de eerste rij en kolom mogen; een rij of kolom "Totaal" wordt weggelaten) ' +
            'of ruwe data: één waarneming per regel, de categorie van X en van Y (bv. "Lijn 1 ⇥ Accepted"). Kolommen gescheiden door een tab ' +
            '(geplakt uit een tabel): dan mogen namen spaties bevatten. Kies daarna wat gevraagd is en wat gegeven is.',
      form: sel('kind', 'soort data', [['tabel', 'kruistabel met aantallen'], ['ruw', 'ruwe data: X en Y per regel']]) +
            sel('head', 'ruwe data: eerste regel', [['0', 'is al een waarneming'], ['1', 'is een kop met de namen van X en Y']]) +
            txt('nx', 'naam van X (rijen)', 'X') + txt('ny', 'naam van Y (kolommen)', 'Y') +
            area('t', 'data', 'Lijn 1\t200\t50\t20\nLijn 2\t150\t40\t40', 5) +
            sel('ev', 'gevraagd: P( … ', [['', '— eerst data plakken —']]) + sel('gv', ' | gegeven … )', [['', 'niets gegeven']]) + ALPHA,
      run: function (v) {
        var t = Calc.crossTable(v.text.t, v.text.kind === 'ruw', v.text.head === '1');
        if (!t) return '';
        if (t.error) return warn(esc(t.error));
        var rawX = v.text.nx.trim() || (t.names ? t.names[0] : '') || 'X', rawY = v.text.ny.trim() || (t.names ? t.names[1] : '') || 'Y';
        var nx = esc(rawX), ny = esc(rawY);
        var rows = t.rowLabels.map(esc), cols = t.colLabels.map(esc), ind = Calc.independence(t.counts);
        if (!ind) return warn('het totaal is 0');
        var c = ind.table, h = '';
        var table = function (title, m, rowExtra, colExtra, corner, digits) {
          var body = m.map(function (r, i) { return ['<b>' + rows[i] + '</b>'].concat(r.map(function (x) { return f(x, digits); })).concat(rowExtra ? [f(rowExtra[i], digits)] : []); });
          if (colExtra) body.push([corner].concat(colExtra.map(function (x) { return f(x, digits); })).concat(rowExtra ? [f(rowExtra.reduce(function (a, b) { return a + b; }, 0), digits)] : []));
          return '<p class="lbl">' + title + '</p>' + grid([nx + ' \\ ' + ny].concat(cols).concat(rowExtra ? ['totaal'] : []), body);
        };
        if (t.dropped.length) h += '<p class="xl">Weggelaten (worden herberekend): ' + esc(t.dropped.join(', ')) + '.</p>';
        h += table('aantallen n (N = ' + f(c.N) + ')', t.counts, c.rowTotals, c.colTotals, 'totaal', 6);
        // the question: P(E | G)
        var q = Calc.conditional(t.counts, v.text.ev, v.text.gv);
        if (q) {
          var E = esc(eventText(v.text.ev, t, rawX, rawY)), G = esc(eventText(v.text.gv, t, rawX, rawY));
          h += '<p class="lbl">jouw vraag</p>' + out(G ? [
            ['<b>P(' + E + ' | ' + G + ')</b> = n(' + E + ' en ' + G + ') / n(' + G + ')', '<b>' + f(q.nEG) + ' / ' + f(q.nG) + ' = ' + f(q.pEgivenG, 4) + '</b>', 'Data p. 20, 25: de rijen filteren waar ' + G],
            ['P(' + E + ')', f(q.nE) + ' / ' + f(q.N) + ' = ' + f(q.pE, 4), 'marginaal'],
            ['P(' + G + ')', f(q.nG) + ' / ' + f(q.N) + ' = ' + f(q.pG, 4), 'marginaal'],
            ['P(' + E + ' en ' + G + ')', f(q.nEG) + ' / ' + f(q.N) + ' = ' + f(q.pEG, 4), 'gezamenlijk'],
            ['omgekeerd: P(' + G + ' | ' + E + ') = n(' + E + ' en ' + G + ') / n(' + E + ')', f(q.nEG) + ' / ' + f(q.nE) + ' = ' + f(q.pGgivenE, 4), 'andere noemer: niet hetzelfde'],
            ['P(' + E + ')·P(' + G + ')', f(q.product, 4), q.independent ? 'gelijk aan P(' + E + ' en ' + G + '): deze twee gebeurtenissen zijn onafhankelijk'
              : 'verschilt van P(' + E + ' en ' + G + '): deze twee gebeurtenissen zijn afhankelijk']
          ] : [['<b>P(' + E + ')</b> = n(' + E + ') / N', '<b>' + f(q.nE) + ' / ' + f(q.N) + ' = ' + f(q.pE, 4) + '</b>', 'niets gegeven: marginale kans']]);
        } else h += '<p class="xl">Kies hierboven wat gevraagd is (en wat gegeven is) voor één kans met de berekening erbij.</p>';
        h += '<p class="lbl">marginale verdelingen (Data p. 18): totaal van de rij of kolom gedeeld door N</p>' +
          grid([nx].concat(rows), [['P(' + nx + ')'].concat(c.pRow.map(function (x) { return f(x, 4); }))]) +
          grid([ny].concat(cols), [['P(' + ny + ')'].concat(c.pCol.map(function (x) { return f(x, 4); }))]);
        h += table('gezamenlijke kansen P(' + nx + ', ' + ny + ') = n / N, met de marginale kansen in de randen', c.joint, c.pRow, c.pCol, 'totaal', 4);
        h += table('P(' + ny + ' | ' + nx + '): elke rij gedeeld door haar rijtotaal; onderaan P(' + ny + ') om te vergelijken', c.colGivenRow, null, c.pCol, 'P(' + ny + ')', 4);
        h += '<p class="lbl">P(' + nx + ' | ' + ny + '): elke kolom gedeeld door haar kolomtotaal; rechts P(' + nx + ')</p>' +
          grid([nx + ' \\ ' + ny].concat(cols).concat(['P(' + nx + ')']), c.rowGivenCol.map(function (r, i) {
            return ['<b>' + rows[i] + '</b>'].concat(r.map(function (x) { return f(x, 4); })).concat([f(c.pRow[i], 4)]); }));
        h += table('P(' + nx + ')·P(' + ny + '): zo zou P(' + nx + ', ' + ny + ') zijn als ' + nx + ' en ' + ny + ' onafhankelijk waren', c.product, null, null, '', 4);
        // independence of X and Y: the table itself (as the course), then the χ²-test when the table is a sample
        var w = ind.worst;
        h += '<p class="lbl">zijn ' + nx + ' en ' + ny + ' onafhankelijk? (Data p. 22, 25: vergelijk P(' + ny + ' | ' + nx + ') met P(' + ny + '))</p>' +
          out([['in deze tabel', ind.independent ? '<b>onafhankelijk</b>' : '<b class="flag">afhankelijk</b>',
                ind.independent ? 'voor elke rij is P(' + ny + ' | ' + nx + ') gelijk aan P(' + ny + ')'
                  : 'grootste verschil: P(' + ny + ' = ' + cols[w.j] + ' | ' + nx + ' = ' + rows[w.i] + ') = ' + f(w.conditional, 4) + ' ≠ P(' + ny + ' = ' + cols[w.j] + ') = ' + f(w.marginal, 4)]]);
        var x2 = t.counts.length > 1 && t.counts[0].length > 1 ? Calc.chi2Table(t.counts, v.alpha) : null;
        if (x2 && num(x2.chi2)) {
          h += '<p class="lbl">is de tabel een steekproef? χ²-toets op onafhankelijkheid (Test Recipes p. 18–20; zie ook 05.13)</p>' +
            out([['χ² = Σ (n − e)²/e, met e = rijtotaal · kolomtotaal / N', f(x2.chi2)], ['vrijheidsgraden (r − 1)(c − 1)', f(x2.df)],
                 ['kritieke waarde χ² (kans α rechts ervan)', f(x2.crit)], ['p-waarde', fp(x2.p)],
                 ['besluit bij α', num(v.alpha) ? (x2.p < v.alpha ? 'verwerp H0: afhankelijk' : 'H0 (onafhankelijk) niet verwerpen') : '–'],
                 num(x2.yates) ? ['2×2: χ² met Yates ; p-waarde', f(x2.yates) + ' ; ' + fp(x2.pYates)] : null,
                 x2.small ? ['<b>' + x2.small + ' cel(len) met e ≤ 5</b>', 'voorwaarde e > 5 niet voldaan (TR p. 19)'] : null]);
        }
        return { html: h, solved: {}, choices: { ev: eventChoices(t, rawX, rawY, '— kies —'), gv: eventChoices(t, rawX, rawY, 'niets gegeven') } };
      }, pct: ['alpha'] }
  ];

  TOOLS.steekproefplan = [
    { title: 'Plan (n, c): OC bij AQL en LQL, producenten- en consumentenrisico',
      help: 'Binomiaal; met N ook hypergeometrisch. Doelen: α 5 %, β 10 % (AS FR p. 4).',
      form: inp('n', 'n = steekproefgrootte') + inp('c', 'c (aanvaard als defecten ≤ c)') + inp('N', 'N = lotgrootte (optioneel)') + inp('aql', 'AQL') + inp('lql', 'LQL (LTPD)') +
            inp('at', 'doel α', '', '0,05') + inp('bt', 'doel β', '', '0,10'),
      run: function (v) {
        var r = Calc.samplingRisks(v.n, v.c, v.N, v.aql, v.lql, v.at, v.bt);
        return r ? grid(['', 'binomiaal', 'hypergeometrisch'], [['OC(AQL)', fp(r.ocAqlBin), fp(r.ocAqlHyp)], ['producentenrisico α = 1 − OC(AQL)', fp(r.alphaBin), fp(r.alphaHyp)],
                    ['consumentenrisico β = OC(LQL)', fp(r.betaBin), fp(r.betaHyp)], ['haalt beide doelen?', f(r.meetsBin), f(r.meetsHyp)]]) : '';
      }, pct: ['aql', 'lql', 'at', 'bt'] },
    { title: 'Eén lotkwaliteit p: OC, AOQ, ATI', help: 'Met N ook de exacte AOQ en de ATI.',
      form: inp('n', 'n = steekproefgrootte') + inp('c', 'c = aanvaardingsgetal') + inp('N', 'N (voor exact AOQ en ATI)') + inp('p', 'p = fractie defect in het lot'),
      run: function (v) {
        var r = Calc.samplingPoint(v.n, v.c, v.N, v.p);
        return r ? out([['OC(p) binomiaal', fp(r.ocBin)], ['OC(p) hypergeometrisch', fp(r.ocHyp)], ['AOQ exact', fp(r.aoq)],
                        ['AOQ ≈ p·OC(p)', fp(r.aoqApprox)], ['ATI', f(r.ati)]]) : '';
      }, pct: ['p'] },
    { title: 'AOQL = hoogste AOQ', help: 'Met N: alle lotfracties M/N; zonder N: binomiaal, p in stappen van 0,0001.',
      form: inp('n', 'n = steekproefgrootte') + inp('c', 'c = aanvaardingsgetal') + inp('N', 'N (optioneel)'),
      run: function (v) {
        var r = Calc.aoql(v.n, v.c, v.N);
        return r ? out([['AOQL ≈ max p·OC(p)', fp(r.approx), 'bij p = ' + pc(r.pApprox)], ['AOQL exact (formule p. 10)', fp(r.exact), num(r.pExact) ? 'bij p = ' + pc(r.pExact) : '']]) : '';
      } },
    { title: 'OC-tabel', form: inp('n', 'n = steekproefgrootte') + inp('c', 'c = aanvaardingsgetal') + inp('N', 'N (optioneel)') + inp('step', 'stap in p', '', '0,01') + inp('to', 'tot p', '', '0,1'),
      run: function (v) {
        if (!num(v.n) || !num(v.c) || !num(v.step) || !num(v.to) || v.step <= 0) return '';
        var rows = [];
        for (var i = 0; i * v.step <= v.to + 1e-12 && rows.length < 201; i++) {
          var p = i * v.step, r = Calc.samplingPoint(v.n, v.c, v.N, p);
          rows.push([pc(p), pc(r.ocBin), pc(r.ocHyp), pc(r.aoq), pc(r.aoqApprox), f(r.ati)]);
        }
        return grid(['p', 'OC binomiaal', 'OC hypergeom.', 'AOQ exact', 'AOQ ≈ p·OC', 'ATI'], rows);
      }, pct: ['step', 'to'] },
    { title: 'Plan voor variabelen (k, n) uit AQL, LQL, α en β', help: 'Vul AQL, LQL, α en β in.',
      form: inp('p0', 'AQL = p0') + inp('pt', 'LQL = pt') + inp('a', 'α', '', '0,05') + inp('b', 'β', '', '0,10'),
      run: function (v) {
        var r = Calc.variablesPlan(v.p0, v.pt, v.a, v.b);
        return r ? out([['k = (z_pt z_α + z_p0 z_β)/(z_(1−α) + z_(1−β))', f(r.k)], ['n = (z_(1−α) + z_(1−β))² (1 + k²/2)/(z_pt − z_p0)²', f(r.n)],
                        ['n naar boven afgerond', f(r.nUp)], ['OC(AQL) van dit plan', fp(r.ocAql)], ['OC(LQL) van dit plan', fp(r.ocLql)]]) : '';
      }, pct: ['p0', 'pt', 'a', 'b'] }
  ];

  TOOLS.regressie = [
    { title: 'Enkelvoudige lineaire regressie: schatting, ANOVA, toetsen, BI en PI',
      help: 'Eén paar "x y" per regel (plak twee kolommen).',
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
    { title: 'Eénweg-ANOVA (one-way)', help: 'Eén groep per regel (de waarnemingen van één niveau).',
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
    { title: 'Alles uit alles: LSL, USL, µ, σ, Cp, Cpk en ppm buiten specificatie',
      help: 'Vul in wat gegeven is. Een uitval in ppm geeft Cpk (één grens) of Cp = Cpk (kies \'gecentreerd\').',
      form: inp('lsl', 'LSL') + inp('usl', 'USL') + inp('mean', 'µ (gemiddelde)') + inp('sigma', 'σ') + inp('cp', 'Cp') + inp('cpk', 'Cpk') +
            inp('ppm', 'uitval in ppm (totaal buiten specificatie)') +
            sel('centred', 'ligging van het proces', [['0', 'zoals ingevuld'], ['1', 'gecentreerd: µ in het midden van LSL en USL']]),
      run: function (v) {
        var r = Calc.capabilitySolve({ lsl: v.lsl, usl: v.usl, mean: v.mean, sigma: v.sigma, cp: v.cp, cpk: v.cpk, ppm: v.ppm, centred: v.text.centred === '1' });
        if (r.error) return warn(r.error);
        var mark = marker(r);
        if (![r.mean, r.sigma, r.cp, r.cpk, r.ppm].some(num)) return r.notes.length ? warn(r.notes.join('; ')) : '';
        return result(out([['µ', num(r.mean) ? f(r.mean) : (r.meanOptions ? f(r.meanOptions[0]) + ' of ' + f(r.meanOptions[1]) : '–'), mark('mean')],
                    ['σ', f(r.sigma), mark('sigma')], ['Cp', f(r.cp), mark('cp')], ['niveau (SPC p. 40)', f(r.level)],
                    ['Cpu ; Cpl', f(r.cpu) + ' ; ' + f(r.cpl)], ['Cpk', f(r.cpk), mark('cpk')], ['Cpk ≥ 1,33 ("Good", SPC p. 41)?', f(r.capable)],
                    ['Z tot LSL ; Z tot USL', f(r.zLsl) + ' ; ' + f(r.zUsl)], ['onder LSL ; boven USL', pc(r.below) + ' ; ' + pc(r.above)],
                    ['uitval in ppm', f(r.ppm), mark('ppm')], ['uitval', pc(r.out)]]) +
          (r.notes.length ? warn(r.notes.join('; ')) : ''), derived(r));
      } }
  ];

  TOOLS.regelkaart = [
    { title: 'Grenzen uit X̿, R̄ en/of s̄ (X̄-R en X̄-s)',
      help: 'n alleen geeft de constanten; met R̄ en/of s̄ ook de R- of s-kaart, σ̂ en de halve breedte van de X̄-kaart; met X̿ de X̄-grenzen.',
      form: inp('n', 'n (subgroepgrootte)') + inp('xbb', 'X̿') + inp('rbar', 'R̄') + inp('sbar', 's̄'),
      run: function (v) {
        if (!num(v.n)) return '';
        var r = Calc.limitsSummary(v.n, v.xbb, v.rbar, v.sbar, K);
        if (!num(r.A2)) return warn('n = ' + f(v.n) + ' staat niet in de tabel');
        var half = [];
        if (!num(v.xbb) && num(v.rbar)) half.push(['X̄-kaart met R̄: X̿ ± A2·R̄', 'X̿ ± ' + f(r.A2 * v.rbar)]);
        if (!num(v.xbb) && num(v.sbar)) half.push(['X̄-kaart met s̄: X̿ ± A3·s̄', 'X̿ ± ' + f(r.A3 * v.sbar)]);
        return out([['constanten bij n = ' + f(v.n), ['A2', 'D3', 'D4', 'd2', 'A3', 'B3', 'B4', 'c4'].map(function (c) { return c + ' = ' + f(r[c]); }).join(' · ')]]
                   .concat(half)) + limitsTable(r);
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
  TOOLS.regelkaart.push(
    { title: 'Omgekeerd: uit gegeven grenzen naar X̿, R̄, s̄ en σ̂',
      help: 'Vul n en de grenzen in die je kent; zonder CL ligt de centrale lijn in het midden van UCL en LCL.',
      form: inp('n', 'n (subgroepgrootte)') + inp('ucl', 'UCL van de X̄-kaart') + inp('cl', 'CL (X̿)') + inp('lcl', 'LCL van de X̄-kaart') +
            inp('uclR', 'UCL van de R-kaart') + inp('uclS', 'UCL van de s-kaart'),
      run: function (v) {
        var r = Calc.limitsInverse(v.n, { ucl: v.ucl, cl: v.cl, lcl: v.lcl, uclR: v.uclR, uclS: v.uclS }, K);
        if (!r) return '';
        if (!num(r.c.A2)) return warn('n = ' + f(v.n) + ' staat niet in de tabel');
        var limits = num(r.half) ? { cl: num(v.cl) ? null : r.xbb, ucl: num(v.ucl) ? null : r.xbb + r.half, lcl: num(v.lcl) ? null : r.xbb - r.half } : {};
        return result(out([['X̿', f(r.xbb)], ['UCL − X̿ = 3σ̂/√n', f(r.half)], ['σ<sub>x̄</sub> = σ̂/√n', f(r.sigmaXbar)], ['σ̂ = (UCL − X̿)·√n/3', f(r.sigma)],
                    ['R̄ uit de X̄-kaart = (UCL − X̿)/A2', f(r.rbarFromX), 'A2 = ' + f(r.c.A2)], ['R̄ uit de R-kaart = UCL<sub>R</sub>/D4', f(r.rbarFromR), 'D4 = ' + f(r.c.D4)],
                    ['s̄ uit de X̄-kaart = (UCL − X̿)/A3', f(r.sbarFromX), 'A3 = ' + f(r.c.A3)], ['s̄ uit de s-kaart = UCL<sub>s</sub>/B4', f(r.sbarFromS), 'B4 = ' + f(r.c.B4)],
                    ['σ̂ = R̄/d2', f(r.sigmaR), 'd2 = ' + f(r.c.d2)], ['σ̂ = s̄/c4', f(r.sigmaS), 'c4 = ' + f(r.c.c4)]]) +
          (r.notes.length ? warn(r.notes.join('; ')) : ''), limits);
      } });
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
      help: 'Eén regel per operator en herhaling (A herhaling 1, A herhaling 2, …, B herhaling 1, …), met de n delen naast elkaar.',
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
      help: 'Vul per model de vier aantallen in, rij per rij (rijen = werkelijke klasse).',
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
    { title: 'Steekproefgrootte, breedte en betrouwbaarheid van een BI (twee van de drie)',
      help: 'Vul twee van α, W en n in; de derde wordt berekend. W is de VOLLEDIGE breedte (CI p. 7). Voor σ onbekend geeft de cursus geen formule.',
      form: inp('alpha', 'α (1 − betrouwbaarheid)', 'bv. 0,05') + inp('W', 'volledige breedte W') + inp('n', 'n') +
            inp('p', 'geschatte proportie p (leeg = 0,5)') + inp('sigma', 'σ (voor een gemiddelde)'),
      run: function (v) {
        var r = Calc.sampleSizeSolve(v.alpha, v.W, v.n, v.p, v.sigma);
        if (!r) return '';
        var q = num(v.sigma) && r.mean ? r.mean : r.prop, solved = !q ? {} :
          !num(v.n) ? { n: q.nUp } : (!num(v.W) ? { W: q.width } : (!num(v.alpha) ? { alpha: q.alpha } : {}));
        var rows = function (q, name, fmt) {
          return q ? [name, ['z', f(q.z)], ['n', f(q.n), num(q.nUp) ? 'naar boven afgerond: ' + f(q.nUp) : ''], ['volledige breedte W', fmt(q.width)],
                      ['betrouwbaarheid 1 − α', fp(q.confidence)]] : [];
        };
        return result(out(rows(r.prop, 'proportie (p = ' + f(r.p) + '): W = 2·z·√(p(1 − p)/n)', pc)
                   .concat(r.prop ? [['verwacht aantal defecten n·p (CI p. 10: minstens 5)', f(r.prop.defectives)]] : [])
                   .concat(rows(r.mean, 'gemiddelde, σ gekend: W = 2·z·σ/√n', f))) +
          '<p class="xl">Valkuil: een halve breedte van 5 % (± 5 %) is een volledige breedte van 10 %. Relatieve nauwkeurigheid eerst omzetten: 10 % van 10 % is W = 2 % (CI p. 7).</p>', solved);
      }, pct: ['W', 'p', 'alpha'] }
  ];
  TOOLS.tolerantie = [
    { title: 'Tolerantie-interval, σ gekend (CI FR p. 22)',
      help: 'β is hier de staartfractie van de verdeling, niet het type-II-risico. Werk op de getransformeerde variabele (bv. Y = ln X) als de opgave dat doet.',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n') + inp('m', 'Ȳ') + inp('s', 'σ'),
      run: function (v) {
        var r = Calc.tolerance(v.n, v.m, v.s, v.alpha, v.beta, true);
        return r ? out([['k (eenzijdig)', f(r.k1)], ['LTL = Ȳ − kσ', num(r.ltl) ? f(r.ltl) : 'Ȳ − ' + f(r.k1) + '·σ'],
                        ['UTL = Ȳ + kσ', num(r.utl) ? f(r.utl) : 'Ȳ + ' + f(r.k1) + '·σ', 'CI FR p. 22 drukt 5,55: een drukfout (Ȳ + kσ geeft dit)'],
                        ['k* (tweezijdig)', f(r.k2)], ['tweezijdig interval', r.two ? iv(r.two) : 'Ȳ ± ' + f(r.k2) + '·σ']]) +
          '<p class="xl">Ligt de eis (bv. ln 240) binnen [LTL; +∞[, dan is ze niet aangetoond (CI FR p. 22).</p>' : '';
      }, pct: ['beta'] },
    { title: 'Tolerantie-interval, σ onbekend (CI FR p. 23)',
      help: 'β is de staartfractie van de verdeling.',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n') + inp('m', 'Ȳ') + inp('s', 's'),
      run: function (v) {
        var r = Calc.tolerance(v.n, v.m, v.s, v.alpha, v.beta, false);
        return r ? out([['k = t(α, β, n) (eenzijdig)', f(r.k1)], ['LTL = Ȳ − ks', num(r.ltl) ? f(r.ltl) : 'Ȳ − ' + f(r.k1) + '·s'],
                        ['UTL = Ȳ + ks', num(r.utl) ? f(r.utl) : 'Ȳ + ' + f(r.k1) + '·s'],
                        ["k′ = t(α/2, β/2, n) (tweezijdig)", f(r.k2)], ['tweezijdig interval', r.two ? iv(r.two) : 'Ȳ ± ' + f(r.k2) + '·s']]) : '';
      }, pct: ['beta'] },
    { title: 'Verdelingsvrij tolerantie-interval [x<sub>(1)</sub>; x<sub>(n)</sub>] (CI FR p. 23)',
      help: 'Zonder n: de kleinste n; met n: de betrouwbaarheid.',
      form: ALPHA + inp('beta', 'β (staartfractie)', '', '0,10') + inp('n', 'n (optioneel)'),
      run: function (v) {
        var r = Calc.toleranceFree(v.alpha, v.beta, v.n);
        return r ? result(out([['kleinste n', f(r.nMin)], ['betrouwbaarheid bij de gegeven n', fp(r.confidence)]]), num(v.n) ? {} : { n: r.nMin }) : '';
      }, pct: ['beta'] }
  ];
  TOOLS.onderscheidingsvermogen = [
    { title: 'β en onderscheidingsvermogen (power) van de Z-toets voor µ',
      help: 'Met µ1: β en power per H_A; met een gewenste β ook n, of zonder µ1 de kleinste verschuiving die de toets ziet. Tweezijdig toont de cursus alleen als grafiek (TH FR p. 14); voor de t-toets geeft de cursus geen β.',
      form: ALPHA + inp('mu0', 'µ0 (H0)') + inp('mu1', 'ware µ1') + inp('sigma', 'σ') + inp('n', 'n') + inp('tb', 'gewenste β (voor n of de kleinste µ1)'),
      run: function (v) {
        var r = Calc.powerMean(v.mu0, v.mu1, v.sigma, v.n, v.alpha, v.tb), shift = Calc.detectableShift(v.sigma, v.n, v.alpha, v.tb);
        var detect = num(shift) ? out([['kleinste verschuiving die de eenzijdige toets met die β ziet: (z<sub>1−α</sub> + z<sub>1−β</sub>)σ/√n', f(shift)],
                                       num(v.mu0) ? ['µ1 voor H<sub>A</sub>: µ > µ0 ; voor H<sub>A</sub>: µ < µ0', f(v.mu0 + shift) + ' ; ' + f(v.mu0 - shift)] : null]) : '';
        if (!r) return detect;
        var crit = { gt: f(r.gt.crit[0]), lt: f(r.lt.crit[0]), ne: f(r.ne.crit[0]) + ' en ' + f(r.ne.crit[1]) };
        var power = num(v.mu1)
          ? grid(['H<sub>A</sub>', 'kritieke waarde(n) x̄', 'β (H0 ten onrechte aanvaarden)', 'power = 1 − β'], [
              ['µ > µ0', crit.gt, fp(r.gt.beta), fp(r.gt.power)], ['µ < µ0', crit.lt, fp(r.lt.beta), fp(r.lt.power)],
              ['µ ≠ µ0', crit.ne, fp(r.ne.beta), fp(r.ne.power)]])
          : grid(['H<sub>A</sub>', 'H0 verwerpen als x̄ voorbij'], [['µ > µ0', crit.gt], ['µ < µ0', crit.lt], ['µ ≠ µ0', crit.ne]]) +
            '<p class="xl">Vul de ware µ1 in voor β en de power.</p>';
        return out([alphaRow(v.alpha), ['σ/√n', f(r.se)]]) + detect + power +
          (num(r.nOneSided) ? out([['n voor die β, eenzijdig: ((z<sub>1−α</sub> + z<sub>1−β</sub>)σ/|µ1 − µ0|)²', f(r.nOneSided)], ['naar boven afgerond', f(r.nOneSidedUp), 'TH FR p. 9: n = 195']]) : '');
      }, pct: ['tb'] },
    { title: 'β van de Z-toets voor een proportie π',
      help: 'Met een gewenste β ook n (formule en kleinste n met β kleiner dan het doel).',
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
      help: 'Geef kansen of verwachte aantallen. De vrijheidsgraden houden rekening met g geschatte parameters.',
      form: ALPHA + area('o', 'waargenomen aantallen n<sub>k</sub> per klasse', '', 2) + area('e', 'verwachte kansen π<sub>k</sub> (of verwachte aantallen)', '', 2) + inp('g', 'g = aantal geschatte parameters', '', '0'),
      run: function (v) {
        var o = parseList(v.text.o), e = parseList(v.text.e);
        if (!o.length || !e.length) return '';
        if (o.length !== e.length) return warn('evenveel waargenomen als verwachte waarden nodig');
        var r = Calc.chi2Fit(o, e, v.g, v.alpha);
        return grid(['klasse', 'n<sub>k</sub>', 'e<sub>k</sub>'], o.map(function (x, i) { return [String(i + 1), f(x), f(r.e[i])]; })) +
          out([['χ²', f(r.chi2)], ['vrijheidsgraden r − g − 1', f(r.df)], ['kritieke waarde χ² (kans α rechts ervan)', f(r.crit)],
               ['p-waarde P(χ² ≥ waarde)', fp(r.p)], ['besluit', num(r.p) ? (r.p < v.alpha ? 'verwerp H0' : 'H0 niet verwerpen') : '–'],
               r.small ? ['<b>' + r.small + ' klasse(n) met e ≤ 5</b>', 'klassen samenvoegen (TR p. 17)'] : null]);
      } },
    { title: 'χ²-toets op onafhankelijkheid (kruistabel)',
      help: 'Eén rij per regel; bij een 2×2-tabel ook Yates.',
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
      help: 'Zonder correctie voor gelijke waarden, zoals de cursus.',
      form: area('a', 'steekproef 1', '', 2) + area('b', 'steekproef 2', '', 2),
      run: function (v) {
        var r = Calc.rankSum(parseList(v.text.a), parseList(v.text.b));
        return r ? out([['rangen van steekproef 1', r.ranks1.map(function (x) { return f(x); }).join(' ')]]) + rankOut(r, 'W = rangsom steekproef 1') : '';
      } },
    { title: 'Wilcoxon signed ranks (gepaarde waarnemingen)',
      help: 'Paren of verschillen; nulverschillen worden weggelaten.',
      form: area('pairs', 'paren x1 x2 per regel, of de verschillen', '', 3),
      run: function (v) {
        var rows = parseRows(v.text.pairs), d = rows.length && rows.every(function (q) { return q.length === 2; })
          ? rows.map(function (q) { return q[0] - q[1]; }) : [].concat.apply([], rows);
        var r = Calc.signedRank(d);
        return r ? out([['n na weglaten van ' + r.dropped + ' nulverschil(len)', f(r.n)]]) + rankOut(r, 'T+ = som van de positieve rangen') : '';
      } },
    { title: 'Runs-toets op aselectheid (Wald-Wolfowitz)',
      help: 'Waarden gelijk aan de mediaan worden weggelaten (de cursus zegt er niets over).',
      form: area('x', 'waarden in de volgorde van de steekproef', '', 3),
      run: function (v) {
        var r = Calc.runsTest(parseList(v.text.x));
        return r ? out([['mediaan', f(r.median)], ['tekens (+ boven, − onder)', r.signs], ['n (zonder waarden gelijk aan de mediaan)', f(r.n)]]) + rankOut(r, 'R = aantal runs') : '';
      } }
  ];
  TOOLS.steekproefmethoden = [
    { title: 'Proportie: SRS tegenover gestratificeerd (twee strata, AS p. 16–18)',
      help: 'Laat π<sub>B</sub> leeg voor alleen SRS.',
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
      form: inp('a', 'µ<sub>A</sub>') + inp('b', 'µ<sub>B</sub>') + inp('s2', 'σ<sub>S</sub>² (binnen een stratum)') + inp('n', 'n'),
      run: function (v) {
        var r = Calc.samplingMeans(v.a, v.b, v.s2, v.n);
        return r ? out([['µ', f(r.mu)], ['σ² van de hele populatie', f(r.sigma2)], ['σ²[X̄] (SRS)', f(r.srs)], ['σ²[X̄<sub>S</sub>] (gestratificeerd)', f(r.strat)]]) : '';
      } }
  ];
  TOOLS.steekproefplan.push(
    { title: 'Bij welke p haalt een plan (n, c) een gegeven OC? (AQL, LQL van een plan)',
      help: 'Geef 1 − α (bv. 0,95) voor de AQL of β (bv. 0,10) voor de LQL van het plan.',
      form: inp('n', 'n = steekproefgrootte') + inp('c', 'c = aanvaardingsgetal') + inp('t', 'gewenste OC (bv. 0,95 of 0,10)'),
      run: function (v) { var p = Calc.inverseOC(v.n, v.c, v.t); return num(p) ? out([['p met OC(p) = ' + pc(v.t), fp(p)]]) : ''; }, pct: ['t'] });
  TOOLS.planontwerp = [
    { title: 'Plan (n, c) zoeken voor (AQL; 1 − α) en (LQL; β)',
      help: 'De cursus ontwerpt met de tabel van Peach (R<sub>0</sub> = LQL/AQL, AS FR p. 4), maar die tabel zit niet in de cursusbestanden. Deze zoektocht (zoals de gids): de kleinste c waarvoor de kleinste n met OC(LQL) ≤ β ook OC(AQL) ≥ 1 − α haalt, binomiaal. Peach geeft bv. (164, 2) voor (0,5 %; 95 %), (3,5 %; 5 %), met β = 7,1 %, dus niet β ≤ 5 %.',
      form: inp('aql', 'AQL') + inp('lql', 'LQL') + inp('a', 'α', '', '0,05') + inp('b', 'β', '', '0,10'),
      run: function (v) {
        var r = Calc.planSearch(v.aql, v.lql, v.a, v.b);
        return r ? out([['plan (n, c)', '(' + r.n + ', ' + r.c + ')'], ['n mag tot', f(r.nMax), 'met dezelfde c'], ['OC(AQL)', fp(r.ocAql)],
                        ['OC(LQL)', fp(r.ocLql)], ['R<sub>0</sub> = LQL/AQL (voor de tabel van Peach)', f(r.r0)]]) : '';
      }, pct: ['aql', 'lql', 'a', 'b'] }
  ];
  TOOLS.dubbelplan = [
    { title: 'Dubbel plan (n1, c1, c2) + (n2, c3): OC, Π en ASN',
      help: 'Binomiaal; met N hypergeometrisch.',
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
      help: 'Met n en het aantal defecten tot nu toe ook de beslissing.',
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
      help: 'Geef ξ direct, of µ en σ: ξ = µ + z<sub>p0</sub>·σ, de waarde met kans p0 links ervan in N(µ, σ), zoals het werkboek.',
      form: inp('p0', 'p0 (AQL)') + ALPHA + inp('n', 'n') + inp('xi', 'ξ (ondergrens)') + inp('mu', 'of µ (voor ξ = µ + z<sub>p0</sub>·σ)') + inp('sg', 'σ (idem)') +
            inp('m', 'X̄ van de steekproef') + inp('s', 's van de steekproef') + inp('k', 'k (leeg = t)'),
      run: function (v) {
        var xi = num(v.xi) ? v.xi : (num(v.mu) && num(v.sg) && num(v.p0) ? v.mu + v.sg * Stats.normInv(v.p0) : null);
        var r = Calc.variablesGivenN(v.p0, v.alpha, v.n, xi, v.m, v.s, v.k);
        return r ? result(out([['Z<sub>1−p0</sub> ; Z<sub>α</sub>', f(r.zP) + ' ; ' + f(r.zA)], ['t(1 − α, p0, n)', f(r.t)], ['ξ', f(r.xi)], ['k gebruikt', f(r.k)],
                        ['Q = (X̄ − ξ)/s', f(r.Q)], ['beslissing (Q ≥ k)', f(r.accept)], ['OC(p0) met deze k', fp(r.ocP0)]]),
                          { xi: num(v.xi) ? null : r.xi, k: num(v.k) ? null : r.k }) : '';
      }, pct: ['p0'] }
  ];
  TOOLS.skiplot = [
    { title: 'Kwalificatie voor skip-lot (AS FR p. 11, notities)',
      help: 'Voorbeeld van de cursus: plan (80, 2), de laatste 10 loten aanvaard (cursus: 2,4 % bij 1 %, 85 % bij 0,1 %).',
      form: inp('p', 'p') + inp('n', 'n per steekproef', '', '80') + inp('lots', 'aantal eerste steekproeven', '', '8') + inp('d', 'hoogstens d defecten samen', '', '3') + inp('last', 'laatste steekproeven zonder defect', '', '2'),
      run: function (v) {
        var r = Calc.skipLot(v.p, v.n, v.lots, v.d, v.last);
        return r ? out([['B(d; aantal·n, p)', fp(r.first)], ['B(0; n, p)', fp(r.lastOne)], ['P<sub>q</sub>', fp(r.pq), 'cursus: 2,4 % bij 1 %, 85 % bij 0,1 %']]) : '';
      }, pct: ['p'] },
    { title: 'Criterium van Deming: geen of volledige inspectie (AS FR p. 13–15)',
      form: inp('p', 'p') + inp('k1', 'k1 (inspectiekost per stuk)') + inp('k2', 'k2 (kost van een defect stuk verder in het proces)'),
      run: function (v) {
        var r = Calc.deming(v.p, v.k1, v.k2);
        return r ? out([['break-even k1/k2', fp(r.breakEven)], ['beslissing', r.decision]]) +
          '<p class="xl">Uit de kostformule van AS FR p. 14 volgt het exacte omslagpunt p(1 − p) = k1/k2; de regel p = k1/k2 van p. 15 is de benadering voor kleine p.</p>' : '';
      }, pct: ['p'] }
  ];

  /* ---------- Deel 14 (extra, niet te kennen): blocks that only the books Six Sigma For Dummies and Harry & Schroeder give ---------- */
  TOOLS.sigma_extra = [
    { title: 'DPU, throughput yield en RTY ≈ e^(−DPU)', form: inp('D', 'D = aantal defecten') + inp('N', 'N = aantal eenheden'),
      run: function (v) {
        var r = Calc.defects(v.D, v.N, null);
        return r ? out([['DPU = D / N', f(r.dpu)], ['throughput yield = 1 − DPU', fp(r.ty)], ['RTY ≈ e^(−DPU)', fp(r.rtyApprox), 'Dummies p. 156: als DPU klein is']]) : '';
      } },
    { title: 'Traditionele yield, first-time yield, verborgen fabriek', form: inp('in', 'eenheden in') + inp('out', 'eenheden uit (goed, na herwerk)') + inp('scrap', 'afgekeurd (scrap)') + inp('rework', 'herwerkt'),
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
    { title: 'Yield per kans uit de eindyield', form: inp('y', 'eindyield') + inp('o', 'aantal kansen'),
      run: function (v) {
        var r = Calc.perOpportunity(v.y, v.o);
        return r ? out([['yield per kans = yield^(1/kansen)', fp(r.ypo)], ['DPMO', f(r.dpmo)], ['Z zonder verschuiving', f(r.z)],
                        ['sigmaniveau met 1,5σ-verschuiving', f(r.level)]]) : '';
      }, pct: ['y'] }
  ];
  TOOLS.regelkaart_extra = [
    { title: 'Individuele waarden en moving range (I-MR)', help: 'Waarden in volgorde.',
      form: area('x', 'waarden in volgorde', '', 4),
      run: function (v) {
        var r = Calc.individuals(parseList(v.text.x), K);
        if (!r) return '';
        return out([['k', f(r.k)], ['X̄', f(r.xbar)], ['MR̄', f(r.mrbar)], ['σ̂ = MR̄/d2(2)', f(r.sigma), 'd2 = ' + f(r.d2)]]) +
          grid(['kaart', 'LCL', 'CL', 'UCL', 'constanten'], [['X', f(r.X[0]), f(r.X[1]), f(r.X[2]), 'E2 = ' + f(r.E2)],
            ['MR', f(r.MR[0]), f(r.MR[1]), f(r.MR[2]), 'D3 = ' + f(r.D3) + ', D4 = ' + f(r.D4)]]) +
          grid(['#', 'x', 'MR', 'x-signaal', 'MR-signaal'], r.points.map(function (p, i) { return [String(i + 1), f(p.x), f(p.mr), flagged(p.fx), flagged(p.fmr)]; }));
      } },
    { title: 'p-kaart (fractie defect) of u-kaart (defecten per eenheid)', help: 'Per regel: subgroepgrootte n_i en aantal.',
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
      help: 'Gemiddelde, mediaan, modus, s (n − 1 in de noemer) en σ (n in de noemer).',
      form: area('x', 'waarden', '', 3),
      run: function (v) {
        var xs = parseList(v.text.x), r = Calc.descriptives(xs);
        return r ? out([['n', f(r.n)], ['som', f(r.sum)], ['gemiddelde x̄', f(r.mean)], ['mediaan', f(r.median)], ['modus', modes(xs)],
                        ['minimum ; maximum', f(r.min) + ' ; ' + f(r.max)], ['bereik R = max − min', f(r.range)],
                        ['s (n − 1, steekproef)', f(r.sd)], ['s² (n − 1)', f(r.variance)], ['s/√n (standaardfout)', f(r.se)],
                        ['σ met deler n ; σ²', f(r.sdPop) + ' ; ' + f(r.variancePop)]]) : '';
      } },
    { title: 'Correlatie en covariantie van paren (x, y)',
      help: 'De cursus noemt de deler van de covariantie niet: beide staan hier (COVARIANCE.S met n − 1, COVAR met n).',
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
      help: 'Met Σy² ook de kwadratensommen.',
      form: inp('n', 'n') + inp('sx', 'Σx') + inp('sy', 'Σy') + inp('sxx', 'Σx²') + inp('sxy', 'Σxy') + inp('syy', 'Σy² (optioneel)'),
      run: function (v) {
        var r = Calc.regSums(v.n, v.sx, v.sy, v.sxx, v.sxy, v.syy);
        return r ? out([['x̄ ; ȳ', f(r.xbar) + ' ; ' + f(r.ybar)], ['S<sub>xx</sub> ; S<sub>xy</sub>', f(r.Sxx) + ' ; ' + f(r.Sxy)], ['b1', f(r.b1)], ['b0', f(r.b0)],
                        num(r.sst) ? ['SS<sub>T</sub> ; SS<sub>R</sub> = b1·S<sub>xy</sub> ; SS<sub>E</sub>', f(r.sst) + ' ; ' + f(r.ssr) + ' ; ' + f(r.sse)] : null,
                        num(r.r2) ? ['R² ; MS<sub>E</sub> ; σ̂', f(r.r2) + ' ; ' + f(r.mse) + ' ; ' + f(r.s)] : null]) : '';
      } },
    { title: 'R², σ̂ en F uit de kwadratensommen (REG p. 27–33, 56)',
      help: 'k = aantal regressoren (1 bij enkelvoudige regressie).',
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
        var h = out([['t-kritiek t<sub>1−α/2; n−2</sub>', f(r.tcrit)], ['F0 = t0² (enkelvoudig)', f(r.F)]]) +
          grid(['', 's.e.', 't0', 'p (≠)', 'BI tweezijdig'], rows.map(function (q) { return [q[0], f(q[2]), f(q[3].stat), fp(q[3].ne.p), iv(q[1].two)]; }));
        if (num(r.y0)) h += out([['ŷ0', f(r.y0)], ['s.e. gemiddelde respons ; BI', f(r.seMean) + ' ; ' + iv(r.ciMean.two)],
                                 ['s.e. nieuwe waarneming ; PI', f(r.sePred) + ' ; ' + iv(r.pi.two)]]);
        return h;
      } },
    { title: 'Partiële F-toets: helpen de extra termen? (REG p. 61)',
      form: ALPHA + inp('rm', 'SS<sub>E</sub>(RM)') + inp('fm', 'SS<sub>E</sub>(FM)') + inp('r', 'k − r (toegevoegde termen)') + inp('df', 'n − p (fout-df volledig model)'),
      run: function (v) {
        var r = Calc.partialF(v.rm, v.fm, v.r, v.df, v.alpha);
        return r ? out([['F0', f(r.F)], ['F-kritiek (kans α rechts ervan; k − r en n − p vrijheidsgraden)', f(r.Fcrit)], ['p-waarde', fp(r.p)], ['besluit', r.d]]) : '';
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
      help: 'Eén regel per waarneming: y gevolgd door x1, x2, … (plak de kolommen, y eerst). Uitvoer zoals de cursus (REG p. 52). Tweede orde = kwadraten en kruisproducten; centreren op het gemiddelde zoals het acetyleenvoorbeeld (REG p. 60) verandert de coëfficiënten van de lagere termen, niet R², S of F. BI en PI bij x0 volgen de standaard kleinste-kwadratenformule; de cursus geeft ze alleen voor enkelvoudige regressie.',
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
        return '<p class="lbl">Regressiestatistieken</p>' + out([['meervoudige R', f(Math.sqrt(r.r2))], ['R²', f(r.r2)], ['R²<sub>adj</sub> (n − k − 1)', f(r.r2adj)],
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
    { title: 'Tweewegs-ANOVA, met of zonder herhalingen',
      help: 'Kolommen = niveaus van factor B; per niveau van factor A r regels onder elkaar. r = 1: zonder herhalingen, de interactie is dan de fout. Met herhalingen zoals de uitvoer in het GRR-werkboek van de cursus (blad 2way anova).',
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
      help: 'SPC p. 68 zegt bij regels 2 en 3 niet of de punten aan dezelfde kant moeten liggen (bij regel 4 wel); de rekenmachine toont beide lezingen. Regels 9 en 10 (ongewoon patroon, punt dicht bij een grens) vragen een oordeel.',
      form: inp('cl', 'centrale lijn CL') + inp('s', 'σ van de uitgezette grootheid') + inp('ucl', 'of UCL (dan σ = (UCL − CL)/3)') + area('x', 'punten in volgorde', '', 3),
      run: function (v) {
        var s = num(v.s) ? v.s : (num(v.ucl) && num(v.cl) ? (v.ucl - v.cl) / 3 : null), r = Calc.runRules(parseList(v.text.x), v.cl, s);
        var solved = num(v.cl) && num(s) ? (num(v.s) ? { ucl: v.cl + 3 * s } : { s: s }) : {};
        if (!r) return result('', solved);
        var names = ['', '1. één of meer punten buiten de controlegrenzen', '2. 2 van 3 opeenvolgende punten voorbij 2σ (zelfde kant)',
          '3. 4 van 5 opeenvolgende punten voorbij 1σ (zelfde kant)', '4. 8 opeenvolgende punten aan één kant van de centrale lijn',
          '5. 6 punten op rij stijgend of dalend', '6. 15 punten op rij in zone C', '7. 14 punten op rij afwisselend op en neer',
          '8. 8 punten op rij aan beide kanten zonder één in zone C'];
        names['2b'] = '2. letterlijk: 2 van 3 voorbij 2σ (eender welke kant)'; names['3b'] = '3. letterlijk: 4 van 5 voorbij 1σ (eender welke kant)';
        return result(grid(['regel', 'signaal bij punt (laatste punt van het venster)'], [1, 2, '2b', 3, '3b', 4, 5, 6, 7, 8].map(function (q) {
            return [names[q], r.hits[q].length ? '<b class="flag">' + r.hits[q].join(', ') + '</b>' : 'geen']; })) +
          grid(['#', 'z = (x − CL)/σ', 'zone'], r.z.map(function (z, i) { return [String(i + 1), f(z, 3), r.zones[i]]; })), solved);
      } });

  /* ---------- Bayes, Beta, k-class confusion matrix ---------- */
  TOOLS.bayes = [
    { title: 'Regel van Bayes: voorwaardelijke kans omkeren',
      form: inp('pa', 'P(A) (voorkennis, prior)') + inp('ba', 'P(B | A)') + inp('bn', 'P(B | niet A)'),
      run: function (v) {
        var r = Calc.bayes(v.pa, v.ba, v.bn);
        return r ? out([['P(B)', fp(r.pB)], ['P(A | B)', fp(r.pAgivenB)], ['P(niet A | B)', fp(r.pNotAgivenB)], ['P(A | niet B)', fp(r.pAgivenNotB)],
                        ['odds vooraf × likelihood-ratio = odds achteraf', f(r.priorOdds) + ' × ' + f(r.likelihoodRatio) + ' = ' + f(r.posteriorOdds)]]) : '';
      }, pct: ['pa', 'ba', 'bn'] },
    { title: 'Bayesiaans bijwerken van een proportie met een Beta-prior',
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
      help: 'Vul C<sub>pa</sub> of C<sub>po</sub> in.',
      form: sel('basis', '%GRR ten opzichte van', [['tol', 'de tolerantie (USL − LSL)'], ['process', 'de procesvariatie (TV)']]) + inp('grr', '%GRR') + inp('cpa', 'werkelijke C<sub>pa</sub>') + inp('cpo', 'waargenomen C<sub>po</sub>'),
      run: function (v) {
        var r = Calc.cpObserved(v.text.basis, v.grr, v.cpa, v.cpo);
        if (!r) return '';
        return num(r.cpo) || num(r.cpa) ? result(out([num(r.cpo) ? ['waargenomen C<sub>po</sub>', f(r.cpo)] : ['werkelijke C<sub>pa</sub>', f(r.cpa)]]), r) : warn('geen oplossing: %GRR te groot voor deze Cp');
      }, pct: ['grr'] },
    { title: 'Gauge performance curve: kans om een stuk te aanvaarden (MSA p. 27)',
      help: 'Eén of meer referentiewaarden.',
      form: inp('lsl', 'LSL') + inp('usl', 'USL') + inp('b', 'bias b', '', '0') + inp('s', 'σ<sub>GRR</sub>') + area('x', 'referentiewaarden X<sub>r</sub>', '', 2),
      run: function (v) {
        var r = Calc.gaugePerformance(v.lsl, v.usl, v.b, v.s, parseList(v.text.x));
        return r ? grid(['X<sub>r</sub>', 'P(aanvaard)', 'P(afgekeurd)'], r.map(function (q) { return [f(q.x), fp(q.accept), fp(q.reject)]; })) : '';
      } },
    { title: 'Onzekerheidsbudget: u<sub>c</sub> en U = k·u<sub>c</sub> (MSA p. 28–29, stalen band)',
      help: 'Kies per bron het soort; k (certificaat) of d2 in het tweede veld, n in het derde als je het gemiddelde van n metingen gebruikt.',
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
      help: 'Plak de subgroepen of vul X̿, R̄, g en m in.',
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
        return result(out([['g × m', f(g) + ' × ' + f(m)], ['X̿ ; R̄', f(xbb) + ' ; ' + f(rbar)], ['bias', f(r.bias)], ['d2 ; d2* ; ν', f(r.d2) + ' ; ' + f(r.d2s) + ' ; ' + f(r.nu)],
                    ['σ<sub>r</sub> = R̄/d2', f(r.sr)], ['t', f(r.t)], ['t-kritiek (1 − α/2; ν)', f(r.tcrit)], ['p-waarde (tweezijdig)', fp(r.p)],
                    ['BI voor de bias', iv(r.ci)], ['besluit', r.significant ? 'bias significant (0 ligt niet in het BI)' : 'geen significante bias']]),
                      rows.length ? { xbb: xbb, rbar: rbar, g: g, m: m } : {});
      } },
    { title: 'Is de meeteenheid fijn genoeg? (MSA p. 30)',
      help: 'Zonder R̄: het grensgeval σ = MU.',
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
      if (el.classList.contains('solved')) { v.text[el.name] = ''; v[el.name] = null; return; }   // derived, not given
      v.text[el.name] = el.value;
      if (el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.getAttribute('data-text')) return;
      var x = parseNumber(el.value), pct = (pctNames || []).indexOf(el.name) >= 0 || el.name === 'alpha';
      if (x !== null && !isNaN(x) && pct && /%\s*$/.test(el.value)) x = x / 100;
      if (el.name === 'alpha' && x > 0.5 && x < 1) x = 1 - x;   // a confidence level 0,95 means α = 0,05
      v[el.name] = x === null || isNaN(x) ? null : x;
      el.classList.toggle('bad', isNaN(x));
    });
    return v;
  }
  // A field the calculator derived gets its value, turns red and is locked, so it cannot be typed over and it is
  // clear what was given and what was calculated. Emptying a given field unlocks the fields that depended on it.
  var LOCKED = 'Berekend uit de andere velden (rood = op slot). Wis een ingevuld veld of klik "Wis alles" om dit veld zelf in te vullen.';
  function lock(form, solved) {
    Array.prototype.forEach.call(form.querySelectorAll('input[name]'), function (el) {
      var x = solved[el.name], given = el.value.trim() !== '' && !el.classList.contains('solved');
      if (num(x) && !given) {
        el.value = f(x).replace(/&amp;/g, '&');
        el.classList.add('solved'); el.readOnly = true; el.title = LOCKED;
      } else if (el.classList.contains('solved')) {
        el.value = ''; el.classList.remove('solved'); el.readOnly = false; el.removeAttribute('title');
      }
    });
  }
  // lists that depend on the data (e.g. the categories of a cross table); true when a selection had to change
  function offer(form, choices) {
    var changed = false;
    Object.keys(choices || {}).forEach(function (name) {
      var el = form.querySelector('select[name="' + name + '"]'), sig = JSON.stringify(choices[name]);
      if (!el || el.getAttribute('data-sig') === sig) return;
      var keep = el.value;
      el.innerHTML = choices[name].map(function (o) { return '<option value="' + esc(o[0]) + '">' + o[1] + '</option>'; }).join('');
      el.setAttribute('data-sig', sig);
      el.value = choices[name].some(function (o) { return o[0] === keep; }) ? keep : choices[name][0][0];
      changed = changed || el.value !== keep;
    });
    return changed;
  }
  function mount(details) {
    if (details.dataset.ready) return;
    details.dataset.ready = '1';
    var body = details.querySelector('.tool-body'), name = details.dataset.tool;
    var tpl = document.getElementById('tpl-' + name);
    var blocks = TOOLS[name] || [], only = details.dataset.blocks ? details.dataset.blocks.split(' ').map(Number) : null;
    blocks.forEach(function (b, index) {
      if (only && only.indexOf(index) < 0) return;   // a calculator placed in the text shows only the blocks it needs
      var box = document.createElement('div');
      box.className = 'calc';
      box.innerHTML = '<h5>' + b.title + '</h5>' + (b.help ? '<p class="help">' + b.help + '</p>' : '') +
        '<form autocomplete="off">' + b.form + '<button type="reset" class="wis" title="alle velden terug leeg (of op hun standaardwaarde)">Wis alles</button></form>' +
        '<div class="calc-out"></div>';
      // the formulas of this block and what every symbol means (study/tool_formulas.html), right under the title
      var fx = document.getElementById('fx-' + name + '-' + index);
      if (fx) {
        var formulas = document.createElement('details');
        formulas.className = 'fx';
        formulas.open = true;
        formulas.innerHTML = '<summary>Formules en betekenis van de symbolen</summary>';
        formulas.appendChild(document.importNode(fx.content, true));
        box.insertBefore(formulas, box.querySelector('h5').nextSibling);
      }
      body.appendChild(box);
      var form = box.querySelector('form'), res = box.querySelector('.calc-out');
      function run() {
        var html, solved = {};
        try {
          var r = b.run(values(form, b.pct), body);
          if (r && typeof r === 'object') { html = r.html; solved = r.solved; if (offer(form, r.choices)) return run(); } else html = r;
        } catch (e) { html = warn(esc(e.message)); }
        lock(form, solved);
        res.innerHTML = html || '';
      }
      form.addEventListener('input', run);
      form.addEventListener('change', run);
      form.addEventListener('reset', function () { setTimeout(run, 0); });   // 'reset' fires before the fields are reset
      form.addEventListener('submit', function (e) { e.preventDefault(); });
      run();
    });
    if (tpl && !only) body.appendChild(document.importNode(tpl.content, true));
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
