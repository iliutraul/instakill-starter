/* Deck engine: scaling, navigation, notes, overview, tooltips, lazy widget mounting. */
(function () {
  const { h } = U;

  const SEGMENTS = [
    { id: 'intro', label: 'Opening', color: '--navy' },
    { id: 'clinic', label: 'Failure clinic', color: '--gold' },
    { id: 'theory', label: 'Theory', color: '--purple' },
    { id: 'live', label: 'Live experiment', color: '--teal' },
    { id: 'reveal', label: 'Challenge reveal', color: '--green' },
  ];

  const store = {
    get(k, d) { try { const v = localStorage.getItem('dirty-data.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('dirty-data.' + k, JSON.stringify(v)); } catch (e) { /* storage may be blocked: the deck works without it */ } },
  };

  const registry = {};
  const Deck = {
    SEGMENTS, store, reduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
    register(name, factory) { registry[name] = factory; },
    index: 0, slides: [], goto: null,
  };
  window.Deck = Deck;

  const mounted = new Map();

  function mountWidgets(slide) {
    slide.querySelectorAll('[data-widget]').forEach((node) => {
      if (mounted.has(node)) return;
      const name = node.dataset.widget;
      const factory = registry[name];
      if (!factory) { node.append(h('p', { class: 'warn' }, `Widget "${name}" is not available.`)); return; }
      try {
        const api = factory(node, node.dataset) || {};
        mounted.set(node, api);
      } catch (err) {
        console.error('widget failed:', name, err);
        node.append(h('p', { class: 'warn' }, `Widget "${name}" failed to load: ${err.message}`));
        mounted.set(node, {});
      }
    });
  }

  function init() {
    if (Deck.reduced) document.documentElement.classList.add('reduced');
    const stage = document.getElementById('stage');
    const slides = Deck.slides = [...document.querySelectorAll('.slide')];
    const N = slides.length;

    // ---- chrome: segment chip, counters, progress ----
    const chip = document.getElementById('seg-chip');
    const counter = document.getElementById('counter');
    const progress = document.getElementById('progress-bar');
    const notesPanel = document.getElementById('notes');
    const notesBody = document.getElementById('notes-body');

    function segOf(slide) { return SEGMENTS.find((s) => s.id === slide.dataset.segment) || SEGMENTS[0]; }

    function show(i, opts = {}) {
      i = U.clamp(i, 0, N - 1);
      const prev = Deck.index;
      slides.forEach((s, k) => {
        s.classList.toggle('active', k === i);
        s.classList.toggle('past', k < i);
        s.setAttribute('aria-hidden', String(k !== i));
        s.inert = k !== i;
      });
      Deck.index = i;
      const slide = slides[i], seg = segOf(slide);
      mountWidgets(slide);
      // pause the widgets of the slide we left, start the ones we entered
      slides[prev] && slides[prev].querySelectorAll('[data-widget]').forEach((n) => { const a = mounted.get(n); a && a.hide && a.hide(); });
      slide.querySelectorAll('[data-widget]').forEach((n) => { const a = mounted.get(n); a && a.show && a.show(); });
      chip.textContent = seg.label;
      chip.style.setProperty('--chip', `var(${seg.color})`);
      counter.textContent = `${i + 1} / ${N}`;
      progress.style.width = `${(i / (N - 1)) * 100}%`;
      notesBody.innerHTML = '';
      const n = slide.querySelector('.notes');
      notesBody.append(h('h3', {}, slide.dataset.title || `Slide ${i + 1}`));
      if (n) notesBody.insertAdjacentHTML('beforeend', n.innerHTML);
      else notesBody.append(h('p', {}, 'No notes for this slide.'));
      if (!opts.silent) history.replaceState(null, '', '#' + (i + 1));
    }
    Deck.goto = show;

    // ---- scaling ----
    function fit() {
      const s = Math.min(innerWidth / 1280, innerHeight / 720);
      stage.style.transform = `translate(-50%, -50%) scale(${s})`;
    }
    addEventListener('resize', fit); fit();

    // ---- overlays ----
    const overlays = { overview: document.getElementById('overview'), help: document.getElementById('help'), notes: notesPanel };
    function toggle(name, force) {
      const el = overlays[name];
      const on = force == null ? !el.classList.contains('open') : force;
      el.classList.toggle('open', on);
      el.setAttribute('aria-hidden', String(!on));
      if (name === 'notes') store.set('open.' + name, on);
    }
    Deck.toggle = toggle;

    // overview grid
    const ov = document.getElementById('overview-grid');
    let lastSeg = null;
    slides.forEach((s, k) => {
      const seg = segOf(s);
      if (seg.id !== lastSeg) {
        ov.append(h('h4', { style: { '--chip': `var(${seg.color})` } }, seg.label));
        lastSeg = seg.id;
      }
      ov.append(h('button', { class: 'ov-tile', type: 'button', 'data-tip': 'Jump to this slide.', style: { '--chip': `var(${seg.color})` }, onclick: () => { toggle('overview', false); show(k); } },
        h('b', {}, String(k + 1)), h('span', {}, s.dataset.title || '')));
    });


    // ---- tooltips: immediate, readable on a projector, also for keyboard focus ----
    const tipEl = document.getElementById('tip');
    let tipTimer = null, tipFor = null;
    const norm = (t) => (t || '').replace(/\s+/g, ' ').trim();
    function tipText(el) {
      const widget = (el.closest('[data-widget]') || {}).dataset ? el.closest('[data-widget]').dataset.widget : (el.closest('.chrome') ? 'chrome' : '');
      let label = '';
      if (el.matches('input[type=range]')) { const l = el.closest('label.slider'); label = l ? norm(l.querySelector('.lab').childNodes[0].textContent) : ''; }
      else if (el.matches('select')) label = norm(el.getAttribute('aria-label'));
      else if (el.matches('input[type=checkbox]')) label = el.id || norm((el.closest('label') || {}).textContent);
      else label = norm(el.textContent);
      const T = window.TIPS || {};
      return T[widget + ':' + label] || T['*:' + label] || el.dataset.tip || '';
    }
    function showTip(el) {
      const text = tipText(el); if (!text) return;
      tipFor = el; tipEl.textContent = text; tipEl.classList.add('on');
      const sr = stage.getBoundingClientRect(), k = sr.width / 1280, r = el.getBoundingClientRect();
      const x0 = (r.left - sr.left) / k, y0 = (r.top - sr.top) / k, w = tipEl.offsetWidth, hgt = tipEl.offsetHeight;
      let x = U.clamp(x0 + (r.width / k) / 2 - w / 2, 8, 1272 - w), y = y0 - hgt - 10;
      if (y < 58) y = (r.bottom - sr.top) / k + 10;
      tipEl.style.left = x + 'px'; tipEl.style.top = y + 'px';
    }
    function hideTip() { clearTimeout(tipTimer); tipEl.classList.remove('on'); tipFor = null; }
    const TARGETS = 'button, select, input[type=range], input[type=checkbox], [role=tab]';
    document.addEventListener('pointerover', (e) => { const el = e.target.closest && e.target.closest(TARGETS); if (!el || el === tipFor) return; hideTip(); tipTimer = setTimeout(() => showTip(el), 220); });
    document.addEventListener('pointerout', (e) => { if (e.target.closest && e.target.closest(TARGETS)) hideTip(); });
    document.addEventListener('pointerdown', hideTip);
    document.addEventListener('focusin', (e) => { const el = e.target.closest && e.target.closest(TARGETS); if (el && e.target.matches(':focus-visible')) showTip(el); });
    document.addEventListener('focusout', hideTip);
    slides.forEach((sl) => sl.addEventListener('transitionstart', hideTip));

    // ---- chrome buttons ----
    const bind = (id, fn) => document.getElementById(id).addEventListener('click', fn);
    bind('btn-prev', () => show(Deck.index - 1)); bind('btn-next', () => show(Deck.index + 1));
    bind('btn-overview', () => toggle('overview')); bind('btn-notes', () => toggle('notes'));
    bind('btn-help', () => toggle('help')); bind('btn-full', fullscreen);
    document.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => toggle(b.dataset.close, false)));
    function fullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen && document.documentElement.requestFullscreen(); }

    // ---- keyboard ----
    addEventListener('keydown', (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const tag = (e.target.tagName || '').toLowerCase();
      const typing = tag === 'input' || tag === 'select' || tag === 'textarea' || e.target.isContentEditable;
      if (typing && !(e.key === 'Escape')) return;
      switch (e.key) {
        case 'ArrowRight': case 'PageDown': show(Deck.index + 1); break;
        case ' ': if (tag === 'button' || tag === 'a') return; show(Deck.index + (e.shiftKey ? -1 : 1)); break;
        case 'ArrowLeft': case 'PageUp': show(Deck.index - 1); break;
        case 'Home': show(0); break;
        case 'End': show(N - 1); break;
        case 'g': case 'G': toggle('overview'); break;
        case 'n': case 'N': toggle('notes'); break;
        case 'f': case 'F': fullscreen(); break;
        case '?': toggle('help'); break;
        case 'Escape': Object.keys(overlays).forEach((k) => { if (k !== 'notes') toggle(k, false); }); break;
        default: return;
      }
      e.preventDefault();
    });
    // sliders keep keyboard focus after a drag, which would swallow the arrow keys: hand focus back to the deck
    addEventListener('pointerup', () => { const a = document.activeElement; if (a && a.type === 'range') a.blur(); });

    // ---- start ----
    if (store.get('open.notes', false)) toggle('notes', true);
    const start = parseInt(location.hash.slice(1), 10);
    show(Number.isFinite(start) ? start - 1 : 0, { silent: true });
    addEventListener('hashchange', () => { const k = parseInt(location.hash.slice(1), 10); if (Number.isFinite(k) && k - 1 !== Deck.index) show(k - 1, { silent: true }); });
    document.documentElement.classList.add('ready');
  }

  document.addEventListener('DOMContentLoaded', init);
})();
