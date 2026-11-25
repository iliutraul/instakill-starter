/* Theory widgets: misleading vs clear charts, anatomy of a figure, the time-split replay. */
(function () {
  const { h, svg, button, segmented } = U;

  /* ===================== clearcharts: misleading vs clear, same data ===================== */
  function heatCell(v, cmap) {
    if (cmap === 'jet') {           // a rainbow on an uncentred range: the classic mistake
      const t = U.clamp((v + 0.45) / 0.7, 0, 1);
      const stops = [[0, [0, 0, 143]], [0.125, [0, 0, 255]], [0.375, [0, 255, 255]], [0.625, [255, 255, 0]], [0.875, [255, 0, 0]], [1, [128, 0, 0]]];
      let k = 0; while (k < stops.length - 2 && t > stops[k + 1][0]) k++;
      const [ta, ca] = stops[k], [tb, cb] = stops[k + 1], f = (t - ta) / (tb - ta);
      return `rgb(${ca.map((x, i) => Math.round(x + (cb[i] - x) * f)).join(',')})`;
    }
    const t = U.clamp(v / 0.45, -1, 1);            // diverging, centred on 0: red below, blue above
    const a = Math.abs(t), base = t < 0 ? [196, 18, 30] : [33, 102, 172];
    return `rgb(${base.map((x) => Math.round(255 + (x - 255) * a)).join(',')})`;
  }
  function heatmap(cmap) {
    const s = Q.frame(470, 270), x0 = 150, y0 = 20, cw = 76, ch = 48;
    Q.D.UG.forEach((ug, r) => {
      s.append(svg('text', { x: x0 - 8, y: y0 + r * ch + ch / 2 + 4, 'text-anchor': 'end', 'font-size': 12, fill: 'var(--ink)' }, ug));
      Q.D.IA.forEach((ia, c) => {
        const ix = Q.idx('val', (i) => Q.D.cols.ug[i] === r && Q.D.cols.ia[i] === c);
        const v = ix.length ? Q.sysMean('learned', ix) - Q.sysMean(Q.best(ix), ix) : 0;
        s.append(svg('rect', { x: x0 + c * cw, y: y0 + r * ch, width: cw - 2, height: ch - 2, fill: heatCell(v, cmap), 'data-tip': `${ug} × ${ia}: ${Q.fmt3(v)} (n=${ix.length})` }));
        s.append(svg('text', { x: x0 + c * cw + cw / 2, y: y0 + r * ch + ch / 2 + 4, 'text-anchor': 'middle', 'font-size': 11, fill: Math.abs(v) > 0.25 || cmap === 'jet' ? '#fff' : '#12182b', 'font-weight': 700 }, (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(2)));
      });
    });
    Q.D.IA.forEach((ia, c) => s.append(svg('text', { x: x0 + c * cw + cw / 2, y: y0 + 4 * ch + 14, 'text-anchor': 'middle', 'font-size': 11.5, fill: 'var(--ink)' }, ia)));
    s.append(svg('text', { x: x0 + 2 * cw, y: y0 + 4 * ch + 32, 'text-anchor': 'middle', 'font-size': 12, 'font-weight': 700, fill: 'var(--accent)' }, 'age of the liked movie · cell = trained model − best simple feed'));
    return s;
  }
  function overallBars(withCI, lo) {
    const ix = Q.idx('val');
    const items = ['popularity', 'learned'].map((sys) => { const r = Q.boot(sys, null, ix, { nBoot: 400, seed: 2 }); return { label: sys, value: r.diff, low: withCI ? r.low : null, high: r.high, color: Q.COLORS[sys] }; });
    return Q.bars(items, { w: 380, hgt: 270, lo, hi: lo ? 0.46 : 0.5, ticks: lo ? [0.37, 0.39, 0.41, 0.43, 0.45] : [0, 0.1, 0.2, 0.3, 0.4, 0.5] });
  }
  function genreBars(withCI) {
    const items = [];
    [0, 1, 2, 5].forEach((k) => {
      const ix = Q.sliceIdx('val', 'main_genre', k);
      ['popularity', 'learned'].forEach((sys) => { const r = Q.boot(sys, null, ix, { nBoot: 300, seed: 4 }); items.push({ label: sys === 'learned' ? Q.D.G[k] : '', sub: sys === 'learned' && withCI ? `n=${ix.length}` : '', value: r.diff, low: withCI ? r.low : null, high: r.high, color: Q.COLORS[sys] }); });
    });
    return Q.bars(items, { w: 470, hgt: 270, hi: 0.7, ticks: [0, 0.2, 0.4, 0.6], labelSize: 11.5 });
  }
  function pieScores() {
    const ix = Q.idx('val'), vals = Q.SYS.map((sys) => Q.sysMean(sys, ix)), tot = vals.reduce((a, b) => a + b, 0);
    const sv = Q.frame(470, 270), cx = 150, cy = 135, r = 110;
    let a0 = -Math.PI / 2;
    Q.SYS.forEach((sys, k) => {
      const a1 = a0 + 2 * Math.PI * vals[k] / tot, big = a1 - a0 > Math.PI ? 1 : 0;
      sv.append(svg('path', { d: `M${cx},${cy} L${cx + r * Math.cos(a0)},${cy + r * Math.sin(a0)} A${r},${r} 0 ${big} 1 ${cx + r * Math.cos(a1)},${cy + r * Math.sin(a1)} Z`, fill: Q.COLORS[sys], stroke: '#fff', 'stroke-width': 2, 'data-tip': `${sys}: ${vals[k].toFixed(3)}` }));
      sv.append(svg('rect', { x: 300, y: 70 + k * 34, width: 16, height: 16, fill: Q.COLORS[sys], rx: 3 }));
      sv.append(svg('text', { x: 324, y: 83 + k * 34, 'font-size': 13.5, fill: 'var(--ink)' }, `${sys} ${(100 * vals[k] / tot).toFixed(0)}%`));
      a0 = a1;
    });
    return sv;
  }
  function scoreBars() {
    const ix = Q.idx('val');
    return Q.bars(Q.SYS.map((sys) => { const r = Q.boot(sys, null, ix, { nBoot: 400, seed: 2 }); return { label: sys, value: r.diff, low: r.low, high: r.high, color: Q.COLORS[sys] }; }),
      { w: 470, hgt: 270, hi: 0.5, ticks: [0, 0.1, 0.2, 0.3, 0.4, 0.5], ylabel: 'mean NDCG@10 (validation)' });
  }
  function colourPanels(consistent) {
    const wrap = h('div', { class: 'row', style: { gap: '4px', alignItems: 'flex-start' } });
    [['user_group', 'by user group'], ['item_age_group', 'by movie age']].forEach(([sl, t], p) => {
      const S = Q.SLICES[sl], items = [];
      S.labels.forEach((lab, k) => { const ix = Q.sliceIdx('val', sl, k); ['popularity', 'learned'].forEach((sys) => {
        const col = consistent || p === 0 ? Q.COLORS[sys] : Q.COLORS[sys === 'learned' ? 'popularity' : 'learned'];
        items.push({ label: sys === 'learned' ? lab.split(' ')[0] : '', value: Q.sysMean(sys, ix), color: col, tip: `${lab} · ${sys}` }); }); });
      const legend = h('div', { class: 'legend', style: { justifyContent: 'center', fontSize: '12px' } }, ['popularity', 'learned'].map((sys) => {
        const col = consistent || p === 0 ? Q.COLORS[sys] : Q.COLORS[sys === 'learned' ? 'popularity' : 'learned'];
        return h('span', {}, h('i', { style: { background: col } }), sys); }));
      wrap.append(h('div', {}, h('div', { class: 'small', style: { textAlign: 'center', fontWeight: 700 } }, t), Q.bars(items, { w: 232, hgt: 240, hi: 0.8, ticks: [0, 0.4, 0.8], ci: false, labelSize: 10 }), legend));
    });
    return wrap;
  }
  function labelled(clear) {
    const rows = Q.liftRows('val', 'item_age_group').map((r) => clear ? { ...r, label: r.label + ' old', sub: `n=${r.n}` } : { ...r, label: '', sub: null });
    return h('div', {}, h('div', { class: 'chart-title' }, clear ? 'Where does the trained model lose to the best simple feed?' : 'Results'),
      Q.forest(rows, { w: 540, rowH: 46, labelW: clear ? 130 : 30, lo: -0.55, hi: 0.55, ticks: [-0.5, -0.25, 0, 0.25, 0.5], tickFmt: (v) => (v > 0 ? '+' : '') + v.toFixed(2),
        label: clear ? 'NDCG@10: trained model − best simple feed, by movie age' : '' }));
  }
  const CASES = [
    { q: 'Claim: "the trained model is far better than popularity".', legend: true, bad: () => overallBars(false, 0.37), good: () => overallBars(true, 0),
      opts: ['The bars do not start at 0, so a 20% gap looks ten times bigger', 'The colours are wrong', 'It should be a pie chart', 'NDCG is the wrong metric'], ok: 0,
      why: 'A bar shows a value by its length. Cut the axis at 0.37 and the lengths no longer match the numbers.',
      takeaway: 'Bars start at 0. To zoom in, use points instead of bars.' },
    { q: 'Claim: "the trained model loses on Animation movies, fix that first".', legend: true, bad: () => genreBars(false), good: () => genreBars(true),
      opts: ['Genres should be sorted alphabetically', 'There is no interval and no count: Animation has only 50 moments', 'Too many colours', 'The y axis should be logarithmic'], ok: 1,
      why: 'Animation has 50 moments and a gap of −0.002. With intervals the two bars overlap completely: there is nothing to fix.',
      takeaway: 'Show an interval and the number of moments on every comparison.' },
    { q: 'Claim: "learned takes almost half of the score".', bad: () => pieScores(), good: () => scoreBars(),
      opts: ['A pie shows parts of a whole, and four separate scores are not parts of anything', 'The slices need more decimals', 'It needs a 3-D effect', 'The colours are too similar'], ok: 0,
      why: 'Adding the four scores together means nothing, so their "shares" mean nothing either. Bars compare them directly.',
      takeaway: 'Use a pie only for parts of a whole. To compare scores, use bars or points.' },
    { q: 'Two charts in the same report.', bad: () => colourPanels(false), good: () => colourPanels(true),
      opts: ['The two charts have different y ranges', 'learned and popularity swap colours between the two charts', 'The labels are too short', 'There should be one chart per group'], ok: 1,
      why: 'Readers learn the colours in the first chart and carry them to the second one, where they now read the opposite.',
      takeaway: 'Give each strategy one colour and keep it in every chart.' },
    { q: 'A chart pasted into a report.', bad: () => labelled(false), good: () => labelled(true),
      opts: ['The dots are too small', 'It should be a line chart', 'Nothing says what is measured: no question, no axis label, no group names', 'The colours are wrong'], ok: 2,
      why: 'The numbers are right, but nobody can tell what the rows are or what the axis measures.',
      takeaway: 'The title is the question the chart answers; every row and axis says what it is.' },
    { q: 'Trained model minus the best simple feed, per user group × movie age.', bad: () => heatmap('jet'), good: () => heatmap('div'),
      opts: ['The cells should be bigger', 'Rows and columns are swapped', 'The rainbow colours hide where the difference is 0', 'There are too many decimals'], ok: 2,
      why: 'In a rainbow, "slightly worse" and "slightly better" get unrelated colours.',
      takeaway: 'For values that can be negative or positive: one colour for worse, one for better, white for no difference.' },
  ];
  Deck.register('clearcharts', (root) => {
    let k = 0, answered = null, fixed = false;
    const stage = h('div');
    const count = h('span', { class: 'readout' });
    function draw() {
      const C = CASES[k];
      count.textContent = `Chart ${k + 1} / ${CASES.length}`;
      stage.innerHTML = '';
      const chart = h('div', { class: 'crime-chart' + (fixed ? ' fixed' : '') }, h('span', { class: 'stamp' }, fixed ? 'CLEAR' : 'MISLEADING'), fixed ? C.good() : C.bad(), C.legend ? Q.legend(['popularity', 'learned']) : null);
      const opts = h('div', { class: 'crime-opts' }, C.opts.map((o, i) => h('button', { type: 'button', class: 'crime-opt' + (answered != null ? (i === C.ok ? ' right' : i === answered ? ' wrong' : '') : ''), 'data-tip': 'The room picks one answer.',
        onpointerdown: (e) => { e.preventDefault(); if (answered == null) { answered = i; draw(); } } }, h('b', {}, 'ABCD'[i]), ' ', o)));
      const fb = answered == null ? null : h('div', { class: 'callout ' + (answered === C.ok ? 'green' : 'red'), style: { fontSize: '15px' } }, h('b', {}, answered === C.ok ? 'Yes. ' : 'Not this one. '), C.why);
      const take = answered == null ? null : h('div', { class: 'callout purple', style: { fontSize: '16px' } }, h('b', {}, 'Takeaway: '), C.takeaway);
      stage.append(h('div', { class: 'cols', style: { gridTemplateColumns: '1fr 1fr', alignItems: 'start', gap: '18px' } }, chart,
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } }, h('p', { style: { fontSize: '17px' } }, h('b', {}, C.q), ' What makes this chart misleading?'), opts, fb, take,
          answered != null ? h('div', { class: 'row' }, button(fixed ? 'Show the misleading version' : 'Show the clear version', () => { fixed = !fixed; draw(); })) : null)));
    }
    root.append(h('div', { class: 'row', style: { justifyContent: 'space-between' } }, count, h('div', { class: 'row' },
      button('◀ Chart', () => { k = (k + CASES.length - 1) % CASES.length; answered = null; fixed = false; draw(); }, 'ghost small'),
      button('Next chart ▶', () => { k = (k + 1) % CASES.length; answered = null; fixed = false; draw(); }),
      button('Reset', () => { k = 0; answered = null; fixed = false; draw(); }, 'ghost small'))), stage);
    draw();
  });

  /* ===================== anatomy: every element of a figure and the line that makes it ===================== */
  const CODE = [
    ['fig', 'fig, ax = plt.subplots(figsize=(8, 5))'],
    ['err', 'ax.errorbar(diffs, y, xerr=[diffs - lows, highs - diffs], fmt="o", capsize=4)'],
    ['zero', 'ax.axvline(0, color="black", lw=1)'],
    ['ticks', 'ax.set_yticks(y, [f"{s} (n={n})" for s, n in zip(slices, ns)])'],
    ['xlabel', 'ax.set_xlabel("NDCG@10 of learned minus the best baseline")'],
    ['title', 'ax.set_title("B · Where does learned lose against the best baseline?")'],
    ['legend', 'ax.legend(handles=[wins, loses], title="verdict")'],
    ['save', 'fig.savefig("failure_atlas.png", dpi=120, bbox_inches="tight")'],
  ];
  const WHAT = {
    fig: 'Figure: the whole canvas. Axes: one panel inside it. Always draw on ax, not plt.',
    err: 'errorbar: one point per slice and its 95% interval. fmt="o" draws points, not a line.',
    zero: 'axvline(0): the reference line. Without it the reader cannot tell wins from losses.',
    ticks: 'set_yticks(positions, labels): put the slice name and its n on each row.',
    xlabel: 'set_xlabel: what the number means, in words. Never "x" or "diff".',
    title: 'set_title: the question this panel answers, starting with its letter.',
    legend: 'legend: needed as soon as colour means something.',
    save: 'savefig: the PNG you submit. bbox_inches="tight" keeps long labels.',
  };
  Deck.register('anatomy', (root) => {
    let sel = 'err';
    const codeBox = h('div', { class: 'code-lines' });
    const what = h('div', { class: 'callout purple', style: { fontSize: '15.5px', minHeight: '64px' } });
    const W = 600, H = 360;
    const s = Q.frame(W, H);
    const hot = {};
    const zone = (key, el) => { el.setAttribute('class', 'hot'); el.setAttribute('data-tip', WHAT[key]); el.addEventListener('pointerdown', (e) => { e.preventDefault(); pick(key); }); hot[key] = (hot[key] || []).concat(el); return el; };
    s.append(zone('fig', svg('rect', { x: 2, y: 2, width: W - 4, height: H - 4, rx: 8, fill: 'var(--surface)', stroke: 'var(--border)', 'stroke-width': 2 })));
    s.append(svg('rect', { x: 170, y: 46, width: 400, height: 240, fill: '#fff', stroke: '#9aa6bd' }));
    s.append(zone('title', svg('text', { x: 370, y: 32, 'text-anchor': 'middle', 'font-size': 14, 'font-weight': 700, fill: 'var(--ink)' }, 'B · Where does learned lose against the best baseline?')));
    const rows = [['<1 year (n=104)', -0.44, 0.065, '#c4121e'], ['1-5 years (n=281)', -0.029, 0.02, '#c4121e'], ['5-15 years (n=844)', 0.037, 0.015, '#2e8a00'], ['15+ years (n=579)', 0.2, 0.02, '#2e8a00']];
    const X = (v) => 170 + (v + 0.5) / 0.75 * 400;
    rows.forEach(([lab, d, e, c], k) => {
      const y = 80 + k * 55;
      s.append(zone('ticks', svg('text', { x: 162, y: y + 4, 'text-anchor': 'end', 'font-size': 12.5, fill: 'var(--ink)' }, lab)));
      s.append(zone('err', svg('line', { x1: X(d - e), x2: X(d + e), y1: y, y2: y, stroke: c, 'stroke-width': 3 })));
      s.append(zone('err', svg('circle', { cx: X(d), cy: y, r: 7, fill: c })));
    });
    s.append(zone('zero', svg('line', { x1: X(0), x2: X(0), y1: 46, y2: 286, stroke: '#000', 'stroke-width': 2.5 })));
    [-0.4, -0.2, 0, 0.2].forEach((t) => s.append(svg('text', { x: X(t), y: 302, 'text-anchor': 'middle', 'font-size': 11.5, fill: 'var(--muted)' }, (t > 0 ? '+' : '') + t.toFixed(1))));
    s.append(zone('xlabel', svg('text', { x: 370, y: 324, 'text-anchor': 'middle', 'font-size': 12.5, 'font-weight': 700, fill: 'var(--accent)' }, 'NDCG@10 of learned minus the best baseline')));
    const lg = svg('g'); lg.append(svg('rect', { x: 440, y: 54, width: 120, height: 48, fill: '#fff', stroke: '#ccc', rx: 4 }), svg('circle', { cx: 456, cy: 70, r: 5, fill: '#2e8a00' }), svg('text', { x: 468, y: 74, 'font-size': 11.5 }, 'wins'), svg('circle', { cx: 456, cy: 90, r: 5, fill: '#c4121e' }), svg('text', { x: 468, y: 94, 'font-size': 11.5 }, 'loses'));
    s.append(zone('legend', lg));
    s.append(zone('save', svg('text', { x: 18, y: 348, 'font-size': 11.5, fill: 'var(--muted)' }, '💾 failure_atlas.png')));
    function pick(key) {
      sel = key;
      Object.entries(hot).forEach(([k, els]) => els.forEach((el) => el.classList.toggle('on', k === key)));
      codeBox.innerHTML = '';
      CODE.forEach(([k, line]) => codeBox.append(h('div', { class: 'code-line' + (k === key ? ' on' : ''), onpointerdown: (e) => { e.preventDefault(); pick(k); } }, line)));
      what.textContent = WHAT[key];
    }
    root.append(h('div', { class: 'cols', style: { gridTemplateColumns: '600px 1fr', gap: '18px', alignItems: 'start' } }, s, h('div', { style: { display: 'flex', flexDirection: 'column', gap: '10px' } }, codeBox, what)));
    pick(sel);
  });

  /* ===================== replay: the time-split protocol for InstaKill (teaching model) ===================== */
  Deck.register('replay', (root) => {
    const r = U.rng(9);
    const POSTS = Array.from({ length: 18 }, (_, k) => ({ id: k, t: 0.02 + 0.9 * (k / 18) + r() * 0.04 }));
    const LIKES = [];
    for (let k = 0; k < 70; k++) { const p = POSTS[(r() * POSTS.length) | 0]; LIKES.push({ post: p.id, t: U.clamp(p.t + r() * 0.35, 0, 0.99), user: (r() * 4) | 0 }); }
    let cut = 0.8;
    const host = h('div'), facts = h('div', { class: 'boot-read' });
    const sl = U.slider({ label: 'Cut-off T', min: 0.3, max: 0.95, step: 0.01, value: cut, digits: 2, format: (v) => `${Math.round(v * 100)}%`, onInput: (v) => { cut = v; draw(); } });
    function draw() {
      const W = 1180, H = 250, x0 = 70, x1 = W - 20;
      const X = (t) => x0 + t * (x1 - x0);
      const s = Q.frame(W, H);
      s.append(svg('rect', { x: x0, y: 8, width: X(cut) - x0, height: 196, fill: 'rgba(11,47,99,.07)' }));
      s.append(svg('rect', { x: X(cut), y: 8, width: x1 - X(cut), height: 196, fill: 'rgba(247,163,15,.12)' }));
      s.append(svg('text', { x: x0 + 8, y: 26, 'font-size': 13, 'font-weight': 800, fill: 'var(--navy)' }, 'SNAPSHOT: what the app knew'));
      s.append(svg('text', { x: x1 - 8, y: 26, 'text-anchor': 'end', 'font-size': 13, 'font-weight': 800, fill: '#8a5500' }, 'ANSWERS: the likes we try to predict'));
      ['posts', 'user 1', 'user 2', 'user 3', 'user 4'].forEach((lab, k) => s.append(svg('text', { x: x0 - 8, y: 58 + k * 34, 'text-anchor': 'end', 'font-size': 12, fill: 'var(--muted)' }, lab)));
      let keptPosts = 0, keptLikes = 0, answers = 0, lostAnswers = 0;
      POSTS.forEach((p) => {
        const before = p.t < cut; if (before) keptPosts++;
        s.append(svg('rect', { x: X(p.t) - 6, y: 48, width: 12, height: 14, rx: 2, fill: before ? 'var(--navy)' : '#c9d2e2', 'data-tip': before ? 'post created before T: in the snapshot' : 'post created after T: deleted from the snapshot' }));
      });
      LIKES.forEach((l) => {
        const post = POSTS[l.post], y = 92 + l.user * 34;
        let fill, tip;
        if (l.t < cut) { fill = 'var(--navy)'; keptLikes++; tip = 'like before T: history, stays in the snapshot'; }
        else if (post.t < cut) { fill = 'var(--gold)'; answers++; tip = 'like after T on a post that existed at T: an answer'; }
        else { fill = '#c9d2e2'; lostAnswers++; tip = 'like after T on a post created after T: not in the snapshot, so not a fair question'; }
        s.append(svg('circle', { cx: X(l.t), cy: y, r: 6, fill, 'data-tip': tip }));
      });
      s.append(svg('line', { x1: X(cut), x2: X(cut), y1: 8, y2: 210, stroke: 'var(--red)', 'stroke-width': 3 }));
      s.append(svg('text', { x: X(cut), y: 228, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 800, fill: 'var(--red)' }, 'T  (now = T for every strategy)'));
      host.innerHTML = ''; host.append(s);
      facts.innerHTML = `Snapshot: <b>${keptPosts}</b> posts, <b>${keptLikes}</b> likes · answers: <b>${answers}</b> likes on snapshot posts · ignored: <b>${lostAnswers}</b> likes on posts that did not exist at T. Move T: later = more history but fewer answers.`;
    }
    root.append(sl.el, host, facts);
    draw();
  });
})();
