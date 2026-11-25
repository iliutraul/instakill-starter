/* Opening widgets: the road so far (with the files each week adds) and the level check. */
(function () {
  const { h, svg, button } = U;

  /* ===================== roadmap: twelve stations ===================== */
  const WEEKS = [
    { w: 1, lab: 'AI Model Detective', did: 'Ran a pretrained classifier on real reviews and found five cases where you disagree with it.', ik: 'Repository from the starter: FastAPI, /health, User and Post models, SQLite.', files: 'app/main.py · app/domain/models.py · app/db/database.py · scripts/seed_db.py · tests/', skill: 'a notebook anyone can re-run' },
    { w: 2, lab: 'Functional Core', did: 'A pure, deterministic ranker behind a service, proven by an acceptance test suite.', ik: 'A service boundary and docs/api-contract.md.', files: 'app/services/ · docs/api-contract.md', skill: 'pure functions + pytest' },
    { w: 3, lab: 'Search by Meaning', did: 'Embeddings from a pretrained encoder; cosine similarity and top-k written by you in NumPy.', ik: 'GET /search over the seeded posts.', files: 'app/search/ (encoder adapter, cosine top-k)', skill: 'vectors, similarity, top-k', req: 'pretrained model integrated (v0)' },
    { w: 4, lab: 'Build the Feed', did: 'Freshness, affinity, popularity; a heap top-k; three weights tuned by hand against two baselines.', ik: 'GET /feed with for_you and chronological; follow and like tables; a pure rank_feed.', files: 'app/feed/ (signals, rank_feed) · follow + like tables', skill: 'algorithms and Big-O', req: 'an algorithm you implemented' },
    { w: 5, lab: 'Learn the Scorer', did: 'A neural network in NumPy: you wrote backprop, passed the gradient check and beat a straight line.', ik: 'CRUD, the MovieLens seeder, strategy=learned with like_model.npz, skew tests.', files: 'app/api/ · app/repositories/ · scripts/seed_movielens.py · models/like_model.npz', skill: 'NumPy, vectorisation, training', req: 'a trained model (v0)' },
    { w: 6, lab: 'Dirty Data Pipeline', did: 'Ran a Colab that turns a broken log into a clean table, and saw a leaky column win by cheating.', ik: 'No change. You kept feature_table.parquet for today.', files: 'nothing (feature_table.parquet stays outside git)', skill: 'pandas, leakage, fingerprints', nolab: true },
    { w: 7, lab: 'Failure Atlas', did: 'Today: where does the model fail, and how sure are we?', ik: 'scripts/evaluate.py, a baseline table with intervals, a static dashboard, the protocol.', files: 'scripts/evaluate.py · reports/ · docs/evaluation-protocol.md', skill: 'slicing, intervals, honest charts', req: 'evaluation against a baseline', now: true },
    { w: 8, lab: 'Beat the Dummy', did: 'A spam/moderation classifier that must beat a trivial baseline.', ik: 'No change.', skill: 'scikit-learn', future: true },
    { w: 9, lab: 'Fine-tune Something Small', did: 'Improve a pretrained model on a small subset; report cost and metrics.', ik: 'Moderation model + a fine-tuned or pretrained feature.', skill: 'transfer learning', future: true },
    { w: 10, lab: 'Notebook to Service', did: 'Adapter, config, tests and versioning around a given model.', ik: 'No change.', skill: 'software design for AI', future: true },
    { w: 11, lab: 'Make It Measurably Faster', did: 'Profile, optimise, benchmark before and after.', ik: 'app/ml adapter, before/after proof, feature freeze.', skill: 'profiling, concurrency', req: 'profiling + optimisation', future: true },
    { w: 12, lab: 'Red-team + Demo Day', did: 'Break someone else\'s frozen repository; present your own.', ik: 'Frozen.', skill: 'end-to-end testing', future: true },
  ];

  Deck.register('roadmap', (root) => {
    const W = 1200, H = 210;
    const pts = WEEKS.map((wk, k) => ({ x: 50 + k * 100, y: k % 2 ? 128 : 70 }));
    const s = svg('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, class: 'chart' });
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let k = 1; k < pts.length; k++) { const a = pts[k - 1], b = pts[k]; d += ` C ${a.x + 50} ${a.y}, ${b.x - 50} ${b.y}, ${b.x} ${b.y}`; }
    s.append(svg('path', { d, fill: 'none', stroke: 'var(--border)', 'stroke-width': 10, 'stroke-linecap': 'round' }));
    const done = svg('path', { d, fill: 'none', stroke: 'var(--gold)', 'stroke-width': 10, 'stroke-linecap': 'round', class: 'road-done' });
    s.append(done);
    const card = h('div', { class: 'card road-card' });
    const nodes = [];
    let sel = 6;
    WEEKS.forEach((wk, k) => {
      const p = pts[k];
      const g = svg('g', { class: 'station' + (wk.now ? ' now' : '') + (wk.future ? ' future' : ''), 'data-tip': `Week ${wk.w}: ${wk.lab}`, tabindex: 0, role: 'button' });
      if (wk.now) g.append(svg('circle', { cx: p.x, cy: p.y, r: 30, class: 'halo' }));
      g.append(svg('circle', { cx: p.x, cy: p.y, r: 22, fill: wk.future ? '#fff' : wk.now ? 'var(--gold)' : 'var(--navy)', stroke: wk.future ? 'var(--border)' : '#fff', 'stroke-width': 3, 'stroke-dasharray': wk.nolab ? '5 4' : 'none' }));
      g.append(svg('text', { x: p.x, y: p.y + 6, 'text-anchor': 'middle', 'font-size': 17, 'font-weight': 800, fill: wk.future ? 'var(--muted)' : wk.now ? '#2a1800' : '#fff' }, 'W' + wk.w));
      g.append(svg('text', { x: p.x, y: k % 2 ? p.y + 46 : p.y - 34, 'text-anchor': 'middle', 'font-size': 11.5, 'font-weight': 700, fill: wk.future ? 'var(--muted)' : 'var(--ink)' }, wk.lab.length > 17 ? wk.lab.slice(0, 16) + '…' : wk.lab));
      if (wk.req) g.append(svg('text', { x: p.x + 17, y: p.y - 15, 'font-size': 15 }, '★'));
      g.addEventListener('pointerdown', (e) => { e.preventDefault(); pick(k); });
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter') pick(k); });
      s.append(g); nodes.push(g);
    });
    function pick(k) {
      sel = k;
      nodes.forEach((n, j) => n.classList.toggle('sel', j === k));
      const wk = WEEKS[k];
      card.innerHTML = '';
      card.append(
        h('div', { class: 'row', style: { justifyContent: 'space-between' } },
          h('h3', {}, `Week ${wk.w} · ${wk.lab}`, wk.nolab ? h('span', { class: 'tag opt', style: { marginLeft: '8px' } }, 'Colab, no lab') : null, wk.now ? h('span', { class: 'tag', style: { marginLeft: '8px', background: 'var(--gold)', color: '#2a1800' } }, 'you are here') : null),
          wk.req ? h('span', { class: 'tag', style: { background: '#e9f6dc', color: '#2e6b00', borderColor: '#bfe39a' } }, '★ unlocks: ' + wk.req) : null),
        h('div', { class: 'cols three', style: { marginTop: '6px' } },
          h('div', {}, h('b', { class: 'small' }, wk.future ? 'WHAT YOU WILL DO' : 'WHAT YOU DID'), h('p', { style: { fontSize: '16px' } }, wk.did)),
          h('div', {}, h('b', { class: 'small' }, 'INSTAKILL'), h('p', { style: { fontSize: '16px' } }, wk.ik)),
          h('div', {}, h('b', { class: 'small' }, wk.files ? 'FILES IN YOUR REPOSITORY' : 'SKILL'), h('p', { class: wk.files ? 'mono-files' : '', style: { fontSize: '15px' } }, wk.files || wk.skill))));
      const len = done.getTotalLength ? done.getTotalLength() : 0;
      if (len) { const frac = Math.min(k, 6) / (WEEKS.length - 1); done.style.strokeDasharray = `${len}`; done.style.strokeDashoffset = `${len * (1 - frac * 1.0)}`; }
    }
    const walk = button('Walk the road ▶', () => { pick(sel >= 6 ? 0 : sel + 1); }, 'gold');
    root.append(s, h('div', { class: 'row', style: { justifyContent: 'space-between' } },
      h('span', { class: 'small' }, '★ = one of the five InstaKill requirements becomes possible · dashed = no lab · grey = still to come'), walk), card);
    requestAnimationFrame(() => pick(6));
    return { show() { pick(sel); } };
  });

  /* ===================== levelcheck: what must already work ===================== */
  const CHECKS = [
    ['W1–W5', 'pytest runs green with one command'],
    ['W4–W5', 'GET /feed serves for_you, chronological and learned'],
    ['W5', 'the skew test passes (the three golden rows)'],
    ['W5', 'the seeder is deterministic: run it twice, same database'],
    ['all', 'at least one git commit for every InstaKill week'],
    ['today', 'feature_table.parquet and like_model.npz are on your laptop'],
  ];
  Deck.register('levelcheck', (root) => {
    const state = Deck.store.get('levelcheck6', CHECKS.map(() => false));
    const bar = h('div', { class: 'xp-fill' });
    const lvl = h('b', { class: 'xp-level' });
    const xp = h('span', { class: 'readout' });
    const box = h('div', { class: 'checks' });
    function draw() {
      box.innerHTML = '';
      CHECKS.forEach(([w, text], i) => {
        const b = h('button', { type: 'button', class: 'check' + (state[i] ? ' on' : ''), 'data-tip': 'Tick it when it works in your repository right now (not "almost").',
          onpointerdown: (e) => { e.preventDefault(); state[i] = !state[i]; Deck.store.set('levelcheck6', state); draw(); } },
          h('span', { class: 'box' }, state[i] ? '✓' : ''), h('span', { class: 'tag' }, w), h('span', {}, text));
        box.append(b);
      });
      const pct = Math.round(100 * state.filter(Boolean).length / CHECKS.length);
      bar.style.width = pct + '%';
      lvl.textContent = pct === 100 ? 'Ready for evaluation' : '';
      xp.textContent = `${state.filter(Boolean).length} / ${CHECKS.length}`;
      root.classList.toggle('maxed', pct === 100);
    }
    const reset = button('Reset', () => { state.fill(false); Deck.store.set('levelcheck6', state); draw(); }, 'ghost small');
    root.append(h('div', { class: 'xp' }, h('div', { class: 'xp-track' }, bar), lvl, xp, reset), box);
    draw();
  });

})();
