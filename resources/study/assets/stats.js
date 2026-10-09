/* Statistical functions for the study guide calculators (offline, no dependencies).
   Normal: Hart/West double-precision cdf, Acklam inverse refined with Halley steps.
   Gamma/beta: Lanczos log-gamma, regularized incomplete gamma and beta (Numerical Recipes continued fractions).
   t, chi-square, F: via incomplete beta/gamma; quantiles by bisection on the cdf (left) or survival function (right).
   Discrete: binomial (via incomplete beta), hypergeometric (log-factorials), Poisson (via incomplete gamma).
   Tested against scipy in tests/test_study_tools.py. */
var Stats = (function () {
  'use strict';
  var LN_SQRT_2PI = 0.9189385332046728;

  function lgamma(x) {
    var g = 7, c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
      -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    if (x < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * x))) - lgamma(1 - x);
    x -= 1;
    var a = c[0], t = x + g + 0.5;
    for (var i = 1; i < g + 2; i++) a += c[i] / (x + i);
    return LN_SQRT_2PI + (x + 0.5) * Math.log(t) - t + Math.log(a);
  }

  /* ---- normal ---- */
  function normCdf(z) {
    if (isNaN(z)) return NaN;
    var x = Math.abs(z), c;
    if (x > 37) c = 0;
    else {
      var e = Math.exp(-x * x / 2), b;
      if (x < 7.07106781186547) {
        b = 3.52624965998911e-02 * x + 0.700383064443688;
        b = b * x + 6.37396220353165; b = b * x + 33.912866078383; b = b * x + 112.079291497871;
        b = b * x + 221.213596169931; b = b * x + 220.206867912376;
        c = e * b;
        b = 8.83883476483184e-02 * x + 1.75566716318264;
        b = b * x + 16.064177579207; b = b * x + 86.7807322029461; b = b * x + 296.564248779674;
        b = b * x + 637.333633378831; b = b * x + 793.826512519948; b = b * x + 440.413735824752;
        c = c / b;
      } else {
        b = x + 0.65; b = x + 4 / b; b = x + 3 / b; b = x + 2 / b; b = x + 1 / b;
        c = e / b / 2.506628274631;
      }
    }
    return z > 0 ? 1 - c : c;
  }
  function normSf(z) { return normCdf(-z); }
  function normPdf(z) { return Math.exp(-z * z / 2 - LN_SQRT_2PI); }
  function normInv(p) {
    if (!(p > 0 && p < 1)) return p === 0 ? -Infinity : (p === 1 ? Infinity : NaN);
    var a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
      -3.066479806614716e+01, 2.506628277459239e+00];
    var b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01,
      -1.328068155288572e+01];
    var c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00,
      4.374664141464968e+00, 2.938163982698783e+00];
    var d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
    var pl = 0.02425, x, q, r;
    if (p < pl) {
      q = Math.sqrt(-2 * Math.log(p));
      x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    } else if (p <= 1 - pl) {
      q = p - 0.5; r = q * q;
      x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
          (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    } else {
      q = Math.sqrt(-2 * Math.log(1 - p));
      x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    for (var i = 0; i < 2; i++) {   // Halley refinement; use the smaller tail for precision
      var err = p < 0.5 ? normCdf(x) - p : (1 - p) - normSf(x);
      var u = err * Math.sqrt(2 * Math.PI) * Math.exp(x * x / 2);
      x = x - u / (1 + x * u / 2);
    }
    return x;
  }

  /* ---- incomplete gamma ---- */
  function gammaP(a, x) {
    if (x <= 0) return 0;
    if (x < a + 1) {
      var ap = a, sum = 1 / a, del = sum;
      for (var n = 0; n < 1000; n++) { ap += 1; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 1e-16) break; }
      return sum * Math.exp(-x + a * Math.log(x) - lgamma(a));
    }
    return 1 - gammaQcf(a, x);
  }
  function gammaQcf(a, x) {
    var b = x + 1 - a, c = 1 / 1e-300, d = 1 / b, h = d;
    for (var i = 1; i < 1000; i++) {
      var an = -i * (i - a); b += 2;
      d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300;
      c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1 / d; var del = d * c; h *= del;
      if (Math.abs(del - 1) < 1e-16) break;
    }
    return Math.exp(-x + a * Math.log(x) - lgamma(a)) * h;
  }
  function gammaQ(a, x) { return x <= 0 ? 1 : (x < a + 1 ? 1 - gammaP(a, x) : gammaQcf(a, x)); }

  /* ---- incomplete beta ---- */
  function betacf(a, b, x) {
    var qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < 1e-300) d = 1e-300;
    d = 1 / d; var h = d;
    for (var m = 1; m <= 3000; m++) {
      var m2 = 2 * m, aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < 1e-300) d = 1e-300;
      c = 1 + aa / c; if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < 1e-300) d = 1e-300;
      c = 1 + aa / c; if (Math.abs(c) < 1e-300) c = 1e-300;
      d = 1 / d; var del = d * c; h *= del;
      if (Math.abs(del - 1) < 1e-16) break;
    }
    return h;
  }
  function betaI(x, a, b) {   // regularized incomplete beta I_x(a, b)
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    var bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    if (x < (a + 1) / (a + b + 2)) return bt * betacf(a, b, x) / a;
    return 1 - bt * betacf(b, a, 1 - x) / b;
  }

  /* ---- continuous distributions ---- */
  function tCdf(t, df) {
    var p = 0.5 * betaI(df / (df + t * t), df / 2, 0.5);
    return t > 0 ? 1 - p : p;
  }
  function tSf(t, df) { return tCdf(-t, df); }
  function chi2Cdf(x, df) { return x <= 0 ? 0 : gammaP(df / 2, x / 2); }
  function chi2Sf(x, df) { return x <= 0 ? 1 : gammaQ(df / 2, x / 2); }
  function fCdf(x, d1, d2) { return x <= 0 ? 0 : betaI(d1 * x / (d1 * x + d2), d1 / 2, d2 / 2); }
  function fSf(x, d1, d2) { return x <= 0 ? 1 : betaI(d2 / (d2 + d1 * x), d2 / 2, d1 / 2); }

  /* quantile of an increasing function f on (lo, hi): f(x) = target, by bisection */
  function solve(f, target, lo, hi, increasing) {
    var flo, fhi, k = 0;
    if (hi === undefined) { hi = 1; while ((increasing ? f(hi) < target : f(hi) > target) && k++ < 2000) hi *= 2; }
    for (var i = 0; i < 400; i++) {
      var mid = (lo + hi) / 2;
      if (mid === lo || mid === hi) break;
      var v = f(mid);
      if (increasing ? v < target : v > target) lo = mid; else hi = mid;
      if (hi - lo <= 1e-15 * Math.abs(mid) || hi - lo < 1e-300) break;   // relative: tail quantiles can be ~1e-12
    }
    return (lo + hi) / 2;
  }
  function tInv(p, df) {   // left quantile: P(T <= x) = p
    if (!(p > 0 && p < 1)) return NaN;
    if (p === 0.5) return 0;
    var x = p < 0.5 ? solve(function (v) { return tCdf(-v, df); }, p, 0, undefined, false) : solve(function (v) { return tSf(v, df); }, 1 - p, 0, undefined, false);
    return p < 0.5 ? -x : x;
  }
  function chi2Inv(p, df) { return p < 0.5 ? solve(function (v) { return chi2Cdf(v, df); }, p, 0, undefined, true) : chi2Isf(1 - p, df); }
  function chi2Isf(q, df) { return solve(function (v) { return chi2Sf(v, df); }, q, 0, undefined, false); }
  function fInv(p, d1, d2) { return p < 0.5 ? solve(function (v) { return fCdf(v, d1, d2); }, p, 0, undefined, true) : fIsf(1 - p, d1, d2); }
  function fIsf(q, d1, d2) { return solve(function (v) { return fSf(v, d1, d2); }, q, 0, undefined, false); }
  function betaInv(p, a, b) { return solve(function (v) { return betaI(v, a, b); }, p, 0, 1, true); }

  /* ---- discrete distributions ---- */
  function lchoose(n, k) { return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1); }
  function binomPmf(k, n, p) {
    if (k < 0 || k > n || k !== Math.floor(k)) return 0;
    if (p === 0) return k === 0 ? 1 : 0;
    if (p === 1) return k === n ? 1 : 0;
    return Math.exp(lchoose(n, k) + k * Math.log(p) + (n - k) * Math.log(1 - p));
  }
  function binomCdf(k, n, p) {
    k = Math.floor(k);
    if (k < 0) return 0;
    if (k >= n) return 1;
    if (p === 0) return 1;
    if (p === 1) return 0;
    return betaI(1 - p, n - k, k + 1);
  }
  function hypergeomPmf(k, N, K, n) {   // k defectives in a sample of n from N items with K defectives
    if (k < Math.max(0, n + K - N) || k > Math.min(n, K) || k !== Math.floor(k)) return 0;
    return Math.exp(lchoose(K, k) + lchoose(N - K, n - k) - lchoose(N, n));
  }
  function hypergeomCdf(k, N, K, n) {
    var s = 0, lo = Math.max(0, n + K - N);
    for (var i = lo; i <= Math.min(Math.floor(k), n, K); i++) s += hypergeomPmf(i, N, K, n);
    return Math.min(1, s);
  }
  function poissonPmf(k, lam) { return k < 0 || k !== Math.floor(k) ? 0 : Math.exp(-lam + k * Math.log(lam) - lgamma(k + 1)); }
  function poissonCdf(k, lam) { k = Math.floor(k); return k < 0 ? 0 : gammaQ(k + 1, lam); }

  /* ---- descriptive ---- */
  function mean(xs) { var s = 0; for (var i = 0; i < xs.length; i++) s += xs[i]; return s / xs.length; }
  function devsq(xs) { var m = mean(xs), s = 0; for (var i = 0; i < xs.length; i++) s += (xs[i] - m) * (xs[i] - m); return s; }
  function sd(xs) { return Math.sqrt(devsq(xs) / (xs.length - 1)); }

  return {
    lgamma: lgamma, normCdf: normCdf, normSf: normSf, normPdf: normPdf, normInv: normInv,
    gammaP: gammaP, gammaQ: gammaQ, betaI: betaI,
    tCdf: tCdf, tSf: tSf, tInv: tInv, chi2Cdf: chi2Cdf, chi2Sf: chi2Sf, chi2Inv: chi2Inv, chi2Isf: chi2Isf,
    fCdf: fCdf, fSf: fSf, fInv: fInv, fIsf: fIsf, betaInv: betaInv,
    lchoose: lchoose, binomPmf: binomPmf, binomCdf: binomCdf, hypergeomPmf: hypergeomPmf, hypergeomCdf: hypergeomCdf,
    poissonPmf: poissonPmf, poissonCdf: poissonCdf, mean: mean, devsq: devsq, sd: sd
  };
})();
if (typeof module !== 'undefined') module.exports = Stats;
