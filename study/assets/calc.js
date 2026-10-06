/* Calculators of the study guide: pure functions, no DOM. They port the formulas of the tested workbook
   (src/bbtools/sheet_*.py, build/bb_toolkit.xlsx) so the guide and the workbook give the same numbers;
   tests/test_study_tools.py runs them in node against the course worked examples and scipy.
   Every function returns plain objects; a missing input gives null (shown as empty), never a guess. */
var Calc = (function () {
  'use strict';
  var S = (typeof Stats !== 'undefined') ? Stats : require('./stats.js');
  function num(x) { return typeof x === 'number' && isFinite(x); }
  function all() { for (var i = 0; i < arguments.length; i++) if (!num(arguments[i])) return false; return true; }
  function decide(p, alpha) { return num(p) && num(alpha) ? (p < alpha ? 'verwerp H0' : 'H0 niet verwerpen') : null; }

  /* ---------- normal distribution (sheet_normal.py; SPC p. 16-19, 27) ---------- */
  // Any sufficient subset of {µ, σ, x, z, P(X ≤ x), P(X > x)} → all of them. z = (x − µ)/σ, P(X ≤ x) = Φ(z).
  function normalSolve(k) {
    var mu = k.mu, s = k.sigma, x = k.x, z = k.z, notes = [], solved = [];
    var zp = num(k.pr) ? -S.normInv(k.pr) : (num(k.pl) ? S.normInv(k.pl) : null);   // right tail keeps far-tail digits
    if (num(k.pl) && num(k.pr) && Math.abs(k.pl + k.pr - 1) > 1e-9) notes.push('P(X ≤ x) + P(X > x) is niet 1');
    if (num(z) && num(zp) && Math.abs(z - zp) > 1e-6) notes.push('z en de kans spreken elkaar tegen');
    if (!num(z) && num(zp)) { z = zp; solved.push('z'); }
    if (num(s) && s <= 0) { notes.push('σ moet positief zijn'); s = null; }
    if (all(mu, s, x)) {
      var zc = (x - mu) / s;
      if (num(z) && Math.abs(z - zc) > 1e-6) notes.push('µ, σ, x en z/kans spreken elkaar tegen; z = (x − µ)/σ gebruikt');
      if (!num(k.z) && !num(zp)) solved.push('z');
      z = zc;
    } else if (num(z)) {
      if (all(mu, s)) { x = mu + z * s; solved.push('x'); }
      else if (all(x, s)) { mu = x - z * s; solved.push('mu'); }
      else if (all(x, mu)) {
        if (z === 0) notes.push('σ volgt niet uit z = 0');
        else if ((x - mu) / z <= 0) notes.push('x − µ en z hebben een verschillend teken: geen positieve σ');
        else { s = (x - mu) / z; solved.push('sigma'); }
      }
    }
    var pl = num(z) ? S.normCdf(z) : null, pr = num(z) ? S.normCdf(-z) : null;
    if (num(z) && !num(k.pl)) solved.push('pl');
    if (num(z) && !num(k.pr)) solved.push('pr');
    return { mu: mu, sigma: s, x: x, z: z, pl: pl, pr: pr, solved: solved, notes: notes };
  }
  function normalBetween(mu, s, a, b) {
    if (!all(mu, s, a, b) || s <= 0) return null;
    var lo = Math.min(a, b), hi = Math.max(a, b);
    var below = S.normCdf((lo - mu) / s), above = S.normCdf(-(hi - mu) / s);
    return { za: (lo - mu) / s, zb: (hi - mu) / s, below: below, above: above, between: 1 - below - above,
             outside: below + above };
  }
  function normalKSigma(mu, s, k) {
    if (!all(mu, s, k)) return null;
    var out = 2 * S.normCdf(-Math.abs(k));
    return { lo: mu - k * s, hi: mu + k * s, inside: 1 - out, outside: out };
  }
  function normalCentral(mu, s, coverage) {
    if (!all(mu, s, coverage) || coverage <= 0 || coverage >= 1) return null;
    var z = S.normInv(1 - (1 - coverage) / 2);
    return { z: z, lo: mu - z * s, hi: mu + z * s };
  }

  /* ---------- quantiles and p-values (z, t, χ², F) ---------- */
  function quantiles(dist, d1, d2, alpha) {
    if (!num(alpha) || alpha <= 0 || alpha >= 1) return null;
    var q = { z: function (p) { return S.normInv(p); }, t: function (p) { return S.tInv(p, d1); },
              chi2: function (p) { return S.chi2Inv(p, d1); }, F: function (p) { return S.fInv(p, d1, d2); } }[dist];
    var r = { chi2: function (a) { return S.chi2Isf(a, d1); }, F: function (a) { return S.fIsf(a, d1, d2); } }[dist];
    if (!q || (dist !== 'z' && !(d1 > 0)) || (dist === 'F' && !(d2 > 0))) return null;
    var right = function (a) { return r ? r(a) : -q(a); };
    return { left: q(alpha), right: right(alpha), twoLo: q(alpha / 2), twoHi: right(alpha / 2) };
  }
  function pValues(dist, d1, d2, stat) {
    if (!num(stat)) return null;
    var cdf, sf;
    if (dist === 'z') { cdf = S.normCdf(stat); sf = S.normCdf(-stat); }
    else if (dist === 't' && d1 > 0) { cdf = S.tCdf(stat, d1); sf = S.tSf(stat, d1); }
    else if (dist === 'chi2' && d1 > 0) { cdf = S.chi2Cdf(stat, d1); sf = S.chi2Sf(stat, d1); }
    else if (dist === 'F' && d1 > 0 && d2 > 0) { cdf = S.fCdf(stat, d1, d2); sf = S.fSf(stat, d1, d2); }
    else return null;
    var two = (dist === 'z' || dist === 't') ? 2 * Math.min(cdf, sf) : Math.min(1, 2 * Math.min(cdf, sf));
    return { left: cdf, right: sf, two: two };
  }

  /* ---------- means and proportions (sheet_means.py; Les 2 Ottoy) ---------- */
  function describe(xs) {
    if (!xs || xs.length < 2) return null;
    return { n: xs.length, mean: S.mean(xs), s: S.sd(xs) };
  }
  // interval rows: two-sided, lower bound only (at least …), upper bound only (at most …)
  function intervals(centre, se, crit2, crit1) {
    return { two: [centre - crit2 * se, centre + crit2 * se], lower: [centre - crit1 * se, Infinity],
             upper: [-Infinity, centre + crit1 * se], half2: crit2 * se, half1: crit1 * se };
  }
  // test rows ≠, >, < for a statistic with a z or t reference distribution
  function tests(stat, df, alpha) {
    var z = !num(df);
    var c2 = z ? S.normInv(1 - alpha / 2) : S.tInv(1 - alpha / 2, df), c1 = z ? S.normInv(1 - alpha) : S.tInv(1 - alpha, df);
    var cdf = z ? S.normCdf(stat) : S.tCdf(stat, df), sf = z ? S.normCdf(-stat) : S.tSf(stat, df);
    var two = 2 * (z ? S.normCdf(-Math.abs(stat)) : S.tSf(Math.abs(stat), df));
    return { stat: stat, ne: { crit: [-c2, c2], p: two, d: decide(two, alpha) },
             gt: { crit: [c1], p: sf, d: decide(sf, alpha) }, lt: { crit: [-c1], p: cdf, d: decide(cdf, alpha) } };
  }
  function oneMean(n, xbar, s, sigma, mu0, alpha) {
    if (!all(n, xbar, alpha) || n < 1) return null;
    var out = { n: n, xbar: xbar, df: n - 1 };
    if (num(sigma) && sigma > 0) {
      out.seZ = sigma / Math.sqrt(n);
      out.ciZ = intervals(xbar, out.seZ, S.normInv(1 - alpha / 2), S.normInv(1 - alpha));
      if (num(mu0)) out.testZ = tests((xbar - mu0) / out.seZ, null, alpha);
    }
    if (num(s) && s > 0 && n > 1) {
      out.seT = s / Math.sqrt(n);
      out.ciT = intervals(xbar, out.seT, S.tInv(1 - alpha / 2, n - 1), S.tInv(1 - alpha, n - 1));
      if (num(mu0)) out.testT = tests((xbar - mu0) / out.seT, n - 1, alpha);
    }
    return out;
  }
  function twoMeansPooled(n1, m1, s1, n2, m2, s2, d0, alpha) {
    if (!all(n1, m1, s1, n2, m2, s2, alpha) || n1 + n2 <= 2) return null;
    var df = n1 + n2 - 2, sp = Math.sqrt(((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / df);
    var se = sp * Math.sqrt(1 / n1 + 1 / n2), diff = m1 - m2;
    return { sp: sp, df: df, se: se, diff: diff,
             ci: intervals(diff, se, S.tInv(1 - alpha / 2, df), S.tInv(1 - alpha, df)),
             test: tests((diff - (num(d0) ? d0 : 0)) / se, df, alpha) };
  }
  function paired(n, dbar, sd, d0, alpha) {
    if (!all(n, dbar, sd, alpha) || n < 2 || sd <= 0) return null;
    var se = sd / Math.sqrt(n), df = n - 1;
    return { se: se, df: df, dbar: dbar, ci: intervals(dbar, se, S.tInv(1 - alpha / 2, df), S.tInv(1 - alpha, df)),
             test: tests((dbar - (num(d0) ? d0 : 0)) / se, df, alpha) };
  }
  function oneProportion(n, x, pi0, alpha) {
    if (!all(n, x, alpha) || n <= 0 || x < 0 || x > n) return null;
    var p = x / n, se = Math.sqrt(p * (1 - p) / n);
    var out = { p: p, se: se, ci: intervals(p, se, S.normInv(1 - alpha / 2), S.normInv(1 - alpha)) };
    // exact (Clopper-Pearson) = R binom.test, CI Further Reading p. 20; BETA.INV as in the workbook
    out.exact = {
      two: [x === 0 ? 0 : S.betaInv(alpha / 2, x, n - x + 1), x === n ? 1 : S.betaInv(1 - alpha / 2, x + 1, n - x)],
      lower: [x === 0 ? 0 : S.betaInv(alpha, x, n - x + 1), Infinity],
      upper: [0, x === n ? 1 : S.betaInv(1 - alpha, x + 1, n - x)]
    };
    if (num(pi0) && pi0 > 0 && pi0 < 1) {
      out.condition = n * pi0 > 5;
      out.test = tests((p - pi0) / Math.sqrt(pi0 * (1 - pi0) / n), null, alpha);
    }
    return out;
  }
  function twoProportions(n1, x1, n2, x2, alpha) {
    if (!all(n1, x1, n2, x2, alpha) || n1 <= 0 || n2 <= 0) return null;
    var p1 = x1 / n1, p2 = x2 / n2, se = Math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2);
    return { p1: p1, p2: p2, diff: p1 - p2, se: se,
             ci: intervals(p1 - p2, se, S.normInv(1 - alpha / 2), S.normInv(1 - alpha)) };
  }

  /* ---------- variances (sheet_variance.py) ---------- */
  function oneVariance(n, s, sigma0, alpha) {
    if (!all(n, s, alpha) || n < 2 || s <= 0) return null;
    var df = n - 1, q = df * s * s;
    var ci = { two: [q / S.chi2Isf(alpha / 2, df), q / S.chi2Inv(alpha / 2, df)],
               lower: [q / S.chi2Isf(alpha, df), Infinity], upper: [0, q / S.chi2Inv(alpha, df)] };
    var out = { df: df, s2: s * s, ci: ci };
    if (num(sigma0) && sigma0 > 0) {
      var x2 = q / (sigma0 * sigma0), lo = S.chi2Cdf(x2, df), hi = S.chi2Sf(x2, df), two = 2 * Math.min(lo, hi);
      out.test = { stat: x2,
                   ne: { crit: [S.chi2Inv(alpha / 2, df), S.chi2Isf(alpha / 2, df)], p: two, d: decide(two, alpha) },
                   gt: { crit: [S.chi2Isf(alpha, df)], p: hi, d: decide(hi, alpha) },
                   lt: { crit: [S.chi2Inv(alpha, df)], p: lo, d: decide(lo, alpha) } };
    }
    return out;
  }
  function twoVariances(n1, s1, n2, s2, alpha) {
    if (!all(n1, s1, n2, s2, alpha) || n1 < 2 || n2 < 2 || s1 <= 0 || s2 <= 0) return null;
    var v1 = n1 - 1, v2 = n2 - 1, F = s1 * s1 / (s2 * s2);
    var ci = { two: [F / S.fIsf(alpha / 2, v1, v2), F / S.fInv(alpha / 2, v1, v2)],
               lower: [F / S.fIsf(alpha, v1, v2), Infinity], upper: [0, F / S.fInv(alpha, v1, v2)] };
    var inv = function (r) { return [r[1] === Infinity ? 0 : 1 / r[1], r[0] === 0 ? Infinity : 1 / r[0]]; };
    var lo = S.fCdf(F, v1, v2), hi = S.fSf(F, v1, v2), two = 2 * Math.min(lo, hi);
    return { v1: v1, v2: v2, F: F, ci: ci, ciInv: { two: inv(ci.two), lower: inv(ci.upper), upper: inv(ci.lower) },
             test: { stat: F,
                     ne: { crit: [S.fInv(alpha / 2, v1, v2), S.fIsf(alpha / 2, v1, v2)], p: two, d: decide(two, alpha) },
                     gt: { crit: [S.fIsf(alpha, v1, v2)], p: hi, d: decide(hi, alpha) },
                     lt: { crit: [S.fInv(alpha, v1, v2)], p: lo, d: decide(lo, alpha) } } };
  }

  /* ---------- discrete and continuous distributions (sheet_distributions.py) ---------- */
  function atLeast(cdfBelow, k) { return k <= 0 ? 1 : 1 - cdfBelow(k - 1); }
  function binomial(n, p, k) {
    if (!all(n, p) || n < 0 || p < 0 || p > 1) return null;
    var out = { mean: n * p, variance: n * p * (1 - p) };
    out.sd = Math.sqrt(out.variance);
    if (num(k)) { out.eq = S.binomPmf(k, n, p); out.le = S.binomCdf(k, n, p);
                  out.ge = atLeast(function (j) { return S.binomCdf(j, n, p); }, k); }
    return out;
  }
  function hypergeometric(N, D, n, k) {
    if (!all(N, D, n) || D > N || n > N) return null;
    var f = D / N, out = { mean: n * f, variance: n * f * (1 - f) * (N - n) / (N - 1) };
    if (num(k)) { out.eq = S.hypergeomPmf(k, N, D, n); out.le = S.hypergeomCdf(k, N, D, n);
                  out.ge = atLeast(function (j) { return S.hypergeomCdf(j, N, D, n); }, k); }
    return out;
  }
  function poisson(lam, k) {
    if (!num(lam) || lam <= 0) return null;
    var out = { mean: lam, variance: lam };
    if (num(k)) { out.eq = S.poissonPmf(k, lam); out.le = S.poissonCdf(k, lam);
                  out.ge = atLeast(function (j) { return S.poissonCdf(j, lam); }, k); }
    return out;
  }
  function exponential(rate, t) {
    if (!num(rate) || rate <= 0) return null;
    var out = { mean: 1 / rate, variance: 1 / (rate * rate) };
    if (num(t)) { out.le = t <= 0 ? 0 : 1 - Math.exp(-rate * t); out.gt = t <= 0 ? 1 : Math.exp(-rate * t); }
    return out;
  }
  function uniform(a, b, x) {
    if (!all(a, b) || b <= a) return null;
    var out = { mean: (a + b) / 2, variance: (b - a) * (b - a) / 12 };
    if (num(x)) out.le = Math.min(1, Math.max(0, (x - a) / (b - a)));
    return out;
  }
  function bernoulli(p) { return num(p) && p >= 0 && p <= 1 ? { mean: p, variance: p * (1 - p) } : null; }

  /* ---------- contingency table: joint, marginal, conditional (Naert Les 1 p. 22-23) ---------- */
  function contingency(rows) {
    if (!rows || !rows.length || rows.some(function (r) { return r.length !== rows[0].length; })) return null;
    var R = rows.length, C = rows[0].length, N = 0, rt = [], ct = [], i, j;
    for (j = 0; j < C; j++) ct.push(0);
    for (i = 0; i < R; i++) { rt.push(0); for (j = 0; j < C; j++) { rt[i] += rows[i][j]; ct[j] += rows[i][j]; N += rows[i][j]; } }
    if (!(N > 0)) return null;
    var joint = rows.map(function (r) { return r.map(function (v) { return v / N; }); });
    return { N: N, rowTotals: rt, colTotals: ct, joint: joint,
             pRow: rt.map(function (v) { return v / N; }), pCol: ct.map(function (v) { return v / N; }),
             colGivenRow: rows.map(function (r, a) { return r.map(function (v) { return rt[a] ? v / rt[a] : null; }); }),
             rowGivenCol: rows.map(function (r) { return r.map(function (v, b) { return ct[b] ? v / ct[b] : null; }); }),
             product: rows.map(function (r, a) { return r.map(function (v, b) { return (rt[a] / N) * (ct[b] / N); }); }) };
  }

  /* ---------- sigma level, DPMO, yield (sheet_sigma.py) ---------- */
  var SHIFT = 1.5, MILLION = 1e6;
  function defects(D, N, O) {
    if (!all(D, N) || N <= 0) return null;
    var out = { dpu: D / N };
    out.ty = 1 - out.dpu; out.rtyApprox = Math.exp(-out.dpu);
    if (num(O) && O > 0) { out.dpo = D / (N * O); out.dpmo = out.dpo * MILLION; out.ypo = 1 - out.dpo; }
    return out;
  }
  function sigmaFromDpmo(dpmo) {
    if (!num(dpmo) || dpmo <= 0 || dpmo >= MILLION) return null;
    var z = -S.normInv(dpmo / MILLION);
    return { yield: 1 - dpmo / MILLION, z: z, level: z + SHIFT };
  }
  function dpmoFromSigma(Z) {
    if (!num(Z)) return null;
    var shifted = MILLION * S.normCdf(-(Z - SHIFT));
    return { shifted: shifted, oneTail: MILLION * S.normCdf(-Z), twoTails: 2 * MILLION * S.normCdf(-Z),
             yieldShifted: 1 - shifted / MILLION };
  }
  function yields(inU, outU, scrap, rework) {
    if (!num(inU) || inU <= 0) return null;
    var out = {};
    if (num(outU)) out.y = outU / inU;
    if (all(scrap, rework)) out.fty = (inU - scrap - rework) / inU;
    if (all(out.y, out.fty)) out.hidden = out.y - out.fty;
    return out;
  }
  function rolled(steps) {
    if (!steps || !steps.length) return null;
    var rty = steps.reduce(function (a, b) { return a * b; }, 1);
    return rollDerived(rty, steps.length);
  }
  function rollDerived(rty, k) {
    if (!num(rty) || rty <= 0 || rty > 1) return null;
    var out = { rty: rty, dpu: -Math.log(rty), repairable: 1 + (1 - rty), scrapped: 1 / rty };
    if (num(k) && k > 0) { out.k = k; out.ny = Math.pow(rty, 1 / k); }
    return out;
  }
  function yieldPower(y, k) { return all(y, k) && y > 0 ? { rty: Math.pow(y, k), oneIn: 1 / Math.pow(y, k) } : null; }
  function perOpportunity(y, opps) {
    if (!all(y, opps) || y <= 0 || y > 1 || opps <= 0) return null;
    var ypo = Math.pow(y, 1 / opps), out = { ypo: ypo, dpmo: (1 - ypo) * MILLION };
    if (ypo < 1) { out.z = S.normInv(ypo); out.level = out.z + SHIFT; }
    return out;
  }

  /* ---------- capability (sheet_capability.py; SPC p. 33-40) ---------- */
  var CP_LEVELS = [[2, '6 Sigma quality level'], [1.67, 'good'], [1.33, 'acceptable'], [1, 'just capable']];
  function cpLevel(cp) {
    for (var i = 0; i < CP_LEVELS.length; i++) if (cp >= CP_LEVELS[i][0]) return CP_LEVELS[i][1];
    return 'not capable';
  }
  function capabilityRow(lsl, usl, mean, sigma) {
    if (!num(sigma) || sigma <= 0 || (all(lsl, usl) && usl <= lsl)) return null;
    var r = { sigma: sigma };
    if (all(lsl, usl)) { r.cp = (usl - lsl) / (6 * sigma); r.level = cpLevel(r.cp); }
    if (all(usl, mean)) { r.cpu = (usl - mean) / (3 * sigma); r.zUsl = (usl - mean) / sigma; r.above = S.normCdf(-r.zUsl); }
    if (all(lsl, mean)) { r.cpl = (mean - lsl) / (3 * sigma); r.zLsl = (mean - lsl) / sigma; r.below = S.normCdf(-r.zLsl); }
    if (num(r.cpu) || num(r.cpl)) {
      r.cpk = num(r.cpu) && num(r.cpl) ? Math.min(r.cpu, r.cpl) : (num(r.cpu) ? r.cpu : r.cpl);
      r.capable = r.cpk > 1.33 ? 'ja' : 'nee';
      r.out = (num(r.below) ? r.below : 0) + (num(r.above) ? r.above : 0);
      r.ppm = r.out * MILLION;
    }
    return r;
  }
  // one row per σ estimate the course uses (decision 1); constants from the tables of decision 4
  function capability(inp, K) {
    var rows = [];
    function add(key, label, sigma, constant) {
      var r = capabilityRow(inp.lsl, inp.usl, inp.mean, sigma);
      if (r) { r.key = key; r.label = label; r.constant = constant; rows.push(r); }
    }
    if (num(inp.sigma)) add('given', 'σ gegeven', inp.sigma, null);
    var d2 = K.get('d2', inp.n), c4 = K.get('c4', inp.n), d2two = K.get('d2', 2);
    if (num(inp.rbar) && num(d2)) add('rbar_d2', 'R̄ / d2 (korte termijn)', inp.rbar / d2, 'd2(' + inp.n + ') = ' + d2);
    if (num(inp.sbar)) add('sbar', 's̄ rechtstreeks (zoals SPC p. 46)', inp.sbar, null);
    if (num(inp.sbar) && num(c4)) add('sbar_c4', 's̄ / c4 (zuiver)', inp.sbar / c4, 'c4(' + inp.n + ') = ' + c4);
    if (num(inp.mrbar) && num(d2two)) add('mrbar', 'MR̄ / d2(2) (individuele waarden)', inp.mrbar / d2two, 'd2(2) = ' + d2two);
    if (num(inp.overall)) add('overall', 'totale s (lange termijn: Pp, Ppk)', inp.overall, null);
    return rows;
  }
  function capabilityInverse(lsl, usl, cpTarget, sigma, cpkTarget) {
    var out = {};
    if (all(lsl, usl, cpTarget) && usl > lsl && cpTarget > 0) out.sigmaForCp = (usl - lsl) / (6 * cpTarget);
    if (all(sigma, cpkTarget) && sigma > 0) {
      if (num(lsl)) out.meanMin = lsl + 3 * cpkTarget * sigma;
      if (num(usl)) out.meanMax = usl - 3 * cpkTarget * sigma;
    }
    return out;
  }

  /* ---------- control charts (sheet_charts.py; SPC p. 74, Dummies p. 249-254) ---------- */
  function limitsSummary(n, xbarbar, rbar, sbar, K) {
    var out = { n: n };
    if (!num(n)) return out;
    ['A2', 'D3', 'D4', 'd2', 'A3', 'B3', 'B4', 'c4'].forEach(function (s) { out[s] = K.get(s, n); });
    if (all(xbarbar, rbar, out.A2)) out.xR = [xbarbar - out.A2 * rbar, xbarbar, xbarbar + out.A2 * rbar];
    if (all(rbar, out.D3, out.D4)) out.R = [out.D3 * rbar, rbar, out.D4 * rbar];
    if (all(rbar, out.d2)) { out.sigmaR = rbar / out.d2; out.sigmaXbar = out.sigmaR / Math.sqrt(n); }
    if (all(xbarbar, sbar, out.A3)) out.xS = [xbarbar - out.A3 * sbar, xbarbar, xbarbar + out.A3 * sbar];
    if (all(sbar, out.B3, out.B4)) out.S = [out.B3 * sbar, sbar, out.B4 * sbar];
    if (all(sbar, out.c4)) out.sigmaS = sbar / out.c4;
    return out;
  }
  function flag(v, lim) { return !lim || !num(v) ? '' : (v > lim[2] ? 'boven UCL' : (v < lim[0] ? 'onder LCL' : '')); }
  function subgroupChart(groups, K) {
    if (!groups || !groups.length) return null;
    var n = groups[0].length;
    if (n < 2 || groups.some(function (g) { return g.length !== n; })) return { error: 'alle subgroepen moeten even groot zijn (n ≥ 2)' };
    var stats = groups.map(function (g) {
      var m = S.mean(g);
      return { mean: m, range: Math.max.apply(null, g) - Math.min.apply(null, g), s: S.sd(g) };
    });
    var xbb = S.mean(stats.map(function (g) { return g.mean; })), rbar = S.mean(stats.map(function (g) { return g.range; }));
    var sbar = S.mean(stats.map(function (g) { return g.s; }));
    var out = limitsSummary(n, xbb, rbar, sbar, K);
    out.k = groups.length; out.xbarbar = xbb; out.rbar = rbar; out.sbar = sbar;
    out.groups = stats.map(function (g) {
      return { mean: g.mean, range: g.range, s: g.s, fxR: flag(g.mean, out.xR), fR: flag(g.range, out.R),
               fxS: flag(g.mean, out.xS), fS: flag(g.s, out.S) };
    });
    return out;
  }
  function individuals(xs, K) {
    if (!xs || xs.length < 2) return null;
    var mr = [];
    for (var i = 1; i < xs.length; i++) mr.push(Math.abs(xs[i] - xs[i - 1]));
    var xbar = S.mean(xs), mrbar = S.mean(mr), E2 = K.get('E2', 2), D3 = K.get('D3', 2), D4 = K.get('D4', 2), d2 = K.get('d2', 2);
    var out = { k: xs.length, xbar: xbar, mrbar: mrbar, E2: E2, D3: D3, D4: D4, d2: d2, sigma: mrbar / d2,
                X: [xbar - E2 * mrbar, xbar, xbar + E2 * mrbar], MR: [D3 * mrbar, mrbar, D4 * mrbar] };
    out.points = xs.map(function (x, j) {
      return { x: x, mr: j ? mr[j - 1] : null, fx: flag(x, out.X), fmr: j ? flag(mr[j - 1], out.MR) : '' };
    });
    return out;
  }
  // p chart (defectives) or u chart (defects): pairs [n_i, count_i]; limits per subgroup, negative LCL → 0
  function attributeChart(kind, pairs) {
    if (!pairs || !pairs.length || pairs.some(function (p) { return p.length !== 2 || !(p[0] > 0); })) return null;
    var tn = 0, tc = 0;
    pairs.forEach(function (p) { tn += p[0]; tc += p[1]; });
    var c = tc / tn;
    return { total: tn, count: tc, centre: c, rows: pairs.map(function (p) {
      var half = 3 * Math.sqrt(kind === 'p' ? c * (1 - c) / p[0] : c / p[0]);
      var lim = [Math.max(0, c - half), c, c + half], v = p[1] / p[0];
      return { n: p[0], count: p[1], value: v, lcl: lim[0], ucl: lim[2], flag: flag(v, lim) };
    }) };
  }

  /* ---------- acceptance sampling (sheet_acceptance.py; Further Reading p. 4, 9, 10) ---------- */
  function ocBinomial(n, c, p) { return S.binomCdf(c, n, p); }
  function ocHyper(n, c, N, p) { return S.hypergeomCdf(c, N, Math.floor(p * N + 1e-9), n); }
  function aoqExact(n, c, N, p) {
    var oc = ocHyper(n, c, N, p), M = Math.floor(p * N + 1e-9);
    if (oc === 0) return 0;
    var rs = (c === 0 || M === 0) ? 0 : S.hypergeomCdf(c - 1, N - 1, M - 1, n - 1) / oc;
    return p * oc * (1 - (n / N) * rs);
  }
  function samplingPoint(n, c, N, p) {
    if (!all(n, c, p)) return null;
    var out = { ocBin: ocBinomial(n, c, p) };
    if (num(N) && N >= n) {
      out.ocHyp = ocHyper(n, c, N, p); out.aoq = aoqExact(n, c, N, p); out.ati = n * out.ocHyp + N * (1 - out.ocHyp);
    }
    out.aoqApprox = p * (num(out.ocHyp) ? out.ocHyp : out.ocBin);
    return out;
  }
  function samplingRisks(n, c, N, aql, lql, alphaT, betaT) {
    if (!all(n, c)) return null;
    var out = {};
    if (num(aql)) { out.ocAqlBin = ocBinomial(n, c, aql); out.alphaBin = 1 - out.ocAqlBin; }
    if (num(lql)) out.betaBin = ocBinomial(n, c, lql);
    if (num(N)) {
      if (num(aql)) { out.ocAqlHyp = ocHyper(n, c, N, aql); out.alphaHyp = 1 - out.ocAqlHyp; }
      if (num(lql)) out.betaHyp = ocHyper(n, c, N, lql);
    }
    if (all(out.alphaBin, out.betaBin, alphaT, betaT)) out.meetsBin = out.alphaBin <= alphaT && out.betaBin <= betaT ? 'ja' : 'nee';
    if (all(out.alphaHyp, out.betaHyp, alphaT, betaT)) out.meetsHyp = out.alphaHyp <= alphaT && out.betaHyp <= betaT ? 'ja' : 'nee';
    return out;
  }
  // AOQL = max over p of AOQ(p). With a lot size N the lot fraction can only be M/N (M defectives), so scan those;
  // without N scan p on a grid of step 0.0001 (binomial OC).
  function aoql(n, c, N) {
    if (!all(n, c)) return null;
    var best = { approx: 0, pApprox: 0, exact: null, pExact: null }, lot = num(N) && N >= n;
    for (var i = 1; i <= (lot ? N : 10000); i++) {
      var p = lot ? i / N : i / 10000, oc = lot ? ocHyper(n, c, N, p) : ocBinomial(n, c, p), a = p * oc;
      if (a > best.approx) { best.approx = a; best.pApprox = p; }
      if (lot) { var e = aoqExact(n, c, N, p); if (best.exact === null || e > best.exact) { best.exact = e; best.pExact = p; } }
      if (oc < 1e-12) break;
    }
    return best;
  }
  function variablesPlan(p0, pt, alpha, beta) {
    if (!all(p0, pt, alpha, beta) || pt <= p0) return null;
    var z = S.normInv, k = (z(pt) * z(alpha) + z(p0) * z(beta)) / (z(1 - alpha) + z(1 - beta));
    var n = Math.pow(z(1 - alpha) + z(1 - beta), 2) * (1 + k * k / 2) / Math.pow(z(pt) - z(p0), 2), nUp = Math.ceil(n - 1e-9);
    var oc = function (p) { return 1 - S.normCdf((z(p) + k) * Math.sqrt(nUp) / Math.sqrt(1 + k * k / 2)); };
    return { k: k, n: n, nUp: nUp, ocAql: oc(p0), ocLql: oc(pt) };
  }

  /* ---------- regression, one-way ANOVA, 2^k factorial (sheet_doe.py) ---------- */
  function regression(xs, ys, x0, b1H0, b0H0, alpha) {
    if (!xs || !ys || xs.length !== ys.length || xs.length < 3) return null;
    var n = xs.length, xb = S.mean(xs), yb = S.mean(ys), sxx = S.devsq(xs), sxy = 0, i;
    for (i = 0; i < n; i++) sxy += (xs[i] - xb) * (ys[i] - yb);
    if (!(sxx > 0)) return null;
    var b1 = sxy / sxx, b0 = yb - b1 * xb, sst = S.devsq(ys), ssr = b1 * b1 * sxx, sse = sst - ssr, mse = sse / (n - 2);
    var r = { n: n, xbar: xb, ybar: yb, sxx: sxx, sxy: sxy, b1: b1, b0: b0, sst: sst, ssr: ssr, sse: sse, mse: mse,
              sigma: Math.sqrt(mse), r2: ssr / sst, r2adj: 1 - (1 - ssr / sst) * (n - 1) / (n - 2),
              r2adjP56: n > 3 ? 1 - (1 - ssr / sst) * (n - 1) / (n - 3) : null, df: n - 2 };
    r.F = ssr / mse; r.pF = S.fSf(r.F, 1, n - 2);
    r.seB1 = Math.sqrt(mse / sxx); r.seB0 = Math.sqrt(mse * (1 / n + xb * xb / sxx));
    var t2 = S.tInv(1 - alpha / 2, n - 2), t1 = S.tInv(1 - alpha, n - 2);
    r.tB1 = tests((b1 - (num(b1H0) ? b1H0 : 0)) / r.seB1, n - 2, alpha);
    r.tB0 = tests((b0 - (num(b0H0) ? b0H0 : 0)) / r.seB0, n - 2, alpha);
    r.ciB1 = intervals(b1, r.seB1, t2, t1); r.ciB0 = intervals(b0, r.seB0, t2, t1);
    if (num(x0)) {
      r.y0 = b0 + b1 * x0;
      r.seMean = Math.sqrt(mse * (1 / n + (x0 - xb) * (x0 - xb) / sxx));
      r.sePred = Math.sqrt(mse * (1 + 1 / n + (x0 - xb) * (x0 - xb) / sxx));
      r.ciMean = intervals(r.y0, r.seMean, t2, t1); r.pi = intervals(r.y0, r.sePred, t2, t1);
    }
    return r;
  }
  function anova1(groups, alpha) {
    groups = (groups || []).filter(function (g) { return g.length > 0; });
    if (groups.length < 2) return null;
    var everything = [].concat.apply([], groups), N = everything.length, a = groups.length, gm = S.mean(everything);
    var sst = S.devsq(everything), sse = 0, sstr = 0;
    var desc = groups.map(function (g) {
      var m = S.mean(g); sse += S.devsq(g); sstr += g.length * (m - gm) * (m - gm);
      return { n: g.length, mean: m, s: g.length > 1 ? S.sd(g) : null };
    });
    var dfTr = a - 1, dfE = N - a, msTr = sstr / dfTr, msE = sse / dfE, F = msTr / msE;
    return { groups: desc, grandMean: gm, N: N, a: a, sst: sst, sstr: sstr, sse: sse, dfTr: dfTr, dfE: dfE,
             msTr: msTr, msE: msE, F: F, p: S.fSf(F, dfTr, dfE), Fcrit: S.fIsf(alpha, dfTr, dfE),
             pooledSd: Math.sqrt(msE), d: decide(S.fSf(F, dfTr, dfE), alpha) };
  }
  function effectName(mask) {
    var s = '';
    for (var j = 0; j < 26; j++) if (mask & (1 << j)) s += String.fromCharCode(65 + j);
    return s;
  }
  function bits(m) { var c = 0; while (m) { c += m & 1; m >>= 1; } return c; }
  // runs in standard order (run i: factor j at +1 when bit j of i is set), replicates per run
  function factorial(k, runs, poolOrder, alpha) {
    var R = 1 << k;
    if (!(k >= 2 && k <= 6) || !runs || runs.length !== R) return { error: 'geef 2^k = ' + R + ' regels (runs) in standaardvolgorde' };
    var n = runs[0].length;
    if (n < 1 || runs.some(function (r) { return r.length !== n; })) return { error: 'elke run moet evenveel herhalingen hebben' };
    var N = R * n, total = 0, sspe = 0, all_ = [];
    var means = runs.map(function (r) { total += r.reduce(function (a, b) { return a + b; }, 0); all_ = all_.concat(r);
                                        if (n > 1) sspe += S.devsq(r); return S.mean(r); });
    var effects = [], ssPool = 0, dfPool = 0, pooling = num(poolOrder) && poolOrder >= 2;
    for (var mask = 1; mask < R; mask++) {
      var contrast = 0;
      // sign of run i in column `mask` = product of the ±1 levels = −1 per factor of the mask that is at its low level
      for (var i = 0; i < R; i++) contrast += ((bits(mask) - bits(i & mask)) % 2 ? -1 : 1) * means[i] * n;
      var e = { name: effectName(mask), order: bits(mask), contrast: contrast, effect: contrast / (n * R / 2),
                ss: contrast * contrast / (n * R) };
      e.coef = e.effect / 2;
      e.pooled = pooling && e.order >= poolOrder;
      if (e.pooled) { ssPool += e.ss; dfPool += 1; }
      effects.push(e);
    }
    var dfPE = R * (n - 1), dfE = dfPE + dfPool, ssE = sspe + ssPool, mse = dfE > 0 ? ssE / dfE : null;
    var se = num(mse) ? Math.sqrt(mse / (n * R / 4)) : null;
    effects.forEach(function (e) {
      if (num(se)) { e.lo = e.effect - 2 * se; e.hi = e.effect + 2 * se; }
      if (!e.pooled && num(mse) && mse > 0) { e.F = e.ss / mse; e.p = S.fSf(e.F, 1, dfE); }
    });
    var model = effects.filter(function (e) { return !e.pooled; });
    var ssModel = model.reduce(function (a, e) { return a + e.ss; }, 0), sst = S.devsq(all_), p = model.length;
    var out = { k: k, n: n, N: N, beta0: total / N, sspe: sspe, dfPE: dfPE, ssPool: ssPool, dfPool: dfPool, ssE: ssE, dfE: dfE,
                mse: mse, se: se, effects: effects, ssModel: ssModel, dfModel: p, sst: sst, dfT: N - 1 };
    if (sst > 0) {
      out.r2 = ssModel / sst;
      if (N - p - 1 > 0) out.r2adj = 1 - (1 - out.r2) * (N - 1) / (N - p - 1);
      if (N - p - 2 > 0) out.r2adjP56 = 1 - (1 - out.r2) * (N - 1) / (N - p - 2);
    }
    if (num(mse) && mse > 0 && p > 0) { out.Fmodel = (ssModel / p) / mse; out.pModel = S.fSf(out.Fmodel, p, dfE); }
    return out;
  }
  // fractional factorial: generators such as "D=ABC; E=ABD" → defining relation, resolution, aliases (DOE p. 80-92)
  function aliases(text) {
    var gens = String(text || '').toUpperCase().split(/[;,\n]+/).map(function (g) { return g.replace(/\s/g, ''); })
      .filter(function (g) { return g; });
    var words = [], used = 0, generated = 0;
    for (var g = 0; g < gens.length; g++) {
      var m = /^([A-Z])=(-?)([A-Z]+)$/.exec(gens[g]);
      if (!m) return { error: 'schrijf generatoren als D=ABC (gescheiden door ; of ,)' };
      var w = 0, letters = m[1] + m[3];
      for (var c = 0; c < letters.length; c++) w ^= 1 << (letters.charCodeAt(c) - 65);
      words.push({ mask: w, sign: m[2] ? -1 : 1 });
      for (c = 0; c < letters.length; c++) used |= 1 << (letters.charCodeAt(c) - 65);
      generated |= 1 << (m[1].charCodeAt(0) - 65);
    }
    if (!words.length) return null;
    var relation = [];
    for (var sub = 1; sub < (1 << words.length); sub++) {
      var mask = 0, sign = 1;
      for (var j = 0; j < words.length; j++) if (sub & (1 << j)) { mask ^= words[j].mask; sign *= words[j].sign; }
      relation.push({ mask: mask, sign: sign, name: (sign < 0 ? '−' : '') + effectName(mask) });
    }
    relation.sort(function (a, b) { return bits(a.mask) - bits(b.mask) || a.mask - b.mask; });
    var k = bits(used), p = words.length, resolution = Math.min.apply(null, relation.map(function (r) { return bits(r.mask); }));
    var factors = [];
    for (var f = 0; f < 26; f++) if (used & (1 << f)) factors.push(1 << f);
    var effectsList = factors.slice();
    for (var a = 0; a < factors.length; a++) for (var b2 = a + 1; b2 < factors.length; b2++) effectsList.push(factors[a] | factors[b2]);
    var chains = effectsList.map(function (e) {
      return { effect: effectName(e), aliases: relation.map(function (r) { return (r.sign < 0 ? '−' : '') + effectName(e ^ r.mask); }) };
    });
    return { k: k, p: p, runs: 1 << (k - p), relation: relation.map(function (r) { return r.name; }), resolution: resolution,
             base: factors.filter(function (x) { return !(generated & x); }).map(effectName).join(''), chains: chains };
  }

  /* ---------- Gage R&R (sheet_grr.py; MSA p. 34-37) ---------- */
  // rows: k·r lines (operator A trials 1..r, operator B …), each with n part values
  function grr(rows, k, r, tol, alpha, M) {
    if (!all(k, r) || k < 2 || r < 2 || !rows || rows.length !== k * r) return { error: 'geef k·r = ' + (k * r) + ' regels (operator × herhaling), elk met n waarden' };
    var n = rows[0].length;
    if (n < 2 || rows.some(function (x) { return x.length !== n; })) return { error: 'elke regel moet n ≥ 2 waarden (delen) hebben' };
    var i, j, t, cell = [], ranges = [], opMean = [], partMean = [], all_ = [];
    for (i = 0; i < k; i++) {
      cell.push([]); ranges.push([]);
      for (j = 0; j < n; j++) {
        var v = [];
        for (t = 0; t < r; t++) v.push(rows[i * r + t][j]);
        cell[i].push(S.mean(v)); ranges[i].push(Math.max.apply(null, v) - Math.min.apply(null, v));
        all_ = all_.concat(v);
      }
      opMean.push(S.mean(cell[i]));
    }
    for (j = 0; j < n; j++) { var s = 0; for (i = 0; i < k; i++) s += cell[i][j]; partMean.push(s / k); }
    var gm = S.mean(all_), rbarbar = S.mean([].concat.apply([], ranges));
    var xdiff = Math.max.apply(null, opMean) - Math.min.apply(null, opMean);
    var rp = Math.max.apply(null, partMean) - Math.min.apply(null, partMean);
    var d2 = M.d2(r), d2k = M.d2star(1, k), d2n = M.d2star(1, n);
    var out = { k: k, n: n, r: r, opMeans: opMean, partMeans: partMean, rbarbar: rbarbar, xdiff: xdiff, rp: rp,
                d2: d2, d2k: d2k, d2n: d2n };
    function finish(ev, av, pv) {
      var g = Math.sqrt(ev * ev + av * av), tv = Math.sqrt(g * g + pv * pv);
      var res = { ev: ev, av: av, pv: pv, grr: g, tv: tv, pctTv: g / tv };
      if (num(tol) && tol > 0) res.pctTol = 6 * g / tol;
      res.verdict = res.pctTv <= 0.10 ? 'aanvaardbaar (≤ 10 %)' : (res.pctTv <= 0.30 ? 'misschien aanvaardbaar (10–30 %)' : 'niet aanvaardbaar (> 30 %)');
      return res;
    }
    if (all(d2, d2k, d2n)) {
      var ev = rbarbar / d2;
      out.ar = finish(ev, Math.sqrt(Math.max(0, Math.pow(xdiff / d2k, 2) - ev * ev / (n * r))),
                      Math.sqrt(Math.max(0, Math.pow(rp / d2n, 2) - ev * ev / (k * r))));
    }
    // ANOVA (two-way, crossed)
    var ssOp = 0, ssPart = 0, ssCells = 0, sst = S.devsq(all_);
    for (i = 0; i < k; i++) ssOp += n * r * Math.pow(opMean[i] - gm, 2);
    for (j = 0; j < n; j++) ssPart += k * r * Math.pow(partMean[j] - gm, 2);
    for (i = 0; i < k; i++) for (j = 0; j < n; j++) ssCells += r * Math.pow(cell[i][j] - gm, 2);
    var ssInt = ssCells - ssOp - ssPart, ssWithin = sst - ssCells;
    var dfOp = k - 1, dfPart = n - 1, dfInt = dfOp * dfPart, dfWithin = n * k * (r - 1);
    var ssErr = ssInt + ssWithin, dfErr = dfInt + dfWithin, msOp = ssOp / dfOp, msPart = ssPart / dfPart, msErr = ssErr / dfErr;
    out.anova = { ssOp: ssOp, ssPart: ssPart, ssErr: ssErr, sst: sst, dfOp: dfOp, dfPart: dfPart, dfErr: dfErr, dfT: n * k * r - 1,
                  msOp: msOp, msPart: msPart, msErr: msErr, fOp: msOp / msErr, fPart: msPart / msErr,
                  pOp: S.fSf(msOp / msErr, dfOp, dfErr), pPart: S.fSf(msPart / msErr, dfPart, dfErr) };
    Object.assign(out.anova, finish(Math.sqrt(msErr), Math.sqrt(Math.max(0, (msOp - msErr) / (n * r))),
                                    Math.sqrt(Math.max(0, (msPart - msErr) / (k * r)))));
    var msInt = ssInt / dfInt, msWithin = ssWithin / dfWithin;
    out.interaction = { ssOp: ssOp, ssPart: ssPart, ssInt: ssInt, ssWithin: ssWithin, dfInt: dfInt, dfWithin: dfWithin,
                        msOp: msOp, msPart: msPart, msInt: msInt, msWithin: msWithin, fInt: msInt / msWithin,
                        pInt: S.fSf(msInt / msWithin, dfInt, dfWithin) };
    return out;
  }

  /* ---------- confusion matrix (sheet_confusion.py; Naert Les 2 p. 29-32) ---------- */
  // m = [[a, b], [c, d]]: rows actual class 1 / 2, columns predicted class 1 / 2
  function confusion(m) {
    var a = m[0][0], b = m[0][1], c = m[1][0], d = m[1][1], N = a + b + c + d;
    if (!all(a, b, c, d) || !(N > 0)) return null;
    function metr(tp, fn, fp) {
      var rec = tp + fn ? tp / (tp + fn) : null, prec = tp + fp ? tp / (tp + fp) : null;
      return { recall: rec, precision: prec, f1: all(rec, prec) && rec + prec > 0 ? 2 * rec * prec / (rec + prec) : null };
    }
    var acc = (a + d) / N;
    return { N: N, accuracy: acc, error: 1 - acc, c1: metr(a, b, c), c2: metr(d, c, b) };
  }

  /* ---------- constant tables, as embedded by study/build_study.py (convention decision 4, tabel MSA.pdf) ---------- */
  function tables(data) {
    return {
      K: { get: function (sym, n) {
        var t = data.chart[sym];
        return t && num(n) && t[String(n)] !== undefined ? t[String(n)] : null;
      } },
      M: { d2: function (m) { var i = data.msa.m.indexOf(m); return i < 0 ? null : data.msa.d2[i]; },
           d2star: function (g, m) {
             var gi = data.msa.g.indexOf(g), mi = data.msa.m.indexOf(m);
             return gi < 0 || mi < 0 ? null : data.msa.d2star[gi][mi];
           } }
    };
  }

  return { tables: tables, normalSolve: normalSolve, normalBetween: normalBetween, normalKSigma: normalKSigma, normalCentral: normalCentral,
           quantiles: quantiles, pValues: pValues, describe: describe, oneMean: oneMean, twoMeansPooled: twoMeansPooled,
           paired: paired, oneProportion: oneProportion, twoProportions: twoProportions, oneVariance: oneVariance,
           twoVariances: twoVariances, bernoulli: bernoulli, binomial: binomial, hypergeometric: hypergeometric,
           poisson: poisson, exponential: exponential, uniform: uniform, contingency: contingency, defects: defects,
           sigmaFromDpmo: sigmaFromDpmo, dpmoFromSigma: dpmoFromSigma, yields: yields, rolled: rolled,
           rollDerived: rollDerived, yieldPower: yieldPower, perOpportunity: perOpportunity, cpLevel: cpLevel,
           capability: capability, capabilityInverse: capabilityInverse, limitsSummary: limitsSummary,
           subgroupChart: subgroupChart, individuals: individuals, attributeChart: attributeChart,
           samplingPoint: samplingPoint, samplingRisks: samplingRisks, aoql: aoql, variablesPlan: variablesPlan,
           regression: regression, anova1: anova1, factorial: factorial, aliases: aliases, grr: grr, confusion: confusion };
})();
if (typeof module !== 'undefined') module.exports = Calc;
