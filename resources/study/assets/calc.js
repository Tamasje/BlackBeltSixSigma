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
  // One mean (CI FR p. 3, 9-15; TH p. 12): everything the inputs allow. n with σ (z) or s (t) gives the standard
  // error; a distance d gives it in standard errors and P(|X̄ − µ| ≤ d); α gives the critical values and half widths
  // ("x̄ ± h", even before x̄ is known); x̄ gives the intervals; µ0 the tests. Missing inputs leave their part empty.
  function oneMean(n, xbar, s, sigma, mu0, alpha, d) {
    var a = num(alpha) && alpha > 0 && alpha < 1, known = num(n) && n >= 1;
    var out = { n: known ? n : null, xbar: num(xbar) ? xbar : null, df: known ? n - 1 : null };
    if (!known) return a ? out : null;   // α alone is enough for the z critical values
    function part(spread, df) {   // df null: z (σ known); a number: t with df
      var se = spread / Math.sqrt(n), cdf = function (x) { return df ? S.tCdf(x, df) : S.normCdf(x); }, r = { se: se };
      if (num(d) && d > 0) { r.k = d / se; r.within = 2 * cdf(r.k) - 1; r.beyond = 1 - cdf(r.k); }
      if (a) {
        r.c2 = df ? S.tInv(1 - alpha / 2, df) : S.normInv(1 - alpha / 2); r.c1 = df ? S.tInv(1 - alpha, df) : S.normInv(1 - alpha);
        r.half2 = r.c2 * se; r.half1 = r.c1 * se;
        if (num(xbar)) r.ci = intervals(xbar, se, r.c2, r.c1);
        if (num(xbar) && num(mu0)) r.test = tests((xbar - mu0) / se, df, alpha);
      }
      return r;
    }
    if (num(sigma) && sigma > 0) { out.z = part(sigma, null); out.seZ = out.z.se; out.ciZ = out.z.ci; out.testZ = out.z.test; }
    if (num(s) && s > 0 && n > 1) { out.t = part(s, n - 1); out.seT = out.t.se; out.ciT = out.t.ci; out.testT = out.t.test; }
    return out;
  }
  // Two independent means with the pooled s (CI FR p. 15; TR p. 5): s_p and the standard error from n and s of both
  // samples; with α the critical t and half width; with both means the interval and the test.
  function twoMeansPooled(n1, m1, s1, n2, m2, s2, d0, alpha) {
    // every result as soon as its own inputs are there: df from n1 and n2, the critical values from df and α,
    // the difference from the two means, s_p and the standard error from the n's and s's
    var a = num(alpha) && alpha > 0 && alpha < 1, out = {};
    if (all(m1, m2)) out.diff = m1 - m2;
    if (!all(n1, n2) || n1 + n2 <= 2) return Object.keys(out).length ? out : null;
    out.df = n1 + n2 - 2;
    if (a) { out.c2 = S.tInv(1 - alpha / 2, out.df); out.c1 = S.tInv(1 - alpha, out.df); }
    if (all(s1, s2)) {
      out.sp = Math.sqrt(((n1 - 1) * s1 * s1 + (n2 - 1) * s2 * s2) / out.df);
      out.se = out.sp * Math.sqrt(1 / n1 + 1 / n2);
      if (a) {
        out.half2 = out.c2 * out.se; out.half1 = out.c1 * out.se;
        if (num(out.diff)) {
          out.ci = intervals(out.diff, out.se, out.c2, out.c1);
          out.test = tests((out.diff - (num(d0) ? d0 : 0)) / out.se, out.df, alpha);
        }
      }
    }
    return out;
  }
  // Paired observations: the differences as one sample (CI FR p. 17-18): s.e. and df from n and s_v; α adds the
  // critical t and half width; v̄ the interval and the test.
  function paired(n, dbar, sd, d0, alpha) {
    if (!num(n) || n < 2) return null;
    var a = num(alpha) && alpha > 0 && alpha < 1, out = { df: n - 1, dbar: num(dbar) ? dbar : null };
    if (a) { out.c2 = S.tInv(1 - alpha / 2, out.df); out.c1 = S.tInv(1 - alpha, out.df); }
    if (num(sd) && sd > 0) {
      out.se = sd / Math.sqrt(n);
      if (a) {
        out.half2 = out.c2 * out.se; out.half1 = out.c1 * out.se;
        if (num(dbar)) {
          out.ci = intervals(dbar, out.se, out.c2, out.c1);
          out.test = tests((dbar - (num(d0) ? d0 : 0)) / out.se, out.df, alpha);
        }
      }
    }
    return out;
  }
  // One proportion (CI p. 20; Test Recipes p. 9-10): with π0 the test's standard error under H0 (and with α the critical p);
  // with x the estimate and its standard error; with α also the intervals; with π0 and α the Z-test.
  function oneProportion(n, x, pi0, alpha) {
    var a = num(alpha) && alpha > 0 && alpha < 1;
    if (!num(n) || n <= 0) return a ? { c2: S.normInv(1 - alpha / 2), c1: S.normInv(1 - alpha) } : null;   // α alone gives z
    var h0 = num(pi0) && pi0 > 0 && pi0 < 1, out = {};
    var z2 = a ? S.normInv(1 - alpha / 2) : null, z1 = a ? S.normInv(1 - alpha) : null;
    if (a) { out.c2 = z2; out.c1 = z1; }
    if (h0) {
      out.se0 = Math.sqrt(pi0 * (1 - pi0) / n);
      out.condition = n * pi0 > 5;
      if (a) out.critical = { ne: [pi0 - z2 * out.se0, pi0 + z2 * out.se0], gt: pi0 + z1 * out.se0, lt: pi0 - z1 * out.se0 };
    }
    if (num(x) && x >= 0 && x <= n) {
      var p = x / n, se = Math.sqrt(p * (1 - p) / n);
      out.p = p; out.se = se;
      if (a) {
        out.ci = intervals(p, se, z2, z1);
        // exact (Clopper-Pearson) = R binom.test, CI Further Reading p. 20; BETA.INV as in the workbook
        out.exact = {
          two: [x === 0 ? 0 : S.betaInv(alpha / 2, x, n - x + 1), x === n ? 1 : S.betaInv(1 - alpha / 2, x + 1, n - x)],
          lower: [x === 0 ? 0 : S.betaInv(alpha, x, n - x + 1), Infinity],
          upper: [0, x === n ? 1 : S.betaInv(1 - alpha, x + 1, n - x)]
        };
      }
      if (a && h0) out.test = tests((p - pi0) / out.se0, null, alpha);
    }
    return Object.keys(out).length ? out : null;
  }
  // Two proportions: with x1 and x2 the difference and its standard error; with α also the intervals.
  function twoProportions(n1, x1, n2, x2, alpha) {
    var a = num(alpha) && alpha > 0 && alpha < 1, out = {};
    var ok1 = all(n1, x1) && n1 > 0, ok2 = all(n2, x2) && n2 > 0;
    if (ok1) out.p1 = x1 / n1;
    if (ok2) out.p2 = x2 / n2;
    if (ok1 && ok2) {
      out.diff = out.p1 - out.p2;
      out.se = Math.sqrt(out.p1 * (1 - out.p1) / n1 + out.p2 * (1 - out.p2) / n2);
    }
    if (a) {
      out.c2 = S.normInv(1 - alpha / 2); out.c1 = S.normInv(1 - alpha);
      if (num(out.se)) out.ci = intervals(out.diff, out.se, out.c2, out.c1);
    }
    return Object.keys(out).length ? out : null;
  }

  /* ---------- variances (sheet_variance.py) ---------- */
  // One variance (CI FR p. 21; TR p. 11): with n and α the χ² critical values; with σ0 also the s beyond which H0 is
  // rejected; with s the intervals and the test.
  function oneVariance(n, s, sigma0, alpha) {
    if (!num(n) || n < 2) return null;
    var df = n - 1, out = { df: df };
    var a = num(alpha) && alpha > 0 && alpha < 1;
    if (a) out.crit = { lo2: S.chi2Inv(alpha / 2, df), hi2: S.chi2Isf(alpha / 2, df), lo1: S.chi2Inv(alpha, df), hi1: S.chi2Isf(alpha, df) };
    if (a && num(sigma0) && sigma0 > 0) {   // (n − 1)s²/σ0² beyond a critical value  ⇔  s beyond σ0·√(χ²/(n − 1))
      var sAt = function (x) { return sigma0 * Math.sqrt(x / df); };
      out.sLimits = { ne: [sAt(out.crit.lo2), sAt(out.crit.hi2)], gt: sAt(out.crit.hi1), lt: sAt(out.crit.lo1) };
    }
    if (!num(s) || s <= 0) return out;
    var q = df * s * s;
    out.s2 = s * s;
    if (a) out.ci = { two: [q / out.crit.hi2, q / out.crit.lo2], lower: [q / out.crit.hi1, Infinity], upper: [0, q / out.crit.lo1] };
    if (a && num(sigma0) && sigma0 > 0) {
      var x2 = q / (sigma0 * sigma0), lo = S.chi2Cdf(x2, df), hi = S.chi2Sf(x2, df), two = 2 * Math.min(lo, hi);
      out.test = { stat: x2,
                   ne: { crit: [out.crit.lo2, out.crit.hi2], p: two, d: decide(two, alpha) },
                   gt: { crit: [out.crit.hi1], p: hi, d: decide(hi, alpha) },
                   lt: { crit: [out.crit.lo1], p: lo, d: decide(lo, alpha) } };
    }
    return out;
  }
  // Two variances (TR p. 12-14; exam Q2): with n1, n2 and α the F critical values; with s1 and s2 the ratio, the
  // intervals in both orientations and the F-test.
  function twoVariances(n1, s1, n2, s2, alpha) {
    var a = num(alpha) && alpha > 0 && alpha < 1, out = {};
    var sOk = all(s1, s2) && s1 > 0 && s2 > 0, nOk = all(n1, n2) && n1 >= 2 && n2 >= 2;
    if (sOk) out.F = s1 * s1 / (s2 * s2);   // the ratio needs no n
    if (nOk) {
      out.v1 = n1 - 1; out.v2 = n2 - 1;
      if (a) out.crit = { lo2: S.fInv(alpha / 2, out.v1, out.v2), hi2: S.fIsf(alpha / 2, out.v1, out.v2),
                          lo1: S.fInv(alpha, out.v1, out.v2), hi1: S.fIsf(alpha, out.v1, out.v2) };
    }
    if (!(sOk && nOk && a)) return Object.keys(out).length ? out : null;
    var F = out.F, v1 = out.v1, v2 = out.v2, c = out.crit;
    var ci = { two: [F / c.hi2, F / c.lo2], lower: [F / c.hi1, Infinity], upper: [0, F / c.lo1] };
    var inv = function (r) { return [r[1] === Infinity ? 0 : 1 / r[1], r[0] === 0 ? Infinity : 1 / r[0]]; };
    var lo = S.fCdf(F, v1, v2), hi = S.fSf(F, v1, v2), two = 2 * Math.min(lo, hi);
    out.ci = ci; out.ciInv = { two: inv(ci.two), lower: inv(ci.upper), upper: inv(ci.lower) };
    out.test = { stat: F,
                 ne: { crit: [c.lo2, c.hi2], p: two, d: decide(two, alpha) },
                 gt: { crit: [c.hi1], p: hi, d: decide(hi, alpha) },
                 lt: { crit: [c.lo1], p: lo, d: decide(lo, alpha) } };
    return out;
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

  // A cross table read from pasted text (Data p. 17–25). Counts: one row per line, names allowed in the first row and
  // the first column. Raw data: one observation per line, the category of X then the category of Y. Excel pastes
  // columns separated by tabs, so names may contain spaces there; otherwise spaces or ';' separate. A row or column
  // named totaal/total is left out: the margins are always recomputed from the cells.
  var TOTAL = /^(totaal|total|som|sum)$/i;
  function cellsOf(line) {
    var cells = line.indexOf('\t') >= 0 ? line.split('\t') : line.trim().split(/[\s;]+/);
    cells = cells.map(function (c) { return c.trim(); });
    while (cells.length && cells[cells.length - 1] === '') cells.pop();
    return cells;
  }
  function count(text) {
    var t = String(text).replace(/\s/g, '');
    return /^\+?\d+([.,]\d+)?$/.test(t) ? parseFloat(t.replace(',', '.')) : NaN;
  }
  function crossTable(text, raw, header) {
    var lines = String(text || '').split('\n').filter(function (l) { return l.trim() !== ''; }).map(cellsOf);
    if (!lines.length) return null;
    var names = null, dropped = [];
    if (raw) {
      if (header) { names = lines[0].slice(0, 2); lines = lines.slice(1); }
      var bad = lines.filter(function (c) { return c.length !== 2; });
      if (bad.length) return { error: 'ruwe data: elke regel precies twee categorieën (X en Y); kopieer uit Excel (tabs) als een naam spaties bevat. Niet gelezen: ' + bad[0].join(' ') };
      var rowLabels = [], colLabels = [], counts = [];
      lines.forEach(function (c) {
        if (rowLabels.indexOf(c[0]) < 0) { rowLabels.push(c[0]); counts.push(colLabels.map(function () { return 0; })); }
        if (colLabels.indexOf(c[1]) < 0) { colLabels.push(c[1]); counts.forEach(function (r) { r.push(0); }); }
        counts[rowLabels.indexOf(c[0])][colLabels.indexOf(c[1])]++;
      });
      return { rowLabels: rowLabels, colLabels: colLabels, counts: counts, names: names, dropped: dropped };
    }
    var head = lines[0].every(function (c) { return isNaN(count(c)); }) ? lines.shift() : null;
    var rows = lines.map(function (c) { return isNaN(count(c[0])) ? { label: c[0], values: c.slice(1) } : { label: null, values: c }; });
    if (!rows.length) return { error: 'geen rij met aantallen gevonden' };
    var C = rows[0].values.length;
    if (rows.some(function (r) { return r.values.length !== C; })) return { error: 'elke rij moet evenveel aantallen hebben' };
    var unread = [].concat.apply([], rows.map(function (r) { return r.values; })).filter(function (c) { return isNaN(count(c)); });
    if (unread.length) return { error: 'geen aantal (alleen getallen ≥ 0 in de cellen): ' + unread.slice(0, 3).join(' ') };
    if (head && head.length === C + 1) head = head.slice(1);   // the corner cell above the row names
    if (head && head.length !== C) return { error: 'de eerste regel heeft ' + head.length + ' namen voor ' + C + ' kolommen' };
    var cols = (head || []).length ? head : rows[0].values.map(function (_, j) { return 'kolom ' + (j + 1); });
    var keepCol = cols.map(function (c) { return !TOTAL.test(c); });
    cols.forEach(function (c, j) { if (!keepCol[j]) dropped.push('kolom ' + c); });
    var kept = rows.filter(function (r) { if (r.label && TOTAL.test(r.label)) { dropped.push('rij ' + r.label); return false; } return true; });
    return { rowLabels: kept.map(function (r, i) { return r.label || 'rij ' + (i + 1); }),
             colLabels: cols.filter(function (_, j) { return keepCol[j]; }),
             counts: kept.map(function (r) { return r.values.map(count).filter(function (_, j) { return keepCol[j]; }); }),
             names: null, dropped: dropped };
  }
  // An event on one variable of the table: 'r:i' (X = row i), 'r!:i' (X ≠ row i), 'c:j', 'c!:j'; '' = no condition.
  function eventCells(spec) {
    var m = /^([rc])(!?):(\d+)$/.exec(spec || '');
    if (!m) return function () { return true; };
    var k = +m[3], not = m[2] === '!';
    return function (i, j) { return ((m[1] === 'r' ? i : j) === k) !== not; };
  }
  // P(E), P(G), P(E en G), P(E | G) = n(E en G)/n(G) and P(G | E) for two events of a cross table (Data p. 20, 25)
  function conditional(counts, event, given) {
    if (!/^[rc]!?:\d+$/.test(event || '')) return null;
    var e = eventCells(event), g = eventCells(given), N = 0, nE = 0, nG = 0, nEG = 0;
    counts.forEach(function (row, i) {
      row.forEach(function (x, j) {
        N += x;
        if (e(i, j)) nE += x;
        if (g(i, j)) nG += x;
        if (e(i, j) && g(i, j)) nEG += x;
      });
    });
    if (!(N > 0)) return null;
    var out = { N: N, nE: nE, nG: nG, nEG: nEG, pE: nE / N, pG: nG / N, pEG: nEG / N,
                pEgivenG: nG > 0 ? nEG / nG : null, pGgivenE: nE > 0 ? nEG / nE : null };
    out.product = out.pE * out.pG;
    out.independent = Math.abs(out.pEG - out.product) <= 1e-12;
    return out;
  }
  // Independence of X and Y in the table itself (Data p. 22, 25): P(Y | X = x) = P(Y) for every row, i.e. every
  // joint probability equals P(X)·P(Y). Returns the cell where P(Y | X = x) differs most from P(Y).
  function independence(counts) {
    var c = contingency(counts);
    if (!c) return null;
    var worst = null;
    counts.forEach(function (row, i) {
      row.forEach(function (_, j) {
        if (c.rowTotals[i] === 0) return;
        var d = Math.abs(c.colGivenRow[i][j] - c.pCol[j]);
        if (!worst || d > worst.diff) worst = { i: i, j: j, diff: d, conditional: c.colGivenRow[i][j], marginal: c.pCol[j] };
      });
    });
    return { table: c, worst: worst, independent: !worst || worst.diff <= 1e-12 };
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
      r.capable = r.cpk >= 1.33 ? 'ja' : 'nee';  // SPC p. 41: Cpk = 1,33 is 'Good'
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
    var d2 = K.get('d2', inp.n), c4 = K.get('c4', inp.n);
    if (num(inp.rbar) && num(d2)) add('rbar_d2', 'R̄ / d2 (korte termijn)', inp.rbar / d2, 'd2(' + inp.n + ') = ' + d2);
    if (num(inp.sbar)) add('sbar', 's̄ rechtstreeks (zoals SPC p. 46)', inp.sbar, null);
    if (num(inp.sbar) && num(c4)) add('sbar_c4', 's̄ / c4 (zuiver)', inp.sbar / c4, 'c4(' + inp.n + ') = ' + c4);
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
  // 2^k design given only its estimated effects (DOE p. 75–77): SS = n·2^(k−2)·effect²; the effects of an order from
  // `poolFrom` on are pooled into the error (df = their number); every other effect is tested with F(1; df)
  function effectsAnova(effects, k, n, poolFrom, alpha) {
    if (!effects || !effects.length || !num(k) || k < 1) return null;
    var reps = num(n) && n >= 1 ? n : 1, factor = reps * Math.pow(2, k - 2), a = num(alpha) && alpha > 0 && alpha < 1;
    var rows = effects.map(function (e) {
      return { name: e.name, order: e.name.length, effect: e.value, ss: factor * e.value * e.value, pooled: num(poolFrom) && e.name.length >= poolFrom };
    });
    var pooled = rows.filter(function (r) { return r.pooled; }), out = { rows: rows, factor: factor };
    if (!pooled.length) return out;
    out.df = pooled.length; out.ssPool = pooled.reduce(function (s, r) { return s + r.ss; }, 0); out.mse = out.ssPool / out.df;
    if (a) out.crit = S.fIsf(alpha, 1, out.df);
    rows.forEach(function (r) {
      if (r.pooled) return;
      r.F = r.ss / out.mse; r.p = S.fSf(r.F, 1, out.df);
      if (a) r.significant = r.p < alpha;
    });
    return out;
  }
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
  // A new subgroup size on the same process (SPC p. 85, exercise 4): σ̂ = R̄/d2(n_old) stays, so R̄_new = d2(n_new)·σ̂ and
  // the limits are X̿ ± A2·R̄_new, D3·R̄_new … D4·R̄_new. A shift of k·σ moves x̄ by k·√n standard errors; the first
  // sample falls outside the 3σ limits with probability 1 − [Φ(3 − k√n) − Φ(−3 − k√n)] (the limits are exactly 3σ/√n).
  function newSampleSize(xbarbar, rbar, nOld, sigma, nNew, shift, K) {
    var out = {};
    var sigmaHat = num(sigma) && sigma > 0 ? sigma : (all(rbar, nOld) && num(K.get('d2', nOld)) ? rbar / K.get('d2', nOld) : null);
    if (num(sigmaHat)) out.sigma = sigmaHat;
    if (!num(nNew) || nNew < 2) return Object.keys(out).length ? out : null;
    out.n = nNew;
    if (num(sigmaHat)) out.sigmaXbar = sigmaHat / Math.sqrt(nNew);
    ['d2', 'A2', 'D3', 'D4'].forEach(function (s) { out[s] = K.get(s, nNew); });
    if (num(sigmaHat) && num(out.d2)) {
      out.rbar = out.d2 * sigmaHat;
      if (all(out.D3, out.D4)) out.R = [out.D3 * out.rbar, out.rbar, out.D4 * out.rbar];
      if (num(xbarbar) && num(out.A2)) out.xbar = [xbarbar - out.A2 * out.rbar, xbarbar, xbarbar + out.A2 * out.rbar];
    }
    if (num(shift)) {   // needs no data at all: only the shift in σ and the subgroup size
      out.delta = shift * Math.sqrt(nNew);
      out.pOut = 1 - (S.normCdf(3 - out.delta) - S.normCdf(-3 - out.delta));
      out.arl = out.pOut > 0 ? 1 / out.pOut : null;
    }
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
    // the four z values as soon as each is known; k, n and the OC values need all four inputs and AQL < LQL
    var z = S.normInv, out = {}, ok = function (x) { return num(x) && x > 0 && x < 1; };
    if (ok(p0)) out.zP0 = z(p0);
    if (ok(pt)) out.zPt = z(pt);
    if (ok(alpha)) { out.zA = z(alpha); out.zA1 = z(1 - alpha); }
    if (ok(beta)) { out.zB = z(beta); out.zB1 = z(1 - beta); }
    if (!(ok(p0) && ok(pt) && ok(alpha) && ok(beta)) || pt <= p0) return Object.keys(out).length ? out : null;
    var k = (z(pt) * z(alpha) + z(p0) * z(beta)) / (z(1 - alpha) + z(1 - beta));
    var n = Math.pow(z(1 - alpha) + z(1 - beta), 2) * (1 + k * k / 2) / Math.pow(z(pt) - z(p0), 2), nUp = Math.ceil(n - 1e-9);
    var oc = function (p) { return 1 - S.normCdf((z(p) + k) * Math.sqrt(nUp) / Math.sqrt(1 + k * k / 2)); };
    out.k = k; out.n = n; out.nUp = nUp; out.ocAql = oc(p0); out.ocLql = oc(pt);
    return out;
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

  /* ---------- Les 2 (Ottoy): sample size, tolerance intervals, β/power, χ² frequency tests, rank tests ---------- */
  // sample size from the CI formulas (CI p. 10, CI FR p. 3) solved for n; W = FULL width (CI p. 7 footnote)
  function sampleSize(alpha, W, p, sigma) {
    if (!all(alpha, W) || W <= 0 || alpha <= 0 || alpha >= 1) return null;
    var z = S.normInv(1 - alpha / 2), out = { z: z };
    var up = function (x) { return Math.ceil(x - 1e-9); };
    var pp = num(p) ? p : 0.5;
    if (pp > 0 && pp < 1) {
      out.p = pp; out.nProp = Math.pow(2 * z * Math.sqrt(pp * (1 - pp)) / W, 2); out.nPropUp = up(out.nProp);
      out.widthProp = 2 * z * Math.sqrt(pp * (1 - pp) / out.nPropUp); out.defectives = out.nPropUp * pp;
    }
    if (num(sigma) && sigma > 0) {
      out.nMean = Math.pow(2 * z * sigma / W, 2); out.nMeanUp = up(out.nMean);
      out.widthMean = 2 * z * sigma / Math.sqrt(out.nMeanUp);
    }
    return out;
  }
  // t(α, β, n) of CI FR p. 23 / AS p. 27 with zA = z(1−α), zB = z(1−β); the variables plan uses zA = z(α) (AS p. 27 notes)
  function toleranceFactor(zA, zB, n) {
    var d = 1 - zA * zA / (2 * n), r = 1 / n + zB * zB / (2 * n) - zA * zA / (2 * n * n);
    return d > 0 && r >= 0 ? (zB + zA * Math.sqrt(r)) / d : null;
  }
  // Tolerance factors (CI FR p. 22-23) from n, α and β alone; with Ȳ and σ (or s) also the limits.
  function tolerance(n, mean, sd, alpha, beta, known) {
    if (!all(n, alpha, beta) || n < 2) return null;
    var z = S.normInv, k1, k2;
    if (known) { k1 = z(1 - alpha) / Math.sqrt(n) + z(1 - beta); k2 = z(1 - alpha / 2) / Math.sqrt(n) + z(1 - beta / 2); }
    else { k1 = toleranceFactor(z(1 - alpha), z(1 - beta), n); k2 = toleranceFactor(z(1 - alpha / 2), z(1 - beta / 2), n); }
    var ok = all(mean, sd) && sd > 0;
    return { k1: k1, ltl: ok && num(k1) ? mean - k1 * sd : null, utl: ok && num(k1) ? mean + k1 * sd : null,
             k2: k2, two: ok && num(k2) ? [mean - k2 * sd, mean + k2 * sd] : null };
  }
  // distribution-free [x(1); x(n)] (CI FR p. 23): smallest n with (1 − β/2)^n − ½(1 − β)^n ≤ α/2
  function toleranceFree(alpha, beta, n) {
    if (!all(alpha, beta) || beta <= 0 || beta >= 1) return null;
    var f = function (m) { return Math.pow(1 - beta / 2, m) - 0.5 * Math.pow(1 - beta, m); }, m = 1;
    while (f(m) > alpha / 2 + 1e-15 && m < 1e6) m++;
    var out = { nMin: m };
    if (num(n) && n >= 1) out.confidence = 1 - 2 * Math.pow(1 - beta / 2, n) + Math.pow(1 - beta, n);
    return out;
  }
  // β and power of the Z-test for µ (TH FR p. 7–9, 14): critical values on the H0 distribution, β under the true mean
  function powerMean(mu0, mu1, sigma, n, alpha, targetBeta) {
    // each result as soon as its inputs are there: z from α, σ/√n from σ and n, the critical x̄ with µ0 added,
    // β and the power with µ1 added, and the n for a target β needs no n at all
    var a = num(alpha) && alpha > 0 && alpha < 1, sOk = num(sigma) && sigma > 0, out = {}, F = S.normCdf;
    var z1 = a ? S.normInv(1 - alpha) : null, z2 = a ? S.normInv(1 - alpha / 2) : null;
    if (a) { out.z1 = z1; out.z2 = z2; }
    if (sOk && num(n) && n > 0) out.se = sigma / Math.sqrt(n);
    if (a && num(out.se) && num(mu0)) {
      var se = out.se, gt = mu0 + z1 * se, lt = mu0 - z1 * se, lo = mu0 - z2 * se, hi = mu0 + z2 * se;
      out.gt = { crit: [gt] }; out.lt = { crit: [lt] }; out.ne = { crit: [lo, hi] };   // critical x̄ without µ1
      if (num(mu1)) {
        out.gt.beta = F((gt - mu1) / se); out.lt.beta = 1 - F((lt - mu1) / se); out.ne.beta = F((hi - mu1) / se) - F((lo - mu1) / se);
        ['gt', 'lt', 'ne'].forEach(function (s) { out[s].power = 1 - out[s].beta; });
      }
    }
    if (a && sOk && all(mu0, mu1) && mu1 !== mu0 && num(targetBeta) && targetBeta > 0 && targetBeta < 1) {
      out.nOneSided = Math.pow((z1 + S.normInv(1 - targetBeta)) * sigma / Math.abs(mu1 - mu0), 2);
      out.nOneSidedUp = Math.ceil(out.nOneSided - 1e-9);
    }
    return Object.keys(out).length ? out : null;
  }
  // β of the Z-test for π (guide ex-05-12: π0 under the root for the critical value, π1 for the true distribution)
  function powerProportion(pi0, pi1, n, alpha, targetBeta) {
    // each result as soon as its inputs are there: z from α, the standard error and the condition from π0 and n,
    // the critical p with α added, β and the power with π1 added, and the n for a target β needs no n
    var a = num(alpha) && alpha > 0 && alpha < 1, F = S.normCdf, out = {};
    var p0 = num(pi0) && pi0 > 0 && pi0 < 1, p1 = num(pi1) && pi1 > 0 && pi1 < 1, nOk = num(n) && n > 0;
    var z1 = a ? S.normInv(1 - alpha) : null;
    function betas(m) {
      var se0 = Math.sqrt(pi0 * (1 - pi0) / m), se1 = Math.sqrt(pi1 * (1 - pi1) / m);
      var cg = pi0 + z1 * se0, cl = pi0 - z1 * se0;
      return { gt: { crit: cg, beta: F((cg - pi1) / se1) }, lt: { crit: cl, beta: 1 - F((cl - pi1) / se1) } };
    }
    if (a) out.z1 = z1;
    if (p0 && nOk) { out.se0 = Math.sqrt(pi0 * (1 - pi0) / n); out.condition = n * pi0 > 5; }
    if (a && p0 && nOk) {
      out.gt = { crit: pi0 + z1 * out.se0 }; out.lt = { crit: pi0 - z1 * out.se0 };
      if (p1) {
        var b = betas(n);
        out.gt.beta = b.gt.beta; out.lt.beta = b.lt.beta;
        out.gt.power = 1 - out.gt.beta; out.lt.power = 1 - out.lt.beta;
      }
    }
    if (a && p0 && p1 && num(targetBeta) && targetBeta > 0 && targetBeta < 1 && pi1 !== pi0) {
      var root = (z1 * Math.sqrt(pi0 * (1 - pi0)) + S.normInv(1 - targetBeta) * Math.sqrt(pi1 * (1 - pi1))) / Math.abs(pi1 - pi0);
      out.nFormula = root * root;
      var side = pi1 > pi0 ? 'gt' : 'lt', m = Math.max(1, Math.floor(out.nFormula) - 5);
      while (betas(m)[side].beta >= targetBeta && m < 1e7) m++;   // strict "<": "kleiner dan" (TH FR p. 22)
      out.nSearch = m;
    }
    return Object.keys(out).length ? out : null;
  }
  // χ² goodness of fit (TR p. 15–17): expected e_k = n·π_k, df = r − g − 1, right tail
  function chi2Fit(observed, expected, g, alpha) {
    if (!observed || !expected || observed.length !== expected.length || observed.length < 2) return null;
    var n = observed.reduce(function (a, b) { return a + b; }, 0), es = expected.reduce(function (a, b) { return a + b; }, 0);
    var e = expected.map(function (x) { return Math.abs(es - 1) < 1e-6 ? x * n : x * n / es; });   // probabilities or counts
    var chi2 = 0;
    observed.forEach(function (o, i) { chi2 += (o - e[i]) * (o - e[i]) / e[i]; });
    var df = observed.length - (num(g) ? g : 0) - 1;
    return { n: n, e: e, chi2: chi2, df: df, p: df > 0 ? S.chi2Sf(chi2, df) : null,
             crit: df > 0 && num(alpha) ? S.chi2Isf(alpha, df) : null, small: e.filter(function (x) { return x <= 5; }).length };
  }
  // χ² test of independence (TR p. 18–20): e_kl = n_k.·n_.l/n, df = (r − 1)(s − 1); Yates for a 2×2 table
  function chi2Table(rows, alpha) {
    var c = contingency(rows);
    if (!c) return null;
    var R = rows.length, C = rows[0].length, chi2 = 0, yates = 0, e = [], i, j;
    for (i = 0; i < R; i++) {
      e.push([]);
      for (j = 0; j < C; j++) {
        var ex = c.rowTotals[i] * c.colTotals[j] / c.N, d = Math.abs(rows[i][j] - ex);
        e[i].push(ex); chi2 += d * d / ex; yates += Math.pow(Math.max(0, d - 0.5), 2) / ex;
      }
    }
    var df = (R - 1) * (C - 1), small = [].concat.apply([], e).filter(function (x) { return x <= 5; }).length;
    var out = { e: e, chi2: chi2, df: df, p: S.chi2Sf(chi2, df), crit: num(alpha) ? S.chi2Isf(alpha, df) : null, small: small };
    if (R === 2 && C === 2) { out.yates = yates; out.pYates = S.chi2Sf(yates, 1); }
    return out;
  }
  function avgRanks(values) {   // average ranks for ties (TR p. 22, 24)
    var idx = values.map(function (v, i) { return [v, i]; }).sort(function (a, b) { return a[0] - b[0]; }), ranks = [];
    for (var i = 0; i < idx.length;) {
      var j = i;
      while (j + 1 < idx.length && idx[j + 1][0] === idx[i][0]) j++;
      for (var q = i; q <= j; q++) ranks[idx[q][1]] = (i + j) / 2 + 1;
      i = j + 1;
    }
    return ranks;
  }
  function zSides(stat, mean, sd) {   // z without and with continuity correction (half a unit towards the mean)
    var z = (stat - mean) / sd, cc = stat > mean ? stat - 0.5 : (stat < mean ? stat + 0.5 : stat), zc = (cc - mean) / sd;
    var p = function (x) { return { left: S.normCdf(x), right: S.normCdf(-x), two: 2 * S.normCdf(-Math.abs(x)) }; };
    return { z: z, p: p(z), zcc: zc, pcc: p(zc) };
  }
  // Wilcoxon-Mann-Whitney (TR p. 21–22): W = rank sum of sample 1, E = n1(N + 1)/2, σ² = n1 n2 (N + 1)/12 (no tie correction)
  function rankSum(x1, x2) {
    if (!x1 || !x2 || x1.length < 1 || x2.length < 1) return null;
    var n1 = x1.length, n2 = x2.length, N = n1 + n2, ranks = avgRanks(x1.concat(x2)), W = 0;
    for (var i = 0; i < n1; i++) W += ranks[i];
    var mean = n1 * (N + 1) / 2, sd = Math.sqrt(n1 * n2 * (N + 1) / 12), out = zSides(W, mean, sd);
    out.W = W; out.mean = mean; out.sd = sd; out.n1 = n1; out.n2 = n2; out.ranks1 = ranks.slice(0, n1); out.small = n1 <= 10 || n2 <= 10;
    return out;
  }
  // Wilcoxon signed ranks (TR p. 23–24): drop v = 0, rank |v|, T+ = sum of ranks of v > 0
  function signedRank(diffs) {
    var v = (diffs || []).filter(function (x) { return x !== 0; });
    if (v.length < 2) return null;
    var n = v.length, ranks = avgRanks(v.map(Math.abs)), T = 0;
    v.forEach(function (x, i) { if (x > 0) T += ranks[i]; });
    var mean = n * (n + 1) / 4, sd = Math.sqrt(n * (n + 1) * (2 * n + 1) / 24), out = zSides(T, mean, sd);
    out.T = T; out.n = n; out.dropped = diffs.length - n; out.mean = mean; out.sd = sd; out.small = n <= 15;
    return out;
  }
  // runs test (TR p. 25–26): runs on either side of the median; values equal to the median left out (course silent)
  function runsTest(xs) {
    if (!xs || xs.length < 3) return null;
    var med = median(xs), signs = xs.filter(function (x) { return x !== med; }).map(function (x) { return x > med ? '+' : '−'; });
    var n = signs.length, R = n ? 1 : 0;
    for (var i = 1; i < n; i++) if (signs[i] !== signs[i - 1]) R++;
    var mean = (n + 2) / 2, sd = Math.sqrt((n - 1) / 4), out = zSides(R, mean, sd);
    out.median = med; out.signs = signs.join(''); out.n = n; out.dropped = xs.length - n; out.R = R; out.mean = mean; out.sd = sd;
    return out;
  }

  /* ---------- Les 2: sampling methods (AS p. 16–19) ---------- */
  function samplingVariance(piA, piB, wA, n) {
    // each result as soon as its inputs are there: σ² per stratum from π, SRS with π_A alone, the stratified
    // variance and the allocations with both strata, the weights and n
    var out = {}, nOk = num(n) && n > 0;
    if (num(piA)) out.sA2 = piA * (1 - piA);
    if (num(piB)) out.sB2 = piB * (1 - piB);
    if (!num(piB)) {   // one population: simple random sampling
      if (num(piA) && nOk) out.srs = piA * (1 - piA) / n;
      return Object.keys(out).length ? out : null;
    }
    if (all(piA, wA)) {
      var wB = 1 - wA;
      out.pi = wA * piA + wB * piB; out.sigma2 = out.pi * (1 - out.pi);
      if (nOk) {
        out.strat = (wA * out.sA2 + wB * out.sB2) / n;
        out.srs = (wA * out.sA2 + wB * out.sB2 + wA * wB * (piA - piB) * (piA - piB)) / n;
        out.nAprop = wA * n;
        out.nAopt = wA * Math.sqrt(out.sA2) / (wA * Math.sqrt(out.sA2) + wB * Math.sqrt(out.sB2)) * n;
        out.nBopt = n - out.nAopt;
      }
    }
    return Object.keys(out).length ? out : null;
  }
  function samplingMeans(muA, muB, s2, n) {   // two equal normal strata, W = ½ (AS p. 19 notes)
    // µ from the two means; σ² of the population with σ_S²; the variances of x̄ also need n
    var out = {};
    if (all(muA, muB)) out.mu = (muA + muB) / 2;
    if (all(muA, muB, s2)) out.sigma2 = s2 + (muA - muB) * (muA - muB) / 4;
    if (num(s2) && num(n) && n > 0) out.strat = s2 / n;
    if (all(muA, muB, s2, n) && n > 0) out.srs = s2 / n + (muA - muB) * (muA - muB) / (4 * n);
    return Object.keys(out).length ? out : null;
  }

  /* ---------- Les 2: more acceptance sampling (AS FR p. 4–11, 13–15; AS p. 26–27) ---------- */
  function inverseOC(n, c, target) {   // p with OC(p) = target, binomial; OC decreases in p
    if (!all(n, c, target) || target <= 0 || target >= 1 || c < 0 || c >= n) return null;
    if (c === 0) return 1 - Math.pow(target, 1 / n);
    var lo = 0, hi = 1;
    for (var i = 0; i < 200; i++) { var mid = (lo + hi) / 2; if (S.binomCdf(c, n, mid) > target) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  }
  // smallest c whose minimal-n plan meets both risks (binomial, non-strict); the guide's search for AS FR p. 17
  function planSearch(aql, lql, alpha, beta) {
    if (!all(aql, lql, alpha, beta) || !(aql < lql)) return null;
    for (var c = 0; c <= 200; c++) {
      var n = c + 1;
      while (S.binomCdf(c, n, lql) > beta && n <= 20000) n++;
      if (n > 20000) return null;
      if (S.binomCdf(c, n, aql) >= 1 - alpha) {
        var nMax = n;
        while (S.binomCdf(c, nMax + 1, aql) >= 1 - alpha && S.binomCdf(c, nMax + 1, lql) <= beta) nMax++;
        return { n: n, c: c, nMax: nMax, ocAql: S.binomCdf(c, n, aql), ocLql: S.binomCdf(c, n, lql), r0: lql / aql };
      }
    }
    return null;
  }
  // double plan (n1, c1, c2) + (n2, c3) of AS FR p. 5: accept X1 ≤ c1, reject X1 ≥ c2, else accept if X1 + X2 ≤ c3
  function doublePlan(n1, c1, c2, n2, c3, p, N) {
    // each result as soon as its inputs are there: P(X1 ≤ c1) needs n1, c1, p; P(X1 ≥ c2) needs n1, c2, p;
    // Π needs both; OC and ASN also need n2 and c3
    if (!all(n1, p)) return null;
    var lot = num(N) && N >= n1 + (num(n2) ? n2 : 0), M = lot ? Math.floor(N * p + 1e-9) : null, out = { hyper: lot };
    var pmf1 = function (j) { return lot ? S.hypergeomPmf(j, N, M, n1) : S.binomPmf(j, n1, p); };
    var cdf1 = function (j) { return lot ? S.hypergeomCdf(j, N, M, n1) : S.binomCdf(j, n1, p); };
    var cdf2 = function (k, j) { return k < 0 ? 0 : (lot ? S.hypergeomCdf(k, N - n1, M - j, n2) : S.binomCdf(k, n2, p)); };
    if (num(c1)) out.acc1 = cdf1(c1);
    if (num(c2)) out.rej1 = 1 - cdf1(c2 - 1);
    if (num(out.acc1) && num(out.rej1) && c1 < c2) {
      out.decided1 = out.acc1 + out.rej1;
      if (all(n2, c3)) {
        out.oc = out.acc1;
        for (var j = c1 + 1; j <= c2 - 1; j++) out.oc += pmf1(j) * cdf2(c3 - j, j);
        out.asn = n1 * out.decided1 + (n1 + n2) * (1 - out.decided1);
      }
    }
    return num(out.acc1) || num(out.rej1) ? out : null;
  }
  // SPRT for attributes (AS FR p. 6–8)
  function sprt(p0, pt, alpha, beta, n, x) {
    // g and the slope s need only p0 and pt; h1, h2, the ASN and the table need α and β as well
    if (!all(p0, pt) || !(p0 < pt)) return null;
    var L = Math.log, g = L(pt * (1 - p0) / (p0 * (1 - pt))), s = L((1 - p0) / (1 - pt)) / g;
    var out = { g: g, s: s };
    if (!all(alpha, beta)) return out;
    var h1 = L((1 - alpha) / beta) / g, h2 = L((1 - beta) / alpha) / g;
    var A = beta / (1 - alpha), B = (1 - beta) / alpha;
    out.h1 = h1; out.h2 = h2; out.nAccept = Math.floor(h1 / s) + 1; out.nReject = Math.floor(h2 / (1 - s)) + 1;
    out.asnS = h1 * h2 / (s * (1 - s)); out.asn0 = L(A) / L((1 - pt) / (1 - p0));
    function oc(tau) { var b = Math.pow(B, tau), a = Math.pow(A, tau); return (b - 1) / (b - a); }
    function pOf(tau) { var r = Math.pow((1 - pt) / (1 - p0), tau); return (1 - r) / (Math.pow(pt / p0, tau) - r); }
    function asn(p, o) { return (o * L(A) + (1 - o) * L(B)) / (p * L(pt / p0) + (1 - p) * L((1 - pt) / (1 - p0))); }
    out.table = [-3, -2, -1, -0.5, 0.5, 1, 2, 3].map(function (t) { var p = pOf(t), o = oc(t); return { tau: t, p: p, oc: o, asn: asn(p, o) }; });
    out.table.splice(4, 0, { tau: 0, p: s, oc: null, asn: out.asnS });
    if (all(n, x)) {
      out.acceptLine = -h1 + s * n; out.rejectLine = h2 + s * n;
      out.decision = x <= out.acceptLine ? 'aanvaard het lot' : (x >= out.rejectLine ? 'verwerp het lot' : 'verder inspecteren');
    }
    return out;
  }
  // variables plan for a given n (AS p. 26–27, AS FR p. 9; AS.xlsm 'variable sampling plan')
  function variablesGivenN(p0, alpha, n, xi, mean, sd, k) {
    // z_(1−p0) from p0, z_α from α, t(1 − α, p0, n) with n; k, OC, Q and the decision as soon as their inputs are known
    var z = S.normInv, out = {}, ok = function (x) { return num(x) && x > 0 && x < 1; };
    if (ok(p0)) out.zP = z(1 - p0);
    if (ok(alpha)) out.zA = z(alpha);
    if (ok(p0) && ok(alpha) && num(n) && n >= 2) out.t = toleranceFactor(out.zA, out.zP, n);
    out.xi = xi;
    var kk = num(k) ? k : out.t;
    out.k = kk;
    if (ok(p0) && num(kk) && num(n) && n >= 2) out.ocP0 = 1 - S.normCdf((z(p0) + kk) * Math.sqrt(n) / Math.sqrt(1 + kk * kk / 2));
    if (all(xi, mean, sd) && sd > 0) {
      out.Q = (mean - xi) / sd;
      if (num(kk)) out.accept = out.Q >= kk ? 'aanvaarden' : 'verwerpen';
    }
    return [out.zP, out.zA, out.t, out.k, out.Q].some(num) ? out : null;
  }
  function skipLot(p, n, lots, d, last) {   // AS FR p. 11 notes: P_q = B(d; lots·n, p)·B(0; n, p)^last
    // B(0; n, p) needs p and n; B(d; lots·n, p) also lots and d; P_q also the number of clean last samples
    if (!all(p, n)) return null;
    var out = { lastOne: S.binomCdf(0, n, p) };
    if (all(lots, d)) out.first = S.binomCdf(d, lots * n, p);
    if (num(out.first) && num(last)) out.pq = out.first * Math.pow(out.lastOne, last);
    return out;
  }
  function deming(p, k1, k2) {   // AS FR p. 15: p < k1/k2 → no inspection; p > k1/k2 → 100 % inspection
    var out = {};
    if (all(k1, k2) && k2 > 0) out.breakEven = k1 / k2;
    if (num(p)) out.exact = p * (1 - p);
    if (num(p) && num(out.breakEven)) {
      out.decision = p < out.breakEven ? 'geen inspectie (n = 0)' : (p > out.breakEven ? 'volledige inspectie (n = N)' : 'gelijk: beide even duur');
    }
    return Object.keys(out).length ? out : null;
  }

  /* ---------- descriptive statistics and correlation ---------- */
  function median(xs) {
    var s = xs.slice().sort(function (a, b) { return a - b; }), m = s.length >> 1;
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  function descriptives(xs) {
    if (!xs || !xs.length) return null;
    var n = xs.length, mean = S.mean(xs), out = { n: n, sum: mean * n, mean: mean, median: median(xs),
      min: Math.min.apply(null, xs), max: Math.max.apply(null, xs) };
    out.range = out.max - out.min;
    if (n > 1) { out.variance = S.devsq(xs) / (n - 1); out.sd = Math.sqrt(out.variance); out.se = out.sd / Math.sqrt(n);
                 out.variancePop = S.devsq(xs) / n; out.sdPop = Math.sqrt(out.variancePop); }
    return out;
  }
  function correlation(xs, ys) {
    if (!xs || !ys || xs.length !== ys.length || xs.length < 3) return null;
    var mx = S.mean(xs), my = S.mean(ys), sxy = 0;
    for (var i = 0; i < xs.length; i++) sxy += (xs[i] - mx) * (ys[i] - my);
    var sxx = S.devsq(xs), syy = S.devsq(ys), r = sxy / Math.sqrt(sxx * syy), n = xs.length;
    var t = r * Math.sqrt((n - 2) / (1 - r * r));
    return { n: n, cov: sxy / (n - 1), r: r, r2: r * r, t: t, p: 2 * S.tSf(Math.abs(t), n - 2) };
  }

  /* ---------- multiple linear regression (least squares with an intercept) ---------- */
  function invert(a) {   // Gauss-Jordan with partial pivoting; null when singular
    var n = a.length, m = a.map(function (row, i) { return row.concat(row.map(function (_, j) { return i === j ? 1 : 0; })); });
    for (var c = 0; c < n; c++) {
      var piv = c;
      for (var r = c + 1; r < n; r++) if (Math.abs(m[r][c]) > Math.abs(m[piv][c])) piv = r;
      if (Math.abs(m[piv][c]) < 1e-12 * Math.max(1, Math.abs(m[c][c]))) return null;
      var tmp = m[c]; m[c] = m[piv]; m[piv] = tmp;
      var d = m[c][c];
      for (var j = 0; j < 2 * n; j++) m[c][j] /= d;
      for (r = 0; r < n; r++) if (r !== c) { var f = m[r][c]; for (j = 0; j < 2 * n; j++) m[r][j] -= f * m[c][j]; }
    }
    return m.map(function (row) { return row.slice(n); });
  }
  // rows: [y, x1, …, xk]; x0: optional point [x1 … xk] for the fitted value and its intervals
  function multipleRegression(rows, x0, alpha) {
    if (!rows || rows.length < 3) return null;
    var k = rows[0].length - 1, n = rows.length, p = k + 1;
    if (k < 1 || rows.some(function (r) { return r.length !== k + 1; })) return { error: 'elke regel: y gevolgd door evenveel x-waarden' };
    if (n <= p) return { error: 'meer waarnemingen nodig dan coëfficiënten (n > k + 1)' };
    var X = rows.map(function (r) { return [1].concat(r.slice(1)); }), y = rows.map(function (r) { return r[0]; });
    var XtX = [], Xty = [], i, j, l;
    for (i = 0; i < p; i++) {
      XtX.push([]); Xty.push(0);
      for (j = 0; j < p; j++) { var s = 0; for (l = 0; l < n; l++) s += X[l][i] * X[l][j]; XtX[i].push(s); }
      for (l = 0; l < n; l++) Xty[i] += X[l][i] * y[l];
    }
    var C = invert(XtX);
    if (!C) return { error: 'de x-kolommen zijn lineair afhankelijk (of constant)' };
    var b = C.map(function (row) { return row.reduce(function (a, c, q) { return a + c * Xty[q]; }, 0); });
    var yb = S.mean(y), sse = 0, sst = S.devsq(y);
    for (l = 0; l < n; l++) { var fit = 0; for (j = 0; j < p; j++) fit += b[j] * X[l][j]; sse += (y[l] - fit) * (y[l] - fit); }
    var ssr = sst - sse, dfE = n - p, mse = sse / dfE, t2 = S.tInv(1 - alpha / 2, dfE);
    var coef = b.map(function (bj, q) {
      var se = Math.sqrt(mse * C[q][q]), t = bj / se;
      return { b: bj, se: se, t: t, p: 2 * S.tSf(Math.abs(t), dfE), lo: bj - t2 * se, hi: bj + t2 * se };
    });
    var out = { n: n, k: k, coef: coef, sst: sst, ssr: ssr, sse: sse, dfR: k, dfE: dfE, msr: ssr / k, mse: mse,
                s: Math.sqrt(mse), r2: ssr / sst, r2adj: 1 - (1 - ssr / sst) * (n - 1) / (n - k - 1),
                r2adjP56: n - k - 2 > 0 ? 1 - (1 - ssr / sst) * (n - 1) / (n - k - 2) : null };
    out.F = out.msr / mse; out.pF = S.fSf(out.F, k, dfE);
    if (x0 && x0.length === k) {
      var v = [1].concat(x0), yh = 0, q2 = 0;
      for (i = 0; i < p; i++) { yh += b[i] * v[i]; for (j = 0; j < p; j++) q2 += v[i] * C[i][j] * v[j]; }
      out.y0 = yh; out.seMean = Math.sqrt(mse * q2); out.sePred = Math.sqrt(mse * (1 + q2));
      out.ciMean = [yh - t2 * out.seMean, yh + t2 * out.seMean]; out.pi = [yh - t2 * out.sePred, yh + t2 * out.sePred];
    }
    return out;
  }
  // partial F-test: does adding r terms (full model) explain significantly more than the reduced model?
  function partialF(sseReduced, sseFull, r, dfFull, alpha) {
    // the critical F needs only α and the two degrees of freedom; F, p and the decision need the two SS_E as well
    var a = num(alpha) && alpha > 0 && alpha < 1, ok = num(r) && r > 0 && num(dfFull) && dfFull > 0, out = {};
    if (!ok) return null;
    if (a) out.Fcrit = S.fIsf(alpha, r, dfFull);
    if (all(sseReduced, sseFull)) {
      out.F = ((sseReduced - sseFull) / r) / (sseFull / dfFull);
      out.p = S.fSf(out.F, r, dfFull);
      if (a) out.d = decide(out.p, alpha);
    }
    return Object.keys(out).length ? out : null;
  }

  /* ---------- two-way ANOVA, balanced (as Excel's 'Anova: Two-Factor With/Without Replication') ---------- */
  // lines: a·r lines (row-factor level 1: r lines, level 2: r lines, …), each with b values (column-factor levels)
  function anova2(lines, r, alpha) {
    if (!lines || !lines.length || !all(r) || r < 1 || lines.length % r) return { error: 'het aantal regels moet een veelvoud zijn van r' };
    var b = lines[0].length, a = lines.length / r, i, j, t;
    if (b < 2 || a < 2 || lines.some(function (l) { return l.length !== b; })) return { error: 'minstens 2 rijniveaus en 2 kolommen, elke regel even lang' };
    var all_ = [].concat.apply([], lines), gm = S.mean(all_), N = all_.length, cell = [], rowM = [], colM = [];
    for (i = 0; i < a; i++) {
      cell.push([]);
      for (j = 0; j < b; j++) { var s = 0; for (t = 0; t < r; t++) s += lines[i * r + t][j]; cell[i].push(s / r); }
      rowM.push(S.mean(cell[i]));
    }
    for (j = 0; j < b; j++) { var c = 0; for (i = 0; i < a; i++) c += cell[i][j]; colM.push(c / a); }
    var ssA = 0, ssB = 0, ssCells = 0, sst = S.devsq(all_);
    for (i = 0; i < a; i++) ssA += b * r * Math.pow(rowM[i] - gm, 2);
    for (j = 0; j < b; j++) ssB += a * r * Math.pow(colM[j] - gm, 2);
    for (i = 0; i < a; i++) for (j = 0; j < b; j++) ssCells += r * Math.pow(cell[i][j] - gm, 2);
    var rowsOut = [], dfA = a - 1, dfB = b - 1;
    function line(name, ss, df, msE, dfE) {
      var ms = ss / df, F = msE ? ms / msE : null;
      return { name: name, ss: ss, df: df, ms: ms, F: F, p: F !== null ? S.fSf(F, df, dfE) : null,
               Fcrit: F !== null && num(alpha) ? S.fIsf(alpha, df, dfE) : null };
    }
    if (r > 1) {
      var ssAB = ssCells - ssA - ssB, ssW = sst - ssCells, dfAB = dfA * dfB, dfW = a * b * (r - 1), msW = ssW / dfW;
      rowsOut = [line('rijen (factor A)', ssA, dfA, msW, dfW), line('kolommen (factor B)', ssB, dfB, msW, dfW),
                 line('interactie A × B', ssAB, dfAB, msW, dfW), { name: 'binnen (fout)', ss: ssW, df: dfW, ms: msW }];
    } else {
      var ssE = sst - ssA - ssB, dfE = dfA * dfB, msE = ssE / dfE;
      rowsOut = [line('rijen (factor A)', ssA, dfA, msE, dfE), line('kolommen (factor B)', ssB, dfB, msE, dfE),
                 { name: 'fout (rest, = interactie)', ss: ssE, df: dfE, ms: msE }];
    }
    rowsOut.push({ name: 'totaal', ss: sst, df: N - 1 });
    return { a: a, b: b, r: r, grandMean: gm, rowMeans: rowM, colMeans: colM, cellMeans: cell, table: rowsOut };
  }

  /* ---------- k × k confusion matrix: per class one-vs-rest ---------- */
  // m[i][j] = count with actual class i and predicted class j (rowsActual) or the transpose
  function confusionK(m, rowsActual) {
    var k = m.length;
    if (!k || m.some(function (r) { return r.length !== k; })) return null;
    var A = rowsActual ? m : m[0].map(function (_, j) { return m.map(function (r) { return r[j]; }); });
    var N = 0, diag = 0, i, j;
    for (i = 0; i < k; i++) for (j = 0; j < k; j++) { N += A[i][j]; if (i === j) diag += A[i][j]; }
    if (!(N > 0)) return null;
    var classes = [];
    for (i = 0; i < k; i++) {
      var tp = A[i][i], fn = 0, fp = 0;
      for (j = 0; j < k; j++) if (j !== i) { fn += A[i][j]; fp += A[j][i]; }
      var rec = tp + fn ? tp / (tp + fn) : null, prec = tp + fp ? tp / (tp + fp) : null;
      classes.push({ tp: tp, fn: fn, fp: fp, tn: N - tp - fn - fp, recall: rec, precision: prec,
                     f1: all(rec, prec) && rec + prec > 0 ? 2 * rec * prec / (rec + prec) : null, support: tp + fn });
    }
    return { N: N, accuracy: diag / N, error: 1 - diag / N, classes: classes };
  }

  /* ---------- Bayes' rule and the Beta posterior of a proportion ---------- */
  function bayes(pA, pBgivenA, pBgivenNotA) {
    // the prior odds need only P(A), the likelihood ratio only the two P(B | …), the rest all three
    var out = {};
    if (num(pA) && pA < 1) out.priorOdds = pA / (1 - pA);
    if (all(pBgivenA, pBgivenNotA) && pBgivenNotA) out.likelihoodRatio = pBgivenA / pBgivenNotA;
    if (num(out.priorOdds) && num(out.likelihoodRatio)) out.posteriorOdds = out.priorOdds * out.likelihoodRatio;
    if (all(pA, pBgivenA, pBgivenNotA)) {
      var pB = pA * pBgivenA + (1 - pA) * pBgivenNotA;
      out.pB = pB;
      out.pAgivenB = pB ? pA * pBgivenA / pB : null;
      out.pNotAgivenB = pB ? (1 - pA) * pBgivenNotA / pB : null;
      out.pAgivenNotB = 1 - pB ? pA * (1 - pBgivenA) / (1 - pB) : null;
    }
    return Object.keys(out).length ? out : null;
  }
  // web slides p. 55: posterior Beta(α + k, β + n − k), mean; Naert notes L1 p. 4 figure: mode, mean, median of Beta(2, 8)
  function betaPosterior(a, b, x, n) {
    var out = {}, prior = all(a, b) && a > 0 && b > 0;
    function summary(p, q) {
      return { a: p, b: q, mean: p / (p + q), mode: p > 1 && q > 1 ? (p - 1) / (p + q - 2) : null, median: S.betaInv(0.5, p, q) };
    }
    if (prior) out.prior = summary(a, b);
    if (all(x, n) && x >= 0 && n >= x && n > 0) {
      out.mle = x / n;   // k/n needs no prior
      if (prior) out.posterior = summary(a + x, b + n - x);
    }
    return Object.keys(out).length ? out : null;
  }

  /* ---------- regression from summary values (REG p. 18–38, 56, 61) ---------- */
  function regSums(n, sx, sy, sxx, sxy, syy) {
    // each result as soon as its sums are there: the means from n and Σx, Σy; S_xx and S_xy with Σx², Σxy; b1 and b0
    // from those; the sums of squares, R² and σ̂ with Σy²
    if (!num(n) || n < 1) return null;
    var out = {};
    if (num(sx)) out.xbar = sx / n;
    if (num(sy)) out.ybar = sy / n;
    if (num(out.xbar) && num(sxx)) out.Sxx = sxx - n * out.xbar * out.xbar;
    if (all(out.xbar, out.ybar) && num(sxy)) out.Sxy = sxy - n * out.xbar * out.ybar;
    if (num(syy) && num(out.ybar)) out.sst = syy - n * out.ybar * out.ybar;
    if (num(out.Sxx) && out.Sxx > 0 && num(out.Sxy)) {
      out.b1 = out.Sxy / out.Sxx;
      if (all(out.xbar, out.ybar)) out.b0 = out.ybar - out.b1 * out.xbar;
      if (num(out.sst)) {
        out.ssr = out.b1 * out.Sxy; out.sse = out.sst - out.ssr; out.r2 = out.ssr / out.sst;
        if (n >= 3) { out.mse = out.sse / (n - 2); out.s = Math.sqrt(out.mse); }
      }
    }
    return Object.keys(out).length ? out : null;
  }
  function regFromSS(ssr, sse, n, k, alpha) {
    // each result as soon as its inputs are there: SS_T and R² from the two sums, the degrees of freedom and the
    // critical F from n, k and α, the mean squares, F and p with the matching sums
    var kk = num(k) && k >= 1 ? k : 1, out = {}, nOk = num(n) && n - kk - 1 > 0;
    if (all(ssr, sse)) { out.sst = ssr + sse; out.r2 = ssr / out.sst; }
    if (nOk) {
      out.dfE = n - kk - 1;
      if (num(alpha) && alpha > 0 && alpha < 1) out.Fcrit = S.fIsf(alpha, kk, out.dfE);
    }
    if (num(ssr)) out.msr = ssr / kk;
    if (num(sse) && nOk) { out.mse = sse / out.dfE; out.s = Math.sqrt(out.mse); }
    if (num(out.msr) && num(out.mse)) { out.F = out.msr / out.mse; out.p = S.fSf(out.F, kk, out.dfE); }
    if (num(out.r2) && nOk) {
      out.r2adj = 1 - (1 - out.r2) * (n - 1) / (n - kk - 1);
      out.r2adjP56 = n - kk - 2 > 0 ? 1 - (1 - out.r2) * (n - 1) / (n - kk - 2) : null;
    }
    return Object.keys(out).length ? out : null;
  }
  function r2adj(r2, n, k) {
    if (!all(r2, n, k) || n - k - 1 <= 0) return null;
    return { usual: 1 - (1 - r2) * (n - 1) / (n - k - 1), p56: n - k - 2 > 0 ? 1 - (1 - r2) * (n - 1) / (n - k - 2) : null };
  }
  // tests and intervals of simple regression from b1, b0, MS_E, S_xx, n, x̄ (REG p. 30–38)
  function regTests(b1, b0, mse, sxx, n, xbar, x0, alpha, b1H0, b0H0, seB1Given) {
    // each result as soon as its inputs are there: the critical t from n and α, the standard errors from MS_E and the
    // spread of x, then the tests and intervals with the estimates added
    var a = num(alpha) && alpha > 0 && alpha < 1, nOk = num(n) && n >= 3, out = {}, t2, t1;
    var spread = all(mse, sxx) && mse > 0 && sxx > 0;
    if (nOk) out.df = n - 2;
    if (nOk && a) { t2 = S.tInv(1 - alpha / 2, out.df); t1 = S.tInv(1 - alpha, out.df); out.tcrit = t2; }
    if (spread) out.seB1 = Math.sqrt(mse / sxx);
    else if (num(seB1Given) && seB1Given > 0) out.seB1 = seB1Given;   // the printed s.e. of the slope instead of MS_E and S_xx
    if (num(out.seB1) && num(b1)) out.F = Math.pow(b1 / out.seB1, 2);
    if (num(out.seB1) && num(b1) && nOk && a) {
      out.tB1 = tests((b1 - (num(b1H0) ? b1H0 : 0)) / out.seB1, out.df, alpha); out.ciB1 = intervals(b1, out.seB1, t2, t1);
    }
    if (spread && nOk && num(xbar)) {
      out.seB0 = Math.sqrt(mse * (1 / n + xbar * xbar / sxx));
      if (num(b0) && a) { out.tB0 = tests((b0 - (num(b0H0) ? b0H0 : 0)) / out.seB0, out.df, alpha); out.ciB0 = intervals(b0, out.seB0, t2, t1); }
      if (num(x0)) {
        out.seMean = Math.sqrt(mse * (1 / n + (x0 - xbar) * (x0 - xbar) / sxx));
        out.sePred = Math.sqrt(mse * (1 + 1 / n + (x0 - xbar) * (x0 - xbar) / sxx));
      }
    }
    if (all(b0, b1, x0)) out.y0 = b0 + b1 * x0;
    if (num(out.y0) && num(out.seMean) && a) {
      out.ciMean = intervals(out.y0, out.seMean, t2, t1); out.pi = intervals(out.y0, out.sePred, t2, t1);
    }
    return Object.keys(out).length ? out : null;
  }

  /* ---------- SPC: limits from standard values (Tabellen SPC p. 2, Table 7.2) and run rules (SPC p. 68–69) ---------- */
  function standardLimits(mu, sigma, n, K) {
    if (!all(mu, sigma, n) || n < 2 || sigma <= 0) return null;
    var g = function (s) { return K.get(s, n); }, f = Math.sqrt(n / (n - 1)), out = { n: n, A: g('A'), d2: g('d2'), D1: g('D1'), D2: g('D2'),
      c2: g('c2'), B1: g('B1'), B2: g('B2') };
    out.sigmaXbar = sigma / Math.sqrt(n);
    out.x3 = [mu - 3 * out.sigmaXbar, mu, mu + 3 * out.sigmaXbar];
    if (num(out.A)) out.xA = [mu - out.A * sigma, mu, mu + out.A * sigma];
    if (all(out.d2, out.D1, out.D2)) out.R = [out.D1 * sigma, out.d2 * sigma, out.D2 * sigma];
    if (all(out.c2, out.B1, out.B2)) out.S = [out.B1 * f * sigma, out.c2 * f * sigma, out.B2 * f * sigma];
    return out;
  }
  // Western Electric and sensitizing rules 1–8 of SPC p. 68 on standardized points z = (x − CL)/σ of the plotted statistic.
  // Rules 2 and 3: the qualifying points on one side (as the Western Electric rules linked on SPC p. 69); a point exactly on
  // the centre line breaks a run; ties break a trend or an alternation; zone C is |z| ≤ 1.
  function runRules(xs, cl, sigma) {
    if (!xs || xs.length < 1 || !all(cl, sigma) || sigma <= 0) return null;
    var z = xs.map(function (x) { return (x - cl) / sigma; }), n = z.length, hits = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], '2b': [], '3b': [] };
    function count(from, to, test) { var c = 0; for (var q = from; q <= to; q++) if (test(z[q])) c++; return c; }
    function all_(from, to, test) { for (var q = from; q <= to; q++) if (!test(z[q], q)) return false; return true; }
    for (var i = 0; i < n; i++) {
      if (Math.abs(z[i]) > 3) hits[1].push(i + 1);
      if (i >= 2 && (count(i - 2, i, function (v) { return v > 2; }) >= 2 || count(i - 2, i, function (v) { return v < -2; }) >= 2)) hits[2].push(i + 1);
      if (i >= 4 && (count(i - 4, i, function (v) { return v > 1; }) >= 4 || count(i - 4, i, function (v) { return v < -1; }) >= 4)) hits[3].push(i + 1);
      // SPC p. 68 does not say 'same side' for rules 2 and 3: the literal reading counts points on either side
      if (i >= 2 && count(i - 2, i, function (v) { return Math.abs(v) > 2; }) >= 2) hits['2b'].push(i + 1);
      if (i >= 4 && count(i - 4, i, function (v) { return Math.abs(v) > 1; }) >= 4) hits['3b'].push(i + 1);
      if (i >= 7 && (all_(i - 7, i, function (v) { return v > 0; }) || all_(i - 7, i, function (v) { return v < 0; }))) hits[4].push(i + 1);
      if (i >= 5 && (all_(i - 4, i, function (v, q) { return z[q] > z[q - 1]; }) || all_(i - 4, i, function (v, q) { return z[q] < z[q - 1]; }))) hits[5].push(i + 1);
      if (i >= 14 && all_(i - 14, i, function (v) { return Math.abs(v) <= 1; })) hits[6].push(i + 1);
      if (i >= 13 && all_(i - 12, i, function (v, q) { var d1 = z[q] - z[q - 1], d0 = z[q - 1] - z[q - 2]; return q >= 2 && d1 * d0 < 0; })) hits[7].push(i + 1);
      if (i >= 7 && all_(i - 7, i, function (v) { return Math.abs(v) > 1; }) && count(i - 7, i, function (v) { return v > 0; }) > 0 &&
          count(i - 7, i, function (v) { return v < 0; }) > 0) hits[8].push(i + 1);
    }
    return { z: z, hits: hits, zones: z.map(function (v) { var a = Math.abs(v); return a > 3 ? 'buiten' : (a > 2 ? 'A' : (a > 1 ? 'B' : 'C')); }) };
  }

  /* ---------- MSA (Les 5): observed vs actual Cp, gauge performance curve, uncertainty, bias test, discrimination ---------- */
  // MSA p. 24: 1/Cpo² = 1/Cpa² + 1/Cpm²; %GRR of process: Cpo = Cpa·√(1 − %GRR²); of tolerance: 1/Cpo² = 1/Cpa² + %GRR²
  function cpObserved(basis, grr, cpa, cpo) {
    if (!num(grr) || grr < 0) return null;
    if (basis === 'process') {
      if (num(cpa)) return { cpo: grr < 1 ? cpa * Math.sqrt(1 - grr * grr) : null };
      if (num(cpo)) return { cpa: grr < 1 ? cpo / Math.sqrt(1 - grr * grr) : null };
    } else {
      if (num(cpa) && cpa > 0) return { cpo: 1 / Math.sqrt(1 / (cpa * cpa) + grr * grr) };
      if (num(cpo) && cpo > 0) { var q = 1 / (cpo * cpo) - grr * grr; return { cpa: q > 0 ? 1 / Math.sqrt(q) : null }; }
    }
    return null;
  }
  function gaugePerformance(lsl, usl, bias, sigma, xr) {   // MSA p. 27
    if (!all(lsl, usl, bias, sigma) || sigma <= 0 || !xr || !xr.length) return null;
    return xr.map(function (x) {
      var b = S.normCdf((usl - (x + bias)) / sigma) - S.normCdf((lsl - (x + bias)) / sigma);
      return { x: x, accept: b, reject: 1 - b };
    });
  }
  // steel strip p. 1–2, MSA p. 28–29: standard uncertainties per source, u_c = √Σu², U = k·u_c
  function uncertaintyBudget(sources, k, K, reading) {
    // one standard uncertainty u per source: certificate U/k, uniform a/√3 (also given as a % of the reading), type A from
    // a range (R/d2, d2 from Table 18 when not typed) or a standard deviation, both divided by √n for a mean of n readings
    var rows = sources.map(function (s) {
      var u = null, d2 = s.kind === 'range' ? (num(s.b) ? s.b : (K && num(s.c) ? K.get('d2', s.c) : null)) : null;
      var share = num(reading) ? reading / 100 : null, root = num(s.c) && s.c > 0 ? Math.sqrt(s.c) : 1;
      if (s.kind === 'cert' && all(s.a, s.b) && s.b > 0) u = s.a / s.b;
      else if (s.kind === 'certpct' && all(s.a, s.b) && s.b > 0 && num(share)) u = s.a * share / s.b;
      else if (s.kind === 'uni' && num(s.a)) u = s.a / Math.sqrt(3);
      else if (s.kind === 'unipct' && num(s.a) && num(share)) u = s.a * share / Math.sqrt(3);
      else if (s.kind === 'range' && num(s.a) && num(d2) && d2 > 0) u = s.a / d2 / root;
      else if (s.kind === 'sd' && num(s.a)) u = s.a / root;
      else if (s.kind === 'u' && num(s.a)) u = s.a;
      return { kind: s.kind, u: u, d2: d2 };
    });
    var sum = 0, used = 0;
    rows.forEach(function (r) { if (num(r.u)) { sum += r.u * r.u; used++; } });
    if (!used) return null;
    rows.forEach(function (r) { r.share = num(r.u) ? r.u * r.u / sum : null; });
    var uc = Math.sqrt(sum);
    return { rows: rows, uc: uc, k: num(k) ? k : 2, U: (num(k) ? k : 2) * uc };
  }
  // MSA p. 31–32: bias = X̿ − ref; σ_r = R̄/d2; t = bias/σ_r·√(gm)·d2*/d2 with ν degrees of freedom (tabel MSA)
  function biasTest(xbarbar, rbar, g, m, ref, alpha, M) {
    // each result as soon as its inputs are there: the bias from X̿ and the reference, d2 from m, d2*, ν and the
    // critical t from g, m and α, σ_r from R̄ and m, then t, p and the interval
    var a = num(alpha) && alpha > 0 && alpha < 1, out = {};
    if (num(xbarbar) && num(ref)) out.bias = xbarbar - ref;
    if (num(m)) { out.d2 = M.d2(m); if (!num(out.d2)) return { error: 'm staat niet in tabel MSA (m 2–20)' }; }
    if (all(g, m)) {
      out.d2s = M.d2star(g, m); out.nu = M.nu(g, m);
      if (!all(out.d2s, out.nu)) return { error: 'g of m staat niet in tabel MSA (g 1–20, m 2–20)' };
      if (a) out.tcrit = S.tInv(1 - alpha / 2, out.nu);
    }
    if (num(rbar) && rbar > 0 && num(out.d2)) out.sr = rbar / out.d2;
    if (num(out.sr) && num(out.d2s)) {
      var unit = out.sr * out.d2 / (out.d2s * Math.sqrt(g * m));   // the standard error of the bias
      if (num(out.bias)) { out.t = out.bias / unit; out.p = 2 * S.tSf(Math.abs(out.t), out.nu); }
      if (num(out.bias) && a) {
        out.ci = [out.bias - unit * out.tcrit, out.bias + unit * out.tcrit];
        out.significant = out.ci[0] > 0 || out.ci[1] < 0;
      }
    }
    return Object.keys(out).length ? out : null;
  }
  // MSA p. 30: count the multiples of the measurement unit between the range chart's limits (Table 18 D3, D4, d2)
  function discrimination(n, mu, rbar, K) {
    if (!all(n, mu) || mu <= 0) return null;
    var D3 = K.get('D3', n), D4 = K.get('D4', n), d2 = K.get('d2', n);
    if (!all(D3, D4, d2)) return { error: 'n staat niet in Table 18' };
    var borderline = !num(rbar), r = borderline ? d2 * mu : rbar, lcl = D3 * r, ucl = D4 * r;
    var values = [];
    for (var q = Math.ceil(lcl / mu - 1e-9); q * mu <= ucl + 1e-9 && values.length < 1000; q++) values.push(q * mu);
    var limit = n === 2 ? 3 : 4;
    return { borderline: borderline, rbar: r, lcl: lcl, ucl: ucl, width: (ucl - lcl) / mu, values: values,
             tooCoarse: values.length <= limit, limit: limit };
  }

  /* ---------- solvers in every direction: any sufficient subset of the inputs gives all the others ---------- */
  // A note when two inputs that should agree differ by more than 0.5 % (a printed table value is rounded).
  function disagree(a, b) { return Math.abs(a - b) > 0.005 * Math.max(Math.abs(a), Math.abs(b)); }
  // Repeat a set of rules until none of them adds a value; each rule returns true when it set something.
  function propagate(rules) {
    for (var pass = 0; pass < 8; pass++) {
      var changed = false;
      rules.forEach(function (rule) { changed = rule() || changed; });
      if (!changed) return;
    }
  }
  // True when any of the already evaluated set() results is true: every set() in the list has run.
  function anySet(results) { return results.some(Boolean); }
  function setter(v, solved) {
    return function (key, value) {
      if (num(v[key]) || !num(value)) return false;
      v[key] = value; solved.push(key);
      return true;
    };
  }

  // Sigma level ↔ DPMO ↔ DPO ↔ yield ↔ (D, N, O): SPC p. 20–21, decision 3 (sigma level = Z + 1,5).
  // The first given quantity in this order fixes DPO: D/(N·O), DPO, DPMO, yield, Z, sigma level.
  function sigmaSolve(k) {
    var notes = [], solved = [], from = [];
    if (all(k.D, k.N, k.O) && k.N > 0 && k.O > 0) from.push(['D/(N·O)', k.D / (k.N * k.O)]);
    if (num(k.dpo)) from.push(['DPO', k.dpo]);
    if (num(k.dpmo)) from.push(['DPMO', k.dpmo / MILLION]);
    if (num(k.yield)) from.push(['yield', 1 - k.yield]);
    if (num(k.z)) from.push(['Z', S.normCdf(-k.z)]);
    if (num(k.level)) from.push(['sigmaniveau', S.normCdf(-(k.level - SHIFT))]);
    var v = { D: k.D, N: k.N, O: k.O, dpo: from.length ? from[0][1] : null }, set = setter(v, solved);
    from.slice(1).forEach(function (f) {
      if (disagree(f[1], v.dpo)) notes.push(f[0] + ' spreekt ' + from[0][0] + ' tegen; ' + from[0][0] + ' gebruikt');
    });
    if (!from.length || from[0][0] !== 'DPO') solved.push('dpo');
    if (num(v.dpo)) {   // the missing one of D, N, O
      if (all(v.N, v.O) && !num(v.D)) set('D', v.dpo * v.N * v.O);
      else if (all(v.D, v.O) && !num(v.N) && v.dpo > 0) set('N', v.D / (v.dpo * v.O));
      else if (all(v.D, v.N) && !num(v.O) && v.dpo > 0) set('O', v.D / (v.dpo * v.N));
    }
    var out = { D: v.D, N: v.N, O: v.O, dpo: v.dpo, solved: solved, notes: notes };
    if (!num(v.dpo)) return out;
    out.dpmo = v.dpo * MILLION; out.yield = 1 - v.dpo;
    if (v.dpo > 0 && v.dpo < 1) {
      out.z = -S.normInv(v.dpo); out.level = out.z + SHIFT;
      out.oneTail = MILLION * S.normCdf(-out.level); out.twoTails = 2 * out.oneTail;   // the level read without shift
    } else notes.push('DPO moet tussen 0 en 1 liggen voor een sigmaniveau');
    ['dpmo', 'yield', 'z', 'level'].forEach(function (key) { if (!num(k[key]) && num(out[key])) solved.push(key); });
    return out;
  }

  // An interval [a ; b] of the normal distribution: µ, σ, a, b, k (bounds µ ± kσ), the fraction inside or outside.
  // Without µ the interval is taken symmetric (µ in the middle) and said so.
  function normalInterval(q) {
    var v = { mu: q.mu, sigma: num(q.sigma) && q.sigma > 0 ? q.sigma : null, a: q.a, b: q.b, k: q.k }, solved = [], notes = [];
    var set = setter(v, solved);
    if (num(q.sigma) && q.sigma <= 0) notes.push('σ moet positief zijn');
    if (num(q.inside) && num(q.outside) && Math.abs(q.inside + q.outside - 1) > 1e-9) notes.push('binnen + buiten is niet 1');
    var inside = num(q.inside) ? q.inside : (num(q.outside) ? 1 - q.outside : null);
    var kFromP = num(inside) && inside > 0 && inside < 1 ? S.normInv(1 - (1 - inside) / 2) : null;
    if (num(v.k) && num(kFromP) && disagree(v.k, kFromP)) notes.push('k en de kans spreken elkaar tegen; k gebruikt');
    if (!num(v.mu) && all(v.a, v.b) && (num(v.sigma) || num(v.k) || num(kFromP))) {
      set('mu', (v.a + v.b) / 2);
      notes.push('symmetrisch interval aangenomen: µ = (a + b)/2');
    }
    propagate([
      function () { return set('k', kFromP); },
      function () { return all(v.mu, v.sigma, v.a, v.b) && Math.abs((v.b - v.mu) - (v.mu - v.a)) < 1e-9 * Math.max(1, Math.abs(v.b)) ? set('k', (v.b - v.mu) / v.sigma) : false; },
      function () {
        if (num(v.sigma) || !all(v.mu, v.k) || v.k <= 0) return false;
        var bound = num(v.b) ? v.b - v.mu : (num(v.a) ? v.mu - v.a : null);
        return num(bound) && bound > 0 ? set('sigma', bound / v.k) : false;
      },
      function () { return all(v.mu, v.sigma, v.k) ? set('a', v.mu - v.k * v.sigma) : false; },
      function () { return all(v.mu, v.sigma, v.k) ? set('b', v.mu + v.k * v.sigma) : false; },
      function () { return all(v.a, v.b, v.k) && !num(v.sigma) && v.k > 0 ? set('sigma', (v.b - v.a) / (2 * v.k)) : false; }
    ]);
    var out = { mu: v.mu, sigma: v.sigma, a: v.a, b: v.b, k: v.k, solved: solved, notes: notes };
    // Each result appears as soon as its own inputs are known: one bound gives its z and tail,
    // and k alone already gives the symmetric interval µ ± kσ in standard units.
    if (all(v.mu, v.sigma, v.a)) { out.za = (v.a - v.mu) / v.sigma; out.below = S.normCdf(out.za); }
    if (all(v.mu, v.sigma, v.b)) { out.zb = (v.b - v.mu) / v.sigma; out.above = S.normCdf(-out.zb); }
    if (num(v.k) && v.k > 0 && !all(v.mu, v.sigma, v.a, v.b)) {
      out.za = -v.k; out.zb = v.k; out.below = out.above = S.normCdf(-v.k);
      out.inside = 1 - 2 * out.below; out.outside = 2 * out.below;
      solved.push('inside', 'outside');
    }
    if (all(v.mu, v.sigma, v.a, v.b)) {
      var lo = Math.min(v.a, v.b), hi = Math.max(v.a, v.b);
      out.za = (lo - v.mu) / v.sigma; out.zb = (hi - v.mu) / v.sigma;
      out.below = S.normCdf(out.za); out.above = S.normCdf(-out.zb);
      out.inside = 1 - out.below - out.above; out.outside = out.below + out.above;
      if (!num(q.inside)) solved.push('inside');
      if (!num(q.outside)) solved.push('outside');
      if (num(inside) && disagree(inside, out.inside)) notes.push('de ingevulde kans past niet bij µ, σ, a en b');
    }
    return out;
  }

  // Capability in every direction (SPC p. 33–40): LSL, USL, µ, σ, Cp, Cpk, ppm outside the specification.
  // Cp = (USL − LSL)/6σ, Cpu = (USL − µ)/3σ, Cpl = (µ − LSL)/3σ, Cpk = min(Cpu, Cpl), so Cpu + Cpl = 2·Cp;
  // the fraction outside is Φ(−3·Cpu) + Φ(−3·Cpl). With only USL (or LSL) the index is Cpu (Cpl).
  function capabilitySolve(q) {
    var lsl = q.lsl, usl = q.usl, two = all(lsl, usl), side = num(usl) ? 'usl' : (num(lsl) ? 'lsl' : null);
    if (two && usl <= lsl) return { error: 'USL moet groter zijn dan LSL' };
    var v = { mean: q.mean, sigma: num(q.sigma) && q.sigma > 0 ? q.sigma : null, cp: two ? q.cp : null, cpk: q.cpk,
              cpu: null, cpl: null, out: num(q.ppm) ? q.ppm / MILLION : null };
    var solved = [], notes = [], set = setter(v, solved), Phi = S.normCdf;
    if (!two && num(q.cp)) notes.push('Cp vraagt beide grenzen; genegeerd');
    if (q.centred && two) set('mean', (lsl + usl) / 2);
    function tails(cpk, cp) { return Phi(-3 * cpk) + Phi(-3 * (2 * cp - cpk)); }
    function bisect(f, lo, hi) {   // f decreasing on [lo, hi]; root of f = 0
      for (var i = 0; i < 200; i++) { var m = (lo + hi) / 2; if (f(m) > 0) lo = m; else hi = m; }
      return (lo + hi) / 2;
    }
    propagate([
      function () { return two && num(v.sigma) ? set('cp', (usl - lsl) / (6 * v.sigma)) : false; },
      function () { return two && num(v.cp) && v.cp > 0 ? set('sigma', (usl - lsl) / (6 * v.cp)) : false; },
      function () { return all(usl, v.mean, v.sigma) ? set('cpu', (usl - v.mean) / (3 * v.sigma)) : false; },
      function () { return all(lsl, v.mean, v.sigma) ? set('cpl', (v.mean - lsl) / (3 * v.sigma)) : false; },
      function () {
        if (!two || !num(v.cpu) || !num(v.cpl)) return false;
        return anySet([set('cpk', Math.min(v.cpu, v.cpl)), set('cp', (v.cpu + v.cpl) / 2)]);
      },
      function () {   // one limit: the index of that side is Cpk
        if (two || !side) return false;
        var key = side === 'usl' ? 'cpu' : 'cpl';
        return anySet([set('cpk', v[key]), set(key, v.cpk)]);
      },
      function () {   // centred: Cpu = Cpl = Cp = Cpk
        if (!q.centred || !two) return false;
        var c = num(v.cp) ? v.cp : v.cpk;
        return anySet([set('cp', c), set('cpk', c), set('cpu', c), set('cpl', c)]);
      },
      function () {   // µ and σ back from an index
        var r = false;
        if (num(v.cpu) && all(usl, v.sigma)) r = set('mean', usl - 3 * v.cpu * v.sigma) || r;
        if (num(v.cpl) && all(lsl, v.sigma)) r = set('mean', lsl + 3 * v.cpl * v.sigma) || r;
        if (num(v.cpu) && all(usl, v.mean) && v.cpu > 0) r = set('sigma', (usl - v.mean) / (3 * v.cpu)) || r;
        if (num(v.cpl) && all(lsl, v.mean) && v.cpl > 0) r = set('sigma', (v.mean - lsl) / (3 * v.cpl)) || r;
        if (num(v.cpk) && num(v.mean) && !num(v.sigma) && v.cpk > 0) {
          var d = two ? Math.min(usl - v.mean, v.mean - lsl) : (side === 'usl' ? usl - v.mean : v.mean - (num(lsl) ? lsl : NaN));
          if (d > 0) r = set('sigma', d / (3 * v.cpk)) || r;
        }
        return r;
      },
      function () {   // the fraction outside from the indices
        if (two && num(v.cpu) && num(v.cpl)) return set('out', Phi(-3 * v.cpu) + Phi(-3 * v.cpl));
        if (two && num(v.cp) && num(v.cpk)) return set('out', tails(v.cpk, v.cp));
        if (!two && num(v.cpk)) return set('out', Phi(-3 * v.cpk));
        return false;
      },
      function () {   // the indices from the fraction outside
        if (!num(v.out) || v.out <= 0 || v.out >= 1) return false;
        if (!two) return set('cpk', -S.normInv(v.out) / 3);
        if (q.centred) return set('cp', -S.normInv(v.out / 2) / 3);
        if (num(v.cp) && !num(v.cpk)) {
          if (v.out < 2 * Phi(-3 * v.cp) * (1 - 1e-12)) { notes.push('zo weinig uitval kan niet bij deze Cp (minimum: gecentreerd)'); return false; }
          return set('cpk', bisect(function (c) { return tails(c, v.cp) - v.out; }, -10, v.cp));
        }
        if (num(v.cpk) && !num(v.cp)) {
          var lo = Phi(-3 * v.cpk), hi = 2 * Phi(-3 * v.cpk);
          if (v.out <= lo || v.out > hi * (1 + 1e-12)) { notes.push('deze uitval past niet bij deze Cpk (tussen één en twee staarten)'); return false; }
          return set('cp', bisect(function (c) { return tails(v.cpk, c) - v.out; }, v.cpk, v.cpk + 20));
        }
        return false;
      }
    ]);
    var out = { lsl: lsl, usl: usl, mean: v.mean, sigma: v.sigma, cp: v.cp, cpk: v.cpk, cpu: v.cpu, cpl: v.cpl,
                ppm: num(v.out) ? v.out * MILLION : null, out: v.out, solved: solved.map(function (s) { return s === 'out' ? 'ppm' : s; }),
                notes: notes };
    if (two && all(v.cp, v.cpk, v.sigma) && !num(v.mean)) {   // two positions give the same Cp and Cpk
      out.meanOptions = [usl - 3 * v.cpk * v.sigma, lsl + 3 * v.cpk * v.sigma];
      notes.push('µ volgt niet eenduidig: dichter bij USL of dichter bij LSL');
    }
    if (num(v.cpu)) { out.zUsl = 3 * v.cpu; out.above = Phi(-out.zUsl); }
    if (num(v.cpl)) { out.zLsl = 3 * v.cpl; out.below = Phi(-out.zLsl); }
    if (num(v.cp)) out.level = cpLevel(v.cp);
    // Cpk alone fixes the tail beyond the nearest limit; with two limits the other tail is at most as large
    if (num(v.cpk) && two && !num(v.out)) { out.nearTail = Phi(-3 * v.cpk); out.outRange = [out.nearTail, 2 * out.nearTail]; }
    if (num(v.cpk)) out.capable = v.cpk >= 1.33 ? 'ja' : 'nee';   // SPC p. 41: Cpk = 1,33 is 'Good'
    return out;
  }

  // Control limits back to X̿, R̄, s̄ and σ̂ (the SPC p. 74 formulas read backwards):
  // X̄-chart UCL − CL = A2·R̄ = A3·s̄ = 3σ̂/√n; R-chart UCL = D4·R̄; s-chart UCL = B4·s̄; σ̂ = R̄/d2 = s̄/c4.
  function limitsInverse(n, q, K) {
    // q: ucl, cl, lcl (X̄-chart), rbar, uclR, lclR (R-chart), sbar, uclS (s-chart), sigma (σ̂). Without n the ratios
    // that fix a constant (A2 = (UCL − X̿)/R̄, D4 = UCL_R/R̄, …) are matched with Table 18 to find n.
    var out = { notes: [], candidates: [], derived: {} };
    var keys = ['ucl', 'cl', 'lcl', 'rbar', 'uclR', 'lclR', 'sbar', 'uclS', 'sigma'];
    if (!num(n) && !keys.some(function (k) { return num(q[k]); })) return null;
    out.xbb = num(q.cl) ? q.cl : (all(q.ucl, q.lcl) ? (q.ucl + q.lcl) / 2 : null);
    var h = all(q.ucl, out.xbb) ? q.ucl - out.xbb : (all(q.lcl, out.xbb) ? out.xbb - q.lcl : null);
    if (all(q.ucl, q.lcl, q.cl) && disagree(q.ucl - q.cl, q.cl - q.lcl)) out.notes.push('UCL en LCL liggen niet symmetrisch rond CL');
    if (num(h)) out.half = h;
    var syms = ['A2', 'A3', 'D3', 'D4', 'B3', 'B4', 'd2', 'c4'];
    var constants = function (m) { var c = {}; syms.forEach(function (s) { c[s] = K.get(s, m); }); return c; };

    var use = num(n) ? n : null;
    if (!num(use)) {   // n from the ratios: each one points at the Table 18 row whose constant is closest
      var obs = [], add = function (sym, value, label) { if (num(value) && value > 0) obs.push({ sym: sym, value: value, label: label }); };
      if (num(h) && num(q.rbar)) add('A2', h / q.rbar, 'A2 = (UCL − X̿)/R̄');
      if (num(h) && num(q.sbar)) add('A3', h / q.sbar, 'A3 = (UCL − X̿)/s̄');
      if (num(q.uclR) && num(q.rbar)) add('D4', q.uclR / q.rbar, 'D4 = UCL_R/R̄');
      if (num(q.lclR) && num(q.rbar)) add('D3', q.lclR / q.rbar, 'D3 = LCL_R/R̄');
      if (num(q.uclS) && num(q.sbar)) add('B4', q.uclS / q.sbar, 'B4 = UCL_s/s̄');
      if (num(q.rbar) && num(q.sigma)) add('d2', q.rbar / q.sigma, 'd2 = R̄/σ̂');
      if (num(q.sbar) && num(q.sigma)) add('c4', q.sbar / q.sigma, 'c4 = s̄/σ̂');
      var root = num(h) && num(q.sigma) && h > 0 ? 3 * q.sigma / h : null;   // UCL − X̿ = 3σ̂/√n  →  √n = 3σ̂/(UCL − X̿)
      var rows = [], scores = [];
      for (var m = 2; m <= 25; m++) {
        var c = constants(m), worst = 0;
        obs.forEach(function (o) { if (num(c[o.sym])) worst = Math.max(worst, Math.abs(c[o.sym] - o.value) / o.value); });
        if (num(root)) worst = Math.max(worst, Math.abs(Math.sqrt(m) - root) / root);
        scores.push({ n: m, worst: worst });
      }
      obs.forEach(function (o) {
        var best = null;
        for (var m = 2; m <= 25; m++) {
          var cv = K.get(o.sym, m), dev = num(cv) ? Math.abs(cv - o.value) / o.value : Infinity;
          if (!best || dev < best.dev) best = { n: m, dev: dev, constant: cv };
        }
        out.candidates.push({ label: o.label, value: o.value, n: best.n, constant: best.constant, dev: best.dev });
      });
      if (num(root)) out.candidates.push({ label: '√n = 3σ̂/(UCL − X̿)', value: root, n: Math.round(root * root), constant: Math.sqrt(Math.round(root * root)),
                                          dev: Math.abs(Math.sqrt(Math.round(root * root)) - root) / root });
      if (obs.length || num(root)) {
        scores.sort(function (a, b) { return a.worst - b.worst; });
        // 2 %: Minitab prints rounded limits (exercise 10.2 differs 0,15 % in A2); the next row must be clearly worse
        if (scores[0].worst <= 0.02 && scores[1].worst > 2 * scores[0].worst) { use = scores[0].n; out.derived.n = use; }
        else out.notes.push(scores[0].worst > 0.02 ? 'geen n in Table 18 past bij deze verhoudingen (controleer de ingevulde getallen)'
                                                   : 'meer dan één n past (' + scores[0].n + ' en ' + scores[1].n + '): vul n in');
      }
    }
    if (!num(use)) return out;
    var c = constants(use);
    out.n = use; out.c = c;
    if (num(h)) {
      out.sigmaXbar = h / 3; out.sigma = h * Math.sqrt(use) / 3;
      if (num(c.A2)) out.rbarFromX = h / c.A2;
      if (num(c.A3)) out.sbarFromX = h / c.A3;
    }
    if (num(q.uclR) && num(c.D4)) out.rbarFromR = q.uclR / c.D4;
    if (num(q.uclS) && num(c.B4)) out.sbarFromS = q.uclS / c.B4;
    // R̄ and s̄ as typed, else from the other chart, else from the X̄-chart, else from σ̂ (d2, c4)
    var first = function (list) { for (var i = 0; i < list.length; i++) if (num(list[i])) return list[i]; return null; };
    var rbar = first([q.rbar, out.rbarFromR, out.rbarFromX, num(q.sigma) && num(c.d2) ? q.sigma * c.d2 : null]);
    var sbar = first([q.sbar, out.sbarFromS, out.sbarFromX, num(q.sigma) && num(c.c4) ? q.sigma * c.c4 : null]);
    out.rbar = rbar; out.sbar = sbar;
    if (num(rbar) && num(c.d2)) out.sigmaR = rbar / c.d2;
    if (num(sbar) && num(c.c4)) out.sigmaS = sbar / c.c4;
    out.sigmaBest = first([q.sigma, out.sigmaR, out.sigmaS, out.sigma]);
    // the half width UCL − X̿: from the limits, else A2·R̄, A3·s̄ or 3σ̂/√n
    var half = first([h, num(rbar) && num(c.A2) ? c.A2 * rbar : null, num(sbar) && num(c.A3) ? c.A3 * sbar : null,
                      num(out.sigmaBest) ? 3 * out.sigmaBest / Math.sqrt(use) : null]);
    out.halfUse = half;
    if (num(h) && num(q.rbar) && num(c.A2) && Math.abs(c.A2 * q.rbar - h) / h > 0.03) out.notes.push('A2·R̄ komt niet overeen met UCL − X̿ voor deze n');
    if (num(q.uclR) && num(q.rbar) && num(c.D4) && Math.abs(c.D4 * q.rbar - q.uclR) / q.uclR > 0.03) out.notes.push('D4·R̄ komt niet overeen met UCL_R voor deze n');
    // fields the calculator can fill in (never a typed one)
    var put = function (key, value) { if (!num(q[key]) && num(value)) out.derived[key] = value; };
    put('cl', out.xbb);
    if (num(half) && num(out.xbb)) { put('ucl', out.xbb + half); put('lcl', out.xbb - half); }
    put('rbar', rbar); put('sbar', sbar); put('sigma', out.sigmaBest);
    if (num(rbar) && num(c.D4)) put('uclR', c.D4 * rbar);
    if (num(rbar) && num(c.D3)) put('lclR', c.D3 * rbar);
    if (num(sbar) && num(c.B4)) put('uclS', c.B4 * sbar);
    return out;
  }

  // Sample size, full width W and confidence 1 − α of a CI (CI p. 7, 10; CI FR p. 3): any two give the third.
  // Proportion: W = 2·z·√(p(1 − p)/n), p = 0,5 when not given (worst case); mean with σ known: W = 2·z·σ/√n.
  function sampleSizeSolve(alpha, W, n, p, sigma) {
    var pp = num(p) ? p : 0.5, up = function (x) { return Math.ceil(x - 1e-9); };
    function solve(spread) {   // spread = √(p(1 − p)) or σ
      var r = {};
      if (all(alpha, W) && !num(n)) {
        r.z = S.normInv(1 - alpha / 2); r.n = Math.pow(2 * r.z * spread / W, 2); r.nUp = up(r.n);
        r.width = 2 * r.z * spread / Math.sqrt(r.nUp); r.alpha = alpha;
      } else if (all(alpha, n) && n > 0) {
        r.z = S.normInv(1 - alpha / 2); r.width = 2 * r.z * spread / Math.sqrt(n); r.n = n; r.alpha = alpha;
      } else if (all(W, n) && n > 0) {
        r.z = W * Math.sqrt(n) / (2 * spread); r.alpha = 2 * S.normCdf(-r.z); r.n = n; r.width = W;
      } else if (num(alpha)) {   // α alone already fixes z
        r.z = S.normInv(1 - alpha / 2); r.alpha = alpha;
      } else return null;
      r.confidence = 1 - r.alpha;
      return r;
    }
    if (num(alpha) && (alpha <= 0 || alpha >= 1)) return null;
    var out = { p: pp, prop: pp > 0 && pp < 1 ? solve(Math.sqrt(pp * (1 - pp))) : null,
                mean: num(sigma) && sigma > 0 ? solve(sigma) : null };
    if (out.prop) out.prop.defectives = (num(out.prop.nUp) ? out.prop.nUp : out.prop.n) * pp;
    return out.prop || out.mean ? out : null;
  }

  // The smallest µ1 that a one-sided Z-test detects with risk β (TH FR p. 9 read backwards):
  // |µ1 − µ0| = (z_{1−α} + z_{1−β})·σ/√n.
  function detectableShift(sigma, n, alpha, beta) {
    if (!all(sigma, n, alpha, beta) || sigma <= 0 || n <= 0) return null;
    return (S.normInv(1 - alpha) + S.normInv(1 - beta)) * sigma / Math.sqrt(n);
  }

  // Quantile of a discrete distribution: the smallest k with P(X ≤ k) ≥ p (as BINOM.INV / CRITBINOM).
  function discreteQuantile(cdf, p, kMax) {
    if (!num(p) || p < 0 || p > 1) return null;
    for (var k = 0; k <= kMax; k++) if (cdf(k) >= p - 1e-12) return k;
    return kMax;
  }
  function binomialInv(n, p, q) { return all(n, p) ? discreteQuantile(function (k) { return S.binomCdf(k, n, p); }, q, n) : null; }
  function poissonInv(lam, q) { return num(lam) && lam > 0 ? discreteQuantile(function (k) { return S.poissonCdf(k, lam); }, q, 100000) : null; }
  function hypergeometricInv(N, D, n, q) {
    return all(N, D, n) ? discreteQuantile(function (k) { return S.hypergeomCdf(k, N, D, n); }, q, Math.min(n, D)) : null;
  }
  // Exponential P(T ≤ t) = 1 − e^(−λt): any two of λ, t, P give the third.
  function exponentialSolve(rate, t, pLe) {
    if (num(pLe) && (pLe <= 0 || pLe >= 1)) return null;
    if (all(rate, t)) return { rate: rate, t: t, le: 1 - Math.exp(-rate * t) };
    if (all(rate, pLe) && rate > 0) return { rate: rate, t: -Math.log(1 - pLe) / rate, le: pLe };
    if (all(t, pLe) && t > 0) return { rate: -Math.log(1 - pLe) / t, t: t, le: pLe };
    return null;
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
           },
           nu: function (g, m) {
             var gi = data.msa.g.indexOf(g), mi = data.msa.m.indexOf(m);
             return gi < 0 || mi < 0 || !data.msa.nu ? null : data.msa.nu[gi][mi];
           } }
    };
  }

  return { tables: tables, normalSolve: normalSolve, normalBetween: normalBetween, normalKSigma: normalKSigma, normalCentral: normalCentral,
           quantiles: quantiles, pValues: pValues, describe: describe, oneMean: oneMean, twoMeansPooled: twoMeansPooled,
           paired: paired, oneProportion: oneProportion, twoProportions: twoProportions, oneVariance: oneVariance,
           twoVariances: twoVariances, bernoulli: bernoulli, binomial: binomial, hypergeometric: hypergeometric,
           poisson: poisson, exponential: exponential, uniform: uniform, contingency: contingency, crossTable: crossTable,
           conditional: conditional, independence: independence, defects: defects,
           sigmaFromDpmo: sigmaFromDpmo, dpmoFromSigma: dpmoFromSigma, yields: yields, rolled: rolled,
           rollDerived: rollDerived, yieldPower: yieldPower, perOpportunity: perOpportunity, cpLevel: cpLevel,
           capability: capability, capabilityInverse: capabilityInverse, limitsSummary: limitsSummary, newSampleSize: newSampleSize, effectsAnova: effectsAnova,
           subgroupChart: subgroupChart, individuals: individuals, attributeChart: attributeChart,
           samplingPoint: samplingPoint, samplingRisks: samplingRisks, aoql: aoql, variablesPlan: variablesPlan,
           regression: regression, anova1: anova1, factorial: factorial, aliases: aliases, grr: grr, confusion: confusion,
           descriptives: descriptives, correlation: correlation, multipleRegression: multipleRegression, partialF: partialF,
           anova2: anova2, confusionK: confusionK, bayes: bayes, betaPosterior: betaPosterior,
           sampleSize: sampleSize, toleranceFactor: toleranceFactor, tolerance: tolerance, toleranceFree: toleranceFree,
           powerMean: powerMean, powerProportion: powerProportion, chi2Fit: chi2Fit, chi2Table: chi2Table,
           rankSum: rankSum, signedRank: signedRank, runsTest: runsTest, samplingVariance: samplingVariance,
           samplingMeans: samplingMeans, inverseOC: inverseOC, planSearch: planSearch, doublePlan: doublePlan,
           sprt: sprt, variablesGivenN: variablesGivenN, skipLot: skipLot, deming: deming,
           regSums: regSums, regFromSS: regFromSS, r2adj: r2adj, regTests: regTests, standardLimits: standardLimits,
           runRules: runRules, cpObserved: cpObserved, gaugePerformance: gaugePerformance,
           uncertaintyBudget: uncertaintyBudget, biasTest: biasTest, discrimination: discrimination,
           sigmaSolve: sigmaSolve, normalInterval: normalInterval, capabilitySolve: capabilitySolve,
           limitsInverse: limitsInverse, sampleSizeSolve: sampleSizeSolve, detectableShift: detectableShift,
           binomialInv: binomialInv, poissonInv: poissonInv, hypergeometricInv: hypergeometricInv,
           exponentialSolve: exponentialSolve };
})();
if (typeof module !== 'undefined') module.exports = Calc;
