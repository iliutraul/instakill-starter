/* The real exam data (window.DATA) as typed arrays, the paired bootstrap, and small SVG chart helpers. */
(function () {
  const { svg, h } = U;
  const D = window.DATA;
  const c = D.cols;
  const N = c.split.length;
  const SYS = D.SYSTEMS;
  const BASE = ['chronological', 'popularity', 'for_you'];
  const NDCG = {};
  SYS.forEach((s) => { NDCG[s] = Float64Array.from(c[s], (v) => v / 1000); });
  const P = Float64Array.from(c.p, (v) => v / 1000);

  const COLORS = { chronological: '#9AA6BD', popularity: '#F7A30F', for_you: '#10ADB6', learned: '#0B2F63' };
  const LABEL = { chronological: 'chronological', popularity: 'popularity', for_you: 'for_you', learned: 'learned' };

  /** indices of the questions of a split ('val' | 'test' | 'all') that satisfy `pred(i)` */
  function idx(split = 'val', pred = null) {
    const out = [];
    for (let i = 0; i < N; i++) {
      if (split !== 'all' && (c.split[i] === 1) !== (split === 'test')) continue;
      if (pred && !pred(i)) continue;
      out.push(i);
    }
    return out;
  }
  const mean = (arr, ix) => { let s = 0; for (const i of ix) s += arr[i]; return ix.length ? s / ix.length : NaN; };
  const sysMean = (s, ix) => mean(NDCG[s], ix);
  function best(ix, among = BASE) { let b = among[0]; for (const s of among) if (sysMean(s, ix) > sysMean(b, ix)) b = s; return b; }

  function percentile(sorted, q) { const pos = (sorted.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos); return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo); }

  /** paired bootstrap of mean(a - b) over the questions ix. a/b: system names or arrays (b may be null = 0). Returns {diff, low, high, means} */
  function boot(a, b, ix, { nBoot = 1000, seed = 42, paired = true } = {}) {
    const A = typeof a === 'string' ? NDCG[a] : a, B = b == null ? null : (typeof b === 'string' ? NDCG[b] : b);
    const n = ix.length, d = new Float64Array(n), av = new Float64Array(n), bv = new Float64Array(n);
    for (let k = 0; k < n; k++) { av[k] = A[ix[k]]; bv[k] = B ? B[ix[k]] : 0; d[k] = av[k] - bv[k]; }
    const rnd = U.rng(seed), means = new Float64Array(nBoot);
    for (let r = 0; r < nBoot; r++) {
      let s = 0;
      if (paired) { for (let k = 0; k < n; k++) s += d[(rnd() * n) | 0]; }
      else { for (let k = 0; k < n; k++) s += av[(rnd() * n) | 0] - bv[(rnd() * n) | 0]; }
      means[r] = s / n;
    }
    const sorted = Float64Array.from(means).sort();
    let tot = 0; for (const v of d) tot += v;
    return { diff: tot / n, low: percentile(sorted, 0.025), high: percentile(sorted, 0.975), means, n };
  }
  const verdict = (r) => (r.low > 0 ? 'wins' : r.high < 0 ? 'loses' : 'unclear');
  const VERDICT_COLOR = { wins: '#2e8a00', loses: '#c4121e', unclear: '#b26b00' };

  /** slice definitions: name -> {labels, of(i)} */
  const UPL_BINS = [3, 10, 25, 50, 100, 200, 400, 1e9];
  const SLICES = {
    user_group: { title: 'user group', labels: D.UG, of: (i) => c.ug[i] },
    item_age_group: { title: 'age of the liked item', labels: D.IA, of: (i) => c.ia[i] },
    main_genre: { title: 'genre of the liked item', labels: D.G, of: (i) => c.g[i] },
    prior_likes: { title: 'likes of the user so far', labels: ['3-9', '10-24', '25-49', '50-99', '100-199', '200-399', '400+'],
      of: (i) => { let k = 0; while (c.upl[i] >= UPL_BINS[k + 1]) k++; return k; } },
  };
  function sliceIdx(split, slice, k) { const S = SLICES[slice]; return idx(split, (i) => S.of(i) === k); }

  /* ---------------- SVG chart helpers ---------------- */
  function frame(w, hgt) { return svg('svg', { width: w, height: hgt, viewBox: `0 0 ${w} ${hgt}`, class: 'chart' }); }
  const fmt3 = (v) => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(3);

  /** horizontal axis with ticks; returns the x-scale */
  function xAxis(g, { x0, x1, y, lo, hi, ticks, label, fmt = (v) => v.toFixed(2) }) {
    const X = (v) => x0 + (v - lo) / (hi - lo) * (x1 - x0);
    g.append(svg('line', { x1: x0, x2: x1, y1: y, y2: y, stroke: 'var(--muted)', 'stroke-width': 1 }));
    ticks.forEach((t) => {
      g.append(svg('line', { x1: X(t), x2: X(t), y1: y, y2: y + 5, stroke: 'var(--muted)' }));
      g.append(svg('text', { x: X(t), y: y + 18, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--muted)' }, fmt(t)));
    });
    if (label) g.append(svg('text', { x: (x0 + x1) / 2, y: y + 36, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 700, fill: 'var(--accent)' }, label));
    return X;
  }

  /**
   * Forest plot: rows [{label, diff, low, high, color, sub, tip}] (null row = gap), a zero line.
   */
  function forest(rows, { w = 620, rowH = 30, labelW = 250, lo = -0.55, hi = 0.3, ticks = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3], label = 'NDCG@10 of learned minus the best baseline', zero = true, tickFmt = (v) => (v > 0 ? '+' : '') + v.toFixed(1) } = {}) {
    const hgt = rows.length * rowH + 52;
    const s = frame(w, hgt), g = svg('g');
    const X = xAxis(g, { x0: labelW, x1: w - 14, y: rows.length * rowH + 4, lo, hi, ticks, label, fmt: tickFmt });
    if (zero) g.append(svg('line', { x1: X(0), x2: X(0), y1: 0, y2: rows.length * rowH + 4, stroke: 'var(--ink)', 'stroke-width': 1.5 }));
    rows.forEach((r, k) => {
      if (!r) return;
      const y = k * rowH + rowH / 2;
      const row = svg('g', { class: 'frow', 'data-tip': r.tip || `${r.label}: ${fmt3(r.diff)} (95% CI ${fmt3(r.low)} .. ${fmt3(r.high)})` });
      row.append(svg('rect', { x: 0, y: y - rowH / 2, width: w, height: rowH, fill: 'transparent' }));
      row.append(svg('text', { x: labelW - 10, y: y + 4, 'text-anchor': 'end', 'font-size': 13.5, fill: 'var(--ink)', 'font-weight': 600 }, r.label));
      if (r.sub) row.append(svg('text', { x: labelW - 10, y: y + 16, 'text-anchor': 'end', 'font-size': 10.5, fill: 'var(--muted)' }, r.sub));
      if (r.low != null) row.append(svg('line', { x1: X(Math.max(lo, r.low)), x2: X(Math.min(hi, r.high)), y1: y, y2: y, stroke: r.color, 'stroke-width': 3, 'stroke-linecap': 'round' }));
      row.append(svg('circle', { cx: X(U.clamp(r.diff, lo, hi)), cy: y, r: 6.5, fill: r.color, stroke: '#fff', 'stroke-width': 1.5 }));
      g.append(row);
    });
    s.append(g);
    return s;
  }

  /** lift rows (learned vs best baseline) for every value of a slice */
  function liftRows(split, slice, { minN = 50, against = null, nBoot = 800 } = {}) {
    const S = SLICES[slice];
    return S.labels.map((lab, k) => {
      const ix = sliceIdx(split, slice, k);
      if (ix.length < minN) return { label: lab, small: true, n: ix.length };
      const b = against || best(ix);
      const r = boot('learned', b, ix, { nBoot, seed: 7 + k });
      const v = verdict(r);
      return { label: lab, sub: `n=${ix.length} · vs ${b}`, diff: r.diff, low: r.low, high: r.high, color: VERDICT_COLOR[v], verdict: v, n: ix.length, against: b,
        tip: `${lab} (n=${ix.length}): learned ${sysMean('learned', ix).toFixed(3)} vs ${b} ${sysMean(b, ix).toFixed(3)} → ${fmt3(r.diff)}, 95% CI ${fmt3(r.low)} .. ${fmt3(r.high)} → ${v}` };
    });
  }

  /** vertical bars with optional CI whiskers. items [{label, value, low, high, color, hatch}] */
  function bars(items, { w = 460, hgt = 260, lo = 0, hi = 0.8, ticks = [0, 0.2, 0.4, 0.6, 0.8], ylabel = 'mean NDCG@10', ci = true, labelSize = 12 } = {}) {
    const s = frame(w, hgt), g = svg('g');
    const x0 = 48, x1 = w - 8, y0 = hgt - 42, y1 = 10;
    const Y = (v) => y0 - (U.clamp(v, lo, hi) - lo) / (hi - lo) * (y0 - y1);
    ticks.forEach((t) => {
      g.append(svg('line', { x1: x0, x2: x1, y1: Y(t), y2: Y(t), stroke: 'var(--border)' }));
      g.append(svg('text', { x: x0 - 6, y: Y(t) + 4, 'text-anchor': 'end', 'font-size': 11.5, fill: 'var(--muted)' }, t.toFixed(2)));
    });
    g.append(svg('text', { x: 12, y: (y0 + y1) / 2, transform: `rotate(-90 12 ${(y0 + y1) / 2})`, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 700, fill: 'var(--accent)' }, ylabel));
    const bw = (x1 - x0) / items.length;
    items.forEach((it, k) => {
      const cx = x0 + bw * (k + 0.5), bwid = Math.min(54, bw * 0.62);
      const grp = svg('g', { 'data-tip': it.tip || `${it.label}: ${it.value.toFixed(3)}${it.low != null ? ` (95% CI ${it.low.toFixed(3)} .. ${it.high.toFixed(3)})` : ''}` });
      grp.append(svg('rect', { x: cx - bwid / 2, y: Y(it.value), width: bwid, height: Math.max(0, Y(lo) - Y(it.value)), fill: it.hatch ? 'url(#hatch)' : it.color, stroke: it.hatch ? it.color : 'none', rx: 3 }));
      if (ci && it.low != null) {
        grp.append(svg('line', { x1: cx, x2: cx, y1: Y(it.low), y2: Y(it.high), stroke: 'var(--ink)', 'stroke-width': 2 }));
        [it.low, it.high].forEach((v) => grp.append(svg('line', { x1: cx - 7, x2: cx + 7, y1: Y(v), y2: Y(v), stroke: 'var(--ink)', 'stroke-width': 2 })));
      }
      grp.append(svg('text', { x: cx, y: y0 + 16, 'text-anchor': 'middle', 'font-size': labelSize, fill: 'var(--ink)', 'font-weight': 600 }, it.label));
      if (it.sub) grp.append(svg('text', { x: cx, y: y0 + 30, 'text-anchor': 'middle', 'font-size': 10.5, fill: 'var(--muted)' }, it.sub));
      g.append(grp);
    });
    g.append(svg('line', { x1: x0, x2: x1, y1: y0, y2: y0, stroke: 'var(--muted)' }));
    s.append(svg('defs', {}, svg('pattern', { id: 'hatch', width: 6, height: 6, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' },
      svg('rect', { width: 6, height: 6, fill: '#eef2f8' }), svg('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: '#9aa6bd', 'stroke-width': 2 }))));
    s.append(g);
    return s;
  }

  /** a legend row of the four systems */
  function legend(systems = SYS) {
    return h('div', { class: 'legend' }, systems.map((s) => h('span', {}, h('i', { style: { background: COLORS[s] } }), LABEL[s])));
  }

  window.Q = { D, N, SYS, BASE, NDCG, P, COLORS, LABEL, idx, mean, sysMean, best, boot, verdict, VERDICT_COLOR, SLICES, sliceIdx, frame, xAxis, forest, liftRows, bars, legend, fmt3, percentile };
})();
