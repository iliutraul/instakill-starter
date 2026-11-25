/* Small helpers shared by the deck engine and the widgets. No dependencies. */
(function () {
  const SVGNS = 'http://www.w3.org/2000/svg';

  /** h('div', {class:'x', onclick:fn, style:{color:'red'}}, child, 'text') */
  function h(tag, attrs, ...children) {
    const svgMode = tag.startsWith('svg:');
    const el = svgMode ? document.createElementNS(SVGNS, tag.slice(4)) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') el.setAttribute('class', v);
      else if (k === 'style' && typeof v === 'object') { for (const [sk, sv] of Object.entries(v)) { if (sk.startsWith('--')) el.style.setProperty(sk, sv); else el.style[sk] = sv; } }
      else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
      else if (k === 'html') el.innerHTML = v;
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      el.append(c.nodeType ? c : document.createTextNode(String(c)));
    }
    return el;
  }
  const svg = (tag, attrs, ...children) => h('svg:' + tag, attrs, ...children);

  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const fmt = (x, d = 2) => (Number.isFinite(x) ? x.toFixed(d) : String(x));
  const sigmoid = (z) => 1 / (1 + Math.exp(-clamp(z, -60, 60)));

  /** deterministic RNG (mulberry32) so every classroom run looks the same */
  function rng(seed) {
    let a = seed >>> 0;
    const next = () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    next.normal = () => {
      const u = 1 - next(), v = next();
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    };
    return next;
  }

  /** read a CSS custom property of the current theme (so canvases follow dark mode) */
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  /** labelled range input. Returns {el, get, set}. */
  function slider({ label, min = 0, max = 1, step = 0.01, value = 0, digits = 2, unit = '', hint = '', onInput, log = false, id, format }) {
    const toPos = (v) => (log ? Math.log10(v) : v);
    const fromPos = (p) => (log ? Math.pow(10, p) : p);
    const input = h('input', { type: 'range', min: toPos(min), max: toPos(max), step: log ? 0.01 : step, value: toPos(value), 'aria-label': label, id });
    const out = h('output', { class: 'val' });
    const row = h('label', { class: 'slider' }, h('span', { class: 'lab' }, label, hint ? h('small', {}, hint) : null), input, out);
    const get = () => fromPos(parseFloat(input.value));
    const show = () => { out.textContent = (format ? format(get()) : fmt(get(), digits)) + unit; };
    input.addEventListener('input', () => { show(); onInput && onInput(get()); });
    show();
    return { el: row, get, set(v) { input.value = toPos(v); show(); }, input };
  }

  function button(label, onClick, cls = '') {
    return h('button', { class: 'btn ' + cls, type: 'button', onclick: onClick }, label);
  }

  /** segmented control. options: [{value,label}] */
  function segmented(options, value, onChange, aria = '') {
    const wrap = h('div', { class: 'seg', role: 'group', 'aria-label': aria });
    const btns = options.map((o) => {
      const b = h('button', { type: 'button', class: 'seg-btn', 'aria-pressed': String(o.value === value), onclick: () => set(o.value, true) }, o.label);
      wrap.append(b);
      return [o.value, b];
    });
    let cur = value;
    function set(v, fire) {
      cur = v;
      btns.forEach(([val, b]) => b.setAttribute('aria-pressed', String(val === v)));
      if (fire && onChange) onChange(v);
    }
    return { el: wrap, get: () => cur, set };
  }

  /** run `fn` on animation frames while `active()` is true; returns {start, stop} */
  function loop(fn) {
    let id = 0, running = false;
    const tick = (t) => { if (!running) return; fn(t); id = requestAnimationFrame(tick); };
    return {
      start() { if (!running) { running = true; id = requestAnimationFrame(tick); } },
      stop() { running = false; cancelAnimationFrame(id); },
      get running() { return running; },
    };
  }

  function u8(b64) {
    const s = atob(b64);
    const a = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
    return a;
  }

  /** HiDPI canvas helper: returns {canvas, ctx, w, h} drawn in CSS pixels */
  function canvas(w, hgt, cls = '') {
    const c = h('canvas', { class: cls });
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    c.width = w * dpr; c.height = hgt * dpr;
    c.style.width = w + 'px'; c.style.height = hgt + 'px';
    const ctx = c.getContext('2d');
    ctx.scale(dpr, dpr);
    return { canvas: c, ctx, w, h: hgt };
  }

  /** copy-to-clipboard code block */
  function codeBlock(text, lang = 'python') {
    const pre = h('pre', { class: 'code', 'data-lang': lang }, h('code', {}, text));
    const b = button('Copy', () => {
      const done = () => { b.textContent = 'Copied'; setTimeout(() => (b.textContent = 'Copy'), 1200); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, done); else done();
    }, 'ghost small copy');
    return h('div', { class: 'codewrap' }, b, pre);
  }

  window.U = { h, svg, clamp, lerp, fmt, sigmoid, rng, css, slider, button, segmented, loop, u8, canvas, codeBlock };
})();
