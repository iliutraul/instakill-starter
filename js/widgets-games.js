/* Game widgets on the real data: bets, the reveal, the population mix. */
(function () {
  const { h, svg, button } = U;

  /* ===================== bets: where does learned lose? ===================== */
  Deck.register('bets', (root) => {
    const CHIPS = 3;
    const cards = [
      ...Q.D.UG.map((lab, k) => ({ slice: 'user_group', k, lab, kind: 'users with' })),
      ...Q.D.IA.map((lab, k) => ({ slice: 'item_age_group', k, lab: lab + ' old', kind: 'the liked movie is' })),
    ];
    let chips = cards.map(() => false);
    let revealed = false;
    const results = cards.map((c) => Q.liftRows('val', c.slice)[c.k]);
    const left = h('span', { class: 'readout' });
    const outcome = h('p', { style: { fontSize: '17px', fontWeight: 700, color: 'var(--accent)' } });
    const grid = h('div', { class: 'bet-grid' });
    const used = () => chips.filter(Boolean).length;
    function draw() {
      grid.innerHTML = '';
      cards.forEach((c, i) => {
        const r = results[i];
        const card = h('button', { type: 'button', class: 'bet-card' + (revealed ? ' rev ' + r.verdict : '') + (chips[i] ? ' bet' : ''), 'data-tip': revealed ? r.tip : 'Put one of the room\'s chips here. Press again to take it back.',
          onpointerdown: (e) => {
            e.preventDefault(); if (revealed) return;
            if (chips[i]) chips[i] = false; else if (used() < CHIPS) chips[i] = true;
            draw();
          } },
          h('span', { class: 'small' }, c.kind), h('b', {}, c.lab),
          h('div', { class: 'chips' }, chips[i] ? h('i', { class: 'chip-dot', style: { background: 'var(--gold)' } }) : null),
          revealed ? h('div', { class: 'bet-res' }, h('b', {}, (r.diff >= 0 ? '+' : '−') + Math.abs(r.diff).toFixed(3)), ` vs ${r.against} · ${r.verdict}`) : null);
        grid.append(card);
      });
      left.textContent = `${CHIPS - used()} of ${CHIPS} chips left`;
      if (revealed) {
        const losing = results.filter((r) => r.verdict !== 'wins').length;
        const hit = cards.filter((_, i) => chips[i] && results[i].verdict !== 'wins').length;
        outcome.textContent = `The room's chips found ${hit} of the ${losing} groups where the trained model does not win.`;
      } else outcome.textContent = '';
    }
    const reveal = button('Reveal', () => { revealed = true; draw(); }, 'gold');
    const reset = button('Reset', () => { chips = cards.map(() => false); revealed = false; draw(); }, 'ghost small');
    root.append(h('div', { class: 'row', style: { justifyContent: 'space-between' } }, left, h('div', { class: 'row' }, reveal, reset)), grid, outcome,
      h('p', { class: 'small' }, 'After Reveal: red = the trained model loses to the best simple feed (95% interval below 0), amber = unclear, green = it wins.'));
    draw();
  });

  /* ===================== reveal: the forest plot, val or test ===================== */
  Deck.register('forest', (root, ds) => {
    let split = ds.split || 'val';
    const host = h('div');
    const note = h('p', { class: 'small' });
    function draw() {
      const rows = [...Q.liftRows(split, 'user_group').map((r) => ({ ...r, label: 'users: ' + r.label })), null,
        ...Q.liftRows(split, 'item_age_group').map((r) => ({ ...r, label: 'liked movie: ' + r.label + ' old' }))];
      host.innerHTML = '';
      host.append(Q.forest(rows, { w: 1180, rowH: 33, labelW: 300, lo: -0.55, hi: 0.55, ticks: [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5],
        label: 'NDCG@10: trained model minus the best simple feed  (left of 0 = it loses)' }));
      const n = Q.idx(split).length;
      note.textContent = `${split === 'val' ? 'Validation set' : 'Test set'} · ${n.toLocaleString('en')} moments · red = loses, green = wins, amber = unclear.`;
    }
    const seg = U.segmented([{ value: 'val', label: 'validation set' }, { value: 'test', label: 'test set' }], split, (v) => { split = v; draw(); }, 'Split');
    root.append(seg.el, host, note);
    draw();
  });

  /* ===================== mix: the average depends on who is in it ===================== */
  const WHAT = {
    chronological: 'newest first',
    popularity: 'most liked in the last year',
    for_you: 'your Week 4 formula (freshness + affinity + popularity)',
    learned: 'the trained model (Week 5)',
  };
  Deck.register('mix', (root) => {
    const ix = Q.D.IA.map((_, k) => Q.sliceIdx('val', 'item_age_group', k));
    const per = Q.SYS.map((s) => ix.map((I) => Q.sysMean(s, I)));
    const MEASURED = ix.map((I) => I.length);
    const PRESETS = { 'Our data (MovieLens)': MEASURED, 'InstaKill: mostly new posts': [60, 25, 10, 5], 'Equal parts': [25, 25, 25, 25] };
    let w = MEASURED.slice();
    const total0 = MEASURED.reduce((a, b) => a + b, 0);
    const rows = Q.D.IA.map((lab, k) => {
      const sl = U.slider({ label: `${lab} old`, min: 0, max: 100, step: 1, value: Math.round(100 * w[k] / total0), digits: 0, unit: '%', onInput: () => { w = rows.map((r) => r.sl.get()); draw(); } });
      const bestJ = per.map((p) => p[k]).indexOf(Math.max(...per.map((p) => p[k])));
      const best = Q.SYS[bestJ];
      const tag = h('span', { class: 'mix-best', style: { '--c': Q.COLORS[best] } }, 'best here: ', h('b', {}, best));
      return { sl, el: h('div', { class: 'mix-row' }, sl.el, tag) };
    });
    const board = h('div', { class: 'mix-board' });
    const banner = h('div', { class: 'callout gold', style: { fontSize: '16px' } });
    function draw() {
      const tot = w.reduce((a, b) => a + b, 0) || 1;
      const overall = Q.SYS.map((s, j) => ({ s, v: per[j].reduce((a, m, k) => a + m * w[k] / tot, 0) }));
      overall.sort((a, b) => b.v - a.v);
      board.innerHTML = '';
      overall.forEach(({ s, v }, r) => board.append(h('div', { class: 'mix-bar' },
        h('div', { class: 'mix-name' }, h('b', {}, `${r + 1}. ${s}`), h('span', {}, WHAT[s])),
        h('div', { class: 'track' }, h('div', { class: 'fill', style: { width: `${100 * v / 0.8}%`, background: Q.COLORS[s] } })),
        h('span', { class: 'num' }, v.toFixed(2)))));
      const top = overall[0].s;
      banner.innerHTML = top === 'learned'
        ? '<b>Challenge:</b> make the likes look like InstaKill (mostly new posts). Does <code>learned</code> still win?'
        : `Now <b>${top}</b> wins. The strategies did not change, only <b>what the users like</b>.`;
    }
    const presets = h('div', { class: 'row' }, Object.entries(PRESETS).map(([name, v]) => button(name, () => { const t = v.reduce((a, b) => a + b, 0); rows.forEach((r, k) => r.sl.set(Math.round(100 * v[k] / t))); w = rows.map((r) => r.sl.get()); draw(); }, 'ghost small')));
    root.append(h('div', { class: 'cols', style: { gridTemplateColumns: '1fr 1.1fr', gap: '18px' } },
      h('div', { class: 'panel' }, h('h3', {}, 'Of all likes, how many go to movies that are…'), ...rows.map((r) => r.el), presets),
      h('div', { class: 'panel' }, h('h3', {}, 'Overall score (NDCG@10) of each strategy'), board, banner)));
    draw();
  });

})();
