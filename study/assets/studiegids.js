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

  /* ---------- collapsible parts, units and exercises: click a heading to fold or unfold it ---------- */
  var foldables = [];
  function makeFoldable(el, headSel) {
    var h = null;
    for (var c = el.firstElementChild; c; c = c.nextElementSibling) if (c.matches(headSel)) { h = c; break; }
    if (!h || !h.nextSibling) return;
    var body = document.createElement('div');
    body.className = 'sec-body';
    while (h.nextSibling) body.appendChild(h.nextSibling);
    el.appendChild(body);
    el.classList.add('foldable');
    h.classList.add('fold-head');
    h.tabIndex = 0;
    h.setAttribute('aria-expanded', 'true');
    h.title = 'Klik om in of uit te klappen';
    foldables.push(el);
  }
  function setFolded(el, folded) {
    el.classList.toggle('folded', folded);
    var h = el.querySelector(':scope > .fold-head');
    if (h) h.setAttribute('aria-expanded', folded ? 'false' : 'true');
  }
  document.querySelectorAll('section.part').forEach(function (el) { makeFoldable(el, 'h2'); });
  document.querySelectorAll('section.unit').forEach(function (el) { makeFoldable(el, 'h3'); });
  document.querySelectorAll('div.exercise').forEach(function (el) { makeFoldable(el, 'h4'); });
  document.addEventListener('click', function (e) {
    var h = e.target.closest && e.target.closest('.fold-head');
    if (!h || e.target.closest('a, button, input, select, textarea, var')) return;
    setFolded(h.parentElement, !h.parentElement.classList.contains('folded'));
  });
  document.addEventListener('keydown', function (e) {
    var h = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && h && h.classList && h.classList.contains('fold-head')) {
      e.preventDefault(); setFolded(h.parentElement, !h.parentElement.classList.contains('folded'));
    }
  });
  var foldAll = document.getElementById('fold-all'), unfoldAll = document.getElementById('unfold-all');
  if (foldAll) foldAll.addEventListener('click', function () { foldables.forEach(function (el) { setFolded(el, true); }); });
  if (unfoldAll) unfoldAll.addEventListener('click', function () { foldables.forEach(function (el) { setFolded(el, false); }); });
  // a link to something inside a folded section or a closed <details> unfolds everything around it (and the target)
  function reveal(id) {
    var el = id && document.getElementById(id);
    if (!el) return;
    if (el.classList.contains('folded')) setFolded(el, false);
    for (var p = el.parentElement; p; p = p.parentElement) {
      if (p.classList && p.classList.contains('folded')) setFolded(p, false);
      if (p.tagName === 'DETAILS') p.open = true;
    }
    // open the matching group in the table of contents and keep the link in view
    var tocLink = document.querySelector('#toc a[href="#' + id + '"]');
    if (tocLink) {
      var group = tocLink.closest('details.toc-part');
      if (group) group.open = true;
      tocLink.scrollIntoView({ block: 'nearest' });
    }
  }
  document.addEventListener('click', function (e) {   // links that open in a new tab unfold there, not here
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (a && a.target !== '_blank') reveal(decodeURIComponent(a.getAttribute('href').slice(1)));
  }, true);
  window.addEventListener('hashchange', function () { reveal(decodeURIComponent(location.hash.slice(1))); });
  if (location.hash) reveal(decodeURIComponent(location.hash.slice(1)));

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
      '<a class="more" href="#' + d.a + '" target="_blank" rel="noopener">Meer uitleg: ' + d.t.replace(/</g, '&lt;') + ' →</a>';
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
  // what the search ranks on: the title, the author keywords (data-kw) and the body of every unit, exercise, tool and table row
  var KIND = { unit: 1, tool: 0.9, exercise: 0.85, row: 0.5 };
  var blocks = [];
  document.querySelectorAll('section.unit, div.exercise, details.tool, table.gloss tr[data-kw], #formuleblad tr[data-kw], #fouten tr[data-kw]')
    .forEach(function (el) {
      var anchor = el.id ? el : el.closest('[id]');
      var kind = el.tagName === 'TR' ? 'row' : (el.tagName === 'DETAILS' ? 'tool' : (el.classList.contains('exercise') ? 'exercise' : 'unit'));
      var head = el.tagName === 'DETAILS' ? el.querySelector('summary') : (el.tagName === 'TR' ? el.querySelector('td') : el.querySelector('h3, h4'));
      blocks.push({ el: el, id: anchor ? anchor.id : '', title: blockTitle(el), part: partTitle(el), kind: kind,
                    head: norm(head ? head.textContent : ''), kw: norm(el.dataset.kw || ''), text: norm(el.textContent),
                    partHead: kind === 'row' ? '' : norm(partTitle(el)) });
    });

  // the query and its glossary translations (weight 1), the query with glossary terms translated in place (0.9),
  // and longer glossary terms that contain the query (0.6: more specific, e.g. "gepaarde t-toets" for "t-test")
  function alternatives(q) {
    var alts = [{ t: q, w: 1 }];
    if (q.length < 3) return alts;
    function add(x, w) {
      if (!x || alts.length >= 16) return;
      for (var i = 0; i < alts.length; i++) if (alts[i].t === x) { alts[i].w = Math.max(alts[i].w, w); return; }
      alts.push({ t: x, w: w });
    }
    function pairs(fn) { gloss.forEach(function (p) { fn(p[0], p[1]); fn(p[1], p[0]); }); }
    pairs(function (a, b) { if (a && b && a === q) add(b, 1); });
    pairs(function (a, b) { if (a && b && a !== q && a.indexOf(q) >= 0 && q.length >= 4) { add(a, 0.6); add(b, 0.6); } });
    var single = q.indexOf(' ') < 0;   // one (compound) word: also search the glossary terms it contains
    for (var i = 0; i < alts.length; i++) {
      var cur = alts[i];
      pairs(function (a, b) {
        if (!a || !b || a.length < 4 || a === cur.t || cur.t.indexOf(a) < 0) return;
        if (single && cur.t === q) { add(b, 0.5); add(a, 0.5); } else add(cur.t.replace(a, b), 0.9 * cur.w);
      });
    }
    return alts;
  }
  // a word of one or two characters (t, z, F, Cp) must stand on its own; longer words may sit inside a word
  function finder(w) {
    if (w.length > 2) return { has: function (h) { return h.indexOf(w) >= 0; }, count: function (h) {
      var c = 0, k = 0; while ((k = h.indexOf(w, k)) >= 0 && c < 9) { c++; k += w.length; } return c; } };
    var re = new RegExp('(^|[^a-z0-9])' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?=[^a-z0-9]|$)', 'g');
    return { has: function (h) { re.lastIndex = 0; return re.test(h); },
             count: function (h) { var c = 0; re.lastIndex = 0; while (re.exec(h) && c < 9) c++; return c; } };
  }
  // relevance of one block for one alternative; 0 when a word is missing
  function score(b, alt) {
    var words = alt.t.split(' ').filter(Boolean), finders = words.map(finder), phrase = finder(alt.t);
    var all = b.head + ' ' + b.kw + ' ' + b.text;
    if (!finders.every(function (f) { return f.has(all); })) return 0;
    var frac = function (h) { return finders.filter(function (f) { return f.has(h); }).length / finders.length; };
    var s = (phrase.has(b.head) ? 10 : 0) + 4 * frac(b.head) + (phrase.has(b.kw) ? 6 : 0) + 2 * frac(b.kw) +
            2 * Math.min(5, phrase.count(b.text)) + Math.min.apply(null, finders.map(function (f) { return Math.min(3, f.count(b.text)); })) +
            (phrase.has(b.partHead) ? 4 : 0);   // the part is about it (e.g. "regelkaart" in Deel 10)
    return s * alt.w * KIND[b.kind];
  }
  function best(b, alts) {
    var top = null;
    alts.forEach(function (a) { var v = score(b, a); if (v > 0 && (!top || v > top.score)) top = { score: v, hit: a.t }; });
    return top;
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
  function link(f) {   // a search result opens in a new tab: the tab you were reading in stays put
    var a = document.createElement('a');
    a.href = '#' + f.b.id;
    a.target = '_blank';
    a.rel = 'noopener';
    a.textContent = f.b.title || f.b.id;
    return a;
  }
  function run() {
    clearMarks();
    list.innerHTML = '';
    var q = norm(box.value);
    if (q.length < 2) { panel.hidden = true; hits.textContent = ''; return; }
    var alts = alternatives(q), found = [];
    blocks.forEach(function (b, i) { var r = best(b, alts); if (r) found.push({ b: b, hit: r.hit, score: r.score, order: i }); });
    found.sort(function (x, y) { return y.score - x.score || x.order - y.order; });
    // the best hits: units, exercises and calculators only (table rows stay under "more"), each title once (a calculator
    // sits in several parts), at most 8, and only those that score at least half of the top hit
    var top = 0, shown = [], seen = {};
    found.forEach(function (f) {
      if (f.b.kind === 'row') return;
      if (!top) top = f.score;
      if (seen[f.b.title]) { seen[f.b.title].also.push(f.b.part); f.dup = true; return; }
      if (shown.length < 8 && f.score >= 0.5 * top) { f.also = []; seen[f.b.title] = f; shown.push(f); }
    });
    var rest = found.filter(function (f) { return shown.indexOf(f) < 0 && !f.dup; });
    hits.textContent = found.length ? shown.length + ' beste van ' + found.length : 'geen treffers';
    var note = document.createElement('li');
    note.className = 'where';
    note.textContent = 'Gezocht op: ' + alts.slice(0, 6).map(function (a) { return a.t; }).join(' · ') + (alts.length > 6 ? ' …' : '');
    list.appendChild(note);
    shown.forEach(function (f) {
      var li = document.createElement('li');
      li.appendChild(link(f));
      var where = document.createElement('span');
      where.className = 'where';
      where.textContent = '  — ' + f.b.part + (f.also.length ? ' (ook in ' + f.also.map(function (p) { return p.split(' — ')[0]; }).join(', ') + ')' : '');
      li.appendChild(where);
      var sn = document.createElement('span');
      sn.className = 'snip';
      sn.textContent = snippet(f.b.text, f.hit);
      li.appendChild(sn);
      list.appendChild(li);
    });
    if (rest.length) {   // the other hits, folded, grouped per part in document order
      var li = document.createElement('li'), more = document.createElement('details'), sum = document.createElement('summary');
      li.className = 'more';
      sum.textContent = 'Meer treffers (' + rest.length + '), per deel';
      more.appendChild(sum);
      var groups = {}, order = [];
      rest.slice().sort(function (x, y) { return x.order - y.order; }).forEach(function (f) {
        if (!groups[f.b.part]) { groups[f.b.part] = []; order.push(f.b.part); }
        groups[f.b.part].push(f);
      });
      order.forEach(function (part) {
        var div = document.createElement('div');
        div.className = 'grp';
        var b = document.createElement('b');
        b.textContent = (part || 'Woordenlijst, formuleblad, fouten') + ': ';
        div.appendChild(b);
        groups[part].forEach(function (f, i) {
          if (i) div.appendChild(document.createTextNode(' · '));
          var a = link(f);
          a.title = snippet(f.b.text, f.hit);
          div.appendChild(a);
        });
        more.appendChild(div);
      });
      li.appendChild(more);
      list.appendChild(li);
    }
    found.slice(0, 120).forEach(function (f) {
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
