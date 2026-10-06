/* Studiegids Black Belt: exercise checking and bilingual search. Offline, no dependencies. */
(function () {
  'use strict';

  /* ---------- exercises ---------- */
  function parseNumber(text) {
    var t = String(text).trim().replace(/\s/g, '').replace(/%$/, '');
    if (/^-?\d{1,3}(\.\d{3})+,\d+$/.test(t)) t = t.replace(/\./g, '');   // 1.234,5 (Dutch thousands)
    t = t.replace(',', '.');
    if (!/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(t)) return NaN;
    return parseFloat(t);
  }
  document.querySelectorAll('.exercise .q').forEach(function (q) {
    var button = q.querySelector('button.check');
    var fb = q.querySelector('.fb');
    var field = q.querySelector('input, select');
    if (!button || !fb || !field) return;
    function check() {
      var ok;
      if (q.dataset.type === 'choice') {
        ok = field.value !== '' && field.value === q.dataset.answer;
      } else {
        var x = parseNumber(field.value), a = parseFloat(q.dataset.answer), tol = parseFloat(q.dataset.tol || '0');
        if (isNaN(x)) { fb.textContent = 'Geef een getal (komma of punt).'; fb.className = 'fb bad'; return; }
        ok = Math.abs(x - a) <= tol + 1e-12 * Math.max(1, Math.abs(a));
      }
      fb.textContent = ok ? '✓ juist' : '✗ niet juist — probeer opnieuw of open de oplossing';
      fb.className = 'fb ' + (ok ? 'ok' : 'bad');
    }
    button.addEventListener('click', check);
    field.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); check(); } });
  });

  /* ---------- clickable variables: <var data-s="NN:key"> opens a short explanation (NN_symbols.tsv) ---------- */
  var symbols = {};
  try { symbols = JSON.parse(document.getElementById('symbols-data').textContent); } catch (e) { symbols = {}; }
  var pop = document.createElement('div');
  pop.id = 'sympop';
  pop.hidden = true;
  pop.setAttribute('role', 'dialog');
  document.body.appendChild(pop);
  var current = null;
  function hidePop() { pop.hidden = true; if (current) current.classList.remove('on'); current = null; }
  function showPop(v) {
    var d = symbols[v.dataset.s];
    if (!d) return;
    if (current) current.classList.remove('on');
    current = v; v.classList.add('on');
    pop.innerHTML = '<button type="button" class="x" aria-label="sluit">×</button><div class="sym">' + d.s + '</div>' +
      '<p class="what">' + d.b + '</p><p class="how"><b>Hoe bekom je het?</b> ' + d.h + '</p>' +
      '<a class="more" href="#' + d.a + '">Meer uitleg: ' + d.t.replace(/</g, '&lt;') + ' →</a>';
    pop.hidden = false;
    var r = v.getBoundingClientRect(), w = Math.min(380, window.innerWidth - 24);
    pop.style.width = w + 'px';
    pop.style.left = Math.max(12, Math.min(window.scrollX + r.left, window.scrollX + window.innerWidth - w - 12)) + 'px';
    pop.style.top = (window.scrollY + r.bottom + 6) + 'px';
  }
  document.querySelectorAll('var[data-s]').forEach(function (v) { v.tabIndex = 0; });
  document.addEventListener('click', function (e) {
    var v = e.target.closest && e.target.closest('var[data-s]');
    if (v) { e.preventDefault(); if (current === v) hidePop(); else showPop(v); return; }
    if (e.target.closest && e.target.closest('#sympop a.more')) { hidePop(); return; }
    if (!(e.target.closest && e.target.closest('#sympop')) || e.target.classList.contains('x')) hidePop();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') hidePop();
    if (e.key === 'Enter' && document.activeElement && document.activeElement.matches('var[data-s]')) showPop(document.activeElement);
  });

  /* ---------- search ---------- */
  function norm(s) {
    return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  }
  var pairs = [];
  try { pairs = JSON.parse(document.getElementById('glossary-data').textContent); } catch (e) { pairs = []; }
  var gloss = pairs.map(function (p) { return [norm(p[0]), norm(p[1])]; });

  function partTitle(el) {
    var part = el.closest('section.part');
    return part ? (part.dataset.title || (part.querySelector('h2') || {}).textContent || '') : '';
  }
  function blockTitle(el) {
    if (el.tagName === 'DETAILS') return el.querySelector('summary').textContent.trim();
    var h = el.querySelector('h4, h3');
    if (h) return h.textContent.replace(/\s+/g, ' ').trim();
    var td = el.querySelector('td');
    return td ? td.textContent.trim() : '';
  }
  var blocks = [];
  document.querySelectorAll('section.unit, div.exercise, details.tool, table.gloss tr[data-kw], #formuleblad tr[data-kw], #fouten tr[data-kw]')
    .forEach(function (el) {
      var anchor = el.id ? el : el.closest('[id]');
      blocks.push({ el: el, id: anchor ? anchor.id : '', title: blockTitle(el), part: partTitle(el),
                    text: norm(el.textContent + ' ' + (el.dataset.kw || '')) });
    });

  // the query, its glossary translations, and the query with every glossary term in it translated in place
  // ("pitfall p-value" -> "valkuil p-value", "pitfall p-waarde", "valkuil p-waarde")
  function alternatives(q) {
    var alts = [q];
    if (q.length < 3) return alts;
    function add(x) { if (x && alts.indexOf(x) < 0 && alts.length < 16) alts.push(x); }
    function pairs(fn) { gloss.forEach(function (p) { fn(p[0], p[1]); fn(p[1], p[0]); }); }
    pairs(function (a, b) { if (a && b && (a === q || (a.indexOf(q) >= 0 && q.length >= 4))) { add(b); add(a); } });
    var single = q.indexOf(' ') < 0;   // one (compound) word: also search the glossary terms it contains, as before
    for (var i = 0; i < alts.length; i++) {
      var cur = alts[i];
      pairs(function (a, b) {
        if (!a || !b || a.length < 4 || a === cur || cur.indexOf(a) < 0) return;
        if (single && cur === q) { add(b); add(a); } else add(cur.replace(a, b));
      });
    }
    return alts;
  }
  function matches(text, alts) {
    for (var i = 0; i < alts.length; i++) {
      var words = alts[i].split(' ');
      var all = words.every(function (w) { return text.indexOf(w) >= 0; });
      if (all) return alts[i];
    }
    return null;
  }

  var marked = [];
  function clearMarks() {
    marked.forEach(function (m) {
      var parent = m.parentNode;
      if (!parent) return;
      parent.replaceChild(document.createTextNode(m.textContent), m);
      parent.normalize();
    });
    marked = [];
  }
  function highlight(el, words) {
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      if (!node.parentNode || node.parentNode.closest('script, style, mark, input, select, option')) return;
      var raw = node.textContent, low = norm(raw);
      if (low.length !== raw.length) return;   // skip nodes where normalisation changes length
      var hits = [];
      words.forEach(function (w) {
        var from = 0, k;
        while (w && (k = low.indexOf(w, from)) >= 0) { hits.push([k, k + w.length]); from = k + w.length; }
      });
      if (!hits.length) return;
      hits.sort(function (a, b) { return a[0] - b[0]; });
      var frag = document.createDocumentFragment(), pos = 0;
      hits.forEach(function (h) {
        if (h[0] < pos) return;
        frag.appendChild(document.createTextNode(raw.slice(pos, h[0])));
        var m = document.createElement('mark');
        m.textContent = raw.slice(h[0], h[1]);
        frag.appendChild(m); marked.push(m);
        pos = h[1];
      });
      frag.appendChild(document.createTextNode(raw.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });
  }
  function snippet(text, phrase) {
    var w = phrase.split(' ')[0], k = text.indexOf(w);
    if (k < 0) k = 0;
    var s = Math.max(0, k - 60), e = Math.min(text.length, k + 110);
    return (s > 0 ? '…' : '') + text.slice(s, e) + (e < text.length ? '…' : '');
  }

  var box = document.getElementById('q'), hits = document.getElementById('hits');
  var panel = document.getElementById('zoek-resultaten'), list = document.getElementById('results');
  var timer = null;
  function run() {
    clearMarks();
    list.innerHTML = '';
    var q = norm(box.value);
    if (q.length < 2) { panel.hidden = true; hits.textContent = ''; return; }
    var alts = alternatives(q), found = [];
    blocks.forEach(function (b) {
      var hit = matches(b.text, alts);
      if (hit) found.push({ b: b, hit: hit });
    });
    // units and exercises first, then glossary/formula/errata rows; keep document order within each group
    found.sort(function (x, y) {
      var gx = x.b.el.tagName === 'TR' ? 1 : 0, gy = y.b.el.tagName === 'TR' ? 1 : 0;
      return gx - gy;
    });
    hits.textContent = found.length + ' treffer' + (found.length === 1 ? '' : 's');
    var note = document.createElement('li');
    note.className = 'where';
    note.textContent = 'Gezocht op: ' + alts.join(' · ');
    list.appendChild(note);
    found.slice(0, 80).forEach(function (f) {
      var li = document.createElement('li'), a = document.createElement('a');
      a.href = '#' + f.b.id;
      a.textContent = f.b.title || f.b.id;
      li.appendChild(a);
      var where = document.createElement('span');
      where.className = 'where';
      where.textContent = '  — ' + f.b.part;
      li.appendChild(where);
      var sn = document.createElement('span');
      sn.className = 'snip';
      sn.textContent = snippet(f.b.text, f.hit);
      li.appendChild(sn);
      list.appendChild(li);
      highlight(f.b.el, f.hit.split(' ').filter(function (w) { return w.length >= 2; }));
    });
    panel.hidden = false;
  }
  box.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 220); });
  box.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      clearTimeout(timer); run();
      var first = list.querySelector('li a');
      panel.scrollIntoView({ block: 'start' });
      if (first && e.shiftKey) first.click();
    }
    if (e.key === 'Escape') { box.value = ''; run(); }
  });
  document.getElementById('clear').addEventListener('click', function () { box.value = ''; run(); box.focus(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== box && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) {
      e.preventDefault(); box.focus(); box.select();
    }
  });
})();
