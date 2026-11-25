/* Widgets: a dirty event log that is cleaned one step at a time, and the "order of steps" demonstration. */
(function () {
  const { h, segmented } = U;

  /* ===================== dirtylog: twelve rows, six cleaning steps ===================== */
  const STEPS = [
    { key: '0 raw', title: 'The raw log', code: 'raw = pd.read_csv("raw_events.csv")', say: 'Twelve rows as they arrived. Look for what is wrong before reading further.' },
    { key: '1 types', title: 'Fix the types', code: 'df["rating"] = to_number(df["rating"])\ndf["ts"] = to_epoch_seconds(df["ts"])', say: 'Spaces, decimal commas, milliseconds and date text become numbers. Unreadable values become NaN, so the next step can find them. Nothing is removed yet.' },
    { key: '2 incomplete', title: 'Drop incomplete rows', code: 'df = df.dropna(subset=["user_id", "item_id", "rating", "ts"])', say: 'A row without a user, an item, a rating or a time cannot be used.' },
    { key: '3 timestamps', title: 'Drop impossible timestamps', code: 'df = df[df["ts"].between(MIN_VALID_TS, EXPORT_TS)]', say: '1970 and 2067 are impossible for a log exported in 2018. Do this before looking for duplicates (see the next demo).' },
    { key: '4 items', title: 'Drop unknown items', code: 'checked = df.merge(movies, on="item_id", how="left", indicator=True, validate="m:1")\ndf = checked[checked["_merge"] == "both"]', say: 'Every event must point to an item that exists. indicator=True says, row by row, whether the match was found.' },
    { key: '5 repeats', title: 'Drop exact repeats', code: 'df = df.drop_duplicates()', say: 'Rows equal in every column are one event written twice.' },
    { key: '6 retries', title: 'Keep the first event per (user, item)', code: 'df = (df.sort_values("ts")\n         .drop_duplicates(subset=["user_id", "item_id"], keep="first"))', say: 'A retry is the same event logged again a few seconds later. The rows differ, the event is one. Keep the earliest.' },
  ];

  // raw: what the log says. fixed: what step 1 turns it into (only the cells that change). gone: [step that removes the row, reason]
  const ROWS = [
    { raw: ['17', '296', '5.0', '1332458321'] },
    { raw: [' 17 ', '318', '4,5', '1332458390'], fixed: { 0: '17', 2: '4.5' } },
    { raw: ['17', '296', '5.0', '1332458321'], gone: [5, 'exact repeat of row 1'] },
    { raw: ['42', '1196', '3.0', '1464712004000'], fixed: { 3: '1464712004' } },
    { raw: ['42', '1196', '3.0', '1464712031'], gone: [6, 'retry of row 4, 27 s later'] },
    { raw: ['', '260', '4.0', '1230788200'], fixed: { 0: 'NaN' }, gone: [2, 'no user'] },
    { raw: ['8', '2571', '', '1230788250'], fixed: { 2: 'NaN' }, gone: [2, 'no rating'] },
    { raw: ['8', '2571', '4.0', '0'], gone: [3, 'timestamp in 1970'] },
    { raw: ['8', '2571', '4.0', '1230788250'] },
    { raw: ['23', '999999', '3.5', '1190000000'], gone: [4, 'item not in movies.csv'] },
    { raw: ['23', '50', '3.5', '2015-03-02 09:15:00'], fixed: { 3: '1425287700' } },
    { raw: ['5', '1', '4.0', '3077000000'], gone: [3, 'timestamp in 2067'] },
  ];

  Deck.register('dirtylog', (root) => {
    let step = 0;
    const tbody = h('tbody');
    const caption = h('p', { class: 'small', style: { margin: '0', fontSize: '15px', lineHeight: '1.35' } });
    const code = h('pre', { class: 'code', style: { margin: '0', minHeight: '64px', fontSize: '12.5px' } }, h('code'));
    const left = h('span', { class: 'readout' });
    const seg = segmented(STEPS.map((s, i) => ({ value: i, label: s.key })), 0, (v) => { step = v; render(); }, 'Cleaning step');

    function render() {
      tbody.innerHTML = '';
      let alive = 0;
      ROWS.forEach((row, i) => {
        const removed = row.gone && step >= row.gone[0];
        if (!removed) alive++;
        const tr = h('tr', { style: removed ? { opacity: '.42' } : {} });
        const pad = { padding: '3px 10px' };
        tr.append(h('td', { style: { ...pad, color: 'var(--muted)', width: '28px', fontSize: '14px' } }, String(i + 1)));
        row.raw.forEach((cell, c) => {
          const fixedNow = step >= 1 && row.fixed && row.fixed[c] !== undefined;
          const text = fixedNow ? row.fixed[c] : cell;
          const shown = text === '' ? '∅' : text;
          tr.append(h('td', {
            class: 'mono',
            style: {
              ...pad, fontSize: '14px',
              whiteSpace: 'pre', textDecoration: removed ? 'line-through' : 'none',
              background: fixedNow ? 'rgba(247,163,15,.28)' : 'transparent',
              color: text === '' || text === 'NaN' ? 'var(--bad)' : 'inherit',
            },
          }, shown));
        });
        tr.append(h('td', { style: { ...pad, fontSize: '14px', color: removed ? 'var(--bad)' : 'var(--good)' } }, removed ? '✗ ' + row.gone[1] : (step === 6 ? '✓ kept' : '')));
        tbody.append(tr);
      });
      caption.innerHTML = '';
      caption.append(h('b', {}, STEPS[step].title + '. '), STEPS[step].say);
      code.firstChild.textContent = STEPS[step].code;
      left.textContent = `${alive} of ${ROWS.length} rows left`;
    }

    const table = h('table', { class: 't', style: { fontSize: '14px' } },
      h('thead', {}, h('tr', {}, ['#', 'user_id', 'item_id', 'rating', 'ts', 'what happens'].map((t) => h('th', { style: { padding: '4px 10px' } }, t)))), tbody);
    root.append(h('div', { class: 'row', style: { alignItems: 'center', gap: '14px' } }, seg.el, left), table,
      h('div', { class: 'cols two', style: { alignItems: 'start' } }, caption, code));
    render();
  });

  /* ===================== order: the same two steps in two different orders ===================== */
  Deck.register('order', (root) => {
    const BASE = [
      { tag: 'the real event', ts: 1230788250 },
      { tag: 'a bad copy', ts: 0 },
      { tag: 'a retry, 20 s later', ts: 1230788270 },
    ];
    const FILTER = { code: 'df = df[df["ts"].between(MIN_VALID_TS, EXPORT_TS)]', name: 'filter impossible timestamps' };
    const DEDUP = { code: 'df = (df.sort_values("ts")\n         .drop_duplicates(["user_id", "item_id"]))', name: 'keep the earliest per (user, item)' };
    // gone[row] = [step that removes it, reason]
    const SCENARIOS = [
      { title: 'A · filter timestamps first', steps: [FILTER, DEDUP],
        gone: { 1: [1, 'ts = 0 is impossible'], 2: [2, 'not the earliest of (8, 2571)'] },
        verdict: ['1 row left: the real event. Correct.', 'green'] },
      { title: 'B · keep the earliest first', steps: [DEDUP, FILTER],
        gone: { 0: [1, 'not the earliest: ts = 0 comes first'], 2: [1, 'not the earliest: ts = 0 comes first'], 1: [2, 'ts = 0 is impossible'] },
        verdict: ['0 rows left: the 1970 copy won, then the filter removed it. The like has vanished. (Skip the filter and a like dated 1970 stays in your data.)', 'red'] },
    ];
    let step = 0;
    const panes = SCENARIOS.map((sc) => {
      const codeEls = sc.steps.map((st) => h('pre', { class: 'code', style: { margin: '0', fontSize: '12.5px', padding: '8px 12px', whiteSpace: 'pre' } }, h('code', {}, st.code)));
      const tbody = h('tbody');
      const count = h('span', { class: 'readout' });
      const verdict = h('div', { class: 'callout', style: { fontSize: '15px', minHeight: '64px' } });
      const el = h('div', { style: { display: 'flex', flexDirection: 'column', gap: '8px' } },
        h('h3', { style: { margin: '0', fontSize: '18px' } }, sc.title),
        h('div', { style: { display: 'flex', flexDirection: 'column', gap: '4px' } },
          h('small', {}, 'Step 1'), codeEls[0], h('small', {}, 'Step 2'), codeEls[1]),
        h('table', { class: 't', style: { fontSize: '14px' } },
          h('thead', {}, h('tr', {}, ['row', 'user_id', 'item_id', 'ts', 'what happens'].map((t) => h('th', { style: { padding: '4px 8px' } }, t)))), tbody),
        count, verdict);
      return { sc, codeEls, tbody, count, verdict, el };
    });

    function render() {
      panes.forEach(({ sc, codeEls, tbody, count, verdict }) => {
        codeEls.forEach((c, k) => {
          const active = step === k + 1;
          c.style.outline = active ? '3px solid var(--gold)' : 'none';
          c.style.opacity = step === 0 || active || step > k + 1 ? '1' : '.55';
        });
        tbody.innerHTML = '';
        let alive = 0;
        BASE.forEach((row, i) => {
          const g = sc.gone[i];
          const removed = g && step >= g[0];
          const justNow = g && step === g[0];
          if (!removed) alive++;
          const pad = { padding: '3px 8px' };
          tbody.append(h('tr', { style: { opacity: removed ? '.45' : '1', background: justNow ? 'rgba(238,25,39,.10)' : 'transparent' } },
            h('td', { style: { ...pad, fontSize: '14px' } }, row.tag),
            h('td', { class: 'mono', style: pad }, '8'),
            h('td', { class: 'mono', style: pad }, '2571'),
            h('td', { class: 'mono', style: { ...pad, textDecoration: removed ? 'line-through' : 'none' } }, String(row.ts)),
            h('td', { style: { ...pad, fontSize: '13px', color: 'var(--bad)' } }, removed ? '✗ ' + g[1] : '')));
        });
        count.textContent = `${alive} of ${BASE.length} rows left`;
        verdict.innerHTML = '';
        verdict.className = 'callout' + (step === 2 ? ' ' + sc.verdict[1] : '');
        verdict.textContent = step === 2 ? sc.verdict[0] : step === 0 ? 'Both pipelines start from the same three rows.' : `After step 1 (${sc.steps[0].name}).`;
      });
    }

    const seg = segmented([{ value: 0, label: 'Start' }, { value: 1, label: 'Step 1' }, { value: 2, label: 'Step 2' }], 0, (v) => { step = v; render(); }, 'Pipeline step');
    root.append(h('div', { class: 'row', style: { alignItems: 'center', gap: '14px' } }, seg.el, h('span', { class: 'small' }, 'Both pipelines run the same two operations. Only the order differs.')),
      h('div', { class: 'cols two', style: { alignItems: 'start' } }, panes[0].el, panes[1].el));
    render();
  });
})();
