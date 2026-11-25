/* Tooltips: what happens if you press / move this control. Keys are "widget:label" (or "*:label" for any widget). Controls with their own data-tip use that. */
window.TIPS = {
  /* ---- header and overlays ---- */
  'chrome:◀': 'Go to the previous slide (keyboard: ←).',
  'chrome:▶': 'Go to the next slide (keyboard: →).',
  'chrome:Slides': 'Open the list of all slides and jump to any of them (keyboard: G).',
  'chrome:Notes': 'Show or hide the instructor notes for this slide: what to say and what to click (keyboard: N).',
  'chrome:Full': 'Show the deck full screen. Press again, or Esc, to leave (keyboard: F).',
  'chrome:?': 'Show the keyboard shortcuts (keyboard: ?).',
  '*:Close': 'Close this panel and go back to the slide.',
  '*:Reset': 'Start this game again from the beginning.',

  'roadmap:Walk the road ▶': 'Step to the next week on the road and show what was done there.',
  'bets:Reveal': 'Turn the cards: real val numbers, learned against the best baseline in each slice.',
  'forest:validation set': 'The moments you explore with.',
  'forest:test set': 'The same comparison on moments nobody looked at. Does it hold?',
  'mix:Our data (MovieLens)': 'The real mix we measured: most likes go to movies that are 5 years old or more.',
  'mix:InstaKill: mostly new posts': 'A mix like a social app: most likes go to posts from the last year.',
  'mix:Equal parts': 'The same share of likes for every age group.',
  'clearcharts:Next chart ▶': 'Next chart.',
  'clearcharts:◀ Chart': 'Previous chart.',
  'clearcharts:Show the clear version': 'Redraw the same numbers so the answer is easy to see.',
  'clearcharts:Show the misleading version': 'Back to the misleading version.',
  'replay:Cut-off T': 'Move the cut-off: everything left of it is the snapshot, the likes right of it are the answers.',
};
